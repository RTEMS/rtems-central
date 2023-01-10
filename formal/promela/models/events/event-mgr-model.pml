/* SPDX-License-Identifier: BSD-2-Clause */

/*
 * event-mgr-model.pml
 *
 * Copyright (C) 2019-2021 Trinity College Dublin (www.tcd.ie)
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
 *   Refinement:   model-events-mgr-rfn.yml
 *   Test Preamble: model-events-mgr-pre.h
 *   Test Postamble: model-events-mgr-post.h
 *   Test Runner: model-events-mgr-run.h
 */

/*
 * We need to output annotations for any #define we use.
 * It is simplest to keep them all together,
 * and use an inline to output them.
 */

// Event Sets - we only support 4 events, rather than 32
#define NO_OF_EVENTS 4
#define EVTS_NONE 0
#define EVTS_PENDING 0
#define EVT_0 1
#define EVT_1 2
#define EVT_2 4
#define EVT_3 8
#define EVTS_ALL 15
#define NO_TIMEOUT 0

// We envisage two RTEMS tasks involved, at most.
#define TASK_MAX 3 // These are the "RTEMS" tasks only, numbered 1 & 2
                   // We reserve 0 to model NULL pointers

// We use two semaphores to synchronise the tasks
#define SEMA_MAX 2

// IDs here index an array, so we use the largest bad index as a bad id
#define BAD_ID TASK_MAX

// Return Values - ultimately, we should #include these
// Defined in cpukit/include/rtems/rtems/status.h
#define RC_OK      0  // RTEMS_SUCCESSFUL
#define RC_InvId   4  // RTEMS_INVALID_ID
#define RC_InvAddr 9  // RTEMS_INVALID_ADDRESS
#define RC_Unsat   13 // RTEMS_UNSATISFIED
#define RC_Timeout 6  // RTEMS_TIMEOUT


inline outputDefines () {
   printf("@@@ %d DEF NO_OF_EVENTS %d\n",_pid,NO_OF_EVENTS);
   printf("@@@ %d DEF EVTS_NONE %d\n",_pid,EVTS_NONE);
   printf("@@@ %d DEF EVTS_PENDING %d\n",_pid,EVTS_PENDING);
   printf("@@@ %d DEF EVT_0 %d\n",_pid,EVT_0);
   printf("@@@ %d DEF EVT_1 %d\n",_pid,EVT_1);
   printf("@@@ %d DEF EVT_2 %d\n",_pid,EVT_2);
   printf("@@@ %d DEF EVT_3 %d\n",_pid,EVT_3);
   printf("@@@ %d DEF EVTS_ALL %d\n",_pid,EVTS_ALL);
   printf("@@@ %d DEF NO_TIMEOUT %d\n",_pid,NO_TIMEOUT);
   printf("@@@ %d DEF TASK_MAX %d\n",_pid,TASK_MAX);
   printf("@@@ %d DEF BAD_ID %d\n",_pid,BAD_ID);
   printf("@@@ %d DEF SEMA_MAX %d\n",_pid,SEMA_MAX);
   printf("@@@ %d DEF RC_OK RTEMS_SUCCESSFUL\n",_pid);
   printf("@@@ %d DEF RC_InvId RTEMS_INVALID_ID\n",_pid);
   printf("@@@ %d DEF RC_InvAddr RTEMS_INVALID_ADDRESS\n",_pid);
   printf("@@@ %d DEF RC_Unsat RTEMS_UNSATISFIED\n",_pid);
   printf("@@@ %d DEF RC_Timeout RTEMS_TIMEOUT\n",_pid);
}



// Special values: task states, options, return codes
mtype = {
  Zombie, Ready, EventWait, TimeWait, OtherWait, // Task states
  Wait, NoWait, All, Any, // Option Set values
};


