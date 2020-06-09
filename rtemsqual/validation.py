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
import os
import string
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Tuple

from rtemsqual.content import CContent, CInclude, enabled_by_to_exp, \
    ExpressionMapper
from rtemsqual.items import Item, ItemCache, ItemMapper

ItemMap = Dict[str, Item]


class StepWrapper(Mapping[str, object]):
    """ Test step wrapper. """
    def __init__(self):
        self._step = 0

    @property
    def steps(self):
        """ The count of test steps. """
        return self._step

    def __getitem__(self, name):
        if name == "step":
            step = self._step
            self._step = step + 1
            return step
        raise KeyError

    def __iter__(self):
        raise StopIteration

    def __len__(self):
        return 1


def _add_ingroup(content: CContent, items: List["_TestItem"]) -> None:
    content.add_ingroup([item.group_identifier for item in items])


class _TestItem:
    """ A test item with a defaul implementation for test cases. """
    def __init__(self, item: Item):
        self._item = item
        self._ident = self.name.replace(" ", "")

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
        return self._item["name"]

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
                content.wrap(action["description"], initial_indent="- ")
                for check in action["checks"]:
                    content.wrap(check["description"],
                                 initial_indent="  - ",
                                 subsequent_indent="    ")

    def _generate_test_case_actions(self, steps: StepWrapper) -> CContent:
        content = CContent()
        for action in self["actions"]:
            content.add(action["action"])
            for check in action["checks"]:
                content.append(
                    string.Template(check["check"]).substitute(steps))
        return content

    def generate(self, content: CContent, _base_directory: str,
                 test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Generates the content. """
        self.add_test_case_description(content, test_case_to_suites)
        content.add(self["support"])
        with content.function_block(f"void T_case_body_{self.ident}( void )"):
            content.add_brief_description(self["brief"])
            content.wrap(self["description"])
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
            content.add(self["prologue"])
            steps = StepWrapper()
            action_content = self._generate_test_case_actions(steps)
            if steps.steps > 0:
                content.add(f"T_plan({steps.steps});")
            content.add(action_content)
            content.add(self["epilogue"])
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
            content.wrap(self["description"])
            content.add("@{")
        content.add(self["code"])
        content.add("/** @} */")


class _PostCondition(NamedTuple):
    """ A set of post conditions with an enabled by expression. """
    enabled_by: str
    conditions: Tuple[int, ...]


_DirectiveIndexToEnum = Tuple[Tuple[str, ...], ...]
_TransitionMap = List[List[_PostCondition]]


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
        ]) for index, condition in enumerate(conditions))


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
    def name(self) -> str:
        return self._item["test-name"]

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
                content.add(",\n".join(f"\"{state['name']}\""
                                       for state in condition["states"]))
            content.add("};")
        content.add("static const char * const * const "
                    f"{self.ident}_PreDesc[] = {{")
        with content.indent():
            content.add(",\n".join(f"{self.ident}_PreDesc_{condition['name']}"
                                   for condition in self["pre-conditions"]))
        content.add("};")

    def _add_context(self, content: CContent, header: Dict[str, Any]) -> None:
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
                content.add(f"{param};")
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

    def _add_scope_body(self, content: CContent) -> None:
        with content.condition("!ctx->in_action_loop"):
            content.add("return;")
        with content.for_loop("i = 0",
                              f"i < RTEMS_ARRAY_SIZE( {self.ident}_PreDesc )",
                              "++i"):
            content.add("size_t m;")
            with content.condition("n > 0"):
                content.add(["buf[ 0 ] = '/';", "--n;", "++buf;"])
            content.call_function(
                "m =", "strlcpy",
                ["buf", f"{self.ident}_PreDesc[ i ][ ctx->pcs[ i ] ]", "n"])
            with content.first_condition("m < n"):
                content.add(["n -= m;", "buf += m;"])
            with content.final_condition(None):
                content.add("n = 0;")

    def _add_fixture_scope(self, content: CContent) -> None:
        params = ["void *arg", "char *buf", "size_t n"]
        with content.function("static void", f"{self.ident}_Scope", params):
            content.add(
                [f"{self.context} *ctx;", "size_t i;", "", "ctx = arg;"])
            self._add_scope_body(content)

    def _add_fixture_method(self, content: CContent,
                            info: Optional[Dict[str, Optional[str]]],
                            name: str) -> str:
        if not info:
            return "NULL"
        method = f"{self.ident}_{name}"
        wrap = f"{method}_Wrap"
        content.add_description_block(info["brief"], info["description"])
        with content.function("static void", method, [f"{self.context} *ctx"]):
            content.add(info["code"])
        with content.function("static void", wrap, ["void *arg"]):
            content.add([
                f"{self.context} *ctx;", "", "ctx = arg;",
                "ctx->in_action_loop = false;", f"{method}( ctx );"
            ])
        return wrap

    def _add_transitions(self, condition_index: int, map_index: int,
                         transition: Dict[str,
                                          Any], transition_map: _TransitionMap,
                         post: Tuple[int, ...]) -> None:
        # pylint: disable=too-many-arguments
        if condition_index < self._pre_condition_count:
            condition = self._pre_index_to_condition[condition_index]
            state_count = len(condition["states"])
            map_index *= state_count
            states = transition["pre-conditions"][condition["name"]]
            if isinstance(states, str):
                assert states == "all"
                for index in range(state_count):
                    self._add_transitions(condition_index + 1,
                                          map_index + index, transition,
                                          transition_map, post)
            else:
                for state in states:
                    self._add_transitions(
                        condition_index + 1, map_index +
                        self._pre_state_to_index[condition_index][state],
                        transition, transition_map, post)
        else:
            enabled_by = enabled_by_to_exp(transition["enabled-by"],
                                           ExpressionMapper())
            assert enabled_by != "1" or not transition_map[map_index]
            transition_map[map_index].append(_PostCondition(enabled_by, post))

    def _get_transition_map(self) -> _TransitionMap:
        transition_count = 1
        for condition in self["pre-conditions"]:
            state_count = len(condition["states"])
            assert state_count > 0
            transition_count *= state_count
        transition_map = [list() for _ in range(transition_count)
                          ]  # type: _TransitionMap
        for transition in self["transition-map"]:
            post = tuple(self._post_state_to_index[index][
                transition["post-conditions"][self._post_index_to_name[index]]]
                         for index in range(self._post_condition_count))
            self._add_transitions(0, 0, transition, transition_map, post)
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
        elements = []
        for transistions in transition_map:
            assert transistions[0].enabled_by == "1"
            if len(transistions) == 1:
                elements.append(
                    self._post_condition_enumerators(
                        transistions[0].conditions))
            else:
                ifelse = "#if "
                enumerators = []  # type: List[str]
                for variant in transistions[1:]:
                    enumerators.append(ifelse + variant.enabled_by)
                    enumerators.append(
                        self._post_condition_enumerators(variant.conditions))
                    ifelse = "#elif "
                enumerators.append("#else")
                enumerators.append(
                    self._post_condition_enumerators(
                        transistions[0].conditions))
                enumerators.append("#endif")
                elements.append("\n".join(enumerators))
        content.append(["\n  }, {\n".join(elements), "  }", "};"])

    def _add_action(self, content: CContent) -> None:
        for index, enum in enumerate(self._pre_index_to_enum):
            content.append(f"{enum[0]}_Prepare( ctx, ctx->pcs[ {index} ] );")
        content.append(self["test-action"])
        transition_map = f"{self.ident}_TransitionMap"
        for index, enum in enumerate(self._post_index_to_enum):
            content.append([
                f"{enum[0]}_Check(", "  ctx,",
                f"  {transition_map}[ index ][ {index} ]", ");"
            ])
        content.append("++index;")

    def _add_for_loops(self, content: CContent, index: int) -> None:
        if index < self._pre_condition_count:
            var = f"ctx->pcs[ {index} ]"
            begin = self._pre_index_to_enum[index][1]
            end = self._pre_index_to_enum[index][-1]
            with content.for_loop(f"{var} = {begin}", f"{var} != {end} + 1",
                                  f"++{var}"):
                self._add_for_loops(content, index + 1)
        else:
            self._add_action(content)

    def _add_test_case(self, content: CContent, header: Dict[str,
                                                             Any]) -> None:
        fixture = f"{self.ident}_Fixture"
        if header:
            ret = "void"
            name = f"{self.ident}_Run"
            params = self._get_run_params(header)
            prologue = [
                f"{self.context} *ctx;", "size_t index;", "",
                f"ctx = T_push_fixture( &{self.ident}_Node, &{fixture} );"
            ]
            prologue.extend(f"ctx->{param['name']} = {param['name']}"
                            for param in header["run-params"])
            prologue.extend(["ctx->in_action_loop = true;", "index = 0;"])
            epilogue = ["T_pop_fixture();"]
        else:
            with content.function_block(
                    f"void T_case_body_{self.ident}( void )"):
                content.add_brief_description(self["test-brief"])
                content.wrap(self["test-description"])
            content.gap = False
            ret = ""
            name = "T_TEST_CASE_FIXTURE"
            params = [f"{self.ident}", f"&{fixture}"]
            prologue = [
                f"{self.context} *ctx;", "size_t index;", "",
                "ctx = T_fixture_context();", "ctx->in_action_loop = true;",
                "index = 0;"
            ]
            epilogue = []
        with content.function(ret, name, params):
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
                content.add(condition["test-prologue"])
                content.add("switch ( state ) {")
                with content.indent():
                    for state_index, state in enumerate(condition["states"]):
                        content.add(f"case {enum[state_index + 1]}: {{")
                        with content.indent():
                            content.add(state["test-code"])
                            content.append("break;")
                        content.add("}")
                content.add("}")
                content.add(condition["test-epilogue"])

    def _get_run_params(self, header: Optional[Dict[str, Any]]) -> List[str]:
        if not header:
            return []
        mapper = ItemMapper(self._item)
        return [
            mapper.substitute_with_prefix(param["specifier"],
                                          f"test-header/run-params[{index}]")
            for index, param in enumerate(header["run-params"])
        ]

    def _generate_header_body(self, content: CContent,
                              header: Dict[str, Any]) -> None:
        _directive_add_enum(content, self._pre_index_to_enum)
        _directive_add_enum(content, self._post_index_to_enum)
        content.add(header["code"])
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
        content.add_spdx_license_identifier()
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
        content.add(self["test-support"])
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
        content.add_spdx_license_identifier()
        with content.file_block():
            _add_ingroup(content, self._test_suites)
            _add_ingroup(content, self._test_cases)
        content.add_copyrights_and_licenses()
        content.add_have_config()
        content.add_includes(includes)
        content.add_includes(local_includes, local=True)
        content.add_includes([CInclude("t.h")])
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


def _gather_items(item: Item, source_files: Dict[str, _SourceFile],
                  test_programs: List[_TestProgram]) -> None:
    for child in item.children():
        _gather_items(child, source_files, test_programs)
    if item["type"] == "test-suite":
        src = _get_source_file(item["target"], source_files)
        src.add_test_suite(item)
    elif item["type"] == "test-case":
        src = _get_source_file(item["target"], source_files)
        src.add_test_case(item)
    elif item["type"] == "requirement" and item[
            "requirement-type"] == "functional" and item[
                "functional-type"] == "action":
        src = _get_source_file(item["test-target-source"], source_files)
        src.add_test_directive(item)
    elif item["type"] == "build" and item["build-type"] == "test-program":
        test_programs.append(_TestProgram(item))


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
    for item in item_cache.top_level.values():
        _gather_items(item, source_files, test_programs)

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
