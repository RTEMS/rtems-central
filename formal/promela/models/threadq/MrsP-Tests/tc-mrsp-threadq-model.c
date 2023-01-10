/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseRtemsEventValSendReceive
 * @ingroup RTEMSTestCaseRtemsEventValSystemSendReceive
 */

/*
 * Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * Do not manually edit this file.  It is part of the RTEMS quality process
 * and was automatically generated.
 *
 * If you find something that needs to be fixed or worded better please
 * post a report to an RTEMS mailing list or raise a bug report:
 *
 * https://docs.rtems.org/branches/master/user/support/bugs.html
 *
 * For information on updating and regenerating please refer to:
 *
 * https://docs.rtems.org/branches/master/eng/req/howto.html
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <rtems/rtems/eventimpl.h>
#include <rtems/rtems/tasksdata.h>
#include <rtems/score/statesimpl.h>
#include <rtems/score/threadimpl.h>

#include "tr-mrsp-threadq-model.h"

#include <rtems/test.h>


T_TEST_CASE( RtemsModelMrsPThreadQ0 )
{
  RtemsModelMrsPThreadQ_Run0(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ1 )
{
  RtemsModelMrsPThreadQ_Run1(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ2 )
{
  RtemsModelMrsPThreadQ_Run2(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ3 )
{
  RtemsModelMrsPThreadQ_Run3(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ4 )
{
  RtemsModelMrsPThreadQ_Run4(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ5 )
{
  RtemsModelMrsPThreadQ_Run5(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ6 )
{
  RtemsModelMrsPThreadQ_Run6(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ7 )
{
  RtemsModelMrsPThreadQ_Run7(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ8 )
{
  RtemsModelMrsPThreadQ_Run8(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ9 )
{
  RtemsModelMrsPThreadQ_Run9(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}





T_TEST_CASE( RtemsModelMrsPThreadQ10 )
{
  RtemsModelMrsPThreadQ_Run10(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ11 )
{
  RtemsModelMrsPThreadQ_Run11(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ12 )
{
  RtemsModelMrsPThreadQ_Run12(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ13 )
{
  RtemsModelMrsPThreadQ_Run13(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ14 )
{
  RtemsModelMrsPThreadQ_Run14(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ15 )
{
  RtemsModelMrsPThreadQ_Run15(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ16 )
{
  RtemsModelMrsPThreadQ_Run16(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ17 )
{
  RtemsModelMrsPThreadQ_Run17(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ18 )
{
  RtemsModelMrsPThreadQ_Run18(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ19 )
{
  RtemsModelMrsPThreadQ_Run19(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}


T_TEST_CASE( RtemsModelMrsPThreadQ20 )
{
  RtemsModelMrsPThreadQ_Run20(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ21 )
{
  RtemsModelMrsPThreadQ_Run21(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ22 )
{
  RtemsModelMrsPThreadQ_Run22(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ23 )
{
  RtemsModelMrsPThreadQ_Run23(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ24 )
{
  RtemsModelMrsPThreadQ_Run24(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ25 )
{
  RtemsModelMrsPThreadQ_Run25(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ26 )
{
  RtemsModelMrsPThreadQ_Run26(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ27 )
{
  RtemsModelMrsPThreadQ_Run27(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ28 )
{
  RtemsModelMrsPThreadQ_Run28(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ29 )
{
  RtemsModelMrsPThreadQ_Run29(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}


T_TEST_CASE( RtemsModelMrsPThreadQ30 )
{
  RtemsModelMrsPThreadQ_Run30(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ31 )
{
  RtemsModelMrsPThreadQ_Run31(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ32 )
{
  RtemsModelMrsPThreadQ_Run32(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ33 )
{
  RtemsModelMrsPThreadQ_Run33(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ34 )
{
  RtemsModelMrsPThreadQ_Run34(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ35 )
{
  RtemsModelMrsPThreadQ_Run35(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ36 )
{
  RtemsModelMrsPThreadQ_Run36(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ37 )
{
  RtemsModelMrsPThreadQ_Run37(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ38 )
{
  RtemsModelMrsPThreadQ_Run38(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ39 )
{
  RtemsModelMrsPThreadQ_Run39(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}


T_TEST_CASE( RtemsModelMrsPThreadQ40 )
{
  RtemsModelMrsPThreadQ_Run40(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ41 )
{
  RtemsModelMrsPThreadQ_Run41(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ42 )
{
  RtemsModelMrsPThreadQ_Run42(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ43 )
{
  RtemsModelMrsPThreadQ_Run43(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ44 )
{
  RtemsModelMrsPThreadQ_Run44(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ45 )
{
  RtemsModelMrsPThreadQ_Run45(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ46 )
{
  RtemsModelMrsPThreadQ_Run46(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}

T_TEST_CASE( RtemsModelMrsPThreadQ47 )
{
  RtemsModelMrsPThreadQ_Run47(
    EventSend,
    EventReceive,
    GetPendingEvents,
    THREAD_WAIT_CLASS_EVENT,
    STATES_WAITING_FOR_EVENT
  );
}



/** @} */