// Tasks
typedef Task {
  byte nodeid; // So we can spot remote calls
  byte pmlid; // Promela process id
  mtype state ; // {Ready,EventWait,TickWait,OtherWait}
  bool preemptable ;
  byte prio ; // lower number is higher priority
  int ticks; //
  bool tout; // true if woken by a timeout
  unsigned wanted  : NO_OF_EVENTS ; // EvtSet, those expected by receiver
  unsigned pending : NO_OF_EVENTS ; // EvtSet, those already received
  bool all; // Do we want All?
};


Task tasks[TASK_MAX]; // tasks[0] models a NULL dereference

byte sendrc;            // Sender global variable
byte recrc;             // Receiver global variable
byte recout[TASK_MAX] ; // models receive 'out' location.

/*
 * Running Orders (maintained by simple global sync counter):
 *   Receive;;Send  =  Receive;Release(1) || Obtain(1);Send
 * Here ;; is "sequential" composition of *different* threads
 */
bool semaphore[SEMA_MAX]; // Semaphore

inline outputDeclarations () {
  printf("@@@ %d DECL byte sendrc 0\n",_pid);
  printf("@@@ %d DECL byte recrc 0\n",_pid);
  // Rather than refine an entire Task array, we refine array 'slices'
  printf("@@@ %d DCLARRAY EvtSet pending TASK_MAX\n",_pid);
  printf("@@@ %d DCLARRAY byte recout TASK_MAX\n",_pid);
  printf("@@@ %d DCLARRAY Semaphore semaphore SEMA_MAX\n",_pid);
}

/*
 * Synchronisation Mechanisms
 *  Obtain(sem_id)   - call that waits to obtain semaphore `sem_id`
 *  Release(sem_id)  - call that releases semaphore `sem_id`
 *  Released(sem_id) - simulates ecosystem behaviour releases `sem_id`
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

inline Released(sem_id)
{
  semaphore[sem_id] = true ;
}


inline printevents (evts) {
  printf("{%d,%d,%d,%d}",(evts)/8%2,(evts)/4%2,(evts)/2%2,(evts)%2);
}

inline events(evts,e3,e2,e1,e0) {
  evts = (8*e3+4*e2+2*e1+e0);
}

inline setminus(diff,minuend,subtrahend) {
  diff = (minuend) & (15-(subtrahend))
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
 * satisfied(task,out,sat) checks if a recieve has been satisfied.
 * It updates its `sat` argument to reflect the check outcome,
 * and logs relevant details.
 */
inline satisfied(task,out,sat) {
  out = task.pending & task.wanted;
  if
  ::  task.all && out == task.wanted  ->  sat = true
  ::  !task.all && out != EVTS_NONE   ->  sat = true
  ::  else                            ->  sat = false
  fi
  printf("@@@ %d LOG satisfied(<pnd:%d wnt:%d all:%d>,out:%d,SAT:%d)\n",
          _pid,task.pending,task.wanted,task.all,out,sat)
}

/*
 * preemptIfRequired(sendid,rcvid) is executed,
 * when task[rcvid] has had its receive request satisfied
 * by a send from task[sendid].
 *
 * It is invoked by the send operation in this model.
 *
 * It checks if task[sendid] should be preempted, and makes it so.
 * This is achieved here by setting the task state to OtherWait.
 */
inline preemptIfRequired(sendid,rcvid) {
  if
  ::  tasks[sendid].preemptable  &&
      // we use the (usual?) convention that higher priority is a lower number
      tasks[rcvid].prio < tasks[sendid].prio &&
      tasks[rcvid].state == Ready
      ->  tasks[sendid].state = OtherWait;
          printf("@@@ %d STATE %d OtherWait\n",_pid,sendid)
  ::  else
  fi
}

/*
 * event_send(self,tid,evts,rc)
 *
 * Simulates a call to rtems_event_send
 *   self : id of process modelling the task/IDR making call
 *   tid  : id of process modelling the target task of the call
 *   evts : event set being sent
 *   rc : updated with the return code when the send completes
 *
 * Corresponding RTEMS call:
 *   rc = rtems_event_send(tid,evts);
 *     `tid`  models `rtems_id id`
 *     `evts` models `rtems_event_set event_in`
 *
 * Modelling the call, as described above, is straightforward.
 * Modelling the behaviour less so, because of the requirement to preempt,
 * under certain circumstances.
 */
