# SPDX-License-Identifier: BSD-2-Clause
"""
This module provides a build step to collect memory usage benchmarks and object
sizes.
"""

# Copyright (C) 2023 embedded brains GmbH & Co. KG
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
from typing import Any, Dict

from rtemsspec.directorystate import DirectoryState
from rtemsspec.items import Item, ItemGetValueContext
from rtemsspec.packagebuild import BuildItem, PackageBuildDirector
from rtemsspec.membench import gather_sections, gather_object_sizes


class MembenchCollector(BuildItem):
    """ Collects memory usage benchmarks and object sizes. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._arch = ""
        self.mapper.add_get_value(f"{self.item.type}:/arch", self._get_arch)

    def _get_arch(self, _ctx: ItemGetValueContext) -> str:
        return self._arch

    def run(self) -> None:
        # Get the memory benchmark results for each build directory
        item_cache = self.item.cache
        results: Dict[str, Dict[str, Any]] = {}
        for link in self.input_links("membench-build"):
            self._arch = self.substitute(link["arch"], link.item)
            path = self.substitute(link["path"], link.item)
            build_label = self.substitute(link["build-label"], link.item)
            logging.info("%s: get memory benchmarks for %s from: %s", self.uid,
                         build_label, path)
            objdump = self["objdump"]
            gdb = self["gdb"]
            assert build_label not in results
            results[build_label] = {
                "membench": gather_sections(item_cache, path, objdump, gdb),
                "object-sizes": gather_object_sizes(item_cache, path, gdb)
            }

        # Save the memory benchmark results
        log = self.output("log")
        assert isinstance(log, DirectoryState)
        log.json_dump(results)
