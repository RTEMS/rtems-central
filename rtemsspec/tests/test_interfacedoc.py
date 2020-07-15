# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.interfacedoc module. """

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

from rtemsspec.interfacedoc import generate
from rtemsspec.items import EmptyItemCache, ItemCache
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_interfacedoc(tmpdir):
    doc_config = {}
    doc_config["group"] = "/gb"
    introduction_rst = os.path.join(tmpdir, "introduction.rst")
    doc_config["introduction-target"] = introduction_rst
    directives_rst = os.path.join(tmpdir, "directives.rst")
    doc_config["directives-target"] = directives_rst

    doc_config_2 = {}
    doc_config_2["group"] = "/ga"
    introduction_2_rst = os.path.join(tmpdir, "introduction-2.rst")
    doc_config_2["introduction-target"] = introduction_2_rst
    directives_2_rst = os.path.join(tmpdir, "directives-2.rst")
    doc_config_2["directives-target"] = directives_2_rst

    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-interface", with_spec_types=True)
    generate([doc_config, doc_config_2], ItemCache(item_cache_config))

    with open(introduction_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. _GroupBIntroduction:

Introduction
============

The directives provided by the Group B are:

* :ref:`VeryLongFunction() <InterfaceVeryLongFunction>` - Very long function
  brief description.

* :ref:`VeryLongTypeFunction() <InterfaceVeryLongTypeFunction>` - Function
  brief description with very long return type.

* :ref:`VoidFunction() <InterfaceVoidFunction>`
"""
        assert content == src.read()

    with open(directives_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. _GroupBDirectives:

Directives
==========

.. _InterfaceVeryLongFunction:

VeryLongFunction()
------------------

Very long function brief description.

CALLING SEQUENCE:
    .. code-block:: c

        int VeryLongFunction(
          int                  VeryLongParam0,
          const struct Struct *VeryLongParam1,
          struct Struct    *( *VeryLongParam2 )( void ),
          struct Struct       *VeryLongParam3
        );

DIRECTIVE PARAMETERS:
    VeryLongParam0
        This parameter is very long parameter 0 with some super important and
        extra very long description which makes a lot of sense.

    VeryLongParam1
        This parameter is very long parameter 1.

    VeryLongParam2
        This parameter is very long parameter 2.

    VeryLongParam3
        This parameter is very long parameter 3.

DIRECTIVE RETURN VALUES:
    1
        is returned, in case A.

    2
        is returned, in case B.

    Sometimes some value.  See :ref:`Function() <InterfaceFunction>`.

DESCRIPTION:
    VeryLongFunction description.

NOTES:
    VeryLongFunction notes.

.. _InterfaceVeryLongTypeFunction:

VeryLongTypeFunction()
----------------------

Function brief description with very long return type.

CALLING SEQUENCE:
    .. code-block:: c

        #if 1
          NotSoVeryLongType VeryLongTypeFunction( void );
        #else
          VeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongType
          VeryLongTypeFunction( void );
        #endif

DIRECTIVE RETURN VALUES:
    This function returns an object with a very long type.

.. _InterfaceVoidFunction:

VoidFunction()
--------------

CALLING SEQUENCE:
    .. code-block:: c

        #if 1
          void VoidFunction( void );
        #endif
"""
        assert content == src.read()

    with open(introduction_2_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. _GroupAIntroduction:

Introduction
============

Group A brief description.

Group A description. The directives provided by the Group A are:

* :ref:`Function() <InterfaceFunction>` - Function brief description.
"""
        assert content == src.read()

    with open(directives_2_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. _GroupADirectives:

Directives
==========

.. _InterfaceFunction:

Function()
----------

Function brief description.

CALLING SEQUENCE:
    .. code-block:: c

        void Function( int Param0, const int *Param1, int *Param2, int *Param3 );

DIRECTIVE PARAMETERS:
    Param0
        This parameter is parameter 0.

    Param1
        This parameter is parameter 1.

    Param2
        This parameter is parameter 2.

    Param3
        This parameter is parameter 3.

DESCRIPTION:
    Function description.  References to :ref:`VeryLongFunction()
    <InterfaceVeryLongFunction>`, Integer, Enum, DEFINE, VERY_LONG_MACRO,
    Variable, ENUMERATOR_0, Struct, :ref:`a`, and interface.
"""
        assert content == src.read()