inline event_send(self,tid,evts,rc) {
  atomic{
    if
    ::  tid >= BAD_ID -> rc = RC_InvId
    ::  tid < BAD_ID ->
        tasks[tid].pending = tasks[tid].pending | evts
        // at this point, have we woken the target task?
        unsigned got : NO_OF_EVENTS;
        bool sat;
        satisfied(tasks[tid],got,sat);
        if
        ::  sat ->
            tasks[tid].state = Ready;
            printf("@@@ %d STATE %d Ready\n",_pid,tid)
            preemptIfRequired(self,tid) ;
            // tasks[self].state may now be OtherWait !
            /* if
            :: tasks[self].state == OtherWait -> Released(sendSema)
            :: else
            fi */
            waitUntilReady(self);
        ::  else -> skip
        fi
        rc = RC_OK;
    fi
  }
}

/*
 * event_receive(self,evts,wait,wantall,interval,out,rc)
 *
 * Simulates a call to rtems_event_receive
 *   self : id of process modelling the task making call
 *   evts : input event set
 *   wait : true if receive should wait
 *   what : all, or some?
 *   interval : wait interval (0 waits forever)
 *   out : pointer to location
 *         updated with the satisfying events when the receive completes
 *   rc : updated with the return code when the receive completes
 *
 * Corresponding RTEMS call:
 *   opts = mergeopts(wait,wantall);
 *   rc = rtems_event_receive(evts,opts,interval,out);
 *     `evts` models `rtems_event_set event_in`
 *     `when` models the waiting aspect of the option set
 *     `what` models the how much aspect of the option set
 *     `opt` models `rtems_option option_set`, a fusion of `wait` and `wantall`
 *       this fusion `(bool,bool)->rtems_option`
 *       is done by C code `mergeopts`, defined in the preamble.
 *     `interval` models `rtems_interval ticks`
 *     `out` models `rtems_event_set *event_out`
 *
 *
 */
inline event_receive(self,evts,wait,wantall,interval,out,rc){
  atomic{
    printf("@@@ %d LOG pending[%d] = ",_pid,self);
    printevents(tasks[self].pending); nl();
    tasks[self].wanted = evts;
    tasks[self].all = wantall
    if
    ::  out == 0 ->
        printf("@@@ %d LOG Receive NULL out.\n",_pid);
        rc = RC_InvAddr ;
    ::  evts == EVTS_PENDING ->
        printf("@@@ %d LOG Receive Pending.\n",_pid);
        recout[out] = tasks[self].pending;
        rc = RC_OK
    ::  else ->
        bool sat;
        retry:  satisfied(tasks[self],recout[out],sat);
        if
        ::  sat ->
            printf("@@@ %d LOG Receive Satisfied!\n",_pid);
            setminus(tasks[self].pending,tasks[self].pending,recout[out]);
            printf("@@@ %d LOG pending'[%d] = ",_pid,self);
            printevents(tasks[self].pending); nl();
            rc = RC_OK;
        ::  !sat && !wait ->
            printf("@@@ %d LOG Receive Not Satisfied (no wait)\n",_pid);
            rc = RC_Unsat;
        ::  !sat && wait && interval > 0 ->
            printf("@@@ %d LOG Receive Not Satisfied (timeout %d)\n",_pid,interval);
            tasks[self].ticks = interval;
            tasks[self].tout = false;
            tasks[self].state = TimeWait;
            printf("@@@ %d STATE %d TimeWait %d\n",_pid,self,interval)
            waitUntilReady(self);
            if
            ::  tasks[self].tout  ->  rc = RC_Timeout
            ::  else              ->  goto retry
            fi
        ::  else -> // !sat && wait && interval <= 0
            printf("@@@ %d LOG Receive Not Satisfied (wait).\n",_pid);
            tasks[self].state = EventWait;
            printf("@@@ %d STATE %d EventWait\n",_pid,self)
            if
            :: sendTwice && !sentFirst -> Released(sendSema);
            :: else
            fi
            waitUntilReady(self);
            goto retry
        fi
    fi
    printf("@@@ %d LOG pending'[%d] = ",_pid,self);
    printevents(tasks[self].pending); nl();
  }
}


