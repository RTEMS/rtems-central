/* SPDX-License-Identifier: BSD-2-Clause */

// Message queue attributes

#define TASK_MAX 4 //three rtems tasks
#define NULL 0

#define SEMA_MAX 3

#define BAD_ID TASK_MAX

#define MAX_MESSAGE_QUEUES 3
#define MAX_PENDING_MESSAGES 4
#define MAX_MESSAGE_SIZE 1
#define QUEUE_NAME 1

//define in cpukit/include/rtems/rtems/status.h
#define RC_OK      0  // RTEMS_SUCCESSFUL
#define RC_InvName 3  // RTEMS_INVALID_NAME 
#define RC_InvId   4  // RTEMS_INVALID_ID
#define RC_InvAddr 9  // RTEMS_INVALID_ADDRESS
#define RC_Unsat   13 // RTEMS_UNSATISFIED
#define RC_Timeout 6  // RTEMS_TIMEOUT
#define RC_InvSize 8 // RTEMS_INVALID_SIZE
#define RC_InvNum 10 // RTEMS_INVALID_NUMBER
#define RC_TooMany 5 // RTEMS_TOO_MANY

inline outputDefines() {
    printf("@@@ %d DEF TASK_MAX %d\n",_pid,TASK_MAX);
    printf("@@@ %d DEF BAD_ID %d\n",_pid,BAD_ID);
    printf("@@@ %d DEF SEMA_MAX %d\n",_pid,SEMA_MAX);
    printf("@@@ %d DEF MAX_MESSAGE_SIZE %d\n",_pid, MAX_MESSAGE_SIZE);
    printf("@@@ %d DEF MAX_MESSAGE_QUEUES %d\n",_pid, MAX_MESSAGE_QUEUES);
    printf("@@@ %d DEF MAX_PENDING_MESSAGES %d\n",_pid, MAX_PENDING_MESSAGES);
}


mtype = {
  Zombie, Ready, MsgWait, TimeWait, OtherWait, // Task states
  Wait, NoWait // Option Set values
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
  bool doCreate; // whether to create a queue
  bool doSend; //whether task should send
  bool doReceive; //whether task should receive
  bool doWait; //whether task should wait message
  int rcvInterval; //how many ticks to wait
  int rcvMsg; //hold value of message received, modelling receive buffer
  int sndMsg; //hold value of message to send, modelling send buffer
  int targetQueue; //queue id for task to interact with
  int numSends; //number of message send calls to make
  int msgSize; //size of message to send
};

Task tasks[TASK_MAX]; // tasks[0] models a NULL dereference


byte sendrc;            // Sender global variable
byte recrc;             // Receiver global variable
byte qrc              // creation variable
byte recout[TASK_MAX] ; // models receive 'out' location.


bool semaphore[SEMA_MAX]; // Semaphore

mtype = {
  FIFO, PRIORITY
};

typedef Config {
    int name; //An integer is used to represent valid RTEMS_NAME
    int count; //Max messages for a queue
    int maxSize; //Max message size
    mtype attrSet; // RTEMS_ATTRIBUTE_SET, FIFO||priority
};

typedef MessageQueue {
  Config config;
  int messages [MAX_PENDING_MESSAGES] //message circular buffer
  int head; //top of message queue
  int tail; //end of message queue
  bool queueFull; //used to determine full or empty state
  int waitingTasks [TASK_MAX]; //task circular buffer
  int nextTask; //top of task queue
  int lastTask; //end of task queue
  bool taskFull;
};

MessageQueue queueList[MAX_MESSAGE_QUEUES]; //queueList[0] is null

/*
* Helper functions for task
* and message queue operations
*/

inline enqueueTask(id, qid) {
  atomic{
    queueList[qid].waitingTasks[queueList[qid].lastTask] = id;
    if 
    :: queueList[qid].lastTask == TASK_MAX-1 -> queueList[qid].lastTask = 0;
    :: else -> queueList[qid].lastTask++;
    fi
    if
    :: queueList[qid].lastTask == queueList[qid].nextTask -> queueList[qid].taskFull = true;
    :: else -> skip;
    fi
  }
}

