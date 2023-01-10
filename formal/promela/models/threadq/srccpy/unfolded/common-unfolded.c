// =============================================================================
_MRSP_Acquire_critical( mrsp, queue_context )
// -----------------------------------------------------------------------------
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


// =============================================================================
void _MRSP_Release(mrsp,queue_context)
// -----------------------------------------------------------------------------
MRSP_Control         *mrsp,
Thread_queue_Context *queue_context

//_Thread_queue_Release( &mrsp->Wait_queue, queue_context );
//    _Thread_queue_Queue_release_critical(
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
RTEMS_COMPILER_MEMORY_BARRIER();
_CPU_ISR_Enable(
  (&queue_context->Lock_context.Lock_context)->Lock_context.isr_level
);


/**
 * @brief Gets priority of the MrsP control.
 *
 * @param mrsp The mrsp to get the priority from.
 * @param scheduler The corresponding scheduler.
 *
 * @return The priority of the MrsP control.
 */
RTEMS_INLINE_ROUTINE Priority_Control _MRSP_Get_priority(
  const MRSP_Control      *mrsp,
  const Scheduler_Control *scheduler
)
{
  uint32_t scheduler_index;

  scheduler_index = _Scheduler_Get_index( scheduler );
  return mrsp->ceiling_priorities[ scheduler_index ];
}

RTEMS_INLINE_ROUTINE void _Priority_Node_initialize(
  Priority_Node    *node,
  Priority_Control  priority
)
{
  node->priority = priority;
  _RBTree_Initialize_node( &node->Node.RBTree );
}


// =============================================================================
Status_Control _MRSP_Raise_priority(mrsp,thread,priority_node,queue_context)
// -----------------------------------------------------------------------------
// ** Assume we don't violate mutex ceiling?
MRSP_Control         *mrsp,
Thread_Control       *thread,
Priority_Node        *priority_node,
Thread_queue_Context *queue_context

Status_Control           status;
ISR_lock_Context         lock_context;
const Scheduler_Control *scheduler;
Priority_Control         ceiling_priority;
Scheduler_Node          *scheduler_node;

//_Thread_queue_Context_clear_priority_updates( queue_context );
queue_context->Priority.update_count = 0
//_Thread_Wait_acquire_default_critical( thread, &lock_context );
unsigned int my_ticket;
unsigned int now_serving;

my_ticket =
  _Atomic_Fetch_add_uint(
    & thread->Wait.Lock.Default.next_ticket, // Lock.Ticket_lock
    1U,
    ATOMIC_ORDER_RELAXED
  );
do {
  now_serving =
    _Atomic_Load_uint(
      & thread->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
      ATOMIC_ORDER_ACQUIRE
    );
} while ( now_serving != my_ticket );

scheduler = thread->Scheduler.home_scheduler;

//scheduler_node = _Thread_Scheduler_get_home_node( thread );
_Assert( !_Chain_Is_empty( &thread->Scheduler.Wait_nodes ) );
// scheduler_node = SCHEDULER_NODE_OF_THREAD_WAIT_NODE(
//                  _Chain_First( &thread->Scheduler.Wait_nodes ) );
scheduler_node
 = (Scheduler_Node *)
     ( (uintptr_t)
       (&thread->Scheduler.Wait_nodes)-offsetof(Scheduler_Node,Thread.Wait_node)
     );

// ceiling_priority = _MRSP_Get_priority( mrsp, scheduler );
uint32_t scheduler_index;
scheduler_index = _Scheduler_Get_index( scheduler );
ceiling_priority = mrsp->ceiling_priorities[ scheduler_index ];

if ( ceiling_priority <= (&scheduler_node->Wait.Priority)->Node.priority;)
{
  // _Priority_Node_initialize( priority_node, ceiling_priority );
  priority_node->priority = ceiling_priority;
  _RBTree_Initialize_node( &priority_node->Node.RBTree );

  _Thread_Priority_add( thread, priority_node, queue_context );
  // complex - see below
  status = STATUS_SUCCESSFUL;
} else { // SHOULD NOT HAPPEN ??
  status = STATUS_MUTEX_CEILING_VIOLATED;
}

