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

from contextlib import contextmanager
import os
import pickle
import string
import stat
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, \
    Tuple
import yaml

ItemMap = Dict[str, "Item"]
ItemGetValue = Callable[["Item", str, Any, str, Optional[int]], Any]


def _is_enabled_op_and(enabled: List[str], enabled_by: Any) -> bool:
    for next_enabled_by in enabled_by:
        if not is_enabled(enabled, next_enabled_by):
            return False
    return True


def _is_enabled_op_not(enabled: List[str], enabled_by: Any) -> bool:
    return not is_enabled(enabled, enabled_by)


def _is_enabled_op_or(enabled: List[str], enabled_by: Any) -> bool:
    for next_enabled_by in enabled_by:
        if is_enabled(enabled, next_enabled_by):
            return True
    return False


_IS_ENABLED_OP = {
    "and": _is_enabled_op_and,
    "not": _is_enabled_op_not,
    "or": _is_enabled_op_or
}


def is_enabled(enabled: List[str], enabled_by: Any) -> bool:
    """ Verifies if the given parameter is enabled by specific enables. """
    if isinstance(enabled_by, bool):
        return enabled_by
    if isinstance(enabled_by, list):
        return _is_enabled_op_or(enabled, enabled_by)
    if isinstance(enabled_by, dict):
        key, value = next(iter(enabled_by.items()))
        return _IS_ENABLED_OP[key](enabled, value)
    return enabled_by in enabled


def _str_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str",
                                   data,
                                   style="|" if "\n" in data else "")


yaml.add_representer(str, _str_representer)


class Link:
    """ A link to an item. """
    def __init__(self, item: "Item", data: Any):
        self._item = item
        self._data = data

    @classmethod
    def create(cls, link: "Link", item: "Item") -> "Link":
        """ Creates a link using an existing link with a new target item. """
        return cls(item, link._data)  # pylint: disable=protected-access

    def __getitem__(self, name: str) -> Any:
        return self._data[name]

    @property
    def item(self) -> "Item":
        """ The item referenced by this link. """
        return self._item

    @property
    def role(self) -> str:
        """ The link role. """
        return self._data["role"]


def _get_value(_item: "Item", _path: str, value: Any, key: str,
               index: Optional[int]) -> str:
    value = value[key]
    if index is not None:
        value = value[index]
    return value


class Item:
    """ Objects of this class represent a specification item. """
    def __init__(self, item_cache: "ItemCache", uid: str, data: Any):
        self._item_cache = item_cache
        self._uid = uid
        self._data = data
        self._links_to_parents = []  # type: List[Link]
        self._links_to_children = []  # type: List[Link]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any) -> Any:
        """
        Gets the attribute value if the attribute exists, otherwise the
        specified default value is returned.
        """
        return self._data.get(key, default)

    def get_by_key_path(self,
                        key_path: str,
                        prefix: str = "",
                        get_value: ItemGetValue = _get_value) -> Any:
        """ Gets the attribute value corresponding to the key path. """
        if not os.path.isabs(key_path):
            key_path = os.path.join(prefix, key_path)
        key_path = os.path.normpath(key_path)
        path = "/"
        value = self._data
        for key in key_path.strip("/").split("/"):
            parts = key.split("[")
            try:
                index = int(parts[1].split("]")[0])  # type: Optional[int]
            except IndexError:
                index = None
            try:
                value = get_value(self, path, value, parts[0], index)
            except KeyError:
                value = _get_value(self, path, value, parts[0], index)
            path = os.path.join(path, key)
        return value

    @property
    def uid(self) -> str:
        """ Returns the UID of the item. """
        return self._uid

    def to_abs_uid(self, abs_or_rel_uid: str) -> str:
        """
        Returns the absolute UID of an absolute UID or an UID relative to this
        item.
        """
        if abs_or_rel_uid == ".":
            return self._uid
        if os.path.isabs(abs_or_rel_uid):
            return abs_or_rel_uid
        return os.path.normpath(
            os.path.join(os.path.dirname(self.uid), abs_or_rel_uid))

    def map(self, abs_or_rel_uid: str) -> "Item":
        """
        Maps the absolute UID or the UID relative to this item to the
        corresponding item.
        """
        return self._item_cache[self.to_abs_uid(abs_or_rel_uid)]

    def links_to_parents(self) -> Iterator[Link]:
        """ Yields the links to the parents of this items. """
        yield from self._links_to_parents

    def parents(self, role: Optional[str] = None) -> Iterator["Item"]:
        """ Yields the parents of this items. """
        if role is None:
            for link in self._links_to_parents:
                yield link.item
        else:
            for link in self._links_to_parents:
                if link.role == role:
                    yield link.item

    def links_to_children(self) -> Iterator[Link]:
        """ Yields the links to the children of this items. """
        yield from self._links_to_children

    def children(self, role: Optional[str] = None) -> Iterator["Item"]:
        """ Yields the children of this items. """
        if role is None:
            for link in self._links_to_children:
                yield link.item
        else:
            for link in self._links_to_children:
                if link.role == role:
                    yield link.item

    def init_parents(self, item_cache: "ItemCache"):
        """ Initializes the list of links to parents of this items. """
        for data in self._data["links"]:
            link = Link(item_cache[self.to_abs_uid(data["uid"])], data)
            self._links_to_parents.append(link)

    def add_link_to_child(self, link: Link):
        """ Adds a link to a child item of this items. """
        self._links_to_children.append(link)

    def is_enabled(self, enabled: List[str]):
        """ Returns true if the item is enabled by the specified enables. """
        return is_enabled(enabled, self["enabled-by"])

    @property
    def data(self) -> Any:
        """ The item data. """
        return self._data

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


