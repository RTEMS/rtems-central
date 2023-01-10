#

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (C) 2019-2021 Trinity College Dublin (www.tcd.ie)

if [ ! -f env/bin/activate ]
then
    make env
fi

source env/bin/activate

make py
