# SPDX-License-Identifier: BSD-2-Clause
""" This module provides support to build the package manual. """

# Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
# Copyright (C) 2021 EDISOFT (https://www.edisoft.pt/)
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

import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from rtemsspec.items import Item, ItemGetValueContext
from rtemsspec.archiver import Archiver
from rtemsspec.content import BSD_2_CLAUSE_LICENSE, Copyrights
from rtemsspec.directorystate import DirectoryState
from rtemsspec.membench import generate, generate_variants_table, \
    MembenchVariant
from rtemsspec.packagebuild import PackageBuildDirector
from rtemsspec.packagechanges import PackageChanges
from rtemsspec.rtems import gather_api_items
from rtemsspec.sphinxcontent import SphinxContent, SphinxMapper
from rtemsspec.sphinxbuilder import SphinxBuilder
from rtemsspec.util import base64_to_hex, run_command

_Measurements = Dict[str, Dict[str, Tuple[float, float, float]]]


def _run_pkg_config(content: SphinxContent, cmd: List[str]) -> None:
    cmd = ["pkg-config"] + cmd
    content.add(f"$$ {' '.join(cmd)}")
    stdout: List[str] = []
    status = run_command(cmd, stdout=stdout)
    assert status == 0
    content.append(stdout)


def _format_digest(digest: Optional[str]) -> str:
    assert digest is not None
    return "\u200b".join(iter(base64_to_hex(digest)))


def _format_line(line: str) -> str:
    line = line.rstrip("\r\n").replace("\t", "        ")
    return f"\u200b{line}"


def _format_path(path: str) -> str:
    for char in "/-_.":
        path = path.replace(char, f"{char}\u200b")
    return path


def _make_code_block(code: List[str]) -> str:
    content = SphinxContent()
    for line in range(0, len(code), 100):
        with content.directive("code-block", value="none"):
            content.add([_format_line(line) for line in code[line:line + 100]])
    return "\n".join(content)


def _make_targets(targets: str) -> List[str]:
    if targets:
        return targets.split(" ")
    return []


def _gather_runtime_performance_items(items: Set[Item], item: Item) -> None:
    if item.type == "requirement/non-functional/performance-runtime":
        items.add(item)
    for child in item.children("requirement-refinement"):
        _gather_runtime_performance_items(items, child)


def _environment_order(name: str) -> int:
    if name == "HotCache":
        return 0
    if name == "FullCache":
        return 1
    if name == "DirtyCache":
        return 2
    return int(name[5:]) + 2


def _add_licenses(content: SphinxContent, deployment_directory: str,
                  member: DirectoryState, bsd_2_clause: Copyrights) -> None:
    copyrights_by_license = member["copyrights-by-license"]
    files = copyrights_by_license.get("files", None)
    if files is not None:
        directory = os.path.relpath(member.directory, deployment_directory)
        with content.section(f"Directory - {directory}"):
            content.add(copyrights_by_license.get("description", None))
            for name in files:
                with content.section(f"File - {name}"):
                    content.add(f"""The license file
:file:`{_format_path(os.path.join(directory, name))}`
is applicable to this directory or parts of the directory:""")
                    content.add_blank_line()
                    file_path = os.path.join(member.directory, name)
                    with open(file_path, "r", encoding="utf-8") as src:
                        content.add(_make_code_block(src.readlines()))
    bsd_2_clause.register(copyrights_by_license.get("BSD-2-Clause", []))


