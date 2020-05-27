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


def _gather_groups(item: Item, groups: ItemMap) -> None:
    for child in item.children():
        _gather_groups(child, groups)
    if item["type"] == "interface" and item[
            "interface-type"] == "appl-config-group":
        groups[item.uid] = item


def _gather_options(item: Item, options: ItemMap) -> None:
    for child in item.children():
        _gather_options(child, options)
    if item["type"] == "interface" and item[
            "interface-type"] == "appl-config-option":
        options[item.uid] = item


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


def _generate_feature(content: SphinxContent, item: Item,
                      option_type: str) -> None:
    content.add_definition_item("DEFAULT CONFIGURATION:",
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


def _resolve_constraint_links(content: SphinxContent, item: Item,
                              constraints: Dict[str, Any]) -> None:
    texts = []  # type: List[str]
    for link in item.links_to_parents():
        if link.role == "constraint":
            content.register_license_and_copyrights_of_item(link.item)
            texts.append(link.item["text"])
    if texts:
        constraints.setdefault("texts", []).extend(reversed(texts))


def _generate_constraint(content: SphinxContent, item: Item) -> None:
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
    content.add_definition_item("VALUE CONSTRAINTS:", lines)


def _generate_initializer_or_integer(content: SphinxContent, item: Item,
                                     _option_type: str) -> None:
    default_value = item["default-value"]
    if not isinstance(default_value, str) or " " not in default_value:
        default_value = f"The default value is {default_value}."
    content.add_definition_item("DEFAULT VALUE:", default_value)
    _generate_constraint(content, item)


_OPTION_GENERATORS = {
    "feature": _generate_feature,
    "feature-enable": _generate_feature,
    "initializer": _generate_initializer_or_integer,
    "integer": _generate_initializer_or_integer
}


def _generate_notes(content: SphinxContent, notes: Optional[str]) -> None:
    if not notes:
        notes = "None."
    content.add_definition_item("NOTES:", notes)


def _generate_file(group: Item, options: ItemMap, target: str) -> None:
    content = SphinxContent()
    content.register_license_and_copyrights_of_item(group)
    content.add_header(group["name"], level=2)
    content.add(group["description"])
    for item in sorted(options.values(), key=lambda x: x.uid):
        name = item["name"]
        content.register_license_and_copyrights_of_item(item)
        content.add_index_entries([name] + item["index-entries"])
        content.add_label(name)
        content.add_header(name, level=3)
        content.add_definition_item("CONSTANT:", f"``{name}``")
        option_type = item["appl-config-option-type"]
        content.add_definition_item("OPTION TYPE:", _OPTION_TYPES[option_type])
        _OPTION_GENERATORS[option_type](content, item, option_type)
        content.add_definition_item("DESCRIPTION:", item["description"])
        _generate_notes(content, item["notes"])
    content.add_licence_and_copyrights()
    content.write(target)


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates application configuration documentation sources according to the
    configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the application
                       configuration groups and options.
    """
    groups = {}  # type: ItemMap
    for item in item_cache.top_level.values():
        _gather_groups(item, groups)

    for group_config in config["groups"]:
        group = groups[group_config["uid"]]
        options = {}  # type: ItemMap
        _gather_options(group, options)
        _generate_file(group, options, group_config["target"])
