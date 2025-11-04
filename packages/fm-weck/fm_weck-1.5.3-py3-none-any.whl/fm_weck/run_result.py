# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from benchexec.tools.template import BaseTool2
    from fm_tools.fmtoolversion import FmToolVersion


@dataclass(frozen=True)
class RunResult:
    command: tuple[str, ...] | list[str]
    exit_code: int
    raw_output: str

    def as_benchexec_run(self):
        from benchexec.tools.template import BaseTool2
        from benchexec.util import ProcessExitCode

        return BaseTool2.Run(
            cmdline=self.command,
            exit_code=ProcessExitCode.create(value=self.exit_code),
            output=BaseTool2.RunOutput(self.raw_output.splitlines(keepends=True)),
            termination_reason=False,  # TODO: We do not know about this
        )

    def determine_result(self, tool: "BaseTool2 | FmToolVersion") -> str:
        from benchexec.tools.template import BaseTool2

        if isinstance(tool, BaseTool2):
            return tool.determine_result(self.as_benchexec_run())

        from fm_tools.run import get_tool_info

        tool_ = get_tool_info(tool)
        return tool_.determine_result(self.as_benchexec_run())
