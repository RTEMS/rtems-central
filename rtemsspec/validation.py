# SPDX-License-Identifier: BSD-2-Clause
""" This module provides functions for the generation of validation tests. """

# Copyright (C) 2020, 2021 embedded brains GmbH (http://www.embedded-brains.de)
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
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from rtemsspec.content import CContent, CInclude, \
    GenericContent, get_value_params, get_value_plural, \
    get_value_doxygen_group, get_value_doxygen_function, to_camel_case
from rtemsspec.items import Item, ItemCache, \
    ItemGetValueContext, ItemMapper
from rtemsspec.transitionmap import TransitionMap

ItemMap = Dict[str, Item]

_STEPS = re.compile(r"^steps/([0-9]+)$")


def _get_test_run(ctx: ItemGetValueContext) -> Any:
    return f"{to_camel_case(ctx.item.uid[1:]).replace(' ', '')}_Run"


class _Mapper(ItemMapper):
    def __init__(self, item: Item):
        super().__init__(item)
        self._step = 0
        self.add_get_value("glossary/term:/plural", get_value_plural)
        self.add_get_value("interface/function:/name",
                           get_value_doxygen_function)
        self.add_get_value("interface/function:/params/name", get_value_params)
        self.add_get_value("interface/group:/name", get_value_doxygen_group)
        self.add_get_value("interface/macro:/name", get_value_doxygen_function)
        self.add_get_value("interface/macro:/params/name", get_value_params)
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
        self._context = f"{self._ident}_Context"
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
        return self._context

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
                content.wrap(self.substitute_text(action["action-brief"]),
                             initial_indent="- ")
                for check in action["checks"]:
                    content.wrap(self.substitute_text(check["brief"]),
                                 initial_indent="  - ",
                                 subsequent_indent="    ")

    def _add_test_case_actions(self, content: CContent) -> CContent:
        actions = CContent()
        for index, action in enumerate(self["test-actions"]):
            method = f"{self._ident}_Action_{index}"
            if self.context == "void":
                args = []
                params = []
            else:
                args = ["ctx"]
                params = [f"{self.context} *ctx"]
            actions.gap = False
            actions.call_function(None, method, args)
            with content.doxygen_block():
                content.add_brief_description(
                    self.substitute_text(action["action-brief"]))
            content.gap = False
            with content.function("static void", method, params):
                content.add(self.substitute_code(action["action-code"]))
                for check in action["checks"]:
                    with content.comment_block():
                        content.wrap(self.substitute_text(check["brief"]))
                    content.append(self.substitute_text(check["code"]))
        return actions

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
        for param in self._get_run_params(self["test-header"]):
            content.add_description_block(
                "This member contains a copy of the corresponding "
                f"{self.ident}_Run() parameter.", None)
            content.add(f"{param.strip()};")

    def add_context(self, content: CContent) -> str:
        """ Adds the context to the content. """
        content.add(self.substitute_code(self["test-context-support"]))
        if not self["test-context"] and (
                not self["test-header"]
                or not self["test-header"]["run-params"]):
            return "NULL"
        with content.doxygen_block():
            content.add_brief_description(
                f"Test context for {self.name} test case.")
        content.append("typedef struct {")
        with content.indent():
            for info in self["test-context"]:
                content.add_description_block(
                    self.substitute_text(info["brief"]),
                    self.substitute_text(info["description"]))
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

    def _add_context_and_fixture(self, content: CContent) -> Optional[str]:
        instance = self.add_context(content)
        if instance == "NULL":
            self._context = "void"
            do_wrap = False
        else:
            do_wrap = True
        setup = self.add_support_method(content,
                                        "test-setup",
                                        "Setup",
                                        do_wrap=do_wrap)
        stop = self.add_support_method(content,
                                       "test-stop",
                                       "Stop",
                                       do_wrap=do_wrap)
        teardown = self.add_support_method(content,
                                           "test-teardown",
                                           "Teardown",
                                           do_wrap=do_wrap)
        if all(ptr == "NULL" for ptr in [instance, setup, stop, teardown]):
            return None
        content.add([
            f"static T_fixture {self.ident}_Fixture = {{",
            f"  .setup = {setup},", f"  .stop = {stop},",
            f"  .teardown = {teardown},", "  .scope = NULL,",
            f"  .initial_context = {instance}", "};"
        ])
        return f"&{self.ident}_Fixture"

    def assign_run_params(self, content: CContent, header: Dict[str,
                                                                Any]) -> None:
        """ Assigns the run parameters to the context.  """
        if header["run-params"]:
            content.add([f"ctx = &{self.ident}_Instance;"] + [
                f"ctx->{param['name']} = {param['name']};"
                for param in header["run-params"]
            ])

    def generate(self, content: CContent, base_directory: str,
                 test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Generates the content. """
        self.add_test_case_description(content, test_case_to_suites)
        fixture = self._add_context_and_fixture(content)
        content.add(self.substitute_code(self["test-support"]))
        self._mapper.reset()
        actions = self._add_test_case_actions(content)
        header = self["test-header"]
        prologue = CContent()
        epilogue = CContent()
        if header:
            self.generate_header(base_directory, header)
            ret = "void"
            name = f"{self.ident}_Run"
            params = self._get_run_params(header)
            if self._mapper.steps > 0 and not fixture:
                fixture = "&T_empty_fixture"
            if fixture:
                content.add(f"static T_fixture_node {self.ident}_Node;")
                if self.context == "void":
                    result = None
                else:
                    prologue.add(f"{self.context} *ctx;")
                    self.assign_run_params(prologue, header)
                    result = "ctx ="
                prologue.call_function(result, "T_push_fixture",
                                       [f"&{self.ident}_Node", fixture])
                epilogue.add("T_pop_fixture();")
            align = True
        else:
            ret = ""
            params = [f"{self.ident}"]
            if fixture:
                params.append(fixture)
                name = "T_TEST_CASE_FIXTURE"
            else:
                name = "T_TEST_CASE"
            if self.context != "void":
                prologue.add([
                    f"{self.context} *ctx;", "", "ctx = T_fixture_context();"
                ])
            align = False
            with content.function_block(
                    f"void T_case_body_{self.ident}( void )"):
                pass
            content.gap = False
        with content.function(ret, name, params, align=align):
            content.add(prologue)
            if self._mapper.steps > 0:
                content.add(f"T_plan( {self._mapper.steps} );")
            content.add(actions)
            content.add(epilogue)
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


_IdxToX = Tuple[Tuple[str, ...], ...]


def _to_enum(prefix: str, conditions: List[Any]) -> _IdxToX:
    return tuple(
        tuple([f"{prefix}_{condition['name']}"] + [
            f"{prefix}_{condition['name']}_{state['name']}"
            for state in condition["states"]
        ] + [f"{prefix}_{condition['name']}_NA"]) for condition in conditions)


def _add_condition_enum(content: CContent, co_idx_to_enum: _IdxToX) -> None:
    for enum in co_idx_to_enum:
        content.add("typedef enum {")
        with content.indent():
            content.add(",\n".join(enum[1:]))
        content.add(f"}} {enum[0]};")


class _ActionRequirementTestItem(_TestItem):
    """ An action requirement test item. """
    def __init__(self, item: Item):
        super().__init__(item)
        self._pre_co_count = len(item["pre-conditions"])
        self._pre_co_idx_to_enum = _to_enum(f"{self.ident}_Pre",
                                            item["pre-conditions"])
        self._post_co_idx_to_enum = _to_enum(f"{self.ident}_Post",
                                             item["post-conditions"])

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
        super().add_default_context_members(content)
        content.add_description_block(
            "This member defines the pre-condition states "
            "for the next action.", None)
        content.add(f"size_t pcs[ {self._pre_co_count} ];")
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

    def _add_call(self, content: CContent, key: str, name: str) -> None:
        if self[key] is not None:
            content.gap = False
            content.call_function(None, f"{self.ident}_{name}", ["ctx"])

    def _add_loop_body(self, content: CContent,
                       transition_map: TransitionMap) -> None:
        has_pre_co_na = max(transition_map.pre_co_summary[1:])
        content.add(f"{self.ident}_Entry entry;")
        if has_pre_co_na:
            content.append(f"size_t pcs[ {self._pre_co_count} ];")
        content.call_function("entry =", f"{self.ident}_GetEntry", ["index"])
        content.append("++index;")
        if transition_map.pre_co_summary[0]:
            with content.condition("entry.Skip"):
                content.append("continue;")
        if has_pre_co_na:
            content.call_function(None, "memcpy",
                                  ["pcs", "ctx->pcs", "sizeof( pcs )"])
            for index, pre_co in enumerate(self._item["pre-conditions"]):
                if transition_map.pre_co_summary[index + 1]:
                    name = pre_co["name"]
                    with content.condition(f"entry.Pre_{name}_NA"):
                        enum_na = self._pre_co_idx_to_enum[index][-1]
                        content.append(f"ctx->pcs[ {index} ] = {enum_na};")
        content.add_blank_line()
        self._add_call(content, "test-prepare", "Prepare")
        for index, enum in enumerate(self._pre_co_idx_to_enum):
            content.gap = False
            content.call_function(None, f"{enum[0]}_Prepare",
                                  ["ctx", f"ctx->pcs[ {index} ]"])
        self._add_call(content, "test-action", "Action")
        for index, enum in enumerate(self._post_co_idx_to_enum):
            content.gap = False
            content.call_function(None, f"{enum[0]}_Check", [
                "ctx", f"entry.{transition_map.get_post_entry_member(index)}"
            ])
        self._add_call(content, "test-cleanup", "Cleanup")
        if has_pre_co_na:
            content.gap = False
            content.call_function(None, "memcpy",
                                  ["ctx->pcs", "pcs", "sizeof( ctx->pcs )"])

    def _add_for_loops(self, content: CContent, transition_map: TransitionMap,
                       index: int) -> None:
        if index < self._pre_co_count:
            var = f"ctx->pcs[ {index} ]"
            begin = self._pre_co_idx_to_enum[index][1]
            end = self._pre_co_idx_to_enum[index][-1]
            with content.for_loop(f"{var} = {begin}", f"{var} < {end}",
                                  f"++{var}"):
                self._add_for_loops(content, transition_map, index + 1)
        else:
            self._add_loop_body(content, transition_map)

    def _add_test_case(self, content: CContent, transition_map: TransitionMap,
                       header: Dict[str, Any]) -> None:
        ret = f"static inline {self.ident}_Entry"
        name = f"{self.ident}_GetEntry"
        params = ["size_t index"]
        with content.function(ret, name, params, align=True):
            content.add([
                f"return {self.ident}_Entries[",
                f"  {self.ident}_Map[ index ]", "];"
            ])
        fixture = f"{self.ident}_Fixture"
        prologue = CContent()
        epilogue = CContent()
        if header:
            content.add(f"static T_fixture_node {self.ident}_Node;")
            ret = "void"
            name = f"{self.ident}_Run"
            params = self._get_run_params(header)
            prologue.add([f"{self.context} *ctx;", "size_t index;"])
            self.assign_run_params(prologue, header)
            prologue.call_function("ctx =", "T_push_fixture",
                                   [f"&{self.ident}_Node", f"&{fixture}"])
            prologue.append(["ctx->in_action_loop = true;", "index = 0;"])
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
            self._add_for_loops(content, transition_map, 0)
            content.add(epilogue)

    def _add_handler(self, content: CContent, conditions: List[Any],
                     co_idx_to_enum: _IdxToX, action: str) -> None:
        for co_idx, condition in enumerate(conditions):
            enum = co_idx_to_enum[co_idx]
            handler = f"{enum[0]}_{action}"
            params = [f"{self.context} *ctx", f"{enum[0]} state"]
            with content.function("static void", handler, params):
                content.add(self.substitute_code(condition["test-prologue"]))
                content.add("switch ( state ) {")
                with content.indent():
                    for state_index, state in enumerate(condition["states"]):
                        content.add(f"case {enum[state_index + 1]}: {{")
                        with content.indent():
                            with content.comment_block():
                                content.wrap(
                                    self.substitute_text(state["text"]))
                            content.append(
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
        _add_condition_enum(content, self._pre_co_idx_to_enum)
        _add_condition_enum(content, self._post_co_idx_to_enum)
        super().add_header_body(content, header)

    def generate(self, content: CContent, base_directory: str,
                 test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        self.add_test_case_description(content, test_case_to_suites)
        header = self["test-header"]
        if header:
            self.generate_header(base_directory, header)
        else:
            _add_condition_enum(content, self._pre_co_idx_to_enum)
            _add_condition_enum(content, self._post_co_idx_to_enum)
        instance = self.add_context(content)
        self._add_pre_condition_descriptions(content)
        content.add(self.substitute_code(self["test-support"]))
        self._add_handler(content, self["pre-conditions"],
                          self._pre_co_idx_to_enum, "Prepare")
        self._add_handler(content, self["post-conditions"],
                          self._post_co_idx_to_enum, "Check")
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
        self.add_function(content, "test-prepare", "Prepare")
        self.add_function(content, "test-action", "Action")
        self.add_function(content, "test-cleanup", "Cleanup")
        transition_map = TransitionMap(self.item)
        transition_map.add_map(content, self.ident)
        self._add_fixture_scope(content)
        content.add([
            f"static T_fixture {self.ident}_Fixture = {{",
            f"  .setup = {setup},", f"  .stop = {stop},",
            f"  .teardown = {teardown},", f"  .scope = {self.ident}_Scope,",
            f"  .initial_context = {instance}", "};"
        ])
        self._add_test_case(content, transition_map, header)
        content.add("/** @} */")


class _RuntimeMeasurementRequestItem(_TestItem):
    """ A runtime measurement request item. """
    def __init__(self, item: Item, context: str):
        super().__init__(item)
        self._context = context


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
