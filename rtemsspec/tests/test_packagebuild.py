# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.packagebuild module. """

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

import json
import logging
import os
import pytest
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import List, NamedTuple

from rtemsspec.items import EmptyItem, Item, ItemCache, ItemGetValueContext
import rtemsspec.gcdaproducer
import rtemsspec.membenchcollector
from rtemsspec.packagebuild import BuildItem, BuildItemMapper, \
    build_item_input, PackageBuildDirector
from rtemsspec.packagebuildfactory import create_build_item_factory
from rtemsspec.rtems import RTEMSItemCache
import rtemsspec.packagemanual
from rtemsspec.specverify import verify
from rtemsspec.sphinxcontent import make_label
import rtemsspec.sphinxbuilder
import rtemsspec.testrunner
from rtemsspec.testrunner import Executable, Report, TestRunner
from rtemsspec.tests.util import get_and_clear_log
from rtemsspec.util import run_command

TestRunner.__test__ = False


def _copy_dir(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for item in os.listdir(src):
        s = src / item
        d = dst / item
        if s.is_dir():
            _copy_dir(s, d)
        else:
            shutil.copy2(str(s), str(d))


def _create_item_cache(tmp_dir: Path, spec_dir: Path) -> ItemCache:
    spec_dst = tmp_dir / "pkg" / "build" / "spec"
    test_dir = Path(__file__).parent
    _copy_dir(test_dir / spec_dir, spec_dst)
    _copy_dir(test_dir / "test-files", tmp_dir)
    _copy_dir(test_dir.parent.parent / "spec-spec", spec_dst)
    _copy_dir(test_dir.parent.parent / "spec" / "spec", spec_dst / "spec")
    _copy_dir(test_dir.parent.parent / "spec-qdp" / "spec", spec_dst / "spec")
    cache_dir = os.path.join(tmp_dir, "cache")
    config = {
        "cache-directory": os.path.normpath(cache_dir),
        "paths": [str(spec_dst.absolute())],
        "spec-type-root-uid": "/spec/root"
    }
    return ItemCache(config)


def test_builditemmapper():
    mapper = BuildItemMapper(EmptyItem())
    with pytest.raises(NotImplementedError):
        mapper.get_link(mapper.item)


class _TestItem(BuildItem):

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item, BuildItemMapper(item, recursive=True))


class _TestRunner(TestRunner):

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.run_count = 0

    def run_tests(self, executables: List[Executable]) -> List[Report]:
        logging.info("executables: %s", executables)
        super().run_tests(executables)
        self.run_count += 1
        if self.run_count == 1:
            return []
        if self.run_count == 2:
            return [{
                "executable":
                executables[0].path,
                "output": [
                    "*** BEGIN OF GCOV INFO BASE64 ***", "foobar",
                    "*** END OF GCOV INFO BASE64 ***"
                ]
            }]
        if self.run_count == 3:
            return [{
                "executable":
                executables[0].path,
                "output": [
                    "*** BEGIN OF TEST TS ***", "*** TEST VERSION: V",
                    "*** TEST STATE: EXPECTED_PASS", "*** TEST BUILD:",
                    "*** TEST TOOLS: C", "A:TS", "S:Platform:RTEMS",
                    "S:Compiler:C", "S:Version:V", "S:BSP:bsp",
                    "S:BuildLabel:DEFAULT",
                    "S:TargetHash:SHA256:qYOFDHUGg5--JyB28V7llk_t6WYeA3VAogeqwGLZeCM=",
                    "S:RTEMS_DEBUG:0", "S:RTEMS_MULTIPROCESSING:0",
                    "S:RTEMS_POSIX_API:0", "S:RTEMS_PROFILING:0",
                    "S:RTEMS_SMP:0", "Z:TS:C:0:N:0:F:0:D:0.014590",
                    "Y:ReportHash:SHA256:JlS-9kM8jYqTjFvRbuUDzHpfph6PznxFxCLx30NkcoI="
                ]
            }]
        return [{
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "output": []
        } for executable in executables]


class _Subprocess(NamedTuple):
    stdout: bytes


def _test_runner_subprocess(command, check, stdin, stdout, timeout):
    if command[2] == "a.exe":
        raise Exception
    if command[2] == "b.exe":
        raise subprocess.TimeoutExpired(command[2], timeout, b"")
    if command[2] == "c.exe":
        raise subprocess.TimeoutExpired(command[2], timeout, None)
    return _Subprocess(b"u\r\nv\nw\n")


def _gcov_tool(command, check, cwd, input):
    assert command == ["foo", "merge-stream"]
    assert check
    assert input == b"gcfnB04R\x00\x00\x00\x95/opt"
    (Path(cwd) / "file.gcda").touch()


def _gather_object_sizes(item_cache, path, gdb):
    return {}


def _gather_sections(item_cache, path, objdump, gdb):
    return {}


def _sphinx_builder_run_command(args, cwd=None, stdout=None):
    if args == ["python3", "-msphinx", "-M", "clean", "source", "build"]:
        return 0
    if args == ["python3", "-msphinx", "-M", "latexpdf", "source", "build"]:
        os.makedirs(os.path.join(cwd, "build/latex"))
        open(os.path.join(cwd, "build/latex/document.pdf"), "w+").close()
        return 0
    if args == ["python3", "-msphinx", "-M", "html", "source", "build"]:
        os.makedirs(os.path.join(cwd, "build/html"))
        open(os.path.join(cwd, "build/html/index.html"), "w+").close()
        return 0
    if args == ["make", "super", "clean"]:
        return 0
    if args == ["make"]:
        stdout.append("example")
        return 0
    if "pkg-config" in args:
        stdout.append(" ".join(args))
        return 0
    if args[0].endswith("verify_package.py"):
        stdout.append("verify_package.py")
        return 0
    return 1