//_Thread_Wait_release_default_critical( thread, &lock_context );
unsigned int current_ticket =
  _Atomic_Load_uint(
    & thread->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
    ATOMIC_ORDER_RELAXED
  );
unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint(
    & thread->Wait.Lock.Default.now_serving,
    next_ticket,
    ATOMIC_ORDER_RELEASE
  );

return status;


// =============================================================================
_MRSP_Remove_priority( executing, &mrsp->Ceiling_priority, queue_context );
// -----------------------------------------------------------------------------
Thread_Control       *executing,
Priority_Node        *priority_node,
Thread_queue_Context *queue_context

ISR_lock_Context lock_context;

//_Thread_queue_Context_clear_priority_updates( queue_context );
queue_context->Priority.update_count = 0;

//_Thread_Wait_acquire_default_critical( executing, &lock_context );
Thread_Control   *executing,
// _ISR_Get_level() != 0
unsigned int my_ticket;
unsigned int now_serving;

my_ticket =
  _Atomic_Fetch_add_uint(
    & executing->Wait.Lock.Default.next_ticket, // Lock.Ticket_lock
    1U,
    ATOMIC_ORDER_RELAXED
  );
do {
  now_serving =
    _Atomic_Load_uint(
      & executing->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
      ATOMIC_ORDER_ACQUIRE
    );
} while ( now_serving != my_ticket );

//_Thread_Priority_remove( executing, priority_node, queue_context );
_Thread_Priority_apply(
  executing,
  priority_node,
  queue_context,
  true,
  PRIORITY_ACTION_REMOVE
);

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


// =============================================================================
void _Thread_Wait_acquire_critical(the_thread,queue_context)
// -----------------------------------------------------------------------------
Thread_Control       *the_thread,
Thread_queue_Context *queue_context
Thread_queue_Queue *queue;

_Thread_Wait_acquire_default_critical(
  the_thread,
  &queue_context->Lock_context.Lock_context
);

queue = the_thread->Wait.queue;
queue_context->Lock_context.Wait.queue = queue;

if ( queue != NULL ) {
  _Thread_queue_Gate_add(
    &the_thread->Wait.Lock.Pending_requests,
    &queue_context->Lock_context.Wait.Gate
  );
  _Thread_Wait_release_default_critical(
    the_thread,
    &queue_context->Lock_context.Lock_context
  );
  _Thread_Wait_acquire_queue_critical( queue, &queue_context->Lock_context );

  if ( queue_context->Lock_context.Wait.queue == NULL ) {
    _Thread_Wait_release_queue_critical(
      queue,
      &queue_context->Lock_context
    );
    _Thread_Wait_acquire_default_critical(
      the_thread,
      &queue_context->Lock_context.Lock_context
    );
    _Thread_Wait_remove_request_locked(
      the_thread,
      &queue_context->Lock_context
    );
    _Assert( the_thread->Wait.queue == NULL );
  }
}


/ =============================================================================
void _Thread_Wait_release_critical(the_thread,queue_context)
// -----------------------------------------------------------------------------
Thread_Control       *the_thread,
Thread_queue_Context *queue_context
Thread_queue_Queue *queue;

queue = queue_context->Lock_context.Wait.queue;

if ( queue != NULL ) {
  _Thread_Wait_release_queue_critical(
    queue, &queue_context->Lock_context
  );
  _Thread_Wait_acquire_default_critical(
    the_thread,
    &queue_context->Lock_context.Lock_context
  );
  _Thread_Wait_remove_request_locked(
    the_thread,
    &queue_context->Lock_context
  );
}

_Thread_Wait_release_default_critical(
  the_thread,
  &queue_context->Lock_context.Lock_context
);




