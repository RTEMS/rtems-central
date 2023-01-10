/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseRtemsSemReqRelease
 */

/*
 * Copyright (C) 2021 embedded brains GmbH (http://www.embedded-brains.de)
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
 * This file is part of the RTEMS quality process and was automatically
 * generated.  If you find something that needs to be fixed or
 * worded better please post a report or patch to an RTEMS mailing list
 * or raise a bug report:
 *
 * https://www.rtems.org/bugs.html
 *
 * For information on updating and regenerating please refer to the How-To
 * section in the Software Requirements Engineering chapter of the
 * RTEMS Software Engineering manual.  The manual is provided as a part of
 * a release.  For development sources please refer to the online
 * documentation at:
 *
 * https://docs.rtems.org
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <rtems.h>
#include <string.h>
#include <rtems/rtems/semimpl.h>

#include "ts-config.h"
#include "tx-support.h"

#include <rtems/test.h>

/**
 * @defgroup RTEMSTestCaseRtemsSemReqRelease spec:/rtems/sem/req/release
 *
 * @ingroup RTEMSTestSuiteTestsuitesValidation0
 *
 * @{
 */

typedef enum {
  RtemsSemReqRelease_Pre_Class_Counting,
  RtemsSemReqRelease_Pre_Class_Simple,
  RtemsSemReqRelease_Pre_Class_Binary,
  RtemsSemReqRelease_Pre_Class_PrioCeiling,
  RtemsSemReqRelease_Pre_Class_PrioInherit,
  RtemsSemReqRelease_Pre_Class_MrsP,
  RtemsSemReqRelease_Pre_Class_NA
} RtemsSemReqRelease_Pre_Class;

typedef enum {
  RtemsSemReqRelease_Pre_Discipline_FIFO,
  RtemsSemReqRelease_Pre_Discipline_Priority,
  RtemsSemReqRelease_Pre_Discipline_NA
} RtemsSemReqRelease_Pre_Discipline;

typedef enum {
  RtemsSemReqRelease_Pre_Count_LessMax,
  RtemsSemReqRelease_Pre_Count_Max,
  RtemsSemReqRelease_Pre_Count_Blocked,
  RtemsSemReqRelease_Pre_Count_NA
} RtemsSemReqRelease_Pre_Count;

typedef enum {
  RtemsSemReqRelease_Pre_Owner_No,
  RtemsSemReqRelease_Pre_Owner_Self,
  RtemsSemReqRelease_Pre_Owner_Other,
  RtemsSemReqRelease_Pre_Owner_Blocked,
  RtemsSemReqRelease_Pre_Owner_Nested,
  RtemsSemReqRelease_Pre_Owner_BlockedNested,
  RtemsSemReqRelease_Pre_Owner_BlockedOther,
  RtemsSemReqRelease_Pre_Owner_BlockedNestedOther,
  RtemsSemReqRelease_Pre_Owner_NA
} RtemsSemReqRelease_Pre_Owner;

typedef enum {
  RtemsSemReqRelease_Pre_Id_Valid,
  RtemsSemReqRelease_Pre_Id_Invalid,
  RtemsSemReqRelease_Pre_Id_NA
} RtemsSemReqRelease_Pre_Id;

typedef enum {
  RtemsSemReqRelease_Post_Status_Ok,
  RtemsSemReqRelease_Post_Status_InvId,
  RtemsSemReqRelease_Post_Status_NotOwner,
  RtemsSemReqRelease_Post_Status_Unsat,
  RtemsSemReqRelease_Post_Status_NA
} RtemsSemReqRelease_Post_Status;

typedef enum {
  RtemsSemReqRelease_Post_Count_Zero,
  RtemsSemReqRelease_Post_Count_One,
  RtemsSemReqRelease_Post_Count_PlusOne,
  RtemsSemReqRelease_Post_Count_Max,
  RtemsSemReqRelease_Post_Count_Nop,
  RtemsSemReqRelease_Post_Count_NA
} RtemsSemReqRelease_Post_Count;

typedef enum {
  RtemsSemReqRelease_Post_Owner_No,
  RtemsSemReqRelease_Post_Owner_Self,
  RtemsSemReqRelease_Post_Owner_Other,
  RtemsSemReqRelease_Post_Owner_FIFO,
  RtemsSemReqRelease_Post_Owner_Priority,
  RtemsSemReqRelease_Post_Owner_MrsP,
  RtemsSemReqRelease_Post_Owner_NA
} RtemsSemReqRelease_Post_Owner;

typedef enum {
  RtemsSemReqRelease_Post_Next_FIFO,
  RtemsSemReqRelease_Post_Next_Priority,
  RtemsSemReqRelease_Post_Next_MrsP,
  RtemsSemReqRelease_Post_Next_NA
} RtemsSemReqRelease_Post_Next;

typedef enum {
  RtemsSemReqRelease_Post_CallerPrio_Inherit,
  RtemsSemReqRelease_Post_CallerPrio_Ceiling,
  RtemsSemReqRelease_Post_CallerPrio_Real,
  RtemsSemReqRelease_Post_CallerPrio_NA
} RtemsSemReqRelease_Post_CallerPrio;

typedef enum {
  RtemsSemReqRelease_Post_CallerCPU_Home,
  RtemsSemReqRelease_Post_CallerCPU_Other,
  RtemsSemReqRelease_Post_CallerCPU_NA
} RtemsSemReqRelease_Post_CallerCPU;

typedef struct {
  uint32_t Skip : 1;
  uint32_t Pre_Class_NA : 1;
  uint32_t Pre_Discipline_NA : 1;
  uint32_t Pre_Count_NA : 1;
  uint32_t Pre_Owner_NA : 1;
  uint32_t Pre_Id_NA : 1;
  uint32_t Post_Status : 3;
  uint32_t Post_Count : 3;
  uint32_t Post_Owner : 3;
  uint32_t Post_Next : 2;
  uint32_t Post_CallerPrio : 2;
  uint32_t Post_CallerCPU : 2;
} RtemsSemReqRelease_Entry;

typedef enum {
  BLOCKER_A,
  BLOCKER_B,
  BLOCKER_C,
  HELPER_HOME,
  HELPER_OTHER,
  WORKER_COUNT
} WorkerKind;

/**
 * @brief Test context for spec:/rtems/sem/req/release test case.
 */