def _package_manual_generate(content, sections_by_uid, root, table_pivots,
                             mapper):
    content.add([root.uid, mapper.item.uid] + table_pivots +
                list(sections_by_uid.keys()))


def _clear_benchmark_variants(ctx: ItemGetValueContext) -> str:
    ctx.item["benchmark-variants"] = [{
        "description": "Description",
        "build-label": "foobar",
        "name": "Name",
        "test-log-uid": "../build/disabled"
    }]
    return "clear benchmark variants"


def _clear_copyrights_by_license(ctx: ItemGetValueContext) -> str:
    ctx.item.cache["/qdp/source/a"]["copyrights-by-license"] = {}
    return "clear copyrights by license"


def _format_path(path: Path) -> str:
    path_2 = str(path)
    for char in "/-_.":
        path_2 = path_2.replace(char, f"{char}\u200b")
    return path_2


def test_packagebuild(caplog, tmpdir, monkeypatch):
    tmp_dir = Path(tmpdir)
    tmp_dir_len = len(str(tmp_dir))
    item_cache = _create_item_cache(tmp_dir, Path("spec-packagebuild"))

    caplog.set_level(logging.WARN)
    verify_config = {"root-type": "/spec/root"}
    status = verify(verify_config, item_cache)
    assert status.critical == 0
    assert status.error == 0

    caplog.set_level(logging.DEBUG)
    factory = create_build_item_factory()
    factory.add_constructor("qdp/build-step/test-mapper", _TestItem)

    def get_tmpdir(_ctx: ItemGetValueContext) -> str:
        return str(tmp_dir.absolute())

    factory.add_get_value("qdp/variant:/tmpdir", get_tmpdir)
    director = PackageBuildDirector(item_cache, factory)
    director.clear()
    variant = director["/qdp/variant"]
    prefix_dir = Path(variant["prefix-directory"])
    status = run_command(["git", "init"], str(prefix_dir))
    assert status == 0

    director.build_package(None, None)
    log = get_and_clear_log(caplog)
    assert "INFO /qdp/steps/a: create build item" in log
    assert "INFO /qdp/steps/b: create build item" not in log
    assert "INFO /qdp/steps/b: is disabled" in log
    assert "INFO /qdp/steps/c: output is disabled: /qdp/output/b" in log

    rtems_item_cache = director["/qdp/steps/rtems-item-cache"]
    assert isinstance(rtems_item_cache, RTEMSItemCache)
    related_items = rtems_item_cache.get_related_items_by_type("test-case")
    assert [item.uid for item in related_items] == ["/rtems/test-case"]
    related_items = rtems_item_cache.get_related_items_by_type(["test-case"])
    assert [item.uid for item in related_items] == ["/rtems/test-case"]
    related_types = rtems_item_cache.get_related_types_by_prefix("requirement")
    assert related_types == [
        "requirement/functional/function", "requirement/non-functional/design",
        "requirement/non-functional/design-target",
        "requirement/non-functional/interface-requirement",
        "requirement/non-functional/performance-runtime",
        "requirement/non-functional/quality"
    ]
    related_items = rtems_item_cache.get_related_interfaces()
    assert [item.uid for item in related_items] == [
        "/rtems/domain", "/rtems/group", "/rtems/group-acfg", "/rtems/header",
        "/rtems/if"
    ]
    related_items = rtems_item_cache.get_related_requirements()
    assert [item.uid for item in related_items] == [
        "/req/api", "/req/root", "/rtems/req", "/rtems/req/mem-basic",
        "/rtems/req/perf", "/rtems/target-a"
    ]
    related_items = rtems_item_cache.get_related_interfaces_and_requirements()
    assert [item.uid for item in related_items] == [
        "/req/api", "/req/root", "/rtems/domain", "/rtems/group",
        "/rtems/group-acfg", "/rtems/header", "/rtems/if", "/rtems/req",
        "/rtems/req/mem-basic", "/rtems/req/perf", "/rtems/target-a"
    ]

    director.build_package(None, ["/qdp/steps/a"])
    log = get_and_clear_log(caplog)
    assert "INFO /qdp/steps/a: build is forced" in log
    assert "INFO /qdp/steps/c: input has changed: /qdp/steps/a" in log

    director.build_package([], None)
    log = get_and_clear_log(caplog)
    assert "INFO /qdp/steps/a: build is skipped" in log

    director.build_package(None, None)
    log = get_and_clear_log(caplog)
    assert "INFO /qdp/steps/a: build is unnecessary" in log
    assert "INFO /qdp/steps/c: build is unnecessary" in log
    assert "INFO /qdp/steps/c: input is disabled: /qdp/steps/b" in log

    c = director["/qdp/steps/c"]
    assert isinstance(c, _TestItem)
    c["foo"] = "bar"
    c["blub"] = "${.:/foo}"
    assert c["foo"] == "bar"
    assert "foo" in c
    assert "nil" not in c
    assert c["blub"] == "bar"
    assert c.substitute(c.item["blub"], c.item) == "bar"
    assert c.substitute("${/qdp/variant:/spec}") == "spec:/qdp/variant"
    assert c.substitute(
        "${/qdp/issue/rtems/2189:/name}"
    ) == "`RTEMS Ticket #2189 <https://devel.rtems.org/ticket/2189>`__"
    assert c.variant.uid == "/qdp/variant"
    variant_config = c.variant["config"]
    c.variant["config"] = ""
    assert c.variant["name"] == "sparc-gr712rc-4"
    assert c.variant["ident"] == "sparc/gr712rc/4"
    c.variant["config"] = variant_config
    assert c.variant["name"] == "sparc-gr712rc-smp-4"
    assert c.variant["ident"] == "sparc/gr712rc/smp/4"
    assert c.enabled_set == []
    assert c.enabled
    assert build_item_input(c.item, "foo").uid == "/qdp/steps/a"
    assert build_item_input(c.item, "bar").uid == "/qdp/steps/a"
    with pytest.raises(KeyError):
        build_item_input(c.item, "blub")
    assert c.input("foo").uid == "/qdp/steps/a"
    assert list(c.input_links("foo"))[0].item.uid == "/qdp/steps/a"
    with pytest.raises(KeyError):
        c.input("nix")
    assert [item.uid for item in c.inputs()
            ] == ["/qdp/variant", "/qdp/steps/a", "/qdp/steps/a"]
    assert [item.uid for item in c.inputs("foo")] == ["/qdp/steps/a"]
    assert c.output("blub").uid == "/qdp/output/a"
    with pytest.raises(KeyError):
        c.output("nix")
    with pytest.raises(ValueError):
        c.output("moo")
    assert c["values"]["list"] == ["a", "b1", "b2", ["d", "e"], "c"]
    c.clear()

    # Test Archiver
    dir_state_a = director["/qdp/source/a"]
    dir_state_a.load()
    with open(tmp_dir / "dir/subdir/d.txt", "w", encoding="utf-8") as dst:
        dst.write("d")
    dir_state_b = director["/qdp/source/b"]
    dir_state_b.load()
    dir_state_e = director["/qdp/source/e"]
    dir_state_e.load()
    variant["enabled"] = ["archive"]
    director.build_package(None, None)
    log = get_and_clear_log(caplog)
    assert "/qdp/steps/archive: duplicate files in directory states /qdp/source/a and /qdp/source/b" in log
    assert f"/qdp/steps/archive: duplicate file: {tmp_dir}/dir/subdir/d.txt" in log
    assert f"/qdp/steps/archive: inconsistent file hashes for '{tmp_dir}/dir/subdir/d.txt': {list(dir_state_a.files_and_hashes())[2][1]} != {list(dir_state_b.files_and_hashes())[2][1]}" in log
    assert f"/qdp/steps/archive: duplicate file: {tmp_dir}/dir/subdir/c.txt" in log
    with tarfile.open(director["/qdp/deployment/archive"].file,
                      "r:*") as archive:
        assert archive.getnames() == [
            'dir/a.txt', 'dir/subdir/c.txt', 'dir/subdir/d.txt', 'dir/b.txt',
            'dir/subdir/c.txt', 'dir/subdir/d.txt', 'dir/e.txt',
            'verify_package.py'
        ]

    verify_package = director["/qdp/deployment/verify-package"]
    stdout = []
    status = run_command([verify_package.file, "--list-files-and-hashes"],
                         str(tmp_dir), stdout)
    assert status == 0
    assert stdout == [
        "dir/a.txt\t7a296fab5364b34ce3e0476d55bf291bd41aa085e5ecf2a96883e593aa1836fed22f7242af48d54af18f55c8d1def13ec9314c926666a0ba63f7663500090565",
        "dir/b.txt\t480a2ddd53e8db95fc737b670302c7ea0914b52ffdb2e961c2ff90887ec2b25873723374da81ae5adafc47ef7ef1c7c5c91243217d41cb904040279b758da0f7",
        "dir/e.txt\t61e9f9edbc37b2b5c2fc9633da2d8777916f0e4515a080374acedd14c935f2c6fb5a882c5459b7a06a03f0d057ce4f73f89def713a5824b8769a5917a3bdda93",
        "dir/subdir/c.txt\t663049a20dfea6b8da28b2eb90eddd10ccf28ef2519563310b9bde25b7268444014c48c4384ee5c5a54e7830e45fcd87df7910a7fda77b68c2efdd75f8de25e8",
        "dir/subdir/d.txt\t48fb10b15f3d44a09dc82d02b06581e0c0c69478c9fd2cf8f9093659019a1687baecdbb38c9e72b12169dc4148690f87467f9154f5931c5df665c6496cbfd5f5"
    ]

    # Test RunActions
    variant["enabled"] = ["run-actions"]
    director.build_package(None, None)
    log = get_and_clear_log(caplog)
    assert f"/qdp/steps/run-actions: make directory: {tmp_dir}/pkg/build/some/more/dirs" in log
    assert f"/qdp/steps/run-actions: remove empty directory: {tmp_dir}/pkg/build/some/more/dirs" in log
    assert f"/qdp/steps/run-actions: remove empty directory: {tmp_dir}/pkg/build/some/more" in log
    assert f"/qdp/steps/run-actions: remove empty directory: {tmp_dir}/pkg/build/some" in log
    assert f"/qdp/steps/run-actions: remove directory tree: {tmp_dir}/pkg/build/some" in log
    assert f"/qdp/steps/run-actions: run in '{tmp_dir}/pkg/build': 'git' 'foobar'" in log
    assert f"/qdp/steps/run-actions: run in '{tmp_dir}/pkg/build': 'git' 'status'" in log

    # Test RepositorySubset
    variant["enabled"] = ["repository-subset"]
    director["/qdp/source/repo"].load()
    assert not os.path.exists(os.path.join(tmpdir, "pkg", "sub-repo", "bsp.c"))
    director.build_package(None, None)
    assert os.path.exists(os.path.join(tmpdir, "pkg", "sub-repo", "bsp.c"))

    # Test DummyTestRunner
    dummy_runner = director["/qdp/test-runner/dummy"]
    with pytest.raises(IOError):
        dummy_runner.run_tests([])

    # Test GRMONManualTestRunner
    grmon_manual_runner = director["/qdp/test-runner/grmon-manual"]
    exe = tmp_dir / "a.exe"
    exe.touch()
    with pytest.raises(IOError):
        grmon_manual_runner.run_tests([
            Executable(
                str(exe), "QvahP3YJU9bvpd7DYxJDkRBLJWbEFMEoH5Ncwu6UtxA"
                "_l9EQ1zLW9yQTprx96BTyYE2ew7vV3KECjlRg95Ya6A==", 456)
        ])
    with tarfile.open(tmp_dir / "tests.tar.xz", "r:*") as archive:
        assert archive.getnames() == [
            "tests/run.grmon", "tests/run.sh", "tests/a.exe"
        ]
        with archive.extractfile("tests/run.grmon") as src:
            assert src.read() == b"a.exe\n"
        with archive.extractfile("tests/run.sh") as src:
            assert src.read() == b"abc\n"

    # Test SubprocessTestRunner
    subprocess_runner = director["/qdp/test-runner/subprocess"]
    monkeypatch.setattr(rtemsspec.testrunner, "subprocess_run",
                        _test_runner_subprocess)
    reports = subprocess_runner.run_tests([
        Executable(
            "a.exe", "QvahP3YJU9bvpd7DYxJDkRBLJWbEFMEoH5Ncwu6UtxA"
            "_l9EQ1zLW9yQTprx96BTyYE2ew7vV3KECjlRg95Ya6A==", 1),
        Executable(
            "b.exe", "4VgX6KGWuDyG5vmlO4J-rdbHpOJoIIYLn_3oSk2BKAc"
            "Au5RXTg1IxhHjiPO6Yzl8u4GsWBh0qc3flRwEFcD8_A==", 2),
        Executable(
            "c.exe", "YtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_"
            "W_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==", 3),
        Executable(
            "d.exe", "ZtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_"
            "W_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==", 4)
    ])
    monkeypatch.undo()
    reports[0]["start-time"] = "c"
    reports[0]["duration"] = 2.
    reports[1]["start-time"] = "d"
    reports[1]["duration"] = 3.
    reports[2]["start-time"] = "e"
    reports[2]["duration"] = 4.
    reports[3]["start-time"] = "f"
    reports[3]["duration"] = 5.
    assert reports == [{
        "command-line": ["foo", "bar", "a.exe"],
        "duration":
        2.0,
        "executable":
        "a.exe",
        "executable-sha512":
        "QvahP3YJU9bvpd7DYxJDkRBLJWbEFMEoH5Ncwu6UtxA_"
        "l9EQ1zLW9yQTprx96BTyYE2ew7vV3KECjlRg95Ya6A==",
        "output": [""],
        "start-time":
        "c"
    }, {
        "command-line": ["foo", "bar", "b.exe"],
        "duration":
        3.,
        "executable":
        "b.exe",
        "executable-sha512":
        "4VgX6KGWuDyG5vmlO4J-rdbHpOJoIIYLn_3oSk2BKAcA"
        "u5RXTg1IxhHjiPO6Yzl8u4GsWBh0qc3flRwEFcD8_A==",
        "output": [""],
        "start-time":
        "d"
    }, {
        "command-line": ["foo", "bar", "c.exe"],
        "duration":
        4.,
        "executable":
        "c.exe",
        "executable-sha512":
        "YtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_W"
        "_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==",
        "output": [""],
        "start-time":
        "e"
    }, {
        "command-line": ["foo", "bar", "d.exe"],
        "duration":
        5.,
        "executable":
        "d.exe",
        "executable-sha512":
        "ZtTC0r1DraKOn9vNGppBAVFVTnI9IqS6jFDRBKVucU_W"
        "_dpQF0xtC_mRjGV7t5RSQKhY7l3iDGbeBZJ-lV37bg==",
        "output": ["u", "v", "w"],
        "start-time":
        "f"
    }]

    # Test RunTests
    variant["enabled"] = ["run-tests"]
    factory.add_constructor("qdp/test-runner/test", _TestRunner)
    build_bsp = director["/qdp/build/bsp"]
    build_bsp.load()
    director.build_package(None, None)
    log = get_and_clear_log(caplog)
    assert "no report for" in log
    assert "gcov info is corrupt for" in log
    assert "test suite report is corrupt for" in log
    assert (f"executables: [Executable(path='{build_bsp.directory}"
            "/a.exe', digest='z4PhNX7vuL3xVChQ1m2AB9Yg5AULVxXcg_SpIdNs6c5H0NE8"
            "XYXysP-DGNKHfuwvY7kxvUdBeoGlODJ6-SfaPg==', timeout=1800), "
            f"Executable(path='{build_bsp.directory}/b.exe', "
            "digest='hopqxuHQKT10-tB_bZWVKz4B09MVPbZ3p12Ad5g_1OMNtr_Im3YIqT-yZ"
            "GkjOp8aCVctaHqcXaeLID6xUQQKFQ==', timeout=1800)]") in log
    director.build_package(None, ["/qdp/steps/run-tests"])
    log = get_and_clear_log(caplog)
    assert f"use previous report for: {build_bsp.directory}/a.exe"

    # Test GCDAProducer
    variant["enabled"] = ["gcda-producer"]
    test_log_coverage = director["/qdp/test-logs/coverage"]
    test_log_coverage.load()
    monkeypatch.setattr(rtemsspec.gcdaproducer, "subprocess_run", _gcov_tool)
    director.build_package(None, None)
    monkeypatch.undo()
    log = get_and_clear_log(caplog)
    assert f"/qdp/steps/gcda-producer: copy *.gcno files from '{tmp_dir}/pkg/build/bsp' to '{tmp_dir}/pkg/build/gcda'" in log
    assert f"/qdp/steps/gcda-producer: remove unexpected *.gcda file in build directory: '{tmp_dir}/pkg/build/bsp/f.gcda'" in log
    assert f"/qdp/steps/gcda-producer: process: ts-unit-no-clock-0.exe" in log
    assert f"/qdp/steps/gcda-producer: move *.gcda files from '{tmp_dir}/pkg/build/bsp' to '{tmp_dir}/pkg/build/gcda'" in log

    # Test MembenchCollector
    variant["enabled"] = ["membench-collector"]
    monkeypatch.setattr(rtemsspec.membenchcollector, "gather_object_sizes",
                        _gather_object_sizes)
    monkeypatch.setattr(rtemsspec.membenchcollector, "gather_sections",
                        _gather_sections)
    director.build_package(None, None)
    monkeypatch.undo()
    log = get_and_clear_log(caplog)
    assert f"/qdp/steps/membench: get memory benchmarks for build-label from: arch/bsp" in log

    # Test SphinxBuilder
    variant["enabled"] = ["sphinx-builder"]
    doc = director["/qdp/steps/doc"]
    doc.substitute("${.:/document-author}") == "embedded brains GmbH & Co. KG"
    doc.substitute("${.:/document-year}") == "2020"
    doc.substitute(
        "${.:/document-copyright}") == "2020 embedded brains GmbH & Co. KG"
    doc.item["document-copyrights"].append("Copyright (C) 2023 John Doe")
    doc.substitute("${.:/document-author}"
                   ) == "embedded brains GmbH & Co. KG and contributors"
    doc.substitute("${.:/document-copyright}"
                   ) == "2020 embedded brains GmbH & Co. KG and contributors"
    doc.item["document-copyrights"].pop()
    doc_src = director["/qdp/source/doc"]
    doc_src.load()
    doc_build = Path(director["/qdp/build/doc"].directory)
    assert not (doc_build / "source" / "copy.rst").exists()
    assert not (doc_build / "other" / "copy.rst").exists()
    monkeypatch.setattr(rtemsspec.sphinxbuilder, "run_command",
                        _sphinx_builder_run_command)
    director.build_package(None, None)
    monkeypatch.undo()
    assert (doc_build / "source" / "copy.rst").is_file()
    assert (doc_build / "other" / "copy.rst").is_file()
    doc_result = doc_build / "source" / "copy-and-substitute.rst"
    with open(doc_result, "r", encoding="utf-8") as src:
        assert src.read() == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

