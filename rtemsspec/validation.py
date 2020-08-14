# SPDX-License-Identifier: BSD-2-Clause
""" This module provides functions for the generation of validation tests. """

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

import itertools
import math
import os
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from rtemsspec.content import CContent, CInclude, enabled_by_to_exp, \
    ExpressionMapper, to_camel_case
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]


class _CodeMapper(ItemMapper):
    def get_value(self, ctx: ItemGetValueContext) -> Any:
        if ctx.type_path_key == "requirement/functional/action:/test-run":
            return f"{to_camel_case(ctx.item.uid[1:]).replace(' ', '')}_Run"
        raise KeyError


class _TextMapper(ItemMapper):
    def __init__(self, item: Item):
        super().__init__(item)
        self._step = 0

    @property
    def steps(self):
        """ The count of test steps. """
        return self._step

    def reset_step(self):
        """ Resets the test step counter. """
        self._step = 0

    def map(self, identifier: str) -> Tuple[Item, Any]:
        if identifier == "step":
            step = self._step
            self._step = step + 1
            return self._item, str(step)
        return super().map(identifier)


def _add_ingroup(content: CContent, items: List["_TestItem"]) -> None:
    content.add_ingroup([item.group_identifier for item in items])


class _TestItem:
    """ A test item with a defaul implementation for test cases. """
    def __init__(self, item: Item):
        self._item = item
        self._ident = to_camel_case(item.uid[1:])
        self._code_mapper = _CodeMapper(item)
        self._text_mapper = _TextMapper(item)

    def __getitem__(self, key: str):
        return self._item[key]

    @property
    def item(self) -> Item:
        """ Returns the item. """
        return self._item

    @property
    def uid(self) -> str:
        """ Returns the item UID. """
        return self._item.uid

    @property
    def ident(self) -> str:
        """ Returns the test identifier. """
        return self._ident

    @property
    def name(self) -> str:
        """ Returns the name. """
        return f"spec:{self._item.uid}"

    @property
    def includes(self) -> List[str]:
        """ Returns the list of includes. """
        return self._item["includes"]

    @property
    def local_includes(self) -> List[str]:
        """ Returns the list of local includes. """
        return self._item["local-includes"]

    @property
    def group_identifier(self) -> str:
        """ Returns the group identifier. """
        return f"RTEMSTestCase{self.ident}"

    def substitute_code(self, text: Optional[str]) -> str:
        """ Performs a variable substitution for code. """
        return self._code_mapper.substitute(text)

    def substitute_text(self,
                        text: Optional[str],
                        prefix: Optional[str] = None) -> str:
        """
        Performs a variable substitution for text with an optinal prefix.
        """
        if prefix:
            return self._text_mapper.substitute_with_prefix(text, prefix)
        return self._text_mapper.substitute(text)

    def add_test_case_description(
            self, content: CContent,
            test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Adds the test case description. """
        with content.defgroup_block(self.group_identifier, self.name):
            _add_ingroup(content, test_case_to_suites[self.uid])
            content.add(["@brief Test Case", "", "@{"])

    def _add_test_case_action_description(self, content: CContent) -> None:
        actions = self["actions"]
        if actions:
            content.add("This test case performs the following actions:")
            for action in actions:
                content.wrap(self.substitute_text(action["description"]),
                             initial_indent="- ")
                for check in action["checks"]:
                    content.wrap(self.substitute_text(check["description"]),
                                 initial_indent="  - ",
                                 subsequent_indent="    ")

    def _generate_test_case_actions(self) -> CContent:
        content = CContent()
        for action in self["actions"]:
            content.add(self.substitute_code(action["action"]))
            for check in action["checks"]:
                content.append(self.substitute_text(check["check"]))
        return content

    def generate(self, content: CContent, _base_directory: str,
                 test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Generates the content. """
        self.add_test_case_description(content, test_case_to_suites)
        content.add(self.substitute_code(self["support"]))
        with content.function_block(f"void T_case_body_{self.ident}( void )"):
            content.add_brief_description(self.substitute_text(self["brief"]))
            content.wrap(self.substitute_text(self["description"]))
            self._add_test_case_action_description(content)
        content.gap = False
        params = [f"{self.ident}"]
        fixture = self["fixture"]
        if fixture:
            params.append(f"&{fixture}")
            name = "T_TEST_CASE_FIXTURE"
        else:
            name = "T_TEST_CASE"
        with content.function("", name, params):
            content.add(self.substitute_code(self["prologue"]))
            self._text_mapper.reset_step()
            action_content = self._generate_test_case_actions()
            if self._text_mapper.steps > 0:
                content.add(f"T_plan({self._text_mapper.steps});")
            content.add(action_content)
            content.add(self.substitute_code(self["epilogue"]))
        content.add("/** @} */")


class _TestSuiteItem(_TestItem):
    """ A test suite item. """
    @property
    def group_identifier(self) -> str:
        return f"RTEMSTestSuite{self.ident}"

    def generate(self, content: CContent, _base_directory: str,
                 _test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        with content.defgroup_block(self.group_identifier, self.name):
            content.add(["@ingroup RTEMSTestSuites", "", "@brief Test Suite"])
            content.wrap(self.substitute_text(self["description"]))
            content.add("@{")
        content.add(self.substitute_code(self["code"]))
        content.add("/** @} */")


class _Transition(NamedTuple):
    """
    A transition to a set of post conditions with an enabled by expression.
    """
    enabled_by: str
    post_conditions: Tuple[int, ...]
    info: str


_DirectiveIndexToEnum = Tuple[Tuple[str, ...], ...]
_TransitionMap = List[List[_Transition]]


def _directive_state_to_index(
        conditions: List[Any]) -> Tuple[Dict[str, int], ...]:
    return tuple(
        dict((state["name"], index)
             for index, state in enumerate(condition["states"]))
        for condition in conditions)


def _directive_index_to_enum(prefix: str,
                             conditions: List[Any]) -> _DirectiveIndexToEnum:
    return tuple(
        tuple([f"{prefix}_{condition['name']}"] + [
            f"{prefix}_{condition['name']}_{state['name']}"
            for state in condition["states"]
        ] + [f"{prefix}_{condition['name']}_NA"])
        for index, condition in enumerate(conditions))


def _directive_add_enum(content: CContent,
                        index_to_enum: _DirectiveIndexToEnum) -> None:
    for enum in index_to_enum:
        content.add("typedef enum {")
        with content.indent():
            content.add(",\n".join(enum[1:]))
        content.add(f"}} {enum[0]};")


class _TestDirectiveItem(_TestItem):
    """ A test directive item. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, item: Item):
        super().__init__(item)
        self._pre_condition_count = len(item["pre-conditions"])
        self._post_condition_count = len(item["post-conditions"])
        self._pre_index_to_enum = _directive_index_to_enum(
            f"{self.ident}_Pre", item["pre-conditions"])
        self._post_index_to_enum = _directive_index_to_enum(
            f"{self.ident}_Post", item["post-conditions"])
        self._pre_state_to_index = _directive_state_to_index(
            item["pre-conditions"])
        self._post_state_to_index = _directive_state_to_index(
            item["post-conditions"])
        self._pre_index_to_condition = dict(
            (index, condition)
            for index, condition in enumerate(item["pre-conditions"]))
        self._post_index_to_name = dict(
            (index, condition["name"])
            for index, condition in enumerate(item["post-conditions"]))

    @property
    def context(self) -> str:
        """ Returns the test case context type. """
        return f"{self._ident}_Context"

    @property
    def includes(self) -> List[str]:
        return self._item["test-includes"]

    @property
    def local_includes(self) -> List[str]:
        return self._item["test-local-includes"]

    def _add_pre_condition_descriptions(self, content: CContent) -> None:
        for condition in self["pre-conditions"]:
            content.add("static const char * const "
                        f"{self.ident}_PreDesc_{condition['name']}[] = {{")
            with content.indent():
                content.add(",\n".join(
                    itertools.chain((f"\"{state['name']}\""
                                     for state in condition["states"]),
                                    ["\"NA\""])))
            content.add("};")
        content.add("static const char * const * const "
                    f"{self.ident}_PreDesc[] = {{")
        with content.indent():
            content.add(",\n".join([
                f"{self.ident}_PreDesc_{condition['name']}"
                for condition in self["pre-conditions"]
            ] + ["NULL"]))
        content.add("};")

    def _add_context(self, content: CContent, header: Dict[str, Any]) -> None:
        content.add(self.substitute_code(self["test-context-support"]))
        with content.doxygen_block():
            content.add_brief_description(
                f"Test context for {self.name} test case.")
        content.append("typedef struct {")
        with content.indent():
            for info in self["test-context"]:
                content.add_description_block(info["brief"],
                                              info["description"])
                content.add(f"{info['member'].strip()};")
            for param in self._get_run_params(header):
                content.add_description_block(
                    "This member contains a copy of the corresponding "
                    f"{self.ident}_Run() parameter.", None)
                content.add(f"{param.strip()};")
            content.add_description_block(
                "This member defines the pre-condition states "
                "for the next action.", None)
            content.add(f"size_t pcs[ {self._pre_condition_count} ];")
            content.add_description_block(
                "This member indicates if the test action loop "
                "is currently executed.", None)
            content.add("bool in_action_loop;")
        content.add([
            f"}} {self.context};", "", f"static {self.context}",
            f"  {self.ident}_Instance;"
        ])

    def _add_fixture_scope(self, content: CContent) -> None:
        params = ["void *arg", "char *buf", "size_t n"]
        with content.function("static size_t", f"{self.ident}_Scope", params):
            content.add([f"{self.context} *ctx;", "", "ctx = arg;"])
            with content.condition("ctx->in_action_loop"):
                content.call_function(
                    "return", "T_get_scope",
                    [f"{self.ident}_PreDesc", "buf", "n", "ctx->pcs"])
            content.add("return 0;")

    def _add_fixture_method(self, content: CContent,
                            info: Optional[Dict[str, Optional[str]]],
                            name: str) -> str:
        if not info:
            return "NULL"
        method = f"{self.ident}_{name}"
        wrap = f"{method}_Wrap"
        content.add_description_block(info["brief"], info["description"])
        with content.function("static void", method, [f"{self.context} *ctx"]):
            content.add(self.substitute_code(info["code"]))
        with content.function("static void", wrap, ["void *arg"]):
            content.add([
                f"{self.context} *ctx;", "", "ctx = arg;",
                "ctx->in_action_loop = false;", f"{method}( ctx );"
            ])
        return wrap

    def _add_transitions(self, condition_index: int, map_index: int,
                         transition: Dict[str,
                                          Any], transition_map: _TransitionMap,
                         pre_cond_not_applicables: List[str],
                         post_cond: Tuple[int, ...]) -> None:
        # pylint: disable=too-many-arguments
        if condition_index < self._pre_condition_count:
            condition = self._pre_index_to_condition[condition_index]
            state_count = len(condition["states"])
            map_index *= state_count
            states = transition["pre-conditions"][condition["name"]]
            if isinstance(states, str):
                assert states in ["all", "N/A"]
                for index in range(state_count):
                    self._add_transitions(
                        condition_index + 1, map_index + index, transition,
                        transition_map,
                        pre_cond_not_applicables + [str(int(states == "N/A"))],
                        post_cond)
            else:
                for state in states:
                    self._add_transitions(
                        condition_index + 1, map_index +
                        self._pre_state_to_index[condition_index][state],
                        transition, transition_map,
                        pre_cond_not_applicables + ["0"], post_cond)
        else:
            enabled_by = enabled_by_to_exp(transition["enabled-by"],
                                           ExpressionMapper())
            assert enabled_by != "1" or not transition_map[map_index]
            transition_map[map_index].append(
                _Transition(enabled_by, post_cond,
                            "    " + ", ".join(pre_cond_not_applicables)))

    def _get_transition_map(self) -> _TransitionMap:
        transition_count = 1
        for condition in self["pre-conditions"]:
            state_count = len(condition["states"])
            assert state_count > 0
            transition_count *= state_count
        transition_map = [list() for _ in range(transition_count)
                          ]  # type: _TransitionMap
        for transition in self["transition-map"]:
            if isinstance(transition["post-conditions"], dict):
                info = ["0"]
                post_cond = tuple(
                    self._post_state_to_index[index][
                        transition["post-conditions"][
                            self._post_index_to_name[index]]]
                    for index in range(self._post_condition_count))
            else:
                info = ["1"]
                post_cond = tuple(
                    len(self._post_state_to_index[index])
                    for index in range(self._post_condition_count))
            self._add_transitions(0, 0, transition, transition_map, info,
                                  post_cond)
        return transition_map

    def _post_condition_enumerators(self, conditions: Any) -> str:
        return ",\n".join(
            f"    {self._post_index_to_enum[index][condition + 1]}"
            for index, condition in enumerate(conditions))

    def _add_transition_map(self, content: CContent) -> None:
        transition_map = self._get_transition_map()
        content.add([
            "static const uint8_t "
            f"{self.ident}_TransitionMap[][ {self._post_condition_count} ]"
            " = {", "  {"
        ])
        map_elements = []
        info_elements = []
        for transistions in transition_map:
            assert transistions[0].enabled_by == "1"
            if len(transistions) == 1:
                map_elements.append(
                    self._post_condition_enumerators(
                        transistions[0].post_conditions))
                info_elements.append(transistions[0].info)
            else:
                ifelse = "#if "
                map_enumerators = []  # type: List[str]
                info_enumerators = []  # type: List[str]
                for variant in transistions[1:]:
                    map_enumerators.append(ifelse + variant.enabled_by)
                    info_enumerators.append(ifelse + variant.enabled_by)
                    map_enumerators.append(
                        self._post_condition_enumerators(
                            variant.post_conditions))
                    info_enumerators.append(variant.info)
                    ifelse = "#elif "
                map_enumerators.append("#else")
                info_enumerators.append("#else")
                map_enumerators.append(
                    self._post_condition_enumerators(
                        transistions[0].post_conditions))
                info_enumerators.append(transistions[0].info)
                map_enumerators.append("#endif")
                info_enumerators.append("#endif")
                map_elements.append("\n".join(map_enumerators))
                info_elements.append("\n".join(info_enumerators))
        content.append(["\n  }, {\n".join(map_elements), "  }", "};"])
        pre_bits = 2**max(math.ceil(math.log2(self._pre_condition_count + 1)),
                          3)
        content.add("static const struct {")
        with content.indent():
            content.append(f"uint{pre_bits}_t Skip : 1;")
            for condition in self["pre-conditions"]:
                content.append(
                    f"uint{pre_bits}_t Pre_{condition['name']}_NA : 1;")
        content.add([f"}} {self.ident}_TransitionInfo[] = {{", "  {"])
        content.append(["\n  }, {\n".join(info_elements), "  }", "};"])

    def _add_function(self, content: CContent, key: str, name: str) -> None:
        if self[key] is not None:
            with content.function("static void", f"{self.ident}_{name}",
                                  [f"{self.context} *ctx"]):
                content.append(self.substitute_code(self[key]))

    def _add_call(self, content: CContent, key: str, name: str) -> None:
        if self[key] is not None:
            content.append(f"{self.ident}_{name}( ctx );")

    def _add_loop_body(self, content: CContent) -> None:
        with content.condition(f"{self.ident}_TransitionInfo[ index ].Skip"):
            content.append(["++index;", "continue;"])
        content.add_blank_line()
        self._add_call(content, "test-prepare", "Prepare")
        for index, enum in enumerate(self._pre_index_to_enum):
            content.append(f"{enum[0]}_Prepare( ctx, ctx->pcs[ {index} ] );")
        self._add_call(content, "test-action", "Action")
        transition_map = f"{self.ident}_TransitionMap"
        for index, enum in enumerate(self._post_index_to_enum):
            content.append([
                f"{enum[0]}_Check(", "  ctx,",
                f"  {transition_map}[ index ][ {index} ]", ");"
            ])
        self._add_call(content, "test-cleanup", "Cleanup")
        content.append("++index;")

    def _add_for_loops(self, content: CContent, index: int) -> None:
        if index < self._pre_condition_count:
            var = f"ctx->pcs[ {index} ]"
            begin = self._pre_index_to_enum[index][1]
            end = self._pre_index_to_enum[index][-1]
            with content.for_loop(f"{var} = {begin}", f"{var} < {end}",
                                  f"++{var}"):
                name = self._item['pre-conditions'][index]["name"]
                pre_na = f"{self.ident}_TransitionInfo[ index ].Pre_{name}_NA"
                with content.condition(pre_na):
                    content.append(f"{var} = {end};")
                    content.append(f"index += ( {end} - 1 )")
                    for index_2 in range(index + 1, self._pre_condition_count):
                        with content.indent():
                            content.append(
                                f"* {self._pre_index_to_enum[index_2][-1]}")
                    content.lines[-1] += ";"
                self._add_for_loops(content, index + 1)
        else:
            self._add_loop_body(content)

    def _add_test_case(self, content: CContent, header: Dict[str,
                                                             Any]) -> None:
        fixture = f"{self.ident}_Fixture"
        prologue = CContent()
        epilogue = CContent()
        if header:
            content.add(f"static T_fixture_node {self.ident}_Node;")
            ret = "void"
            name = f"{self.ident}_Run"
            params = self._get_run_params(header)
            prologue.add([f"{self.context} *ctx;", "size_t index;"])
            prologue.call_function("ctx =", "T_push_fixture",
                                   [f"&{self.ident}_Node", f"&{fixture}"])
            prologue.add([
                f"ctx->{param['name']} = {param['name']};"
                for param in header["run-params"]
            ] + ["ctx->in_action_loop = true;", "index = 0;"])
            epilogue.add("T_pop_fixture();")
            align = True
        else:
            with content.function_block(
                    f"void T_case_body_{self.ident}( void )"):
                content.add_brief_description(self["test-brief"])
                content.wrap(self["test-description"])
            content.gap = False
            ret = ""
            name = "T_TEST_CASE_FIXTURE"
            params = [f"{self.ident}", f"&{fixture}"]
            prologue.add([
                f"{self.context} *ctx;", "size_t index;", "",
                "ctx = T_fixture_context();", "ctx->in_action_loop = true;",
                "index = 0;"
            ])
            align = False
        with content.function(ret, name, params, align=align):
            content.add(prologue)
            self._add_for_loops(content, 0)
            content.add(epilogue)

    def _add_handler(self, content: CContent, conditions: List[Any],
                     index_to_enum: _DirectiveIndexToEnum,
                     action: str) -> None:
        for condition_index, condition in enumerate(conditions):
            enum = index_to_enum[condition_index]
            handler = f"{enum[0]}_{action}"
            params = [f"{self.context} *ctx", f"{enum[0]} state"]
            with content.function("static void", handler, params):
                content.add(self.substitute_code(condition["test-prologue"]))
                content.add("switch ( state ) {")
                with content.indent():
                    for state_index, state in enumerate(condition["states"]):
                        content.add(f"case {enum[state_index + 1]}: {{")
                        with content.indent():
                            content.add(
                                self.substitute_code(state["test-code"]))
                            content.append("break;")
                        content.add("}")
                    content.add(f"case {enum[-1]}:")
                    with content.indent():
                        content.append("break;")
                content.add("}")
                content.add(self.substitute_code(condition["test-epilogue"]))

    def _get_run_params(self, header: Optional[Dict[str, Any]]) -> List[str]:
        if not header:
            return []
        return [
            self.substitute_text(param["specifier"],
                                 f"test-header/run-params[{index}]")
            for index, param in enumerate(header["run-params"])
        ]

    def _generate_header_body(self, content: CContent,
                              header: Dict[str, Any]) -> None:
        _directive_add_enum(content, self._pre_index_to_enum)
        _directive_add_enum(content, self._post_index_to_enum)
        content.add(self.substitute_code(header["code"]))
        with content.doxygen_block():
            content.add_brief_description(self["test-brief"])
            content.wrap(self["test-description"])
            content.add_param_description(header["run-params"])
        content.gap = False
        content.declare_function("void", f"{self.ident}_Run",
                                 self._get_run_params(header))

    def _generate_header(self, base_directory: str, header: Dict[str,
                                                                 Any]) -> None:
        content = CContent()
        content.register_license_and_copyrights_of_item(self._item)
        content.prepend_spdx_license_identifier()
        with content.file_block():
            content.add_ingroup([self.group_identifier])
        content.add_copyrights_and_licenses()
        with content.header_guard(os.path.basename(header["target"])):
            content.add_includes(list(map(CInclude, header["includes"])))
            content.add_includes(list(map(CInclude, header["local-includes"])),
                                 local=True)
            with content.extern_c():
                with content.add_to_group(self.group_identifier):
                    self._generate_header_body(content, header)
        content.write(os.path.join(base_directory, header["target"]))

    def generate(self, content: CContent, base_directory: str,
                 test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        self.add_test_case_description(content, test_case_to_suites)
        header = self["test-header"]
        if header:
            self._generate_header(base_directory, header)
        else:
            _directive_add_enum(content, self._pre_index_to_enum)
            _directive_add_enum(content, self._post_index_to_enum)
        self._add_context(content, header)
        self._add_pre_condition_descriptions(content)
        content.add(self.substitute_code(self["test-support"]))
        self._add_handler(content, self["pre-conditions"],
                          self._pre_index_to_enum, "Prepare")
        self._add_handler(content, self["post-conditions"],
                          self._post_index_to_enum, "Check")
        setup = self._add_fixture_method(content, self["test-setup"], "Setup")
        stop = self._add_fixture_method(content, self["test-stop"], "Stop")
        teardown = self._add_fixture_method(content, self["test-teardown"],
                                            "Teardown")
        self._add_fixture_scope(content)
        content.add([
            f"static T_fixture {self.ident}_Fixture = {{",
            f"  .setup = {setup},", f"  .stop = {stop},",
            f"  .teardown = {teardown},", f"  .scope = {self.ident}_Scope,",
            f"  .initial_context = &{self.ident}_Instance", "};"
        ])
        self._add_transition_map(content)
        self._add_function(content, "test-prepare", "Prepare")
        self._add_function(content, "test-action", "Action")
        self._add_function(content, "test-cleanup", "Cleanup")
        self._add_test_case(content, header)
        content.add("/** @} */")


class _SourceFile:
    """ A test source file. """
    def __init__(self, filename: str):
        """ Initializes a test source file. """
        self._file = filename
        self._test_suites = []  # type: List[_TestItem]
        self._test_cases = []  # type: List[_TestItem]

    @property
    def test_suites(self) -> List[_TestItem]:
        """ The test suites of the source file. """
        return self._test_suites

    @property
    def test_cases(self) -> List[_TestItem]:
        """ The test cases of the source file. """
        return self._test_cases

    def add_test_suite(self, test_suite: Item) -> None:
        """ Adds a test suite to the source file. """
        self._test_suites.append(_TestSuiteItem(test_suite))

    def add_test_case(self, test_case: Item) -> None:
        """ Adds a test case to the source file. """
        self._test_cases.append(_TestItem(test_case))

    def add_test_directive(self, test_directive: Item) -> None:
        """ Adds a test directive to the source file. """
        self._test_cases.append(_TestDirectiveItem(test_directive))

    def generate(self, base_directory: str,
                 test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        """
        Generates the source file and the corresponding build specification.
        """
        content = CContent()
        includes = []  # type: List[CInclude]
        local_includes = []  # type: List[CInclude]
        for item in itertools.chain(self._test_suites, self._test_cases):
            includes.extend(map(CInclude, item.includes))
            local_includes.extend(map(CInclude, item.local_includes))
            content.register_license_and_copyrights_of_item(item.item)
        content.prepend_spdx_license_identifier()
        with content.file_block():
            _add_ingroup(content, self._test_suites)
            _add_ingroup(content, self._test_cases)
        content.add_copyrights_and_licenses()
        content.add_have_config()
        content.add_includes(includes)
        content.add_includes(local_includes, local=True)
        content.add_includes([CInclude("rtems/test.h")])
        for item in sorted(self._test_cases, key=lambda x: x.name):
            item.generate(content, base_directory, test_case_to_suites)
        for item in sorted(self._test_suites, key=lambda x: x.name):
            item.generate(content, base_directory, test_case_to_suites)
        content.write(os.path.join(base_directory, self._file))


class _TestProgram:
    """ A test program. """
    def __init__(self, item: Item):
        """ Initializes a test program. """
        self._item = item
        self._source_files = []  # type: List[_SourceFile]

    @property
    def source_files(self) -> List[_SourceFile]:
        """ The source files of the test program. """
        return self._source_files

    def add_source_files(self, source_files: Dict[str, _SourceFile]) -> None:
        """
        Adds the source files of the test program which are present in the
        source file map.
        """
        for filename in self._item["source"]:
            source_file = source_files.get(filename, None)
            if source_file is not None:
                self._source_files.append(source_file)


def _get_source_file(filename: str,
                     source_files: Dict[str, _SourceFile]) -> _SourceFile:
    return source_files.setdefault(filename, _SourceFile(filename))


def _gather_action(item: Item, source_files: Dict[str, _SourceFile],
                   _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["test-target"], source_files)
    src.add_test_directive(item)


def _gather_test_case(item: Item, source_files: Dict[str, _SourceFile],
                      _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["target"], source_files)
    src.add_test_case(item)


def _gather_test_program(item: Item, _source_files: Dict[str, _SourceFile],
                         test_programs: List[_TestProgram]) -> None:
    test_programs.append(_TestProgram(item))


def _gather_test_suite(item: Item, source_files: Dict[str, _SourceFile],
                       _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["target"], source_files)
    src.add_test_suite(item)


def _gather_default(_item: Item, _source_files: Dict[str, _SourceFile],
                    _test_programs: List[_TestProgram]) -> None:
    pass


_GATHER = {
    "requirement/functional/action": _gather_action,
    "test-case": _gather_test_case,
    "build/test-program": _gather_test_program,
    "test-suite": _gather_test_suite,
}


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates source files and build specification items for validation test
    suites and test cases according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the validation
                       test suites and test cases.
    """
    source_files = {}  # type: Dict[str, _SourceFile]
    test_programs = []  # type: List[_TestProgram]
    for item in item_cache.all.values():
        _GATHER.get(item.type, _gather_default)(item, source_files,
                                                test_programs)

    test_case_to_suites = {}  # type: Dict[str, List[_TestItem]]
    for test_program in test_programs:
        test_program.add_source_files(source_files)
        test_suites = []  # type: List[_TestItem]
        for source_file in test_program.source_files:
            test_suites.extend(source_file.test_suites)
        for source_file in test_program.source_files:
            for test_case in source_file.test_cases:
                test_case_to_suites.setdefault(test_case.uid,
                                               []).extend(test_suites)

    for src in source_files.values():
        src.generate(config["base-directory"], test_case_to_suites)
