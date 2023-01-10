/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * SPARC-TSO.pml
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

#ifndef _FORMAL_SPARC_TSO
#define _FORMAL_SPARC_TSO


// We assume a byte-memory
#define MEM_SIZE 8
byte memory[MEM_SIZE] ; // Global shared memory

// Instructions: Load, Store, Atomic-Load-Store
mtype = { LD      // addr,reg    reg:=mem[addr]
        , ST      // reg,addr    mem[addr]:=reg
        , SWAP    // addr,reg    reg,mem[addr]:=mem[addr],reg
        , LDSTUB  // addr,reg    reg:=mem[addr]; mem[addr]:=0xFF
        , WORK    //  ?   ?      Some internal work
        , HALT    // end of program (NOP, incl. pc!)
        }

typedef Instruction{
  mtype op
; byte  addr
; byte  reg
} ;

inline load(i, a, r){
  i.op = LD;
  i.addr = a ;
  i.reg = r ;
} ;
inline store(i, r, a)  { i.op = ST;     i.addr = a ; i.reg = r } ;
inline swap(i, a, r)   { i.op = SWAP;   i.addr = a ; i.reg = r } ;
inline ldstub(i, a, r) { i.op = LDSTUB; i.addr = a ; i.reg = r } ;



#define REG_NUM 4
#define CODE_SIZE 8
typedef Processor {
  byte regs[REG_NUM]  // Processor registers
; byte pc             // Program counter
  // FIFO write buffer of length 1
; bool mt             // True if wbuf is empty
; byte wbufaddr  // write address
; byte wbufdata  // write data
; Instruction  program[CODE_SIZE]
} ;

#define CORE_NUM 4
Processor procs[CORE_NUM];

inline execute(p) {
  // NEED TO MOVE ALL 'LOCAL' VARS HERE INTO PROCESSOR struct
  { byte ppc;       // local copy of program counter
    Instruction ir; // Instruction Register
    byte tmp;

    ppc = procs[p].pc;
    ir.op = procs[p].program[ppc].op;
    ir.addr = procs[p].program[ppc].addr;
    ir.reg = procs[p].program[ppc].reg;
    printf("Proc[%d]@[%d] : ",p,ppc);
    printm(ir.op);
    printf(" %d %d\n",ir.addr,ir.reg);
    // Increment PC (if not HALT)
    if
    :: ir.op == HALT -> procs[p].pc = CODE_SIZE;
    :: else -> procs[p].pc = ppc+1;
    fi
    // Perform Instruction
    if
    :: ir.op == LD ->
         if
         :: !procs[p].mt && ir.addr == procs[p].wbufaddr ->
               procs[p].regs[ir.reg] = procs[p].wbufdata
               printf("LD_%d from write buffer\n",p)
         ::  else ->
               procs[p].regs[ir.reg] = memory[ir.addr];
               printf("LD_%d from %d\n",p,ir.addr)
         fi
    :: ir.op == ST ->
         procs[p].mt ; // wait for write buffer to be written out
         procs[p].wbufaddr = ir.addr ;
         procs[p].wbufdata = procs[p].regs[ir.reg] ;
         procs[p].mt = false;
    :: ir.op == SWAP ->
         procs[p].mt ; // wait for write buffer to be written out
         atomic{
           tmp = memory[ir.addr];
           printf("LD_%d from %d\n",p,ir.addr);
           memory[ir.addr] = procs[p].regs[ir.reg];
           printf("ST_%d to %d\n",p,ir.addr);
         }
         procs[p].regs[ir.reg] = tmp;
    :: ir.op == LDSTUB ->
         procs[p].mt ;
         atomic{
           procs[p].regs[ir.reg] = memory[ir.addr];
           printf("LD_%d from %d\n",p,ir.addr);
           memory[ir.addr] = 255;
           printf("ST_%d to %d\n",p,ir.addr);
         }
    :: else // WORK, HALT
    fi
  }
}

inline runproc(p) {
  do
  :: procs[p].pc == CODE_SIZE -> break;
  :: else -> execute(p);
  od
}

inline writer(p) {
  do
  :: !procs[p].mt ->
     memory[procs[p].wbufaddr] = procs[p].wbufdata;
     printf("ST_%d from write buffer to %d\n",p,procs[p].wbufaddr);
     procs[p].mt -> true;
  od
}

proctype Runner(byte p) {
   runproc(p);
}

proctype Writer(byte p) {
   writer(p);
}

init {
  int i;

  printf("Booting up...\n");
  do
  :: i == CORE_NUM -> break ;
  :: else ->
       procs[i].pc = 0;
       procs[i].mt = true;
       store(procs[i].program[0],1,1);
       load(procs[i].program[1],1,1);
       store(procs[i].program[2],1,1);
       swap(procs[i].program[3],1,1);
       store(procs[i].program[4],1,1);
       ldstub(procs[i].program[5],1,1);
       store(procs[i].program[6],1,1);
       i++;
  od

  printf("Running...\n");
  atomic{
    run Writer(0); run Runner(0);
    run Writer(1); run Runner(1);
    run Writer(2); run Runner(2);
    run Writer(3); run Runner(3);
  }


}

#endif
