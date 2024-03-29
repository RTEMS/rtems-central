# SPDX-License-Identifier: BSD-2-Clause
""" This module provides classes for Sphinx content generation. """

# Copyright (C) 2019, 2022 embedded brains GmbH & Co. KG
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
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Union

from rtemsspec.content import Content, get_value_header_file, \
     get_value_plural, make_lines, to_camel_case
from rtemsspec.items import Item, ItemGetValue, ItemGetValueContext, ItemMapper

GenericContent = Union[str, List[str], "Content"]
GenericContentIterable = Union[Iterable[str], Iterable[List[str]],
                               Iterable[GenericContent]]

_HEADER_LEVELS = ["#", "*", "=", "-", "^", "\""]


def get_reference(label: str, name: Optional[str] = None) -> str:
    """ Returns the reference to the specified label. """
    if name:
        return f":ref:`{name} <{label}>`"
    return f":ref:`{label}`"


def make_label(name: str) -> str:
    """ Returns the label for the specified name. """
    return to_camel_case(name.strip())


def _simple_sep(maxi: Iterable[int]) -> str:
    return " ".join(f"{'=' * width}" for width in maxi)


def _simple_row(row: Iterable[str], maxi: Iterable[int]) -> str:
    line = " ".join(f"{cell:{width}}" for cell, width in zip(row, maxi))
    return line.rstrip()


def _grid_sep(maxi: Iterable[int], sep: str) -> str:
    return f"+{sep}" + f"{sep}+{sep}".join(f"{sep * width}"
                                           for width in maxi) + f"{sep}+"


def _grid_row(row: Iterable[str], maxi: Iterable[int]) -> str:
    line = " | ".join(f"{cell:{width}}" for cell, width in zip(row, maxi))
    return f"| {line} |"


