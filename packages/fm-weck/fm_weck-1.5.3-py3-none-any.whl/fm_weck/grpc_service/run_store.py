# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
from threading import Lock

from .request_handling import RunHandler

RUNS_IN_PROGRESS = {}
EXCEPTIONS = {}
LOCK = Lock()
logger = logging.getLogger(__name__)


def add_run(run_handler: RunHandler) -> str:
    with LOCK:
        RUNS_IN_PROGRESS[run_handler.run_id] = run_handler

    return run_handler.run_id


def remove_run(run_id: str) -> None:
    with LOCK:
        RUNS_IN_PROGRESS.pop(run_id, None)


def get_run(run_id: str) -> RunHandler:
    with LOCK:
        return RUNS_IN_PROGRESS.get(run_id)


def active_runs() -> frozenset:
    with LOCK:
        return frozenset(RUNS_IN_PROGRESS.keys())
