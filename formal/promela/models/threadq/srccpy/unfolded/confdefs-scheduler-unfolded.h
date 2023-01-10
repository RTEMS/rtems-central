/* SPDX-License-Identifier: BSD-2-Clause */


#include <rtems/confdefs/percpu.h>

// From smpmrsp01/init.c config:
#define CONFIGURE_MICROSECONDS_PER_TICK 1000
#define CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_SIMPLE_CONSOLE_DRIVER
#define CONFIGURE_MAXIMUM_TASKS (2 * CPU_COUNT + 2)
#define CONFIGURE_MAXIMUM_SEMAPHORES (MRSP_COUNT + 1)
#define CONFIGURE_MAXIMUM_TIMERS 1
#define CONFIGURE_MAXIMUM_PROCESSORS CPU_COUNT
#define CONFIGURE_SCHEDULER_SIMPLE_SMP
define CONFIGURE_INITIAL_EXTENSIONS \
  { .thread_switch = switch_extension }, \
  RTEMS_TEST_INITIAL_EXTENSION
#define CONFIGURE_INIT_TASK_NAME rtems_build_name('M', 'A', 'I', 'N')
#define CONFIGURE_INIT_TASK_PRIORITY 2
#define CONFIGURE_RTEMS_INIT_TASKS_TABLE
#define CONFIGURE_INIT


#include <rtems/scheduler.h>

#define RTEMS_SCHEDULER_ASSIGN( index, attr ) \
  { \
    ( index ) < RTEMS_ARRAY_SIZE( _Scheduler_Table ) ? \
      &_Scheduler_Table[ ( index ) ] : &RTEMS_SCHEDULER_INVALID_INDEX, \
    ( attr ) \
  }


#include <rtems/score/scheduler.h>

#define SCHEDULER_CONTEXT_NAME( name ) \
  _Configuration_Scheduler_ ## name

#include <rtems/score/schedulersimplesmp.h>

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


#define SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( name ) \
  SCHEDULER_CONTEXT_NAME( simple_SMP_ ## name )

#define RTEMS_SCHEDULER_SIMPLE_SMP( name ) \
  static Scheduler_simple_SMP_Context \
    SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( name )

#define RTEMS_SCHEDULER_TABLE_SIMPLE_SMP( name, obj_name ) \
  { \
    &SCHEDULER_SIMPLE_SMP_CONTEXT_NAME( name ).Base.Base, \
    SCHEDULER_SIMPLE_SMP_ENTRY_POINTS, \
    SCHEDULER_SIMPLE_SMP_MAXIMUM_PRIORITY, \
    ( obj_name ) \
    SCHEDULER_CONTROL_IS_NON_PREEMPT_MODE_SUPPORTED( false ) \
  }

#define CONFIGURE_MAXIMUM_PRIORITY 255

#define CONFIGURE_SCHEDULER_NAME rtems_build_name( 'M', 'P', 'S', ' ' )
#define CONFIGURE_SCHEDULER RTEMS_SCHEDULER_SIMPLE_SMP( dflt )
#define CONFIGURE_SCHEDULER_TABLE_ENTRIES \
      RTEMS_SCHEDULER_TABLE_SIMPLE_SMP( dflt, CONFIGURE_SCHEDULER_NAME )

static Scheduler_simple_SMP_Context _Configuration_Scheduler_simple_SMP_dflt


const Scheduler_Control _Scheduler_Table[] = {
    { &_Configuration_Scheduler_simple_SMP_dflt.Base.Base,
      {
          _Scheduler_simple_SMP_Initialize,
          _Scheduler_default_Schedule,
          _Scheduler_simple_SMP_Yield,
          _Scheduler_simple_SMP_Block,
          _Scheduler_simple_SMP_Unblock,
          _Scheduler_simple_SMP_Update_priority,
          _Scheduler_default_Map_priority,
          _Scheduler_default_Unmap_priority,
          _Scheduler_simple_SMP_Ask_for_help,
          _Scheduler_simple_SMP_Reconsider_help_request,
          _Scheduler_simple_SMP_Withdraw_node,
          _Scheduler_default_Pin_or_unpin,
          _Scheduler_default_Pin_or_unpin,
          _Scheduler_simple_SMP_Add_processor,
          _Scheduler_simple_SMP_Remove_processor,
          _Scheduler_simple_SMP_Node_initialize,
          _Scheduler_default_Node_destroy,
          _Scheduler_default_Release_job,
          _Scheduler_default_Cancel_job,
          _Scheduler_default_Tick,
          _Scheduler_SMP_Start_idle,
          _Scheduler_default_Set_affinity
      }
      255,
      rtems_build_name( 'M', 'P', 'S', ' ' ),
      false
    }
};

#define _CONFIGURE_SCHEDULER_COUNT RTEMS_ARRAY_SIZE( _Scheduler_Table )

const size_t _Scheduler_Count = _CONFIGURE_SCHEDULER_COUNT;

const Scheduler_Assignment _Scheduler_Initial_assignments[] = {
    #define _CONFIGURE_SCHEDULER_ASSIGN \
      RTEMS_SCHEDULER_ASSIGN( \
        0, \
        RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL \
      )
    RTEMS_SCHEDULER_ASSIGN( \
      0, \
      RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL \
    )
    { &_Scheduler_Table[ ( 0 ) ],
      ( RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL )
    }
    #if _CONFIGURE_MAXIMUM_PROCESSORS >= 2
      , _CONFIGURE_SCHEDULER_ASSIGN
    #endif
    // They are all pointig at schedular 0 !!!!
    #if _CONFIGURE_MAXIMUM_PROCESSORS >= 32
      , _CONFIGURE_SCHEDULER_ASSIGN
    #endif
    #undef _CONFIGURE_SCHEDULER_ASSIGN
  #endif
};

RTEMS_STATIC_ASSERT(
  _CONFIGURE_MAXIMUM_PROCESSORS
    == RTEMS_ARRAY_SIZE( _Scheduler_Initial_assignments ),
  _Scheduler_Initial_assignments
);

