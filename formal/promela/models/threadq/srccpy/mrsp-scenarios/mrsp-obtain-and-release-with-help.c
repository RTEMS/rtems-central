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

typedef struct {
  uint32_t cpu_index;
  const Thread_Control *executing;
  const Thread_Control *heir;
  const Thread_Control *heir_node;
  Priority_Control heir_priority;
} switch_event;

typedef struct {
  rtems_id main_task_id;
  rtems_id mrsp_ids[MRSP_COUNT];
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

static void wait_for_prio(rtems_id task_id, rtems_task_priority prio)
{
  while (get_prio(task_id) != prio) {
    /* Wait */
  }
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

static void reset_switch_events(test_context *ctx)
{
  SMP_lock_Context lock_context;

  _SMP_lock_ISR_disable_and_acquire(&ctx->switch_lock, &lock_context);
  ctx->switch_index = 0;
  _SMP_lock_Release_and_ISR_enable(&ctx->switch_lock, &lock_context);
}

static size_t get_switch_events(test_context *ctx)
{
  SMP_lock_Context lock_context;
  size_t events;

  _SMP_lock_ISR_disable_and_acquire(&ctx->switch_lock, &lock_context);
  events = ctx->switch_index;
  _SMP_lock_Release_and_ISR_enable(&ctx->switch_lock, &lock_context);

  return events;
}

static void print_switch_events(test_context *ctx)
{
  size_t n = get_switch_events(ctx);
  size_t i;

  for (i = 0; i < n; ++i) {
    switch_event *e = &ctx->switch_events[i];
    char ex[5];
    char hr[5];
    char hn[5];

    rtems_object_get_name(e->executing->Object.id, sizeof(ex), &ex[0]);
    rtems_object_get_name(e->heir->Object.id, sizeof(hr), &hr[0]);
    rtems_object_get_name(e->heir_node->Object.id, sizeof(hn), &hn[0]);

    printf(
      "[%" PRIu32 "] %4s -> %4s (prio %3" PRIu64 ", node %4s)\n",
      e->cpu_index,
      &ex[0],
      &hr[0],
      e->heir_priority,
      &hn[0]
    );
  }
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

static void run_task(rtems_task_argument arg)
{
  volatile bool *run = (volatile bool *) arg;

  *run = true;

  while (true) {
    /* Do nothing */
  }
}


static void help_task(rtems_task_argument arg)
{
  test_context *ctx = &test_instance;
  rtems_status_code sc;

  sc = rtems_semaphore_obtain(ctx->mrsp_ids[0], RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_semaphore_release(ctx->mrsp_ids[0]);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  while (true) {
    /* Do nothing */
  }
}

static void test_mrsp_obtain_and_release_with_help(test_context *ctx)
{
  rtems_status_code sc;
  rtems_id help_task_id;
  rtems_id run_task_id;
  volatile bool run = false;

  puts("test MrsP obtain and release with help");

  change_prio(RTEMS_SELF, 3);

  reset_switch_events(ctx);

  create_mrsp_sema(ctx, &ctx->mrsp_ids[0], 2);

  sc = rtems_semaphore_obtain(ctx->mrsp_ids[0], RTEMS_WAIT, RTEMS_NO_TIMEOUT);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  assert_prio(RTEMS_SELF, 2);

  sc = rtems_task_create(
    rtems_build_name('H', 'E', 'L', 'P'),
    255,
    RTEMS_MINIMUM_STACK_SIZE,
    RTEMS_DEFAULT_MODES,
    RTEMS_DEFAULT_ATTRIBUTES,
    &help_task_id
  );
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_task_set_scheduler(
    help_task_id,
    ctx->scheduler_ids[1],
    3
  );
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_task_start(help_task_id, help_task, 0);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_task_create(
    rtems_build_name(' ', 'R', 'U', 'N'),
    4,
    RTEMS_MINIMUM_STACK_SIZE,
    RTEMS_DEFAULT_MODES,
    RTEMS_DEFAULT_ATTRIBUTES,
    &run_task_id
  );
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_task_start(run_task_id, run_task, (rtems_task_argument) &run);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  wait_for_prio(help_task_id, 2);

  sc = rtems_task_wake_after(2);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  rtems_test_assert(rtems_scheduler_get_processor() == 0);
  rtems_test_assert(!run);

  change_prio(run_task_id, 1);

  rtems_test_assert(rtems_scheduler_get_processor() == 1);

  while (!run) {
    /* Wait */
  }

  sc = rtems_task_wake_after(2);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  rtems_test_assert(rtems_scheduler_get_processor() == 1);

  change_prio(run_task_id, 4);

  rtems_test_assert(rtems_scheduler_get_processor() == 1);

  /*
   * With this operation the scheduler instance 0 has now only the main and the
   * idle threads in the ready set.
   */
  sc = rtems_task_suspend(run_task_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  rtems_test_assert(rtems_scheduler_get_processor() == 1);

  change_prio(RTEMS_SELF, 1);
  change_prio(RTEMS_SELF, 3);

  sc = rtems_semaphore_release(ctx->mrsp_ids[0]);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  rtems_test_assert(rtems_scheduler_get_processor() == 0);

  assert_prio(RTEMS_SELF, 3);

  wait_for_prio(help_task_id, 3);

  print_switch_events(ctx);

  sc = rtems_semaphore_delete(ctx->mrsp_ids[0]);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_task_delete(help_task_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);

  sc = rtems_task_delete(run_task_id);
  rtems_test_assert(sc == RTEMS_SUCCESSFUL);
}


static void Init_Obtain_and_Release_with_Help(rtems_task_argument arg)
{
  test_context *ctx = &test_instance;
  rtems_status_code sc;
  rtems_resource_snapshot snapshot;
  uint32_t cpu_count = 2 // rtems_scheduler_get_processor_maximum();
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

  if (cpu_count > 1) {
    test_mrsp_obtain_and_release_with_help(ctx);
  }

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
  RTEMS_SCHEDULER_TABLE_SIMPLE_SMP(1, 1), \
  ...
  RTEMS_SCHEDULER_TABLE_SIMPLE_SMP(16, 16)

#define CONFIGURE_SCHEDULER_ASSIGNMENTS \
  RTEMS_SCHEDULER_ASSIGN(0, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_MANDATORY), \
  RTEMS_SCHEDULER_ASSIGN(1, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL), \
  RTEMS_SCHEDULER_ASSIGN(2, RTEMS_SCHEDULER_ASSIGN_PROCESSOR_OPTIONAL), \
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
