# SPDX-License-Identifier: BSD-2-Clause
""" This module provides specification items and an item cache. """

# Copyright (C) 2019, 2022 embedded brains GmbH & Co. KG
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

# pylint: disable=too-many-lines

from contextlib import contextmanager
import base64
import hashlib
import os
import pickle
import re
import string
import stat
from typing import Any, Callable, Dict, Iterable, Iterator, List, Match, \
    NamedTuple, Optional, Set, TextIO, Tuple, Union
import json
import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader  # type: ignore


class ItemGetValueContext(NamedTuple):
    """ Context used to get an item value. """
    item: "Item"
    path: str
    value: Any
    key: str
    index: Any  # should be int, but this triggers a mypy error
    args: Optional[str]

    def arg(self, name: str, value: Optional[str] = None) -> str:
        """ Get argument value by name. """
        args = dict(
            kv.split("=")  # type: ignore
            for kv in self.args.split(","))  # type: ignore
        if value:
            return args.get(name, value)
        return args[name]


ItemMap = Dict[str, "Item"]
ItemGetValue = Callable[[ItemGetValueContext], Any]
ItemGetValueMap = Dict[str, Tuple[ItemGetValue, Any]]


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

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    @property
    def item(self) -> "Item":
        """ The item referenced by this link. """
        return self._item

    @property
    def role(self) -> str:
        """ The link role. """
        return self._data["role"]


def _get_value(ctx: ItemGetValueContext) -> Any:
    value = ctx.value[ctx.key]
    if ctx.index >= 0:
        return value[ctx.index]
    return value


def normalize_key_path(key_path: str, prefix: str = "") -> str:
    """ Normalizes the key path with an optional prefix path. """
    if not os.path.isabs(key_path):
        key_path = os.path.join(prefix, key_path)
    return os.path.normpath(key_path)


_TYPES = {
    type(True): "B".encode("utf-8"),
    type(1.0): "F".encode("utf-8"),
    type(1): "I".encode("utf-8"),
    type(None): "N".encode("utf-8"),
    type(""): "S".encode("utf-8"),
}


def _hash_data(data, state) -> None:
    if isinstance(data, list):
        for value in data:
            _hash_data(value, state)
    elif isinstance(data, dict):
        for key, value in sorted(data.items()):
            if not key.startswith("_"):
                state.update(key.encode("utf-8"))
                _hash_data(value, state)
    else:
        state.update(_TYPES[type(data)])
        state.update(str(data).encode("utf-8"))


def data_digest(data: Any) -> str:
    """ Returns a digest of the data. """
    state = hashlib.sha256()
    _hash_data(data, state)
    return base64.urlsafe_b64encode(state.digest()).decode("ascii")


_UID_TO_UPPER = re.compile(r"[/_-]+(.)")


def _match_to_upper(match: Match) -> str:
    return match.group(1).upper()


def _is_link_enabled(link: Link) -> bool:
    return link.item._data["_enabled"]  # pylint: disable=protected-access


def link_is_enabled(_link: Link) -> bool:
    """ Returns true. """
    return True


