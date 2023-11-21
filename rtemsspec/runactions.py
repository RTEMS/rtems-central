# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a build step to run actions. """

# Copyright (C) 2022, 2023 embedded brains GmbH (http://www.embedded-brains.de)
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
import os
import logging
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Union

from rtemsspec.directorystate import DirectoryState
from rtemsspec.items import Item, ItemGetValueContext, is_enabled
from rtemsspec.packagebuild import BuildItem, PackageBuildDirector
from rtemsspec.util import copy_and_substitute, remove_empty_directories


def _env_clear(item: "RunActions", env: Dict, _action: Dict[str, str]) -> None:
    logging.info("%s: env: clear", item.uid)
    env.clear()


def _env_path_append(item: "RunActions", env: Dict, action: Dict[str,
                                                                 str]) -> None:
    name = action["name"]
    value = action["value"]
    logging.info("%s: env: append '%s' to %s", item.uid, value, name)
    env[name] = f"{env[name]}:{value}"


def _env_path_prepend(item: "RunActions", env: Dict,
                      action: Dict[str, str]) -> None:
    name = action["name"]
    value = action["value"]
    logging.info("%s: env: prepend '%s' to %s", item.uid, value, name)
    env[name] = f"{value}:{env[name]}"


def _env_set(item: "RunActions", env: Dict, action: Dict[str, str]) -> None:
    name = action["name"]
    value = action["value"]
    logging.info("%s: env: %s = '%s'", item.uid, name, value)
    env[name] = value


def _env_unset(item: "RunActions", env: Dict, action: Dict[str, str]) -> None:
    name = action["name"]
    logging.info("%s: env: unset %s", item.uid, name)
    del env[name]


_ENV_ACTIONS = {
    "clear": _env_clear,
    "path-append": _env_path_append,
    "path-prepend": _env_path_prepend,
    "set": _env_set,
    "unset": _env_unset
}


def _get_host_processor_count(_ctx: ItemGetValueContext) -> str:
    count = os.cpu_count()
    return str(count if count is not None else 1)


