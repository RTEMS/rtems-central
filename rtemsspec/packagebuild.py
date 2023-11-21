# SPDX-License-Identifier: BSD-2-Clause
""" This module provides the basic support to build a QDP. """

# Copyright (C) 2021 EDISOFT (https://www.edisoft.pt/)
# Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
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

import copy
import itertools
import logging
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type

from rtemsspec.items import data_digest, Item, ItemCache, \
    ItemGetValueContext, ItemGetValue, ItemMapper, is_enabled, \
    Link, link_is_enabled
from rtemsspec.sphinxcontent import SphinxMapper

_SINGLE_SUBSTITUTION = re.compile(
    r"^\${[a-zA-Z0-9._/-]+(:[a-zA-Z0-9._/-]+)?(:[^${}]*)?}$")


def _get_input_links(item: Item) -> Iterator[Link]:
    yield from itertools.chain(item.links_to_parents("input"),
                               item.links_to_children("input-to"))


def build_item_input(item: Item, name: str) -> Item:
    """ Returns the first input item with the name.  """
    for link in _get_input_links(item):
        if link["name"] == name:
            return link.item
    raise KeyError


def _get_spec(ctx: ItemGetValueContext) -> Any:
    return ctx.item.spec


class BuildItemMapper(SphinxMapper):
    """
    The build item mapper provides a method to get a link to the primary
    documentation place of the item.
    """

    def __init__(self, item: Item, recursive: bool = False):
        super().__init__(item, recursive)
        for type_name in item.cache.items_by_type:
            self.add_get_value(f"{type_name}:/spec", _get_spec)

    def get_link(self, _item: Item) -> str:
        """ Returns a link to the primary documentation place of the item. """
        raise NotImplementedError


