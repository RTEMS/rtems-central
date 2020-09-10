# SPDX-License-Identifier: BSD-2-Clause
""" This module provides functions for the generation of interfaces. """

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

from contextlib import contextmanager
import os
from typing import Any, Callable, Dict, Iterator, List, Union

from rtemsspec.content import CContent, CInclude, enabled_by_to_exp, \
    ExpressionMapper, get_value_double_colon, get_value_doxygen_function, \
    get_value_hash
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]
Lines = Union[str, List[str]]
GetLines = Callable[["Node", Item, Any], Lines]


def _get_ingroups(item: Item) -> ItemMap:
    ingroups = {}  # type: ItemMap
    for link in item.links_to_parents():
        if link.role == "interface-ingroup":
            ingroups[link.item.uid] = link.item
    return ingroups


def _get_group_identifiers(groups: ItemMap) -> List[str]:
    return [item["identifier"] for item in groups.values()]


def _forward_declaration(item: Item) -> str:
    target = next(item.parents("interface-target"))
    return f"{target['interface-type']} {target['name']}"


def _get_value_forward_declaration(ctx: ItemGetValueContext) -> Any:
    return _forward_declaration(ctx.item)


class _InterfaceMapper(ItemMapper):
    def __init__(self, node: "Node"):
        super().__init__(node.item)
        self._node = node
        self._code_or_doc = "doc"
        self.add_get_value("interface/forward-declaration:code:/name",
                           _get_value_forward_declaration)
        self.add_get_value("interface/forward-declaration:doc:/name",
                           _get_value_forward_declaration)
        self.add_get_value("interface/function:doc:/name",
                           get_value_doxygen_function)
        self.add_get_value("interface/enumerator:doc:/name",
                           get_value_double_colon)
        self.add_get_value("interface/typedef:doc:/name",
                           get_value_double_colon)
        self.add_get_value("interface/define:doc:/name", get_value_hash)
        self.add_get_value("interface/enum:doc:/name", get_value_hash)
        self.add_get_value("interface/macro:doc:/name", get_value_hash)
        self.add_get_value("interface/variable:doc:/name", get_value_hash)
        for opt in ["feature-enable", "feature", "initializer", "integer"]:
            name = f"interface/appl-config-option/{opt}:doc:/name"
            self.add_get_value(name, get_value_hash)

    @contextmanager
    def code(self) -> Iterator[None]:
        """ Enables code mapping. """
        code_or_doc = self._code_or_doc
        self._code_or_doc = "code"
        yield
        self._code_or_doc = code_or_doc

    def get_value(self, ctx: ItemGetValueContext) -> Any:
        if self._code_or_doc == "code" and ctx.item["type"] == "interface":
            node = self._node
            header_file = node.header_file
            if ctx.item["interface-type"] == "enumerator":
                for link in ctx.item.links_to_children():
                    if link.role == "interface-enumerator":
                        header_file.add_includes(link.item)
            else:
                header_file.add_includes(ctx.item)
            header_file.add_potential_edge(node, ctx.item)
        return super().get_value(
            ItemGetValueContext(ctx.item, f"{self._code_or_doc}:{ctx.path}",
                                ctx.value, ctx.key, ctx.index))

    def enabled_by_to_defined(self, enabled_by: str) -> str:
        """
        Maps an item-level enabled-by attribute value to the corresponding
        defined expression.
        """
        return self._node.header_file.enabled_by_defined[enabled_by]


class _InterfaceExpressionMapper(ExpressionMapper):
    def __init__(self, mapper: _InterfaceMapper):
        super().__init__()
        self._mapper = mapper

    def map_symbol(self, symbol: str) -> str:
        with self._mapper.code():
            return self._mapper.substitute(symbol)