class PackageManualBuilder(SphinxBuilder):
    """ Builds the package user manual. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._membench: Dict[str, Any] = {}
        my_type = self.item.type
        self.mapper.add_get_value(f"{my_type}:/archive-file",
                                  self._get_archive_file)
        self.mapper.add_get_value(f"{my_type}:/archive-sha512",
                                  self._get_archive_sha512)
        self.mapper.add_get_value(f"{my_type}:/benchmark-variants-list",
                                  self._get_benchmark_variants_list)
        self.mapper.add_get_value(f"{my_type}:/memory-benchmarks",
                                  self._get_membench)
        self.mapper.add_get_value(f"{my_type}:/memory-benchmark-section",
                                  self._get_membench_section)
        self.mapper.add_get_value(
            f"{my_type}:/memory-benchmark-compare-section",
            self._get_membench_compare_section)
        self.mapper.add_get_value(
            f"{my_type}:/memory-benchmark-variants-table",
            self._get_membench_variants_table)
        self.mapper.add_get_value(f"{my_type}:/performance-variants-table",
                                  self._get_performance_variants_table)
        self.mapper.add_get_value(f"{my_type}:/pkg-config",
                                  self._get_pkg_config)
        self.mapper.add_get_value(f"{my_type}:/pre-qualified-interfaces",
                                  self._get_pre_qualified_interfaces)
        self.mapper.add_get_value(f"{my_type}:/repositories", self._get_repos)
        self.mapper.add_get_value(f"{my_type}:/verify-package-file",
                                  self._get_verify_pkg_file)
        self.mapper.add_get_value(f"{my_type}:/verify-package-help",
                                  self._get_verify_pkg_help)
        self.mapper.add_get_value(f"{my_type}:/verify-package-sha512",
                                  self._get_verify_pkg_sha512)
        self.mapper.add_get_value(f"{my_type}:/change-list",
                                  self._get_change_list)
        self.mapper.add_get_value(f"{my_type}:/open-issues",
                                  self._get_open_issues)
        self.mapper.add_get_value(f"{my_type}:/license-info",
                                  self._get_license_info)
        self.mapper.add_get_value(f"{my_type}:/targets", self._get_targets)
        for name in [my_type, "qdp/sphinx-section"]:
            self.mapper.add_get_value(f"{name}:/make", self._get_make)
            self.mapper.add_get_value(f"{name}:/object-size",
                                      self._get_object_size)

    def run(self) -> None:
        membench = self.input("membench-results")
        assert isinstance(membench, DirectoryState)
        self._membench = membench.json_load()
        super().run()

    def _get_archive_file(self, _ctx: ItemGetValueContext) -> Any:
        archive = self.input("archive")
        assert isinstance(archive, DirectoryState)
        return os.path.basename(archive.file)

    def _get_archive_sha512(self, _ctx: ItemGetValueContext) -> Any:
        archive = self.input("archive")
        assert isinstance(archive, DirectoryState)
        _, digest = next(archive.files_and_hashes())
        return _format_digest(digest)

    def _get_make(self, ctx: ItemGetValueContext) -> Any:
        assert ctx.args
        dirs, make_args = ctx.args.split(" ", 1)
        make_list = make_args.split(",")
        cwd = self.substitute("${/qdp/variant:/deployment-directory}/") + dirs
        for targets in make_list[:-1]:
            status = run_command(["make"] + _make_targets(targets), cwd=cwd)
            assert status == 0
        stdout: List[str] = []
        status = run_command(["make"] + _make_targets(make_list[-1]),
                             cwd=cwd,
                             stdout=stdout)
        assert status == 0
        return _make_code_block(stdout)

    def _get_benchmark_variants_list(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            for variant in self["benchmark-variants"]:
                content.add_definition_item(variant["name"],
                                            variant["description"])
            return "\n".join(content)

    def _get_membench(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            label = self["memory-benchmark-build-label"]
            sections_by_uid = self._membench[label]["membench"]
            root = self.item.cache["/rtems/req/mem-basic"]
            table_pivots = ["/rtems/req/mem-smp-1"]
            generate(content, sections_by_uid, root, table_pivots,
                     SphinxMapper(root))
            return "\n".join(content)

    def _get_membench_section(self, ctx: ItemGetValueContext) -> Any:
        assert ctx.args
        uid, section = ctx.args.split(":")
        item = self.item.cache[uid]
        label = self["memory-benchmark-build-label"]
        sections = self._membench[label]["membench"][item.uid]
        return str(sections[section])

    def _get_membench_compare_section(self, ctx: ItemGetValueContext) -> Any:
        assert ctx.args
        uid, other_uid, section = ctx.args.split(":")
        item = self.item.cache[uid]
        label = self["memory-benchmark-build-label"]
        sections = self._membench[label]["membench"][item.uid]
        other_item = self.item.cache[other_uid]
        other_sections = self._membench[label]["membench"][other_item.uid]
        return f"{other_sections[section] - sections[section]:+}"

    def _get_membench_variants_table(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            root = self.item.cache["/rtems/req/mem-basic"]
            variants: List[MembenchVariant] = []
            for variant in self["benchmark-variants"]:
                variant_label = variant["build-label"]
                if variant_label not in self._membench:
                    continue
                variants.append(MembenchVariant(variant["name"],
                                                variant_label))
            generate_variants_table(content, self._membench, root, variants)
            return "\n".join(content)

    def _get_measurements_by_variant(self) -> Dict[int, _Measurements]:
        measurements_by_variant: Dict[int, _Measurements] = {}
        for index, variant in enumerate(self["benchmark-variants"]):
            test_log = self.director[self.item.to_abs_uid(
                variant["test-log-uid"])]
            measurements: _Measurements = {}
            if not test_log.item.enabled:
                if index == 0:
                    break
                measurements_by_variant[index] = measurements
                continue
            assert isinstance(test_log, DirectoryState)
            with open(test_log.file, "r", encoding="utf-8") as src:
                data = json.load(src)
            for report in data["reports"]:
                for test_case in report.get("test-suite",
                                            {}).get("test-cases", []):
                    for measurement in test_case["runtime-measurements"]:
                        stats = (measurement["min"], measurement["q2"],
                                 measurement["max"])
                        measurements.setdefault(
                            measurement["name"],
                            {})[measurement["variant"]] = stats
            measurements_by_variant[index] = measurements
        return measurements_by_variant

    def _make_performance_variants_rows(
        self, item: Item, envs: List[str], env_links: Dict[str, str],
        measurements_by_variant: Dict[int, _Measurements]
    ) -> List[Tuple[str, ...]]:
        rows: List[Tuple[str, ...]] = []
        info_spec = item.spec
        for env in envs:
            env_link = env_links[env.split("/")[0]]
            info_env = f"`{env} <{env_link}>`__"
            for index, variant in enumerate(self["benchmark-variants"]):
                stats = measurements_by_variant[index].get(item.ident,
                                                           {}).get(env, None)
                info = (info_spec, info_env, variant["name"])
                if index == 0:
                    assert stats
                    base = stats
                    rows.append(info + tuple(f"{value * 1e6:.3f}"
                                             for value in stats))
                elif stats:
                    rows.append(info + tuple(
                        f"{(value - base[j]) / base[j] * 100.0:+.3g} %"
                        for j, value in enumerate(stats)))
                else:
                    rows.append(info + ("?", "?", "?"))
                info_spec = ""
                info_env = ""
        return rows

    def _get_performance_variants_table(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, _):
            measurements_by_variant = self._get_measurements_by_variant()
            if not measurements_by_variant:
                return "There is no performance variants table available."
            items: Set[Item] = set()
            _gather_runtime_performance_items(items,
                                              self.item.cache["/req/root"])
            envs = list(measurements_by_variant[0][next(
                iter(items)).ident].keys())
            envs.sort(key=_environment_order)
            req_path = self.substitute(
                "${/qdp/variant:/deployment-directory}/doc/ts/srs/"
                "html/requirements.html#spec-req-perf-runtime-environment-")
            env_links = {
                "HotCache": f"{req_path}hot-cache",
                "FullCache": f"{req_path}full-cache",
                "DirtyCache": f"{req_path}dirty-cache",
                "Load": f"{req_path}load"
            }
            rows: List[Tuple[str, ...]] = [
                ("Specification", "Environment", "Variant", "Min [μs]",
                 "Median [μs]", "Max [μs]")
            ]
            for item in sorted(items):
                rows.extend(
                    self._make_performance_variants_rows(
                        item, envs, env_links, measurements_by_variant))
            content = SphinxContent(section_level=section_level)
            with content.latex_tiny("scriptsize"):
                content.add_grid_table(rows, [31, 14, 19, 12, 12, 12])
            return "\n".join(content)

    def _get_pkg_config(self, _ctx: ItemGetValueContext) -> Any:
        pkg = self.substitute(
            "${/qdp/variant:/deployment-directory}/lib/pkgconfig/"
            "${/qdp/variant:/arch}-rtems${/qdp/variant:/rtems-version}-"
            "${/qdp/variant:/bsp}-qual-only.pc")
        content = SphinxContent()
        with content.directive("code-block", value="none"):
            _run_pkg_config(content, ["--variable=ABI_FLAGS", pkg])
            _run_pkg_config(content, ["--cflags", pkg])
            _run_pkg_config(content, ["--libs", pkg])
        return "\n".join(content)

    def _get_pre_qualified_interfaces(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            items: Dict[str, List[Item]] = {}
            gather_api_items(self.item.cache, items)
            for group, group_items in sorted(items.items()):
                with content.section(group):
                    content.add_list(item["name"] for item in group_items)
            return "\n".join(content)

    def _get_repos(self, ctx: ItemGetValueContext) -> Any:
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            variant = self.item.map("/qdp/variant")
            prefix = self.substitute("${/qdp/variant:/deployment-directory}")
            for item in variant.children("repository"):
                step = self.director[item.uid]
                origin_branch = step["origin-branch"]
                origin_commit = step["origin-commit"]
                if origin_branch and origin_commit:
                    dest = os.path.relpath(step["directory"], prefix)
                    with content.section(f"Git Repository: {dest}"):
                        content.add(step["description"])
                        content.add(f"""The ``{step["branch"]}`` branch with
