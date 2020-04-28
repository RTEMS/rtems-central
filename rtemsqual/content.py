# SPDX-License-Identifier: BSD-2-Clause
""" This module provides classes for content generation. """

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
import itertools
import os
import re
import textwrap
from typing import Callable, ContextManager, Iterator, List, Optional, Union

AddContext = Callable[["Content"], ContextManager[None]]
GenericContent = Union[str, List[str], "Content"]


class Copyright:
    """
    This class represents a copyright holder with its years of substantial
    contributions.
    """
    def __init__(self, holder):
        self._holder = holder
        self._years = set()

    def add_year(self, year: str):
        """
        Adds a year to the set of substantial contributions of this copyright
        holder.
        """
        self._years.add(year)

    def get_statement(self) -> str:
        """ Returns a copyright statement. """
        line = "Copyright (C)"
        years = sorted(self._years)
        year_count = len(years)
        if year_count == 1:
            line += " " + years[0]
        elif year_count > 1:
            line += " " + years[0] + ", " + years[-1]
        line += " " + self._holder
        return line

    def __lt__(self, other: "Copyright") -> bool:
        # pylint: disable=protected-access
        if self._years and other._years:
            self_first_year = sorted(self._years)[0]
            other_first_year = sorted(other._years)[0]
            if self_first_year == other_first_year:
                return self._holder > other._holder
            return self_first_year > other_first_year
        if self._years or other._years:
            return True
        return self._holder > other._holder


class Copyrights:
    """ This class represents a set of copyright holders. """
    def __init__(self):
        self.copyrights = {}

    def register(self, statement):
        """ Registers a copyright statement. """
        match = re.search(
            r"^\s*Copyright\s+\(C\)\s+([0-9]+),\s*([0-9]+)\s+(.+)\s*$",
            statement,
            flags=re.I,
        )
        if match:
            holder = match.group(3)
            the_copyright = self.copyrights.setdefault(holder,
                                                       Copyright(holder))
            the_copyright.add_year(match.group(1))
            the_copyright.add_year(match.group(2))
            return
        match = re.search(
            r"^\s*Copyright\s+\(C\)\s+([0-9]+)\s+(.+)\s*$",
            statement,
            flags=re.I,
        )
        if match:
            holder = match.group(2)
            the_copyright = self.copyrights.setdefault(holder,
                                                       Copyright(holder))
            the_copyright.add_year(match.group(1))
            return
        match = re.search(r"^\s*Copyright\s+\(C\)\s+(.+)\s*$",
                          statement,
                          flags=re.I)
        if match:
            holder = match.group(1)
            self.copyrights.setdefault(holder, Copyright(holder))
            return
        raise ValueError(statement)

    def get_statements(self):
        """ Returns all registered copyright statements as a sorted list. """
        statements = []
        for the_copyright in sorted(self.copyrights.values()):
            statements.append(the_copyright.get_statement())
        return statements


def _make_lines(content: GenericContent) -> List[str]:
    if isinstance(content, str):
        return content.strip("\n").split("\n")
    if isinstance(content, list):
        return content
    return content.lines


def _indent(lines: List[str], indent: str,
            empty_line_indent: str) -> List[str]:
    if indent:
        return [
            indent + line if line else empty_line_indent + line
            for line in lines
        ]
    return lines


@contextmanager
def _add_context(_content: "Content") -> Iterator[None]:
    yield