class _ItemLevelExpressionMapper(ExpressionMapper):
    def __init__(self, mapper: _InterfaceMapper):
        super().__init__()
        self._mapper = mapper

    def map_symbol(self, symbol: str) -> str:
        with self._mapper.code():
            return self._mapper.substitute(
                self._mapper.enabled_by_to_defined(symbol))


class _HeaderExpressionMapper(ExpressionMapper):
    def __init__(self, item: Item, enabled_by_defined: Dict[str, str]):
        super().__init__()
        self._mapper = ItemMapper(item)
        self._enabled_by_defined = enabled_by_defined

    def map_symbol(self, symbol: str) -> str:
        return self._mapper.substitute(self._enabled_by_defined[symbol])


def _add_definition(node: "Node", item: Item, prefix: str,
                    value: Dict[str, Any], get_lines: GetLines) -> CContent:
    content = CContent()
    default = value["default"]
    variants = value["variants"]
    if variants:
        ifelse = "#if "
        with node.mapper.prefix(os.path.join(prefix, "variants")):
            for variant in variants:
                enabled_by = enabled_by_to_exp(
                    variant["enabled-by"],
                    _InterfaceExpressionMapper(node.mapper))
                content.append(f"{ifelse}{enabled_by}")
                with content.indent():
                    content.append(get_lines(node, item,
                                             variant["definition"]))
                ifelse = "#elif "
        if default is not None:
            content.append("#else")
            with node.mapper.prefix(os.path.join(prefix, "default")):
                with content.indent():
                    content.append(get_lines(node, item, default))
        content.append("#endif")
    else:
        with node.mapper.prefix(os.path.join(prefix, "default")):
            content.append(get_lines(node, item, default))
    return content


