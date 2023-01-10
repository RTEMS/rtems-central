/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * MrsP-MAIN.pml
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
 * Main top-level model file
 ******************************************************************************/

#include "Structs.pml"
#include "State.pml"
#include "Concurrency.pml"
#include "Init.pml"
#include "Scenarios.pml"

inline Run () {

  mtype status;

  printf("\nRunning\n\n");

  printf( "\nSema Create:\n" );
  rtems_semaphore_create( 1, 2, 0, status );
  printf("@@@ %d SCALAR status %e\n", _pid, status);

  printf( "\nSema Obtain:\n" );
  rtems_semaphore_obtain( 1, 0, 1, 0, status );
  printf("@@@ %d SCALAR status %e\n", _pid, status);

  printf( "\nSema Release:\n" );
  rtems_semaphore_release( 1, 0, status );
  printf("@@@ %d SCALAR status %e\n", _pid, status);
}

init{

  printf("\n\n**************** RTEMS-SMP Thread-Q Model ****************\n\n");

  Init();
  Run();
}
