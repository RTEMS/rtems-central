# SPDX-License-Identifier: BSD-2-Clause
""" This module provides utility functions. """

# Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG
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

import argparse
import base64
import binascii
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, List, Optional, Union
import yaml


def base64_to_hex(data: str) -> str:
    """ Converts the data from base64 to hex. """
    binary = base64.urlsafe_b64decode(data)
    return binascii.hexlify(binary).decode('ascii')


def copy_file(src_file: str, dst_file: str, log_context: str) -> None:
    """ Copies the source file to the destination file. """
    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    logging.info("%s: copy '%s' to '%s'", log_context, src_file, dst_file)
    shutil.copy2(src_file, dst_file)


def copy_files(src_dir: str, dst_dir: str, files: List[str],
               log_context: str) -> None:
    """
    Copies a list of files in the source directory to the destination
    directory preserving the directory of the files relative to the source
    directory.
    """
    for a_file in files:
        src_file = os.path.join(src_dir, a_file)
        dst_file = os.path.join(dst_dir, a_file)
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        logging.info("%s: copy '%s' to '%s'", log_context, src_file, dst_file)
        shutil.copy2(src_file, dst_file)


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
                cwd: Union[str, Path] = ".",
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


def create_argument_parser(
        default_log_level: str = "INFO") -> argparse.ArgumentParser:
    """ Creates an argument parser with default logging options. """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log-level',
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        default=default_log_level,
        help="log level")
    parser.add_argument('--log-file',
                        type=str,
                        default=None,
                        help="log to this file")
    return parser


def init_logging(args: argparse.Namespace) -> None:
    """ Initializes the logging module. """
    handlers: List[Any] = [logging.StreamHandler()]
    if args.log_file is not None:
        handlers.append(logging.FileHandler(args.log_file, mode="a"))
    logging.basicConfig(level=args.log_level,
                        datefmt="%Y-%m-%dT%H:%M:%S",
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        handlers=handlers)
