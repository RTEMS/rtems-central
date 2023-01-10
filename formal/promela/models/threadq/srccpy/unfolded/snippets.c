// ************* key snippets **************************************************

// ####### GATES ###############################################################

/**
 * @brief Closes the gate.
 *
 * @param[out] gate The gate to close.
 */
RTEMS_INLINE_ROUTINE void _Thread_queue_Gate_close(
  Thread_queue_Gate *gate
)
{
  _Atomic_Store_uint( &gate->go_ahead, 0, ATOMIC_ORDER_RELAXED );
}

/**
 * @brief Adds the gate to the chain.
 *
 * @param[in, out] chain The chain to add the gate to.
 * @param gate The gate to add to the chain.
 */
RTEMS_INLINE_ROUTINE void _Thread_queue_Gate_add(
  Chain_Control     *chain,
  Thread_queue_Gate *gate
)
{
  _Chain_Append_unprotected( chain, &gate->Node );
}

/**
 * @brief Opens the gate.
 *
 * @param[out] gate The gate to open.
 */
RTEMS_INLINE_ROUTINE void _Thread_queue_Gate_open(
  Thread_queue_Gate *gate
)
{
  _Atomic_Store_uint( &gate->go_ahead, 1, ATOMIC_ORDER_RELAXED );
}

/**
 * @brief Waits on a gate to open.
 *
 * Performs busy waiting.
 *
 * @param gate The gate to wait for.
 */
RTEMS_INLINE_ROUTINE void _Thread_queue_Gate_wait(
  Thread_queue_Gate *gate
)
{
  while ( _Atomic_Load_uint( &gate->go_ahead, ATOMIC_ORDER_RELAXED ) == 0 ) {
    /* Wait */
  }
}


// ####### THREAD QUEUES #######################################################


/**
 * @brief Initializes the thread queue heads.
 *
 * @param[out] heads The thread queue heads to initialize.
 */
RTEMS_INLINE_ROUTINE void _Thread_queue_Heads_initialize(
  Thread_queue_Heads *heads
)
{
#if defined(RTEMS_SMP)
  size_t i;

  for ( i = 0; i < _Scheduler_Count; ++i ) {
    _Chain_Initialize_node( &heads->Priority[ i ].Node );
    _Priority_Initialize_empty( &heads->Priority[ i ].Queue );
    heads->Priority[ i ].Queue.scheduler = &_Scheduler_Table[ i ];
  }
#endif

  _Chain_Initialize_empty( &heads->Free_chain );
  _Chain_Initialize_node( &heads->Free_node );
}


/**
 * @brief Claims the thread wait queue.
 *
 * The caller must not be the owner of the default thread wait lock.  The
 * caller must be the owner of the corresponding thread queue lock.  The
 * registration of the corresponding thread queue operations is deferred and
 * done after the deadlock detection.  This is crucial to support timeouts on
 * SMP configurations.
 *
 * @param[in, out] the_thread The thread.
 * @param[in, out] queue The new thread queue.
 *
 * @see _Thread_Wait_claim_finalize() and _Thread_Wait_restore_default().
 */
RTEMS_INLINE_ROUTINE void _Thread_Wait_claim(
  Thread_Control     *the_thread,
  Thread_queue_Queue *queue
)
{
  ISR_lock_Context lock_context;

  _Thread_Wait_acquire_default_critical( the_thread, &lock_context );

  _Assert( the_thread->Wait.queue == NULL );

  _Chain_Initialize_empty( &the_thread->Wait.Lock.Pending_requests );
  _Chain_Initialize_node( &the_thread->Wait.Lock.Tranquilizer.Node );
  _Thread_queue_Gate_close( &the_thread->Wait.Lock.Tranquilizer );

  the_thread->Wait.queue = queue;

  _Thread_Wait_release_default_critical( the_thread, &lock_context );
}

// ####### LOCKS ###############################################################

// LOCK ACQUIRE ................................................................

#define _ISR_lock_Acquire( _lock, _context )
_Assert( _ISR_Get_level() != 0 );
_SMP_lock_Acquire(
  &( _lock )->Lock,
  &( _context )->Lock_context
);

