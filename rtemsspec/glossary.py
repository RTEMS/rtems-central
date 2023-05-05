# SPDX-License-Identifier: BSD-2-Clause
""" This module provides functions for glossary of terms generation. """

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

import glob
import re
from typing import Any, Dict, List, NamedTuple

from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]


class _Glossary(NamedTuple):
    """ A glossary of terms. """
    uid_to_item: ItemMap
    term_to_item: ItemMap


def augment_glossary_terms(item: Item, path: List[str]) -> None:
    """
    Augments the glossary term items of the cache with a glossary path prefix.
    """
    for child in item.children("requirement-refinement"):
        augment_glossary_terms(child, path + [child["name"]])
    for child in item.children("glossary-member"):
        term = " - ".join(path + [child["term"]])
        child["_term"] = term


def _gather_glossary_terms(item: Item, glossary: _Glossary) -> None:
    for child in item.children("requirement-refinement"):
        _gather_glossary_terms(child, glossary)
    for child in item.children("glossary-member"):
        glossary.uid_to_item[child.uid] = child
        term = child["_term"]
        assert term not in glossary.term_to_item
        glossary.term_to_item[term] = child


def _generate_glossary_content(terms: ItemMap, header: str, target: str,
                               mapper: ItemMapper) -> None:
    content = SphinxContent()
    content.add_header(header, level=1)
    content.add(".. glossary::")
    with content.indent():
        content.add(":sorted:")
        for item in sorted(terms.values(), key=lambda x: x["_term"].lower()):
            content.register_license_and_copyrights_of_item(item)
            text = mapper.substitute(item["text"], item)
            content.add_definition_item(item["_term"], text)
    content.add_licence_and_copyrights()
    content.write(target)


_TERM = re.compile(r":term:`([^`]+)`")
_TERM_2 = re.compile(r"^[^<]+<([^>]+)>")
_SPACE = re.compile(r"\s+")


def _find_glossary_terms(path: str, document_terms: ItemMap,
                         glossary: _Glossary) -> None:
    for src in glob.glob(path + "/**/*.rst", recursive=True):
        if src.endswith("glossary.rst"):
            continue
        with open(src, "r", encoding="utf-8") as out:
            for term in _TERM.findall(out.read()):
                match = _TERM_2.search(term)
                if match:
                    term = match.group(1)
                term = _SPACE.sub(" ", term)
                item = glossary.term_to_item[term]
                document_terms[item.uid] = item


class _GlossaryMapper(ItemMapper):

    def __init__(self, item: Item, document_terms: ItemMap):
        super().__init__(item)
        self._document_terms = document_terms
        self.add_get_value("glossary/term:/term", self._add_to_terms)
        self.add_get_value("glossary/term:/plural", self._add_to_terms)

    def _add_to_terms(self, ctx: ItemGetValueContext) -> Any:
        if ctx.item.uid not in self._document_terms:
            self._document_terms[ctx.item.uid] = ctx.item
            _GlossaryMapper(ctx.item,
                            self._document_terms).substitute(ctx.item["text"])
        # The value of this substitute is unused.
        return ""


def _resolve_glossary_terms(document_terms: ItemMap) -> None:
    for term in list(document_terms.values()):
        _GlossaryMapper(term, document_terms).substitute(term["text"])


def _generate_project_glossary(glossary: _Glossary, header: str, target: str,
                               mapper: ItemMapper) -> None:
    if target:
        _generate_glossary_content(glossary.uid_to_item, header, target,
                                   mapper)


def _generate_document_glossary(config: dict, glossary: _Glossary,
                                mapper: ItemMapper) -> None:
    document_terms: ItemMap = {}
    for path in config["rest-source-paths"]:
        _find_glossary_terms(path, document_terms, glossary)
    _resolve_glossary_terms(document_terms)
    _generate_glossary_content(document_terms, config["header"],
                               config["target"], mapper)


def generate(config: dict, item_cache: ItemCache, mapper: ItemMapper) -> None:
    """
    Generates glossaries of terms according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the glossary
                       groups and terms.
    """
    project_glossary = _Glossary({}, {})
    for uid in config["project-groups"]:
        group = item_cache[uid]
        assert group.type == "glossary/group"
        _gather_glossary_terms(group, project_glossary)

    _generate_project_glossary(project_glossary, config["project-header"],
                               config["project-target"], mapper)

    for document_config in config["documents"]:
        _generate_document_glossary(document_config, project_glossary, mapper)
