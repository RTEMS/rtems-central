/* SPDX-License-Identifier: BSD-2-Clause */


// from init.c
#define CONFIGURE_INITIAL_EXTENSIONS \
  { .thread_switch = switch_extension }, \
  RTEMS_TEST_INITIAL_EXTENSION

#define CONFIGURE_INIT_TASK_NAME rtems_build_name('M', 'A', 'I', 'N')
#define CONFIGURE_INIT_TASK_PRIORITY 2

#define _CONFIGURE_ASSERT_NOT_NULL( _type, _value ) \
  ( ( _value ) != NULL ? ( _value ) : \
    ( _type ) sizeof( int[ ( _value ) != NULL ? 1 : -1 ] ) )

#include <rtems/confdefs/percpu.h>
#include <rtems/confdefs/threads.h>
#include <rtems/rtems/object.h>
#include <rtems/rtems/tasksdata.h>
#include <rtems/sysinit.h>

#define CONFIGURE_INIT_TASK_ATTRIBUTES 0x00000000
#define CONFIGURE_INIT_TASK_INITIAL_MODES 0x00000000


rtems_task Init( rtems_task_argument );
#define CONFIGURE_INIT_TASK_ENTRY_POINT Init

extern const char *bsp_boot_cmdline;
#define CONFIGURE_INIT_TASK_ARGUMENTS \
      ( (rtems_task_argument) &bsp_boot_cmdline )
 


#define CONFIGURE_INIT_TASK_STACK_SIZE CONFIGURE_MINIMUM_TASK_STACK_SIZE


const rtems_initialization_tasks_table _RTEMS_tasks_User_task_table = {
  rtems_build_name('M', 'A', 'I', 'N'),
  CONFIGURE_MINIMUM_TASK_STACK_SIZE,
  2,
  0x00000000,
  rtems_task_entry,
  0x00000000,
  (rtems_task_argument) &bsp_boot_cmdline
};

#define RTEMS_SYSINIT_CLASSIC_USER_TASKS         002900
#define RTEMS_SYSINIT_ORDER_MIDDLE     80

// RTEMS_SYSINIT_ITEM(_RTEMS_tasks_Initialize_user_task,002900,80);
// _RTEMS_SYSINIT_ITEM(_RTEMS_tasks_Initialize_user_task,002900,80);
// _RTEMS_SYSINIT_INDEX_ITEM(_RTEMS_tasks_Initialize_user_task,0x00290080);
enum { _Sysinit_0x00290080 = index };
RTEMS_LINKER_ROSET_ITEM_ORDERED( \   // Linker stuff
  _Sysinit, \
  rtems_sysinit_item, \
  handler, \
  index \
) = { _RTEMS_tasks_Initialize_user_task }


#define _CONFIGURE_INIT_TASK_STACK_EXTRA 0


