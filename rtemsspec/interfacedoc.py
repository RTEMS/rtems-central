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
from typing import Any, Dict, List, Optional, Tuple

from rtemsspec.content import CContent, get_value_compound, \
    get_value_forward_declaration, get_value_unspecified_type
from rtemsspec.sphinxcontent import make_label, get_reference, sanitize_name, \
    SphinxContent, SphinxInterfaceMapper
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]


def _get_reference(name: str) -> str:
    return get_reference(make_label(f"Interface {name}"))


def _get_code_param(ctx: ItemGetValueContext) -> Any:
    return sanitize_name(ctx.value[ctx.key])


class CodeMapper(ItemMapper):
    """ Item mapper for code blocks. """

    def __init__(self, item: Item):
        super().__init__(item)
        self.add_get_value("interface/forward-declaration:/name",
                           get_value_forward_declaration)
        self.add_get_value("interface/struct:/name", get_value_compound)
        self.add_get_value("interface/union:/name", get_value_compound)
        self.add_get_value("interface/macro:/params/name", _get_code_param)
        self.add_get_value("interface/unspecified-struct:/name",
                           get_value_unspecified_type)
        self.add_get_value("interface/unspecified-unione:/name",
                           get_value_unspecified_type)


def _generate_introduction(target: str, group: Item, group_uids: List[str],
                           items: List[Item]) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    content.add_automatically_generated_warning()
    content.add(f".. Generated from spec:{group.uid}")
    group_name = group["name"]
    content.push_label(make_label(group_name))
    with content.section("Introduction"):
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


def _add_text(content: SphinxContent, mapper: ItemMapper, item: Item,
              key: str) -> None:
    text = item[key]
    if text:
        content.add(f".. rubric:: {key.upper()}:")
        content.wrap(mapper.substitute(text))


def _document_directive(content: SphinxContent, mapper: ItemMapper,
                        code_mapper: CodeMapper, item: Item,
                        enabled: List[str]) -> None:
    content.wrap(mapper.substitute(item["brief"]))
    content.add_rubric("CALLING SEQUENCE:")
    with content.directive("code-block", "c"):
        code = CContent()
        _add_definition(code, code_mapper, item, "definition",
                        item["definition"])
        content.add(code)
    if item["params"]:
        content.add_rubric("PARAMETERS:")
        for param in item["params"]:
            description = param["description"]
            if description:
                content.add_definition_item(
                    f"``{sanitize_name(param['name'])}``",
                    mapper.substitute(f"This parameter {description}"),
                    wrap=True)
    _add_text(content, mapper, item, "description")
    ret = item["return"]
    if ret:
        content.add_rubric("RETURN VALUES:")
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
    _add_text(content, mapper, item, "notes")
    constraints = [
        mapper.substitute(parent["text"], parent)
        for parent in item.parents("constraint") if parent.is_enabled(enabled)
    ]
    if constraints:
        content.add_rubric("CONSTRAINTS:")
        content.add_list(constraints,
                         "The following constraints apply to this directive:")


def document_directive(item: Item, enabled: List[str],
                       mapper: ItemMapper) -> SphinxContent:
    """
    Documents the directive specified by the item using the item mapper and
    enabled set.
    """
    content = SphinxContent()
    _document_directive(content, mapper, CodeMapper(item), item, enabled)
    return content


def _generate_directives(target: str, group: Item, group_uids: List[str],
                         items: List[Item], enabled: List[str]) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    content.add_automatically_generated_warning()
    group_name = group["name"]
    content.push_label(make_label(group_name))
    with content.section("Directives"):
        content.wrap([
            f"This section details the directives of the {group_name}.",
            "A subsection is dedicated to each of this manager's directives",
            "and lists the calling sequence, parameters, description,",
            "return values, and notes of the directive."
        ])
        for item in items:
            content.register_license_and_copyrights_of_item(item)
            name = item["name"]
            code_mapper = CodeMapper(item)
            mapper = SphinxInterfaceMapper(item, group_uids)
            content.add(f".. Generated from spec:{item.uid}")
            with content.directive("raw", "latex"):
                content.add("\\clearpage")
            directive = f"{name}()"
            content.add_index_entries([directive] + item["index-entries"])
            with content.section(directive,
                                 label=make_label(f"Interface {directive}")):
                _document_directive(content, mapper, code_mapper, item,
                                    enabled)
    content.add_licence_and_copyrights()
    content.write(target)


