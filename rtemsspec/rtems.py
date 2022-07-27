# SPDX-License-Identifier: BSD-2-Clause
""" This module provides details of the RTEMS specification. """

# Copyright (C) 2021, 2022 embedded brains GmbH (http://www.embedded-brains.de)
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

from rtemsspec.items import Item, ItemCache, Link

_NOT_PRE_QUALIFIED = set([
    "/acfg/constraint/option-not-pre-qualified",
    "/constraint/constant-not-pre-qualified",
    "/constraint/directive-not-pre-qualified",
])


def is_pre_qualified(item: Item) -> bool:
    """ Returns true, if the item is pre-qualified, otherwise false. """
    return not bool(
        set(parent.uid for parent in item.parents("constraint")).intersection(
            _NOT_PRE_QUALIFIED))


def _add_link(item_cache: ItemCache, child: Item, link: Link) -> None:
    parent = item_cache[child.to_abs_uid(link["uid"])]
    parent.add_link_to_child(Link(child, link))


def augment_with_test_links(item_cache: ItemCache) -> None:
    """ Augments links of test case items with links from their actions. """
    for item in item_cache.all.values():
        if item.type == "test-case":
            for actions in item["test-actions"]:
                for checks in actions["checks"]:
                    for link in checks["links"]:
                        _add_link(item_cache, item, link)
                for link in actions["links"]:
                    _add_link(item_cache, item, link)