class Content:
    """ This class builds content. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, the_license):
        self._lines = []  # type: List[str]
        self._license = the_license
        self._copyrights = Copyrights()
        self._gap = False
        self._tab = "  "
        self._indents = [""]
        self._indent = ""
        self._empty_line_indents = [""]
        self._empty_line_indent = ""

    def __str__(self):
        return "\n".join(itertools.chain(self._lines, [""]))

    @property
    def lines(self) -> List[str]:
        """ The lines. """
        return self._lines

    def append(self, content: GenericContent) -> None:
        """ Appends the content. """
        self._lines.extend(
            _indent(_make_lines(content), self._indent,
                    self._empty_line_indent))

    def prepend(self, content: GenericContent) -> None:
        """ Prepends the content. """
        self._lines[0:0] = _indent(_make_lines(content), self._indent,
                                   self._empty_line_indent)

    def add(self,
            content: Optional[GenericContent],
            context: AddContext = _add_context) -> None:
        """
        Skips leading empty lines, adds a gap if needed, then adds the content.
        """
        if not content:
            return
        lines = _make_lines(content)
        index = 0
        for line in lines:
            if line:
                if self._gap:
                    self._lines.extend(
                        _indent([""], self._indent, self._empty_line_indent))
                self._gap = True
                with context(self):
                    self._lines.extend(
                        _indent(lines[index:], self._indent,
                                self._empty_line_indent))
                break
            index += 1

    @property
    def gap(self) -> bool:
        """
        True if the next Content.add() adds a gap before the new content,
        otherwise False.
        """
        return self._gap

    @gap.setter
    def gap(self, value: bool) -> None:
        """ Sets the gap indicator for Content.add(). """
        self._gap = value

    def _update_indent(self) -> None:
        self._indent = "".join(self._indents)
        empty_line_indent = "".join(self._empty_line_indents)
        if empty_line_indent.isspace():
            self._empty_line_indent = ""
        else:
            self._empty_line_indent = empty_line_indent

    def push_indent(self,
                    indent: Optional[str] = None,
                    empty_line_indent: Optional[str] = None) -> None:
        """ Pushes an indent level. """
        self._indents.append(indent if indent else self._tab)
        self._empty_line_indents.append(
            empty_line_indent if empty_line_indent else self._tab)
        self._update_indent()

    def pop_indent(self) -> None:
        """ Pops an indent level. """
        self._indents.pop()
        self._empty_line_indents.pop()
        self._update_indent()

    @contextmanager
    def indent(self,
               indent: Optional[str] = None,
               empty_line_indent: Optional[str] = None) -> Iterator[None]:
        """ Opens an indent context. """
        self.push_indent(indent, empty_line_indent)
        yield
        self.pop_indent()

    def indent_lines(self, level: int) -> None:
        """ Indents all lines by the specified indent level. """
        prefix = level * self._tab
        self._lines = [prefix + line if line else line for line in self._lines]

    def add_blank_line(self):
        """ Adds a blank line. """
        self._lines.append("")

    def register_license(self, the_license: str) -> None:
        """ Registers a licence for the content. """
        licenses = re.split(r"\s+OR\s+", the_license)
        if self._license not in licenses:
            raise ValueError(the_license)

    def register_copyright(self, statement: str) -> None:
        """ Registers a copyright statement for the content. """
        self._copyrights.register(statement)

    def write(self, path: str) -> None:
        """ Writes the content to the file specified by the path. """
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w+") as out:
            out.write(str(self))


class SphinxContent(Content):
    """ This class builds Sphinx content. """
    def __init__(self):
        super().__init__("CC-BY-SA-4.0")
        self._tab = "    "

    def add_label(self, label: str) -> None:
        """ Adds a label. """
        self.add(".. _" + label.strip() + ":")

    def add_header(self, name, level="=") -> None:
        """ Adds a header. """
        name = name.strip()
        self.add([name, level * len(name)])

    def add_index_entries(self, entries) -> None:
        """ Adds a list of index entries the content. """
        self.add([".. index:: " + entry for entry in _make_lines(entries)])

    def add_definition_item(self, name, lines) -> None:
        """ Adds a definition item the content. """
        @contextmanager
        def _definition_item_context(content: Content) -> Iterator[None]:
            content.append(name)
            content.push_indent()
            yield
            content.pop_indent()

        self.add(lines, _definition_item_context)

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


class MacroToSphinx:
    """ This class expands specification item macros to Sphinx markup. """
    def __init__(self):
        self._terms = {}

    def set_terms(self, terms):
        """ Sets the glossary of terms used for macro expansion. """
        self._terms = terms

    def substitute(self, text):
        """
        Substitutes all specification item macros contained in the text.
        """
        return re.sub(r"@@|@([a-z]+){([^}]+)}", self, text)

    def __call__(self, match):
        name = match.group(1)
        if name:
            roles = {
                "term":
                lambda x: ":term:`" + self._terms[x]["glossary-term"] + "`"
            }
            return roles[name](match.group(2))
        assert match.group(0) == "@@"
        return "@"


_BSD_2_CLAUSE_LICENSE = """Redistribution and use in source and binary \
forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""


