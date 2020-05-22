# SPDX-License-Identifier: BSD-2-Clause
""" This module provides functions to document specification items. """

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

from typing import Any, Dict, Iterator, Optional, Set, Tuple

from rtemsqual.content import SphinxContent
from rtemsqual.items import Item, ItemCache
from rtemsqual.specverify import NAME

_DocumenterMap = Dict[str, "_Documenter"]

_PRIMITIVE_TYPES = {
    "bool": "{} {} be a boolean.",
    "float": "{} {} be a floating-point number.",
    "int": "{} {} be an integer number.",
    "list-str": "{} {} be a list of strings.",
    "none": "The attribute shall have no value.",
    "optional-str": "{} {} be an optional string.",
    "str": "{} {} be a string.",
}

_REQUIRED_ATTRIBUTES = {
    "all": "All explicitly defined attributes shall be specified.",
    "at-least-one":
    "At least one of the explicitly defined attributes shall be specified.",
    "at-most-one":
    "At most one of the explicitly defined attributes shall be specified.",
    "exactly-one":
    "Exactly one of the explicitly defined attributes shall be specified.",
    "none": "None of the explicitly defined attributes are required.",
}

_SECTION_PREFIX = "SpecType"


def _a_or_an(value: str) -> str:
    if value[0].lower() in ["a", "e", "i", "o", "u"]:
        return "an"
    return "a"


