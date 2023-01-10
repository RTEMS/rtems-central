/* SPDX-License-Identifier: BSD-2-Clause */

/*
 * barrier-mgr-model.pml
 *
 * Copyright (C) 2022 Trinity College Dublin (www.tcd.ie)
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *
 *     * Redistributions in binary form must reproduce the above
 *       copyright notice, this list of conditions and the following
 *       disclaimer in the documentation and/or other materials provided
 *       with the distribution.
 *
 *     * Neither the name of the copyright holders nor the names of its
 *       contributors may be used to endorse or promote products derived
 *       from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * The model presented here is designed to work with the following files:
 *   Refinement:   barrier-events-mgr-rfn.yml
 *   Test Preamble: barrier-events-mgr-pre.h
 *   Test Postamble: barrier-events-mgr-post.h
 *   Test Runner: barrier-events-mgr-run.h
 */

/*
 * We need to output annotations for any #define we use.
 * It is simplest to keep them all together,
 * and use an inline to output them.
 */

// Barriers - we will test Automatic and Manual Barriers 
#define MAX_BARRIERS 2 // Max amount of barriers available to be created
                       // 0 reserved for NULL pointers
// Barrier Configurations
#define BARRIER_MAN 0
#define BARRIER_AUTO 1
#define MAX_WAITERS 3
#define NO_TIMEOUT 0

// We envisage three RTEMS tasks involved.
#define TASK_MAX 4 // These are the "RTEMS" tasks only, numbered 1, 2 & 3
                   // We reserve 0 to model NULL pointers

// We use semaphores to synchronise the tasks
#define SEMA_MAX 3

// Return Values
// Defined in cpukit/include/rtems/rtems/status.h
#define RC_OK      0  // RTEMS_SUCCESSFUL 
#define RC_InvName 3  // RTEMS_INVALID_NAME 
#define RC_InvId   4  // RTEMS_INVALID_ID 
#define RC_TooMany 5  // RTEMS_TOO_MANY 
#define RC_Timeout 6  // RTEMS_TIMEOUT 
#define RC_Deleted 7  // RTEMS_OBJECT_WAS_DELETED 
#define RC_InvAddr 9  // RTEMS_INVALID_ADDRESS 
#define RC_InvNum  10 // RTEMS_INVALID_NUMBER 

// Output configuration
inline outputDefines () {
   printf("@@@ %d DEF MAX_BARRIERS %d\n",_pid,MAX_BARRIERS);
   printf("@@@ %d DEF BARRIER_MAN %d\n",_pid,BARRIER_MAN);
   printf("@@@ %d DEF BARRIER_AUTO %d\n",_pid,BARRIER_AUTO);
   printf("@@@ %d DEF MAX_WAITERS %d\n",_pid,MAX_WAITERS);
   printf("@@@ %d DEF TASK_MAX %d\n",_pid,TASK_MAX);
   printf("@@@ %d DEF SEMA_MAX %d\n",_pid,SEMA_MAX);
}

// Special values: task states, options, return codes
mtype = {
  // Task states, BarrierWait is same as TimeWait but with no timeout
  Zombie, Ready, BarrierWait, TimeWait, OtherWait,
};

// Tasks
typedef Task {
  byte nodeid; // So we can spot remote calls
  byte pmlid; // Promela process id
  mtype state ; // {Ready,BarrierWait,TimeWait,OtherWait}
  bool preemptable;
  byte prio; // lower number is higher priority
  int ticks; // clock ticks to keep track of timeout
  bool tout; // true if woken by a timeout
};

// Barriers
typedef Barrier {
  byte b_name; // barrier name
  bool isAutomatic; // true for automatic, false for manual barrier
  int maxWaiters; // maximum count of waiters for automatic barrier
  int waiterCount; // current amount of tasks waiting on the barrier
  bool waiters[TASK_MAX]; // waiters on the barrier
  bool isInitialised; // indicated whenever this barrier was created
}

Task tasks[TASK_MAX]; // tasks[0] models a NULL dereference
Barrier barriers[MAX_BARRIERS]; // barriers[0] models a NULL dereference

/*
 * Running Orders (maintained by simple global sync counter):
 *  Create;;Ident = Barrier Identified only after creating
 *  Acquire;;Release = Manual barrier is acquired and then released
 *  Acquire;;Delete = Manual barrier is acquired and then deleted
 * Here ;; is "sequential" composition of *different* threads.
 * Additionally task 1 will always create a barrier before operations
 */
bool semaphore[SEMA_MAX]; // Semaphore

inline outputDeclarations () {
  printf("@@@ %d DCLARRAY Semaphore semaphore SEMA_MAX\n",_pid);
}

/*
 * Synchronisation Mechanisms
 *
 *  Obtained(sem_id) - call that waits if semaphore 
 *   `sem_id` is aquired by someone.
 *  Obtain(sem_id) - obttains semaphore `sem_id`
 *  Release(sem_id)  - call that releases semaphore `sem_id`
 *
 * Binary semaphores:  True means available, False means in use.
 */

