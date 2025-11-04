# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ErrorCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EC_RUN_NOT_TERMINATED: _ClassVar[ErrorCode]
    EC_RUN_NOT_FOUND: _ClassVar[ErrorCode]
    EC_RUN_CANCELLED: _ClassVar[ErrorCode]
    EC_RUN_FAILED: _ClassVar[ErrorCode]
    EC_UNKNOWN_ERROR: _ClassVar[ErrorCode]
EC_RUN_NOT_TERMINATED: ErrorCode
EC_RUN_NOT_FOUND: ErrorCode
EC_RUN_CANCELLED: ErrorCode
EC_RUN_FAILED: ErrorCode
EC_UNKNOWN_ERROR: ErrorCode

class ToolType(_message.Message):
    __slots__ = ("tool_version", "tool_file", "tool_id")
    TOOL_VERSION_FIELD_NUMBER: _ClassVar[int]
    TOOL_FILE_FIELD_NUMBER: _ClassVar[int]
    TOOL_ID_FIELD_NUMBER: _ClassVar[int]
    tool_version: str
    tool_file: File
    tool_id: str
    def __init__(self, tool_version: _Optional[str] = ..., tool_file: _Optional[_Union[File, _Mapping]] = ..., tool_id: _Optional[str] = ...) -> None: ...

class Property(_message.Message):
    __slots__ = ("property_id", "property_file")
    PROPERTY_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTY_FILE_FIELD_NUMBER: _ClassVar[int]
    property_id: str
    property_file: File
    def __init__(self, property_id: _Optional[str] = ..., property_file: _Optional[_Union[File, _Mapping]] = ...) -> None: ...

class RunRequest(_message.Message):
    __slots__ = ("tool", "property", "c_program", "data_model")
    TOOL_FIELD_NUMBER: _ClassVar[int]
    PROPERTY_FIELD_NUMBER: _ClassVar[int]
    C_PROGRAM_FIELD_NUMBER: _ClassVar[int]
    DATA_MODEL_FIELD_NUMBER: _ClassVar[int]
    tool: ToolType
    property: Property
    c_program: bytes
    data_model: str
    def __init__(self, tool: _Optional[_Union[ToolType, _Mapping]] = ..., property: _Optional[_Union[Property, _Mapping]] = ..., c_program: _Optional[bytes] = ..., data_model: _Optional[str] = ...) -> None: ...

class ExpertRunRequest(_message.Message):
    __slots__ = ("tool", "command")
    TOOL_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    tool: ToolType
    command: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tool: _Optional[_Union[ToolType, _Mapping]] = ..., command: _Optional[_Iterable[str]] = ...) -> None: ...

class RunResult(_message.Message):
    __slots__ = ("run_id", "success", "output", "filenames")
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    FILENAMES_FIELD_NUMBER: _ClassVar[int]
    run_id: RunID
    success: bool
    output: str
    filenames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, run_id: _Optional[_Union[RunID, _Mapping]] = ..., success: bool = ..., output: _Optional[str] = ..., filenames: _Optional[_Iterable[str]] = ...) -> None: ...

class WaitRunResult(_message.Message):
    __slots__ = ("timeout", "error", "run_result")
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RUN_RESULT_FIELD_NUMBER: _ClassVar[int]
    timeout: bool
    error: ErrorCode
    run_result: RunResult
    def __init__(self, timeout: bool = ..., error: _Optional[_Union[ErrorCode, str]] = ..., run_result: _Optional[_Union[RunResult, _Mapping]] = ...) -> None: ...

class CancelRunRequest(_message.Message):
    __slots__ = ("run_id", "timeout", "cleanup_on_success")
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    CLEANUP_ON_SUCCESS_FIELD_NUMBER: _ClassVar[int]
    run_id: RunID
    timeout: int
    cleanup_on_success: bool
    def __init__(self, run_id: _Optional[_Union[RunID, _Mapping]] = ..., timeout: _Optional[int] = ..., cleanup_on_success: bool = ...) -> None: ...

class CancelRunResult(_message.Message):
    __slots__ = ("timeout", "error", "run_result")
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    RUN_RESULT_FIELD_NUMBER: _ClassVar[int]
    timeout: bool
    error: ErrorCode
    run_result: RunResult
    def __init__(self, timeout: bool = ..., error: _Optional[_Union[ErrorCode, str]] = ..., run_result: _Optional[_Union[RunResult, _Mapping]] = ...) -> None: ...

class CleanUpResponse(_message.Message):
    __slots__ = ("success", "error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error: ErrorCode
    def __init__(self, success: bool = ..., error: _Optional[_Union[ErrorCode, str]] = ...) -> None: ...

class RunID(_message.Message):
    __slots__ = ("run_id",)
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    run_id: str
    def __init__(self, run_id: _Optional[str] = ...) -> None: ...

class WaitParameters(_message.Message):
    __slots__ = ("timeout", "run_id")
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    timeout: int
    run_id: RunID
    def __init__(self, timeout: _Optional[int] = ..., run_id: _Optional[_Union[RunID, _Mapping]] = ...) -> None: ...

class FileQuery(_message.Message):
    __slots__ = ("run_id", "filenames", "name_patterns")
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    FILENAMES_FIELD_NUMBER: _ClassVar[int]
    NAME_PATTERNS_FIELD_NUMBER: _ClassVar[int]
    run_id: RunID
    filenames: _containers.RepeatedScalarFieldContainer[str]
    name_patterns: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, run_id: _Optional[_Union[RunID, _Mapping]] = ..., filenames: _Optional[_Iterable[str]] = ..., name_patterns: _Optional[_Iterable[str]] = ...) -> None: ...

class File(_message.Message):
    __slots__ = ("name", "file")
    NAME_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    name: str
    file: bytes
    def __init__(self, name: _Optional[str] = ..., file: _Optional[bytes] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
