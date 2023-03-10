# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.util module. """

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

import os
import logging

from rtemsspec.util import copy_files, load_config, run_command
from rtemsspec.tests.util import get_and_clear_log


def test_copy_files(tmpdir):
    src_dir = os.path.dirname(__file__)
    copy_files(src_dir, tmpdir, [])
    filename = "config/c/d.yml"
    assert not os.path.exists(os.path.join(tmpdir, filename))
    copy_files(src_dir, tmpdir, [filename])
    assert os.path.exists(os.path.join(tmpdir, filename))


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