. Contract
Contract
The Title
The \\break \\break Title
2
2020 embedded brains GmbH \\& Co. KG
The Title
:term:`Term`
:term:`Terms <Term>`
:c:func:`identity`
spec:/qdp/steps/doc
.. _SectionHeader:

Section Header
--------------

Section content:

.. _SubsectionHeader:

Subsection Header
^^^^^^^^^^^^^^^^^

Subsection content.
"""
    doc_index = doc_build / "source" / "index.rst"
    with open(doc_index, "r", encoding="utf-8") as src:
        assert src.read() == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

2020 embedded brains GmbH & Co. KG

embedded brains GmbH & Co. KG

| © 2023 Alice
| © 2020, 2023 embedded brains GmbH & Co. KG

| © 2023 Bob
| © 2023 embedded brains GmbH & Co. KG

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

The Title
*********

.. topic:: Release: 2, Date: 2020-10-26, Status: Draft

    * 2020 embedded brains GmbH & Co. KG

    * e

.. topic:: Release: 1, Date: 1970-01-01, Status: Replaced

    Initial release.

.. table::
    :class: longtable
    :widths: 16 26 30 28

    +--------------+---------------------+-------------------+-----------+
    | Action       | Name                | Organization      | Signature |
    +==============+=====================+===================+===========+
    | Written by   | John Doe            | Some Organization |           |
    +              +---------------------+-------------------+-----------+
    |              | Foo                 | Bár Organization  |           |
    +--------------+---------------------+-------------------+-----------+
    | Super Action | This is a Long Name | Short             |           |
    +--------------+---------------------+-------------------+-----------+

.. toctree::
    :maxdepth: 4
    :numbered:

    copy-and-substitute
    glossary
"""
    doc_glossary = doc_build / "source" / "glossary.rst"
    with open(doc_glossary, "r", encoding="utf-8") as src:
        assert src.read() == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 Alice