typedef struct {
  /**
   * @brief This member contains the identifier of the runner home scheduler.
   */
  rtems_id runner_scheduler_id;

  /**
   * @brief This member contains the identifier of another scheduler.
   */
  rtems_id other_scheduler_id;

  /**
   * @brief This member contains the identifier of a third scheduler.
   */
  rtems_id third_scheduler_id;

  /**
   * @brief This member contains the identifier of the scheduler owning the
   *   processor of the calling task after the rtems_semaphore_release() call.
   */
  rtems_id after_release_scheduler_id;

  /**
   * @brief This member contains the current priority of the calling task after
   *   the rtems_semaphore_release() call.
   */
  rtems_id after_release_priority;

  /**
   * @brief This member contains the runner task identifier.
   */
  rtems_id runner_id;

  /**
   * @brief This member contains the worker task identifiers.
   */
  rtems_id worker_id[ WORKER_COUNT ];

  /**
   * @brief If this member is true, then the worker shall busy wait.
   */
  volatile bool busy_wait;

  /**
   * @brief This member contains the worker activity counter.
   */
  uint32_t counter;

  /**
   * @brief This member contains the semaphore obtain counter of a specific
   *   worker.
   */
  uint32_t obtain_counter[ WORKER_COUNT ];

  /**
   * @brief This member contains the count of the semaphore after the
   *   rtems_semaphore_release() call.
   */
  uint32_t sem_count;

  /**
   * @brief This member contains identifier of the owner of the semaphore after
   *   the rtems_semaphore_release() call or zero if it had no owner.
   */
  rtems_id owner;

  /**
   * @brief This member specifies if the attribute set of the semaphore.
   */
  rtems_attribute attribute_set;

  /**
   * @brief This member specifies if the initial count of the semaphore.
   */
  uint32_t count;

  /**
   * @brief This member contains the semaphore identifier.
   */
  rtems_id semaphore_id;

  /**
   * @brief If this member is true, then the ``id`` parameter shall be valid.
   */
  bool valid_id;

  /**
   * @brief If this member is true, then other tasks shall be blocked on the
   *   semaphore.
   */
  bool blocked;

  /**
   * @brief If this member is true, then a task other than the runner task
   *   shall be the owner of the semaphore.
   */
  bool owner_other;

  /**
   * @brief If this member is true, then the runner task shall obtain the
   *   semaphore recursively.
   */
  bool nested;

  /**
   * @brief If this member is true, then the runner task shall migrate to
   *   another scheduler due to the locking protocol used by the semaphore.
   */
  bool other_scheduler;

  /**
   * @brief If this member is true, then the properties of the semaphore shall
   *   be obtained.
   */
  bool need_properties;

  /**
   * @brief This member specifies the ``id`` parameter for the
   *   rtems_semaphore_release() call.
   */
  rtems_id id;

  /**
   * @brief This member contains the rtems_semaphore_release() return status.
   */
  rtems_status_code status;

  struct {
    /**
     * @brief This member defines the pre-condition indices for the next
     *   action.
     */
    size_t pci[ 5 ];

    /**
     * @brief This member defines the pre-condition states for the next action.
     */
    size_t pcs[ 5 ];

    /**
     * @brief If this member is true, then the test action loop is executed.
     */
    bool in_action_loop;

    /**
     * @brief This member contains the next transition map index.
     */
    size_t index;

    /**
     * @brief This member contains the current transition map entry.
     */
    RtemsSemReqRelease_Entry entry;

    /**
     * @brief If this member is true, then the current transition variant
     *   should be skipped.
     */
    bool skip;
  } Map;
} RtemsSemReqRelease_Context;

static RtemsSemReqRelease_Context
  RtemsSemReqRelease_Instance;

static const char * const RtemsSemReqRelease_PreDesc_Class[] = {
  "Counting",
  "Simple",
  "Binary",
  "PrioCeiling",
  "PrioInherit",
  "MrsP",
  "NA"
};

static const char * const RtemsSemReqRelease_PreDesc_Discipline[] = {
  "FIFO",
  "Priority",
  "NA"
};

static const char * const RtemsSemReqRelease_PreDesc_Count[] = {
  "LessMax",
  "Max",
  "Blocked",
  "NA"
};

static const char * const RtemsSemReqRelease_PreDesc_Owner[] = {
  "No",
  "Self",
  "Other",
  "Blocked",
  "Nested",
  "BlockedNested",
  "BlockedOther",
  "BlockedNestedOther",
  "NA"
};

static const char * const RtemsSemReqRelease_PreDesc_Id[] = {
  "Valid",
  "Invalid",
  "NA"
};

static const char * const * const RtemsSemReqRelease_PreDesc[] = {
  RtemsSemReqRelease_PreDesc_Class,
  RtemsSemReqRelease_PreDesc_Discipline,
  RtemsSemReqRelease_PreDesc_Count,
  RtemsSemReqRelease_PreDesc_Owner,
  RtemsSemReqRelease_PreDesc_Id,
  NULL
};

#define NAME rtems_build_name( 'T', 'E', 'S', 'T' )

typedef RtemsSemReqRelease_Context Context;

typedef enum {
  EVENT_HELPER_SYNC = RTEMS_EVENT_0,
  EVENT_OBTAIN = RTEMS_EVENT_1,
  EVENT_GET_PROPERTIES = RTEMS_EVENT_2,
  EVENT_OBTAIN_SYNC = RTEMS_EVENT_3,
  EVENT_RELEASE = RTEMS_EVENT_4,
  EVENT_RUNNER_SYNC = RTEMS_EVENT_5,
  EVENT_BUSY_WAIT = RTEMS_EVENT_6
} Event;

static void SynchronizeRunner( void )
{
  rtems_event_set events;

  events = ReceiveAnyEvents();
  T_eq_u32( events, EVENT_RUNNER_SYNC );
}

static void Send(
  const Context  *ctx,
  WorkerKind      worker,
  rtems_event_set events
)
{
  SendEvents( ctx->worker_id[ worker ], events );
}

static void MoveBackHome( Context *ctx )
{
#if defined(RTEMS_SMP)
  rtems_task_priority priority;

  /* Move us back to a processor of our home scheduler */
  ctx->busy_wait = true;
  Send( ctx, HELPER_OTHER, EVENT_BUSY_WAIT );
  priority = SetPriority( ctx->worker_id[ HELPER_OTHER ], PRIO_VERY_ULTRA_HIGH );
  SetPriority( ctx->worker_id[ HELPER_OTHER ], priority );
  ctx->busy_wait = false;
#else
  (void) ctx;
#endif
}

static bool CanUseThirdScheduler( void )
{
  return rtems_scheduler_get_processor_maximum() >= 4;
}

static bool IsFIFO( const Context *ctx )
{
  return ( ctx->attribute_set & RTEMS_PRIORITY ) == 0;
}

static bool IsMrsP( const Context *ctx )
{
  return ( ctx->attribute_set & RTEMS_MULTIPROCESSOR_RESOURCE_SHARING ) != 0;
}

