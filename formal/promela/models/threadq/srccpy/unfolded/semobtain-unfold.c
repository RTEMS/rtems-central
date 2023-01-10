/**
 * UNFOLDED: semobtain.c
 *  we apply all macro simplifications for the MrsP scenario
 *
 * We assume the following settings throughout:
 *   Defined macros:
 *     RTEMS_SMP  RTEMS_SCORE_CPUSTDATOMIC_USE_STDATOMIC
 *   Undefined macros:
 *     RTEMS_DEBUG  RTEMS_PROFILING  RTEMS_SMP_LOCK_DO_NOT_INLINE
 *     RTEMS_MULTIPROCESSING
 *   Semaphore setup arguments:
 *     RTEMS_PRIORITY                         : rtems_attribute (bit)
 *     RTEMS_BINARY_SEMAPHORE                 : rtems_attribute (bit)
 *     RTEMS_MULTIPROCESSOR_RESOURCE_SHARING  : rtems_attribute (bit)
 */

rtems_status_code rtems_semaphore_obtain(
  rtems_id        id,
  rtems_option    option_set,
  rtems_interval  timeout
)
{
  Semaphore_Control    *the_semaphore;
  Thread_queue_Context  queue_context;
  Thread_Control       *executing;
  bool                  wait;
  uintptr_t             flags;
  Semaphore_Variant     variant;
  Status_Control        status;

/*
 * We assume id is valid
 * We assume flags are SEMAPHORE_VARIANT_MRSP | SEMAPHORE_DISCIPLINE_PRIORITY
 * We assume wait is true and timeout is zero
 * Nothing has to be done
 */

  //the_semaphore = _Semaphore_Get( id, &queue_context );
  //    _Thread_queue_Context_initialize( queue_context );
  // (void) queue_context;
  the_semaphore = pointer-to-semaphore-object

  executing = _Thread_Executing;
  wait = !_Options_Is_no_wait( option_set );

  if ( wait ) {
    queue_context->Timeout.ticks = ticks;
    queue_context->enqueue_callout = _Thread_queue_Add_timeout_ticks;
  } else {
    queue_context->enqueue_callout = _Thread_queue_Enqueue_do_nothing_extra;
  }
  // if timeout==0 then both arms are the same - NOP !

  flags = _Semaphore_Get_flags( the_semaphore );
  variant = _Semaphore_Get_variant( flags );

  switch ( variant ) {
    case SEMAPHORE_VARIANT_MRSP:
      status = _MRSP_Seize(
        &the_semaphore->Core_control.MRSP,
        executing,
        wait,
        &queue_context
      );
      break;
  }
  return (rtems_status_code) STATUS_GET_CLASSIC( status );
}


/**
 * @brief Seizes the MrsP mutex.
 *
 * @param[in, out] mrsp is the MrsP mutex to seize.
 *
 * @param[in, out] executing is the currently executing thread.
 *
 * @param wait shall be true, if the executing thread is willing to wait,
 *   otherwise it shall be false.
 *
 * @param[in, out] queue_context is the thread queue context.
 *
 * @retval STATUS_SUCCESSFUL The requested operation was successful.
 *
 * @retval STATUS_UNAVAILABLE Seizing the mutex was not immmediately possible.
 *
 * @retval STATUS_DEADLOCK The executing thread was already the owner of
 *   the mutex.
 *
 * @retval STATUS_MUTEX_CEILING_VIOLATED The current priority of the executing
 *   thread exceeds the ceiling priority of the mutex.
 */
RTEMS_INLINE_ROUTINE Status_Control _MRSP_Seize(
  MRSP_Control         *mrsp,
  Thread_Control       *executing,
  bool                  wait,
  Thread_queue_Context *queue_context
)
{
  Status_Control  status;
  Thread_Control *owner;

  //_MRSP_Acquire_critical( mrsp, queue_context );
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

  owner = mrsp->Wait_queue.Queue.owner;

  if ( owner == NULL ) {

    status = _MRSP_Claim_ownership( mrsp, executing, queue_context );

  } else if ( owner == executing ) {

    // _MRSP_Release( mrsp, queue_context );
    MRSP_Control         *mrsp,
    Thread_queue_Context *queue_context

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
    RTEMS_COMPILER_MEMORY_BARRIER();
    _CPU_ISR_Enable(
      (&queue_context->Lock_context.Lock_context)->Lock_context.isr_level
    );
    status = STATUS_DEADLOCK;

  } else if ( wait ) {

    status = _MRSP_Wait_for_ownership( mrsp, executing, queue_context );

  } else {

    //_MRSP_Release( mrsp, queue_context );
    MRSP_Control         *mrsp,
    Thread_queue_Context *queue_context

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
    RTEMS_COMPILER_MEMORY_BARRIER();
    _CPU_ISR_Enable(
      (&queue_context->Lock_context.Lock_context)->Lock_context.isr_level
    );
    status = STATUS_UNAVAILABLE;

  }

  return status;
}


