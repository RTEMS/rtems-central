/******************************************************************************
 * FV2-201
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

/*@

ML \<open>
structure V1 =
struct

datatype 'a tree = T of 'a tree list
                 | L of 'a

val tl' = fn [] => [] | _ :: l => l

fun get_forest_ass x =
 (fn L b => [ L (not b) ]
   | T ts =>
      let val (_, _, ts_res) =
            fold
              (fn t => fn (ts_pred, ts_succ, ts_res) =>
                ( t :: ts_pred
                , tl' ts_succ
                , map let val ts_pred' = rev ts_pred
                      in fn t_ass => T (ts_pred' @ t_ass :: ts_succ) end
                      (get_forest_ass t)
                  ::
                  ts_res))
              ts
              ([], tl' ts, [])
      in flat (rev ts_res) end
 ) x
end

structure V2 =
struct

datatype 'a tree = T of string option * 'a tree list
                 | L of 'a

val tl' = fn [] => [] | _ :: l => l

fun get_forest_ass x =
 (fn L b => [ (NONE, L (not b)) ]
   | T (t_msg, ts) =>
      let val (_, _, ts_res) =
            fold
              (fn t => fn (ts_pred, ts_succ, ts_res) =>
                ( t :: ts_pred
                , tl' ts_succ
                , map let val ts_pred' = rev ts_pred
                      in fn (msg, t_ass) => ( (case msg of NONE => t_msg | _ => msg)
                                            , T (t_msg, ts_pred' @ t_ass :: ts_succ))
                      end
                      (get_forest_ass t)
                  ::
                  ts_res))
              ts
              ([], tl' ts, [])
      in flat (rev ts_res) end
 ) x
end
\<close>

ML \<open>
let
  open V1
  val ass = L true
  val leaf = T []
  val node = T [ass, T [leaf, T [ass]]]
in
  get_forest_ass (T [ T [ T [ T [ ass
                                , ass] ]
                        , leaf ]
                    , node
                    , node ])
end
\<close>

ML \<open>
let
  open V2
  val ass = L true
  fun t l = T (NONE, l)
  fun t' s l = T (SOME s, l)
  val leaf = t []
  val node = t' "b1" [ass, t' "b2" [leaf, t' "b3" [ass]]]
in
  get_forest_ass (t' "c1" [ t' "c2" [ t' "c3" [ t' "c4" [ ass
                                                        , ass] ]
                                    , leaf ]
                          , node
                          , node ])
end
\<close>

*/