.. Copyright (C) 2020 embedded brains GmbH & Co. KG

Terms, definitions and abbreviated terms
****************************************

.. glossary::
    :sorted:

    Term
        This is the term.
"""
    doc_deployment = director["/qdp/deployment/doc"]
    assert doc_deployment["copyrights-by-license"] == {
        "BSD-2-Clause": [
            "Copyright (C) 2023 Bob",
            "Copyright (C) 2023 embedded brains GmbH & Co. KG"
        ]
    }

    variant["enabled"] = ["sphinx-builder-2"]
    doc_2 = director["/qdp/steps/doc-2"]
    doc_2.substitute("${.:/document-bsd-2-clause-copyrights}") == "\n"

    with pytest.raises(NotImplementedError):
        doc_2.mapper.get_link(doc_2.mapper.item)

    with doc_2.section_level(
            ItemGetValueContext(doc_2.item, "", "", "", -1,
                                "")) as (section_level, args):
        assert section_level == 3
        assert args == None
    with doc_2.section_level(
            ItemGetValueContext(doc_2.item, "", "", "", -1,
                                "-1")) as (section_level, args):
        assert section_level == 1
        assert args == None
    with doc_2.section_level(
            ItemGetValueContext(doc_2.item, "", "", "", -1,
                                "2:mo:re")) as (section_level, args):
        assert section_level == 4
        assert args == "mo:re"

    doc_2.item["document-components"].append({
        "action": "foobar",
        "add-to-index": False,
        "value": 123
    })
    action_run = 0

    def action(component):
        nonlocal action_run
        action_run += 1
        assert component["value"] == 123

    doc_2.add_component_action("foobar", action)
    director.build_package(None, None)
    assert action_run == 1

    # Test SRelDBuilder
    variant["enabled"] = ["ddf-sreld"]
    director["/qdp/source/doc-ddf-sreld"].load()
    director.build_package(None, None)
    ddf_sreld_build = Path(director["/qdp/build/doc-ddf-sreld"].directory)
    ddf_sreld_index = ddf_sreld_build / "source" / "index.rst"
    with open(ddf_sreld_index, "r", encoding="utf-8") as src:
        assert src.read() == f""".. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

