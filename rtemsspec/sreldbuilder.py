# SPDX-License-Identifier: BSD-2-Clause
""" Builds the software release document (SRelD). """

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

from rtemsspec.items import Item, ItemGetValueContext
from rtemsspec.packagebuild import PackageBuildDirector
from rtemsspec.packagechanges import PackageChanges
from rtemsspec.sphinxbuilder import SphinxBuilder


class SRelDBuilder(SphinxBuilder):
    """ Builds the software release document (SRelD). """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        my_type = self.item.type
        self.mapper.add_get_value(f"{my_type}:/changes", self._get_changes)
        self.mapper.add_get_value(f"{my_type}:/issues", self._get_issues)

    def _get_changes(self, _ctx: ItemGetValueContext) -> str:
        changes = self.input("package-changes")
        assert isinstance(changes, PackageChanges)
        return changes.get_current_changes()

    def _get_issues(self, ctx: ItemGetValueContext) -> str:
        with self.section_level(ctx) as (section_level, _):
            changes = self.input("package-changes")
            assert isinstance(changes, PackageChanges)
            return changes.get_current_issues(section_level)
