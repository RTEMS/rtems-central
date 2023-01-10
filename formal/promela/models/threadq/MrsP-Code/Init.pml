/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Init.pml
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
 * Here we model the scenario-agnostic initialisation performed by the Init
 * function call in smptests/smpmrsp01/init.c
 *
 * NOTE:
 *  For simplicity we assume all of this initialisation is done by one initial
 *  task for all tasks, which we assume are statically defined.
 *  This means we do not use the scheduler/task number  parameter required for
 *  proper concurrency modelling at this stage.
 ******************************************************************************/

#ifndef _INIT
#define _INIT

#include "Structs.pml"
#include "Locks.pml"
#include "State.pml"
#include "Semaphores.pml"

// initialization index
byte ii;

/******************************************************************************
 * Here we model scenario initialisation
 ******************************************************************************/


/******************************************************************************
 * _Scheduler_simple_SMP_Initialize
 *    cpukit/score/src/schedulersimplesmp.c
 ******************************************************************************/
inline _Scheduler_simple_SMP_Initialize( _scheduler ) {
  printf("_Scheduler_simple_SMP_Initialize NYI\n");
}

/******************************************************************************
 * _Scheduler_simple_SMP_Initialize
 *    cpukit/score/src/schedulersimplesmp.c
 ******************************************************************************/

inline InitScheduler( schedno ) {
  // from confdefs.h
  _SControl[schedno].maximum_priority = 255; // we might want to shrink this!
  _Chain_Initialize_empty( _SControl[schedno].context.Scheduled );
  _Chain_Initialize_empty( _SControl[schedno].context.Idle_threads );
  _Chain_Initialize_empty( _SControl[schedno].context.Ready );
  // Operations.initialize = _Scheduler_simple_SMP_Initialize
  // _Scheduler_simple_SMP_Initialize( _SControl[schedno] );
  // Operations.node_initialize =_Scheduler_simple_SMP_Node_initialize
}

inline InitSchedulers() {
  ii = 0;
  do
  ::  ii == sched_count -> break ;
  ::  else ->
        printf( "Static Initialisation for Scheduler %d\n", ii );
        InitScheduler( ii );
      ii++ ;
  od
}

// following is called from _RTEMS_tasks_Manager_initialization
// in taskconstruct.c
/* void _Thread_Initialize_information( Thread_Information *information )
{
  _Objects_Initialize_information( &information->Objects );

  _Freechain_Initialize(
    &information->Thread_queue_heads.Free,
    information->Thread_queue_heads.initial,
    _Objects_Get_maximum_index( &information->Objects ),
    _Thread_queue_Heads_size
  );
} */

// _RTEMS_tasks_Information is setup statically
inline InitThread0() {
  printf( "Static Setup for Tasks \n" );

  _RTEMS_tasks_Information[0].initial = 0; // index into _RTEMS_tasks_Heads
  _Freechain_Initialize( _RTEMS_tasks_Information[0].Free, 0, cpu_count_MAX ) ;

}

/******************************************************************************
 * Thread_Control_add_on
 *    cpukit/include/rtems/score/thread.h
 *
    typedef struct {
      // Offset of the pointer field in Thread_Control referencing an
      // application configuration dependent memory area in the thread control
      // block.
      size_t destination_offset;
      // Offset relative to the thread control block begin to an application
      // configuration dependent memory area.
      size_t source_offset;
    } Thread_Control_add_on;
 *
 * _Thread_Control_add_ons
 *    cpukit/include/rtems/confdefs/threads.h
 *
         const Thread_Control_add_on _Thread_Control_add_ons[] = {
        {
          offsetof( Thread_Configured_control, Control.Scheduler.nodes ),
          offsetof( Thread_Configured_control, Scheduler_nodes )
        }, {
          offsetof(
            Thread_Configured_control,
            Control.API_Extensions[ THREAD_API_RTEMS ]
          ),
          offsetof( Thread_Configured_control, API_RTEMS )
        }, {
          offsetof(
            Thread_Configured_control,
            Control.libc_reent
          ),
          offsetof( Thread_Configured_control, Newlib )
        }
        #if CONFIGURE_MAXIMUM_THREAD_NAME_SIZE > 1
          , {
            offsetof(
              Thread_Configured_control,
              Control.Join_queue.Queue.name
            ),
            offsetof( Thread_Configured_control, name )
          }
        #endif
      };
 *
 * _Thread_Try_initialize
 *    cpukit/score/src/threadinitialize.c
 *
       for ( i = 0 ; i < _Thread_Control_add_on_count ; ++i ) {
        const Thread_Control_add_on *add_on = &_Thread_Control_add_ons[ i ];

        *(void **) ( (char *) the_thread + add_on->destination_offset ) =
          (char *) the_thread + add_on->source_offset;
      }
 *
 * We don't implement this as above.
 *
 * Instead we do explicit assignments
 * We gather the "offsets":
 *
 *    destination                                   source
 *  Control.Scheduler.nodes                       Scheduler_nodes
 *  Control.API_Extensions[ THREAD_API_RTEMS ]    API_RTEMS
 *  Control.libc_reent                            Newlib
 *  Control.Join_queue.Queue.name                 name
 *
 * The only one relevant to us is  Control.Scheduler.nodes
 *
 * In the RTEMS code, `the_thread` points to a Thread_Control struct that is
 * embedded in a Thread_Configured_control. All the source offsets are beyond
 * the Thread_Control and in the rest of the outer structure
 ******************************************************************************/
