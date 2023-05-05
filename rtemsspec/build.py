# SPDX-License-Identifier: BSD-2-Clause
""" This module provides support for the build specification. """

# Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
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

from typing import Dict, List

from rtemsspec.items import is_enabled, Item, ItemCache

BSPMap = Dict[str, Dict[str, Item]]
ItemMap = Dict[str, Item]


def _extend_by_install(item: Item, source_files: List[str]) -> None:
    for install in item["install"]:
        source_files.extend(install["source"])


def _extend_by_source(item: Item, source_files: List[str]) -> None:
    source_files.extend(item["source"])


def _extend_by_install_and_source(item: Item, source_files: List[str]) -> None:
    _extend_by_install(item, source_files)
    _extend_by_source(item, source_files)


def _extend_by_nothing(_item: Item, _source_files: List[str]) -> None:
    pass


_EXTEND_SOURCE_FILES = {
    "ada-test-program": _extend_by_nothing,
    "bsp": _extend_by_install_and_source,
    "config-file": _extend_by_nothing,
    "config-header": _extend_by_nothing,
    "test-program": _extend_by_source,
    "group": _extend_by_install,
    "library": _extend_by_install_and_source,
    "objects": _extend_by_install_and_source,
    "option": _extend_by_nothing,
    "script": _extend_by_nothing,
    "start-file": _extend_by_source,
}

_BUILD_ROLES = ["build-dependency", "build-dependency-conditional"]


def _gather_source_files(item: Item, enabled: List[str],
                         source_files: List[str]) -> None:
    for link in item.links_to_parents(_BUILD_ROLES):
        if (link.role == "build-dependency" or is_enabled(
                enabled,
                link["enabled-by"])) and link.item.is_enabled(enabled):
            _gather_source_files(link.item, enabled, source_files)
    _EXTEND_SOURCE_FILES[item["build-type"]](item, source_files)


def _gather_test_header(item_cache: ItemCache, enabled: List[str],
                        source_files: List[str]) -> None:
    for item in item_cache.all.values():
        tests = ["test-case", "requirement/functional/action"]
        if item.type in tests and item["test-header"] and item.is_enabled(
                enabled):
            source_files.append(item["test-header"]["target"])


def gather_files(config: dict,
                 item_cache: ItemCache,
                 test_header: bool = True) -> List[str]:
    """ Generates a list of files form the build specification. """
    bsps: BSPMap = {}
    for item in item_cache.all.values():
        if item["type"] == "build" and item["build-type"] == "bsp":
            arch_bsps = bsps.setdefault(item["arch"].strip(), {})
            arch_bsps[item["bsp"].strip()] = item
    source_files: List[str] = list(config["extra-files"])
    arch = config["arch"]
    bsp = config["bsp"]
    enabled = [arch, arch + "/" + bsp] + config["enabled"]
    _gather_source_files(bsps[arch][bsp], enabled, source_files)
    for uid in config["build-uids"]:
        _gather_source_files(item_cache[uid], enabled, source_files)
    if test_header:
        _gather_test_header(item_cache, enabled, source_files)
    return source_files
