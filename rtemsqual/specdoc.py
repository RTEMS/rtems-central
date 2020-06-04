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

from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from rtemsqual.sphinxcontent import get_reference, get_label, \
    SphinxContent, SphinxMapper
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

_MANDATORY_ATTRIBUTES = {
    "all":
    "All explicit attributes shall be specified.",
    "at-least-one":
    "At least one of the explicit attributes shall be specified.",
    "at-most-one":
    "At most one of the explicit attributes shall be specified.",
    "exactly-one":
    "Exactly one of the explicit attributes shall be specified.",
    "none":
    "None of the explicit attributes is mandatory, "
    "they are all are optional.",
}

_SPEC_TYPE_PREFIX = "SpecType"


def _a_or_an(value: str) -> str:
    if value[0].lower() in ["a", "e", "i", "o", "u"]:
        return "an"
    return "a"


def _get_ref_specification_type(value: Any, key: str) -> str:
    return get_reference(_SPEC_TYPE_PREFIX + get_label(value[key]))


class _AssertContext:
    """ This class provides a context to document assert expressions. """
    def __init__(self, content: SphinxContent, ops: Dict[str, Any]):
        self.content = content
        self.ops = ops
        self._comma = ""

    def comma(self):
        """ Adds a comma to the content if necessary. """
        if not self.content.lines[-1].endswith(","):
            self.content.lines[-1] += self._comma
            self._comma = ","

    def paste(self, text: str):
        """ Pastes a text to the content. """
        self.content.paste(text)


def _negate(negate: bool) -> str:
    if negate:
        return "not "
    return ""


def _value(value: Any) -> str:
    if isinstance(value, str):
        return f"\"``{value}``\""
    if isinstance(value, bool):
        if value:
            return "true"
        return "false"
    return str(value)


def _list(ctx: _AssertContext, assert_info: List[str]) -> None:
    ctx.content.add_list([f"{_value(value)}," for value in assert_info[:-2]])
    try:
        ctx.content.add_list_item(f"{_value(assert_info[-2])}, and")
    except IndexError:
        pass
    try:
        ctx.content.add_list_item(f"{_value(assert_info[-1])}")
    except IndexError:
        pass


def _document_op_and_or(ctx: _AssertContext, negate: bool, assert_info: Any,
                        and_or: str) -> None:
    if len(assert_info) == 1:
        _document_assert(ctx, negate, assert_info[0])
    else:
        if negate or ctx.content.lines[-1].endswith("* "):
            ctx.paste(f"shall {_negate(negate)}meet")
        intro = ""
        for element in assert_info:
            ctx.comma()
            with ctx.content.list_item(intro):
                _document_assert(ctx, False, element)
            intro = and_or


def _document_op_and(ctx: _AssertContext, negate: bool,
                     assert_info: Any) -> None:
    _document_op_and_or(ctx, negate, assert_info, "and, ")


def _document_op_not(ctx: _AssertContext, negate: bool,
                     assert_info: Any) -> None:
    _document_assert(ctx, not negate, assert_info)


