# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests utility module. """

# Copyright (C) 2020 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import shutil
from typing import Dict


def create_item_cache_config_and_copy_spec(
        tmp_dir: str,
        spec_dir: str,
        with_spec_types: bool = False) -> Dict[str, str]:
    """
    Creates an item cache configuration and copies a specification
    directory to the temporary tests directory.
    """
    config = {}
    cache_dir = os.path.join(tmp_dir, "cache")
    config["cache-directory"] = os.path.normpath(cache_dir)
    spec_src = os.path.join(os.path.dirname(__file__), spec_dir)
    spec_dst = os.path.join(tmp_dir, "spec")
    shutil.copytree(spec_src, spec_dst)
    config["paths"] = [os.path.normpath(spec_dst)]
    if with_spec_types:
        spec = os.path.join(os.path.dirname(__file__), "spec")
        shutil.copytree(spec, os.path.join(spec_dst, "spec"))
        config["spec-type-root-uid"] = "/spec/root"
    else:
        config["spec-type-root-uid"] = None
    return config


def get_and_clear_log(the_caplog) -> str:
    log = "\n".join(f"{rec.levelname} {rec.message}"
                    for rec in the_caplog.records)
    the_caplog.clear()
    return log