def _directive_key(order: List[Item], item: Item) -> Tuple[int, str]:
    try:
        index = order.index(item) - len(order)
    except ValueError:
        index = 1
    return (index, item.uid)


def _add_type_definition(definition: Any, mapper: SphinxInterfaceMapper,
                         content: SphinxContent) -> None:
    text = definition["brief"].strip()
    if definition["description"]:
        text += "\n" + definition["description"].strip()
    content.add_definition_item(definition["name"],
                                mapper.substitute(text),
                                wrap=True)


def _type_compound(item: Item, mapper: SphinxInterfaceMapper,
                   content: SphinxContent) -> None:
    content.add(".. rubric:: MEMBERS:")
    for member in item["definition"]:
        _add_type_definition(member["default"], mapper, content)


def _type_enum(item: Item, mapper: SphinxInterfaceMapper,
               content: SphinxContent) -> None:
    content.add(".. rubric:: ENUMERATORS:")
    for enumerator in item.parents("interface-enumerator"):
        _add_type_definition(enumerator, mapper, content)


def _type_nop(_item: Item, _mapper: SphinxInterfaceMapper,
              _content: SphinxContent) -> None:
    pass


_TYPE_GENERATORS = {
    "interface/enum": _type_enum,
    "interface/struct": _type_compound,
    "interface/typedef": _type_nop,
    "interface/union": _type_compound
}


def _gather_types(item: Item, types: List[Item]) -> None:
    for child in item.children("interface-placement"):
        if child.type in _TYPE_GENERATORS:
            types.append(child)
        _gather_types(child, types)


def _is_opaque_type(item: Item) -> Optional[Item]:
    for constraint in item.parents("constraint"):
        if constraint.uid == "/constraint/type-opaque":
            return constraint
    return None


def _generate_types(config: dict, group_uids: List[str],
                    item_cache: ItemCache) -> None:
    types: List[Item] = []
    for domain in config["domains"]:
        _gather_types(item_cache[domain], types)
    content = SphinxContent()
    content.add_automatically_generated_warning()
    content.add_index_entries(["RTEMS Data Types", "data types"])
    content.add_header("RTEMS Data Types", level=1)
    with content.section("Introduction"):
        content.wrap("""This chapter contains a complete list of the RTEMS
primitive data types in alphabetical order.  This is intended to be an overview
and the user is encouraged to look at the appropriate chapters in the manual
for more information about the usage of the various data types.""")

    with content.section("List of Data Types"):
        content.wrap(
            "The following is a complete list of the RTEMS primitive data "
            "types in alphabetical order:")
        for item in sorted(types, key=lambda x: x["name"]):
            content.register_license_and_copyrights_of_item(item)
            content.add(f".. Generated from spec:{item.uid}")
            name = item["name"]
            content.add_index_entries([name] + item["index-entries"])
            with content.section(name, label=make_label(f"Interface {name}")):
                mapper = SphinxInterfaceMapper(item, group_uids)
                content.wrap(mapper.substitute(item["brief"]))
                constraint = _is_opaque_type(item)
                if constraint is None:
                    _TYPE_GENERATORS[item.type](item, mapper, content)
                else:
                    content.add(".. rubric:: MEMBERS:")
                    content.wrap(mapper.substitute(constraint["text"]))
                _add_text(content, mapper, item, "description")
                _add_text(content, mapper, item, "notes")
    content.add_licence_and_copyrights()
    content.write(config["target"])


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates interface documentation according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the interfaces.
    """
    groups = config["groups"]
    enabled = config["enabled"]
    group_uids = [doc_config["group"] for doc_config in groups]
    group_uids.extend(uid for uid in config["types"]["groups"])
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
    _generate_types(config["types"], group_uids, item_cache)
