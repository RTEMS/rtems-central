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

import copy
from typing import Any, Dict, List, Optional

from rtemsspec.content import CContent, get_value_double_colon, \
    get_value_doxygen_function, get_value_hash
from rtemsspec.sphinxcontent import SphinxContent, SphinxMapper
from rtemsspec.items import EmptyItem, Item, ItemCache, ItemGetValueContext, \
    ItemMapper

ItemMap = Dict[str, Item]

_FEATURE = "This configuration option is a boolean feature define."

_OPTION_TYPES = {
    "feature": _FEATURE,
    "feature-enable": _FEATURE,
    "integer": "This configuration option is an integer define.",
    "initializer": "This configuration option is an initializer define."
}

_OPTION_DEFAULT_CONFIG = {
    "feature":
    lambda item: item["default"],
    "feature-enable":
    lambda item:
    """If this configuration option is undefined, then the described feature is not
enabled."""
}


class _ContentAdaptor:
    """
    The content adaptor provides a specialized interface to a content class.

    By default, Sphinx content is generated.
    """
    def __init__(self, mapper: ItemMapper, content: Any) -> None:
        self.mapper = mapper
        self.content = content

    def substitute(self, text: Optional[str]) -> str:
        """ Substitutes the optional text using the item mapper. """
        return self.mapper.substitute(text)

    def add_group(self, name: str, description: str) -> None:
        """ Adds an option group. """
        self.content.add_automatically_generated_warning()
        self.content.add_header(name, level=2)
        self.content.add(description)

    def add_option(self, name: str, index_entries: List[str]) -> None:
        """ Adds an option. """
        self.content.add_index_entries([name] + index_entries)
        self.content.add_label(name)
        self.content.add_header(name, level=3)
        self.content.add_definition_item("CONSTANT:", f"``{name}``")

    def add_option_type(self, option_type: str) -> None:
        """ Adds an option type. """
        self.content.add_definition_item("OPTION TYPE:", option_type)

    def add_option_default_value(self, value: str) -> None:
        """ Adds an option default value. """
        self.content.add_definition_item("DEFAULT VALUE:", value)

    def add_option_default_config(self, config: str) -> None:
        """ Adds an option default configuration. """
        self.content.add_definition_item("DEFAULT CONFIGURATION:", config)

    def add_option_value_constraints(self, lines: List[str]) -> None:
        """ Adds a option value constraints. """
        self.content.add_definition_item("VALUE CONSTRAINTS:", lines)

    def add_option_description(self, description: str) -> None:
        """ Adds a option description. """
        self.content.add_definition_item("DESCRIPTION:", description)

    def add_option_notes(self, notes: Optional[str]) -> None:
        """ Adds option notes. """
        if not notes:
            notes = "None."
        self.content.add_definition_item("NOTES:", notes)

    def add_licence_and_copyrights(self) -> None:
        """ Adds the license and copyrights. """
        self.content.add_licence_and_copyrights()

    def register_license_and_copyrights_of_item(self, item: Item) -> None:
        """ Registers the license and copyrights of the item. """
        self.content.register_license_and_copyrights_of_item(item)

    def write(self, filename: str):
        """ Writes the content to the file specified by the path. """
        self.content.write(filename)


class _SphinxContentAdaptor(_ContentAdaptor):
    def __init__(self, mapper: ItemMapper) -> None:
        super().__init__(mapper, SphinxContent())


class _DoxygenContentAdaptor(_ContentAdaptor):
    # pylint: disable=attribute-defined-outside-init

    def __init__(self, mapper: ItemMapper) -> None:
        super().__init__(mapper, CContent())
        self._reset()

    def _reset(self) -> None:
        self._name = ""
        self._option_type = ""
        self._default_value = ""
        self._default_config = ""
        self._value_constraints = []  # type: List[str]
        self._description = ""

    def add_group(self, name: str, description: str) -> None:
        identifier = f"RTEMSApplConfig{name.replace(' ', '')}"
        with self.content.defgroup_block(identifier, name):
            self.content.add("@ingroup RTEMSApplConfig")
            self.content.doxyfy(description)
            self.content.add("@{")

    def add_option(self, name: str, _index_entries: List[str]) -> None:
        self.content.open_doxygen_block()
        self._name = name

    def add_option_type(self, option_type: str) -> None:
        self._option_type = option_type

    def add_option_default_value(self, value: str) -> None:
        self._default_value = value

    def add_option_default_config(self, config: str) -> None:
        self._default_config = config

    def add_option_value_constraints(self, lines: List[str]) -> None:
        self._value_constraints = lines

    def add_option_description(self, description: str) -> None:
        self._description = description

    def add_option_notes(self, notes: Optional[str]) -> None:
        self.content.add_brief_description(self._option_type)
        self.content.doxyfy(self._description)
        self.content.add_paragraph("Default Value", self._default_value)
        self.content.add_paragraph("Default Configuration",
                                   self._default_config)
        self.content.add_paragraph("Value Constraints",
                                   self._value_constraints)
        self.content.add_paragraph("Notes", notes)
        self.content.close_comment_block()
        self.content.append(f"#define {self._name}")
        self._reset()

    def add_licence_and_copyrights(self) -> None:
        self.content.add("/** @} */")


