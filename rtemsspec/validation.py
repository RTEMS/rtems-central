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

# pylint: disable=too-many-lines

import itertools
import math
import os
import re
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from rtemsspec.content import CContent, CInclude, enabled_by_to_exp, \
    ExpressionMapper, GenericContent, to_camel_case
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]

_STEPS = re.compile(r"^steps/([0-9]+)$")


def _get_test_run(ctx: ItemGetValueContext) -> Any:
    return f"{to_camel_case(ctx.item.uid[1:]).replace(' ', '')}_Run"


class _Mapper(ItemMapper):
    def __init__(self, item: Item):
        super().__init__(item)
        self._step = 0
        self.add_get_value("requirement/functional/action:/test-run",
                           _get_test_run)
        self.add_get_value("test-case:/test-run", _get_test_run)

    @property
    def steps(self):
        """ The count of test steps. """
        return self._step

    def reset(self):
        """ Resets the test step counter. """
        self._step = 0

    def map(self,
            identifier: str,
            item: Optional[Item] = None,
            prefix: Optional[str] = None) -> Tuple[Item, str, Any]:
        if identifier == "step":
            step = self._step
            self._step = step + 1
            return self._item, "step", str(step)
        match = _STEPS.search(identifier)
        if match:
            inc = int(match.group(1))
            self._step += inc
            return self._item, "step", f"Accounts for {inc} test plan steps"
        return super().map(identifier, item, prefix)


def _add_ingroup(content: CContent, items: List["_TestItem"]) -> None:
    content.add_ingroup([item.group_identifier for item in items])


