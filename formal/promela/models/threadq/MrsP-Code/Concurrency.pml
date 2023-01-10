/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Concurrency.pml
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
 * For now:
 *  We run initialization from the Promela `init` process.
 *  Then the modelled tasks each run in their own `proctype`.
 *  However all tasks have an indicator of which CPU they are running on.
 *  So a task can switch CPU.
 *  We do not distinguish task behaviour from that of the schedulers.
 *
 *  The key safety/correctness invariant is that at most one task process
 *  can be enabled at any time on any given CPU.
 *
 ******************************************************************************/

#ifndef _CONCURRENCY
#define _CONCURRENCY



/******************************************************************************
 * C11 Atomics
 * Note: Promela assignment is atomic
 ******************************************************************************/

inline AtomicInit( var, val ) {
  var = val ;
}

inline AtomicLoad( result, atom ) {
  result = atom ;
}

inline AtomicFetchAdd( result, atom, val) {
  atomic{
    result = atom;
    atom = atom + val;
  }
}

inline AtomicStore( var, val) {
  var = val ;
}


/******************************************************************************
 * Action Sequence information
 *   we will use Promela `proctype`s to model scheduler and task behaviour
 *  - we will refer to these as action sequences
 * THIS SHOULD ALL BE IN CONCURRENCY, NOT HERE
 ******************************************************************************/
typedef ASEQ_info{
  BITS(2,exeSchd); // scheduler state of code
  BITS(3,exeCPU)  // cpu on which code is running
}
// indices are task numbers,
//    0..task_count_MAX-1 are tasks
ASEQ_info aseq_info[task_count_MAX];


#define E_SCHEDULER_STATE(i) aseq_info[i].exeSchd

#define E_CPU(i) aseq_info[i].exeCPU

/******************************************************************************
 * We have the following (temporal) invariant (where t > 0):
 *
 * E_SCHEDULER_STATE(0)==SCHED
 *     => forall t @ E_CPU(t)==E_CPU(0] => exeSchd(t) != SCHED
 * E_SCHEDULER_STATE(t)==SCHED
 *     => (E_CPU(t] != E_CPU(0] \/ E_SCHEDULER_STATE(0) != SCHED)
 *        /\
 *        forall t' @ (E_CPU(t) != E_CPU(t') \/ E_SCHEDULER_STATE(t') != SCHED)
 *
 * The simplest way to check this is to compute a usage level for each core,
 * and check these are never greater than one.
 *
 * usage(c) = sum(i in 0..4) (E_SCHEDULER_STATE(i)==SCHED) * (E_CPU(i)==c)
 *
 ******************************************************************************/
#define CPU_USAGE(c) \
  ( (E_SCHEDULER_STATE(0)==SCHEDULER_SMP_NODE_SCHEDULED) * (E_CPU(0)==c) \
  + (E_SCHEDULER_STATE(1)==SCHEDULER_SMP_NODE_SCHEDULED) * (E_CPU(1)==c) \
  )

#define AT_MOST_ONE_SCHEDULED_ON_CPU(c) (CPU_USAGE(c) <= 1)

/* ltl AtMostOneScheduledOn0 { [] ( AT_MOST_ONE_SCHEDULED_ON_CPU(0) ) }
ltl AtMostOneScheduledOn1 { [] ( AT_MOST_ONE_SCHEDULED_ON_CPU(1) ) }
ltl AtMostOneScheduledOn2 { [] ( AT_MOST_ONE_SCHEDULED_ON_CPU(2) ) }
ltl AtMostOneScheduledOn3 { [] ( AT_MOST_ONE_SCHEDULED_ON_CPU(3) ) } */



/******************************************************************************
 * Blocks thread execution while it is not SCHEDULED.
 ******************************************************************************/
inline WaitToRun( task_no ) {
  E_SCHEDULER_STATE( task_no ) == SCHEDULER_SMP_NODE_SCHEDULED;
}

/******************************************************************************
 * Does a voluntary return to the scheduler, remaining READY
 * Task task_no should be currently under control of scheduler sched_no
 ******************************************************************************/
inline Yield( task_no,sched_no ) {
  atomic {
    E_SCHEDULER_STATE( task_no ) = SCHEDULER_SMP_NODE_READY;
    E_SCHEDULER_STATE( sched_no ) = SCHEDULER_SMP_NODE_SCHEDULED;
  }
}

/******************************************************************************
 * Returns to the scheduler as task gets blocked
 * Task task_no should be currently under control of scheduler sched_no
 ******************************************************************************/
inline Block( task_no, sched_no ) {
  atomic {
    E_SCHEDULER_STATE( task_no ) = SCHEDULER_SMP_NODE_BLOCKED;
    E_SCHEDULER_STATE( sched_no ) = SCHEDULER_SMP_NODE_SCHEDULED;
  }
}

/******************************************************************************
 * Set the processor on which the thread will run once SCHEDULED
 ******************************************************************************/
inline SetProc( thread_no, cpu_no) {
  E_CPU( task_no ) = cpu_no;
}

/******************************************************************************
 * Used by scheduler to start a task thread running
 ******************************************************************************/
inline Dispatch( sched_no, task_no ) {
  atomic {
    E_SCHEDULER_STATE(task_no) = SCHEDULER_SMP_NODE_SCHEDULED;
    E_SCHEDULER_STATE(sched_no) = SCHEDULER_SMP_NODE_READY;
  }
}


/******************************************************************************
 ******************************************************************************/


#endif
