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

# pylint: disable=too-many-lines

from contextlib import contextmanager
import collections
import itertools
import os
import re
import sys
import textwrap
from typing import Any, Callable, ContextManager, Deque, Dict, Iterable, \
    Iterator, List, NamedTuple, Optional, Set, Tuple, Union

from rtemsspec.items import Item, ItemGetValueContext

AddContext = Callable[["Content"], ContextManager[None]]
GenericContent = Union[str, List[str], "Content"]
GenericContentIterable = Union[Iterable[str], Iterable[List[str]],
                               Iterable[GenericContent]]


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


def make_lines(content: GenericContent) -> List[str]:
    """ Makes a list of lines from a generic content. """
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


_SPECIAL_BLOCK = re.compile(r"^( *\* | *[0-9]+\. | +)")

_AUTOMATICALLY_GENERATED_WARNING = [
    "This file is part of the RTEMS quality process and was automatically",
    "generated.  If you find something that needs to be fixed or",
    "worded better please post a report or patch to an RTEMS mailing list",
    "or raise a bug report:",
    "",
    "https://www.rtems.org/bugs.html",
    "",
    "For information on updating and regenerating please refer to the How-To",
    "section in the Software Requirements Engineering chapter of the",
    "RTEMS Software Engineering manual.  The manual is provided as a part of",
    "a release.  For development sources please refer to the online",
    "documentation at:",
    "",
    "https://docs.rtems.org",
]


