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
import shutil

from rtemsqual.items import Item
from rtemsqual.items import ItemCache


class TestItem(object):
    def test_uid(self):
        i = Item("x", {})
        assert i.uid == "x"

    def test_contains(self):
        data = {}
        data["x"] = "y"
        i = Item("z", data)
        assert "x" in i
        assert "a" not in i

    def test_getitem(self):
        data = {}
        data["x"] = "y"
        i = Item("z", data)
        assert i["x"] == "y"

    def test_children(self):
        c = Item("c", {})
        p = Item("p", {})
        p.add_child(c)
        x = p.children
        assert len(x) == 1
        assert c == x[0]


class TestItemCache(object):
    def test_config_error(self):
        with pytest.raises(KeyError):
            ItemCache({})

    def test_load(self, tmpdir):
        config = {}
        cache_file = "spec.pickle"
        config["cache-file"] = cache_file
        spec_src = os.path.join(os.path.dirname(__file__), "spec-item-cache")
        spec_dst = os.path.join(tmpdir, "spec")
        shutil.copytree(spec_src, spec_dst)
        config["paths"] = [str(spec_dst)]
        ic = ItemCache(config)
        assert os.path.exists(os.path.join(spec_dst, cache_file))
        assert os.path.exists(os.path.join(spec_dst, "d", cache_file))
        assert ic["c"]["v"] == "c"
        assert ic["p"]["v"] == "p"
        t = ic.top_level
        assert len(t) == 1
        assert t["p"]["v"] == "p"
        ic2 = ItemCache(config)
        assert ic2["c"]["v"] == "c"
        with open(os.path.join(tmpdir, "spec", "d", "c.yml"), "w+") as out:
            out.write("links:\n- p: null\nv: x\n")
        ic3 = ItemCache(config)
        assert ic3["c"]["v"] == "x"
