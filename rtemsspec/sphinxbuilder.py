# SPDX-License-Identifier: BSD-2-Clause
""" Contains the SphinxBuilder class. """

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

from contextlib import contextmanager
import logging
import os
import re
import shutil
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
import yaml

from rtemsspec.content import BSD_2_CLAUSE_LICENSE, Copyrights
from rtemsspec.directorystate import DirectoryState
from rtemsspec.packagebuild import BuildItem, BuildItemFactory, \
    PackageBuildDirector
from rtemsspec.items import is_enabled, Item, ItemGetValueContext, Link
from rtemsspec import glossary
from rtemsspec.sphinxcontent import SphinxContent
from rtemsspec.util import run_command

_BREAK = "\\break"

_PUSH_ENABLED_BY = re.compile(r"^\${\.:/push-enabled-by:(.+)}$")

_POP_ENABLED_BY = re.compile(r"^\${\.:/pop-enabled-by")

_RST_HEADERS = re.compile(
    r"^\.\. SPDX-License-Identifier: (.+)\n\n((\.\. Copyright \(C\).*\n)+)\n",
    flags=re.MULTILINE)


def _get_normal_title(ctx: ItemGetValueContext) -> Any:
    return ctx.item["document-title"].replace(_BREAK, " ")


def _get_sphinx_title(ctx: ItemGetValueContext) -> Any:
    content = SphinxContent()
    content.add_header(_get_normal_title(ctx), level=1)
    return "\n".join(content.lines)


def _get_release(ctx: ItemGetValueContext) -> Any:
    return str(len(ctx.item["document-releases"]))


def _no_action(_component: Dict[str, Any]) -> None:
    pass


def _sep(seps: Tuple[str, ...], maxi: Tuple[int, ...]) -> str:
    return "+" + "+".join(f"{sep * (val + 2)}"
                          for sep, val in zip(seps, maxi)) + "+"


def _row(row: Tuple[str, ...], maxi: Tuple[int, ...]) -> str:
    return "|" + "|".join(f" {cell:{width}} "
                          for cell, width in zip(row, maxi)) + "|"


def _get_contributors(ctx: ItemGetValueContext) -> Any:
    rows = [("Action", "Name", "Organization", "Signature")]
    maxi = tuple(map(len, rows[0]))
    for action in ctx.item["document-contributors"]:
        for contributor in action["contributors"]:
            row = (action["action"], contributor["name"],
                   contributor["organization"], "")
            rows.append(row)
            row_lengths = tuple(map(len, row))
            maxi = tuple(map(max, zip(maxi, row_lengths)))
    sep_0 = _sep(("-", "-", "-", "-"), maxi)
    sep_1 = _sep(("=", "=", "=", "="), maxi)
    sep_2 = _sep((" ", "-", "-", "-"), maxi)
    lines = [sep_0, _row(rows[0], maxi)]
    last_action = rows[0][0]
    for row in rows[1:]:
        if last_action == "Action":
            lines.append(sep_1)
            last_action = row[0]
        elif last_action == row[0]:
            lines.append(sep_2)
            row = ("", row[1], row[2], row[3])
        else:
            lines.append(sep_0)
            last_action = row[0]
        lines.append(_row(row, maxi))
    lines.append(sep_0)
    content = SphinxContent()
    with content.directive(
            "table", options=[":class: longtable", ":widths: 16 26 30 28"]):
        content.add(lines)
    return "\n".join(content.lines)


def _latex_escape(value: str) -> str:
    return value.replace("_", "\\_").replace("&", "\\&")


_COPYRIGHT = re.compile(r"^\s*Copyright\s+\(C\)\s+", re.IGNORECASE)
_YEARS = re.compile(r"^[0-9, ]*")


def _get_document_copyright(ctx: ItemGetValueContext) -> Any:
    copyrights = ctx.item["document-copyrights"]
    main = _COPYRIGHT.sub("", copyrights[0])
    if len(copyrights) == 1:
        return main
    return f"{main} and contributors"


def _get_document_author(ctx: ItemGetValueContext) -> Any:
    return _YEARS.sub("", _get_document_copyright(ctx))


