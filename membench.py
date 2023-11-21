#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
""" Generates a memory benchmark report. """

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

import sys
from typing import Dict, List, Optional

from rtemsspec.items import ItemCache
from rtemsspec.membench import gather_sections, generate, \
    generate_variants_table, MembenchVariant, SectionsByUID
from rtemsspec.sphinxcontent import SphinxContent, SphinxMapper
from rtemsspec.util import create_argument_parser, init_logging, load_config


def _split(value: Optional[str]) -> List[str]:
    return value.split(",") if value else []


def main() -> None:
    """ Generates a memory benchmark report. """
    parser = create_argument_parser()
    parser.add_argument(
        "builddir",
        metavar="BUILDDIR",
        nargs="+",
        help="the build directory containing the memory benchmark executables")
    parser.add_argument(
        "--enabled",
        help=("a comma separated list of enabled options used to evaluate "
              "enabled-by expressions"))
    parser.add_argument("--variants",
                        help="a comma separated list of variant names")
    args = parser.parse_args(sys.argv[1:])
    init_logging(args)
    config = load_config("config.yml")["spec"]
    config["enabled"] = _split(args.enabled)
    item_cache = ItemCache(config)
    content = SphinxContent()
    root = item_cache["/rtems/req/mem-basic"]
    table_pivots = ["/rtems/req/mem-smp-1"]
    if len(args.builddir) == 1:
        sections_by_uid = gather_sections(item_cache, args.builddir[0],
                                          "objdump", "gdb")
        generate(content, sections_by_uid, root, table_pivots,
                 SphinxMapper(root))
    else:
        names = _split(args.variants)
        assert len(names) == len(args.builddir)
        sections_by_build_label: Dict[str, Dict[str, SectionsByUID]] = {}
        variants: List[MembenchVariant] = []
        for name, builddir in zip(names, args.builddir):
            sections_by_build_label[name]["membench"] = gather_sections(
                item_cache, builddir, "objdump", "gdb")
            variants.append(MembenchVariant(name, name))
        generate_variants_table(content, sections_by_build_label, root,
                                variants)
    print(str(content))


if __name__ == "__main__":
    main()