class Content:
    """ This class builds content. """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    def __init__(self, the_license: str, pop_indent_gap: bool):
        self._lines = []  # type: List[str]
        self._license = the_license
        self._copyrights = Copyrights()
        self._gap = False
        self._tab = "  "
        self._indents = [""]
        self._indent = ""
        self._empty_line_indents = [""]
        self._empty_line_indent = ""
        self._pop_indent_gap = pop_indent_gap

    def __str__(self):
        return "\n".join(itertools.chain(self._lines, [""]))

    @property
    def lines(self) -> List[str]:
        """ The lines. """
        return self._lines

    @property
    def tab(self) -> str:
        """ The tabulator. """
        return self._tab

    def append(self, content: GenericContent) -> None:
        """ Appends the content. """
        self._lines.extend(
            _indent(make_lines(content), self._indent,
                    self._empty_line_indent))

    def prepend(self, content: GenericContent) -> None:
        """ Prepends the content. """
        self._lines[0:0] = _indent(make_lines(content), self._indent,
                                   self._empty_line_indent)

    def add(self,
            content: Optional[GenericContent],
            context: AddContext = _add_context) -> None:
        """
        Skips leading empty lines, adds a gap if needed, then adds the content.
        """
        if not content:
            return
        lines = make_lines(content)
        for index, line in enumerate(lines):
            if line:
                self._add_gap()
                with context(self):
                    self._lines.extend(
                        _indent(lines[index:], self._indent,
                                self._empty_line_indent))
                break

    def _add_verbatim(self, blocks: Deque[str]) -> None:
        while blocks:
            block = blocks.popleft()
            if block.startswith("    "):
                self.add(block[4:].replace("\n    ", "\n"))
            else:
                blocks.appendleft(block)
                break

    def wrap_text(self,
                  text: str,
                  initial_indent: str = "",
                  subsequent_indent: Optional[str] = None,
                  context: AddContext = _add_context) -> None:
        """ Adds a gap if needed, then adds the wrapped text.  """
        self._add_gap()
        with context(self):
            if subsequent_indent is None:
                if initial_indent:
                    subsequent_indent = self._tab
                else:
                    subsequent_indent = ""
            wrapper = textwrap.TextWrapper()
            wrapper.break_long_words = False
            wrapper.break_on_hyphens = False
            wrapper.initial_indent = initial_indent
            wrapper.width = 79 - len(self._indent)
            gap = []  # type: List[str]
            blocks = collections.deque(text.split("\n\n"))
            while blocks:
                block = blocks.popleft()
                match = _SPECIAL_BLOCK.search(block)
                if match:
                    space = len(match.group(0)) * " "
                    wrapper.subsequent_indent = f"{subsequent_indent}{space}"
                    block = block.replace(f"\n{space}", "\n")
                elif block.startswith(".. code-block"):
                    self.add(block)
                    with self.indent():
                        self.gap = True
                        self._add_verbatim(blocks)
                    continue
                else:
                    wrapper.subsequent_indent = subsequent_indent
                self._lines.extend(gap)
                self._lines.extend(
                    _indent(wrapper.wrap(block), self._indent,
                            self._empty_line_indent))
                gap = [self._empty_line_indent]

    def wrap(self,
             content: Optional[GenericContent],
             initial_indent: str = "",
             subsequent_indent: Optional[str] = None,
             context: AddContext = _add_context) -> None:
        """ Adds a gap if needed, then adds the wrapped content.  """
        if not content:
            return
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = "\n".join(content)
        else:
            text = "\n".join(content.lines)
        text = text.strip()
        if not text:
            return
        self.wrap_text(text, initial_indent, subsequent_indent, context)

    def paste(self, content: Optional[GenericContent]) -> None:
        """ Pastes the wrapped content directly to the last line.  """
        if not content:
            return
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = "\n".join(content)
        else:
            text = "\n".join(content.lines)
        indent_len = len(self._indent)
        try:
            last = self._lines[-1]
            text = last[indent_len:] + " " + text
        except IndexError:
            last = ""
        text = text.strip()
        if not text:
            return
        wrapper = textwrap.TextWrapper()
        wrapper.break_long_words = False
        wrapper.break_on_hyphens = False
        wrapper.initial_indent = ""
        wrapper.width = 79 - len(self._indent)
        for index, block in enumerate(text.split("\n\n")):
            if index == 0:
                wrapper.subsequent_indent = ""
                lines = wrapper.wrap(block)
                if 0 < len(last) >= indent_len:
                    self._lines[-1] = last[0:indent_len] + lines[0]
                    lines = lines[1:]
                self.gap = True
            else:
                match = _SPECIAL_BLOCK.search(block)
                if match:
                    space = len(match.group(0)) * " "
                    wrapper.subsequent_indent = space
                    block = block.replace(f"\n{space}", "\n")
                else:
                    wrapper.subsequent_indent = ""
                lines = wrapper.wrap(block)
                self._lines.append(self._empty_line_indent)
            self._lines.extend(
                _indent(lines, self._indent, self._empty_line_indent))

    def _add_gap(self) -> None:
        if self._gap:
            self._lines.extend(
                _indent([""], self._indent, self._empty_line_indent))
        self._gap = True

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
        self.gap = False

    def pop_indent(self) -> None:
        """ Pops an indent level. """
        self._indents.pop()
        self._empty_line_indents.pop()
        self._update_indent()
        self.gap = self._pop_indent_gap

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
        self._gap = False

    def ensure_blank_line(self):
        """ Ensures that the last line is blank. """
        if not self._lines or self._lines[-1]:
            self._lines.append("")
            self._gap = False

    def register_license(self, the_license: str) -> None:
        """ Registers a licence for the content. """
        licenses = re.split(r"\s+OR\s+", the_license)
        if self._license not in licenses:
            raise ValueError(the_license)

    def register_copyright(self, statement: str) -> None:
        """ Registers a copyright statement for the content. """
        self._copyrights.register(statement)

    def register_license_and_copyrights_of_item(self, item: Item) -> None:
        """ Registers the license and copyrights of the item. """
        self.register_license(item["SPDX-License-Identifier"])
        for statement in item["copyrights"]:
            self.register_copyright(statement)

    def open_comment_block(self) -> None:
        """ Opens a comment block. """
        self.push_indent("# ", "#")

    def close_comment_block(self) -> None:
        """ Closes a comment block. """
        self.pop_indent()
        self.gap = True

    @contextmanager
    def comment_block(self) -> Iterator[None]:
        """ Opens a comment block context. """
        self.open_comment_block()
        yield
        self.close_comment_block()

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

    def add_automatically_generated_warning(self) -> None:
        """ Adds a warning that the file is automatically generated. """
        with self.comment_block():
            self.append(_AUTOMATICALLY_GENERATED_WARNING)

    def write(self, path: str) -> None:
        """ Writes the content to the file specified by the path. """
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w+") as out:
            out.write(str(self))


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

