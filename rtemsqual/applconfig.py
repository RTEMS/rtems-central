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

from rtemsqual.sphinxcontent import SphinxContent
from rtemsqual.items import Item, ItemCache

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
    def __init__(self, content: Any) -> None:
        self.content = content

    def add_group(self, name: str, description: str) -> None:
        """ Adds an option group. """
        self.content.add_header(name, level=2)
        self.content.add(description)

    def add_option(self, name: str, index_entries: List[str]) -> None:
        """ Adds an option. """
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
        self.content.add_definition_item("VALUE CONSTRAINTS:", lines)

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
    def __init__(self) -> None:
        super().__init__(SphinxContent())


def _generate_feature(content: _ContentAdaptor, item: Item,
                      option_type: str) -> None:
    content.add_option_default_config(
        _OPTION_DEFAULT_CONFIG[option_type](item))


def _generate_min_max(lines: List[str], value: str, word: str) -> None:
    lines.append("The value of this configuration option shall be "
                 f"{word} than or equal to {value}.")


def _generate_set(lines: List[str], values: List[Any]) -> None:
    value_set = "{" + ", ".join([str(x) for x in values]) + "}"
    lines.append("The value of this configuration option shall be")
    lines.append(f"an element of {value_set}.")


def _start_constraint_list(lines: List[str]) -> None:
    lines.append("The value of this configuration option shall "
                 "satisfy all of the following")
    lines.append("constraints:")


def _generate_item_min(lines: List[str], constraints: Dict[str, Any]) -> None:
    if "min" in constraints:
        value = constraints["min"]
        lines.append("")
        lines.append(f"* It shall be greater than or equal to {value}.")


def _generate_item_max(lines: List[str], constraints: Dict[str, Any]) -> None:
    if "max" in constraints:
        value = constraints["max"]
        lines.append("")
        lines.append(f"* It shall be less than or equal to {value}.")


def _generate_item_set(lines: List[str], constraints: Dict[str, Any]) -> None:
    if "set" in constraints:
        value_set = constraints["set"]
        lines.append("")
        lines.append(f"* It shall be an element of {value_set}.")


def _generate_item_texts(lines: List[str], constraints: Dict[str,
                                                             Any]) -> None:
    for text in constraints.get("texts", []):
        lines.append("")
        text = text.replace("The value of this configuration option", "It")
        text = text.strip().split("\n")
        lines.append(f"* {text[0]}")
        lines.extend([f"  {x}" if x else "" for x in text[1:]])


def _resolve_constraint_links(content: _ContentAdaptor, item: Item,
                              constraints: Dict[str, Any]) -> None:
    texts = []  # type: List[str]
    for parent in item.parents("constraint"):
        content.register_license_and_copyrights_of_item(parent)
        texts.append(parent["text"])
    if texts:
        constraints.setdefault("texts", []).extend(reversed(texts))


def _generate_constraint(content: _ContentAdaptor, item: Item) -> None:
    constraints = item["constraints"]
    _resolve_constraint_links(content, item, constraints)
    lines = []  # type: List[str]
    count = len(constraints)
    if count == 1:
        if "min" in constraints:
            _generate_min_max(lines, constraints["min"], "greater")
        elif "max" in constraints:
            _generate_min_max(lines, constraints["max"], "less")
        elif "set" in constraints:
            _generate_set(lines, constraints["set"])
        elif "texts" in constraints:
            if len(constraints["texts"]) == 1:
                lines.extend(constraints["texts"][0].strip().split("\n"))
            else:
                _start_constraint_list(lines)
                _generate_item_texts(lines, constraints)
    elif count == 2 and "min" in constraints and "max" in constraints:
        minimum = constraints["min"]
        maximum = constraints["max"]
        lines.append("The value of this configuration option shall be "
                     f"greater than or equal to {minimum}")
        lines.append(f"and less than or equal to {maximum}.")
    else:
        _start_constraint_list(lines)
        _generate_item_min(lines, constraints)
        _generate_item_max(lines, constraints)
        _generate_item_set(lines, constraints)
        _generate_item_texts(lines, constraints)
    content.add_option_value_constraints(lines)


def _generate_initializer_or_integer(content: _ContentAdaptor, item: Item,
                                     _option_type: str) -> None:
    default_value = item["default-value"]
    if not isinstance(default_value, str) or " " not in default_value:
        default_value = f"The default value is {default_value}."
    content.add_option_default_value(default_value)
    _generate_constraint(content, item)


_OPTION_GENERATORS = {
    "feature": _generate_feature,
    "feature-enable": _generate_feature,
    "initializer": _generate_initializer_or_integer,
    "integer": _generate_initializer_or_integer
}


def _generate(group: Item, options: ItemMap, content: _ContentAdaptor) -> None:
    content.register_license_and_copyrights_of_item(group)
    content.add_group(group["name"], group["description"])
    for item in sorted(options.values(), key=lambda x: x["name"]):
        name = item["name"]
        content.register_license_and_copyrights_of_item(item)
        content.add_option(name, item["index-entries"])
        option_type = item["appl-config-option-type"]
        content.add_option_type(_OPTION_TYPES[option_type])
        _OPTION_GENERATORS[option_type](content, item, option_type)
        content.add_option_description(item["description"])
        content.add_option_notes(item["notes"])
    content.add_licence_and_copyrights()


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates application configuration documentation sources according to the
    configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the application
                       configuration groups and options.
    """
    for group_config in config["groups"]:
        group = item_cache[group_config["uid"]]
        assert group.type == "interface/appl-config-group"
        options = {}  # type: ItemMap
        for child in group.children("appl-config-group-member"):
            assert child.type.startswith("interface/appl-config-option")
            options[child.uid] = child
        sphinx_content = _SphinxContentAdaptor()
        _generate(group, options, sphinx_content)
        sphinx_content.write(group_config["target"])
