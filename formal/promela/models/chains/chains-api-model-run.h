/* SPDX-License-Identifier: BSD-2-Clause */

void RtemsModelChainsAPI_Run{0}(
)
{{
  Context ctx;

  memset( &ctx, 0, sizeof( ctx ) );

  T_set_verbosity( T_NORMAL );

  TestSegment0( &ctx );
}}

T_TEST_CASE( RtemsModelChainAPI{0} )
{{
  RtemsModelChainsAPI_Run{0}( );
}}
