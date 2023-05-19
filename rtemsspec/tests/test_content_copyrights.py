# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.content module. """

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

import pytest

from rtemsspec.content import Copyright
from rtemsspec.content import Copyrights


def test_copyright_get_statement():
    c = Copyright("John Doe")
    assert "Copyright (C) John Doe" == c.get_statement()
    c.add_year("3")
    assert "Copyright (C) 3 John Doe" == c.get_statement()
    c.add_year("3")
    assert "Copyright (C) 3 John Doe" == c.get_statement()
    c.add_year("5")
    assert "Copyright (C) 3, 5 John Doe" == c.get_statement()
    c.add_year("4")
    assert "Copyright (C) 3, 5 John Doe" == c.get_statement()
    c.add_year("2")
    assert "Copyright (C) 2, 5 John Doe" == c.get_statement()


def test_copyright_lt():
    a = Copyright("A")
    b = Copyright("B")
    c = Copyright("C")
    assert b < a
    assert c < a
    assert c < b
    b.add_year("1")
    assert b < c
    a.add_year("2")
    assert a < b


def test_copyrights_register():
    c = Copyrights()
    with pytest.raises(ValueError):
        c.register("abc")
    c.register("Copyright (C) A")
    c.register("Copyright (C) 2 A")
    c.register("Copyright (C) 2, 3 A")
    c.register("Copyright (C) D")
    c.register("Copyright (C) 1 D")
    c.register("Copyright (C) 1, 4 D")
    c.register("Copyright (C) C")
    c.register("Copyright (C) 1 B")
    s = c.get_statements()
    assert 4 == len(s)
    assert "Copyright (C) C" == s[0]
    assert "Copyright (C) 2, 3 A" == s[1]
    assert "Copyright (C) 1, 4 D" == s[2]
    assert "Copyright (C) 1 B" == s[3]