inline Obtain(sem_id){
  atomic{
    printf("@@@ %d WAIT %d\n",_pid,sem_id);
    semaphore[sem_id] ;        // wait until available
    semaphore[sem_id] = false; // set as in use
    printf("@@@ %d LOG WAIT %d Over\n",_pid,sem_id);
  }
}

inline Release(sem_id){
  atomic{
    printf("@@@ %d SIGNAL %d\n",_pid,sem_id);
    semaphore[sem_id] = true ; // release
  }
}

/* The following inlines are not given here as atomic,
 * but are intended to be used in an atomic context.
*/

inline nl() { printf("\n") } // Useful shorthand

/*
 * waitUntilReady(id) logs that task[id] is waiting,
 * and then attempts to execute a statement that blocks,
 * until some other process changes task[id]'s state to Ready.
 * It relies on the fact that if a statement blocks inside an atomic block,
 * the block loses its atomic behaviour and yields to other Promela processes
 *
 * It is used to model a task that has been suspended for any reason.
 */
inline waitUntilReady(id){
  atomic{
    printf("@@@ %d LOG Task %d waiting, state = ",_pid,id);
    printm(tasks[id].state); nl()
  }
  tasks[id].state == Ready; // breaks out of atomics if false
  printf("@@@ %d STATE %d Ready\n",_pid,id)
}

/*
 * satisfied(bid, sat) checks if a barrier reached enough 
 * waiters to be released. Relevant only for automatic barriers.
 */
inline satisfied(bid,sat) {
  if
  ::  barriers[bid].waiterCount >= barriers[bid].maxWaiters -> 
      printf("@@@ %d LOG Auto Barrier satisfied(<bid:%d wt:%d max:%d>)\n",
              _pid,bid,barriers[bid].waiterCount,barriers[bid].maxWaiters);
      sat = true
  ::  else -> sat = false
  fi
}

/*
 * preemptIfRequired(callerid) is executed,
 * when the tasks waiting on the barrier are released.
 *
 * It checks if task[callerid] should be preempted, and makes it so.
 * This is achieved here by setting the calling task state to OtherWait.
 * Task goes over all of the released processes and chooses one with
 * highest priority.
 */
inline preemptIfRequired(callerid) {
  int t_index = 1;
  do
  ::  t_index < TASK_MAX && t_index != callerid ->
      if
      ::  tasks[callerid].preemptable  &&
          // we use the (usual?) convention that higher priority is a lower 
          // number
          tasks[t_index].prio < tasks[callerid].prio &&
          tasks[t_index].state == Ready
          ->  tasks[callerid].state = OtherWait;
          printf("@@@ %d STATE %d OtherWait\n",_pid,callerid)
          callerid = t_index;
      ::  (!tasks[callerid].preemptable  ||
          tasks[t_index].prio > tasks[callerid].prio) &&
          tasks[t_index].state == Ready ->
          tasks[t_index].state = OtherWait;
          printf("@@@ %d STATE %d OtherWait\n",_pid,t_index)
      ::  else -> skip
      fi
      t_index++
  ::  else -> break
  od
}

/*
 * waitAtBarrier(tid, bid, rc) holds the task at the barrier. 
 *
 * It utilises the same principle as the waitUntilReady to hold the task.
 * However, here when the task is released it is checked why it was released.
 * This allows to model us correct return codes, whenever the task was released
 * due to barrier release, barrier deletion or timeout of the waiting task. 
 */
inline waitAtBarrier(tid,bid,rc){
  atomic{
    printf("@@@ %d LOG Task %d waiting, state = ",_pid,tid);
    printm(tasks[tid].state); nl()
  }
  tasks[tid].state == Ready; // breaks out of atomics if false
  if
  ::  tasks[tid].tout -> 
      barriers[bid].waiters[tid] = false; // remove self from waiters
      rc = RC_Timeout
      tasks[tid].tout = false; // reset timeout in case we reaquire
      barriers[bid].waiterCount--;
      preemptIfRequired(tid); 
      waitUntilReady(tid) // if we were higher prio, need to pre-empt others
  ::  !barriers[bid].isInitialised ->
      rc = RC_Deleted
  ::  else -> // normally released
      rc = RC_OK    
  fi
  printf("@@@ %d STATE %d Ready\n",_pid,tid)
}

/*
 * barrierRelease(self,bid) is executed, when the tasks waiting on the barrier 
 * are released.
 *
 * It can be invoked by release or delete directives in this model.
 *
 * It checks if calling task should be preempted, and makes it so.
 */
inline barrierRelease(self,bid) {
  atomic{
    int tid = 1;
    do
    :: tid < TASK_MAX -> 
       if
       ::  barriers[bid].waiters[tid] ->
           barriers[bid].waiters[tid] = false;
           tasks[tid].state = Ready
       ::  else -> skip
       fi
       tid++
    :: else -> break
    od
    barriers[bid].waiterCount = 0; 
    preemptIfRequired(self);
    waitUntilReady(self) // Of all the tasks released only one should have 
                         // Ready state and the rest is in OtherWait State.
  }
}

