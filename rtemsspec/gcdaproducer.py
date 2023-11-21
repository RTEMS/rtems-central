# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a build step to produce gcda files. """

# Copyright (C) 2022 embedded brains GmbH & Co. KG
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

import base64
import glob
import json
import logging
import os
import shutil
from subprocess import run as subprocess_run

from rtemsspec.directorystate import DirectoryState
from rtemsspec.packagebuild import BuildItem


class GCDAProducer(BuildItem):
    """ Runs the gcov-tool to produce gcda files from a test log. """

    def run(self):
        build = self.input("build")
        assert isinstance(build, DirectoryState)

        destination = self.output("destination")
        assert isinstance(destination, DirectoryState)

        logging.info("%s: copy *.gcno files from '%s' to '%s'", self.uid,
                     build.directory, destination.directory)
        for file in build.files():
            assert not file.endswith(".gcda")
            if file.endswith(".gcno"):
                file_dest = file.replace(build.directory,
                                         destination.directory)
                os.makedirs(os.path.dirname(file_dest), exist_ok=True)
                shutil.copy2(file, file_dest)

        gcda_pattern = f"{build.directory}/**/*.gcda"
        for file in glob.glob(gcda_pattern, recursive=True):
            logging.warning(
                "%s: remove unexpected *.gcda file in build directory: '%s'",
                self.uid, file)
            os.remove(file)

        log = self.input("log")
        assert isinstance(log, DirectoryState)

        gcov_tool = self["gcov-tool"]
        cwd = self["working-directory"]

        with open(log.file, "r", encoding="utf-8") as src:
            data = json.load(src)

        for report in data["reports"]:
            if "line-end-of-test" not in report["info"]:
                # Do not use coverage data of failed tests
                continue
            begin = report.get("line-gcov-info-base64-begin", -1)
            end = report.get("line-gcov-info-base64-end", -1)
            if begin >= 0 and end >= 0:
                logging.debug("%s: process: %s", self.uid,
                              report["executable"])
                gcov_info = base64.b64decode("".join(report["output"][begin +
                                                                      1:end]))
                subprocess_run([gcov_tool, "merge-stream"],
                               check=True,
                               cwd=cwd,
                               input=gcov_info)

        logging.info("%s: move *.gcda files from '%s' to '%s'", self.uid,
                     build.directory, destination.directory)
        for file in glob.glob(gcda_pattern, recursive=True):
            file_dest = file.replace(build.directory, destination.directory)
            os.replace(file, file_dest)
