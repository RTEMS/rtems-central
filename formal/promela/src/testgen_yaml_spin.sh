#!/bin/bash

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (C) 2019-2021 Trinity College Dublin (www.tcd.ie)

set -x
set -e
set -o pipefail

# resolve home directory of the project
HOME0="$(dirname "$(python3 -c "import os; print(os.path.realpath('$0'))")")"

# load virtual environment
cd "$HOME0"
source src.sh
cd -

# exec in the virtual environment
exec python3 "$HOME0/testgen_yaml.py" "$HOME0/../examples/model_checker/spin.pml" "$@"