class Item:
    """ Objects of this class represent a specification item. """

    # pylint: disable=too-many-public-methods
    def __init__(self, item_cache: "ItemCache", uid: str, data: Any):
        data["_type"] = ""
        self._cache = item_cache
        self._ident = _UID_TO_UPPER.sub(_match_to_upper, uid)
        self._uid = uid
        self._data = data
        self._links_to_parents: List[Link] = []
        self._links_to_children: List[Link] = []
        self._resolved_proxy = False

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Item):
            return NotImplemented
        return self._uid == other._uid  # pylint: disable=protected-access

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Item):
            return NotImplemented
        return self._uid < other._uid  # pylint: disable=protected-access

    def __hash__(self) -> int:
        return hash(self._uid)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    @property
    def cache(self) -> "ItemCache":
        """ Returns the cache of the item. """
        return self._cache

    @property
    def digest(self) -> str:
        """ Returns the digest of the item data. """
        return data_digest(self._data)

    def get(self, key: str, default: Any) -> Any:
        """
        Gets the attribute value if the attribute exists, otherwise the
        specified default value is returned.
        """
        return self._data.get(key, default)

    @property
    def uid(self) -> str:
        """ Returns the UID of the item. """
        return self._uid

    @property
    def ident(self) -> str:
        """ Returns the identifier of the item. """
        return self._ident

    @property
    def spec(self) -> str:
        """ Returns the UID of the item with an URL-like format. """
        return f"spec:{self._uid}"

    @property
    def spec_2(self) -> str:
        """
        Returns the UID of the item with an URL-like format with invisible
        white space to allow line breaks.
        """
        uid = self._uid.replace("/", "/\u200b")
        return f"spec:{uid}"

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
        return self._cache[self.to_abs_uid(abs_or_rel_uid)]

    def links_to_parents(
        self,
        role: Optional[Union[str, Iterable[str]]] = None,
        is_link_enabled: Callable[[Link], bool] = _is_link_enabled
    ) -> Iterator[Link]:
        """ Yields the links to the parents of this items. """
        if role is None:
            for link in self._links_to_parents:
                if is_link_enabled(link):
                    yield link
        elif isinstance(role, str):
            for link in self._links_to_parents:
                if link.role == role and is_link_enabled(link):
                    yield link
        else:
            for link in self._links_to_parents:
                if link.role in role and is_link_enabled(link):
                    yield link

    def parents(
        self,
        role: Optional[Union[str, Iterable[str]]] = None,
        is_link_enabled: Callable[[Link], bool] = _is_link_enabled
    ) -> Iterator["Item"]:
        """ Yields the parents of this items. """
        for link in self.links_to_parents(role, is_link_enabled):
            yield link.item

    def parent(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            index: Optional[int] = 0,
            is_link_enabled: Callable[[Link],
                                      bool] = _is_link_enabled) -> "Item":
        """ Returns the parent with the specified role and index. """
        for item_index, item in enumerate(self.parents(role, is_link_enabled)):
            if item_index == index:
                return item
        raise IndexError

    def parent_link(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            index: Optional[int] = 0,
            is_link_enabled: Callable[[Link],
                                      bool] = _is_link_enabled) -> Link:
        """ Returns the parent link with the specified role and index. """
        for link_index, link in enumerate(
                self.links_to_parents(role, is_link_enabled)):
            if link_index == index:
                return link
        raise IndexError

    def links_to_children(
        self,
        role: Optional[Union[str, Iterable[str]]] = None,
        is_link_enabled: Callable[[Link], bool] = _is_link_enabled
    ) -> Iterator[Link]:
        """ Yields the links to the children of this items. """
        if role is None:
            for link in self._links_to_children:
                if is_link_enabled(link):
                    yield link
        elif isinstance(role, str):
            for link in self._links_to_children:
                if link.role == role and is_link_enabled(link):
                    yield link
        else:
            for link in self._links_to_children:
                if link.role in role and is_link_enabled(link):
                    yield link

    def children(
        self,
        role: Optional[Union[str, Iterable[str]]] = None,
        is_link_enabled: Callable[[Link], bool] = _is_link_enabled
    ) -> Iterator["Item"]:
        """ Yields the children of this items. """
        for link in self.links_to_children(role, is_link_enabled):
            yield link.item

    def child(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            index: Optional[int] = 0,
            is_link_enabled: Callable[[Link],
                                      bool] = _is_link_enabled) -> "Item":
        """ Returns the child with the specified role and index. """
        for item_index, item in enumerate(self.children(role,
                                                        is_link_enabled)):
            if item_index == index:
                return item
        raise IndexError

    def child_link(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            index: Optional[int] = 0,
            is_link_enabled: Callable[[Link],
                                      bool] = _is_link_enabled) -> Link:
        """ Returns the child link with the specified role and index. """
        for link_index, link in enumerate(
                self.links_to_children(role, is_link_enabled)):
            if link_index == index:
                return link
        raise IndexError

    def init_parents(self, item_cache: "ItemCache") -> None:
        """ Initializes the list of links to parents of this items. """
        for data in self._data["links"]:
            try:
                link = Link(item_cache[self.to_abs_uid(data["uid"])], data)
                self._links_to_parents.append(link)
            except KeyError as err:
                msg = (f"item '{self.uid}' links "
                       f"to non-existing item '{data['uid']}'")
                raise KeyError(msg) from err

    def init_children(self) -> None:
        """ Initializes the list of links to children of this items. """
        for link in self._links_to_parents:
            link.item.add_link_to_child(Link.create(link, self))

    def add_link_to_parent(self, link: Link):
        """ Adds the link as a parent item link to this item. """
        self._links_to_parents.append(link)

    def add_link_to_child(self, link: Link):
        """ Adds the link as a child item link to this item. """
        self._links_to_children.append(link)

    def is_enabled(self, enabled: List[str]):
        """
        Returns true if the item is enabled by the enabled set, otherwise
        returns false.
        """
        return is_enabled(enabled, self._data["enabled-by"])

    @property
    def enabled(self) -> bool:
        """ Returns true if the item is enabled, otherwise returns false. """
        return self._data["_enabled"]

    @property
    def resolved_proxy(self) -> bool:
        """ Is true if the item is a resolved proxy, otherwise false. """
        return self._resolved_proxy

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

    @property
    def type(self) -> str:
        """ Returns the type of the item. """
        return self._data["_type"]

    def save(self):
        """ Saves the item to the corresponding file. """
        self._cache.save_data(self.file, self._data)

    def load(self):
        """ Loads the item from the corresponding file. """
        self._data = self._cache.load_data(self.file, self._uid)


