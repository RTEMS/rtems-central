/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Priority.pml
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


#ifndef _PRIORITY
#define _PRIORITY

#include "Heaps.pml"
#include "RBTrees.pml"

#define Priority_Control byte

/******************************************************************************
 * Code to model Priority Nodes:

typedef struct {
  union {
    Chain_Node Chain;
    RBTree_Node RBTree;
  } Node;
  Priority_Control priority;
} Priority_Node;
 ******************************************************************************/
typedef Priority_Node {
  ADDR(RBTree); // short-circuits Node -> RBTree_Node in RBT
  Priority_Control _priority; // priority is Promela keyword
  // other fields to be added if required
}

#define PRIORITY_TOP 15
Priority_Node PN[PRIORITY_TOP] ;
int usedPN ;
byte ixPN; ;

inline allocatePN( newNode ) {
  allocateNode( PRIORITY_TOP, usedPN, ixPN, newNode)
}

inline freePN( oldNode ) {
  freeNode( usedPN, oldNode );
}

inline _Priority_Node_initialize( node, prio ) {
  PN[node].RBTree = 0 ;
  PN[node]._priority = prio ;
}

/******************************************************************************
struct Priority_Aggregation {
  Priority_Node Node; // Overall priority
  RBTree_Control Contributors;
  const struct _Scheduler_Control *scheduler;
  struct {
    Priority_Aggregation *next;
    Priority_Node *node;
    Priority_Action_type type;
  } Action;
};
 ******************************************************************************/
typedef Priority_Aggregation {
  ADDR(iNode); // -> Priority_Node
  RBTree_Control Contributors;
  ADDR(scheduler) ;
}

Priority_Aggregation PA[PRIORITY_TOP] ;
int usedPA ;
byte ixPA; ;

inline allocatePA( newNode ) {
  allocateNode( PRIORITY_TOP, usedPA, ixPA, newNode)
}

inline freePA( oldNode ) {
  freeNode( usedPA, oldNode );
}

inline _Priority_Initialize_one( aggregation, node )
{
  _Priority_Node_initialize(
    aggregation,
    PN[node]._priority,
  );
  _RBTree_Initialize_one(
    PA[aggregation].Contributors,
    RBT[node].RBTree,
  );
}

/* RTEMS_INLINE_ROUTINE void _Priority_Initialize_one(
  Priority_Aggregation *aggregation,
  Priority_Node        *node
)
{
  _Priority_Node_initialize( &aggregation->Node, node->priority );
   -- &aggregation->Node->priority = node->priority
  _RBTree_Initialize_one( &aggregation->Contributors, &node->Node.RBTree );
} */

#endif
