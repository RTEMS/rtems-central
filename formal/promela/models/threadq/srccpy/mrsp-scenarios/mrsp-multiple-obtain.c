/*
 * Copyright (c) 2014-2015 embedded brains GmbH.  All rights reserved.
 *
 *  embedded brains GmbH
 *  Dornierstr. 4
 *  82178 Puchheim
 *  Germany
 *  <rtems@embedded-brains.de>
 *
 * The license and distribution terms for this file may be
 * found in the file LICENSE in this distribution or at
 * http://www.rtems.org/license/LICENSE.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <sys/param.h>

#include <stdio.h>
#include <inttypes.h>

#include <rtems.h>
#include <rtems/libcsupport.h>
#include <rtems/score/schedulersmpimpl.h>
#include <rtems/score/smpbarrier.h>
#include <rtems/score/smplock.h>

#include "tmacros.h"

const char rtems_test_name[] = "SMPMRSP 1";

#define CPU_COUNT 32

#define MRSP_COUNT 32

#define SWITCH_EVENT_COUNT 32

// a lot of the fields in the two structs below belong to switch extension
typedef struct {
  uint32_t cpu_index;
  const Thread_Control *executing;
  const Thread_Control *heir;
  const Thread_Control *heir_node;
  Priority_Control heir_priority;
} switch_event;

typedef struct {
  rtems_id main_task_id;
  rtems_id scheduler_ids[CPU_COUNT];
  SMP_lock_Control switch_lock;
  size_t switch_index;
  switch_event switch_events[32];
} test_context;

static test_context test_instance = {
  .switch_lock = SMP_LOCK_INITIALIZER("test instance switch lock")
};


static rtems_task_priority get_prio(rtems_id task_id)
{
  rtems_status_code sc;
  rtems_task_priority prio;

  sc = rtems_task_set_priority(task_id, RTEMS_CURRENT_PRIORITY, &prio);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  return prio;
}


static void assert_prio(rtems_id task_id, rtems_task_priority expected_prio)
{
  rtems_test_assert(get_prio(task_id) == expected_prio);
}

static void change_prio(rtems_id task_id, rtems_task_priority prio)
{
  rtems_status_code sc;

  sc = rtems_task_set_priority(task_id, prio, &prio);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);
}

static void switch_extension(Thread_Control *executing, Thread_Control *heir)
{
  test_context *ctx = &test_instance;
  SMP_lock_Context lock_context;
  size_t i;

  _SMP_lock_ISR_disable_and_acquire(&ctx->switch_lock, &lock_context);

  i = ctx->switch_index;
  if (i < SWITCH_EVENT_COUNT) {
    switch_event *e = &ctx->switch_events[i];
    Scheduler_SMP_Node *node = _Scheduler_SMP_Thread_get_node(heir);

    e->cpu_index = rtems_scheduler_get_processor();
    e->executing = executing;
    e->heir = heir;
    e->heir_node = _Scheduler_Node_get_owner(&node->Base);
    e->heir_priority = node->priority;

    ctx->switch_index = i + 1;
  }

  _SMP_lock_Release_and_ISR_enable(&ctx->switch_lock, &lock_context);
}


static void create_mrsp_sema(
  test_context *ctx,
  rtems_id *id,
  rtems_task_priority prio
)
{
  uint32_t cpu_count = rtems_scheduler_get_processor_maximum();
  uint32_t index;
  rtems_status_code sc;

  sc = rtems_semaphore_create(
    rtems_build_name('M', 'R', 'S', 'P'),
    1,
    RTEMS_BINARY_SEMAPHORE | RTEMS_PRIORITY |
      RTEMS_MULTIPROCESSOR_RESOURCE_SHARING,
    prio,
    id
  );
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  for (index = 1; index < cpu_count; index = ((index + 2) & ~UINT32_C(1))) {
    rtems_task_priority old_prio;

    old_prio = 1;
    sc = rtems_semaphore_set_priority(
      *id,
      ctx->scheduler_ids[index],
      prio,
      &old_prio
    );
    rtems_test_assert(sc == RTEMS_SUCCESSFUL);
    rtems_test_assert(old_prio == 0);
  }
}


/*
 * Scenario:  Multiple Obtain
 */