Description 2.

.. _NewIssues:

New issues
----------

When the QDP of this package version was produced, there were the following new issues associated:

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+---------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                 |
    +==============+===============================================+=========================================================+
    | RTEMS Ticket | `2548 <https://devel.rtems.org/ticket/2548>`_ | Problematic integer conversion in rtems_clock_get_tod() |
    +--------------+-----------------------------------------------+---------------------------------------------------------+

.. _OpenIssues:

Open issues
-----------

When the QDP of this package version was produced, there were the following open issues associated:

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                    |
    +==============+===============================================+============================================================+
    | RTEMS Ticket | `2365 <https://devel.rtems.org/ticket/2365>`_ | Task pre-emption disable is broken due to pseudo ISR tasks |
    +--------------+-----------------------------------------------+------------------------------------------------------------+

.. _ClosedIssues:

Closed issues
-------------

The following issues were closed for this package version.

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                              |
    +==============+===============================================+======================================================+
    | RTEMS Ticket | `2189 <https://devel.rtems.org/ticket/2189>`_ | Insufficient documentation for rtems_clock_get_tod() |
    +--------------+-----------------------------------------------+------------------------------------------------------+
"""

    # Test PackageManualBuilder
    variant["enabled"] = ["package-manual"]
    director["/qdp/source/archive"].load()
    director["/qdp/source/doc-package-manual"].load()
    director["/qdp/test-logs/membench-2"].load()
    pm = director["/qdp/steps/doc-package-manual"]
    pm.mapper.add_get_value(f"{pm.item.type}:/clear-benchmark-variants",
                            _clear_benchmark_variants)
    pm.mapper.add_get_value(f"{pm.item.type}:/clear-copyrights-by-license",
                            _clear_copyrights_by_license)
    monkeypatch.setattr(rtemsspec.packagemanual, "run_command",
                        _sphinx_builder_run_command)
    monkeypatch.setattr(rtemsspec.packagemanual, "generate",
                        _package_manual_generate)
    director.build_package(None, None)
    monkeypatch.undo()
    pm_build = Path(director["/qdp/build/doc-package-manual"].directory)
    pm_index = pm_build / "source" / "index.rst"
    with open(pm_index, "r", encoding="utf-8") as src:
        assert src.read() == f""".. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2023 embedded brains GmbH & Co. KG

