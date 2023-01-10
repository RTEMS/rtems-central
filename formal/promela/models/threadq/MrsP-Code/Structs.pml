/* SPDX-License-Identifier: BSD-2-Clause */

/*******************************************************************************
 * Structs.pml
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

/*******************************************************************************
 * Important Notes
 *
 * These are simplified versions of the actual RTEMS structs. Only fields that
 * are relevant to the code under verification are included.
 *
 * As a result of pre-processor settings, there are a number of structs that
 * just have a single field, which is itself a struct. Some of these structs
 * themselves also have a single struct field. We basically collapse these
 * down to the underlying struct. Places below where this has happened are
 * flagged with the phrase "short-circuit" (abbrev. "s.c.").
 *
 * Many of the RTEMS structs have other structs embedded in them. A lot of
 * initialization is done with arrays of these large structs, and then various
 * lists being built by pointing at the embedded structures. We cannot reproduce
 * this directly in Promela.
 * Instead, we have to factor those structs out in their own arrays, and replace
 * the embedded struct by an index into the appropriate array. It is also
 * necessary to have a naming convention that makes it easy to remember when an
 * array lookup is required.
 *
 * In addition, any variable or struct field that is declared as a pointer has
 * to be modelled as an index into the appropriate array.
 *
 * The only construct in Promela that supports the use of locally scopes names
 * is the `proctype`, which defines a running process. The other abstraction
 * language feature `inline` is basically just a text replacement mechanism,
 * just like that provided by the C preprocessor. We need to be very careful
 * to ensure that inline argument identifiers do not clash with those used in
 * structs and other variables
 * In addition, we can only model local variables in C code by global variables,
 * in an array indexed by task numbers. An array is required because each task
 * could be running the same code at the same time. We do not need to model
 * stacks because there is no recursion.
 *
 * Naming Convention
 *
 * As far as possible, we use the same names in Promela as found in the RTEMS
 * sources
 *
 * For an embedded struct called "SubStruct",
 *   we replace it with an array index called "iSubStruct".
 *
 * For a C pointer called "pointer", we replace it with "pointeri".
 *
 * All inline formal parameters will start with an underscore.
 *
 * For a local variable "var", we replace it with "XXvar1[taskno]",
 *  where "XX" is a short string that identifies the relevant function.
 * If the same name is used in a lower call that can have a different value,
 * then we increment the number ("XXvar2[..]","XXvar3[],..").
 *
 * The exception is for initialization, where there is only one Promela process
 * active, where we use the form "XX_var".
 *
 ******************************************************************************/

#ifndef _STRUCTS
#define _STRUCTS

#define Atomic_Uint byte
#define rtems_id byte
#define States_Control byte

#include "Sizing.pml"
#include "Chains.pml"
#include "RBTrees.pml"
#include "Priority.pml"

/*******************************************************************************
 * typedef struct {
 *   Atomic_Uint next_ticket ;
 *   Atomic_Uint now_serving ;
 * } SMP_ticket_lock_Control ;
 *
 * Note following shortcut:
 * typedef struct {
 *   SMP_ticket_lock_Control Ticket_lock;
 * } SMP_lock_Control;
 ******************************************************************************/
typedef SMP_ticket_lock_Control {
  byte  next_ticket ;
; byte  now_serving ;
}

/*******************************************************************************
 * typedef struct {
 *   Chain_Node Node ;
 *   Atomic_Uint go_ahead ;
 * } Thread_queue_Gate ;
 ******************************************************************************/
typedef Thread_queue_Gate {
  Chain_Node Node ;
  Atomic_Uint go_ahead;
}


/*******************************************************************************
 * struct Thread_queue_Queue {
 *   SMP_ticket_lock_Control Lock;
 *   Thread_queue_Heads *heads;
 *   Thread_Control *owner;
 *   const char *name;
 * };
 ******************************************************************************/
typedef Thread_queue_Queue {
  SMP_ticket_lock_Control Lock;
  ADDR(headsi);
  ADDR(owneri);
  // other fields to be added if required
}

/*******************************************************************************
 *  Unamed internal struct
 *    (inside Thread_queue_Lock_context).
 *     struct {
 *       Thread_queue_Gate Gate;
 *       Thread_queue_Queue *queue;
 *     } Wait;
 ******************************************************************************/
typedef TqLC_Wait {
  Thread_queue_Gate Gate;
  // other fields to be added if required
}