static bool IsPrioCeiling( const Context *ctx )
{
  return ( ctx->attribute_set & RTEMS_PRIORITY_CEILING ) != 0;
}

#if defined(RTEMS_SMP)
static void SetWorkerScheduler(
  const Context *ctx,
  WorkerKind     worker,
  rtems_id       scheduler_id,
  Priority       priority
)
{
  rtems_status_code sc;

  sc = rtems_task_set_scheduler(
    ctx->worker_id[ worker ],
    scheduler_id,
    priority
  );
  T_rsc_success( sc );
}

static void SendAndWaitForIntendToBlock(
  const Context  *ctx,
  WorkerKind      worker,
  rtems_event_set events
)
{
  Thread_Control   *the_thread;
  Thread_Wait_flags intend_to_block;

  Send( ctx, worker, events );
  the_thread = GetThread( ctx->worker_id[ worker ] );
  T_assert_not_null( the_thread );
  intend_to_block = THREAD_WAIT_CLASS_OBJECT |
    THREAD_WAIT_STATE_INTEND_TO_BLOCK;

  while ( _Thread_Wait_flags_get_acquire( the_thread ) != intend_to_block ) {
    /* Wait */
  }
}

static void BlockMrsP( Context *ctx )
{
  if ( CanUseThirdScheduler() ) {
    SetWorkerScheduler(
      ctx,
      BLOCKER_A,
      ctx->third_scheduler_id,
      PRIO_HIGH
    );
    SetWorkerScheduler(
      ctx,
      BLOCKER_C,
      ctx->third_scheduler_id,
      PRIO_ULTRA_HIGH
    );
    SendAndWaitForIntendToBlock(
      ctx,
      BLOCKER_A,
      EVENT_OBTAIN | EVENT_GET_PROPERTIES | EVENT_RELEASE
    );
    SendAndWaitForIntendToBlock(
      ctx,
      BLOCKER_B,
      EVENT_OBTAIN | EVENT_RELEASE
    );
    SendAndWaitForIntendToBlock(
      ctx,
      BLOCKER_C,
      EVENT_OBTAIN | EVENT_OBTAIN_SYNC | EVENT_RELEASE
    );
  } else {
    SendAndWaitForIntendToBlock(
      ctx,
      BLOCKER_B,
      EVENT_OBTAIN | EVENT_GET_PROPERTIES | EVENT_OBTAIN_SYNC | EVENT_RELEASE
    );
  }
}
#endif

static void Obtain( const Context *ctx )
{
  rtems_status_code sc;

  sc = rtems_semaphore_obtain(
    ctx->semaphore_id,
    RTEMS_WAIT,
    RTEMS_NO_TIMEOUT
  );
  T_rsc_success( sc );
}

static void Release( const Context *ctx )
{
  rtems_status_code sc;

  sc = rtems_semaphore_release( ctx->semaphore_id );
  T_rsc_success( sc );
}

static void BlockNormal( Context *ctx )
{
  rtems_event_set first;
  rtems_event_set last;

  first = EVENT_OBTAIN | EVENT_GET_PROPERTIES | EVENT_RELEASE;
  last = EVENT_OBTAIN | EVENT_OBTAIN_SYNC | EVENT_RELEASE;

  if ( IsFIFO( ctx ) ) {
    Send( ctx, BLOCKER_A, first );
  } else {
    Send( ctx, BLOCKER_A, last );
  }

#if defined(RTEMS_SMP)
  Send( ctx, BLOCKER_B, EVENT_OBTAIN | EVENT_RELEASE | EVENT_HELPER_SYNC );
  SynchronizeRunner();
#else
  Send( ctx, BLOCKER_B, EVENT_OBTAIN | EVENT_RELEASE );
#endif

  if ( IsFIFO( ctx ) ) {
    Send( ctx, BLOCKER_C, last );
  } else {
    Send( ctx, BLOCKER_C, first );
  }

  MoveBackHome( ctx );
}

static void BlockPrioCeiling( const Context *ctx )
{
  SetPriority( ctx->worker_id[ BLOCKER_A ], PRIO_ULTRA_HIGH );
  Send( ctx, BLOCKER_A, EVENT_OBTAIN | EVENT_OBTAIN_SYNC | EVENT_RELEASE );
  Yield();
  SetPriority( ctx->worker_id[ BLOCKER_A ], PRIO_HIGH );

  SetPriority( ctx->worker_id[ BLOCKER_B ], PRIO_ULTRA_HIGH );
  Send( ctx, BLOCKER_B, EVENT_OBTAIN | EVENT_RELEASE );
  Yield();
  SetPriority( ctx->worker_id[ BLOCKER_B ], PRIO_VERY_HIGH );

  Send(
    ctx,
    BLOCKER_C,
    EVENT_OBTAIN | EVENT_GET_PROPERTIES | EVENT_RELEASE
  );
  Yield();
}

static void PrepareForAction( Context *ctx )
{
  rtems_status_code sc;

  sc = rtems_semaphore_create(
    NAME,
    ctx->count,
    ctx->attribute_set,
    PRIO_ULTRA_HIGH,
    &ctx->semaphore_id
  );
  T_rsc_success( sc );

  if ( ctx->valid_id ) {
    ctx->id = ctx->semaphore_id;
  } else {
    ctx->id = 0;
  }

#if defined(RTEMS_SMP)
  if ( !IsPrioCeiling( ctx ) ) {
    SetWorkerScheduler(
      ctx,
      BLOCKER_B,
      ctx->other_scheduler_id,
      PRIO_LOW
    );
  }
#endif

  if ( ctx->owner_other ) {
    Event event;

    event = EVENT_OBTAIN;
#if defined(RTEMS_SMP)
    event |= EVENT_OBTAIN_SYNC;
#endif

    Send( ctx, BLOCKER_B, event );
#if defined(RTEMS_SMP)
    SynchronizeRunner();
#endif
  }

  if ( ctx->nested ) {
    Obtain( ctx );
  }

  if ( ctx->blocked ) {
#if defined(RTEMS_SMP)
    if ( IsMrsP( ctx ) ) {
      BlockMrsP( ctx );
    } else if ( IsPrioCeiling( ctx ) ) {
      BlockPrioCeiling( ctx );
    } else {
      BlockNormal( ctx );
    }
#else
    if ( IsPrioCeiling( ctx ) || IsMrsP( ctx ) ) {
      BlockPrioCeiling( ctx );
    } else {
      BlockNormal( ctx );
    }
#endif
  }

  if ( ctx->other_scheduler ) {
    ctx->busy_wait = true;
    Send( ctx, HELPER_HOME, EVENT_BUSY_WAIT );
    ctx->busy_wait = false;
  }
}