def _generate_feature(content: _ContentAdaptor, item: Item,
                      option_type: str) -> None:
    content.add_option_default_config(
        content.substitute(_OPTION_DEFAULT_CONFIG[option_type](item)))


def _generate_min_max(lines: List[str], value: str, word: str) -> None:
    lines.append("The value of this configuration option shall be "
                 f"{word} than or equal to {value}.")


def _generate_set(lines: List[str], values: List[Any]) -> None:
    value_set = "{" + ", ".join([str(x) for x in values]) + "}"
    lines.append("The value of this configuration option shall be")
    lines.append(f"an element of {value_set}.")


def _start_constraint_list(lines: List[str]) -> None:
    lines.append("The value of this configuration option shall "
                 "satisfy all of the following")
    lines.append("constraints:")


def _generate_item_min(lines: List[str], constraints: Dict[str, Any]) -> None:
    if "min" in constraints:
        value = constraints["min"]
        lines.append("")
        lines.append(f"* It shall be greater than or equal to {value}.")


def _generate_item_max(lines: List[str], constraints: Dict[str, Any]) -> None:
    if "max" in constraints:
        value = constraints["max"]
        lines.append("")
        lines.append(f"* It shall be less than or equal to {value}.")


def _generate_item_set(lines: List[str], constraints: Dict[str, Any]) -> None:
    if "set" in constraints:
        value_set = constraints["set"]
        lines.append("")
        lines.append(f"* It shall be an element of {value_set}.")


def _generate_item_texts(lines: List[str], constraints: Dict[str,
                                                             Any]) -> None:
    for text in constraints.get("texts", []):
        lines.append("")
        text = text.replace("The value of this configuration option", "It")
        text = text.strip().split("\n")
        lines.append(f"* {text[0]}")
        lines.extend([f"  {x}" if x else "" for x in text[1:]])


def _resolve_constraint_links(content: _ContentAdaptor, item: Item,
                              constraints: Dict[str, Any]) -> None:
    texts = []  # type: List[str]
    for parent in item.parents("constraint"):
        content.register_license_and_copyrights_of_item(parent)
        texts.append(parent["text"])
    if texts:
        constraints.setdefault("texts", []).extend(reversed(texts))


def _generate_constraint(content: _ContentAdaptor, item: Item) -> None:
    constraints = copy.deepcopy(item["constraints"])
    _resolve_constraint_links(content, item, constraints)
    lines = []  # type: List[str]
    count = len(constraints)
    if count == 1:
        if "min" in constraints:
            _generate_min_max(lines, constraints["min"], "greater")
        elif "max" in constraints:
            _generate_min_max(lines, constraints["max"], "less")
        elif "set" in constraints:
            _generate_set(lines, constraints["set"])
        elif "texts" in constraints:
            if len(constraints["texts"]) == 1:
                lines.extend(constraints["texts"][0].strip().split("\n"))
            else:
                _start_constraint_list(lines)
                _generate_item_texts(lines, constraints)
    elif count == 2 and "min" in constraints and "max" in constraints:
        minimum = constraints["min"]
        maximum = constraints["max"]
        lines.append("The value of this configuration option shall be "
                     f"greater than or equal to {minimum}")
        lines.append(f"and less than or equal to {maximum}.")
    else:
        _start_constraint_list(lines)
        _generate_item_min(lines, constraints)
        _generate_item_max(lines, constraints)
        _generate_item_set(lines, constraints)
        _generate_item_texts(lines, constraints)
    content.add_option_value_constraints(
        [content.substitute(line) for line in lines])


def _generate_initializer_or_integer(content: _ContentAdaptor, item: Item,
                                     _option_type: str) -> None:
    default_value = item["default-value"]
    if not isinstance(default_value, str) or " " not in default_value:
        default_value = f"The default value is {default_value}."
    content.add_option_default_value(content.substitute(default_value))
    _generate_constraint(content, item)


_OPTION_GENERATORS = {
    "feature": _generate_feature,
    "feature-enable": _generate_feature,
    "initializer": _generate_initializer_or_integer,
    "integer": _generate_initializer_or_integer
}


