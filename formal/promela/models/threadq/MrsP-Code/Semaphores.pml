/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * MrsP-Semaphores.pml
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

#ifndef _SEMAPHORES
#define _SEMAPHORES

#include "Values.pml"
#include "Structs.pml"
#include "Concurrency.pml"
#include "Locks.pml"
#include "State.pml"

/******************************************************************************
 * Here we model the three key MrsP semaphore operations
 *
 * We assume the following settings throughout:
 *   Defined macros:
 *     RTEMS_SMP  RTEMS_SCORE_CPUSTDATOMIC_USE_STDATOMIC
 *   Undefined macros:
 *     RTEMS_DEBUG  RTEMS_PROFILING  RTEMS_SMP_LOCK_DO_NOT_INLINE
 *     RTEMS_MULTIPROCESSING
 *   Semaphore call arguments:
 *     RTEMS_PRIORITY                         : rtems_attribute (bit)
 *     RTEMS_BINARY_SEMAPHORE                 : rtems_attribute (bit)
 *     RTEMS_MULTIPROCESSOR_RESOURCE_SHARING  : rtems_attribute (bit)
 *
 * All functions below take an action sequence number (aseqno) as first argument
 *
 * The current task is often represented by `executing`. We can generate
 * this from an action sequence number
 ******************************************************************************/

/******************************************************************************
 ******************************************************************************
 * SEMAPHORE CREATE
 *
 * rtems_status_code rtems_semaphore_create(
 *   rtems_name           name,
 *   uint32_t             count,
 *   rtems_attribute      attribute_set,
 *   rtems_task_priority  priority_ceiling,
 *   rtems_id            *id
 * )
 *
 * sc = rtems_semaphore_create(
 *   rtems_build_name('M', 'R', 'S', 'P'),
 *   1,
 *   RTEMS_BINARY_SEMAPHORE | RTEMS_PRIORITY |
 *     RTEMS_MULTIPROCESSOR_RESOURCE_SHARING,
 *   prio,
 *   id
 * );
 *
 * We ignore the name (for now) - not sure we need it here
 * We ignore the count because we always set it to 1 at creation time
 * We ignore attribute_set as it is always fixed as shown above
 * We provide the priority ceiling
 * We supply the id, as the index we use for it in `sema_info`
 * We ignore the return code as this always succeeds
 ******************************************************************************/
inline rtems_semaphore_create( aseqno, // action sequence number
                               priority_ceiling, id, // actual parameters
                               rc ) // return value
{
  printf( "@@@ %d CALL semcreate %d %d %d\n",
          _pid, aseqno, priority_ceiling, id );
  { BITS(sched_count_SIZE,i);

    // given that we have "pre-allocated" objects in this model,
    // this MrsP creation just requires _MRSP_Initialize to be done:
    i = 0;
    do
    ::  i == sched_count -> break;
    ::  else ->
        if
        ::  _Thread_Scheduler_get_home( aseqno ) == i ->
            sema_info[id].MRSP.ceiling_priorities[i] = priority_ceiling ;
        ::  else ->
            sema_info[id].MRSP.ceiling_priorities[i] = 0 ;
        fi
        i++;
    od
    sema_info[id].MRSP.Wait_queue.Lock.next_ticket = 0 ;
    sema_info[id].MRSP.Wait_queue.headsi = 0 ;
    sema_info[id].MRSP.Wait_queue.owneri = 0 ;

  }
  rc = RTEMS_SUCCESSFUL;
}

/******************************************************************************
 ******************************************************************************
 * SEMAPHORE OBTAIN
 *
 * rtems_status_code rtems_semaphore_obtain(
 *   rtems_id        id,
 *   rtems_option    option_set,
 *   rtems_interval  timeout
 * )
 *
 * sc = rtems_semaphore_obtain(mrsp_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT)
 * We assume the id is valid
 * We assume we wait, with no timeout, for now
 *
 *
 ******************************************************************************/
// local variable (per-task) arrays
Thread_queue_Context queue_context[task_count_MAX] ;