static void GetSemaphoreProperties( Context *ctx )
{
  Semaphore_Control   *semaphore;
  Thread_queue_Context queue_context;
  Thread_Control      *owner;

  if ( !ctx->need_properties ) {
    return;
  }

  ctx->need_properties = false;

  semaphore = _Semaphore_Get( ctx->semaphore_id, &queue_context );
  T_assert_not_null( semaphore );
  ctx->sem_count = semaphore->Core_control.Semaphore.count;
  owner = semaphore->Core_control.Wait_queue.Queue.owner;
  _ISR_lock_ISR_enable( &queue_context.Lock_context.Lock_context );

  if ( owner != NULL ) {
    ctx->owner = owner->Object.id;
  } else {
    ctx->owner = 0;
  }
}

static void CleanupAfterAction( Context *ctx )
{
  rtems_status_code sc;

  sc = rtems_scheduler_ident_by_processor(
    rtems_scheduler_get_processor(),
    &ctx->after_release_scheduler_id
  );
  T_rsc_success( sc );

  ctx->after_release_priority = GetSelfPriority();

  if ( ctx->nested ) {
    Release( ctx );
  }

  if ( ctx->count == 0 && ctx->status != RTEMS_SUCCESSFUL ) {
    Release( ctx );
  }

  if ( ctx->owner_other ) {
    Send( ctx, BLOCKER_B, EVENT_RELEASE );
  }

  if ( ctx->blocked ) {
    SynchronizeRunner();

#if defined(RTEMS_SMP)
    if ( IsMrsP( ctx ) ) {
      SetWorkerScheduler(
        ctx,
        BLOCKER_A,
        ctx->runner_scheduler_id,
        PRIO_HIGH
      );
      SetWorkerScheduler(
        ctx,
        BLOCKER_C,
        ctx->runner_scheduler_id,
        PRIO_ULTRA_HIGH
      );
    }
#endif
  }

  Obtain( ctx );
  Release( ctx );

#if defined(RTEMS_SMP)
  if ( !IsPrioCeiling( ctx ) ) {
    SetWorkerScheduler(
      ctx,
      BLOCKER_B,
      ctx->runner_scheduler_id,
      PRIO_VERY_HIGH
    );
  }
#endif

  sc = rtems_semaphore_delete( ctx->semaphore_id );
  T_rsc_success( sc );
}

static void Worker( rtems_task_argument arg, WorkerKind worker )
{
  Context *ctx;

  ctx = (Context *) arg;

  while ( true ) {
    rtems_event_set events;

    events = ReceiveAnyEvents();

#if defined(RTEMS_SMP)
    if ( ( events & EVENT_HELPER_SYNC ) != 0 ) {
      SendEvents( ctx->worker_id[ HELPER_OTHER ], EVENT_RUNNER_SYNC );
    }
#endif

    if ( ( events & EVENT_OBTAIN ) != 0 ) {
      uint32_t counter;

      Obtain( ctx );

      counter = ctx->counter;
      ++counter;
      ctx->counter = counter;
      ctx->obtain_counter[ worker ] = counter;
    }

    if ( ( events & EVENT_GET_PROPERTIES ) != 0 ) {
      GetSemaphoreProperties( ctx );
    }

    if ( ( events & EVENT_OBTAIN_SYNC ) != 0 ) {
      SendEvents( ctx->runner_id, EVENT_RUNNER_SYNC );
    }

#if defined(RTEMS_SMP)
    if ( ( events & EVENT_BUSY_WAIT ) != 0 ) {
      while ( ctx->busy_wait ) {
        /* Wait */
      }
    }
#endif

    if ( ( events & EVENT_RELEASE ) != 0 ) {
      Release( ctx );
    }

    if ( ( events & EVENT_RUNNER_SYNC ) != 0 ) {
      SendEvents( ctx->runner_id, EVENT_RUNNER_SYNC );
    }
  }
}

static void BlockerA( rtems_task_argument arg )
{
  Worker( arg, BLOCKER_A );
}

static void BlockerB( rtems_task_argument arg )
{
  Worker( arg, BLOCKER_B );
}

static void BlockerC( rtems_task_argument arg )
{
  Worker( arg, BLOCKER_C );
}

#if defined(RTEMS_SMP)
static void HelperHome( rtems_task_argument arg )
{
  Worker( arg, HELPER_HOME );
}

static void HelperOther( rtems_task_argument arg )
{
  Worker( arg, HELPER_OTHER );
}
#endif

static void RtemsSemReqRelease_Pre_Class_Prepare(
  RtemsSemReqRelease_Context  *ctx,
  RtemsSemReqRelease_Pre_Class state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Pre_Class_Counting: {
      /*
       * While the semaphore object is a counting semaphore.
       */
      ctx->attribute_set |= RTEMS_COUNTING_SEMAPHORE;
      break;
    }

    case RtemsSemReqRelease_Pre_Class_Simple: {
      /*
       * While the semaphore object is a simple binary semaphore.
       */
      ctx->attribute_set |= RTEMS_SIMPLE_BINARY_SEMAPHORE;
      break;
    }

    case RtemsSemReqRelease_Pre_Class_Binary: {
      /*
       * While the semaphore object is a binary semaphore.
       */
      ctx->attribute_set |= RTEMS_BINARY_SEMAPHORE;
      break;
    }

    case RtemsSemReqRelease_Pre_Class_PrioCeiling: {
      /*
       * While the semaphore object is a priority ceiling semaphore.
       */
      ctx->attribute_set |= RTEMS_BINARY_SEMAPHORE | RTEMS_PRIORITY_CEILING;
      break;
    }

    case RtemsSemReqRelease_Pre_Class_PrioInherit: {
      /*
       * While the semaphore object is a priority inheritance semaphore.
       */
      ctx->attribute_set |= RTEMS_BINARY_SEMAPHORE | RTEMS_INHERIT_PRIORITY;
      break;
    }

    case RtemsSemReqRelease_Pre_Class_MrsP: {
      /*
       * While the semaphore object is a MrsP semaphore.
       */
      ctx->attribute_set |= RTEMS_BINARY_SEMAPHORE |
        RTEMS_MULTIPROCESSOR_RESOURCE_SHARING;
      break;
    }

    case RtemsSemReqRelease_Pre_Class_NA:
      break;
  }
}

static void RtemsSemReqRelease_Pre_Discipline_Prepare(
  RtemsSemReqRelease_Context       *ctx,
  RtemsSemReqRelease_Pre_Discipline state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Pre_Discipline_FIFO: {
      /*
       * While the semaphore uses the FIFO task wait queue discipline.
       */
      ctx->attribute_set |= RTEMS_FIFO;
      break;
    }

    case RtemsSemReqRelease_Pre_Discipline_Priority: {
      /*
       * While the semaphore uses the priority task wait queue discipline.
       */
      ctx->attribute_set |= RTEMS_PRIORITY;
      break;
    }

    case RtemsSemReqRelease_Pre_Discipline_NA:
      break;
  }
}