class Node:
    """ Nodes of a header file. """
    def __init__(self, header_file: "_HeaderFile", item: Item,
                 ingroups: ItemMap):
        self.header_file = header_file
        self.item = item
        self.ingroups = ingroups
        self.in_edges = {}  # type: ItemMap
        self.out_edges = {}  # type: ItemMap
        self.content = CContent()
        self.mapper = _InterfaceMapper(self)

    def __lt__(self, other: "Node") -> bool:
        return self.item.uid < other.item.uid

    @contextmanager
    def _enum_struct_or_union(self) -> Iterator[None]:
        self.content.add(self._get_description(self.item, self.ingroups))
        name = self.item["name"]
        typename = self.item["interface-type"]
        kind = self.item["definition-kind"]
        if kind == f"{typename}-only":
            self.content.append(f"{typename} {name} {{")
        elif kind == "typedef-only":
            self.content.append(f"typedef {typename} {{")
        else:
            self.content.append(f"typedef {typename} {name} {{")
        self.content.push_indent()
        yield
        self.content.pop_indent()
        if kind == f"{typename}-only":
            self.content.append("};")
        else:
            self.content.append(f"}} {name};")

    def _generate(self) -> None:
        _NODE_GENERATORS[self.item["interface-type"]](self)

    def generate(self) -> None:
        """ Generates a node to generate the node content. """
        enabled_by = self.item["enabled-by"]
        if not isinstance(enabled_by, bool) or not enabled_by:
            mapper = _ItemLevelExpressionMapper(self.mapper)
            self.content.add(f"#if {enabled_by_to_exp(enabled_by, mapper)}")
            with self.content.indent():
                self._generate()
            self.content.add("#endif")
        else:
            self._generate()

    def generate_compound(self) -> None:
        """ Generates a compound (struct or union). """
        with self._enum_struct_or_union():
            for index, definition in enumerate(self.item["definition"]):
                self.content.add(
                    _add_definition(self, self.item, f"definition[{index}]",
                                    definition, Node._get_compound_definition))

    def generate_enum(self) -> None:
        """ Generates an enum. """
        with self._enum_struct_or_union():
            enumerators = []  # type: List[CContent]
            for link in self.item.links_to_parents():
                if link.role != "interface-enumerator":
                    continue
                enumerator = self._get_description(link.item, {})
                enumerator.append(
                    _add_definition(self, link.item, "definition",
                                    link.item["definition"],
                                    Node._get_enumerator_definition))
                enumerators.append(enumerator)
            for enumerator in enumerators[0:-1]:
                enumerator.lines[-1] += ","
                enumerator.append("")
                self.content.append(enumerator)
            try:
                self.content.append(enumerators[-1])
            except IndexError:
                pass

    def generate_define(self) -> None:
        """ Generates a define. """
        self._add_generic_definition(Node._get_define_definition)

    def generate_forward_declaration(self) -> None:
        """ Generates a forward declaration. """
        self.content.append([
            "", "/* Forward declaration */",
            _forward_declaration(self.item) + ";"
        ])

    def generate_function(self) -> None:
        """ Generates a function. """
        self._add_generic_definition(Node._get_function_definition)

    def generate_group(self) -> None:
        """ Generates a group. """
        self.header_file.add_ingroup(self.item)
        for ingroup in self.ingroups.values():
            self.header_file.add_potential_edge(self, ingroup)
        self.content.add_group(self.item["identifier"], self.item["name"],
                               _get_group_identifiers(self.ingroups),
                               self.item["brief"], self.item["description"])

    def generate_macro(self) -> None:
        """ Generates a macro. """
        self._add_generic_definition(Node._get_macro_definition)

    def generate_typedef(self) -> None:
        """ Generates a typedef. """
        self._add_generic_definition(Node._get_typedef_definition)

    def generate_variable(self) -> None:
        """ Generates a variable. """
        self._add_generic_definition(Node._get_variable_definition)

    def substitute_code(self, text: str) -> str:
        """
        Performs a variable substitution on code using the item mapper of the
        node.
        """
        if text:
            with self.mapper.code():
                return self.mapper.substitute(text.strip("\n"))
        return text

    def substitute_text(self, text: str) -> str:
        """
        Performs a variable substitution on a description using the item mapper
        of the node.
        """
        if text:
            return self.mapper.substitute(text.strip("\n"))
        return text

    def _get_compound_definition(self, item: Item, definition: Any) -> Lines:
        content = CContent()
        content.add_description_block(
            self.substitute_text(definition["brief"]),
            self.substitute_text(definition["description"]))
        kind = definition["kind"]
        if kind == "member":
            member = self.substitute_code(definition["definition"]) + ";"
            content.append(member.split("\n"))
        else:
            content.append(f"{kind} {{")
            content.gap = False
            with content.indent():
                for index, compound_member in enumerate(
                        definition["definition"]):
                    content.add(
                        _add_definition(self, item, f"definition[{index}]",
                                        compound_member,
                                        Node._get_compound_definition))
            name = definition["name"]
            content.append(f"}} {name};")
        return content.lines

    def _get_enumerator_definition(self, item: Item, definition: Any) -> Lines:
        name = item["name"]
        if definition:
            return f"{name} = {self.substitute_code(definition)}"
        return f"{name}"

    def _get_define_definition(self, item: Item, definition: Any) -> Lines:
        name = item["name"]
        value = self.substitute_code(definition)
        if value:
            return f"#define {name} {value}".split("\n")
        return f"#define {name}"

    def _get_function_definition(self, item: Item, definition: Any) -> Lines:
        content = CContent()
        name = item["name"]
        ret = self.substitute_code(definition["return"])
        params = [
            self.substitute_code(param) for param in definition["params"]
        ]
        body = definition["body"]
        if body:
            with content.function("static inline " + ret, name, params):
                content.add(self.substitute_code(body))
        else:
            content.declare_function(ret, name, params)
        return content.lines

    def _get_macro_definition(self, item: Item, definition: Any) -> Lines:
        name = item["name"]
        params = [param["name"] for param in item["params"]]
        if params:
            param_line = " " + ", ".join(params) + " "
        else:
            param_line = ""
        line = f"#define {name}({param_line})"
        if len(line) > 79:
            param_block = ", \\\n  ".join(params)
            line = f"#define {name}( \\\n  {param_block} \\\n)"
        if not definition:
            return line
        body_lines = self.substitute_code(definition).split("\n")
        if len(body_lines) == 1 and len(line + body_lines[0]) <= 79:
            body = " "
        else:
            body = " \\\n  "
        body += " \\\n  ".join(body_lines)
        return line + body

    def _get_typedef_definition(self, _item: Item, definition: Any) -> Lines:
        return f"typedef {self.substitute_code(definition)};"

    def _get_variable_definition(self, _item: Item, definition: Any) -> Lines:
        return f"extern {self.substitute_code(definition)};"

    def _get_description(self, item: Item, ingroups: ItemMap) -> CContent:
        content = CContent()
        with content.doxygen_block():
            content.add_ingroup(_get_group_identifiers(ingroups))
            content.add_brief_description(self.substitute_text(item["brief"]))
            content.wrap(self.substitute_text(item["description"]))
            content.wrap(self.substitute_text(item["notes"]))
            if "params" in item:
                content.add_param_description(item["params"],
                                              self.substitute_text)
            if "return" in item:
                ret = item["return"]
                for retval in ret["return-values"]:
                    content.wrap(self.substitute_text(retval["description"]),
                                 initial_indent=self.substitute_text(
                                     f"@retval {retval['value']} "))
                content.wrap(self.substitute_text(ret["return"]),
                             initial_indent="@return ")
        return content

    def _add_generic_definition(self, get_lines: GetLines) -> None:
        self.content.add(self._get_description(self.item, self.ingroups))
        self.content.append(
            _add_definition(self, self.item, "definition",
                            self.item["definition"], get_lines))


