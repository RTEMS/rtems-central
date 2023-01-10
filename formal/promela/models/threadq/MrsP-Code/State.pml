/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * State.pml
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
 * Here we define all the RTEMS runtime state we need.
 ******************************************************************************/

#ifndef _STATE
#define _STATE

#include "Sizing.pml"
#include "Structs.pml"

/******************************************************************************
 * X information
 *  these hold top-level information about relationships between the key
 *  entities: CPUs, Schedulers, Tasks, and Semaphores.
 ******************************************************************************/

/******************************************************************************
 * CPU information
 *  it has exactly one scheduler running on it
 ******************************************************************************/
typedef CPU_Info {
  BITS(3,cpu_scheduler) ;
}
CPU_Info cpu_info[cpu_count_MAX];

/******************************************************************************
 * Scheduler information
 *  - tbd
 ******************************************************************************/
typedef SCHED_Info {
  byte sched_dummy; // placeholder
}
SCHED_Info sched_info[sched_count_MAX];

Scheduler_Control _SControl[sched_count_MAX];
// We don't use Scheduler_Assignment here unless we need to

/******************************************************************************
 * Task/Thread information
 *  - it has exactly one home scheduler
 ******************************************************************************/
typedef TASK_Info {
  BITS(3,task_home_scheduler);
  Priority_Control initial_priority ;
}

TASK_Info task_info[task_count_MAX];

Thread_queue_Configured_heads _RTEMS_tasks_Heads[task_count_MAX];

Thread_Information _RTEMS_tasks_Information;

// Here we need to distinguish NULL from an address
// For us: Thread_Configured_control is just a Configuration_Scheduler_node,
// which itself is just a Scheduler_SMP_Node
Scheduler_SMP_Node TCC[task_count_MAX+1];

// We have the following "sub" arrays of TCC:
// Chain_Node CN[...]; // Base.Wait_node
// Chain_Node CN[...]; // Base.Thread.Scheduler_node
// Priority_Aggregation PA[...] // Base.Priority
// Priority_Node PN[...] // base.Priority.Node

// Priority_Node PN[....] ;
// RBTree_Node RBT[task_count_MAX+1]; //

Thread_Configuration _TConfig[task_count_MAX];

Thread_Control _TControl[task_count_MAX] ;

/******************************************************************************
 * We have commonly used macros we reproduce here
 ******************************************************************************/
#define _Thread_Scheduler_get_home( task_no ) \
 ( task_info[ task_no ].task_home_scheduler )

/******************************************************************************
 * Semaphore information
 *  - it is used by at least one task
 *  Here we will use a bitmap
 ******************************************************************************/
typedef SEMA_Info {
  BITS(task_count_MAX,sema_tasks);
  MRSP_Control MRSP;
}
SEMA_Info sema_info[sema_count_MAX];


/******************************************************************************
 * The "Heap"
 *
 * Promela has no pointers or notion of heap. We provide arrays to hold the
 * various kinds of nodes that we use here.
 * In all cases the index 0 is treated like the NULL pointer
 ******************************************************************************/

Thread_queue_Heads _TqH[sched_count_MAX+1] ;

#endif
