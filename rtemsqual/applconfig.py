# SPDX-License-Identifier: BSD-2-Clause
""" Functions for application configuration documentation generation. """

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

import rtemsqual.content


def _application_configuration_option_content(item, content):
    content.add_index_entries(item["index"])
    content.add_blank_line()
    header = item["header"]
    content.add_label(header)
    content.add_blank_line()
    content.add_header(header)
    content.add_definition_item("DESCRIPTION:",
                                item["description"].split("\n"))
    content.add_definition_item("NOTES:", item["notes"].split("\n"))


def _application_configuration_group_content(item, document):
    content = rtemsqual.content.SphinxContent()
    for child in item.children:
        if (child["type"] == "interface" and
                child["interface-type"] == "application-configuration-option"):
            _application_configuration_option_content(child, content)
        else:
            raise Exception("unexpected item type")


def classic_api_guide_content(item, document):
    """ This is work in progress. """
    for child in item.children:
        if (child["type"] == "interface" and
                child["interface-type"] == "application-configuration-group"):
            _application_configuration_group_content(child, document)
        else:
            classic_api_guide_content(child, document)
