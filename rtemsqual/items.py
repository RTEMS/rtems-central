# SPDX-License-Identifier: BSD-2-Clause
""" This module provides specification items and an item cache. """

# Copyright (C) 2019, 2020 embedded brains GmbH (http://www.embedded-brains.de)
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
import pickle
import stat
from typing import Any, List, Dict
import yaml

from rtemsqual.content import SphinxContent

ItemList = List["Item"]
ItemMap = Dict[str, "Item"]


def _is_enabled_op_and(enabled: List[str], enabled_by: Any) -> bool:
    for next_enabled_by in enabled_by:
        if not _is_enabled(enabled, next_enabled_by):
            return False
    return True


def _is_enabled_op_false(_enabled: List[str], _enabled_by: Any) -> bool:
    return False


def _is_enabled_op_not(enabled: List[str], enabled_by: Any) -> bool:
    return not _is_enabled(enabled, enabled_by)


def _is_enabled_op_or(enabled: List[str], enabled_by: Any) -> bool:
    for next_enabled_by in enabled_by:
        if _is_enabled(enabled, next_enabled_by):
            return True
    return False


_IS_ENABLED_OP = {
    "and": _is_enabled_op_and,
    "not": _is_enabled_op_not,
    "or": _is_enabled_op_or
}


def _is_enabled(enabled: List[str], enabled_by: Any) -> bool:
    if enabled_by:
        if isinstance(enabled_by, list):
            return _is_enabled_op_or(enabled, enabled_by)
        if isinstance(enabled_by, dict):
            if len(enabled_by) == 1:
                key = next(iter(enabled_by))
                return _IS_ENABLED_OP.get(key, _is_enabled_op_false)(
                    enabled, enabled_by[key])
            return False
        return enabled_by in enabled
    return True


def _str_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str",
                                   data,
                                   style="|" if "\n" in data else "")


yaml.add_representer(str, _str_representer)


class Item:
    """ Objects of this class represent a specification item. """
    def __init__(self, uid: str, data: Any):
        self._uid = uid
        self._data = data
        self._links = []  # type: ItemList
        self._children = []  # type: ItemList

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getitem__(self, name: str) -> Any:
        return self._data[name]

    @property
    def uid(self) -> str:
        """ Returns the UID of the item. """
        return self._uid

    def to_abs_uid(self, abs_or_rel_uid: str) -> str:
        """
        Returns the absolute UID of an absolute UID or an UID relative to this
        item.
        """
        if os.path.isabs(abs_or_rel_uid):
            return abs_or_rel_uid
        return os.path.normpath(
            os.path.join(os.path.dirname(self.uid), abs_or_rel_uid))

    @property
    def parents(self) -> ItemList:
        """ Returns the list of parents of this items. """
        return self._links

    @property
    def children(self) -> ItemList:
        """ Returns the list of children of this items. """
        return self._children

    def init_parents(self, item_cache: "ItemCache"):
        """ Initializes the list of parents of this items. """
        for link in self._data["links"]:
            self._links.append(item_cache[self.to_abs_uid(link["uid"])])

    def add_child(self, child: "Item"):
        """ Adds a child to this item. """
        self._children.append(child)

    def register_license_and_copyrights(self, content: SphinxContent):
        """ Registers the license and copyrights of this item. """
        content.register_license(self["SPDX-License-Identifier"])
        for statement in self["copyrights"]:
            content.register_copyright(statement)

    def is_enabled(self, enabled: List[str]):
        """ Returns true if the item is enabled by the specified enables. """
        return _is_enabled(enabled, self["enabled-by"])

    @property
    def file(self) -> str:
        """ Returns the file of the item. """
        return self._data["_file"]

    @file.setter
    def file(self, value: str):
        """ Sets the file of the item. """
        self._data["_file"] = value

    def save(self):
        """ Saves the item to the corresponding file. """
        with open(self.file, "w") as dst:
            data = self._data.copy()
            del data["_file"]
            dst.write(
                yaml.dump(data, default_flow_style=False, allow_unicode=True))

    def load(self):
        """ Loads the item from the corresponding file. """
        filename = self.file
        with open(filename, "r") as src:
            self._data = yaml.safe_load(src.read())
            self._data["_file"] = filename


class ItemCache:
    """ This class provides a cache of specification items. """
    def __init__(self, config: Any):
        self._items = {}  # type: ItemMap
        self._top_level = {}  # type: ItemMap
        self._load_items(config)

    def __getitem__(self, uid: str) -> Item:
        return self._items[uid]

    @property
    def all(self) -> ItemMap:
        """ Returns the map of all specification items. """
        return self._items

    @property
    def top_level(self) -> ItemMap:
        """ Returns the map of top-level specification items. """
        return self._top_level

    def _load_items_in_dir(self, base: str, path: str, cache_file: str,
                           update_cache: bool) -> None:
        data_by_uid = {}  # type: Dict[str, Any]
        if update_cache:
            for name in os.listdir(path):
                path2 = os.path.join(path, name)
                if name.endswith(".yml") and not name.startswith("."):
                    uid = "/" + os.path.relpath(path2, base).replace(
                        ".yml", "")
                    with open(path2, "r") as yaml_src:
                        data = yaml.safe_load(yaml_src.read())
                        data["_file"] = os.path.abspath(path2)
                        data_by_uid[uid] = data
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "wb") as out:
                pickle.dump(data_by_uid, out)
        else:
            with open(cache_file, "rb") as pickle_src:
                data_by_uid = pickle.load(pickle_src)
        for uid, data in data_by_uid.items():
            item = Item(uid, data)
            self._items[uid] = item
            if not item["links"]:
                self._top_level[uid] = item

    def _load_items_recursive(self, base: str, path: str,
                              cache_dir: str) -> None:
        mid = os.path.abspath(path)
        mid = mid.replace(os.path.commonprefix([cache_dir, mid]), "")
        cache_file = os.path.join(cache_dir, mid, "spec.pickle")
        try:
            mtime = os.path.getmtime(cache_file)
            update_cache = False
        except FileNotFoundError:
            update_cache = True
        for name in os.listdir(path):
            path2 = os.path.join(path, name)
            if name.endswith(".yml") and not name.startswith("."):
                update_cache = update_cache or mtime <= os.path.getmtime(path2)
            else:
                if stat.S_ISDIR(os.lstat(path2).st_mode):
                    self._load_items_recursive(base, path2, cache_dir)
        self._load_items_in_dir(base, path, cache_file, update_cache)

    def _init_parents(self) -> None:
        for item in self._items.values():
            item.init_parents(self)

    def _init_children(self) -> None:
        for item in self._items.values():
            for parent in item.parents:
                parent.add_child(item)

    def _load_items(self, config: Any) -> None:
        cache_dir = os.path.abspath(config["cache-directory"])
        for path in config["paths"]:
            self._load_items_recursive(path, path, cache_dir)
        self._init_parents()
        self._init_children()
