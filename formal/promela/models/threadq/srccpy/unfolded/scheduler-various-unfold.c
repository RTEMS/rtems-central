// ---------------- Scheduler_SMP_Node ---------------------------------------

static inline Scheduler_SMP_Node *_Scheduler_SMP_Thread_get_node(
  Thread_Control *thread
)
{w
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
  Scheduler_simple_SMP_Context *self = scheduler->context;
  _Chain_Initialize_empty( &self->Base.Scheduled );
  _Chain_Initialize_empty( &self->Base.Idle_threads );
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

// ---- Scheduler Node Initialisation for MrsP -----

void _Scheduler_simple_SMP_Node_initialize(
  const Scheduler_Control *scheduler,
  Scheduler_Node          *node,
  Thread_Control          *the_thread,
  Priority_Control         priority
)
{
  Scheduler_SMP_Node *smp_node;

  smp_node = _Scheduler_SMP_Node_downcast( node );
  _Scheduler_SMP_Node_initialize( scheduler, smp_node, the_thread, priority );
}
