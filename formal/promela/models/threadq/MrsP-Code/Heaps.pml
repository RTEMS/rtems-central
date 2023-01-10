/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Heaps.pml
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
 * Here we define ways to allocate and free "heap nodes"
 ******************************************************************************/

#ifndef _HEAPS
#define _HEAPS


/******************************************************************************
 * BitSets
 * to compress state, we encode some sets as bitsets
 * Bitsets contain natural numbers from 0 upwards
 *  So, Bitset value 0x1 denotes the set {0}
 ******************************************************************************/
#define EMPTY  ( bitset   ) (  !bitset  )
#define INTSCT ( bs1, bs2 ) ( bs1 & bs2 )
#define UNION  ( bs1, bs2 ) ( bs1 | bs2 )
#define DIFF   ( bs1, bs2 ) ( bs1 & ~bs2 )

#define NAT2BIT( nat ) ( 1 << nat )

/******************************************************************************
 * A common use-case is when we have a natural number and a bitset and want
 * to do set operations for this special case
 ******************************************************************************/
#define MEMBER( num, bitset) ( INTSCT( NAT2BIT(num), bitset ) )
#define ADDNUM( num, bitset) ( UNION( NAT2BIT(num), bitset ) )
#define REMNUM( num, bitset) ( DIFF( bitset, NAT2BIT(num) ) )

/******************************************************************************
 * All pointers become indices into arrays
 ******************************************************************************/
// we assume a max required index of 15 for now
// the below expands to  `unsigned addr : 4`.
#define ADDR(addr) BITS(4,addr)

/******************************************************************************
 * allocateNode:
 *  MAX - maximum number of nodes available
 *  used - bitset indicating nodes in use
 *  allocIx - variable to use to search bitset
 *  newNode - number of the free node found (in range 1..MAX)
 *  We assume an array 0..MAX (i.e size MAX+1) is available
 ******************************************************************************/
inline allocateNode( MAX, used, allocIx, newNode ) {
  atomic{
    allocIx = 1;
    do
    ::  allocIx > MAX ->
          printf( "Heap out of memory !\n");
          assert(false);
    ::  MEMBER( allocIx, used ) -> allocIx++ ;
    ::  else ->
          used = ADDNUM( allocIx, used );
          newNode = allocIx ;
          break;
    od
  }
}

inline freeNode( used, oldNode ) {
  used = REMNUM( oldNode, used );
}

#endif