static void RtemsSemReqRelease_Pre_Count_Prepare(
  RtemsSemReqRelease_Context  *ctx,
  RtemsSemReqRelease_Pre_Count state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Pre_Count_LessMax: {
      /*
       * While the count of the semaphore is less than the maximum count.
       */
      if ( ( ctx->attribute_set & RTEMS_SIMPLE_BINARY_SEMAPHORE ) != 0 ) {
        ctx->count = 0;
      } else {
        ctx->count = UINT32_MAX - 1;
      }
      break;
    }

    case RtemsSemReqRelease_Pre_Count_Max: {
      /*
       * While the count of the semaphore is equal to the maximum count.
       */
      if ( ( ctx->attribute_set & RTEMS_SIMPLE_BINARY_SEMAPHORE ) != 0 ) {
        ctx->count = 1;
      } else {
        ctx->count = UINT32_MAX;
      }
      break;
    }

    case RtemsSemReqRelease_Pre_Count_Blocked: {
      /*
       * While the semaphore has tasks blocked on the semaphore.
       */
      ctx->blocked = true;
      ctx->count = 0;
      break;
    }

    case RtemsSemReqRelease_Pre_Count_NA:
      break;
  }
}

static void RtemsSemReqRelease_Pre_Owner_Prepare(
  RtemsSemReqRelease_Context  *ctx,
  RtemsSemReqRelease_Pre_Owner state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Pre_Owner_No: {
      /*
       * While the semaphore has no owner.
       */
      ctx->count = 1;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_Self: {
      /*
       * While the calling task is the owner of the semaphore, while the
       * calling task did not recursively obtain the semaphore.
       */
      ctx->count = 0;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_Other: {
      /*
       * While a task other than the calling task is the owner of the
       * semaphore.
       */
      ctx->count = 1;
      ctx->owner_other = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_Blocked: {
      /*
       * While the calling task is the owner of the semaphore, while the
       * calling task did not recursively obtain the semaphore, while tasks are
       * blocked on the semaphore.
       */
      ctx->count = 0;
      ctx->blocked = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_Nested: {
      /*
       * While the calling task is the owner of the semaphore, while the
       * calling task did recursively obtain the semaphore.
       */
      ctx->count = 0;
      ctx->nested = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_BlockedNested: {
      /*
       * While the calling task is the owner of the semaphore, while the
       * calling task did recursively obtain the semaphore, while tasks are
       * blocked on the semaphore.
       */
      ctx->count = 0;
      ctx->blocked = true;
      ctx->nested = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_BlockedOther: {
      /*
       * While the calling task is the owner of the semaphore, while the
       * calling task did not recursively obtain the semaphore, while tasks are
       * blocked on the semaphore, while the calling task executes on a
       * processor owned by a scheduler other than its home scheduler due to a
       * locking protocol mechanism provided by the semaphore.
       */
      ctx->count = 0;
      ctx->blocked = true;
      ctx->other_scheduler = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_BlockedNestedOther: {
      /*
       * While the calling task is the owner of the semaphore, while the
       * calling task did recursively obtain the semaphore, while tasks are
       * blocked on the semaphore, while the calling task executes on a
       * processor owned by a scheduler other than its home scheduler due to a
       * locking protocol mechanism provided by the semaphore.
       */
      ctx->count = 0;
      ctx->blocked = true;
      ctx->nested = true;
      ctx->other_scheduler = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Owner_NA:
      break;
  }
}

static void RtemsSemReqRelease_Pre_Id_Prepare(
  RtemsSemReqRelease_Context *ctx,
  RtemsSemReqRelease_Pre_Id   state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Pre_Id_Valid: {
      /*
       * While the ``id`` parameter is associated with the semaphore.
       */
      ctx->valid_id = true;
      break;
    }

    case RtemsSemReqRelease_Pre_Id_Invalid: {
      /*
       * While the ``id`` parameter is not associated with a semaphore.
       */
      ctx->valid_id = false;
      break;
    }

    case RtemsSemReqRelease_Pre_Id_NA:
      break;
  }
}

static void RtemsSemReqRelease_Post_Status_Check(
  RtemsSemReqRelease_Context    *ctx,
  RtemsSemReqRelease_Post_Status state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Post_Status_Ok: {
      /*
       * The return status of rtems_semaphore_release() shall be
       * RTEMS_SUCCESSFUL.
       */
      T_rsc_success( ctx->status );
      break;
    }

    case RtemsSemReqRelease_Post_Status_InvId: {
      /*
       * The return status of rtems_semaphore_release() shall be
       * RTEMS_INVALID_ID.
       */
      T_rsc( ctx->status, RTEMS_INVALID_ID );
      break;
    }

    case RtemsSemReqRelease_Post_Status_NotOwner: {
      /*
       * The return status of rtems_semaphore_release() shall be
       * RTEMS_NOT_OWNER_OF_RESOURCE.
       */
      T_rsc( ctx->status, RTEMS_NOT_OWNER_OF_RESOURCE );
      break;
    }

    case RtemsSemReqRelease_Post_Status_Unsat: {
      /*
       * The return status of rtems_semaphore_release() shall be
       * RTEMS_UNSATISFIED.
       */
      T_rsc( ctx->status, RTEMS_UNSATISFIED );
      break;
    }

    case RtemsSemReqRelease_Post_Status_NA:
      break;
  }
}

static void RtemsSemReqRelease_Post_Count_Check(
  RtemsSemReqRelease_Context   *ctx,
  RtemsSemReqRelease_Post_Count state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Post_Count_Zero: {
      /*
       * The count of the semaphore shall be zero.
       */
      T_eq_u32( ctx->sem_count, 0 );
      break;
    }

    case RtemsSemReqRelease_Post_Count_One: {
      /*
       * The count of the semaphore shall be one.
       */
      T_eq_u32( ctx->sem_count, 1 );
      break;
    }

    case RtemsSemReqRelease_Post_Count_PlusOne: {
      /*
       * The count of the semaphore shall be incremented by one.
       */
      T_eq_u32( ctx->sem_count, ctx->count + 1 );
      break;
    }

    case RtemsSemReqRelease_Post_Count_Max: {
      /*
       * The count of the semaphore shall be the maximum count.
       */
      T_eq_u32( ctx->sem_count, UINT32_MAX );
      break;
    }

    case RtemsSemReqRelease_Post_Count_Nop: {
      /*
       * The count of the semaphore shall not be modified.
       */
      T_eq_u32( ctx->sem_count, ctx->count );
      break;
    }

    case RtemsSemReqRelease_Post_Count_NA:
      break;
  }
}

static void RtemsSemReqRelease_Post_Owner_Check(
  RtemsSemReqRelease_Context   *ctx,
  RtemsSemReqRelease_Post_Owner state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Post_Owner_No: {
      /*
       * The semaphore shall not have an owner.
       */
      T_eq_u32( ctx->owner, 0 );
      break;
    }

    case RtemsSemReqRelease_Post_Owner_Self: {
      /*
       * The owner of the semaphore shall be the calling task.
       */
      T_eq_u32( ctx->owner, ctx->runner_id );
      break;
    }

    case RtemsSemReqRelease_Post_Owner_Other: {
      /*
       * The owner of the semaphore shall be the other task.
       */
      T_eq_u32( ctx->owner, ctx->worker_id[ BLOCKER_B ] );
      break;
    }

    case RtemsSemReqRelease_Post_Owner_FIFO: {
      /*
       * The owner of the semaphore shall be the first task unblocked in FIFO
       * order.
       */
      T_eq_u32( ctx->owner, ctx->worker_id[ BLOCKER_A ] );
      break;
    }

    case RtemsSemReqRelease_Post_Owner_Priority: {
      /*
       * The owner of the semaphore shall be the first task unblocked in
       * priority order.
       */
      T_eq_u32( ctx->owner, ctx->worker_id[ BLOCKER_C ] );
      break;
    }

    case RtemsSemReqRelease_Post_Owner_MrsP: {
      /*
       * The owner of the semaphore shall be the first task unblocked in MrsP
       * priority order.
       */
      if ( CanUseThirdScheduler() ) {
        T_eq_u32( ctx->owner, ctx->worker_id[ BLOCKER_A ] );
      } else {
        T_eq_u32( ctx->owner, ctx->worker_id[ BLOCKER_B ] );
      }
      break;
    }

    case RtemsSemReqRelease_Post_Owner_NA:
      break;
  }
}

static void RtemsSemReqRelease_Post_Next_Check(
  RtemsSemReqRelease_Context  *ctx,
  RtemsSemReqRelease_Post_Next state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Post_Next_FIFO: {
      /*
       * The first blocked task in FIFO order shall be made ready.
       */
      T_eq_u32( ctx->obtain_counter[ BLOCKER_A ], 1 );
      T_eq_u32( ctx->obtain_counter[ BLOCKER_B ], 2 );
      T_eq_u32( ctx->obtain_counter[ BLOCKER_C ], 3 );
      break;
    }

    case RtemsSemReqRelease_Post_Next_Priority: {
      /*
       * The first blocked task in priority order shall be made ready.
       */
      if ( ctx->owner_other ) {
        T_eq_u32( ctx->obtain_counter[ BLOCKER_A ], 0 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_B ], 1 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_C ], 0 );
      } else {
        T_eq_u32( ctx->obtain_counter[ BLOCKER_A ], 3 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_B ], 2 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_C ], 1 );
      }
      break;
    }

    case RtemsSemReqRelease_Post_Next_MrsP: {
      /*
       * The first blocked task in MrsP priority order shall be made ready.
       */
      if ( CanUseThirdScheduler() ) {
        T_eq_u32( ctx->obtain_counter[ BLOCKER_A ], 1 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_B ], 2 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_C ], 3 );
      } else {
        T_eq_u32( ctx->obtain_counter[ BLOCKER_A ], 0 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_B ], 1 );
        T_eq_u32( ctx->obtain_counter[ BLOCKER_C ], 0 );
      }
      break;
    }

    case RtemsSemReqRelease_Post_Next_NA:
      break;
  }
}

