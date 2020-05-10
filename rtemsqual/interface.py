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
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

from rtemsqual.content import CContent, enabled_by_to_exp, ExpressionMapper
from rtemsqual.items import Item, ItemCache, ItemMapper

ItemMap = Dict[str, Item]
Lines = Union[str, List[str]]
GetLines = Callable[["Node", Item, Any], Lines]


def _designator(name: str) -> str:
    return name.replace(" ", "")


def _get_ingroups(item: Item) -> ItemMap:
    ingroups = {}  # type: ItemMap
    for link in item.links_to_parents():
        if link["role"] == "interface-ingroup":
            ingroups[link.item.uid] = link.item
    return ingroups


def _ingroups_to_designators(ingroups: ItemMap) -> List[str]:
    return [_designator(item["group-name"]) for item in ingroups.values()]


def _forward_declaration(item: Item) -> str:
    target = item.map(item["interface-target"])
    return target["interface-type"] + " " + target["interface-name"]


class _InterfaceMapper(ItemMapper):
    def __init__(self, node: "Node"):
        super().__init__(node.item)
        self._node = node

    def __getitem__(self, identifier):
        item, value = self.map(identifier)
        if item["type"] == "interface":
            node = self._node
            header_file = node.header_file
            if item["interface-type"] == "enumerator":
                for link in item.links_to_children():
                    if link["role"] == "interface-enumerator":
                        header_file.add_includes(link.item)
            else:
                header_file.add_includes(item)
            header_file.add_potential_edge(node, item)
        return value

    def get_value(self, item: Item, _path: str, _value: Any, key: str,
                  _index: Optional[int]) -> Any:
        # pylint: disable=no-self-use
        if key == "interface-name" and item["type"] == "interface" and item[
                "interface-type"] == "forward-declaration":
            return _forward_declaration(item)
        raise KeyError

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

    def map(self, symbol: str) -> str:
        return self._mapper.substitute(symbol)


class _ItemLevelExpressionMapper(ExpressionMapper):
    def __init__(self, mapper: _InterfaceMapper):
        super().__init__()
        self._mapper = mapper

    def map(self, symbol: str) -> str:
        return self._mapper.substitute(
            self._mapper.enabled_by_to_defined(symbol))


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
        if default:
            content.append("#else")
            with node.mapper.prefix(os.path.join(prefix, "default")):
                with content.indent():
                    content.append(get_lines(node, item, default))
        content.append("#endif")
    else:
        with node.mapper.prefix(os.path.join(prefix, "default")):
            content.append(get_lines(node, item, default))
    return content


def _get_description(item: Item, ingroups: ItemMap) -> CContent:
    content = CContent()
    with content.doxygen_block():
        content.add_ingroup(_ingroups_to_designators(ingroups))
        content.add_brief_description(item["interface-brief"])
        content.add(content.wrap(item["interface-description"]))
        if "interface-params" in item:
            for param in item["interface-params"]:
                content.add(
                    content.wrap(param["name"] + " " + param["description"],
                                 intro=_PARAM[param["dir"]]))
        if "interface-return" in item:
            ret = item["interface-return"]
            for retval in ret["return-values"]:
                val = retval["value"]
                intro = f"@retval {val} "
                content.add(content.wrap(retval["description"], intro=intro))
            content.add(content.wrap(ret["return"], intro="@return "))
    return content


