# SPDX-License-Identifier: BSD-2-Clause
""" This module provides support to describe package changes. """

# Copyright (C) 2023 embedded brains GmbH & Co. KG
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
from typing import Dict, List, Set, Tuple

from rtemsspec.items import Item, ItemMapper
from rtemsspec.packagebuild import BuildItem
from rtemsspec.sphinxcontent import SphinxContent


def _issue_prologue(status: str) -> str:
    return ("When the QDP of this package version was produced, "
            f"there were the following {status} issues associated:")


def _add_issues(content: SphinxContent, issues: Set[Item], header: str,
                prologue: str, which: str) -> None:
    with content.section(header):
        if issues:
            content.add(prologue)
            rows: List[Tuple[str,
                             ...]] = [("Database", "Identifier", "Subject")]
            for item in sorted(issues):
                database = item.parent("issue-member")
                url = ItemMapper(item).substitute(database["url"])
                identifier = f"`{item['identifier']} <{url}>`_"
                subject = item["subject"].replace("`", "\\`")
                rows.append((database["name"], identifier, subject))
            content.add_grid_table(rows, [27, 14, 59])
        else:
            content.add(f"""When the QDP of this package version was produced,
there were no {which} issues associated.""")


class PackageChanges(BuildItem):
    """ Describes package changes. """

    def _get_issues(self, change: Dict[str,
                                       str]) -> Tuple[Set[Item], Set[Item]]:
        issues: Tuple[Set[Item], Set[Item]] = (set(), set())
        package_status = self.item.map(change["package-status"])
        for link in package_status.links_to_parents("issue"):
            issues[int(link["status"] == "open")].add(link.item)
        return issues

    def _get_change_list(self, section_level: int,
                         with_description: bool) -> List[SphinxContent]:
        change_list: List[SphinxContent] = []
        past_issues: Tuple[Set[Item], Set[Item]] = (set(), set())
        previous_issues: Tuple[Set[Item], Set[Item]] = (set(), set())
        for change in self["change-list"]:
            for past, previous in zip(past_issues, previous_issues):
                past.update(previous)
            content = SphinxContent(section_level=section_level)
            if with_description:
                content.add_blank_line()
                content.open_section(change["name"])
                content.add(change["description"])
            current_issues = self._get_issues(change)
            new_issues = current_issues[1].difference(previous_issues[1])
            _add_issues(content, new_issues, "New issues",
                        _issue_prologue("new"), "new")
            open_issues = current_issues[1].intersection(previous_issues[1])
            _add_issues(content, open_issues, "Open issues",
                        _issue_prologue("open"), "open")
            closed_issues = current_issues[0].difference(past_issues[0])
            _add_issues(
                content, closed_issues, "Closed issues",
                "The following issues were closed "
                "for this package version.", "closed")
            if with_description:
                content.close_section()
            change_list.insert(0, content)
            previous_issues = current_issues
        return change_list

    def get_change_list(self, section_level: int) -> str:
        """ Gets the change list using the section level. """
        change_list = self._get_change_list(section_level, True)
        return "\n".join(itertools.chain.from_iterable(change_list))

    def get_open_issues(self, section_level: int) -> str:
        """ Gets the open issues using the section level. """
        content = SphinxContent(section_level=section_level)
        _, open_issues = self._get_issues(self["change-list"][-1])
        _add_issues(content, open_issues, "Open issues",
                    _issue_prologue("open"), "open")
        return "\n".join(content)

    def get_current_changes(self) -> str:
        """ Gets the current changes. """
        return self["change-list"][-1]["description"]

    def get_current_issues(self, section_level: int) -> str:
        """ Gets the current issues using the section level. """
        change_list = self._get_change_list(section_level, False)
        return "\n".join(change_list[0])