static void RtemsSemReqRelease_Post_CallerPrio_Check(
  RtemsSemReqRelease_Context        *ctx,
  RtemsSemReqRelease_Post_CallerPrio state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Post_CallerPrio_Inherit: {
      /*
       * The current priority of the calling task shall be the inherited
       * priority of the semaphore.
       */
      T_eq_u32( ctx->after_release_priority, PRIO_ULTRA_HIGH );
      break;
    }

    case RtemsSemReqRelease_Post_CallerPrio_Ceiling: {
      /*
       * The current priority of the calling task shall be the ceiling priority
       * of the semaphore.
       */
      T_eq_u32( ctx->after_release_priority, PRIO_ULTRA_HIGH );
      break;
    }

    case RtemsSemReqRelease_Post_CallerPrio_Real: {
      /*
       * The current priority of the calling task shall be its real priority.
       */
      T_eq_u32( ctx->after_release_priority, PRIO_NORMAL );
      break;
    }

    case RtemsSemReqRelease_Post_CallerPrio_NA:
      break;
  }
}

static void RtemsSemReqRelease_Post_CallerCPU_Check(
  RtemsSemReqRelease_Context       *ctx,
  RtemsSemReqRelease_Post_CallerCPU state
)
{
  switch ( state ) {
    case RtemsSemReqRelease_Post_CallerCPU_Home: {
      /*
       * The calling task shall execute on a processor owned by its home
       * scheduler.
       */
      T_eq_u32( ctx->after_release_scheduler_id, ctx->runner_scheduler_id );
      break;
    }

    case RtemsSemReqRelease_Post_CallerCPU_Other: {
      /*
       * The calling task shall execute on a processor not owned by its home
       * scheduler.
       */
      if ( IsMrsP( ctx ) && CanUseThirdScheduler() ) {
        T_eq_u32( ctx->after_release_scheduler_id, ctx->third_scheduler_id );
      } else {
        T_eq_u32( ctx->after_release_scheduler_id, ctx->other_scheduler_id );
      }
      break;
    }

    case RtemsSemReqRelease_Post_CallerCPU_NA:
      break;
  }
}

