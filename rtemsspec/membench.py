# SPDX-License-Identifier: BSD-2-Clause
"""
This module provides functions for the generation of memory benchmark
documentation.
"""

# Copyright (C) 2021 embedded brains GmbH (http://www.embedded-brains.de)
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
import re
from typing import Dict, List, Tuple

from rtemsspec.items import Item, ItemMapper
from rtemsspec.sphinxcontent import get_label, get_reference, SphinxContent
from rtemsspec.util import run_command

_SECTION = re.compile(
    r"^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+[0-9a-fA-F]+"
    r"\s+[0-9a-fA-F]+\s+.*$")

_SECTION_MAP = {
    ".ARM.attributes": None,
    ".ARM.exidx": ".rodata",
    ".bss": ".bss",
    ".comment": None,
    ".data": ".data",
    ".debug_abbrev": None,
    ".debug_aranges": None,
    ".debug_frame": None,
    ".debug_info": None,
    ".debug_line": None,
    ".debug_loc": None,
    ".debug_ranges": None,
    ".debug_str": None,
    ".eh_frame": ".rodata",
    ".fini": ".text",
    ".fini_array": ".rodata",
    ".gnu.attributes": None,
    ".init": ".text",
    ".init_array": ".rodata",
    ".nocachenoload": None,
    ".robarrier": None,
    ".rodata": ".rodata",
    ".rtemsroset": ".rodata",
    ".rtemsrwset": ".data",
    ".rtemsstack": ".rtemsstack",
    ".rwbarrier": None,
    ".stack": None,
    ".start": ".text",
    ".text": ".text",
    ".vector": ".vector",
    ".work": None,
    ".xbarrier": None,
}


def _do_gather_test_suites(items: List[Item], item: Item) -> None:
    if item.type == "test-suite":
        items.append(item)
    for child in item.children("validation"):
        _do_gather_test_suites(items, child)
    for child in item.children("requirement-refinement"):
        _do_gather_test_suites(items, child)


def gather_test_suites(root: Item) -> List[Item]:
    """ Gather all test suite items related to the root item. """
    items = []  # type: List[Item]
    _do_gather_test_suites(items, root)
    return items


def get_path_to_test_suite_elf_file(item: Item, path: str) -> str:
    """ Returns the path to the ELF file of the test suite. """
    name = os.path.basename(item.uid).replace("mem-", "")
    module = os.path.basename(os.path.dirname(os.path.dirname(item.uid)))
    return f"{path}/mem-{module}-{name}.norun.exe"


def _get_sections(item: Item, path: str) -> Dict[str, Tuple[int, int]]:
    elf = get_path_to_test_suite_elf_file(item, path)
    stdout = []  # type: List[str]
    status = run_command(["objdump", "-h", elf], stdout=stdout)
    assert status == 0
    sections = {}  # type: Dict[str, Tuple[int, int]]
    for line in stdout:
        match = _SECTION.search(line)
        if match:
            name = match.group(1)
            size = int(match.group(2), 16)
            section = _SECTION_MAP[name]
            if size != 0 and section:
                start = int(match.group(3), 16)
                end = start + size
                info = sections.get(section, (2**64, 0))
                sections[section] = (min(info[0], start), max(info[1], end))
    return sections


def _get_label(item: Item) -> str:
    return get_label(f"MemBenchmark {item.uid[1:]}")


def _generate_table(content: SphinxContent, items: List[Item],
                    path: str) -> None:
    rows = []  # type: List[Tuple[str, ...]]
    for index, item in enumerate(items):
        sections = _get_sections(item, path)
        name = (get_reference(_get_label(item), item.uid), )
        if index == 0:
            keys = ("spec", ) + tuple(sections.keys())
            base = {key: info[1] - info[0] for key, info in sections.items()}
            rows.append(keys)
            rows.append(name + tuple(map(str, base.values())))
        else:
            rows.append(name + tuple(f"{info[1] - info[0] - base[key]:+}"
                                     for key, info in sections.items()))

    pivot = items[0]
    section = f"Benchmarks Based on: {pivot.spec}"
    with content.section(section):
        content.wrap(f"""The following memory benchmarks are based on the
memory benchmark defined by {get_reference(_get_label(pivot), pivot.spec)}.""")
        content.add_simple_table(rows)


def _generate_paragraphs(content: SphinxContent, items: List[Item],
                         mapper: ItemMapper) -> None:
    for item in items:
        section = f"Benchmark: {item.spec}"
        with content.section(section, label=_get_label(item)):
            content.wrap(mapper.substitute(item["test-brief"], item))
            content.wrap(mapper.substitute(item["test-description"], item))


def generate(content: SphinxContent, root: Item, mapper: ItemMapper,
             table_pivots: List[str], path: str) -> None:
    """
    Generates memory benchmark documentation for items dependent on the root
    item and executables in the path.
    """
    for pivot in table_pivots:
        items = gather_test_suites(root.map(pivot))
        _generate_table(content, items, path)
    items = gather_test_suites(root)
    _generate_paragraphs(content, items, mapper)