_NODE_GENERATORS = {
    "enum": Node.generate_enum,
    "define": Node.generate_define,
    "forward-declaration": Node.generate_forward_declaration,
    "function": Node.generate_function,
    "group": Node.generate_group,
    "macro": Node.generate_macro,
    "struct": Node.generate_compound,
    "typedef": Node.generate_typedef,
    "union": Node.generate_compound,
    "variable": Node.generate_variable,
}


class _HeaderFile:
    """ A header file. """
    def __init__(self, item: Item, enabled_by_defined: Dict[str, str]):
        self._item = item
        self._content = CContent()
        self._ingroups = {}  # type: ItemMap
        self._includes = []  # type: List[Item]
        self._nodes = {}  # type: Dict[str, Node]
        self.enabled_by_defined = enabled_by_defined

    def add_includes(self, item: Item) -> None:
        """ Adds the includes of the item to the header file includes. """
        for link in item.links_to_parents():
            if link.role == "interface-placement" and link.item[
                    "interface-type"] == "header-file":
                self._includes.append(link.item)

    def add_ingroup(self, item: Item) -> None:
        """ Adds an ingroup to the header file. """
        self._ingroups[item.uid] = item

    def _add_child(self, item: Item) -> None:
        ingroups = _get_ingroups(item)
        if item["interface-type"] != "group":
            self._ingroups.update(ingroups)
        self._nodes[item.uid] = Node(self, item, ingroups)
        self._content.register_license_and_copyrights_of_item(item)

    def add_potential_edge(self, node: Node, item: Item) -> None:
        """
        Adds a potential edge from a node to another node identified by an
        item.
        """
        if item.uid in self._nodes and item.uid != node.item.uid:
            node.out_edges[item.uid] = item
            self._nodes[item.uid].in_edges[node.item.uid] = node.item

    def _resolve_ingroups(self, node: Node) -> None:
        for ingroup in node.ingroups.values():
            self.add_potential_edge(node, ingroup)

    def generate_nodes(self) -> None:
        """ Generates all nodes of this header file. """
        for link in self._item.links_to_children():
            if link.role == "interface-placement":
                self._add_child(link.item)
        for node in self._nodes.values():
            self._resolve_ingroups(node)
            node.generate()

    def _get_nodes_in_dependency_order(self) -> List[Node]:
        """
        Gets the nodes of this header file ordered according to node
        dependencies and UIDs.

        Performs a topological sort using Kahn's algorithm.
        """
        nodes_in_dependency_order = []  # type: List[Node]

        # Get incoming edge degrees for all nodes
        in_degree = {}  # type: Dict[str, int]
        for node in self._nodes.values():
            in_degree[node.item.uid] = len(node.in_edges)

        # Create a queue with all nodes with no incoming edges sorted by UID
        queue = []  # type: List[Node]
        for node in self._nodes.values():
            if in_degree[node.item.uid] == 0:
                queue.append(node)
        queue.sort(reverse=True)

        # Topological sort
        while queue:
            node = queue.pop(0)
            nodes_in_dependency_order.insert(0, node)

            # Sort by UID
            for uid in sorted(node.out_edges):
                in_degree[uid] -= 1
                if in_degree[uid] == 0:
                    queue.append(self._nodes[uid])

        return nodes_in_dependency_order

    def finalize(self) -> None:
        """ Finalizes the header file. """
        self._content.prepend_spdx_license_identifier()
        with self._content.file_block():
            self._content.add_ingroup(_get_group_identifiers(self._ingroups))
            self._content.add_brief_description(self._item["brief"])
        self._content.add_copyrights_and_licenses()
        self._content.add_automatically_generated_warning()
        with self._content.header_guard(self._item["path"]):
            exp_mapper = _HeaderExpressionMapper(self._item,
                                                 self.enabled_by_defined)
            includes = [
                CInclude(item["path"],
                         enabled_by_to_exp(item["enabled-by"], exp_mapper))
                for item in self._includes if item != self._item
            ]
            includes.extend([
                CInclude(link.item["path"],
                         enabled_by_to_exp(link["enabled-by"], exp_mapper))
                for link in self._item.links_to_parents()
                if link.role == "interface-include"
            ])
            self._content.add_includes(includes)
            with self._content.extern_c():
                for node in self._get_nodes_in_dependency_order():
                    self._content.add(node.content)

    def write(self, domain_path: str) -> None:
        """ Writes the header file. """
        self._content.write(
            os.path.join(domain_path, self._item["prefix"],
                         self._item["path"]))