// =============================================================================
bool _Thread_queue_Path_acquire_critical( queue, executing, queue_context )

SH: The loop in _Thread_queue_Path_acquire_critical is not infinite.
It is bounded by the size of the dependency graph.
I hope you don't find any potentially infinite loops in the RTEMS implementation.
// -----------------------------------------------------------------------------
  Thread_Control     *owner;
  Thread_queue_Link  *link;
  Thread_queue_Queue *target;
  /*
   * For an overview please look at the non-SMP part:
            do { owner = queue->owner;
                 if ( owner == NULL ) return true;
                 if ( owner == the_thread ) return false;
                 queue = owner->Wait.queue;
            } while ( queue != NULL );
   * We basically do the same on SMP configurations.
   * The fact that we may have more than one
   * executing thread and each thread queue has its own SMP lock makes the task
   * a bit more difficult.  We have to avoid deadlocks at SMP lock level, since
   * this would result in an unrecoverable deadlock of the overall system.
   */
  _Chain_Initialize_empty( &queue_context->Path.Links );
  owner = queue->owner;
  if ( owner == NULL ) { return true; }
  if ( owner == executing ) { return false; }
  _Chain_Initialize_node(
    &queue_context->Path.Start.Lock_context.Wait.Gate.Node
  );
  link = &queue_context->Path.Start;
  _RBTree_Initialize_node( &link->Registry_node );
  _Chain_Initialize_node( &link->Path_node );
  do {
    _Chain_Append_unprotected( &queue_context->Path.Links, &link->Path_node );
    link->owner = owner;
    _Thread_Wait_acquire_default_critical( owner, &link->Lock_context.Lock_context);

    target = owner->Wait.queue;
    link->Lock_context.Wait.queue = target;

    if ( target != NULL ) {
      if ( _Thread_queue_Link_add( link, queue, target ) ) {
        _Thread_queue_Gate_add(
          &owner->Wait.Lock.Pending_requests,
          &link->Lock_context.Wait.Gate
        );
        _Thread_Wait_release_default_critical(
          owner,
          &link->Lock_context.Lock_context
        );
        _Thread_Wait_acquire_queue_critical( target, &link->Lock_context );

        if ( link->Lock_context.Wait.queue == NULL ) {
          _Thread_queue_Link_remove( link );
          _Thread_Wait_release_queue_critical( target, &link->Lock_context );
          _Thread_Wait_acquire_default_critical(
            owner,
            &link->Lock_context.Lock_context
          );
          _Thread_Wait_remove_request_locked( owner, &link->Lock_context );
          _Assert( owner->Wait.queue == NULL );
          return true;
        }
      } else {
        link->Lock_context.Wait.queue = NULL;
        _Thread_queue_Path_append_deadlock_thread( owner, queue_context );
        return false;
      }
    } else {
      return true;
    }

    link = &owner->Wait.Link;
    queue = target;
    owner = queue->owner;
  } while ( owner != NULL );

  return true;


// =============================================================================
_Thread_Wait_acquire_queue_critical(queue,queue_lock_context)
// -----------------------------------------------------------------------------
Thread_queue_Queue        *queue,
Thread_queue_Lock_context *queue_lock_context
unsigned int                   my_ticket;
unsigned int                   now_serving;

my_ticket =
  _Atomic_Fetch_add_uint(
    &(&queue->Lock)->next_ticket,
    1U,
    ATOMIC_ORDER_RELAXED
  );
  do {
    now_serving =
      _Atomic_Load_uint(
        &(&queue->Lock)->now_serving,
        ATOMIC_ORDER_ACQUIRE
      );
  } while ( now_serving != my_ticket );


// =============================================================================
_Thread_Wait_release_queue_critical(queue,queue_lock_context)
// -----------------------------------------------------------------------------
Thread_queue_Queue        *queue,
Thread_queue_Lock_context *queue_lock_context