class _Documenter:
    def __init__(self, item: Item, documenter_map: _DocumenterMap):
        self._name = item["spec-type"]
        self.section = item["spec-name"]
        self._description = item["spec-description"]
        self._info_map = item["spec-info"]
        self._item = item
        self._documenter_map = documenter_map
        self.used_by = set()  # type: Set[str]
        assert self._name not in documenter_map
        documenter_map[self._name] = self

    def get_section_reference(self, content: SphinxContent) -> str:
        """ Returns the section reference. """
        return content.get_reference(
            content.get_section_label(self.section, _SECTION_PREFIX))

    def get_a_section_reference(self, content: SphinxContent) -> str:
        """ Returns a section reference. """
        return _a_or_an(
            self.section) + " " + self.get_section_reference(content)

    def get_list_element_type(self) -> str:
        """ Returns the list element type if this is a list only type. """
        if len(self._info_map) == 1 and "list" in self._info_map:
            return self._info_map["list"]["spec-type"]
        return ""

    def get_list_phrase(self, content: SphinxContent, value: str, shall: str,
                        type_name: str) -> str:
        """ Returns a list phrase. """
        if type_name in _PRIMITIVE_TYPES:
            type_phrase = _PRIMITIVE_TYPES[type_name].format(
                "Each list element", shall)
        else:
            documenter = self._documenter_map[type_name]
            ref = documenter.get_a_section_reference(content)
            type_phrase = f"Each list element shall be {ref}."
        return f"{value} {shall} be a list. {type_phrase}"

    def get_value_type_phrase(self, content: SphinxContent, value: str,
                              shall: str, type_name: str) -> str:
        """ Returns a value type phrase. """
        if type_name in _PRIMITIVE_TYPES:
            return _PRIMITIVE_TYPES[type_name].format(value, shall)
        documenter = self._documenter_map[type_name]
        element_type_name = documenter.get_list_element_type()
        if element_type_name:
            return self.get_list_phrase(content, value, shall,
                                        element_type_name)
        return (f"{value} {shall} be "
                f"{documenter.get_a_section_reference(content)}.")

    def refinements(self) -> Iterator["_Documenter"]:
        """ Yields the refinements of this type. """
        refinements = set(self._documenter_map[link.item["spec-type"]]
                          for link in self._item.links_to_children()
                          if link.role == "spec-refinement")
        yield from sorted(refinements, key=lambda x: x.section)

    def refines(self) -> Iterator[Tuple["_Documenter", str, str]]:
        """ Yields the types refined by type. """
        refines = [(self._documenter_map[link.item["spec-type"]],
                    link["spec-key"], link["spec-value"])
                   for link in self._item.links_to_parents()
                   if link.role == "spec-refinement"]
        yield from sorted(refines, key=lambda x: x[0].section)

    def hierarchy(self, content: SphinxContent) -> None:
        """ Documents the item type hierarchy. """
        with content.list_item(self.get_section_reference(content)):
            for refinement in self.refinements():
                refinement.hierarchy(content)

    def _document_attributes(self, content: SphinxContent,
                             attributes: Any) -> None:
        for key, info in attributes.items():
            content.add(key)
            with content.indent():
                content.wrap(
                    self.get_value_type_phrase(content, "The attribute value",
                                               "shall", info["spec-type"]))
                content.paste(info["description"])

    def document_dict(self, content: SphinxContent, _variant: str, shall: str,
                      info: Any) -> None:
        """ Documents an attribute set. """
        if shall == "may":
            content.paste("The value may be a set of attributes.")
        content.paste(info["description"])
        has_explicit_attributes = len(info["attributes"]) > 0
        if has_explicit_attributes:
            required_attributes = info["required-attributes"]
            if isinstance(required_attributes, str):
                content.paste(_REQUIRED_ATTRIBUTES[required_attributes])
            else:
                assert isinstance(required_attributes, list)
                required_attribute_count = len(required_attributes)
                if required_attribute_count == 1:
                    content.paste(f"Only the ``{required_attributes[0]}`` "
                                  "attribute is required.")
                elif required_attribute_count > 1:
                    content.paste("The following explicitly defined "
                                  "attributes are required:")
                    for attribute in sorted(required_attributes):
                        content.add_list_item(f"``{attribute}``")
                    content.add_blank_line()
                else:
                    content.add_blank_line()
            content.paste("The following attributes are explicitly "
                          "defined for this type:")
            self._document_attributes(content, info["attributes"])
        if "generic-attributes" in info:
            if has_explicit_attributes:
                content.wrap(
                    "In addition to the explicitly defined "
                    "attributes above, generic attributes may be defined.")
            else:
                content.paste("Generic attributes may be defined.")
            content.paste("Each attribute key shall be a :ref:`SpecTypeName`.")
            type_phrase = self.get_value_type_phrase(
                content, "The attribute value", "shall",
                info["generic-attributes"]["spec-type"])
            content.paste(type_phrase)
            content.paste(info["generic-attributes"]["description"])

    def document_value(self, content: SphinxContent, variant: str, shall: str,
                       info: Any) -> None:
        """ Documents a value. """
        content.paste(
            self.get_value_type_phrase(content, "The value", shall, variant))
        content.paste(info["description"])

    def document_list(self, content: SphinxContent, _variant: str, shall: str,
                      info: Any) -> None:
        """ Documents a list value. """
        content.paste(
            self.get_list_phrase(content, "The value", shall,
                                 info["spec-type"]))
        content.paste(info["description"])

    def document_none(self, content: SphinxContent, _variant: str, shall: str,
                      _info: Any) -> None:
        """ Documents a none value. """
        # pylint: disable=no-self-use
        content.paste(f"There {shall} by be no value (null).")

    def _add_description(self, content: SphinxContent) -> None:
        refines = [
            f"{documenter.get_section_reference(content)} though the "
            f"``{key}`` attribute if the value is ``{value}``"
            for documenter, key, value in self.refines()
        ]
        if len(refines) == 1:
            content.wrap(f"This type refines the {refines[0]}.")
            content.paste(self._description)
        else:
            content.add_list(refines,
                             "This type refines the following types:",
                             add_blank_line=True)
            content.wrap(self._description)

    def document(self,
                 content: SphinxContent,
                 names: Optional[Set[str]] = None) -> None:
        """ Document this type. """
        if self.get_list_element_type():
            return
        content.register_license_and_copyrights_of_item(self._item)
        with content.section(self.section, _SECTION_PREFIX):
            last = content.lines[-1]
            self._add_description(content)
            if len(self._info_map) == 1:
                if last == content.lines[-1]:
                    content.add_blank_line()
                key, info = next(iter(self._info_map.items()))
                _DOCUMENT[key](self, content, key, "shall", info)
            else:
                content.add("A value of this type shall be of one of "
                            "the following variants:")
                for key in sorted(self._info_map):
                    with content.list_item(""):
                        _DOCUMENT[key](self, content, key, "may",
                                       self._info_map[key])
            content.add_list([
                refinement.get_section_reference(content)
                for refinement in self.refinements()
            ], "This type is refined by the following types:")
            content.add_list(sorted(self.used_by),
                             "This type is used by the following types:")
            example = self._item["spec-example"]
            if example:
                content.add("Please have a look at the following example:")
                with content.directive("code-block", "yaml"):
                    content.add(example)
        if names:
            names.remove(self._name)
            for refinement in self.refinements():
                refinement.document(content, names)

    def _add_used_by(self, content: SphinxContent, type_name: str) -> None:
        if type_name not in _PRIMITIVE_TYPES:
            documenter = self._documenter_map[type_name]
            element_type_name = documenter.get_list_element_type()
            if element_type_name:
                type_name = element_type_name
        if type_name not in _PRIMITIVE_TYPES:
            documenter = self._documenter_map[type_name]
            documenter.used_by.add(self.get_section_reference(content))

    def resolve_used_by(self, content: SphinxContent) -> None:
        """ Resolves type uses in attribute sets. """
        info = self._info_map.get("dict", None)
        if info is not None:
            for attribute in info["attributes"].values():
                self._add_used_by(content, attribute["spec-type"])
            if "generic-attributes" in info:
                self._add_used_by(content,
                                  info["generic-attributes"]["spec-type"])