archive.tar.xz
6\u200b6\u200b3\u200b0\u200b4\u200b9\u200ba\u200b2\u200b0\u200bd\u200bf\u200be\u200ba\u200b6\u200bb\u200b8\u200bd\u200ba\u200b2\u200b8\u200bb\u200b2\u200be\u200bb\u200b9\u200b0\u200be\u200bd\u200bd\u200bd\u200b1\u200b0\u200bc\u200bc\u200bf\u200b2\u200b8\u200be\u200bf\u200b2\u200b5\u200b1\u200b9\u200b5\u200b6\u200b3\u200b3\u200b1\u200b0\u200bb\u200b9\u200bb\u200bd\u200be\u200b2\u200b5\u200bb\u200b7\u200b2\u200b6\u200b8\u200b4\u200b4\u200b4\u200b0\u200b1\u200b4\u200bc\u200b4\u200b8\u200bc\u200b4\u200b3\u200b8\u200b4\u200be\u200be\u200b5\u200bc\u200b5\u200ba\u200b5\u200b4\u200be\u200b7\u200b8\u200b3\u200b0\u200be\u200b4\u200b5\u200bf\u200bc\u200bd\u200b8\u200b7\u200bd\u200bf\u200b7\u200b9\u200b1\u200b0\u200ba\u200b7\u200bf\u200bd\u200ba\u200b7\u200b7\u200bb\u200b6\u200b8\u200bc\u200b2\u200be\u200bf\u200bd\u200bd\u200b7\u200b5\u200bf\u200b8\u200bd\u200be\u200b2\u200b5\u200be\u200b8
.. code-block:: none

    $ pkg-config --variable=ABI_FLAGS {tmp_dir}/pkg/lib/pkgconfig/sparc-rtems6-gr712rc-qual-only.pc
    pkg-config --variable=ABI_FLAGS {tmp_dir}/pkg/lib/pkgconfig/sparc-rtems6-gr712rc-qual-only.pc

    $ pkg-config --cflags {tmp_dir}/pkg/lib/pkgconfig/sparc-rtems6-gr712rc-qual-only.pc
    pkg-config --cflags {tmp_dir}/pkg/lib/pkgconfig/sparc-rtems6-gr712rc-qual-only.pc

    $ pkg-config --libs {tmp_dir}/pkg/lib/pkgconfig/sparc-rtems6-gr712rc-qual-only.pc
    pkg-config --libs {tmp_dir}/pkg/lib/pkgconfig/sparc-rtems6-gr712rc-qual-only.pc
