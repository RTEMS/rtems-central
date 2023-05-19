#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
""" Views the specification. """

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

import argparse
import itertools
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from rtemsspec.items import EmptyItem, Item, ItemCache, ItemMapper, \
    ItemGetValueContext
from rtemsspec.rtems import augment_with_test_links, is_pre_qualified, \
    recursive_is_enabled
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.transitionmap import Transition, TransitionMap
from rtemsspec.util import load_config
from rtemsspec.validation import augment_with_test_case_links

_CHILD_ROLES = [
    "requirement-refinement", "interface-ingroup", "interface-ingroup-hidden",
    "interface-function", "glossary-member", "runtime-measurement-request",
    "test-case"
]

_PARENT_ROLES = [
    "function-implementation", "interface-enumerator",
    "performance-runtime-limits"
]


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
_MAPPER.add_get_value(
    "requirement/non-functional/performance-runtime-limits:/text-template",
    _get_value_dummy)

_SPEC_TYPES = [
    "requirement/functional/action",
    "requirement/functional/capability",
    "requirement/functional/function",
    "requirement/non-functional/design",
    "requirement/non-functional/design-group",
    "requirement/non-functional/interface-requirement",
    "requirement/non-functional/performance",
    "requirement/non-functional/performance-runtime",
    "requirement/non-functional/quality",
]

for type_name in _SPEC_TYPES:
    _MAPPER.add_get_value(f"{type_name}:/spec", _get_value_dummy)


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


def _view(item: Item, level: int, role: Optional[str],
          validated_filter: str) -> None:
    if not _visit_item(item, level, role, validated_filter):
        return
    for child in item.children("validation"):
        _visit_item(child, level + 1, "validation", validated_filter)
    _view_interface_placment(item, level + 1, validated_filter)
    for link in item.links_to_children(_CHILD_ROLES):
        _view(link.item, level + 1, link.role, validated_filter)
    for link in item.links_to_parents(_PARENT_ROLES):
        _view(link.item, level + 1, link.role, validated_filter)


_VALIDATION_LEAF = [
    "constraint",
    "glossary/group",
    "glossary/term",
    "interface/domain",
    "interface/enum",
    "interface/enumerator",
    "interface/forward-declaration",
    "interface/header-file",
    "interface/register-block",
    "interface/struct",
    "interface/typedef",
    "interface/union",
    "interface/unspecified-define",
    "interface/unspecified-enum",
    "interface/unspecified-enumerator",
    "interface/unspecified-function",
    "interface/unspecified-group",
    "interface/unspecified-macro",
    "interface/unspecified-object",
    "interface/unspecified-struct",
    "interface/unspecified-typedef",
    "interface/unspecified-union",
    "memory-benchmark",
    "requirement/functional/action",
    "requirement/non-functional/performance-runtime",
    "runtime-measurement-test",
    "test-case",
    "validation/by-analysis",
    "validation/by-inspection",
    "validation/by-review-of-design",
]

_VALIDATION_ROLES = _CHILD_ROLES + ["validation"]


def _validate_tree(item: Item) -> bool:
    pre_qualified = is_pre_qualified(item)
    item["_pre_qualified"] = pre_qualified
    validated = True
    count = 0
    for link in itertools.chain(item.links_to_children(_VALIDATION_ROLES),
                                item.links_to_parents(_PARENT_ROLES)):
        validated = _validate_tree(link.item) and validated
        count += 1
    if count == 0:
        validated = (not pre_qualified) or (item.type in _VALIDATION_LEAF)
    item["_validated"] = validated
    return validated


def _validate_containers(item: Item) -> None:
    for item_2 in itertools.chain(
            item.cache.items_by_type["interface/domain"],
            item.cache.items_by_type["interface/header-file"]):
        for item_3 in item_2.children("interface-placement"):
            if not item_3["_validated"]:
                item_2["_validated"] = False
                break


def _validate(item: Item) -> None:
    _validate_tree(item)
    _validate_containers(item)


def _validation_count(item: Item) -> int:
    return len(list(child for child in item.children("validation")))


