/**
 * UNFOLDED: semcreate.c
 *  we apply all macro simplifications for the MrsP scenario
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
 */

/*
 *  COPYRIGHT (c) 1989-2014.
 *  On-Line Applications Research Corporation (OAR).
 *
 *  The license and distribution terms for this file may be
 *  found in the file LICENSE in this distribution or at
 *  http://www.rtems.org/license/LICENSE.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <rtems/rtems/semimpl.h>
#include <rtems/rtems/statusimpl.h>

/*
 * We assume the id is valid
 * We assume flags are SEMAPHORE_VARIANT_MRSP | SEMAPHORE_DISCIPLINE_PRIORITY
 */

rtems_status_code rtems_semaphore_release( rtems_id id )
{
  Semaphore_Control    *the_semaphore;
  Thread_queue_Context  queue_context;
  Thread_Control       *executing;
  uintptr_t             flags;
  Semaphore_Variant     variant;
  Status_Control        status;

  //_Thread_queue_Context_initialize( &queue_context );
  (void) &queue_context;

  ISR_Level level;
  _ISR_Local_disable( level );
  _ISR_lock_Context_set_level( &queue_context->Lock_context.Lock_context, level );
  the_semaphore = pointer-to-semaphore-object

  executing = _Thread_Executing;
  flags = _Semaphore_Get_flags( the_semaphore );
  variant = _Semaphore_Get_variant( flags );

  status = _MRSP_Surrender(
    &the_semaphore->Core_control.MRSP,
    executing,
    &queue_context
  );

  return (rtems_status_code) STATUS_GET_CLASSIC( status );
}

/*
 * We will unfold _MRSP_Surrender here
 * We assume the task owns this semaphore
 */

/**
 * @brief Surrenders the MrsP control.
 *
 * @param[in, out] mrsp The MrsP control to surrender the control of.
 * @param[in, out] executing The currently executing thread.
 * @param queue_context The thread queue context.
 *
 * @retval STATUS_SUCCESSFUL The operation succeeded.
 * @retval STATUS_NOT_OWNER The executing thread does not own the MrsP control.
 */
