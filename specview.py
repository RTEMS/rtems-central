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
from typing import Any, List, Set, Tuple

from rtemsspec.items import EmptyItem, Item, ItemCache, ItemMapper, \
    ItemGetValueContext, Link
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.util import load_config
from rtemsspec.validation import Transition, TransitionMap

_CHILD_ROLES = [
    "requirement-refinement", "interface-ingroup", "interface-ingroup-hidden",
    "interface-function", "validation", "appl-config-group-member"
]

_PARENT_ROLES = ["interface-enumerator", "interface-placement"]


def _get_value_dummy(_ctx: ItemGetValueContext) -> Any:
    return ""


_MAPPER = ItemMapper(EmptyItem())
_MAPPER.add_get_value("requirement/functional/action:/text-template",
                      _get_value_dummy)
_MAPPER.add_get_value("glossary/term:/plural", _get_value_dummy)
_MAPPER.add_get_value(
    "requirement/non-functional/performance-runtime:/limit-kind",
    _get_value_dummy)
_MAPPER.add_get_value(
    "requirement/non-functional/performance-runtime:/limit-condition",
    _get_value_dummy)
_MAPPER.add_get_value(
    "requirement/non-functional/performance-runtime:/environment",
    _get_value_dummy)


def _visit_action_conditions(item: Item, name: str) -> None:
    for index, condition in enumerate(item[name]):
        for index_2, state in enumerate(condition["states"]):
            _MAPPER.substitute(state["text"], item,
                               f"{name}[{index}]/states[{index_2}]/text")


def _visit_action(item: Item) -> None:
    _visit_action_conditions(item, "pre-conditions")
    _visit_action_conditions(item, "post-conditions")


_VISITORS = {
    "requirement/functional/action": _visit_action,
}


def _visit_item(item: Item, level: int) -> None:
    print(f"{'  ' * level}{item.uid}")
    if item.type.startswith("requirement"):
        _MAPPER.substitute(item["text"], item)
    try:
        visitor = _VISITORS[item.type]
    except KeyError:
        pass
    else:
        visitor(item)


def _view_interface_placment(item: Item, level: int) -> None:
    for child in item.children("interface-placement"):
        _visit_item(child, level)
        _view_interface_placment(child, level + 1)


def _view(item: Item, level: int) -> None:
    _visit_item(item, level)
    _view_interface_placment(item, level + 1)
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


def _gather_interface_placement(item: Item, spec: Set) -> None:
    for child in item.children("interface-placement"):
        spec.add(child)
        _gather_interface_placement(child, spec)


def _gather(item: Item, spec: Set) -> None:
    spec.add(item)
    _gather_interface_placement(item, spec)
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
                 transition_map.map_idx_to_pre_co_states(
                     map_idx, variant.pre_cond_na))),
            (transition_map.post_co_idx_st_idx_to_st_name(co_idx, st_idx)
             for co_idx, st_idx in enumerate(variant.post_cond))))


def _action_table(enabled: List[str], item: Item) -> None:
    rows = [
        tuple(
            itertools.chain(["Entry", "Descriptor"],
                            (condition["name"]
                             for condition in item["pre-conditions"]),
                            (condition["name"]
                             for condition in item["post-conditions"])))
    ]
    transition_map = TransitionMap(item)
    for map_idx, variant in transition_map.get_variants(enabled):
        rows.append(_make_row(transition_map, map_idx, variant))
    content = SphinxContent()
    content.add_simple_table(rows)
    print(str(content))


def _to_name(transition_map, co_idx: int, st_idx: int) -> str:
    return (f"{transition_map.post_co_idx_to_co_name(co_idx)} = "
            f"{transition_map.post_co_idx_st_idx_to_st_name(co_idx, st_idx)}")


def _action_list(enabled: List[str], item: Item) -> None:
    transition_map = TransitionMap(item)
    for post_cond, pre_conds in transition_map.get_post_conditions(enabled):
        print("")
        if post_cond[0]:
            print(transition_map.skip_idx_to_name(post_cond[0]))
        else:
            print(", ".join(
                _to_name(transition_map, co_idx, st_idx)
                for co_idx, st_idx in enumerate(post_cond[1:])))
        for row in pre_conds:
            entries = []
            for co_idx, co_states in enumerate(row):
                co_name = transition_map.pre_co_idx_to_co_name(co_idx)
                states = [
                    transition_map.pre_co_idx_st_idx_to_st_name(
                        co_idx, st_idx) for st_idx in set(co_states)
                ]
                if len(states) == 1:
                    entries.append(f"{co_name} = {states[0]}")
                else:
                    entries.append(f"{co_name} = {{ " + ", ".join(states) +
                                   " }")
            print("")
            print("    * " + ", ".join(entries))


def main() -> None:
    """ Views the specification. """
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter',
                        choices=[
                            "none", "orphan", "no-validation", "action-table",
                            "action-list"
                        ],
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
    elif args.filter == "action-table":
        enabled = args.enabled.split(",") if args.enabled else []
        for uid in args.UIDs:
            _action_table(enabled, item_cache[uid])
    elif args.filter == "action-list":
        enabled = args.enabled.split(",") if args.enabled else []
        for uid in args.UIDs:
            _action_list(enabled, item_cache[uid])
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
