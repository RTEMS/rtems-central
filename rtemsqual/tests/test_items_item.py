# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsqual.items module. """

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

import os
import pytest

from rtemsqual.items import Item, Link


def test_to_abs_uid():
    item = Item("/x/y", {})
    assert item.to_abs_uid("z") == "/x/z"
    assert item.to_abs_uid("/z") == "/z"
    assert item.to_abs_uid("../z") == "/z"
    assert item.to_abs_uid("../../z") == "/z"


def test_uid():
    item = Item("x", {})
    assert item.uid == "x"


def test_contains():
    data = {}
    data["x"] = "y"
    item = Item("z", data)
    assert "x" in item
    assert "a" not in item


def test_getitem():
    data = {}
    data["x"] = "y"
    item = Item("z", data)
    assert item["x"] == "y"


def test_children():
    child = Item("c", {})
    parent = Item("p", {})
    parent.add_link_to_child(Link(child, {"a": "b"}))
    children = [item for item in parent.children()]
    assert len(children) == 1
    assert children[0] == child
    links = [link for link in parent.links_to_children()]
    assert len(links) == 1
    assert links[0].item == child
    assert links[0]["a"] == "b"


def _is_enabled(enabled, enabled_by):
    item = Item("i", {"enabled-by": enabled_by})
    return item.is_enabled(enabled)


def test_is_enabled():
    assert _is_enabled([], None)
    assert _is_enabled([], [])
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
    assert not _is_enabled(["A"], {"and": "A", "x": "y"})
    assert not _is_enabled(["A"], {"x": "A"})
    assert _is_enabled([], {"not": {"and": ["A", {"not": "A"}]}})


def test_save_and_load(tmpdir):
    item_file = os.path.join(tmpdir, "i.yml")
    item = Item("i", {"k": "v"})
    item.file = item_file
    assert item.file == item_file
    item.save()
    with open(item_file, "r") as src:
        assert src.read() == "k: v\n"
    assert item.file == item_file

    item2 = Item("i2", {})
    item2.file = item_file
    with pytest.raises(KeyError):
        item2["k"]
    item2.load()
    assert item2["k"] == "v"
    assert item.file == item_file
