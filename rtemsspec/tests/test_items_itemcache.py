# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsspec.items module. """

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

from rtemsspec.items import EmptyItem, ItemCache, ItemMapper, ItemTemplate
from rtemsspec.tests.util import create_item_cache_config_and_copy_spec


def test_config_error():
    with pytest.raises(KeyError):
        ItemCache({})


def test_load(tmpdir):
    config = create_item_cache_config_and_copy_spec(tmpdir, "spec-item-cache")
    config["enabled"] = ["foobar"]
    item_count = 0

    def post_process_load(items):
        nonlocal item_count
        item_count = len(items)

    item_cache = ItemCache(config, post_process_load)
    assert item_cache.enabled == ["foobar"]
    assert len(item_cache.types) == 1
    assert list(item_cache.types)[0] == ""
    assert item_count == len(item_cache.all)
    assert item_cache.updates
    cache_dir = config["cache-directory"]
    assert os.path.exists(os.path.join(cache_dir, "0", "spec", "spec.pickle"))
    assert os.path.exists(
        os.path.join(cache_dir, "0", "spec", "d", "spec.pickle"))
    assert item_cache["/d/c"]["v"] == "c"
    assert item_cache["/p"]["v"] == "p"
    p = item_cache["/p"]
    assert not p.enabled
    assert p.is_enabled(["blub"])
    assert p["v"] == "p"
    assert p.map("/p") == p
    assert p.map("p") == p
    a = item_cache.all
    assert len(a) == 7
    assert a["/p"]["v"] == "p"
    assert a["/d/c"]["v"] == "c"
    item_cache.set_enabled([])
    assert p.enabled
    item_cache_2 = ItemCache(config)
    assert not item_cache_2.updates
    assert item_cache_2["/d/c"]["v"] == "c"
    with open(os.path.join(tmpdir, "spec", "d", "c.yml"), "w+") as out:
        out.write("""enabled-by: true
links:
- role: null
  uid: ../p
v: x""")
    item_cache_3 = ItemCache(config)
    assert item_cache_3.updates
    assert item_cache_3["/d/c"]["v"] == "x"
    item = item_cache_3.add_volatile_item_from_file(
        "/foo/bar", os.path.join(os.path.dirname(__file__), "spec/root.yml"))
    assert item.uid == "/foo/bar"
    assert item.type == ""
    assert item["type"] == "spec"
    os.remove(os.path.join(tmpdir, "spec", "d", "c.yml"))
    item_cache_4 = ItemCache(config)
    assert item_cache_4.updates
    with pytest.raises(KeyError):
        item_cache_4["/d/c"]


def test_load_link_error(tmpdir):
    config = create_item_cache_config_and_copy_spec(tmpdir,
                                                    "spec-item-cache-2")
    with pytest.raises(
            KeyError,
            match=r"^\"item '/a' links to non-existing item 'nix'\"$"):
        ItemCache(config)


def test_load_yaml_error(tmpdir):
    config = create_item_cache_config_and_copy_spec(tmpdir,
                                                    "spec-item-cache-3")
    match = r"""YAML error while loading specification item file '.*invalid.yml': while parsing a block mapping
expected <block end>, but found ':'
  in "<unicode string>", line 1, column 1:
    :
    \^"""
    with pytest.raises(IOError, match=match):
        ItemCache(config)


def get_x_to_b_value(ctx):
    assert ctx.key == "x-to-b"
    args = ctx.args if ctx.args is not None else ""
    return ctx.value["b"] + args


def get_value_dict(ctx):
    return ctx.key


def test_item_mapper(tmpdir):
    config = create_item_cache_config_and_copy_spec(tmpdir,
                                                    "spec-item-cache",
                                                    with_spec_types=True)
    config["enabled"] = ["foobar"]
    config["resolve-proxies"] = True
    item_cache = ItemCache(config)
    item = item_cache["/p"]
    base_mapper = ItemMapper(item)
    assert base_mapper["d/c:v"] == "c"
    mapper = ItemMapper(item)
    assert mapper.substitute(None) == ""
    assert mapper.substitute(None, prefix="v") == ""
    with mapper.prefix("v"):
        assert mapper[".:."] == "p"
        assert mapper[".:../x/y"] == "z"
        item_2, key_path_2, value_2 = mapper.map(".:.")
        assert item_2 == item
        assert key_path_2 == "/v"
        assert value_2 == "p"
        assert mapper.substitute("$$${.:.}") == "$p"
    assert mapper.substitute("$$${.:.}", prefix="v") == "$p"
    with mapper.prefix("x"):
        with mapper.prefix("y"):
            assert mapper[".:."] == "z"
    assert mapper["."] == "/p"
    match = r"cannot get value for '/v' of spec:/proxy specified by 'proxy:/v"
    with pytest.raises(ValueError, match=match):
        mapper["proxy:/v"]
    assert not item_cache["/proxy"].resolved_proxy
    assert item_cache["/proxy2"].resolved_proxy
    assert not item_cache["/r"].resolved_proxy
    assert mapper["proxy2:/v"] == "s"
    assert item_cache["/r"].child("xyz").uid == "/s"
    assert mapper["d/c"] == "/d/c"
    assert mapper["d/c:v"] == "c"
    assert mapper["d/c:a/b"] == "e"
    mapper.add_get_value("other:/a/x-to-b", get_x_to_b_value)
    assert mapper["d/c:a/x-to-b:args:0:%"] == "eargs:0:%"
    assert mapper["d/c:a/f[1]"] == 2
    assert mapper["d/c:a/../a/f[3]/g[0]"] == 4
    item_3, key_path_3, value_3 = mapper.map("/p:/v")
    assert item_3 == item
    assert key_path_3 == "/v"
    assert value_3 == "p"
    mapper.add_get_value_dictionary("other:/dict", get_value_dict)
    assert mapper["d/c:/dict/some-arbitrary-key"] == "some-arbitrary-key"
    recursive_mapper = ItemMapper(item, recursive=True)
    assert recursive_mapper.substitute("${.:/r1/r2/r3}") == "foobar"
    assert recursive_mapper[".:/r1/r2/r3"] == "foobar"
    match = r"substitution for spec:/p using prefix 'blub' failed for text: \${}"
    with pytest.raises(ValueError, match=match):
        mapper.substitute("${}", item, "blub")
    match = r"item 'boom' relative to spec:/p specified by 'boom:bam' does not exist"
    with pytest.raises(ValueError, match=match):
        mapper.map("boom:bam", item, "blub")
    match = r"cannot get value for 'blub/bam' of spec:/p specified by '.:bam'"
    with pytest.raises(ValueError, match=match):
        mapper.map(".:bam", item, "blub")


def test_empty_item_mapper():
    item = EmptyItem()
    mapper = ItemMapper(item)
    assert mapper.item == item
    item_2 = EmptyItem()
    mapper.item = item_2
    assert mapper.item == item_2
