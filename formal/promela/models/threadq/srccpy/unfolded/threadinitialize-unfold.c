/*
 *  COPYRIGHT (c) 1989-2014.
 *  On-Line Applications Research Corporation (OAR).
 *
 *  The license and distribution terms for this file may be
 *  found in the file LICENSE in this distribution or at
 *  http://www.rtems.org/license/LICENSE.
 */

static void _Thread_Initialize_scheduler_and_wait_nodes(
  Thread_Control             *the_thread,
  const Thread_Configuration *config
)
{
  Scheduler_Node          *home_scheduler_node;
  Scheduler_Node          *scheduler_node;
  const Scheduler_Control *scheduler;
  size_t                   scheduler_index;

  home_scheduler_node = NULL;
  scheduler_node = the_thread->Scheduler.nodes;
  scheduler = &_Scheduler_Table[ 0 ];
  scheduler_index = 0;

  /*
   * In SMP configurations, the thread has exactly one scheduler node for each
   * configured scheduler.  Initialize the scheduler nodes of each scheduler.
   * The application configuration ensures that we have at least one scheduler
   * configured.
   */
  while ( scheduler_index < _Scheduler_Count ) {
    Priority_Control priority;

    if ( scheduler == config->scheduler ) {
      priority = config->priority;
      home_scheduler_node = scheduler_node;
    } else {
      /*
       * Use the idle thread priority for the non-home scheduler instances by
       * default.
       */
      priority = _Scheduler_Map_priority(
        scheduler,
        scheduler->maximum_priority
      );
    }

    _Scheduler_Node_initialize(
      scheduler,
      scheduler_node,
      the_thread,
      priority
    );

    /*
     * Since the size of a scheduler node depends on the application
     * configuration, the _Scheduler_Node_size constant is used to get the next
     * scheduler node.  Using sizeof( Scheduler_Node ) would be wrong.
     */
    scheduler_node = (Scheduler_Node *)
      ( (uintptr_t) scheduler_node + _Scheduler_Node_size );
    ++scheduler;
    ++scheduler_index;
  }

  /*
   * The thread is initialized to use exactly one scheduler node which is
   * provided by its home scheduler.
   */
  _Assert( home_scheduler_node != NULL );
  _Chain_Initialize_one(
    &the_thread->Scheduler.Wait_nodes,
    &home_scheduler_node->Thread.Wait_node
  );
  _Chain_Initialize_one(
    &the_thread->Scheduler.Scheduler_nodes,
    &home_scheduler_node->Thread.Scheduler_node.Chain
  );

  /*
   * The current priority of the thread is initialized to exactly the real
   * priority of the thread.  During the lifetime of the thread, it may gain
   * more priority nodes, for example through locking protocols such as
   * priority inheritance or priority ceiling.
   */
  _Priority_Node_initialize( &the_thread->Real_priority, config->priority );
  _Priority_Initialize_one(
    &home_scheduler_node->Wait.Priority,
    &the_thread->Real_priority
  );

  RTEMS_STATIC_ASSERT( THREAD_SCHEDULER_BLOCKED == 0, Scheduler_state );
  the_thread->Scheduler.home_scheduler = config->scheduler;
  _ISR_lock_Initialize( &the_thread->Scheduler.Lock, "Thread Scheduler" );
  _ISR_lock_Initialize( &the_thread->Wait.Lock.Default, "Thread Wait Default" );
  _Thread_queue_Gate_open( &the_thread->Wait.Lock.Tranquilizer );
  _RBTree_Initialize_node( &the_thread->Wait.Link.Registry_node );
}


static bool _Thread_Try_initialize(
  Thread_Information         *information,
  Thread_Control             *the_thread,
  const Thread_Configuration *config
)
{
  uintptr_t                tls_size;
  size_t                   i;
  char                    *stack_begin;
  char                    *stack_end;
  uintptr_t                stack_align;
  Per_CPU_Control         *cpu = _Per_CPU_Get_by_index( 0 );

  memset(
    &the_thread->Join_queue,
    0,
    information->Objects.object_size - offsetof( Thread_Control, Join_queue )
  );

  for ( i = 0 ; i < _Thread_Control_add_on_count ; ++i ) {
    const Thread_Control_add_on *add_on = &_Thread_Control_add_ons[ i ];

    *(void **) ( (char *) the_thread + add_on->destination_offset ) =
      (char *) the_thread + add_on->source_offset;
  }

  /* Set up the properly aligned stack area begin and end */
  /* Allocate floating-point context in stack area */
  /* Allocate thread-local storage (TLS) area in stack area */

  /*
   *  Get thread queue heads
   */
  the_thread->Wait.spare_heads = _Freechain_Pop(
    &information->Thread_queue_heads.Free
  );
  _Thread_queue_Heads_initialize( the_thread->Wait.spare_heads );

  /*
   *  General initialization
   */

  the_thread->is_fp                  = config->is_fp;
  the_thread->cpu_time_budget        = config->cpu_time_budget;
  the_thread->Start.isr_level        = config->isr_level;
  the_thread->Start.is_preemptible   = config->is_preemptible;
  the_thread->Start.budget_algorithm = config->budget_algorithm;
  the_thread->Start.budget_callout   = config->budget_callout;
  the_thread->Start.stack_free       = config->stack_free;

  _Thread_Timer_initialize( &the_thread->Timer, cpu );
  _Thread_Initialize_scheduler_and_wait_nodes( the_thread, config );

  _Processor_mask_Assign(
    &the_thread->Scheduler.Affinity,
    _SMP_Get_online_processors()
   );
  _SMP_lock_Stats_initialize( &the_thread->Potpourri_stats, "Thread Potpourri" );
  _SMP_lock_Stats_initialize( &the_thread->Join_queue.Lock_stats, "Thread State" );

  /* Initialize the CPU for the non-SMP schedulers */
  _Thread_Set_CPU( the_thread, cpu );

  the_thread->current_state           = STATES_DORMANT;
  the_thread->Wait.operations         = &_Thread_queue_Operations_default;
  the_thread->Start.initial_priority  = config->priority;

  RTEMS_STATIC_ASSERT( THREAD_WAIT_FLAGS_INITIAL == 0, Wait_flags );

  /* POSIX Keys */

  _Thread_Action_control_initialize( &the_thread->Post_switch_actions );

  _Objects_Open_u32( &information->Objects, &the_thread->Object, config->name );

  /*
   * We do following checks of simple error conditions after the thread is
   * fully initialized to simplify the clean up in case of an error.  With a
   * fully initialized thread we can simply use _Thread_Free() and do not have
   * to bother with partially initialized threads.
   */

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

  /*
   *  We assume the Allocator Mutex is locked and dispatching is
   *  enabled when we get here.  We want to be able to run the
   *  user extensions with dispatching enabled.  The Allocator
   *  Mutex provides sufficient protection to let the user extensions
   *  run safely.
   */
  return _User_extensions_Thread_create( the_thread );
}

Status_Control _Thread_Initialize(
  Thread_Information         *information,
  Thread_Control             *the_thread,
  const Thread_Configuration *config
)
{
  bool ok;

  ok = _Thread_Try_initialize( information, the_thread, config );

  if ( !ok ) {
    _Objects_Close( &information->Objects, &the_thread->Object );
    _Thread_Free( information, the_thread );

    return STATUS_UNSATISFIED;
  }

  return STATUS_SUCCESSFUL;
}
