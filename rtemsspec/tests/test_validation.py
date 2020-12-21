# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.validation module. """

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

from rtemsspec.validation import generate
from rtemsspec.items import EmptyItemCache, ItemCache
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_validation(tmpdir):
    validation_config = {}
    base_directory = os.path.join(tmpdir, "base")
    validation_config["base-directory"] = base_directory

    generate(validation_config, EmptyItemCache())

    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-validation", with_spec_types=True)
    generate(validation_config, ItemCache(item_cache_config))

    with open(os.path.join(base_directory, "ts.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestSuiteTs
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <blue.h>

#include "green.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestSuiteTs spec:/ts
 *
 * @ingroup RTEMSTestSuites
 *
 * @brief The Blue Green brief description.
 *
 * The Blue Green description.
 *
 * @{
 */

/* Blue green code */

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc12.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseDirective
 * @ingroup RTEMSTestCaseTc
 * @ingroup RTEMSTestCaseTc2
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <a.h>
#include <b.h>
#include <rtems.h>

#include "x.h"
#include "y.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestCaseDirective spec:/directive
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test rtems_task_ident() brief description.
 *
 * Test rtems_task_ident() description.
 *
 * @{
 */

typedef enum {
  Directive_Pre_Name_Invalid,
  Directive_Pre_Name_Self,
  Directive_Pre_Name_Valid,
  Directive_Pre_Name_NA
} Directive_Pre_Name;

typedef enum {
  Directive_Pre_Node_Local,
  Directive_Pre_Node_Remote,
  Directive_Pre_Node_Invalid,
  Directive_Pre_Node_SearchAll,
  Directive_Pre_Node_SearchOther,
  Directive_Pre_Node_SearchLocal,
  Directive_Pre_Node_NA
} Directive_Pre_Node;

typedef enum {
  Directive_Pre_Id_NullPtr,
  Directive_Pre_Id_Valid,
  Directive_Pre_Id_NA
} Directive_Pre_Id;

typedef enum {
  Directive_Post_Status_Ok,
  Directive_Post_Status_InvAddr,
  Directive_Post_Status_InvName,
  Directive_Post_Status_InvNode,
  Directive_Post_Status_InvId,
  Directive_Post_Status_NA
} Directive_Post_Status;

typedef enum {
  Directive_Post_Id_Nop,
  Directive_Post_Id_NullPtr,
  Directive_Post_Id_Self,
  Directive_Post_Id_LocalTask,
  Directive_Post_Id_RemoteTask,
  Directive_Post_Id_NA
} Directive_Post_Id;

/**
 * @brief Test context for spec:/directive test case.
 */
typedef struct {
  /**
   * @brief Brief context member description.
   *
   * Context member description.
   */
  rtems_status_code status;

  rtems_name name;

  uint32_t node;

  rtems_id *id;

  rtems_id id_value;

  rtems_id id_local_task;

  rtems_id id_remote_task;

  /**
   * @brief This member defines the pre-condition states for the next action.
   */
  size_t pcs[ 3 ];

  /**
   * @brief This member indicates if the test action loop is currently
   *   executed.
   */
  bool in_action_loop;
} Directive_Context;

static Directive_Context
  Directive_Instance;

static const char * const Directive_PreDesc_Name[] = {
  "Invalid",
  "Self",
  "Valid",
  "NA"
};

static const char * const Directive_PreDesc_Node[] = {
  "Local",
  "Remote",
  "Invalid",
  "SearchAll",
  "SearchOther",
  "SearchLocal",
  "NA"
};

static const char * const Directive_PreDesc_Id[] = {
  "NullPtr",
  "Valid",
  "NA"
};

static const char * const * const Directive_PreDesc[] = {
  Directive_PreDesc_Name,
  Directive_PreDesc_Node,
  Directive_PreDesc_Id,
  NULL
};

/* Test rtems_task_ident() support */

static void Directive_Pre_Name_Prepare(
  Directive_Context *ctx,
  Directive_Pre_Name state
)
{
  /* Prologue */

  switch ( state ) {
    case Directive_Pre_Name_Invalid: {
      ctx->name = 1;
      break;
    }

    case Directive_Pre_Name_Self: {
      ctx->name = RTEMS_SELF;
      break;
    }

    case Directive_Pre_Name_Valid: {
      ctx->name = rtems_build_name( 'T', 'A', 'S', 'K' );
      break;
    }

    case Directive_Pre_Name_NA:
      break;
  }

  /* Epilogue */
}

static void Directive_Pre_Node_Prepare(
  Directive_Context *ctx,
  Directive_Pre_Node state
)
{
  switch ( state ) {
    case Directive_Pre_Node_Local: {
      ctx->node = 1;
      break;
    }

    case Directive_Pre_Node_Remote: {
      ctx->node = 2;
      break;
    }

    case Directive_Pre_Node_Invalid: {
      ctx->node = 256;
      break;
    }

    case Directive_Pre_Node_SearchAll: {
      ctx->node = RTEMS_SEARCH_ALL_NODES;
      break;
    }

    case Directive_Pre_Node_SearchOther: {
      ctx->node = RTEMS_SEARCH_OTHER_NODES;
      break;
    }

    case Directive_Pre_Node_SearchLocal: {
      ctx->node = RTEMS_SEARCH_LOCAL_NODE;
      break;
    }

    case Directive_Pre_Node_NA:
      break;
  }
}

static void Directive_Pre_Id_Prepare(
  Directive_Context *ctx,
  Directive_Pre_Id   state
)
{
  switch ( state ) {
    case Directive_Pre_Id_NullPtr: {
      ctx->id = NULL;
      break;
    }

    case Directive_Pre_Id_Valid: {
      ctx->id_value = 0xffffffff;
      ctx->id = &ctx->id_value;
      break;
    }

    case Directive_Pre_Id_NA:
      break;
  }
}

static void Directive_Post_Status_Check(
  Directive_Context    *ctx,
  Directive_Post_Status state
)
{
  switch ( state ) {
    case Directive_Post_Status_Ok: {
      T_rsc(ctx->status, RTEMS_SUCCESSFUL);
      break;
    }

    case Directive_Post_Status_InvAddr: {
      T_rsc(ctx->status, RTEMS_INVALID_ADDRESS);
      break;
    }

    case Directive_Post_Status_InvName: {
      T_rsc(ctx->status, RTEMS_INVALID_NAME);
      break;
    }

    case Directive_Post_Status_InvNode: {
      T_rsc(ctx->status, RTEMS_INVALID_NODE);
      break;
    }

    case Directive_Post_Status_InvId: {
      T_rsc(ctx->status, RTEMS_INVALID_ID);
      break;
    }

    case Directive_Post_Status_NA:
      break;
  }
}

static void Directive_Post_Id_Check(
  Directive_Context *ctx,
  Directive_Post_Id  state
)
{
  switch ( state ) {
    case Directive_Post_Id_Nop: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, 0xffffffff);
      break;
    }

    case Directive_Post_Id_NullPtr: {
      T_null(ctx->id)
      break;
    }

    case Directive_Post_Id_Self: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, rtems_task_self());
      break;
    }

    case Directive_Post_Id_LocalTask: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, ctx->id_local_task);
      break;
    }

    case Directive_Post_Id_RemoteTask: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, ctx->id_remote_task);
      break;
    }

    case Directive_Post_Id_NA:
      break;
  }
}

