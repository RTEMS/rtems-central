# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.applconfig module. """

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

from rtemsspec.applconfig import generate
from rtemsspec.items import ItemCache
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_applconfig(tmpdir):
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-applconfig", with_spec_types=True)
    item_cache = ItemCache(item_cache_config)

    applconfig_config = {}
    g_rst = os.path.join(tmpdir, "g.rst")
    applconfig_config["groups"] = [{"uid": "/g", "target": g_rst}]
    doxygen_h = os.path.join(tmpdir, "doxygen.h")
    applconfig_config["doxygen-target"] = doxygen_h
    generate(applconfig_config, item_cache)

    with open(g_rst, "r") as src:
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

.. Generated from spec:/g

group name
==========

description

.. Generated from spec:/a

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

    * :c:func:`func`

    * :c:type:`td`

    * :c:macro:`DEFINE`

    * :ref:`UNSPEC_DEFINE <SphinxRefTarget>`

    * `UNSPEC_DEFINE_2 <https://foo>`_

    * :c:type:`unspec_type`

    * `unspec_type_2 <https://bar>`_

.. Generated from spec:/b

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

.. Generated from spec:/c

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

.. Generated from spec:/e

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

.. Generated from spec:/f

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

.. Generated from spec:/h

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

.. Generated from spec:/i

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

.. Generated from spec:/j

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

.. Generated from spec:/k

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

.. Generated from spec:/l

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

.. Generated from spec:/m

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
    with open(doxygen_h, "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/*
 * Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
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

/*
 * This file is part of the RTEMS quality process and was automatically
 * generated.  If you find something that needs to be fixed or
 * worded better please post a report or patch to an RTEMS mailing list
 * or raise a bug report:
 *
 * https://www.rtems.org/bugs.html
 *
 * For information on updating and regenerating please refer to the How-To
 * section in the Software Requirements Engineering chapter of the
 * RTEMS Software Engineering manual.  The manual is provided as a part of
 * a release.  For development sources please refer to the online
 * documentation at:
 *
 * https://docs.rtems.org
 */

/**
 * @defgroup RTEMSApplConfig Application Configuration Options
 *
 * @ingroup RTEMSAPI
 */

/* Generated from spec:/g */

/**
 * @defgroup RTEMSApplConfiggroupname group name
 *
 * @ingroup RTEMSApplConfig
 *
 * description
 *
 * @{
 */

/* Generated from spec:/a */

/**
 * @brief This configuration option is a boolean feature define.
 *
 * description a
 *
 * @par Default Configuration
 * default a
 *
 * @par Notes
 * @parblock
 * notes a
 *
 * references:
 *
 * * #b
 *
 * * <a
 *   href=https://docs.rtems.org/branches/master/c-user/fatal_error.html#announcing-a-fatal-error>Announcing
 *   a Fatal Error</a>
 *
 * * func()
 *
 * * ::td
 *
 * * #DEFINE
 *
 * * #UNSPEC_DEFINE
 *
 * * <a href="https://foo">UNSPEC_DEFINE_2</a>
 *
 * * ::unspec_type
 *
 * * <a href="https://bar">unspec_type_2</a>
 * @endparblock
 */
#define a

/* Generated from spec:/b */

/**
 * @brief This configuration option is a boolean feature define.
 *
 * description b
 *
 * @par Default Configuration
 * If this configuration option is undefined, then the described feature is not
 * enabled.
 */
#define b

/* Generated from spec:/c */

/**
 * @brief This configuration option is an integer define.
 *
 * description c
 *
 * @par Default Value
 * The default value is 13.
 *
 * @par Value Constraints
 * @parblock
 * The value of this configuration option shall satisfy all of the following
 * constraints:
 *
 * * It shall be greater than or equal to -1.
 *
 * * It shall be less than or equal to 99.
 *
 * * custom c 1
 *
 * * custom c 2
 *
 * * constraint d
 * @endparblock
 *
 * @par Notes
 * notes c
 */
#define c

/* Generated from spec:/e */

/**
 * @brief This configuration option is an integer define.
 *
 * description e
 *
 * @par Default Value
 * The default value is 7.
 *
 * @par Value Constraints
 * The value of this configuration option shall be greater than or equal to -2.
 */
#define e

/* Generated from spec:/f */

/**
 * @brief This configuration option is an integer define.
 *
 * description f
 *
 * @par Default Value
 * The default value is 1.
 *
 * @par Value Constraints
 * The value of this configuration option shall be less than or equal to 2.
 */
#define f

/* Generated from spec:/h */

/**
 * @brief This configuration option is an integer define.
 *
 * description h
 *
 * @par Default Value
 * The default value is 1.
 *
 * @par Value Constraints
 * custom h
 */
#define h

/* Generated from spec:/i */

/**
 * @brief This configuration option is an integer define.
 *
 * description i
 *
 * @par Default Value
 * The default value is 1.
 *
 * @par Value Constraints
 * The value of this configuration option shall be an element of {1, 2, 3}.
 */
#define i

/* Generated from spec:/j */

/**
 * @brief This configuration option is an integer define.
 *
 * description j
 *
 * @par Default Value
 * Foo bar.
 *
 * @par Value Constraints
 * @parblock
 * The value of this configuration option shall satisfy all of the following
 * constraints:
 *
 * * It shall be an element of [1, 2].
 *
 * * constraint d
 * @endparblock
 */
#define j

/* Generated from spec:/k */

/**
 * @brief This configuration option is an integer define.
 *
 * description k
 *
 * @par Default Value
 * The default value is 1.
 *
 * @par Value Constraints
 * @parblock
 * The value of this configuration option shall satisfy all of the following
 * constraints:
 *
 * * custom k 1
 *
 * * custom k 2
 * @endparblock
 */
#define k

/* Generated from spec:/l */

/**
 * @brief This configuration option is an initializer define.
 *
 * description l
 *
 * @par Default Value
 * The default value is 1.
 *
 * @par Value Constraints
 * The value of this configuration option shall be greater than or equal to 0
 * and less than or equal to 2.
 */
#define l

/* Generated from spec:/m */

/**
 * @brief This configuration option is an initializer define.
 *
 * description m
 *
 * @par Default Value
 * The default value is 1.
 */
#define m

/** @} */
"""
        assert content == src.read()
