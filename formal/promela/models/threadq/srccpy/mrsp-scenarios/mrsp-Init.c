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

typedef struct {
  rtems_id main_task_id;
  rtems_id scheduler_ids[CPU_COUNT];
} test_context;


static void Init(rtems_task_argument arg)
{
  test_context *ctx = &test_instance;
  rtems_status_code sc;
  rtems_resource_snapshot snapshot;
  uint32_t cpu_count = rtems_scheduler_get_processor_maximum();
  // number of processors owned by the current scheduler
  uint32_t cpu_index;

  TEST_BEGIN();

  rtems_resource_snapshot_take(&snapshot);

  ctx->main_task_id = rtems_task_self();

  for (cpu_index = 0; cpu_index < MIN(2, cpu_count); ++cpu_index) {
    sc = rtems_scheduler_ident(cpu_index, &ctx->scheduler_ids[cpu_index]);
    rtems_test_assert(sc == RTEMS_SUCCESSFUL);
  }
  // rtems_scheduler_ident(0, &ctx->scheduler_ids[0]);
  // rtems_scheduler_ident(1, &ctx->scheduler_ids[1]);

  for (cpu_index = 2; cpu_index < cpu_count; ++cpu_index) {
    sc = rtems_scheduler_ident(
      cpu_index / 2 + 1,
      &ctx->scheduler_ids[cpu_index]
    );
    rtems_test_assert(sc == RTEMS_SUCCESSFUL);
  }
  // rtems_scheduler_ident(2, &ctx->scheduler_ids[2]);   // 2/2+1
  // rtems_scheduler_ident(2, &ctx->scheduler_ids[3]);   // 3/2+1
  // rtems_scheduler_ident(3, &ctx->scheduler_ids[4]);   // 4/2+1
  // rtems_scheduler_ident(3, &ctx->scheduler_ids[5]);   // 5/2+1
  // ...

  // If we assume all calls are succesfull, then:
  //  ctx->scheduler_ids[0] = _Scheduler_Build_id(0)
  //  ctx->scheduler_ids[1] = _Scheduler_Build_id(1)
  //  ctx->scheduler_ids[2] = _Scheduler_Build_id(2)
  //  ctx->scheduler_ids[3] = _Scheduler_Build_id(2)
  //  ctx->scheduler_ids[4] = _Scheduler_Build_id(3)
  //  ctx->scheduler_ids[5] = _Scheduler_Build_id(3)
  //  ...

  /* test scenarios all go here */

  rtems_test_assert(rtems_resource_snapshot_check(&snapshot));

  TEST_END();
  rtems_test_exit(0);
}


/***** PRECONDITION ************************************************************
  True
*******************************************************************************/
rtems_status_code rtems_scheduler_ident(
  rtems_name  name,
  rtems_id   *id
)
{
  rtems_status_code sc;

  if ( id != NULL ) {
    size_t n = _Scheduler_Count;
    size_t i;

    sc = RTEMS_INVALID_NAME;

    for ( i = 0 ; i < n && sc == RTEMS_INVALID_NAME ; ++i ) {
      const Scheduler_Control *scheduler = &_Scheduler_Table[ i ];

      if ( scheduler->name == name ) {
        *id = _Scheduler_Build_id( i );
        sc = RTEMS_SUCCESSFUL;
      }
    }
  } else {
    sc = RTEMS_INVALID_ADDRESS;
  }

  return sc;
}
/***** PRECONDITION ************************************************************
  id == NULL ==> returns(RTEMS_INVALID_ADDRESS)
  exists i @ name == _Scheduler_Table[i].name
      ==> id -> _Scheduler_Build_id(i) && returns(RTEMS_SUCCESSFUL)
  not (exists i @ name == _Scheduler_Table[i].name)
      ==> returns(RTEMS_INVALID_NAME)
*******************************************************************************/



RTEMS_INLINE_ROUTINE Objects_Id _Scheduler_Build_id( uint32_t scheduler_index )
{
  return _Objects_Build_id(
    OBJECTS_FAKE_OBJECTS_API,
    OBJECTS_FAKE_OBJECTS_SCHEDULERS,
    _Objects_Local_node,
    (uint16_t) ( scheduler_index + 1 )
  );
}
