# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import subprocess
import traceback
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class NoImageError(Exception):
    pass


class RunFailedError(Exception):
    def __init__(self, exit_code, command, output=None):
        super().__init__(f"Run failed with exit code {exit_code}: {output}")
        self.exit_code = exit_code
        self.command = command
        self.output = output


@dataclass
class Failure:
    kind: str  # e.g., "IMAGE_NOT_FOUND", "CALLED_PROCESS_ERROR", "EXCEPTION"
    message: str  # short, user-facing
    detail: Optional[str] = None  # optional verbose info (stderr/traceback)


def failure_from_exception(e: BaseException) -> Failure:
    # Special cases first
    if isinstance(e, NoImageError):
        failure = Failure("IMAGE_NOT_FOUND", str(e))
    elif isinstance(e, RunFailedError):
        failure = Failure("RUN_FAILED", f"Run failed with exit code {e.exit_code}", detail=e.output)
    elif isinstance(e, subprocess.CalledProcessError):
        # Try to surface stderr/stdout
        stderr = e.stderr if hasattr(e, "stderr") else None
        stdout = e.stdout if hasattr(e, "stdout") else None
        text = stderr or stdout or str(e)
        failure = Failure("CALLED_PROCESS_ERROR", f"Tool failed with exit code {e.returncode}", detail=text)
    else:
        # Generic fallback
        failure = Failure("EXCEPTION", str(e), detail="".join(traceback.format_exception(type(e), e, e.__traceback__)))

    logger.error(f"[failure] kind={failure.kind}: {failure.message}")
    return failure


def failure_to_error_code(failure: "Failure"):
    from fm_weck.grpc_service.proto.fm_weck_service_pb2 import ErrorCode

    FAILURE_KIND_TO_ERROR_CODE = {
        "RUN_NOT_TERMINATED": ErrorCode.EC_RUN_NOT_TERMINATED,
        "RUN_NOT_FOUND": ErrorCode.EC_RUN_NOT_FOUND,
        "RUN_CANCELLED": ErrorCode.EC_RUN_CANCELLED,
        "RUN_FAILED": ErrorCode.EC_RUN_FAILED,
        "CALLED_PROCESS_ERROR": ErrorCode.EC_RUN_FAILED,
        "IMAGE_NOT_FOUND": ErrorCode.EC_RUN_FAILED,
        "EXCEPTION": ErrorCode.EC_UNKNOWN_ERROR,
    }
    return FAILURE_KIND_TO_ERROR_CODE.get(failure.kind, ErrorCode.EC_RUN_FAILED)