verify_package.py
.. code-block:: none

    $ cd {tmp_dir}
    $ ./verify_package.py --help
    verify_package.py
b​6​3​5​4​f​6​4​a​1​a​2​6​1​a​2​e​7​1​0​1​5​a​b​5​1​f​c​5​d​3​c​a​8​7​6​3​0​5​c​b​a​2​7​3​3​5​5​7​e​b​f​e​3​e​2​c​0​a​0​9​5​1​e​2​c​6​1​e​7​6​3​d​8​a​9​e​d​d​b​b​4​d​4​1​e​5​6​c​e​f​3​d​d​f​8​a​8​0​2​3​e​a​7​e​f​7​a​a​f​e​9​9​6​b​b​b​1​f​a​4​5​4​7​3​3​5​0
.. code-block:: none

    ​example
4
Name 1
    Description 1

Name 2
    Description 2

Name 3
    Description 3
/rtems/req/mem-basic
/rtems/req/mem-basic
/rtems/req/mem-smp-1
/rtems/val/mem-basic
123
+0
.. raw:: latex

    \\begin{{scriptsize}}

.. table::
    :class: longtable
    :widths: 35,20,9,9,9,9,9

    +---------------+---------+-------+---------+-------+------+---------+
    | Specification | Variant | .text | .rodata | .data | .bss | .noinit |
    +===============+=========+=======+=========+=======+======+=========+
    +---------------+---------+-------+---------+-------+------+---------+

.. raw:: latex

    \\end{{scriptsize}}
.. raw:: latex

    \\begin{{scriptsize}}

.. table::
    :class: longtable
    :widths: 31,14,19,12,12,12

    +----------------------+-------------{'-' * tmp_dir_len}------------------------------------------------------------------------------------------+---------+----------+-------------+----------+
    | Specification        | Environment {' ' * tmp_dir_len}                                                                                          | Variant | Min [μs] | Median [μs] | Max [μs] |
    +======================+============={'=' * tmp_dir_len}==========================================================================================+=========+==========+=============+==========+
    | spec:/rtems/req/perf | `HotCache <{tmp_dir}/pkg/doc/ts/srs/html/requirements.html#spec-req-perf-runtime-environment-hot-cache>`__     | Name 1  | 0.275    | 0.275       | 0.275    |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 2  | +0 %     | +0 %        | +0 %     |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 3  | ?        | ?           | ?        |
    +                      +-------------{'-' * tmp_dir_len}------------------------------------------------------------------------------------------+---------+----------+-------------+----------+
    |                      | `FullCache <{tmp_dir}/pkg/doc/ts/srs/html/requirements.html#spec-req-perf-runtime-environment-full-cache>`__   | Name 1  | 0.275    | 0.275       | 0.475    |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 2  | +0 %     | +0 %        | +0 %     |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 3  | ?        | ?           | ?        |
    +                      +-------------{'-' * tmp_dir_len}------------------------------------------------------------------------------------------+---------+----------+-------------+----------+
    |                      | `DirtyCache <{tmp_dir}/pkg/doc/ts/srs/html/requirements.html#spec-req-perf-runtime-environment-dirty-cache>`__ | Name 1  | 2.125    | 2.125       | 2.125    |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 2  | +0 %     | +0 %        | +0 %     |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 3  | ?        | ?           | ?        |
    +                      +-------------{'-' * tmp_dir_len}------------------------------------------------------------------------------------------+---------+----------+-------------+----------+
    |                      | `Load/1 <{tmp_dir}/pkg/doc/ts/srs/html/requirements.html#spec-req-perf-runtime-environment-load>`__            | Name 1  | 1.062    | 1.062       | 1.062    |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 2  | +0 %     | +0 %        | +0 %     |
    +                      +             {' ' * tmp_dir_len}                                                                                          +---------+----------+-------------+----------+
    |                      |             {' ' * tmp_dir_len}                                                                                          | Name 3  | ?        | ?           | ?        |
    +----------------------+-------------{'-' * tmp_dir_len}------------------------------------------------------------------------------------------+---------+----------+-------------+----------+