static void RtemsSemReqRelease_Setup( RtemsSemReqRelease_Context *ctx )
{
  rtems_status_code sc;

  memset( ctx, 0, sizeof( *ctx ) );
  ctx->runner_id = rtems_task_self();
  SetSelfPriority( PRIO_NORMAL );
  ctx->worker_id[ BLOCKER_A ] = CreateTask( "BLKA", PRIO_HIGH );
  StartTask( ctx->worker_id[ BLOCKER_A ], BlockerA, ctx );
  ctx->worker_id[ BLOCKER_B ] = CreateTask( "BLKB", PRIO_VERY_HIGH );
  StartTask( ctx->worker_id[ BLOCKER_B ], BlockerB, ctx );
  ctx->worker_id[ BLOCKER_C ] = CreateTask( "BLKC", PRIO_ULTRA_HIGH );
  StartTask( ctx->worker_id[ BLOCKER_C ], BlockerC, ctx );

  sc = rtems_task_get_scheduler( RTEMS_SELF, &ctx->runner_scheduler_id );
  T_rsc_success( sc );

  #if defined(RTEMS_SMP)
  ctx->worker_id[ HELPER_HOME ] = CreateTask( "HLPH", PRIO_VERY_ULTRA_HIGH );
  StartTask( ctx->worker_id[ HELPER_HOME ], HelperHome, ctx );
  ctx->worker_id[ HELPER_OTHER ] = CreateTask( "HLPO", PRIO_VERY_LOW );
  StartTask( ctx->worker_id[ HELPER_OTHER ], HelperOther, ctx );

  sc = rtems_scheduler_ident(
    TEST_SCHEDULER_B_NAME,
    &ctx->other_scheduler_id
  );
  T_rsc_success( sc );

  sc = rtems_scheduler_ident(
    TEST_SCHEDULER_C_NAME,
    &ctx->third_scheduler_id
  );
  T_rsc_success( sc );

  SetWorkerScheduler(
    ctx,
    HELPER_OTHER,
    ctx->other_scheduler_id,
    PRIO_VERY_LOW
  );
  #endif
}

static void RtemsSemReqRelease_Setup_Wrap( void *arg )
{
  RtemsSemReqRelease_Context *ctx;

  ctx = arg;
  ctx->Map.in_action_loop = false;
  RtemsSemReqRelease_Setup( ctx );
}

static void RtemsSemReqRelease_Teardown( RtemsSemReqRelease_Context *ctx )
{
  size_t i;

  for ( i = 0; i < RTEMS_ARRAY_SIZE( ctx->worker_id ); ++i ) {
    DeleteTask( ctx->worker_id[ i ] );
  }

  RestoreRunnerPriority();
}

static void RtemsSemReqRelease_Teardown_Wrap( void *arg )
{
  RtemsSemReqRelease_Context *ctx;

  ctx = arg;
  ctx->Map.in_action_loop = false;
  RtemsSemReqRelease_Teardown( ctx );
}

static void RtemsSemReqRelease_Prepare( RtemsSemReqRelease_Context *ctx )
{
  size_t i;

  ctx->counter = 0;

  for ( i = 0; i < RTEMS_ARRAY_SIZE( ctx->worker_id ); ++i ) {
    ctx->obtain_counter[ i ] = 0;
  }

  ctx->attribute_set = RTEMS_DEFAULT_ATTRIBUTES;
  ctx->blocked = false;
  ctx->owner_other = false;
  ctx->nested = false;
  ctx->other_scheduler = false;
  ctx->need_properties = true;
}

static void RtemsSemReqRelease_Action( RtemsSemReqRelease_Context *ctx )
{
  PrepareForAction( ctx );
  ctx->status = rtems_semaphore_release( ctx->id );
  GetSemaphoreProperties( ctx );
  CleanupAfterAction( ctx );
}

static const RtemsSemReqRelease_Entry
RtemsSemReqRelease_Entries[] = {
  { 1, 0, 0, 0, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
  { 0, 0, 0, 0, 1, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_Nop, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
  { 0, 0, 0, 0, 1, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_One, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Ceiling,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 0, 1, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_PlusOne, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 0, 1, 0, RtemsSemReqRelease_Post_Status_Unsat,
    RtemsSemReqRelease_Post_Count_Max, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 0, 1, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_Zero, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_FIFO, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 0, 1, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_Zero, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_Priority,
    RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NotOwner,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_No,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_No,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_No,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NotOwner,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Other,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Other,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Priority,
    RtemsSemReqRelease_Post_Next_Priority,
    RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Ceiling,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Inherit,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#if defined(RTEMS_SMP)
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Inherit,
    RtemsSemReqRelease_Post_CallerCPU_Other },
#else
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#endif
#if defined(RTEMS_SMP)
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#else
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Ceiling,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#endif
#if defined(RTEMS_SMP)
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#else
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Ceiling,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#endif
#if defined(RTEMS_SMP)
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#else
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#endif
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_FIFO,
    RtemsSemReqRelease_Post_Next_FIFO, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Inherit,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#if defined(RTEMS_SMP)
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Priority,
    RtemsSemReqRelease_Post_Next_Priority,
    RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#else
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#endif
#if defined(RTEMS_SMP)
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Inherit,
    RtemsSemReqRelease_Post_CallerCPU_Other },
#else
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#endif
#if defined(RTEMS_SMP)
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_MrsP,
    RtemsSemReqRelease_Post_Next_MrsP, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#else
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Priority,
    RtemsSemReqRelease_Post_Next_Priority,
    RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#endif
#if defined(RTEMS_SMP)
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_Ok,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_MrsP,
    RtemsSemReqRelease_Post_Next_MrsP, RtemsSemReqRelease_Post_CallerPrio_Real,
    RtemsSemReqRelease_Post_CallerCPU_Home },
#else
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA },
#endif
#if defined(RTEMS_SMP)
  { 0, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_InvId,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_Self,
    RtemsSemReqRelease_Post_Next_NA,
    RtemsSemReqRelease_Post_CallerPrio_Ceiling,
    RtemsSemReqRelease_Post_CallerCPU_Other }
#else
  { 1, 0, 0, 1, 0, 0, RtemsSemReqRelease_Post_Status_NA,
    RtemsSemReqRelease_Post_Count_NA, RtemsSemReqRelease_Post_Owner_NA,
    RtemsSemReqRelease_Post_Next_NA, RtemsSemReqRelease_Post_CallerPrio_NA,
    RtemsSemReqRelease_Post_CallerCPU_NA }
#endif
};

static const uint8_t
RtemsSemReqRelease_Map[] = {
  6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1,
  7, 1, 7, 1, 7, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 6, 1, 6, 1,
  6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 6, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1,
  7, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 3, 1, 3, 1, 3, 1, 3, 1,
  3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 8, 1,
  8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1,
  3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 9, 1, 9, 1, 9, 1,
  9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 10, 11, 12, 4, 13, 14, 23, 4, 15, 4, 15, 4, 2,
  2, 2, 2, 10, 11, 12, 4, 13, 14, 23, 4, 15, 4, 15, 4, 2, 2, 2, 2, 10, 11, 12,
  4, 13, 14, 23, 4, 15, 4, 15, 4, 2, 2, 2, 2, 10, 11, 12, 4, 13, 14, 16, 4, 15,
  4, 15, 4, 2, 2, 2, 2, 10, 11, 12, 4, 13, 14, 16, 4, 15, 4, 15, 4, 2, 2, 2, 2,
  10, 11, 12, 4, 13, 14, 16, 4, 15, 4, 15, 4, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 11, 12, 5, 13, 14, 16, 5,
  17, 5, 17, 5, 2, 2, 2, 2, 10, 11, 12, 5, 13, 14, 16, 5, 17, 5, 17, 5, 2, 2,
  2, 2, 10, 11, 12, 5, 13, 14, 16, 5, 17, 5, 17, 5, 2, 2, 2, 2, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 11, 12, 4, 13, 14, 16,
  18, 15, 4, 24, 18, 25, 19, 26, 19, 10, 11, 12, 4, 13, 14, 16, 18, 15, 4, 24,
  18, 25, 19, 26, 19, 10, 11, 12, 4, 13, 14, 16, 18, 15, 4, 24, 18, 25, 19, 26,
  19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10,
  11, 12, 5, 13, 14, 27, 5, 20, 21, 20, 21, 28, 29, 22, 22, 10, 11, 12, 5, 13,
  14, 27, 5, 20, 21, 20, 21, 28, 29, 22, 22, 10, 11, 12, 5, 13, 14, 27, 5, 20,
  21, 20, 21, 28, 29, 22, 22
};