/*
 * barrier_create(name,attribs,max_waiters,id,rc)
 *
 * Simulates a call to rtems_barrier_create
 *   name : name of the barrier
 *   arrtibs : attribute set of the barrier
 *   max_waiters : (automatic only, optional) amount of max waiters 
 *                  on the barrier
 *   id : id of the barrier if created successfully
 *   rc : updated with the return code when directive completes
 *
 * Corresponding RTEMS call:
 *   rc = rtems_barrier_create(name,attribs,max_waiters,id);
 *     `name` models `rtems_name name`
 *     `attribs` models `rtems_attribute attribute_set`
 *     `max_waiters` models `uint32_t maximum_waiters`
 *     `id` models `rtems_event_set *id`
 *
 *  This directive does not preempt the task, so it's relatively 
 *  straightforward.
 */
inline barrier_create(name,attribs,max_waiters,id,rc) {
  atomic{
    int new_bid = 1;
    if
    ::  id == 0 -> rc = RC_InvAddr;
    ::  name <= 0 -> rc = RC_InvName;
    ::  else ->
        do
          ::  new_bid < MAX_BARRIERS ->
              if
              ::  !barriers[new_bid].isInitialised ->
                  if
                  ::  attribs == BARRIER_AUTO ->
                      if
                      ::  max_waiters > 0 ->
                            barriers[new_bid].maxWaiters = max_waiters;
                      ::  else -> 
                            rc = RC_InvNum;
                            break;
                      fi
                      barriers[new_bid].b_name = name;
                      barriers[new_bid].isAutomatic = 
                        barriers[new_bid].isAutomatic | attribs;
                      barriers[new_bid].waiterCount = 0;
                      barriers[new_bid].isInitialised = true;
                      id = new_bid;
                      rc = RC_OK;
                      printf("@@@ %d LOG %d Created {n: %d, auto: true, mw: %d}\n"
                              ,_pid, new_bid, name, max_waiters);
                      break
                  ::  else -> // attribs == BARRIER_MAN
                      barriers[new_bid].b_name = name;
                      barriers[new_bid].isAutomatic = 
                        barriers[new_bid].isAutomatic | attribs;
                      barriers[new_bid].waiterCount = 0;
                      barriers[new_bid].isInitialised = true;
                      id = new_bid;
                      rc = RC_OK;
                      printf("@@@ %d LOG %d Created {n: %d, auto: false}\n"
                              ,_pid, new_bid, name);
                      break
                  fi
              ::  else /* barriers[id].isInitialised */ -> new_bid++;
              fi
          ::  else -> // new_bid >= MAX_BARRIERS
              rc = RC_TooMany;
              break
          od
    fi 
  }
}


/*
 * barrier_ident(name,id,rc)
 *
 * Simulates a call to rtems_barrier_ident
 *   name : name of the barrier
 *   id : id of the barrier if created successfully
 *   rc : updated with the return code when the directive completes
 *
 * Corresponding RTEMS call:
 *   rc = rtems_barrier_ident(name,id);
 *     `name` models `rtems_name name`
 *     `id` models `rtems_event_set *id`
 *
 * Here we assuming that the node where the barrier was created
 * is searched.
 */
inline barrier_ident(name,id,rc) {
  atomic{
    int b_index = 1; // 0 is NULL deref
    if
    ::  id == 0 -> rc = RC_InvAddr;
    ::  name <= 0 -> 
        rc = RC_InvName;
        id = 0;
    ::  else -> // name > 0
        do
        ::  b_index < MAX_BARRIERS ->
            if
            ::  barriers[b_index ].isInitialised && 
                barriers[b_index ].b_name == name ->
                  id = b_index ;
                  printf("@@@ %d LOG Barrier %d Identified by name %d\n",
                          _pid, b_index, name);
                  rc = RC_OK;
                  break;
            ::  else -> /* !barriers[id].isInitialised || 
                           barriers[b_index ].b_name!=name */ 
                  b_index ++;
            fi
        ::  else -> // b_index  >= MAX_BARRIERS
              rc = RC_InvName;
              break;
        od
    fi
  }
}

/*
 * barrier_wait(self,bid,interval,rc)
 *
 * Simulates a call to rtems_barrier_wait
 *   self : task id making the call
 *   bid : id of the barrier
 *   interval : wait time on the barrier (0 waits forever)
 *   rc : updated with the return code when the wait completes
 *
 * Corresponding RTEMS call:
 *   rc = rtems_barrier_wait(bid, interval;
 *     `bid` models `rtems_id id`
 *     `interval` models `rtems_interval timeout`
 *
 * This directive almost always blocks the calling taks, unless it 
 * releases automatic barrier and the task still has the priority.
 * It's hard to model automatic release therefore in this model the 
 * task is calling for release of the barriers if it was going to be the
 * waiter that triggers the release.
 *
 */
