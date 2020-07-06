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

from rtemsqual.content import CContent, CInclude


def test_doxyfy():
    content = CContent()
    content.doxyfy(None)
    assert str(content) == ""
    content.doxyfy(" ")
    assert str(content) == ""
    content.doxyfy([" "])
    assert str(content) == ""
    content.doxyfy(CContent())
    assert str(content) == ""
    content.doxyfy(""".. code-block:: c

    abc

    def

ghi

.. code-block:: c
""")
    assert str(content) == """@code
abc

def
@endcode

ghi

@code
@endcode
"""


def test_add_have_config():
    content = CContent()
    content.add_have_config()
    assert str(content) == """#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
"""
    content.add_have_config()
    assert str(content) == """#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
"""


def test_add_includes():
    assert not CInclude("a") == "a"
    content = CContent()
    content.add_includes([])
    assert str(content) == ""
    content = CContent()
    content.add_includes([CInclude("a"), CInclude("a")])
    assert str(content) == """#include <a>
"""
    content.add_includes([CInclude("b")])
    assert str(content) == """#include <a>

#include <b>
"""
    content = CContent()
    content.add_includes([CInclude("c"), CInclude("b")], local=True)
    assert str(content) == """#include "b"
#include "c"
"""
    content = CContent()
    content.add_includes([CInclude("d/f"), CInclude("d/e")])
    assert str(content) == """#include <d/e>
#include <d/f>
"""
    content = CContent()
    content.add_includes([CInclude("h"), CInclude("g/h")])
    assert str(content) == """#include <h>
#include <g/h>
"""
    content = CContent()
    content.add_includes([CInclude("i/l/k"), CInclude("i/j/k")])
    assert str(content) == """#include <i/j/k>
#include <i/l/k>
"""
    content = CContent()
    content.add_includes([CInclude("a", "X"), CInclude("a")])
    assert str(content) == """#if X
  #include <a>
#endif
"""
    content = CContent()
    content.add_includes([CInclude("a"), CInclude("a", "X")])
    assert str(content) == """#if X
  #include <a>
#endif
"""
    content = CContent()
    content.add_includes([CInclude("a", "X"), CInclude("b", "X")])
    assert str(content) == """#if X
  #include <a>
  #include <b>
#endif
"""
    content = CContent()
    content.add_includes(
        [CInclude("a", "Y"),
         CInclude("a", "X"),
         CInclude("b", "X")])
    assert str(content) == """#if X
  #include <b>
#endif

#if X && Y
  #include <a>
#endif
"""


def test_comment_block():
    content = CContent()
    with content.comment_block():
        assert not content.gap
        content.add("")
        assert not content.gap
        assert str(content) == """/*
"""
        content.add("a")
        assert content.gap
        assert str(content) == """/*
 * a
"""
        content.add("b")
        assert content.gap
        assert str(content) == """/*
 * a
 *
 * b
"""
        content.gap = False
        content.add("c")
        assert content.gap
        assert str(content) == """/*
 * a
 *
 * b
 * c
"""


def test_for_loop():
    content = CContent()
    with content.for_loop("i = 0", "i < 3", "++i"):
        content.add("j[i] = i;")
    assert str(content) == """for ( i = 0; i < 3; ++i ) {
  j[i] = i;
}
"""
    content = CContent()
    with content.for_loop("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii = 0",
                          "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii < 3",
                          "++iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"):
        content.add("j[i] = i;")
    assert str(content) == """for (
  iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii = 0;
  iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii < 3;
  ++iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
) {
  j[i] = i;
}
"""


def test_add_brief_description():
    content = CContent()
    content.add_brief_description("")
    assert str(content) == ""
    content.gap = True
    content.add_brief_description(
        "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT "
        "HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED "
        "WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES "
        "OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE "
        "DISCLAIMED.")
    assert str(content) == """
@brief THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED.
"""