static void test_mrsp_multiple_obtain(test_context *ctx)
{
  rtems_status_code sc;
  rtems_id sem_a_id;
  rtems_id sem_b_id;
  rtems_id sem_c_id;

  puts("test MrsP multiple obtain");

  change_prio(RTEMS_SELF, 4);

  create_mrsp_sema(ctx, &sem_a_id, 3);
  create_mrsp_sema(ctx, &sem_b_id, 2);
  create_mrsp_sema(ctx, &sem_c_id, 1);

  assert_prio(RTEMS_SELF, 4);

  sc = rtems_semaphore_obtain(sem_a_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 3);

  sc = rtems_semaphore_obtain(sem_b_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 2);

  sc = rtems_semaphore_obtain(sem_c_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 1);

  sc = rtems_semaphore_release(sem_c_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 2);

  sc = rtems_semaphore_release(sem_b_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 3);

  sc = rtems_semaphore_release(sem_a_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 4);

  sc = rtems_semaphore_obtain(sem_a_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 3);

  sc = rtems_semaphore_obtain(sem_b_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 2);

  sc = rtems_semaphore_obtain(sem_c_id, RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 1);
  change_prio(RTEMS_SELF, 3);
  assert_prio(RTEMS_SELF, 1);

  sc = rtems_semaphore_release(sem_c_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 2);

  sc = rtems_semaphore_release(sem_b_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 3);

  sc = rtems_semaphore_release(sem_a_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 3);

  sc = rtems_semaphore_delete(sem_a_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_semaphore_delete(sem_b_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_semaphore_delete(sem_c_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);
}


static void Init_Multiple_Obtain(rtems_task_argument arg)
{
  test_context *ctx = &test_instance;
  rtems_status_code sc;
  rtems_resource_snapshot snapshot;
  uint32_t cpu_count = rtems_scheduler_get_processor_maximum(); // 1
  uint32_t cpu_index;

  TEST_BEGIN();

  rtems_resource_snapshot_take(&snapshot);

  ctx->main_task_id = rtems_task_self();

  for (cpu_index = 0; cpu_index < MIN(2, cpu_count); ++cpu_index) {
    sc = rtems_scheduler_ident(cpu_index, &ctx->scheduler_ids[cpu_index]);
    rtems_test_assert(sc == RTEMS_SUCCESSFUL);
  }

  for (cpu_index = 2; cpu_index < cpu_count; ++cpu_index) {
    sc = rtems_scheduler_ident(
      cpu_index / 2 + 1,
      &ctx->scheduler_ids[cpu_index]
    );
    rtems_test_assert(sc == RTEMS_SUCCESSFUL);
  }

  test_mrsp_multiple_obtain(ctx);

  rtems_test_assert(rtems_resource_snapshot_check(&snapshot));

  TEST_END();
  rtems_test_exit(0);
}

#define CONFIGURE_MICROSECONDS_PER_TICK 1000

#define CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_SIMPLE_CONSOLE_DRIVER

#define CONFIGURE_MAXIMUM_TASKS (2 * CPU_COUNT + 2)
#define CONFIGURE_MAXIMUM_SEMAPHORES (MRSP_COUNT + 1)
#define CONFIGURE_MAXIMUM_TIMERS 1

#define CONFIGURE_MAXIMUM_PROCESSORS CPU_COUNT

#define CONFIGURE_SCHEDULER_SIMPLE_SMP

#include <rtems/scheduler.h>

RTEMS_SCHEDULER_SIMPLE_SMP(0);
...
RTEMS_SCHEDULER_SIMPLE_SMP(16);

#define CONFIGURE_SCHEDULER_TABLE_ENTRIES \
  RTEMS_SCHEDULER_TABLE_SIMPLE_SMP(0, 0), \
  ...
  RTEMS_SCHEDULER_TABLE_SIMPLE_SMP(16, 16)

#define CONFIGURE_SCHEDULER_ASSIGNMENTS \
  RTEMS_SCHEDULER_ASSIGN(0, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_MANDATORY), \
  RTEMS_SCHEDULER_ASSIGN(1, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL), \
  ...
  RTEMS_SCHEDULER_ASSIGN(16, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL)

#define CONFIGURE_INITIAL_EXTENSIONS \
  { .thread_switch = switch_extension }, \
  RTEMS_TEST_INITIAL_EXTENSION

#define CONFIGURE_INIT_TASK_NAME rtems_build_name('M', 'A', 'I', 'N')
#define CONFIGURE_INIT_TASK_PRIORITY 2

#define CONFIGURE_RTEMS_INIT_TASKS_TABLE

#define CONFIGURE_INIT

#include <rtems/confdefs.h>