def create_unique_link(child: Item, parent: Item, data: Any) -> None:
    """
    Creates a unique link from the child to the parent item and vice versa
    using the data for the link.
    """
    for item in parent.children(data["role"]):
        if item.uid == child.uid:
            break
    else:
        parent.add_link_to_child(Link(child, data))
        child.add_link_to_parent(Link(parent, data))


class ItemTemplate(string.Template):
    """ String template for item mapper identifiers. """
    idpattern = "[a-zA-Z0-9._/-]+:[\\[\\]a-zA-Z0-9._/-]+(:[^${}]*)?"


class _ItemMapperContext(dict):
    """ Context to map identifiers to items and attribute values. """

    def __init__(self, mapper: "ItemMapper", item: Optional[Item],
                 prefix: Optional[str], recursive: bool):
        super().__init__()
        self._mapper = mapper
        self._item = item
        self._prefix = prefix
        self._recursive = recursive

    def __getitem__(self, identifier):
        item, key_path, value = self._mapper.map(identifier, self._item,
                                                 self._prefix)
        if self._recursive:
            return self._mapper.substitute(value, item,
                                           os.path.dirname(key_path))
        return value


class _GetValueDictionary(dict):

    def __init__(self, get_value: ItemGetValue):
        super().__init__()
        self._get_value = get_value

    def get(self, _key, _default):
        return (self._get_value, {})


