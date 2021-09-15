# SPDX-License-Identifier: BSD-2-Clause
""" Functions for application configuration documentation generation. """

# Copyright (C) 2019, 2020 embedded brains GmbH (http://www.embedded-brains.de)
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

from typing import Any, Dict, List, Optional

from rtemsspec.content import Content, CContent, get_value_double_colon, \
    get_value_doxygen_function, get_value_doxygen_group, get_value_hash
from rtemsspec.sphinxcontent import SphinxContent, SphinxInterfaceMapper
from rtemsspec.items import EmptyItem, Item, ItemCache, ItemGetValueContext, \
    ItemMapper

ItemMap = Dict[str, Item]

_FEATURE = "This configuration option is a boolean feature define."

_OPTION_TYPES = {
    "feature": _FEATURE,
    "feature-enable": _FEATURE,
    "integer": "This configuration option is an integer define.",
    "initializer": "This configuration option is an initializer define."
}

_OPTION_DEFAULT_CONFIG = {
    "feature":
    lambda item: item["default"],
    "feature-enable":
    lambda item:
    """If this configuration option is undefined, then the described feature is not
enabled."""
}


class _ContentAdaptor:
    """
    The content adaptor provides a specialized interface to a content class.

    By default, Sphinx content is generated.
    """
    def __init__(self, mapper: ItemMapper, content: Any) -> None:
        self.mapper = mapper
        self.content = content

    def substitute(self, text: Optional[str]) -> str:
        """ Substitutes the optional text using the item mapper. """
        return self.mapper.substitute(text)

    def add_group(self, uid: str, name: str, description: str) -> None:
        """ Adds an option group. """
        self.content.add_automatically_generated_warning()
        self.content.add(f".. Generated from spec:{uid}")
        self.content.add_header(name, level=2)
        self.content.add(description)

    def add_option(self, uid: str, name: str,
                   index_entries: List[str]) -> None:
        """ Adds an option. """
        self.content.add(f".. Generated from spec:{uid}")
        self.content.add_index_entries([name] + index_entries)
        self.content.add_label(name)
        self.content.add_header(name, level=3)
        self.content.add_definition_item("CONSTANT:", f"``{name}``")

    def add_option_type(self, option_type: str) -> None:
        """ Adds an option type. """
        self.content.add_definition_item("OPTION TYPE:", option_type)

    def add_option_default_value(self, value: str) -> None:
        """ Adds an option default value. """
        self.content.add_definition_item("DEFAULT VALUE:", value)

    def add_option_default_config(self, config: str) -> None:
        """ Adds an option default configuration. """
        self.content.add_definition_item("DEFAULT CONFIGURATION:", config)

    def add_option_value_constraints(self, lines: List[str]) -> None:
        """ Adds a option value constraints. """
        self.content.add_definition_item("VALUE CONSTRAINTS:",
                                         lines,
                                         wrap=True)

    def add_option_description(self, description: str) -> None:
        """ Adds a option description. """
        self.content.add_definition_item("DESCRIPTION:", description)

    def add_option_notes(self, notes: Optional[str]) -> None:
        """ Adds option notes. """
        if not notes:
            notes = "None."
        self.content.add_definition_item("NOTES:", notes)

    def add_licence_and_copyrights(self) -> None:
        """ Adds the license and copyrights. """
        self.content.add_licence_and_copyrights()

    def register_license_and_copyrights_of_item(self, item: Item) -> None:
        """ Registers the license and copyrights of the item. """
        self.content.register_license_and_copyrights_of_item(item)

    def write(self, filename: str):
        """ Writes the content to the file specified by the path. """
        self.content.write(filename)


class _SphinxContentAdaptor(_ContentAdaptor):
    def __init__(self, mapper: ItemMapper) -> None:
        super().__init__(mapper, SphinxContent())


