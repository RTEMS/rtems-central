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

import rtemsspec


def main() -> None:
    """ Generates files of the modules from the specification. """
    config = rtemsspec.util.load_config("config.yml")
    item_cache = rtemsspec.items.ItemCache(config["spec"])
    rtemsspec.interface.generate(config["interface"], item_cache)
    rtemsspec.validation.generate(config["validation"], item_cache)
    rtemsspec.applconfig.generate(config["appl-config"], item_cache)
    rtemsspec.specdoc.document(config["spec-documentation"], item_cache)
    rtemsspec.glossary.generate(config["glossary"], item_cache)
    rtemsspec.interfacedoc.generate(config["interface-documentation"],
                                    item_cache)


if __name__ == "__main__":
    main()
