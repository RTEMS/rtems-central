/* SPDX-License-Identifier: BSD-2-Clause */

/*
static void Worker{0}( rtems_task_argument arg )
{{
  Context *ctx;

  ctx = (Context *) arg;
  rtems_event_set events;

  T_log( T_NORMAL, "Worker Running" );
  TestSegment4( ctx );
  T_log( T_NORMAL, "Worker finished" );

  rtems_event_receive( RTEMS_ALL_EVENTS, RTEMS_DEFAULT_OPTIONS, 0, &events );
}}


RTEMS_ALIGNED( RTEMS_TASK_STORAGE_ALIGNMENT ) static char WorkerStorage{0}[
  RTEMS_TASK_STORAGE_SIZE(
    MAX_TLS_SIZE + RTEMS_MINIMUM_STACK_SIZE,
    WORKER_ATTRIBUTES
  )
];

static const rtems_task_config WorkerConfig{0} = {{
  .name = rtems_build_name( 'W', 'O', 'R', 'K' ),
  .initial_priority = PRIO_LOW,
  .storage_area = WorkerStorage{0},
  .storage_size = sizeof( WorkerStorage{0} ),
  .maximum_thread_local_storage_size = MAX_TLS_SIZE,
  .initial_modes = RTEMS_DEFAULT_MODES,
  .attributes = WORKER_ATTRIBUTES
}};

*/
static void Worker1( rtems_task_argument arg )
{{
  Context *ctx;

  ctx = (Context *) arg;
  rtems_event_set events;

  T_log( T_NORMAL, "Worker1 Running" );
  TestSegment4( ctx );
  T_log( T_NORMAL, "Worker1 finished" );

  rtems_event_receive( RTEMS_ALL_EVENTS, RTEMS_DEFAULT_OPTIONS, 0, &events );
}}

static void Worker2( rtems_task_argument arg )
{{
  Context *ctx;

  ctx = (Context *) arg;
  rtems_event_set events;

  T_log( T_NORMAL, "Worker2 Running" );
  TestSegment5( ctx );
  T_log( T_NORMAL, "Worker2 finished" );

  rtems_event_receive( RTEMS_ALL_EVENTS, RTEMS_DEFAULT_OPTIONS, 0, &events );
}}

static void RtemsModelMessageMgr_Setup{0}(
  RtemsModelMessageMgr_Context *ctx
)
{{
  rtems_status_code   sc;
  rtems_task_priority prio;

  T_log( T_NORMAL, "Runner Setup" );

  memset( ctx, 0, sizeof( *ctx ) );
  ctx->runner_thread = _Thread_Get_executing();
  ctx->runner_id = ctx->runner_thread->Object.id;
  ctx->worker1_wakeup = CreateWakeupSema();
  ctx->worker2_wakeup = CreateWakeupSema();
  ctx->runner_wakeup = CreateWakeupSema();

  sc = rtems_task_get_scheduler( RTEMS_SELF, &ctx->runner_sched );
  T_rsc_success( sc );

  #if defined(RTEMS_SMP)
  sc = rtems_scheduler_ident_by_processor( 1, &ctx->other_sched );
  T_rsc_success( sc );
  T_ne_u32( ctx->runner_sched, ctx->other_sched );
  #endif

  prio = 0;
  sc = rtems_task_set_priority( RTEMS_SELF, PRIO_NORMAL, &prio );
  T_rsc_success( sc );
  T_eq_u32( prio, PRIO_HIGH );

  //sc = rtems_task_construct( &WorkerConfig{0}, &ctx->worker_id );
  //T_log( T_NORMAL, "Construct Worker, sc = %x", sc );
  //T_assert_rsc_success( sc );

  //T_log( T_NORMAL, "Starting Worker..." );
  //sc = rtems_task_start( ctx->worker_id, Worker{0}, (rtems_task_argument) ctx );
  //T_log( T_NORMAL, "Started Worker, sc = %x", sc );
  //T_assert_rsc_success( sc );

  sc = rtems_task_create("WRKR",
                          PRIO_NORMAL,
                          RTEMS_MINIMUM_STACK_SIZE,
                          RTEMS_DEFAULT_MODES,
                          RTEMS_DEFAULT_ATTRIBUTES,
                          &ctx->worker1_id);
  T_assert_rsc_success( sc );

  T_log( T_NORMAL, "Starting Worker1..." );
  sc = rtems_task_start( ctx->worker1_id, Worker1,ctx );
  T_log( T_NORMAL, "Started Worker1, sc = %x", sc );
  T_assert_rsc_success( sc );

  sc = rtems_task_create("WRKR",
                          PRIO_NORMAL,
                          RTEMS_MINIMUM_STACK_SIZE,
                          RTEMS_DEFAULT_MODES,
                          RTEMS_DEFAULT_ATTRIBUTES,
                          &ctx->worker2_id);
  T_assert_rsc_success( sc );

  T_log( T_NORMAL, "Starting Worker2..." );
  sc = rtems_task_start( ctx->worker2_id, Worker2,ctx );
  T_log( T_NORMAL, "Started Worker2, sc = %x", sc );
  T_assert_rsc_success( sc );

}}


static void RtemsModelMessageMgr_Setup_Wrap{0}( void *arg )
{{
  RtemsModelMessageMgr_Context *ctx;

  ctx = arg;
  RtemsModelMessageMgr_Setup{0}( ctx );
}}


static RtemsModelMessageMgr_Context RtemsModelMessageMgr_Instance{0};

static T_fixture RtemsModelMessageMgr_Fixture{0} = {{
  .setup = RtemsModelMessageMgr_Setup_Wrap{0},
  .stop = NULL,
  .teardown = RtemsModelMessageMgr_Teardown_Wrap,
  .scope = RtemsModelMessageMgr_Scope,
  .initial_context = &RtemsModelMessageMgr_Instance{0}
}};

static T_fixture_node RtemsModelMessageMgr_Node{0};

void RtemsModelMessageMgr_Run{0}()
{{
  RtemsModelMessageMgr_Context *ctx;

  T_set_verbosity( T_NORMAL );

  T_log( T_NORMAL, "Runner Invoked" );
  T_log( T_NORMAL, "Pushing Test Fixture..." );


  ctx = T_push_fixture(
    &RtemsModelMessageMgr_Node{0},
    &RtemsModelMessageMgr_Fixture{0}
  );

  T_log( T_NORMAL, "Test Fixture Pushed" );



  ctx->this_test_number = {0};


  ctx->send_status = RTEMS_INCORRECT_STATE;
  ctx->receive_option_set = 0;
  ctx->receive_timeout = RTEMS_NO_TIMEOUT;
  _Thread_Wait_flags_set( ctx->runner_thread, THREAD_WAIT_CLASS_PERIOD );

  TestSegment0( ctx );

  Runner( ctx );

  RtemsModelMessageMgr_Cleanup( ctx );

  T_log( T_NORMAL, "Run Pop Fixture" );
  T_pop_fixture();
}}

/** @}} */