/*******************************************************************************
 * typedef struct {
 *   ISR_lock_Context Lock_context;
 *   struct {
 *     Thread_queue_Gate Gate;
 *     Thread_queue_Queue *queue;
 *   } Wait;
 * } Thread_queue_Lock_context;
 ******************************************************************************/
typedef Thread_queue_Lock_context {
  TqLC_Wait Wait;
}

/*******************************************************************************
 * struct Thread_queue_Context {
 *   Thread_queue_Lock_context Lock_context;
 *   States_Control thread_state;
 *   Thread_queue_Enqueue_callout enqueue_callout;
 *   union {
 *     Watchdog_Interval ticks;
 *     const void *arg;
 *   } Timeout;
 *   bool timeout_absolute;
 *   struct {
 *     Chain_Control Links;
 *     Thread_queue_Link Start;
 *     Thread_queue_Link Deadlock;
 *   } Path;
 *   struct {
 *     Priority_Actions Actions;
 *     size_t update_count;
 *     Thread_Control *update[ 2 ];
 *   } Priority;
 *   Thread_queue_Deadlock_callout deadlock_callout;
 * };
 ******************************************************************************/
typedef TcC_Priority {
  byte update_count;
}

typedef Thread_queue_Context {
  Thread_queue_Lock_context Lock_context ;
  byte enqueue_callout ;
  byte deadlock_callout ;
  TcC_Priority Priority ;
}

/*******************************************************************************
 *  Unamed internal struct (inside Thread_Wait_information).
 *     struct {
 *       ISR_lock_Control Default ; // SMP_ticket_lock_Control - short circuit.
 *       Chain_Control Pending_requests ;
 *       Thread_queue_Gate Tranquilizer ;
 *     } Lock ;
 ******************************************************************************/
typedef TW_Lock {
  SMP_ticket_lock_Control Default;
  Chain_Control Pending_requests ;
  Thread_queue_Gate Tranquilizer ;
}

/*******************************************************************************
 * typedef struct {
 *   RBTree_Node Registry_node;
 *   Thread_queue_Queue *source;
 *   Thread_queue_Queue *target;
 *   Chain_Node Path_node;
 *   Thread_Control *owner;
 *   Thread_queue_Lock_context Lock_context;
 * } Thread_queue_Link;
 ******************************************************************************/

/*******************************************************************************
 *   typedef struct {
 *     uint32_t count ;
 *     void * return_argument ;
 *     Thread_Wait_information_Object_argument_type
 *     return_argument_second ;
 *     uint32_t option ;
 *     uint32_t return_code ;
 *     Atomic_Uint flags ;
 *     struct {
 *       ISR_lock_Control Default ;
 *       Chain_Control Pending_requests ;
 *       Thread_queue_Gate Tranquilizer ;
 *     } Lock ;
 *     Thread_queue_Link Link ;
 *     Thread_queue_Queue * queue ;
 *     const Thread_queue_Operations * operations ;
 *     Thread_queue_Heads * spare_heads ;
 *   } Thread_Wait_information ;
 ******************************************************************************/
typedef Thread_Wait_information {
  TW_Lock Lock;
  // Thread_queue_Link Link -- to be done when we actually 'touch' it.
  ADDR(spare_heads); // of Thread_queue_Heads, indexing from 0 into:
  // Thread_queue_Configured_heads _RTEMS_tasks_Heads[task_count_MAX];
}


/*******************************************************************************
 * 
 ******************************************************************************/
#define Processor_mask( var) BITS(cpu_count_MAX,var)

/*******************************************************************************
 * 
 * typedef struct {
 *   const struct _Scheduler_Control *scheduler;
 *   void *stack_area;
 *   size_t stack_size;
 *   // It shall not be NULL.  Use _Objects_Free_nothing() if nothing is to free.
 *   void ( *stack_free )( void * );
 *   Priority_Control priority;
 *   Thread_CPU_budget_algorithms budget_algorithm;
 *   Thread_CPU_budget_algorithm_callout budget_callout;
 *   uint32_t cpu_time_budget;
 *   uint32_t name;
 *   uint32_t isr_level;
 *   bool is_fp;
 *   bool is_preemptible;
 * } Thread_Configuration;
 * 
 ******************************************************************************/
typedef Thread_Configuration {
  ADDR(scheduler);
  Priority_Control _priority; // 'priority' is a Promela keyword
  byte isr_level;
  byte is_preemptible ;
}

