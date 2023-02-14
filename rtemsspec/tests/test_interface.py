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
    interface_config["enabled"] = []

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
 * Copyright (C) 2020, 2022 embedded brains GmbH (http://www.embedded-brains.de)
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

/* Generated from spec:/forward-decl */

/* Forward declaration */
struct Struct;

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
 * Function description.  References to xs, VeryLongFunction(), ::Integer,
 * #Enum, #DEFINE, VERY_LONG_MACRO(), #Variable, ::ENUMERATOR_0, Struct, @ref
 * a, interface, @ref GroupA, and @ref GroupF.  Second parameter is ``Param1``.
 *
 * @code
 * these two lines
 * are not wrapped
 * @endcode
 *
 * @par Constraints
 * @parblock
 * The following constraints apply to this directive:
 *
 * * Constraint A for Function().
 * @endparblock
 */
void Function(
  int        Param0,
  const int *Param1,
  int       *Param2,
  int       *Param3,
  int       *Param4
);

/* Generated from spec:/func6 */
void Function6( int Param0 );

/* Generated from spec:/irqamp-timestamp */

/**
 * @defgroup IrqampTimestamp IRQ(A)MP Timestamp
 *
 * @brief This group contains the IRQ(A)MP Timestamp interfaces.
 *
 * @{
 */

/**
 * @defgroup IrqampTimestampITCNT \\
 *   Interrupt timestamp counter n register (ITCNT)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define IRQAMP_ITCNT_TCNT_SHIFT 0
#define IRQAMP_ITCNT_TCNT_MASK 0xffffffffU
#define IRQAMP_ITCNT_TCNT_GET( _reg ) \\
  ( ( ( _reg ) >> 0 ) & 0xffffffffU )
#define IRQAMP_ITCNT_TCNT( _val ) ( ( _val ) << 0 )

/** @} */

/**
 * @defgroup IrqampTimestampITSTMPC \\
 *   Interrupt timestamp n control register (ITSTMPC)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define IRQAMP_ITSTMPC_TSTAMP_SHIFT 27
#define IRQAMP_ITSTMPC_TSTAMP_MASK 0xf8000000U
#define IRQAMP_ITSTMPC_TSTAMP_GET( _reg ) \\
  ( ( ( _reg ) >> 27 ) & 0x1fU )
#define IRQAMP_ITSTMPC_TSTAMP( _val ) ( ( _val ) << 27 )

#define IRQAMP_ITSTMPC_S1 0x4000000U

#define IRQAMP_ITSTMPC_S2 0x2000000U

#define IRQAMP_ITSTMPC_KS 0x20U

#define IRQAMP_ITSTMPC_TSISEL_SHIFT 0
#define IRQAMP_ITSTMPC_TSISEL_MASK 0x1fU
#define IRQAMP_ITSTMPC_TSISEL_GET( _reg ) \\
  ( ( ( _reg ) >> 0 ) & 0x1fU )
#define IRQAMP_ITSTMPC_TSISEL( _val ) ( ( _val ) << 0 )

/** @} */

/**
 * @defgroup IrqampTimestampITSTMPAS \\
 *   Interrupt Assertion Timestamp n register (ITSTMPAS)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define IRQAMP_ITSTMPAS_TASSERTION_SHIFT 0
#define IRQAMP_ITSTMPAS_TASSERTION_MASK 0xffffffffU
#define IRQAMP_ITSTMPAS_TASSERTION_GET( _reg ) \\
  ( ( ( _reg ) >> 0 ) & 0xffffffffU )
#define IRQAMP_ITSTMPAS_TASSERTION( _val ) ( ( _val ) << 0 )

/** @} */

/**
 * @defgroup IrqampTimestampITSTMPAC \\
 *   Interrupt Acknowledge Timestamp n register (ITSTMPAC)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define IRQAMP_ITSTMPAC_TACKNOWLEDGE_SHIFT 0
#define IRQAMP_ITSTMPAC_TACKNOWLEDGE_MASK 0xffffffffU
#define IRQAMP_ITSTMPAC_TACKNOWLEDGE_GET( _reg ) \\
  ( ( ( _reg ) >> 0 ) & 0xffffffffU )
#define IRQAMP_ITSTMPAC_TACKNOWLEDGE( _val ) ( ( _val ) << 0 )

/** @} */

/**
 * @brief This structure defines the IRQ(A)MP Timestamp register block memory
 *   map.
 */
typedef struct irqamp_timestamp {
  /**
   * @brief See @ref IrqampTimestampITCNT.
   */
  uint32_t itcnt;

  /**
   * @brief See @ref IrqampTimestampITSTMPC.
   */
  uint32_t itstmpc;

  /**
   * @brief See @ref IrqampTimestampITSTMPAS.
   */
  uint32_t itstmpas;

  /**
   * @brief See @ref IrqampTimestampITSTMPAC.
   */
  uint32_t itstmpac;
} irqamp_timestamp;

/** @} */

/* Generated from spec:/irqamp */

/**
 * @defgroup Irqamp IRQ(A)MP
 *
 * @brief This group contains the IRQ(A)MP interfaces.
 *
 * @{
 */

/**
 * @defgroup IrqampILEVEL Interrupt level register (ILEVEL)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

#define IRQAMP_ILEVEL_IL_15_1_SHIFT 1
#define IRQAMP_ILEVEL_IL_15_1_MASK 0xfffeU
#define IRQAMP_ILEVEL_IL_15_1_GET( _reg ) \\
  ( ( ( _reg ) >> 1 ) & 0x7fffU )
#define IRQAMP_ILEVEL_IL_15_1( _val ) ( ( _val ) << 1 )

/** @} */

/**
 * @defgroup IrqampIPEND8 Interrupt pending register (IPEND8)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

/** @} */

/**
 * @brief This structure defines the IRQ(A)MP register block memory map.
 */
typedef struct irqamp {
  /**
   * @brief See @ref IrqampILEVEL.
   */
  uint32_t foobar_0;

  #if defined(RTEMS_SMP)
    /**
     * @brief See @ref IrqampIPEND8.
     */
    uint8_t ipend8_0[ 4 ];
  #else
    /**
     * @brief See @ref IrqampILEVEL.
     */
    uint32_t foobar_1;
  #endif

  uint8_t reserved_8_9;

  /**
   * @brief See @ref IrqampIPEND8.
   */
  uint8_t ipend8_1[ 4 ];

  uint8_t reserved_d_100[ 243 ];

  /**
   * @brief See @ref IrqampTimestamp.
   */
  irqamp_timestamp itstmp[ 16 ];

  uint32_t reserved_200_400[ 128 ];
} irqamp;

/** @} */

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

/* Generated from spec:/register-block-no-size */

/**
 * @defgroup RBNS RBNS
 *
 * @brief This group contains the RBNS interfaces.
 *
 * @{
 */

/**
 * @defgroup RBNSR Brief. (R)
 *
 * @brief This group contains register bit definitions.
 *
 * @{
 */

/** @} */

/**
 * @name Registers
 *
 * @brief Brief.
 *
 * @{
 */

/**
 * @brief See @ref RBNSR.
 */
#define RBNS_R 0x0

/** @} */

/** @} */

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

/* Generated from spec:/u */

/**
 * @ingroup GroupC
 */
typedef union Union {
  /**
   * @brief Brief member 0 description.
   */
  int m_0;

  /**
   * @brief Brief member 1 description.
   */
  long m_1;
} Union;

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
  Union            *( *VeryLongParam2 )( void ),
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
