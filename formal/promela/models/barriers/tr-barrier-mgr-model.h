/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseRtemsModelBarrierMgr_Run
 */

/*
 * Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
 *               2022 Trinity College Dublin (http://www.tcd.ie)
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
 * Do not manually edit this file.  It is part of the RTEMS quality process
 * and was automatically generated.
 *
 * If you find something that needs to be fixed or worded better please
 * post a report to an RTEMS mailing list or raise a bug report:
 *
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifndef _TR_MODEL_BARRIER_MGR_H
#define _TR_MODEL_BARRIER_MGR_H

#include <rtems.h>
#include <rtems/score/thread.h>

#include <rtems/test.h>
#include "tx-support.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Run Setup/Cleanup structs/functions
 */
typedef struct {
  int this_test_number; // test number used to identify a test runner instance

  Thread_Control *runner_thread; // TCB of the runner task
  rtems_id runner_id; // ID of the tasks
  rtems_id worker0_id;
  rtems_id worker1_id;

  rtems_id runner_sema; // ID of the Runner semaphore
  rtems_id worker0_sema; // ID of the Worker0 semaphore
  rtems_id worker1_sema; // ID of the Worker1 semaphore
  rtems_id barrier_id; // ID of the created barrier

  rtems_id runner_sched; // scheduler ID of scheduler used by the runner task
  rtems_id other_sched; // scheduler ID of another scheduler
                        // which is not used by the runner task
  T_thread_switch_log_4 thread_switch_log; // thread switch log
} RtemsModelBarrierMgr_Context;

typedef enum {
  BM_PRIO_HIGH = 1,
  BM_PRIO_NORMAL,
  BM_PRIO_LOW,
  BM_PRIO_OTHER
} Priorities;

#define POWER_OF_10 100

#define CreateTask( name, priority ) \
  DoCreateTask( \
    rtems_build_name( name[ 0 ], name[ 1 ], name[ 2 ], name[ 3 ] ), \
    priority \
  )

typedef RtemsModelBarrierMgr_Context Context;

rtems_id DoCreateTask( rtems_name name, rtems_task_priority priority );

void StartTask( rtems_id id, rtems_task_entry entry, void *arg );

void DeleteTask( rtems_id id );

rtems_id CreateSema( char * name);

void DeleteSema( rtems_id id );

void ObtainSema( rtems_id id );

void ReleaseSema( rtems_id id );

rtems_task_priority SetPriority( rtems_id id, rtems_task_priority priority );

rtems_task_priority SetSelfPriority( rtems_task_priority priority );

rtems_option mergeattribs( bool automatic );

void checkTaskIs( rtems_id expected_id ) ;

void ShowSemaId( Context *ctx ) ;

void initialise_id ( rtems_id * id );

void initialise_semaphore( Context *ctx, rtems_id semaphore[] );

void RtemsModelBarrierMgr_Setup( void *arg ) ;

void RtemsModelBarrierMgr_Teardown( void *arg ) ;

size_t RtemsModelBarrierMgr_Scope( void *arg, char *buf, size_t n ) ;

void RtemsModelBarrierMgr_Cleanup( RtemsModelBarrierMgr_Context *ctx );

/**
 * @addtogroup RTEMSTestCaseRtemsModelBarrierMgr_Run
 *
 * @{
 */

/**
 * @brief Runs the test case.
 */

void RtemsModelBarrierMgr_Run0(void);

void RtemsModelBarrierMgr_Run1(void);

void RtemsModelBarrierMgr_Run2(void);

void RtemsModelBarrierMgr_Run3(void);

void RtemsModelBarrierMgr_Run4(void);

void RtemsModelBarrierMgr_Run5(void);

void RtemsModelBarrierMgr_Run6(void);

void RtemsModelBarrierMgr_Run7(void);

void RtemsModelBarrierMgr_Run8(void);

void RtemsModelBarrierMgr_Run9(void);

void RtemsModelBarrierMgr_Run10(void);

void RtemsModelBarrierMgr_Run11(void);

void RtemsModelBarrierMgr_Run12(void);

void RtemsModelBarrierMgr_Run13(void);

void RtemsModelBarrierMgr_Run14(void);

void RtemsModelBarrierMgr_Run15(void);

void RtemsModelBarrierMgr_Run16(void);

void RtemsModelBarrierMgr_Run17(void);

void RtemsModelBarrierMgr_Run18(void);

void RtemsModelBarrierMgr_Run19(void);

void RtemsModelBarrierMgr_Run20(void);

void RtemsModelBarrierMgr_Run21(void);

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _TR_BARRIER_H */
