# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a test output parser. """

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

import base64
import hashlib
import re
from typing import Any, Dict, Iterable

_TEST_BEGIN = re.compile(r"\*\*\* BEGIN OF TEST ([^*]+) \*\*\*")
_TEST_VERSION = re.compile(r"\*\*\* TEST VERSION: (.+)")
_TEST_STATE = re.compile(r"\*\*\* TEST STATE: (.+)")
_TEST_BUILD = re.compile(r"\*\*\* TEST BUILD: ?(.*)")
_TEST_TOOLS = re.compile(r"\*\*\* TEST TOOLS: (.+)")
_TEST_END = re.compile(r"\*\*\* END OF TEST ([^*]+) \*\*\*")

_TS_SUITE_BEGIN = re.compile(r"A:(.+)")
_TS_SUITE_END = re.compile(r"Z:([^:]+):C:([^:]+):N:([^:]+):F:([^:]+):D:(.+)")
_TS_CASE_BEGIN = re.compile(r"B:(.+)")
_TS_CASE_END = re.compile(r"E:([^:]+):N:([^:]+):F:([^:]+):D:(.+)")
_TS_PLATFORM = re.compile(r"S:Platform:(.+)")
_TS_COMPILER = re.compile(r"S:Compiler:(.+)")
_TS_VERSION = re.compile(r"S:Version:(.+)")
_TS_BSP = re.compile(r"S:BSP:(.+)")
_TS_BUILD_LABEL = re.compile(r"S:BuildLabel:(.+)")
_TS_TARGET_HASH = re.compile(r"S:TargetHash:SHA256:(.*)")
_TS_RTEMS_DEBUG = re.compile(r"S:RTEMS_DEBUG:([01])$")
_TS_RTEMS_MULTIPROCESSING = re.compile(r"S:RTEMS_MULTIPROCESSING:([01])$")
_TS_RTEMS_POSIX_API = re.compile(r"S:RTEMS_POSIX_API:([01])$")
_TS_RTEMS_PROFILING = re.compile(r"S:RTEMS_PROFILING:([01])$")
_TS_RTEMS_SMP = re.compile(r"S:RTEMS_SMP:([01])$")
_TS_REMARK = re.compile(r"R:(.+)")
_TS_REPORT_HASH = re.compile(r"Y:ReportHash:SHA256:(.+)")

_M_BEGIN = re.compile(r"M:B:(.+)")
_M_END = re.compile(r"M:E:([^:]+):D:(.+)")
_M_V = re.compile(r"M:V:(.+)")
_M_N = re.compile(r"M:N:(.+)")
_M_S = re.compile(r"M:S:([^:]+):(.+)")
_M_MI = re.compile(r"M:MI:(.+)")
_M_P1 = re.compile(r"M:P1:(.+)")
_M_Q1 = re.compile(r"M:Q1:(.+)")
_M_Q2 = re.compile(r"M:Q2:(.+)")
_M_Q3 = re.compile(r"M:Q3:(.+)")
_M_P99 = re.compile(r"M:P99:(.+)")
_M_MX = re.compile(r"M:MX:(.+)")
_M_MAD = re.compile(r"M:MAD:(.+)")
_M_D = re.compile(r"M:D:(.+)")

_GCOV_BEGIN = "*** BEGIN OF GCOV INFO BASE64 ***"
_GCOV_END = "*** END OF GCOV INFO BASE64 ***"
_GCOV_HASH = re.compile(r"\*\*\* GCOV INFO SHA256 (.*) \*\*\*")

_RECORDS_BEGIN = "*** BEGIN OF RECORDS BASE64 ***"
_RECORDS_END = "*** END OF RECORDS BASE64 ***"
_RECORDS_ZLIB_BEGIN = "*** BEGIN OF RECORDS BASE64 ZLIB ***"
_RECORDS_ZLIB_END = "*** END OF RECORDS BASE64 ZLIB ***"


def _are_samples_valid(measurement) -> bool:
    if len(measurement["samples"]) != measurement["sample-count"]:
        return False
    if not measurement["samples"]:
        return True
    if measurement["min"] != measurement["samples"][0]:
        return False
    return measurement["max"] == measurement["samples"][-1]


