// apt install spin // 6.4.6+dfsg-2
/*@
  model_checker_verifier \<open>spin\<close> \<open>-a\<close>
  model_checker_compile \<open>gcc\<close> \<open>-DVECTORSZ=4096\<close> \<open>-o\<close> \<open>pan\<close> \<open>pan.c\<close>
  model_checker_exec_one \<open>./pan\<close> \<open>-a\<close> \<open>-n\<close>
  model_checker_exec_all \<open>./pan\<close> \<open>-a\<close> \<open>-n\<close> \<open>-e\<close>
  model_checker_trail \<open>spin\<close> \<open>-p\<close> \<open>-T\<close> \<open>-t\<close> \<open>-k\<close>
*/
