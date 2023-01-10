/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * chains-api-model.pml
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
 ******************************************************************************/

// Sizings, MEM_SIZE = 2 ** PTR_SIZE
#define PTR_SIZE 3
#define MEM_SIZE 8

// Nodes types
typedef Node {
  unsigned nxt  : PTR_SIZE
; unsigned prv  : PTR_SIZE
; byte     itm
}

inline ncopy (dst,src) {
  dst.nxt = src.nxt; dst.prv=src.prv; dst.itm = src.itm
}

// Memory
Node memory[MEM_SIZE] ;
unsigned nptr : PTR_SIZE ;  // one node pointer

// We ignore pointer values here as their values depend on $RTEMS_DEBUG
inline show_node (){
   atomic{
     printf("@@@ 0 PTR nptr %d\n",nptr);
     if
     :: nptr -> printf("@@@ 0 STRUCT nptr\n");
                // printf("@@@ 0 PTR nxt %d\n", memory[nptr].nxt);
                // printf("@@@ 0 PTR prv %d\n", memory[nptr].prv);
                printf("@@@ 0 SCALAR itm %d\n", memory[nptr].itm);
                printf("@@@ 0 END nptr\n")
     :: else -> skip
     fi
   }
}

typedef Control {
  unsigned head : PTR_SIZE
; unsigned tail : PTR_SIZE
; unsigned size : PTR_SIZE
}

Control chain ; // one chain


inline show_chain () {
   int cnp;
   atomic{
     cnp = chain.head;
     printf("@@@ 0 SEQ chain\n");
     do
       :: (cnp == 0) -> break;
       :: (cnp != 0) ->
            printf("@@@ 0 SCALAR _ %d\n",memory[cnp].itm);
            cnp = memory[cnp].nxt
     od
     printf("@@@ 0 END chain\n");
   }
}

inline append(ch,np) {
  assert(np!=0);
  assert(ch.size < 7);
  if
    :: (ch.head == 0) ->
         ch.head = np;
         ch.tail = np;
         ch.size = 1;
         memory[np].nxt = 0;
         memory[np].prv = 0;
    :: (ch.head != 0) ->
         memory[ch.tail].nxt = np;
         memory[np].prv = ch.tail;
         ch.tail = np;
         ch.size = ch.size + 1;
  fi
}

proctype doAppend(int addr; int val) {
  atomic{
    memory[addr].itm = val;
    append(chain,addr);
    printf("@@@ 0 CALL append %d %d\n",val,addr);
    show_chain();
  } ;
}

/* np = get(ch) */
inline get(ch,np) {
  np = ch.head ;
  if
    :: (np != 0) ->
         ch.head = memory[np].nxt;
         ch.size = ch.size - 1;
         // memory[np].nxt = 0
    :: (np == 0) -> skip
  fi
  if
    :: (ch.head == 0) -> ch.tail = 0
    :: (ch.head != 0) -> skip
  fi
}

proctype doGet() {
  atomic{
    get(chain,nptr);
    printf("@@@ 0 CALL get %d\n",nptr);
    show_chain();
    assert(nptr != 0);
    show_node();
  } ;
}

/* -----------------------------
 doNonNullGet waits for a non-empty chain
 before doing a get.
 In generated sequential C code this can be simply be treated
  the same as a call to doGet()
*/
proctype doNonNullGet() {
  atomic{
    chain.head != 0;
    get(chain,nptr);
    printf("@@@ 0 CALL getNonNull %d\n",nptr);
    show_chain();
    assert(nptr != 0);
    show_node();
  } ;
}


init {
  pid nr;
  atomic{
    printf("\n\n Chain Model running.\n");
    printf("@@@ 0 NAME Chain_AutoGen\n")
    printf("@@@ 0 DEF MAX_SIZE 8\n");
    printf("@@@ 0 DCLARRAY Node memory MAX_SIZE\n");
    printf("@@@ 0 DECL unsigned nptr NULL\n")
    printf("@@@ 0 DECL Control chain\n");

    printf("\nInitialising...\n")
    printf("@@@ 0 INIT\n");
    chain.head = 0; chain.tail = 0; chain.size = 0;
    show_chain();
    show_node();
  } ;

  nr = _nr_pr;

  run doAppend(6,21);
  run doAppend(3,22);
  run doAppend(4,23);
  run doNonNullGet();
  run doNonNullGet();
  run doNonNullGet();

  nr == _nr_pr;

#ifdef TEST_GEN
  assert (chain.size != 0);
#else
  assert (chain.size == 0);
#endif

  printf("\nChain Model finished !\n\n")
}
