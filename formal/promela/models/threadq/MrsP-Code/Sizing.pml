/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Sizing.pml
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
 * Here we define all the key sizes of arrays, and bitset stuff
 ******************************************************************************/

#ifndef _SIZING
#define _SIZING

/******************************************************************************
 * Scenario State
 *
 * These are state components that define a scenario:
 *  No. of cpus
 *  No. of schedulers
 *  Mapping of cpus to schedulers
 *  No. of tasks
 *  Mapping of tasks to (home) schedulers
 *  Task priorities
 *  No. of semaphores
 *  The pattern of semaphore access of each task
 *
 *  We start with maximum allowed values for the numbers
 ******************************************************************************/

// #define cpu_count_MAX 4    // gr712rc and gr740 are in scope
#define cpu_count_MAX 2    // gr712rc and gr740 are in scope
#define cpu_count_SIZE 2

#define sched_count_MAX cpu_count_MAX  // At most one scheduler per cpu
#define sched_count_SIZE 2

// #define task_count_MAX 6   // At least one per cpu
#define task_count_MAX 2   // At least one per cpu
#define task_count_SIZE 3

// #define sema_count_MAX 4  // At least two semaphores, otherwise what's the point?
#define sema_count_MAX 2
#define sema_count_SIZE 2

#define BITS( size, var ) unsigned var : size

/******************************************************************************
 * We now define global state variables for these numbers,
 * as well as an assertion that describes well-formedness constraints
 ******************************************************************************/
//unsigned cpu_count : 3 ;
BITS( cpu_count_SIZE, cpu_count ) ;
BITS( sched_count_SIZE, sched_count ) ;
BITS( task_count_SIZE,task_count ) ;
BITS( sema_count_SIZE, sema_count ) ;

#define VALID_ENTITY_COUNTS \
     cpu_count <= cpu_count_MAX \
  && sched_count <= sched_count_MAX \
  && task_count <= task_count_MAX \
  && sema_count <= sema_count_MAX \
  && cpu_count >= sched_count \
  && task_count >= cpu_count \
  && sema_count > 0

#endif