/*******************************************************************************
 * typedef struct {
 *   ISR_lock_Control Lock;
 *   Thread_Scheduler_state state;
 *   const struct _Scheduler_Control *home_scheduler;
 *   const struct _Scheduler_Control *pinned_scheduler;
 *   struct Per_CPU_Control *cpu;
 *   Chain_Control Wait_nodes;
 *   Chain_Control Scheduler_nodes;
 *   Chain_Node Help_node;
 *   size_t helping_nodes;
 *   Scheduler_Node *requests;
 *   int pin_level;
 *   Processor_mask Affinity;
 *   Scheduler_Node *nodes;
 * } Thread_Scheduler_control;
 ******************************************************************************/
typedef Thread_Scheduler_control {
  SMP_ticket_lock_Control Ticket_lock; // Lock.SMP_lock_Control.Ticket_lock
  byte home_scheduler ;
  ADDR(cpui) ; // -> Per_CPU_Control, no array as yet
  Chain_Control Wait_nodes;
  Chain_Control Scheduler_nodes;
  ADDR(nodes); // -> Scheduler_Node
}

/*******************************************************************************
 * typedef struct {
 *   Thread_queue_Queue Queue; // The actual thread queue.
 * } Thread_queue_Control;
 * WE CAN SHORT-CIRCUIT THIS
 ******************************************************************************/


/*******************************************************************************
 * typedef struct {
 *   Thread_Entry_information             Entry;
 *   bool                                 is_preemptible;
 *   Thread_CPU_budget_algorithms         budget_algorithm;
 *   Thread_CPU_budget_algorithm_callout  budget_callout;
 *   uint32_t                             isr_level;
 *   Priority_Control                     initial_priority;
 *   void                              ( *stack_free )( void * );
 *   Stack_Control                        Initial_stack;
 * } Thread_Start_information;
 * 
 ******************************************************************************/
typedef Thread_Start_information {
  bool is_preemptible;
  byte isr_level;
  Priority_Control initial_priority ;
}

/*******************************************************************************
 * typedef struct {
 *   Chain_Control Chain;
 * } Thread_Action_control;
 ******************************************************************************/

/*******************************************************************************
 *   We mark add_on destinations with D
 *   struct _Thread_Control {
 *     Objects_Control Object ;
 *   D Thread_queue_Control Join_queue ; // zeroed from here
 *     States_Control current_state ;
 *     Priority_Node Real_priority ;
 *   D Thread_Scheduler_control Scheduler ;
 *     Thread_Wait_information Wait ;
 *     Thread_Timer_information Timer ;
 *     / * ================= end of common block ================= * /
 *     bool is_idle ;
 *     bool is_preemptible ;
 *     bool is_fp ;
 *     bool was_created_with_inherited_scheduler ;
 *     uint32_t cpu_time_budget ;
 *     Thread_CPU_budget_algorithms budget_algorithm ;
 *     Thread_CPU_budget_algorithm_callout budget_callout ;
 *     Timestamp_Control cpu_time_used ;
 *     Thread_Start_information Start ;
 *     Thread_Action_control Post_switch_actions ;
 *     Context_Control Registers ;
 *     #if ( CPU_HARDWARE_FP == TRUE ) || ( CPU_SOFTWARE_FP == TRUE )
 *     Context_Control_fp * fp_context ;
 *     # endif
 *   D struct _reent * libc_reent ;
 *   D void * API_Extensions [ THREAD_API_LAST + 1 ];
 *     Thread_Keys_information Keys ;
 *     Thread_Life_control Life ;
 *     Thread_Capture_control Capture ;
 *     struct rtems_user_env_t * user_environment ;
 *     struct _pthread_cleanup_context * last_cleanup_context ;
 *     struct User_extensions_Iterator * last_user_extensions_iterator ;
 *     void * extensions [ RTEMS_ZERO_LENGTH_ARRAY ];
 *   };
 ******************************************************************************/
typedef Thread_Control {
  //Thread_queue_Control Join_queue ; // D
  Thread_queue_Queue Queue // short circuits Join_queue.Queue
  States_Control current_state ;
  ADDR(Real_priority) ; // -> Priority_Node in PN[]
  Thread_Scheduler_control Scheduler ; // D
  Thread_Wait_information Wait;
  // uncommon block below
  Thread_Start_information Start;
  Chain_Control Post_switch_actions ; // s.c. through Thread_Action_control
}

/*******************************************************************************
 * typedef struct {
 *   Priority_Aggregation *actions;
 * } Priority_Actions;
 ******************************************************************************/

/*******************************************************************************
 * typedef struct {
 *   Thread_queue_Control Wait_queue; // manage ownership and waiting threads
 *   Priority_Node Ceiling_priority;  // used by the owner thread.
 *   // One ceiling priority per scheduler instance.
 *   Priority_Control ceiling_priorities[ RTEMS_ZERO_LENGTH_ARRAY ];
 * } MRSP_Control;
 ******************************************************************************/
