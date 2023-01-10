/* SPDX-License-Identifier: BSD-2-Clause */

// Task 0
static void Runner( RtemsModelBarrierMgr_Context *ctx )
{
  T_log( T_NORMAL, "Runner(Task 0) running" );
  TestSegment3( ctx );
  T_log( T_NORMAL, "Runner(Task 0) finished" );

  // Ensure we hold no semaphores
  ReleaseSema( ctx->runner_sema );
  ReleaseSema( ctx->worker0_sema );
  ReleaseSema( ctx->worker1_sema );
}

// Task 1
static void Worker0( rtems_task_argument arg )
{
  Context *ctx;
  ctx = (Context *) arg;
  rtems_event_set events;

  T_log( T_NORMAL, "Worker0(Task 1) running" );
  TestSegment4( ctx );
  T_log( T_NORMAL, "Worker0(Task 1) finished" );

  // Wait for events so that we don't terminate
  rtems_event_receive( RTEMS_ALL_EVENTS, RTEMS_DEFAULT_OPTIONS, 0, &events );
}

// Task 2
static void Worker1( rtems_task_argument arg )
{
  Context *ctx;
  ctx = (Context *) arg;
  rtems_event_set events;

  T_log( T_NORMAL, "Worker1(Task 2) running" );
  TestSegment5( ctx );
  T_log( T_NORMAL, "Worker1(Task 2) finished" );

  // Wait for events so that we don't terminate
  rtems_event_receive( RTEMS_ALL_EVENTS, RTEMS_DEFAULT_OPTIONS, 0, &events );
}