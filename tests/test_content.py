# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsqual.content module. """

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

import tempfile
import unittest

from rtemsqual.content import Copyright
from rtemsqual.content import Copyrights
from rtemsqual.content import SphinxContent
from rtemsqual.content import MacroToSphinx
from rtemsqual.items import Item


class TestCopyright(unittest.TestCase):
    def test_get_statement(self):
        c = Copyright("John Doe")
        self.assertEqual("Copyright (C) John Doe", c.get_statement())
        c.add_year("3")
        self.assertEqual("Copyright (C) 3 John Doe", c.get_statement())
        c.add_year("3")
        self.assertEqual("Copyright (C) 3 John Doe", c.get_statement())
        c.add_year("5")
        self.assertEqual("Copyright (C) 3, 5 John Doe", c.get_statement())
        c.add_year("4")
        self.assertEqual("Copyright (C) 3, 5 John Doe", c.get_statement())
        c.add_year("2")
        self.assertEqual("Copyright (C) 2, 5 John Doe", c.get_statement())

    def test_lt(self):
        a = Copyright("A")
        b = Copyright("B")
        c = Copyright("C")
        self.assertLess(b, a)
        self.assertLess(c, a)
        self.assertLess(c, b)
        b.add_year("1")
        self.assertLess(b, c)
        a.add_year("2")
        self.assertLess(a, b)


class TestCopyrights(unittest.TestCase):
    def test_register(self):
        c = Copyrights()
        self.assertRaises(ValueError, c.register, "abc")
        c.register("Copyright (C) A")
        c.register("Copyright (C) 2 A")
        c.register("Copyright (C) 2, 3 A")
        c.register("Copyright (C) D")
        c.register("Copyright (C) 1 D")
        c.register("Copyright (C) 1, 4 D")
        c.register("Copyright (C) C")
        c.register("Copyright (C) 1 B")
        s = c.get_statements()
        self.assertEqual(4, len(s))
        self.assertEqual("Copyright (C) C", s[0])
        self.assertEqual("Copyright (C) 2, 3 A", s[1])
        self.assertEqual("Copyright (C) 1, 4 D", s[2])
        self.assertEqual("Copyright (C) 1 B", s[3])


class TestSphinxContent(unittest.TestCase):
    def test_add_label(self):
        sc = SphinxContent()
        sc.add_label("x")
        self.assertEqual(".. _x:\n", sc.content)

    def test_add_header(self):
        sc = SphinxContent()
        sc.add_header("x")
        self.assertEqual("x\n=\n", sc.content)

    def test_add_blank_line(self):
        sc = SphinxContent()
        sc.add_blank_line()
        self.assertEqual("\n", sc.content)

    def test_add_line(self):
        sc = SphinxContent()
        sc.add_line("x")
        self.assertEqual("x\n", sc.content)
        sc.add_line("y", 1)
        self.assertEqual("x\n    y\n", sc.content)
        sc.add_line("")
        self.assertEqual("x\n    y\n\n", sc.content)

    def test_add_index_entries(self):
        sc = SphinxContent()
        sc.add_index_entries(["x", "y"])
        self.assertEqual("\n.. index:: x\n.. index:: y\n", sc.content)

    def test_add_definition_item(self):
        sc = SphinxContent()
        sc.add_definition_item("x", ["y", "z"])
        self.assertEqual("\nx\n    y\n    z\n", sc.content)

    def test_license(self):
        sc = SphinxContent()
        self.assertRaises(ValueError, sc.register_license, "x")
        sc.register_license("CC-BY-SA-4.0")
        self.assertEqual("", sc.content)
        sc.add_licence_and_copyrights()
        self.assertEqual(".. SPDX-License-Identifier: CC-BY-SA-4.0\n\n",
                         sc.content)

    def test_license_and_copyrights(self):
        sc = SphinxContent()
        self.assertRaises(ValueError, sc.register_license, "x")
        sc.register_copyright("Copyright (C) A")
        self.assertEqual("", sc.content)
        sc.add_licence_and_copyrights()
        self.assertEqual(
            ".. SPDX-License-Identifier: CC-BY-SA-4.0\n\n.. Copyright (C) A\n\n",
            sc.content)

    def test_write(self):
        sc = SphinxContent()
        sc.add_line("x")
        with tempfile.TemporaryDirectory() as tempdir:
            path = tempdir + "/y/z"
            sc.write(path)
            with open(path, "r") as src:
                self.assertEqual("x\n", src.read())


class TestMacroToSphinx(unittest.TestCase):
    def test_substitute(self):
        macro_to_sphinx = MacroToSphinx()
        data = {}
        data["glossary-term"] = "y"
        terms = {}
        terms["x"] = Item("x", data)
        macro_to_sphinx.set_terms(terms)
        self.assertEqual("@", macro_to_sphinx.substitute("@@"))
        self.assertEqual("@x", macro_to_sphinx.substitute("@x"))
        self.assertRaises(KeyError, macro_to_sphinx.substitute, "@x{y}")
        self.assertEqual(":term:`y`", macro_to_sphinx.substitute("@term{x}"))