class CContent(Content):
    """ This class builds C content. """

    # pylint: disable=too-many-public-methods
    def __init__(self):
        super().__init__("BSD-2-Clause")

    def add_spdx_license_identifier(self):
        """
        Adds an SPDX License Identifier according to the registered licenses.
        """
        self.prepend([f"/* SPDX-License-Identifier: {self._license} */", ""])

    def add_copyrights_and_licenses(self):
        """
        Adds the copyrights and licenses according to the registered copyrights
        and licenses.
        """
        with self.comment_block():
            self.add(self._copyrights.get_statements())
            self.add(_BSD_2_CLAUSE_LICENSE)

    def add_have_config(self):
        """ Adds a guarded config.h include. """
        self.add(["#ifdef HAVE_CONFIG_H", "#include \"config.h\"", "#endif"])

    def add_includes(self, includes: List[str], local: bool = False) -> None:
        """ Adds a block of includes. """
        class IncludeKey:  # pylint: disable=too-few-public-methods
            """ Provides a key to sort includes. """
            def __init__(self, inc: str):
                self._inc = inc

            def __lt__(self, other: "IncludeKey") -> bool:
                left = self._inc.split("/")
                right = other._inc.split("/")
                left_len = len(left)
                right_len = len(right)
                if left_len == right_len:
                    for left_part, right_part in zip(left[:-1], right[:-1]):
                        if left_part != right_part:
                            return left_part < right_part
                    return left[-1] < right[-1]
                return left_len < right_len

        left = "\"" if local else "<"
        right = "\"" if local else ">"
        self.add([
            f"#include {left}{inc}{right}"
            for inc in sorted(set(includes), key=IncludeKey)
        ])

    def wrap(self, content: Optional[str], intro: str = "") -> List[str]:
        """ Wraps a text. """
        if not content:
            return [""]
        wrapper = textwrap.TextWrapper()
        wrapper.drop_whitespace = True
        wrapper.initial_indent = intro
        wrapper.subsequent_indent = len(intro) * " "
        wrapper.width = 79 - len(self._indent)
        return wrapper.wrap(content)

    def _open_comment_block(self, begin) -> None:
        self.add(begin)
        self.push_indent(" * ", " *")
        self.gap = False

    def open_comment_block(self) -> None:
        """ Opens a comment block. """
        self._open_comment_block("/*")

    def open_doxygen_block(self) -> None:
        """ Opens a Doxygen comment block. """
        self._open_comment_block("/**")

    def open_file_block(self) -> None:
        """ Opens a Doxygen @file comment block. """
        self._open_comment_block(["/**", " * @file"])
        self.gap = True

    def open_defgroup_block(self, identifier: str, name: str) -> None:
        """ Opens a Doxygen @defgroup comment block. """
        self._open_comment_block(["/**", f" * @defgroup {identifier} {name}"])
        self.gap = True

    def open_function_block(self, function: str) -> None:
        """ Opens a Doxygen @fn comment block. """
        self._open_comment_block(["/**", f" * @fn {function}"])
        self.gap = True

    def close_comment_block(self) -> None:
        """ Closes a comment block. """
        self.pop_indent()
        self.append(" */")
        self.gap = True

    @contextmanager
    def comment_block(self) -> Iterator[None]:
        """ Opens a comment block context. """
        self.open_comment_block()
        yield
        self.close_comment_block()

    @contextmanager
    def doxygen_block(self) -> Iterator[None]:
        """ Opens a Doxygen comment block context. """
        self.open_doxygen_block()
        yield
        self.close_comment_block()

    @contextmanager
    def file_block(self) -> Iterator[None]:
        """ Opens a Doxygen @file comment block context. """
        self.open_file_block()
        yield
        self.close_comment_block()

    @contextmanager
    def defgroup_block(self, identifier: str, name: str) -> Iterator[None]:
        """ Opens a Doxygen @defgroup comment block context. """
        self.open_defgroup_block(identifier, name)
        yield
        self.close_comment_block()

    @contextmanager
    def function_block(self, function: str) -> Iterator[None]:
        """ Opens a Doxygen @fn comment block context. """
        self.open_function_block(function)
        yield
        self.close_comment_block()

    def add_brief_description(self, description: Optional[str]) -> None:
        """ Adds a brief description. """
        return self.add(self.wrap(description, intro="@brief "))

    def add_ingroup(self, ingroups: List[str]) -> None:
        """ Adds an ingroup comment block. """
        self.add(["@ingroup " + ingroup for ingroup in sorted(set(ingroups))])

    def add_group(self, identifier: str, name: str, ingroups: List[str],
                  brief: Optional[str], description: Optional[str]) -> None:
        # pylint: disable=too-many-arguments
        """ Adds a group definition. """
        with self.defgroup_block(identifier, name):
            self.add_ingroup(ingroups)
            self.add_brief_description(brief)
            self.add(self.wrap(description))

    @contextmanager
    def header_guard(self, filename: str) -> Iterator[None]:
        """ Opens a header guard context. """
        filename = os.path.basename(filename)
        guard = "_" + filename.replace(".", "_").upper()
        self.add([f"#ifndef {guard}", f"#define {guard}"])
        yield
        self.add(f"#endif /* {guard} */")

    @contextmanager
    def extern_c(self) -> Iterator[None]:
        """ Opens an extern "C" context. """
        self.add(["#ifdef __cplusplus", "extern \"C\" {", "#endif"])
        yield
        self.add(["#ifdef __cplusplus", "}", "#endif"])
