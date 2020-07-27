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
 * @ingroup RTEMSTestSuiteBlueGreen
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <blue.h>

#include "green.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestSuiteBlueGreen Blue Green
 *
 * @ingroup RTEMSTestSuites
 *
 * @brief Test Suite
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
 * @ingroup RTEMSTestCaseClassicTaskIdentification
 * @ingroup RTEMSTestCaseTestCase
 * @ingroup RTEMSTestCaseTestCase2
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
 * @defgroup RTEMSTestCaseClassicTaskIdentification Classic Task Identification
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

typedef enum {
  ClassicTaskIdentification_Pre_Name_Invalid,
  ClassicTaskIdentification_Pre_Name_Self,
  ClassicTaskIdentification_Pre_Name_Valid,
  ClassicTaskIdentification_Pre_Name_NA
} ClassicTaskIdentification_Pre_Name;

typedef enum {
  ClassicTaskIdentification_Pre_Node_Local,
  ClassicTaskIdentification_Pre_Node_Remote,
  ClassicTaskIdentification_Pre_Node_Invalid,
  ClassicTaskIdentification_Pre_Node_SearchAll,
  ClassicTaskIdentification_Pre_Node_SearchOther,
  ClassicTaskIdentification_Pre_Node_SearchLocal,
  ClassicTaskIdentification_Pre_Node_NA
} ClassicTaskIdentification_Pre_Node;

typedef enum {
  ClassicTaskIdentification_Pre_Id_NullPtr,
  ClassicTaskIdentification_Pre_Id_Valid,
  ClassicTaskIdentification_Pre_Id_NA
} ClassicTaskIdentification_Pre_Id;

typedef enum {
  ClassicTaskIdentification_Post_Status_Ok,
  ClassicTaskIdentification_Post_Status_InvAddr,
  ClassicTaskIdentification_Post_Status_InvName,
  ClassicTaskIdentification_Post_Status_InvNode,
  ClassicTaskIdentification_Post_Status_InvId,
  ClassicTaskIdentification_Post_Status_NA
} ClassicTaskIdentification_Post_Status;

typedef enum {
  ClassicTaskIdentification_Post_Id_Nop,
  ClassicTaskIdentification_Post_Id_NullPtr,
  ClassicTaskIdentification_Post_Id_Self,
  ClassicTaskIdentification_Post_Id_LocalTask,
  ClassicTaskIdentification_Post_Id_RemoteTask,
  ClassicTaskIdentification_Post_Id_NA
} ClassicTaskIdentification_Post_Id;

/**
 * @brief Test context for Classic Task Identification test case.
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
} ClassicTaskIdentification_Context;

static ClassicTaskIdentification_Context
  ClassicTaskIdentification_Instance;

static const char * const ClassicTaskIdentification_PreDesc_Name[] = {
  "Invalid",
  "Self",
  "Valid"
};

static const char * const ClassicTaskIdentification_PreDesc_Node[] = {
  "Local",
  "Remote",
  "Invalid",
  "SearchAll",
  "SearchOther",
  "SearchLocal"
};

static const char * const ClassicTaskIdentification_PreDesc_Id[] = {
  "NullPtr",
  "Valid"
};

static const char * const * const ClassicTaskIdentification_PreDesc[] = {
  ClassicTaskIdentification_PreDesc_Name,
  ClassicTaskIdentification_PreDesc_Node,
  ClassicTaskIdentification_PreDesc_Id,
  NULL
};

/* Test rtems_task_ident() support */

static void ClassicTaskIdentification_Pre_Name_Prepare(
  ClassicTaskIdentification_Context *ctx,
  ClassicTaskIdentification_Pre_Name state
)
{
  /* Prologue */

  switch ( state ) {
    case ClassicTaskIdentification_Pre_Name_Invalid: {
      ctx->name = 1;
      break;
    }

    case ClassicTaskIdentification_Pre_Name_Self: {
      ctx->name = RTEMS_SELF;
      break;
    }

    case ClassicTaskIdentification_Pre_Name_Valid: {
      ctx->name = rtems_build_name( 'T', 'A', 'S', 'K' );
      break;
    }

    case ClassicTaskIdentification_Pre_Name_NA:
      break;
  }

  /* Epilogue */
}

