#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
""" This script generates glossaries of terms from the specification. """

# Copyright (C) 2019, 2020 embedded brains GmbH (http://www.embedded-brains.de)
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
import string
import subprocess
from typing import List

import rtemsqual.applconfig
import rtemsqual.build
from rtemsqual.items import ItemCache
import rtemsqual.glossary
import rtemsqual.util


def _run_command(args: List[str], cwd: str) -> int:
    task = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            cwd=cwd)
    while True:
        line = task.stdout.readline()
        if line:
            print(line.decode("utf-8").strip())
        elif task.poll() is not None:
            break
    return task.wait()


def _run_pre_qualified_only_build(config: dict, item_cache: ItemCache) -> None:
    files = rtemsqual.build.gather_files(config, item_cache)
    source_dir = config["source-directory"]
    workspace_dir = config["workspace-directory"]
    rtemsqual.util.copy_files(source_dir, workspace_dir, files)
    with open(os.path.join(workspace_dir, "config.ini"), "w") as config_ini:
        content = string.Template(config["config-ini"]).substitute(config)
        config_ini.write(content)
    specs = os.path.relpath(os.path.join(source_dir, "spec"), workspace_dir)
    _run_command([
        "./waf", "configure", "--rtems-specs", specs, "--rtems-top-group",
        "/build/grp"
    ], workspace_dir)
    _run_command(["./waf"], workspace_dir)


def main() -> None:
    """ Generates glossaries of terms according to the configuration. """
    config = rtemsqual.util.load_config("config.yml")
    item_cache = ItemCache(config["spec"])
    rtemsqual.glossary.generate(config["glossary"], item_cache)
    rtemsqual.applconfig.generate(config["appl-config"], item_cache)
    _run_pre_qualified_only_build(config["build"], item_cache)


if __name__ == "__main__":
    main()