class BuildItem():
    """ This is the base class for build steps. """

    # pylint: disable=too-many-public-methods
    @classmethod
    def prepare_factory(cls, _factory: "BuildItemFactory",
                        _type_name: str) -> None:
        """ Prepares the build item factory for the type. """

    def __init__(self,
                 director: "PackageBuildDirector",
                 item: Item,
                 mapper: Optional[BuildItemMapper] = None):
        if mapper is None:
            mapper = BuildItemMapper(item, recursive=True)
        self.director = director
        self.item = item
        self.mapper = mapper
        director.factory.add_get_values_to_mapper(self.mapper)
        self._did_run = False

    def __contains__(self, key: str) -> bool:
        return key in self.item

    def __getitem__(self, key: str) -> Any:
        return self.substitute(self.item[key])

    def __setitem__(self, key: str, value: Any) -> None:
        self.item[key] = value

    @property
    def uid(self) -> str:
        """ Returns the UID of the build item. """
        return self.item.uid

    @property
    def variant(self) -> "BuildItem":
        """ Returns the variant build item. """
        return self.director["/qdp/variant"]

    @property
    def enabled_set(self) -> List["str"]:
        """ Is the enabled set of the variant item. """
        return self.director["/qdp/variant"]["enabled"]

    @property
    def enabled(self) -> bool:
        """
        Is true, if the build item is enabled using the enabled set of the
        variant item, otherwise false.
        """
        return is_enabled(self.enabled_set, self["enabled-by"])

    def build(self, force: bool) -> None:
        """ Runs the build if necessary. """
        self._did_run = False
        self.mapper.item = self.item
        logging.info("%s: check if build is necessary", self.uid)
        necessary = self.is_build_necessary()
        if necessary:
            logging.info("%s: build is necessary", self.uid)
        if force:
            logging.info("%s: build is forced", self.uid)
        if force or necessary:
            logging.info("%s: discard outputs", self.uid)
            self.discard_outputs()
            logging.info("%s: run", self.uid)
            self.run()
            self._did_run = True
            logging.info("%s: refresh outputs", self.uid)
            self.refresh_outputs()
            logging.info("%s: refresh input links", self.uid)
            self.refresh_input_links()
            logging.info("%s: refresh", self.uid)
            self.refresh()
            logging.info("%s: commit", self.uid)
            self.commit("Finish build step")
            logging.info("%s: finished", self.uid)
        else:
            logging.info("%s: build is unnecessary", self.uid)

    def has_changed(self, link: Link) -> bool:
        """
        Returns true, if the build item state changed with respect to the state
        of the link, otherwise false.
        """
        return self._did_run or link["hash"] is None or self.digest != link[
            "hash"]

    def is_build_necessary(self) -> bool:
        """ Returns true, if the build is necessary, otherwise false. """
        necessary = False
        for link in itertools.chain(
                self.item.links_to_parents("input",
                                           is_link_enabled=link_is_enabled),
                self.item.links_to_children("input-to",
                                            is_link_enabled=link_is_enabled)):
            if not link.item.is_enabled(self.enabled_set):
                logging.info("%s: input is disabled: %s", self.uid,
                             link.item.uid)
                continue
            build_item = self.director[link.item.uid]
            if link["hash"] is None:
                logging.info("%s: input is new: %s", self.uid, build_item.uid)
            if build_item.has_changed(link):
                logging.info("%s: input has changed: %s", self.uid,
                             build_item.uid)
                necessary = True
            else:
                logging.info("%s: input has not changed: %s", self.uid,
                             build_item.uid)
        return necessary

    def discard(self) -> None:
        """ Discards the data associated with the build item.  """

    def discard_outputs(self) -> None:
        """ Discards all outputs of the build item.  """
        for item in self.item.parents("output",
                                      is_link_enabled=link_is_enabled):
            if not item.is_enabled(self.enabled_set):
                logging.info("%s: output is disabled: %s", self.uid, item.uid)
                continue
            self.director[item.uid].discard()

    def clear(self) -> None:
        """ Clears the state of the build item.  """

    def refresh(self) -> None:
        """ Refreshes the build item state.  """

    def commit(self, _reason: str) -> None:
        """ Commits the build item state.  """
        for item in self.item.children("input-to"):
            item.save()
        self.item.save()

    @property
    def digest(self) -> str:
        """ Is the hash of the build item. """
        data = self.item.data
        data["links"] = copy.deepcopy(data["links"])
        for link in data["links"]:
            if link["role"] == "input-to":
                link["hash"] = None
        return data_digest(data)

    def refresh_link(self, link: Link) -> None:
        """ Refreshes the link to reflect the state of the build item. """
        link["hash"] = self.digest

    def refresh_outputs(self) -> None:
        """ Refreshes all outputs of the build item.  """
        for item in self.item.parents("output"):
            self.director[item.uid].refresh()

    def refresh_input_links(self) -> None:
        """ Refreshes all input links of the build item.  """
        for link in _get_input_links(self.item):
            self.director[link.item.uid].refresh_link(link)

    def run(self):
        """ Runs the build item tasks. """

    def substitute(self, data: Any, item: Optional[Item] = None) -> Any:
        """
        Recursively substitutes the data using the item mapper of the build
        step.
        """
        if item is None:
            item = self.item
        if isinstance(data, str):
            return self.mapper.substitute(data, item)
        if isinstance(data, list):
            new_list: List[Any] = []
            for element in data:
                if isinstance(element, str):
                    match = _SINGLE_SUBSTITUTION.search(element)
                    if match:
                        new_item, _, new_element = self.mapper.map(
                            element[2:-1], item)
                        if isinstance(new_element, list):
                            new_list.extend(
                                self.mapper.substitute(new_element_2, new_item)
                                for new_element_2 in new_element)
                        else:
                            new_list.append(
                                self.mapper.substitute(new_element, new_item))
                    else:
                        new_list.append(self.mapper.substitute(element, item))
                else:
                    new_list.append(self.substitute(element))
            return new_list
        if isinstance(data, dict):
            new_dict: Dict[Any, Any] = {}
            for key, value in data.items():
                new_dict[key] = self.substitute(value)
            return new_dict
        return data

    def input(self, name: str) -> "BuildItem":
        """
        Returns the first directory state dependency and the expected hash
        associated with the name.
        """
        for link in _get_input_links(self.item):
            if link["name"] == name:
                return self.director[link.item.uid]
        raise KeyError

    def inputs(self, name: Optional[str] = None) -> Iterator["BuildItem"]:
        """ Yields the inputs associated with the name. """
        for link in _get_input_links(self.item):
            if name is None or link["name"] == name:
                yield self.director[link.item.uid]

    def input_links(self, name: Optional[str] = None) -> Iterator[Link]:
        """ Yields the inputs associated with the name. """
        for link in _get_input_links(self.item):
            if name is None or link["name"] == name:
                yield link

    def output(self, name: str) -> "BuildItem":
        """
        Returns the first directory state production associated with the
        name.
        """
        for link in self.item.links_to_parents(
                "output", is_link_enabled=link_is_enabled):
            if link["name"] == name:
                if link.item.is_enabled(self.enabled_set):
                    return self.director[link.item.uid]
                logging.info("%s: output is disabled: %s", self.uid,
                             link.item.uid)
                raise ValueError
        raise KeyError