inline dequeueTask(id,qid) {
  atomic{
    id = queueList[qid].waitingTasks[queueList[qid].nextTask];
    if 
    :: queueList[qid].nextTask == TASK_MAX-1 -> queueList[qid].nextTask = 0;
    :: else -> queueList[qid].nextTask++;
    fi
    if
    :: queueList[qid].lastTask == queueList[qid].nextTask -> queueList[qid].taskFull = false;
    :: else -> skip;
    fi
  }
}



inline enqueueMessage(id,msg) {
  atomic{
    queueList[id].messages[queueList[id].head] = msg;
   //printf("enqueue message %d", msg);
    if 
    :: queueList[id].head == MAX_PENDING_MESSAGES-1 -> queueList[id].head = 0;
    :: else -> queueList[id].head++;
    fi
    if
    :: queueList[id].head == queueList[id].tail -> queueList[id].queueFull = true;
    :: else -> skip;
    fi
  }
}

inline dequeueMessage(id,msg) {
  atomic{
    msg = queueList[id].messages[queueList[id].tail];
    //printf("dequeue message %d", msg);
    if 
    :: msg == 0 -> skip;
    :: queueList[id].tail == MAX_PENDING_MESSAGES-1 -> queueList[id].tail = 0;
    :: else -> queueList[id].tail++;
    fi
    if
    :: queueList[id].head == queueList[id].tail -> queueList[id].queueFull = false;
    :: else -> skip;
    fi
  }
}


inline sizeOfQueue(id, qsize) {
  atomic{
  if 
  :: queueList[id].head == queueList[id].tail ->
      if
      ::  -> qsize = MAX_PENDING_MESSAGES;
      :: else -> qsize = 0;
      fi
  :: queueList[id].head > queueList[id].tail -> qsize = queueList[id].head - queueList[id].tail;
  :: queueList[id].head < queueList[id].tail -> qsize = MAX_PENDING_MESSAGES + queueList[id].head - queueList[id].tail;
  fi
  return qsize;
  }
}

//Declare needed arrays, variables
inline outputDeclarations () {
  printf("@@@ %d DECL byte sendrc 0\n",_pid);
  printf("@@@ %d DECL byte recrc 0\n",_pid);
  printf("@@@ %d DECL byte qrc 0\n",_pid);
  printf("@@@ %d DECL uint8_t send_counter 0\n",_pid);
  printf("@@@ %d DCLARRAY uint8_t receive_buffer MAX_MESSAGE_SIZE\n",_pid);
  printf("@@@ %d DCLARRAY uint8_t send_buffer MAX_MESSAGE_SIZE\n",_pid);
  printf("@@@ %d DCLARRAY RTEMS_MESSAGE_QUEUE_BUFFER queue_buffer MAX_PENDING_MESSAGES\n",_pid);
  // Rather than refine an entire Task array, we refine array 'slices'
  printf("@@@ %d DCLARRAY byte recout TASK_MAX\n",_pid);
  printf("@@@ %d DCLARRAY Semaphore semaphore SEMA_MAX\n",_pid);
}

inline nl() { printf("\n") }
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


/* message_queue_create()
* creates a message queue object from passed parameters
* queue_name -rtems object name
* msg_count - max messages in queue
* max_size - max message size
* rc - return flag
*/

inline message_queue_create(queue_name, msg_count, max_size, rc) {
    atomic{
      //only one queue created
      int qid = 1;
      if
      ::  queue_name == 0 -> rc = RC_InvName;
      ::  max_size == 0 -> rc = RC_InvSize;
      ::  msg_count == 0 -> rc = RC_InvNum;
      ::  else -> 
            queueList[qid].config.count = msg_count;
            queueList[qid].config.maxSize = max_size;
            queueList[qid].queueFull = false;
            queueList[qid].config.name = queue_name;
            rc = RC_OK;
      fi
      ;
  }
}


/*
* message_queue_send
*    self: id of calling task
*    qid: id of queue
*    msg : message
*    size : size of the message
*    rc: return code
*
* This directive will send a message to the to the specficied
* message queue.
*  If there is a task waiting it will copy the message to that tasks
*  buffer and unblock it
*  If there is no task waiting it will ad the message to the message queue
*/

