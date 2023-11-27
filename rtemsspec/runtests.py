# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a build step to run the RTEMS Tester. """

# Copyright (C) 2022 embedded brains GmbH (http://www.embedded-brains.de)
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

import datetime
import json
import os
import logging
import time
from typing import Dict, List

from rtemsspec.directorystate import DirectoryState
from rtemsspec.items import Item
from rtemsspec.packagebuild import BuildItem, PackageBuildDirector
from rtemsspec.testoutputparser import augment_report
from rtemsspec.testrunner import Executable, Report, TestRunner


def _now_utc() -> str:
    return datetime.datetime.utcnow().isoformat()


class TestLog(DirectoryState):
    """ Maintains a test log. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.reports: List[Report] = []

    def discard(self) -> None:
        try:
            with open(self.file, "r", encoding="utf-8") as src:
                self.reports = json.load(src)["reports"]
            logging.info("%s: loaded test log: %s", self.uid, self.file)
        except FileNotFoundError:
            self.reports = []
        super().discard()

    def get_reports_by_hash(self) -> Dict[str, Report]:
        """ Gets the reports by executable hash. """
        reports_by_hash: Dict[str, Report] = {}
        for report in self.reports:
            digest = report["executable-sha512"]
            assert digest not in reports_by_hash
            assert isinstance(digest, str)
            reports_by_hash[digest] = report
        return reports_by_hash


class RunTests(BuildItem):
    """ Runs the tests. """

    def run(self) -> None:
        start_time = _now_utc()
        begin = time.monotonic()
        log = self.output("log")
        assert isinstance(log, TestLog)
        previous_reports_by_hash = log.get_reports_by_hash()

        # Use previous report if the executable hash did not change
        source = self.input("source")
        assert isinstance(source, DirectoryState)
        reports: List[Report] = []
        executables: List[Executable] = []
        for path, digest in source.files_and_hashes():
            if not path.endswith(".exe") or path.endswith(".norun.exe"):
                continue
            assert digest
            report = previous_reports_by_hash.get(digest, None)
            if report is None:
                logging.debug("%s: run: %s", self.uid, path)
                executables.append(Executable(path, digest, 1800))
            else:
                logging.debug("%s: use previous report for: %s", self.uid,
                              path)
                report["executable"] = path
                reports.append(report)

        # Run the tests with changed executables
        if executables:
            reports.extend(self._run_tests(executables))

        # Save the reports
        os.makedirs(os.path.dirname(log.file), exist_ok=True)
        with open(log.file, "w", encoding="utf-8") as dst:
            data = {
                "duration": time.monotonic() - begin,
                "end-time": _now_utc(),
                "reports": sorted(reports, key=lambda x: x["executable"]),
                "start-time": start_time
            }
            json.dump(data, dst, sort_keys=True, indent=2)

    def _run_tests(self, executables: List[Executable]) -> List[Report]:
        runner = self.input("runner")
        assert isinstance(runner, TestRunner)
        max_run_count = runner["max-retry-count-per-executable"] + 1
        reports_by_path: Dict[str, Report] = {}
        while executables and max_run_count:
            for new_report in runner.run_tests(executables):
                augment_report(new_report, new_report["output"])
                logging.warning("%s: report: %s", self.uid, new_report)
                reports_by_path[new_report["executable"]] = new_report
            next_executables: List[Executable] = []
            for executable in executables:
                report = reports_by_path.get(executable.path, None)
                if report is None:
                    logging.warning("%s: no report for: %s", self.uid,
                                    executable.path)
                    next_executables.append(executable)
                    continue
                if report.get("gcov-info-hash",
                              "") != report.get("gcov-info-hash-calculated",
                                                ""):
                    next_executables.append(executable)
                    logging.warning("%s: gcov info is corrupt for: %s",
                                    self.uid, executable.path)
                    continue
                test_suite = report.get("test-suite", {})
                if test_suite.get("report-hash", "") != test_suite.get(
                        "report-hash-calculated", ""):
                    next_executables.append(executable)
                    logging.warning("%s: test suite report is corrupt for: %s",
                                    self.uid, executable.path)
                    continue
            executables = next_executables
            max_run_count -= 1
        return list(reports_by_path.values())