class SphinxContent(Content):
    """ This class builds Sphinx content. """

    # pylint: disable=too-many-public-methods
    def __init__(self, section_level: int = 2):
        super().__init__("CC-BY-SA-4.0", True)
        self._tab = "    "
        self._section_level = section_level
        self._label_stack = [""]
        self._section_stack: List[str] = []

    def get_sections(self) -> List[str]:
        """ Gets the list of sections of the current scope. """
        return self._section_stack

    @property
    def label(self) -> str:
        """ This is the top of the label stack. """
        return self._label_stack[-1]

    def get_label(self, label_tail: str = "") -> str:
        """
        Returns the concatenation of the top of the label stack and the label
        tail.
        """
        return f"{self.label}{label_tail}"

    def push_label(self, label: str) -> None:
        """ Pushes the label to the label stack. """
        self._label_stack.append(label)

    def push_label_tail(self, label_tail: str) -> str:
        """
        Makes a label from the concatenation of the top of the label stack and
        the label tail.  Pushes this label to the label stack and returns it.
        """
        label = self.get_label(label_tail)
        self.push_label(label)
        return label

    def pop_label(self) -> None:
        """ Pops the top from the label stack. """
        self._label_stack.pop()

    @contextmanager
    def label_scope(self, label: str) -> Iterator[None]:
        """ Opens a label scope context. """
        self.push_label(label)
        yield
        self.pop_label()

    def add_label(self, label: str) -> None:
        """ Adds a label. """
        self.add(".. _" + label.strip() + ":")

    def add_header(self, name, level=2) -> None:
        """ Adds a header. """
        name = name.strip()
        self.add([name, _HEADER_LEVELS[level] * len(name)])

    def add_rubric(self, name: str) -> None:
        """ Adds a rubric. """
        self.add(f".. rubric:: {name}")

    def add_image(self, base: str, width: Optional[str] = None) -> None:
        """
        Adds an image associated with the base file name.

        The image will have the optional width.
        """
        options = [":align: center"]
        if width is not None:
            options.append(f":width: {width}")
        with self.directive("image", base, options):
            pass

    def add_index_entries(self, entries) -> None:
        """ Adds a list of index entries the content. """
        self.add([".. index:: " + entry for entry in make_lines(entries)])

    def add_definition_item(self,
                            name: GenericContent,
                            definition: GenericContent,
                            wrap: bool = False) -> None:
        """ Adds a definition item the content. """

        @contextmanager
        def _definition_item_context(content: Content) -> Iterator[None]:
            content.append(name)
            content.push_indent()
            yield
            content.pop_indent()

        if wrap:
            self.wrap(definition, context=_definition_item_context)
        else:
            self.add(definition, context=_definition_item_context)

    @contextmanager
    def definition_item(self, name: GenericContent) -> Iterator[None]:
        """ Opens a definition item context. """
        self.wrap(name)
        self.push_indent()
        yield
        self.pop_indent()

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
                     label_tail: Optional[str] = None,
                     label: Optional[str] = None) -> str:
        """ Opens a section. """
        if label is None:
            if label_tail is None:
                label_tail = make_label(name)
            label = self.push_label_tail(label_tail)
        else:
            self.push_label(label)
        self.add_label(label)
        self.add_header(name, self._section_level + len(self._section_stack))
        self._section_stack.append(name)
        return label

    def close_section(self) -> None:
        """ Closes a section. """
        self.pop_label()
        self._section_stack.pop()

    @contextmanager
    def section(self,
                name: str,
                label_tail: Optional[str] = None,
                label: Optional[str] = None) -> Iterator[str]:
        """ Opens a section context. """
        yield self.open_section(name, label_tail, label)
        self.close_section()

    def open_latex_tiny(self, size: str = "tiny") -> None:
        """ Opens a LaTeX tiny environment. """
        with self.directive("raw", "latex"):
            self.add(f"\\begin{{{size}}}")

    def close_latex_tiny(self, size: str = "tiny") -> None:
        """ Closes a LaTeX tiny environment. """
        with self.directive("raw", "latex"):
            self.add(f"\\end{{{size}}}")

    @contextmanager
    def latex_tiny(self, size: str = "tiny") -> Iterator[None]:
        """ Opens a LaTeX tiny environment. """
        self.open_latex_tiny(size)
        yield
        self.close_latex_tiny(size)

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

    def open_comment_block(self) -> None:
        """ Opens a comment block. """
        self.push_indent(".. ", "..")

    def add_simple_table(self, rows: Sequence[Iterable[str]]) -> None:
        """ Adds a simple table. """
        if not rows:
            return
        maxi = tuple(map(len, rows[0]))
        for row in rows:
            row_lengths = tuple(map(len, row))
            maxi = tuple(map(max, zip(maxi, row_lengths)))
        sep = _simple_sep(maxi)
        lines = [sep, _simple_row(rows[0], maxi), sep]
        lines.extend(_simple_row(row, maxi) for row in rows[1:])
        lines.append(sep)
        with self.directive("table", options=[":class: longtable"]):
            self.add(lines)

    def add_grid_table(self, rows: Sequence[Iterable[str]],
                       widths: List[int]) -> None:
        """ Adds a grid table. """
        if not rows:
            return
        maxi = tuple(map(len, rows[0]))
        for row in rows:
            row_lengths = tuple(map(len, row))
            maxi = tuple(map(max, zip(maxi, row_lengths)))
        begin_end = _grid_sep(maxi, "-")
        lines = [begin_end, _grid_row(rows[0], maxi), _grid_sep(maxi, "=")]
        for index, row in enumerate(rows[1:]):
            if index > 0:
                sep = ""
                for cell, width in zip(row, maxi):
                    if cell:
                        sep += f"+{'-' * (width + 2)}"
                    else:
                        sep += f"+{' ' * (width + 2)}"
                lines.append(sep + "+")
            lines.append(_grid_row(row, maxi))
        lines.append(begin_end)
        with self.directive(
                "table",
                options=[
                    ":class: longtable",
                    f":widths: {','.join(str(width) for width in widths)}"
                ]):
            self.add(lines)


def get_value_sphinx_glossary_term(ctx: ItemGetValueContext) -> Any:
    """ Gets a gossary term. """
    term = ctx.value[ctx.key]
    term_2 = ctx.item["_term"]
    if term == term_2:
        return f":term:`{term}`"
    return f":term:`{term} <{term_2}>`"


