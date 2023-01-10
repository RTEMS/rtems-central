/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Configure.pml
 *
 * Copyright (C) 2021 Trinity College Dublin (www.tcd.ie)
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
 ******************************************************************************/

/*******************************************************************************
 *  Scenario Deployment
 *    1. Allocate tasks to cores, at least one task per core
 *    2. Allocate resources to tasks, at least two tasks per resource
 *
 *  - a task runs on one core
 *  -- taskCores : Task -m-> Core
 *
 *  - a core handles multiple tasks
 *  -- coreTasks : Core -m-> P+ Task
 *
 *  - a task uses at least one resource
 *  -- taskRes : Task -m-> P Res
 *
 *  - a resource is used by at least two tasks
 *  -- resTasks : Res -m-> P+2 Task
 *
 ******************************************************************************/

// for use by inlines
byte taskIx;
byte coreIx;

byte remTasks ; // N below
byte possibleP ; // min(C,N) below
byte chosenP; // P below
byte coresLeft ; // C below
byte partSize ; // L below
byte prevSize; // Lprev below
byte smallestP; // N/P below
byte largestP; // min(N+1-P,Lprev) below


inline deployTasks() {

  // printf("  Assign Tasks to Cores\n");
  // Each task has a core, and each core has at least one task

  // Phase 1  core i handles task i
  taskIx = 0;
  do
  :: taskIx == core_count -> break;
  :: else ->
      taskConfig[taskIx].taskCore = taskIx;
      // printf( "    Phase 1 : Task %d managed by core %d\n",
      //        taskIx, taskConfig[taskIx].taskCore );
      taskIx++;
  od

  // Phase 2 assign remaining tasks to cores

  // Want a canonical solution
  // Given N tasks to be assigned to C cores:
  // 1. choose number P of non-empty partitions  P in {1,..,min(C,N)}
  // Parameters: (N, C, P, Lprev = N+1-P).
  // We generate partitions largest first.
  // If L is the size of the largest partition, we know it has to satisfy:
  //  N/P <= L <= min(N+1-P,Lprev)
  //  2. We choose L as per above.
  //  3. For the rest, we recurse with (N-L, C-1, P-1, L).
  // printf("### task_count=%d core_count:%d\n",task_count,core_count);
  remTasks = task_count - core_count;
  if
  ::  remTasks ->
      // printf("### remTasks(N=%d)\n",remTasks);
      coresLeft = core_count ;
      // printf("### coresLeft=%d\n",coresLeft);
      setMin( remTasks, core_count, possibleP );
      // printf("### possibleP(min(C,N)=%d)\n",possibleP);
      prevSize = remTasks + 1 - chosenP;
      // printf("### prevSize(Lprev=%d)\n",prevSize);
      chooseLowHigh( 1, possibleP, chosenP );
      // printf("Chosen number of partitions: [%d,%d] =  %d\n", 1, possibleP, chosenP);
      coreIx = 0;
      // printf("TOP(N,C,P,Lprev) = (%d,%d,%d,%d)\n",remTasks,coresLeft,chosenP,prevSize);
  ::  else
  fi

  do // (N,C,P,Lprev) (remTasks,coresLeft,chosenP,prevSize)
  :: remTasks == 0 -> break
  :: else ->
     lowerRatio( remTasks, chosenP, smallestP );
     setMin( remTasks + 1 - chosenP, prevSize, largestP );
     chooseLowHigh( smallestP, largestP, partSize );
     // printf("Chosen partition size: [%d,%d] =  %d\n", smallestP, largestP, partSize);
     // need to do these two before we use partSize to countdown a partition
     remTasks = remTasks - partSize ;
     prevSize = partSize;
     // assign partSize tasks to coreIx
     do
     :: partSize == 0 ->  break;
     :: else ->
        taskConfig[taskIx].taskCore = coreIx;
        // printf( "    Phase 2 : Task %d managed by core %d\n",
        //         taskIx, taskConfig[taskIx].taskCore );
        taskIx++;
        partSize--;
     od
     // setup for next iteration
     coresLeft--;
     chosenP--
     coreIx++;
     // printf("POST(N,C,P,Lprev) = (%d,%d,%d,%d)\n",remTasks,coresLeft,chosenP,prevSize)
  od

}

// for use by inlines
byte resIx;
byte resTCount; // no of tasks still needed for a resource
byte available; // no of tasks not yet allocated
byte target;    // 1..available - chosen task from those still available
byte tskResCount // no of resources allocated to task in Phase 1 below