.. raw:: latex

    \\end{{scriptsize}}
clear benchmark variants
.. raw:: latex

    \\begin{{scriptsize}}

.. table::
    :class: longtable
    :widths: 35,20,9,9,9,9,9

    +---------------+---------+-------+---------+-------+------+---------+
    | Specification | Variant | .text | .rodata | .data | .bss | .noinit |
    +===============+=========+=======+=========+=======+======+=========+
    +---------------+---------+-------+---------+-------+------+---------+

.. raw:: latex

    \\end{{scriptsize}}
There is no performance variants table available.
.. _GitRepositoryBuildSrcB:

Git Repository: build/src/b
---------------------------

B

The ``qdp`` branch with
commit ``52f06822b8921ad825cb593b792eab7640e26cde``
was used to build the QDP.  This branch is checked out after unpacking the
archive.  It is based on
commit `bcef89f2360b97005e490c92fe624ab9dec789e6 <https://git.rtems.org/rtems/commit/?id=bcef89f2360b97005e490c92fe624ab9dec789e6>`_
of the ``master`` branch of the ``origin`` remote repository.
.. _Name:

Name
----

* identity
.. _NameTargetA:

Name Target A
-------------

Brief target A.

Description target A.

.. _Name2:

Name 2
------

Description 2.

.. _Name2NewIssues:

New issues
^^^^^^^^^^

When the QDP of this package version was produced, there were the following new issues associated:

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+---------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                 |
    +==============+===============================================+=========================================================+
    | RTEMS Ticket | `2548 <https://devel.rtems.org/ticket/2548>`_ | Problematic integer conversion in rtems_clock_get_tod() |
    +--------------+-----------------------------------------------+---------------------------------------------------------+

.. _Name2OpenIssues:

Open issues
^^^^^^^^^^^

When the QDP of this package version was produced, there were the following open issues associated:

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                    |
    +==============+===============================================+============================================================+
    | RTEMS Ticket | `2365 <https://devel.rtems.org/ticket/2365>`_ | Task pre-emption disable is broken due to pseudo ISR tasks |
    +--------------+-----------------------------------------------+------------------------------------------------------------+

.. _Name2ClosedIssues:

Closed issues
^^^^^^^^^^^^^

The following issues were closed for this package version.

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                              |
    +==============+===============================================+======================================================+
    | RTEMS Ticket | `2189 <https://devel.rtems.org/ticket/2189>`_ | Insufficient documentation for rtems_clock_get_tod() |
    +--------------+-----------------------------------------------+------------------------------------------------------+

.. _Name1:

Name 1
------

Description 1.

.. _Name1NewIssues:

New issues
^^^^^^^^^^

When the QDP of this package version was produced, there were the following new issues associated:

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                    |
    +==============+===============================================+============================================================+
    | RTEMS Ticket | `2189 <https://devel.rtems.org/ticket/2189>`_ | Insufficient documentation for rtems_clock_get_tod()       |
    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | RTEMS Ticket | `2365 <https://devel.rtems.org/ticket/2365>`_ | Task pre-emption disable is broken due to pseudo ISR tasks |
    +--------------+-----------------------------------------------+------------------------------------------------------------+

.. _Name1OpenIssues:

Open issues
^^^^^^^^^^^

When the QDP of this package version was produced,
there were no open issues associated.

.. _Name1ClosedIssues:

Closed issues
^^^^^^^^^^^^^

When the QDP of this package version was produced,
there were no closed issues associated.
.. _OpenIssues:

Open issues
-----------

When the QDP of this package version was produced, there were the following open issues associated:

.. table::
    :class: longtable
    :widths: 27,14,59

    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | Database     | Identifier                                    | Subject                                                    |
    +==============+===============================================+============================================================+
    | RTEMS Ticket | `2365 <https://devel.rtems.org/ticket/2365>`_ | Task pre-emption disable is broken due to pseudo ISR tasks |
    +--------------+-----------------------------------------------+------------------------------------------------------------+
    | RTEMS Ticket | `2548 <https://devel.rtems.org/ticket/2548>`_ | Problematic integer conversion in rtems_clock_get_tod()    |
    +--------------+-----------------------------------------------+------------------------------------------------------------+
All directories and file paths in this section are
relative to :file:`{_format_path(tmp_dir / 'pkg')}`.

.. _Directory:

Directory - ..
--------------

.. _Directory FileDirATxt:

File - dir/a.txt
^^^^^^^^^^^^^^^^

The license file
:file:`.​.​/​dir/​a.​txt`
is applicable to this directory or parts of the directory:

.. code-block:: none

    ​A

.. _BSD2ClauseCopyrights:

BSD-2-Clause copyrights
-----------------------

| © 2023 Alice

.. code-block:: none

    ​Redistribution and use in source and binary forms, with or without
    ​modification, are permitted provided that the following conditions
    ​are met:
    ​1. Redistributions of source code must retain the above copyright
    ​   notice, this list of conditions and the following disclaimer.
    ​2. Redistributions in binary form must reproduce the above copyright
    ​   notice, this list of conditions and the following disclaimer in the
    ​   documentation and/or other materials provided with the distribution.
    ​
    ​THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    ​AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    ​IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ​ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
    ​LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    ​CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    ​SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    ​INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    ​CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ​ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    ​POSSIBILITY OF SUCH DAMAGE.
clear copyrights by license
All directories and file paths in this section are
relative to :file:`{_format_path(tmp_dir / 'pkg')}`.
"""