def get_value_sphinx_glossary_plural(ctx: ItemGetValueContext) -> Any:
    """ Gets a gossary term in plural form. """
    return f":term:`{get_value_plural(ctx)} <{ctx.item['_term']}>`"


def _get_appl_config_option(ctx: ItemGetValueContext) -> Any:
    return f":ref:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_data(ctx: ItemGetValueContext) -> Any:
    return f":c:data:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_macro(ctx: ItemGetValueContext) -> Any:
    return f":c:macro:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_function(ctx: ItemGetValueContext) -> Any:
    return f":c:func:`{ctx.value[ctx.key]}`"


def _get_value_sphinx_type(ctx: ItemGetValueContext) -> Any:
    if ctx.item.get("definition-kind", "") == "struct-only":
        return f"``struct {ctx.value[ctx.key]}``"
    return f":c:type:`{ctx.value[ctx.key]}`"


def _compound_kind(ctx: ItemGetValueContext) -> str:
    type_name = ctx.item.type
    return f"{type_name[type_name.rfind('-') + 1:]} "


def _get_value_sphinx_compound(ctx: ItemGetValueContext) -> Any:
    return f"``{_compound_kind(ctx)}{ctx.value[ctx.key]}``"


def _get_value_sphinx_ref(ctx: ItemGetValueContext,
                          get_value: ItemGetValue,
                          postfix: str = "",
                          prefix: str = "") -> Any:
    for ref in ctx.item["references"]:
        ref_type = ref["type"]
        identifier = ref["identifier"]
        name_ref = f"`{prefix}{ctx.value[ctx.key]}{postfix} <{identifier}>`"
        if ref_type == "document" and ref["name"] == "c-user":
            return f":ref:{name_ref}"
        if ref_type == "url":
            return f"{name_ref}_"
    return get_value(ctx)


def _get_value_sphinx_unspecified_define(ctx: ItemGetValueContext) -> Any:
    return _get_value_sphinx_ref(ctx, _get_value_sphinx_macro)


def _get_value_sphinx_unspecified_function(ctx: ItemGetValueContext) -> Any:
    return _get_value_sphinx_ref(ctx, _get_value_sphinx_function, "()")


def _get_value_sphinx_unspecified_group(ctx: ItemGetValueContext) -> Any:
    for ref in ctx.item["references"]:
        ref_type = ref["type"]
        identifier = ref["identifier"]
        if ref_type == "document" and ref["name"] == "c-user":
            return f":ref:`{identifier}`"
        if ref_type == "url":
            return f"`{ctx.value[ctx.key]} <{identifier}>`_"
    return ctx.value[ctx.key]


def _get_value_sphinx_unspecified_type(ctx: ItemGetValueContext) -> Any:
    return _get_value_sphinx_ref(ctx, _get_value_sphinx_type)


def _get_value_sphinx_unspecified_compound(ctx: ItemGetValueContext) -> Any:
    return _get_value_sphinx_ref(ctx,
                                 _get_value_sphinx_compound,
                                 prefix=_compound_kind(ctx))