commit ``{step["commit"]}``
was used to build the QDP.  This branch is checked out after unpacking the
archive.  It is based on
commit `{origin_commit} <{step['origin-commit-url']}>`_
of the ``{origin_branch}`` branch of the ``origin`` remote repository.""")
            return "\n".join(content)

    def _get_object_size(self, ctx: ItemGetValueContext) -> Any:
        assert ctx.args
        label = self["memory-benchmark-build-label"]
        return str(self._membench[label]["object-sizes"][ctx.args])

    def _get_verify_pkg_file(self, _ctx: ItemGetValueContext) -> Any:
        verify_package = self.input("verify-package")
        assert isinstance(verify_package, DirectoryState)
        return os.path.basename(verify_package.file)

    def _get_verify_pkg_help(self, _ctx: ItemGetValueContext) -> Any:
        content = SphinxContent()
        with content.directive("code-block", value="none"):
            verify_package = self.input("verify-package")
            assert isinstance(verify_package, DirectoryState)
            cmd = [verify_package.file, "--help"]
            content.add([
                f"$$ cd {os.path.dirname(cmd[0])}",
                f"$$ ./{os.path.basename(cmd[0])} --help"
            ])
            stdout: List[str] = []
            status = run_command(cmd, stdout=stdout)
            assert status == 0
            content.append(stdout)
        return "\n".join(content)

    def _get_verify_pkg_sha512(self, _ctx: ItemGetValueContext) -> Any:
        verify_package = self.input("verify-package")
        assert isinstance(verify_package, DirectoryState)
        _, digest = next(verify_package.files_and_hashes())
        return _format_digest(digest)

    def _get_change_list(self, ctx: ItemGetValueContext) -> str:
        with self.section_level(ctx) as (section_level, _):
            changes = self.input("package-changes")
            assert isinstance(changes, PackageChanges)
            return changes.get_change_list(section_level)

    def _get_open_issues(self, ctx: ItemGetValueContext) -> str:
        with self.section_level(ctx) as (section_level, _):
            changes = self.input("package-changes")
            assert isinstance(changes, PackageChanges)
            return changes.get_open_issues(section_level)

    def _get_license_info(self, ctx: ItemGetValueContext) -> str:
        archive = self.input("archive")
        assert isinstance(archive, DirectoryState)
        archiver = self.director[archive.item.child("output").uid]
        assert isinstance(archiver, Archiver)
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            bsd_2_clause = Copyrights()
            deployment_directory = self.substitute(
                "${/qdp/variant:/deployment-directory}")
            content.add(f"""All directories and file paths in this section are
relative to :file:`{_format_path(deployment_directory)}`.""")
            for member in archiver.inputs("member"):
                assert isinstance(member, DirectoryState)
                _add_licenses(content, deployment_directory, member,
                              bsd_2_clause)
            if bsd_2_clause:
                with content.section("BSD-2-Clause copyrights"):
                    content.add(bsd_2_clause.get_statements("| ©"))
                    content.add(
                        _make_code_block(BSD_2_CLAUSE_LICENSE.split("\n")))
            return "\n".join(content)

    def _get_targets(self, ctx: ItemGetValueContext) -> str:
        with self.section_level(ctx) as (section_level, _):
            content = SphinxContent(section_level=section_level)
            for target in sorted(
                    self.item.cache.items_by_type.get(
                        "requirement/non-functional/design-target", [])):
                if not target.enabled:
                    continue
                with content.section(target["name"]):
                    content.add(target["brief"])
                    content.add(target["description"])
            return "\n".join(content)