/**
 * @brief Claims ownership of the MrsP control.
 *
 * @param mrsp The MrsP control to claim the ownership of.
 * @param[in, out] executing The currently executing thread.
 * @param queue_context The thread queue context.
 *
 * @retval STATUS_SUCCESSFUL The operation succeeded.
 * @retval STATUS_MUTEX_CEILING_VIOLATED The wait priority of the executing
 *      thread exceeds the ceiling priority.
 */
RTEMS_INLINE_ROUTINE Status_Control _MRSP_Claim_ownership(
  MRSP_Control         *mrsp,
  Thread_Control       *executing,
  Thread_queue_Context *queue_context
)
{
  Status_Control   status;
  Per_CPU_Control *cpu_self;
  uint32_t disable_level;
  ISR_lock_Context lock_context;

  status = _MRSP_Raise_priority(mrsp,executing,&mrsp->Ceiling_priority,queue_context);
  // complex - see common unfolds

  if ( status != STATUS_SUCCESSFUL ) {
    // _MRSP_Release( mrsp, queue_context );
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
      );    //    _ISR_lock_ISR_enable( &queue_context->Lock_context.Lock_context );
    RTEMS_COMPILER_MEMORY_BARRIER();
    _CPU_ISR_Enable(
      (&queue_context->Lock_context.Lock_context)->Lock_context.isr_level
    );
    return status;
  }

  //_MRSP_Set_owner( mrsp, executing );
  mrsp->Wait_queue.Queue.owner = execute
  // cpu_self = _Thread_queue_Dispatch_disable( queue_context );
  cpu_self = _Per_CPU_Get();
  disable_level = cpu_self->thread_dispatch_disable_level;
  cpu_self->thread_dispatch_disable_level = disable_level + 1;

  //_MRSP_Release( mrsp, queue_context );
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
    );    //    _ISR_lock_ISR_enable( &queue_context->Lock_context.Lock_context );
  RTEMS_COMPILER_MEMORY_BARRIER();
  _CPU_ISR_Enable(
    (&queue_context->Lock_context.Lock_context)->Lock_context.isr_level
  );

  //_Thread_Priority_and_sticky_update( executing, 1 );
  _Thread_State_acquire( executing, &lock_context );
  _Scheduler_Priority_and_sticky_update( executing, 1 ); // complex
  _Thread_State_release( executing, &lock_context );

  _Thread_Dispatch_enable( cpu_self );
  return STATUS_SUCCESSFUL;
}



/**
 * @brief Waits for the ownership of the MrsP control.
 *
 * @param[in, out] mrsp The MrsP control to get the ownership of.
 * @param[in, out] executing The currently executing thread.
 * @param queue_context the thread queue context.
 *
 * @retval STATUS_SUCCESSFUL The operation succeeded.
 * @retval STATUS_MUTEX_CEILING_VIOLATED The wait priority of the
 *      currently executing thread exceeds the ceiling priority.
 * @retval STATUS_DEADLOCK A deadlock occurred.
 * @retval STATUS_TIMEOUT A timeout occurred.
 */
RTEMS_INLINE_ROUTINE Status_Control _MRSP_Wait_for_ownership(
  MRSP_Control         *mrsp,
  Thread_Control       *executing,
  Thread_queue_Context *queue_context
)
{
  Status_Control status;
  Priority_Node  ceiling_priority;

  status = _MRSP_Raise_priority(mrsp,executing,&ceiling_priority,queue_context);
  // complex

  if ( status != STATUS_SUCCESSFUL ) {
    _MRSP_Release( mrsp, queue_context );
    // simple, but we should keep it abstract
    return status;
  }

  //_Thread_queue_Context_set_deadlock_callout(queue_context,_Thread_queue_Deadlock_status);
  queue_context->deadlock_callout = _Thread_queue_Deadlock_status;

  status = _Thread_queue_Enqueue_sticky(
    &mrsp->Wait_queue.Queue,
    MRSP_TQ_OPERATIONS,
    executing,
    queue_context
  ); // v. complex (see below)

  if ( status == STATUS_SUCCESSFUL ) {
    _MRSP_Replace_priority( mrsp, executing, &ceiling_priority ); // complex
  } else {
    Per_CPU_Control *cpu_self;
    int              sticky_level_change;

    if ( status != STATUS_DEADLOCK ) {
      sticky_level_change = -1;
    } else {
      sticky_level_change = 0;
    }

    _ISR_lock_ISR_disable( &queue_context->Lock_context.Lock_context );
    _MRSP_Remove_priority( executing, &ceiling_priority, queue_context );
    cpu_self = _Thread_Dispatch_disable_critical(
      &queue_context->Lock_context.Lock_context
    );
    _ISR_lock_ISR_enable( &queue_context->Lock_context.Lock_context );
    _Thread_Priority_and_sticky_update( executing, sticky_level_change );
    _Thread_Dispatch_enable( cpu_self );
  }

  return status;
}