inline barrier_wait(self,bid,interval,rc) {
  atomic{
    if
    ::  bid >= MAX_BARRIERS || bid <= 0 || !barriers[bid].isInitialised ->
        rc = RC_InvId
    ::  else -> // id is correct
        barriers[bid].waiterCount++;
        if
        ::  barriers[bid].isAutomatic ->
            bool sat;
            satisfied(bid, sat) // check if enough waiters to release barrier
            if
            ::  sat ->
                barrierRelease(self,bid);
                rc = RC_OK
            ::  else -> // !sat
                barriers[bid].waiters[self] = true;
                if
                ::  interval > NO_TIMEOUT ->
                    tasks[self].tout = false;
                    tasks[self].ticks = interval;
                    tasks[self].state = TimeWait;
                    printf("@@@ %d STATE %d TimeWait %d\n",_pid,self,interval);
                ::  else -> 
                    tasks[self].state = BarrierWait;
                    printf("@@@ %d STATE %d BarrierWait\n",_pid,self)
                fi
                waitAtBarrier(self,bid,rc)
            fi
        ::  else -> // !barriers[bid].isAutomatic
            barriers[bid].waiters[self] = true;
            if
            ::  interval > NO_TIMEOUT ->
                tasks[self].tout = false;
                tasks[self].ticks = interval;
                tasks[self].state = TimeWait
                printf("@@@ %d STATE %d TimeWait %d\n",_pid,self,interval);
            ::  else -> 
                tasks[self].state = BarrierWait;
                printf("@@@ %d STATE %d BarrierWait\n",_pid,self)
            fi
            waitAtBarrier(self,bid,rc)
        fi
    fi
  }
}

/*
 * barrier_release(self,bid,nreleased,rc)
 *
 * Simulates a call to rtems_barrier_release
 *   self: if of the calling task
 *   bid : id of the barrier
 *   nrelease : contains number of released tasks if successful
 *   rc : updated with the return code when the directive completes
 *
 * Corresponding RTEMS call:
 *   rc = rtems_barrier_release(bid, nreleased);
 *     `bid` models `rtems_id id`
 *     `nreleased models `uint32_t` *released`
 *
 */
inline barrier_release(self,bid,nreleased,rc) {
  atomic{
    if
    ::  nreleased == 0 -> rc = RC_InvAddr;
    ::  bid >= MAX_BARRIERS || bid <= 0 || !barriers[bid].isInitialised ->
        rc = RC_InvId
    ::  else -> 
        nreleased = barriers[bid].waiterCount;
        barrierRelease(self,bid);
        printf("@@@ %d LOG Barrier %d manually released\n", _pid, bid)
        rc = RC_OK
    fi
  }
}

/*
 * barrier_delete(self,bid,rc)
 *
 * Simulates a call to rtems_barrier_delete
 *   bid : id of the barrier
 *   rc : updated with the return code when the directive completes
 *
 * Corresponding RTEMS call:
 *   rc = rtems_barrier_delete(bid);
 *     `bid`  models `rtems_id id`
 *
 * All tasks waiting on deleted barrier are released
 */
inline barrier_delete(self,bid,rc) {
  atomic{
    if
    ::  bid >= MAX_BARRIERS || bid <= 0 || !barriers[bid].isInitialised ->
        rc = RC_InvId
    ::  else -> 
        barriers[bid].isInitialised = false; 
        barrierRelease(self,bid);
        printf("@@@ %d LOG Barrier %d deleted\n", _pid, bid)
        rc = RC_OK
    fi
  }
}

/*
 * Model Processes
 * We shall use five processes in this model.
 *  Three will represent the RTEMS tasks that will make use of the
 *    barrier directives.
 *  One will model a timer.
 *  One will model scheduling and other task management behaviour.
 */

// These are not output to test generation
#define TASK1_ID 1
#define TASK2_ID 2
#define TASK3_ID 3
#define BARRIER1_NAME 1
#define BARRIER2_NAME 2
// In SMP setting there are different cores, but all are settled on same node.
#define THIS_CORE 0
#define THAT_CORE 1

/*
 * Scenario Generation
 */

 /*
 * Task variants:
 *   Task objectives - Barrier {Create, Acquire, Release, Delete}
 *   timeout_length in {0,1,2...}
 *   
 * Task Scenarios:
 *   vary: priority, preemptable, timeout interval, barrier options
 */
