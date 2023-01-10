/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Locks.pml
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
 * For now:
 *  We run initialization from the Promela `init` process.
 *  Then the modelled tasks each run in their own `proctype`.
 *  However all tasks have an indicator of which CPU they are running on.
 *  So a task can switch CPU.
 *  We do not distinguish task behaviour from that of the schedulers.
 *
 *  The key safety/correctness invariant is that at most one task process
 *  can be enabled at any time on any given CPU.
 *
 ******************************************************************************/

#ifndef _LOCKS
#define _LOCKS

#include "Structs.pml"
#include "Concurrency.pml"


/******************************************************************************
 * Initialize Ticket Lock
 ******************************************************************************/
inline _SMP_ticket_lock_Initialize( ticket_lock ) {
  AtomicInit( ticket_lock.next_ticket, 0 );
  AtomicInit( ticket_lock.now_serving, 0 );
}

#endif
