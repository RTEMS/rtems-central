/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseRtemsModelBarrierMgr
 */

/*
 * Copyright (C) 2020-2022 embedded brains GmbH (http://www.embedded-brains.de)
 *                         Trinity College Dublin (http://www.tcd.ie)
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
 * This file was automatically generated.  Do not edit it manually.
 * Please have a look at
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 *
 * for information how to maintain and re-generate this file.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <rtems/score/threadimpl.h>

#include "tr-barrier-mgr-model.h"
#include "tx-support.h"

static const char PromelaModelBarrierMgr[] = "/PML-BarrierMgr";

rtems_id CreateSema( char * name )
{
  rtems_status_code sc;
  rtems_id id;

  sc = rtems_semaphore_create(
    rtems_build_name( name[ 0 ], name[ 1 ], name[ 2 ], name[ 3 ] ),
    0,
    RTEMS_SIMPLE_BINARY_SEMAPHORE,
    0,
    &id
  );
  T_assert_rsc_success( sc );

  return id;
}

void DeleteSema( rtems_id id )
{
  if ( id != 0 ) {
    rtems_status_code sc;

    sc = rtems_semaphore_delete( id );
    T_rsc_success( sc );
  }
}

void ObtainSema( rtems_id id )
{
  rtems_status_code sc;
  sc = rtems_semaphore_obtain( id, RTEMS_WAIT, RTEMS_NO_TIMEOUT );
  T_quiet_rsc_success( sc );
}

void ReleaseSema( rtems_id id )
{
  rtems_status_code sc;

  sc = rtems_semaphore_release( id );
  T_quiet_rsc_success( sc );
}

// rtems_task_priority SetPriority( rtems_id id, rtems_task_priority priority )
// {
//   rtems_status_code   sc;
//   rtems_task_priority previous;
//
//   sc = rtems_task_set_priority( id, priority, &previous );
//   T_rsc_success( sc );
//
//   return previous;
// }

// rtems_task_priority SetSelfPriority( rtems_task_priority priority )
// {
//   return SetPriority( RTEMS_SELF, priority );
// }

// rtems_id DoCreateTask( rtems_name name, rtems_task_priority priority )
// {
//   rtems_status_code sc;
//   rtems_id          id;
//
//   sc = rtems_task_create(
//     name,
//     priority,
//     RTEMS_MINIMUM_STACK_SIZE,
//     RTEMS_DEFAULT_MODES,
//     RTEMS_DEFAULT_ATTRIBUTES,
//     &id
//   );
//   T_assert_rsc_success( sc );
//
//   return id;
// }

// void StartTask( rtems_id id, rtems_task_entry entry, void *arg )
// {
//   rtems_status_code sc;
//
//   sc = rtems_task_start( id, entry, (rtems_task_argument) arg);
//   T_assert_rsc_success( sc );
// }

// void DeleteTask( rtems_id id )
// {
//   if ( id != 0 ) {
//     rtems_status_code sc;
//     T_printf( "L:Deleting Task id : %d\n", id );
//     sc = rtems_task_delete( id );
//     T_rsc_success( sc );
//   }
// }

rtems_attribute mergeattribs( bool automatic )
{
  rtems_attribute attribs;

  if ( automatic ) { attribs = RTEMS_BARRIER_AUTOMATIC_RELEASE; }
  else { attribs = RTEMS_BARRIER_MANUAL_RELEASE; }

  return attribs;
}

void checkTaskIs( rtems_id expected_id )
{
  rtems_id own_id;

  own_id = _Thread_Get_executing()->Object.id;
  T_eq_u32( own_id, expected_id );
}

void initialise_semaphore( Context *ctx, rtems_id semaphore[] ) {
  semaphore[0] = ctx->runner_sema;
  semaphore[1] = ctx->worker0_sema;
  semaphore[2] = ctx->worker1_sema;
}

void ShowSemaId( Context *ctx ) {
  T_printf( "L:ctx->runner_sema = %d\n", ctx->runner_sema );
  T_printf( "L:ctx->worker0_sema = %d\n", ctx->worker0_sema );
  T_printf( "L:ctx->worker1_sema = %d\n", ctx->worker1_sema );
}

void initialise_id ( rtems_id * id ) {
  *id = 0;
}

void RtemsModelBarrierMgr_Teardown( void *arg )
{
  RtemsModelBarrierMgr_Context *ctx;

  ctx = arg;

  rtems_status_code   sc;
  rtems_task_priority prio;

  T_log( T_NORMAL, "Teardown" );

  prio = 0;
  sc = rtems_task_set_priority( RTEMS_SELF, BM_PRIO_HIGH, &prio );
  T_rsc_success( sc );
  T_eq_u32( prio, BM_PRIO_NORMAL );

  DeleteTask(ctx->worker0_id);
  DeleteTask(ctx->worker1_id);

  T_log( T_NORMAL, "Deleting Runner Semaphore" );
  DeleteSema( ctx->runner_sema );
  T_log( T_NORMAL, "Deleting Worker0 Semaphore" );
  DeleteSema( ctx->worker0_sema );
  T_log( T_NORMAL, "Deleting Worker1 Semaphore" );
  DeleteSema( ctx->worker1_sema );
}


size_t RtemsModelBarrierMgr_Scope( void *arg, char *buf, size_t n )
{
  RtemsModelBarrierMgr_Context *ctx;
  size_t m;
  int p10;
  int tnum ;
  char digit;

  ctx = arg;
  p10 = POWER_OF_10;

  m = T_str_copy(buf, PromelaModelBarrierMgr, n);
  buf += m;
  tnum = ctx->this_test_number;
  while( p10 > 0 && m < n )
  {
    digit = (char) ( (int) '0' + tnum / p10 );
    buf[0] = digit;
    ++buf;
    ++m;
    tnum = tnum % p10;
    p10 /= 10;
  }
  return m;
}

void RtemsModelBarrierMgr_Cleanup(
  RtemsModelBarrierMgr_Context *ctx
)
{
  rtems_status_code sc;

  if (ctx->barrier_id != 0) {
    sc = rtems_barrier_delete(ctx->barrier_id);
    if ( sc != RTEMS_SUCCESSFUL ) {
      T_quiet_rsc( sc, RTEMS_INVALID_ID );
    }
  }
}