static size_t RtemsSemReqRelease_Scope( void *arg, char *buf, size_t n )
{
  RtemsSemReqRelease_Context *ctx;

  ctx = arg;

  if ( ctx->Map.in_action_loop ) {
    return T_get_scope( RtemsSemReqRelease_PreDesc, buf, n, ctx->Map.pcs );
  }

  return 0;
}

static T_fixture RtemsSemReqRelease_Fixture = {
  .setup = RtemsSemReqRelease_Setup_Wrap,
  .stop = NULL,
  .teardown = RtemsSemReqRelease_Teardown_Wrap,
  .scope = RtemsSemReqRelease_Scope,
  .initial_context = &RtemsSemReqRelease_Instance
};

static inline RtemsSemReqRelease_Entry RtemsSemReqRelease_PopEntry(
  RtemsSemReqRelease_Context *ctx
)
{
  size_t index;

  index = ctx->Map.index;
  ctx->Map.index = index + 1;
  return RtemsSemReqRelease_Entries[
    RtemsSemReqRelease_Map[ index ]
  ];
}

static void RtemsSemReqRelease_SetPreConditionStates(
  RtemsSemReqRelease_Context *ctx
)
{
  ctx->Map.pcs[ 0 ] = ctx->Map.pci[ 0 ];
  ctx->Map.pcs[ 1 ] = ctx->Map.pci[ 1 ];

  if ( ctx->Map.entry.Pre_Count_NA ) {
    ctx->Map.pcs[ 2 ] = RtemsSemReqRelease_Pre_Count_NA;
  } else {
    ctx->Map.pcs[ 2 ] = ctx->Map.pci[ 2 ];
  }

  if ( ctx->Map.entry.Pre_Owner_NA ) {
    ctx->Map.pcs[ 3 ] = RtemsSemReqRelease_Pre_Owner_NA;
  } else {
    ctx->Map.pcs[ 3 ] = ctx->Map.pci[ 3 ];
  }

  ctx->Map.pcs[ 4 ] = ctx->Map.pci[ 4 ];
}

static void RtemsSemReqRelease_TestVariant( RtemsSemReqRelease_Context *ctx )
{
  RtemsSemReqRelease_Pre_Class_Prepare( ctx, ctx->Map.pcs[ 0 ] );
  RtemsSemReqRelease_Pre_Discipline_Prepare( ctx, ctx->Map.pcs[ 1 ] );
  RtemsSemReqRelease_Pre_Count_Prepare( ctx, ctx->Map.pcs[ 2 ] );
  RtemsSemReqRelease_Pre_Owner_Prepare( ctx, ctx->Map.pcs[ 3 ] );
  RtemsSemReqRelease_Pre_Id_Prepare( ctx, ctx->Map.pcs[ 4 ] );
  RtemsSemReqRelease_Action( ctx );
  RtemsSemReqRelease_Post_Status_Check( ctx, ctx->Map.entry.Post_Status );
  RtemsSemReqRelease_Post_Count_Check( ctx, ctx->Map.entry.Post_Count );
  RtemsSemReqRelease_Post_Owner_Check( ctx, ctx->Map.entry.Post_Owner );
  RtemsSemReqRelease_Post_Next_Check( ctx, ctx->Map.entry.Post_Next );
  RtemsSemReqRelease_Post_CallerPrio_Check(
    ctx,
    ctx->Map.entry.Post_CallerPrio
  );
  RtemsSemReqRelease_Post_CallerCPU_Check(
    ctx,
    ctx->Map.entry.Post_CallerCPU
  );
}

/**
 * @fn void T_case_body_RtemsSemReqRelease( void )
 */
T_TEST_CASE_FIXTURE( RtemsSemReqRelease, &RtemsSemReqRelease_Fixture )
{
  RtemsSemReqRelease_Context *ctx;

  ctx = T_fixture_context();
  ctx->Map.in_action_loop = true;
  ctx->Map.index = 0;

  for (
    ctx->Map.pci[ 0 ] = RtemsSemReqRelease_Pre_Class_Counting;
    ctx->Map.pci[ 0 ] < RtemsSemReqRelease_Pre_Class_NA;
    ++ctx->Map.pci[ 0 ]
  ) {
    for (
      ctx->Map.pci[ 1 ] = RtemsSemReqRelease_Pre_Discipline_FIFO;
      ctx->Map.pci[ 1 ] < RtemsSemReqRelease_Pre_Discipline_NA;
      ++ctx->Map.pci[ 1 ]
    ) {
      for (
        ctx->Map.pci[ 2 ] = RtemsSemReqRelease_Pre_Count_LessMax;
        ctx->Map.pci[ 2 ] < RtemsSemReqRelease_Pre_Count_NA;
        ++ctx->Map.pci[ 2 ]
      ) {
        for (
          ctx->Map.pci[ 3 ] = RtemsSemReqRelease_Pre_Owner_No;
          ctx->Map.pci[ 3 ] < RtemsSemReqRelease_Pre_Owner_NA;
          ++ctx->Map.pci[ 3 ]
        ) {
          for (
            ctx->Map.pci[ 4 ] = RtemsSemReqRelease_Pre_Id_Valid;
            ctx->Map.pci[ 4 ] < RtemsSemReqRelease_Pre_Id_NA;
            ++ctx->Map.pci[ 4 ]
          ) {
            ctx->Map.entry = RtemsSemReqRelease_PopEntry( ctx );

            if ( ctx->Map.entry.Skip ) {
              continue;
            }

            RtemsSemReqRelease_SetPreConditionStates( ctx );
            RtemsSemReqRelease_Prepare( ctx );
            RtemsSemReqRelease_TestVariant( ctx );
          }
        }
      }
    }
  }
}

/** @} */