inline do_Thread_Control_add_ons( the_thread ) {
  printf("do_Thread_Control_add_ons\n");
  // the_thread ".destination" = the_thread ".source"
  // the_thread.Scheduler.nodes = the_thread.Scheduler_nodes
  the_thread.Scheduler.nodes = 1 ; // 0 is a null pointer
  // start address of TCC.Scheduler_nodes
}


/******************************************************************************
 *  _Thread_queue_Heads_initialize
 *    cpukit/include/rtems/score/threadqimpl.h
 ******************************************************************************/
inline _Thread_queue_Heads_initialize( _heads ) {
  printf("_Thread_queue_Heads_initialize\n");
  ii = 0;
  printf("_TqHi, sched_count = %d\n",sched_count);
  do
  :: ii >= sched_count -> break;
  :: else ->
     printf("_TqHi ii = %d\n",ii);
     // _Chain_Initialize_node( &heads->Priority[ i ].Node ); NOOP(!RTEMS_DEBUG)
     // _Priority_Initialize_empty( &heads->Priority[ i ].Queue );
       // _RBTree_Initialize_node( &heads->Priority[ i ].Queue.Node.Node.RBTree );
                                                           // NOOP(!RTEMS_DEBUG)
       // _RBTree_Initialize_empty( heads->Priority[ i ].Queue->Contributors );
         // RB_INIT( the_rbtree );
     // heads->Priority[ i ].Queue.scheduler = &_Scheduler_Table[ i ];
     _heads.Priority[ii].Queue.scheduler = ii;
     ii++;
  od
  printf("_TqHi heads.Free_chain BEFORE = %d\n",_heads.Free_chain);
  _Chain_Initialize_empty( _heads.Free_chain );
  printf("_TqHi heads.Free_chain AFTER = %d\n",_heads.Free_chain);
  // _Chain_Initialize_node( &heads->Free_node ); NOOP(!RTEMS_DEBUG)
}

Priority_Control TI_priority;
ADDR(TI_scheduler);  // -> Scheduler_Control

/******************************************************************************
 *  _Scheduler_simple_SMP_Node_initialize
 *    cpukit/...
 ******************************************************************************/
byte ITi; // global thread index used for initialization

inline _Scheduler_simple_SMP_Node_initialize(
  TI_scheduler, smp_node, the_thread, prio )
{
  // smp_node = _Scheduler_SMP_Node_downcast( node )
      // node is in fact TCC[smp_node].Base here
  // _Scheduler_SMP_Node_initialize( scheduler, smp_node, the_thread, priority );
  // becomes
  //  _Scheduler_Node_do_initialize( scheduler, &smp_node->Base, thread, priority );
  //  becomes
  //   node->owner = the_thread;
  TCC[smp_node].Base.owneri = ITi;
  //   node->Priority.value = priority;
  TCC[smp_node].Base.value = prio;
  // We set Wait_node index to ITi+1
  TCC[smp_node].Base.iWait_node = smp_node;
  //   _Chain_Initialize_node( &node->Thread.Wait_node ); NOOP !
  //   node->Wait.Priority.scheduler = scheduler;
  PA[TCC[smp_node].Base.iPriority].scheduler = TI_scheduler;
  //   node->user = the_thread;
  TCC[smp_node].Base.user = ITi;
  //   node->idle = NULL;
  TCC[smp_node].Base.idle = 0;
  // #if CPU_SIZEOF_POINTER != 8
  //   _ISR_lock_Initialize( &node->Priority.Lock, "Scheduler Node Priority" );
  // #endif
  // We ignore for now

  //  smp_node->state = SCHEDULER_SMP_NODE_BLOCKED;
  TCC[smp_node].state = SCHEDULER_SMP_NODE_BLOCKED;
  //  smp_node->priority = priority;
  TCC[smp_node]._priority = prio ;
}