inline message_queue_send(self,qid,msg,size,rc) {
    atomic{
      int queuedTask = queueList[qid].waitingTasks[queueList[qid].nextTask];
      if
      ::  qid == 0 -> rc = RC_InvId;
      ::  else ->
          if
          ::  msg == NULL -> rc = RC_InvAddr;
          ::  size > queueList[qid].config.maxSize -> rc = RC_InvSize;
          ::  queueList[qid].queueFull -> rc = RC_TooMany;
          ::  else ->
              if 
              ::  queuedTask == 0 -> //no task waiting, add to buffer
                  enqueueMessage(qid,msg);
                  printf("@@@ %d LOG Send queueing message\n",_pid)
                  rc = RC_OK;
              ::  else -> //task waiting
                  dequeueTask(queuedTask,qid);
                  enqueueMessage(qid,msg);
                  printf("@@@ %d LOG Send to task %d\n",_pid, queuedTask)
                  //tasks[queuedTask].rcvMsg = msg;
                  //printf("%d rcv msg %d",_pid,tasks[queuedTask].rcvMsg)
                  tasks[queuedTask].state = Ready
                  printf("@@@ %d STATE %d Ready\n",_pid, queuedTask)
                  rc = RC_OK;
              fi
          fi
      fi 
    }
}

inline message_queue_receive(self,qid,msg,rc) { 
  int rcvmsg;
  atomic{
    if
    :: qid == 0 -> rc = RC_InvId;
    //:: msg == 0 -> rc = RC_InvAddr
    //:: size >= config.maxSize -> RC_InvSize
    :: else -> 
      dequeueMessage(qid,msg);
      if
      :: msg == 0 && !tasks[self].doWait -> 
        rc = RC_Unsat; printf("@@@ %d LOG Receive Not Satisfied (no wait)\n",_pid)
      :: msg == 0 && tasks[self].doWait ->
        printf("@@@ %d LOG Receive Not Satisfied (timeout %d)\n",
                _pid,
                tasks[self].rcvInterval);
        tasks[self].ticks = tasks[self].rcvInterval;
        tasks[self].tout = false;
        printf("@@@ %d STATE %d TimeWait %d\n",
                _pid,
                self,
                tasks[self].rcvInterval);
        tasks[self].state = TimeWait;
        enqueueTask(self,qid);
        waitUntilReady(self);
        
        if
        ::  tasks[self].tout  ->  dequeueTask(self,qid); rc = RC_Timeout; 
        ::  else              -> dequeueMessage(qid,msg);
        fi

      :: else -> rc = RC_OK;
      fi
    fi   
  }
}


/*
 * Model Processes
 * We shall use four processes in this model.
 *  One will represent the RTEMS send task 
 *  Two will represent the RTEMS receive tasks
 *  One will model a timer
 */

// These are not output to test generation
#define SEND_ID 1
#define RCV1_ID 2
#define RCV2_ID 3

/*
 * Sender Scenario
 */
byte sendTarget;
byte msize;
bool sendAgain
int totalSendCount
int currSendCount
/*
 * Receiver Scenario
 */

/*
 * Semaphore Setup
 */
int sendSema;
int rcvSema1;
int startSema;
int rcvSema2;

/*
* Queue setup
*
*/
bool queueCreated;
int queueId;




mtype = {Send,Receive,SndRcv, RcvSnd};
mtype scenario;

