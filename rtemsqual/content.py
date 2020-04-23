# SPDX-License-Identifier: BSD-2-Clause
""" This module provides classes for content generation. """

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

import os
import re


class Copyright:
    """
    This class represents a copyright holder with its years of substantial
    contributions.
    """
    def __init__(self, holder):
        self._holder = holder
        self._years = set()

    def add_year(self, year: str):
        """
        Adds a year to the set of substantial contributions of this copyright
        holder.
        """
        self._years.add(year)

    def get_statement(self) -> str:
        """ Returns a copyright statement. """
        line = "Copyright (C)"
        years = sorted(self._years)
        year_count = len(years)
        if year_count == 1:
            line += " " + years[0]
        elif year_count > 1:
            line += " " + years[0] + ", " + years[-1]
        line += " " + self._holder
        return line

    def __lt__(self, other: "Copyright") -> bool:
        # pylint: disable=protected-access
        if self._years and other._years:
            self_first_year = sorted(self._years)[0]
            other_first_year = sorted(other._years)[0]
            if self_first_year == other_first_year:
                return self._holder > other._holder
            return self_first_year > other_first_year
        if self._years or other._years:
            return True
        return self._holder > other._holder


class Copyrights:
    """ This class represents a set of copyright holders. """
    def __init__(self):
        self.copyrights = {}

    def register(self, statement):
        """ Registers a copyright statement. """
        match = re.search(
            r"^\s*Copyright\s+\(C\)\s+([0-9]+),\s*([0-9]+)\s+(.+)\s*$",
            statement,
            flags=re.I,
        )
        if match:
            holder = match.group(3)
            the_copyright = self.copyrights.setdefault(holder,
                                                       Copyright(holder))
            the_copyright.add_year(match.group(1))
            the_copyright.add_year(match.group(2))
            return
        match = re.search(
            r"^\s*Copyright\s+\(C\)\s+([0-9]+)\s+(.+)\s*$",
            statement,
            flags=re.I,
        )
        if match:
            holder = match.group(2)
            the_copyright = self.copyrights.setdefault(holder,
                                                       Copyright(holder))
            the_copyright.add_year(match.group(1))
            return
        match = re.search(r"^\s*Copyright\s+\(C\)\s+(.+)\s*$",
                          statement,
                          flags=re.I)
        if match:
            holder = match.group(1)
            self.copyrights.setdefault(holder, Copyright(holder))
            return
        raise ValueError(statement)

    def get_statements(self):
        """ Returns all registered copyright statements as a sorted list. """
        statements = []
        for the_copyright in sorted(self.copyrights.values()):
            statements.append(the_copyright.get_statement())
        return statements


def _make_lines(lines):
    if not isinstance(lines, list):
        return lines.strip("\n").split("\n")
    return lines


def _make_list(value):
    if not isinstance(value, list):
        return [value]
    return value


class Content:
    """ This class builds content. """
    def __init__(self, the_license):
        self._content = ""
        self._license = the_license
        self._copyrights = Copyrights()

    @property
    def content(self):
        """ Returns the content. """
        return self._content

    def register_license(self, the_license):
        """ Registers a licence for the content. """
        licenses = re.split(r"\s+OR\s+", the_license)
        if self._license not in licenses:
            raise ValueError(the_license)

    def register_copyright(self, statement):
        """ Registers a copyright statement for the content. """
        self._copyrights.register(statement)

    def write(self, path):
        """ Writes the content to the file specified by the path. """
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w+") as out:
            out.write(self._content)


class SphinxContent(Content):
    """ This class builds Sphinx content. """
    def __init__(self):
        super().__init__("CC-BY-SA-4.0")

    def add_label(self, label):
        """ Adds a label to the content. """
        self._content += ".. _" + label.strip() + ":\n"

    def add_header(self, name, level="="):
        """ Adds a header to the content. """
        name = name.strip()
        self._content += name + "\n" + level * len(name) + "\n"

    def add_blank_line(self):
        """ Adds a blank line to the content. """
        self._content += "\n"

    def add_line(self, line, indent=0):
        """ Adds a line to the content. """
        if line:
            self._content += indent * "    " + line + "\n"
        else:
            self._content += "\n"

    def add_lines(self, lines, indent=0):
        """ Adds a lines to the content. """
        for line in _make_lines(lines):
            self.add_line(line, indent)

    def add_index_entries(self, entries):
        """ Adds a list of index entries the content. """
        first = True
        for entry in _make_list(entries):
            if first:
                first = False
                self.add_blank_line()
            self._content += ".. index:: " + entry + "\n"

    def add_definition_item(self, name, lines, indent=0):
        """ Adds a definition item the content. """
        first = True
        for line in _make_lines(lines):
            if first:
                first = False
                self.add_blank_line()
                self.add_line(name, indent)
            self.add_line(line, indent=indent + 1)

    def add_licence_and_copyrights(self):
        """
        Adds a licence and copyright block to the content according to the
        registered licenses and copyrights.
        """
        spdx = f".. SPDX-License-Identifier: {self._license}\n"
        statements = "\n.. ".join(self._copyrights.get_statements())
        if statements:
            self._content = f"{spdx}\n.. {statements}\n\n{self._content}"
        else:
            self._content = f"{spdx}\n{self._content}"


class MacroToSphinx:
    """ This class expands specification item macros to Sphinx markup. """
    def __init__(self):
        self._terms = {}

    def set_terms(self, terms):
        """ Sets the glossary of terms used for macro expansion. """
        self._terms = terms

    def substitute(self, text):
        """
        Substitutes all specification item macros contained in the text.
        """
        return re.sub(r"@@|@([a-z]+){([^}]+)}", self, text)

    def __call__(self, match):
        name = match.group(1)
        if name:
            roles = {
                "term":
                lambda x: ":term:`" + self._terms[x]["glossary-term"] + "`"
            }
            return roles[name](match.group(2))
        assert match.group(0) == "@@"
        return "@"
