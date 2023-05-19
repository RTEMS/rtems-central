# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.membench module. """

# Copyright (C) 2021 embedded brains GmbH & Co. KG
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

from rtemsspec.membench import generate
from rtemsspec.items import ItemCache, ItemMapper
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def run_command(args, cwd=None, stdout=None):
    stdout.extend([
        "  0 .start        00000708  00100000  00100000  00010000  2**2",
        "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
        "  2 .text         000090bc  00100740  00100740  00010740  2**6",
        "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
        " 22 .debug_aranges 000011d8  00000000  00000000  000202e8  2**3"
    ])
    return 0


def test_membench(tmpdir, monkeypatch):
    monkeypatch.setattr("rtemsspec.membench.run_command", run_command)
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-membench", with_spec_types=True)
    item_cache = ItemCache(item_cache_config)
    root = item_cache["/r0"]
    content = SphinxContent()
    generate(content, root, ItemMapper(root), ["/r0"], "path")
    assert str(content) == """.. _BenchmarksBasedOnSpecT0:

Benchmarks Based on: spec:/t0
=============================

The following memory benchmarks are based on the memory benchmark defined by
:ref:`spec:/t0 <MemBenchmarkT0>`.

.. table::
    :class: longtable

    =========================== =====
    spec                        .text
    =========================== =====
    :ref:`/t0 <MemBenchmarkT0>` 38908
    :ref:`/t1 <MemBenchmarkT1>` +0
    =========================== =====

.. _MemBenchmarkT0:

Benchmark: spec:/t0
===================

The Blue Green brief description.

The Blue Green description.

.. _MemBenchmarkT1:

Benchmark: spec:/t1
===================

The Blue Green brief description.

The Blue Green description.
"""