inline chooseScenario() {

  sendAgain = false;
  semaphore[0] = false;
  semaphore[1] = false;
  semaphore[2] = false;
  sendSema = 0;
  rcvSema1 = 1;
  rcvSema2 = 2;
  startSema = sendSema;
  tasks[SEND_ID].doCreate = true;

  //Queue parameters
  queueCreated = false;
  queueId = 1;

  msize = MAX_MESSAGE_SIZE;
  //set up defaults
  tasks[SEND_ID].numSends = 1;
  tasks[SEND_ID].sndMsg = 1;
  tasks[SEND_ID].targetQueue = queueId;
  tasks[RCV1_ID].targetQueue = queueId;
  tasks[RCV2_ID].targetQueue = queueId;
  tasks[SEND_ID].sndMsg = 1;
  tasks[SEND_ID].msgSize = MAX_MESSAGE_SIZE;


  //select scenario
  if
  ::  scenario = Send;
  ::  scenario = Receive;
  ::  scenario = SndRcv;
  ::  scenario = RcvSnd;
  fi

  atomic{printf("@@@ %d LOG scenario ",_pid); 
  printm(scenario); 
  nl()};


  if
  :: scenario == Send ->
        tasks[RCV1_ID].doReceive = false;
        tasks[RCV2_ID].doReceive = false;
        tasks[SEND_ID].doSend = true;
        if
        ::  tasks[SEND_ID].targetQueue = 0;
            printf("@@@ %d LOG sub-scenario Send Bad ID\n", _pid)
        ::  tasks[SEND_ID].targetQueue = queueId;
            printf("@@@ %d LOG sub-scenario Send Success\n", _pid)
        ::  tasks[SEND_ID].msgSize = MAX_MESSAGE_SIZE + 1;
            printf("@@@ %d LOG sub-scenario Send Size Error\n", _pid)
        ::  tasks[SEND_ID].sndMsg = 0;
            printf("@@@ %d LOG sub-scenario Buffer Address Error\n", _pid)
        ::  tasks[SEND_ID].numSends = MAX_PENDING_MESSAGES + 1;
            printf("@@@ %d LOG sub-scenario Too Many messages Error\n", _pid)         
        fi

  :: scenario == Receive ->
        tasks[SEND_ID].doSend = false;
        tasks[RCV1_ID].doReceive = true;
        tasks[RCV2_ID].doReceive = false;
        startSema = rcvSema1;
        
        if
        ::  tasks[RCV1_ID].doWait = false;
            if
            ::  tasks[RCV1_ID].targetQueue = 0;
                printf("@@@ %d LOG sub-scenario Rcv Bad ID No Wait\n", _pid)
            ::  tasks[SEND_ID].targetQueue = queueId;
                printf("@@@ %d LOG sub-scenario Rcv Success No Wait\n", _pid, tasks[RCV1_ID].doWait, tasks[RCV1_ID].rcvInterval)
            fi 
        ::  tasks[RCV1_ID].doWait = true; tasks[RCV1_ID].rcvInterval = 5;
            printf("@@@ %d LOG sub-scenario Rcv Success wait:%d interval:%d\n", _pid, tasks[RCV1_ID].doWait, tasks[RCV1_ID].rcvInterval)
        fi
        
        /*
        if
        ::  tasks[RCV2_ID].doWait = false;  
        ::  tasks[RCV2_ID].doWait = true; tasks[RCV2_ID].rcvInterval = 5;
        fi
        printf("@@@ %d LOG sub-scenario Receive2 wait:%d interval:%d\n", _pid, tasks[RCV2_ID].doWait, tasks[RCV2_ID].rcvInterval)
        */

  :: scenario == SndRcv ->

        if
        ::  tasks[SEND_ID].numSends = 2;     
        ::  tasks[SEND_ID].numSends = 1;
        fi
        printf("@@@ %d LOG sub-scenario SndRcv numSends:%d\n", 
                _pid, 
                tasks[SEND_ID].numSends
                )
        /* 
        if
        ::  tasks[RCV1_ID].doWait = false;      
        ::  tasks[RCV1_ID].doWait = true; tasks[RCV1_ID].rcvInterval = 5;
        fi
        printf("@@@ %d LOG sub-scenario Receive1 wait:%d interval:%d\n", _pid, tasks[RCV1_ID].doWait, tasks[RCV1_ID].rcvInterval)
        if
        ::  tasks[RCV2_ID].doWait = false;      
        ::  tasks[RCV2_ID].doWait = true; tasks[RCV2_ID].rcvInterval = 5;
        fi
        printf("@@@ %d LOG sub-scenario Receive2 wait:%d interval:%d\n", _pid, tasks[RCV2_ID].doWait, tasks[RCV2_ID].rcvInterval)
        */
        
        tasks[SEND_ID].doSend = true;
        tasks[RCV1_ID].doReceive = true;
        tasks[RCV2_ID].doReceive = true;

  :: scenario == RcvSnd ->
        startSema = rcvSema1;
        tasks[SEND_ID].doSend = true;
        tasks[RCV1_ID].doReceive = true;
        tasks[RCV2_ID].doReceive = false;
        tasks[RCV1_ID].doWait = true;  tasks[RCV1_ID].rcvInterval = 10;
        //tasks[SEND_ID].numSends = 2
        /*
        if
        :: tasks[RCV1_ID].doWait = false; tasks[RCV2_ID].doWait = false;
        :: tasks[RCV1_ID].doWait = true;  tasks[RCV2_ID].doWait = true; tasks[RCV1_ID].rcvInterval = 10; tasks[RCV2_ID].rcvInterval = 10;
        fi
        printf("@@@ %d LOG sub-scenario RcvSnd wait:%d interval:%d\n", _pid, tasks[RCV1_ID].doWait, tasks[RCV1_ID].rcvInterval)
        */

  fi
}


