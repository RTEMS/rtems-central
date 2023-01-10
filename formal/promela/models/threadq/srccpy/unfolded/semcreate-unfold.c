/**
 * UNFOLDED: semcreate.c
 *  we apply all macro simplifications for the MrsP scenario
 *
 * We assume the following settings throughout:
 *   Defined macros:
 *     RTEMS_SMP  RTEMS_SCORE_CPUSTDATOMIC_USE_STDATOMIC
 *   Undefined macros:
 *     RTEMS_DEBUG  RTEMS_PROFILING  RTEMS_SMP_LOCK_DO_NOT_INLINE
 *     RTEMS_MULTIPROCESSING
 *   Semaphore call arguments:
 *     RTEMS_PRIORITY                         : rtems_attribute (bit)
 *     RTEMS_BINARY_SEMAPHORE                 : rtems_attribute (bit)
 *     RTEMS_MULTIPROCESSOR_RESOURCE_SHARING  : rtems_attribute (bit)
 */

/*
 *  COPYRIGHT (c) 1989-2014.
 *  On-Line Applications Research Corporation (OAR).
 *
 *  The license and distribution terms for this file may be
 *  found in the file LICENSE in this distribution or at
 *  http://www.rtems.org/license/LICENSE.
 */


#define SEMAPHORE_KIND_MASK (
     RTEMS_BINARY_SEMAPHORE       | RTEMS_COUNTING_SEMAPHORE
  | RTEMS_SIMPLE_BINARY_SEMAPHORE | RTEMS_INHERIT_PRIORITY
  | RTEMS_PRIORITY_CEILING        | RTEMS_MULTIPROCESSOR_RESOURCE_SHARING )

/*
 * We assume name and id are valid
 * We assume count == 1
 * We assume attribute_set
 *  ==  RTEMS_PRIORITY | RTEMS_BINARY_SEMAPHORE
 *    | RTEMS_MULTIPROCESSOR_RESOURCE_SHARING
 * We assume that allocations succeed
 */


rtems_status_code rtems_semaphore_create(
  rtems_name           name,
  uint32_t             count, // = 1
  rtems_attribute      attribute_set,
  rtems_task_priority  priority_ceiling,
  rtems_id            *id
)
{
  Semaphore_Control       *the_semaphore;
  Thread_Control          *executing;
  // Status_Control           status;
  const Scheduler_Control *scheduler;
  // bool                     valid;
  Priority_Control         priority;

  // attribute_set = RTEMS_PRIORITY | RTEMS_BINARY_SEMAPHORE
                     | RTEMS_MULTIPROCESSOR_RESOURCE_SHARING

    
  the_semaphore = _Semaphore_Allocate(); // allocator locked on return
  _Semaphore_Set_flags( the_semaphore,
                        SEMAPHORE_VARIANT_MRSP | SEMAPHORE_DISCIPLINE_PRIORITY );
  executing = _Thread_Get_executing();
  scheduler = _Thread_Scheduler_get_home( executing );
  priority = _RTEMS_Priority_To_core( scheduler, priority_ceiling, &valid );
  // net effect of the above is priority = priority_ceiling for us

  status = _MRSP_Initialize(
          &the_semaphore->Core_control.MRSP,
          scheduler,
          priority,
          executing,
          false // count == 0
        );

 *id = _Objects_Open_u32(
    &_Semaphore_Information,
    &the_semaphore->Object,
    name
  );
  _Objects_Allocator_unlock();
  return RTEMS_SUCCESSFUL;
}

/*
 * We will unfold _MRSP_Initialize here
 */
 RTEMS_INLINE_ROUTINE Status_Control _MRSP_Initialize(
   MRSP_Control            *mrsp,
   const Scheduler_Control *scheduler,
   Priority_Control         ceiling_priority,
   Thread_Control          *executing,
   bool                     initially_locked // false
 )
 {
   Thread_queue_Context queue_context;
   ISR_Level            level;
   size_t               scheduler_count;

   scheduler_count = _Scheduler_Count;

   for ( i = 0 ; i < scheduler_count ; ++i ) {
     const Scheduler_Control *scheduler_of_index;

     scheduler_of_index = &_Scheduler_Table[ i ];

     if ( scheduler != scheduler_of_index ) {
       mrsp->ceiling_priorities[ i ] =
         // _Scheduler_Map_priority( scheduler_of_index, 0 );
         // for us, all priority maps are identity functions
         ( *scheduler_of_index->Operations.map_priority )
         ( scheduler_of_index, 0 );
     } else {
       mrsp->ceiling_priorities[ i ] = ceiling_priority;
     }
   }

   const char TOname[] = { '\0' };

   _Atomic_Init_uint( &(&(&(&mrsp->Wait_queue)->Queue)->Lock)->next_ticket, 0U );
   _Atomic_Init_uint( &(&(&(&mrsp->Wait_queue)->Queue)->Lock)->now_serving, 0U );
   &(&mrsp->Wait_queue)->Queue->heads = NULL;
   &(&mrsp->Wait_queue)->Queue->owner = NULL;
   &(&mrsp->Wait_queue)->Queue->name = TOname ;

   return STATUS_SUCCESSFUL;
 }
