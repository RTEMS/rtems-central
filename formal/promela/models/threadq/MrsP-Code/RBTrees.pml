/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * RBTrees.pml
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


#ifndef _RBTREES
#define _RBTREES

#include "Heaps.pml"

/******************************************************************************
 * Code to model red-black trees
 *
 * RTEMS uses red-black trees for priority queues
 *
 *   typedef struct RBTree_Node {
 *     struct {
 *     	struct RBTree_Node *rbe_left;
 *     	struct RBTree_Node *rbe_right;
 *     	struct RBTree_Node *rbe_parent;
 *     	int rbe_color;
 *     } Node;
 *   } RBTree_Node;
 *
 *   struct RBTree_Control {
 *     struct RBTree_Node *rbh_root;
 *   };
 *
 * We are going to model these as a singly linked list:
 *
 * The control is just an address of the first rbtree node, or 0 if empty
 * A node is two pointers and a priority value:
 *   a next pointer to the next node,
 *   and a pointer to the payload
 ******************************************************************************/

#define RBTree_Control byte

typedef RBTree_Node {
  ADDR(next) ; // index into RBTree_Node array (from 1 upwards)
  byte payload ; // can be index into array (from 0 upwards)
  // payload can also be a value that fits in a byte.
  byte prio;
}

/******************************************************************************
 * All RBTree_Nodes used in this model live here. This includes such nodes
 * that are embedded into C structs in the RTEMS code. In C it is possible to
 * take the address of a struct sub-compoment, while in Promela this is not
 * possible.
 ******************************************************************************/

#define RBTREE_TOP 15
RBTree_Node RBT[RBTREE_TOP] ;
int usedRBTN ;
byte ixRBTN; ;

inline allocateRBTN( newNode ) {
  allocateNode( RBTree, usedRBTN, ixRBTN, newNode)
}

inline freeRBTN( oldNode ) {
  freeNode( usedRBTN, oldNode );
}

inline _RBTree_Initialize_empty( the_rbtree ) {
  the_rbtree = 0 ;
}

// _RBTree_Initialize_node( the_node ) { No-Op }

inline _RBTree_Initialize_one( the_rbtree, the_node ) {
  assert( RBT[the_node].next == 0 );
  the_rbtree = the_node ;
}

#endif
