# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.util module. """

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

import os
import logging

from rtemsspec.util import copy_file, copy_files, create_argument_parser, \
    create_build_argument_parser, base64_to_hex, init_logging, load_config, \
    run_command
from rtemsspec.tests.util import get_and_clear_log


def test_copy_files(caplog, tmpdir):
    caplog.set_level(logging.INFO)
    src_dir = os.path.dirname(__file__)
    copy_files(src_dir, tmpdir, [], "uid")
    filename = "config/c/d.yml"
    dst_dir = os.path.join(tmpdir, "1")
    assert not os.path.exists(os.path.join(dst_dir, filename))
    copy_files(src_dir, dst_dir, [filename], "uid")
    assert os.path.exists(os.path.join(dst_dir, filename))
    assert get_and_clear_log(caplog) == (
        f"INFO uid: copy '{src_dir}"
        f"/config/c/d.yml' to '{dst_dir}/config/c/d.yml'")
    src_file = os.path.join(src_dir, filename)
    dst_file = os.path.join(tmpdir, "2", filename)
    assert not os.path.exists(dst_file)
    copy_file(src_file, dst_file, "uid")
    assert os.path.exists(dst_file)
    assert get_and_clear_log(
        caplog) == f"INFO uid: copy '{src_file}' to '{dst_file}'"


def test_base64_to_hex():
    assert base64_to_hex("ABCD") == "001083"


def test_load_config():
    filename = os.path.join(os.path.dirname(__file__), "config", "a.yml")
    config = load_config(filename)
    assert config["a"] == "b"
    assert config["c"] == "d"


def test_run(caplog):
    caplog.set_level(logging.DEBUG)
    status = run_command(["echo", "A"])
    assert status == 0
    assert get_and_clear_log(caplog) == """INFO run in '.': 'echo' 'A'
DEBUG A"""
    stdout = []
    status = run_command(["echo", "A"], stdout=stdout)
    assert status == 0
    assert stdout[0].strip() == "A"
    status = run_command(["sleep", "0.1"])
    assert status == 0


def test_args():
    parser = create_build_argument_parser()
    args = parser.parse_args([])
    assert args.log_level == "INFO"
    assert args.log_file is None
    assert args.only is None
    assert args.force is None
    assert not args.no_spec_verify
    init_logging(args)
    log_file = "log.txt"
    args = parser.parse_args([
        "--log-level=DEBUG", f"--log-file={log_file}", "--only", "abc",
        "--force", "def", "--no-spec-verify"
    ])
    assert args.log_level == "DEBUG"
    assert args.log_file == log_file
    assert args.only == ["abc"]
    assert args.force == ["def"]
    assert args.no_spec_verify
    init_logging(args)