Status_Control _Thread_queue_Enqueue_sticky(
  Thread_queue_Queue            *queue,
  const Thread_queue_Operations *operations,
  Thread_Control                *the_thread,
  Thread_queue_Context          *queue_context
)
{
  Per_CPU_Control *cpu_self;
  ISR_lock_Context lock_context;

  _Assert( queue_context->enqueue_callout != NULL );

  //_Thread_Wait_claim( the_thread, queue );
  _Thread_Wait_acquire_default_critical( the_thread, &lock_context );
  _Assert( the_thread->Wait.queue == NULL );
  _Chain_Initialize_empty( &the_thread->Wait.Lock.Pending_requests );
  _Chain_Initialize_node( &the_thread->Wait.Lock.Tranquilizer.Node );
  _Thread_queue_Gate_close( &the_thread->Wait.Lock.Tranquilizer );
  the_thread->Wait.queue = queue;
  _Thread_Wait_release_default_critical( the_thread, &lock_context );

  if ( !_Thread_queue_Path_acquire_critical( queue, the_thread, queue_context ) ) {
    _Thread_queue_Path_release_critical( queue_context );
    _Thread_Wait_restore_default( the_thread );
    _Thread_queue_Queue_release( queue, &queue_context->Lock_context.Lock_context );
    //_Thread_Wait_tranquilize( the_thread );
    while ( _Atomic_Load_uint(
            &(&the_thread->Wait.Lock.Tranquilizer)->go_ahead,
            ATOMIC_ORDER_RELAXED ) == 0 ) {/* Wait */}

    ( *queue_context->deadlock_callout )( the_thread );
    return _Thread_Wait_get_status( the_thread );
  }

  //_Thread_queue_Context_clear_priority_updates( queue_context );
  queue_context->Priority.update_count = 0;
  // GOT TO HERE

  //_Thread_Wait_claim_finalize( the_thread, operations );
  the_thread->Wait.operations = operations;

  ( *operations->enqueue )( queue, the_thread, queue_context );

  _Thread_queue_Path_release_critical( queue_context ); // see common

  the_thread->Wait.return_code = STATUS_SUCCESSFUL;

  //_Thread_Wait_flags_set( the_thread, THREAD_QUEUE_INTEND_TO_BLOCK );
  _Atomic_Store_uint(
    &the_thread->Wait.flags,
    THREAD_QUEUE_INTEND_TO_BLOCK,
    ATOMIC_ORDER_RELAXED
  );

  cpu_self = _Thread_queue_Dispatch_disable( queue_context );
  _Thread_queue_Queue_release( queue, &queue_context->Lock_context.Lock_context );

  if ( cpu_self->thread_dispatch_disable_level != 1 ) {
    _Internal_error(
      INTERNAL_ERROR_THREAD_QUEUE_ENQUEUE_STICKY_FROM_BAD_STATE
    );
  }

  ( *queue_context->enqueue_callout )(
    queue,
    the_thread,
    cpu_self,
    queue_context
  );

  _Thread_Priority_update( queue_context );
  _Thread_Priority_and_sticky_update( the_thread, 1 );
  _Thread_Dispatch_enable( cpu_self );

  while (
    _Thread_Wait_flags_get_acquire( the_thread ) == THREAD_QUEUE_INTEND_TO_BLOCK
  ) {
    /* Wait */
  }

  //_Thread_Wait_tranquilize( the_thread );
  while ( _Atomic_Load_uint(
          &(&the_thread->Wait.Lock.Tranquilizer)->go_ahead,
          ATOMIC_ORDER_RELAXED ) == 0 ) {/* Wait */}

  //_Thread_Timer_remove( the_thread );
  _ISR_lock_ISR_disable_and_acquire( &the_thread->Timer.Lock, &lock_context );
  _Watchdog_Per_CPU_remove(
    &the_thread->Timer.Watchdog,
    the_thread->Timer.Watchdog.cpu,
    the_thread->Timer.header
  ); // see snippets
  _ISR_lock_Release_and_ISR_enable( &the_thread->Timer.Lock, &lock_context );

  return _Thread_Wait_get_status( the_thread );
}




/**
 * @brief Disables dispatching in a critical section.
 *
 * @param queue_context The thread queue context to get the lock context from.
 *
 * @return The current processor.
 */
RTEMS_INLINE_ROUTINE Per_CPU_Control *_Thread_queue_Dispatch_disable(
  Thread_queue_Context *queue_context
)
{
  Per_CPU_Control *cpu_self,
  uint32_t disable_level;

  cpu_self = _Per_CPU_Get();

  disable_level = cpu_self->thread_dispatch_disable_level;
  cpu_self->thread_dispatch_disable_level = disable_level + 1;

  return cpu_self;
}
