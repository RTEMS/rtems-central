# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsqual.specdoc module. """

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

from rtemsqual.items import ItemCache
from rtemsqual.specdoc import document
from rtemsqual.tests.util import create_item_cache_config_and_copy_spec


def test_document(tmpdir):
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-doc")
    item_cache = ItemCache(item_cache_config)
    doc_target = os.path.join(tmpdir, "items.rst")
    config = {
        "root-type": "/root",
        "doc-target": doc_target,
    }
    document(config, item_cache)
    with open(doc_target, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

.. _SectionSpecificationItems:

Specification Items
===================

.. _SectionSpecificationItemHierarchy:

Specification Item Hierarchy
----------------------------

The specification item types have the following hierarchy:

* :ref:`SpecTypeRoot`

  * :ref:`SpecTypeA`

  * :ref:`SpecTypeB`

.. _SectionSpecificationItemTypes:

Specification Item Types
------------------------

.. _SpecTypeRoot:

Root
^^^^

A value of this type shall be of one of the following variants:

* The value may be a boolean.

* The value may be a set of attributes. All explicitly defined attributes shall
  be specified. The following attributes are explicitly defined for this type:

  type
      The attribute value shall be a :ref:`SpecTypeName`.

  In addition to the explicitly defined attributes above, generic attributes
  may be defined. Each attribute key shall be a :ref:`SpecTypeName`. The
  generic attribute value shall be a :ref:`SpecTypeRoot`.

* The value may be a floating-point number.

* The value may be an integer number.

* The value may be a list. Each list element shall be a :ref:`SpecTypeRoot`.

* There may by be no value (null).

* The value may be a string.

This type is refined by the following types:

* :ref:`SpecTypeA`

* :ref:`SpecTypeB`

This type is used by the following types:

* :ref:`SpecTypeRoot`

.. _SpecTypeA:

A
^

This type refines the :ref:`SpecTypeRoot` though the ``type`` attribute if the
value is ``a``.

The following attributes are explicitly defined for this type:

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

Generic attributes may be defined. Each attribute key shall be a
:ref:`SpecTypeName`. The value shall be a list. Each list element shall be a
string.

.. _SectionSpecificationAttributeSetsAndValueTypes:

Specification Attribute Sets and Value Types
--------------------------------------------

.. _SpecTypeC:

C
^

Only the ``c`` attribute is required. The following attributes are explicitly
defined for this type:

c
    The attribute value shall be a floating-point number.

.. _SpecTypeD:

D
^

The following explicitly defined attributes are required:

* ``d1``

* ``d2``

The following attributes are explicitly defined for this type:

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

* :ref:`SpecTypeD`

* :ref:`SpecTypeRoot`

.. _SpecTypeUID:

UID
^^^

The value shall be a string. The string shall be a valid absolute or relative
item UID.
"""
        assert content == src.read()
