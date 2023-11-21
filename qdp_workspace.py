#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
""" Creates a QDP workspace directory according to the configuration file. """

# Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG
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
import logging
import os
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from rtemsspec.items import Item, ItemCache, JSONItemCache, is_enabled
from rtemsspec.directorystate import DirectoryState
from rtemsspec.packagebuild import BuildItem, BuildItemFactory, \
    PackageBuildDirector
from rtemsspec.packagebuildfactory import create_build_item_factory
from rtemsspec.specverify import verify
from rtemsspec.util import create_build_argument_parser, hash_file, \
    init_logging, load_config, run_command


class _ConfigItem(BuildItem):

    def __init__(self, director: PackageBuildDirector, item: Item,
                 factory: BuildItemFactory):
        super().__init__(director, item)
        workspace_cache_config: Dict[str, Any] = {
            "enabled": [],
            "initialize-links": False,
            "paths": [],
            "resolve-proxies": False,
            "spec-type-root-uid": None
        }
        self.workspace_cache = JSONItemCache(workspace_cache_config)
        self.workspace_director = PackageBuildDirector(self.workspace_cache,
                                                       factory)

    def is_enabled(self, enabled_by: Any) -> bool:
        """
        Returns true, if the enabled by expression evaluates to true for the
        enabled set of the configuration item, otherwise returns false.
        """
        try:
            enabled_set = self.enabled_set
        except KeyError:
            enabled_set = []
        return is_enabled(self.substitute(enabled_set), enabled_by)

    def set_file(self, item: Item) -> None:
        """ Sets the file of the item.  """
        file = os.path.join(self["spec-directory"], f"{item.uid[1:]}.json")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        item.file = file

    def try_save(self, build_item: BuildItem, _reason: str) -> None:
        """ Tries to set the file of the item and save it.  """
        if "spec-directory" in self:
            self.set_file(build_item.item)
            build_item.item.save()
            self.item.cache[build_item.uid].data.clear()
            self.item.cache[build_item.uid].data.update(build_item.item.data)
        else:
            logging.info("%s: cannot save item", build_item.uid)


def _create_item(
    config: _ConfigItem,
    action: Dict[str, Any],
    data: Dict[str, Any],
    type_name: str,
    prepare: Optional[Callable[[_ConfigItem, Dict[str, Any]], None]] = None
) -> Optional[BuildItem]:
    uid = action["uid"]
    item = config.item.cache.create_item(uid, data)
    item["_type"] = type_name
    if prepare is not None:
        prepare(config, action)
    workspace_item = config.workspace_cache.create_item(
        uid, copy.deepcopy(data))
    workspace_item["_type"] = type_name
    build_item = config.workspace_director[uid]
    return build_item


def _make_root_data(config: _ConfigItem, type_name: str) -> Any:
    return {
        "SPDX-License-Identifier": config.variant["SPDX-License-Identifier"],
        "copyrights": config.variant["copyrights"],
        "enabled-by": True,
        "links": [],
        "qdp-type": type_name,
        "type": "qdp"
    }


def _make_directory_state_data(config: _ConfigItem, directory: str,
                               directory_state_type: str) -> Any:
    data = _make_root_data(config, "directory-state")
    data["copyrights-by-license"] = {}
    data["directory"] = directory
    data["directory-state-type"] = directory_state_type
    data["files"] = []
    data["hash"] = None
    data["patterns"] = []
    return data


def _load_directory(config: _ConfigItem, action: Dict[str, Any]) -> None:
    directory_state = config.director[action["uid"]]
    assert isinstance(directory_state, DirectoryState)
    directory_state.load()
    directory_state["patterns"] = []


def _action_copy_directory(config: _ConfigItem, action: Dict[str,
                                                             Any]) -> None:
    source_directory = config.substitute(action["source-directory"])
    data = _make_directory_state_data(config, source_directory, "generic")
    data["copyrights-by-license"] = action["copyrights-by-license"]
    data["patterns"] = action["patterns"]
    data["files"] = action["files"]
    data["links"] = action["links"]
    workspace_directory_state = _create_item(config, action, data,
                                             "qdp/directory-state/generic",
                                             _load_directory)
    assert isinstance(workspace_directory_state, DirectoryState)
    directory_state = config.director[action["uid"]]
    assert isinstance(directory_state, DirectoryState)
    workspace_directory_state["directory"] = action["destination-directory"]
    workspace_directory_state.clear()
    workspace_directory_state.lazy_clone(directory_state)
    config.try_save(workspace_directory_state, "Update directory state")