_PARAM = {
    None: "@param ",
    "in": "@param[in] ",
    "out": "@param[out] ",
    "inout": "@param[in,out] ",
}


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
        self.content.add(_get_description(self.item, self.ingroups))
        name = self.item["interface-name"]
        typename = self.item["interface-type"]
        kind = self.item["interface-definition-kind"]
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
        if enabled_by:
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
            self.content.append(
                _add_definition(self, self.item, "interface-definition",
                                self.item["interface-definition"],
                                Node._get_compound_definition))

    def generate_enum(self) -> None:
        """ Generates an enum. """
        with self._enum_struct_or_union():
            enumerators = []  # type: List[CContent]
            for link in self.item.links_to_parents():
                if link["role"] != "interface-enumerator":
                    continue
                enumerator = _get_description(link.item, {})
                enumerator.append(
                    _add_definition(self, link.item, "interface-definition",
                                    link.item["interface-definition"],
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
        name = self.item["group-name"]
        self.content.add_group(_designator(name), name,
                               _ingroups_to_designators(self.ingroups),
                               self.item["group-brief"],
                               self.item["group-description"])

    def generate_macro(self) -> None:
        """ Generates a macro. """
        self._add_generic_definition(Node._get_macro_definition)

    def generate_typedef(self) -> None:
        """ Generates a typedef. """
        self._add_generic_definition(Node._get_typedef_definition)

    def generate_variable(self) -> None:
        """ Generates a variable. """
        self._add_generic_definition(Node._get_variable_definition)

    def substitute(self, text: str) -> str:
        """
        Performs a variable substitution using the item mapper of the node.
        """
        return self.mapper.substitute(text.strip("\n"))

    def _get_compound_definition(self, item: Item, definition: Any) -> Lines:
        content = CContent()
        with content.doxygen_block():
            content.add_brief_description(definition["brief"])
            content.add(content.wrap(definition["description"]))
        kind = definition["kind"]
        if kind == "member":
            member = self.substitute(definition["definition"]) + ";"
            content.append(member.split("\n"))
        else:
            content.append(f"{kind} {{")
            content.gap = False
            with content.indent():
                index = 0
                for compound_member in definition["definition"]:
                    content.add(
                        _add_definition(self, item, f"definition[{index}]",
                                        compound_member,
                                        Node._get_compound_definition))
                    index += 1
            name = definition["name"]
            content.append(f"}} {name};")
        return content.lines

    def _get_enumerator_definition(self, item: Item, definition: Any) -> Lines:
        name = item["interface-name"]
        if definition:
            return f"{name} = {self.substitute(definition)}"
        return f"{name}"

    def _get_define_definition(self, item: Item, definition: Any) -> Lines:
        name = item["interface-name"]
        return f"#define {name} {self.substitute(definition)}".split("\n")

    def _get_function_definition(self, item: Item, definition: Any) -> Lines:
        ret = self.substitute(definition["return"])
        if "body" in definition:
            ret = "static inline " + ret
        name = item["interface-name"]
        space = "" if ret.endswith("*") else " "
        params = [self.substitute(param) for param in definition["params"]]
        param_line = ", ".join(params)
        line = f"{ret}{space}{name}({param_line})"
        if len(line) > 79:
            param_block = ",\n  ".join(params)
            line = f"{ret}{space}{name}(\n  {param_block}\n)"
        if "body" in definition:
            body = self.substitute("\n  ".join(
                definition["body"].strip("\n").split("\n")))
            line = f"""{line}
{{
  {body}
}}"""
        else:
            line += ";"
        return line

    def _get_macro_definition(self, item: Item, definition: Any) -> Lines:
        name = item["interface-name"]
        params = [param["name"] for param in item["interface-params"]]
        param_line = ", ".join(params)
        line = f"#define {name}({param_line}) "
        if len(line) > 79:
            param_block = ", \\\n  ".join(params)
            line = f"#define {name}( \\\n  {param_block} \\\n) "
        body = self.substitute(" \\\n  ".join(
            definition.strip("\n").split("\n")))
        return line + body

    def _get_typedef_definition(self, _item: Item, definition: Any) -> Lines:
        return f"typedef {self.substitute(definition)};"

    def _get_variable_definition(self, _item: Item, definition: Any) -> Lines:
        return f"extern {self.substitute(definition)};"

    def _add_generic_definition(self, get_lines: GetLines) -> None:
        self.content.add(_get_description(self.item, self.ingroups))
        self.content.append(
            _add_definition(self, self.item, "interface-definition",
                            self.item["interface-definition"], get_lines))


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
            if link["role"] == "interface-placement" and link.item[
                    "interface-type"] == "header-file":
                self._includes.append(link.item)

    def add_ingroup(self, item: Item) -> None:
        """ Adds an ingroup to the header file. """
        self._ingroups[item.uid] = item

    def _add_child(self, item: Item) -> None:
        ingroups = _get_ingroups(item)
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
            if link["role"] == "interface-placement":
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
            for uid in sorted(node.out_edges.keys()):
                in_degree[uid] -= 1
                if in_degree[uid] == 0:
                    queue.append(self._nodes[uid])

        return nodes_in_dependency_order

    def finalize(self) -> None:
        """ Finalizes the header file. """
        self._content.add_spdx_license_identifier()
        with self._content.file_block():
            self._content.add_ingroup(_ingroups_to_designators(self._ingroups))
        self._content.add_copyrights_and_licenses()
        with self._content.header_guard(self._item["interface-path"]):
            self._content.add_includes([
                inc["interface-path"] for inc in self._includes
                if inc != self._item
            ])
            with self._content.extern_c():
                for node in self._get_nodes_in_dependency_order():
                    self._content.add(node.content)

    def write(self, domain_path: str) -> None:
        """ Writes the header file. """
        self._content.write(
            os.path.join(domain_path, self._item["interface-prefix"],
                         self._item["interface-path"]))


def _generate_header_file(item: Item, domains: Dict[str, str],
                          enabled_by_defined: Dict[str, str]) -> None:
    domain_path = domains.get(item["interface-domain"], None)
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
            if link["role"] == "interface-placement":
                define = f"defined(${{{link.item.uid}:/interface-name}})"
                enabled_by_defined[link.item["interface-name"]] = define
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
        _visit_header_files(item, config["interface-domains"],
                            enabled_by_defined)
