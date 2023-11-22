# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.testoutputparser module. """

# Copyright (C) 2023 embedded brains GmbH & Co. KG
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

import pytest

from rtemsspec.testoutputparser import augment_report

_OUTPUT = [
    "*** BEGIN OF TEST TestsuitesUnitNoClock0 ***",
    "*** TEST VERSION: 6.0.0.52f06822b8921ad825cb593b792eab7640e26cde",
    "*** TEST STATE: EXPECTED_PASS", "*** TEST BUILD:",
    "*** TEST TOOLS: 10.4.0", "A:TestsuitesUnitNoClock0", "S:Platform:RTEMS",
    "S:Compiler:10.4.0",
    "S:Version:6.0.0.52f06822b8921ad825cb593b792eab7640e26cde",
    "S:BSP:xilinx_zynq_a9_qemu", "S:BuildLabel:foobar",
    "S:TargetHash:SHA256:oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
    "S:RTEMS_DEBUG:0", "S:RTEMS_MULTIPROCESSING:0", "S:RTEMS_POSIX_API:0",
    "S:RTEMS_PROFILING:0", "S:RTEMS_SMP:0", "B:ScoreRbtreeUnitRbtree",
    "E:ScoreRbtreeUnitRbtree:N:495132:F:0:D:0.868197",
    "B:RtemsConfigUnitConfig", "E:RtemsConfigUnitConfig:N:1:F:0:D:0.000291",
    "B:RtemsTaskValPerf", "M:B:RtemsTaskReqPerfConstruct", "M:V:FullCache",
    "M:N:6", "M:S:6:0.000006460", "M:MI:0.000006460", "M:P1:0.000006460",
    "M:Q1:0.000006460", "M:Q2:0.000006460", "M:Q3:0.000006460",
    "M:P99:0.000006460", "M:MX:0.000006460", "M:MAD:0.000000000",
    "M:D:0.000908880", "M:E:RtemsTaskReqPerfConstruct:D:0.013368190",
    "R:Remark", "E:RtemsTaskValPerf:N:1007:F:0:D:0.293161",
    "Z:TestsuitesUnitNoClock0:C:3:N:495175:F:0:D:0.897917",
    "Y:ReportHash:SHA256:ZNUhinVyKcmR1PY5VSQVJIxxvXK5LMnG9Zf9JU5nOoE=", "",
    "*** END OF TEST TestsuitesUnitNoClock0 ***", "",
    "*** BEGIN OF GCOV INFO BASE64 ***",
    "bmZjZ1I0MEKUAAAAL29wdC9ydGVtcy9ydGVtcy02LXNhZmVzdC0xL2J1aWxkL2JzcC1xdWFsLW9u",
    "AAAAOi+8CuS72SFYlu6BAAChAcD///8AAAAA", "*** END OF GCOV INFO BASE64 ***"
    "", "*** BEGIN OF RECORDS BASE64 ***",
    "bmZjZ1I0MEKUAAAAL29wdC9ydGVtcy9ydGVtcy02LXNhZmVzdC0xL2J1aWxkL2JzcC1xdWFsLW9u",
    "AAAAOi+8CuS72SFYlu6BAAChAcD///8AAAAA", "*** END OF RECORDS BASE64 ***"
    "", "*** BEGIN OF RECORDS BASE64 ZLIB ***",
    "bmZjZ1I0MEKUAAAAL29wdC9ydGVtcy9ydGVtcy02LXNhZmVzdC0xL2J1aWxkL2JzcC1xdWFsLW9u",
    "AAAAOi+8CuS72SFYlu6BAAChAcD///8AAAAA",
    "*** END OF RECORDS BASE64 ZLIB ***"
]

_INCOMPLETE_TEST_SUITE = {
    "duration": "?",
    "failed-steps-count": "?",
    "line-duration": "?",
    "line-end": "?",
    "line-failed-steps-count": "?",
    "line-report-hash": "?",
    "line-step-count": "?",
    "report-hash": "?",
    "report-hash-calculated": "?",
    "step-count": "?"
}


