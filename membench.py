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

from rtemsspec.items import ItemCache, item_is_enabled
from rtemsspec.membench import generate
from rtemsspec.sphinxcontent import SphinxContent, SphinxMapper
from rtemsspec.util import create_argument_parser, init_logging, load_config


def main() -> None:
    """ Generates a memory benchmark report. """
    parser = create_argument_parser()
    parser.add_argument(
        "builddir",
        metavar="BUILDDIR",
        nargs=1,
        help="the build directory containing the memory benchmark executables")
    args = parser.parse_args(sys.argv[1:])
    init_logging(args)
    config = load_config("config.yml")
    item_cache = ItemCache(config["spec"])
    item_cache.set_enabled([], item_is_enabled)
    content = SphinxContent()
    root = item_cache["/rtems/req/mem-basic"]
    table_pivots = ["/rtems/req/mem-basic", "/rtems/req/mem-smp-1"]
    generate(content, root, SphinxMapper(root), table_pivots, args.builddir[0])
    print(str(content))


if __name__ == "__main__":
    main()
