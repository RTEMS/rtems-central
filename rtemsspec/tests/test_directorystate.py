# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the rtemsspec.directorystate module. """

# Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
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

from rtemsspec.items import Item, EmptyItemCache, Link
from rtemsspec.directorystate import DirectoryState
from rtemsspec.packagebuild import BuildItemFactory, PackageBuildDirector
from rtemsspec.tests.util import get_and_clear_log


class _TestState(DirectoryState):
    pass


@pytest.fixture
def _change_cwd():
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield
    os.chdir(cwd)


_DOC_RST_HASH = "Cm41zmS2o7TF6FBxnQxWxmPDVhufFst7pFkkQriQnEOwJWXS_zjEwKLVsgBT4L-v1iWzRUCilifIdY4uqkg5Gw=="
_T_YML_HASH = "_FTeBKV04q5fMTETF65lBzv6dNeHTMLT3dZmHF1BEAOLtmxvPdAJc_7-RDmGRiv3GU_uddvkFc005S0EeSx0PA=="
_INCLUDE_ALL = [{"include": "**/*", "exclude": []}]


def test_directorystate(caplog, tmpdir, _change_cwd):
    item_cache = EmptyItemCache()
    factory = BuildItemFactory()
    factory.add_constructor("qdp/directory-state/generic", _TestState)
    director = PackageBuildDirector(item_cache, factory)
    base = "spec-glossary"

    data = {
        "SPDX-License-Identifier":
        "CC-BY-SA-4.0 OR BSD-2-Clause",
        "copyrights":
        ["Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG"],
        "copyrights-by-license": {},
        "directory":
        base,
        "enabled-by":
        True,
        "files": [
            {
                "file": "doc.rst",
                "hash": None
            },
            {
                "file": "glossary/t.yml",
                "hash": None
            },
        ],
        "hash":
        None,
        "links": [],
        "patterns": [],
    }
    item = item_cache.add_volatile_item("/directory-state", data)
    item["_type"] = "qdp/directory-state/generic"
    item_file = os.path.join(tmpdir, "item.yml")
    item.file = str(item_file)
    dir_state = director["/directory-state"]
    assert dir_state.directory == base
    with pytest.raises(ValueError):
        dir_state.digest
    with pytest.raises(ValueError):
        dir_state.has_changed(Link(item, {"hash": "blub"}))
    overall_hash = dir_state.lazy_load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="
    assert dir_state.digest == overall_hash
    dir_state.save()
    with open(item_file, "r") as src:
        assert f"""SPDX-License-Identifier: CC-BY-SA-4.0 OR BSD-2-Clause
copyrights:
- Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
copyrights-by-license: {{}}
directory: {base}
enabled-by: true
files:
- file: doc.rst
  hash: {_DOC_RST_HASH}
- file: glossary/t.yml
  hash: {_T_YML_HASH}
hash: SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag==
links: []
patterns: []
""" == src.read()
    assert dir_state.file == "spec-glossary/doc.rst"
    assert dir_state.substitute("${.:/file}") == "spec-glossary/doc.rst"
    assert dir_state.substitute("${.:/file[0]}") == "spec-glossary/doc.rst"
    assert dir_state.substitute(
        "${.:/file[1]}") == "spec-glossary/glossary/t.yml"
    assert dir_state.substitute(
        "${.:/file-without-extension[1]}") == "spec-glossary/glossary/t"
    assert list(dir_state.files(".")) == ["./doc.rst", "./glossary/t.yml"]
    assert list(dir_state.files()) == [
        str(os.path.join(base, "doc.rst")),
        str(os.path.join(base, "glossary/t.yml"))
    ]
    assert list(dir_state.files_and_hashes(".")) == [
        ("./doc.rst", _DOC_RST_HASH), ("./glossary/t.yml", _T_YML_HASH)
    ]
    assert list(dir_state.files_and_hashes()) == [
        (str(os.path.join(base, "doc.rst")), _DOC_RST_HASH),
        (str(os.path.join(base, "glossary/t.yml")), _T_YML_HASH)
    ]

    dir_state.set_files(["doc.rst"])
    dir_state.add_files(["glossary/t.yml"])
    with pytest.raises(ValueError):
        dir_state.digest
    overall_hash = dir_state.lazy_load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="
    overall_hash = dir_state.lazy_load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="

    caplog.set_level(logging.DEBUG)
    data_2 = {
        "directory": base,
        "enabled-by": True,
        "files": [],
        "links": [{
            "role": "directory-state-exclude",
            "uid": "directory-state"
        }],
        "patterns": [],
    }
    item_2 = item_cache.add_volatile_item("/directory-state-2", data_2)
    dir_state_2 = DirectoryState(director, item_2)
    dir_state_2.add_files(
        os.path.relpath(path, dir_state_2.directory) for path in dir_state)
    assert list(dir_state_2.files()) == []
    dir_state_2.set_files(
        os.path.relpath(path, dir_state_2.directory) for path in dir_state)
    assert list(dir_state_2.files()) == []
    dir_state_2.set_files([])
    assert list(dir_state_2.files()) == []
    with pytest.raises(ValueError):
        dir_state_2.digest
    overall_hash = dir_state_2.load()
    assert overall_hash == "YtmDhTiLc9q20OthwE35dnsoPQz5gkQqajQQC2K3h5_yzY67hX35LlnhuR_kEx-_blEsjQlT1ijdP5YwUwb3bw=="

    dir_state_2["patterns"] = _INCLUDE_ALL
    overall_hash = dir_state_2.load()
    assert overall_hash == "GSGvDhHq3M-csmWHrXBLJPB7yFB1hjxiZt3hROQP_dltVlHvCslNii9PzzbSiEYCEsi5qnOUp1OOs916PUvX4g=="

    item["patterns"] = [{
        "include": "**/*",
        "exclude": ["*/glossary.rst", "*/[guv].yml", "*/sub/*"]
    }]
    overall_hash = dir_state.load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="

    item["patterns"] = [{
        "include": "**/doc.rst",
        "exclude": []
    }, {
        "include": "**/t.yml",
        "exclude": []
    }]
    overall_hash = dir_state.load()
    assert overall_hash == "SrJDe4-ewVrM9BV9ttASllPsrXz2r_-ts9urtVeBa9s7JuBORQrvuPyW-hvsef80a8HvKvfeNSOmAh2eQ2_aag=="

    item["patterns"] = [{"include": "**/foo", "exclude": []}]
    overall_hash = dir_state.load()
    assert overall_hash == "YtmDhTiLc9q20OthwE35dnsoPQz5gkQqajQQC2K3h5_yzY67hX35LlnhuR_kEx-_blEsjQlT1ijdP5YwUwb3bw=="

    caplog.set_level(logging.DEBUG)
    data_3 = {
        "directory": str(tmpdir),
        "enabled-by": True,
        "patterns": [],
        "files": [],
        "links": [],
    }
    item_3 = item_cache.add_volatile_item("/directory-state-3", data_3)
    item_3["_type"] = "qdp/directory-state/generic"
    item_3_file = os.path.join(tmpdir, "item-3.yml")
    item_3.file = str(item_3_file)
    dir_state_3 = director["/directory-state-3"]

    src_file = os.path.join(base, "doc.rst")
    dir_state_3.copy_file(src_file, "doc.rst")
    dst_file = os.path.join(tmpdir, "doc.rst")
    assert os.path.exists(dst_file)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy '{src_file}' to '{dst_file}'" in log
    dir_state_3.load()

    dir_state_3.remove_files()
    assert not os.path.exists(dst_file)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: remove: {dst_file}" in log

    dir_state_3.remove_files()
    log = get_and_clear_log(caplog)
    assert f"DEBUG /directory-state-3: file not found: {dst_file}" in log

    dir_state_3["patterns"] = _INCLUDE_ALL
    dir_state_3.remove_files()
    dir_state_3["patterns"] = []
    log = get_and_clear_log(caplog)
    assert f"WARNING /directory-state-3: file not found: {dst_file}" in log

    assert dir_state_3.digest
    assert list(dir_state_3.files_and_hashes()) == [(str(dst_file),
                                                     _DOC_RST_HASH)]
    dir_state_3.invalidate()
    with pytest.raises(ValueError):
        dir_state_3.digest
    assert list(dir_state_3.files_and_hashes()) == [(str(dst_file), None)]
    dir_state_3["patterns"] = _INCLUDE_ALL
    dir_state_3.invalidate()
    dir_state_3["patterns"] = []
    assert list(dir_state_3.files_and_hashes()) == []

    dir_state_3.copy_tree(base, "x")
    for path in [
            "doc.rst", "g.yml", "glossary.rst", "glossary/sub/g.yml",
            "glossary/sub/x.yml", "glossary/t.yml", "glossary/u.yml",
            "glossary/v.yml"
    ]:
        assert os.path.exists(os.path.join(tmpdir, "x", path))

    dir_state_3["patterns"] = _INCLUDE_ALL
    dir_state_3.invalidate()
    dir_state_3["patterns"] = []
    dir_state_3.add_tree(os.path.join("spec-glossary", "glossary", "sub"),
                         excludes=["/x.*"])
    assert list(dir_state_3.files()) == [f"{tmpdir}/g.yml"]
    assert not os.path.exists(os.path.join(tmpdir, "g.yml"))
    assert os.path.exists(os.path.join(tmpdir, "x", "glossary", "sub",
                                       "g.yml"))
    dir_state_3.move_tree(os.path.join(tmpdir, "x", "glossary", "sub"))
    assert list(dir_state_3.files()) == [f"{tmpdir}/g.yml", f"{tmpdir}/x.yml"]
    assert not os.path.exists(
        os.path.join(tmpdir, "x", "glossary", "sub", "g.yml"))
    assert os.path.exists(os.path.join(tmpdir, "g.yml"))

    link = Link(item_3, {"hash": None})
    dir_state_3.load()
    assert dir_state_3.has_changed(link)
    dir_state_3.refresh_link(link)
    assert not dir_state_3.has_changed(link)

    dir_state_3.discard()
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: discard" in log

    dir_state_3.clear()
    dir_state_3.refresh()
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: refresh" in log

    dir_state_3.clear()
    dir_state_3.add_tarfile_members("test-files/archive.tar.xz", tmpdir, False)
    assert list(dir_state_3.files()) == [
        f"{tmpdir}/member-dir/dir-member.txt", f"{tmpdir}/member.txt"
    ]
    assert not os.path.exists(os.path.join(tmpdir, "member.txt"))
    dir_state_3.add_tarfile_members("test-files/archive.tar.xz", tmpdir, True)
    assert list(dir_state_3.files()) == [
        f"{tmpdir}/member-dir/dir-member.txt", f"{tmpdir}/member.txt"
    ]
    assert os.path.exists(os.path.join(tmpdir, "member.txt"))

    dir_state_3.clear()
    src_file = os.path.join(base, "doc.rst")
    dir_state_3.copy_files(base, ["doc.rst"], "uvw")
    dst_file = os.path.join(tmpdir, "uvw", "doc.rst")
    assert os.path.exists(dst_file)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy '{src_file}' to '{dst_file}'" in log
    assert list(name for name in dir_state_3) == [dst_file]

    symlink = os.path.join(tmpdir, "symlink")
    os.symlink("foobar", symlink)
    dir_state_3.set_files(["symlink"])
    dir_state_3.load()
    assert list(dir_state_3.files_and_hashes()) == [(
        symlink,
        "ClAmHr0aOQ_tK_Mm8mc8FFWCpjQtUjIElz0CGTN_gWFqgGmwElh89WNfaSXxtWw2AjDBmyc1AO4BPgMGAb8kJQ=="
    )]

    get_and_clear_log(caplog)

    item["patterns"] = [{"include": "**/t.yml", "exclude": []}]
    dir_state.load()
    dir_state_3.lazy_clone(dir_state)
    assert list(dir_state_3.files(".")) == ["./glossary/t.yml"]
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy" in log

    item["patterns"] = [{"include": "**/x.yml", "exclude": []}]
    dir_state.load()
    dir_state_3.lazy_clone(dir_state)
    assert list(dir_state_3.files(".")) == ["./glossary/sub/x.yml"]
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: remove" in log

    os.unlink(dir_state_3.file)
    item["patterns"] = [{"include": "**/t.yml", "exclude": []}]
    dir_state.load()
    dir_state_3.lazy_clone(dir_state)
    log = get_and_clear_log(caplog)
    assert f"WARNING /directory-state-3: file not found" in log

    dir_state_3.invalidate()
    dir_state_3.lazy_clone(dir_state)
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: copy" in log

    dir_state_3.lazy_clone(dir_state)
    assert list(dir_state_3.files(".")) == ["./glossary/t.yml"]
    log = get_and_clear_log(caplog)
    assert f"INFO /directory-state-3: keep as is" in log

    assert dir_state_3.directory == tmpdir
    dir_state_3.set_files(["/a/b", "/a/c"])
    dir_state_3.compact()
    assert dir_state_3.directory == tmpdir
    dir_state_3.set_files(["a/b", "c/d"])
    dir_state_3.compact()
    assert dir_state_3.directory == tmpdir
    dir_state_3.set_files(["a/b", "a/c"])
    dir_state_3.compact()
    assert dir_state_3.directory == f"{tmpdir}/a"

    dir_state_3.set_files(["data.json"])
    assert not os.path.exists(dir_state_3.file)
    dir_state_3.json_dump({"foo": "bar"})
    assert os.path.exists(dir_state_3.file)
    assert dir_state_3.json_load() == {"foo": "bar"}
