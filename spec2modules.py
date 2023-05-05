#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
""" Generates files of the modules from the specification. """

# Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)
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

import argparse
import difflib
import sys

import rtemsspec


def _diff(obj: rtemsspec.content.Content, path: str) -> None:
    from_file = f"a/{path}"
    to_file = f"b/{path}"
    try:
        with open(path, encoding="utf-8") as src:
            file_lines = src.read().splitlines()
    except FileNotFoundError:
        file_lines = []
    diff_lines = list(
        difflib.unified_diff(file_lines,
                             str(obj).splitlines(),
                             fromfile=from_file,
                             tofile=to_file,
                             n=3,
                             lineterm=""))
    if diff_lines:
        print(f"diff -u {from_file} {to_file}")
        print("\n".join(diff_lines))


def main() -> None:
    """ Generates files of the modules from the specification. """
    parser = argparse.ArgumentParser()
    parser.add_argument("-u",
                        "--diff",
                        action="store_true",
                        help="print the unified difference from the original"
                        " file content to the new generated content")
    parser.add_argument("targets",
                        metavar="TARGET",
                        nargs="*",
                        help="a target file of a specification item")
    args = parser.parse_args(sys.argv[1:])
    if args.diff:
        rtemsspec.content.Content.write = _diff  # type: ignore
    config = rtemsspec.util.load_config("config.yml")
    item_cache = rtemsspec.items.ItemCache(
        config["spec"], is_item_enabled=rtemsspec.items.item_is_enabled)
    rtemsspec.validation.generate(config["validation"], item_cache,
                                  args.targets)

    if not args.targets:
        group_uids = [
            doc["group"] for doc in config["interface-documentation"]["groups"]
        ]
        rtemsspec.interface.generate(config["interface"], item_cache)
        rtemsspec.applconfig.generate(config["appl-config"], group_uids,
                                      item_cache)
        rtemsspec.specdoc.document(config["spec-documentation"], item_cache)
        rtemsspec.glossary.generate(config["glossary"], group_uids, item_cache)
        rtemsspec.interfacedoc.generate(config["interface-documentation"],
                                        item_cache)


if __name__ == "__main__":
    main()
