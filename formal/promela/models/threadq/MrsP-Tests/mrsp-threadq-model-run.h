/* SPDX-License-Identifier: BSD-2-Clause */

void RtemsModelMrsPThreadQ{0}(
)
{{
  Context ctx;

  memset( &ctx, 0, sizeof( ctx ) );

  T_set_verbosity( T_NORMAL );

  TestSegment0( &ctx );
}}

T_TEST_CASE( RtemsModelMrsPThreadQ{0} )
{{
  RtemsModelMrsPThreadQ_Run{0}( );
}}