inline linkResourcesAndTasks() {

  // printf("  Associating Resources and Tasks\n");
  // Each resource has at least two associated tasks
  // Each task has at least one associated resource

  // Phase 1 : Assign intended task count to each resource (2..task_count)
  //           and choose that number of tasks to be associated
  // printf("    Phase 1 : ensure resources have at least two associated tasks\n");
  resIx = 0;
  do
  ::  resIx == res_count -> break;
  ::  else ->
      // printf("      Resource %d : identify Tasks\n", resIx);
      if
      ::                      resTCount = 2;
      ::  task_count > 2  ->  resTCount = 3;
      ::  task_count > 3  ->  resTCount = 4;
      ::  task_count > 4  ->  resTCount = 5;
      ::  task_count > 5  ->  resTCount = 6;
      fi
      resSetup[resIx].resTaskCount = resTCount ;
      // now, make it so... we decrement resTCount for every task we add
      available = task_count;
      // printf("        resTCount = %d, available=%d\n", resIx, resTCount, available);
      do
      ::  !resTCount -> break;
      ::  else -> // find an as yet unallocated task
          // pick a number in 1..available
          if
          ::  available > 0 -> target = 1;
          ::  available > 1 -> target = 2;
          ::  available > 2 -> target = 3;
          ::  available > 3 -> target = 4;
          ::  available > 4 -> target = 5;
          ::  available > 5 -> target = 6;
          fi
          // printf("        available,target = %d,%d\n", available, target);
          // allocate that task by counting available spaces in task array
          taskIx = 0; // printf("         !taskIx:%d\n",taskIx);
          do
          ::  target == 0 || taskIx >= task_count -> break;
          ::  else ->
              if
              ::  !taskConfig[taskIx].taskRes[resIx] -> target--; break;
              ::  else -> // target > 0 or taskConfig[taskIx].taskRes[resIx]
              fi
              taskIx++; // printf("         .taskIx:%d, target:%d\n",taskIx,target);
          od
          // mark allocation in both arrays
          // printf("        Task %d uses Resource %d\n",taskIx,resIx);
          taskConfig[taskIx].taskRes[resIx] = true;
          // printf("           taskConfig[%d].taskRes[%d]=%d\n",taskIx,resIx,
          //        taskConfig[taskIx].taskRes[resIx]);
          resSetup[resIx].resTasks[taskIx] = true;
          // printf("           resSetup[%d].resTasks[%d]=%d\n",resIx,taskIx,
          //      resSetup[resIx].resTasks[taskIx]);
          resTCount--;
          available--;
      od
      resIx++;
  od

  // Phase 2 : ensure that all tasks have at least one associated resource
  // printf("    Phase 2 : ensure tasks have at least one resource\n");
  taskIx = 0;
  do
  ::  taskIx == task_count -> break;
  ::  else ->
      // printf("      Checking Task %d\n",taskIx);
      resIx = 0; tskResCount = 0;
      do
      ::  resIx == res_count -> break;
      ::  else ->
          if
          ::  taskConfig[taskIx].taskRes[resIx] -> tskResCount++ ;
          ::  else
          fi
          resIx++;
      od
      // printf("      Task %d has %d resources\n",taskIx, tskResCount);
      if
      ::  !tskResCount ->
          if
          ::                  resIx = 0;
          :: res_count > 1 -> resIx = 1;
          :: res_count > 2 -> resIx = 2;
          :: res_count > 3 -> resIx = 3;
          fi
          // printf("      Task %d assigned resources %d\n",taskIx,resIx)
          // mark allocation in both arrays
          // printf("        Task %d uses Resource %d\n",taskIx,resIx);
          taskConfig[taskIx].taskRes[resIx] = true;
          // printf("           taskConfig[%d].taskRes[%d]=%d\n",taskIx,resIx,
          //         taskConfig[taskIx].taskRes[resIx]);
          resSetup[resIx].resTasks[taskIx] = true;
          // printf("           resSetup[%d].resTasks[%d]=%d\n",resIx,taskIx,
          //        resSetup[resIx].resTasks[taskIx]);
          resSetup[resIx].resTaskCount = resSetup[resIx].resTaskCount + 1;
      ::  else
      fi
      taskIx++;
  od

}

inline generateDeployment() {
    printf("\nGenerating deployment...\n");
    deployTasks();
    linkResourcesAndTasks();
}

// for use by inlines
byte trIx;


