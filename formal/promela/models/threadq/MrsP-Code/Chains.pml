/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Chains.pml
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


#ifndef _CHAINS
#define _CHAINS

#include "Heaps.pml"

/******************************************************************************
 * Code to model chains
 *
 * RTEMS chains are doubly-linked lists of payload-carrying Nodes, accessed
 * from a Chain-Control that is an overlay of two Nodes
 *
 * typedef struct Chain_Node_struct Chain_Node;
 * struct Chain_Node_struct {
 *   Chain_Node *next;
 *   Chain_Node *previous;
 * };
 *
 * typedef struct My_Data_Node {
 *   Chain_Node Node;
 *   My_Type payload;
 * }
 *
 * typedef union {
 *   struct {
 *     Chain_Node Node;
 *     Chain_Node *fill;
 *   } Head;
 *   struct {
 *    Chain_Node *fill;
 *    Chain_Node Node;
 *   } Tail;
 * } Chain_Control;
 *
 * This is the following overlay
 * struct{
 *   Chain_Node *(Head.Node.next|Tail.fill)
 *   Chain_Node *(Head.Node.previous|Tail.Node.next) -- always Null
 *   Chain_Node *(Head.fill|Tail.Node.previous)
 * }
 *
 * We are going to model these as a singly linked list:
 *
 * The control is just an address of the first chain node, or 0 if empty
 * A node is just two pointers:
 *   a next pointer to the next node,
 *   and a pointer to the payload
 * Sometimes a chain is constructed using _Chain_Initialize from a contiguous
 * array. We simply provide the array
 ******************************************************************************/

#define Chain_Control byte

typedef Chain_Node {
  ADDR(next) ; // index into Chain_Node array (from 1 upwards)
  byte payload ; // can be index into array (from 0 upwards)
  // payload can also be a value that fits in a byte.
}

/******************************************************************************
 * All Chain_Nodes used in this model live here. This includes such nodes
 * that are embedded into C structs in the RTEMS code. In C it is possible to
 * take the address of a struct sub-compoment, while in Promela this is not
 * possible.
 ******************************************************************************/

#define CHAIN_TOP 15
Chain_Node CN[CHAIN_TOP] ;
int usedCN ;
byte ixCN; ;

inline allocateCN( newNode ) {
  allocateNode( CHAIN_TOP, usedCN, ixCN, newNode)
}

inline freeCN( oldNode ) {
  freeNode( usedCN, oldNode );
}


inline _Chain_Initialize_empty( the_chain ) {
  the_chain = 0 ;
}

#define _Chain_Is_Empty( the_chain ) ( the_chain == 0 )

#define _Chain_First( the_chain ) ( the_chain )

inline _Chain_Initialize_one( the_chain, the_node ) {
  assert( CN[the_node].next == 0 );
  the_chain = the_node ;
}

/******************************************************************************
 * Freechain support
 ******************************************************************************/

byte _fc_ix, _fc_addr, _fc_cnt;  // we assume atomic use for now.
// otherwise we might need one of each per task
// also given one - we can calculate the others:
//  _fc_ix   + _fc_cnt  ==  number_nodes + 1
//  _fc_addr + _fc_cnt  ==  number_nodes + starting_address
//  _fc_ix   ==  number_nodes + 1                - _fc_nt
//  _fc_addr ==  number_nodes + starting_address - _fc_cnt

inline _Freechain_Initialize( freechain, starting_address, number_nodes ) {
  atomic{
    _fc_cnt  = number_nodes ;
    _fc_ix   = 1;
    _fc_addr = starting_address ;
    do
    :: _fc_cnt == 0 -> break
    :: else ->
       freechain.nodes[_fc_ix].next = _fc_ix+1;
       freechain.nodes[_fc_ix].payload = _fc_addr;       // printf("fc.nodes[%d].payload = %d\n",_fc_ix,freechain.nodes[_fc_ix].payload);
       _fc_ix++;
       _fc_addr++;
       _fc_cnt--
    od    // printf("_fc_ix = %d, _fc_addr = %d, _fc_cnt = %d\n", _fc_ix, _fc_addr, _fc_cnt);
    freechain.Free = 1 ;
    freechain.nodes[_fc_ix-1].next = 0;
  }
}

inline _Freechain_Pop( freechain, firstnode ) {
  assert( freechain.Free ) ;  // cannot be empty
  firstnode = freechain.Free ;
  freechain.Free = freechain.nodes[firstnode].next;
}
#endif