proctype Sender (byte taskid) {

  tasks[taskid].pmlid = _pid;
  tasks[taskid].state = Ready;
  printf("@@@ %d TASK Runner\n",_pid,taskid);
  
  if 
  ::  (tasks[taskid].doCreate && !queueCreated) ->
      printf("@@@ %d CALL message_queue_construct %d %d %d %d %d qrc\n", _pid, 
              taskid, 
              QUEUE_NAME,
              MAX_PENDING_MESSAGES, 
              MAX_MESSAGE_SIZE, 
              queueId);
      message_queue_create(QUEUE_NAME, 
                            MAX_PENDING_MESSAGES, 
                            MAX_MESSAGE_SIZE, 
                            qrc);
      printf("@@@ %d SCALAR qrc %d\n",_pid,qrc);
      queueCreated = true;
      Release(startSema);
  fi
  
  if
  :: tasks[taskid].doSend -> 
      Obtain(sendSema);
      repeat:
      atomic{
      printf("@@@ %d CALL message_queue_send %d %d %d %d sendrc\n",
              _pid,
              taskid, 
              tasks[taskid].targetQueue, 
              tasks[taskid].sndMsg, 
              tasks[taskid].msgSize);
      message_queue_send(taskid,
                          tasks[taskid].targetQueue,
                          tasks[taskid].sndMsg,
                          tasks[taskid].msgSize,
                          sendrc);
      printf("@@@ %d SCALAR sendrc %d\n",_pid,sendrc);
      tasks[taskid].numSends-- ;
      if
      :: tasks[taskid].numSends != 0 -> tasks[SEND_ID].sndMsg++; goto repeat; 
      :: scenario == RcvSnd -> skip;
      :: else -> Release(rcvSema1);
      fi
      }
  :: else -> skip;
  fi


  //adjust semaphore behaviour for RcvSnd as Receive1 starts
  if 
  :: scenario == RcvSnd -> 
        Obtain(rcvSema1);
        Obtain(rcvSema2);
  :: else ->         
        Obtain(sendSema);
        Obtain(rcvSema2);
        Obtain(rcvSema1);
  fi
  
  printf("@@@ %d LOG Sender %d finished\n",_pid,taskid);
  tasks[taskid].state = Zombie;
  printf("@@@ %d STATE %d Zombie\n",_pid,taskid);
}