class ItemMapper:
    """ Maps identifiers to items and attribute values. """

    def __init__(self, item: Item, recursive: bool = False):
        self._item = item
        self._recursive = recursive
        self._prefix = [""]
        self._get_value_map: Dict[str, ItemGetValueMap] = {}

    @property
    def item(self) -> Item:
        """ The item of the mapper. """
        return self._item

    @item.setter
    def item(self, item: Item) -> None:
        """ Sets the item of the mapper. """
        self._item = item

    def _add_get_value_map(
            self, type_path_key: str, new_get_value_map: Tuple[ItemGetValue,
                                                               Dict]) -> None:
        type_name, path_key = type_path_key.split(":")
        keys = path_key.strip("/").split("/")
        get_value_map = self._get_value_map.setdefault(type_name, {})
        for key in keys[:-1]:
            _, get_value_map = get_value_map.setdefault(key, (_get_value, {}))
        get_value_map[keys[-1]] = new_get_value_map

    def add_get_value(self, type_path_key: str,
                      get_value: ItemGetValue) -> None:
        """
        Adds a get value for the specified type and key path.
        """
        self._add_get_value_map(type_path_key, (get_value, {}))

    def add_get_value_dictionary(self, type_path_key: str,
                                 get_value: ItemGetValue) -> None:
        """
        Adds a get value dictionary for the specified type and key path.
        """
        self._add_get_value_map(type_path_key,
                                (_get_value, _GetValueDictionary(get_value)))

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

    @contextmanager
    def scope(self, item: Item) -> Iterator[None]:
        """ Opens an item scope context. """
        previous = self._item
        self._item = item
        yield
        self._item = previous

    def get_value_map(self, item: Item) -> ItemGetValueMap:
        """ Returns the get value map for the item. """
        return self._get_value_map.get(item.type, {})

    def _get_by_normalized_key_path(self, item: Item, normalized_key_path: str,
                                    args: Optional[str]) -> Any:
        """
        Gets the attribute value associated with the normalized key path.
        """
        get_value_map = self.get_value_map(item)
        path = "/"
        value = item.data
        for key in normalized_key_path.strip("/").split("/"):
            parts = key.split("[")
            try:
                index = int(parts[1].split("]")[0])
            except IndexError:
                index = -1
            ctx = ItemGetValueContext(item, path, value, parts[0], index, args)
            get_value, get_value_map = get_value_map.get(
                parts[0], (_get_value, {}))
            value = get_value(ctx)
            path = os.path.join(path, key)
        return value

    def map(self,
            identifier: str,
            item: Optional[Item] = None,
            prefix: Optional[str] = None) -> Tuple[Item, str, Any]:
        """
        Maps the identifier with item and prefix to the associated item, key
        path, and attribute value.
        """
        colon = identifier.find(":")
        uid = identifier[:colon]
        more = identifier[colon + 1:]
        colon = more.find(":")
        if colon < 0:
            key_path = more
            args = None
        else:
            key_path = more[:colon]
            args = more[colon + 1:]
        if item is None:
            item = self._item
        if uid == ".":
            if prefix is None:
                prefix = "/".join(self._prefix)
        else:
            prefix = ""
            try:
                item = item.map(uid)
            except KeyError as err:
                msg = (f"item '{uid}' relative to {item.spec} "
                       f"specified by '{identifier}' does not exist")
                raise ValueError(msg) from err
        key_path = normalize_key_path(key_path, prefix)
        try:
            value = self._get_by_normalized_key_path(item, key_path, args)
        except Exception as err:
            msg = (f"cannot get value for '{key_path}' of {item.spec} "
                   f"specified by '{identifier}'")
            raise ValueError(msg) from err
        return item, key_path, value

    def __getitem__(self, identifier):
        item, key_path, value = self.map(identifier)
        if self._recursive:
            return self.substitute(value, item, os.path.dirname(key_path))
        return value

    def substitute(self,
                   text: Optional[str],
                   item: Optional[Item] = None,
                   prefix: Optional[str] = None) -> str:
        """
        Performs a variable substitution using the item mapper with the item
        and prefix.
        """
        if not text:
            return ""
        try:
            context = _ItemMapperContext(self, item, prefix, self._recursive)
            return ItemTemplate(text).substitute(context)
        except Exception as err:
            spec = self._item.spec if item is None else item.spec
            if prefix is None:
                prefix = "/".join(self._prefix)
            msg = (f"substitution for {spec} using prefix '{prefix}' "
                   f"failed for text: {text}")
            raise ValueError(msg) from err


class _SpecType(NamedTuple):
    key: str
    refinements: Dict[str, Any]


def _gather_spec_refinements(item: Item) -> Optional[_SpecType]:
    new_type: Optional[_SpecType] = None
    for link in item._links_to_children:  # pylint: disable=protected-access
        if link.role == "spec-refinement":
            key = link["spec-key"]
            if new_type is None:
                new_type = _SpecType(key, {})
            assert new_type.key == key
            new_type.refinements[
                link["spec-value"]] = _gather_spec_refinements(link.item)
    return new_type


def _load_yaml_data(path: str, uid: str) -> Any:
    with open(path, "r", encoding="utf-8") as src:
        try:
            data = yaml.load(src.read(), Loader=SafeLoader)
        except yaml.YAMLError as err:
            msg = ("YAML error while loading specification item file "
                   f"'{path}': {str(err)}")
            raise IOError(msg) from err
        data["_file"] = os.path.abspath(path)
        data["_uid"] = uid
    return data


def _load_json_data(path: str, uid: str) -> Any:
    with open(path, "r", encoding="utf-8") as src:
        try:
            data = json.load(src)
        except json.JSONDecodeError as err:
            msg = ("JSON error while loading specification item file "
                   f"'{path}': {str(err)}")
            raise IOError(msg) from err
        data["_file"] = os.path.abspath(path)
        data["_uid"] = uid
    return data


def _is_item_enabled(enabled: List[str], item: Item) -> bool:
    return is_enabled(enabled, item["enabled-by"])


def item_is_enabled(_enabled: List[str], _item: Item) -> bool:
    """ Returns true. """
    return True