void _SMP_lock_Acquire(
  SMP_lock_Control *lock,
  SMP_lock_Context *context
)
{
  _SMP_lock_Acquire_inline( lock, context );
}

static inline void _SMP_lock_Acquire_inline(
  SMP_lock_Control *lock,
  SMP_lock_Context *context
)
{
  (void) context;
  _SMP_ticket_lock_Acquire(
    &lock->Ticket_lock,
    &lock->Stats,
    &context->Stats_context
  );
}

#define _SMP_ticket_lock_Acquire( lock, stats, stats_context )
_SMP_ticket_lock_Do_acquire( lock )

static inline void _SMP_ticket_lock_Do_acquire(
  SMP_ticket_lock_Control *lock
)
{
  unsigned int                   my_ticket;
  unsigned int                   now_serving;

  my_ticket =
    _Atomic_Fetch_add_uint( &lock->next_ticket, 1U, ATOMIC_ORDER_RELAXED );
    do {
      now_serving =
        _Atomic_Load_uint( &lock->now_serving, ATOMIC_ORDER_ACQUIRE );
    } while ( now_serving != my_ticket );
}

// LOCK ENABLE .................................................................

#define _ISR_lock_ISR_enable( _context ) \
  _ISR_Local_enable( ( _context )->Lock_context.isr_level )

#define _ISR_Local_enable( _level ) \
  do { \
    RTEMS_COMPILER_MEMORY_BARRIER(); \
    _CPU_ISR_Enable( _level ); \
  } while (0)

// LOCK RELEASE ................................................................

#define _ISR_lock_Release( _lock, _context )
  _SMP_lock_Release(
    &( _lock )->Lock,
    &( _context )->Lock_context
  )

#define _SMP_lock_Release( lock, context ) \
  _SMP_lock_Release_inline( lock, context )

void _SMP_lock_Release(
  SMP_lock_Control *lock,
  SMP_lock_Context *context
)
{
  _SMP_lock_Release_inline( lock, context );
}

static inline void _SMP_lock_Release_inline(
  SMP_lock_Control *lock,
  SMP_lock_Context *context
)
{
  _SMP_ticket_lock_Release(
    &lock->Ticket_lock,
    &context->Stats_context
  );
}

#define _SMP_ticket_lock_Release( lock, stats_context )
    _SMP_ticket_lock_Do_release( lock )

static inline void _SMP_ticket_lock_Do_release(
  SMP_ticket_lock_Control *lock
)
{
  unsigned int current_ticket =
    _Atomic_Load_uint( &lock->now_serving, ATOMIC_ORDER_RELAXED );
  unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint( &lock->now_serving, next_ticket, ATOMIC_ORDER_RELEASE );
}

// ####### THREADS STATE #######################################################


// THREAD INITIALISATION ...................................................