typedef MRSP_Control {
  // SHORT CIRCUIT through Queue in Thread_queue_Control
  Thread_queue_Queue Wait_queue;
  ADDR(Ceiling_priority);
  Priority_Control ceiling_priorities[sched_count_MAX];
}

/*******************************************************************************
 * typedef struct {
 *   Objects_Control Object;
 *   union {  //-- only interested in TQ & MRSP variants
 *     Thread_queue_Control Wait_queue;
 *     // CORE_ceiling_mutex_Control Mutex;
 *     // CORE_semaphore_Control Semaphore;
 *     MRSP_Control MRSP;
 *   } Core_control;
 * }   Semaphore_Control;
 ******************************************************************************/
typedef Semaphore_Control {
  MRSP_Control MRSP ;
  // Thread_queue_Control Wait_queue ;  // Needed above somewhere
}

/*******************************************************************************
 * typedef struct {
 *   ISR_Level isr_level;
 * } SMP_lock_Context;
 * 
 * typedef struct {
 *   SMP_lock_Context Lock_context;
 * } ISR_lock_Context;
 ******************************************************************************/

/*******************************************************************************
 * typedef struct {
 *   SMP_ticket_lock_Control Ticket_lock;
 * } SMP_lock_Control;
 * 
 * typedef struct {
 *   SMP_lock_Control Lock;
 * } ISR_lock_Control;
 * 
 * #define ISR_LOCK_MEMBER( _designator ) ISR_lock_Control _designator;
 * 
 * typedef BITSET_DEFINE( Processor_mask, CPU_MAXIMUM_PROCESSORS ) Processor_mask;
 * 
 * typedef struct Scheduler_Context {
 *   ISR_LOCK_MEMBER( Lock ) // ISR_lock_Control Lock
 *   //
 *   Processor_mask Processors;
 * } Scheduler_Context;
 ******************************************************************************/
typedef Scheduler_Context {
  SMP_ticket_lock_Control Ticket_lock // Lock.SMP_lock_Control.Ticket_lock
  Processor_mask(Processors);
}

/*******************************************************************************
 * typedef struct {
 *   Scheduler_Context Base; // short circuit !
 *   Chain_Control Scheduled;
 *    * Idle threads are used for the scheduler helping protocol.  It is crucial
 *    * that the idle threads preserve their relative order.  This is the case for
 *    * this priority based scheduler.
 *   Chain_Control Idle_threads;
 * } Scheduler_SMP_Context;
 ******************************************************************************/
typedef Scheduler_SMP_Context {
  // Scheduler_Context Base ;
  SMP_ticket_lock_Control Ticket_lock // Lock.SMP_lock_Control.Ticket_lock
  Processor_mask(Processors);
  Chain_Control Scheduled ;
  Chain_Control Idle_threads;
}

/*******************************************************************************
 * typedef struct {
 *   Scheduler_SMP_Context Base; // short curcuit
 *   Chain_Control         Ready;
 * } Scheduler_simple_SMP_Context;
 ******************************************************************************/
typedef Scheduler_simple_SMP_Context {
  // Scheduler_SMP_Context Base;
  // Scheduler_Context Base ;
  SMP_ticket_lock_Control Ticket_lock // Lock.SMP_lock_Control.Ticket_lock
  Processor_mask(Processors);
  Chain_Control Scheduled ;
  Chain_Control Idle_threads;
  Chain_Control Ready;
}