unsigned int current_ticket =
  _Atomic_Load_uint(
    &(&queue->Lock))->now_serving,
    ATOMIC_ORDER_RELAXED
  );
unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint(
    &(&queue->Lock)->now_serving,
    next_ticket,
    ATOMIC_ORDER_RELEASE
  );


// =============================================================================
_Thread_queue_Path_acquire_critical(queue_context)
// -----------------------------------------------------------------------------


// =============================================================================
_Thread_queue_Path_release_critical(queue_context)
// -----------------------------------------------------------------------------
Chain_Node *head;
Chain_Node *node;

head = _Chain_Head( &queue_context->Path.Links );
node = _Chain_Last( &queue_context->Path.Links );

while ( head != node ) {
  Thread_queue_Link *link;

  link = THREAD_QUEUE_LINK_OF_PATH_NODE( node );

  if ( link->Lock_context.Wait.queue != NULL ) {
    _Thread_queue_Link_remove( link );
    _Thread_Wait_release_queue_critical(
      link->Lock_context.Wait.queue,
      &link->Lock_context
    );
    _Thread_Wait_remove_request( link->owner, &link->Lock_context );
  } else {
    _Thread_Wait_release_default_critical(
      link->owner,
      &link->Lock_context.Lock_context
    );
  }

  node = _Chain_Previous( node );
}



// =============================================================================
void _Thread_Wait_acquire_default_critical(the_thread)
// -----------------------------------------------------------------------------
Thread_Control   *the_thread,
// _ISR_Get_level() != 0
unsigned int my_ticket;
unsigned int now_serving;

my_ticket =
  _Atomic_Fetch_add_uint(
    & the_thread->Wait.Lock.Default.next_ticket, // Lock.Ticket_lock
    1U,
    ATOMIC_ORDER_RELAXED
  );
do {
  now_serving =
    _Atomic_Load_uint(
      & the_thread->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
      ATOMIC_ORDER_ACQUIRE
    );
} while ( now_serving != my_ticket );



// =============================================================================
_Thread_Wait_release_default_critical(the_thread,lock_context)
// -----------------------------------------------------------------------------
Thread_Control   *the_thread,
ISR_lock_Context *lock_context
unsigned int current_ticket =
  _Atomic_Load_uint(
    & the_thread->Wait.Lock.Default.now_serving, // Lock.Ticket_lock
    ATOMIC_ORDER_RELAXED
  );
unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint(
    & the_thread->Wait.Lock.Default.now_serving,
    next_ticket,
    ATOMIC_ORDER_RELEASE
  );


// =============================================================================
_Thread_queue_Queue_acquire_critical(queue, lock_stats, lock_context)
// -----------------------------------------------------------------------------
unsigned int                   my_ticket;
unsigned int                   now_serving;

my_ticket =
  _Atomic_Fetch_add_uint(
    &(&queue->Lock)->next_ticket,
    1U,
    ATOMIC_ORDER_RELAXED
  );
  do {
    now_serving =
      _Atomic_Load_uint(
        &(&queue->Lock)->now_serving,
        ATOMIC_ORDER_ACQUIRE
      );
  } while ( now_serving != my_ticket );

// =============================================================================
_Thread_queue_Queue_release_critical(queue,lock_context)
// -----------------------------------------------------------------------------
Thread_queue_Queue *queue,
ISR_lock_Context   *lock_context

unsigned int current_ticket =
  _Atomic_Load_uint(
    &(&queue->Lock))->now_serving,
    ATOMIC_ORDER_RELAXED
  );
unsigned int next_ticket = current_ticket + 1U;
  _Atomic_Store_uint(
    &(&queue->Lock)->now_serving,
    next_ticket,
    ATOMIC_ORDER_RELEASE
  );

// =============================================================================
void _Thread_Priority_perform_actions(start_of_path,queue_context)
// -----------------------------------------------------------------------------
Thread_Control       *start_of_path,
Thread_queue_Context *queue_context

