# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import contextlib
import multiprocessing
import multiprocessing.synchronize
import os
import threading
import uuid
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Generator, Optional, Tuple, Union

from fm_tools.benchexec_helper import DataModel

from fm_weck.config import Config
from fm_weck.exceptions import Failure, RunFailedError, failure_from_exception
from fm_weck.resources import fm_tools_choice_map, property_choice_map
from fm_weck.serve import run_guided, run_manual

from .server_utils import TMP_DIR

if TYPE_CHECKING:
    from fm_weck.grpc_service.proto.fm_weck_service_pb2 import File, RunRequest
    from fm_weck.run_result import RunResult


def _get_unique_id() -> str:
    return str(uuid.uuid4())


class StillRunningError(Exception):
    pass


def worker(setup_complete_flag, queue: multiprocessing.SimpleQueue, initializer, initargs, target, args, kwargs):
    import signal
    import sys

    # In the rare case that a cancel happens before the target function overrides the
    # signal handler, we need to make sure that the process still sends something over the queue and exits.
    def handle_extremely_fast_sigterm(signum, frame):
        queue.put((False, InterruptedError("Run was canceled before setup complete.")))
        sys.exit(1)

    signal.signal(signal.SIGTERM, handle_extremely_fast_sigterm)
    setup_complete_flag.set()

    try:
        if initializer:
            initializer(*initargs)
        result = target(*args, **kwargs)
        if hasattr(result, "exit_code") and getattr(result, "exit_code", 0) != 0:
            raise RunFailedError(result.exit_code, result.command, getattr(result, "raw_output", None))
        queue.put((True, result))
    except Exception as e:
        queue.put((False, failure_from_exception(e)))