def _resolve_proxy(proxy: Item, is_link_enabled: Callable[[Link],
                                                          bool]) -> None:

    # pylint: disable=protected-access
    try:
        member = proxy.child("proxy-member", is_link_enabled=is_link_enabled)
    except IndexError:
        pass
    else:
        member._links_to_parents.extend(proxy._links_to_parents)
        member._links_to_children.extend(proxy._links_to_children)
        proxy._data = member._data
        proxy._ident = member._ident
        proxy._resolved_proxy = True
        proxy._uid = member._uid
        for link in proxy._links_to_parents:
            for link_2 in link.item._links_to_children:
                if link_2.item == proxy:
                    link_2._item = member
        for link in proxy._links_to_children:
            for link_2 in link.item._links_to_parents:
                if link_2.item == proxy:
                    link_2._item = member
        proxy._links_to_children = member._links_to_children
        proxy._links_to_parents = member._links_to_parents


class ItemCache(dict):
    """ This class provides a cache of specification items. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 config: Any,
                 post_process_load: Optional[Callable[[ItemMap], None]] = None,
                 is_item_enabled: Callable[[List[str], Item],
                                           bool] = _is_item_enabled):
        super().__init__()
        self._cache_index: int = 0
        self._cache_directory: str = os.path.abspath(
            config.get("cache-directory", "cache"))
        self._types: Set[str] = set()
        self.items_by_type: Dict[str, List[Item]] = {}
        self._updates = 0
        for path in config["paths"]:
            self.load_items(path)
        if post_process_load:
            post_process_load(self)
        if config.get("initialize-links", True):
            self.initialize_links()
        spec_root = config["spec-type-root-uid"]
        if spec_root:
            self._root_type = _gather_spec_refinements(self[spec_root])
        else:
            self._root_type = None
        self._enabled = config.get("enabled", [])
        self._is_enabled = is_item_enabled
        for item in self.values():
            self.set_type(item)
            item["_enabled"] = is_item_enabled(self._enabled, item)
        if config.get("resolve-proxies", False):
            self.resolve_proxies()

    @property
    def updates(self) -> bool:
        """
        Returns true if the item cache updates occurred due to new, modified,
        or removed files.
        """
        return self._updates > 0

    @property
    def types(self) -> Set[str]:
        """ Returns the types of the items. """
        return self._types

    @property
    def enabled(self) -> List[str]:
        """ Returns the enabled set. """
        return self._enabled

    def set_enabled(self,
                    enabled: List[str],
                    is_item_enabled: Callable[[List[str], Item],
                                              bool] = _is_item_enabled):
        """
        Sets the enabled status of all items according to the enabled set using
        the is item enabled function.
        """
        self._enabled = enabled
        self._is_enabled = is_item_enabled
        for item in self.values():
            item["_enabled"] = is_item_enabled(enabled, item)

    def resolve_proxies(
            self,
            is_link_enabled: Callable[[Link],
                                      bool] = _is_link_enabled) -> None:
        """ Resolves each proxy item to the its first enabled member. """
        for item in self.items_by_type.get("proxy", []):
            _resolve_proxy(item, is_link_enabled)

    def add_volatile_item(self, uid: str, data: Any) -> Item:
        """
        Adds an item with the specified data to the cache and returns it.

        The item is not added to the persistent cache storage.
        """
        item = self.create_item(uid, data)
        item.init_parents(self)
        item.init_children()
        self.set_type(item)
        item["_enabled"] = self._is_enabled(self._enabled, item)
        return item

    def add_volatile_item_from_file(self, uid: str, path: str) -> Item:
        """
        Adds an item stored in the specified file to the cache and returns it.

        The item is not added to the persistent cache storage.
        """
        return self.add_volatile_item(uid, self.load_data(path, uid))

    def create_item(self, uid: str, data: Any) -> Item:
        """
        Creates an item for the UID with the data and adds it to the cache.
        """
        item = Item(self, uid, data)
        self[uid] = item
        return item

    def _load_items_in_dir(self, base: str, path: str, cache_file: str,
                           update_cache: bool) -> Set[str]:
        data_by_uid: Dict[str, Any] = {}
        if update_cache:
            self._updates += 1
            for name in os.listdir(path):
                path2 = os.path.join(path, name)
                if name.endswith(".yml") and not name.startswith("."):
                    uid = "/" + os.path.relpath(path2, base).replace(
                        ".yml", "")
                    data_by_uid[uid] = _load_yaml_data(path2, uid)
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "wb") as out:
                pickle.dump(data_by_uid, out)
        else:
            with open(cache_file, "rb") as pickle_src:
                data_by_uid = pickle.load(pickle_src)
        for uid, data in iter(data_by_uid.items()):
            self.create_item(uid, data)
        return set(data_by_uid.keys())

    def _load_items_recursive(self, index: str, base: str, path: str,
                              cache_dir: str) -> Set[str]:
        uids: Set[str] = set()
        mid = os.path.abspath(path)
        mid = mid.replace(os.path.commonpath([cache_dir, mid]), "").strip("/")
        cache_file = os.path.join(cache_dir, index, mid, "spec.pickle")
        try:
            mtime = os.path.getmtime(cache_file)
            update_cache = False
        except FileNotFoundError:
            update_cache = True
        else:
            update_cache = mtime <= os.path.getmtime(path)
        for name in os.listdir(path):
            path2 = os.path.join(path, name)
            if name.endswith(".yml") and not name.startswith("."):
                if not update_cache:
                    update_cache = mtime <= os.path.getmtime(path2)
            elif stat.S_ISDIR(os.lstat(path2).st_mode):
                uids.update(
                    self._load_items_recursive(index, base, path2, cache_dir))
        uids.update(
            self._load_items_in_dir(base, path, cache_file, update_cache))
        return uids

    def load_items(self, path: str) -> Set[str]:
        """ Recursively loads the items in the directory path. """
        index = self._cache_index
        self._cache_index = index + 1
        return self._load_items_recursive(str(index), path, path,
                                          self._cache_directory)

    def load_data(self, path: str, uid: str) -> Any:
        """ Loads the item data from the file specified by path. """
        return _load_yaml_data(path, uid)

    def _save_data(self, file: TextIO, data: Any) -> None:
        file.write(
            yaml.dump(data, default_flow_style=False, allow_unicode=True))

    def save_data(self, path: str, data: Any) -> None:
        """ Saves the item data to the file specified by path. """
        with open(path, "w", encoding="utf-8") as file:
            data2 = {}
            for key, value in data.items():
                if not key.startswith("_"):
                    data2[key] = value
            self._save_data(file, data2)

    def initialize_links(self) -> None:
        """ Initializes the links to parents and children. """
        for item in self.values():
            item.init_parents(self)
        for item in sorted(self.values()):
            item.init_children()

    def set_type(self, item: Item) -> None:
        """ Sets the type of the item. """
        spec_type = self._root_type
        value = item.data
        path: List[str] = []
        while spec_type is not None:
            type_name = value[spec_type.key]
            path.append(type_name)
            spec_type = spec_type.refinements[type_name]
        the_type = "/".join(path)
        item["_type"] = the_type
        self._types.add(the_type)
        self.items_by_type.setdefault(the_type, []).append(item)

    def set_types(self, root_type_uid: str) -> None:
        """
        Sets the root type of the cache and then sets the type of all items.
        """
        self._root_type = _gather_spec_refinements(self[root_type_uid])
        for item in self.values():
            self.set_type(item)


class EmptyItemCache(ItemCache):
    """ This class provides a empty cache of specification items. """

    def __init__(self):
        super().__init__({
            "cache-directory": ".",
            "paths": [],
            "spec-type-root-uid": None
        })


class JSONItemCache(ItemCache):
    """ This class provides a cache of specification items using JSON. """

    def _load_json_items(self, base: str, path: str) -> Set[str]:
        uids: Set[str] = set()
        for name in os.listdir(path):
            path2 = os.path.join(path, name)
            if name.endswith(".json") and not name.startswith("."):
                uid = "/" + os.path.relpath(path2, base).replace(".json", "")
                self.create_item(uid, _load_json_data(path2, uid))
            elif stat.S_ISDIR(os.lstat(path2).st_mode):
                uids.update(self._load_json_items(base, path2))
        return uids

    def load_items(self, path: str) -> Set[str]:
        return self._load_json_items(path, path)

    def load_data(self, path: str, uid: str) -> Any:
        return _load_json_data(path, uid)

    def _save_data(self, file: TextIO, data: Any) -> None:
        json.dump(data, file, sort_keys=True, indent=2)


class EmptyItem(Item):
    """ Objects of this class represent empty items. """

    def __init__(self):
        super().__init__(EmptyItemCache(), "", {})