def _copy_file(config: _ConfigItem, action: Dict[str, Any],
               the_type: str) -> None:
    source_file = config.substitute(action["source-file"])
    data = _make_directory_state_data(config, os.path.dirname(source_file),
                                      the_type)
    data["files"] = [{"file": os.path.basename(source_file), "hash": None}]
    data["links"] = action["links"]
    workspace_directory_state = _create_item(
        config, action, data, f"qdp/directory-state/{the_type}",
        _load_directory)
    assert isinstance(workspace_directory_state, DirectoryState)
    directory_state = config.director[action["uid"]]
    assert isinstance(directory_state, DirectoryState)
    workspace_directory_state["directory"] = action["destination-directory"]
    workspace_directory_state.clear()
    workspace_directory_state.copy_file(source_file,
                                        action["destination-file"])
    workspace_directory_state.load()
    config.try_save(workspace_directory_state, "Update directory state")


def _action_copy_file(config: _ConfigItem, action: Dict[str, Any]) -> None:
    _copy_file(config, action, "generic")


def _action_copy_test_log(config: _ConfigItem, action: Dict[str, Any]) -> None:
    _copy_file(config, action, "test-log")


def _git_clone(config: _ConfigItem, action: Dict[str, Any],
               repository: DirectoryState) -> None:
    source_directory = config.substitute(action["source-directory"])
    status = run_command(["git", "fetch", "origin"], source_directory)
    assert status == 0
    branch = action["branch"]
    commit = action["commit"]
    status = run_command(["git", "branch", "-f", branch, commit],
                         source_directory)
    assert status == 0
    destination_directory = repository.directory
    status = run_command([
        "git", "clone", "--branch", branch, "--single-branch",
        f"file://{source_directory}", destination_directory
    ], source_directory)
    assert status == 0
    origin_url = action["origin-url"]
    if origin_url:
        status = run_command(
            ["git", "remote", "add", "tmp",
             config.substitute(origin_url)], destination_directory)
        assert status == 0
        status = run_command(["git", "remote", "remove", "origin"],
                             destination_directory)
        assert status == 0
        status = run_command(["git", "remote", "rename", "tmp", "origin"],
                             destination_directory)
        assert status == 0
    for fetch in action["origin-fetch"]:
        status = run_command(
            ["git", "fetch", "origin",
             config.substitute(fetch)], destination_directory)
        assert status == 0
    origin_branch = action["origin-branch"]
    origin_commit = action["origin-commit"]
    if origin_branch and origin_commit:
        status = run_command(
            ["git", "checkout", "-b", origin_branch, origin_commit],
            destination_directory)
        assert status == 0
        status = run_command(["git", "checkout", branch],
                             destination_directory)
        assert status == 0
        status = run_command([
            "git", "symbolic-ref", "refs/remotes/origin/HEAD",
            f"refs/remotes/origin/{origin_branch}"
        ], destination_directory)
        assert status == 0
    for command in action["post-clone-commands"]:
        status = run_command(config.substitute(command), destination_directory)
        assert status == 0
    repository.load()
    config.try_save(repository, "Clone Git repository")


def _action_git_clone(config: _ConfigItem, action: Dict[str, Any]) -> None:
    data = _make_directory_state_data(config, action["destination-directory"],
                                      "repository")
    data["patterns"] = [{"include": "**/*", "exclude": []}]
    for key in [
            "branch", "commit", "copyrights-by-license", "description",
            "links", "origin-branch", "origin-commit", "origin-commit-url",
            "origin-url"
    ]:
        data[key] = action[key]
    repository = _create_item(config, action, data,
                              "qdp/directory-state/repository")
    assert isinstance(repository, DirectoryState)
    destination_directory = repository.directory
    assert not os.path.exists(destination_directory)
    _git_clone(config, action, repository)


def _add_item(config: _ConfigItem, action: Dict[str, Any],
              data: Dict[str, Any]) -> None:
    config.item.cache.create_item(action["uid"], data)


def _action_add_item(config: _ConfigItem, action: Dict[str, Any]) -> None:
    source_file = config.substitute(action["source"])
    data = config.item.cache.load_data(source_file, action["uid"])
    _add_item(config, action, data)


def _action_make_item(config: _ConfigItem, action: Dict[str, Any]) -> None:
    _add_item(config, action, action["data"])


def _action_make_uuid_item(config: _ConfigItem, action: Dict[str,
                                                             Any]) -> None:
    data = _make_root_data(config, "uuid")
    data["uuid"] = str(uuid.uuid4())
    _add_item(config, action, data)


def _set_types(item_cache: ItemCache, action: Dict[str, Any]) -> None:
    for set_type in action["set-types"]:
        item_cache[set_type["uid"]]["_type"] = set_type["type"]


