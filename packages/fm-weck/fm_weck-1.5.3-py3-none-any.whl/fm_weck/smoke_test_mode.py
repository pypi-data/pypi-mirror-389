# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import subprocess
from pathlib import Path

from fm_tools.fmtoolversion import FmToolVersion

from .engine import CACHE_MOUNT_LOCATION, Engine

logger = logging.getLogger(__name__)


class SmokeTestError(Exception):
    """Custom exception for smoke test errors."""

    pass


class NoSmokeTestFileError(SmokeTestError):
    """Exception raised when no smoke test file is found."""

    pass


class SmokeTestFileIsEmptyError(SmokeTestError):
    """Exception raised when the smoke test file is empty."""

    pass


class SmokeTestFileIsNotExecutableError(SmokeTestError):
    """Exception raised when the smoke test file is not executable."""

    smoke_test_file: Path

    def __init__(self, smoke_test_file: Path):
        self.smoke_test_file = smoke_test_file
        super().__init__(f"Smoke test file is not executable: {smoke_test_file}")

    pass


def locate_and_check_smoke_test_file(shelve_space: Path) -> str:
    """Check if the smoke test file exists, is executable, and is not empty.

    Args:
        shelve_space: Path to the shelve space directory.

    Returns:
        The relative path to the smoke test file as a string.

    Raises:
        NoSmokeTestFileError: If the smoke test file does not exist.
        SmokeTestFileIsEmptyError: If the smoke test file is empty.
        SmokeTestFileIsNotExecutableError: If the smoke test file is not executable.
    """
    file_path = shelve_space / "smoketest.sh"
    if not file_path.exists():
        raise NoSmokeTestFileError(f"Smoke test file 'smoketest.sh' not found in: {shelve_space}")

    if not file_path.stat().st_mode & os.X_OK:
        raise SmokeTestFileIsNotExecutableError(file_path.relative_to(shelve_space))

    if file_path.stat().st_size == 0:
        raise SmokeTestFileIsEmptyError(f"Smoke test file is empty: {file_path}")

    return f"./{file_path.name}"


def run_smoke_test(fm_data, shelve_space, config):
    if not shelve_space.exists() or not shelve_space.is_dir():
        raise ValueError(f"Invalid shelve space path: {shelve_space}")

    engine = Engine.from_config(fm_data, config)

    tool_dir = shelve_space.relative_to(config.cache_location)
    engine.work_dir = CACHE_MOUNT_LOCATION / tool_dir

    command = locate_and_check_smoke_test_file(shelve_space)

    # Return the result so callers can react to failures and print diagnostics
    return engine.run(command)


def run_smoke_test_gitlab_ci(fm_data: FmToolVersion, tool_dir: Path):
    """
    Run smoke test in GitLab CI mode.
    This mode directly installs required packages using apt instead of building/pulling images.

    Args:
        fm_data: The FmToolVersion object containing tool information
        tool_dir: The directory containing the tool's smoketest.sh script
    """
    # Get required packages from fm_data
    required_packages = fm_data.get_images().required_packages

    if required_packages:
        logger.info("Installing required packages: %s", " ".join(required_packages))

        # Install packages
        try:
            subprocess.run(["apt", "install", "-y", *required_packages], check=True)
            logger.info("Successfully installed packages: %s", " ".join(required_packages))
        except subprocess.CalledProcessError:
            logger.error("Failed to install packages.")
            raise
    else:
        logger.info("No required packages specified for this tool")

    script_command = locate_and_check_smoke_test_file(tool_dir)

    logger.info("Running smoke test script: %s", script_command)
    try:
        subprocess.run([script_command], cwd=tool_dir, check=True)
        logger.info("Smoke test completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error("Smoke test failed with return code %d", e.returncode)
        raise
