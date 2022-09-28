# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.rtems module. """

# Copyright (C) 2022 embedded brains GmbH (http://www.embedded-brains.de)
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

import pytest

from rtemsspec.items import EmptyItemCache, Item
from rtemsspec.rtems import augment_with_test_links, is_pre_qualified


def test_is_pre_qualified():
    item_cache = EmptyItemCache()
    uid = "/constraint/constant-not-pre-qualified"
    constraint = item_cache.add_volatile_item(uid, {"links": []})
    assert is_pre_qualified(constraint)
    item = item_cache.add_volatile_item(
        "/i", {"links": [{
            "role": "constraint",
            "uid": uid
        }]})
    assert not is_pre_qualified(item)


def test_augment_with_test_links():
    item_cache = EmptyItemCache()
    item = item_cache.add_volatile_item("/i", {"links": []})
    link = {"role": "validation", "uid": "/i"}
    test_case = item_cache.add_volatile_item(
        "/t", {
            "links": [],
            "test-actions": [{
                "checks": [{
                    "links": [link]
                }],
                "links": [link]
            }]
        })
    test_case.data["_type"] = "test-case"
    item_cache.items_by_type["test-case"] = [test_case]
    augment_with_test_links(item_cache)
    assert item.child("validation") == test_case
    assert test_case.parent("validation") == item