/**
 * @brief Setup brief description.
 *
 * Setup description.
 */
static void Directive_Setup( Directive_Context *ctx )
{
  rtems_status_code sc;

  sc = rtems_task_create(
    rtems_build_name( 'T', 'A', 'S', 'K' ),
    1,
    RTEMS_MINIMUM_STACK_SIZE,
    RTEMS_DEFAULT_MODES,
    RTEMS_DEFAULT_ATTRIBUTES,
    &ctx->id_local_task
  );
  T_assert_rsc_success( sc );
}

static void Directive_Setup_Wrap( void *arg )
{
  Directive_Context *ctx;

  ctx = arg;
  ctx->in_action_loop = false;
  Directive_Setup( ctx );
}

static void Directive_Teardown( Directive_Context *ctx )
{
  rtems_status_code sc;

  if ( ctx->id_local_task != 0 ) {
    sc = rtems_task_delete( ctx->id_local_task );
    T_rsc_success( sc );
  }
}

static void Directive_Teardown_Wrap( void *arg )
{
  Directive_Context *ctx;

  ctx = arg;
  ctx->in_action_loop = false;
  Directive_Teardown( ctx );
}

static size_t Directive_Scope( void *arg, char *buf, size_t n )
{
  Directive_Context *ctx;

  ctx = arg;

  if ( ctx->in_action_loop ) {
    return T_get_scope( Directive_PreDesc, buf, n, ctx->pcs );
  }

  return 0;
}

