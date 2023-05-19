# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.items module. """

# Copyright (C) 2020 embedded brains GmbH & Co. KG
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

import os
import pytest

from rtemsspec.items import EmptyItemCache, Item, ItemGetValueContext, \
    JSONItemCache, Link


def test_to_abs_uid():
    item = Item(EmptyItemCache(), "/x/y", {})
    assert item.to_abs_uid(".") == "/x/y"
    assert item.to_abs_uid("z") == "/x/z"
    assert item.to_abs_uid("/z") == "/z"
    assert item.to_abs_uid("../z") == "/z"
    assert item.to_abs_uid("../../z") == "/z"


def test_eq():
    a = Item(EmptyItemCache(), "a", {})
    b = Item(EmptyItemCache(), "b", {})
    assert a == a
    assert a != b
    assert a != 0


def test_lt():
    a = Item(EmptyItemCache(), "a", {})
    b = Item(EmptyItemCache(), "b", {})
    assert a < b
    with pytest.raises(TypeError):
        b = a < 0


def test_hash():
    a = Item(EmptyItemCache(), "a", {})
    assert hash(a) == hash("a")


def test_uid():
    item = Item(EmptyItemCache(), "x", {})
    assert item.uid == "x"


def test_spec():
    item = Item(EmptyItemCache(), "x/y/z", {})
    assert item.spec == "spec:x/y/z"
    assert item.spec_2 == "spec:x/\u200by/\u200bz"


def test_contains():
    data = {}
    data["x"] = "y"
    item = Item(EmptyItemCache(), "z", data)
    assert "x" in item
    assert "a" not in item


def test_data():
    data = {}
    data["x"] = "y"
    item = Item(EmptyItemCache(), "z", data)
    assert item.data == {"x": "y"}


def test_cache():
    item_cache = EmptyItemCache()
    item = Item(item_cache, "i", {})
    assert item.cache == item_cache


def test_digest():
    i = Item(EmptyItemCache(), "i", {})
    assert i.digest == "47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU="
    i["_ignored"] = "nix"
    assert i.digest == "47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU="
    i["a"] = {"b": ["c", 1, False, 1.25], "d": None}
    assert i.digest == "J0ljdR4wMT8y9Rid7I50SfVlgtvn1iTbgCLC5G7RNNQ="
    i["a"] = {"b": ["e", 1, False, 1.25], "d": None}
    assert i.digest == "_6QYG-kB-AmaRXaskJZ9fuJwxvM6mQRTNNrWbIRcYGw="
    i["a"] = {"b": ["e", "1", False, 1.25], "d": None}
    assert i.digest == "_sNRYXk0DTOp1lptrqqd2kb5hIlg-SGeynVVLGnbmKs="


def test_getitem():
    data = {}
    data["x"] = "y"
    item = Item(EmptyItemCache(), "z", data)
    assert item["x"] == "y"


def test_setitem():
    data = {}
    item = Item(EmptyItemCache(), "z", data)
    with pytest.raises(KeyError):
        item["a"]
    item["a"] = "b"
    assert item["a"] == "b"


def test_get():
    data = {}
    data["x"] = "y"
    item = Item(EmptyItemCache(), "z", data)
    assert item.get("x", "z") == "y"
    assert item.get("z", "a") == "a"


def test_children():
    child = Item(EmptyItemCache(), "c", {})
    child["_enabled"] = True
    child_2 = Item(EmptyItemCache(), "c2", {})
    child_2["_enabled"] = False
    parent = Item(EmptyItemCache(), "p", {})
    parent["_enabled"] = True
    parent.add_link_to_child(Link(child, {"a": "b", "role": "c"}))
    parent.add_link_to_child(Link(child_2, {"a": "b", "role": "c2"}))
    children = [item for item in parent.children()]
    assert len(children) == 1
    assert children[0] == child
    children = [item for item in parent.children("c")]
    assert len(children) == 1
    assert children[0] == child
    children = [item for item in parent.children(["c", "d"])]
    assert len(children) == 1
    assert children[0] == child
    children = [item for item in parent.children([])]
    assert len(children) == 0
    children = [item for item in parent.children("d")]
    assert len(children) == 0
    links = [link for link in parent.links_to_children()]
    assert len(links) == 1
    assert links[0].item == child
    assert links[0]["a"] == "b"
    assert links[0].role == "c"
    assert parent.child("c") == child
    with pytest.raises(IndexError):
        parent.child("c", 1)
    assert parent.child_link("c").item == child
    with pytest.raises(IndexError):
        parent.child_link("c", 1)