/*
 * Model Processes
 * We shall use four processes in this model.
 *  Two will represent the RTEMS send and receive tasks
 *  One will model a timer
 *  One will model scheduling and other task management behaviour.
 */

// These are not output to test generation
#define SEND_ID 1
#define RCV_ID 2
#define THIS_NODE 0
#define THAT_NODE 1
#define MAX_STEPS 3
#define MAX_WAIT 10

/*
 * Scenario Generation
 */

 /*
 * Send variants:
 *   self = SEND_ID
 *   tid in {BAD_ID,RCV_ID,SEND_ID}
 *   evts in a "suitable" subset of all events.
 *   prio in low, medium, high
 */
typedef SendInputs {
  byte target_id ;
  unsigned send_evts : NO_OF_EVENTS ;
} ;
SendInputs  send_in[MAX_STEPS];

 /*
 * Receive variants:
 *   self in {RCV_ID,SEND_ID}, latter requires send.tid = SEND_ID
 *   evts in "suitable" subset of all events.
 *   wait in {true,false}, a.k.a. {Wait,NoWait}
 *   wantall in {true,false}, a.k.a. {All,Any}
 *   interval in {0..MAX_WAIT}
 *   prio = medium
 */
typedef ReceiveInputs {
  unsigned receive_evts : NO_OF_EVENTS ;
  bool will_wait;
  bool everything;
  byte wait_length;
};
ReceiveInputs receive_in[MAX_STEPS];


/*
 * Sender Scenario
 *   vary: priority, preemptable,target,events
 */
bool doSend; // false for receive-only scenarios
bool sendTwice;
bool sentFirst;
byte sendPrio;
bool sendPreempt;
byte sendTarget;
unsigned sendEvents : NO_OF_EVENTS
unsigned sendEvents1 : NO_OF_EVENTS
unsigned sendEvents2 : NO_OF_EVENTS

/*
 * Receiver Scenario
 *   vary: events,wanted,wait,interval,
 *   fixed: priority (mid)
 */
bool doReceive; // false for send-only scenarios
unsigned rcvEvents : NO_OF_EVENTS;
bool rcvWait;
bool rcvAll;
int rcvInterval;
int rcvOut;
byte rcvPrio;


/*
 * Semaphore Setup
 */
int sendSema;
int rcvSema;
int startSema;

/*
 * Multicore setup
 */
bool multicore;
int sendCore;
int rcvCore;

/*
 * Generating Scenarios
 *
 * We consider the following broad scenario classes:
 *
 *   Send only - check for bad target ids
 *   Receive only - check for timeouts, etc.
 *   Send ; Receive - check correct event transmission
 *   Receive ; Send - check waiting, event transmission and preemption
 *
 * Issues to do with sending to self, or to another node,
 * can be covered in Send; Receive.
 */
mtype = {Send,Receive,SndRcv,RcvSnd,SndRcvSnd,SndPre, MultiCore};
mtype scenario;