def _generate_header_file(item: Item, domains: Dict[str, str],
                          enabled_by_defined: Dict[str, str]) -> None:
    domain = next(item.parents("interface-placement"))
    assert domain["interface-type"] == "domain"
    domain_path = domains.get(domain.uid, None)
    if domain_path is None:
        return
    header_file = _HeaderFile(item, enabled_by_defined)
    header_file.generate_nodes()
    header_file.finalize()
    header_file.write(domain_path)


def _visit_header_files(item: Item, domains: Dict[str, str],
                        enabled_by_defined: Dict[str, str]) -> None:
    for child in item.children():
        _visit_header_files(child, domains, enabled_by_defined)
    if item["type"] == "interface" and item["interface-type"] == "header-file":
        _generate_header_file(item, domains, enabled_by_defined)


def _gather_enabled_by_defined(item_level_interfaces: List[str],
                               item_cache: ItemCache) -> Dict[str, str]:
    enabled_by_defined = {}  # type: Dict[str, str]
    for uid in item_level_interfaces:
        for link in item_cache[uid].links_to_children():
            if link.role == "interface-placement":
                define = f"defined(${{{link.item.uid}:/name}})"
                enabled_by_defined[link.item["name"]] = define
    return enabled_by_defined


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates header files according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the interfaces.
    """
    enabled_by_defined = _gather_enabled_by_defined(
        config["item-level-interfaces"], item_cache)
    for item in item_cache.top_level.values():
        _visit_header_files(item, config["domains"], enabled_by_defined)
