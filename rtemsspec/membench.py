# SPDX-License-Identifier: BSD-2-Clause
"""
This module provides functions for the generation of memory benchmark
documentation.
"""

# Copyright (C) 2021, 2023 embedded brains GmbH & Co. KG
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
from typing import Any, Dict, List, NamedTuple, Tuple

from rtemsspec.items import Item, ItemCache, ItemMapper
from rtemsspec.sphinxcontent import get_reference, SphinxContent
from rtemsspec.util import run_command


class MembenchVariant(NamedTuple):
    """ Represents a static memory benchmark configuration. """
    name: str
    build_label: str


SectionsByUID = Dict[str, Dict[str, int]]

_SECTIONS = {".text": 0, ".rodata": 1, ".data": 2, ".bss": 3, ".noinit": 4}

_SECTION_KEYS = tuple(sorted(_SECTIONS.keys(), key=lambda x: _SECTIONS[x]))

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
    ".debug_line_str": None,
    ".debug_loc": None,
    ".debug_loclists": None,
    ".debug_pubnames": None,
    ".debug_ranges": None,
    ".debug_rnglists": None,
    ".debug_str": None,
    ".eh_frame": ".rodata",
    ".fini": ".text",
    ".fini_array": ".rodata",
    ".gnu.attributes": None,
    ".init": ".text",
    ".init_array": ".rodata",
    ".nocachenoload": None,
    ".noinit": ".noinit",
    ".riscv.attributes": None,
    ".robarrier": None,
    ".rodata": ".rodata",
    ".rtemsroset": ".rodata",
    ".rtemsrwset": ".data",
    ".rtemsstack": ".noinit",
    ".rwbarrier": None,
    ".sbss": ".bss",
    ".sdata": ".data",
    ".stack": None,
    ".start": ".text",
    ".text": ".text",
    ".vector": ".vector",
    ".work": None,
    ".xbarrier": None,
}