RTEMS_INLINE_ROUTINE Status_Control _MRSP_Surrender(
  MRSP_Control         *mrsp,
  Thread_Control       *executing,
  Thread_queue_Context *queue_context
)
{
  Thread_queue_Heads *heads;

  // interrupts are disabled

  //  _MRSP_Acquire_critical( mrsp, queue_context )
  unsigned int my_ticket;
  unsigned int now_serving;

  my_ticket =
    _Atomic_Fetch_add_uint(
         &(&(&(&mrsp->Wait_queue)->Queue)->Lock)->next_ticket,
         1U, ATOMIC_ORDER_RELAXED );
  do {
      now_serving =
        _Atomic_Load_uint(
          &(&(&(&mrsp->Wait_queue)->Queue)->Lock)->now_serving,
          ATOMIC_ORDER_ACQUIRE );
  } while ( now_serving != my_ticket );


  // _MRSP_Set_owner(mrsp,NULL)
  mrsp->Wait_queue.Queue.owner = NULL;

  // _MRSP_Remove_priority( executing, &mrsp->Ceiling_priority, queue_context )
  ISR_lock_Context lock_context;

  // MRP/_Thread_queue_Context_clear_priority_updates( queue_context );
  queue_context->Priority.update_count = 0;

  // MRP/_Thread_Wait_acquire_default_critical( executing, &lock_context );
  _Assert( _ISR_Get_level() != 0 );

  my_ticket =
      _Atomic_Fetch_add_uint(
        &(&(&(&executing->Wait.Lock.Default)->Lock)->Ticket_lock)->next_ticket,
        1U,
        ATOMIC_ORDER_RELAXED
      );

  do {
    now_serving =
          _Atomic_Load_uint(
            &(&(&(&executing->Wait.Lock.Default)->Lock)->Ticket_lock)->now_serving,
            ATOMIC_ORDER_ACQUIRE
          );
  } while ( now_serving != my_ticket );


  //MRP/_Thread_Priority_remove( executing, &mrsp->Ceiling_priority, queue_context );
  //MRP/TPr/_Thread_Priority_apply(
  //  executing, &mrsp->Ceiling_priority, queue_context,
  //  true,
  //  PRIORITY_ACTION_REMOVE );
  Scheduler_Node     *scheduler_node;
  Thread_queue_Queue *queue;

  scheduler_node = _Thread_Scheduler_get_home_node( executing );
  // _Priority_Actions_initialize_one(&queue_context->Priority.Actions,
  //    &scheduler_node->Wait.Priority,
  //    &mrsp->Ceiling_priority,
  //    PRIORITY_ACTION_REMOVE )
  (&scheduler_node->Wait.Priority)->Action.next = NULL;
  (&scheduler_node->Wait.Priority)->Action.node = &mrsp->Ceiling_priority;
  (&scheduler_node->Wait.Priority)->Action.type = PRIORITY_ACTION_REMOVE;
  (&queue_context->Priority.Actions)->actions = &scheduler_node->Wait.Priority;

  queue = executing->Wait.queue;
  // _Thread_Priority_do_perform_actions(
  //   executing,
  //   queue,
  //   executing->Wait.operations,
  //   true,
  //   queue_context
  // );
  Priority_Aggregation *priority_aggregation;

  // _Assert( !_Priority_Actions_is_empty( &queue_context->Priority.Actions ) );
  _Assert( !(&queue_context->Priority.Actions)->actions == NULL;)
  // priority_aggregation = _Priority_Actions_move( &queue_context->Priority.Actions );
  priority_aggregation = &queue_context->Priority.Actions->actions;
  &queue_context->Priority.Actions->actions = NULL;

  do {
    Priority_Aggregation *next_aggregation;
    Priority_Node        *priority_action_node;
    Priority_Action_type  priority_action_type;

    next_aggregation = NULL; // priority_aggregation->Action.next; // NULL
    priority_action_node = &mrsp->Ceiling_priority;
    priority_action_type = PRIORITY_ACTION_REMOVE

    //switch ( priority_action_type ) {
    // case PRIORITY_ACTION_REMOVE:
    // _Priority_Extract(
    //   priority_aggregation,
    //   &mrsp->Ceiling_priority,
    //   &queue_context->Priority.Actions,
    //   _Thread_Priority_action_remove,
    //   _Thread_Priority_action_change,
    //   executing
    );
    _Priority_Plain_extract( priority_aggregation, &mrsp->Ceiling_priority );

    if ( _RBTree_Is_empty( &priority_aggregation->Contributors) ) {
      ( *_Thread_Priority_action_remove )
            ( priority_aggregation, &queue_context->Priority.Actions, executing );
    } else {
      Priority_Node *min;

      /* The aggregation is non-empty, so the minimum node exists. */
      min = (Priority_Node *) _RBTree_Minimum( &priority_aggregation->Contributors );
      _Assert( min != NULL );

      if ( (&mrsp->Ceiling_priority)->priority < min->priority ) {
        priority_aggregation->Node.priority = min->priority;
        ( *_Thread_Priority_action_change )
             ( priority_aggregation, true,
               &queue_context->Priority.Actions, executing );
      }
    }
    priority_aggregation = NULL; // next_aggregation;
  } while ( false /* ( priority_aggregation != NULL ) */ );


  if ( !( &queue_context->Priority.Actions->actions == NULL ) ) {
    // _Thread_queue_Context_add_priority_update( queue_context, executing );
    size_t n;

    n = queue_context->Priority.update_count;
    _Assert( n < RTEMS_ARRAY_SIZE( queue_context->Priority.update ) );

    queue_context->Priority.update_count = n + 1;
    queue_context->Priority.update[ n ] = executing;


    ( *(executing->Wait.operations)->priority_actions )(
      queue,
      &queue_context->Priority.Actions
    );
  }

  /* GOT TO HERE */

  if ( !( &queue_context->Priority.Actions->actions == NULL ) ) {

    _Thread_queue_Path_acquire_critical( queue, executing, queue_context );
    // see common unfolds

    _Thread_Priority_perform_actions( queue->owner, queue_context );
    // v. complex -- see common unfolds

    _Thread_queue_Path_release_critical( queue_context );
    // see common unfolds
  }

  //_Thread_Wait_release_default_critical( executing, &lock_context );
  unsigned int current_ticket =
    _Atomic_Load_uint(
      & executing->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
      ATOMIC_ORDER_RELAXED
    );
  unsigned int next_ticket = current_ticket + 1U;
    _Atomic_Store_uint(
      & executing->Wait.Lock.Default.now_serving,
      next_ticket,
      ATOMIC_ORDER_RELEASE
    );

  heads = mrsp->Wait_queue.Queue.heads;

  if ( heads == NULL ) {
    Per_CPU_Control *cpu_self;

    // cpu_self = _Thread_Dispatch_disable_critical(
    //   &queue_context->Lock_context.Lock_context
    //);
    cpu_self = &_Per_CPU_Information[ _SMP_Get_current_processor() ].per_cpu
    uint32_t disable_level;

    disable_level = cpu_self->thread_dispatch_disable_level;
    cpu_self->thread_dispatch_disable_level = disable_level + 1;

    //_MRSP_Release( mrsp, queue_context );
    // _Thread_queue_Release( &mrsp->Wait_queue, queue_context );
    //_Thread_queue_Queue_release_critical(
    //    &(&mrsp->Wait_queue)->Queue,
    //    &queue_context->Lock_context.Lock_context
    //  );
    unsigned int current_ticket =
      _Atomic_Load_uint(
        &(&(&(&mrsp->Wait_queue)->Queue)->Lock))->now_serving,
        ATOMIC_ORDER_RELAXED
      );
    unsigned int next_ticket = current_ticket + 1U;
      _Atomic_Store_uint(
        &(&(&(&mrsp->Wait_queue)->Queue)->Lock)->now_serving,
        next_ticket,
        ATOMIC_ORDER_RELEASE
      );
    //    _ISR_lock_ISR_enable( &queue_context->Lock_context.Lock_context );
    //        _ISR_Local_enable( (&queue_context->Lock_context.Lock_context)->Lock_context.isr_level )
    RTEMS_COMPILER_MEMORY_BARRIER();
    _CPU_ISR_Enable(&queue_context->Lock_context.Lock_context)->Lock_context.isr_level);

    //_Thread_Priority_and_sticky_update( executing, -1 );
    //    _Thread_State_acquire( executing, &lock_context );
    _ISR_lock_ISR_disable( lock_context );
    my_ticket =
      _Atomic_Fetch_add_uint(
        &(((&executing->Join_queue)->Queue)->Lock)->next_ticket,
        1U,
        ATOMIC_ORDER_RELAXED
      );
      do {
        now_serving =
          _Atomic_Load_uint(
            &(((&executing->Join_queue)->Queue)->Lock)->now_serving,
            ATOMIC_ORDER_ACQUIRE
          );
      } while ( now_serving != my_ticket );


    _Scheduler_Priority_and_sticky_update( executing, -1 );
    // complex include/rtems/score/schedulerimpl.h:417

    //   _Thread_State_release( executing, &lock_context );
    unsigned int current_ticket =
      _Atomic_Load_uint(
        &(((&the_thread->Join_queue)->Queue)->Lock)->now_serving,
        ATOMIC_ORDER_RELAXED
      );
    unsigned int next_ticket = current_ticket + 1U;
    _Atomic_Store_uint(
      &(((&the_thread->Join_queue)->Queue)->Lock)->now_serving,
      next_ticket,
      ATOMIC_ORDER_RELEASE
    );
    _ISR_lock_ISR_enable( lock_context );



    _Thread_Dispatch_enable( cpu_self );
    // complex score/src/threaddispatch.c:364

    return STATUS_SUCCESSFUL;
  }

  // heads != NULL
  _Thread_queue_Surrender_sticky(
    &mrsp->Wait_queue.Queue,
    heads,
    executing,
    queue_context,
    MRSP_TQ_OPERATIONS
  );
  // complex  score/src/threadqenqueue.c:824
  return STATUS_SUCCESSFUL;
}




/*
 * _MRSP_Release( mrsp, queue_context );
 */

/**
 * @brief Releases according to MrsP.
 *
 * @param mrsp The MrsP control for the operation.
 * @param queue_context The thread queue context.
 */
RTEMS_INLINE_ROUTINE void _MRSP_Release(
  MRSP_Control         *mrsp,
  Thread_queue_Context *queue_context
)
{
  _Thread_queue_Queue_release_critical(
    &(&mrsp->Wait_queue)->Queue,
    &queue_context->Lock_context.Lock_context
  );
  _ISR_lock_ISR_enable( &queue_context->Lock_context.Lock_context );
}