/*******************************************************************************
 * typedef struct {
 *   void (*initialize)(Scheduler_Control*);
 *   void (*schedule)(Scheduler_Control*, Thread_Control*);
 *   void (*yield)(Scheduler_Control*, Thread_Control*,Scheduler_Node*);
 *   void (*block)(Scheduler_Control*,Thread_Control*,Scheduler_Node*);
 *   void (*unblock)(Scheduler_Control*,Thread_Control*,Scheduler_Node*);
 *   void (*update_priority )(Scheduler_Control*,Thread_Control*,Scheduler_Node*);
 *   Priority_Control (*map_priority )(Scheduler_Control*,Priority_Control);
 *   Priority_Control (*unmap_priority )(Scheduler_Control*,Priority_Control);
 *   bool (*ask_for_help)
 *        (Scheduler_Control *scheduler,Thread_Control*,Scheduler_Node*);
 *   void (*reconsider_help_request)
 *       (Scheduler_Control*,Thread_Control*,Scheduler_Node*);
 *   void (*withdraw_node)
 *     (Scheduler_Control*,Thread_Control*,Scheduler_Node*,Thread_Scheduler_state);
 *   void (*pin)
 *    (Scheduler_Control*,Thread_Control*,Scheduler_Node*,struct Per_CPU_Control*);
 *   void (*unpin)
 *    (Scheduler_Control*,Thread_Control*,Scheduler_Node*,struct Per_CPU_Control*);
 *   void (*add_processor)(
 *     Scheduler_Control*,
 *     Thread_Control*
 *   );
 *   Thread_Control *(*remove_processor)(
 *     Scheduler_Control*,
 *     struct Per_CPU_Control*
 *   );
 *   void (*node_initialize)(
 *     Scheduler_Control*,
 *     Scheduler_Node*,
 *     Thread_Control*,
 *     Priority_Control
 *   );
 *   void (*node_destroy)( Scheduler_Control*, Scheduler_Node * );
 *   void (*release_job) (
 *     Scheduler_Control*,
 *     Thread_Control*,
 *     Priority_Node*,
 *     uint64_t,
 *     Thread_queue_Context *
 *   );
 *   void (*cancel_job) (
 *     Scheduler_Control*,
 *     Thread_Control*,
 *     Priority_Node*,
 *     Thread_queue_Context*
 *   );
 *   void (*tick)(Scheduler_Control*,Thread_Control*);
 *   void (*start_idle )(
 *     Scheduler_Control*,
 *     Thread_Control*,
 *     struct Per_CPU_Control*
 *   );
 *   Status_Control (*set_affinity)
 *        (Scheduler_Control*,Thread_Control*,Scheduler_Node*,Processor_mask*);
 * } Scheduler_Operations;
 * 
 * 
 * 
 * struct _Scheduler_Control { // aka  Scheduler_Control
 *   Scheduler_Context *context;
 *   Scheduler_Operations Operations;
 *   Priority_Control maximum_priority;
 *   uint32_t name;
 *   bool is_non_preempt_mode_supported; // not relevent (always false)
 * };
 ******************************************************************************/
typedef Scheduler_Control {
  Scheduler_simple_SMP_Context context ;
  // Scheduler_Operations Operations ;
  Priority_Control maximum_priority ;
}

/*******************************************************************************
 * typedef struct {
 *   Scheduler_Control *scheduler;
 *   uint32_t attributes; // SCHEDULER_ASSIGN_PROCESSOR_{MANDATORY|OPTIONAL}
 * } Scheduler_Assignment;
 ******************************************************************************/
typedef Scheduler_Assignment {
  Scheduler_Control scheduler;
  bool attributes ;  // is mandatory?   Optional, if not.
}

/*******************************************************************************
 * typedef struct {
 *   Chain_Node Node;
 *   Priority_Aggregation Queue;
 *   struct Scheduler_Node *scheduler_node;
 * } Thread_queue_Priority_queue;
 ******************************************************************************/
typedef Thread_queue_Priority_queue {
  Chain_Node Node;
  Priority_Aggregation Queue;
  ADDR(scheduler_node);
}

/*******************************************************************************
 * typedef struct _Thread_queue_Heads {
 *   union {
 *     Chain_Control Fifo;
 *     // alternate not here if doing RTEMS_SMP
 *   } Heads;
 *   Chain_Control Free_chain;
 *   Chain_Node Free_node;
 *   Thread_queue_Priority_queue Priority[ RTEMS_ZERO_LENGTH_ARRAY ];
 * } Thread_queue_Heads;
 ******************************************************************************/
typedef Thread_queue_Heads {
  Chain_Control Fifo; // short circuit for Heads.Fifo
  Chain_Control Free_chain;
  Chain_Node Free_Node;
  // BELOW ALSO IN  Thread_queue_Configured_heads WHICH CONTAINS THIS STRUCT
  Thread_queue_Priority_queue Priority[sched_count_MAX]; //
}