_OBJECT_SIZES = {
    "/c/void-pointer": {
        "commands": ["sizeof(void *)"],
        "uid": "/rtems/val/mem-basic"
    },
    "/rtems/barrier/info": {
        "commands": ["sizeof(_Barrier_Information)"],
        "uid": "/rtems/barrier/val/mem-wait-rel-del"
    },
    "/rtems/barrier/obj": {
        "commands": ["sizeof(Objects_Control *) + sizeof(Barrier_Control)"],
        "uid": "/rtems/barrier/val/mem-wait-rel-del"
    },
    "/rtems/message/info": {
        "commands": ["sizeof(_Message_queue_Information)"],
        "uid": "/rtems/message/val/mem-snd-rcv-del"
    },
    "/rtems/message/obj": {
        "commands":
        ["sizeof(Objects_Control *) + sizeof(Message_queue_Control)"],
        "uid": "/rtems/message/val/mem-snd-rcv-del"
    },
    "/rtems/part/info": {
        "commands": ["sizeof(_Partition_Information)"],
        "uid": "/rtems/part/val/mem-get-ret-del"
    },
    "/rtems/part/obj": {
        "commands": ["sizeof(Objects_Control *) + sizeof(Partition_Control)"],
        "uid": "/rtems/part/val/mem-get-ret-del"
    },
    "/rtems/priority/control": {
        "commands": ["sizeof(Priority_Control)"],
        "uid": "/rtems/sem/val/mem-obt-rel-del"
    },
    "/rtems/ratemon/info": {
        "commands": ["sizeof(_Rate_monotonic_Information)"],
        "uid": "/rtems/ratemon/val/mem-period-del"
    },
    "/rtems/ratemon/obj": {
        "commands":
        ["sizeof(Objects_Control *) + sizeof(Rate_monotonic_Control)"],
        "uid": "/rtems/ratemon/val/mem-period-del"
    },
    "/rtems/sem/info": {
        "commands": ["sizeof(_Semaphore_Information)"],
        "uid": "/rtems/sem/val/mem-obt-rel-del"
    },
    "/rtems/sem/obj": {
        "commands": ["sizeof(Objects_Control *) + sizeof(Semaphore_Control)"],
        "uid": "/rtems/sem/val/mem-obt-rel-del"
    },
    "/rtems/sem/obj-mrsp": {
        "commands": [
            "sizeof(Objects_Control *) + sizeof(Objects_Control) + "
            "sizeof(MRSP_Control)"
        ],
        "uid":
        "/rtems/sem/val/mem-obt-rel-del"
    },
    "/rtems/task/info": {
        "commands": ["sizeof(_RTEMS_tasks_Information)"],
        "uid": "/rtems/val/mem-basic"
    },
    "/rtems/task/obj": {
        "commands": [
            "sizeof(Objects_Control *) + sizeof(Thread_Control) + "
            "sizeof(RTEMS_API_Control) + sizeof(Thread_queue_Heads)",
            "sizeof(Objects_Control *) + sizeof(Thread_Control) + "
            "sizeof(RTEMS_API_Control)"
        ],
        "uid":
        "/rtems/val/mem-basic"
    },
    "/rtems/timer/info": {
        "commands": ["sizeof(_Timer_Information)"],
        "uid": "/rtems/timer/val/mem-after"
    },
    "/rtems/timer/obj": {
        "commands": ["sizeof(Objects_Control *) + sizeof(Timer_Control)"],
        "uid": "/rtems/timer/val/mem-after"
    },
    "/rtems/userext/info": {
        "commands": ["sizeof(_Extension_Information)"],
        "uid": "/rtems/userext/val/mem-create"
    },
    "/rtems/userext/obj": {
        "commands": ["sizeof(Objects_Control *) + sizeof(Extension_Control)"],
        "uid": "/rtems/userext/val/mem-create"
    },
    "/scheduler/control": {
        "commands": ["sizeof(Scheduler_Control)"],
        "uid": "/rtems/val/mem-basic"
    },
    "/scheduler/priority/context": {
        "commands": ["sizeof(Scheduler_priority_Context)"],
        "uid": "/rtems/val/mem-basic"
    },
    "/scheduler/priority/node": {
        "commands": ["sizeof(Scheduler_priority_Node)"],
        "uid": "/rtems/val/mem-basic"
    },
    "/scheduler/smp/edf/context": {
        "commands": [
            "sizeof(Scheduler_EDF_SMP_Context) + "
            "sizeof(Scheduler_EDF_SMP_Ready_queue)"
        ],
        "uid":
        "/rtems/val/mem-smp-1"
    },
    "/scheduler/smp/edf/node": {
        "commands": ["sizeof(Scheduler_EDF_SMP_Node)"],
        "uid": "/rtems/val/mem-smp-1"
    },
    "/scheduler/smp/edf/ready-queue": {
        "commands": ["sizeof(Scheduler_EDF_SMP_Ready_queue)"],
        "uid": "/rtems/val/mem-smp-1"
    },
    "/score/chain/control": {
        "commands": ["sizeof(Chain_Control)"],
        "uid": "/rtems/val/mem-basic"
    },
    "/score/tq/priority-queue": {
        "commands": ["sizeof(Thread_queue_Priority_queue)"],
        "uid": "/rtems/val/mem-basic"
    },
}


def _section_key(key_value: Tuple[str, Any]) -> int:
    return _SECTIONS[key_value[0]]


def _get_sections_of_item(sections_by_uid: SectionsByUID,
                          item: Item) -> Tuple[int, ...]:
    return tuple(size for _, size in sorted(
        sections_by_uid.get(item.uid, {}).items(), key=_section_key))


def gather_sections(item_cache: ItemCache, path: str, objdump: str,
                    gdb: str) -> Dict[str, Dict[str, int]]:
    """
    Gathers the object sizes for all memory benchmarks of the item cache using
    the programs of the path.
    """
    sections_by_uid: Dict[str, Dict[str, int]] = {}
    for item in item_cache.items_by_type["memory-benchmark"]:
        sections = _get_sections(item, path, objdump, gdb)
        if sections:
            sections_by_uid[item.uid] = sections
    return sections_by_uid


