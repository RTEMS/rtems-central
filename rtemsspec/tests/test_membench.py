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

from rtemsspec.membench import gather_object_sizes, gather_sections, \
    generate, generate_tables, generate_variants_table, MembenchVariant
from rtemsspec.items import ItemCache, ItemMapper
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def run_command(args, cwd=None, stdout=None):
    if args[0] == "object-sizes":
        if "Thread" in args[2]:
            stdout.append("$1 = 42")
            return 0
        return 1
    if args[0] == "gdb" and "t3" in args[-1]:
        stdout.append("$1 = 133")
        return 0
    if "t2" in args[-1]:
        return 1
    if "t1" in args[-1] and "path-2" in args[-1]:
        return 1
    stdout.extend([
        "  0 .start        00000708  00100000  00100000  00010000  2**2",
        "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
        "  2 .text         000090bc  00100740  00100740  00010740  2**6",
        "                  CONTENTS, ALLOC, LOAD, READONLY, CODE",
        " 22 .debug_aranges 000011d8  00000000  00000000  000202e8  2**3"
    ])
    if "t1" in args[-1]:
        stdout.extend([
            "  3 .noinit       00001900  400809e0  400809e0  000909e0  2**3",
            "                  ALLOC"
        ])
    return 0


def test_membench(tmpdir, monkeypatch):
    monkeypatch.setattr("rtemsspec.membench.run_command", run_command)
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-membench", with_spec_types=True)
    item_cache = ItemCache(item_cache_config)
    object_sizes = gather_object_sizes(item_cache, "path", "object-sizes")
    assert len(object_sizes) == 2
    assert object_sizes["/rtems/task/obj"] == 42
    sections_by_uid = gather_sections(item_cache, "path", "objdump", "gdb")
    sections_by_uid_2 = gather_sections(item_cache, "path-2", "objdump", "gdb")
    root = item_cache["/r0"]
    content = SphinxContent()
    generate(content, sections_by_uid, root, ["r0", "r4"], ItemMapper(root))
    assert str(content) == """.. _BenchmarksBasedOnSpecT0:

Benchmarks Based on: spec:/t0
=============================

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/t0 <MembenchT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. table::
    :class: longtable

    ======================= ===== ======= ===== ==== =======
    Specification           .text .rodata .data .bss .noinit
    ======================= ===== ======= ===== ==== =======
    :ref:`/t0 <MembenchT0>` 38908 0       0     0    0
    :ref:`/t1 <MembenchT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <MembenchT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <MembenchT3>` +0    +0      +0    +0   +133
    ======================= ===== ======= ===== ==== =======

.. _BenchmarksBasedOnSpecT0:

Benchmarks Based on: spec:/t0
=============================

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/t0 <MembenchT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. table::
    :class: longtable

    ======================= ===== ======= ===== ==== =======
    Specification           .text .rodata .data .bss .noinit
    ======================= ===== ======= ===== ==== =======
    :ref:`/t0 <MembenchT0>` 38908 0       0     0    0
    :ref:`/t1 <MembenchT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <MembenchT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <MembenchT3>` +0    +0      +0    +0   +133
    ======================= ===== ======= ===== ==== =======

.. _MembenchT0:

Benchmark: spec:/t0
===================

The Blue Green brief description.

The Blue Green description.

.. table::
    :class: longtable

    ===== ======= ===== ==== =======
    .text .rodata .data .bss .noinit
    ===== ======= ===== ==== =======
    38908 0       0     0    0
    ===== ======= ===== ==== =======

.. _MembenchT1:

Benchmark: spec:/t1
===================

The Blue Green brief description.

The Blue Green description.

.. table::
    :class: longtable

    ===== ======= ===== ==== =======
    .text .rodata .data .bss .noinit
    ===== ======= ===== ==== =======
    38908 0       0     0    6400
    ===== ======= ===== ==== =======

.. _MembenchT2:

Benchmark: spec:/t2
===================

The Blue Green brief description.

The Blue Green description.

.. topic:: WARNING

    There are no results available for this static memory usage benchmark.

.. _MembenchT3:

Benchmark: spec:/t3
===================

The Blue Green brief description.

The Blue Green description.

.. table::
    :class: longtable

    ===== ======= ===== ==== =======
    .text .rodata .data .bss .noinit
    ===== ======= ===== ==== =======
    38908 0       0     0    133
    ===== ======= ===== ==== =======
"""
    content = SphinxContent()
    generate_tables(content, sections_by_uid, root, ["r0", "r4"])
    assert str(content) == """.. _BenchmarksBasedOnSpecT0:

Benchmarks Based on: spec:/t0
=============================

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/t0 <MembenchT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. table::
    :class: longtable

    ======================= ===== ======= ===== ==== =======
    Specification           .text .rodata .data .bss .noinit
    ======================= ===== ======= ===== ==== =======
    :ref:`/t0 <MembenchT0>` 38908 0       0     0    0
    :ref:`/t1 <MembenchT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <MembenchT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <MembenchT3>` +0    +0      +0    +0   +133
    ======================= ===== ======= ===== ==== =======

.. _BenchmarksBasedOnSpecT0:

Benchmarks Based on: spec:/t0
=============================

The following static memory benchmarks are based on the
reference memory benchmark specified by
:ref:`spec:/t0 <MembenchT0>`.
The numbers of the first row represent the section sizes of the reference
memory benchmark program in bytes.  The numbers in the following rows indicate
the change in bytes of the section sizes with respect to the reference memory
benchmark program of the first row.  A ``+`` indicates a size increase and a
``-`` indicates a size decrease.  This hints how the static memory usage
changes when the feature set changes with respect to the reference memory
benchmark.

.. table::
    :class: longtable

    ======================= ===== ======= ===== ==== =======
    Specification           .text .rodata .data .bss .noinit
    ======================= ===== ======= ===== ==== =======
    :ref:`/t0 <MembenchT0>` 38908 0       0     0    0
    :ref:`/t1 <MembenchT1>` +0    +0      +0    +0   +6400
    :ref:`/t2 <MembenchT2>` ?     ?       ?     ?    ?
    :ref:`/t3 <MembenchT3>` +0    +0      +0    +0   +133
    ======================= ===== ======= ===== ==== =======
"""
    content = SphinxContent()
    root_2 = item_cache["/r1"]
    generate_variants_table(
        content, {
            "bla": {
                "membench": sections_by_uid
            },
            "blb": {
                "membench": sections_by_uid_2
            }
        }, root_2, [MembenchVariant("a", "bla"),
                    MembenchVariant("b", "blb")])
    assert str(content) == """.. raw:: latex

    \\begin{scriptsize}

.. table::
    :class: longtable
    :widths: 35,20,9,9,9,9,9

    +-------------------------+---------+-------+---------+-------+------+---------+
    | Specification           | Variant | .text | .rodata | .data | .bss | .noinit |
    +=========================+=========+=======+=========+=======+======+=========+
    | :ref:`/t0 <MembenchT0>` | a       | 38908 | 0       | 0     | 0    | 0       |
    +                         +---------+-------+---------+-------+------+---------+
    |                         | b       | +0    | +0      | +0    | +0   | +0      |
    +-------------------------+---------+-------+---------+-------+------+---------+
    | :ref:`/t1 <MembenchT1>` | a       | 38908 | 0       | 0     | 0    | 6400    |
    +                         +---------+-------+---------+-------+------+---------+
    |                         | b       | ?     | ?       | ?     | ?    | ?       |
    +-------------------------+---------+-------+---------+-------+------+---------+

.. raw:: latex

    \\end{scriptsize}
"""