class _DoxygenContentAdaptor(_ContentAdaptor):
    # pylint: disable=attribute-defined-outside-init

    def __init__(self, mapper: ItemMapper) -> None:
        super().__init__(mapper, CContent())
        self._reset()

    def _reset(self) -> None:
        self._name = ""
        self._option_type = ""
        self._default_value = ""
        self._default_config = ""
        self._value_constraints = []  # type: List[str]
        self._description = ""

    def add_group(self, uid: str, name: str, description: str) -> None:
        identifier = f"RTEMSApplConfig{name.replace(' ', '')}"
        self.content.add(f"/* Generated from spec:{uid} */")
        with self.content.defgroup_block(identifier, name):
            self.content.add("@ingroup RTEMSApplConfig")
            self.content.doxyfy(description)
            self.content.add("@{")

    def add_option(self, uid: str, name: str,
                   _index_entries: List[str]) -> None:
        self.content.add(f"/* Generated from spec:{uid} */")
        self.content.open_doxygen_block()
        self._name = name

    def add_option_type(self, option_type: str) -> None:
        self._option_type = option_type

    def add_option_default_value(self, value: str) -> None:
        self._default_value = value

    def add_option_default_config(self, config: str) -> None:
        self._default_config = config

    def add_option_value_constraints(self, lines: List[str]) -> None:
        self._value_constraints = lines

    def add_option_description(self, description: str) -> None:
        self._description = description

    def add_option_notes(self, notes: Optional[str]) -> None:
        self.content.add_brief_description(self._option_type)
        self.content.doxyfy(self._description)
        self.content.add_paragraph("Default Value", self._default_value)
        self.content.add_paragraph("Default Configuration",
                                   self._default_config)
        self.content.add_paragraph("Value Constraints",
                                   self._value_constraints)
        self.content.add_paragraph("Notes", notes)
        self.content.close_comment_block()
        self.content.append(f"#define {self._name}")
        self._reset()

    def add_licence_and_copyrights(self) -> None:
        self.content.add("/** @} */")


def _generate_feature(content: _ContentAdaptor, item: Item,
                      option_type: str) -> None:
    content.add_option_default_config(
        content.substitute(_OPTION_DEFAULT_CONFIG[option_type](item)))


def _get_constraints(content: _ContentAdaptor, item: Item) -> List[str]:
    constraints = []  # type: List[str]
    for parent in item.parents("constraint"):
        content.register_license_and_copyrights_of_item(parent)
        constraints.append(content.substitute(parent["text"]))
    return constraints


_THE_VALUE = "The value of the application configuration option"


def _generate_constraint(content: _ContentAdaptor, item: Item) -> None:
    constraints = _get_constraints(content, item)
    if len(constraints) > 1:
        constraint_list = Content("BSD-2-Clause", False)
        prologue = """The value of this configuration option shall satisfy all
of the following constraints:"""
        constraint_list.add_list([
            constraint.replace(_THE_VALUE, "It") for constraint in constraints
        ], prologue)
        constraints = constraint_list.lines
    elif constraints:
        constraints[0] = constraints[0].replace(
            _THE_VALUE, "The value of this configuration option")
    content.add_option_value_constraints(constraints)


def _generate_initializer_or_integer(content: _ContentAdaptor, item: Item,
                                     _option_type: str) -> None:
    default_value = item["default-value"]
    if not isinstance(default_value, str) or " " not in default_value:
        default_value = f"The default value is {default_value}."
    content.add_option_default_value(content.substitute(default_value))
    _generate_constraint(content, item)


_OPTION_GENERATORS = {
    "feature": _generate_feature,
    "feature-enable": _generate_feature,
    "initializer": _generate_initializer_or_integer,
    "integer": _generate_initializer_or_integer
}


