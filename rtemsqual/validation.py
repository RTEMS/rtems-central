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
from typing import Dict, List, Mapping

from rtemsqual.content import CContent, CInclude
from rtemsqual.items import Item, ItemCache

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

    def generate(self, content: CContent,
                 test_case_to_suites: Dict[str, List["_TestItem"]]) -> None:
        """ Generates the content. """
        self.add_test_case_description(content, test_case_to_suites)
        content.add(self["support"])
        with content.function_block(f"void T_case_body_{self.ident}(void)"):
            content.add_brief_description(self["brief"])
            content.wrap(self["description"])
            self._add_test_case_action_description(content)
        fixture = self["fixture"]
        if fixture:
            content.append(f"T_TEST_CASE_FIXTURE({self.ident}, &{fixture})")
        else:
            content.append(f"T_TEST_CASE({self.ident})")
        content.append("{")
        content.gap = False
        with content.indent():
            content.add(self["prologue"])
            steps = StepWrapper()
            action_content = self._generate_test_case_actions(steps)
            if steps.steps > 0:
                content.add(f"T_plan({steps.steps});")
            content.add(action_content)
            content.add(self["epilogue"])
        content.add(["}", "", "/** @} */"])


class _TestSuiteItem(_TestItem):
    """ A test suite item. """
    @property
    def group_identifier(self) -> str:
        return f"RTEMSTestSuite{self.ident}"

    def generate(self, content: CContent,
                 _test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        with content.defgroup_block(self.group_identifier, self.name):
            content.add(["@ingroup RTEMSTestSuites", "", "@brief Test Suite"])
            content.wrap(self["description"])
            content.add("@{")
        content.add(self["code"])
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

    def generate(self, base_directory: str,
                 test_case_to_suites: Dict[str, List[_TestItem]]) -> None:
        """
        Generates the source file and the corresponding build specification.
        """
        content = CContent()
        includes = []  # type: List[CInclude]
        local_includes = []  # type: List[CInclude]
        for item in itertools.chain(self._test_suites, self._test_cases):
            for inc in item.includes:
                includes.append(CInclude(inc))
            for inc in item.local_includes:
                local_includes.append(CInclude(inc))
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
            item.generate(content, test_case_to_suites)
        for item in sorted(self._test_suites, key=lambda x: x.name):
            item.generate(content, test_case_to_suites)
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