inline chooseScenario() {

  // Common Defaults
  doSend = true;
  doReceive = true;
  sendTwice = false;
  sentFirst = false;
  semaphore[0] = false;
  semaphore[1] = false;
  sendPrio = 2;
  sendPreempt = false;
  sendTarget = RCV_ID;
  rcvPrio = 2;
  rcvWait = true;
  rcvAll = true;
  rcvInterval = 0;
  rcvOut = RCV_ID ;
  tasks[SEND_ID].state = Ready;
  tasks[RCV_ID].state = Ready;

  sendEvents1 = 10; // {1,0,1,0}
  sendEvents2 = 0; // {0,0,0,0}
  sendEvents = sendEvents1;
  rcvEvents  = 10; // {1,0,1,0}
  sendSema = 0;
  rcvSema = 1;
  startSema = sendSema;

  multicore = false;
  sendCore = 0;
  rcvCore = 0;

  if
  ::  scenario = Send;
  ::  scenario = Receive;
  ::  scenario = SndRcv;
  ::  scenario = SndPre;
  ::  scenario = SndRcvSnd;
  ::  scenario = MultiCore;
  fi
  atomic{printf("@@@ %d LOG scenario ",_pid); printm(scenario); nl()} ;


  if
  ::  scenario == Send ->
        doReceive = false;
        sendTarget = BAD_ID;
  ::  scenario == Receive ->
        doSend = false
        if
        :: rcvWait = false
        :: rcvWait = true; rcvInterval = 4
        :: rcvOut = 0;
        fi
        printf( "@@@ %d LOG sub-senario wait:%d interval:%d, out:%d\n",
                _pid, rcvWait, rcvInterval, rcvOut )
  ::  scenario == SndRcv ->
        if
        ::  sendEvents = 14; // {1,1,1,0}
        ::  sendEvents = 11; // {1,0,1,1}
        ::  rcvEvents = EVTS_PENDING;
        ::  rcvEvents = EVTS_ALL;
            rcvWait = false;
            rcvAll = false;
        fi
        printf( "@@@ %d LOG sub-senario send/receive events:%d/%d\n",
                _pid, sendEvents, rcvEvents )
  ::  scenario == SndPre ->
        sendPrio = 3;
        sendPreempt = true;
        startSema = rcvSema;
        printf( "@@@ %d LOG sub-senario send-preemptable events:%d\n",
                _pid, sendEvents )
  ::  scenario == SndRcvSnd ->
        sendEvents1 = 2; // {0,0,1,0}
        sendEvents2 = 8; // {1,0,0,0}
        sendEvents = sendEvents1;
        sendTwice = true;
        printf( "@@@ %d LOG sub-senario send-receive-send events:%d\n",
                _pid, sendEvents )
  ::  scenario == MultiCore ->
        multicore = true;
        sendCore = 1;
        printf( "@@@ %d LOG sub-senario multicore send-receive events:%d\n",
                _pid, sendEvents )
  ::  else // go with defaults
  fi

}


proctype Sender (byte nid, taskid) {

  tasks[taskid].nodeid = nid;
  tasks[taskid].pmlid = _pid;
  tasks[taskid].prio = sendPrio;
  tasks[taskid].preemptable = sendPreempt;
  tasks[taskid].state = Ready;
  printf("@@@ %d TASK Worker\n",_pid);
  /* printf("@@@ %d LOG Sender Task %d running on Node %d\n",_pid,taskid,nid); */

  if
  :: multicore ->
       // printf("@@@ %d CALL OtherScheduler %d\n", _pid, sendCore);
       printf("@@@ %d CALL SetProcessor %d\n", _pid, sendCore);
  :: else
  fi

  if
  :: sendPrio > rcvPrio -> printf("@@@ %d CALL LowerPriority\n", _pid);
  :: sendPrio == rcvPrio -> printf("@@@ %d CALL EqualPriority\n", _pid);
  :: sendPrio < rcvPrio -> printf("@@@ %d CALL HigherPriority\n", _pid);
  :: else
  fi

repeat:

  Obtain(sendSema);

  if
  :: doSend ->
    if
    :: !sentFirst -> printf("@@@ %d CALL StartLog\n",_pid);
    :: else
    fi
    printf("@@@ %d CALL event_send %d %d %d sendrc\n",_pid,taskid,sendTarget,sendEvents);

    if
    :: sendPreempt && !sentFirst -> printf("@@@ %d CALL CheckPreemption\n",_pid);
    :: !sendPreempt && !sentFirst -> printf("@@@ %d CALL CheckNoPreemption\n",_pid);
    :: else
    fi

           /* (self,  tid,       evts,      rc) */
    event_send(taskid,sendTarget,sendEvents,sendrc);

    printf("@@@ %d SCALAR sendrc %d\n",_pid,sendrc);
  :: else
  fi

  Release(rcvSema);

  if
  :: sendTwice && !sentFirst ->
     sentFirst = true;
     sendEvents = sendEvents2;
     goto repeat;
  :: else
  fi

  printf("@@@ %d LOG Sender %d finished\n",_pid,taskid);
  tasks[taskid].state = Zombie;
  printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
}