static void ClassicTaskIdentification_Pre_Node_Prepare(
  ClassicTaskIdentification_Context *ctx,
  ClassicTaskIdentification_Pre_Node state
)
{
  switch ( state ) {
    case ClassicTaskIdentification_Pre_Node_Local: {
      ctx->node = 1;
      break;
    }

    case ClassicTaskIdentification_Pre_Node_Remote: {
      ctx->node = 2;
      break;
    }

    case ClassicTaskIdentification_Pre_Node_Invalid: {
      ctx->node = 256;
      break;
    }

    case ClassicTaskIdentification_Pre_Node_SearchAll: {
      ctx->node = RTEMS_SEARCH_ALL_NODES;
      break;
    }

    case ClassicTaskIdentification_Pre_Node_SearchOther: {
      ctx->node = RTEMS_SEARCH_OTHER_NODES;
      break;
    }

    case ClassicTaskIdentification_Pre_Node_SearchLocal: {
      ctx->node = RTEMS_SEARCH_LOCAL_NODE;
      break;
    }

    case ClassicTaskIdentification_Pre_Node_NA:
      break;
  }
}

static void ClassicTaskIdentification_Pre_Id_Prepare(
  ClassicTaskIdentification_Context *ctx,
  ClassicTaskIdentification_Pre_Id   state
)
{
  switch ( state ) {
    case ClassicTaskIdentification_Pre_Id_NullPtr: {
      ctx->id = NULL;
      break;
    }

    case ClassicTaskIdentification_Pre_Id_Valid: {
      ctx->id_value = 0xffffffff;
      ctx->id = &ctx->id_value;
      break;
    }

    case ClassicTaskIdentification_Pre_Id_NA:
      break;
  }
}

static void ClassicTaskIdentification_Post_Status_Check(
  ClassicTaskIdentification_Context    *ctx,
  ClassicTaskIdentification_Post_Status state
)
{
  switch ( state ) {
    case ClassicTaskIdentification_Post_Status_Ok: {
      T_rsc(ctx->status, RTEMS_SUCCESSFUL);
      break;
    }

    case ClassicTaskIdentification_Post_Status_InvAddr: {
      T_rsc(ctx->status, RTEMS_INVALID_ADDRESS);
      break;
    }

    case ClassicTaskIdentification_Post_Status_InvName: {
      T_rsc(ctx->status, RTEMS_INVALID_NAME);
      break;
    }

    case ClassicTaskIdentification_Post_Status_InvNode: {
      T_rsc(ctx->status, RTEMS_INVALID_NODE);
      break;
    }

    case ClassicTaskIdentification_Post_Status_InvId: {
      T_rsc(ctx->status, RTEMS_INVALID_ID);
      break;
    }

    case ClassicTaskIdentification_Post_Status_NA:
      break;
  }
}

static void ClassicTaskIdentification_Post_Id_Check(
  ClassicTaskIdentification_Context *ctx,
  ClassicTaskIdentification_Post_Id  state
)
{
  switch ( state ) {
    case ClassicTaskIdentification_Post_Id_Nop: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, 0xffffffff);
      break;
    }

    case ClassicTaskIdentification_Post_Id_NullPtr: {
      T_null(ctx->id)
      break;
    }

    case ClassicTaskIdentification_Post_Id_Self: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, rtems_task_self());
      break;
    }

    case ClassicTaskIdentification_Post_Id_LocalTask: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, ctx->id_local_task);
      break;
    }

    case ClassicTaskIdentification_Post_Id_RemoteTask: {
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, ctx->id_remote_task);
      break;
    }

    case ClassicTaskIdentification_Post_Id_NA:
      break;
  }
}

/**
 * @brief Setup brief description.
 *
 * Setup description.
 */
static void ClassicTaskIdentification_Setup(
  ClassicTaskIdentification_Context *ctx
)
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

static void ClassicTaskIdentification_Setup_Wrap( void *arg )
{
  ClassicTaskIdentification_Context *ctx;

  ctx = arg;
  ctx->in_action_loop = false;
  ClassicTaskIdentification_Setup( ctx );
}

