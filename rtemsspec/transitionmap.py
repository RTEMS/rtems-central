# SPDX-License-Identifier: BSD-2-Clause
"""
This module provides the Transition and TransitionMap classes used to work with
action requirements.
"""

# Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG
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

import itertools
import math
import textwrap
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Tuple

from rtemsspec.content import CContent, enabled_by_to_exp, ExpressionMapper, \
    get_integer_type
from rtemsspec.items import is_enabled, Item


class Transition(NamedTuple):
    """ Represents a action requirement transition map entry.  """
    desc_idx: int
    enabled_by: Any
    skip: int
    pre_cond_na: Tuple[int, ...]
    post_cond: Tuple[Any, ...]


def _variant_to_key(variant: Transition) -> str:
    return "".join((enabled_by_to_exp(variant.enabled_by,
                                      ExpressionMapper()), str(variant.skip),
                    str(variant.pre_cond_na), str(variant.post_cond)))


class _TransitionEntry:

    def __init__(self):
        self.key = ""
        self.variants: List[Transition] = []

    def __bool__(self):
        return bool(self.variants)

    def __getitem__(self, key):
        return self.variants[key]

    def __len__(self):
        return len(self.variants)

    def add(self, variant: Transition) -> None:
        """ Adds the variant to the transitions of the entry. """
        self.key += _variant_to_key(variant)
        self.variants.append(variant)

    def replace(self, index: int, variant: Transition) -> None:
        """ Replace the variant at transition variant index. """
        self.key = self.key.replace(_variant_to_key(self.variants[index]),
                                    _variant_to_key(variant))
        self.variants[index] = variant


_TransitionMap = List[_TransitionEntry]


def _to_st_idx(conditions: List[Any]) -> Tuple[Dict[str, int], ...]:
    return tuple(
        dict((state["name"], st_idx) for st_idx, state in enumerate(
            itertools.chain(condition["states"], [{
                "name": "N/A"
            }]))) for condition in conditions)


def _to_st_name(conditions: List[Any]) -> Tuple[Tuple[str, ...], ...]:
    return tuple(
        tuple(
            itertools.chain((state["name"]
                             for state in condition["states"]), ["NA"]))
        for condition in conditions)


class _PostCondContext(NamedTuple):
    transition_map: "TransitionMap"
    map_idx: int
    pre_co_states: Tuple[int, ...]
    post_co_states: Tuple[Any, ...]
    post_co_idx: int
    ops: Any


def _post_cond_bool_and(ctx: _PostCondContext, exp: Any) -> bool:
    for element in exp:
        if not _post_cond_bool_exp(ctx, element):
            return False
    return True


def _post_cond_bool_not(ctx: _PostCondContext, exp: Any) -> bool:
    return not _post_cond_bool_exp(ctx, exp)


def _post_cond_bool_or(ctx: _PostCondContext, exp: Any) -> bool:
    for element in exp:
        if _post_cond_bool_exp(ctx, element):
            return True
    return False


def _post_cond_bool_post_cond(ctx: _PostCondContext, exp: Any) -> bool:
    for post_co_name, status in exp.items():
        if isinstance(status, str):
            status = [status]
        post_co_idx = ctx.transition_map.post_co_name_to_co_idx(post_co_name)
        st_idx = [
            ctx.transition_map.post_co_idx_st_name_to_st_idx(
                post_co_idx, st_name) for st_name in status
        ]
        if ctx.post_co_states[post_co_idx] not in st_idx:
            return False
    return True


def _post_cond_bool_pre_cond(ctx: _PostCondContext, exp: Any) -> bool:
    for pre_co_name, status in exp.items():
        if isinstance(status, str):
            status = [status]
        pre_co_idx = ctx.transition_map.pre_co_name_to_co_idx(pre_co_name)
        st_idx = [
            ctx.transition_map.pre_co_idx_st_name_to_st_idx(
                pre_co_idx, st_name) for st_name in status
        ]
        if ctx.pre_co_states[pre_co_idx] not in st_idx:
            return False
    return True


_POST_COND_BOOL_OPS = {
    "and": _post_cond_bool_and,
    "not": _post_cond_bool_not,
    "or": _post_cond_bool_or,
    "post-conditions": _post_cond_bool_post_cond,
    "pre-conditions": _post_cond_bool_pre_cond,
}