class _TestItem:
    """ A test item with a default implementation for test cases. """

    # pylint: disable=too-many-public-methods
    def __init__(self, item: Item):
        self._item = item
        self._ident = to_camel_case(item.uid[1:])
        self._mapper = _Mapper(item)

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
    def context(self) -> str:
        """ Returns the test case context type. """
        return f"{self._ident}_Context"

    @property
    def name(self) -> str:
        """ Returns the name. """
        return self._item.spec

    @property
    def includes(self) -> List[str]:
        """ Returns the list of includes. """
        return self._item["test-includes"]

    @property
    def local_includes(self) -> List[str]:
        """ Returns the list of local includes. """
        return self._item["test-local-includes"]

    @property
    def brief(self) -> str:
        """ Returns the substituted brief description. """
        return self.substitute_text(self["test-brief"])

    @property
    def description(self) -> str:
        """ Returns the substituted description. """
        return self.substitute_text(self["test-description"])

    @property
    def group_identifier(self) -> str:
        """ Returns the group identifier. """
        return f"RTEMSTestCase{self.ident}"

    def substitute_code(self, text: Optional[str]) -> str:
        """ Performs a variable substitution for code. """
        return self._mapper.substitute(text)

    def substitute_text(self,
                        text: Optional[str],
                        prefix: Optional[str] = None) -> str:
        """
        Performs a variable substitution for text with an optional prefix.
        """
        return self._mapper.substitute(text, prefix=prefix)

    def add_test_case_description(
            self, content: CContent,
            test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Adds the test case description. """
        with content.defgroup_block(self.group_identifier, self.name):
            try:
                test_suites = test_case_to_suites[self.uid]
            except KeyError as err:
                msg = (f"the target file '{self['test-target']}' of "
                       f"{self.item.spec} is not a source file of an item of "
                       "type 'build/test-program'")
                raise ValueError(msg) from err
            _add_ingroup(content, test_suites)
            content.add_brief_description(self.brief)
            content.wrap(self.description)
            self.add_test_case_action_description(content)
            content.add("@{")

    def add_test_case_action_description(self, content: CContent) -> None:
        """ Adds the test case action description. """
        actions = self["test-actions"]
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
        for action in self["test-actions"]:
            content.add(self.substitute_code(action["action"]))
            for check in action["checks"]:
                content.append(self.substitute_text(check["check"]))
        return content

    def _get_run_params(self, header: Optional[Dict[str, Any]]) -> List[str]:
        if not header:
            return []
        return [
            self.substitute_text(param["specifier"],
                                 f"test-header/run-params[{index}]")
            for index, param in enumerate(header["run-params"])
        ]

    def add_header_body(self, content: CContent, header: Dict[str,
                                                              Any]) -> None:
        """ Adds the test header body. """
        content.add(self.substitute_code(header["code"]))
        with content.doxygen_block():
            content.add_brief_description("Runs the parameterized test case.")
            content.add_param_description(header["run-params"])
        content.gap = False
        content.declare_function("void", f"{self.ident}_Run",
                                 self._get_run_params(header))

    def add_support_method(self,
                           content: CContent,
                           key: str,
                           name: str,
                           mandatory_code: Optional[GenericContent] = None,
                           optional_code: Optional[GenericContent] = None,
                           ret: str = "void",
                           extra_params: Optional[List[str]] = None,
                           extra_args: Optional[List[str]] = None,
                           do_wrap: bool = True) -> str:
        """ Adds a support method to the content. """

        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        info = self[key]
        if not info and not mandatory_code:
            return "NULL"
        if extra_params is None:
            extra_params = []
        if extra_args is None:
            extra_args = []
        method = f"{self.ident}_{name}"
        wrap = f"{method}_Wrap"
        if info:
            content.add_description_block(
                self.substitute_text(info["brief"]),
                self.substitute_text(info["description"]))
            params = [f"{self.context} *ctx"] + extra_params
            with content.function(f"static {ret}", method, params):
                if not do_wrap:
                    content.gap = False
                    content.add(mandatory_code)
                    content.gap = False
                    content.add(optional_code)
                content.add(self.substitute_code(info["code"]))
        if not do_wrap:
            assert info
            return method
        params = ["void *arg"] + extra_params
        with content.function(f"static {ret}", wrap, params):
            content.add([f"{self.context} *ctx;", "", "ctx = arg;"])
            content.gap = False
            content.add(mandatory_code)
            content.gap = False
            content.add(optional_code)
            if info:
                content.gap = False
                ret_2 = None if ret == "void" else "return"
                args = ["ctx"] + extra_args
                content.call_function(ret_2, f"{method}", args)
        return wrap

    def add_function(self, content: CContent, key: str, name: str) -> None:
        """
        Adds a function with the name to the content if there is one defined
        for the attribute key.
        """
        if self[key] is not None:
            with content.function("static void", f"{self.ident}_{name}",
                                  [f"{self.context} *ctx"]):
                content.append(self.substitute_code(self[key]))

    def add_default_context_members(self, content: CContent) -> None:
        """ Adds the default context members to the content """

    def add_context(self, content: CContent) -> str:
        """ Adds the context to the content. """
        content.add(self.substitute_code(self["test-context-support"]))
        if not self["test-context"]:
            return "NULL"
        with content.doxygen_block():
            content.add_brief_description(
                f"Test context for {self.name} test case.")
        content.append("typedef struct {")
        with content.indent():
            for info in self["test-context"]:
                content.add_description_block(info["brief"],
                                              info["description"])
                content.add(f"{info['member'].strip()};")
            self.add_default_context_members(content)
        content.add([
            f"}} {self.context};", "", f"static {self.context}",
            f"  {self.ident}_Instance;"
        ])
        return f"&{self.ident}_Instance"

    def generate_header(self, base_directory: str, header: Dict[str,
                                                                Any]) -> None:
        """ Generates the test header. """
        content = CContent()
        content.register_license_and_copyrights_of_item(self._item)
        content.prepend_spdx_license_identifier()
        with content.file_block():
            content.add_ingroup([self.group_identifier])
        content.add_copyrights_and_licenses()
        content.add_automatically_generated_warning()
        with content.header_guard(os.path.basename(header["target"])):
            content.add_includes(list(map(CInclude, header["includes"])))
            content.add_includes(list(map(CInclude, header["local-includes"])),
                                 local=True)
            with content.extern_c():
                with content.add_to_group(self.group_identifier):
                    self.add_header_body(content, header)
        content.write(os.path.join(base_directory, header["target"]))

    def generate(self, content: CContent, base_directory: str,
                 test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Generates the content. """
        self.add_test_case_description(content, test_case_to_suites)
        self._mapper.reset()
        actions = self._generate_test_case_actions()
        fixture = self["test-fixture"]
        header = self["test-header"]
        if header:
            self.generate_header(base_directory, header)
            if self._mapper.steps > 0 and not fixture:
                fixture = "T_empty_fixture"
        content.add(self.substitute_code(self["test-support"]))
        if header:
            params = self._get_run_params(header)
            if fixture:
                ret = "static void"
                name = f"{self.ident}_Wrap"
            else:
                ret = "void"
                name = f"{self.ident}_Run"
            align = True
        else:
            ret = ""
            params = [f"{self.ident}"]
            if fixture:
                params.append(f"&{fixture}")
                name = "T_TEST_CASE_FIXTURE"
            else:
                name = "T_TEST_CASE"
            align = False
            with content.function_block(
                    f"void T_case_body_{self.ident}( void )"):
                pass
            content.gap = False
        with content.function(ret, name, params, align=align):
            content.add(self.substitute_code(self["test-prologue"]))
            if self._mapper.steps > 0:
                content.add(f"T_plan({self._mapper.steps});")
            content.add(actions)
            content.add(self.substitute_code(self["test-epilogue"]))
        if header and fixture:
            run = f"{self.ident}_Run"
            content.add(f"static T_fixture_node {self.ident}_Node;")
            with content.function("void", run, params, align=align):
                content.call_function(None, "T_push_fixture",
                                      [f"&{self.ident}_Node", f"&{fixture}"])
                content.gap = False
                content.call_function(
                    None, name,
                    [param["name"] for param in header["run-params"]])
                content.append("T_pop_fixture();")
        content.add("/** @} */")


class _TestSuiteItem(_TestItem):
    """ A test suite item. """
    @property
    def group_identifier(self) -> str:
        return f"RTEMSTestSuite{self.ident}"

    def generate(self, content: CContent, _base_directory: str,
                 _test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        with content.defgroup_block(self.group_identifier, self.name):
            content.add("@ingroup RTEMSTestSuites")
            content.add_brief_description(self.brief)
            content.wrap(self.description)
            content.add("@{")
        content.add(self.substitute_code(self["test-code"]))
        content.add("/** @} */")


class _Transition(NamedTuple):
    """
    A transition to a set of post conditions with an enabled by expression.
    """
    enabled_by: str
    post_conditions: Tuple[int, ...]
    info: str
    map_entry_index: int


_ConditionIndexToEnum = Tuple[Tuple[str, ...], ...]
_TransitionMap = List[List[_Transition]]


def _state_to_index(conditions: List[Any]) -> Tuple[Dict[str, int], ...]:
    return tuple(
        dict((state["name"], index)
             for index, state in enumerate(condition["states"]))
        for condition in conditions)


def _condition_index_to_enum(prefix: str,
                             conditions: List[Any]) -> _ConditionIndexToEnum:
    return tuple(
        tuple([f"{prefix}_{condition['name']}"] + [
            f"{prefix}_{condition['name']}_{state['name']}"
            for state in condition["states"]
        ] + [f"{prefix}_{condition['name']}_NA"])
        for index, condition in enumerate(conditions))


def _add_condition_enum(content: CContent,
                        index_to_enum: _ConditionIndexToEnum) -> None:
    for enum in index_to_enum:
        content.add("typedef enum {")
        with content.indent():
            content.add(",\n".join(enum[1:]))
        content.add(f"}} {enum[0]};")


class _ActionRequirementTestItem(_TestItem):
    """ An action requirement test item. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, item: Item):
        super().__init__(item)
        self._pre_condition_count = len(item["pre-conditions"])
        self._post_condition_count = len(item["post-conditions"])
        self._pre_index_to_enum = _condition_index_to_enum(
            f"{self.ident}_Pre", item["pre-conditions"])
        self._post_index_to_enum = _condition_index_to_enum(
            f"{self.ident}_Post", item["post-conditions"])
        self._pre_state_to_index = _state_to_index(item["pre-conditions"])
        self._post_state_to_index = _state_to_index(item["post-conditions"])
        self._pre_index_to_condition = dict(
            (index, condition)
            for index, condition in enumerate(item["pre-conditions"]))
        self._post_index_to_name = dict(
            (index, condition["name"])
            for index, condition in enumerate(item["post-conditions"]))

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

    def add_default_context_members(self, content: CContent) -> None:
        for param in self._get_run_params(self["test-header"]):
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

    def _add_fixture_scope(self, content: CContent) -> None:
        params = ["void *arg", "char *buf", "size_t n"]
        with content.function("static size_t", f"{self.ident}_Scope", params):
            content.add([f"{self.context} *ctx;", "", "ctx = arg;"])
            with content.condition("ctx->in_action_loop"):
                content.call_function(
                    "return", "T_get_scope",
                    [f"{self.ident}_PreDesc", "buf", "n", "ctx->pcs"])
            content.add("return 0;")

    def _map_index_to_pre_conditions(self, map_index: int) -> str:
        conditions = []
        for condition in reversed(self.item["pre-conditions"]):
            states = condition["states"]
            count = len(states)
            index = int(map_index % count)
            conditions.append(f"{condition['name']}={states[index]['name']}")
            map_index //= count
        return ", ".join(reversed(conditions))

    def _add_transitions(self, trans_index: int, condition_index: int,
                         map_index: int, transition: Dict[str, Any],
                         transition_map: _TransitionMap,
                         pre_cond_not_applicables: List[str],
                         post_cond: Tuple[int, ...]) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        if condition_index < self._pre_condition_count:
            condition = self._pre_index_to_condition[condition_index]
            state_count = len(condition["states"])
            map_index *= state_count
            states = transition["pre-conditions"][condition["name"]]
            if isinstance(states, str):
                assert states in ["all", "N/A"]
                for index in range(state_count):
                    self._add_transitions(
                        trans_index, condition_index + 1, map_index + index,
                        transition, transition_map,
                        pre_cond_not_applicables + [str(int(states == "N/A"))],
                        post_cond)
            else:
                for state in states:
                    try:
                        index = self._pre_state_to_index[condition_index][
                            state]
                    except KeyError as err:
                        msg = (f"transition map entry {trans_index} of "
                               f"{self.item.spec} refers to non-existent "
                               f"state {err} of pre-condition "
                               f"'{condition['name']}'")
                        raise ValueError(msg) from err
                    self._add_transitions(trans_index, condition_index + 1,
                                          map_index + index, transition,
                                          transition_map,
                                          pre_cond_not_applicables + ["0"],
                                          post_cond)
        else:
            enabled_by = enabled_by_to_exp(transition["enabled-by"],
                                           ExpressionMapper())
            if enabled_by == "1" and transition_map[map_index]:
                raise ValueError(
                    f"transition map entry {trans_index} of "
                    f"{self.item.spec} duplicates pre-condition set "
                    f"{{{self._map_index_to_pre_conditions(map_index)}}} "
                    "defined by transition map entry "
                    f"{transition_map[map_index][0].map_entry_index}")
            transition_map[map_index].append(
                _Transition(enabled_by, post_cond,
                            "    " + ", ".join(pre_cond_not_applicables),
                            trans_index))

    def _get_transition_map(self) -> _TransitionMap:
        transition_count = 1
        for condition in self["pre-conditions"]:
            state_count = len(condition["states"])
            if state_count == 0:
                raise ValueError(f"pre-condition '{condition['name']}' of "
                                 f"{self.item.spec} has no states")
            transition_count *= state_count
        transition_map = [list() for _ in range(transition_count)
                          ]  # type: _TransitionMap
        for trans_index, transition in enumerate(self["transition-map"]):
            if isinstance(transition["post-conditions"], dict):
                try:
                    info = ["0"]
                    post_cond = tuple(
                        self._post_state_to_index[index][
                            transition["post-conditions"][
                                self._post_index_to_name[index]]]
                        for index in range(self._post_condition_count))
                except KeyError as err:
                    msg = (f"transition map entry {trans_index} of "
                           f"{self.item.spec} refers to non-existent "
                           f"post-condition state {err}")
                    raise ValueError(msg) from err
            else:
                info = ["1"]
                post_cond = tuple(
                    len(self._post_state_to_index[index])
                    for index in range(self._post_condition_count))
            self._add_transitions(trans_index, 0, 0, transition,
                                  transition_map, info, post_cond)
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
        for map_index, transistions in enumerate(transition_map):
            if not transistions or transistions[0].enabled_by != "1":
                raise ValueError(
                    f"transition map of {self.item.spec} contains no default "
                    "entry for pre-condition set "
                    f"{{{self._map_index_to_pre_conditions(map_index)}}}")
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

    def _add_call(self, content: CContent, key: str, name: str) -> None:
        if self[key] is not None:
            content.gap = False
            content.call_function(None, f"{self.ident}_{name}", ["ctx"])

    def _add_loop_body(self, content: CContent) -> None:
        with content.condition(f"{self.ident}_TransitionInfo[ index ].Skip"):
            content.append(["++index;", "continue;"])
        content.add_blank_line()
        self._add_call(content, "test-prepare", "Prepare")
        for index, enum in enumerate(self._pre_index_to_enum):
            content.gap = False
            content.call_function(None, f"{enum[0]}_Prepare",
                                  ["ctx", f"ctx->pcs[ {index} ]"])
        self._add_call(content, "test-action", "Action")
        transition_map = f"{self.ident}_TransitionMap"
        for index, enum in enumerate(self._post_index_to_enum):
            content.gap = False
            content.call_function(
                None, f"{enum[0]}_Check",
                ["ctx", f"{transition_map}[ index ][ {index} ]"])
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
                pass
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
                     index_to_enum: _ConditionIndexToEnum,
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

    def add_test_case_action_description(self, _content: CContent) -> None:
        pass

    def add_header_body(self, content: CContent, header: Dict[str,
                                                              Any]) -> None:
        _add_condition_enum(content, self._pre_index_to_enum)
        _add_condition_enum(content, self._post_index_to_enum)
        super().add_header_body(content, header)

    def generate(self, content: CContent, base_directory: str,
                 test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        self.add_test_case_description(content, test_case_to_suites)
        header = self["test-header"]
        if header:
            self.generate_header(base_directory, header)
        else:
            _add_condition_enum(content, self._pre_index_to_enum)
            _add_condition_enum(content, self._post_index_to_enum)
        instance = self.add_context(content)
        self._add_pre_condition_descriptions(content)
        content.add(self.substitute_code(self["test-support"]))
        self._add_handler(content, self["pre-conditions"],
                          self._pre_index_to_enum, "Prepare")
        self._add_handler(content, self["post-conditions"],
                          self._post_index_to_enum, "Check")
        optional_code = "ctx->in_action_loop = false;"
        setup = self.add_support_method(content,
                                        "test-setup",
                                        "Setup",
                                        optional_code=optional_code)
        stop = self.add_support_method(content,
                                       "test-stop",
                                       "Stop",
                                       optional_code=optional_code)
        teardown = self.add_support_method(content,
                                           "test-teardown",
                                           "Teardown",
                                           optional_code=optional_code)
        self._add_fixture_scope(content)
        content.add([
            f"static T_fixture {self.ident}_Fixture = {{",
            f"  .setup = {setup},", f"  .stop = {stop},",
            f"  .teardown = {teardown},", f"  .scope = {self.ident}_Scope,",
            f"  .initial_context = {instance}", "};"
        ])
        self._add_transition_map(content)
        self.add_function(content, "test-prepare", "Prepare")
        self.add_function(content, "test-action", "Action")
        self.add_function(content, "test-cleanup", "Cleanup")
        self._add_test_case(content, header)
        content.add("/** @} */")


class _RuntimeMeasurementRequestItem(_TestItem):
    """ A runtime measurement request item. """
    def __init__(self, item: Item, context: str):
        super().__init__(item)
        self._context = context

    @property
    def context(self) -> str:
        return self._context


def _add_call_method(content: CContent, name: str) -> None:
    if name != "NULL":
        content.gap = False
        content.call_function(None, name, ["ctx"])


class _RuntimeMeasurementTestItem(_TestItem):
    """ A runtime measurement test item. """
    def add_test_case_action_description(self, _content: CContent) -> None:
        pass

    def add_default_context_members(self, content: CContent) -> None:
        content.add_description_block(
            "This member references the measure runtime context.", None)
        content.add("T_measure_runtime_context *context;")
        content.add_description_block(
            "This member provides the measure runtime request.", None)
        content.add("T_measure_runtime_request request;")

    def _add_requests(self, content: CContent) -> CContent:
        requests = CContent()
        prepare = self.add_support_method(content,
                                          "test-prepare",
                                          "Prepare",
                                          do_wrap=False)
        cleanup = self.add_support_method(content,
                                          "test-cleanup",
                                          "Cleanup",
                                          do_wrap=False)
        for item in self.item.children("runtime-measurement-request"):
            req = _RuntimeMeasurementRequestItem(item, self.context)
            requests.add_blank_line()
            _add_call_method(requests, prepare)
            name = req.add_support_method(content,
                                          "test-prepare",
                                          "Prepare",
                                          do_wrap=False)
            _add_call_method(requests, name)
            name = req.add_support_method(content, "test-setup", "Setup")
            requests.append([
                f"ctx->request.name = \"{req.ident}\";",
                f"ctx->request.setup = {name};"
            ])
            name = req.add_support_method(content, "test-body", "Body")
            requests.append([f"ctx->request.body = {name};"])
            extra_params = [
                "T_ticks *delta", "uint32_t tic", "uint32_t toc",
                "unsigned int retry"
            ]
            extra_args = ["delta", "tic", "toc", "retry"]
            name = req.add_support_method(content,
                                          "test-teardown",
                                          "Teardown",
                                          ret="bool",
                                          extra_params=extra_params,
                                          extra_args=extra_args)
            requests.append([f"ctx->request.teardown = {name};"])
            requests.gap = False
            requests.call_function(None, "T_measure_runtime",
                                   ["ctx->context", "&ctx->request"])
            name = req.add_support_method(content,
                                          "test-cleanup",
                                          "Cleanup",
                                          do_wrap=False)
            _add_call_method(requests, name)
            _add_call_method(requests, cleanup)
        return requests

    def generate(self, content: CContent, base_directory: str,
                 test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        self.add_test_case_description(content, test_case_to_suites)
        instance = self.add_context(content)
        content.add(self.substitute_code(self["test-support"]))
        setup = f"{self.ident}_Setup_Context"
        with content.function("static void", setup, [f"{self.context} *ctx"]):
            content.add([
                "T_measure_runtime_config config;",
                "",
                "memset( &config, 0, sizeof( config ) );",
                f"config.sample_count = {self['params']['sample-count']};",
                "ctx->request.arg = ctx;",
                "ctx->request.flags = T_MEASURE_RUNTIME_REPORT_SAMPLES;",
                "ctx->context = T_measure_runtime_create( &config );",
                "T_assert_not_null( ctx->context );",
            ])
        setup = self.add_support_method(content,
                                        "test-setup",
                                        "Setup",
                                        mandatory_code=f"{setup}( ctx );")
        stop = self.add_support_method(content, "test-stop", "Stop")
        teardown = self.add_support_method(content, "test-teardown",
                                           "Teardown")
        content.add([
            f"static T_fixture {self.ident}_Fixture = {{",
            f"  .setup = {setup},", f"  .stop = {stop},",
            f"  .teardown = {teardown},", "  .scope = NULL,",
            f"  .initial_context = {instance}", "};"
        ])
        requests = self._add_requests(content)
        with content.function_block(f"void T_case_body_{self.ident}( void )"):
            pass
        content.gap = False
        ret = ""
        name = "T_TEST_CASE_FIXTURE"
        params = [f"{self.ident}", f"&{self.ident}_Fixture"]
        with content.function(ret, name, params, align=False):
            content.add([
                f"{self.context} *ctx;",
                "",
                "ctx = T_fixture_context();",
            ])
            content.append(requests)
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

    def add_test_suite(self, item: Item) -> None:
        """ Adds a test suite to the source file. """
        self._test_suites.append(_TestSuiteItem(item))

    def add_test_case(self, item: Item) -> None:
        """ Adds a test case to the source file. """
        self._test_cases.append(_TestItem(item))

    def add_action_requirement_test(self, item: Item) -> None:
        """ Adds an action requirement test to the source file. """
        self._test_cases.append(_ActionRequirementTestItem(item))

    def add_runtime_measurement_test(self, item: Item) -> None:
        """ Adds a runtime measurement test to the source file. """
        self._test_cases.append(_RuntimeMeasurementTestItem(item))

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
        content.add_automatically_generated_warning()
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


def _gather_action_requirement_test(
        item: Item, source_files: Dict[str, _SourceFile],
        _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["test-target"], source_files)
    src.add_action_requirement_test(item)


def _gather_runtime_measurement_test(
        item: Item, source_files: Dict[str, _SourceFile],
        _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["test-target"], source_files)
    src.add_runtime_measurement_test(item)


def _gather_test_case(item: Item, source_files: Dict[str, _SourceFile],
                      _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["test-target"], source_files)
    src.add_test_case(item)


def _gather_test_program(item: Item, _source_files: Dict[str, _SourceFile],
                         test_programs: List[_TestProgram]) -> None:
    test_programs.append(_TestProgram(item))


def _gather_test_suite(item: Item, source_files: Dict[str, _SourceFile],
                       _test_programs: List[_TestProgram]) -> None:
    src = _get_source_file(item["test-target"], source_files)
    src.add_test_suite(item)


def _gather_default(_item: Item, _source_files: Dict[str, _SourceFile],
                    _test_programs: List[_TestProgram]) -> None:
    pass


_GATHER = {
    "build/test-program": _gather_test_program,
    "requirement/functional/action": _gather_action_requirement_test,
    "runtime-measurement-test": _gather_runtime_measurement_test,
    "test-case": _gather_test_case,
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