def test_parents():
    item_cache = EmptyItemCache()
    child = Item(
        item_cache, "c", {
            "links": [{
                "a": "b",
                "role": "c",
                "uid": "p"
            }, {
                "a": "b",
                "role": "c",
                "uid": "p2"
            }]
        })
    child["_enabled"] = True
    parent = Item(item_cache, "p", {"links": []})
    parent["_enabled"] = True
    item_cache._items["p"] = parent
    parent_2 = Item(EmptyItemCache(), "p2", {})
    parent_2["_enabled"] = False
    item_cache._items["p2"] = parent_2
    child.init_parents(item_cache)
    for link in child.links_to_parents():
        link.item.add_link_to_child(Link.create(link, child))
        link["foo"] = "bar"
    assert child["links"][0]["foo"] == "bar"
    parents = [item for item in child.parents()]
    assert len(parents) == 1
    assert parents[0] == parent
    parents = [item for item in child.parents("c")]
    assert len(parents) == 1
    assert parents[0] == parent
    parents = [item for item in child.parents(["c", "d"])]
    assert len(parents) == 1
    assert parents[0] == parent
    parents = [item for item in child.parents([])]
    assert len(parents) == 0
    parents = [item for item in child.parents("d")]
    assert len(parents) == 0
    links = [link for link in child.links_to_parents()]
    assert len(links) == 1
    assert links[0].item == parent
    assert links[0]["a"] == "b"
    assert links[0].role == "c"
    assert child.parent("c") == parent
    with pytest.raises(IndexError):
        child.parent("c", 1)
    assert child.parent_link("c").item == parent
    with pytest.raises(IndexError):
        child.parent_link("c", 1)


def _is_enabled(enabled, enabled_by):
    item = Item(EmptyItemCache(), "i", {"enabled-by": enabled_by})
    return item.is_enabled(enabled)


def test_is_enabled():
    assert _is_enabled([], True)
    assert not _is_enabled([], False)
    assert not _is_enabled([], [])
    assert not _is_enabled([], ["A"])
    assert _is_enabled(["A"], "A")
    assert not _is_enabled(["B"], "A")
    assert _is_enabled(["A"], ["A"])
    assert not _is_enabled(["B"], ["A"])
    assert _is_enabled(["A"], ["A", "B"])
    assert _is_enabled(["B"], ["A", "B"])
    assert not _is_enabled(["C"], ["A", "B"])
    assert not _is_enabled(["A"], {"not": "A"})
    assert _is_enabled(["B"], {"not": "A"})
    assert not _is_enabled(["A"], {"and": ["A", "B"]})
    assert _is_enabled(["A", "B"], {"and": ["A", "B"]})
    assert _is_enabled(["A", "B", "C"], {"and": ["A", "B"]})
    assert _is_enabled(["A", "B"], {"and": ["A", "B", {"not": "C"}]})
    assert not _is_enabled(["A", "B", "C"], {"and": ["A", "B", {"not": "C"}]})
    with pytest.raises(KeyError):
        _is_enabled(["A"], {"x": "A"})
    assert _is_enabled([], {"not": {"and": ["A", {"not": "A"}]}})


def test_save_and_load(tmpdir):
    item_file = os.path.join(tmpdir, "i.yml")
    item = Item(EmptyItemCache(), "i", {"k": "v"})
    item.file = item_file
    assert item.file == item_file
    item.save()
    with open(item_file, "r") as src:
        assert src.read() == "k: v\n"
    assert item.file == item_file

    item2 = Item(EmptyItemCache(), "i2", {})
    item2.file = item_file
    with pytest.raises(KeyError):
        item2["k"]
    item2.load()
    assert item2["k"] == "v"
    assert item.file == item_file


def test_save_and_load_json(tmpdir):
    spec_dir = os.path.join(os.path.dirname(__file__), "spec-json")
    config = {"paths": [spec_dir], "spec-type-root-uid": None}
    item_cache = JSONItemCache(config)
    item = item_cache["/d/b"].parent("b")
    file = os.path.join(tmpdir, "file")
    item.file = file
    assert item["enabled-by"]
    item["enabled-by"] = False
    item.save()
    with open(file, "r") as src:
        assert src.read() == """{
  "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
  "copyrights": [
    "Copyright (C) 2022 embedded brains GmbH & Co. KG
  ],
  "enabled-by": false,
  "links": [],
  "type": "a"
}"""
    item.load()
    with open(file, "w") as dst:
        dst.write("invalid")
    with pytest.raises(IOError):
        item.load()


def test_item_get_value_arg():
    item = Item(EmptyItemCache(), "i", {})
    ctx = ItemGetValueContext(item, "", None, "", 0, "k=v,k2=v2")
    assert ctx.arg("k") == "v"
    assert ctx.arg("k2") == "v2"
    assert ctx.arg("k3", "v3") == "v3"