class ItemTemplate(string.Template):
    """ String template for item mapper identifiers. """
    idpattern = "[a-zA-Z0-9._/-]+:[][a-zA-Z0-9._/-]+(|[a-zA-Z0-9_]+)*"


class ItemMapper(Mapping[str, object]):
    """ Maps identifiers to items and attribute values. """
    def __init__(self, item: "Item"):
        self._item = item
        self._prefix = [""]

    def push_prefix(self, prefix: str) -> None:
        """ Pushes a key path prefix. """
        self._prefix.append(prefix)

    def pop_prefix(self) -> None:
        """ Pops a key path prefix. """
        self._prefix.pop()

    @contextmanager
    def prefix(self, prefix: str) -> Iterator[None]:
        """ Opens a key path prefix context. """
        self.push_prefix(prefix)
        yield
        self.pop_prefix()

    def map(self, identifier: str) -> Tuple[Item, Any]:
        """
        Maps an identifier to the corresponding item and attribute value.
        """
        parts = identifier.split("|")
        uid, key_path = parts[0].split(":")
        if uid == ".":
            item = self._item
            prefix = "/".join(self._prefix)
        else:
            item = self._item.map(uid)
            prefix = ""
        value = item.get_by_key_path(key_path, prefix, self.get_value)
        for func in parts[1:]:
            value = getattr(self, func)(value)
        return item, value

    def __getitem__(self, identifier):
        return self.map(identifier)[1]

    def __iter__(self):
        raise StopIteration

    def __len__(self):
        raise AttributeError

    def substitute(self, text: Optional[str]) -> str:
        """ Performs a variable substitution using the item mapper. """
        if not text:
            return ""
        return ItemTemplate(text).substitute(self)

    def substitute_with_prefix(self, text: Optional[str], prefix: str) -> str:
        """
        Performs a variable substitution using the item mapper with a prefix.
        """
        if not text:
            return ""
        with self.prefix(prefix):
            return ItemTemplate(text).substitute(self)

    def get_value(self, _item: Item, _path: str, _value: Any, _key: str,
                  _index: Optional[int]) -> Any:
        """ Gets a value by key and optional index. """
        # pylint: disable=no-self-use
        raise KeyError


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
        for uid, data in iter(data_by_uid.items()):
            item = Item(self, uid, data)
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
        for uid in sorted(self._items):
            item = self._items[uid]
            for link in item.links_to_parents():
                link.item.add_link_to_child(Link.create(link, item))

    def _load_items(self, config: Any) -> None:
        cache_dir = os.path.abspath(config["cache-directory"])
        for path in config["paths"]:
            self._load_items_recursive(path, path, cache_dir)
        self._init_parents()
        self._init_children()


class EmptyItemCache(ItemCache):
    """ This class provides a empty cache of specification items. """
    def __init__(self):
        super().__init__({"cache-directory": ".", "paths": []})