/******************************************************************************
 *  _Thread_Initialize_scheduler_and_wait_nodes
 *    cpukit/score/src/threadinitialize.c
 ******************************************************************************/
ADDR(home_scheduler_node); // ->  Scheduler_SMP_Node  in  TCC
ADDR(scheduler_node); // -> Scheduler_SMP_Node  in  TCC
byte scheduler_index;

inline _Thread_Initialize_scheduler_and_wait_nodes( the_thread, config ) {
  printf("_Thread_Initialize_scheduler_and_wait_nodes\n");

  home_scheduler_node = 0;
  scheduler_node = the_thread.Scheduler.nodes;
  printf("scheduler_node = %d\n", scheduler_node);
  TI_scheduler = 0; // &_Scheduler_Table[ 0 ]  a.k.a. _SControl
  scheduler_index = 0;

  do
  ::  scheduler_index >= sched_count_MAX -> break;
  ::  else ->
      printf("scheduler_index = %d\n", scheduler_index);
      printf("TI scheduler = %d\n", TI_scheduler);
      if
      ::  TI_scheduler == config.scheduler ->
          TI_priority = config._priority;
          home_scheduler_node = scheduler_node;
      ::  else ->
          TI_priority = _SControl[TI_scheduler].maximum_priority;
      fi
      printf("home_scheduler_node = %d\n", home_scheduler_node);
      printf("priority = %d\n",TI_priority);

      // _Scheduler_Node_initialize calls scheduler->Operations.node_initialize
      // which is
      _Scheduler_simple_SMP_Node_initialize(
        TI_scheduler, scheduler_node, the_thread, TI_priority );

      scheduler_node++;
      TI_scheduler++;
      scheduler_index++;
  od
  printf("out of loop: home_scheduler_node = %d\n", home_scheduler_node);
  assert( home_scheduler_node) ;

  _Chain_Initialize_one(
    _TControl[ITi].Scheduler.Wait_nodes,
    TCC[home_scheduler_node].Base.iWait_node
  );
  _Chain_Initialize_one(
    _TControl[ITi].Scheduler.Scheduler_nodes,
    TCC[home_scheduler_node].Base.iChain
  );

  _Priority_Node_initialize(
    _TControl[ITi].Real_priority,
    config._priority
  );
  printf("initialized Real_priority\n");

  _Priority_Node_initialize(
    // &home_scheduler_node->Wait.Priority.Node
    TCC[home_scheduler_node].Base.iPriority,
    // &the_thread->Real_priority.priority
    _TControl[ITi].Real_priority
  );
  printf("initialized Base.Priority\n");

  printf("PA[TCC[home_scheduler_node].Base.iPriority].Contributors = %d\n",
   PA[TCC[home_scheduler_node].Base.iPriority].Contributors);

  printf("_TControl[ITi].Real_priority = %d\n", _TControl[ITi].Real_priority);

  printf( "RBT[_TControl[ITi].Real_priority].next = %d\n",
     RBT[_TControl[ITi].Real_priority].next);

  _RBTree_Initialize_one(
    PA[TCC[home_scheduler_node].Base.iPriority].Contributors,
    _TControl[ITi].Real_priority
  );
  printf("initialized Contributors\n");

  //the_thread->Scheduler.home_scheduler = config->scheduler;
  _TControl[ITi].Scheduler.home_scheduler = config.scheduler;
  //_ISR_lock_Initialize( &the_thread->Scheduler.Lock, "Thread Scheduler" );
  _SMP_ticket_lock_Initialize( _TControl[ITi].Scheduler.Ticket_lock );
  //_ISR_lock_Initialize( &the_thread->Wait.Lock.Default, "Thread Wait Default" );
  _SMP_ticket_lock_Initialize( _TControl[ITi].Wait.Lock.Default );
  //_Thread_queue_Gate_open( &the_thread->Wait.Lock.Tranquilizer );
  AtomicStore( _TControl[ITi].Wait.Lock.Tranquilizer.go_ahead, 1 );

  //_RBTree_Initialize_node( &the_thread->Wait.Link.Registry_node );
  // NOOP

  printf("\n *** _Thread_Initialize_scheduler_and_wait_nodes DONE ***\n\n");

}
/******************************************************************************
 *  _Thread_Initialize
 *    cpukit/score/src/threadinitialize.c
 * We just go straight into _Thread_Try_initialize and ignore checks
 ******************************************************************************/
