/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Values.pml
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
 * Here we define value code in use in this model
 ******************************************************************************/

#ifndef _VALUES
#define _VALUES

/******************************************************************************
 * rtems_status_code
  RTEMS_SUCCESSFUL = 0,
  RTEMS_TASK_EXITTED = 1,
  RTEMS_MP_NOT_CONFIGURED = 2,
  RTEMS_INVALID_NAME = 3,
  RTEMS_INVALID_ID = 4,
  RTEMS_TOO_MANY = 5,
  RTEMS_TIMEOUT = 6,
  RTEMS_OBJECT_WAS_DELETED = 7,
  RTEMS_INVALID_SIZE = 8,
  RTEMS_INVALID_ADDRESS = 9,
  RTEMS_INVALID_NUMBER = 10,
  RTEMS_NOT_DEFINED = 11,
  RTEMS_RESOURCE_IN_USE = 12,
  RTEMS_UNSATISFIED = 13,
  RTEMS_INCORRECT_STATE = 14,
  RTEMS_ALREADY_SUSPENDED = 15,
  RTEMS_ILLEGAL_ON_SELF = 16,
  RTEMS_ILLEGAL_ON_REMOTE_OBJECT = 17,
  RTEMS_CALLED_FROM_ISR = 18,
  RTEMS_INVALID_PRIORITY = 19,
  RTEMS_INVALID_CLOCK = 20,
  RTEMS_INVALID_NODE = 21,
  RTEMS_NOT_CONFIGURED = 22,
  RTEMS_NOT_OWNER_OF_RESOURCE = 23,
  RTEMS_NOT_IMPLEMENTED = 24,
  RTEMS_INTERNAL_ERROR = 25,
  RTEMS_NO_MEMORY = 26,
  RTEMS_IO_ERROR = 27,
  RTEMS_INTERRUPTED = 28,
  RTEMS_PROXY_BLOCKING = 29
 ******************************************************************************/
mtype = {
  // status codes
  RTEMS_SUCCESSFUL,
  RTEMS_UNSATISFIED,
  RTEMS_INCORRECT_STATE,
  RTEMS_NOT_IMPLEMENTED,
  RTEMS_INVALID_PRIORITY,
  // thread states
  STATES_DORMANT
}

#define STATUS_SUCCESSFUL RTEMS_SUCCESSFUL
#define STATUS_DEADLOCK RTEMS_INCORRECT_STATE
#define STATUS_MUTEX_CEILING_VIOLATED RTEMS_INVALID_PRIORITY

#endif