proctype Receiver (byte nid, taskid) {

  tasks[taskid].nodeid = nid;
  tasks[taskid].pmlid = _pid;
  tasks[taskid].prio = rcvPrio;
  tasks[taskid].preemptable = false;
  tasks[taskid].state = Ready;
  printf("@@@ %d TASK Runner\n",_pid,taskid);

  if
  :: multicore ->
       // printf("@@@ %d CALL RunnerScheduler %d\n", _pid, rcvCore);
       printf("@@@ %d CALL SetProcessor %d\n", _pid, rcvCore);
  :: else
  fi

  Release(startSema); // make sure stuff starts */
  /* printf("@@@ %d LOG Receiver Task %d running on Node %d\n",_pid,taskid,nid); */

  Obtain(rcvSema);

  // If the receiver is higher priority then it will be running
  // The sender is either blocked waiting for its semaphore
  // or because it is lower priority.
  // A high priority receiver needs to release the sender now, before it
  // gets blocked on its own event receive.
  if
  :: rcvPrio < sendPrio -> Release(sendSema);  // Release send semaphore for preemption
  :: else
  fi

  if
  :: doReceive ->
    printf("@@@ %d SCALAR pending %d %d\n",_pid,taskid,tasks[taskid].pending);

    if
    :: sendTwice && !sentFirst -> Release(sendSema)
    :: else
    fi

    printf("@@@ %d CALL event_receive %d %d %d %d %d recrc\n",
           _pid,rcvEvents,rcvWait,rcvAll,rcvInterval,rcvOut);

              /* (self,  evts,     when,   what,  ticks,      out,   rc) */
    event_receive(taskid,rcvEvents,rcvWait,rcvAll,rcvInterval,rcvOut,recrc);

    printf("@@@ %d SCALAR recrc %d\n",_pid,recrc);
    if
    :: rcvOut > 0 ->
      printf("@@@ %d SCALAR recout %d %d\n",_pid,rcvOut,recout[rcvOut]);
    :: else
    fi
    printf("@@@ %d SCALAR pending %d %d\n",_pid,taskid,tasks[taskid].pending);
  :: else
  fi

  /*  Again, not sure this is a good idea
  if
  :: rcvPrio >= sendPrio -> Release(sendSema);
  :: rcvPrio < sendPrio -> Obtain(rcvSema);  // Allow send task to complete after preemption
  :: else
  fi
  */
  Release(sendSema);

  printf("@@@ %d LOG Receiver %d finished\n",_pid,taskid);
  tasks[taskid].state = Zombie;
  printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
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
                printf("@@@ %d STATE %d Ready\n",_pid,taskid)
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
          atomic{printf("Clock: tid=%d, state=",tid); printm(tasks[tid].state); nl()};
          if
          ::  tasks[tid].state == TimeWait ->
              tix = tasks[tid].ticks - 1;
              // printf("Clock: ticks=%d, tix=%d\n",tasks[tid].ticks,tix);
              if
              ::  tix == 0
                  tasks[tid].tout = true
                  tasks[tid].state = Ready
                  printf("@@@ %d STATE %d Ready\n",_pid,tid)
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

  printf("Event Manager Model running.\n");
  printf("Setup...\n");

  printf("@@@ %d NAME Event_Manager_TestGen\n",_pid)
  outputDefines();
  outputDeclarations();

  printf("@@@ %d INIT\n",_pid);
  chooseScenario();



  printf("Run...\n");

  run System();
  run Clock();

  run Sender(THIS_NODE,SEND_ID);
  run Receiver(THIS_NODE,RCV_ID);

  _nr_pr == 1;

#ifdef TEST_GEN
  assert(false);
#endif

  printf("Event Manager Model finished !\n")
}
