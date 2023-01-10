/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Sizing.pml
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

/******************************************************************************
 * We model a number of cores on which one or more tasks can be running,
 * under the control of a number of schedulers.
 * We assume tasks are accessing resources protected by MrsP semaphores.
 * The focus is on modelling the algorithms used to create, obtain, and release
 * such semaphores.
 ******************************************************************************/
#define MAX_CORES 4
#define MAX_TASKS 6
#define MAX_RES 4

/******************************************************************************
 * After discussion with SH (26/10/2021), we assume one core per scheduler
 *
 * Key relationships:
 *
 *  - each core has its own scheduler
 *  --  Core ~ Sched
 *
 *  - a task runs on one core
 *  -- taskCores : Task -m-> Core
 *
 *  - a core handles multiple tasks
 *  -- coreTasks : Core -m-> P+ Task
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
 * Scenario Generation:
 *
 *  Scenario Sizing:
 *    1. choose number of cores, at least one
 *    2. choose number of tasks, at least two, and at least one per core
 *    3. choose number of resources, at least one
 ******************************************************************************/

typedef TaskConfig {
  byte taskCore ;        // Core
  byte taskPrio ;        // Prio (baseline)
  bool taskRes[MAX_RES]; // P+ Res
} ;
TaskConfig taskConfig[MAX_TASKS];   // Task -m-> TaskConfig

typedef ResSetup {
  byte resTaskCount;        // No of tasks in resTasks (> 1)
  bool resTasks[MAX_TASKS]; // P_2 task
  byte resPrio[MAX_CORES] ; // Core -m-> Prio
} ;
ResSetup resSetup[MAX_RES];  // Res -m-> ResSetup


/*******************************************************************************
 *  Scenario Sizing:
 *    1. choose number of cores - core_count > 0
 *    2. choose number of tasks - 2 <= task_count >= core_count
 *    3. choose number of resources - res_count > 0
 ******************************************************************************/
byte core_count;
byte task_count;
byte res_count;

#define VALID_COUNTS ( \
  core_count > 0 && core_count <= MAX_CORES \
  && task_count >= core_count && task_count <= MAX_TASKS \
  && res_count > 0 && res_count <= MAX_RES \
)

inline fixCounts() {
  printf("\nFixing Counts\n")
  core_count  = 3;
  task_count  = 3;
  res_count   = 2;
}

inline chooseCounts() {
  printf("\nNondeterministically Choosing Counts\n");
  // choose core_count
  if
  :: core_count = 1;
  :: core_count = 2;
  :: core_count = 3;
  :: core_count = 4;
  fi
 // Choose task count >= core count
  if
  // always have at least 2 tasks (to fight over a resource!)
  :: core_count <= 2 -> task_count = 2;
  :: core_count <= 3 -> task_count = 3;
  :: core_count <= 4 -> task_count = 4;
  ::                    task_count = 5;
  ::                    task_count = 6;
  fi
  // Choose number of resources
  if
  :: res_count = 1;
  :: res_count = 2;
  :: res_count = 3;
  :: res_count = 4;
  fi
}

inline printCounts() {
  printf("  Core count:     %d\n",core_count);
  printf("  Task count:     %d\n",task_count);
  printf("  Resource count: %d\n",res_count);
}

inline logCounts() {
  printf("@@@ %d DEF core_count %d\n",_pid,core_count);
  printf("@@@ %d DEF task_count %d\n",_pid,task_count);
  printf("@@@ %d DEF res_count %d\n",_pid,res_count);
}