inline rtems_semaphore_obtain ( aseqno, // action sequence number
                                mrsp_id, wait, tout, // actual parameter
                                rc ) // return value
{
  printf( "@@@ %d CALL semobtain %d %d %d\n",
          _pid, mrsp_id, wait, tout );

    // _Chain_Initialize_node( &queue_context->Lock_context.Wait.Gate.Node );
    // Does nothing if not in RTEMS_DEBUG mode!
    queue_context[aseqno].enqueue_callout = 0;
    queue_context[aseqno].deadlock_callout = 0;

    // queue_context->enqueue_callout = _Thread_queue_Enqueue_do_nothing_extra;

    _MRSP_Seize( aseqno, mrsp_id, wait, rc ) ;
    // queue_context is as above
}

/******************************************************************************
 *  MRSP SEIZE
 ******************************************************************************/
// local variable (per-task) arrays
byte my_ticket[task_count_MAX];
byte now_serving[task_count_MAX];
byte owner[task_count_MAX];

inline _MRSP_Seize( aseqno, // action sequence number
                    mrsp_id, wait, // more actual parameters
                    // queue_context is same as in caller above
                    rc ) // return value
{
  printf("_MRSP_Seize(...)\n");

  SpinWait( aseqno,
            sema_info[mrsp_id].MRSP.Wait_queue.Lock.next_ticket,
            sema_info[mrsp_id].MRSP.Wait_queue.Lock.now_serving ) ;

  printf("_MRSP_Seize, got past ticket wait\n");

  owner[aseqno] = sema_info[mrsp_id].MRSP.Wait_queue.owneri ;
  printf("owner[%d] = %d\n",aseqno,owner[aseqno]);

  rc = RTEMS_NOT_IMPLEMENTED;

  if
  ::  owner[aseqno] == 0 ->
      printf("_MRSP_Seize: owner is NULL\n");
      _MRSP_Claim_ownership( aseqno, mrsp_id, rc );
  ::  else ->
      if
      ::  owner[aseqno] == aseqno ->
          printf("_MRSP_Seize: owner is executing\n");
          rc = RTEMS_INCORRECT_STATE ;
      ::  else ->
          if
          ::  wait ->
              printf("_MRSP_Seize: waiting\n");
          ::  else ->
              // more to do
              rc = RTEMS_UNSATISFIED ;
          fi
      fi
  fi
}

/******************************************************************************
 *  SpinWait
 ******************************************************************************/
inline SpinWait( taskno, nextTicket, nowServing ) {
    AtomicFetchAdd( my_ticket[taskno], nextTicket, 1 );
    AtomicLoad( now_serving[taskno], nowServing ) ;
    do
    :: now_serving[taskno] == my_ticket[taskno] -> break ;
    :: else -> AtomicLoad( now_serving[taskno], nowServing ) ;
    od
}

/******************************************************************************
 *  WaitRelease
 ******************************************************************************/
byte current_ticket[task_count_MAX];
byte next_ticket[task_count_MAX];

inline WaitRelease( taskno, nowServing ) {
  // _Thread_Wait_release_default_critical( thread, &lock_context );
  /* unsigned int current_ticket =
  _Atomic_Load_uint(
    & thread->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
    ATOMIC_ORDER_RELAXED
  ); */
  AtomicLoad( current_ticket[taskno], nowServing );

  next_ticket[taskno] = current_ticket[taskno]+1;

  AtomicStore( nowServing, next_ticket[taskno] );
  /* unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint(
    & thread->Wait.Lock.Default.now_serving,
    next_ticket,
    ATOMIC_ORDER_RELEASE
  ); */
}

/******************************************************************************
 *  MRSP CLAIM OWNERSHIP
 ******************************************************************************/

inline _MRSP_Claim_ownership( aseqno, // action sequence number
                              mrsp_id, // more actual parameters
                              rc ) // return value
{
  printf("_MRSP_Claim_ownership(...)\n");

  printf(" MrsP Prio = %d\n",
          PN[sema_info[mrsp_id].MRSP.Ceiling_priority]._priority);
  printf(" Before: Thread Prio = %d\n",
          PN[_TControl[aseqno].Real_priority]._priority);
  _MRSP_Raise_priority( aseqno,
                        mrsp_id,
                        sema_info[mrsp_id].MRSP.Ceiling_priority,
                        rc );
  printf(" After: Thread Prio = %d\n",
          PN[_TControl[aseqno].Real_priority]._priority);
  assert( rc == STATUS_SUCCESSFUL ); // We expect success here



  printf("_Claim NYfII\n");
}

