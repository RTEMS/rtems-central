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

import os
from typing import Any, Callable, Dict, List, Optional

from rtemsqual.content import CContent, enabled_by_to_exp, ExpressionMapper
from rtemsqual.sphinxcontent import get_label, get_reference, SphinxContent
from rtemsqual.items import Item, ItemCache, ItemMapper

ItemMap = Dict[str, Item]
AddDefinition = Callable[[CContent, ItemMapper, Item, Dict[str, Any]], None]

INTERFACE = "Interface"


def _forward_declaration(item: Item) -> str:
    target = next(item.parents("interface-target"))
    return f"{target['interface-type']} {target['name']}"


def _get_reference(name: str) -> str:
    return get_reference(get_label(f"{INTERFACE}{name}"), f"{name}()")


class _CodeMapper(ItemMapper):
    def get_value(self, item: Item, path: str, _value: Any, key: str,
                  _index: Optional[int]) -> Any:
        # pylint: disable=duplicate-code
        if path == "/" and key == "name" and item["type"] == "interface":
            interface_type = item["interface-type"]
            if interface_type == "forward-declaration":
                return _forward_declaration(item)
        raise KeyError


class _Mapper(_CodeMapper):
    def get_value(self, item: Item, path: str, value: Any, key: str,
                  index: Optional[int]) -> Any:
        # pylint: disable=too-many-arguments
        try:
            return super().get_value(item, path, value, key, index)
        except KeyError:
            if path == "/" and key == "name" and item["type"] == "interface":
                value = value[key]
                interface_type = item["interface-type"]
                if interface_type == "function":
                    return _get_reference(value)
                if interface_type == "appl-config-option":
                    return f":ref:`{value}`"
                return value
        raise KeyError


def _generate_introduction(target: str, group: Item,
                           items: List[Item]) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    group_name = group["name"]
    with content.section("Introduction", get_label(group_name)):
        content.append("")
        content.gap = False
        content.wrap(group["brief"])
        content.wrap(group["description"])
        content.paste(f"The directives provided by the {group_name} are:")
        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            brief = item["brief"]
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
    name = item["name"]
    ret = mapper.substitute(value["return"])
    params = [mapper.substitute(param) for param in value["params"]]
    content.declare_function(ret, name, params)


def _add_definition(content: CContent, mapper: ItemMapper, item: Item,
                    prefix: str, value: Dict[str, Any],
                    add_definition: AddDefinition) -> None:
    # pylint: disable=too-many-arguments
    assert item["interface-type"] == "function"
    default = value["default"]
    variants = value["variants"]
    if variants:
        ifelse = "#if "
        with mapper.prefix(os.path.join(prefix, "variants")):
            for variant in variants:
                enabled_by = enabled_by_to_exp(variant["enabled-by"],
                                               ExpressionMapper())
                content.append(f"{ifelse}{enabled_by}")
                with content.indent():
                    add_definition(content, mapper, item,
                                   variant["definition"])
                ifelse = "#elif "
        if default is not None:
            content.append("#else")
            with mapper.prefix(os.path.join(prefix, "default")):
                with content.indent():
                    add_definition(content, mapper, item, default)
        content.append("#endif")
    else:
        with mapper.prefix(os.path.join(prefix, "default")):
            add_definition(content, mapper, item, default)


def _generate_directives(target: str, group: Item, items: List[Item]) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    group_name = group["name"]
    with content.section("Directives", get_label(group_name)):
        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            code_mapper = _CodeMapper(item)
            mapper = _Mapper(item)
            with content.section(f"{name}()", "Interface"):
                content.wrap(item["brief"])
                with content.definition_item("CALLING SEQUENCE:"):
                    with content.directive("code-block", "c"):
                        code = CContent()
                        _add_definition(code, code_mapper, item, "definition",
                                        item["definition"],
                                        _add_function_definition)
                        content.add(code)
                if item["params"]:
                    with content.definition_item("DIRECTIVE PARAMETERS:"):
                        for param in item["params"]:
                            content.add_definition_item(
                                mapper.substitute(param["name"]),
                                mapper.substitute(
                                    f"This parameter {param['description']}"),
                                wrap=True)
                ret = item["return"]
                if ret["return"] or ret["return-values"]:
                    with content.definition_item("DIRECTIVE RETURN VALUES:"):
                        if ret["return-values"]:
                            for retval in ret["return-values"]:
                                content.add_definition_item(
                                    mapper.substitute(str(retval["value"])),
                                    mapper.substitute(retval["description"]),
                                    wrap=True)
                        content.wrap(mapper.substitute(ret["return"]))
                content.add_definition_item("DESCRIPTION:",
                                            mapper.substitute(
                                                item["description"]),
                                            wrap=True)
                content.add_definition_item("NOTES:",
                                            mapper.substitute(item["notes"]),
                                            wrap=True)
    content.add_licence_and_copyrights()
    content.write(target)


def generate(config: list, item_cache: ItemCache) -> None:
    """
    Generates interface documentation according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the interfaces.
    """
    for doc_config in config:
        items = []  # type: List[Item]
        group = item_cache[doc_config["group"]]
        assert group["type"] == "interface"
        assert group["interface-type"] == "group"
        for child in group.children("interface-ingroup"):
            if child["interface-type"] in ["function"]:
                items.append(child)
        items.sort(key=lambda x: x["name"])
        _generate_introduction(doc_config["introduction-target"], group, items)
        _generate_directives(doc_config["directives-target"], group, items)