Thread_Control *the_thread;
size_t          update_count;

_Assert( start_of_path != NULL );
/* This function is tricky on SMP configurations.  Please note that we do not
 * use the thread queue path available via the thread queue context.  Instead
 * we directly use the thread wait information to traverse the thread queue
 * path.  Thus, we do not necessarily acquire all thread queue locks on our
 * own.  In case of a deadlock, we use locks acquired by other processors
 * along the path. */
the_thread = start_of_path;
update_count = queue_context->Priority.update_count;
while ( true ) {
  Thread_queue_Queue *queue;
  queue = the_thread->Wait.queue;
  _Thread_Priority_do_perform_actions(
    the_thread,
    queue,
    the_thread->Wait.operations,
    false,
    queue_context
  );
  if ( (&queue_context->Priority.Actions)->actions == NULL ) {
    return;
  }
  _Assert( queue != NULL );
  the_thread = queue->owner;
  _Assert( the_thread != NULL );
  /* In case the priority action list is non-empty, then the current thread
   * is enqueued on a thread queue.  There is no need to notify the scheduler
   * about a priority change, since it will pick up the new priority once it
   * is unblocked.  Restore the previous set of threads bound to update the
   * priority.*/
  _Thread_queue_Context_restore_priority_updates(
    queue_context,
    update_count
  );
}


/ =============================================================================
void _Thread_Priority_do_perform_actions
                          (the_thread,queue,operations,prepend_it,queue_context)
// -----------------------------------------------------------------------------
Thread_Control                *the_thread,
Thread_queue_Queue            *queue,
const Thread_queue_Operations *operations,
bool                           prepend_it,
Thread_queue_Context          *queue_context

Priority_Aggregation *priority_aggregation;

_Assert( (&queue_context->Priority.Actions)->actions != NULL  );
priority_aggregation = _Priority_Actions_move( &queue_context->Priority.Actions );
do {
  Priority_Aggregation *next_aggregation;
  Priority_Node        *priority_action_node;
  Priority_Action_type  priority_action_type;

  next_aggregation = _Priority_Get_next_action( priority_aggregation );
  priority_action_node = priority_aggregation->Action.node;
  priority_action_type = priority_aggregation->Action.type;
  switch ( priority_action_type ) {
    case PRIORITY_ACTION_ADD:
      _Priority_Insert(
        priority_aggregation,
        priority_action_node,
        &queue_context->Priority.Actions,
        _Thread_Priority_action_add,
        _Thread_Priority_action_change,
        the_thread
      );
      break;
    case PRIORITY_ACTION_REMOVE:
      _Priority_Extract(
        priority_aggregation,
        priority_action_node,
        &queue_context->Priority.Actions,
        _Thread_Priority_action_remove,
        _Thread_Priority_action_change,
        the_thread
      );
      break;
    default:
      _Assert( priority_action_type == PRIORITY_ACTION_CHANGE );
      _Priority_Changed(
        priority_aggregation,
        priority_action_node,
        prepend_it,
        &queue_context->Priority.Actions,
        _Thread_Priority_action_change,
        NULL
      );
      break;
  }
  priority_aggregation = next_aggregation;
} while ( _Priority_Actions_is_valid( priority_aggregation ) );
if ( !_Priority_Actions_is_empty( &queue_context->Priority.Actions ) ) {
  _Thread_queue_Context_add_priority_update( queue_context, the_thread );

  ( *operations->priority_actions )(
    queue,
    &queue_context->Priority.Actions
  );
}


// =============================================================================
void _Thread_Wait_tranquilize(the_thread)
// -----------------------------------------------------------------------------
Thread_Control *the_thread
_Thread_queue_Gate_wait( &the_thread->Wait.Lock.Tranquilizer );



_Thread_Wait_get_status
// =============================================================================
// -----------------------------------------------------------------------------