/******************************************************************************
 *  MRSP RAISE PRIORITY
 ******************************************************************************/
//local variables
byte scheduler[task_count_MAX]; // Scheduler_Control *scheduler;
byte RPschedNode[task_count_MAX];  // Scheduler_Node *scheduler_node
Priority_Control ceil_prio[task_count_MAX];

inline _MRSP_Raise_priority( aseqno, // action sequence number
                             mrsp_id, // MRSP_Control *
                             priority_node, // Priority_Node *
                             // queue_context argument defined above
                             rc )
{
  printf("MRSP Raise priority(...)\n");
  printf("aseqno=%d, mrsp_id=%d, priority_node=%d\n",
          aseqno,mrsp_id,priority_node);

  //   _Thread_queue_Context_clear_priority_updates( queue_context );
  queue_context[aseqno].Priority.update_count = 0;

  // _Thread_Wait_acquire_default_critical( thread, &lock_context );
  SpinWait( aseqno,
            _TControl[aseqno].Wait.Lock.Default.next_ticket,
            _TControl[aseqno].Wait.Lock.Default.now_serving
          );
  printf("MRSP Raise priority: acquired ticket lock\n");

  // scheduler = _Thread_Scheduler_get_home( thread );
  scheduler[aseqno] = _TControl[aseqno].Scheduler.home_scheduler;
  printf( "_TControl[aseqno].Scheduler.home_scheduler = %d\n",
          _TControl[aseqno].Scheduler.home_scheduler );

  // scheduler_node = _Thread_Scheduler_get_home_node( thread );
  assert(_TControl[aseqno].Scheduler.Wait_nodes);
  RPschedNode[aseqno] = _TControl[aseqno].Scheduler.Wait_nodes ;
  printf( " RPschedNode[aseqno] = %d\n", RPschedNode[aseqno] );

  // ceiling_priority = _MRSP_Get_priority( mrsp, scheduler );
  ceil_prio[aseqno] =
     sema_info[mrsp_id].MRSP.ceiling_priorities[scheduler[aseqno]];
  printf(" ceiling_priority is %d\n", ceil_prio[aseqno] );
  printf("ceil_prio = %d\n", ceil_prio[aseqno]);
  printf("PN[]._priority = %d\n",PN[priority_node]._priority);

  if
  :: ( ceil_prio[aseqno]
       <= PN[PA[TCC[RPschedNode[aseqno]].Base.iPriority].iNode]._priority ) ->
     printf("OK: ceil_prio <= ShedNode priority\n" );
     // priority_node->priority = ceiling_priority;

     PN[priority_node]._priority = ceil_prio[aseqno];

     // _RBTree_Initialize_node( &priority_node->Node.RBTree ); NOOP

     // _Thread_Priority_add( thread, priority_node, queue_context );
     rc = STATUS_SUCCESSFUL ;
  :: else ->
          printf("NOT-OK: ceil_prio > ShedNode priority\n" );

     rc = STATUS_MUTEX_CEILING_VIOLATED ;
  fi

  // thread->Wait.Lock.Default.now_serving
  WaitRelease( aseqno, _TControl[aseqno].Wait.Lock.Default.now_serving );
  printf("MRSP Raise priority: released ticket lock\n");

}

/******************************************************************************
 ******************************************************************************
 * SEMAPHORE RELEASE
 *
 * rtems_status_code rtems_semaphore_release( rtems_id id )
 *
 * sc = rtems_semaphore_release(mrsp_id);
 ******************************************************************************/
inline rtems_semaphore_release( aseqno, // action sequence number
                                mrsp_id, // actual parameter
                                rc )     // return value
{
  printf( "@@@ %d CALL semrelease %d %d\n", _pid, aseqno, mrsp_id );
  rc = RTEMS_NOT_IMPLEMENTED;
}

#endif