proctype Receiver1 (byte taskid) {

  tasks[taskid].pmlid = _pid;
  tasks[taskid].state = Ready;
  printf("@@@ %d TASK Worker1\n",_pid);

  
  Obtain(rcvSema1);

  if
  :: tasks[taskid].doReceive && scenario != RcvSnd->
      atomic{
      printf("@@@ %d CALL message_queue_receive %d %d %d %d recrc\n",
              _pid,taskid,
              tasks[taskid].targetQueue,
              tasks[taskid].doWait,
              tasks[taskid].rcvInterval);
      message_queue_receive(taskid,
                              tasks[taskid].targetQueue,
                              tasks[taskid].rcvMsg,
                              recrc);
      printf("@@@ %d LOG received %d\n", _pid,tasks[taskid].rcvMsg);
      printf("@@@ %d SCALAR recrc %d\n",_pid,recrc);
      Release(rcvSema2);
      }   
  :: tasks[taskid].doReceive && scenario == RcvSnd->
      atomic{
      Release(sendSema);
      printf("@@@ %d CALL message_queue_receive %d %d %d %d recrc\n",
                _pid,
                taskid,
                tasks[taskid].targetQueue,
                tasks[taskid].doWait,
                tasks[taskid].rcvInterval);
      message_queue_receive(taskid,
                              tasks[taskid].targetQueue,
                              tasks[taskid].rcvMsg,
                              recrc);
      printf("@@@ %d LOG received %d\n", _pid,tasks[taskid].rcvMsg);
      printf("@@@ %d SCALAR recrc %d\n",_pid,recrc);
      }
  :: else -> Release(rcvSema2); 
  fi

 

  atomic{
  Release(rcvSema1);
  printf("@@@ %d LOG Receiver1 %d finished\n",_pid,taskid);
  tasks[taskid].state = Zombie;
  printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
  }
}

proctype Receiver2 (byte taskid) {

  tasks[taskid].pmlid = _pid;
  tasks[taskid].state = Ready;
  printf("@@@ %d TASK Worker2\n",_pid);
  
  if
  :: scenario == RcvSnd ->
      goto rcvSkip;
  :: else -> Obtain(rcvSema2);
  fi
  
  
  if
  :: tasks[taskid].doReceive && scenario != RcvSnd-> 
      atomic{
      printf("@@@ %d CALL message_queue_receive %d %d %d %d recrc\n",
              _pid,
              taskid,
              tasks[taskid].targetQueue,
              tasks[taskid].doWait,
              tasks[taskid].rcvInterval);
      message_queue_receive(taskid,tasks[taskid].targetQueue,tasks[taskid].rcvMsg,recrc);
      printf("@@@ %d LOG received %d\n", _pid,tasks[taskid].rcvMsg);
      printf("@@@ %d SCALAR recrc %d\n",_pid,recrc);
      Release(sendSema);
      }
  :: tasks[taskid].doReceive && scenario == RcvSnd->
      atomic{
      printf("@@@ %d CALL message_queue_receive %d %d %d %d recrc\n",
              _pid,
              taskid,tasks[taskid].targetQueue,
              tasks[taskid].doWait,
              tasks[taskid].rcvInterval);
      Release(sendSema);
      message_queue_receive(taskid,tasks[taskid].targetQueue,tasks[taskid].rcvMsg,recrc);
      printf("@@@ %d LOG received %d\n", _pid,tasks[taskid].rcvMsg);
      printf("@@@ %d SCALAR recrc %d\n",_pid,recrc);
      }
  :: else -> Release(sendSema);
  fi

  rcvSkip:
  atomic{
  Release(rcvSema2);
  printf("@@@ %d LOG Receiver2 %d finished\n",_pid,taskid);
  tasks[taskid].state = Zombie;
  printf("@@@ %d STATE %d Zombie\n",_pid,taskid)
  }
}


/*
 * We need a process that periodically wakes up blocked processes.
 * This is modelling background behaviour of the system,
 * such as ISRs and scheduling.
 * We visit all tasks in round-robin order (to prevent starvation)
 * and make them ready if waiting on "other" things.
 * Tasks waiting for events or timeouts are not touched
 * This terminates when all tasks are zombies.
 */

bool stopclock = false;

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

  printf("Message Manager Model running.\n");
  printf("Setup...\n");
  
  printf("@@@ %d NAME Message_Manager_TestGen\n",_pid)
  //#define required in test file
  outputDefines();
  //Structures and data types required in test file
  outputDeclarations();

  printf("@@@ %d INIT\n",_pid);
  chooseScenario();

  printf("Run...\n");
  //start nececssary processes
  run System();
  run Clock();
  
  run Sender(SEND_ID);
  run Receiver1(RCV1_ID);
  run Receiver2(RCV2_ID);
  
  _nr_pr == 1;

#ifdef TEST_GEN
  assert(false);
#endif


printf("Message Manager Model finished !\n")
}