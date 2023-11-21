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

import logging
import os
import pytest
from pathlib import Path
import shutil
import tarfile

from rtemsspec.items import EmptyItem, Item, ItemCache, ItemGetValueContext
from rtemsspec.packagebuild import BuildItem, BuildItemMapper, \
    build_item_input, PackageBuildDirector
from rtemsspec.packagebuildfactory import create_build_item_factory
from rtemsspec.specverify import verify
from rtemsspec.tests.util import get_and_clear_log
from rtemsspec.util import run_command


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


def test_packagebuild(caplog, tmpdir):
    tmp_dir = Path(tmpdir)
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

    director.build_package(None, None)
    log = get_and_clear_log(caplog)
    assert "INFO /qdp/steps/a: create build item" in log
    assert "INFO /qdp/steps/b: create build item" not in log
    assert "INFO /qdp/steps/b: is disabled" in log
    assert "INFO /qdp/steps/c: output is disabled: /qdp/output/b" in log

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