typedef TaskInputs {
  bool doCreate; // will task create a barrier
  bool isAutomatic; // if doCreate is true, specifies barrier type
  int maxWaiters; // if isAutomatic is true, specifies max barrier waiters
  byte bName; // Name of barrier to create or identify
  bool doAcquire; // will task aquire the barrier
  byte timeoutLength; // only relevant if doAcquire is true, gives wait time
  bool doDelete; // will task delete the barrier
  bool doRelease; // will task release the barrier

  byte taskPrio;
  bool taskPreempt;

  bool idNull; // indicates whenever passed id is null
  bool releasedNull // indicates whenever nreleased param is null
};
TaskInputs task_in[TASK_MAX];

 /* 
 * Convenience function that assigns default options to a given `TaskInputs` 
 * structure.
 */
inline assignDefaults(defaults, opts) {
  opts.doCreate = defaults.doCreate;
  opts.isAutomatic = defaults.isAutomatic;
  opts.maxWaiters = defaults.maxWaiters;
  opts.doAcquire = defaults.doAcquire;
  opts.timeoutLength = defaults.timeoutLength;
  opts.doRelease = defaults.doRelease;
  opts.doDelete = defaults.doDelete;
  opts.taskPrio = defaults.taskPrio;
  opts.taskPreempt = defaults.taskPreempt;
  opts.bName = defaults.bName;
  opts.idNull = defaults.idNull;
  opts.releasedNull = defaults.releasedNull;
}

/*
 * Semaphore Setup
 */
int task1Sema
int task2Sema;
int task3Sema;

/* 
 * Multicore setup
 */
bool multicore;
int task1Core;
int task2Core;
int task3Core;

/*
 * Generating Scenarios
 *
 * We consider the following broad scenario classes:
 *
 *   Manual Barrier - Check for barrier creation and manual release with delete
 *   Automatic Barrier - Check for barrier creation and automatic release
 *   Acquire ; Timeout ; Delete - check correct timeout and delete behaviour
 *
 */
mtype = {ManAcqRel,AutoAcq,AutoToutDel};
mtype scenario;

inline chooseScenario() {
  // Common Defaults
  TaskInputs defaults;
  defaults.doCreate = false;
  defaults.isAutomatic = false;
  defaults.maxWaiters = 0;
  defaults.doAcquire = true;
  defaults.timeoutLength = NO_TIMEOUT;
  defaults.doRelease= false;
  defaults.doDelete = false;
  defaults.taskPrio = 2;
  defaults.taskPreempt = false;
  defaults.idNull = false;
  defaults.releasedNull = false;
  defaults.bName = BARRIER1_NAME;
  // Set the defaults
  assignDefaults(defaults, task_in[TASK1_ID]);
  task_in[TASK1_ID].doCreate = true; // Task 1 is always the creator
  assignDefaults(defaults, task_in[TASK2_ID]);
  assignDefaults(defaults, task_in[TASK3_ID]);

  // Semaphore initialization
  semaphore[0] = false;
  task1Sema = 0;
  semaphore[1] = false;
  task2Sema = 1;
  semaphore[2] = false;
  task3Sema = 2;

  tasks[TASK1_ID].state = Ready;
  tasks[TASK2_ID].state = Ready;
  tasks[TASK3_ID].state = Ready;

  multicore = false;
  task1Core = THIS_CORE;
  task2Core = THIS_CORE;
  task3Core = THIS_CORE;

  if
  ::  scenario = ManAcqRel;
  ::  scenario = AutoAcq;
  ::  scenario = AutoToutDel;
  fi
  atomic{printf("@@@ %d LOG scenario ",_pid); printm(scenario); nl()} ;

  if
  ::  scenario == ManAcqRel ->
        task_in[TASK1_ID].doAcquire = false;
        task_in[TASK1_ID].doRelease = true;
        task_in[TASK1_ID].doDelete = true;
        if
        ::  task_in[TASK1_ID].bName = 0;
            printf( "@@@ %d LOG sub-senario bad create, invalid name\n", _pid);
        ::  task_in[TASK1_ID].idNull = true;
            printf( "@@@ %d LOG sub-senario bad create, passed id null\n", 
                      _pid);
        ::  task_in[TASK2_ID].doAcquire = false;
            task_in[TASK3_ID].doAcquire = false;
            printf( "@@@ %d LOG sub-senario barrier not acquired\n", _pid);
        ::  task_in[TASK2_ID].bName = 0;
            printf( "@@@ %d LOG sub-senario Worker0 ident barrier name is 0\n",
                      _pid);
        ::  task_in[TASK1_ID].releasedNull = true;
            printf( "@@@ %d LOG sub-senario realesed passed is null\n", _pid);
        ::  task_in[TASK2_ID].idNull = true;
            printf( "@@@ %d LOG sub-senario Worker0 ident passed id null\n",
                      _pid);
        /* ::  task_in[TASK2_ID].doAcquire = false;
            task_in[TASK2_ID].doCreate = true;
            task_in[TASK2_ID].bName = BARRIER2_NAME;
            printf( "@@@ %d LOG sub-senario TooMany barriers created\n", _pid); */
        ::  skip
        fi
  ::  scenario == AutoAcq ->
        task_in[TASK1_ID].isAutomatic = true;
        task_in[TASK1_ID].maxWaiters = MAX_WAITERS;
        if
        ::  task_in[TASK1_ID].maxWaiters = 0;
            printf( "@@@ %d LOG sub-senario bad create, max_waiters is 0\n",
                      _pid);
        ::  skip
        fi
  ::  scenario == AutoToutDel ->
        task_in[TASK1_ID].doAcquire = false;
        task_in[TASK1_ID].isAutomatic = true;
        task_in[TASK1_ID].maxWaiters = MAX_WAITERS;
        task_in[TASK3_ID].timeoutLength = 4;
        task_in[TASK3_ID].doDelete = true;
  fi

  // Multicore subscenario
  if
  ::  multicore = true;
      // Its enough for the main creator task to be on another core to test
      // everything
      task1Core = THAT_CORE;
      printf( "@@@ %d LOG sub-senario multicore enabled, cores:(%d,%d,%d)\n",
                _pid, task1Core, task2Core, task3Core );
  ::  skip
  fi
}

