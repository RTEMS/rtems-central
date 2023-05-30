# SPDX-License-Identifier: BSD-2-Clause
""" This module provides functions for specification item verification. """

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

from contextlib import contextmanager
import logging
import re
from typing import Any, Dict, Iterator, List, NamedTuple, Set

from rtemsspec.items import Item, ItemCache

_VerifierMap = Dict[str, "_Verifier"]


class VerifyStatus(NamedTuple):
    """ This tuple provides the verify message counts by category. """
    critical: int
    error: int
    warning: int
    info: int
    debug: int


class _Filter(logging.Filter):

    def __init__(self):
        super().__init__()
        self._counts: Dict[int, int] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        count = self._counts.get(record.levelno, 0)
        self._counts[record.levelno] = count + 1
        return True

    def get_verify_info(self) -> VerifyStatus:
        """ Returns the gathered verify information. """
        return VerifyStatus(self._counts.get(logging.CRITICAL, 0),
                            self._counts.get(logging.ERROR, 0),
                            self._counts.get(logging.WARNING, 0),
                            self._counts.get(logging.INFO, 0),
                            self._counts.get(logging.DEBUG, 0))


def _type_name(value: Any):
    type_name = type(value).__name__
    if type_name == "NoneType":
        return "none"
    return type_name


class _Path(NamedTuple):
    item: Item
    path: str


class _AssertContext(NamedTuple):
    path: _Path
    value: Any
    type_info: Dict[str, Any]
    ops: Dict[str, Any]


def _assert_op_and(ctx: _AssertContext, assert_info: Any) -> bool:
    for element in assert_info:
        if not _assert(ctx, element):
            return False
    return True


def _assert_op_not(ctx: _AssertContext, assert_info: Any) -> bool:
    return not _assert(ctx, assert_info)


def _assert_op_or(ctx: _AssertContext, assert_info: Any) -> bool:
    for element in assert_info:
        if _assert(ctx, element):
            return True
    return False