def _action_load_items(config: _ConfigItem, action: Dict[str, Any]) -> None:
    action_name = action["action-name"]
    item_cache = config.item.cache
    for path in action["paths"]:
        path = config.substitute(path)
        logging.info("%s: load items from: %s", action_name, path)
        item_cache.load_items(path)
    _set_types(item_cache, action)
    config.director.clear()
    config.workspace_director.clear()


def _new_workspace_items(config: _ConfigItem, action_name: str,
                         new: Set[str]) -> None:
    for uid in sorted(new):
        logging.debug("%s: new item: %s", action_name, uid)
        data = config.item.cache[uid].data
        item = config.workspace_cache.create_item(uid, copy.deepcopy(data))
        item["_type"] = data["_type"]
        config.set_file(item)
        item.save()


def _action_load_workspace_items(config: _ConfigItem,
                                 action: Dict[str, Any]) -> None:
    action_name = action["action-name"]
    path = config.substitute(action["path"])
    config["spec-directory"] = path
    config.variant.item["enabled"] = config.variant["enabled"]
    logging.info("%s: add workspace items to: %s", action_name, path)
    new = set(config.item.cache.keys())
    _new_workspace_items(config, action_name, new)
    _set_types(config.workspace_cache, action)


def _action_finalize_workspace_items(config: _ConfigItem,
                                     action: Dict[str, Any]) -> None:
    action_name = action["action-name"]
    new = set(config.item.cache.keys())
    _new_workspace_items(config, action_name, new)
    logging.info("%s: initialize workspace item links", action_name)
    config.workspace_cache.initialize_links()
    enabled_set = config.variant["enabled"]
    logging.info("%s: set workspace enabled: %s", action_name, enabled_set)
    config.workspace_cache.set_enabled(enabled_set)
    logging.info("%s: set workspace item types", action_name)
    config.workspace_cache.set_types(action["spec-type-root-uid"])
    config.workspace_director.clear()
    if action["verify"] and config["spec-verify"]:
        logging.info("%s: verify workspace items", action_name)
        logger = logging.getLogger()
        level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
        verify_config = {"root-type": action["spec-type-root-uid"]}
        status = verify(verify_config, config.workspace_cache)
        assert status.critical == 0
        assert status.error == 0
        logger.setLevel(level)
        logging.debug("%s: finished verifying workspace items", action_name)


def _action_make_deployment_directory(config: _ConfigItem,
                                      _action: Dict[str, Any]) -> None:
    deployment_directory = config.variant["deployment-directory"]
    assert not os.path.exists(deployment_directory)
    logging.info("workspace: create deployment directory: %s",
                 deployment_directory)
    os.makedirs(deployment_directory)


def _create_symbolic_links(action: Dict[str, Any],
                           unpacked_archive: DirectoryState) -> None:
    for symbolic_link in action["archive-symbolic-links"]:
        link = unpacked_archive.substitute(symbolic_link["link"])
        link_path = os.path.join(unpacked_archive.directory, link)
        target = unpacked_archive.substitute(symbolic_link["target"])
        target = os.path.relpath(target, os.path.dirname(link_path))
        logging.info("%s: create symbolic link from '%s' to '%s'",
                     action["action-name"], link_path, target)
        os.symlink(target, link_path)
        unpacked_archive.add_files([link])


def _apply_patches(config: _ConfigItem, action: Dict[str, Any],
                   unpacked_archive: DirectoryState) -> None:
    for patch in action["archive-patches"]:
        if patch["type"] == "inline":
            source = "-"
            stdin = config.substitute(patch["patch"]).encode("utf-8")
            logging.info("%s: apply inline patch: %s", action["action-name"],
                         stdin)
        else:
            assert patch["type"] == "file"
            source = patch["file"]
            stdin = None
            logging.info("%s: apply patch: %s", action["action-name"], source)
        command = [
            "git", "apply", "--apply", "--numstat", "--directory",
            unpacked_archive.directory, "-p", "1", "--unsafe-paths", source
        ]
        output = subprocess.check_output(command,
                                         stdin=stdin,
                                         cwd=config["toolchain-directory"])
        unpacked_archive.add_files([
            line.decode("utf-8").split("\t")[2]
            for line in output.splitlines()
        ])