proctype Runner (byte nid, taskid; TaskInputs opts) {
  tasks[taskid].nodeid = nid;
  tasks[taskid].pmlid = _pid;
  tasks[taskid].prio = opts.taskPrio;

  printf("@@@ %d TASK Runner\n",_pid);
  if 
  :: tasks[taskid].prio == 1 -> printf("@@@ %d CALL HighPriority\n", _pid);
  :: tasks[taskid].prio == 2 -> printf("@@@ %d CALL NormalPriority\n", _pid);
  :: tasks[taskid].prio == 3 -> printf("@@@ %d CALL LowPriority\n", _pid);
  fi
  // Preemption check setup, uncomment if necessary
  //printf("@@@ %d CALL StartLog\n",_pid);
  byte rc;
  byte bid;
  if
  :: opts.idNull -> bid = 0;
  :: else -> bid = 1;
  fi

  if
  :: multicore ->
       printf("@@@ %d CALL SetProcessor %d\n", _pid, tasks[taskid].nodeid);
  :: else -> skip
  fi

  if
  ::  opts.doCreate -> 
        printf("@@@ %d CALL barrier_create %d %d %d %d\n"
                ,_pid, opts.bName, opts.isAutomatic, opts.maxWaiters, bid);
                  /*  (name,       attribs,          max_waiters,     id, rc) */
        barrier_create(opts.bName, opts.isAutomatic, opts.maxWaiters, bid, rc);
        if
        :: rc == RC_OK -> 
            printf("@@@ %d SCALAR created %d\n", _pid, bid);
        :: else -> skip;
        fi
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> 
        printf("@@@ %d CALL barrier_ident %d %d\n", _pid, opts.bName, bid);
                  /* (name,      id, rc) */
        barrier_ident(opts.bName,bid,rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  fi
  Release(task2Sema);

  if
  ::  opts.doAcquire -> 
        printf("@@@ %d CALL barrier_wait %d %d\n",
                _pid, bid, opts.timeoutLength);
                 /* (self,   bid, timeout,            rc) */
        barrier_wait(taskid, bid, opts.timeoutLength, rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> skip
  fi

  if
  ::  opts.doRelease -> 
        Obtain(task1Sema);
        int nreleased;
        if
        :: opts.releasedNull -> nreleased = 0;
        :: else -> nreleased = 1;
        fi
        int toRelease = barriers[bid].waiterCount;
        printf("@@@ %d CALL barrier_release %d %d\n", _pid, bid, nreleased);
                    /* (self,   bid, nreleased, rc) */
        barrier_release(taskid, bid, nreleased, rc);
        if
        :: rc == RC_OK -> 
            printf("@@@ %d SCALAR released %d\n", _pid, toRelease);
        :: else -> skip;
        fi
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
        Release(task1Sema);
  ::  else -> skip
  fi

  if
  ::  opts.doDelete -> 
        Obtain(task1Sema);
        printf("@@@ %d CALL barrier_delete %d\n",_pid, bid);
                  /*  (self,   bid, rc) */
        barrier_delete(taskid, bid, rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
        Release(task1Sema);
  ::  else -> skip
  fi

  // Make sure everyone ran
  Obtain(task1Sema);
  // Wait for other tasks to finish
  Obtain(task2Sema);
  Obtain(task3Sema);

  printf("@@@ %d LOG Task %d finished\n",_pid,taskid);
  tasks[taskid].state = Zombie;
  printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
}

proctype Worker0 (byte nid, taskid; TaskInputs opts) {
  tasks[taskid].nodeid = nid;
  tasks[taskid].pmlid = _pid;
  tasks[taskid].prio = opts.taskPrio;

  printf("@@@ %d TASK Worker0\n",_pid);
  if 
  :: tasks[taskid].prio == 1 -> printf("@@@ %d CALL HighPriority\n", _pid);
  :: tasks[taskid].prio == 2 -> printf("@@@ %d CALL NormalPriority\n", _pid);
  :: tasks[taskid].prio == 3 -> printf("@@@ %d CALL LowPriority\n", _pid);
  fi
  // Preemption check setup, uncomment if necessary
  //printf("@@@ %d CALL StartLog\n",_pid);
  byte rc;
  byte bid;
  if
  :: opts.idNull -> bid = 0;
  :: else -> bid = 1;
  fi

  if
  :: multicore ->
       printf("@@@ %d CALL SetProcessor %d\n", _pid, tasks[taskid].nodeid);
  :: else -> skip
  fi

  Obtain(task2Sema);
  if
  ::  opts.doCreate -> 
        printf("@@@ %d CALL barrier_create %d %d %d %d\n"
                ,_pid, opts.bName, opts.isAutomatic, opts.maxWaiters, bid);
                  /*  (name,       attribs,          max_waiters,     id, rc) */
        barrier_create(opts.bName, opts.isAutomatic, opts.maxWaiters, bid, rc);
        if
        :: rc == RC_OK -> 
            printf("@@@ %d SCALAR created %d\n", _pid, bid);
        :: else -> skip;
        fi
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> 
        printf("@@@ %d CALL barrier_ident %d %d\n", _pid, opts.bName, bid);
                  /* (name,      id, rc) */
        barrier_ident(opts.bName,bid,rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  fi

  if
  ::  opts.doAcquire -> 
        atomic{
          Release(task3Sema);
          printf("@@@ %d CALL barrier_wait %d %d\n",
                    _pid, bid, opts.timeoutLength);          
                   /* (self,   bid, timeout,            rc) */
          barrier_wait(taskid, bid, opts.timeoutLength, rc);
        }
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> Release(task3Sema);
  fi

  if
  ::  opts.doRelease -> 
        int nreleased;
        if
        :: opts.releasedNull -> nreleased = 0;
        :: else -> nreleased = 1;
        fi
        int toRelease = barriers[bid].waiterCount;
        printf("@@@ %d CALL barrier_release %d %d\n", _pid, bid, nreleased);
                    /* (self,   bid, nreleased, rc) */
        barrier_release(taskid, bid, nreleased, rc);
        if
        :: rc == RC_OK -> 
            printf("@@@ %d SCALAR released %d\n", _pid, toRelease);
        :: else -> skip;
        fi
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> skip
  fi

  if
  ::  opts.doDelete -> 
        printf("@@@ %d CALL barrier_delete %d\n",_pid, bid);
                  /*  (self,   bid, rc) */
        barrier_delete(taskid, bid, rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> skip
  fi
  atomic{
    Release(task2Sema);
    printf("@@@ %d LOG Task %d finished\n",_pid,taskid);
    tasks[taskid].state = Zombie;
    printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
  }
}

proctype Worker1 (byte nid, taskid; TaskInputs opts) {
  tasks[taskid].nodeid = nid;
  tasks[taskid].pmlid = _pid;
  tasks[taskid].prio = opts.taskPrio;

  printf("@@@ %d TASK Worker1\n",_pid);
  if 
  :: tasks[taskid].prio == 1 -> printf("@@@ %d CALL HighPriority\n", _pid);
  :: tasks[taskid].prio == 2 -> printf("@@@ %d CALL NormalPriority\n", _pid);
  :: tasks[taskid].prio == 3 -> printf("@@@ %d CALL LowPriority\n", _pid);
  fi
  // Preemption check setup, uncomment if necessary
  //printf("@@@ %d CALL StartLog\n",_pid);
  byte rc;
  byte bid;
  if
  :: opts.idNull -> bid = 0;
  :: else -> bid = 1;
  fi

  if
  :: multicore ->
       printf("@@@ %d CALL SetProcessor %d\n", _pid, tasks[taskid].nodeid);
  :: else -> skip
  fi
  Obtain(task3Sema);

  if
  ::  opts.doCreate -> 
        printf("@@@ %d CALL barrier_create %d %d %d %d\n"
                ,_pid, opts.bName, opts.isAutomatic, opts.maxWaiters, bid);
                  /*  (name,       attribs,          max_waiters,     id, rc) */
        barrier_create(opts.bName, opts.isAutomatic, opts.maxWaiters, bid, rc);
        if
        :: rc == RC_OK -> 
            printf("@@@ %d SCALAR created %d\n", _pid, bid);
        :: else -> skip;
        fi
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> 
        printf("@@@ %d CALL barrier_ident %d %d\n", _pid, opts.bName, bid);
                  /* (name,      id, rc) */
        barrier_ident(opts.bName,bid,rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  fi

  if
  ::  opts.doAcquire -> 
        atomic{
          Release(task1Sema);
          printf("@@@ %d CALL barrier_wait %d %d\n",
                    _pid, bid, opts.timeoutLength);          
                   /* (self,   bid, timeout,            rc) */
          barrier_wait(taskid, bid, opts.timeoutLength, rc);
        }
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> Release(task1Sema);
  fi

  if
  ::  opts.doRelease -> 
        int nreleased;
        if
        :: opts.releasedNull -> nreleased = 0;
        :: else -> nreleased = 1;
        fi
        int toRelease = barriers[bid].waiterCount;
        printf("@@@ %d CALL barrier_release %d %d\n", _pid, bid, nreleased);
                    /* (self,   bid, nreleased, rc) */
        barrier_release(taskid, bid, nreleased, rc);
        if
        :: rc == RC_OK -> 
            printf("@@@ %d SCALAR released %d\n", _pid, toRelease);
        :: else -> skip;
        fi
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> skip
  fi

  if
  ::  opts.doDelete -> 
        printf("@@@ %d CALL barrier_delete %d\n",_pid, bid);
                  /*  (self,   bid, rc) */
        barrier_delete(taskid, bid, rc);
        printf("@@@ %d SCALAR rc %d\n",_pid, rc);
  ::  else -> skip
  fi
  atomic {
    Release(task3Sema);
    printf("@@@ %d LOG Task %d finished\n",_pid,taskid);
    tasks[taskid].state = Zombie;
    printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
  }
}

bool stopclock = false;

/*
 * We need a process that periodically wakes up blocked processes.
 * This is modelling background behaviour of the system,
 * such as ISRs and scheduling.
 * We visit all tasks in round-robin order (to prevent starvation)
 * and make them ready if waiting on "other" things.
 * Tasks waiting for events or timeouts are not touched
 * This terminates when all tasks are zombies.
 */
proctype System () {
  byte taskid ;
  bool liveSeen;

  printf("@@@ %d LOG System running...\n",_pid);

  loop:
  taskid = 1;
  liveSeen = false;

  printf("@@@ %d LOG Loop through tasks...\n",_pid);
  atomic {
    printf("@@@ %d LOG Scenario is ",_pid);
    printm(scenario); nl();
  }
  do   // while taskid < TASK_MAX ....
  ::  taskid == TASK_MAX -> break;
  ::  else ->
      atomic {
        printf("@@@ %d LOG Task %d state is ",_pid,taskid);
        printm(tasks[taskid].state); nl()
      }
      if
      :: tasks[taskid].state == Zombie -> taskid++
      :: else ->
         if
         ::  tasks[taskid].state == OtherWait
             -> tasks[taskid].state = Ready
                printf("@@@ %d LOG %d Ready\n",_pid,taskid)
         ::  else -> skip
         fi
         liveSeen = true;
         taskid++
      fi
  od

  printf("@@@ %d LOG ...all visited, live:%d\n",_pid,liveSeen);

  if
  ::  liveSeen -> goto loop
  ::  else
  fi
  printf("@@@ %d LOG All are Zombies, game over.\n",_pid);
  stopclock = true;
}


/*
 * We need a process that handles a clock tick,
 * by decrementing the tick count for tasks waiting on a timeout.
 * Such a task whose ticks become zero is then made Ready,
 * and its timer status is flagged as a timeout
 * This terminates when all tasks are zombies
 * (as signalled by System via `stopclock`).
 */
proctype Clock () {
  int tid, tix;
  printf("@@@ %d LOG Clock Started\n",_pid)
  do
  ::  stopclock  -> goto stopped
  ::  !stopclock ->
      printf(" (tick) \n");
      tid = 1;
      do
      ::  tid == TASK_MAX -> break
      ::  else ->
          atomic{
            printf("Clock: tid=%d, state=",tid); printm(tasks[tid].state); nl()
          };
          if
          ::  tasks[tid].state == TimeWait ->
              tix = tasks[tid].ticks - 1;
              // printf("Clock: ticks=%d, tix=%d\n",tasks[tid].ticks,tix);
              if
              ::  tix == 0
                  tasks[tid].tout = true
                  tasks[tid].state = Ready
                  printf("@@@ %d LOG %d Ready\n",_pid,tid)
              ::  else
                  tasks[tid].ticks = tix
              fi
          ::  else // state != TimeWait
          fi
          tid = tid + 1
      od
  od
stopped:
  printf("@@@ %d LOG Clock Stopped\n",_pid);
}


init {
  pid nr;

  printf("Barrier Manager Model running.\n");
  printf("Setup...\n");

  printf("@@@ %d LOG TestName: Barrier_Manager_TestGen\n",_pid)
  outputDefines();
  outputDeclarations();

  printf("@@@ %d INIT\n",_pid);
  chooseScenario();


  printf("Run...\n");

  run System();
  run Clock();

  run Runner(task1Core,TASK1_ID,task_in[TASK1_ID]);
  run Worker0(task2Core,TASK2_ID,task_in[TASK2_ID]);
  run Worker1(task3Core,TASK3_ID,task_in[TASK3_ID]);

  _nr_pr == 1;

//#ifdef TEST_GEN
  assert(false);
//#endif

  printf("Barrier Manager Model finished !\n")
}