/*******************************************************************************
 * Currently needed:
 * Per_CPU_State
 * Per_CPU_Control
 * 
 * 
 * typedef enum {
 *   PER_CPU_STATE_INITIAL,
 *   PER_CPU_STATE_READY_TO_START_MULTITASKING,
 *   PER_CPU_STATE_UP,
 *   PER_CPU_STATE_SHUTDOWN
 * } Per_CPU_State;
 * 
 * typedef struct Per_CPU_Control {
 *   #if CPU_PER_CPU_CONTROL_SIZE > 0  // == 8 if sparc has FPU, 0 otherwise
 *     CPU_Per_CPU_control cpu_per_cpu;
 *   #endif
 *   void *interrupt_stack_low;
 *   void *interrupt_stack_high;
 *   uint32_t isr_nest_level;
 *   uint32_t isr_dispatch_disable;
 *   volatile uint32_t thread_dispatch_disable_level;
 *   volatile bool dispatch_necessary;
 *   bool reserved_for_executing_alignment[ 3 ];
 *   struct _Thread_Control *executing;
 *   struct _Thread_Control *heir;
 *   CPU_Interrupt_frame Interrupt_frame;
 *   Timestamp_Control cpu_usage_timestamp;
 *   struct {
 *     ISR_LOCK_MEMBER( Lock )
 *     uint64_t ticks;
 *     Watchdog_Header Header[ PER_CPU_WATCHDOG_COUNT ];
 *   } Watchdog;
 *     ISR_lock_Control Lock;
 *     ISR_lock_Context Lock_context;
 *     Chain_Control Threads_in_need_for_help;
 *     Atomic_Ulong message;
 *     struct {
 *       const struct _Scheduler_Control *control;
 *       const struct Scheduler_Context *context;
 *       struct _Thread_Control *idle_if_online_and_unused;
 *     } Scheduler;
 *     struct _Thread_Control *ancestor;
 *     char *data;
 *     Atomic_Uint state;
 *     struct {
 *       ISR_lock_Control Lock;
 *       struct Per_CPU_Job *head;
 *       struct Per_CPU_Job **tail;
 *     } Jobs;
 *     bool online;
 *     bool boot;
 *   struct Record_Control *record;
 *   Per_CPU_Stats Stats;
 * } Per_CPU_Control;
 * 
 * 
 * typedef struct {
 *   Chain_Node     Node;
 *   Objects_Id     id;
 *   Objects_Name   name;
 * } Objects_Control;
 * 
 * struct Objects_Information {
 *   Objects_Id maximum_id;
 *   Objects_Control **local_table;
 *   Objects_Control *( *allocate )( Objects_Information * );
 *   void ( *deallocate )( Objects_Information *, Objects_Control * );
 *   Objects_Maximum inactive;
 *   Objects_Maximum objects_per_block;
 *   uint16_t object_size;
 *   uint16_t name_length;
 *   Chain_Control Inactive;
 *   Objects_Maximum *inactive_per_block;
 *   Objects_Control **object_blocks;
 *   Objects_Control *initial_objects;
 * };
 * 
 ******************************************************************************/


/*******************************************************************************
 * struct Thread_queue_Configured_heads {
 *     Thread_queue_Heads Heads;
 *     Thread_queue_Priority_queue Priority[ CONFIGURE_SCHEDULER_COUNT ];
 * };
 * 
 * typedef struct {
 *   Chain_Control Free; // short-circuit
 * } Freechain_Control;
 ******************************************************************************/
typedef Thread_queue_Configured_heads {
  Thread_queue_Heads Heads ;
  Thread_queue_Priority_queue Priority[sched_count_MAX];
}

/*******************************************************************************
 * typedef struct {
 *   Chain_Control Free; // short-circuit?
 * } Freechain_Control;
 * // We provide an array of its nodes as well
 ******************************************************************************/
typedef Freechain_Control {
  Chain_Control Free;
  Chain_Node nodes[sched_count_MAX+1]; // index from 1
}

/*******************************************************************************
 * typedef struct {
 *   Objects_Information Objects;
 *   union {
 *     //This is set by <rtems/confdefs.h> via THREAD_INFORMATION_DEFINE().
 *     Thread_queue_Configured_heads *initial;
 *     // This member is initialized by _Thread_Initialize_information().
 *     Freechain_Control Free; // short circuit of Chain_Control
 *   } Thread_queue_heads ; // shortcut into union
 * } Thread_Information;
 ******************************************************************************/
typedef Thread_Information {
  // We ignore Objects for now
  Freechain_Control Free;
  // union
  ADDR(initial);
}