def test_add_param_description():
    content = CContent()
    content.add_param_description([])
    assert str(content) == ""
    params = [{"description": "A", "dir": None, "name": "a"}]
    content.add_param_description(params)
    assert str(content) == """@param a A
"""
    content = CContent()
    params = [
        {
            "description": "A",
            "dir": None,
            "name": "a"
        },
        {
            "description": "B",
            "dir": "in",
            "name": "b"
        },
        {
            "description": "C",
            "dir": "out",
            "name": "c"
        },
        {
            "description": "D",
            "dir": "inout",
            "name": "d"
        },
    ]
    content.add_param_description(params, lambda x: x + x)
    assert str(content) == """@param a AA

@param[in] b BB

@param[out] c CC

@param[in,out] d DD
"""


def test_add_description_block():
    content = CContent()
    content.add_description_block("", None)
    assert str(content) == ""
    content.add_description_block("a", "b")
    assert str(content) == """/**
 * @brief a
 *
 * b
 */
"""
    content = CContent()
    content.add_description_block("a", None)
    assert str(content) == """/**
 * @brief a
 */
"""
    content = CContent()
    content.add_description_block(None, "b")
    assert str(content) == """/**
 * b
 */
"""


def test_add_to_group():
    content = CContent()
    with content.add_to_group("a"):
        content.add("b")
    assert str(content) == """/**
 * @addtogroup a
 *
 * @{
 */

b

/** @} */
"""


def test_function():
    content = CContent()
    content.call_function("a =", "b", [])
    assert str(content) == """a = b();
"""
    content = CContent()
    content.call_function(None, "a", [
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    ])
    assert str(content) == """a(
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
);
"""
    content = CContent()
    content.call_function(
        None,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        [])
    assert str(
        content
    ) == """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa();
"""
    content = CContent()
    content.call_function("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa =",
                          "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", [])
    assert str(content) == """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa =
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb();
"""
    content = CContent()
    content.declare_function("a", "b", [])
    assert str(content) == """a b( void );
"""
    content = CContent()
    content.declare_function("a *", "b", [])
    assert str(content) == """a *b( void );
"""
    content = CContent()
    content.declare_function("a", "b", ["..."])
    assert str(content) == """a b( ... );
"""
    content = CContent()
    content.declare_function("a *", "b", [
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx x",
        "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy y",
        "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz z", "..."
    ])
    assert str(content) == """a *b(
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx x,
  yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy             y,
  zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz          z,
  ...
);
"""
    content = CContent()
    content.declare_function(
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa *",
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", [
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx x",
            "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy *y",
            "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz *( *z )( void )"
        ])
    assert str(content) == """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa *
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb(
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx x,
  yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy            *y,
  zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz      *( *z )( void )
);
"""
    content = CContent()
    content.declare_function("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa *",
                             "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", [])
    assert str(content) == """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa *
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb( void );
"""
    content = CContent()
    with content.function("a", "b", []):
        content.add("c")
    assert str(content) == """a b( void )
{
  c
}
"""


def test_condition():
    content = CContent()
    with content.condition("a"):
        content.add("b")
    assert str(content) == """if ( a ) {
  b
}
"""
    content = CContent()
    with content.first_condition("a"):
        content.add("b")
    with content.next_condition("c"):
        content.add("d")
    with content.final_condition(None):
        content.add("e")
    assert str(content) == """if ( a ) {
  b
} else if ( c ) {
  d
} else {
  e
}
"""


def test_prepend_copyrights_and_licenses():
    content = CContent()
    content.add("x")
    assert str(content) == """x
"""
    content.register_copyright("Copyright (C) 1234 Foo Bar")
    content.prepend_copyrights_and_licenses()
    content.prepend_spdx_license_identifier()
    assert str(content) == """/* SPDX-License-Identifier: BSD-2-Clause */

/*
 * Copyright (C) 1234 Foo Bar
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

x
"""
