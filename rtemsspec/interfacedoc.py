# SPDX-License-Identifier: BSD-2-Clause
"""
This module provides functions for the generation of interface documentation.
"""

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

import functools
import os
from typing import Any, Dict, List, Tuple

from rtemsspec.content import CContent, get_value_compound, \
    get_value_forward_declaration
from rtemsspec.sphinxcontent import get_label, get_reference, sanitize_name, \
    SphinxContent, SphinxInterfaceMapper
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]


def _get_reference(name: str) -> str:
    return get_reference(get_label(f"Interface {name}"))


def _get_code_param(ctx: ItemGetValueContext) -> Any:
    return sanitize_name(ctx.value[ctx.key])


class _CodeMapper(ItemMapper):

    def __init__(self, item: Item):
        super().__init__(item)
        self.add_get_value("interface/forward-declaration:/name",
                           get_value_forward_declaration)
        self.add_get_value("interface/struct:/name", get_value_compound)
        self.add_get_value("interface/union:/name", get_value_compound)
        self.add_get_value("interface/macro:/params/name", _get_code_param)


def _generate_introduction(target: str, group: Item, group_uids: List[str],
                           items: List[Item]) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    content.add_automatically_generated_warning()
    group_name = group["name"]
    content.add(f".. Generated from spec:{group.uid}")
    with content.section("Introduction", get_label(group_name)):
        # This needs to be in front of the list since comment blocks have an
        # effect on the list layout in the HTML output
        content.add(".. The following list was generated from:")
        for item in items:
            content.append(f".. spec:{item.uid}")

        content.append("")
        content.gap = False
        mapper = SphinxInterfaceMapper(group, group_uids)
        content.wrap(mapper.substitute(group["brief"]))
        content.wrap(mapper.substitute(group["description"]))
        content.paste(f"The directives provided by the {group_name} are:")

        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            mapper = SphinxInterfaceMapper(item, group_uids)
            brief = mapper.substitute(item["brief"])
            if brief:
                brief = f" - {brief}"
            else:
                brief = ""
            ref = _get_reference(name)
            content.add_list_item(f"{ref}{brief}")
    content.add_licence_and_copyrights()
    content.write(target)


def _add_function_definition(content: CContent, mapper: ItemMapper, item: Item,
                             value: Dict[str, Any]) -> None:
    ret = mapper.substitute(value["return"])
    name = item["name"]
    params = [mapper.substitute(param) for param in value["params"]]
    content.declare_function(ret, name, params)


_ADD_DEFINITION = {
    "interface/function": _add_function_definition,
    "interface/macro": _add_function_definition,
}


def _add_definition(content: CContent, mapper: ItemMapper, item: Item,
                    prefix: str, value: Dict[str, Any]) -> None:
    # pylint: disable=too-many-arguments
    add_definition = _ADD_DEFINITION[item.type]
    key = "default"
    definition = value[key]
    if not definition:
        # Assume that all definitions have the same interface
        key = "variants"
        definition = value["variants"][0]["definition"]
    with mapper.prefix(os.path.join(prefix, key)):
        add_definition(content, mapper, item, definition)


def _generate_directive(content: SphinxContent, mapper: SphinxInterfaceMapper,
                        code_mapper: _CodeMapper, item: Item,
                        enabled: List[str]) -> None:
    content.wrap(mapper.substitute(item["brief"]))
    content.add(".. rubric:: CALLING SEQUENCE:")
    with content.directive("code-block", "c"):
        code = CContent()
        _add_definition(code, code_mapper, item, "definition",
                        item["definition"])
        content.add(code)
    if item["params"]:
        content.add(".. rubric:: PARAMETERS:")
        for param in item["params"]:
            description = param["description"]
            if description:
                content.add_definition_item(
                    f"``{sanitize_name(param['name'])}``",
                    mapper.substitute(f"This parameter {description}"),
                    wrap=True)
    if item["description"]:
        content.add(".. rubric:: DESCRIPTION:")
        content.wrap(mapper.substitute(item["description"]))
    ret = item["return"]
    if ret:
        content.add(".. rubric:: RETURN VALUES:")
        for retval in ret["return-values"]:
            if isinstance(retval["value"], str):
                value = mapper.substitute(str(retval["value"]))
            else:
                value = f"``{str(retval['value'])}``"
            content.add_definition_item(value,
                                        mapper.substitute(
                                            retval["description"]),
                                        wrap=True)
        content.wrap(mapper.substitute(ret["return"]))
    if item["notes"]:
        content.add(".. rubric:: NOTES:")
        content.wrap(mapper.substitute(item["notes"]))
    constraints = [
        mapper.substitute(parent["text"], parent)
        for parent in item.parents("constraint") if parent.is_enabled(enabled)
    ]
    if constraints:
        content.add(".. rubric:: CONSTRAINTS:")
        content.add_list(constraints,
                         "The following constraints apply to this directive:")


def _generate_directives(target: str, group: Item, group_uids: List[str],
                         items: List[Item], enabled: List[str]) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    content.add_automatically_generated_warning()
    group_name = group["name"]
    with content.section("Directives", get_label(group_name)):
        content.wrap([
            f"This section details the directives of the {group_name}.",
            "A subsection is dedicated to each of this manager's directives",
            "and lists the calling sequence, parameters, description,",
            "return values, and notes of the directive."
        ])
        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            code_mapper = _CodeMapper(item)
            mapper = SphinxInterfaceMapper(item, group_uids)
            content.add(f".. Generated from spec:{item.uid}")
            with content.directive("raw", "latex"):
                content.add("\\clearpage")
            directive = f"{name}()"
            content.add_index_entries([directive] + item["index-entries"])
            with content.section(directive, "Interface"):
                _generate_directive(content, mapper, code_mapper, item,
                                    enabled)
    content.add_licence_and_copyrights()
    content.write(target)


def _directive_key(order: List[Item], item: Item) -> Tuple[int, str]:
    try:
        index = order.index(item) - len(order)
    except ValueError:
        index = 1
    return (index, item.uid)


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates interface documentation according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the interfaces.
    """
    groups = config["groups"]
    enabled = config["enabled"]
    group_uids = [doc_config["group"] for doc_config in groups]
    for doc_config in groups:
        items: List[Item] = []
        group = item_cache[doc_config["group"]]
        assert group.type == "interface/group"
        for child in group.children("interface-ingroup"):
            if child.type in ["interface/function", "interface/macro"]:
                items.append(child)
        items.sort(key=functools.partial(
            _directive_key, list(group.parents("placement-order"))))
        _generate_introduction(doc_config["introduction-target"], group,
                               group_uids, items)
        _generate_directives(doc_config["directives-target"], group,
                             group_uids, items, enabled)
