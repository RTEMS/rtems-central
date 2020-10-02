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
from typing import Any, Dict, NamedTuple

from rtemsspec.sphinxcontent import SphinxContent, SphinxMapper
from rtemsspec.items import Item, ItemCache, ItemGetValueContext, ItemMapper

ItemMap = Dict[str, Item]


class _Glossary(NamedTuple):
    """ A glossary of terms. """
    uid_to_item: ItemMap = {}
    term_to_item: ItemMap = {}


def _gather_glossary_terms(item: Item, glossary: _Glossary) -> None:
    for child in item.children():
        _gather_glossary_terms(child, glossary)
    if item["type"] == "glossary" and item["glossary-type"] == "term":
        glossary.uid_to_item[item.uid] = item
        term = item["term"]
        assert term not in glossary.term_to_item
        glossary.term_to_item[term] = item


def _generate_glossary_content(terms: ItemMap) -> SphinxContent:
    content = SphinxContent()
    content.add_header("Glossary", level=1)
    content.add(".. glossary::")
    with content.indent():
        content.add(":sorted:")
        for item in sorted(terms.values(), key=lambda x: x["term"].lower()):
            content.register_license_and_copyrights_of_item(item)
            text = SphinxMapper(item).substitute(item["text"])
            content.add_definition_item(item["term"], text)
    content.add_licence_and_copyrights()
    return content


def _find_glossary_terms(path: str, document_terms: ItemMap,
                         glossary: _Glossary) -> None:
    for src in glob.glob(path + "/**/*.rst", recursive=True):
        if src.endswith("glossary.rst"):
            continue
        with open(src, "r") as out:
            for term in re.findall(":term:`([^`]+)`", out.read()):
                item = glossary.term_to_item[term]
                document_terms[item.uid] = item


class _GlossaryMapper(ItemMapper):
    def __init__(self, item: Item, document_terms: ItemMap):
        super().__init__(item)
        self._document_terms = document_terms

    def get_value(self, ctx: ItemGetValueContext) -> Any:
        """ Recursively adds glossary terms to the document terms. """
        if ctx.type_path_key == "glossary/term:/term":
            if ctx.item.uid not in self._document_terms:
                self._document_terms[ctx.item.uid] = ctx.item
                _GlossaryMapper(ctx.item, self._document_terms).substitute(
                    ctx.item["text"])
        # The value of this substitute is unused.
        return ""


def _resolve_glossary_terms(document_terms: ItemMap) -> None:
    for term in list(document_terms.values()):
        _GlossaryMapper(term, document_terms).substitute(term["text"])


def _generate_project_glossary(target: str, glossary: _Glossary) -> None:
    content = _generate_glossary_content(glossary.uid_to_item)
    content.write(target)


def _generate_document_glossary(config: dict, glossary: _Glossary) -> None:
    document_terms = {}  # type: ItemMap
    for path in config["rest-source-paths"]:
        _find_glossary_terms(path, document_terms, glossary)
    _resolve_glossary_terms(document_terms)
    content = _generate_glossary_content(document_terms)
    content.write(config["target"])


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates glossaries of terms according to the configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the glossary
                       groups and terms.
    """
    groups = {}  # type: ItemMap
    for uid, item in item_cache.all.items():
        if item.type == "glossary/group":
            groups[uid] = item

    project_glossary = _Glossary()
    for group in config["project-groups"]:
        _gather_glossary_terms(groups[group], project_glossary)

    _generate_project_glossary(config["project-target"], project_glossary)

    for document_config in config["documents"]:
        _generate_document_glossary(document_config, project_glossary)