def _generate(group: Item, options: ItemMap, content: _ContentAdaptor) -> None:
    content.register_license_and_copyrights_of_item(group)
    content.add_group(group["name"], content.substitute(group["description"]))
    for item in sorted(options.values(), key=lambda x: x["name"]):
        content.mapper.item = item
        name = item["name"]
        content.register_license_and_copyrights_of_item(item)
        content.add_option(name, item["index-entries"])
        option_type = item["appl-config-option-type"]
        content.add_option_type(_OPTION_TYPES[option_type])
        _OPTION_GENERATORS[option_type](content, item, option_type)
        content.add_option_description(content.substitute(item["description"]))
        content.add_option_notes(content.substitute(item["notes"]))
    content.add_licence_and_copyrights()


def _get_value_none(_ctx: ItemGetValueContext) -> Any:
    return None


def _sphinx_ref(ref: str) -> str:
    return f":ref:`{ref}`"


_PTHREAD_NAME_NP = "http://man7.org/linux/man-pages/man3/" \
    "pthread_setname_np.3.html"

_SPHINX_DOC_REFS = {
    "config-scheduler-clustered":
    _sphinx_ref("ConfigurationSchedulersClustered"),
    "config-scheduler-table": _sphinx_ref("ConfigurationSchedulerTable"),
    "config-unlimited-objects": _sphinx_ref("ConfigUnlimitedObjects"),
    "mp-proxies": _sphinx_ref("MPCIProxies"),
    "mrsp": _sphinx_ref("MrsP"),
    "pthread-setname-np": f"`PTHREAD_SETNAME_NP(3) <{_PTHREAD_NAME_NP}>`_",
    "scheduler-cbs": _sphinx_ref("SchedulerCBS"),
    "scheduler-concepts": _sphinx_ref("SchedulingConcepts"),
    "scheduler-edf": _sphinx_ref("SchedulerEDF"),
    "scheduler-priority": _sphinx_ref("SchedulerPriority"),
    "scheduler-priority-simple": _sphinx_ref("SchedulerPrioritySimple"),
    "scheduler-smp-edf": _sphinx_ref("SchedulerSMPEDF"),
    "scheduler-smp-priority-affinity":
    _sphinx_ref("SchedulerSMPPriorityAffinity"),
    "scheduler-smp-priority": _sphinx_ref("SchedulerSMPPriority"),
    "scheduler-smp-priority-simple": _sphinx_ref("SchedulerSMPPrioritySimple"),
    "terminate": _sphinx_ref("Terminate"),
}


def _get_value_sphinx_reference(ctx: ItemGetValueContext) -> Any:
    return _SPHINX_DOC_REFS[ctx.key]


def _add_sphinx_get_values(mapper: ItemMapper) -> None:
    for key in _SPHINX_DOC_REFS:
        for opt in ["feature-enable", "feature", "initializer", "integer"]:
            doc_ref = f"interface/appl-config-option/{opt}:/document-reference"
            mapper.add_get_value(doc_ref, _get_value_none)
            mapper.add_get_value(f"{doc_ref}/{key}",
                                 _get_value_sphinx_reference)


def _c_user_ref(ref: str, name: str) -> str:
    c_user = "https://docs.rtems.org/branches/master/c-user/"
    return f"<a href={c_user}{ref}>{name}</a>"


_DOXYGEN_DOC_REFS = {
    "config-scheduler-clustered":
    _c_user_ref("config/scheduler-clustered.html",
                "Clustered Scheduler Configuration"),
    "config-scheduler-table":
    _c_user_ref(
        "config/scheduler-clustered.html#configuration-step-3-scheduler-table",
        "Configuration Step 3 - Scheduler Table"),
    "config-unlimited-objects":
    _c_user_ref("config/intro.html#unlimited-objects", "Unlimited Objects"),
    "mp-proxies":
    _c_user_ref("multiprocessing.html#proxies", "Proxies"),
    "mrsp":
    _c_user_ref(
        "key_concepts.html#multiprocessor-resource-sharing-protocol-mrsp",
        "Multiprocessor Resource Sharing Protocol (MrsP)"),
    "pthread-setname-np":
    f"<a href={_PTHREAD_NAME_NP}>PTHREAD_SETNAME_NP(3)</a>",
    "scheduler-cbs":
    _c_user_ref(
        "scheduling_concepts.html#constant-bandwidth-server-scheduling-cbs",
        "Constant Bandwidth Server Scheduling (CBS)"),
    "scheduler-concepts":
    _c_user_ref("scheduling_concepts.html", "Scheduling Concepts"),
    "scheduler-edf":
    _c_user_ref("scheduling_concepts.html#earliest-deadline-first-scheduler",
                "Earliest Deadline First Scheduler"),
    "scheduler-priority":
    _c_user_ref("scheduling_concepts.html#deterministic-priority-scheduler",
                "Deterministic Priority Scheduler"),
    "scheduler-priority-simple":
    _c_user_ref("scheduling_concepts.html#simple-priority-scheduler",
                "Simple Priority Scheduler"),
    "scheduler-smp-edf":
    _c_user_ref(
        "scheduling_concepts.html#earliest-deadline-first-smp-scheduler",
        "Earliest Deadline First SMP Scheduler"),
    "scheduler-smp-priority-affinity":
    _c_user_ref(
        "scheduling_concepts.html"
        "#arbitrary-processor-affinity-priority-smp-scheduler",
        "Arbitrary Processor Affinity Priority SMP Scheduler"),
    "scheduler-smp-priority":
    _c_user_ref(
        "scheduling_concepts.html#deterministic-priority-smp-scheduler",
        "Deterministic Priority SMP Scheduler"),
    "scheduler-smp-priority-simple":
    _c_user_ref("scheduling_concepts.html#simple-priority-smp-scheduler",
                "Simple Priority SMP Scheduler"),
    "terminate":
    _c_user_ref("fatal_error.html#announcing-a-fatal-error",
                "Announcing a Fatal Error"),
}