static T_fixture Directive_Fixture = {
  .setup = Directive_Setup_Wrap,
  .stop = NULL,
  .teardown = Directive_Teardown_Wrap,
  .scope = Directive_Scope,
  .initial_context = &Directive_Instance
};

static const uint8_t Directive_TransitionMap[][ 2 ] = {
  {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_Self
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_Self
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_Self
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_Self
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_Self
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_Self
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_LocalTask
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    Directive_Post_Status_Ok,
    Directive_Post_Id_RemoteTask
#else
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
#endif
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_LocalTask
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    Directive_Post_Status_Ok,
    Directive_Post_Id_RemoteTask
#else
    Directive_Post_Status_InvName,
    Directive_Post_Id_Nop
#endif
  }, {
    Directive_Post_Status_InvAddr,
    Directive_Post_Id_NullPtr
  }, {
    Directive_Post_Status_Ok,
    Directive_Post_Id_LocalTask
  }
};

static const struct {
  uint8_t Skip : 1;
  uint8_t Pre_Name_NA : 1;
  uint8_t Pre_Node_NA : 1;
  uint8_t Pre_Id_NA : 1;
} Directive_TransitionInfo[] = {
  {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    0, 0, 0, 0
#else
    0, 0, 0, 0
#endif
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    0, 0, 0, 0
#else
    0, 0, 0, 0
#endif
  }, {
    0, 0, 0, 0
  }, {
    0, 0, 0, 0
  }
};

static void Directive_Action( Directive_Context *ctx )
{
  ctx->status = rtems_task_ident( ctx->name, ctx->node, ctx->id );
}

/**
 * @fn void T_case_body_Directive( void )
 */
