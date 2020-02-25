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
import tempfile
import shutil
import unittest

from rtemsqual.items import Item
from rtemsqual.items import ItemCache


class TestItem(unittest.TestCase):
    def test_uid(self):
        i = Item("x", {})
        self.assertEqual("x", i.uid)

    def test_getitem(self):
        data = {}
        data["x"] = "y"
        i = Item("z", data)
        self.assertEqual("y", i["x"])

    def test_children(self):
        c = Item("c", {})
        p = Item("p", {})
        p.add_child(c)
        x = p.children
        self.assertEqual(1, len(x))
        self.assertEqual(c, x[0])


class TestItemCache(unittest.TestCase):
    def test_config_error(self):
        self.assertRaises(KeyError, ItemCache, {})

    def test_load(self):
        with tempfile.TemporaryDirectory() as tempdir:
            config = {}
            cache_file = tempdir + "/spec.pickle"
            config["cache-file"] = cache_file
            spec_dir = tempdir + "/spec"
            shutil.copytree(
                os.path.dirname(__file__) + "/spec-item-cache", spec_dir)
            config["paths"] = [spec_dir]
            ic = ItemCache(config)
            self.assertTrue(os.path.exists(cache_file))
            self.assertEqual("c", ic["c"]["v"])
            self.assertEqual("p", ic["p"]["v"])
            t = ic.top_level
            self.assertEqual(1, len(t))
            self.assertEqual("p", t["p"]["v"])
            ic2 = ItemCache(config)
            self.assertEqual("c", ic2["c"]["v"])
            with open(tempdir + "/spec/d/c.yml", "w+") as out:
                out.write("links:\n- p: null\nv: x\n")
            ic3 = ItemCache(config)
            self.assertEqual("x", ic3["c"]["v"])
