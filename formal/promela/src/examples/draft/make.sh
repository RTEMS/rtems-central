#!/bin/bash

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (C) 2019-2021 Trinity College Dublin (www.tcd.ie)

set -e
set -x

######

HOME0="$(dirname "$(python3 -c "import os; print(os.path.realpath('$0'))")")"
cd "$HOME0"

######

pip_check_test='true'
function pip_check () {
    if [ "$pip_check_test" ] ; then
	set +e
	version=$(pip3 show "$1")
	st="$?"
	set -e
	[ "$st" = 0 ] || (echo '`'"pip3 show $1"'`'" failed: "'`'"pip3 install $1"'`' && exit "$st")

	version=$(echo "$version" | grep -m 1 Version | cut -d ' ' -f 2)
        set +x
	[ "$version" = "$2" ] || (echo "$1 version $version installed instead of $2: "'`'"pip3 install $1==$2"'`' && echo -n "Continue? (ENTER/CTRL+C): " && read)
        set -x
    fi
}

# The compilation will require the installation of these libraries:

pip_check coconut 1.4.3
pip_check mypy 0.761

coconut --target 3 library.coco --mypy --ignore-missing-imports --allow-redefinition
coconut --target 3 syntax_pml.coco --mypy --ignore-missing-imports --allow-redefinition
coconut --target 3 syntax_yaml.coco --mypy --ignore-missing-imports --allow-redefinition
coconut --target 3 syntax_ml.coco --mypy --ignore-missing-imports --allow-redefinition
coconut --target 3 refine_command.coco refine_command.py
coconut --target 3 testgen.coco --mypy --follow-imports silent --ignore-missing-imports --allow-redefinition

######

# as well as all dependencies of ( https://github.com/johnyf/promela ):

pip_check promela 0.0.2

# The above command was mainly executed to install dependencies of the package.

## git clone git@gitlab.scss.tcd.ie:tuongf/promela_yacc.git # see also deliverables/FV2-201/wip/ftuong/src_ext

######

# Additionally, we use a library to do various operations on C-style comments ( https://github.com/codeauroraforum/comment-filter ):

## git clone git@gitlab.scss.tcd.ie:tuongf/comment-filter.git # see also deliverables/FV2-201/wip/ftuong/src_ext

# We also modify $PYTHONPATH (so that the library can be used, at least while mypy is executing):

export PYTHONPATH=`pwd`/comment-filter

######

# At run-time, we will need these libraries:

pip_check parsec 3.5
## apt install spin # 6.4.6+dfsg-2

######

cd -

# Finally, the main execution proceeds as follows:

exec python3 "$HOME0/testgen.py" "$@"