def _post_cond_bool_exp(ctx: _PostCondContext, exp: Any) -> Optional[int]:
    if isinstance(exp, list):
        return _post_cond_bool_or(ctx, exp)
    key = next(iter(exp))
    return _POST_COND_BOOL_OPS[key](ctx, exp[key])


def _post_cond_do_specified_by(ctx: _PostCondContext, pre_co_name: str) -> int:
    pre_co_idx = ctx.transition_map.pre_co_name_to_co_idx(pre_co_name)
    st_name = ctx.transition_map.pre_co_idx_st_idx_to_st_name(
        pre_co_idx, ctx.pre_co_states[pre_co_idx])
    return ctx.transition_map.post_co_idx_st_name_to_st_idx(
        ctx.post_co_idx, st_name)


def _post_cond_if(ctx: _PostCondContext) -> Optional[int]:
    if _post_cond_bool_exp(ctx, ctx.ops["if"]):
        if "then-specified-by" in ctx.ops:
            return _post_cond_do_specified_by(ctx,
                                              ctx.ops["then-specified-by"])
        return ctx.transition_map.post_co_idx_st_name_to_st_idx(
            ctx.post_co_idx, ctx.ops["then"])
    return None


def _post_cond_specified_by(ctx: _PostCondContext) -> Optional[int]:
    return _post_cond_do_specified_by(ctx, ctx.ops["specified-by"])


def _post_cond_else(ctx: _PostCondContext) -> Optional[int]:
    return ctx.transition_map.post_co_idx_st_name_to_st_idx(
        ctx.post_co_idx, ctx.ops["else"])


_POST_COND_OP = {
    "else": _post_cond_else,
    "if": _post_cond_if,
    "specified-by": _post_cond_specified_by,
}

PostCond = Tuple[int, ...]

PreCondsOfPostCond = List[Tuple[List[int], ...]]


def _compact(pre_conds: PreCondsOfPostCond) -> PreCondsOfPostCond:
    while True:
        last = pre_conds[0]
        combined_pre_conds = [last]
        combined_count = 0
        for row in pre_conds[1:]:
            diff = [
                index for index, states in enumerate(last)
                if states != row[index]
            ]
            if len(diff) == 1:
                index = diff[0]
                combined_count += 1
                last[index].extend(row[index])
            else:
                combined_pre_conds.append(row)
                last = row
        pre_conds = combined_pre_conds
        if combined_count == 0:
            break
    return pre_conds


def _compact_more(pre_conds: PreCondsOfPostCond) -> PreCondsOfPostCond:
    while True:
        combined_count = 0
        next_pre_conds = []
        while pre_conds:
            first = pre_conds.pop(0)
            next_pre_conds.append(first)
            for row in pre_conds:
                diff = [
                    index for index, states in enumerate(first)
                    if states != row[index]
                ]
                if len(diff) <= 1:
                    if diff:
                        index = diff[0]
                        first[index].extend(row[index])
                    combined_count += 1
                    pre_conds.remove(row)
        pre_conds = next_pre_conds
        if combined_count == 0:
            break
    return pre_conds