def _assert_op_eq(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value == assert_info


def _assert_op_ne(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value != assert_info


def _assert_op_le(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value <= assert_info


def _assert_op_lt(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value < assert_info


def _assert_op_ge(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value >= assert_info


def _assert_op_gt(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value > assert_info


def _assert_op_uid(ctx: _AssertContext, _assert_info: Any) -> bool:
    try:
        ctx.path.item.map(ctx.value)
    except KeyError:
        logging.warning("%s cannot resolve UID: %s", _prefix(ctx.path),
                        ctx.value)
        return False
    return True


def _assert_op_re(ctx: _AssertContext, assert_info: Any) -> bool:
    return re.search(assert_info, ctx.value) is not None


def _assert_op_in(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value in assert_info


_WORD_SEPARATOR = re.compile(r"[ \t\n\r\f\v-]+")


def _assert_op_contains(ctx: _AssertContext, assert_info: Any) -> bool:
    value = " " + " ".join(_WORD_SEPARATOR.split(ctx.value.lower())) + " "
    return any(f" {substring} " in value for substring in assert_info)


def _assert(ctx: _AssertContext, assert_info: Any) -> bool:
    if isinstance(assert_info, list):
        return _assert_op_or(ctx, assert_info)
    key = next(iter(assert_info))
    return ctx.ops[key](ctx, assert_info[key])


def _maybe_assert(path: _Path, value: Any, type_info: Any,
                  ops: Dict[str, Any]) -> bool:
    if "assert" in type_info:
        return _assert(_AssertContext(path, value, type_info, ops),
                       type_info["assert"])
    return True


_ASSERT_OPS_INT_OR_FLOAT = {
    "and": _assert_op_and,
    "not": _assert_op_not,
    "or": _assert_op_or,
    "eq": _assert_op_eq,
    "ne": _assert_op_ne,
    "le": _assert_op_le,
    "lt": _assert_op_lt,
    "ge": _assert_op_ge,
    "gt": _assert_op_gt,
}


def _assert_int_or_float(path: _Path, value: Any, type_info: Any) -> bool:
    return _maybe_assert(path, value, type_info, _ASSERT_OPS_INT_OR_FLOAT)


_ASSERT_OPS_STR = {
    "and": _assert_op_and,
    "not": _assert_op_not,
    "or": _assert_op_or,
    "eq": _assert_op_eq,
    "ne": _assert_op_ne,
    "le": _assert_op_le,
    "lt": _assert_op_lt,
    "ge": _assert_op_ge,
    "gt": _assert_op_gt,
    "uid": _assert_op_uid,
    "re": _assert_op_re,
    "in": _assert_op_in,
    "contains": _assert_op_contains,
}


def _assert_str(path: _Path, value: Any, type_info: Any) -> bool:
    return _maybe_assert(path, value, type_info, _ASSERT_OPS_STR)


def _assert_type(path: _Path, value: Any, type_expected: str) -> bool:
    type_actual = _type_name(value)
    if type_actual == type_expected:
        return True
    logging.error("%s expected type '%s', actual type '%s'", _prefix(path),
                  type_expected, type_actual)
    return False


NAME = re.compile(r"^([a-z][a-z0-9-]*|SPDX-License-Identifier)$")


def _prefix(prefix: _Path) -> str:
    if prefix.path.endswith(":"):
        return prefix.path
    return prefix.path + ":"


class _Verifier:

    def __init__(self, name: str, verifier_map: _VerifierMap):
        self._name = name
        self._verifier_map = verifier_map
        self.is_subtype = False
        verifier_map[name] = self

    def verify_info(self, path: _Path) -> None:
        """ Produces a verify logging information. """
        logging.info("%s verify using type '%s'", _prefix(path), self._name)

    def verify(self, path: _Path, value: Any) -> Set[str]:
        """ Verifies a value according to the type information. """
        self.verify_info(path)
        _assert_type(path, value, self._name)
        return set()

    def resolve_type_refinements(self) -> None:
        """ Resolves the type refinements for this type. """


class _AnyVerifier(_Verifier):

    def verify(self, path: _Path, _value: Any) -> Set[str]:
        """ Does not verify the value. """
        self.verify_info(path)
        return set()


class _NameVerifier(_Verifier):

    def verify(self, path: _Path, value: Any) -> Set[str]:
        """ Verifies a name. """
        self.verify_info(path)
        if _assert_type(path, value, "str") and NAME.search(value) is None:
            logging.error("%s invalid name: %s", _prefix(path), value)
        return set()


class _UIDVerifier(_Verifier):

    def verify(self, path: _Path, value: Any) -> Set[str]:
        """ Verifies an attribute key. """
        self.verify_info(path)
        if _assert_type(path, value, "str"):
            try:
                path.item.map(value)
            except KeyError:
                logging.error("%s cannot resolve UID: %s", _prefix(path),
                              value)
        return set()


class _ItemVerifier(_Verifier):

    def __init__(self, name: str, verifier_map: _VerifierMap,
                 info_map: Dict[str, Any], item: Item):
        super().__init__(name, verifier_map)
        self._info_map = info_map
        self._item = item
        self._subtype_key = ""
        self._subtype_verifiers: _VerifierMap = {}

    def verify_bool(self, path: _Path, value: Any, type_info: Any) -> Set[str]:
        """ Verifies a boolean value. """
        if type_info and "assert" in type_info:
            expected = type_info["assert"]
            if expected != value:
                logging.error("%s expected %r, actual %r", _prefix(path),
                              expected, value)
        return set()

    def _verify_key(self, path: _Path, value: Any, type_name: str,
                    key: str) -> None:
        if type_name in self._verifier_map:
            self._verifier_map[type_name].verify(
                _Path(path.item, path.path + f"/{key}"), value[key])
        else:
            logging.error("%s unknown specification type: %s", _prefix(path),
                          type_name)

    def assert_keys_no_constraints(self, path: _Path, specified_keys: Set[str],
                                   keys: List[str]) -> None:
        """ Asserts nothing in particular. """

    def assert_keys_at_least_one(self, path: _Path, specified_keys: Set[str],
                                 keys: List[str]) -> None:
        """ Asserts that at least one specified key is present in the keys. """
        present_keys = specified_keys.intersection(keys)
        if len(present_keys) == 0:
            logging.error(
                "%s not at least one key out of %s is present for type '%s'",
                _prefix(path), str(sorted(specified_keys)), self._name)

    def assert_keys_at_most_one(self, path: _Path, specified_keys: Set[str],
                                keys: List[str]) -> None:
        """ Asserts that at most one specified key is present in the keys. """
        present_keys = specified_keys.intersection(keys)
        if len(present_keys) > 1:
            logging.error(
                "%s not at most one key out of %s "
                "is present for type '%s': %s", _prefix(path),
                str(sorted(specified_keys)), self._name,
                str(sorted(present_keys)))

    def assert_keys_exactly_one(self, path: _Path, specified_keys: Set[str],
                                keys: List[str]) -> None:
        """ Asserts that exactly one specified key is present in the keys. """
        present_keys = specified_keys.intersection(keys)
        if len(present_keys) != 1:
            logging.error(
                "%s not exactly one key out of %s "
                "is present for type '%s': %s", _prefix(path),
                str(sorted(specified_keys)), self._name,
                str(sorted(present_keys)))

    def assert_keys_subset(self, path: _Path, specified_keys: Set[str],
                           keys: List[str]) -> None:
        """ Asserts that the specified keys are a subset of the keys. """
        if not specified_keys.issubset(keys):
            missing_keys = specified_keys.difference(
                specified_keys.intersection(keys))
            logging.error("%s missing mandatory keys for type '%s': %s",
                          _prefix(path), self._name, str(sorted(missing_keys)))

    def _assert_mandatory_keys(self, path: _Path, type_info: Any,
                               attr_info: Any, keys: List[str]) -> None:
        mandatory_attr_info = type_info["mandatory-attributes"]
        if isinstance(mandatory_attr_info, str):
            _ASSERT_KEYS[mandatory_attr_info](self, path, set(attr_info), keys)
        else:
            assert isinstance(mandatory_attr_info, list)
            self.assert_keys_subset(path, set(mandatory_attr_info), keys)

    def verify_dict(self, path: _Path, value: Any, type_info: Any) -> Set[str]:
        """ Verifies a dictionary value. """
        keys = sorted(filter(lambda key: not key.startswith("_"), value))
        attr_info = type_info["attributes"]
        self._assert_mandatory_keys(path, type_info, attr_info, keys)
        verified_keys: Set[str] = set()
        for key in keys:
            if key in attr_info:
                self._verify_key(path, value, attr_info[key]["spec-type"], key)
                verified_keys.add(key)
            elif "generic-attributes" in type_info:
                key_as_value = {key: key}
                self._verify_key(
                    path, key_as_value,
                    type_info["generic-attributes"]["key-spec-type"], key)
                self._verify_key(
                    path, value,
                    type_info["generic-attributes"]["value-spec-type"], key)
                verified_keys.add(key)
        if self._subtype_key:
            if self._subtype_key in keys:
                subtype_value = value[self._subtype_key]
                if subtype_value in self._subtype_verifiers:
                    verified_keys.update(
                        self._subtype_verifiers[subtype_value].verify(
                            path, value))
                else:
                    logging.error(
                        "%s unknown subtype for key '%s' for type '%s': %s",
                        _prefix(path), self._subtype_key, self._name,
                        subtype_value)
            else:
                logging.error("%s subtype key '%s' not present for type '%s'",
                              _prefix(path), self._subtype_key, self._name)
        if not self.is_subtype:
            unverified_keys = set(keys).difference(verified_keys)
            if unverified_keys:
                logging.error(
                    "%s has unverfied keys for type '%s' and its subtypes: %s",
                    _prefix(path), self._name, str(sorted(unverified_keys)))
        return verified_keys

    def verify_int_or_float(self, path: _Path, value: Any,
                            type_info: Any) -> Set[str]:
        """ Verifies an integer or float value. """
        if not _assert_int_or_float(path, value, type_info):
            logging.error("%s invalid value: %s", _prefix(path), str(value))
        return set()

    def verify_list(self, path: _Path, value: Any, type_info: Any) -> Set[str]:
        """ Verifies a list value. """
        verifier = self._verifier_map[type_info["spec-type"]]
        for index, element in enumerate(value):
            verifier.verify(_Path(path.item, path.path + f"[{index}]"),
                            element)
        return set()

    def verify_none(self, _path: _Path, _value: Any,
                    _type_info: Any) -> Set[str]:
        """ Verifies a none value. """
        return set()

    def verify_str(self, path: _Path, value: Any, type_info: Any) -> Set[str]:
        """ Verifies a string value. """
        if not _assert_str(path, value, type_info):
            logging.error("%s invalid value: %s", _prefix(path), value)
        return set()

    def verify(self, path: _Path, value: Any) -> Set[str]:
        self.verify_info(path)
        type_name = _type_name(value)
        if type_name in self._info_map:
            return _VERIFY[type_name](self, path, value,
                                      self._info_map[type_name])
        logging.error(
            "%s expected value of types %s for type '%s', "
            "actual type '%s'", _prefix(path), str(sorted(self._info_map)),
            self._name, type_name)
        return set()

    def _add_subtype_verifier(self, subtype_key: str, subtype_value: str,
                              subtype_name: str) -> None:
        logging.info("add subtype '%s' to '%s'", subtype_name, self._name)
        assert not self._subtype_key or self._subtype_key == subtype_key
        assert subtype_value not in self._subtype_verifiers
        subtype_verifier = self._verifier_map[subtype_name]
        subtype_verifier.is_subtype = True
        self._subtype_key = subtype_key
        self._subtype_verifiers[subtype_value] = subtype_verifier

    def resolve_type_refinements(self) -> None:
        for link in self._item.links_to_children():
            if link.role == "spec-refinement":
                self._add_subtype_verifier(link["spec-key"],
                                           link["spec-value"],
                                           link.item["spec-type"])


_VERIFY = {
    "bool": _ItemVerifier.verify_bool,
    "dict": _ItemVerifier.verify_dict,
    "float": _ItemVerifier.verify_int_or_float,
    "int": _ItemVerifier.verify_int_or_float,
    "list": _ItemVerifier.verify_list,
    "none": _ItemVerifier.verify_none,
    "str": _ItemVerifier.verify_str,
}

_ASSERT_KEYS = {
    "all": _ItemVerifier.assert_keys_subset,
    "at-least-one": _ItemVerifier.assert_keys_at_least_one,
    "at-most-one": _ItemVerifier.assert_keys_at_most_one,
    "exactly-one": _ItemVerifier.assert_keys_exactly_one,
    "none": _ItemVerifier.assert_keys_no_constraints,
}


def _create_verifier(item: Item, verifier_map: _VerifierMap) -> _Verifier:
    spec_type = item["spec-type"]
    assert spec_type not in verifier_map
    spec_info = item["spec-info"]
    assert isinstance(spec_info, dict)
    return _ItemVerifier(spec_type, verifier_map, spec_info, item)


def _gather_item_verifiers(item: Item, verifier_map: _VerifierMap) -> None:
    for link in item.links_to_children():
        if link.role == "spec-member":
            _create_verifier(link.item, verifier_map)


@contextmanager
def _add_filter() -> Iterator[_Filter]:
    logger = logging.getLogger()
    log_filter = _Filter()
    logger.addFilter(log_filter)
    yield log_filter
    logger.removeFilter(log_filter)


class SpecVerifier:
    """ Verifies items according to the specification of the specification. """

    # pylint: disable=too-few-public-methods
    def __init__(self, item_cache: ItemCache, root_uid: str):
        verifier_map: _VerifierMap = {}
        _AnyVerifier("any", verifier_map)
        _NameVerifier("name", verifier_map)
        _UIDVerifier("uid", verifier_map)
        _Verifier("bool", verifier_map)
        _Verifier("float", verifier_map)
        _Verifier("int", verifier_map)
        _Verifier("none", verifier_map)
        _Verifier("str", verifier_map)
        try:
            root_item = item_cache[root_uid]
        except KeyError:
            self._root_verifier = None
        else:
            self._root_verifier = _create_verifier(root_item, verifier_map)
            _gather_item_verifiers(root_item, verifier_map)
            for name in sorted(verifier_map):
                logging.info("type: %s", name)
                verifier_map[name].resolve_type_refinements()

    def verify_all(self, item_cache: ItemCache) -> VerifyStatus:
        """ Verifies all items of the cache. """
        with _add_filter() as log_filter:
            if self._root_verifier is None:
                logging.error("root type item does not exist in item cache")
            else:
                logging.info("start specification item verification")
                for key in sorted(item_cache):
                    item = item_cache[key]
                    self._root_verifier.verify(_Path(item, f"{item.uid}:"),
                                               item.data)
                logging.info("finished specification item verification")
        return log_filter.get_verify_info()

    def verify(self, item: Item) -> VerifyStatus:
        """ Verifies the item. """
        with _add_filter() as log_filter:
            if self._root_verifier is None:
                logging.error("root type item does not exist in item cache")
            else:
                self._root_verifier.verify(_Path(item, f"{item.uid}:"),
                                           item.data)
        return log_filter.get_verify_info()


def verify(config: dict, item_cache: ItemCache) -> VerifyStatus:
    """
    Verifies specification items according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache.
    """
    try:
        root_uid = config["root-type"]
    except KeyError:
        logging.error("configuration has no root type")
        return VerifyStatus(0, 1, 0, 0, 0)
    verifier = SpecVerifier(item_cache, root_uid)
    return verifier.verify_all(item_cache)