def _check(old: str, new: str, line: int, error: int) -> dict:
    report = {}
    assert _OUTPUT[line] == old
    _OUTPUT[line] = new
    augment_report(report, _OUTPUT)
    assert error < 0 or report["line-parser-error"] == error
    _OUTPUT[line] = old
    return report


def _info(t_begin: int = 0, t_end: int = 40) -> None:
    info = {
        "build": [],
        "line-begin-of-test": t_begin,
        "line-build": t_begin + 3,
        "line-state": t_begin + 2,
        "line-tools": t_begin + 4,
        "line-version": t_begin + 1,
        "name": "TestsuitesUnitNoClock0",
        "state": "EXPECTED_PASS",
        "tools": "10.4.0",
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    if t_end >= 0:
        info["line-end-of-test"] = t_end
    return info


def _test_case_0(tc_begin_0: int = 17) -> None:
    return {
        "duration": 0.868197,
        "failed-steps-count": 0,
        "line-begin": tc_begin_0,
        "line-duration": tc_begin_0 + 1,
        "line-end": tc_begin_0 + 1,
        "line-failed-steps-count": tc_begin_0 + 1,
        "line-step-count": tc_begin_0 + 1,
        "name": "ScoreRbtreeUnitRbtree",
        "remarks": [],
        "runtime-measurements": [],
        "step-count": 495132
    }


def _test_case_1(tc_begin_1: int = 19) -> None:
    return {
        "duration": 0.000291,
        "failed-steps-count": 0,
        "line-begin": tc_begin_1,
        "line-duration": tc_begin_1 + 1,
        "line-end": tc_begin_1 + 1,
        "line-failed-steps-count": tc_begin_1 + 1,
        "line-step-count": tc_begin_1 + 1,
        "name": "RtemsConfigUnitConfig",
        "remarks": [],
        "runtime-measurements": [],
        "step-count": 1
    }


def _test_case_2(tc_begin_2: int = 21) -> None:
    return {
        "duration":
        0.293161,
        "failed-steps-count":
        0,
        "line-begin":
        tc_begin_2,
        "line-duration":
        tc_begin_2 + 16,
        "line-end":
        tc_begin_2 + 16,
        "line-failed-steps-count":
        tc_begin_2 + 16,
        "line-step-count":
        tc_begin_2 + 16,
        "name":
        "RtemsTaskValPerf",
        "remarks": [{
            'line': 36,
            'remark': 'Remark'
        }],
        "runtime-measurements": [{
            "duration-sum":
            0.00090888,
            "duration-total":
            0.01336819,
            "line-begin":
            tc_begin_2 + 1,
            "line-end":
            tc_begin_2 + 14,
            "mad":
            0.0,
            "max":
            6.46e-06,
            "min":
            6.46e-06,
            "name":
            "RtemsTaskReqPerfConstruct",
            "p1":
            6.46e-06,
            "p99":
            6.46e-06,
            "q1":
            6.46e-06,
            "q2":
            6.46e-06,
            "q3":
            6.46e-06,
            "sample-count":
            6,
            "samples":
            [6.46e-06, 6.46e-06, 6.46e-06, 6.46e-06, 6.46e-06, 6.46e-06],
            "variant":
            "FullCache"
        }],
        "step-count":
        1007
    }


def _test_suite(ts_begin: int = 5,
                tc_begin_0: int = 17,
                tc_begin_1: int = 19,
                tc_begin_2: int = 21) -> None:
    test_suite = {
        "bsp":
        "xilinx_zynq_a9_qemu",
        "build-label":
        "foobar",
        "compiler":
        "10.4.0",
        "duration":
        0.897917,
        "failed-steps-count":
        0,
        "line-begin":
        ts_begin,
        "line-bsp":
        ts_begin + 4,
        "line-build-label":
        ts_begin + 5,
        "line-compiler":
        ts_begin + 2,
        "line-duration":
        ts_begin + 33,
        "line-end":
        ts_begin + 33,
        "line-failed-steps-count":
        ts_begin + 33,
        "line-platform":
        ts_begin + 1,
        "line-report-hash":
        ts_begin + 34,
        "line-rtems-debug":
        ts_begin + 7,
        "line-rtems-multiprocessing":
        ts_begin + 8,
        "line-rtems-posix-api":
        ts_begin + 9,
        "line-rtems-profiling":
        ts_begin + 10,
        "line-rtems-smp":
        ts_begin + 11,
        "line-step-count":
        ts_begin + 33,
        "line-target-hash":
        ts_begin + 6,
        "line-version":
        ts_begin + 3,
        "name":
        "TestsuitesUnitNoClock0",
        "platform":
        "RTEMS",
        "report-hash":
        "ZNUhinVyKcmR1PY5VSQVJIxxvXK5LMnG9Zf9JU5nOoE=",
        "report-hash-calculated":
        "m47nvOy9BV70dpdyy-EkN_L7GqWiGgmdM4uDFP2mPnk=",
        "rtems-debug":
        False,
        "rtems-multiprocessing":
        False,
        "rtems-posix-api":
        False,
        "rtems-profiling":
        False,
        "rtems-smp":
        False,
        "step-count":
        495175,
        "target-hash":
        "oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "test-cases": [
            _test_case_0(tc_begin_0),
            _test_case_1(tc_begin_1),
            _test_case_2(tc_begin_2)
        ],
        "version":
        "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    return test_suite


def _data_ranges(range_begin: int = 43) -> list:
    return [(range_begin, range_begin + 2), (range_begin + 4, range_begin + 6),
            (range_begin + 8, range_begin + 10)]


def _report(t_begin: int = 0,
            t_end: int = 41,
            ts_begin: int = 5,
            tc_begin_0: int = 17,
            tc_begin_1: int = 19,
            tc_begin_2: int = 21,
            data_begin: int = 43,
            error: int = -1) -> None:
    report = {
        "data-ranges": _data_ranges(data_begin + 1),
        "info": _info(t_begin, t_end),
        "line-gcov-info-base64-begin": data_begin,
        "line-gcov-info-base64-end": data_begin + 3,
        "line-records-base64-begin": data_begin + 4,
        "line-records-base64-end": data_begin + 7,
        "line-records-base64-zlib-begin": data_begin + 8,
        "line-records-base64-zlib-end": data_begin + 11,
        "test-suite": _test_suite(ts_begin, tc_begin_0, tc_begin_1, tc_begin_2)
    }
    if error >= 0:
        report["line-parser-error"] = error
    return report


def test_testoutputparser():
    report = {}
    augment_report(report, [])
    assert report == {"data-ranges": [], "info": {}}
    report = {}
    augment_report(report, _OUTPUT)
    assert report == _report()

    report = _check("M:N:6", "M:N:7", 24, 35)
    expected = _report(error=35, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:MI:0.000006460", "M:MI:0.000006461", 26, 35)
    expected = _report(error=35, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    _OUTPUT[24] = "M:N:0"
    report = _check("M:S:6:0.000006460", "M:S:0:0.000006460", 25, -1)
    _OUTPUT[24] = "M:N:6"
    expected = _report()
    expected["test-suite"][
        "report-hash-calculated"] = "SgqwqrpqjV5dZ3kPQWBgWmOD-V7bXRFQ7LGVMoaHtXc="
    expected["test-suite"]["test-cases"][2]["runtime-measurements"][0][
        "sample-count"] = 0
    expected["test-suite"]["test-cases"][2]["runtime-measurements"][0][
        "samples"] = []
    assert report == expected

    report = _check("M:V:FullCache", "?", 23, 23)
    expected = _report(error=23, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:N:6", "?", 24, 24)
    expected = _report(error=24, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:S:6:0.000006460", "?", 25, 25)
    expected = _report(error=25, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:MX:0.000006460", "M:MX:0.000006461", 32, 35)
    expected = _report(error=35, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:P1:0.000006460", "?", 27, 27)
    expected = _report(error=27, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:Q1:0.000006460", "?", 28, 28)
    expected = _report(error=28, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:Q2:0.000006460", "?", 29, 29)
    expected = _report(error=29, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:Q3:0.000006460", "?", 30, 30)
    expected = _report(error=30, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:P99:0.000006460", "?", 31, 31)
    expected = _report(error=31, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:MX:0.000006460", "?", 32, 32)
    expected = _report(error=32, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:MAD:0.000000000", "?", 33, 33)
    expected = _report(error=33, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:D:0.000908880", "?", 34, 34)
    expected = _report(error=34, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:E:RtemsTaskReqPerfConstruct:D:0.013368190", "?", 35, 35)
    expected = _report(error=35, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("M:E:RtemsTaskReqPerfConstruct:D:0.013368190",
                    "M:E:FooBar:D:0.013368190", 35, 35)
    expected = _report(error=35, t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    del expected["test-suite"]["test-cases"][2]
    assert report == expected

    report = _check("*** BEGIN OF TEST TestsuitesUnitNoClock0 ***",
                    "BEGIN OF TEST XYZ", 0, -1)
    expected = _report(t_end=-1)
    expected["info"] = {}
    del expected["test-suite"]
    assert report == expected

    report = _check(
        "*** TEST VERSION: 6.0.0.52f06822b8921ad825cb593b792eab7640e26cde",
        "foobar", 1, -1)

    report = _check("*** TEST STATE: EXPECTED_PASS", "?", 2, 2)
    expected = _report(error=2)
    expected["info"] = {
        "line-begin-of-test": 0,
        "line-version": 1,
        "name": "TestsuitesUnitNoClock0",
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    del expected["test-suite"]
    assert report == expected

    report = _check("*** TEST BUILD:", "?", 3, 3)
    expected = _report(error=3)
    expected["info"] = {
        "line-begin-of-test": 0,
        "line-state": 2,
        "line-version": 1,
        "name": "TestsuitesUnitNoClock0",
        "state": "EXPECTED_PASS",
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    del expected["test-suite"]
    assert report == expected

    report = _check("*** TEST BUILD:",
                    "*** TEST BUILD: RTEMS_DEBUG, RTEMS_SMP", 3, -1)
    expected = _report()
    expected["info"]["build"] = ["RTEMS_DEBUG", "RTEMS_SMP"]
    assert report == expected

    report = _check("*** TEST TOOLS: 10.4.0", "?", 4, 4)
    expected = _report(error=4)
    expected["info"] = {
        "build": [],
        "line-begin-of-test": 0,
        "line-build": 3,
        "line-state": 2,
        "line-version": 1,
        "name": "TestsuitesUnitNoClock0",
        "state": "EXPECTED_PASS",
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    del expected["test-suite"]
    assert report == expected

    report = _check("*** END OF TEST TestsuitesUnitNoClock0 ***",
                    "*** END OF TEST FooBar ***", 41, -1)
    expected = _report(t_end=-1, error=41)
    assert report == expected

    report = _check("S:Platform:RTEMS", "?", 6, 6)
    expected = _report(error=6, t_end=-1)
    expected["test-suite"] = {
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-step-count": "?",
        "name": "TestsuitesUnitNoClock0",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "test-cases": []
    }
    assert report == expected

    report = _check("S:Compiler:10.4.0", "?", 7, 7)
    expected = _report(error=7, t_end=-1)
    expected["test-suite"] = {
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-platform": 6,
        "line-step-count": "?",
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "test-cases": []
    }
    assert report == expected

    report = _check("S:Version:6.0.0.52f06822b8921ad825cb593b792eab7640e26cde",
                    "?", 8, 8)
    expected = _report(error=8, t_end=-1)
    expected["test-suite"] = {
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-platform": 6,
        "line-step-count": "?",
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "test-cases": []
    }
    assert report == expected

    report = _check("S:BSP:xilinx_zynq_a9_qemu", "?", 9, 9)
    expected = _report(error=9, t_end=-1)
    expected["test-suite"] = {
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-platform": 6,
        "line-step-count": "?",
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("S:BuildLabel:foobar", "?", 10, 10)
    expected = _report(error=10, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-platform": 6,
        "line-step-count": "?",
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check(
        "S:TargetHash:SHA256:oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "?", 11, 11)
    expected = _report(error=11, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "build-label": "foobar",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-build-label": 10,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-platform": 6,
        "line-step-count": "?",
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("S:RTEMS_DEBUG:0", "?", 12, 12)
    expected = _report(error=12, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "build-label": "foobar",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-build-label": 10,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-platform": 6,
        "line-step-count": "?",
        "line-target-hash": 11,
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "step-count": "?",
        "target-hash": "oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("S:RTEMS_MULTIPROCESSING:0", "?", 13, 13)
    expected = _report(error=13, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "build-label": "foobar",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-build-label": 10,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-rtems-debug": 12,
        "line-platform": 6,
        "line-step-count": "?",
        "line-target-hash": 11,
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "rtems-debug": False,
        "step-count": "?",
        "target-hash": "oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("S:RTEMS_POSIX_API:0", "?", 14, 14)
    expected = _report(error=14, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "build-label": "foobar",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-build-label": 10,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-rtems-debug": 12,
        "line-rtems-multiprocessing": 13,
        "line-platform": 6,
        "line-step-count": "?",
        "line-target-hash": 11,
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "rtems-debug": False,
        "rtems-multiprocessing": False,
        "step-count": "?",
        "target-hash": "oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("S:RTEMS_PROFILING:0", "?", 15, 15)
    expected = _report(error=15, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "build-label": "foobar",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-build-label": 10,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-rtems-debug": 12,
        "line-rtems-multiprocessing": 13,
        "line-rtems-posix-api": 14,
        "line-platform": 6,
        "line-step-count": "?",
        "line-target-hash": 11,
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "rtems-debug": False,
        "rtems-multiprocessing": False,
        "rtems-posix-api": False,
        "step-count": "?",
        "target-hash": "oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("S:RTEMS_SMP:0", "?", 16, 16)
    expected = _report(error=16, t_end=-1)
    expected["test-suite"] = {
        "bsp": "xilinx_zynq_a9_qemu",
        "build-label": "foobar",
        "compiler": "10.4.0",
        "duration": "?",
        "failed-steps-count": "?",
        "line-begin": 5,
        "line-bsp": 9,
        "line-build-label": 10,
        "line-compiler": 7,
        "line-duration": "?",
        "line-end": "?",
        "line-failed-steps-count": "?",
        "line-report-hash": "?",
        "line-rtems-debug": 12,
        "line-rtems-multiprocessing": 13,
        "line-rtems-posix-api": 14,
        "line-rtems-profiling": 15,
        "line-platform": 6,
        "line-step-count": "?",
        "line-target-hash": 11,
        "line-version": 8,
        "name": "TestsuitesUnitNoClock0",
        "platform": "RTEMS",
        "report-hash": "?",
        "report-hash-calculated": "?",
        "rtems-debug": False,
        "rtems-multiprocessing": False,
        "rtems-posix-api": False,
        "rtems-profiling": False,
        "step-count": "?",
        "target-hash": "oqNHrlFi_jsico5ygHk-OcfeM9oaY3JMw_z6dmF09-U=",
        "test-cases": [],
        "version": "6.0.0.52f06822b8921ad825cb593b792eab7640e26cde"
    }
    assert report == expected

    report = _check("E:ScoreRbtreeUnitRbtree:N:495132:F:0:D:0.868197", "?", 18,
                    20)
    expected = _report(t_end=-1, error=20)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    expected["test-suite"]["test-cases"] = []
    assert report == expected

    report = _check("Z:TestsuitesUnitNoClock0:C:3:N:495175:F:0:D:0.897917",
                    "Z:FooBar:C:3:N:495175:F:0:D:0.897917", 38, 38)
    expected = _report(t_end=-1, error=38)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    assert report == expected

    report = _check("Z:TestsuitesUnitNoClock0:C:3:N:495175:F:0:D:0.897917",
                    "?", 38, -1)
    expected = _report(t_end=-1)
    expected["test-suite"].update(_INCOMPLETE_TEST_SUITE)
    assert report == expected

    report = _check(
        "Y:ReportHash:SHA256:ZNUhinVyKcmR1PY5VSQVJIxxvXK5LMnG9Zf9JU5nOoE=",
        "?", 39, -1)
    expected = _report(t_end=-1)
    expected["test-suite"]["line-report-hash"] = "?"
    expected["test-suite"]["report-hash"] = "?"
    expected["test-suite"]["report-hash-calculated"] = "?"
    assert report == expected