class RunHandler:
    mp = multiprocessing.get_context("spawn")
    _success: bool = False
    _result: Optional[Union["RunResult", Failure]] = None
    _setup_complete: Optional[multiprocessing.synchronize.Event] = None

    def __init__(self, request: "RunRequest"):
        self.request = request
        self.run_id = _get_unique_id()
        self.run_path = TMP_DIR / self.run_id

        self._is_cancelled: bool = False

        self._output_log = self.run_path / "output" / "output.txt"
        self._output_dir = self.run_path / "output"

        self.run_path.mkdir(parents=True, exist_ok=False)

        self._process = None
        self._done = threading.Event()
        self._queue = self.mp.SimpleQueue()

        self._result_listener: threading.Thread = None

    def _set(self, result=Tuple[bool, object]):
        self._success, self._result = result
        if isinstance(self._result, Failure):
            self._success = False
        self._done.set()

    def ready(self) -> bool:
        return self._done.is_set()

    @property
    def output(self) -> str:
        if self.is_running():
            try:
                with self._output_log.open("r") as output_file:
                    return output_file.read()
            except (FileNotFoundError, PermissionError):
                return ""

        if self.ready() and self.successful():
            return self._result.raw_output

    def successful(self) -> bool:
        """
        Returns True if the run was successful, False otherwise.

        :raises StillRunningError: If the run is still running.
        :raises ValueError: If the run has not been started yet.
        """
        if self.ready():
            return self._success

        if self._process is None:
            raise ValueError("Run has not been started yet.")

        raise StillRunningError("The run is still running.")

    @property
    def output_files(self) -> Generator[str, None, None]:
        """
        Names of the files produced by the run.
        """
        for root, _, files in os.walk(self._output_dir):
            for file in files:
                yield os.path.relpath(os.path.join(root, file), self._output_dir)

    def is_running(self):
        """
        A run handler is running, if it has been started and is not finished yet.
        """
        return self._process and (not self.ready())

    def is_canceled(self):
        """
        Returns True if the run was really canceled, i.e. the underlying process terminated, False otherwise.
        Since cancelling a finished run has no effect, calling `cancel_run` will not necessarily
        result in is_canceled() returning True.
        """

        return self._is_cancelled

    def _apply(self, func, args, kwds):
        self._setup_complete = self.mp.Event()
        self._process = self.mp.Process(
            target=worker,
            args=(self._setup_complete, self._queue, os.chdir, (str(self.run_path.absolute()),), func, args, kwds),
            daemon=True,
        )
        self._result_listener = threading.Thread(target=self._listen_for_result, daemon=True)
        self._result_listener.start()
        self._process.start()

    def _listen_for_result(self):
        result = self._queue.get()
        self._process.join()
        self._process.close()
        self._queue.close()
        # Make sure resources are released before
        # setting the result.
        self._set(result)

    def start(self):
        c_program = self.get_c_program(self.request)
        data_model = self.request.data_model

        fm_data = self.get_tool(self.request)
        property_path = self.get_property(self.request)

        tool_version = None
        if self.request.tool.HasField("tool_version"):
            tool_version = self.request.tool.tool_version

        config = Config()
        config.load()

        self._apply(
            func=run_guided,
            args=(
                fm_data.absolute(),
                tool_version,
                config,
                property_path.absolute(),
                [c_program],
            ),
            kwds=dict(
                additional_args=[],
                data_model=DataModel[data_model],
                log_output_to=self._output_log.absolute(),
                output_files_to=self._output_dir.absolute(),
            ),
        )

    def start_expert(self, command: str):
        fm_data = self.get_tool(self.request)
        tool_version = None
        if self.request.tool.HasField("tool_version"):
            tool_version = self.request.tool.tool_version
        command = list(self.request.command)

        config = Config()
        config.load()

        self._apply(
            func=run_manual,
            args=(
                fm_data.absolute(),
                tool_version,
                config,
                command,
            ),
            kwds=dict(
                log_output_to=self._output_log.absolute(),
                output_files_to=self._output_dir.absolute(),
            ),
        )

    def join(self, timeout=None):
        done = self._done.wait(timeout)
        if not done:
            raise TimeoutError(f"Timeout while joining run {self.run_id}.")

    def cleanup(self):
        if self.is_running():
            raise StillRunningError("The run is still running.")

        rmtree(self.run_path, ignore_errors=True)

    def get_tool(self, request: "RunRequest") -> Path:
        tool = request.tool

        if tool.HasField("tool_id"):
            return fm_tools_choice_map()[tool.tool_id]
        else:
            return self.get_custom_tool(tool.tool_file)

    def get_custom_tool(self, data: "File") -> Path:
        custom_tool_path = self.run_path / "_custom_tool.yml"

        with custom_tool_path.open("wb") as custom_tool_file:
            custom_tool_file.write(data.file)
        return custom_tool_path

    def get_property(self, request: "RunRequest") -> Path:
        property = request.property

        if property.HasField("property_id"):
            return property_choice_map()[property.property_id]
        else:
            return self.get_custom_property(property.property_file)

    def get_custom_property(self, property_file: "File") -> Path:
        custom_property_path = self.run_path / "_custom_property.prp"

        with custom_property_path.open("wb") as custom_property_file:
            custom_property_file.write(property_file.file)
        return custom_property_path

    def get_c_program(self, request) -> Path:
        c_program = "_c_program.c"
        c_program_path = self.run_path / c_program
        c_program_path.parent.mkdir(parents=True, exist_ok=True)
        with open(c_program_path, "wb") as c_file:
            c_file.write(request.c_program)
        return c_program

    def cancel_run(self):
        if self.ready():
            # Canceling a run that is already finished has no effect.
            return

        if self._setup_complete is None:
            raise RuntimeError("Run has not been started yet.")

        self._setup_complete.wait()

        if self._process.is_alive():
            self._process.terminate()
            self._is_cancelled = True

    def get_file(self, file_name: str) -> Path:
        """
        Finds the file with the given name in the output directory of the run.
        :param file_name: The name of the file.
        :return: The path to the file.
        :raises FileNotFoundError: If the file does not exist.
        """

        file_path = self._output_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_name} not found.")
        return file_path

    def glob(self, name_pattern: str) -> Generator[Path, None, None]:
        """
        Finds all files in the output directory of the run that match the given pattern.
        :param name_pattern: The pattern to match.
        :return: The paths to the files.
        """

        return self._output_dir.glob(name_pattern)

    def close(self):
        """
        Close the process and the result listener.
        It is a StillRunningError to call this method if the process is still running.
        """

        if self._process is None or self.ready():
            return

        if self._process.is_alive():
            raise StillRunningError("Process is still running.")

        # Should normally not occur, as this would mean, that the process is not alive,
        # but the result listener is still running.
        with contextlib.suppress(ValueError):
            self._process.close()

    def failed(self) -> bool:
        return self.ready() and not self._success

    def failure(self):
        """Return the error object/text when failed, else None."""
        if self.failed():
            return self._result
        return None
