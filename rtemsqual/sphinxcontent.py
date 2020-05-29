# SPDX-License-Identifier: BSD-2-Clause
""" This module provides classes for Sphinx content generation. """

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

from contextlib import contextmanager
import os
import re
from typing import Any, Dict, Callable, Iterable, Iterator, List, Optional, \
    Union

from rtemsqual.content import Content, make_lines
from rtemsqual.items import Item, ItemMapper

GenericContent = Union[str, List[str], "Content"]
GenericContentIterable = Union[Iterable[str], Iterable[List[str]],
                               Iterable[GenericContent]]

_HEADER_LEVELS = ["#", "*", "=", "-", "^", "\""]


def _to_camel_case(name: str) -> str:
    return name[0].upper() + re.sub(
        r"[^a-zA-Z0-9]", "X",
        re.sub(r"[ \n\t]+([a-zA-Z0-9])", lambda match: match.group(1).upper(),
               name[1:]))


def get_reference(label: str, name: Optional[str] = None) -> str:
    """ Returns the reference to the specified label. """
    if name:
        return f":ref:`{name} <{label}>`"
    return f":ref:`{label}`"


def get_label(name: str) -> str:
    """ Returns the label for the specified name. """
    return _to_camel_case(name.strip())


class SphinxContent(Content):
    """ This class builds Sphinx content. """
    def __init__(self, section_level: int = 2):
        super().__init__("CC-BY-SA-4.0", True)
        self._tab = "    "
        self._section_level = section_level
        self.section_label_prefix = "Section"

    def add_label(self, label: str) -> None:
        """ Adds a label. """
        self.add(".. _" + label.strip() + ":")

    def add_header(self, name, level=2) -> None:
        """ Adds a header. """
        name = name.strip()
        self.add([name, _HEADER_LEVELS[level] * len(name)])

    def add_header_with_label(self,
                              name: str,
                              level: int = 2,
                              label_prefix: Optional[str] = None) -> str:
        """ Adds a header with label. """
        if label_prefix is None:
            label_prefix = self.section_label_prefix
        label = label_prefix + get_label(name)
        self.add_label(label)
        self.add_header(name, level)
        return label

    def add_index_entries(self, entries) -> None:
        """ Adds a list of index entries the content. """
        self.add([".. index:: " + entry for entry in make_lines(entries)])

    def add_definition_item(self, name, lines) -> None:
        """ Adds a definition item the content. """
        @contextmanager
        def _definition_item_context(content: Content) -> Iterator[None]:
            content.append(name)
            content.push_indent()
            yield
            content.pop_indent()

        self.add(lines, _definition_item_context)

    def open_directive(self,
                       name: str,
                       value: Optional[str] = None,
                       options: Optional[List[str]] = None) -> None:
        """ Opens a directive. """
        value = " " + value if value else ""
        self.add(f".. {name.strip()}::{value}")
        self.push_indent()
        self.add(options)
        self.gap = True

    def close_directive(self) -> None:
        """ Closes a directive. """
        self.pop_indent()

    @contextmanager
    def directive(self,
                  name: str,
                  value: Optional[str] = None,
                  options: Optional[List[str]] = None):
        """ Opens a directive context. """
        self.open_directive(name, value, options)
        yield
        self.close_directive()

    def open_section(self,
                     name: str,
                     label_prefix: Optional[str] = None) -> str:
        """ Opens a section. """
        label = self.add_header_with_label(name, self._section_level,
                                           label_prefix)
        self._section_level += 1
        return label

    def close_section(self) -> None:
        """ Closes a section. """
        self._section_level -= 1

    @contextmanager
    def section(self,
                name: str,
                label_prefix: Optional[str] = None) -> Iterator[str]:
        """ Opens a section context. """
        yield self.open_section(name, label_prefix)
        self.close_section()

    def add_list_item(self, content: GenericContent) -> None:
        """ Adds a list item. """
        self.wrap(content, initial_indent="* ", subsequent_indent="  ")

    def add_list(self,
                 items: GenericContentIterable,
                 prologue: Optional[GenericContent] = None,
                 epilogue: Optional[GenericContent] = None,
                 add_blank_line: bool = False) -> None:
        """ Adds a list with introduction. """
        if items:
            self.wrap(prologue)
            for item in items:
                self.add_list_item(item)
            if add_blank_line:
                self.add_blank_line()
            self.wrap(epilogue)

    def open_list_item(self, content: GenericContent) -> None:
        """ Opens a list item. """
        self.add(["* "])
        self.push_indent("  ")
        self.gap = True
        self.paste(content)

    def close_list_item(self) -> None:
        """ Closes a list item. """
        self.pop_indent()
        self.gap = True

    @contextmanager
    def list_item(self, content: GenericContent) -> Iterator[None]:
        """ Opens a list item context. """
        self.open_list_item(content)
        yield
        self.close_list_item()

    def add_licence_and_copyrights(self) -> None:
        """
        Adds a licence and copyright block according to the registered licenses
        and copyrights.
        """
        statements = self._copyrights.get_statements()
        if statements:
            self.prepend("")
            self.prepend([f".. {stm}" for stm in statements])
        self.prepend([f".. SPDX-License-Identifier: {self._license}", ""])


def _get_ref_term(value: Any, key: str) -> str:
    return f":term:`{value[key]}`"


class SphinxMapper(ItemMapper):
    """ Sphinx mapper. """
    def __init__(self, item: Item):
        super().__init__(item)
        self._get_ref = {
            "glossary:/term": _get_ref_term
        }  # type: Dict[str, Callable[[Any, str], str]]

    def add_get_reference(self, type_name: str, path: str,
                          get_ref: Callable[[Any, str], str]) -> None:
        """
        Adds a function to get a reference to the specified path for items of
        the specified type.
        """
        self._get_ref[f"{type_name}:{path}"] = get_ref

    def get_value(self, item: Item, path: str, value: Any, key: str,
                  _index: Optional[int]) -> Any:
        """ Gets a value by key and optional index. """
        return self._get_ref[f"{item['type']}:{os.path.join(path, key)}"](
            value, key)
