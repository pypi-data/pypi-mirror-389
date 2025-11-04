# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

from concurrent import futures
from pathlib import Path
from typing import Generator

import grpc

from fm_weck.exceptions import failure_to_error_code

from . import run_store as RunStore
from .proto.fm_weck_service_pb2 import (
    CancelRunRequest,
    CancelRunResult,
    CleanUpResponse,
    ErrorCode,
    ExpertRunRequest,
    File,
    FileQuery,
    RunID,
    RunRequest,
    RunResult,
    WaitParameters,
    WaitRunResult,
)
from .proto.fm_weck_service_pb2_grpc import FmWeckRemoteServicer, add_FmWeckRemoteServicer_to_server
from .request_handling import RunHandler, StillRunningError
from .server_utils import (
    logger,
    read_file,
)


class FmWeckRemote(FmWeckRemoteServicer):
    def startRun(self, request: RunRequest, context) -> RunID:
        run_handler = RunHandler(request)
        run_handler.start()

        run_id = RunStore.add_run(run_handler)

        return RunID(run_id=run_id)

    def startExpertRun(self, request: ExpertRunRequest, context) -> RunID:
        run_handler = RunHandler(request)
        run_handler.start_expert(request.command)

        run_id = RunStore.add_run(run_handler)

        return RunID(run_id=run_id)

    def cancelRun(self, request: CancelRunRequest, context) -> CancelRunResult:
        run_handler = RunStore.get_run(request.run_id.run_id)

        if not run_handler:
            return CancelRunResult(error=ErrorCode.EC_RUN_NOT_FOUND)

        if run_handler.is_running():
            run_handler.cancel_run()
            # Wait a short amount of time. For most cases, the run should be canceled by now.
            try:
                run_handler.join(request.timeout)
            except TimeoutError:
                return CancelRunResult(timeout=True)

        if request.cleanup_on_success:
            run_handler.cleanup()

        return CancelRunResult(run_result=self._run_result_from_handler(run_handler))

    def waitOnRun(self, request: WaitParameters, context) -> WaitRunResult:
        logger.info("waitOnRun called for run_id=%s, timeout=%s", request.run_id.run_id, request.timeout)
        run_handler = RunStore.get_run(request.run_id.run_id)

        if run_handler is None:
            logger.info("waitOnRun: run not found (run_id=%s)", request.run_id.run_id)
            return WaitRunResult(error=ErrorCode.EC_RUN_NOT_FOUND)

        try:
            run_handler.join(request.timeout)
        except TimeoutError:
            logger.info("waitOnRun: timeout (run_id=%s)", request.run_id.run_id)
            return WaitRunResult(timeout=True)

        if run_handler.ready() and not run_handler._success:
            failure = run_handler.failure()
            error_code = failure_to_error_code(failure) if failure else ErrorCode.EC_UNKNOWN_ERROR
            logger.info("waitOnRun: failed (run_id=%s)", request.run_id.run_id)
            return WaitRunResult(error=error_code)

        logger.info("waitOnRun: success (run_id=%s)", request.run_id.run_id)
        return WaitRunResult(run_result=self._run_result_from_handler(run_handler))

    def queryFiles(self, query: FileQuery, context) -> Generator[File, None, None]:
        run_handler = RunStore.get_run(query.run_id.run_id)
        if run_handler is None:
            return

        filenames_to_consider = query.filenames or []
        name_patterns_to_consider = query.name_patterns or []

        for file_name in filenames_to_consider:
            try:
                file = run_handler.get_file(file_name)
                yield self._file_from_path(file)
            except FileNotFoundError:
                continue

        for name_pattern in name_patterns_to_consider:
            for file in run_handler.glob(name_pattern):
                yield self._file_from_path(file)

        # The empty query returns all files.
        if len(filenames_to_consider) == 0 and len(name_patterns_to_consider) == 0:
            files_generator = self._all_files_from_path(run_handler._output_dir)
            for file in files_generator:
                yield file

    def cleanupRun(self, request: RunID, context):
        run_handler = RunStore.get_run(request.run_id)

        if run_handler is None:
            return CleanUpResponse(success=False, error=ErrorCode.EC_RUN_NOT_FOUND)

        try:
            run_handler.cleanup()
        except StillRunningError:
            return CleanUpResponse(success=False, error=ErrorCode.EC_RUN_NOT_TERMINATED)

        RunStore.remove_run(request.run_id)

        return CleanUpResponse(success=True)

    @staticmethod
    def _file_from_path(file_path: str | Path) -> File:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        return File(name=file_path.name, file=read_file(file_path))

    @staticmethod
    def _all_files_from_path(directory_path: str | Path):
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)

        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                yield FmWeckRemote._file_from_path(file_path)

    @staticmethod
    def _run_result_from_handler(run_handler: RunHandler) -> RunResult:
        return RunResult(
            run_id=RunID(run_id=run_handler.run_id),
            success=run_handler.ready() and run_handler.successful(),
            output=run_handler.output,
            filenames=run_handler.output_files,
        )


def serve(ipaddr: str, port: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_FmWeckRemoteServicer_to_server(FmWeckRemote(), server)
    server.add_insecure_port(f"{ipaddr}:{port}")
    server.start()
    logger.info("Server started, listening on " + port)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down the server...")
        server.stop(grace=0)
        logger.info("Server successfully shut down.")
