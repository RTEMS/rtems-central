/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Scenarios.pml
 *
 * Copyright (C) 2021 Trinity College Dublin (www.tcd.ie)
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *
 *     * Redistributions in binary form must reproduce the above
 *       copyright notice, this list of conditions and the following
 *       disclaimer in the documentation and/or other materials provided
 *       with the distribution.
 *
 *     * Neither the name of the copyright holders nor the names of its
 *       contributors may be used to endorse or promote products derived
 *       from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 ******************************************************************************/

/******************************************************************************
 * Here we model a non-deterministic choice between various MrsP scenarios.
 *
 * Initially we will follow the breakdown in smpmrsp01, namely:

   test_mrsp_flush_error(ctx);
   test_mrsp_initially_locked();
   test_mrsp_nested_obtain_error(ctx);
   test_mrsp_deadlock_error(ctx);
   test_mrsp_multiple_obtain(ctx);
   test_mrsp_various_block_and_unblock(ctx);
   test_mrsp_obtain_after_migration(ctx);
   test_mrsp_obtain_and_sleep_and_release(ctx);
   test_mrsp_obtain_and_release_with_help(ctx);
   test_mrsp_obtain_and_release(ctx);
   test_mrsp_load(ctx);

 *
 * Later, we will try to generalise this to mix things up a bit.
 ******************************************************************************/

#ifndef _SCENARIOS
#define _SCENARIOS

#include "Priority.pml"
#include "Structs.pml"
#include "State.pml"

/******************************************************************************
 * Current scenario:
 *  2 processors, 2 schedulers, 2 tasks, 2 sempahores
 ******************************************************************************/


inline ChooseScenario() {

  cpu_count = 2;
  printf( "cpu_count MAX=%d, actual = %d\n",cpu_count_MAX,cpu_count);
  sched_count = 2;
  task_count = 2;
  sema_count = 2;
  printf( "sema_count MAX=%d, actual = %d\n",sema_count_MAX,sema_count);

  /* assert(VALID_ENTITY_COUNTS); */

  cpu_info[0].cpu_scheduler = 0;
  cpu_info[1].cpu_scheduler = 1;

  task_info[0].task_home_scheduler = 0 ;
  task_info[0].initial_priority = 3 ;
  task_info[1].task_home_scheduler = 1 ;
  task_info[1].initial_priority = 3 ;

  sema_info[0].MRSP.Ceiling_priority = 2;
  PN[sema_info[0].MRSP.Ceiling_priority]._priority = 2 ;
  sema_info[1].MRSP.Ceiling_priority= 2;
  PN[sema_info[1].MRSP.Ceiling_priority]._priority = 2 ;

  /* assert(AT_MOST_ONE_SCHEDULED_ON_CPU(0));
  assert(AT_MOST_ONE_SCHEDULED_ON_CPU(1));
  assert(AT_MOST_ONE_SCHEDULED_ON_CPU(2));
  assert(AT_MOST_ONE_SCHEDULED_ON_CPU(3)); */
}

#endif