_PARAM = {
    None: "@param ",
    "in": "@param[in] ",
    "out": "@param[out] ",
    "inout": "@param[in,out] ",
}


class CInclude(NamedTuple):
    """ A C include file. """
    path: str
    enabled_by: str = ""


def _split_includes(
        includes: List[CInclude]) -> Tuple[Set[str], Dict[str, Set[str]]]:
    includes_unconditional = set()  # type: Set[str]
    includes_enabled_by = {}  # type: Dict[str, Set[str]]
    for inc in list(dict.fromkeys(includes)):
        if inc.enabled_by and inc.enabled_by != "1":
            try:
                includes_unconditional.remove(inc.path)
            except KeyError:
                pass
            includes_enabled_by.setdefault(inc.path, set()).add(inc.enabled_by)
        elif inc.path not in includes_enabled_by:
            includes_unconditional.add(inc.path)
    return includes_unconditional, includes_enabled_by


_FUNCTION_POINTER = re.compile(r"^[^(]+\(\s\*([^)]+)\)\s*\(")
_DESIGNATOR = re.compile(r"([a-zA-Z0-9_]+)$")


def _get_align_pos(param: str) -> Tuple[int, int]:
    if param == "...":
        return 0, sys.maxsize
    match = _DESIGNATOR.search(param)
    if not match:
        match = _FUNCTION_POINTER.search(param)
        assert match
    star = param.find("*")
    if star >= 0:
        return star, match.start(1)
    return match.start(1), match.start(1)


def _align_params(params: List[str]) -> List[str]:
    positions = list(map(_get_align_pos, params))
    max_pos = max(positions)[1]
    return [
        param[:pos[0]] + (max_pos - pos[1]) * " " + param[pos[0]:]
        for param, pos in zip(params, positions)
    ]


_NOT_ALPHANUM = re.compile(r"[^a-zA-Z0-9_]")
_SPHINX_FILE_TO_DOXYGEN = re.compile(r":file:`([^`]+)`")


def _make_str(value: Optional[str]) -> str:
    return value if value else ""