#define THREAD_INFORMATION_DEFINE( name, api, cls, max ) \
static Objects_Control * \
name##_Local_table[ _Objects_Maximum_per_allocation( max ) ]; \
static Thread_Configured_control \
name##_Objects[ _Objects_Maximum_per_allocation( max ) ]; \
static Thread_queue_Configured_heads \
name##_Heads[ _Objects_Maximum_per_allocation( max ) ]; \
Thread_Information name##_Information = { \
  { \
    _Objects_Build_id( api, cls, 1, _Objects_Maximum_per_allocation( max ) ), \
    name##_Local_table, \
    _Objects_Is_unlimited( max ) ? \
      _Thread_Allocate_unlimited : _Objects_Allocate_static, \
    _Objects_Is_unlimited( max ) ? \
      _Objects_Free_unlimited : _Objects_Free_static, \
    0, \
    _Objects_Is_unlimited( max ) ? _Objects_Maximum_per_allocation( max ) : 0, \
    sizeof( Thread_Configured_control ), \
    OBJECTS_NO_STRING_NAME, \
    CHAIN_INITIALIZER_EMPTY( name##_Information.Objects.Inactive ), \
    NULL, \
    NULL, \
    &name##_Objects[ 0 ].Control.Object \
    OBJECTS_INFORMATION_MP( name##_Information.Objects, NULL ) \
  }, { \
    &name##_Heads[ 0 ] \
  } \
}

OBJECTS_INFORMATION_MP is only defined for multiprocessing

typedef enum {
  OBJECTS_NO_API       = 0,
  OBJECTS_INTERNAL_API = 1,
  OBJECTS_CLASSIC_API  = 2,
  OBJECTS_POSIX_API    = 3,
  OBJECTS_FAKE_OBJECTS_API = 7
} Objects_APIs;

typedef enum {
  OBJECTS_INTERNAL_NO_CLASS = 0,
  OBJECTS_INTERNAL_THREADS = 1
} Objects_Internal_API;

typedef enum {
  OBJECTS_CLASSIC_NO_CLASS = 0,
  OBJECTS_RTEMS_TASKS = 1,
  OBJECTS_RTEMS_TIMERS,
  OBJECTS_RTEMS_SEMAPHORES,
  OBJECTS_RTEMS_MESSAGE_QUEUES,
  OBJECTS_RTEMS_PARTITIONS,
  OBJECTS_RTEMS_REGIONS,
  OBJECTS_RTEMS_PORTS,
  OBJECTS_RTEMS_PERIODS,
  OBJECTS_RTEMS_EXTENSIONS,
  OBJECTS_RTEMS_BARRIERS
} Objects_Classic_API;

// THREAD STATE ACQUIRE ........................................................

RTEMS_INLINE_ROUTINE void _Thread_State_acquire(
  Thread_Control   *the_thread,
  ISR_lock_Context *lock_context
)
{
  _ISR_lock_ISR_disable( lock_context );
  _Thread_State_acquire_critical( the_thread, lock_context );
}

RTEMS_INLINE_ROUTINE void _Thread_State_acquire_critical(
  Thread_Control   *the_thread,
  ISR_lock_Context *lock_context
)
{
  _Thread_queue_Do_acquire_critical( &the_thread->Join_queue, lock_context );
}

void _Thread_queue_Do_acquire_critical(
  Thread_queue_Control *the_thread_queue, // &the_thread->Join_queue
  ISR_lock_Context     *lock_context
)
{
  _Thread_queue_Queue_acquire_critical(
    &the_thread_queue->Queue,
    &the_thread_queue->Lock_stats,
    lock_context
  );
}

#define \
  _Thread_queue_Queue_acquire_critical( queue, lock_stats, lock_context ) \
  _Thread_queue_Queue_do_acquire_critical( queue, lock_context )
  // queue = (&the_thread->Join_queue)->Queue

RTEMS_INLINE_ROUTINE void _Thread_queue_Queue_do_acquire_critical(
  Thread_queue_Queue *queue, // (&the_thread->Join_queue)->Queue
)
{
  _SMP_ticket_lock_Acquire(
    &queue->Lock,
    lock_stats,
    &lock_context->Lock_context.Stats_context
  );
}// ((&the_thread->Join_queue)->Queue)->Lock


// THREAD STATE RELEASE ........................................................

RTEMS_INLINE_ROUTINE void _Thread_State_release(
  Thread_Control   *the_thread,
  ISR_lock_Context *lock_context
)
{
  _Thread_State_release_critical( the_thread, lock_context );
  _ISR_lock_ISR_enable( lock_context );
}

RTEMS_INLINE_ROUTINE void _Thread_State_release_critical(
  Thread_Control   *the_thread,
  ISR_lock_Context *lock_context
)
{
  _Thread_queue_Do_release_critical( &the_thread->Join_queue, lock_context );
}

void _Thread_queue_Do_release_critical(
  Thread_queue_Control *the_thread_queue, // &the_thread->Join_queue
  ISR_lock_Context     *lock_context
)
{
  _Thread_queue_Queue_release_critical(
    &the_thread_queue->Queue,
    lock_context
  );
}

RTEMS_INLINE_ROUTINE void _Thread_queue_Queue_release_critical(
  Thread_queue_Queue *queue, // (&the_thread->Join_queue)->Queue
  ISR_lock_Context   *lock_context
)
{
  _SMP_ticket_lock_Release(
    &queue->Lock,
    &lock_context->Lock_context.Stats_context
  );
}

#define _SMP_ticket_lock_Release( lock, stats_context )
    _SMP_ticket_lock_Do_release( lock ) // ((&the_thread->Join_queue)->Queue)->Lock

static inline void _SMP_ticket_lock_Do_release(
  SMP_ticket_lock_Control *lock
)
{
  unsigned int current_ticket =
    _Atomic_Load_uint( &lock->now_serving, ATOMIC_ORDER_RELAXED );
  unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint( &lock->now_serving, next_ticket, ATOMIC_ORDER_RELEASE );
}


// ####### STICKINESS ##########################################################
/

// PRIORITY + STICKY UPDATE ....................................................

void _Thread_Priority_and_sticky_update(
  Thread_Control *the_thread,
  int             sticky_level_change
)
{
  ISR_lock_Context lock_context;

  _Thread_State_acquire( the_thread, &lock_context );
  _Scheduler_Priority_and_sticky_update(
    the_thread,
    sticky_level_change
  );
  _Thread_State_release( the_thread, &lock_context );
}

RTEMS_INLINE_ROUTINE void _Scheduler_Priority_and_sticky_update(
  Thread_Control *the_thread,
  int             sticky_level_change
)
{
  Chain_Node              *node;
  const Chain_Node        *tail;
  Scheduler_Node          *scheduler_node;
  const Scheduler_Control *scheduler;
  ISR_lock_Context         lock_context;

  _Thread_Scheduler_process_requests( the_thread );

  node = _Chain_First( &the_thread->Scheduler.Scheduler_nodes );
  scheduler_node = SCHEDULER_NODE_OF_THREAD_SCHEDULER_NODE( node );
  scheduler = _Scheduler_Node_get_scheduler( scheduler_node );

  _Scheduler_Acquire_critical( scheduler, &lock_context );

  scheduler_node->sticky_level += sticky_level_change;
  _Assert( scheduler_node->sticky_level >= 0 );

  ( *scheduler->Operations.update_priority )(
    scheduler,
    the_thread,
    scheduler_node
  );

  _Scheduler_Release_critical( scheduler, &lock_context );

  tail = _Chain_Immutable_tail( &the_thread->Scheduler.Scheduler_nodes );
  node = _Chain_Next( node );

  while ( node != tail ) {
    scheduler_node = SCHEDULER_NODE_OF_THREAD_SCHEDULER_NODE( node );
    scheduler = _Scheduler_Node_get_scheduler( scheduler_node );

    _Scheduler_Acquire_critical( scheduler, &lock_context );
    ( *scheduler->Operations.update_priority )(
      scheduler,
      the_thread,
      scheduler_node
    );
    _Scheduler_Release_critical( scheduler, &lock_context );

    node = _Chain_Next( node );
  }
}

// TQ ENQUEUE STICKY .........................................................

Status_Control _Thread_queue_Enqueue_sticky(
  Thread_queue_Queue            *queue,
  const Thread_queue_Operations *operations,
  Thread_Control                *the_thread,
  Thread_queue_Context          *queue_context
)
{
  Per_CPU_Control *cpu_self;

  _Assert( queue_context->enqueue_callout != NULL );

  _Thread_Wait_claim( the_thread, queue );

  if ( !_Thread_queue_Path_acquire_critical( queue, the_thread, queue_context ) ) {
    _Thread_queue_Path_release_critical( queue_context );
    _Thread_Wait_restore_default( the_thread );
    _Thread_queue_Queue_release( queue, &queue_context->Lock_context.Lock_context );
    _Thread_Wait_tranquilize( the_thread );
    ( *queue_context->deadlock_callout )( the_thread );
    return _Thread_Wait_get_status( the_thread );
  }

  _Thread_queue_Context_clear_priority_updates( queue_context );
  _Thread_Wait_claim_finalize( the_thread, operations );
  ( *operations->enqueue )( queue, the_thread, queue_context );

  _Thread_queue_Path_release_critical( queue_context );

  the_thread->Wait.return_code = STATUS_SUCCESSFUL;
  _Thread_Wait_flags_set( the_thread, THREAD_QUEUE_INTEND_TO_BLOCK );
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

  _Thread_Wait_tranquilize( the_thread );
  _Thread_Timer_remove( the_thread );
  return _Thread_Wait_get_status( the_thread );
}

// TQ SURRENDER STICKY .........................................................

void _Thread_queue_Surrender_sticky(
  Thread_queue_Queue            *queue,
  Thread_queue_Heads            *heads,
  Thread_Control                *previous_owner,
  Thread_queue_Context          *queue_context,
  const Thread_queue_Operations *operations
)
{
  Thread_Control  *new_owner;
  Per_CPU_Control *cpu_self;

  _Assert( heads != NULL );

  _Thread_queue_Context_clear_priority_updates( queue_context );
  new_owner = ( *operations->surrender )(
    queue,
    heads,
    previous_owner,
    queue_context
  );
  queue->owner = new_owner;

  /*
   * There is no need to check the unblock status, since in the corresponding
   * _Thread_queue_Enqueue_sticky() the thread is not blocked by the scheduler.
   * Instead, the thread busy waits for a change of its thread wait flags.
   */
  (void) _Thread_queue_Make_ready_again( new_owner );

  cpu_self = _Thread_queue_Dispatch_disable( queue_context );
  _Thread_queue_Queue_release(
    queue,
    &queue_context->Lock_context.Lock_context
  );
  _Thread_Priority_and_sticky_update( previous_owner, -1 );
  _Thread_Priority_and_sticky_update( new_owner, 0 );
  _Thread_Dispatch_enable( cpu_self );
}
#endif

// ####### THREAD DISPATCH #####################################################

// THREAD DISPATCH ENABLE ......................................................

void _Thread_Dispatch_enable( Per_CPU_Control *cpu_self )
{
  uint32_t disable_level = cpu_self->thread_dispatch_disable_level;

  if ( disable_level == 1 ) {
    ISR_Level level;

    _ISR_Local_disable( level );

    if (
      cpu_self->dispatch_necessary
#if defined(RTEMS_SCORE_ROBUST_THREAD_DISPATCH)
        || !_ISR_Is_enabled( level )
#endif
    ) {
      _Thread_Do_dispatch( cpu_self, level );
    } else {
      cpu_self->thread_dispatch_disable_level = 0;
      _Profiling_Thread_dispatch_enable( cpu_self, 0 );
      _ISR_Local_enable( level );
    }
  } else {
    _Assert( disable_level > 0 );
    cpu_self->thread_dispatch_disable_level = disable_level - 1;
  }
}

// THREAD DISPATCH DISABLE ......................................................


RTEMS_INLINE_ROUTINE Per_CPU_Control *_Thread_queue_Dispatch_disable(
  Thread_queue_Context *queue_context
)
{
  return _Thread_Dispatch_disable_critical(
    &queue_context->Lock_context.Lock_context
  );
}

RTEMS_INLINE_ROUTINE Per_CPU_Control *_Thread_Dispatch_disable_critical(
  const ISR_lock_Context *lock_context
)
{
  return _Thread_Dispatch_disable_with_CPU( _Per_CPU_Get(), lock_context );
}

RTEMS_INLINE_ROUTINE Per_CPU_Control *_Thread_Dispatch_disable_with_CPU(
  Per_CPU_Control        *cpu_self,
  const ISR_lock_Context *lock_context
)
{
  uint32_t disable_level;

  disable_level = cpu_self->thread_dispatch_disable_level;
  _Profiling_Thread_dispatch_disable_critical( // void (no profiling)
    cpu_self,
    disable_level,
    lock_context
  );
  cpu_self->thread_dispatch_disable_level = disable_level + 1;

  return cpu_self;
}





// ##### PRIORITY ##############################################################

RTEMS_INLINE_ROUTINE void _Priority_Node_initialize(
  Priority_Node    *node,
  Priority_Control  priority
)
{
  node->priority = priority;
  _RBTree_Initialize_node( &node->Node.RBTree );
}


static void _Thread_Priority_apply(
  Thread_Control       *the_thread,
  Priority_Node        *priority_action_node,
  Thread_queue_Context *queue_context,
  bool                  prepend_it,
  Priority_Action_type  priority_action_type
)
{
  Scheduler_Node     *scheduler_node;
  Thread_queue_Queue *queue;

  scheduler_node = _Thread_Scheduler_get_home_node( the_thread );
  _Priority_Actions_initialize_one(
    &queue_context->Priority.Actions,
    &scheduler_node->Wait.Priority,
    priority_action_node,
    priority_action_type
  );
  queue = the_thread->Wait.queue;
  _Thread_Priority_do_perform_actions(
    the_thread,
    queue,
    the_thread->Wait.operations,
    prepend_it,
    queue_context
  );

  if ( !_Priority_Actions_is_empty( &queue_context->Priority.Actions ) ) {
    _Thread_queue_Path_acquire_critical( queue, the_thread, queue_context );
    _Thread_Priority_perform_actions( queue->owner, queue_context );
    _Thread_queue_Path_release_critical( queue_context );
  }
}

void _Thread_Priority_add(
  Thread_Control       *the_thread,
  Priority_Node        *priority_node,
  Thread_queue_Context *queue_context
)
{
  _Thread_Priority_apply(
    the_thread,
    priority_node,
    queue_context,
    false,
    PRIORITY_ACTION_ADD
  );
}

void _Thread_Priority_remove(
  Thread_Control       *the_thread,
  Priority_Node        *priority_node,
  Thread_queue_Context *queue_context
)
{
  _Thread_Priority_apply(
    the_thread,
    priority_node,
    queue_context,
    true,
    PRIORITY_ACTION_REMOVE
  );
}

void _Thread_Priority_changed(
  Thread_Control       *the_thread,
  Priority_Node        *priority_node,
  bool                  prepend_it,
  Thread_queue_Context *queue_context
)
{
  _Thread_Priority_apply(
    the_thread,
    priority_node,
    queue_context,
    prepend_it,
    PRIORITY_ACTION_CHANGE
  );
}


// ####### CALLOUTS  ###########################################################


// Thread Queue Callouts .......................................................

void _Thread_queue_Add_timeout_ticks(
  Thread_queue_Queue   *queue,
  Thread_Control       *the_thread,
  Per_CPU_Control      *cpu_self,
  Thread_queue_Context *queue_context
)
{
  Watchdog_Interval ticks;

  ticks = queue_context->Timeout.ticks;

  if ( ticks != WATCHDOG_NO_TIMEOUT ) {
    _Thread_Add_timeout_ticks(
      the_thread,
      cpu_self,
      queue_context->Timeout.ticks
    );
  }
}

void _Thread_queue_Enqueue_do_nothing_extra(
  Thread_queue_Queue   *queue,
  Thread_Control       *the_thread,
  Per_CPU_Control      *cpu_self,
  Thread_queue_Context *queue_context
)
{
  /* Do nothing */
}

// Deadlock Callouts ...........................................................

void _Thread_queue_Deadlock_status( Thread_Control *the_thread )
{
  the_thread->Wait.return_code = STATUS_DEADLOCK;
}

void _Thread_queue_Deadlock_fatal( Thread_Control *the_thread )
{
  _Internal_error( INTERNAL_ERROR_THREAD_QUEUE_DEADLOCK );
}

// ###### RTEMS CONTAINERS #######

#define RTEMS_CONTAINER_OF( _m, _type, _member_name ) \
  ( (_type *) ( (uintptr_t) ( _m ) - offsetof( _type, _member_name ) ) )

extern const size_t _Scheduler_Node_size;

#define SCHEDULER_NODE_OF_THREAD_WAIT_NODE( node ) \
  RTEMS_CONTAINER_OF( node, Scheduler_Node, Thread.Wait_node )

  (Scheduler_Node *)
  ((uintptr_t) (node)-offsetof(Scheduler_Node,Thread.Wait_node))

#define SCHEDULER_NODE_OF_THREAD_SCHEDULER_NODE( node ) \
  RTEMS_CONTAINER_OF( node, Scheduler_Node, Thread.Scheduler_node.Chain )

  (Scheduler_Node *)
  ((uintptr_t) (node)-offsetof(Scheduler_Node,Thread.Scheduler_node.Chain))


// ####### WATCHDOGS ###########################################################

/**
 * @brief Removes the watchdog from the cpu and the scheduled watchdogs.
 *
 * @param[in, out] the_watchdog The watchdog to remove.
 * @param cpu The cpu to remove the watchdog from.
 * @param[in, out] The scheduled watchdogs.
 */
RTEMS_INLINE_ROUTINE void _Watchdog_Per_CPU_remove(
  Watchdog_Control *the_watchdog,
  Per_CPU_Control  *cpu,
  Watchdog_Header  *header
)
{
  ISR_lock_Context lock_context;

  _Watchdog_Per_CPU_acquire_critical( cpu, &lock_context );
  _Watchdog_Remove(
    header,
    the_watchdog
  );
  _Watchdog_Per_CPU_release_critical( cpu, &lock_context );
}


// ################ SCHEDULER STUFF ###########################################


// ---------------- Scheduler_SMP_Node ---------------------------------------

static inline Scheduler_SMP_Node *_Scheduler_SMP_Thread_get_node(
  Thread_Control *thread
)
{
  return (Scheduler_SMP_Node *) _Thread_Scheduler_get_home_node( thread );
}

RTEMS_INLINE_ROUTINE Scheduler_Node *_Thread_Scheduler_get_home_node(
  const Thread_Control *the_thread
)
{
  _Assert( !_Chain_Is_empty( &the_thread->Scheduler.Wait_nodes ) );
  return SCHEDULER_NODE_OF_THREAD_WAIT_NODE( // see container stuff above
    _Chain_First( &the_thread->Scheduler.Wait_nodes )
  );
}


// ---------------- Scheduler Initialization for MrsP ------------------------
void _Scheduler_simple_SMP_Initialize( const Scheduler_Control *scheduler )
{
  Scheduler_simple_SMP_Context *self =
    _Scheduler_simple_SMP_Get_context( scheduler );

  _Scheduler_SMP_Initialize( &self->Base );
  _Chain_Initialize_empty( &self->Ready );
}

static inline void _Scheduler_SMP_Initialize(
  Scheduler_SMP_Context *self
)
{
  _Chain_Initialize_empty( &self->Scheduled );
  _Chain_Initialize_empty( &self->Idle_threads );
}

static Scheduler_simple_SMP_Context *
_Scheduler_simple_SMP_Get_context( const Scheduler_Control *scheduler )
{
  return (Scheduler_simple_SMP_Context *) _Scheduler_Get_context( scheduler );
}

RTEMS_INLINE_ROUTINE Scheduler_Context *_Scheduler_Get_context(
  const Scheduler_Control *scheduler
)
{
  return scheduler->context;
}


// -------

#define SCHEDULER_CONTEXT_NAME( name ) \
  _Configuration_Scheduler_ ## name

#define SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( name ) \
    SCHEDULER_CONTEXT_NAME( simple_SMP_ ## name )

#define RTEMS_SCHEDULER_SIMPLE_SMP( name ) \
    static Scheduler_simple_SMP_Context \
      SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( name )



RTEMS_SCHEDULER_SIMPLE_SMP(0);
-->
static Scheduler_simple_SMP_Context SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( 0 )
-->
static Scheduler_simple_SMP_Context SCHEDULER_CONTEXT_NAME( simple_SMP_0 )
-->
static Scheduler_simple_SMP_Context _Configuration_Scheduler_simple_SMP_0

#define SCHEDULER_SIMPLE_SMP_ENTRY_POINTS \
  { \
    _Scheduler_simple_SMP_Initialize, \
    _Scheduler_default_Schedule, \
    _Scheduler_simple_SMP_Yield, \
    _Scheduler_simple_SMP_Block, \
    _Scheduler_simple_SMP_Unblock, \
    _Scheduler_simple_SMP_Update_priority, \
    _Scheduler_default_Map_priority, \
    _Scheduler_default_Unmap_priority, \
    _Scheduler_simple_SMP_Ask_for_help, \
    _Scheduler_simple_SMP_Reconsider_help_request, \
    _Scheduler_simple_SMP_Withdraw_node, \
    _Scheduler_default_Pin_or_unpin, \
    _Scheduler_default_Pin_or_unpin, \
    _Scheduler_simple_SMP_Add_processor, \
    _Scheduler_simple_SMP_Remove_processor, \
    _Scheduler_simple_SMP_Node_initialize, \
    _Scheduler_default_Node_destroy, \
    _Scheduler_default_Release_job, \
    _Scheduler_default_Cancel_job, \
    _Scheduler_default_Tick, \
    _Scheduler_SMP_Start_idle \
    SCHEDULER_OPERATION_DEFAULT_GET_SET_AFFINITY \
  }

#define SCHEDULER_SIMPLE_SMP_MAXIMUM_PRIORITY 255

#define SCHEDULER_CONTROL_IS_NON_PREEMPT_MODE_SUPPORTED( value ) \
    , value


#define RTEMS_SCHEDULER_TABLE_SIMPLE_SMP( name, obj_name ) \
    { \
      &SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( name ).Base.Base, \
      {SCHEDULER_SIMPLE_SMP_ENTRY_POINTS, \}
      SCHEDULER_SIMPLE_SMP_MAXIMUM_PRIORITY, \
      ( obj_name ) \
      SCHEDULER_CONTROL_IS_NON_PREEMPT_MODE_SUPPORTED( false ) \
    }


RTEMS_SCHEDULER_TABLE_SIMPLE_SMP(0, 0)
-->
{ &_Configuration_Scheduler_simple_SMP_0.Base.Base,
  {_Scheduler_simple_SMP_Initialize,...,_Scheduler_default_Set_affinity},
  255,
  ( 0 )
  , false
}
// Scheduler_Control with Scheduler_simple_SMP_Context !

extern const Scheduler_Control RTEMS_SCHEDULER_INVALID_INDEX;

#define SCHEDULER_ASSIGN_DEFAULT UINT32_C(0x0)

#define RTEMS_SCHEDULER_ASSIGN_DEFAULT \
  SCHEDULER_ASSIGN_DEFAULT

#define SCHEDULER_ASSIGN_PROCESSOR_MANDATORY UINT32_C(0x1)

#define SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL SCHEDULER_ASSIGN_DEFAULT

#define RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL \
              SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL

#define RTEMS_SCHEDULER_ASSIGN_PROCESSOR_MANDATORY \
              SCHEDULER_ASSIGN_PROCESSOR_MANDATORY

#define RTEMS_SCHEDULER_ASSIGN( index, attr ) \
  { \
    ( index ) < RTEMS_ARRAY_SIZE( _Scheduler_Table ) ? \
      &_Scheduler_Table[ ( index ) ] : &RTEMS_SCHEDULER_INVALID_INDEX, \
    ( attr ) \
  }


RTEMS_SCHEDULER_ASSIGN(0, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_MANDATORY)
-->
RTEMS_SCHEDULER_ASSIGN(0, SCHEDULER_ASSIGN_PROCESSOR_MANDATORY)
-->
RTEMS_SCHEDULER_ASSIGN(0, UINT32_C(0x1))
-->
{ ( 0 ) < RTEMS_ARRAY_SIZE( _Scheduler_Table ) ?
  &_Scheduler_Table[ ( 0 ) ] : &RTEMS_SCHEDULER_INVALID_INDEX,
  ( UINT32_C(0x1) )
}
-->
{ &_Scheduler_Table[ 0 ],
  ( UINT32_C(0x1) )
}


RTEMS_SCHEDULER_ASSIGN(1, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL)
-->
RTEMS_SCHEDULER_ASSIGN(1, SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL)
-->
RTEMS_SCHEDULER_ASSIGN(1, SCHEDULER_ASSIGN_DEFAULT)
-->
RTEMS_SCHEDULER_ASSIGN(1, UINT32_C(0x0))
-->
-->
{ &_Scheduler_Table[ 1 ],
  ( UINT32_C(0x0) )
}