def _action_unpack_archive(config: _ConfigItem, action: Dict[str,
                                                             Any]) -> None:
    data = _make_directory_state_data(config, action["destination-directory"],
                                      "unpacked-archive")
    archive_file = config.substitute(action["archive-file"])
    data["archive-file"] = os.path.basename(archive_file)
    for key in [
            "archive-hash", "archive-patches", "archive-symbolic-links",
            "archive-url", "copyrights-by-license", "description",
            "enabled-by", "links"
    ]:
        data[key] = action[key]
    unpacked_archive = _create_item(config, action, data,
                                    "qdp/directory-state/unpacked-archive")
    assert isinstance(unpacked_archive, DirectoryState)
    unpacked_archive.add_tarfile_members(archive_file,
                                         unpacked_archive.directory, True)
    assert hash_file(archive_file) == unpacked_archive["archive-hash"]
    unpacked_archive.compact()
    _create_symbolic_links(action, unpacked_archive)
    _apply_patches(config, action, unpacked_archive)
    unpacked_archive.load()
    config.try_save(unpacked_archive, "Unpack archive")


def _create_dummy(config: _ConfigItem, action: Dict[str, Any]) -> None:
    data = _make_root_data(config, "dummy")
    data["enabled-by"] = action["enabled-by"]
    dummy = _create_item(config, action, data, "qdp/dummy")
    if dummy is None:
        return
    config.try_save(dummy, "Add dummy item")


_ACTIONS = {
    "add-item": _action_add_item,
    "copy-directory": _action_copy_directory,
    "copy-file": _action_copy_file,
    "copy-test-log": _action_copy_test_log,
    "finalize-workspace-items": _action_finalize_workspace_items,
    "git-clone": _action_git_clone,
    "load-items": _action_load_items,
    "load-workspace-items": _action_load_workspace_items,
    "make-deployment-directory": _action_make_deployment_directory,
    "make-item": _action_make_item,
    "make-uuid-item": _action_make_uuid_item,
    "unpack-archive": _action_unpack_archive
}

_NEEDS_DUMMY = [
    "add-item", "copy-directory", "copy-file", "copy-test-log", "git-clone",
    "make-item", "unpack-archive"
]


def _run_actions(config: _ConfigItem, when: int,
                 actions: List[Dict[str, Any]]) -> None:
    logging.info("workspace: run actions at: %i", when)
    for action in actions:
        action_type = action["action-type"]
        if config.is_enabled(action["enabled-by"]):
            logging.info("%s: run action", action["action-name"])
            _ACTIONS[action_type](config, action)
        else:
            logging.info("%s: action is disabled", action["action-name"])
            if action_type in _NEEDS_DUMMY:
                _create_dummy(config, action)


def _toolchain_commit(toolchain_directory: str) -> str:
    stdout: List[str] = []
    status = run_command(["git", "rev-parse", "HEAD"], toolchain_directory,
                         stdout)
    assert status == 0
    return stdout[0].strip()


def main(argv: List[str]) -> None:
    """
    Creates a QDP workspace directory according to the configuration files.
    """
    parser = create_build_argument_parser()
    parser.add_argument("--prefix",
                        help="the prefix directory",
                        default="/tmp/qdp")
    parser.add_argument("--cache-directory",
                        help="the config cache directory",
                        default="config-cache")
    parser.add_argument('config_files', nargs='+')
    args = parser.parse_args(argv)
    init_logging(args)
    config_cache_config: Dict[str, Any] = {
        "cache-directory": os.path.abspath(args.cache_directory),
        "enabled": [],
        "resolve-proxies": False,
        "initialize-links": False,
        "paths": [],
        "spec-type-root-uid": None,
    }
    config_cache = ItemCache(config_cache_config)
    factory = create_build_item_factory()
    director = PackageBuildDirector(config_cache, factory)
    config_item = Item(
        config_cache, "/qdp/config", {
            "SPDX-License-Identifier":
            "CC-BY-SA-4.0 OR BSD-2-Clause",
            "copyrights":
            ["Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG"]
        })
    config_item["_type"] = "config"
    config = _ConfigItem(director, config_item, factory)
    config["prefix-directory"] = os.path.abspath(args.prefix)
    config["spec-verify"] = not args.no_spec_verify
    toolchain_directory = os.path.abspath(os.path.dirname(__file__))
    logging.info("workspace: toolchain directory: %s", toolchain_directory)
    config["toolchain-directory"] = toolchain_directory
    config["toolchain-commit"] = _toolchain_commit(toolchain_directory)
    config["enabled"] = []
    actions_at: Dict[int, List[Dict[str, Any]]] = {}
    for file in args.config_files:
        logging.info("workspace: load configuration from: %s", file)
        for action in load_config(file)["workspace-actions"]:
            actions_at.setdefault(action["action-when"], []).append(action)
    for when, actions in sorted(actions_at.items()):
        _run_actions(config, when, actions)
    config.workspace_director.build_package(args.only, args.force)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
