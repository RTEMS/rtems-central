/* SPDX-License-Identifier: BSD-2-Clause */

// from smpmrsp01/init.c:

#define CONFIGURE_MAXIMUM_TASKS (2 * CPU_COUNT + 2)
#define CONFIGURE_MAXIMUM_SEMAPHORES (MRSP_COUNT + 1)
#define CONFIGURE_MAXIMUM_TIMERS 1
#define CONFIGURE_MAXIMUM_PROCESSORS CPU_COUNT
#define CONFIGURE_SCHEDULER_SIMPLE_SMP
#define CONFIGURE_INIT_TASK_NAME rtems_build_name('M', 'A', 'I', 'N')
#define CONFIGURE_INIT_TASK_PRIORITY 2
#define CONFIGURE_RTEMS_INIT_TASKS_TABLE
#define CONFIGURE_INIT


#define _CONFIGURE_TASKS ( CONFIGURE_MAXIMUM_TASKS + _CONFIGURE_LIBBLOCK_TASKS )

#define CONFIGURE_MINIMUM_TASKS_WITH_USER_PROVIDED_STORAGE 0
#define CONFIGURE_MAXIMUM_POSIX_THREADS 0
#define CONFIGURE_MAXIMUM_THREAD_NAME_SIZE 16
#define CONFIGURE_MAXIMUM_THREAD_LOCAL_STORAGE_SIZE 0

typedef union {
  Scheduler_Node Base;
  Scheduler_SMP_Node Simple_SMP;
} Configuration_Scheduler_node;

const size_t _Scheduler_Node_size = sizeof( Configuration_Scheduler_node );
const size_t _Thread_Maximum_name_size = CONFIGURE_MAXIMUM_THREAD_NAME_SIZE;
const size_t _Thread_Maximum_TLS_size =
  CONFIGURE_MAXIMUM_THREAD_LOCAL_STORAGE_SIZE;

struct Thread_Configured_control {
  Thread_Control Control;
  Configuration_Scheduler_node Scheduler_nodes[ _CONFIGURE_SCHEDULER_COUNT ];
  RTEMS_API_Control API_RTEMS;
  char name[ CONFIGURE_MAXIMUM_THREAD_NAME_SIZE ];
  struct { /* Empty */ } Newlib;
};

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
    , {
      offsetof(
        Thread_Configured_control,
        Control.Join_queue.Queue.name
      ),
      offsetof( Thread_Configured_control, name )
    }
  };

const size_t _Thread_Control_add_on_count =
  RTEMS_ARRAY_SIZE( _Thread_Control_add_ons );

struct Thread_queue_Configured_heads {
  Thread_queue_Heads Heads;
  Thread_queue_Priority_queue Priority[ _CONFIGURE_SCHEDULER_COUNT ];
};

const size_t _Thread_queue_Heads_size
  = sizeof( Thread_queue_Configured_heads );

const size_t _Thread_Initial_thread_count =
  rtems_resource_maximum_per_allocation( _CONFIGURE_TASKS ) +
  rtems_resource_maximum_per_allocation( CONFIGURE_MAXIMUM_POSIX_THREADS );

#define _CONFIGURE_MPCI_RECEIVE_SERVER_COUNT 0

THREAD_INFORMATION_DEFINE(
  _Thread,
  OBJECTS_INTERNAL_API,
  OBJECTS_INTERNAL_THREADS,
  CPU_COUNT
);


static Objects_Control *
_Thread_Local_table[ CPU_COUNT ];

static Thread_Configured_control
_Thread_Local_Objects[ CPU_COUNT ];

static Thread_queue_Configured_heads
_Thread_Heads[ CPU_COUNT ];


// we assume limited objects w.l.o.g.
Thread_Information _Thread_Information = {
  // Objects:
  {  // maximum_id:
    _Objects_Build_id( OBJECTS_INTERNAL_API,
                       OBJECTS_INTERNAL_THREADS,
                       1, CPU_COUNT ),
    _Thread_Local_table, // local_table
    _Objects_Allocate_static, // allocate
    _Objects_Free_static, // deallocate
    0, // inactive
    0, // objects_per_block
    sizeof( Thread_Configured_control ), // object_size
    OBJECTS_NO_STRING_NAME, // name_length
    CHAIN_INITIALIZER_EMPTY( _Thread_Information.Objects.Inactive ), // Inactive
    NULL, // inactive_per_block
    NULL, // object block
    // initial_objects:
    &_Thread_Objects[ 0 ].Control.Object
  },
  // initial:
  {
    &_Thread_Heads[ 0 ]
  }
}


THREAD_INFORMATION_DEFINE(
    _RTEMS_tasks,
    OBJECTS_CLASSIC_API,
    OBJECTS_RTEMS_TASKS,
    CONFIGURE_MAXIMUM_TASKS
);


static Objects_Control *
_RTEMS_tasks_Local_table[ CONFIGURE_MAXIMUM_TASKS ];

static Thread_Configured_control
_RTEMS_tasks_Objects[ CONFIGURE_MAXIMUM_TASKS ];

static Thread_queue_Configured_heads
_RTEMS_tasks_Heads[ CONFIGURE_MAXIMUM_TASKS ];

Thread_Information _RTEMS_tasks_Information = {
  // Objects:
  {
    _Objects_Build_id( OBJECTS_CLASSIC_API, OBJECTS_RTEMS_TASKS,
                       1, CONFIGURE_MAXIMUM_TASKS ),
    _RTEMS_tasks_Local_table,
    _Objects_Allocate_static,
    _Objects_Free_static,
    0,
    0,
    sizeof( Thread_Configured_control ),
    OBJECTS_NO_STRING_NAME,
    CHAIN_INITIALIZER_EMPTY( _RTEMS_tasks_Information.Objects.Inactive ),
    NULL,
    NULL,
    &_RTEMS_tasks_Objects[ 0 ].Control.Object
  },
  // initial:
  {
    &_RTEMS_tasks_Heads[ 0 ]
  }
}


#define _Objects_Build_id( the_api, the_class, node, index )
  ( (Objects_Id) ( (Objects_Id) 2 << 24U )   |
                 ( (Objects_Id) 1 << 27U ) |
                 ( (Objects_Id) 1 << 16U )  |
                 ( (Objects_Id) CPU_COUNT << 0U ) )
