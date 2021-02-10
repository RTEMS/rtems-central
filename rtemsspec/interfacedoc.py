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

from rtemsspec.content import CContent
from rtemsspec.sphinxcontent import get_label, get_reference, SphinxContent, \
     SphinxMapper
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]

INTERFACE = "Interface"


def _sanitize_name(name: str) -> str:
    return name.lstrip("_")


def _forward_declaration(item: Item) -> str:
    target = item.parent("interface-target")
    return f"{target['interface-type']} {target['name']}"


def _get_reference(name: str) -> str:
    return get_reference(get_label(f"{INTERFACE} {name}"))


def _get_value_forward_declaration(ctx: ItemGetValueContext) -> Any:
    return _forward_declaration(ctx.item)


class _CodeMapper(ItemMapper):
    def __init__(self, item: Item):
        super().__init__(item)
        self.add_get_value("interface/forward-declaration:/name",
                           _get_value_forward_declaration)


def _get_param(ctx: ItemGetValueContext) -> Any:
    return f"``{_sanitize_name(ctx.value[ctx.key])}``"


class _Mapper(SphinxMapper):
    def __init__(self, item: Item, group_uids: List[str]):
        super().__init__(item)
        self._group_uids = set(group_uids)
        self.add_get_value("interface/function:/name", self._get_function)
        self.add_get_value("interface/function:/params/name", _get_param)
        self.add_get_value("interface/group:/name", self._get_group)
        self.add_get_value("interface/macro:/name", self._get_function)
        self.add_get_value("interface/macro:/params/name", _get_param)

    def _get_function(self, ctx: ItemGetValueContext) -> Any:
        name = ctx.value[ctx.key]
        for group in ctx.item.parents("interface-ingroup"):
            if group.uid in self._group_uids:
                return _get_reference(name)
        return f":c:func:`{name}`"

    def _get_group(self, ctx: ItemGetValueContext) -> Any:
        if ctx.item.uid in self._group_uids:
            return get_reference(ctx.value["identifier"])
        return ctx.value[ctx.key]


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
        content.wrap(group["brief"])
        content.wrap(group["description"])
        content.paste(f"The directives provided by the {group_name} are:")

        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            mapper = _Mapper(item, group_uids)
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
    params = [
        mapper.substitute(_sanitize_name(param)) for param in value["params"]
    ]
    content.declare_function(ret, name, params)


def _add_macro_definition(content: CContent, _mapper: ItemMapper, item: Item,
                          _value: Dict[str, Any]) -> None:
    ret = "#define"
    name = item["name"]
    params = [_sanitize_name(param["name"]) for param in item["params"]]
    content.call_function(ret, name, params, semicolon="")


_ADD_DEFINITION = {
    "interface/function": _add_function_definition,
    "interface/macro": _add_macro_definition,
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


def _generate_directive(content: SphinxContent, mapper: _Mapper,
                        code_mapper: _CodeMapper, item: Item) -> None:
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
                    f"``{_sanitize_name(param['name'])}``",
                    mapper.substitute(f"This parameter {description}"),
                    wrap=True)
    if item["description"]:
        content.add(".. rubric:: DESCRIPTION:")
        content.wrap(mapper.substitute(item["description"]))
    ret = item["return"]
    if ret["return"] or ret["return-values"]:
        content.add(".. rubric:: RETURN VALUES:")
        if ret["return-values"]:
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
        for parent in item.parents("constraint")
    ]
    if constraints:
        content.add(".. rubric:: CONSTRAINTS:")
        content.add_list(constraints,
                         "The following constraints apply to this directive:")


def _generate_directives(target: str, group: Item, group_uids: List[str],
                         items: List[Item]) -> None:
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
            mapper = _Mapper(item, group_uids)
            content.add(f".. Generated from spec:{item.uid}")
            with content.directive("raw", "latex"):
                content.add("\\clearpage")
            directive = f"{name}()"
            content.add_index_entries([directive] + item["index-entries"])
            with content.section(directive, "Interface"):
                _generate_directive(content, mapper, code_mapper, item)
    content.add_licence_and_copyrights()
    content.write(target)


def _directive_key(order: List[Item], item: Item) -> Tuple[int, str]:
    try:
        index = order.index(item) - len(order)
    except ValueError:
        index = 1
    return (index, item.uid)


def generate(config: list, item_cache: ItemCache) -> None:
    """
    Generates interface documentation according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the interfaces.
    """
    group_uids = [doc_config["group"] for doc_config in config]
    for doc_config in config:
        items = []  # type: List[Item]
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
                             group_uids, items)
