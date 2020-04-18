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
from typing import Dict

from rtemsqual.content import MacroToSphinx, SphinxContent
from rtemsqual.items import Item, ItemCache

ItemMap = Dict[str, Item]


def _gather_glossary_groups(item: Item, glossary_groups: ItemMap) -> None:
    for child in item.children:
        _gather_glossary_groups(child, glossary_groups)
    if item["type"] == "glossary" and item["glossary-type"] == "group":
        glossary_groups[item.uid] = item


def _gather_glossary_terms(item: Item, glossary_terms: ItemMap) -> None:
    for child in item.children:
        _gather_glossary_terms(child, glossary_terms)
    if item["type"] == "glossary" and item["glossary-type"] == "term":
        glossary_terms[item.uid] = item


def _generate_glossary_content(terms: ItemMap) -> SphinxContent:
    content = SphinxContent()
    content.add_header("Glossary", level="*")
    content.add_blank_line()
    content.add_line(".. glossary::")
    content.add_line(":sorted:", indent=1)
    macro_to_sphinx = MacroToSphinx()
    macro_to_sphinx.set_terms(terms)
    for item in sorted(terms.values(),
                       key=lambda x: x["glossary-term"].lower()):
        text = macro_to_sphinx.substitute(item["text"].strip())
        item.register_license_and_copyrights(content)
        content.add_definition_item(item["glossary-term"], text, indent=1)
    content.add_licence_and_copyrights()
    return content


def _make_glossary_term_uid(term: str) -> str:
    return ("RTEMS-GLOS-TERM-" +
            re.sub(r"[^a-zA-Z0-9]+", "", term.replace("+", "X")).upper())


def _find_glossary_terms(path: str, document_terms: ItemMap,
                         project_terms: ItemMap) -> None:
    for src in glob.glob(path + "/**/*.rst", recursive=True):
        if src.endswith("glossary.rst"):
            continue
        with open(src, "r") as out:
            for term in re.findall(":term:`([^`]+)`", out.read()):
                uid = _make_glossary_term_uid(term)
                document_terms[uid] = project_terms[uid]


def _resolve_glossary_term(document_terms: ItemMap, project_terms: ItemMap,
                           term: Item) -> None:
    for match in re.findall(r"@@|@([a-z]+){([^}]+)}", term["text"]):
        if match[1] and match[1] not in document_terms:
            new_term = project_terms[match[1]]
            document_terms[match[1]] = new_term
            _resolve_glossary_term(document_terms, project_terms, new_term)


def _resolve_glossary_terms(document_terms: ItemMap,
                            project_terms: ItemMap) -> None:
    for term in list(document_terms.values()):
        _resolve_glossary_term(document_terms, project_terms, term)


def _generate_project_glossary(target: str, project_terms: ItemMap) -> None:
    content = _generate_glossary_content(project_terms)
    content.write(target)


def _generate_document_glossary(config: dict, project_terms: ItemMap) -> None:
    document_terms = {}  # type: ItemMap
    for path in config["rest-source-paths"]:
        _find_glossary_terms(path, document_terms, project_terms)
    _resolve_glossary_terms(document_terms, project_terms)
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
    for item in item_cache.top_level.values():
        _gather_glossary_groups(item, groups)

    project_terms = {}  # type: ItemMap
    for group in config["project-groups"]:
        _gather_glossary_terms(groups[group], project_terms)

    _generate_project_glossary(config["project-target"], project_terms)

    for document_config in config["documents"]:
        _generate_document_glossary(document_config, project_terms)
