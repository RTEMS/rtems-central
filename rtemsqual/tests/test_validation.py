# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsqual.validation module. """

# Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import pytest
import shutil

from rtemsqual.validation import generate, StepWrapper
from rtemsqual.items import ItemCache


def test_step_wrapper(tmpdir):
    steps = StepWrapper()
    assert steps.steps == 0
    assert len(steps) == 1
    with pytest.raises(KeyError):
        steps["nix"]
    assert steps["step"] == 0
    assert steps.steps == 1
    with pytest.raises(StopIteration):
        for step in steps:
            pass


def test_validation(tmpdir):
    item_cache_config = {}
    item_cache_config["cache-directory"] = "cache"

    validation_config = {}
    base_directory = os.path.join(tmpdir, "base")
    validation_config["base-directory"] = base_directory

    item_cache_config["paths"] = [os.path.normpath(tmpdir)]
    generate(validation_config, ItemCache(item_cache_config))

    spec_src = os.path.join(os.path.dirname(__file__), "spec-validation")
    spec_dst = os.path.join(tmpdir, "spec")
    shutil.copytree(spec_src, spec_dst)
    item_cache_config["paths"] = [os.path.normpath(spec_dst)]
    generate(validation_config, ItemCache(item_cache_config))

    with open(os.path.join(base_directory, "ts.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestSuiteBlueGreen
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <blue.h>

#include "green.h"

#include <t.h>

/**
 * @defgroup RTEMSTestSuiteBlueGreen Blue Green
 *
 * @ingroup RTEMSTestSuites
 *
 * @brief Test Suite
 *
 * The Blue Green description.
 *
 * @{
 */

/* Blue green code */

/** @} */
"""
        assert content == src.read()

    with open(os.path.join(base_directory, "tc12.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseTestCase
 * @ingroup RTEMSTestCaseTestCase2
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
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\"
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <a.h>
#include <b.h>

#include "x.h"
#include "y.h"

#include <t.h>

/**
 * @defgroup RTEMSTestCaseTestCase Test Case
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/* Test case support code */

/**
 * @fn void T_case_body_TestCase(void)
 *
 * @brief Test case brief description.
 *
 * Test case description.
 *
 * This test case performs the following actions:
 *
 * - Test case action 0 description.
 *
 *   - Test case action 0 check 0 description.
 *
 *   - Test case action 0 check 1 description.
 *
 * - Test case action 1 description.
 *
 *   - Test case action 1 check 0 description.
 *
 *   - Test case action 1 check 1 description.
 */
T_TEST_CASE(TestCase)
{
  /* Test case prologue code */

  T_plan(2);

  /* Test case action 0 code */
  /* Test case action 0 check 0 code */
  /* Test case action 0 check 1 code; step 0 */

  /* Test case action 1 code */
  /* Test case action 1 check 0 code; step 1 */
  /* Test case action 1 check 1 code */

  /* Test case epilogue code */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTestCase2 Test Case 2
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @fn void T_case_body_TestCase2(void)
 *
 * @brief Test case 2 brief description.
 *
 * Test case 2 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 2 action 0 description.
 *
 *   - Test case 2 action 0 check 0 description.
 *
 *   - Test case 2 action 0 check 1 description.
 *
 * - Test case 2 action 1 description.
 */
T_TEST_CASE_FIXTURE(TestCase2, &test_case_2_fixture)
{
  /* Test case 2 action 0 code */
  /* Test case 2 action 0 check 0 code */
  /* Test case 2 action 0 check 1 code */

  /* Test case 2 action 1 code */
}

/** @} */
"""
        assert content == src.read()

    with open(os.path.join(base_directory, "tc34.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup RTEMSTestCaseTestCase3
 * @ingroup RTEMSTestCaseTestCase4
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
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\"
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <c.h>

#include "z.h"

#include <t.h>

/**
 * @defgroup RTEMSTestCaseTestCase3 Test Case 3
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @fn void T_case_body_TestCase3(void)
 *
 * @brief Test case 3 brief description.
 *
 * Test case 3 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 3 action 0 description.
 *
 *   - Test case 3 action 0 check 0 description.
 */
T_TEST_CASE(TestCase3)
{
  T_plan(1);

  /* Test case 3 action 0 code */
  /* Test case 3 action 0 check 0 code; step 0 */
}

/** @} */

/**
 * @defgroup RTEMSTestCaseTestCase4 Test Case 4
 *
 * @ingroup RTEMSTestSuiteBlueGreen
 *
 * @brief Test Case
 *
 * @{
 */

/**
 * @fn void T_case_body_TestCase4(void)
 *
 * @brief Test case 4 brief description.
 *
 * Test case 4 description.
 */
T_TEST_CASE(TestCase4)
{
  /* Test case 4 epilogue code */
}

/** @} */
"""
        assert content == src.read()