static void ClassicTaskIdentification_Teardown(
  ClassicTaskIdentification_Context *ctx
)
{
  rtems_status_code sc;

  if ( ctx->id_local_task != 0 ) {
    sc = rtems_task_delete( ctx->id_local_task );
    T_rsc_success( sc );
  }
}

static void ClassicTaskIdentification_Teardown_Wrap( void *arg )
{
  ClassicTaskIdentification_Context *ctx;

  ctx = arg;
  ctx->in_action_loop = false;
  ClassicTaskIdentification_Teardown( ctx );
}

static void ClassicTaskIdentification_Scope( void *arg, char *buf, size_t n )
{
  ClassicTaskIdentification_Context *ctx;

  ctx = arg;

  if ( ctx->in_action_loop ) {
    T_get_scope( ClassicTaskIdentification_PreDesc, buf, n, ctx->pcs );
  }
}

static T_fixture ClassicTaskIdentification_Fixture = {
  .setup = ClassicTaskIdentification_Setup_Wrap,
  .stop = NULL,
  .teardown = ClassicTaskIdentification_Teardown_Wrap,
  .scope = ClassicTaskIdentification_Scope,
  .initial_context = &ClassicTaskIdentification_Instance
};

static const uint8_t ClassicTaskIdentification_TransitionMap[][ 2 ] = {
  {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_Self
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_Self
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_Self
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_Self
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_Self
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_Self
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_LocalTask
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_RemoteTask
#else
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
#endif
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_LocalTask
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_RemoteTask
#else
    ClassicTaskIdentification_Post_Status_InvName,
    ClassicTaskIdentification_Post_Id_Nop
#endif
  }, {
    ClassicTaskIdentification_Post_Status_InvAddr,
    ClassicTaskIdentification_Post_Id_NullPtr
  }, {
    ClassicTaskIdentification_Post_Status_Ok,
    ClassicTaskIdentification_Post_Id_LocalTask
  }
};

static const struct {
  uint8_t Pre_Name_NA : 1;
  uint8_t Pre_Node_NA : 1;
  uint8_t Pre_Id_NA : 1;
} ClassicTaskIdentification_TransitionInfo[] = {
  {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    0, 0, 0
#else
    0, 0, 0
#endif
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }, {
#if defined(RTEMS_MULTIPROCESSING)
    0, 0, 0
#else
    0, 0, 0
#endif
  }, {
    0, 0, 0
  }, {
    0, 0, 0
  }
};

/**
 * @fn void T_case_body_ClassicTaskIdentification( void )
 *
 * @brief Test rtems_task_ident() brief description.
 *
 * Test rtems_task_ident() description.
 */