def _get_value_doxygen_reference(ctx: ItemGetValueContext) -> Any:
    return _DOXYGEN_DOC_REFS[ctx.key]


def _get_value_doxygen_url(ctx: ItemGetValueContext) -> Any:
    return f"<a href=\"{ctx.item['reference']}\">{ctx.value[ctx.key]}</a>"


def _get_value_doxygen_unspecfied_define(ctx: ItemGetValueContext) -> Any:
    if ctx.item["reference"]:
        return _get_value_doxygen_url(ctx)
    return get_value_hash(ctx)


def _get_value_doxygen_unspecfied_type(ctx: ItemGetValueContext) -> Any:
    if ctx.item["reference"]:
        return _get_value_doxygen_url(ctx)
    return get_value_double_colon(ctx)


def _add_doxygen_get_values(mapper: ItemMapper) -> None:
    for key in _DOXYGEN_DOC_REFS:
        for opt in ["feature-enable", "feature", "initializer", "integer"]:
            doc_ref = f"interface/appl-config-option/{opt}:/document-reference"
            mapper.add_get_value(doc_ref, _get_value_none)
            mapper.add_get_value(f"{doc_ref}/{key}",
                                 _get_value_doxygen_reference)
            name = f"interface/appl-config-option/{opt}:/name"
            mapper.add_get_value(name, get_value_hash)
    mapper.add_get_value("interface/define:/name", get_value_hash)
    mapper.add_get_value("interface/function:/name",
                         get_value_doxygen_function)
    mapper.add_get_value("interface/macro:/name", get_value_doxygen_function)
    mapper.add_get_value("interface/struct:/name", get_value_double_colon)
    mapper.add_get_value("interface/typedef:/name", get_value_double_colon)
    mapper.add_get_value("interface/union:/name", get_value_double_colon)
    mapper.add_get_value("interface/unspecified-define:/name",
                         _get_value_doxygen_unspecfied_define)
    mapper.add_get_value("interface/unspecified-function:/name",
                         get_value_doxygen_function)
    mapper.add_get_value("interface/unspecified-type:/name",
                         _get_value_doxygen_unspecfied_type)


def generate(config: dict, item_cache: ItemCache) -> None:
    """
    Generates application configuration documentation sources according to the
    configuration.

    :param config: A dictionary with configuration entries.
    :param item_cache: The specification item cache containing the application
                       configuration groups and options.
    """
    sphinx_mapper = SphinxMapper(EmptyItem())
    _add_sphinx_get_values(sphinx_mapper)
    doxygen_mapper = ItemMapper(EmptyItem())
    _add_doxygen_get_values(doxygen_mapper)
    doxygen_content = _DoxygenContentAdaptor(doxygen_mapper)
    doxygen_content.content.add_automatically_generated_warning()
    with doxygen_content.content.defgroup_block(
            "RTEMSApplConfig", "Application Configuration Options"):
        doxygen_content.content.add("@ingroup RTEMSAPI")
    for group_config in config["groups"]:
        group = item_cache[group_config["uid"]]
        assert group.type == "interface/appl-config-group"
        options = {}  # type: ItemMap
        for child in group.children("appl-config-group-member"):
            assert child.type.startswith("interface/appl-config-option")
            options[child.uid] = child
        sphinx_content = _SphinxContentAdaptor(sphinx_mapper)
        _generate(group, options, sphinx_content)
        sphinx_content.write(group_config["target"])
        _generate(group, options, doxygen_content)
    doxygen_content.content.prepend_copyrights_and_licenses()
    doxygen_content.content.prepend_spdx_license_identifier()
    doxygen_content.write(config["doxygen-target"])