class CContent(Content):
    """ This class builds C content. """

    # pylint: disable=too-many-public-methods
    def __init__(self):
        super().__init__("BSD-2-Clause", False)

    def doxyfy(self, content: Optional[GenericContent]) -> None:
        """
        Adds a gap if needed, then adds the wrapped text with some conversion
        to Doxygen markup.
        """
        if not content:
            return
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = "\n".join(content)
        else:
            text = "\n".join(content.lines)
        text = text.strip()
        if not text:
            return
        blocks = collections.deque(text.split("\n\n"))
        while blocks:
            block = blocks.popleft()
            block = _SPHINX_FILE_TO_DOXYGEN.sub(
                lambda match: f"``{match.group(1)}``", block)
            if block.startswith(".. code-block"):
                self.add("@code")
                self.gap = False
                self._add_verbatim(blocks)
                self.append("@endcode")
            else:
                self.wrap_text(block)

    def prepend_spdx_license_identifier(self):
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

    def prepend_copyrights_and_licenses(self):
        """
        Prepends the copyrights and licenses according to the registered
        copyrights and licenses.
        """
        content = CContent()
        with content.comment_block():
            content.add(self._copyrights.get_statements())
            content.add(_BSD_2_CLAUSE_LICENSE)
        content.append("")
        self.prepend(content)

    def add_have_config(self):
        """ Adds a guarded config.h include. """
        self.add(["#ifdef HAVE_CONFIG_H", "#include \"config.h\"", "#endif"])

    def _add_includes(self, includes: Set[str], local: bool) -> None:
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
            for inc in sorted(includes, key=IncludeKey)
        ])

    def _add_includes_enabled_by(self, includes: Dict[str, Set[str]],
                                 local: bool) -> None:
        enabled_by_includes = {}  # type: Dict[str, Set[str]]
        for inc, enabled_bys in iter(includes.items()):
            enabled_by_includes.setdefault(" && ".join(sorted(enabled_bys)),
                                           set()).add(inc)
        for enabled_by, incs in sorted(iter(enabled_by_includes.items())):
            self.add(f"#if {enabled_by}")
            with self.indent():
                self._add_includes(incs, local)
            self.add("#endif")

    def add_includes(self,
                     includes: List[CInclude],
                     local: bool = False) -> None:
        """ Adds a block of includes. """
        includes_unconditional, includes_enabled_by = _split_includes(includes)
        self._add_includes(includes_unconditional, local)
        self._add_includes_enabled_by(includes_enabled_by, local)

    def _open_comment_block(self, begin) -> None:
        self.add(begin)
        self.push_indent(" * ", " *")

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
        defgroup = [f" * @defgroup {identifier} {name}"]
        if len(self._indent) + len(defgroup[0]) > 79:
            defgroup = [f" * @defgroup {identifier} \\", f" *   {name}"]
        self._open_comment_block(["/**"] + defgroup)
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

    def open_add_to_group(self, group: str) -> None:
        """ Opens an add to group. """
        with self.doxygen_block():
            self.append([f"@addtogroup {group}", "", "@{"])

    def close_add_to_group(self) -> None:
        """ Closes an add to group. """
        self.add("/** @} */")

    @contextmanager
    def add_to_group(self, group: str) -> Iterator[None]:
        """ Opens an add to group context. """
        self.open_add_to_group(group)
        yield
        self.close_add_to_group()

    def open_for_loop(self, begin: str, end: str, step: str) -> None:
        """ Opens a for loop. """
        for_loop = [f"for ( {begin}; {end}; {step} ) {{"]
        if len(self._indent) + len(for_loop[0]) > 79:
            for_loop = [
                "for (", f"{self.tab}{begin};", f"{self.tab}{end};",
                f"{self.tab}{step}", ") {"
            ]
        self.add(for_loop)
        self.push_indent()

    def close_for_loop(self) -> None:
        """ Closes a for loop. """
        self.pop_indent()
        self.append(["}"])
        self.gap = True

    @contextmanager
    def for_loop(self, begin: str, end: str, step: str) -> Iterator[None]:
        """ Opens a for loop context. """
        self.open_for_loop(begin, end, step)
        yield
        self.close_for_loop()

    def _function(self, ret: str, name: str, params: List[str],
                  param_line: str, space: str, semicolon: str) -> None:
        # pylint: disable=too-many-arguments
        line = f"{ret}{space}{name}("
        if len(self._indent) + len(line) > 79:
            line = f"{name}{param_line}{semicolon}"
            if len(self._indent) + len(line) > 79:
                self.add([ret, f"{name}("])
            else:
                self.add([ret, line])
                return
        else:
            self.add(line)
        with self.indent():
            self.add(",\n".join(params))
        self.add(f"){semicolon}")

    def call_function(self,
                      ret: Optional[str],
                      name: str,
                      params: Optional[List[str]] = None,
                      semicolon: str = ";") -> None:
        """ Adds a function call. """
        if ret:
            space = " "
        else:
            ret = ""
            space = ""
        if params:
            params = [param.strip() for param in params]
            param_line = "( " + ", ".join(params) + " )"
        else:
            param_line = "()"
        line = f"{ret}{space}{name}{param_line}{semicolon}"
        if len(self._indent) + len(line) > 79:
            if params:
                self._function(ret, name, params, param_line, space, semicolon)
            elif ret:
                self.add(ret)
                with self.indent():
                    self.add(f"{name}(){semicolon}")
            else:
                self.add(f"{name}(){semicolon}")
        else:
            self.add(line)

    def declare_function(self,
                         ret: str,
                         name: str,
                         params: Optional[List[str]] = None,
                         define: bool = False,
                         align: bool = True) -> None:
        # pylint: disable=too-many-arguments
        """ Adds a function declaration. """
        if params:
            params = [param.strip() for param in params]
        else:
            params = ["void"]
        param_line = f"( {', '.join(params)} )"
        space = "" if not ret or ret.endswith("*") else " "
        semicolon = "" if define else ";"
        line = f"{ret}{space}{name}{param_line}{semicolon}"
        if len(self._indent) + len(line) > 79:
            if align:
                params = _align_params(params)
            self._function(ret, name, params, param_line, space, semicolon)
        else:
            self.add(line)

    def open_function(self,
                      ret: str,
                      name: str,
                      params: Optional[List[str]] = None,
                      align: bool = True) -> None:
        """ Opens a function definition. """
        self.declare_function(ret, name, params, define=True, align=align)
        self.append("{")
        self.push_indent()

    def close_function(self) -> None:
        """ Closes a function definition. """
        self.pop_indent()
        self.add("}")

    @contextmanager
    def function(self,
                 ret: str,
                 name: str,
                 params: Optional[List[str]] = None,
                 align: bool = True) -> Iterator[None]:
        """ Opens a function context. """
        self.open_function(ret, name, params, align=align)
        yield
        self.close_function()

    def open_condition(self,
                       expression: Optional[str],
                       chain: bool = False) -> None:
        """ Opens a condition. """
        begin = "} else " if chain else ""
        ifelse = f"if ( {expression} ) " if expression else ""
        self.add(f"{begin}{ifelse}{{")
        self.push_indent()

    def close_condition(self) -> None:
        """ Closes a condition. """
        self.pop_indent()
        self.add("}")

    @contextmanager
    def condition(self, expression: Optional[str]) -> Iterator[None]:
        """ Opens a condition context. """
        self.open_condition(expression)
        yield
        self.close_condition()

    @contextmanager
    def first_condition(self, expression: Optional[str]) -> Iterator[None]:
        """ Opens the first condition context. """
        self.open_condition(expression, False)
        yield
        self.pop_indent()

    @contextmanager
    def next_condition(self, expression: Optional[str]) -> Iterator[None]:
        """ Opens the next condition context. """
        self.open_condition(expression, True)
        yield
        self.pop_indent()

    @contextmanager
    def final_condition(self, expression: Optional[str]) -> Iterator[None]:
        """ Opens the final condition context. """
        self.open_condition(expression, True)
        yield
        self.close_condition()

    def add_brief_description(self, description: Optional[str]) -> None:
        """ Adds a brief description. """
        self.wrap(description, initial_indent="@brief ")

    def add_param_description(
            self,
            params: Iterable[Dict[str, str]],
            substitute: Callable[[Optional[str]], str] = _make_str) -> None:
        """ Adds a list of parameter descriptions. """
        for param in params:
            self.wrap(param["name"] + " " + substitute(param["description"]),
                      initial_indent=_PARAM[param["dir"]])

    def add_description_block(self, brief: Optional[str],
                              description: Optional[str]) -> None:
        """ Adds a description block. """
        if brief or description:
            with self.doxygen_block():
                self.add_brief_description(brief)
                self.wrap(description)
            self.gap = False

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
            self.wrap(description)

    @contextmanager
    def header_guard(self, filename: str) -> Iterator[None]:
        """ Opens a header guard context. """
        guard = "_" + _NOT_ALPHANUM.sub("_", filename).upper()
        self.add([f"#ifndef {guard}", f"#define {guard}"])
        yield
        self.add(f"#endif /* {guard} */")

    @contextmanager
    def extern_c(self) -> Iterator[None]:
        """ Opens an extern "C" context. """
        self.add(["#ifdef __cplusplus", "extern \"C\" {", "#endif"])
        yield
        self.add(["#ifdef __cplusplus", "}", "#endif"])

    def add_paragraph(self, name: str,
                      content: Optional[GenericContent]) -> None:
        """ Adds a Doxygen paragraph block. """
        if content:
            self.add(f"@par {name}")
            self.gap = False
            last = len(self.lines)
            self.doxyfy(content)
            if self._empty_line_indent in self.lines[last:]:
                self.lines.insert(last, f"{self._indent}@parblock")
                self.lines.append(f"{self._indent}@endparblock")