_DOCUMENT = {
    "bool": _Documenter.document_value,
    "dict": _Documenter.document_dict,
    "float": _Documenter.document_value,
    "int": _Documenter.document_value,
    "list": _Documenter.document_list,
    "none": _Documenter.document_none,
    "str": _Documenter.document_value,
}


def _gather_item_documenters(item: Item,
                             documenter_map: _DocumenterMap) -> None:
    for link in item.links_to_children():
        if link.role == "spec-member":
            _Documenter(link.item, documenter_map)


def _create_str_documenter(item_cache: ItemCache, name: str, description: str,
                           documenter_map: _DocumenterMap) -> None:
    type_name = name.lower()
    _Documenter(
        Item(
            item_cache, f"/spec/{type_name}", {
                "SPDX-License-Identifier":
                "CC-BY-SA-4.0 OR BSD-2-Clause",
                "copyrights": [
                    "Copyright (C) 2020 embedded brains GmbH "
                    "(http://www.embedded-brains.de)"
                ],
                "spec-description":
                None,
                "spec-example":
                None,
                "spec-info": {
                    "str": {
                        "description": description
                    }
                },
                "spec-name":
                name,
                "spec-type":
                type_name,
            }), documenter_map)


def document(config: dict, item_cache: ItemCache) -> None:
    """
    Documents specification items according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache.
    """
    documenter_map = {}  # type: _DocumenterMap
    root_item = item_cache[config["root-type"]]
    _create_str_documenter(
        item_cache, "Name",
        f"A string is a valid name if it matches with the ``{NAME.pattern}`` "
        "regular expression.", documenter_map)
    _create_str_documenter(
        item_cache, "UID",
        "The string shall be a valid absolute or relative item UID.",
        documenter_map)
    root_documenter = _Documenter(root_item, documenter_map)
    _gather_item_documenters(root_item, documenter_map)
    content = SphinxContent()
    for documenter in documenter_map.values():
        documenter.resolve_used_by(content)
    documenter_names = set(documenter_map.keys())
    with content.section("Specification Items"):
        with content.section("Specification Item Hierarchy"):
            content.add(
                "The specification item types have the following hierarchy:")
            root_documenter.hierarchy(content)
        with content.section("Specification Item Types"):
            root_documenter.document(content, documenter_names)
        with content.section("Specification Attribute Sets and Value Types"):
            documenters = [documenter_map[name] for name in documenter_names]
            for documenter in sorted(documenters, key=lambda x: x.section):
                documenter.document(content)
    content.add_licence_and_copyrights()
    content.write(config["doc-target"])
