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

import logging
import os
import string

import rtemsspec.applconfig
import rtemsspec.build
from rtemsspec.items import ItemCache
import rtemsspec.util


def _run_pre_qualified_only_build(config: dict, item_cache: ItemCache) -> None:
    files = rtemsspec.build.gather_files(config, item_cache)
    source_dir = config["source-directory"]
    workspace_dir = config["workspace-directory"]
    rtemsspec.util.copy_files(source_dir, workspace_dir, files)
    with open(os.path.join(workspace_dir, "config.ini"), "w",
              encoding="utf-8") as config_ini:
        content = string.Template(config["config-ini"]).substitute(config)
        config_ini.write(content)
    specs = os.path.relpath(os.path.join(source_dir, "spec"), workspace_dir)
    rtemsspec.util.run_command([
        "./waf", "configure", "--rtems-specs", specs, "--rtems-top-group",
        "/build/grp"
    ], workspace_dir)
    rtemsspec.util.run_command(["./waf"], workspace_dir)


def _run_pre_qualified_doxygen(config: dict) -> None:
    workspace_dir = config["workspace-directory"]
    with open(config["doxyfile-template"], "r",
              encoding="utf-8") as doxyfile_template:

        class Template(string.Template):
            """ Template class with custom delimiter. """
            delimiter = "%"

        doxyfile_vars = {}
        doxyfile_vars["project_name"] = "RTEMS"
        doxyfile_vars["output_directory"] = "doc"
        content = Template(doxyfile_template.read()).substitute(doxyfile_vars)
        with open(os.path.join(workspace_dir, "Doxyfile"),
                  "w",
                  encoding="utf-8") as doxyfile:
            doxyfile.write(content)
    rtemsspec.util.run_command(["doxygen"], workspace_dir)


def main() -> None:
    """ Generates glossaries of terms according to the configuration. """
    logging.basicConfig(level="DEBUG")
    config = rtemsspec.util.load_config("config.yml")
    item_cache = ItemCache(config["spec"])
    _run_pre_qualified_only_build(config["build"], item_cache)
    _run_pre_qualified_doxygen(config["build"])


if __name__ == "__main__":
    main()