T_TEST_CASE_FIXTURE( Directive, &Directive_Fixture )
{
  Directive_Context *ctx;
  size_t index;

  ctx = T_fixture_context();
  ctx->in_action_loop = true;
  index = 0;

  for (
    ctx->pcs[ 0 ] = Directive_Pre_Name_Invalid;
    ctx->pcs[ 0 ] < Directive_Pre_Name_NA;
    ++ctx->pcs[ 0 ]
  ) {
    if ( Directive_TransitionInfo[ index ].Pre_Name_NA ) {
      ctx->pcs[ 0 ] = Directive_Pre_Name_NA;
      index += ( Directive_Pre_Name_NA - 1 )
        * Directive_Pre_Node_NA
        * Directive_Pre_Id_NA;
    }

    for (
      ctx->pcs[ 1 ] = Directive_Pre_Node_Local;
      ctx->pcs[ 1 ] < Directive_Pre_Node_NA;
      ++ctx->pcs[ 1 ]
    ) {
      if ( Directive_TransitionInfo[ index ].Pre_Node_NA ) {
        ctx->pcs[ 1 ] = Directive_Pre_Node_NA;
        index += ( Directive_Pre_Node_NA - 1 )
          * Directive_Pre_Id_NA;
      }

      for (
        ctx->pcs[ 2 ] = Directive_Pre_Id_NullPtr;
        ctx->pcs[ 2 ] < Directive_Pre_Id_NA;
        ++ctx->pcs[ 2 ]
      ) {
        if ( Directive_TransitionInfo[ index ].Pre_Id_NA ) {
          ctx->pcs[ 2 ] = Directive_Pre_Id_NA;
          index += ( Directive_Pre_Id_NA - 1 );
        }

        if ( Directive_TransitionInfo[ index ].Skip ) {
          ++index;
          continue;
        }

        Directive_Pre_Name_Prepare( ctx, ctx->pcs[ 0 ] );
        Directive_Pre_Node_Prepare( ctx, ctx->pcs[ 1 ] );
        Directive_Pre_Id_Prepare( ctx, ctx->pcs[ 2 ] );
        Directive_Action( ctx );
        Directive_Post_Status_Check(
          ctx,
          Directive_TransitionMap[ index ][ 0 ]
        );
        Directive_Post_Id_Check( ctx, Directive_TransitionMap[ index ][ 1 ] );
        ++index;
      }
    }
  }
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTc spec:/tc
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test case brief description.
 *
 * Test case description.
 *
 * This test case performs the following actions:
 *
 * - Test case action 0 description.
 *
 *   - Test case action 0 check 0 description.
 *
 *   - Test case action 0 check 1 description.
 *
 * - Test case action 1 description.
 *
 *   - Test case action 1 check 0 description.
 *
 *   - Test case action 1 check 1 description.
 *
 * @{
 */

/* Test case support code */

/**
 * @fn void T_case_body_Tc( void )
 */
T_TEST_CASE( Tc )
{
  /* Test case prologue code */

  T_plan(125);

  /* Test case action 0 code */
  /* Test case action 0 check 0 code: Accounts for 123 test plan steps */
  /* Test case action 0 check 1 code; step 123 */

  /* Test case action 1 code */
  /* Test case action 1 check 0 code; step 124 */
  /* Test case action 1 check 1 code */

  /* Test case epilogue code */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTc2 spec:/tc2
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test case 2 brief description.
 *
 * Test case 2 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 2 action 0 description.
 *
 *   - Test case 2 action 0 check 0 description.
 *
 *   - Test case 2 action 0 check 1 description.
 *
 * - Test case 2 action 1 description.
 *
 * @{
 */

/**
 * @fn void T_case_body_Tc2( void )
 */
T_TEST_CASE_FIXTURE( Tc2, &test_case_2_fixture )
{
  /* Test case 2 action 0 code */
  /* Test case 2 action 0 check 0 code */
  /* Test case 2 action 0 check 1 code */

  /* Test case 2 action 1 code */
}

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc34.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseRtm
 * @ingroup RTEMSTestCaseTc3
 * @ingroup RTEMSTestCaseTc4
 * @ingroup RTEMSTestCaseTc5
 * @ingroup RTEMSTestCaseTc6
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <c.h>
#include <u.h>

#include "v.h"
#include "z.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestCaseRtm spec:/rtm
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test brief.
 *
 * Test description.
 *
 * @{
 */

/* Context support code */

/**
 * @brief Test context for spec:/rtm test case.
 */
typedef struct {
  /**
   * @brief Context member brief.
   *
   * Context member description.
   */
  int member;

  /**
   * @brief This member references the measure runtime context.
   */
  T_measure_runtime_context *context;

  /**
   * @brief This member provides the measure runtime request.
   */
  T_measure_runtime_request request;
} Rtm_Context;

static Rtm_Context
  Rtm_Instance;

/* Support code */

static void Rtm_Setup_Context( Rtm_Context *ctx )
{
  T_measure_runtime_config config;

  memset( &config, 0, sizeof( config ) );
  config.sample_count = 100;
  ctx->request.arg = ctx;
  ctx->request.flags = T_MEASURE_RUNTIME_REPORT_SAMPLES;
  ctx->context = T_measure_runtime_create( &config );
  T_assert_not_null( ctx->context );
}

static void Rtm_Setup_Wrap( void *arg )
{
  Rtm_Context *ctx;

  ctx = arg;
  Rtm_Setup_Context( ctx );
}

/**
 * @brief Stop brief.
 *
 * Stop description.
 */
static void Rtm_Stop( Rtm_Context *ctx )
{
  /* Stop code */
}

static void Rtm_Stop_Wrap( void *arg )
{
  Rtm_Context *ctx;

  ctx = arg;
  Rtm_Stop( ctx );
}

/**
 * @brief Teardown brief.
 *
 * Teardown description.
 */
static void Rtm_Teardown( Rtm_Context *ctx )
{
  /* Teardown code */
}

static void Rtm_Teardown_Wrap( void *arg )
{
  Rtm_Context *ctx;

  ctx = arg;
  Rtm_Teardown( ctx );
}

static T_fixture Rtm_Fixture = {
  .setup = Rtm_Setup_Wrap,
  .stop = Rtm_Stop_Wrap,
  .teardown = Rtm_Teardown_Wrap,
  .scope = NULL,
  .initial_context = &Rtm_Instance
};

/**
 * @brief Cleanup brief.
 *
 * Cleanup description.
 */
static void Rtm_Cleanup( Rtm_Context *ctx )
{
  /* Cleanup code */
}

/**
 * @brief Body brief.
 *
 * Body description.
 */
static void Rpr_Body( Rtm_Context *ctx )
{
  /* Body code */
}

static void Rpr_Body_Wrap( void *arg )
{
  Rtm_Context *ctx;

  ctx = arg;
  Rpr_Body( ctx );
}

/**
 * @brief Teardown brief.
 *
 * Teardown description.
 */
static bool Rpr_Teardown(
  Rtm_Context *ctx,
  T_ticks     *delta,
  uint32_t     tic,
  uint32_t     toc,
  unsigned int retry
)
{
  /* Teardown code */
}

static bool Rpr_Teardown_Wrap(
  void        *arg,
  T_ticks     *delta,
  uint32_t     tic,
  uint32_t     toc,
  unsigned int retry
)
{
  Rtm_Context *ctx;

  ctx = arg;
  return Rpr_Teardown( ctx, delta, tic, toc, retry );
}

/**
 * @brief Cleanup brief.
 *
 * Cleanup description.
 */
static void Rpr_Cleanup( Rtm_Context *ctx )
{
  /* Cleanup code */
}

/**
 * @fn void T_case_body_Rtm( void )
 */
T_TEST_CASE_FIXTURE( Rtm, &Rtm_Fixture )
{
  Rtm_Context *ctx;

  ctx = T_fixture_context();

  ctx->request.name = "Rpr";
  ctx->request.setup = NULL;
  ctx->request.body = Rpr_Body_Wrap;
  ctx->request.teardown = Rpr_Teardown_Wrap;
  T_measure_runtime( ctx->context, &ctx->request );
  Rpr_Cleanup( ctx );
  Rtm_Cleanup( ctx );
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTc3 spec:/tc3
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test case 3 brief description.
 *
 * Test case 3 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 3 action 0 description.
 *
 *   - Test case 3 action 0 check 0 description.
 *
 * @{
 */

/**
 * @fn void T_case_body_Tc3( void )
 */
T_TEST_CASE( Tc3 )
{
  T_plan(1);

  /* Test case 3 action 0 code */
  /* Test case 3 action 0 check 0 code; step 0 */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTc4 spec:/tc4
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test case 4 brief description.
 *
 * Test case 4 description.
 *
 * @{
 */

/**
 * @fn void T_case_body_Tc4( void )
 */
T_TEST_CASE( Tc4 )
{
  /* Test case 4 epilogue code */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTc5 spec:/tc5
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test case 5 brief description.
 *
 * Test case 5 description.
 *
 * This test case performs the following actions:
 *
 * - Test case action 0 description.
 *
 *   - Test case action 0 check 0 description.
 *
 *   - Test case action 0 check 1 description.
 *
 * - Test case action 1 description.
 *
 *   - Test case action 1 check 0 description.
 *
 *   - Test case action 1 check 1 description.
 *
 * @{
 */

static void Tc5_Wrap( int *a, int b, int *c )
{
  T_plan(2);

  /* Test case action 0 code */
  /* Test case action 0 check 0 code */
  /* Test case action 0 check 1 code; step 0 */

  /* Test case action 1 code */
  /* Test case action 1 check 0 code; step 1 */
  /* Test case action 1 check 1 code */

  /* Test case 5 epilogue code */
}

static T_fixture_node Tc5_Node;

void Tc5_Run( int *a, int b, int *c )
{
  T_push_fixture( &Tc5_Node, &T_empty_fixture );
  Tc5_Wrap( a, b, c );
  T_pop_fixture();
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTc6 spec:/tc6
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @{
 */

void Tc6_Run( void )
{
}

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc5.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseTc5
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifndef _TC5_H
#define _TC5_H

#include <d.h>

#include "e.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @addtogroup RTEMSTestCaseTc5
 *
 * @{
 */

/* Header code for Tc5_Run() */

/**
 * @brief Runs the parameterized test case.
 *
 * @param[in] a Parameter A description.
 *
 * @param b Parameter B description.
 *
 * @param[out] c Parameter C description.
 */
void Tc5_Run( int *a, int b, int *c );

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _TC5_H */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc6.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseTc6
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifndef _TC6_H
#define _TC6_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @addtogroup RTEMSTestCaseTc6
 *
 * @{
 */

/**
 * @brief Runs the parameterized test case.
 */
void Tc6_Run( void );

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _TC6_H */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "action2.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseAction2
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifndef _ACTION2_H
#define _ACTION2_H

#include <d.h>

#include "e.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @addtogroup RTEMSTestCaseAction2
 *
 * @{
 */

typedef enum {
  Action2_Pre_A_X,
  Action2_Pre_A_Y,
  Action2_Pre_A_NA
} Action2_Pre_A;

typedef enum {
  Action2_Pre_B_X,
  Action2_Pre_B_Y,
  Action2_Pre_B_Z,
  Action2_Pre_B_NA
} Action2_Pre_B;

typedef enum {
  Action2_Post_A_X,
  Action2_Post_A_Y,
  Action2_Post_A_NA
} Action2_Post_A;

typedef enum {
  Action2_Post_B_X,
  Action2_Post_B_Y,
  Action2_Post_B_NA
} Action2_Post_B;

/* Header code for Action 2 with Action2_Run() */

/**
 * @brief Runs the parameterized test case.
 *
 * @param[in] a Parameter A description.
 *
 * @param b Parameter B description.
 *
 * @param[out] c Parameter C description.
 */
void Action2_Run( int *a, int b, int *c );

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _ACTION2_H */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "action2.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseAction2
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
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <a.h>

#include "b.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestCaseAction2 spec:/action2
 *
 * @ingroup RTEMSTestSuiteTs
 *
 * @brief Test brief.
 *
 * Test description.
 *
 * @{
 */

/* Context support code */

/**
 * @brief Test context for spec:/action2 test case.
 */
typedef struct {
  /**
   * @brief Context member brief.
   *
   * Context member description.
   */
  int member;

  /**
   * @brief This member contains a copy of the corresponding Action2_Run()
   *   parameter.
   */
  int *a;

  /**
   * @brief This member contains a copy of the corresponding Action2_Run()
   *   parameter.
   */
  int b;

  /**
   * @brief This member contains a copy of the corresponding Action2_Run()
   *   parameter.
   */
  int *c;

  /**
   * @brief This member defines the pre-condition states for the next action.
   */
  size_t pcs[ 2 ];

  /**
   * @brief This member indicates if the test action loop is currently
   *   executed.
   */
  bool in_action_loop;
} Action2_Context;

static Action2_Context
  Action2_Instance;

static const char * const Action2_PreDesc_A[] = {
  "X",
  "Y",
  "NA"
};

static const char * const Action2_PreDesc_B[] = {
  "X",
  "Y",
  "Z",
  "NA"
};

static const char * const * const Action2_PreDesc[] = {
  Action2_PreDesc_A,
  Action2_PreDesc_B,
  NULL
};

/* Support code */

static void Action2_Pre_A_Prepare( Action2_Context *ctx, Action2_Pre_A state )
{
  /* Pre A prologue. */

  switch ( state ) {
    case Action2_Pre_A_X: {
      /* Pre A X */
      break;
    }

    case Action2_Pre_A_Y: {
      /* Pre A Y */
      break;
    }

    case Action2_Pre_A_NA:
      break;
  }

  /* Pre A epilogue. */
}

static void Action2_Pre_B_Prepare( Action2_Context *ctx, Action2_Pre_B state )
{
  /* Pre B prologue. */

  switch ( state ) {
    case Action2_Pre_B_X: {
      /* Pre B X */
      break;
    }

    case Action2_Pre_B_Y: {
      /* Pre B Y */
      break;
    }

    case Action2_Pre_B_Z: {
      /* Pre B Z */
      break;
    }

    case Action2_Pre_B_NA:
      break;
  }

  /* Pre B epilogue. */
}

static void Action2_Post_A_Check( Action2_Context *ctx, Action2_Post_A state )
{
  /* Post A prologue. */

  switch ( state ) {
    case Action2_Post_A_X: {
      /* Post A X */
      break;
    }

    case Action2_Post_A_Y: {
      /* Post A Y */
      break;
    }

    case Action2_Post_A_NA:
      break;
  }

  /* Post A epilogue. */
}

static void Action2_Post_B_Check( Action2_Context *ctx, Action2_Post_B state )
{
  /* Post B prologue. */

  switch ( state ) {
    case Action2_Post_B_X: {
      /* Post B X */
      break;
    }

    case Action2_Post_B_Y: {
      /* Post B Y */
      break;
    }

    case Action2_Post_B_NA:
      break;
  }

  /* Post B epilogue. */
}

/**
 * @brief Setup brief.
 *
 * Setup description.
 */
static void Action2_Setup( Action2_Context *ctx )
{
  /* Setup code */
}

static void Action2_Setup_Wrap( void *arg )
{
  Action2_Context *ctx;

  ctx = arg;
  ctx->in_action_loop = false;
  Action2_Setup( ctx );
}

/**
 * @brief Teardown brief.
 *
 * Teardown description.
 */
static void Action2_Teardown( Action2_Context *ctx )
{
  /* Teardown code */
}

static void Action2_Teardown_Wrap( void *arg )
{
  Action2_Context *ctx;

  ctx = arg;
  ctx->in_action_loop = false;
  Action2_Teardown( ctx );
}

static size_t Action2_Scope( void *arg, char *buf, size_t n )
{
  Action2_Context *ctx;

  ctx = arg;

  if ( ctx->in_action_loop ) {
    return T_get_scope( Action2_PreDesc, buf, n, ctx->pcs );
  }

  return 0;
}

static T_fixture Action2_Fixture = {
  .setup = Action2_Setup_Wrap,
  .stop = NULL,
  .teardown = Action2_Teardown_Wrap,
  .scope = Action2_Scope,
  .initial_context = &Action2_Instance
};

static const uint8_t Action2_TransitionMap[][ 2 ] = {
  {
    Action2_Post_A_X,
    Action2_Post_B_Y
  }, {
    Action2_Post_A_Y,
    Action2_Post_B_X
  }, {
    Action2_Post_A_X,
    Action2_Post_B_X
  }, {
    Action2_Post_A_X,
    Action2_Post_B_Y
  }, {
    Action2_Post_A_Y,
    Action2_Post_B_X
  }, {
    Action2_Post_A_NA,
    Action2_Post_B_NA
  }
};

static const struct {
  uint8_t Skip : 1;
  uint8_t Pre_A_NA : 1;
  uint8_t Pre_B_NA : 1;
} Action2_TransitionInfo[] = {
  {
    0, 0, 0
  }, {
    0, 1, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 1, 0
  }, {
    1, 0, 0
  }
};

static void Action2_Prepare( Action2_Context *ctx )
{
  /* Prepare */
}

static void Action2_Action( Action2_Context *ctx )
{
  /* Action */
}

static void Action2_Cleanup( Action2_Context *ctx )
{
  /* Cleanup */
}

static T_fixture_node Action2_Node;

void Action2_Run( int *a, int b, int *c )
{
  Action2_Context *ctx;
  size_t index;

  ctx = T_push_fixture( &Action2_Node, &Action2_Fixture );

  ctx->a = a;
  ctx->b = b;
  ctx->c = c;
  ctx->in_action_loop = true;
  index = 0;

  for (
    ctx->pcs[ 0 ] = Action2_Pre_A_X;
    ctx->pcs[ 0 ] < Action2_Pre_A_NA;
    ++ctx->pcs[ 0 ]
  ) {
    if ( Action2_TransitionInfo[ index ].Pre_A_NA ) {
      ctx->pcs[ 0 ] = Action2_Pre_A_NA;
      index += ( Action2_Pre_A_NA - 1 )
        * Action2_Pre_B_NA;
    }

    for (
      ctx->pcs[ 1 ] = Action2_Pre_B_X;
      ctx->pcs[ 1 ] < Action2_Pre_B_NA;
      ++ctx->pcs[ 1 ]
    ) {
      if ( Action2_TransitionInfo[ index ].Pre_B_NA ) {
        ctx->pcs[ 1 ] = Action2_Pre_B_NA;
        index += ( Action2_Pre_B_NA - 1 );
      }

      if ( Action2_TransitionInfo[ index ].Skip ) {
        ++index;
        continue;
      }

      Action2_Prepare( ctx );
      Action2_Pre_A_Prepare( ctx, ctx->pcs[ 0 ] );
      Action2_Pre_B_Prepare( ctx, ctx->pcs[ 1 ] );
      Action2_Action( ctx );
      Action2_Post_A_Check( ctx, Action2_TransitionMap[ index ][ 0 ] );
      Action2_Post_B_Check( ctx, Action2_TransitionMap[ index ][ 1 ] );
      Action2_Cleanup( ctx );
      ++index;
    }
  }

  T_pop_fixture();
}

/** @} */
"""
        assert content == src.read()
