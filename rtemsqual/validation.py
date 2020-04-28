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

from rtemsqual.content import CContent
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


def _designator(name: str) -> str:
    return name.replace(" ", "")


def _add_ingroup(content: CContent, items: List[Item], prefix: str,
                 key: str) -> None:
    content.add_ingroup(
        [f"{prefix}{_designator(item[key])}" for item in items])


def _add_test_case_description(content: CContent, item: Item,
                               test_case_to_suites: Dict[str, List[Item]],
                               identifier: str, name: str) -> None:
    with content.defgroup_block(f"RTEMSTestCase{identifier}", name):
        _add_ingroup(content, test_case_to_suites[item.uid], "RTEMSTestSuite",
                     "test-suite-name")
        content.add(["@brief Test Case", "", "@{"])


def _add_test_case_action_description(content: CContent, item: Item) -> None:
    actions = item["test-case-actions"]
    if actions:
        content.add("This test case performs the following actions:")
        for action in actions:
            content.add(content.wrap(action["description"], intro="- "))
            for check in action["checks"]:
                content.add(content.wrap(check["description"], intro="  - "))


def _generate_test_case_actions(item: Item, steps: StepWrapper) -> CContent:
    content = CContent()
    for action in item["test-case-actions"]:
        content.add(action["action"])
        for check in action["checks"]:
            content.append(string.Template(check["check"]).substitute(steps))
    return content


def _generate_test_case(content: CContent, item: Item,
                        test_case_to_suites: Dict[str, List[Item]]) -> None:
    name = item["test-case-name"]
    desi = _designator(name)
    _add_test_case_description(content, item, test_case_to_suites, desi, name)
    content.add(item["test-case-support"])
    with content.function_block(f"void T_case_body_{desi}(void)"):
        content.add_brief_description(item["test-case-brief"])
        content.add(content.wrap(item["test-case-description"]))
        _add_test_case_action_description(content, item)
    fixture = item["test-case-fixture"]
    if fixture:
        content.append(f"T_TEST_CASE_FIXTURE({desi}, &{fixture})")
    else:
        content.append(f"T_TEST_CASE({desi})")
    content.append("{")
    content.gap = False
    with content.indent():
        content.add(item["test-case-prologue"])
        steps = StepWrapper()
        action_content = _generate_test_case_actions(item, steps)
        if steps.steps > 0:
            content.add(f"T_plan({steps.steps});")
        content.add(action_content)
        content.add(item["test-case-epilogue"])
    content.append(["}", "", "/** @} */"])


def _generate_test_suite(content: CContent, item: Item) -> None:
    name = item["test-suite-name"]
    with content.defgroup_block(f"RTEMSTestSuite{_designator(name)}", name):
        content.add(["@ingroup RTEMSTestSuites", "", "@brief Test Suite"])
        content.add(content.wrap(item["test-suite-description"]))
        content.add("@{")
    content.add(item["test-suite-code"])
    content.add("/** @} */")


class SourceFile:
    """ A test source file. """
    def __init__(self, filename: str):
        """ Initializes a test source file. """
        self._file = filename
        self._test_suites = []  # type: List[Item]
        self._test_cases = []  # type: List[Item]

    @property
    def test_suites(self) -> List[Item]:
        """ The test suites of the source file. """
        return self._test_suites

    @property
    def test_cases(self) -> List[Item]:
        """ The test cases of the source file. """
        return self._test_cases

    def add_test_suite(self, test_suite: Item) -> None:
        """ Adds a test suite to the source file. """
        self._test_suites.append(test_suite)

    def add_test_case(self, test_case: Item) -> None:
        """ Adds a test case to the source file. """
        self._test_cases.append(test_case)

    def generate(self, base_directory: str,
                 test_case_to_suites: Dict[str, List[Item]]) -> None:
        """
        Generates the source file and the corresponding build specification.
        """
        content = CContent()
        includes = []  # type: List[str]
        local_includes = []  # type: List[str]
        for item in itertools.chain(self._test_suites, self._test_cases):
            includes.extend(item["includes"])
            local_includes.extend(item["local-includes"])
            item.register_license_and_copyrights(content)
        content.add_spdx_license_identifier()
        with content.file_block():
            _add_ingroup(content, self._test_suites, "RTEMSTestSuite",
                         "test-suite-name")
            _add_ingroup(content, self._test_cases, "RTEMSTestCase",
                         "test-case-name")
        content.add_copyrights_and_licenses()
        content.add_have_config()
        content.add_includes(includes)
        content.add_includes(local_includes, local=True)
        content.add_includes(["t.h"])
        for item in sorted(self._test_cases,
                           key=lambda x: x["test-case-name"]):
            _generate_test_case(content, item, test_case_to_suites)
        for item in sorted(self._test_suites,
                           key=lambda x: x["test-suite-name"]):
            _generate_test_suite(content, item)
        content.write(os.path.join(base_directory, self._file))


class TestProgram:
    """ A test program. """
    def __init__(self, item: Item):
        """ Initializes a test program. """
        self._item = item
        self._source_files = []  # type: List[SourceFile]

    @property
    def source_files(self) -> List[SourceFile]:
        """ The source files of the test program. """
        return self._source_files

    def add_source_files(self, source_files: Dict[str, SourceFile]) -> None:
        """
        Adds the source files of the test program which are present in the
        source file map.
        """
        for filename in self._item["source"]:
            source_file = source_files.get(filename, None)
            if source_file is not None:
                self._source_files.append(source_file)


def _get_source_file(filename: str,
                     source_files: Dict[str, SourceFile]) -> SourceFile:
    return source_files.setdefault(filename, SourceFile(filename))


def _gather_items(item: Item, source_files: Dict[str, SourceFile],
                  test_programs: List[TestProgram]) -> None:
    for child in item.children():
        _gather_items(child, source_files, test_programs)
    if item["type"] == "test-suite":
        src = _get_source_file(item["source"], source_files)
        src.add_test_suite(item)
    elif item["type"] == "test-case":
        src = _get_source_file(item["source"], source_files)
        src.add_test_case(item)
    elif item["type"] == "build" and item["build-type"] == "test-program":
        test_programs.append(TestProgram(item))


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates source files and build specification items for validation test
    suites and test cases according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the validation
                       test suites and test cases.
    """
    source_files = {}  # type: Dict[str, SourceFile]
    test_programs = []  # type: List[TestProgram]
    for item in item_cache.top_level.values():
        _gather_items(item, source_files, test_programs)

    test_case_to_suites = {}  # type: Dict[str, List[Item]]
    for test_program in test_programs:
        test_program.add_source_files(source_files)
        test_suites = []  # type: List[Item]
        for source_file in test_program.source_files:
            test_suites.extend(source_file.test_suites)
        for source_file in test_program.source_files:
            for test_case in source_file.test_cases:
                test_case_to_suites.setdefault(test_case.uid,
                                               []).extend(test_suites)

    for src in source_files.values():
        src.generate(config["base-directory"], test_case_to_suites)