inline printDeployment() {

  printf( "\nTask/Resource Deployment\n");

  printf( "  Task Deployment:\n");
  taskIx = 0;
  do
  :: taskIx == task_count -> break;
  :: else ->
      printf( "    taskConfig[%d] core=%d, prio=%d, taskRes:", taskIx,
              taskConfig[taskIx].taskCore, taskConfig[taskIx].taskPrio
            );
      trIx = 0;
      do
      :: trIx == res_count -> break ;
      :: else ->
          printf( " %d", taskConfig[taskIx].taskRes[trIx] );
          trIx++
      od
      printf("\n");
      taskIx++;
  od

  printf( "  Resource Deployment:\n");
  resIx = 0;
  do
  :: resIx == res_count -> break;
  :: else ->
      printf("    Resource[%d]:\n",resIx);

      printf("      Tasks:     ");
      taskIx = 0;
      do
      :: taskIx == task_count -> break;
      :: else ->
          printf(" %d",resSetup[resIx].resTasks[taskIx]);
          taskIx++
      od
      printf("\n");

      printf("      Priorities:");
      coreIx = 0;
      do
      :: coreIx == core_count -> break;
      :: else ->
          printf(" %d",resSetup[resIx].resPrio[coreIx]);
          coreIx++
      od
      printf("\n");
      resIx++
  od
}

/*******************************************************************************
 *  Scenario Priorities
 *    Every task gets a unique priority
 *
 *  - a task has a (unique) priority w.r.t to its core
 *  -- taskPrio : Task -m-> Prio
 *
 *  - a task uses at least one resource
 *  -- taskRes : Task -m-> P+ Res
 *
 *  - a resource is used by at least two tasks
 *  -- resTasks : Res -m-> P+2 Task
 *
 *  - a resource has a ceiling priority for every core which is at least
 *    as high as the highest priority of any task on that core that uses
 *    that resource.
 *  -- resPrio : Res -m-> (Core -m-> Prio)
 *
 *  Scenario Priorities
 *    1. Task priority ordering on a core matches task numbering
 *    2. Resource priority set to core/scheduler ceiling priority
 ******************************************************************************/

#define PRIO_STEP 2
#define MIN_PRIO  0
#define MAX_PRIO ((MAX_TASKS+2) * PRIO_STEP)

bool prioUsed[MAX_PRIO];

inline choosePriority( p ) {
  if
  ::                    !prioUsed[ 1]  -> p =  1  ; prioUsed[ 1]  = true;
  :: (task_count > 1 && !prioUsed[ 3]) -> p =  3  ; prioUsed[ 3]  = true;
  :: (task_count > 2 && !prioUsed[ 5]) -> p =  5  ; prioUsed[ 5]  = true;
  :: (task_count > 3 && !prioUsed[ 7]) -> p =  7  ; prioUsed[ 7]  = true;
  :: (task_count > 4 && !prioUsed[ 9]) -> p =  9  ; prioUsed[ 9]  = true;
  :: (task_count > 5 && !prioUsed[11]) -> p = 11  ; prioUsed[11]  = true;
  fi
}

byte core;
byte prio;
byte resprio;

inline setupPriorities() {
  printf("\nSetup Priorities\n");

  printf("  Assigning Priorities to Tasks\n");
  // printf("    MAX_PRIO = %d, PRIO_STEP = %d\n", MAX_PRIO, PRIO_STEP);
  // reserve extreme priorities for "system" use
  prioUsed[0] = true;
  prioUsed[MAX_PRIO-1] = true;
  taskIx = 0;
  do
  :: taskIx == task_count -> break;
  :: else ->
     choosePriority( prio );
     taskConfig[taskIx].taskPrio = prio ;
     printf("    Task %d on core %d has priority %d\n", taskIx,
                 taskConfig[taskIx].taskCore,
                 taskConfig[taskIx].taskPrio );
     taskIx++;
     printf("taskIx = %d\n",taskIx);
  od

  printf("  Computing Ceiling Priorities\n")
  // for every resource, for every task that uses it,
  //  compute the maximum priority found per core
  // First, set resource priorities to lowest (highest number)
  resIx = 0;
  do
  ::  resIx == res_count -> break;
  ::  else ->
      // printf("    Ceiling for Resource %d\n", resIx);
      taskIx = 0;
      do
      ::  taskIx == task_count -> break;
      ::  else ->
          if
          ::  resSetup[resIx].resTasks[taskIx] ->
              core = taskConfig[taskIx].taskCore;
              prio = taskConfig[taskIx].taskPrio;
              resprio = resSetup[resIx].resPrio[core];
              // printf("      Task %d, core:%d, prio:%d; Ceiling %d\n",
              //             taskIx, core, prio, resprio );
              if
              :: prio > resprio -> resSetup[resIx].resPrio[core] = prio;
              :: else
              fi
              // printf("      Ceiling is now %d\n", resSetup[resIx].resPrio[core]);
          ::  else
          fi
          taskIx++;
      od
      resIx++
  od

}

