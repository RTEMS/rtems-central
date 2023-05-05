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
    config = {"enabled": [], "groups": [doc_config, doc_config_2]}
    generate(config, ItemCache(item_cache_config))

    with open(introduction_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. This file is part of the RTEMS quality process and was automatically
.. generated.  If you find something that needs to be fixed or
.. worded better please post a report or patch to an RTEMS mailing list
.. or raise a bug report:
..
.. https://www.rtems.org/bugs.html
..
.. For information on updating and regenerating please refer to the How-To
.. section in the Software Requirements Engineering chapter of the
.. RTEMS Software Engineering manual.  The manual is provided as a part of
.. a release.  For development sources please refer to the online
.. documentation at:
..
.. https://docs.rtems.org

.. Generated from spec:/gb

.. _GroupBIntroduction:

Introduction
============

.. The following list was generated from:
.. spec:/func4
.. spec:/func2
.. spec:/func3
.. spec:/macro
.. spec:/macro2
.. spec:/macro3

The directives provided by the Group B are:

* :ref:`InterfaceVeryLongTypeFunction` - Function brief description with very
  long return type.

* :ref:`InterfaceVeryLongFunction` - Very long function brief description.

* :ref:`InterfaceVoidFunction`

* :ref:`InterfaceVERYLONGMACRO` - Very long macro brief description.

* :ref:`InterfaceMACRO` - Short macro brief description.

* :ref:`InterfaceMACRO` - Macro without parameters.
"""
        assert content == src.read()

    with open(directives_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. This file is part of the RTEMS quality process and was automatically
.. generated.  If you find something that needs to be fixed or
.. worded better please post a report or patch to an RTEMS mailing list
.. or raise a bug report:
..
.. https://www.rtems.org/bugs.html
..
.. For information on updating and regenerating please refer to the How-To
.. section in the Software Requirements Engineering chapter of the
.. RTEMS Software Engineering manual.  The manual is provided as a part of
.. a release.  For development sources please refer to the online
.. documentation at:
..
.. https://docs.rtems.org

.. _GroupBDirectives:

Directives
==========

This section details the directives of the Group B. A subsection is dedicated
to each of this manager's directives and lists the calling sequence,
parameters, description, return values, and notes of the directive.

.. Generated from spec:/func4

.. raw:: latex

    \\clearpage

.. index:: VeryLongTypeFunction()

.. _InterfaceVeryLongTypeFunction:

VeryLongTypeFunction()
----------------------

Function brief description with very long return type.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    VeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongType
    VeryLongTypeFunction( void );

.. rubric:: DESCRIPTION:

I am defined in ``<h4.h>``.

.. rubric:: RETURN VALUES:

This function returns an object with a very long type.

.. rubric:: NOTES:

See also :c:func:`Func5`.

.. Generated from spec:/func2

.. raw:: latex

    \\clearpage

.. index:: VeryLongFunction()

.. _InterfaceVeryLongFunction:

VeryLongFunction()
------------------

Very long function brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    int VeryLongFunction(
      int                  VeryLongParam0,
      const struct Struct *VeryLongParam1,
      Union            *( *VeryLongParam2 )( void ),
      struct Struct       *VeryLongParam3
    );

.. rubric:: PARAMETERS:

``VeryLongParam0``
    This parameter is very long parameter 0 with some super important and extra
    very long description which makes a lot of sense.

``VeryLongParam1``
    This parameter is very long parameter 1.

``VeryLongParam2``
    This parameter is very long parameter 2.

``VeryLongParam3``
    This parameter is very long parameter 3.

.. rubric:: DESCRIPTION:

VeryLongFunction description.

.. rubric:: RETURN VALUES:

``1``
    is returned, in case A.

``2``
    is returned, in case B.

:c:type:`Enum`
    is returned, in case C.

Sometimes some value.  See :ref:`InterfaceFunction`.

.. rubric:: NOTES:

VeryLongFunction notes.

.. Generated from spec:/func3

.. raw:: latex

    \\clearpage

.. index:: VoidFunction()

.. _InterfaceVoidFunction:

VoidFunction()
--------------

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    void VoidFunction( void );

.. Generated from spec:/macro

.. raw:: latex

    \\clearpage

.. index:: VERY_LONG_MACRO()

.. _InterfaceVERYLONGMACRO:

VERY_LONG_MACRO()
-----------------

Very long macro brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    VERY_LONG_MACRO(
      VeryLongParam0,
      VeryLongParam1,
      VeryLongParam2,
      VeryLongParam3
    );

.. rubric:: PARAMETERS:

``VeryLongParam0``
    This parameter is very long parameter 0 with some super important and extra
    very long description which makes a lot of sense.

``VeryLongParam1``
    This parameter is very long parameter 1.

``VeryLongParam2``
    This parameter is very long parameter 2.

``VeryLongParam3``
    This parameter is very long parameter 3.

.. rubric:: RETURN VALUES:

``1``
    is returned, in case A.

``2``
    is returned, in case B.

Sometimes some value.

.. Generated from spec:/macro2

.. raw:: latex

    \\clearpage

.. index:: MACRO()

.. _InterfaceMACRO:

MACRO()
-------

Short macro brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    MACRO( Param0 );

.. rubric:: PARAMETERS:

``Param0``
    This parameter is parameter 0.

.. rubric:: RETURN VALUES:

Sometimes some value.

.. Generated from spec:/macro3

.. raw:: latex

    \\clearpage

.. index:: MACRO()

.. _InterfaceMACRO:

MACRO()
-------

Macro without parameters.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    MACRO( void );
"""
        assert content == src.read()

    with open(introduction_2_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. This file is part of the RTEMS quality process and was automatically
.. generated.  If you find something that needs to be fixed or
.. worded better please post a report or patch to an RTEMS mailing list
.. or raise a bug report:
..
.. https://www.rtems.org/bugs.html
..
.. For information on updating and regenerating please refer to the How-To
.. section in the Software Requirements Engineering chapter of the
.. RTEMS Software Engineering manual.  The manual is provided as a part of
.. a release.  For development sources please refer to the online
.. documentation at:
..
.. https://docs.rtems.org

.. Generated from spec:/ga

.. _GroupAIntroduction:

Introduction
============

.. The following list was generated from:
.. spec:/func

Group A brief description.

Group A description. The directives provided by the Group A are:

* :ref:`InterfaceFunction` - Function brief description.
"""
        assert content == src.read()

    with open(directives_2_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. This file is part of the RTEMS quality process and was automatically
.. generated.  If you find something that needs to be fixed or
.. worded better please post a report or patch to an RTEMS mailing list
.. or raise a bug report:
..
.. https://www.rtems.org/bugs.html
..
.. For information on updating and regenerating please refer to the How-To
.. section in the Software Requirements Engineering chapter of the
.. RTEMS Software Engineering manual.  The manual is provided as a part of
.. a release.  For development sources please refer to the online
.. documentation at:
..
.. https://docs.rtems.org

.. _GroupADirectives:

Directives
==========

This section details the directives of the Group A. A subsection is dedicated
to each of this manager's directives and lists the calling sequence,
parameters, description, return values, and notes of the directive.

.. Generated from spec:/func

.. raw:: latex

    \\clearpage

.. index:: Function()

.. _InterfaceFunction:

Function()
----------

Function brief description.

.. rubric:: CALLING SEQUENCE:

.. code-block:: c

    void Function(
      int        Param0,
      const int *Param1,
      int       *Param2,
      int       *Param3,
      int       *Param4
    );

.. rubric:: PARAMETERS:

``Param0``
    This parameter is parameter 0.

``Param1``
    This parameter is parameter 1.

``Param2``
    This parameter is parameter 2.

``Param3``
    This parameter is parameter 3.

.. rubric:: DESCRIPTION:

Function description.  References to :term:`xs <x>`,
:ref:`InterfaceVeryLongFunction`, :c:type:`Integer`, :c:type:`Enum`,
:c:macro:`DEFINE`, :ref:`InterfaceVERYLONGMACRO`, Variable,
:c:macro:`ENUMERATOR_0`, ``struct Struct``, :ref:`a`, interface, :ref:`GroupA`,
and Group F.  Second parameter is ``Param1``. Mention :c:type:`US`.

.. code-block:

    these two lines
    are not wrapped

.. rubric:: CONSTRAINTS:

The following constraints apply to this directive:

* Constraint A for :ref:`InterfaceFunction`.
"""
        assert content == src.read()
