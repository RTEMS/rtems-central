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
from typing import Any, List, Optional, Set, Tuple

from rtemsspec.items import EmptyItem, Item, ItemCache, ItemMapper, \
    ItemGetValueContext, Link
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.util import load_config
from rtemsspec.transitionmap import Transition, TransitionMap

_CHILD_ROLES = [
    "requirement-refinement", "interface-ingroup", "interface-ingroup-hidden",
    "interface-function", "appl-config-group-member", "glossary-member"
]

_PARENT_ROLES = ["function-implementation", "interface-enumerator"]


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


def _info(item: Item) -> str:
    if not item.get("_pre_qualified", True):
        return ", not-pre-qualified"
    try:
        if item["_validated"]:
            return ""
        return ", not-validated"
    except KeyError:
        return ""


_TEXT_ATTRIBUTES = [
    "brief",
    "description",
    "notes",
    "rationale",
    "test-brief",
    "test-description",
    "text",
]


def _visit_item(item: Item, level: int, role: Optional[str],
                validated_filter: str) -> bool:
    validated = item.get("_validated", True)
    if validated_filter == "yes" and not validated:
        return False
    if validated_filter == "no" and validated:
        return False
    role_info = "" if role is None else f", role={role}"
    print(
        f"{'  ' * level}{item.uid} (type={item.type}{role_info}{_info(item)})")
    for name in _TEXT_ATTRIBUTES:
        if name in item:
            _MAPPER.substitute(item[name], item)
    try:
        visitor = _VISITORS[item.type]
    except KeyError:
        pass
    else:
        visitor(item)
    return True


def _view_interface_placment(item: Item, level: int,
                             validated_filter: str) -> None:
    for link in item.links_to_children("interface-placement"):
        if _visit_item(link.item, level, link.role, validated_filter):
            _view_interface_placment(link.item, level + 1, validated_filter)


def _view(item: Item, level: int, role: Optional[str], validated_filter: str,
          enabled: List[str]) -> None:
    if not item.is_enabled(enabled):
        return
    if not _visit_item(item, level, role, validated_filter):
        return
    for child in item.children("validation"):
        if child.is_enabled(enabled):
            _visit_item(child, level + 1, "validation", validated_filter)
    _view_interface_placment(item, level + 1, validated_filter)
    for link in item.links_to_children(_CHILD_ROLES):
        _view(link.item, level + 1, link.role, validated_filter, enabled)
    for link in item.links_to_parents(_PARENT_ROLES):
        _view(link.item, level + 1, link.role, validated_filter, enabled)


_VALIDATION_LEAF = [
    "constraint",
    "glossary/group",
    "glossary/term",
    "interface/appl-config-group",
    "interface/container",
    "interface/domain",
    "interface/enum",
    "interface/enumerator",
    "interface/header-file",
    "interface/register-block",
    "interface/struct",
    "interface/typedef",
    "interface/union",
    "interface/unspecified-define",
    "interface/unspecified-function",
    "requirement/functional/action",
    "requirement/non-functional/performance-runtime",
    "runtime-measurement-test",
    "test-case",
    "test-suite",
    "validation",
]

_NOT_PRE_QUALIFIED = set([
    "/acfg/constraint/option-not-pre-qualified",
    "/constraint/constant-not-pre-qualified",
    "/constraint/directive-not-pre-qualified",
])


def _is_pre_qualified(item: Item) -> bool:
    return not bool(
        set(parent.uid for parent in item.parents("constraint")).intersection(
            _NOT_PRE_QUALIFIED))


def _validation_count(item: Item, enabled: List[str]) -> int:
    return len(
        list(child for child in item.children("validation")
             if child.is_enabled(enabled)))


def _validate(item: Item, enabled: List[str]) -> bool:
    count = _validation_count(item, enabled)
    validated = True
    for child in item.children(_CHILD_ROLES):
        if child.is_enabled(enabled):
            validated = _validate(child, enabled) and validated
            count += 1
    for parent in item.parents(_PARENT_ROLES):
        if parent.is_enabled(enabled):
            validated = _validate(parent, enabled) and validated
            count += 1
    pre_qualified = _is_pre_qualified(item)
    item["_pre_qualified"] = pre_qualified
    if count == 0:
        if not pre_qualified:
            validated = True
        else:
            validated = item.type in _VALIDATION_LEAF
    item["_validated"] = validated
    return validated


def _no_validation(item: Item, path: List[str],
                   enabled: List[str]) -> List[str]:
    path_2 = path + [item.uid]
    if not item.is_enabled(enabled):
        return path_2[:-1]
    leaf = _validation_count(item, enabled) == 0
    for child in item.children(_CHILD_ROLES):
        path_2 = _no_validation(child, path_2, enabled)
        leaf = False
    for parent in item.parents(_PARENT_ROLES):
        path_2 = _no_validation(parent, path_2, enabled)
        leaf = False
    if leaf and not item.get("_validated", True):
        for index, component in enumerate(path_2):
            if component:
                print(f"{'  ' * index}{component}")
            path_2[index] = ""
    return path_2[:-1]