inline printSetup() {
  printf("\nSystem Setup\n");

  printf("\n  Task Cores, Priorities, and Resources\n");
  taskIx = 0;
  do
  ::  taskIx == task_count -> break;
  ::  else ->
      printf("    Task %d on core %d with priority %d\n",
                  taskIx,
                  taskConfig[taskIx].taskCore,
                  taskConfig[taskIx].taskPrio);
      printf("      Resources used:");
      resIx = 0;
      do
      ::  resIx == res_count -> break;
      ::  else ->
          if
          :: taskConfig[taskIx].taskRes[resIx] -> printf(" %d",resIx);
          :: else
          fi
          resIx++;
      od
      printf("\n");
      taskIx++;
  od


/* typedef ResSetup {
  byte resTaskCount;        // No of tasks in resTasks (> 1)
  bool resTasks[MAX_TASKS]; // P_2 task
  byte resPrio[MAX_CORES] ; // Core -m-> Prio
} ;
ResSetup resSetup[MAX_RES];  // Res -m-> ResSetup */



  printf("\n  Resource Tasks, and Core Priorities\n");
    resIx = 0;
    do
    ::  resIx == res_count -> break;
    ::  else ->
        printf("    Resource %d used by %d task(s)\n",
                    resIx,
                    resSetup[resIx].resTaskCount);
        printf("     Tasks making use:");
        taskIx = 0;
        do
        :: taskIx == task_count -> break;
        :: else ->
           if
           :: resSetup[resIx].resTasks[taskIx] -> printf(" %d",taskIx);
           :: else
           fi
           taskIx++;
        od
        printf("\n");
        printf("     Core ceiling priorities (core@prio):");
        coreIx = 0;
        do
        :: coreIx == core_count -> break;
        :: else ->
           printf(" (%d@%d)", coreIx, resSetup[resIx].resPrio[coreIx])
           coreIx++;
        od
        printf("\n");
        resIx++;
    od
}

/******************************************************************************
 * Fixed Counts
 *   MAXes: [CORE;TASK;RES]
 *   Priorities: {p,q,r,...}
 *   fixed: (core,task,res)
 *
 * TRAIL GEN 1 - [4;8;4] {1,3,5,7,9}
 *    (2,2,2) --> 1300 trail files
 *    (3,3,2) --> 4500 trail files
 *
 * TRAIL GEN 2 - [4;8;4] {1,2,3,4,5}
 *    (2,2,2) --> 1300 trail files
 *
 * TRAIL GEN 3 - [4;8;4] {1,2,3,4}
 *    (2,2,2) -->   192 trail files
 *    (3,3,2) -->  2304 trail files
 *    (3,3,3) --> 25088 trail files
 *
 * TRAIL GEN 4 - [4;6;4] {1,2,3,4}
 *    (2,2,2) -->   192 trail files
 *    (3,3,2) -->  2304 trail files
 *    (3,3,3) --> ????? trail files (prob. 25088)
 *
 * TRAIL GEN 5 - [4;6;4] {1,2,3}
 *    (3,3,2) --> 972 without full symmetry breaking
 *    (3,3,2) --> 216 with some symmettry breaking, priorities not complete
 *
 * TRAIL GEN 6 - [4;6;4] {1,...}
 *    (3,3,2) --> 8 with some symmettry breaking, priorities not complete
 *    (3,4,2) --> 102 with some symmettry breaking, priorities not complete
 *    (3,5,2) --> 999 with some symmettry breaking, priorities not complete
 *    (3,6,2) --> 8505 process priorities assigned
 *
 * TRAIL GEN 7 - [4;6;4] {1,...} left over task symmetry breaking
 *    (3,3,2) --> 8
 *    (3,4,2) --> 34
 *    (3,5,2) --> 222
 *    (3,6,2) --> 1575
 *
 * TRAIL GEN 7 - [4;6;4] {1,...} new largest task partition first algorithm.
 *    (3,3,2) --> 8
 *    (3,4,2) --> 34
 *    (3,5,2) --> 222
 *    (3,6,2) --> 945
 *
 * TRAIL GEN 8 - [4;6;4] {1,...} ceiling priorities computed.
 *    (3,3,2) --> 8
 *    (3,4,2) --> 34
 *    (3,5,2) --> 222
 *    (3,6,2) --> 945
 *
 * TRAIL GEN 9 - [4;6;4] {3,5,7,9,11,13} ceiling priorities computed.
 *    (3,3,2) --> 960
 *
 * TRAIL GEN 9 - [4;6;4] {3,5,7} ceiling priorities computed.
 *    (3,3,2) --> 48
 *
 ******************************************************************************/
