# SPDX-License-Identifier: BSD-2-Clause
""" Unit tests for the rtemsqual.glossary module. """

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

import os

from rtemsqual.glossary import generate
from rtemsqual.items import ItemCache
from rtemsqual.tests.util import create_item_cache_config_and_copy_spec


def test_glossary(tmpdir):
    item_cache_config = create_item_cache_config_and_copy_spec(
        tmpdir, "spec-glossary")
    item_cache = ItemCache(item_cache_config)

    glossary_config = {}
    glossary_config["project-groups"] = ["/g"]
    project_glossary = os.path.join(tmpdir, "project", "glossary.rst")
    glossary_config["project-target"] = project_glossary
    doc = {}
    doc["rest-source-paths"] = [str(tmpdir)]
    document_glossary = os.path.join(tmpdir, "document", "glossary.rst")
    doc["target"] = document_glossary
    glossary_config["documents"] = [doc]
    generate(glossary_config, item_cache)

    with open(project_glossary, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

Glossary
********

.. glossary::
    :sorted:

    T
        Term text $:term:`U` :term:`T`
        term.

    U
        Term text U.

    V
        Term text V.
"""
        assert content == src.read()

    with open(document_glossary, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH (http://www.embedded-brains.de)

Glossary
********

.. glossary::
    :sorted:

    T
        Term text $:term:`U` :term:`T`
        term.

    U
        Term text U.
"""
        assert content == src.read()