def _document_op_or(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    _document_op_and_or(ctx, negate, assert_info, "or, ")


def _document_op_eq(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_ne(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be equal to {_value(assert_info)}")


def _document_op_ne(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_eq(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be not equal to {_value(assert_info)}")


def _document_op_le(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_gt(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be less than or equal to {_value(assert_info)}")


def _document_op_lt(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_ge(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be less than {_value(assert_info)}")


def _document_op_ge(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_lt(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be greater than or equal to {_value(assert_info)}")


def _document_op_gt(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_le(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be greater than {_value(assert_info)}")


def _document_op_uid(ctx: _AssertContext, negate: bool,
                     _assert_info: Any) -> None:
    if negate:
        ctx.paste("shall be an invalid item UID")
    else:
        ctx.paste("shall be a valid item UID")


def _document_op_re(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    ctx.paste(f"shall {_negate(negate)}match with "
              f"the regular expression \"``{assert_info}\"``")


def _document_op_in(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    ctx.paste(f"shall {_negate(negate)}be an element of")
    _list(ctx, assert_info)


def _document_op_contains(ctx: _AssertContext, negate: bool,
                          assert_info: Any) -> None:
    ctx.paste(f"shall {_negate(negate)}contain an element of")
    _list(ctx, assert_info)


def _document_assert(ctx: _AssertContext, negate: bool,
                     assert_info: Any) -> None:
    if isinstance(assert_info, bool):
        if negate:
            assert_info = not assert_info
        ctx.paste(f"shall be {_value(assert_info)}")
    elif isinstance(assert_info, list):
        _document_op_or(ctx, negate, assert_info)
    else:
        key = next(iter(assert_info))
        ctx.ops[key](ctx, negate, assert_info[key])


_DOCUMENT_OPS = {
    "and": _document_op_and,
    "contains": _document_op_contains,
    "eq": _document_op_eq,
    "ge": _document_op_ge,
    "gt": _document_op_gt,
    "in": _document_op_in,
    "le": _document_op_le,
    "lt": _document_op_lt,
    "ne": _document_op_ne,
    "not": _document_op_not,
    "or": _document_op_or,
    "re": _document_op_re,
    "uid": _document_op_uid,
}


def _maybe_document_assert(content: SphinxContent, type_info: Any) -> None:
    if "assert" in type_info:
        content.paste("The value ")
        _document_assert(_AssertContext(content, _DOCUMENT_OPS), False,
                         type_info["assert"])
        content.lines[-1] += "."


class _Documenter:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, item: Item, documenter_map: _DocumenterMap):
        self._name = item["spec-type"]
        self.section = item["spec-name"]
        self._description = item["spec-description"]
        self._info_map = item["spec-info"]
        self._item = item
        self._documenter_map = documenter_map
        self.used_by = set()  # type: Set[str]
        self._mapper = SphinxMapper(item)
        self._mapper.add_get_reference("spec", "/spec-name",
                                       _get_ref_specification_type)
        assert self._name not in documenter_map
        documenter_map[self._name] = self

    def _substitute(self, text: str) -> str:
        if text:
            return self._mapper.substitute(text)
        return text

    def get_section_reference(self) -> str:
        """ Returns the section reference. """
        return get_reference(_SPEC_TYPE_PREFIX + get_label(self.section))

    def get_a_section_reference(self) -> str:
        """ Returns a section reference. """
        return f"{_a_or_an(self.section)} {self.get_section_reference()}"

    def get_list_element_type(self) -> str:
        """ Returns the list element type if this is a list only type. """
        if len(self._info_map) == 1 and "list" in self._info_map:
            return self._info_map["list"]["spec-type"]
        return ""

    def get_list_phrase(self, value: str, shall: str, type_name: str) -> str:
        """ Returns a list phrase. """
        if type_name in _PRIMITIVE_TYPES:
            type_phrase = _PRIMITIVE_TYPES[type_name].format(
                "Each list element", "shall")
        else:
            documenter = self._documenter_map[type_name]
            ref = documenter.get_a_section_reference()
            type_phrase = f"Each list element shall be {ref}."
        return f"{value} {shall} be a list. {type_phrase}"

    def get_value_type_phrase(self, value: str, shall: str,
                              type_name: str) -> str:
        """ Returns a value type phrase. """
        if type_name in _PRIMITIVE_TYPES:
            return _PRIMITIVE_TYPES[type_name].format(value, shall)
        documenter = self._documenter_map[type_name]
        element_type_name = documenter.get_list_element_type()
        if element_type_name:
            return self.get_list_phrase(value, shall, element_type_name)
        return (f"{value} {shall} be "
                f"{documenter.get_a_section_reference()}.")

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
        with content.list_item(self.get_section_reference()):
            for refinement in self.refinements():
                refinement.hierarchy(content)

    def _document_attributes(self, content: SphinxContent,
                             attributes: Any) -> None:
        for key in sorted(attributes):
            info = attributes[key]
            content.add(key)
            with content.indent():
                content.wrap(
                    self.get_value_type_phrase("The attribute value", "shall",
                                               info["spec-type"]))
                content.paste_and_add(self._substitute(info["description"]))

    def document_dict(self, content: SphinxContent, _variant: str, shall: str,
                      info: Any) -> None:
        """ Documents an attribute set. """
        if shall == "may":
            content.paste("The value may be a set of attributes.")
        content.paste_and_add(self._substitute(info["description"]))
        has_explicit_attributes = len(info["attributes"]) > 0
        if has_explicit_attributes:
            mandatory_attributes = info["mandatory-attributes"]
            if isinstance(mandatory_attributes, str):
                content.paste(_MANDATORY_ATTRIBUTES[mandatory_attributes])
            else:
                assert isinstance(mandatory_attributes, list)
                mandatory_attribute_count = len(mandatory_attributes)
                if mandatory_attribute_count == 1:
                    content.paste(f"Only the ``{mandatory_attributes[0]}`` "
                                  "attribute is mandatory.")
                elif mandatory_attribute_count > 1:
                    content.paste("The following explicit "
                                  "attributes are mandatory:")
                    for attribute in sorted(mandatory_attributes):
                        content.add_list_item(f"``{attribute}``")
                    content.add_blank_line()
                else:
                    content.add_blank_line()
            content.paste("The explicit attributes for this type are:")
            self._document_attributes(content, info["attributes"])
        if "generic-attributes" in info:
            if has_explicit_attributes:
                content.wrap("In addition to the explicit attributes, "
                             "generic attributes may be specified.")
            else:
                content.paste("Generic attributes may be specified.")
            content.paste(
                self.get_value_type_phrase(
                    "Each generic attribute key", "shall",
                    info["generic-attributes"]["key-spec-type"]))
            content.paste(
                self.get_value_type_phrase(
                    "Each generic attribute value", "shall",
                    info["generic-attributes"]["value-spec-type"]))
            content.paste_and_add(
                self._substitute(info["generic-attributes"]["description"]))

    def document_value(self, content: SphinxContent, variant: str, shall: str,
                       info: Any) -> None:
        """ Documents a value. """
        content.paste(self.get_value_type_phrase("The value", shall, variant))
        content.paste_and_add(self._substitute(info["description"]))
        _maybe_document_assert(content, info)

    def document_list(self, content: SphinxContent, _variant: str, shall: str,
                      info: Any) -> None:
        """ Documents a list value. """
        content.paste(
            self.get_list_phrase("The value", shall, info["spec-type"]))
        content.paste_and_add(self._substitute(info["description"]))

    def document_none(self, content: SphinxContent, _variant: str, shall: str,
                      _info: Any) -> None:
        """ Documents a none value. """
        # pylint: disable=no-self-use
        content.paste(f"There {shall} by be no value (null).")

    def _add_description(self, content: SphinxContent) -> None:
        refines = [
            f"{documenter.get_section_reference()} though the "
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
        with content.section(self.section, _SPEC_TYPE_PREFIX):
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
                refinement.get_section_reference()
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

    def _add_used_by(self, type_name: str) -> None:
        if type_name not in _PRIMITIVE_TYPES:
            documenter = self._documenter_map[type_name]
            element_type_name = documenter.get_list_element_type()
            if element_type_name:
                type_name = element_type_name
        if type_name not in _PRIMITIVE_TYPES:
            documenter = self._documenter_map[type_name]
            documenter.used_by.add(self.get_section_reference())

    def resolve_used_by(self) -> None:
        """ Resolves type uses in attribute sets. """
        info = self._info_map.get("dict", None)
        if info is not None:
            for attribute in info["attributes"].values():
                self._add_used_by(attribute["spec-type"])
            if "generic-attributes" in info:
                self._add_used_by(info["generic-attributes"]["key-spec-type"])
                self._add_used_by(
                    info["generic-attributes"]["value-spec-type"])


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
        item_cache, "Name", "A string is a valid name if it matches with the "
        f"``{NAME.pattern.replace('$', '$$')}`` regular expression.",
        documenter_map)
    _create_str_documenter(
        item_cache, "UID",
        "The string shall be a valid absolute or relative item UID.",
        documenter_map)
    root_documenter = _Documenter(root_item, documenter_map)
    _gather_item_documenters(root_item, documenter_map)
    content = SphinxContent()
    for documenter in documenter_map.values():
        documenter.resolve_used_by()
    documenter_names = set(documenter_map)
    content.section_label_prefix = "ReqEng"
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