class TransitionMap:
    """ Representation of an action requirement transition map. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, item: Item):
        self._item = item
        self._pre_co_count = len(item["pre-conditions"])
        self._post_co_count = len(item["post-conditions"])
        self.pre_co_summary = tuple(0 for _ in range(self._pre_co_count + 1))
        self._pre_co_idx_st_idx_to_st_name = _to_st_name(
            item["pre-conditions"])
        self._post_co_idx_st_idx_to_st_name = _to_st_name(
            item["post-conditions"])
        self._pre_co_idx_st_name_to_st_idx = _to_st_idx(item["pre-conditions"])
        self._post_co_idx_st_name_to_st_idx = _to_st_idx(
            item["post-conditions"])
        self._pre_co_idx_to_cond = dict(
            (co_idx, condition)
            for co_idx, condition in enumerate(item["pre-conditions"]))
        self._pre_co_name_to_co_idx = dict(
            (condition["name"], co_idx)
            for co_idx, condition in enumerate(item["pre-conditions"]))
        self._post_co_name_to_co_idx = dict(
            (condition["name"], co_idx)
            for co_idx, condition in enumerate(item["post-conditions"]))
        self._post_co_idx_to_co_name = dict(
            (co_idx, condition["name"])
            for co_idx, condition in enumerate(item["post-conditions"]))
        self._skip_idx_to_name = dict(
            (skip_idx + 1, key)
            for skip_idx, key in enumerate(item["skip-reasons"].keys()))
        self._skip_name_to_idx = dict(
            (key, skip_idx + 1)
            for skip_idx, key in enumerate(item["skip-reasons"].keys()))
        self._entries: Dict[str, List[Any]] = {}
        self._map = self._build_map()
        self._post_process()

    def __getitem__(self, key: str):
        return self._item[key]

    def __iter__(self):
        yield from self._map

    def entries(self) -> Iterator[List[Any]]:
        """ Yields the transition map entry variants sorted by frequency. """
        yield from sorted(self._entries.values(), key=lambda x: x[1])

    def get_variants(self,
                     enabled: List[str]) -> Iterator[Tuple[int, Transition]]:
        """
        Yields the map index and the transition variants enabled by the enabled
        list.
        """
        for map_idx, transitions in enumerate(self._map):
            for variant in transitions[1:]:
                if is_enabled(enabled, variant.enabled_by):
                    break
            else:
                variant = transitions[0]
            yield map_idx, variant

    def get_post_conditions(
            self, enabled: List[str]
    ) -> Iterator[Tuple[PostCond, PreCondsOfPostCond]]:
        """
        Yields tuples of post-condition variants and the corresponding
        pre-condition variants which are enabled by the enabled list.

        The first entry of the post-condition variant is the skip index.  The
        remaining entries are post-condition indices.  The pre-condition
        variants are a list of tuples.  Each tuple entry corresponds to a
        pre-condition and provides a list of corresponding pre-condition state
        indices.
        """
        entries: Dict[PostCond, PreCondsOfPostCond] = {}
        for map_idx, variant in self.get_variants(enabled):
            key = (variant.skip, ) + variant.post_cond
            entry = entries.setdefault(key, [])
            entry.append(
                tuple([state] for state in self.map_idx_to_pre_co_states(
                    map_idx, variant.pre_cond_na)))
        for post_cond, pre_conds in sorted(entries.items(),
                                           key=lambda x: (x[0][0], len(x[1]))):
            pre_conds = _compact_more(_compact(pre_conds))
            yield post_cond, pre_conds

    def _post_process(self) -> None:
        for map_idx, transitions in enumerate(self):
            if not transitions or not isinstance(
                    transitions[0].enabled_by,
                    bool) or not transitions[0].enabled_by:
                raise ValueError(
                    f"transition map of {self._item.spec} contains no default "
                    "entry for pre-condition set "
                    f"{{{self._map_index_to_pre_conditions(map_idx)}}}")
            entry = self._entries.setdefault(transitions.key,
                                             [0, 0, transitions, []])
            entry[0] += 1
            entry[3].append(map_idx)
        for index, entry in enumerate(
                sorted(self._entries.values(),
                       key=lambda x: x[0],
                       reverse=True)):
            entry[1] = index

    def _map_index_to_pre_conditions(self, map_idx: int) -> str:
        conditions = []
        for condition in reversed(self._item["pre-conditions"]):
            states = condition["states"]
            count = len(states)
            st_idx = int(map_idx % count)
            conditions.append(f"{condition['name']}={states[st_idx]['name']}")
            map_idx //= count
        return ", ".join(reversed(conditions))

    def map_idx_to_pre_co_states(
            self, map_idx: int, pre_cond_na: Tuple[int,
                                                   ...]) -> Tuple[int, ...]:
        """
        Maps the transition map index and the associated pre-condition state
        indices.
        """
        co_states = []
        for condition in reversed(self._item["pre-conditions"]):
            count = len(condition["states"])
            co_states.append(count if pre_cond_na[self._pre_co_name_to_co_idx[
                condition["name"]]] else int(map_idx % count))
            map_idx //= count
        return tuple(reversed(co_states))

    def has_pre_co_not_applicable(self) -> bool:
        """
        Returns true, if there are N/A pre-conditions, otherwise false.
        """
        return sum(self.pre_co_summary[1:]) > 0

    def pre_co_name_to_co_idx(self, co_name: str) -> int:
        """
        Maps the pre-condition name to the associated pre-condition index.
        """
        return self._pre_co_name_to_co_idx[co_name]

    def pre_co_idx_to_co_name(self, co_idx: int) -> str:
        """
        Maps the pre-condition index to the associated pre-condition name.
        """
        return self._pre_co_idx_to_cond[co_idx]["name"]

    def post_co_name_to_co_idx(self, co_name: str) -> int:
        """
        Maps the post-condition name to the associated post-condition index.
        """
        return self._post_co_name_to_co_idx[co_name]

    def post_co_idx_to_co_name(self, co_idx: int) -> str:
        """
        Maps the post-condition index to the associated post-condition name.
        """
        return self._post_co_idx_to_co_name[co_idx]

    def pre_co_idx_st_idx_to_st_name(self, co_idx: int, st_idx: int) -> str:
        """
        Maps the pre-condition name and state index to the associated state
        name.
        """
        return self._pre_co_idx_st_idx_to_st_name[co_idx][st_idx]

    def post_co_idx_st_idx_to_st_name(self, co_idx: int, st_idx: int) -> str:
        """
        Maps the post-condition name and state index to the associated state
        name.
        """
        return self._post_co_idx_st_idx_to_st_name[co_idx][st_idx]

    def pre_co_idx_st_name_to_st_idx(self, co_idx: int, st_name: str) -> int:
        """
        Maps the pre-condition index and state name to the associated state
        index.
        """
        return self._pre_co_idx_st_name_to_st_idx[co_idx][st_name]

    def post_co_idx_st_name_to_st_idx(self, co_idx: int, st_name: str) -> int:
        """
        Maps the post-condition index and state name to the associated state
        index.
        """
        return self._post_co_idx_st_name_to_st_idx[co_idx][st_name]

    def skip_idx_to_name(self, skip_idx: int) -> str:
        """
        Maps the skip index the associated skip name index.
        """
        return self._skip_idx_to_name[skip_idx]

    def _map_post_cond(self, map_idx: int, co_idx: int,
                       variant: Transition) -> Transition:
        if isinstance(variant.post_cond[co_idx], int):
            return variant
        pre_co_states = self.map_idx_to_pre_co_states(map_idx,
                                                      variant.pre_cond_na)
        for ops in variant.post_cond[co_idx]:
            idx = _POST_COND_OP[next(iter(ops))](_PostCondContext(
                self, map_idx, pre_co_states, variant.post_cond, co_idx, ops))
            if idx is not None:
                return Transition(
                    variant.desc_idx, variant.enabled_by, variant.skip,
                    variant.pre_cond_na, variant.post_cond[0:co_idx] +
                    (idx, ) + variant.post_cond[co_idx + 1:])
        raise ValueError(
            "cannot determine state for post-condition "
            f"'{self._post_co_idx_to_co_name[co_idx]}' of transition map "
            f"descriptor {variant.desc_idx} of {self._item.spec} for "
            "pre-condition set "
            f"{{{self._map_index_to_pre_conditions(map_idx)}}}")

    def _make_post_cond(self, map_idx: int, variant: Transition) -> Transition:
        for co_idx in range(len(variant.post_cond)):
            variant = self._map_post_cond(map_idx, co_idx, variant)
        return variant

    def _update_pre_co_summary(self, variant: Transition) -> None:
        self.pre_co_summary = tuple(
            a + b for a, b in zip(self.pre_co_summary, (variant.skip, ) +
                                  variant.pre_cond_na))

    def _add_variant(self, transition_map: _TransitionMap, map_idx: int,
                     variant: Transition) -> None:
        if transition_map[map_idx]:
            for index, existing in enumerate(transition_map[map_idx].variants):
                if existing.enabled_by == variant.enabled_by:
                    if variant.skip:
                        # Allow transition map variants with a skip reason to
                        # overwrite existing variants with the same enabled-by
                        # attribute.  This is important if variants use N/A for
                        # some pre-conditions.  It makes it also easier to skip
                        # pre-conditon states which are controlled by build
                        # options.
                        self._update_pre_co_summary(variant)
                        transition_map[map_idx].replace(index, variant)
                        return
                    raise ValueError(
                        f"transition map descriptor {variant.desc_idx} of "
                        f"{self._item.spec} duplicates pre-condition set "
                        f"{{{self._map_index_to_pre_conditions(map_idx)}}}"
                        " defined by transition map descriptor "
                        f"{existing.desc_idx}")
            default = transition_map[map_idx][0]
            if (default.post_cond, default.skip,
                    default.pre_cond_na) == (variant.post_cond, variant.skip,
                                             variant.pre_cond_na):
                return
        elif not isinstance(variant.enabled_by,
                            bool) or not variant.enabled_by:
            raise ValueError(
                f"transition map descriptor {variant.desc_idx} of "
                f"{self._item.spec} is the first variant for "
                f"{{{self._map_index_to_pre_conditions(map_idx)}}} "
                "and it is not enabled by default")
        self._update_pre_co_summary(variant)
        transition_map[map_idx].add(variant)

    def _add_transitions(self, transition_map: _TransitionMap,
                         desc: Dict[str, Any], desc_idx: int,
                         skip_post_cond: Tuple[Any, ...], co_idx: int,
                         map_idx: int, pre_cond_na: Tuple[int, ...]) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        if co_idx < self._pre_co_count:
            condition = self._pre_co_idx_to_cond[co_idx]
            state_count = len(condition["states"])
            map_idx *= state_count
            states = desc["pre-conditions"][condition["name"]]
            if isinstance(states, str):
                assert states in ["all", "N/A"]
                for st_idx in range(state_count):
                    self._add_transitions(
                        transition_map, desc, desc_idx, skip_post_cond,
                        co_idx + 1, map_idx + st_idx,
                        pre_cond_na + (int(states == "N/A"), ))
            else:
                for st_name in states:
                    try:
                        st_idx = self._pre_co_idx_st_name_to_st_idx[co_idx][
                            st_name]
                    except KeyError as err:
                        msg = (f"transition map descriptor {desc_idx} of "
                               f"{self._item.spec} refers to non-existent "
                               f"state {err} of pre-condition "
                               f"'{condition['name']}'")
                        raise ValueError(msg) from err
                    self._add_transitions(transition_map, desc, desc_idx,
                                          skip_post_cond, co_idx + 1,
                                          map_idx + st_idx,
                                          pre_cond_na + (0, ))
        else:
            variant = self._make_post_cond(
                map_idx,
                Transition(desc_idx, desc["enabled-by"], skip_post_cond[0],
                           pre_cond_na, skip_post_cond[1:]))
            self._add_variant(transition_map, map_idx, variant)

    def _add_default(self, transition_map: _TransitionMap, desc: Dict[str,
                                                                      Any],
                     desc_idx: int, skip_post_cond: Tuple[int, ...]) -> None:
        enabled_by = desc["enabled-by"]
        for map_idx, transition in enumerate(transition_map):
            if not transition:
                transition.add(
                    self._make_post_cond(
                        map_idx,
                        Transition(desc_idx, enabled_by, skip_post_cond[0],
                                   (0, ) * self._pre_co_count,
                                   skip_post_cond[1:])))

    def _get_post_cond(self, desc: Dict[str, Any], co_idx: int) -> Any:
        info = desc["post-conditions"][self._post_co_idx_to_co_name[co_idx]]
        if isinstance(info, str):
            return self._post_co_idx_st_name_to_st_idx[co_idx][info]
        return info

    def _build_map(self) -> _TransitionMap:
        transition_count = 1
        for condition in self["pre-conditions"]:
            state_count = len(condition["states"])
            if state_count == 0:
                raise ValueError(f"pre-condition '{condition['name']}' of "
                                 f"{self._item.spec} has no states")
            transition_count *= state_count
        transition_map = [_TransitionEntry() for _ in range(transition_count)]
        for desc_idx, desc in enumerate(self["transition-map"]):
            if isinstance(desc["post-conditions"], dict):
                try:
                    skip_post_cond = (0, ) + tuple(
                        self._get_post_cond(desc, co_idx)
                        for co_idx in range(self._post_co_count))
                except KeyError as err:
                    msg = (f"transition map descriptor {desc_idx} of "
                           f"{self._item.spec} refers to non-existent "
                           f"post-condition state {err}")
                    raise ValueError(msg) from err
            else:
                skip_post_cond = (
                    self._skip_name_to_idx[desc["post-conditions"]], ) + tuple(
                        self._post_co_idx_st_name_to_st_idx[co_idx]["N/A"]
                        for co_idx in range(self._post_co_count))
            if isinstance(desc["pre-conditions"], dict):
                self._add_transitions(transition_map, desc, desc_idx,
                                      skip_post_cond, 0, 0, ())
            else:
                assert desc["pre-conditions"] == "default"
                self._add_default(transition_map, desc, desc_idx,
                                  skip_post_cond)
        return transition_map

    def _get_entry(self, ident: str, variant: Transition) -> str:
        text = "{ " + ", ".join(
            itertools.chain(
                map(str, (int(variant.skip != 0), ) + variant.pre_cond_na),
                ((f"{ident}_Post_{self._post_co_idx_to_co_name[co_idx]}"
                  f"_{self._post_co_idx_st_idx_to_st_name[co_idx][st_idx]}")
                 for co_idx, st_idx in enumerate(variant.post_cond))))
        wrapper = textwrap.TextWrapper()
        wrapper.initial_indent = "  "
        wrapper.subsequent_indent = "    "
        wrapper.width = 79
        return "\n".join(wrapper.wrap(text)) + " },"

    def _get_entry_bits(self) -> int:
        bits = self._pre_co_count + 1
        for st_idx_to_st_name in self._post_co_idx_st_idx_to_st_name:
            bits += math.ceil(math.log2(len(st_idx_to_st_name)))
        return 2**max(math.ceil(math.log2(bits)), 3)

    def add_map_entry_type(self, content: CContent, ident: str) -> None:
        """ Adds the transition map entry type definition to the content. """
        bits = self._get_entry_bits()
        content.add("typedef struct {")
        with content.indent():
            content.append(f"uint{bits}_t Skip : 1;")
            for condition in self["pre-conditions"]:
                content.append(f"uint{bits}_t Pre_{condition['name']}_NA : 1;")
            for condition in self["post-conditions"]:
                state_bits = math.ceil(math.log2(len(condition["states"]) + 1))
                content.append(
                    f"uint{bits}_t Post_{condition['name']} : {state_bits};")
        content.add(f"}} {ident}_Entry;")

    def add_map(self, content: CContent, ident: str) -> None:
        """ Adds the transition map definitions to the content. """
        entries = []
        mapper = ExpressionMapper()
        for entry in self.entries():
            transitions = entry[2]
            if len(transitions) == 1:
                entries.append(self._get_entry(ident, transitions[0]))
            else:
                ifelse = "#if "
                enumerators: List[str] = []
                for variant in transitions[1:]:
                    enumerators.append(
                        ifelse + enabled_by_to_exp(variant.enabled_by, mapper))
                    enumerators.append(self._get_entry(ident, variant))
                    ifelse = "#elif "
                enumerators.append("#else")
                enumerators.append(self._get_entry(ident, transitions[0]))
                enumerators.append("#endif")
                entries.append("\n".join(enumerators))
        content.add([f"static const {ident}_Entry", f"{ident}_Entries[] = {{"])
        entries[-1] = entries[-1].replace("},", "}")
        content.append(entries)
        integer_type = get_integer_type(len(self._entries))
        content.append(
            ["};", "", f"static const {integer_type}", f"{ident}_Map[] = {{"])
        text = ", ".join(
            str(self._entries[transitions.key][1])
            for transitions in self._map)
        wrapper = textwrap.TextWrapper()
        wrapper.initial_indent = "  "
        wrapper.subsequent_indent = "  "
        wrapper.width = 79
        content.append(wrapper.wrap(text))
        content.append("};")

    def get_post_entry_member(self, co_idx: int) -> str:
        """
        Gets the post-condition entry member name for the post-condition index.
        """
        return f"Post_{self._post_co_idx_to_co_name[co_idx]}"
