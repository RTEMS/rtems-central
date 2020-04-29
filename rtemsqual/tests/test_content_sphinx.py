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

import os
import pytest

from rtemsqual.content import SphinxContent
from rtemsqual.content import MacroToSphinx
from rtemsqual.items import Item, ItemCache


class EmptyCache(ItemCache):
    def __init__(self):
        return


def test_add_label():
    sc = SphinxContent()
    sc.add_label("x")
    assert ".. _x:\n" == sc.content


def test_add_header():
    sc = SphinxContent()
    sc.add_header("x")
    assert "x\n=\n" == sc.content


def test_add_blank_line():
    sc = SphinxContent()
    sc.add_blank_line()
    assert "\n" == sc.content


def test_add_line():
    sc = SphinxContent()
    sc.add_line("x")
    assert "x\n" == sc.content
    sc.add_line("y", 1)
    assert "x\n    y\n" == sc.content
    sc.add_line("")
    assert "x\n    y\n\n" == sc.content


def test_add_lines():
    sc = SphinxContent()
    sc.add_lines("x")
    assert sc.content == "x\n"
    sc.add_lines("y", 1)
    assert sc.content == "x\n    y\n"
    sc.add_lines(["a", "b"])
    assert sc.content == "x\n    y\na\nb\n"


def test_add_index_entries():
    sc = SphinxContent()
    sc.add_index_entries(["x", "y"])
    assert "\n.. index:: x\n.. index:: y\n" == sc.content
    sc.add_index_entries("z")
    assert "\n.. index:: x\n.. index:: y\n\n.. index:: z\n" == sc.content


def test_add_definition_item():
    sc = SphinxContent()
    sc.add_definition_item("x", ["y", "z"])
    assert sc.content == "\nx\n    y\n    z\n"
    sc = SphinxContent()
    sc.add_definition_item("a", "\n b\n")
    assert sc.content == "\na\n     b\n"


def test_license():
    sc = SphinxContent()
    with pytest.raises(ValueError):
        sc.register_license("x")
    sc.register_license("CC-BY-SA-4.0")
    assert "" == sc.content
    sc.add_licence_and_copyrights()
    assert ".. SPDX-License-Identifier: CC-BY-SA-4.0\n\n" == sc.content


def test_license_and_copyrights():
    sc = SphinxContent()
    with pytest.raises(ValueError):
        sc.register_license("x")
    sc.register_copyright("Copyright (C) A")
    assert "" == sc.content
    sc.add_licence_and_copyrights()
    assert ".. SPDX-License-Identifier: CC-BY-SA-4.0\n\n.. Copyright (C) A\n\n" == sc.content


def test_write(tmpdir):
    sc = SphinxContent()
    sc.add_line("x")
    path = os.path.join(tmpdir, "x", "y")
    sc.write(path)
    with open(path, "r") as src:
        assert "x\n" == src.read()
    tmpdir.chdir()
    path = "z"
    sc.write(path)
    with open(path, "r") as src:
        assert "x\n" == src.read()


def test_substitute():
    macro_to_sphinx = MacroToSphinx()
    data = {}
    data["glossary-term"] = "y"
    terms = {}
    terms["x"] = Item(EmptyCache(), "x", data)
    macro_to_sphinx.set_terms(terms)
    assert "@" == macro_to_sphinx.substitute("@@")
    assert "@x" == macro_to_sphinx.substitute("@x")
    with pytest.raises(KeyError):
        macro_to_sphinx.substitute("@x{y}")
    assert ":term:`y`" == macro_to_sphinx.substitute("@term{x}")
