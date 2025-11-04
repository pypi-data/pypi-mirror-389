# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

#!/bin/bash

script_dir="$(dirname "$(realpath "$0")")"

cd "$script_dir" || exit

python -m grpc_tools.protoc -I./ --python_out=./ --pyi_out=./ --grpc_python_out=./ ./fm_weck_service.proto

sed -i 's/^import fm_weck_service_pb2 as fm__weck__service__pb2/from . import fm_weck_service_pb2 as fm__weck__service__pb2/' fm_weck_service_pb2_grpc.py

reuse annotate -y 2024 -l Apache-2.0 -c "Dirk Beyer <https://www.sosy-lab.org>" --template header --skip-existing --skip-unrecognised ./fm_weck_service_pb2_grpc.py ./fm_weck_service_pb2.pyi ./fm_weck_service_pb2.py