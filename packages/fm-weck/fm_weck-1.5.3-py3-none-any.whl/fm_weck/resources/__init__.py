# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import importlib.resources as pkg_resources
from functools import cache
from pathlib import Path

# During the build of the wheel file, the fm-tools/data directory is copied
# to the wheel file under fm_weck/resources/fm_tools

RUN_WITH_OVERLAY = "run_with_overlay.sh"
BENCHEXEC_WHL = "BenchExec-3.25-py3-none-any.whl"
RUNEXEC_SCRIPT = "runexec"


def iter_fm_data():
    root = pkg_resources.files(__package__) / "fm_tools"
    for entry in root.iterdir():
        if entry.name.endswith((".yml", ".yaml")):
            with pkg_resources.as_file(entry) as path:
                fm_data_path = Path(path)
                if fm_data_path.is_file():
                    yield fm_data_path


def iter_properties():
    root = pkg_resources.files(__package__) / "properties"
    for entry in root.iterdir():
        with pkg_resources.as_file(entry) as path:
            prop_path = Path(path)
            if prop_path.is_file():
                yield prop_path


@cache
def fm_tools_choice_map():
    ignore = {
        "schema.yml",
    }

    actors = {actor_def.stem: actor_def for actor_def in iter_fm_data() if (actor_def.name not in ignore)}

    return actors


@cache
def property_choice_map():
    return {spec_path.stem: spec_path for spec_path in iter_properties() if spec_path.suffix != ".license"}
