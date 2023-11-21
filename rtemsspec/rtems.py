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

import base64
import hashlib
import itertools
from typing import Any, Dict, List, Set, Tuple, Union

from rtemsspec.items import create_unique_link, Item, ItemCache, Link
from rtemsspec.glossary import augment_glossary_terms
from rtemsspec.packagebuild import BuildItem, PackageBuildDirector
from rtemsspec.validation import augment_with_test_case_links

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


def _visit_domain(item: Item, domain: Item) -> None:
    for item_2 in itertools.chain(item.children("interface-placement"),
                                  item.parents("interface-enumerator")):
        item_2["_interface_domain"] = domain
        _visit_domain(item_2, domain)


def _augment_with_interface_domains(item_cache: ItemCache) -> None:
    """ Augments the interface items with their interface domain. """
    for item in item_cache.items_by_type["interface/domain"]:
        _visit_domain(item, item)


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


def _validate_tree(item: Item, order: Tuple[int, ...],
                   related_items: Set[Item]) -> bool:
    item["_order"] = order
    related_items.add(item)
    pre_qualified = is_pre_qualified(item)
    item["_pre_qualified"] = pre_qualified
    validated = True
    validation_dependencies: List[Tuple[str, str]] = []
    for index, link in enumerate(
            sorted(
                itertools.chain(item.links_to_children(_CHILD_ROLES),
                                item.links_to_parents(_PARENT_ROLES)))):
        item_2 = link.item
        related_items.add(item)
        validated = _validate_tree(item_2, order[:-1] +
                                   (order[-1] + index + 1, 0),
                                   related_items) and validated
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


def validate(root: Item) -> Set[Item]:
    """
    Validates the item tree starting at the root item.

    Returns the set of items related to the root item.
    """
    related_items: Set[Item] = set()
    _validate_tree(root, (0, ), related_items)
    _validate_containers(root)
    _fixup_pre_qualified(root,
                         ["interface/appl-config-group", "interface/group"],
                         ["interface-ingroup", "interface-ingroup-hidden"])
    _fixup_pre_qualified(root, ["interface/header-file"],
                         "interface-placement")
    return related_items


_API_INTERFACES = [
    "interface/appl-config-option/feature",
    "interface/appl-config-option/feature-enable",
    "interface/appl-config-option/initializer",
    "interface/appl-config-option/integer",
    "interface/function",
    "interface/macro",
    "interface/unspecified-function",
    "interface/unspecified-macro",
]

_API_ROLES = [
    "requirement-refinement",
    "interface-ingroup",
]


def _gather_api_items(item: Item, items: Dict[str, List[Item]]) -> None:
    if item.type in _API_INTERFACES and item["_pre_qualified"]:
        parent = item.parent(_API_ROLES)
        group = items.setdefault(parent.get("name", parent.spec), [])
        group.append(item)
    for child in item.children(_API_ROLES):
        _gather_api_items(child, items)


def gather_api_items(item_cache: ItemCache, items: Dict[str,
                                                        List[Item]]) -> None:
    """
    Gathers all API related items and groups them by the associated interface
    group name.

    If a group has no name, then the UID is used instead.
    """
    for group in item_cache["/req/api"].children("requirement-refinement"):
        _gather_api_items(group, items)


def _is_proxy_link_enabled(link: Link) -> bool:
    return link.item.is_enabled(link.item.cache.enabled)


class RTEMSItemCache(BuildItem):
    """
    This build step augments the items with RTEMS-specific attributes and
    links.
    """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.item_cache = self.item.cache

        # It is crucial to resolve the proxies before we use the recursive
        # enabled below since unresolved proxy items have no links.
        self.item_cache.resolve_proxies(_is_proxy_link_enabled)
        self.item_cache.set_enabled(self.enabled_set, recursive_is_enabled)

        augment_with_test_links(self.item_cache)
        augment_with_test_case_links(self.item_cache)
        _augment_with_interface_domains(self.item_cache)
        for glossary in ["/glossary-general", "/req/glossary"]:
            augment_glossary_terms(self.item_cache[glossary], [])
        self.related_items = validate(self.item_cache[self["spec-root-uid"]])
        self.related_items_by_type: Dict[str, List[Item]] = {}
        for item_2 in self.related_items:
            self.related_items_by_type.setdefault(item_2.type,
                                                  []).append(item_2)

        # Calculate the overall item cache hash.  Ignore QDP configuration
        # items and specification type changes.
        state = hashlib.sha512()
        for item_2 in sorted(self.item_cache.values()):
            if not item_2.type.startswith(("qdp", "spec")):
                state.update(item_2.digest.encode("ascii"))
        self._hash = base64.urlsafe_b64encode(state.digest()).decode("ascii")

    def has_changed(self, link: Link) -> bool:
        return link["hash"] is None or self._hash != link["hash"]

    def refresh_link(self, link: Link) -> None:
        link["hash"] = self._hash

    def get_related_items_by_type(self, types: Union[str,
                                                     List[str]]) -> List[Item]:
        """ Gets related items by a list of types. """
        if isinstance(types, str):
            types = [types]
        items: List[Item] = []
        for type_name in types:
            items.extend(
                item for item in self.related_items_by_type.get(type_name, []))
        return sorted(items)

    def get_related_types_by_prefix(
            self, prefix: Union[str, Tuple[str, ...]]) -> List[str]:
        """
        Gets the types of the related items having one of the type prefixes.
        """
        return [
            type_name for type_name in sorted(self.related_items_by_type)
            if type_name.startswith(prefix)
        ]

    def get_related_interfaces(self) -> List[Item]:
        """ Gets the related interfaces. """
        return self.get_related_items_by_type(
            self.get_related_types_by_prefix("interface/"))

    def get_related_requirements(self) -> List[Item]:
        """ Gets the related requirements. """
        return self.get_related_items_by_type(
            self.get_related_types_by_prefix("requirement/"))

    def get_related_interfaces_and_requirements(self) -> List[Item]:
        """ Gets the related interfaces and requirements. """
        return self.get_related_items_by_type(
            self.get_related_types_by_prefix(("interface/", "requirement/")))