def _generate(group: Item, options: ItemMap, content: _ContentAdaptor) -> None:
    content.register_license_and_copyrights_of_item(group)
    content.add_group(group.uid, group["name"],
                      content.substitute(group["description"]))
    for item in sorted(options.values(), key=lambda x: x["name"]):
        content.mapper.item = item
        name = item["name"]
        content.register_license_and_copyrights_of_item(item)
        content.add_option(item.uid, name, item["index-entries"])
        option_type = item["appl-config-option-type"]
        content.add_option_type(_OPTION_TYPES[option_type])
        _OPTION_GENERATORS[option_type](content, item, option_type)
        content.add_option_description(content.substitute(item["description"]))
        content.add_option_notes(content.substitute(item["notes"]))
    content.add_licence_and_copyrights()


def _get_value_doxygen_url(ctx: ItemGetValueContext) -> Optional[str]:
    for ref in ctx.item["references"]:
        if ref["type"] == "url":
            return f"<a href=\"{ref['identifier']}\">{ctx.value[ctx.key]}</a>"
    return None


def _get_value_doxygen_unspecified_define(ctx: ItemGetValueContext) -> Any:
    return _get_value_doxygen_url(ctx) or get_value_hash(ctx)


def _get_value_doxygen_unspecified_group(ctx: ItemGetValueContext) -> Any:
    return _get_value_doxygen_url(ctx) or ctx.value[ctx.key]


def _get_value_doxygen_unspecfied_type(ctx: ItemGetValueContext) -> Any:
    return _get_value_doxygen_url(ctx) or get_value_double_colon(ctx)


def _add_doxygen_get_values(mapper: ItemMapper) -> None:
    for opt in ["feature-enable", "feature", "initializer", "integer"]:
        name = f"interface/appl-config-option/{opt}:/name"
        mapper.add_get_value(name, get_value_hash)
    mapper.add_get_value("interface/define:/name", get_value_hash)
    mapper.add_get_value("interface/function:/name",
                         get_value_doxygen_function)
    mapper.add_get_value("interface/group:/name", get_value_doxygen_group)
    mapper.add_get_value("interface/macro:/name", get_value_doxygen_function)
    mapper.add_get_value("interface/struct:/name", get_value_double_colon)
    mapper.add_get_value("interface/typedef:/name", get_value_double_colon)
    mapper.add_get_value("interface/union:/name", get_value_double_colon)
    mapper.add_get_value("interface/unspecified-define:/name",
                         _get_value_doxygen_unspecified_define)
    mapper.add_get_value("interface/unspecified-function:/name",
                         get_value_doxygen_function)
    mapper.add_get_value("interface/unspecified-group:/name",
                         _get_value_doxygen_unspecified_group)
    mapper.add_get_value("interface/unspecified-type:/name",
                         _get_value_doxygen_unspecfied_type)


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates application configuration documentation sources according to the
    configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the application
                       configuration groups and options.
    """
    sphinx_mapper = SphinxInterfaceMapper(EmptyItem())
    doxygen_mapper = ItemMapper(EmptyItem())
    _add_doxygen_get_values(doxygen_mapper)
    doxygen_content = _DoxygenContentAdaptor(doxygen_mapper)
    doxygen_content.content.add_automatically_generated_warning()
    with doxygen_content.content.defgroup_block(
            "RTEMSApplConfig", "Application Configuration Options"):
        doxygen_content.content.add("@ingroup RTEMSAPI")
    for group_config in config["groups"]:
        group = item_cache[group_config["uid"]]
        assert group.type == "interface/appl-config-group"
        options = {}  # type: ItemMap
        for child in group.children("appl-config-group-member"):
            assert child.type.startswith("interface/appl-config-option")
            options[child.uid] = child
        sphinx_content = _SphinxContentAdaptor(sphinx_mapper)
        _generate(group, options, sphinx_content)
        sphinx_content.write(group_config["target"])
        _generate(group, options, doxygen_content)
    doxygen_content.content.prepend_copyrights_and_licenses()
    doxygen_content.content.prepend_spdx_license_identifier()
    doxygen_content.write(config["doxygen-target"])