def get_value_doxygen_function(ctx: ItemGetValueContext) -> Any:
    """ Gets a value as a function for Doxygen markup. """
    return f"{ctx.value[ctx.key]}()"


def get_value_doxygen_group(ctx: ItemGetValueContext) -> Any:
    """ Gets a value as a group reference for Doxygen markup. """
    return f"@ref {ctx.value['identifier']}"


def get_value_double_colon(ctx: ItemGetValueContext) -> Any:
    """ Gets a value with a :: prefix. """
    return f"::{ctx.value[ctx.key]}"


def get_value_hash(ctx: ItemGetValueContext) -> Any:
    """ Gets a value with a # prefix. """
    return f"#{ctx.value[ctx.key]}"


class ExpressionMapper:
    """ Maps symbols and operations to form a C expression. """

    # pylint: disable=no-self-use
    def map_bool(self, value: bool) -> str:
        """ Maps a boolean value to build an expression. """
        return str(int(value))

    # pylint: disable=no-self-use
    def map_symbol(self, symbol: str) -> str:
        """ Maps a symbol to build an expression. """
        return f"defined({symbol})"

    def op_and(self) -> str:
        """ Returns the and operator. """
        return " && "

    def op_or(self) -> str:
        """ Returns the or operator. """
        return " || "

    def op_not(self, symbol: str) -> str:
        """ Returns the negation of the symbol. """
        return f"!{symbol}"


