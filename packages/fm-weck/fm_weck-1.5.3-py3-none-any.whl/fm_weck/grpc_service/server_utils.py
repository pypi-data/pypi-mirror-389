# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import tempfile
from pathlib import Path

TMP_DIR = Path(tempfile.gettempdir()) / "fm_weck"
TMP_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def read_file(file_path: Path) -> bytes:
    """
    Returns the content of a file as bytes.

    :param file_path: The path to the file.
    :return: The content of the file as bytes.
    """

    with open(file_path, "rb") as file:
        return file.read()