def _get_dash(ctx: ItemGetValueContext) -> str:
    return f"-{ctx.value}" if ctx.value else ""


def _get_slash(ctx: ItemGetValueContext) -> str:
    return f"/{ctx.value}" if ctx.value else ""


class PackageVariant(BuildItem):
    """ This is the class represents a package variant. """

    @classmethod
    def prepare_factory(cls, factory: "BuildItemFactory",
                        type_name: str) -> None:
        BuildItem.prepare_factory(factory, type_name)
        factory.add_get_value(f"{type_name}:/config/dash", _get_dash)
        factory.add_get_value(f"{type_name}:/config/slash", _get_slash)


class BuildItemFactory:
    """
    The build item factory can create build items for registered build item
    types.
    """

    def __init__(self) -> None:
        """ Initializes the dictionary of build steps """
        self._build_step_map: Dict[str, Type[BuildItem]] = {}
        self._get_values: List[Tuple[str, ItemGetValue]] = []

    def add_constructor(self, type_name: str, cls: Type[BuildItem]):
        """ Associates the build item constructor with the type name. """
        self._build_step_map[type_name] = cls
        cls.prepare_factory(self, type_name)

    def create(self, director: "PackageBuildDirector",
               item: Item) -> BuildItem:
        """
        Creates a build item for the item.

        The new build item will be assocated with the build director.
        """
        return self._build_step_map.get(item.type, BuildItem)(director, item)

    def add_get_value(self, type_path_key: str,
                      get_value: ItemGetValue) -> None:
        """ Adds a get value method for the type key path. """
        self._get_values.append((type_path_key, get_value))

    def add_get_values_to_mapper(self, mapper: ItemMapper) -> None:
        """ Adds add registered get value methods to the mapper. """
        for type_path_key, get_value in self._get_values:
            mapper.add_get_value(type_path_key, get_value)


class PackageBuildDirector:
    """
    The package build director contains the package build state and runs the
    build.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, item_cache: ItemCache, factory: BuildItemFactory):
        self._item_cache = item_cache
        self.factory = factory
        self._build_items: Dict[str, BuildItem] = {}

    def __getitem__(self, uid: str) -> BuildItem:
        item = self._build_items.get(uid, None)
        if item is not None:
            return item
        logging.info("%s: create build item", uid)
        item = self.factory.create(self, self._item_cache[uid])
        self._build_items[uid] = item
        return item

    def clear(self) -> None:
        """ Clears the build items of the director.  """
        self._build_items.clear()

    def build_package(self, only: Optional[List[str]],
                      force: Optional[List[str]]):
        """ Builds the package """
        if force is None:
            force = []
        build_steps = self._item_cache["/qdp/variant"].parent("package-build")
        enabled_set = self["/qdp/variant"]["enabled"]
        logging.info("%s: build the package", build_steps.uid)
        for step in build_steps.parents("build-step",
                                        is_link_enabled=link_is_enabled):
            if not step.is_enabled(enabled_set):
                logging.info("%s: is disabled", step.uid)
                continue
            builder = self[step.uid]
            if only is not None and step.uid not in only:
                logging.info("%s: build is skipped", step.uid)
                continue
            builder.build(step.uid in force)
        logging.info("%s: finished building package", build_steps.uid)