def gather_object_sizes(item_cache: ItemCache, path: str,
                        gdb: str) -> Dict[str, int]:
    """
    Gathers the object sizes for all memory benchmarks of the item cache using
    the programs of the path.
    """
    object_sizes: Dict[str, int] = {}
    for key, value in _OBJECT_SIZES.items():
        try:
            item = item_cache[value["uid"]]
        except KeyError:
            continue
        file = _get_path_to_test_suite_elf_file(item, path)
        for command in value["commands"]:
            cmd = [gdb, "-ex", f"p {command}", "--batch", ""]
            cmd[-1] = file
            stdout: List[str] = []
            status = run_command(cmd, stdout=stdout)
            if status == 0:
                output = " ".join(stdout)
                match = re.search(r"\$[0-9]+\s*=\s*([0-9]+)", output)
                assert match
                object_sizes[key] = int(match.group(1))
                break
    return object_sizes


def _do_gather_test_suites(items: List[Item], item: Item) -> None:
    if item.type == "memory-benchmark":
        items.append(item)
    for child in item.children("validation"):
        _do_gather_test_suites(items, child)
    for child in item.children("requirement-refinement"):
        _do_gather_test_suites(items, child)


def _gather_benchmarks(root: Item) -> List[Item]:
    """ Gather all test suite items related to the root item. """
    items: List[Item] = []
    _do_gather_test_suites(items, root)
    return items


def _get_path_to_test_suite_elf_file(item: Item, path: str) -> str:
    """ Returns the path to the ELF file of the test suite. """
    name = item["test-target"]
    return os.path.join(path, f"{name[:name.rfind('.')]}.norun.exe")


def _try_add_workspace(gdb: str, elf: str,
                       section_limits: Dict[str, Tuple[int, int]]) -> None:
    if ".noinit" in section_limits:
        return
    # Maybe an older version of RTEMS
    stdout: List[str] = []
    cmd = [gdb, "-ex", "p Configuration.work_space_size", "--batch", elf]
    status = run_command(cmd, stdout=stdout)
    if status == 0 and stdout[0].startswith("$1 = "):
        section_limits[".noinit"] = (0, int(stdout[0][5:]))


def _get_size(section_limits: Dict[str, Tuple[int, int]], key: str) -> int:
    limits = section_limits.get(key, (0, 0))
    return limits[1] - limits[0]


def _run_objdump(objdump: str, elf: str) -> List[str]:
    stdout: List[str] = []
    status = run_command([objdump, "-h", elf], stdout=stdout)
    if status != 0:
        return []
    return stdout


def _make_sections(
        section_limits: Dict[str, Tuple[int, int]]) -> Dict[str, int]:
    sections: Dict[str, int] = {}
    for key in _SECTIONS:
        sections[key] = _get_size(section_limits, key)
    sections[".noinit"] += _get_size(section_limits, ".vector")
    return sections


def _get_sections(item: Item, path_to_elf_files: str, objdump: str,
                  gdb: str) -> Dict[str, int]:
    """
    Gets the memory benchmark sections of the program associated with the item
    in the path to ELF files.
    """
    elf = _get_path_to_test_suite_elf_file(item, path_to_elf_files)
    stdout = _run_objdump(objdump, elf)
    if not stdout:
        return {}
    section_limits: Dict[str, Tuple[int, int]] = {}
    for line in stdout:
        match = _SECTION.search(line)
        if match:
            name = match.group(1)
            size = int(match.group(2), 16)
            section = _SECTION_MAP[name]
            if size != 0 and section:
                start = int(match.group(3), 16)
                end = start + size
                limits = section_limits.get(section, (2**64, 0))
                section_limits[section] = (min(limits[0],
                                               start), max(limits[1], end))
    _try_add_workspace(gdb, elf, section_limits)
    return _make_sections(section_limits)


def _make_label(item: Item) -> str:
    return f"Membench{item.ident}"


