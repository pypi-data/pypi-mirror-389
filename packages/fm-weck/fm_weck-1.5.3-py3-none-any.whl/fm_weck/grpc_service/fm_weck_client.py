# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Tuple

import grpc

from .proto.fm_weck_service_pb2 import (
    CancelRunRequest,
    ExpertRunRequest,
    FileQuery,
    Property,
    RunID,
    RunRequest,
    ToolType,
    WaitParameters,
)
from .proto.fm_weck_service_pb2_grpc import FmWeckRemoteStub


def start_run(stub, tool, prop, c_program):
    with open(tool[0], "rb") as tool_file, open(prop, "rb") as property_file:
        tool_bin = tool_file.read()
        prop_bin = property_file.read()

    tool_data: ToolType = ToolType(tool_version=tool[1], tool_file={"name": "fm-tool.yml", "file": tool_bin})
    prop_data: Property = Property(property_file={"name": "property.prp", "file": prop_bin})
    run_info = RunRequest(tool=tool_data, property=prop_data, c_program=c_program, data_model="ILP32")
    run_id = stub.startRun(run_info)

    return run_id


def start_expert_run(stub, tool, command):
    with open(tool[0], "rb") as tool_file:
        tool_bin = tool_file.read()

    tool_data: ToolType = ToolType(tool_version=tool[1], tool_file={"name": "fm-tool.yml", "file": tool_bin})
    expert_run_info = ExpertRunRequest(tool=tool_data, command=command)
    run_id = stub.startExpertRun(expert_run_info)

    return run_id


def cancel_run(stub, run_id, confirmed=True):
    if confirmed:
        stub.cancelRun(CancelRunRequest(run_id=run_id, timeout=5, cleanup_on_success=True))


def wait_on_run(stub, run_id, timelimit):
    response = stub.waitOnRun(WaitParameters(run_id=run_id, timeout=timelimit))

    if not response:
        print("Server timed out or returned no files.")
        exit(1)

    if response.error:
        print(response.error, ": Error occurred on the server side.")
        exit(response.error)
    elif response.timeout:
        print("Run timed out.")
        exit(1)

    if not response.run_result.success:
        print("There was an error running the tool.")
        exit(1)

    print()
    print(response.run_result.output)
    if response.run_result.filenames:
        print("The run produced the following files:")
        print(response.run_result.filenames)
        print(
            "\nFiles can be obtained by running:\nfm-weck query-files [-h] --host HOST [--timelimit TIMELIMIT]"
            "[--output-path OUTPUT_PATH] RUN-ID [files ...]"
        )
    else:
        print("The run produced no files.")
    print()

    return response


def query_files(host: str, run_id: str, file_names: str, timelimit: int, output_path: Path):
    print("Establishing a connection to the server ...")
    with grpc.insecure_channel(host) as channel:
        stub = FmWeckRemoteStub(channel)

        run_id = RunID(run_id=run_id)
        try:
            wait_on_run(stub, run_id, timelimit)
        except KeyboardInterrupt:
            cancel_run(stub, run_id)

        request = FileQuery(filenames=file_names, run_id=run_id)
        responses = stub.queryFiles(request)

        output_path = output_path / "fm_weck_server_files" / run_id.run_id
        output_path.mkdir(exist_ok=True, parents=True)
        for response in responses:
            with open(output_path / response.name, "wb") as output_file:
                output_file.write(response.file)


def client_run(tool: Tuple[Path, str], host: str, prop: Path, files: list[Path], timelimit: int):
    with open(files[0], "rb") as c_file:
        c_program = c_file.read()

    print("Establishing a connection to the server ...")
    with grpc.insecure_channel(host) as channel:
        stub = FmWeckRemoteStub(channel)

        run_id = start_run(stub, tool, prop, c_program)
        print("Run ID: ", run_id.run_id)
        try:
            wait_on_run(stub, run_id, timelimit)
        except KeyboardInterrupt:
            cancel_run(stub, run_id)


def client_expert_run(tool: Tuple[Path, str], host: str, command: list[str], timelimit: int):
    print("Establishing a connection to the server ...")
    with grpc.insecure_channel(host) as channel:
        stub = FmWeckRemoteStub(channel)

        run_id = start_expert_run(stub, tool, command)
        print("Run ID: ", run_id.run_id)
        try:
            wait_on_run(stub, run_id, timelimit)
        except KeyboardInterrupt:
            cancel_run(stub, run_id)


def client_get_run(host: str, run_id: str, timelimit: int):
    print("Establishing a connection to the server ...")
    with grpc.insecure_channel(host) as channel:
        stub = FmWeckRemoteStub(channel)

        run_id = RunID(run_id=run_id)
        try:
            wait_on_run(stub, run_id, timelimit)
        except KeyboardInterrupt:
            cancel_run(stub, run_id)
