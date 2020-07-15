# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.content module. """

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

from rtemsspec.content import Content, enabled_by_to_exp, \
    ExpressionMapper, PythonExpressionMapper


def test_tab():
    content = Content("BSD-2-Clause", True)
    assert content.tab == "  "


def test_append():
    content = Content("BSD-2-Clause", True)
    content.append("")
    assert str(content) == """
"""
    content.append(["a", "b"])
    assert str(content) == """
a
b
"""
    with content.indent():
        content.append(["c", "d"])
        assert str(content) == """
a
b
  c
  d
"""


def test_prepend():
    content = Content("BSD-2-Clause", True)
    content.prepend("")
    assert str(content) == """
"""
    content.prepend(["a", "b"])
    assert str(content) == """a
b

"""
    with content.indent():
        content.prepend(["c", "d"])
        assert str(content) == """  c
  d
a
b

"""


def test_add():
    content = Content("BSD-2-Clause", True)
    content.add("")
    assert str(content) == ""
    content.add("a")
    assert str(content) == """a
"""
    content.add(["b", "c"])
    assert str(content) == """a

b
c
"""


def test_wrap():
    content = Content("BSD-2-Clause", True)
    content.wrap("")
    assert str(content) == ""
    content.wrap("a")
    assert str(content) == """a
"""
    content.wrap(["b", "c"])
    assert str(content) == """a

b c
"""
    content.wrap(content)
    assert str(content) == """a

b c

a

b c
"""
    content = Content("BSD-2-Clause", True)
    content.wrap("\n")
    assert str(content) == ""
    content = Content("BSD-2-Clause", True)
    content.wrap(["a", "", "  b"])
    assert str(content) == """a

  b
"""
    content = Content("BSD-2-Clause", True)
    content.wrap([
        "a", "", "* b",
        "cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff",
        "ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii",
        "jjjjjjjjjjjjjjjjjjj"
    ])
    assert str(content) == """a

* b cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff
  ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii
  jjjjjjjjjjjjjjjjjjj
"""


def test_paste():
    content = Content("BSD-2-Clause", True)
    content.paste("")
    assert str(content) == ""
    content.paste("a")
    assert str(content) == """a
"""
    content.paste(["b", "c"])
    assert str(content) == """a b c
"""
    content.paste(content)
    assert str(content) == """a b c a b c
"""
    content = Content("BSD-2-Clause", True)
    content.paste("\n")
    assert str(content) == ""
    content.append("")
    content.paste("a")
    assert str(content) == """
a
"""
    content = Content("BSD-2-Clause", True)
    content.paste(["a", "b", "", "c"])
    assert str(content) == """a b

c
"""
    content = Content("BSD-2-Clause", True)
    content.paste(["a", "b", "", "  c"])
    assert str(content) == """a b

  c
"""


def test_add_blank_line():
    content = Content("BSD-2-Clause", True)
    content.add_blank_line()
    assert str(content) == """
"""


def test_indent():
    content = Content("BSD-2-Clause", True)
    content.add_blank_line()
    content.append("x")
    content.indent_lines(3)
    assert str(content) == """
      x
"""


def test_write(tmpdir):
    content = Content("BSD-2-Clause", True)
    content.append("x")
    path = os.path.join(tmpdir, "x", "y")
    content.write(path)
    with open(path, "r") as src:
        assert src.read() == """x
"""
    tmpdir.chdir()
    path = "z"
    content.write(path)
    with open(path, "r") as src:
        assert src.read() == """x
"""


def to_c_exp(enabled_by):
    return enabled_by_to_exp(enabled_by, ExpressionMapper())


def test_enabled_by_to_exp():
    assert to_c_exp(True) == "1"
    assert to_c_exp(False) == "0"
    assert to_c_exp([]) == ""
    assert to_c_exp(["A"]) == "defined(A)"
    assert to_c_exp(["B"]) == "defined(B)"
    assert to_c_exp(["A", "B"]) == "defined(A) || defined(B)"
    assert to_c_exp({"not": "A"}) == "!defined(A)"
    assert to_c_exp({"and": ["A", "B"]}) == "defined(A) && defined(B)"
    assert to_c_exp({"and": ["A", "B", {
        "not": "C"
    }]}) == "defined(A) && defined(B) && !defined(C)"
    assert to_c_exp(
        {
            "not": {
                "and":
                ["A",
                 {
                     "not": ["B", "C",
                             {
                                 "and": ["D",
                                         {
                                             "not": "E"
                                         }]
                             }]
                 }]
            }
        }
    ) == "!(defined(A) && !(defined(B) || defined(C) || (defined(D) && !defined(E))))"
    with pytest.raises(KeyError):
        to_c_exp({"foo": "bar"})
    with pytest.raises(ValueError):
        to_c_exp({"foo": "bar", "bla": "blub"})


def to_python_exp(enabled_by):
    return enabled_by_to_exp(enabled_by, PythonExpressionMapper())


def test_enabled_by_to_python_exp():
    assert to_python_exp(True) == "True"
    assert to_python_exp(False) == "False"
    assert to_python_exp([]) == ""
    assert to_python_exp(["A"]) == "A"
    assert to_python_exp(["B"]) == "B"
    assert to_python_exp(["A", "B"]) == "A or B"
    assert to_python_exp({"not": "A"}) == "not A"
    assert to_python_exp({"and": ["A", "B"]}) == "A and B"
    assert to_python_exp({"and": ["A", "B", {
        "not": "C"
    }]}) == "A and B and not C"
    assert to_python_exp({
        "not": {
            "and": ["A", {
                "not": ["B", "C", {
                    "and": ["D", {
                        "not": "E"
                    }]
                }]
            }]
        }
    }) == "not (A and not (B or C or (D and not E)))"
    with pytest.raises(KeyError):
        to_python_exp({"foo": "bar"})
    with pytest.raises(ValueError):
        to_python_exp({"foo": "bar", "bla": "blub"})
