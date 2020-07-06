# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsqual.applconfig module. """

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

from rtemsqual.applconfig import generate
from rtemsqual.items import ItemCache
from rtemsqual.tests.util import create_item_cache_config_and_copy_spec


def test_applconfig(tmpdir):
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-applconfig", with_spec_types=True)
    item_cache = ItemCache(item_cache_config)

    applconfig_config = {}
    g_rst = os.path.join(tmpdir, "g.rst")
    applconfig_config["groups"] = [{"uid": "/g", "target": g_rst}]
    generate(applconfig_config, item_cache)

    with open(g_rst, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

group name
==========

description

.. index:: a
.. index:: index a

.. _a:

a
-

CONSTANT:
    ``a``

OPTION TYPE:
    This configuration option is a boolean feature define.

DEFAULT CONFIGURATION:
    default a

DESCRIPTION:
    description a

NOTES:
    notes a

    references:

    * :ref:`b`

    * :ref:`Terminate`

    * ``func()``

    * ``td``

.. index:: b

.. _b:

b
-

CONSTANT:
    ``b``

OPTION TYPE:
    This configuration option is a boolean feature define.

DEFAULT CONFIGURATION:
    If this configuration option is undefined, then the described feature is \
not
    enabled.

DESCRIPTION:
    description b

NOTES:
    None.

.. index:: c

.. _c:

c
-

CONSTANT:
    ``c``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    The default value is 13.

VALUE CONSTRAINTS:
    The value of this configuration option shall satisfy all of the following
    constraints:

    * It shall be greater than or equal to -1.

    * It shall be less than or equal to 99.

    * custom c 1

    * custom c 2

    * constraint d

DESCRIPTION:
    description c

NOTES:
    notes c

.. index:: e

.. _e:

e
-

CONSTANT:
    ``e``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    The default value is 7.

VALUE CONSTRAINTS:
    The value of this configuration option shall be greater than or equal to \
-2.

DESCRIPTION:
    description e

NOTES:
    None.

.. index:: f

.. _f:

f
-

CONSTANT:
    ``f``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    The default value is 1.

VALUE CONSTRAINTS:
    The value of this configuration option shall be less than or equal to 2.

DESCRIPTION:
    description f

NOTES:
    None.

.. index:: h

.. _h:

h
-

CONSTANT:
    ``h``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    The default value is 1.

VALUE CONSTRAINTS:
    custom h

DESCRIPTION:
    description h

NOTES:
    None.

.. index:: i

.. _i:

i
-

CONSTANT:
    ``i``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    The default value is 1.

VALUE CONSTRAINTS:
    The value of this configuration option shall be
    an element of {1, 2, 3}.

DESCRIPTION:
    description i

NOTES:
    None.

.. index:: j

.. _j:

j
-

CONSTANT:
    ``j``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    Foo bar.

VALUE CONSTRAINTS:
    The value of this configuration option shall satisfy all of the following
    constraints:

    * It shall be an element of [1, 2].

    * constraint d

DESCRIPTION:
    description j

NOTES:
    None.

.. index:: k

.. _k:

k
-

CONSTANT:
    ``k``

OPTION TYPE:
    This configuration option is an integer define.

DEFAULT VALUE:
    The default value is 1.

VALUE CONSTRAINTS:
    The value of this configuration option shall satisfy all of the following
    constraints:

    * custom k 1

    * custom k 2

DESCRIPTION:
    description k

NOTES:
    None.

.. index:: l

.. _l:

l
-

CONSTANT:
    ``l``

OPTION TYPE:
    This configuration option is an initializer define.

DEFAULT VALUE:
    The default value is 1.

VALUE CONSTRAINTS:
    The value of this configuration option shall be greater than or equal to 0
    and less than or equal to 2.

DESCRIPTION:
    description l

NOTES:
    None.

.. index:: m

.. _m:

m
-

CONSTANT:
    ``m``

OPTION TYPE:
    This configuration option is an initializer define.

DEFAULT VALUE:
    The default value is 1.

DESCRIPTION:
    description m

NOTES:
    None.
"""
        assert content == src.read()
