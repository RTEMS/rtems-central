# SPDX-License-Identifier: BSD-2-Clause
""" This module provides utility functions. """

# Copyright (C) 2020, 2021 embedded brains GmbH (http://www.embedded-brains.de)
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
import shutil
import subprocess
from typing import Any, List, Optional
import yaml


def copy_files(src_dir: str, dst_dir: str, files: List[str]) -> None:
    """
    Copies a list of files in the source directory to the destination
    directory preserving the directory of the files relative to the source
    directory.
    """
    for a_file in files:
        src = os.path.join(src_dir, a_file)
        dst = os.path.join(dst_dir, a_file)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def load_config(config_filename: str) -> Any:
    """ Loads the configuration file with recursive includes. """

    class IncludeLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
        """ YAML loader customization to process custom include tags. """
        _filenames = [config_filename]

        def include(self, node):
            """ Processes the custom include tag. """
            container = IncludeLoader._filenames[0]
            dirname = os.path.dirname(container)
            filename = os.path.join(dirname, self.construct_scalar(node))
            IncludeLoader._filenames.insert(0, filename)
            with open(filename, "r", encoding="utf-8") as included_file:
                data = yaml.load(included_file, IncludeLoader)
            IncludeLoader._filenames.pop()
            return data

    IncludeLoader.add_constructor("!include", IncludeLoader.include)
    with open(config_filename, "r", encoding="utf-8") as config_file:
        return yaml.load(config_file.read(), Loader=IncludeLoader)


def run_command(args: List[str],
                cwd: str = ".",
                stdout: Optional[List[str]] = None,
                env=None) -> int:
    """
    Runs the command in a subprocess in the working directory and environment.

    Optionally, the standard output of the subprocess is returned.  Returns the
    exit status of the subprocess.
    """
    logging.info("run in '%s': %s", cwd, " ".join(f"'{arg}'" for arg in args))
    with subprocess.Popen(args,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          cwd=cwd,
                          env=env) as task:
        assert task.stdout is not None
        while True:
            raw_line = task.stdout.readline()
            if raw_line:
                line = raw_line.decode("utf-8", "ignore").rstrip()
                if stdout is None:
                    logging.debug("%s", line)
                else:
                    stdout.append(line)
            elif task.poll() is not None:
                break
        return task.wait()