def _generate_table(content: SphinxContent, sections_by_uid: SectionsByUID,
                    items: List[Item]) -> None:
    rows: List[Tuple[str, ...]] = []
    for index, item in enumerate(items):
        sections = _get_sections_of_item(sections_by_uid, item)
        spec = (get_reference(_make_label(item), item.uid), )
        if index == 0:
            assert sections
            keys = ("Specification", ) + _SECTION_KEYS
            base = sections
            rows.append(keys)
            rows.append(spec + tuple(map(str, sections)))
        elif sections:
            rows.append(spec + tuple(f"{i - j:+}"
                                     for i, j in zip(sections, base)))
        else:
            rows.append(spec + tuple("?") * len(keys))

    pivot = items[0]
    section = f"Benchmarks Based on: {pivot.spec}"
    with content.section(section):
        content.wrap(f"""The following memory benchmarks are based on the
memory benchmark defined by
{get_reference(_make_label(pivot), pivot.spec)}.""")
        content.add_simple_table(rows)


_WARNING_NO_MEMBENCH = """.. topic:: WARNING

    There are no results available for this static memory usage benchmark.
"""


def _generate_paragraphs(content: SphinxContent,
                         sections_by_uid: SectionsByUID, mapper: ItemMapper,
                         items: List[Item]) -> None:
    for item in items:
        section = f"Benchmark: {item.spec}"
        with content.section(section, label=_make_label(item)):
            content.wrap(mapper.substitute(item["test-brief"], item))
            content.wrap(mapper.substitute(item["test-description"], item))
            sections = _get_sections_of_item(sections_by_uid, item)
            if sections:
                content.add_simple_table(
                    [_SECTION_KEYS, tuple(map(str, sections))])
            else:
                content.add(_WARNING_NO_MEMBENCH)


def _generate_tables(content: SphinxContent, sections_by_uid: SectionsByUID,
                     root: Item, table_pivots: List[str]) -> List[Item]:
    root_items = _gather_benchmarks(root)
    _generate_table(content, sections_by_uid, root_items)
    for pivot_uid in table_pivots:
        pivot = root.map(pivot_uid)
        if not pivot.enabled:
            continue
        pivot_items = _gather_benchmarks(pivot)
        _generate_table(content, sections_by_uid, pivot_items)
    return root_items


def generate_tables(content: SphinxContent, sections_by_uid: SectionsByUID,
                    root: Item, table_pivots: List[str]) -> None:
    """ Generates memory benchmark tables. """
    _generate_tables(content, sections_by_uid, root, table_pivots)


def generate_variants_table(content: SphinxContent,
                            sections_by_build_label: Dict[str,
                                                          Dict[str,
                                                               SectionsByUID]],
                            root: Item,
                            variants: List[MembenchVariant]) -> None:
    """ Generates memory benchmark variant comparison tables. """
    items = _gather_benchmarks(root)
    rows: List[Tuple[str,
                     ...]] = [("Specification", "Variant") + _SECTION_KEYS]
    for item in items:
        spec = get_reference(_make_label(item), item.uid)
        for index, variant in enumerate(variants):
            sections = _get_sections_of_item(
                sections_by_build_label[variant.build_label]["membench"], item)
            what = (spec, variant.name)
            if index == 0:
                assert sections
                base = sections
                rows.append(what + tuple(map(str, sections)))
            else:
                if sections:
                    rows.append(what + tuple(f"{i - j:+}"
                                             for i, j in zip(sections, base)))
                else:
                    rows.append(what + tuple("?") * len(base))
            spec = ""
    with content.latex_tiny("scriptsize"):
        content.add_grid_table(rows, [35, 20, 9, 9, 9, 9, 9])


def generate(content: SphinxContent, sections_by_uid: SectionsByUID,
             root: Item, table_pivots: List[str], mapper: ItemMapper) -> None:
    """
    Generates memory benchmark documentation for items dependent on the root
    item and executables in the path.
    """
    root_items = _generate_tables(content, sections_by_uid, root, table_pivots)
    _generate_paragraphs(content, sections_by_uid, mapper, root_items)
