# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.build module. """

# Copyright (C) 2020 embedded brains GmbH & Co. KG
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

from rtemsspec.build import gather_files
from rtemsspec.items import ItemCache, item_is_enabled
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_build(tmpdir):
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-build", with_spec_types=True)
    item_cache = ItemCache(item_cache_config, is_item_enabled=item_is_enabled)

    build_config = {}
    build_config["arch"] = "foo"
    build_config["bsp"] = "bar"
    build_config["enabled"] = ["A"]
    build_config["extra-files"] = ["a", "b"]
    build_config["build-uids"] = ["/g"]
    files = gather_files(build_config, item_cache)
    assert files == ["a", "b", "stu", "jkl", "mno", "abc", "def", "ghi", "th"]
    files = gather_files(build_config, item_cache, test_header=False)
    assert files == ["a", "b", "stu", "jkl", "mno", "abc", "def", "ghi"]