/*******************************************************************************
 * struct Scheduler_Node {
 *   union {
 *     Chain_Node Chain;
 *     RBTree_Node RBTree;
 *   } Node;
 *   int sticky_level;
 *   struct _Thread_Control *user; // owner or idle thread
 *   struct _Thread_Control *idle;
 *   struct _Thread_Control *owner;
 *   //  Block to register and manage this scheduler node in the thread
 *   //  control block of the owner of this scheduler node.
 *   struct {
 *     Chain_Node Wait_node;
 *     union {
 *       Chain_Node Chain; // add to scheduler nodes
 *       Scheduler_Node *next; // add to temporary remove list.
 *     } Scheduler_node;
 *     Scheduler_Node *next_request;
 *     Scheduler_Node_request request;
 *   } Thread;
 *   struct {
 *     Priority_Aggregation Priority;
 *   } Wait;
 *   struct {
 *     Priority_Control value; // CPU_SIZEOF_POINTER != 8
 *     ISR_lock_Control Lock;
 *   } Priority;
 * };
 ******************************************************************************/
typedef Scheduler_Node {
  byte sticky_level ;
  ADDR(user); // -> Thread_Control
  ADDR(idle); // -> Thread_Control
  ADDR(owneri); // -> Thread_Control
  ADDR(iWait_node); // short-circuit Thread -> Chain_Node CN[]
  ADDR(iChain); // short-circuit Thread.Scheduler_node -> Chain_Node CN[]
  // We don't model ISR_lock_Control here for now
  ADDR(iPriority); // short-circuit Wait -> Priority_Aggregation PA[...]
  Priority_Control value; // Short circuit Priority
}

/*******************************************************************************
 * typedef enum {
 *    // A scheduler node is blocked if the corresponding thread is not ready.
 *   SCHEDULER_SMP_NODE_BLOCKED,
 * 
 *    // A scheduler node is scheduled if the corresponding thread is ready and the
 *    // scheduler allocated a processor for it.  A scheduled node is assigned to
 *    // exactly one processor.  The count of scheduled nodes in this scheduler
 *    // instance equals the processor count owned by the scheduler instance.
 *   SCHEDULER_SMP_NODE_SCHEDULED,
 * 
 *    // A scheduler node is ready if the corresponding thread is ready and the
 *    // scheduler did not allocate a processor for it.
 *   SCHEDULER_SMP_NODE_READY
 * } Scheduler_SMP_Node_state;
 ******************************************************************************/
#define SCHEDULER_SMP_NODE_BLOCKED 0
#define SCHEDULER_SMP_NODE_SCHEDULED 1
#define SCHEDULER_SMP_NODE_READY 2
#define Scheduler_SMP_Node_state(name) unsigned name : 2
// see include/rtems/score/schedulersmpimpl.h

/*******************************************************************************
 * typedef struct {
 *   Scheduler_Node Base;
 *   Scheduler_SMP_Node_state state;
 *   Priority_Control priority;
 * } Scheduler_SMP_Node;
 ******************************************************************************/
typedef Scheduler_SMP_Node {
  Scheduler_Node Base;
  Scheduler_SMP_Node_state(state);
  Priority_Control _priority; // "priority" is PML keyword
}

/*******************************************************************************
 * typedef union {
 *   Scheduler_Node Base;
 *   Scheduler_SMP_Node Simple_SMP;
 * } Configuration_Scheduler_node;
 ******************************************************************************/
typedef Configuration_Scheduler_node { // union
  Scheduler_Node Base;
  Scheduler_SMP_Node Simple_SMP;
}

/*******************************************************************************
 *   We mark add_on destinations with D
 *   We mark add_on sources with S
 * 
 *  Control.Scheduler.nodes                       Scheduler_nodes
 *  Control.API_Extensions[ THREAD_API_RTEMS ]    API_RTEMS
 *  Control.libc_reent                            Newlib
 *  Control.Join_queue.Queue.name                 name
 * 
 * struct Thread_Configured_control {
 * D  Thread_Control Control;
 * S  Configuration_Scheduler_node Scheduler_nodes[_CONFIGURE_SCHEDULER_COUNT];
 * S  RTEMS_API_Control API_RTEMS;
 * S  char name[ CONFIGURE_MAXIMUM_THREAD_NAME_SIZE ];
 * S  struct {} Newlib;
 * };
 * 
 * We only model the add-ons after the Thread_Control, and we are only
 * interested in one of those.
 ******************************************************************************/
typedef Thread_Configured_control {
    //Thread_Control Control; // found elsewhere
    Configuration_Scheduler_node Scheduler_nodes[sched_count_MAX];
    // RTEMS_API_Control API_RTEMS;
    // char name[ 4 ];
    // struct {} Newlib;
}


/*******************************************************************************
 * irr/taskdata.h
 * typedef struct {
 *   Event_Control            Event;
 *   Event_Control            System_event;
 *   ASR_Information          Signal;
 *   Thread_Action            Signal_action;
 * }  RTEMS_API_Control;
 *  NOT RELEVANT?
 ******************************************************************************/