_REFINEMENTS = ["interface-function", "requirement-refinement"]

_GROUPS = ["requirement/non-functional/design-group", "interface/group"]


def _is_refinement(item: Item, other: Item) -> bool:
    for parent in item.parents(_REFINEMENTS):
        if parent == other:
            return True
        if _is_refinement(parent, other):
            return True
    return False


def _gather_design_components(item: Item, components: List[Item]) -> bool:
    if item.type in _GROUPS:
        components.append(item)
        return True
    if item.type.startswith("requirement"):
        for parent in item.parents("interface-function"):
            components.append(parent)
        for parent in item.parents("requirement-refinement"):
            _gather_design_components(parent, components)
        return True
    return False


def _design(item_cache: ItemCache, enabled: List[str]) -> None:
    for item in item_cache.all.values():
        if not item.is_enabled(enabled):
            continue
        components = []  # type: List[Item]
        if not _gather_design_components(item, components):
            continue
        compact = set()  # type: Set[Item]
        for component in components:
            for component_2 in components:
                if component != component_2:
                    if _is_refinement(component_2, component):
                        break
            else:
                compact.add(component)
        if compact:
            text = ", ".join(component.uid for component in compact)
        else:
            text = "N/A"
        print(f"{item.uid}\t{text}")


def _gather_interface_placement(item: Item, spec: Set) -> None:
    for child in item.children("interface-placement"):
        spec.add(child)
        _gather_interface_placement(child, spec)


def _gather(item: Item, spec: Set) -> None:
    spec.add(item)
    _gather_interface_placement(item, spec)
    for child in item.children("validation"):
        spec.add(child)
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
            names = []  # type: List[str]
            for co_idx, st_idx in enumerate(post_cond[1:]):
                st_name = transition_map.post_co_idx_st_idx_to_st_name(
                    co_idx, st_idx)
                if st_name != "NA":
                    co_name = transition_map.post_co_idx_to_co_name(co_idx)
                    names.append(f"{co_name} = {st_name}")
            print(", ".join(names))
        for row in pre_conds:
            entries = []
            for co_idx, co_states in enumerate(row):
                co_name = transition_map.pre_co_idx_to_co_name(co_idx)
                states = [
                    transition_map.pre_co_idx_st_idx_to_st_name(
                        co_idx, st_idx) for st_idx in set(co_states)
                ]
                if len(states) == 1:
                    if states[0] != "NA":
                        entries.append(f"{co_name} = {states[0]}")
                else:
                    entries.append(f"{co_name} = {{ " + ", ".join(states) +
                                   " }")
            print("")
            print("    * " + ", ".join(entries))


_API_INTERFACES = [
    "interface/appl-config-option/feature",
    "interface/appl-config-option/initializer",
    "interface/appl-config-option/integer",
    "interface/function",
    "interface/macro",
]

_API_ROLES = [
    "requirement-refinement",
    "interface-placement",
    "appl-config-group-member",
]


def _gather_api_names(item: Item, names: List[str]) -> None:
    if item.type in _API_INTERFACES and _is_pre_qualified(item):
        names.append(item["name"])
    for child in item.children(_API_ROLES):
        _gather_api_names(child, names)


def _list_api(item_cache: ItemCache) -> None:
    names = []  # type: List[str]
    _gather_api_names(item_cache["/if/domain"], names)
    _gather_api_names(item_cache["/acfg/if/domain"], names)
    for name in sorted(names):
        print(name)


def main() -> None:
    """ Views the specification. """
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter',
                        choices=[
                            "none", "api", "orphan", "no-validation",
                            "action-table", "action-list", "design"
                        ],
                        type=str.lower,
                        default="none",
                        help="filter the items")
    parser.add_argument('--validated',
                        choices=["all", "yes", "no"],
                        type=str.lower,
                        default="all",
                        help="filter the items by the validated status")
    parser.add_argument(
        "--enabled",
        help=("a comma separated list of enabled options used to evaluate "
              "enabled-by expressions"))
    parser.add_argument("UIDs",
                        metavar="UID",
                        nargs="*",
                        help="an UID of a specification item")
    args = parser.parse_args(sys.argv[1:])
    enabled = args.enabled.split(",") if args.enabled else []
    config = load_config("config.yml")
    item_cache = ItemCache(config["spec"])
    _process_test_cases(item_cache)
    root = item_cache["/req/root"]

    if args.filter == "none":
        _validate(root, enabled)
        _view(root, 0, None, args.validated, enabled)
    elif args.filter == "action-table":
        for uid in args.UIDs:
            _action_table(enabled, item_cache[uid])
    elif args.filter == "action-list":
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
        _validate(root, enabled)
        _no_validation(root, [], enabled)
    elif args.filter == "api":
        _validate(root, enabled)
        _list_api(item_cache)
    elif args.filter == "design":
        _design(item_cache, enabled)


if __name__ == "__main__":
    main()