class TestOutputParser:
    """ Provides a line by line parser of test output. """

    # pylint: disable=too-few-public-methods
    def __init__(self, data) -> None:
        self.data = data
        self.consume = self._test_begin
        self.hash_line = self._hash_none
        assert "info" not in data
        self.data["info"] = {}
        self.data["data-ranges"] = []
        assert "test-suite" not in data
        self.level = 0
        self._hash_state = hashlib.sha256()
        self._measurement: Dict[str, Any] = {}
        self._test_case: Dict[str, Any] = {}

    def _error(self, index: int) -> bool:
        assert "line-parser-error" not in self.data
        self.data["line-parser-error"] = index
        self.consume = self._extra
        return False

    def _hash_none(self, line: str) -> None:
        pass

    def _hash_sha256(self, line: str) -> None:
        self._hash_state.update(f"{line}\n".encode("ascii"))

    def _hash_sha256_skip_one(self, line: str) -> None:
        # pylint: disable=unused-argument
        self.hash_line = self._hash_sha256

    def _hash_finalize(self) -> str:
        self.hash_line = self._hash_none
        digest = base64.urlsafe_b64encode(
            self._hash_state.digest()).decode("ascii")
        return digest

    def _test_begin(self, index: int, line: str) -> bool:
        mobj = _TEST_BEGIN.match(line)
        if mobj:
            self.level += 1
            self.data["info"]["line-begin-of-test"] = index
            self.data["info"]["name"] = mobj.group(1)
            self.consume = self._test_version
            return True
        return self._extra(index, line)

    def _test_version(self, index: int, line: str) -> bool:
        mobj = _TEST_VERSION.match(line)
        if mobj:
            self.data["info"]["version"] = mobj.group(1)
            self.data["info"]["line-version"] = index
            self.consume = self._test_state
            return True
        self.consume = self._test_body
        return self._test_body(index, line)

    def _test_state(self, index: int, line: str) -> bool:
        mobj = _TEST_STATE.match(line)
        if mobj:
            self.data["info"]["state"] = mobj.group(1)
            self.data["info"]["line-state"] = index
            self.consume = self._test_build
            return True
        return self._error(index)

    def _test_build(self, index: int, line: str) -> bool:
        mobj = _TEST_BUILD.match(line)
        if mobj:
            build = mobj.group(1)
            if build:
                self.data["info"]["build"] = build.split(", ")
            else:
                self.data["info"]["build"] = []
            self.data["info"]["line-build"] = index
            self.consume = self._test_tools
            return True
        return self._error(index)

    def _test_tools(self, index: int, line: str) -> bool:
        mobj = _TEST_TOOLS.match(line)
        if mobj:
            self.data["info"]["tools"] = mobj.group(1)
            self.data["info"]["line-tools"] = index
            self.consume = self._test_body
            return True
        return self._error(index)

    def _test_body(self, index: int, line: str) -> bool:
        if self._test_suite_begin(index, line):
            return True
        mobj = _TEST_END.match(line)
        if mobj:
            self.level -= 1
            if self.data["info"]["name"] == mobj.group(1):
                self.data["info"]["line-end-of-test"] = index
                self.consume = self._extra
                return True
            return self._error(index)
        return self._extra(index, line)

    def _test_suite_begin(self, index: int, line: str) -> bool:
        mobj = _TS_SUITE_BEGIN.match(line)
        if mobj:
            self.level += 1
            self.data["test-suite"] = {
                "duration": "?",
                "failed-steps-count": "?",
                "line-begin": index,
                "line-duration": "?",
                "line-end": "?",
                "line-failed-steps-count": "?",
                "line-report-hash": "?",
                "line-step-count": "?",
                "name": mobj.group(1),
                "report-hash": "?",
                "report-hash-calculated": "?",
                "step-count": "?",
                "test-cases": []
            }
            self.consume = self._test_suite_platform
            self._hash_state = hashlib.sha256()
            self.hash_line = self._hash_sha256
            return True
        return self._extra(index, line)

    def _test_suite_platform(self, index: int, line: str) -> bool:
        mobj = _TS_PLATFORM.match(line)
        if mobj:
            self.data["test-suite"]["platform"] = mobj.group(1)
            self.data["test-suite"]["line-platform"] = index
            self.consume = self._test_suite_compiler
            return True
        return self._error(index)

    def _test_suite_compiler(self, index: int, line: str) -> bool:
        mobj = _TS_COMPILER.match(line)
        if mobj:
            self.data["test-suite"]["compiler"] = mobj.group(1)
            self.data["test-suite"]["line-compiler"] = index
            self.consume = self._test_suite_version
            return True
        return self._error(index)

    def _test_suite_version(self, index: int, line: str) -> bool:
        mobj = _TS_VERSION.match(line)
        if mobj:
            self.data["test-suite"]["version"] = mobj.group(1)
            self.data["test-suite"]["line-version"] = index
            self.consume = self._test_suite_bsp
            return True
        return self._error(index)

    def _test_suite_bsp(self, index: int, line: str) -> bool:
        mobj = _TS_BSP.match(line)
        if mobj:
            self.data["test-suite"]["bsp"] = mobj.group(1)
            self.data["test-suite"]["line-bsp"] = index
            self.consume = self._test_suite_build_label
            return True
        return self._error(index)

    def _test_suite_build_label(self, index: int, line: str) -> bool:
        mobj = _TS_BUILD_LABEL.match(line)
        if mobj:
            self.data["test-suite"]["build-label"] = mobj.group(1)
            self.data["test-suite"]["line-build-label"] = index
            self.consume = self._test_suite_target_hash
            return True
        return self._error(index)

    def _test_suite_target_hash(self, index: int, line: str) -> bool:
        mobj = _TS_TARGET_HASH.match(line)
        if mobj:
            self.data["test-suite"]["target-hash"] = mobj.group(1)
            self.data["test-suite"]["line-target-hash"] = index
            self.consume = self._test_suite_rtems_debug
            return True
        return self._error(index)

    def _test_suite_rtems_debug(self, index: int, line: str) -> bool:
        mobj = _TS_RTEMS_DEBUG.match(line)
        if mobj:
            self.data["test-suite"]["rtems-debug"] = bool(int(mobj.group(1)))
            self.data["test-suite"]["line-rtems-debug"] = index
            self.consume = self._test_suite_rtems_multiprocessing
            return True
        return self._error(index)

    def _test_suite_rtems_multiprocessing(self, index: int, line: str) -> bool:
        mobj = _TS_RTEMS_MULTIPROCESSING.match(line)
        if mobj:
            self.data["test-suite"]["rtems-multiprocessing"] = bool(
                int(mobj.group(1)))
            self.data["test-suite"]["line-rtems-multiprocessing"] = index
            self.consume = self._test_suite_rtems_posix_api
            return True
        return self._error(index)

    def _test_suite_rtems_posix_api(self, index: int, line: str) -> bool:
        mobj = _TS_RTEMS_POSIX_API.match(line)
        if mobj:
            self.data["test-suite"]["rtems-posix-api"] = bool(
                int(mobj.group(1)))
            self.data["test-suite"]["line-rtems-posix-api"] = index
            self.consume = self._test_suite_rtems_profiling
            return True
        return self._error(index)

    def _test_suite_rtems_profiling(self, index: int, line: str) -> bool:
        mobj = _TS_RTEMS_PROFILING.match(line)
        if mobj:
            self.data["test-suite"]["rtems-profiling"] = bool(
                int(mobj.group(1)))
            self.data["test-suite"]["line-rtems-profiling"] = index
            self.consume = self._test_suite_rtems_smp
            return True
        return self._error(index)

    def _test_suite_rtems_smp(self, index: int, line: str) -> bool:
        mobj = _TS_RTEMS_SMP.match(line)
        if mobj:
            self.data["test-suite"]["rtems-smp"] = bool(int(mobj.group(1)))
            self.data["test-suite"]["line-rtems-smp"] = index
            self.consume = self._test_suite_body
            return True
        return self._error(index)

    def _test_suite_body(self, index: int, line: str) -> bool:
        if self._test_case_begin(index, line):
            return True
        mobj = _TS_SUITE_END.match(line)
        if mobj:
            self.level -= 1
            data = self.data["test-suite"]
            count = int(mobj.group(2))
            if data["name"] == mobj.group(1) and len(
                    data["test-cases"]) == count:
                data["line-end"] = index
                data["line-step-count"] = index
                data["line-failed-steps-count"] = index
                data["line-duration"] = index
                data["step-count"] = int(mobj.group(3))
                data["failed-steps-count"] = int(mobj.group(4))
                data["duration"] = float(mobj.group(5))
                self.consume = self._report_hash
                return True
            return self._error(index)
        return self._extra(index, line)

    def _test_case_begin(self, index: int, line: str) -> bool:
        mobj = _TS_CASE_BEGIN.match(line)
        if mobj:
            self.level += 1
            self._test_case = {
                "line-begin": index,
                "name": mobj.group(1),
                "remarks": [],
                "runtime-measurements": []
            }
            self.consume = self._test_case_body
            return True
        return self._extra(index, line)

    def _remark(self, index: int, line: str) -> bool:
        mobj = _TS_REMARK.match(line)
        if mobj:
            self._test_case["remarks"].append({
                "line": index,
                "remark": mobj.group(1)
            })
            return True
        return False

    def _test_case_body(self, index: int, line: str) -> bool:
        if self._measurement_begin(index, line):
            return True
        if self._remark(index, line):
            return True
        mobj = _TS_CASE_END.match(line)
        if mobj:
            self.level -= 1
            if self._test_case["name"] == mobj.group(1):
                self._test_case["line-end"] = index
                self._test_case["line-step-count"] = index
                self._test_case["line-failed-steps-count"] = index
                self._test_case["line-duration"] = index
                self._test_case["step-count"] = int(mobj.group(2))
                self._test_case["failed-steps-count"] = int(mobj.group(3))
                self._test_case["duration"] = float(mobj.group(4))
                self.data["test-suite"]["test-cases"].append(self._test_case)
                self.consume = self._test_suite_body
                return True
            return self._error(index)
        return self._extra(index, line)

    def _measurement_begin(self, index: int, line: str) -> bool:
        mobj = _M_BEGIN.match(line)
        if mobj:
            self.level += 1
            self._measurement = {
                "line-begin": index,
                "name": mobj.group(1),
                "samples": []
            }
            self.consume = self._measurement_variant
            return True
        return False

    def _measurement_variant(self, index: int, line: str) -> bool:
        mobj = _M_V.match(line)
        if mobj:
            self._measurement["variant"] = mobj.group(1)
            self.consume = self._measurement_count
            return True
        return self._error(index)

    def _measurement_count(self, index: int, line: str) -> bool:
        mobj = _M_N.match(line)
        if mobj:
            self._measurement["sample-count"] = int(mobj.group(1))
            self.consume = self._measurement_samples
            return True
        return self._error(index)

    def _measurement_samples(self, index: int, line: str) -> bool:
        if self._measurement_min(index, line):
            return True
        mobj = _M_S.match(line)
        if mobj:
            self._measurement["samples"].extend(  # type: ignore
                int(mobj.group(1)) * [float(mobj.group(2))])
            return True
        return self._error(index)

    def _measurement_min(self, index: int, line: str) -> bool:
        mobj = _M_MI.match(line)
        if mobj:
            self._measurement["min"] = float(mobj.group(1))
            self.consume = self._measurement_p1
            return True
        return self._extra(index, line)

    def _measurement_p1(self, index: int, line: str) -> bool:
        mobj = _M_P1.match(line)
        if mobj:
            self._measurement["p1"] = float(mobj.group(1))
            self.consume = self._measurement_q1
            return True
        return self._error(index)

    def _measurement_q1(self, index: int, line: str) -> bool:
        mobj = _M_Q1.match(line)
        if mobj:
            self._measurement["q1"] = float(mobj.group(1))
            self.consume = self._measurement_q2
            return True
        return self._error(index)

    def _measurement_q2(self, index: int, line: str) -> bool:
        mobj = _M_Q2.match(line)
        if mobj:
            self._measurement["q2"] = float(mobj.group(1))
            self.consume = self._measurement_q3
            return True
        return self._error(index)

    def _measurement_q3(self, index: int, line: str) -> bool:
        mobj = _M_Q3.match(line)
        if mobj:
            self._measurement["q3"] = float(mobj.group(1))
            self.consume = self._measurement_p99
            return True
        return self._error(index)

    def _measurement_p99(self, index: int, line: str) -> bool:
        mobj = _M_P99.match(line)
        if mobj:
            self._measurement["p99"] = float(mobj.group(1))
            self.consume = self._measurement_max
            return True
        return self._error(index)

    def _measurement_max(self, index: int, line: str) -> bool:
        mobj = _M_MX.match(line)
        if mobj:
            self._measurement["max"] = float(mobj.group(1))
            self.consume = self._measurement_mad
            return True
        return self._error(index)

    def _measurement_mad(self, index: int, line: str) -> bool:
        mobj = _M_MAD.match(line)
        if mobj:
            self._measurement["mad"] = float(mobj.group(1))
            self.consume = self._measurement_duration
            return True
        return self._error(index)

    def _measurement_duration(self, index: int, line: str) -> bool:
        mobj = _M_D.match(line)
        if mobj:
            self._measurement["duration-sum"] = float(mobj.group(1))
            self.consume = self._measurement_end
            return True
        return self._error(index)

    def _measurement_end(self, index: int, line: str) -> bool:
        mobj = _M_END.match(line)
        if mobj:
            self.level -= 1
            if self._measurement["name"] == mobj.group(
                    1) and _are_samples_valid(self._measurement):
                self._measurement["line-end"] = index
                self._measurement["duration-total"] = float(mobj.group(2))
                self._test_case["runtime-measurements"].append(  # type: ignore
                    self._measurement)
                self.consume = self._test_case_body
                return True
        return self._error(index)

    def _report_hash(self, index: int, line: str) -> bool:
        mobj = _TS_REPORT_HASH.match(line)
        if mobj:
            self.data["test-suite"][
                "report-hash-calculated"] = self._hash_finalize()
            self.data["test-suite"]["report-hash"] = mobj.group(1)
            self.data["test-suite"]["line-report-hash"] = index
            self.consume = self._test_body
            return True
        return self._extra(index, line)

    def _gcov_begin(self, index: int, line: str) -> bool:
        if line in _GCOV_BEGIN:
            self.level += 1
            self.data["line-gcov-info-base64-begin"] = index
            self.consume = self._gcov_end
            self._hash_state = hashlib.sha256()
            self.hash_line = self._hash_sha256_skip_one
            return True
        return False

    def _gcov_end(self, index: int, line: str) -> bool:
        if line in _GCOV_END:
            self.level -= 1
            self.data["gcov-info-hash-calculated"] = self._hash_finalize()
            self.data["line-gcov-info-base64-end"] = index
            self.data["data-ranges"].append(
                (self.data["line-gcov-info-base64-begin"] + 1, index))
            self.consume = self._extra
            return True
        return False

    def _gcov_hash(self, index: int, line: str) -> bool:
        mobj = _GCOV_HASH.match(line)
        if mobj:
            self.data["gcov-info-hash"] = mobj.group(1)
            self.data["line-gcov-info-hash"] = index
            return True
        return False

    def _records_begin(self, index: int, line: str) -> bool:
        if line in _RECORDS_BEGIN:
            self.level += 1
            self.data["line-records-base64-begin"] = index
            self.consume = self._records_end
            return True
        return False

    def _records_end(self, index: int, line: str) -> bool:
        if line in _RECORDS_END:
            self.level -= 1
            self.data["line-records-base64-end"] = index
            self.data["data-ranges"].append(
                (self.data["line-records-base64-begin"] + 1, index))
            self.consume = self._extra
            return True
        return False

    def _records_zlib_begin(self, index: int, line: str) -> bool:
        if line in _RECORDS_ZLIB_BEGIN:
            self.level += 1
            self.data["line-records-base64-zlib-begin"] = index
            self.consume = self._records_zlib_end
            return True
        return False

    def _records_zlib_end(self, index: int, line: str) -> bool:
        if line in _RECORDS_ZLIB_END:
            self.level -= 1
            self.data["line-records-base64-zlib-end"] = index
            self.data["data-ranges"].append(
                (self.data["line-records-base64-zlib-begin"] + 1, index))
            self.consume = self._extra
            return True
        return False

    def _extra(self, index: int, line: str) -> bool:
        if self._gcov_begin(index, line):
            return True
        if self._gcov_hash(index, line):
            return True
        if self._records_begin(index, line):
            return True
        if self._records_zlib_begin(index, line):
            return True
        return False


def augment_report(report: Dict[str, Any], output: Iterable[str]) -> None:
    """ Augments the report with the results of the parsed output. """
    test_parser = TestOutputParser(report)
    for index, line in enumerate(output):
        if not line:
            continue
        test_parser.consume(index, line)
        test_parser.hash_line(line)