/*******************************************************************************
 * typedef struct {
 *   Atomic_Uint value;
 *   Atomic_Uint sense;
 * } SMP_barrier_Control;
 ******************************************************************************/
typedef SMP_barrier_Control {
  Atomic_Uint value;
  Atomic_Uint sense;
}


/*******************************************************************************
 ******************************************************************************/




/*******************************************************************************
 * low level startup stuff
 * typedef struct {
 *   rtems_name name;
 *   size_t stack_size;
 *   rtems_task_priority initial_priority;
 *   rtems_attribute attribute_set;
 *   rtems_task_entry entry_point;
 *   rtems_mode mode_set;
 *   rtems_task_argument argument;
 * } rtems_initialization_tasks_table;
 ******************************************************************************/

/*******************************************************************************
 * typedef struct Per_CPU_Control {
 *   void *interrupt_stack_low;
 *   void *interrupt_stack_high;
 *   uint32_t isr_nest_level;
 *   uint32_t isr_dispatch_disable;
 *   volatile uint32_t thread_dispatch_disable_level;
 *   volatile bool dispatch_necessary;
 *   bool reserved_for_executing_alignment[ 3 ];
 *   struct _Thread_Control *executing;
 *   struct _Thread_Control *heir;
 *   CPU_Interrupt_frame Interrupt_frame;
 *   Timestamp_Control cpu_usage_timestamp;
 *   struct {
 *     ISR_LOCK_MEMBER( Lock )
 *     uint64_t ticks;
 *     Watchdog_Header Header[ PER_CPU_WATCHDOG_COUNT ];
 *   } Watchdog;
 *     ISR_lock_Control Lock;
 *     ISR_lock_Context Lock_context;
 *     Chain_Control Threads_in_need_for_help;
 *     Atomic_Ulong message;
 *     struct {
 *       const struct _Scheduler_Control *control;
 *       const struct Scheduler_Context *context;
 *       struct _Thread_Control *idle_if_online_and_unused;
 *     } Scheduler;
 *     struct _Thread_Control *ancestor;
 *     char *data;
 *     Atomic_Uint state;
 *     struct {
 *       ISR_lock_Control Lock;
 *       struct Per_CPU_Job *head;
 *       struct Per_CPU_Job **tail;
 *     } Jobs;
 *     bool online;
 *     bool boot;
 *   struct Record_Control *record;
 *   Per_CPU_Stats Stats;
 * } Per_CPU_Control;
 * 
 * typedef struct {
 *   Per_CPU_Control per_cpu;
 *   char unused_space_for_cache_line_alignment
 *     [ PER_CPU_CONTROL_SIZE - sizeof( Per_CPU_Control ) ];
 * } Per_CPU_Control_envelope;
 ******************************************************************************/
typedef Per_CPU_Control {
  bool online; // enough for now
}


/*******************************************************************************
 * We finish with the test context structures used in the smpmrsp01 test
 * 
 * typedef struct {
 *   uint32_t sleep;
 *   uint32_t timeout;
 *   uint32_t obtain[MRSP_COUNT];
 *   uint32_t cpu[CPU_COUNT];
 * } counter;
 * 
 * typedef struct {
 *   uint32_t cpu_index;
 *   const Thread_Control *executing;
 *   const Thread_Control *heir;
 *   const Thread_Control *heir_node;
 *   Priority_Control heir_priority;
 * } switch_event;
 * 
 * typedef struct {
 *   rtems_id main_task_id;
 *   rtems_id migration_task_id;
 *   rtems_id low_task_id[2];
 *   rtems_id high_task_id[2];
 *   rtems_id timer_id;
 *   rtems_id counting_sem_id;
 *   rtems_id mrsp_ids[MRSP_COUNT];
 *   rtems_id scheduler_ids[CPU_COUNT];
 *   rtems_id worker_ids[2 * CPU_COUNT];
 *   volatile bool stop_worker[2 * CPU_COUNT];
 *   counter counters[2 * CPU_COUNT];
 *   uint32_t migration_counters[CPU_COUNT];
 *   Thread_Control *worker_task;
 *   SMP_barrier_Control barrier;
 *   SMP_lock_Control switch_lock;
 *   size_t switch_index;
 *   switch_event switch_events[32];
 *   volatile bool high_run[2];
 *   volatile bool low_run[2];
 * } test_context;
 * 
 ******************************************************************************/
typedef test_context {
  rtems_id main_task_id;
}

#endif