class PythonExpressionMapper(ExpressionMapper):
    """ Maps symbols and operations to form a Python expression. """

    # pylint: disable=no-self-use
    def map_bool(self, value: bool) -> str:
        return str(value)

    # pylint: disable=no-self-use
    def map_symbol(self, symbol: str) -> str:
        return symbol

    def op_and(self) -> str:
        return " and "

    def op_or(self) -> str:
        return " or "

    def op_not(self, symbol: str) -> str:
        return f"not {symbol}"


def _to_expression_op(enabled_by: Any, mapper: ExpressionMapper,
                      operation: str) -> str:
    symbols = [
        _to_expression(next_enabled_by, mapper)
        for next_enabled_by in enabled_by
    ]
    if len(symbols) == 1:
        return symbols[0]
    return f"({operation.join(symbols)})"


def _to_expression_op_and(enabled_by: Any, mapper: ExpressionMapper) -> str:
    return _to_expression_op(enabled_by, mapper, mapper.op_and())


def _to_expression_op_not(enabled_by: Any, mapper: ExpressionMapper) -> str:
    return mapper.op_not(_to_expression(enabled_by, mapper))


def _to_expression_op_or(enabled_by: Any, mapper: ExpressionMapper) -> str:
    return _to_expression_op(enabled_by, mapper, mapper.op_or())


_TO_EXPRESSION_OP = {
    "and": _to_expression_op_and,
    "not": _to_expression_op_not,
    "or": _to_expression_op_or
}


def _to_expression(enabled_by: Any, mapper: ExpressionMapper) -> str:
    if isinstance(enabled_by, bool):
        return mapper.map_bool(enabled_by)
    if isinstance(enabled_by, list):
        return _to_expression_op_or(enabled_by, mapper)
    if isinstance(enabled_by, dict):
        if len(enabled_by) == 1:
            key = next(iter(enabled_by))
            return _TO_EXPRESSION_OP[key](enabled_by[key], mapper)
        raise ValueError
    return mapper.map_symbol(enabled_by)


def enabled_by_to_exp(enabled_by: Any, mapper: ExpressionMapper) -> str:
    """
    Returns an expression for an enabled-by attribute value.
    """
    exp = _to_expression(enabled_by, mapper)
    if exp.startswith("("):
        return exp[1:-1]
    return exp


_CAMEL_CASE_TO_UPPER = re.compile(r"\s+(.)")
_CAMEL_CASE_DISCARD = re.compile(r"[^ \t\n\r\f\va-zA-Z0-9]")


def to_camel_case(name: str) -> str:
    """ Returns the name in CamelCase. """
    return name[0].upper() + _CAMEL_CASE_TO_UPPER.sub(
        lambda match: match.group(1).upper(),
        _CAMEL_CASE_DISCARD.sub(" ", name[1:].replace("+", "X")))
