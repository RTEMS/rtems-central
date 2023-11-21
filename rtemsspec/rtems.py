# SPDX-License-Identifier: BSD-2-Clause
""" This module provides details of the RTEMS specification. """

# Copyright (C) 2021, 2022 embedded brains GmbH & Co. KG
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

import itertools
from typing import Any, List, Tuple, Union

from rtemsspec.items import create_unique_link, Item, ItemCache, Link

_NOT_PRE_QUALIFIED = set([
    "/acfg/constraint/option-not-pre-qualified",
    "/constraint/constant-not-pre-qualified",
    "/constraint/directive-not-pre-qualified",
])


def is_pre_qualified(item: Item) -> bool:
    """ Returns true, if the item is pre-qualified, otherwise false. """
    return not bool(
        set(parent.uid for parent in item.parents("constraint")).intersection(
            _NOT_PRE_QUALIFIED))


_ENABLEMENT_ROLES = [
    "interface-function", "interface-ingroup", "interface-ingroup-hidden",
    "requirement-refinement", "validation"
]


def _link_is_enabled(_link: Link) -> bool:
    return True


def recursive_is_enabled(enabled: List[str], item: Item) -> bool:
    """
    Returns true, if the item is enabled and there exists a path to the root
    item where each item on the path is enabled, otherwise false.
    """
    if not item.is_enabled(enabled):
        return False
    result = True
    for parent in item.parents(_ENABLEMENT_ROLES,
                               is_link_enabled=_link_is_enabled):
        if recursive_is_enabled(enabled, parent):
            return True
        result = False
    return result


def _add_link(item_cache: ItemCache, child: Item, data: Any) -> None:
    parent = item_cache[child.to_abs_uid(data["uid"])]
    create_unique_link(child, parent, data)


def augment_with_test_links(item_cache: ItemCache) -> None:
    """ Augments links of test case items with links from their actions. """
    for item in item_cache.items_by_type["test-case"]:
        for actions in item["test-actions"]:
            for checks in actions["checks"]:
                for link in checks["links"]:
                    _add_link(item_cache, item, link)
            for link in actions["links"]:
                _add_link(item_cache, item, link)


_SELF_VALIDATION = {
    "memory-benchmark": "memory benchmark",
    "requirement/functional/action": "validation by test",
    "requirement/non-functional/performance-runtime": "validation by test",
    "runtime-measurement-test": "validation by test"
}

_VALIDATION_METHOD = {
    "memory-benchmark": "validation by inspection",
    "requirement/functional/action": "validation by test",
    "requirement/non-functional/performance-runtime": "validation by test",
    "runtime-measurement-test": "validation by test",
    "test-case": "validation by test",
    "validation/by-analysis": "validation by analysis",
    "validation/by-inspection": "validation by inspection",
    "validation/by-review-of-design": "validation by review of design",
}

_CONTAINER_TYPE = ["interface/domain", "interface/header-file"]

# In the first pass using _validate_tree() we consider interface domains and
# header files as validated.  We have to do this since a traversal to interface
# placements would lead to an infinite recursion in _validate_tree().  In the
# second pass using _validate_containers() the interface domain and header file
# validations are fixed.
_VALIDATION_LEAF = list(_VALIDATION_METHOD.keys()) + _CONTAINER_TYPE

_CHILD_ROLES = [
    "requirement-refinement", "interface-ingroup", "interface-ingroup-hidden",
    "interface-function", "glossary-member", "test-case", "validation"
]

_PARENT_ROLES = [
    "function-implementation", "interface-enumerator",
    "performance-runtime-limits"
]


def _validate_glossary_term(item: Item) -> bool:
    for item_2 in item.parents("glossary-member"):
        if item_2.type != "glossary/group":
            return False
    return True


def _validate_constraint(item: Item) -> bool:
    for item_2 in item.parents("requirement-refinement"):
        if item_2.uid != "/req/usage-constraints":
            return False
    return True


_VALIDATOR = {
    "constraint": _validate_constraint,
    "glossary/term": _validate_glossary_term
}


def _validate_tree(item: Item) -> bool:
    pre_qualified = is_pre_qualified(item)
    item["_pre_qualified"] = pre_qualified
    validated = True
    validation_dependencies: List[Tuple[str, str]] = []
    for link in itertools.chain(item.links_to_children(_CHILD_ROLES),
                                item.links_to_parents(_PARENT_ROLES)):
        item_2 = link.item
        validated = _validate_tree(item_2) and validated
        if link.role == "validation":
            role = _VALIDATION_METHOD[item_2.type]
        elif link.role == "requirement-refinement":
            role = "refinement"
        elif link.role.startswith("interface-ingroup"):
            role = "group member"
        elif link.role == "performance-runtime-limits":
            role = "runtime performance requirement"
        else:
            role = link.role.replace("-", " ")
        validation_dependencies.append((item_2.uid, role))
    type_name = item.type
    if type_name in _SELF_VALIDATION:
        validation_dependencies.append((item.uid, _SELF_VALIDATION[type_name]))
    elif not validation_dependencies:
        if type_name in _VALIDATOR:
            validated = _VALIDATOR[type_name](item)
        else:
            validated = (not pre_qualified) or (type_name in _VALIDATION_LEAF)
    if type_name in _CONTAINER_TYPE:
        validation_dependencies.extend(
            (item_2.uid, "interface placement")
            for item_2 in item.children("interface-placement"))
    item["_validated"] = validated
    item["_validation_dependencies"] = sorted(validation_dependencies)
    return validated


def _validate_containers(item: Item) -> bool:
    validated = item["_validated"]
    if item.type in _CONTAINER_TYPE:
        # If at least one not validated child exists, then the container is not
        # validated
        for item_2 in item.children("interface-placement"):
            if not item_2["_validated"]:
                validated = False
                item["_validated"] = validated
                break
    for item_2 in itertools.chain(item.children(_CHILD_ROLES),
                                  item.parents(_PARENT_ROLES)):
        validated = _validate_containers(item_2) and validated
    return validated


def _fixup_pre_qualified(item: Item, types: List[str],
                         roles: Union[str, List[str]]) -> None:
    for type_name in types:
        for item_2 in item.cache.items_by_type[type_name]:
            # Count of not pre-qualified (index 0) and pre-qualified (index 1)
            # children
            count = [0, 0]
            for item_3 in item_2.children(roles):
                count[int(item_3["_pre_qualified"])] += 1
            # If at least one not pre-qualified child exists and no
            # pre-qualified child exists, then the item is not pre-qualified.
            if count[0] > 0 and count[1] == 0:
                item_2["_pre_qualified"] = False


def validate(item: Item) -> None:
    """ Validates the item tree starting at the root item. """
    _validate_tree(item)
    _validate_containers(item)
    _fixup_pre_qualified(item,
                         ["interface/appl-config-group", "interface/group"],
                         ["interface-ingroup", "interface-ingroup-hidden"])
    _fixup_pre_qualified(item, ["interface/header-file"],
                         "interface-placement")