def _no_validation(item: Item, path: List[str]) -> List[str]:
    path_2 = path + [item.uid]
    leaf = _validation_count(item) == 0
    for child in item.children(_CHILD_ROLES):
        path_2 = _no_validation(child, path_2)
        leaf = False
    for parent in item.parents(_PARENT_ROLES):
        path_2 = _no_validation(parent, path_2)
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


def _design(item_cache: ItemCache) -> None:
    for item in item_cache.all.values():
        if not item.enabled:
            continue
        components: List[Item] = []
        if not _gather_design_components(item, components):
            continue
        compact: Set[Item] = set()
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


def _action_table(item: Item) -> None:
    rows = [
        tuple(
            itertools.chain(["Entry", "Descriptor"],
                            (condition["name"]
                             for condition in item["pre-conditions"]),
                            (condition["name"]
                             for condition in item["post-conditions"])))
    ]
    transition_map = TransitionMap(item)
    for map_idx, variant in transition_map.get_variants(item.cache.enabled):
        rows.append(_make_row(transition_map, map_idx, variant))
    content = SphinxContent()
    content.add_simple_table(rows)
    print(str(content))


def _to_name(transition_map, co_idx: int, st_idx: int) -> str:
    return (f"{transition_map.post_co_idx_to_co_name(co_idx)} = "
            f"{transition_map.post_co_idx_st_idx_to_st_name(co_idx, st_idx)}")


def _action_list(item: Item) -> None:
    transition_map = TransitionMap(item)
    for post_cond, pre_conds in transition_map.get_post_conditions(
            item.cache.enabled):
        print("")
        if post_cond[0]:
            print(transition_map.skip_idx_to_name(post_cond[0]))
        else:
            names: List[str] = []
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
    "interface/appl-config-option/feature-enable",
    "interface/appl-config-option/initializer",
    "interface/appl-config-option/integer",
    "interface/function",
    "interface/macro",
    "interface/unspecified-function",
]

_API_ROLES = [
    "requirement-refinement",
    "interface-ingroup",
]


def _gather_api_names(item: Item, names: Dict[str, List[str]]) -> None:
    if item.type in _API_INTERFACES and is_pre_qualified(item):
        try:
            name = item.parent(_API_ROLES)["name"]
        except KeyError:
            name = item.parent(_API_ROLES).spec
        group = names.setdefault(name, [])
        group.append(item["name"])
    for child in item.children(_API_ROLES):
        _gather_api_names(child, names)


def _list_api(item_cache: ItemCache) -> None:
    names: Dict[str, List[str]] = {}
    _gather_api_names(item_cache["/req/applconfig"], names)
    _gather_api_names(item_cache["/if/group"], names)
    _gather_api_names(item_cache["/c/if/group"], names)
    _gather_api_names(item_cache["/newlib/if/group"], names)
    for group in sorted(names.keys()):
        print(group)
        for name in sorted(names[group]):
            print(f"\t{name}")


def main() -> None:
    """ Views the specification. """

    # pylint: disable=too-many-branches
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter',
                        choices=[
                            "none", "api", "orphan", "no-validation",
                            "action-table", "action-list", "design", "types"
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
    config = load_config("config.yml")["spec"]
    config["enabled"] = args.enabled.split(",") if args.enabled else []
    item_cache = ItemCache(config, is_item_enabled=recursive_is_enabled)
    augment_with_test_links(item_cache)
    augment_with_test_case_links(item_cache)
    root = item_cache["/req/root"]

    if args.filter == "none":
        _validate(root)
        _view(root, 0, None, args.validated)
    elif args.filter == "action-table":
        for uid in args.UIDs:
            _action_table(item_cache[uid])
    elif args.filter == "action-list":
        for uid in args.UIDs:
            _action_list(item_cache[uid])
    elif args.filter == "orphan":
        _validate(root)
        for item in item_cache.all.values():
            if item["type"] in ["build", "spec"]:
                continue
            if item.enabled and "_validated" not in item:
                print(item.uid)
    elif args.filter == "no-validation":
        _validate(root)
        _no_validation(root, [])
    elif args.filter == "api":
        _validate(root)
        _list_api(item_cache)
    elif args.filter == "design":
        _design(item_cache)
    elif args.filter == "types":
        for name in sorted(item_cache.items_by_type.keys()):
            print(name)


if __name__ == "__main__":
    main()
