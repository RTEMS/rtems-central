# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.specdoc module. """

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

from rtemsspec.items import ItemCache
from rtemsspec.specdoc import document
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_document(tmpdir):
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-doc")
    item_cache_config["spec-type-root-uid"] = "/root"
    item_cache = ItemCache(item_cache_config)
    assert item_cache["/root"].type == "spec"
    doc_target = os.path.join(tmpdir, "items.rst")
    config = {
        "root-type": "/root",
        "doc-target": doc_target,
    }
    document(config, item_cache)
    with open(doc_target, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. _ReqEngSpecificationItems:

Specification Items
===================

.. _ReqEngSpecificationItemHierarchy:

Specification Item Hierarchy
----------------------------

The specification item types have the following hierarchy:

* :ref:`SpecTypeRoot`

  * :ref:`SpecTypeA`

  * :ref:`SpecTypeB`

.. _ReqEngSpecificationItemTypes:

Specification Item Types
------------------------

.. _SpecTypeRoot:

Root
^^^^

A value of this type shall be of one of the following variants:

* The value may be a boolean. A reference to :ref:`SpecTypeRoot`. The value
  shall be true.

* The value may be a set of attributes. All explicit attributes shall be
  specified. The explicit attributes for this type are:

  type
      The attribute value shall be a :ref:`SpecTypeName`.

  In addition to the explicit attributes, generic attributes may be specified.
  Each generic attribute key shall be a :ref:`SpecTypeName`. Each generic
  attribute value shall be a :ref:`SpecTypeRoot`.

* The value may be a floating-point number. The value shall be equal to 0.0.

* The value may be an integer number. The value shall be equal to 0.

* The value may be a list. Each list element shall be a :ref:`SpecTypeRoot`.

* There may by be no value (null).

* The value may be a string. The value

  * shall meet,

    * shall contain an element of

      * "``a``",

      * "``b``", and

      * "``c``",

    * and, shall be equal to "``d``",

    * and, shall be greater than or equal to "``e``",

    * and, shall be greater than "``f``",

    * and, shall be an element of

      * "``g``", and

      * "``h``",

    * and, shall be less than or equal to "``i``",

    * and, shall be less than "``j``",

    * and, shall be not equal to "``k``",

    * and, shall match with the regular expression "``l"``,

    * and, shall be true,

    * and, shall be a valid item UID,

  * or,

    * shall be an element of,

    * or, shall be an element of

      * "``x``",

  * or, shall not meet,

    * shall not contain an element of

      * "``a``",

      * "``b``", and

      * "``c``",

    * or, shall be not equal to "``d``",

    * or, shall be less than "``e``",

    * or, shall be less than or equal to "``f``",

    * or, shall not be an element of

      * "``g``", and

      * "``h``",

    * or, shall be greater than "``i``",

    * or, shall be greater than or equal to "``j``",

    * or, shall be equal to "``k``",

    * or, shall not match with the regular expression "``l"``,

    * or, shall be false,

    * or, shall be an invalid item UID.

This type is refined by the following types:

* :ref:`SpecTypeA`

* :ref:`SpecTypeB`

This type is used by the following types:

* :ref:`SpecTypeRoot`

.. _SpecTypeA:

A
^

This type refines the :ref:`SpecTypeRoot` though the ``type`` attribute if the
value is ``spec``.

The explicit attributes for this type are:

a
    The attribute value shall be an :ref:`SpecTypeA`.

This type is used by the following types:

* :ref:`SpecTypeA`

Please have a look at the following example:

.. code-block:: yaml

    a: null

.. _SpecTypeB:

B
^

This type refines the following types:

* :ref:`SpecTypeD` though the ``d1`` attribute if the value is ``b``

* :ref:`SpecTypeRoot` though the ``type`` attribute if the value is ``b``

Generic attributes may be specified. Each generic attribute key shall be a
:ref:`SpecTypeName`. Each generic attribute value shall be a list. Each list
element shall be a string.

.. _ReqEngSpecificationAttributeSetsAndValueTypes:

Specification Attribute Sets and Value Types
--------------------------------------------

.. _SpecTypeC:

C
^

Only the ``c`` attribute is mandatory. The explicit attributes for this type
are:

c
    The attribute value shall be a floating-point number.

.. _SpecTypeD:

D
^

The following explicit attributes are mandatory:

* ``d1``

* ``d2``

The explicit attributes for this type are:

d1
    The attribute value shall be a :ref:`SpecTypeName`.

d2
    The attribute shall have no value.

This type is refined by the following types:

* :ref:`SpecTypeB`

.. _SpecTypeName:

Name
^^^^

The value shall be a string. A string is a valid name if it matches with the
``^([a-z][a-z0-9-]*|SPDX-License-Identifier)$`` regular expression.

This type is used by the following types:

* :ref:`SpecTypeB`

* :ref:`SpecTypeD`

* :ref:`SpecTypeRoot`

.. _SpecTypeUID:

UID
^^^

The value shall be a string. The string shall be a valid absolute or relative
item UID.
"""
        assert content == src.read()