def _get_document_year(ctx: ItemGetValueContext) -> Any:
    match = _YEARS.search(_get_document_copyright(ctx))
    assert match
    return match.group(0).split(",")[-1]


class SphinxBuilder(BuildItem):
    """ Base class for Sphinx document builds. """

    # pylint: disable=too-many-instance-attributes
    @classmethod
    def prepare_factory(cls, factory: BuildItemFactory,
                        type_name: str) -> None:
        BuildItem.prepare_factory(factory, type_name)
        factory.add_get_value(f"{type_name}:/document-release", _get_release)
        factory.add_get_value(f"{type_name}:/document-year",
                              _get_document_year)

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        source = self.input("source")
        assert isinstance(source, DirectoryState)

        build = self.output("build")
        assert isinstance(build, DirectoryState)

        self._index: List[str] = []
        self._section_level = 2
        self.source_dir = source.directory
        self.build_dir = build.directory
        self.file_path = self.build_dir
        my_type = self.item.type
        self.mapper.add_get_value(f"{my_type}:/document-author",
                                  _get_document_author)
        self.mapper.add_get_value(f"{my_type}:/document-contract-html",
                                  self._get_contract_html)
        self.mapper.add_get_value(f"{my_type}:/document-contract-latex",
                                  self._get_contract_latex)
        self.mapper.add_get_value(f"{my_type}:/document-copyright",
                                  _get_document_copyright)
        self.mapper.add_get_value(f"{my_type}:/document-copyrights",
                                  self._get_document_copyrights)
        self.mapper.add_get_value(
            f"{my_type}:/document-bsd-2-clause-copyrights",
            self._get_document_bsd_2_clause_copyrights)
        self.mapper.add_get_value(f"{my_type}:/document-normal-title",
                                  _get_normal_title)
        self.mapper.add_get_value(f"{my_type}:/document-latex-copyright",
                                  self._get_latex_copyright)
        self.mapper.add_get_value(f"{my_type}:/document-latex-title",
                                  self._get_latex_title)
        self.mapper.add_get_value(f"{my_type}:/document-title-page-title",
                                  self._get_title_page_title)
        self.mapper.add_get_value(f"{my_type}:/document-sphinx-title",
                                  _get_sphinx_title)
        self.mapper.add_get_value(f"{my_type}:/document-index",
                                  self._get_index)
        self.mapper.add_get_value(f"{my_type}:/document-releases",
                                  self._get_releases)
        self.mapper.add_get_value(f"{my_type}:/document-contributors",
                                  _get_contributors)
        for name in [my_type, "qdp/sphinx-section"]:
            self.mapper.add_get_value(f"{name}:/sections", self._get_sections)
        self._actions = {
            "add-to-index": _no_action,
            "copy": self._copy,
            "copy-and-substitute": self._copy_and_substitute,
            "copy-files": self._copy_files,
            "glossary": self._glossary
        }

    def run(self) -> None:
        self.mapper.copyrights_by_license.clear()

        destination = self.output("destination")
        assert isinstance(destination, DirectoryState)
        destination.clear()

        os.makedirs(os.path.join(self.build_dir, "source"), exist_ok=True)
        status = run_command(
            ["python3", "-msphinx", "-M", "clean", "source", "build"],
            self.build_dir)
        assert status == 0
        enabled_set = self.enabled_set
        for component in self["document-components"]:
            if is_enabled(enabled_set, component.get("enabled-by", True)):
                self.file_path = os.path.join(
                    self.build_dir, component.get("destination", "."))
                self._actions[component["action"]](component)
                self._add_to_index(component)
        output = self["output-pdf"]
        if output:
            status = run_command(
                ["python3", "-msphinx", "-M", "latexpdf", "source", "build"],
                self.build_dir)
            assert status == 0
            src_path = os.path.join(self.build_dir, "build", "latex",
                                    "document.pdf")
            destination.copy_file(src_path, output)
        output = self["output-html"]
        if output:
            status = run_command(
                ["python3", "-msphinx", "-M", "html", "source", "build"],
                self.build_dir)
            assert status == 0
            src_path = os.path.join(self.build_dir, "build", "html")
            destination.copy_tree(src_path, output)

        my_license = self["document-license"]
        destination["copyrights-by-license"] = dict(
            (key, value.get_statements())
            for key, value in self._get_copyrights().items()
            if key != my_license)

    def add_component_action(self, name: str,
                             action: Callable[[Dict[str, Any]], None]) -> None:
        """ Adds a component action. """
        self._actions[name] = action

    def _get_releases(self, ctx: ItemGetValueContext) -> Any:
        content = SphinxContent()
        releases = ctx.item["document-releases"]
        count = len(releases)
        for idx, release in enumerate(reversed(releases)):
            date = release["date"]
            status = release["status"]
            line = f"Release: {count - idx}, Date: {date}, Status: {status}"
            with content.directive("topic", line):
                lines = self._push_pop_enabled_by(
                    release["changes"].splitlines())
                content.add(self.mapper.substitute("\n".join(lines), ctx.item))
        return "\n".join(content.lines)

    def _add_to_index(self, component: Dict[str, Any]) -> None:
        if component.get("add-to-index", False):
            self._index.append(
                os.path.basename(component["destination"]).replace(".rst", ""))

    def _get_index(self, ctx: ItemGetValueContext) -> Any:
        content = SphinxContent()
        maxdepth = f":maxdepth: {ctx.item['document-toctree-maxdepth']}"
        with content.directive("toctree", options=[maxdepth, ":numbered:"]):
            content.add(self._index)
        return "\n".join(content.lines)

    def _get_contract_html(self, ctx: ItemGetValueContext) -> Any:
        contract = self.mapper.substitute(ctx.item["document-contract"])
        dot = ". " if contract else ""
        return f"{dot}{contract.replace(_BREAK, ' ')}"

    def _get_contract_latex(self, ctx: ItemGetValueContext) -> Any:
        return _latex_escape(
            self.mapper.substitute(ctx.item["document-contract"]).replace(
                _BREAK, " \\vspace{-4pt} \\break "))

    def _get_latex_copyright(self, ctx: ItemGetValueContext) -> Any:
        return _latex_escape(
            self.mapper.substitute(_get_document_copyright(ctx)))

    def _get_copyrights(self) -> Dict[str, Copyrights]:
        my_license = self["document-license"]
        copyrights: Dict[str, Copyrights] = {}
        copyrights.setdefault(my_license, Copyrights()).register(
            self["document-copyrights"])
        license_map = self["document-license-map"]
        for key, value in self.mapper.copyrights_by_license.items():
            the_license = license_map.get(key, key)
            copyrights.setdefault(the_license, Copyrights()).register(value)
        return copyrights

    def _get_document_copyrights(self, ctx: ItemGetValueContext) -> Any:
        my_license = self["document-license"]
        assert " OR " not in my_license
        copyrights = self._get_copyrights()
        prefix = ctx.args if ctx.args else ""
        return "\n".join(copyrights[my_license].get_statements(f"{prefix}| ©"))

    def _get_document_bsd_2_clause_copyrights(
            self, _ctx: ItemGetValueContext) -> Any:
        copyrights = self._get_copyrights()
        the_license = "BSD-2-Clause"
        if the_license not in copyrights:
            return ""
        statements = "\n".join(copyrights[the_license].get_statements("| ©"))
        return f"""{statements}

{BSD_2_CLAUSE_LICENSE}"""

    def _get_latex_title(self, ctx: ItemGetValueContext) -> Any:
        return _latex_escape(
            self.mapper.substitute(ctx.item["document-title"].replace(
                _BREAK, " ")))

    def _get_title_page_title(self, ctx: ItemGetValueContext) -> Any:
        return _latex_escape(
            self.mapper.substitute(ctx.item["document-title"].replace(
                _BREAK, " \\break \\break ")))

    @contextmanager
    def section_level(
            self,
            ctx: ItemGetValueContext) -> Iterator[Tuple[int, Optional[str]]]:
        """ Opens a section level with optional additional arguments. """
        if ctx.args:
            colon = ctx.args.find(":")
            if colon >= 0:
                level_change = int(ctx.args[:colon])
                args: Optional[str] = ctx.args[colon + 1:]
            else:
                level_change = int(ctx.args)
                args = None
        else:
            level_change = 1
            args = None
        section_level = self._section_level
        new_section_level = section_level + level_change
        self._section_level = new_section_level
        yield new_section_level, args
        self._section_level = section_level

    def _get_sections(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, args):
            assert args
            content = SphinxContent(section_level)
            build_item = self.director[ctx.item.uid]
            for section in build_item.inputs(args):
                with content.section(section.item["header"],
                                     label=section.item["label"]):
                    content.add(section.item["content"].strip())
        return "\n".join(content.lines)

    def _register_text_copyrights(self, text: str) -> None:
        match = _RST_HEADERS.match(text)
        assert match
        the_license = match.group(1)
        statements = [
            statement[3:] for statement in match.group(2).split("\n")[:-1]
        ]
        logging.info("%s: register license %s with copyrights %s", self.uid,
                     the_license, statements)
        self.mapper.copyrights_by_license.setdefault(the_license,
                                                     set()).update(statements)

    def _do_copy(self, src_file: str, dst_file: str) -> None:
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        if dst_file.endswith(".rst"):
            logging.info("%s: read: %s", self.uid, src_file)
            with open(src_file, "r", encoding="utf-8") as src:
                text = src.read()
                self._register_text_copyrights(text)
                logging.info("%s: write: %s", self.uid, dst_file)
                with open(dst_file, "w+", encoding="utf-8") as dst:
                    dst.write(text)
        else:
            logging.info("%s: copy '%s' to '%s'", self.uid, src_file, dst_file)
            shutil.copy2(src_file, dst_file)

    def _copy(self, component: Dict[str, Any]) -> None:
        self._do_copy(os.path.join(self.source_dir, component["source"]),
                      os.path.join(self.build_dir, component["destination"]))

    def _push_pop_enabled_by(self, lines: List[str]) -> List[str]:
        filtered_lines: List[str] = []
        enabled: List[bool] = [True]
        for line in lines:
            push_match = _PUSH_ENABLED_BY.search(line)
            if push_match is not None:
                data = push_match.group(1)
                enabled_by = yaml.load(data, yaml.SafeLoader)
                enabled.append(enabled[-1]
                               and is_enabled(self.enabled_set, enabled_by))
                continue
            if _POP_ENABLED_BY.search(line) is not None:
                enabled.pop()
            elif enabled[-1]:
                filtered_lines.append(line)
        return filtered_lines

    def _copy_and_substitute(self, component: Dict[str, Any]) -> None:
        src_path = os.path.join(self.source_dir, component["source"])
        dst_path = os.path.join(self.build_dir, component["destination"])
        logging.info("%s: read: %s", self.uid, src_path)
        with open(src_path, "r", encoding="utf-8") as src:
            logging.info("%s: process push/pop enabled by", self.uid)
            text = "".join(self._push_pop_enabled_by(src.readlines()))
            if dst_path.endswith(".rst"):
                self._register_text_copyrights(text)
            logging.info("%s: substitute", self.uid)
            text = self.mapper.substitute(text)
            logging.info("%s: write: %s", self.uid, dst_path)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            with open(dst_path, "w+", encoding="utf-8") as dst:
                dst.write(text)

    def _copy_files(self, component: Dict[str, Any]) -> None:
        src_dir = os.path.join(self.source_dir, component["source"])
        dst_dir = os.path.join(self.build_dir, component["destination"])
        for a_file in component["files"]:
            self._do_copy(os.path.join(src_dir, a_file),
                          os.path.join(dst_dir, a_file))

    def _glossary(self, component: Dict[str, Any]) -> None:
        config = {
            "project-groups":
            component["glossary-groups"],
            "project-header":
            None,
            "project-target":
            None,
            "documents": [{
                "header":
                "Terms, definitions and abbreviated terms",
                "rest-source-paths": [
                    str(os.path.join(self.build_dir, "source")),
                    str(os.path.join(self.build_dir, "include"))
                ],
                "target":
                str(os.path.join(self.build_dir, component["destination"])),
            }]
        }
        glossary.generate(config, self.item.cache, self.mapper)


class SphinxSection(BuildItem):
    """ This class represents a Sphinx section. """

    def has_changed(self, link: Link) -> bool:
        if self.is_build_necessary():
            return True
        return super().has_changed(link)
