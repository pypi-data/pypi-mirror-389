# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import io
import os
import sys
from typing import Literal


class Capture:
    def __init__(self, target: io.TextIOBase, stream: Literal["stdout, stderr, stdin"] = "stdout"):
        self.io_stream = getattr(sys, stream)
        self._copy = os.dup(self.io_stream.fileno())
        os.dup2(target.fileno(), self.io_stream.fileno())

    def __del__(self):
        # Ensure cleanup in case the context manager isn't used
        self._cleanup()

    def _cleanup(self):
        os.dup2(self._copy, self.io_stream.fileno())

    def __enter__(self):
        return self  # Return the instance for use within the context

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()  # Clean up resources upon leaving the context