class SphinxMapper(ItemMapper):
    """ Sphinx item mapper. """

    def __init__(self, item: Item, recursive: bool = False):
        super().__init__(item, recursive)
        self.add_get_value("glossary/term:/term",
                           get_value_sphinx_glossary_term)
        self.add_get_value("glossary/term:/plural",
                           get_value_sphinx_glossary_plural)
        self.add_get_value("interface/appl-config-option/feature-enable:/name",
                           _get_value_sphinx_data)
        self.add_get_value("interface/appl-config-option/feature:/name",
                           _get_value_sphinx_data)
        self.add_get_value("interface/appl-config-option/initializer:/name",
                           _get_value_sphinx_data)
        self.add_get_value("interface/appl-config-option/integer:/name",
                           _get_value_sphinx_data)
        self.add_get_value("interface/define:/name", _get_value_sphinx_macro)
        self.add_get_value("interface/enum:/name", _get_value_sphinx_type)
        self.add_get_value("interface/enumerator:/name",
                           _get_value_sphinx_macro)
        self.add_get_value("interface/function:/name",
                           _get_value_sphinx_function)
        self.add_get_value("interface/header-file:/path",
                           get_value_header_file)
        self.add_get_value("interface/macro:/name", _get_value_sphinx_function)
        self.add_get_value("interface/struct:/name", _get_value_sphinx_type)
        self.add_get_value("interface/typedef:/name", _get_value_sphinx_type)
        self.add_get_value("interface/union:/name", _get_value_sphinx_type)
        self.add_get_value("interface/unspecified-define:/name",
                           _get_value_sphinx_unspecified_define)
        self.add_get_value("interface/unspecified-enumerator:/name",
                           _get_value_sphinx_unspecified_define)
        self.add_get_value("interface/unspecified-function:/name",
                           _get_value_sphinx_unspecified_function)
        self.add_get_value("interface/unspecified-group:/name",
                           _get_value_sphinx_unspecified_group)
        self.add_get_value("interface/unspecified-enum:/name",
                           _get_value_sphinx_unspecified_type)
        self.add_get_value("interface/unspecified-struct:/name",
                           _get_value_sphinx_unspecified_compound)
        self.add_get_value("interface/unspecified-typedef:/name",
                           _get_value_sphinx_unspecified_type)
        self.add_get_value("interface/unspecified-union:/name",
                           _get_value_sphinx_unspecified_compound)


def sanitize_name(name: str) -> str:
    """ Removes leading underscores from the name. """
    return name.lstrip("_")


def get_value_sphinx_param(ctx: ItemGetValueContext) -> Any:
    """ Gets a function or macro parameter. """
    return f"``{sanitize_name(ctx.value[ctx.key])}``"


class SphinxInterfaceMapper(SphinxMapper):
    """ Sphinx item mapper for the interface documentation. """

    def __init__(self,
                 item: Item,
                 group_uids: List[str],
                 recursive: bool = False):
        super().__init__(item, recursive)
        self._group_uids = set(group_uids)
        self.add_get_value("interface/appl-config-option/feature-enable:/name",
                           _get_appl_config_option)
        self.add_get_value("interface/appl-config-option/feature:/name",
                           _get_appl_config_option)
        self.add_get_value("interface/appl-config-option/initializer:/name",
                           _get_appl_config_option)
        self.add_get_value("interface/appl-config-option/integer:/name",
                           _get_appl_config_option)
        self.add_get_value("interface/enum:/name", self._get_type)
        self.add_get_value("interface/function:/name", self._get_function)
        self.add_get_value("interface/function:/params/name",
                           get_value_sphinx_param)
        self.add_get_value("interface/group:/name", self._get_group)
        self.add_get_value("interface/macro:/name", self._get_function)
        self.add_get_value("interface/macro:/params/name",
                           get_value_sphinx_param)
        self.add_get_value("interface/struct:/name", self._get_compound)
        self.add_get_value("interface/typedef:/name", self._get_type)
        self.add_get_value("interface/union:/name", self._get_compound)

    def _get_reference(self, ctx: ItemGetValueContext, name: str,
                       fallback: str) -> str:
        for group in ctx.item.parents("interface-ingroup"):
            if group.uid in self._group_uids:
                return get_reference(make_label(f"Interface {name}"))
        return fallback

    def _get_compound(self, ctx: ItemGetValueContext) -> Any:
        if ctx.item["definition-kind"] in ["struct-only", "union-only"]:
            prefix = f"{ctx.item['interface-type']} "
        else:
            prefix = ""
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f"``{prefix}{name}``")

    def _get_function(self, ctx: ItemGetValueContext) -> Any:
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f":c:func:`{name}`")

    def _get_type(self, ctx: ItemGetValueContext) -> Any:
        name = ctx.value[ctx.key]
        return self._get_reference(ctx, name, f":c:type:`{name}`")

    def _get_group(self, ctx: ItemGetValueContext) -> Any:
        if ctx.item.uid in self._group_uids:
            return get_reference(ctx.value["identifier"])
        return ctx.value[ctx.key]
