# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.sphinxcontent module. """

# Copyright (C) 2020, 2021 embedded brains GmbH (http://www.embedded-brains.de)
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

from rtemsspec.sphinxcontent import get_reference, get_label, \
    SphinxContent, SphinxMapper
from rtemsspec.items import Item, ItemCache, ItemMapper
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_add_label():
    content = SphinxContent()
    content.add_label("x")
    assert str(content) == """.. _x:
"""


def test_directive():
    content = SphinxContent()
    with content.directive("x"):
        content.add("y")
        assert str(content) == """.. x::

    y
"""
    with content.directive("z", "xy", [":a:", ":b:"]):
        content.add("c")
        assert str(content) == """.. x::

    y

.. z:: xy
    :a:
    :b:

    c
"""


def test_add_header():
    content = SphinxContent()
    content.add_header("x")
    assert str(content) == """x
=
"""
    content.add_header("yz", 1)
    assert str(content) == """x
=

yz
**
"""


def test_add_header_with_label():
    content = SphinxContent()
    label = content.add_header_with_label("x", 1)
    assert label == "SectionX"
    assert str(content) == """.. _SectionX:

x
*
"""
    label = content.add_header_with_label("yz w", 2)
    assert label == "SectionYzW"
    assert str(content) == """.. _SectionX:

x
*

.. _SectionYzW:

yz w
====
"""


def test_get_reference():
    assert get_reference("a") == ":ref:`a`"
    assert get_reference("a", "b") == ":ref:`b <a>`"


def test_get_label():
    assert get_label("ab cd") == "AbCd"


def test_section():
    content = SphinxContent()
    with content.section("ab cd") as label:
        content.add(label)
        with content.section("ef gh") as label2:
            content.add(label2)
    assert str(content) == """.. _SectionAbCd:

ab cd
=====

SectionAbCd

.. _SectionEfGh:

ef gh
-----

SectionEfGh
"""


def test_list_item():
    content = SphinxContent()
    with content.list_item("ab cd"):
        content.paste("ef gh")
        with content.list_item("ij kl"):
            content.add("mn op")
        content.paste("qr st")
    with content.list_item("uv"):
        pass
    content.add_list_item("wx")
    assert str(content) == """* ab cd ef gh

  * ij kl

  mn op qr st

* uv

* wx
"""


def test_add_list():
    content = SphinxContent()
    content.add_list([], "a")
    assert str(content) == ""
    content.add_list(["b", "c"], "a", "d")
    assert str(content) == """a

* b

* c

d
"""
    content = SphinxContent()
    content.add_list(["b", "c"], add_blank_line=True)
    assert str(content) == """* b

* c

"""


def test_append():
    content = SphinxContent()
    content.append("x")
    assert str(content) == """x
"""
    with content.indent():
        content.append("y")
        assert str(content) == """x
    y
"""
        content.append("")
        assert str(content) == """x
    y

"""


def test_add_index_entries():
    content = SphinxContent()
    content.add_index_entries(["x", "y"])
    assert str(content) == """.. index:: x
.. index:: y
"""
    content.add_index_entries("z")
    assert str(content) == """.. index:: x
.. index:: y

.. index:: z
"""


def test_add_definition_item():
    content = SphinxContent()
    content.add_definition_item("x", ["y", "z"])
    assert str(content) == """x
    y
    z
"""
    content = SphinxContent()
    content.add_definition_item("a", "\n b\n")
    assert str(content) == """a
     b
"""
    content = SphinxContent()
    content.add_definition_item("a", "\n b\nc", wrap=True)
    assert str(content) == """a
    b c
"""


def test_definition_item():
    content = SphinxContent()
    with content.definition_item("x"):
        content.add(["y", "z"])
    assert str(content) == """x
    y
    z
"""


def test_license():
    content = SphinxContent()
    with pytest.raises(ValueError):
        content.register_license("x")
    content.register_license("CC-BY-SA-4.0")
    assert str(content) == ""
    content.add_licence_and_copyrights()
    assert str(content) == """.. SPDX-License-Identifier: CC-BY-SA-4.0

"""


def test_license_and_copyrights():
    content = SphinxContent()
    with pytest.raises(ValueError):
        content.register_license("x")
    content.register_copyright("Copyright (C) A")
    assert str(content) == ""
    content.add_licence_and_copyrights()
    assert str(content) == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) A

"""


def test_comment():
    content = SphinxContent()
    with content.comment_block():
        content.add(["abc", "", "def"])
    assert str(content) == """.. abc
..
.. def
"""


def test_simple_table():
    content = SphinxContent()
    content.add_simple_table([])
    assert str(content) == ""
    content.add_simple_table([["a", "b"], ["cc", "ddd"]])
    assert str(content) == """.. table::
    :class: longtable

    == ===
    a  b
    == ===
    cc ddd
    == ===
"""


def test_substitute(tmpdir):
    config = create_item_cache_config_and_copy_spec(tmpdir,
                                                    "spec-sphinx",
                                                    with_spec_types=True)
    item_cache = ItemCache(config)
    mapper = SphinxMapper(item_cache["/x"])
    match = r"substitution for spec:/x using prefix '' failed for text: \${x:/y}"
    with pytest.raises(ValueError, match=match):
        mapper.substitute("${x:/y}")
    assert mapper.substitute("${x:/term}") == ":term:`y`"
    assert mapper.substitute("${x:/plural}") == ":term:`ies <y>`"
    assert mapper.substitute("${z:/plural}") == ":term:`zs <z>`"
    mapper.add_get_value("other:/name", lambda ctx: ctx.value[ctx.key])
    assert mapper.substitute("${y:/name}") == "foobar"
    assert mapper.substitute("${a:/name}") == ":c:data:`a`"
    assert mapper.substitute("${f:/name}") == ":c:func:`f`"
