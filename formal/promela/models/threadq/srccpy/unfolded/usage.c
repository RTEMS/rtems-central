ISR_lock_Context
lock_context->Lock_context.Stats_context

MRSP_Control
mrsp->ceiling_priorities
mrsp->Ceiling_priority
mrsp->Ceiling_priority.priority
mrsp->Wait_queue.Queue
mrsp->Wait_queue.Queue.owner
mrsp->Wait_queue.Queue->heads
mrsp->Wait_queue.Queue->name
mrsp->Wait_queue.Queue.Lock.next_ticket
mrsp->Wait_queue.Queue.Lock.now_serving

Per_CPU_Control
cpu_self->thread_dispatch_disable_level

Priority_Node
&priority_node->Node.RBTree

Priority_Aggregation
priority_aggregation->Contributors
priority_aggregation->Node.priority

Semaphore_Control
the_semaphore->Core_control.MRSP
the_semaphore->Object

Scheduler_Node
scheduler_of_index->Operations.map_priority
    scheduler_node->Wait.Priority.Action.next
    scheduler_node->Wait.Priority.Action.node
    scheduler_node->Wait.Priority.Action.type
    scheduler_node->Wait.Priority
    scheduler_node->Wait.Priority->Node.priority

SMP_lock_Control
SMP_ticket_lock_Control
lock->next_ticket
lock->now_serving

Thread_Control
the_thread->Join_queue
the_thread->Scheduler.Scheduler_nodes
    thread->Scheduler.Wait_nodes
the_thread->Timer.header
the_thread->Timer.Lock
the_thread->Timer.Watchdog,
the_thread->Timer.Watchdog.cpu
the_thread->Wait.flags
    thread->Wait.Lock.Default.next_ticket // Lock.Ticket_lock
    thread->Wait.Lock.Default.now_serving // Lock.Ticket_lock
the_thread->Wait.Lock.Pending_requests
the_thread->Wait.Lock.Tranquilizer.go_ahead
the_thread->Wait.Lock.Tranquilizer.Node
the_thread->Wait.Lock.Tranquilizer
the_thread->Wait.operations
 executing->Wait.operations.priority_actions
the_thread->Wait.return_code
the_thread->Wait.queue

Thread_queue_Context
queue_context->deadlock_callout
queue_context->enqueue_callout
queue_context->Lock_context
queue_context->Lock_context.Lock_context
queue_context->Lock_context.Lock_context->Lock_context.isr_level
queue_context->Lock_context.Wait.Gate
queue_context->Lock_context.Wait.queue
queue_context->Path.Links
queue_context->Path.Start
queue_context->Path.Start.Lock_context.Wait.Gate.Node
queue_context->Priority.Actions
queue_context->Priority.Actions->actions
queue_context->Priority.update_count
queue_context->Timeout.ticks
queue_context->Priority.update[n]
queue_context->Priority.update_count

Thread_queue_Control
the_thread_queue->Queue
the_thread_queue->Lock_stats

Thread_queue_Gate
gate->go_ahead
gate->Node

Thread_queue_Link
link->Lock_context.Lock_context
link->Lock_context.Wait.Gate
link->Lock_context.Wait.queue
link->owner
link->Path_node
link->Registry_node

Thread_queue_Operations
operations->enqueue
operations->surrender

Thread_queue_Queue
queue->Lock
queue->Lock->now_serving
queue->owner
