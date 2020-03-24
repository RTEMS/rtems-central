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

from typing import Dict

from rtemsqual.content import SphinxContent
from rtemsqual.items import Item, ItemCache

ItemMap = Dict[str, Item]


def _gather_groups(item: Item, groups: ItemMap) -> None:
    for child in item.children:
        _gather_groups(child, groups)
    if item["type"] == "interface" and item[
            "interface-type"] == "appl-config-group":
        groups[item.uid] = item


def _gather_options(item: Item, options: ItemMap) -> None:
    for child in item.children:
        _gather_options(child, options)
    if item["type"] == "interface" and item[
            "interface-type"] == "appl-config-option":
        options[item.uid] = item


_FEATURE = "This configuration option is a boolean feature define."

_OPTION_TYPES = {"feature": _FEATURE, "feature-enable": _FEATURE}

_OPTION_DEFAULTS = {
    "feature":
    lambda item: item["appl-config-option-default"],
    "feature-enable":
    lambda item:
    """If this configuration option is undefined, then the described feature is not
enabled."""
}


def _generate_content(group: Item, options: ItemMap) -> SphinxContent:
    content = SphinxContent()
    group.register_license_and_copyrights(content)
    content.add_header(group["appl-config-group-name"], level="=")
    content.add_blank_line()
    content.add_lines(group["appl-config-group-description"])
    for item in sorted(options.values(), key=lambda x: x.uid):
        name = item["appl-config-option-name"]
        item.register_license_and_copyrights(content)
        content.add_index_entries([name] + item["appl-config-option-index"])
        content.add_blank_line()
        content.add_label(name)
        content.add_blank_line()
        content.add_header(name, level="-")
        content.add_definition_item("CONSTANT:", f"``{name}``")
        if "appl-config-option-type" in item:
            option_type = item["appl-config-option-type"]
            content.add_definition_item("OPTION TYPE:",
                                        _OPTION_TYPES[option_type])
            content.add_definition_item("DEFAULT CONFIGURATION:",
                                        _OPTION_DEFAULTS[option_type](item))
        else:
            content.add_definition_item("DATA TYPE:",
                                        item["appl-config-option-data-type"])
            content.add_definition_item("RANGE:",
                                        item["appl-config-option-range"])
            content.add_definition_item(
                "DEFAULT VALUE:", item["appl-config-option-default-value"])
        content.add_definition_item("DESCRIPTION:",
                                    item["appl-config-option-description"])
        content.add_definition_item("NOTES:", item["appl-config-option-notes"])
    content.add_licence_and_copyrights()
    return content


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
        content = _generate_content(group, options)
        content.write(group_config["target"])