inline _Thread_Initialize( information, the_thread, config ) {

  // Per_CPU_Control         *cpu = _Per_CPU_Get_by_index( 0 );
  //     *cpu = &_Per_CPU_Information[ 0 ].per_cpu
  //   *cpu == ITi

  printf("_Thread_Initialize\n");
    // memset( &the_thread->Join_queue, 0,
  //   information->Objects.object_size - offsetof( Thread_Control, Join_queue )
  // );
  // Promela does an implicit memset(...,0,...) everywhere

  do_Thread_Control_add_ons( the_thread );

  // the_thread->Wait.spare_heads = _Freechain_Pop(
  //   &information->Thread_queue_heads.Free
  // );
  _Freechain_Pop( information.Free, the_thread.Wait.spare_heads );
  printf("the_thread.Wait.spare_heads = %d\n",the_thread.Wait.spare_heads);

  _Thread_queue_Heads_initialize( _TqH[the_thread.Wait.spare_heads] );

  the_thread.Start.isr_level = config.isr_level ;
  the_thread.Start.is_preemptible = config.is_preemptible;

  _Thread_Initialize_scheduler_and_wait_nodes( the_thread, config );


  // more to come - see threadinitialize-unfold.c
  // _Thread_Set_CPU( the_thread, cpu );
  // We are running on cpu 0 right now
  the_thread.Scheduler.cpui = 0;

  the_thread.current_state = STATES_DORMANT;
  the_thread.Start.initial_priority  = config._priority;

  // _Thread_Action_control_initialize( &the_thread->Post_switch_actions );
  _Chain_Initialize_empty( the_thread.Post_switch_actions );

  printf("Thread cpu=%d, curr.st=%e, init.prio=%d, post-sw=%d\n",
    the_thread.Scheduler.cpui,
    the_thread.current_state,
    the_thread.Start.initial_priority,
    the_thread.Post_switch_actions);


/*
  {-
   * We do following checks of simple error conditions after the thread is
   * fully initialized to simplify the clean up in case of an error.  With a
   * fully initialized thread we can simply use _Thread_Free() and do not have
   * to bother with partially initialized threads.
   -}
  if (
    !config->is_preemptible
      && !_Scheduler_Is_non_preempt_mode_supported( config->scheduler )
  ) {
    return false;
  }
  if (
    config->isr_level != 0
#if CPU_ENABLE_ROBUST_THREAD_DISPATCH == FALSE
      && _SMP_Need_inter_processor_interrupts()
#endif
  ) {
    return false;
  }

*/
  printf("INITIALIZATIION COMPLETE FOR TASK %d\n",ITi);
}



inline InitThreads() {
  ITi = 0;

  printf( "\n*** InitThread0\n");
  InitThread0() ; // Static setup of _RTEMS_tasks_Information
  printf("\nTask count = %d\n",task_count);
  do
  ::  ITi >= task_count -> break ;
  ::  else ->
      printf( "\n** Initialising Thread %d\n", ITi ) ;
      // modelled on _RTEMS_tasks_Create
      _TConfig[ITi].scheduler = task_info[ITi].task_home_scheduler ;  // Sched-Home(Thrd-Get-Exec)
      _TConfig[ITi]._priority = task_info[ITi].initial_priority;

      _Thread_Initialize( _RTEMS_tasks_Information,
                          _TControl[ITi],
                          _TConfig[ITi] );
      printf("Thread %d now setup!\n",ITi);
      ITi++ ;
  od
}


inline Init() {

  printf("Initialising...\n");

  // We assume aseqno = 0 here.
  ChooseScenario();
  InitSchedulers();
  InitThreads();

}

#endif