class RunActions(BuildItem):
    """ Runs actions. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self.mapper.add_get_value(f"{self.item.type}:/host-processor-count",
                                  _get_host_processor_count)

    def run(self):
        for index, action in enumerate(self["actions"]):
            action_type = action["action"]
            logging.info("%s: run action %i: %s", self.uid, index, action_type)
            if is_enabled(self.enabled_set, action["enabled-by"]):
                output_name = action.get("output-name", None)
                if output_name is None:
                    output = None
                else:
                    try:
                        output = self.output(output_name)
                    except ValueError:
                        continue
                RunActions._ACTIONS[action_type](self, action, output)

    def _copy_and_substitute(self, action: Dict,
                             output: Optional[DirectoryState]) -> None:
        assert isinstance(output, DirectoryState)
        input_state = self.input(action["input-name"])
        assert isinstance(input_state, DirectoryState)
        source = action["source"]
        source_base = input_state.directory
        target_base = output.directory
        if source is None:
            prefix = action["target"]
            if prefix is None:
                prefix = "."
            targets: List[str] = []
            for source_file in input_state:
                tail = os.path.relpath(source_file, source_base)
                target_file = os.path.join(target_base, prefix, tail)
                targets.append(tail)
                copy_and_substitute(source_file, target_file, self.mapper,
                                    self.uid)
            output.add_files(targets)
        else:
            source_file = os.path.join(source_base, source)
            target = action["target"]
            if target is None:
                target_file = output.file
            else:
                output.add_files([target])
                target_file = os.path.join(target_base, target)
            copy_and_substitute(source_file, target_file, self.mapper,
                                self.uid)

    def _create_ini_file(self, action: Dict,
                         output: Optional[DirectoryState]) -> None:
        assert isinstance(output, DirectoryState)
        target = action["target"]
        if target is None:
            target = output.file
        else:
            output.add_files([target])
            target = os.path.join(output.directory, target)
        logging.info("%s: create: %s", self.uid, target)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as dst:
            for section in action["sections"]:
                if not is_enabled(self.enabled_set, section["enabled-by"]):
                    continue
                dst.write(f"[{section['name']}]\n")
                for key_value in section["key-value-pairs"]:
                    if not is_enabled(self.enabled_set,
                                      key_value["enabled-by"]):
                        continue
                    dst.write(f"{key_value['key']} = {key_value['value']}\n")

    def _directory_state_clear(self, _action: Dict,
                               output: Optional[DirectoryState]) -> None:
        assert isinstance(output, DirectoryState)
        output.clear()

    def _directory_state_add_files(self, action: Dict,
                                   output: Optional[DirectoryState]) -> None:
        assert isinstance(output, DirectoryState)
        root = Path(action["path"]).absolute()
        pattern = action["pattern"]
        logging.info("%s: add files matching '%s' in: %s", self.uid, pattern,
                     root)
        base = output.directory
        output.add_files(
            [os.path.relpath(path, base) for path in root.glob(pattern)])

    def _directory_state_add_tarfile_members(
            self, action: Dict, output: Optional[DirectoryState]) -> None:
        assert isinstance(output, DirectoryState)
        root = Path(action["search-path"])
        pattern = action["pattern"]
        logging.info("%s: search for tarfiles matching '%s' in: %s", self.uid,
                     pattern, root)
        for path in root.glob(pattern):
            output.add_tarfile_members(path, action["prefix-path"],
                                       action["extract"])

    def _directory_state_tree_op(self, action: Dict,
                                 output: Optional[DirectoryState],
                                 tree_op: Any) -> None:
        assert isinstance(output, DirectoryState)
        root = Path(action["root"]).absolute()
        prefix = action["prefix"]
        if prefix is None:
            prefix = "."
        tree_op(output, root, prefix, action["excludes"])

    def _directory_state_add_tree(self, action: Dict,
                                  output: Optional[DirectoryState]) -> None:
        self._directory_state_tree_op(action, output, DirectoryState.add_tree)

    def _directory_state_copy_tree(self, action: Dict,
                                   output: Optional[DirectoryState]) -> None:
        self._directory_state_tree_op(action, output, DirectoryState.copy_tree)

    def _directory_state_move_tree(self, action: Dict,
                                   output: Optional[DirectoryState]) -> None:
        self._directory_state_tree_op(action, output, DirectoryState.move_tree)

    def _process(self, action: Dict,
                 _output: Optional[DirectoryState]) -> None:
        env: Union[Dict, None] = None
        env_actions = action["env"]
        if env_actions:
            logging.info("%s: env: modify", self.uid)
            env = copy.deepcopy(os.environ.copy())
            for env_action in env_actions:
                _ENV_ACTIONS[env_action["action"]](self, env, env_action)
        cmd = action["command"]
        cwd = action["working-directory"]
        logging.info("%s: run in '%s': %s", self.uid, cwd,
                     " ".join(f"'{i}'" for i in cmd))
        status = subprocess.run(cmd, env=env, check=False, cwd=cwd)
        expected_return_code = action["expected-return-code"]
        if expected_return_code is not None:
            assert status.returncode == expected_return_code

    def _mkdir(self, action: Dict, _output: Optional[DirectoryState]) -> None:
        path = Path(action["path"])
        logging.info("%s: make directory: %s", self.uid, path)
        path.mkdir(parents=action["parents"], exist_ok=action["exist-ok"])

    def _remove_path(self, path: Path) -> None:
        if path.is_dir():
            logging.info("%s: remove directory: %s", self.uid, path)
            path.rmdir()
        else:
            logging.info("%s: unlink file: %s", self.uid, path)
            path.unlink()

    def _remove(self, action: Dict, _output: Optional[DirectoryState]) -> None:
        path = Path(action["path"])
        if action["missing-ok"]:
            try:
                self._remove_path(path)
            except FileNotFoundError:
                pass
        else:
            self._remove_path(path)

    def _remove_empty_directories(self, action: Dict,
                                  _output: Optional[DirectoryState]) -> None:
        remove_empty_directories(self.uid, action["path"])

    def _remove_glob(self, action: Dict,
                     _output: Optional[DirectoryState]) -> None:
        root = Path(action["path"])
        for pattern in action["patterns"]:
            logging.info(
                "%s: remove files and directories matching with '%s' in: %s",
                self.uid, pattern, root)
            for path in root.glob(pattern):
                if path.is_dir():
                    if action["remove-tree"]:
                        logging.info("%s: remove directory tree: %s", self.uid,
                                     path)
                        shutil.rmtree(path)
                    else:
                        logging.info("%s: remove directory: %s", self.uid,
                                     path)
                        path.rmdir()
                else:
                    logging.info("%s: remove file: %s", self.uid, path)
                    path.unlink()

    def _remove_tree(self, action: Dict,
                     _output: Optional[DirectoryState]) -> None:
        path = action["path"]
        logging.info("%s: remove directory tree: %s", self.uid, path)
        if action["missing-ok"]:
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                pass
        else:
            shutil.rmtree(path)

    def _touch(self, action: Dict, _output: Optional[DirectoryState]) -> None:
        path = Path(action["path"])
        logging.info("%s: touch file: %s", self.uid, path)
        path.touch(exist_ok=action["exist-ok"])

    _ACTIONS = {
        "copy-and-substitute": _copy_and_substitute,
        "create-ini-file": _create_ini_file,
        "directory-state-add-files": _directory_state_add_files,
        "directory-state-add-tarfile-members":
        _directory_state_add_tarfile_members,
        "directory-state-add-tree": _directory_state_add_tree,
        "directory-state-clear": _directory_state_clear,
        "directory-state-copy-tree": _directory_state_copy_tree,
        "directory-state-move-tree": _directory_state_move_tree,
        "mkdir": _mkdir,
        "remove": _remove,
        "remove-empty-directories": _remove_empty_directories,
        "remove-glob": _remove_glob,
        "remove-tree": _remove_tree,
        "subprocess": _process,
        "touch": _touch
    }
