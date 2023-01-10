/* SPDX-License-Identifier: BSD-2-Clause */

/******************************************************************************
 * Utilities.pml
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

inline setMin( a, b, min ) {
  if
  :: a < b  ->  min = a ;
  :: else   ->  min = b ;
  fi
}

// We assume 5 is the highest as at least one task has been assigned to one core
inline chooseLowHigh( low, high, choice ) {
  if
  :: low <= 1 && 1 <= high -> choice = 1 ;
  :: low <= 2 && 2 <= high -> choice = 2 ;
  :: low <= 3 && 3 <= high -> choice = 3 ;
  :: low <= 4 && 4 <= high -> choice = 4 ;
  :: low <= 5 && 5 <= high -> choice = 5 ;
  :: else ->
     printf("!!!chooseFail, low=%d, high=%d\n",low,high);
  fi
}

// We have a lower bound N/P where both are integers
// IF N/P is exact, that is fine.
// If not, we need to add 1
inline lowerRatio( n, p, lowerbound) {
  if
  :: n % p -> lowerbound = (n / p) + 1 ;
  :: else  -> lowerbound = (n / p) ;
  fi
}