T_TEST_CASE_FIXTURE(
  ClassicTaskIdentification,
  &ClassicTaskIdentification_Fixture
)
{
  ClassicTaskIdentification_Context *ctx;
  size_t index;

  ctx = T_fixture_context();
  ctx->in_action_loop = true;
  index = 0;

  for (
    ctx->pcs[ 0 ] = ClassicTaskIdentification_Pre_Name_Invalid;
    ctx->pcs[ 0 ] < ClassicTaskIdentification_Pre_Name_NA;
    ++ctx->pcs[ 0 ]
  ) {
    if ( ClassicTaskIdentification_TransitionInfo[ index ].Pre_Name_NA ) {
      ctx->pcs[ 0 ] = ClassicTaskIdentification_Pre_Name_NA;
      index += ( ClassicTaskIdentification_Pre_Name_NA - 1 )
        * ClassicTaskIdentification_Pre_Node_NA
        * ClassicTaskIdentification_Pre_Id_NA;
    }

    for (
      ctx->pcs[ 1 ] = ClassicTaskIdentification_Pre_Node_Local;
      ctx->pcs[ 1 ] < ClassicTaskIdentification_Pre_Node_NA;
      ++ctx->pcs[ 1 ]
    ) {
      if ( ClassicTaskIdentification_TransitionInfo[ index ].Pre_Node_NA ) {
        ctx->pcs[ 1 ] = ClassicTaskIdentification_Pre_Node_NA;
        index += ( ClassicTaskIdentification_Pre_Node_NA - 1 )
          * ClassicTaskIdentification_Pre_Id_NA;
      }

      for (
        ctx->pcs[ 2 ] = ClassicTaskIdentification_Pre_Id_NullPtr;
        ctx->pcs[ 2 ] < ClassicTaskIdentification_Pre_Id_NA;
        ++ctx->pcs[ 2 ]
      ) {
        if ( ClassicTaskIdentification_TransitionInfo[ index ].Pre_Id_NA ) {
          ctx->pcs[ 2 ] = ClassicTaskIdentification_Pre_Id_NA;
          index += ( ClassicTaskIdentification_Pre_Id_NA - 1 );
        }

        ClassicTaskIdentification_Pre_Name_Prepare( ctx, ctx->pcs[ 0 ] );
        ClassicTaskIdentification_Pre_Node_Prepare( ctx, ctx->pcs[ 1 ] );
        ClassicTaskIdentification_Pre_Id_Prepare( ctx, ctx->pcs[ 2 ] );
        ctx->status = rtems_task_ident( ctx->name, ctx->node, ctx->id );
        ClassicTaskIdentification_Post_Status_Check(
          ctx,
          ClassicTaskIdentification_TransitionMap[ index ][ 0 ]
        );
        ClassicTaskIdentification_Post_Id_Check(
          ctx,
          ClassicTaskIdentification_TransitionMap[ index ][ 1 ]
        );
        ++index;
      }
    }
  }
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTestCase Test Case
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/* Test case support code */

/**
 * @fn void T_case_body_TestCase( void )
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
 */
T_TEST_CASE( TestCase )
{
  /* Test case prologue code */

  T_plan(2);

  /* Test case action 0 code */
  /* Test case action 0 check 0 code */
  /* Test case action 0 check 1 code; step 0 */

  /* Test case action 1 code */
  /* Test case action 1 check 0 code; step 1 */
  /* Test case action 1 check 1 code */

  /* Test case epilogue code */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTestCase2 Test Case 2
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @fn void T_case_body_TestCase2( void )
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
 */
T_TEST_CASE_FIXTURE( TestCase2, &test_case_2_fixture )
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
 * @ingroup RTEMSTestCaseTestCase3
 * @ingroup RTEMSTestCaseTestCase4
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <c.h>

#include "z.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestCaseTestCase3 Test Case 3
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @fn void T_case_body_TestCase3( void )
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
 */
T_TEST_CASE( TestCase3 )
{
  T_plan(1);

  /* Test case 3 action 0 code */
  /* Test case 3 action 0 check 0 code; step 0 */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTestCase4 Test Case 4
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @fn void T_case_body_TestCase4( void )
 *
 * @brief Test case 4 brief description.
 *
 * Test case 4 description.
 */
T_TEST_CASE( TestCase4 )
{
  /* Test case 4 epilogue code */
}

/** @} */
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
 * @brief Test brief.
 *
 * Test description.
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <a.h>

#include "b.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestCaseAction2 Action 2
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @brief Test context for Action 2 test case.
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
  "Y"
};

static const char * const Action2_PreDesc_B[] = {
  "X",
  "Y"
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

static void Action2_Scope( void *arg, char *buf, size_t n )
{
  Action2_Context *ctx;

  ctx = arg;

  if ( ctx->in_action_loop ) {
    T_get_scope( Action2_PreDesc, buf, n, ctx->pcs );
  }
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
    Action2_Post_B_Y
  }, {
    Action2_Post_A_Y,
    Action2_Post_B_X
  }
};

static const struct {
  uint8_t Pre_A_NA : 1;
  uint8_t Pre_B_NA : 1;
} Action2_TransitionInfo[] = {
  {
    0, 0
  }, {
    1, 0
  }, {
    0, 0
  }, {
    1, 0
  }
};

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

      Action2_Pre_A_Prepare( ctx, ctx->pcs[ 0 ] );
      Action2_Pre_B_Prepare( ctx, ctx->pcs[ 1 ] );
      /* Action */
      Action2_Post_A_Check(
        ctx,
        Action2_TransitionMap[ index ][ 0 ]
      );
      Action2_Post_B_Check(
        ctx,
        Action2_TransitionMap[ index ][ 1 ]
      );
      ++index;
    }
  }

  T_pop_fixture();
}

/** @} */
"""
        assert content == src.read()
