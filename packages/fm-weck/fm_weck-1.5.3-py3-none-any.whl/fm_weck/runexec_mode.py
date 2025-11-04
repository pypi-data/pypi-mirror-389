# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import importlib.resources as pkg_resources
import logging
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Optional

from fm_weck.resources import BENCHEXEC_WHL, RUNEXEC_SCRIPT
from fm_weck.runexec_util import mountable_absolute_paths_of_command

from .config import Config
from .engine import CACHE_MOUNT_LOCATION, Engine

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tempfile import _TemporaryFileWrapper

    from fm_weck.run_result import RunResult


def _setup_script_in_cache(target: "_TemporaryFileWrapper[bytes]") -> Path:
    # When running multiple instances in parallel it can happen, that two processes interfere
    # when copying the script causing a "Text file is busy" error.
    # Using a temp file avoids this problem.
    # The cleaner solution would be to use a direct bind mount from the package resource, but this does not
    # work on the benchcloud right now.

    with pkg_resources.path("fm_weck.resources", RUNEXEC_SCRIPT) as source_path:
        shutil.copy(source_path, target.name)

    target_path = Path(target.name)
    mode = target_path.stat().st_mode
    # make the temp file executable
    target_path.chmod(mode | os.X_OK)
    target.flush()
    target.close()

    return target_path


def run_runexec(
    benchexec_package: Optional[Path],
    use_image: Optional[str],
    configuration: Config,
    extra_container_args: list[list[str]],
    command: list[str],
) -> "RunResult| None":
    if use_image is not None:
        configuration.set_default_image(use_image)

    engine = Engine.from_config(configuration)
    engine.add_benchexec_capabilities = True
    engine.add_mounting_capabilities = False

    if benchexec_package is not None:
        engine.mount(str(benchexec_package.parent.absolute()), "/home/__fm_weck_benchexec")
        engine.env["PYTHONPATH"] = f"/home/__fm_weck_benchexec/{benchexec_package.name}"
    else:
        # Default to the bundled benchexec package
        benchexec_package = configuration.get_shelve_path_for_benchexec()
        try:
            with pkg_resources.path("fm_weck.resources", BENCHEXEC_WHL) as source_path:
                shutil.copy(source_path, benchexec_package)
            engine.env["PYTHONPATH"] = f"{CACHE_MOUNT_LOCATION}/.lib/benchexec.whl"
        except FileNotFoundError:
            logging.error(f"Resource {BENCHEXEC_WHL} not found in package.")
            return None

    for path in mountable_absolute_paths_of_command(Path.cwd().absolute(), command):
        engine.mount(str(path), str(path) + ":ro")

    for arg in extra_container_args:
        engine.add_container_long_opt(arg)

    engine.handle_io = False

    with (
        NamedTemporaryFile(
            prefix="runexec_", dir=str(configuration.cache_location / ".scripts"), delete=True, delete_on_close=False
        ) as tmp_file,
    ):
        script_path = _setup_script_in_cache(tmp_file)

        rel_path = script_path.relative_to(configuration.cache_location)
        return engine.run(f"{CACHE_MOUNT_LOCATION}/{rel_path}", *command)
