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
    assert str(sc) == """.. _x:
"""


def test_add_header():
    sc = SphinxContent()
    sc.add_header("x")
    assert str(sc) == """x
=
"""


def test_append():
    sc = SphinxContent()
    sc.append("x")
    assert str(sc) == """x
"""
    with sc.indent():
        sc.append("y")
        assert str(sc) == """x
    y
"""
        sc.append("")
        assert str(sc) == """x
    y

"""


def test_add_index_entries():
    sc = SphinxContent()
    sc.add_index_entries(["x", "y"])
    assert str(sc) == """.. index:: x
.. index:: y
"""
    sc.add_index_entries("z")
    assert str(sc) == """.. index:: x
.. index:: y

.. index:: z
"""


def test_add_definition_item():
    sc = SphinxContent()
    sc.add_definition_item("x", ["y", "z"])
    assert str(sc) == """x
    y
    z
"""
    sc = SphinxContent()
    sc.add_definition_item("a", "\n b\n")
    assert str(sc) == """a
     b
"""


def test_license():
    sc = SphinxContent()
    with pytest.raises(ValueError):
        sc.register_license("x")
    sc.register_license("CC-BY-SA-4.0")
    assert str(sc) == ""
    sc.add_licence_and_copyrights()
    assert str(sc) == """.. SPDX-License-Identifier: CC-BY-SA-4.0

"""


def test_license_and_copyrights():
    sc = SphinxContent()
    with pytest.raises(ValueError):
        sc.register_license("x")
    sc.register_copyright("Copyright (C) A")
    assert str(sc) == ""
    sc.add_licence_and_copyrights()
    assert str(sc) == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) A

"""


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
