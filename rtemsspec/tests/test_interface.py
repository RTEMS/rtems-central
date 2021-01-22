# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.interface module. """

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

from rtemsspec.interface import generate
from rtemsspec.items import EmptyItemCache, ItemCache
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_interface(tmpdir):
    interface_config = {}
    interface_config["item-level-interfaces"] = []
    base_directory = os.path.join(tmpdir, "base")
    interface_domains = {"/domain-abc": base_directory}
    interface_config["domains"] = interface_domains

    generate(interface_config, EmptyItemCache())

    interface_config["item-level-interfaces"] = ["/command-line"]

    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-interface", with_spec_types=True)
    generate(interface_config, ItemCache(item_cache_config))

    with open(os.path.join(base_directory, "include", "h.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup GroupA
 * @ingroup GroupB
 * @ingroup GroupC
 *
 * @brief This header file defines X.
 */

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

/* Generated from spec:/h */

#ifndef _H_H
#define _H_H

#include <h3.h>
#include <math.h>
#include <stdint.h>

#if !defined(ASM) && defined(RTEMS_SMP)
  #include <h2.h>
#endif

#if defined(ASM) && defined(RTEMS_SMP)
  #include <h4.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Generated from spec:/ga */

/**
 * @defgroup GroupA Group A
 *
 * @brief Group A brief description.
 *
 * Group A description.
 */

/* Generated from spec:/gb */

/**
 * @defgroup GroupB Group B
 *
 * @ingroup GroupA
 */

/* Generated from spec:/define */

/**
 * @ingroup GroupA
 */
#if defined(A) || (B > C)
  #define DEFINE ((float_t) 456)
#elif defined(C) && defined(D)
  #define DEFINE ((float_t) 789)
#else
  #define DEFINE \\
    ((float_t) 123)
#endif

/* Generated from spec:/forward-decl */

/* Forward declaration */
struct Struct;

/* Generated from spec:/enum */

/**
 * @ingroup GroupB
 *
 * @brief Enum brief description.
 *
 * Enum description.
 */
typedef enum {
  /**
   * @brief Enumerator 0 brief description.
   */
  ENUMERATOR_0,

  /**
   * @brief Enumerator 1 brief description.
   */
  ENUMERATOR_1,

  /**
   * @brief Enumerator 2 brief description.
   */
  ENUMERATOR_2
} Enum;

/* Generated from spec:/enum3 */

/**
 * @ingroup GroupB
 *
 * @brief Enum B brief description.
 */
typedef enum EnumB {
  /**
   * @brief Enumerator B brief description.
   */
  ENUMERATOR_B = ENUMERATOR_A
} EnumB;

/* Generated from spec:/func */

/**
 * @ingroup GroupA
 *
 * @brief Function brief description.
 *
 * @param Param0 is parameter 0.
 *
 * @param[in] Param1 is parameter 1.
 *
 * @param[out] Param2 is parameter 2.
 *
 * @param[in,out] Param3 is parameter 3.
 *
 * Function description.  References to VeryLongFunction(), ::Integer, #Enum,
 * #DEFINE, VERY_LONG_MACRO(), #Variable, ::ENUMERATOR_0, Struct, #a,
 * interface, @ref GroupA, and @ref GroupF.  Second parameter is ``Param1``.
 *
 * @code
 * these two lines
 * are not wrapped
 * @endcode
 */
void Function( int Param0, const int *Param1, int *Param2, int *Param3 );

/* Generated from spec:/macro */

/**
 * @ingroup GroupB
 *
 * @brief Very long macro brief description.
 *
 * @param VeryLongParam0 is very long parameter 0 with some super important and
 *   extra very long description which makes a lot of sense.
 *
 * @param[in] VeryLongParam1 is very long parameter 1.
 *
 * @param[out] VeryLongParam2 is very long parameter 2.
 *
 * @param[in,out] VeryLongParam3 is very long parameter 3.
 *
 * @retval 1 is returned, in case A.
 *
 * @retval 2 is returned, in case B.
 *
 * @return Sometimes some value.
 */
#define VERY_LONG_MACRO( \\
  VeryLongParam0, \\
  VeryLongParam1, \\
  VeryLongParam2, \\
  VeryLongParam3 \\
) \\
  do { \\
    (void) VeryLongParam1; \\
    (void) VeryLongParam2; \\
    (void) VeryLongParam3; \\
  } while ( 0 ); \\
  VeryLongParam0 + 1;

/* Generated from spec:/macro2 */

/**
 * @ingroup GroupB
 *
 * @brief Short macro brief description.
 *
 * @param Param0 is parameter 0.
 *
 * @return Sometimes some value.
 */
#if 0
  #define MACRO( Param0 )
#else
  #define MACRO( Param0 ) ( ( Param0 ) + 1 )
#endif

/* Generated from spec:/s */

/**
 * @ingroup GroupC
 */
struct Struct {
  /**
   * @brief Brief union description.
   *
   * Union description.
   */
  union {
    /**
     * @brief Brief member description.
     *
     * Member description.
     */
    uint32_t some_member;

    /**
     * @brief Brief struct description.
     *
     * struct description.
     */
    struct {
      /**
       * @brief Brief member 2 description.
       *
       * Member 2 description.
       */
      uint32_t some_member_2;

      /**
       * @brief Brief member 3 description.
       *
       * Member 3 description.
       */
      Enum some_member_3;
    } some_struct;
  } some_union;

  /**
   * @brief Brief member 4 description.
   *
   * Member 4 description.
   */
  Enum some_member_4;
};

/* Generated from spec:/td */

/**
 * @ingroup GroupB
 *
 * @brief Typedef Integer brief description.
 *
 * Typedef Integer description.
 */
typedef uint32_t Integer /* Some comment. */;

/* Generated from spec:/td3 */

/**
 * @ingroup GroupB
 */
#if defined(RTEMS_SMP)
  typedef uint32_t Integer3;
#endif

#if !defined(ASM)
  /* Generated from spec:/var */

  /**
   * @ingroup GroupC
   *
   * @brief Variable brief description.
   *
   * Variable description.
   */
  extern struct Struct *Variable;
#endif

/* Generated from spec:/func2 */

/**
 * @ingroup GroupB
 *
 * @brief Very long function brief description.
 *
 * @param VeryLongParam0 is very long parameter 0 with some super important and
 *   extra very long description which makes a lot of sense.
 *
 * @param[in] VeryLongParam1 is very long parameter 1.
 *
 * @param[out] VeryLongParam2 is very long parameter 2.
 *
 * @param[in,out] VeryLongParam3 is very long parameter 3.
 *
 * VeryLongFunction description.
 *
 * @retval 1 is returned, in case A.
 *
 * @retval 2 is returned, in case B.
 *
 * @retval #Enum is returned, in case C.
 *
 * @return Sometimes some value.  See Function().
 *
 * @par Notes
 * VeryLongFunction notes.
 */
__attribute__((__const__)) static inline int VeryLongFunction(
  int                  VeryLongParam0,
  const struct Struct *VeryLongParam1,
  struct Struct    *( *VeryLongParam2 )( void ),
  struct Struct       *VeryLongParam3
)
{
  (void) VeryLongParam1;
  (void) VeryLongParam2;
  (void) VeryLongParam3;
  return VeryLongParam0 + 1;
}

#ifdef __cplusplus
}
#endif

#endif /* _H_H */
"""
        assert content == src.read()
