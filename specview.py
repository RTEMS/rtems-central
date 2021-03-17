#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
""" Views the specification. """

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

import argparse
import itertools
import sys
from typing import List, Set, Tuple

from rtemsspec.items import is_enabled, Item, ItemCache, Link
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.util import load_config
from rtemsspec.validation import Transition, TransitionMap

_CHILD_ROLES = [
    "requirement-refinement", "interface-ingroup", "interface-function",
    "validation", "appl-config-group-member"
]

_PARENT_ROLES = ["interface-enumerator", "interface-placement"]


def _view(item: Item, level: int) -> None:
    print(f"{'  ' * level}{item.uid}")
    for child in item.children(_CHILD_ROLES):
        _view(child, level + 1)


def _no_validation(item: Item, path: List[str]) -> List[str]:
    leaf = True
    path_2 = path + [item.uid]
    for child in item.children(_CHILD_ROLES):
        path_2 = _no_validation(child, path_2)
        leaf = False
    if leaf and item.type not in [
            "requirement/functional/action", "test-case", "test-suite"
    ]:
        for index, component in enumerate(path_2):
            if component:
                print(f"{'  ' * index}{component}")
            path_2[index] = ""
    return path_2[:-1]


def _gather(item: Item, spec: Set) -> None:
    spec.add(item)
    for child in item.children(_CHILD_ROLES):
        _gather(child, spec)
    for parent in item.parents(_PARENT_ROLES):
        _gather(parent, spec)


def _add_link(item_cache: ItemCache, child: Item, link: Link) -> None:
    parent = item_cache[child.to_abs_uid(link["uid"])]
    parent.add_link_to_child(Link(child, link))


def _process_test_cases(item_cache: ItemCache) -> None:
    for item in item_cache.all.values():
        if item.type == "test-case":
            for actions in item["test-actions"]:
                for checks in actions["checks"]:
                    for link in checks["links"]:
                        _add_link(item_cache, item, link)
                for link in actions["links"]:
                    _add_link(item_cache, item, link)


def _make_row(transition_map: TransitionMap, map_idx: int,
              variant: Transition) -> Tuple[str, ...]:
    return tuple(
        itertools.chain(
            [str(map_idx), str(variant.desc_idx)],
            (transition_map.pre_co_idx_st_idx_to_st_name(co_idx, st_idx)
             for co_idx, st_idx in enumerate(
                 transition_map.map_idx_to_pre_co_states(map_idx))),
            (transition_map.post_co_idx_st_idx_to_st_name(co_idx, st_idx)
             for co_idx, st_idx in enumerate(variant.post_cond))))


def main() -> None:
    """ Views the specification. """
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter',
                        choices=["none", "orphan", "no-validation", "action"],
                        type=str.lower,
                        default="none",
                        help="filter the items")
    parser.add_argument(
        "--enabled",
        help=("a comma separated list of enabled options used to evaluate "
              "enabled-by expressions"))
    parser.add_argument("UIDs",
                        metavar="UID",
                        nargs="*",
                        help="an UID of a specification item")
    args = parser.parse_args(sys.argv[1:])
    config = load_config("config.yml")
    item_cache = ItemCache(config["spec"])
    _process_test_cases(item_cache)
    root = item_cache["/req/root"]

    if args.filter == "none":
        _view(root, 0)
    elif args.filter == "action":
        enabled = args.enabled.split(",") if args.enabled else []
        for uid in args.UIDs:
            item = item_cache[uid]
            rows = [
                tuple(
                    itertools.chain(
                        ["Entry", "Descriptor"],
                        (condition["name"]
                         for condition in item["pre-conditions"]),
                        (condition["name"]
                         for condition in item["post-conditions"])))
            ]
            transition_map = TransitionMap(item)
            for map_idx, transitions in enumerate(transition_map):
                for variant in transitions[1:]:
                    if is_enabled(enabled, variant.enabled_by):
                        rows.append(_make_row(transition_map, map_idx,
                                              variant))
                        break
                else:
                    rows.append(
                        _make_row(transition_map, map_idx, transitions[0]))
        content = SphinxContent()
        content.add_simple_table(rows)
        print(str(content))
    elif args.filter == "orphan":
        spec = set()  # type: Set[Item]
        _gather(root, spec)
        for item in item_cache.all.values():
            if item["type"] in ["build", "glossary", "spec"]:
                continue
            if item not in spec:
                print(item.uid)
    elif args.filter == "no-validation":
        _no_validation(root, [])


if __name__ == "__main__":
    main()
