# SPDX-License-Identifier: BSD-2-Clause
""" This module provides support for directory states. """

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

import base64
import fnmatch
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, \
    Set, Tuple, Union

from rtemsspec.items import Item, ItemGetValueContext, Link
from rtemsspec.packagebuild import BuildItem, BuildItemFactory, \
    PackageBuildDirector
from rtemsspec.util import hash_file

_Path = Union[Path, str]


def _get_file_path(ctx: ItemGetValueContext) -> str:
    index = max(ctx.index, 0)
    return f"{ctx.item['directory']}/{ctx.item['files'][index]['file']}"


def _get_file_path_without_extension(ctx: ItemGetValueContext) -> str:
    return os.path.splitext(_get_file_path(ctx))[0]


def _file_nop(_source: _Path, _target: _Path) -> None:
    pass


class DirectoryState(BuildItem):
    """ Maintains a directory state. """

    # pylint: disable=too-many-public-methods
    @classmethod
    def prepare_factory(cls, factory: BuildItemFactory,
                        type_name: str) -> None:
        BuildItem.prepare_factory(factory, type_name)
        factory.add_get_value(f"{type_name}:/file", _get_file_path)
        factory.add_get_value(f"{type_name}:/file-without-extension",
                              _get_file_path_without_extension)

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._discarded_files: Set[str] = set()
        self._files: Dict[str, Union[str, None]] = dict(
            (file_info["file"], file_info["hash"])
            for file_info in item["files"])

    def __iter__(self):
        yield from self.files()

    @property
    def directory(self) -> str:
        """ Returns the base directory of the directory state. """
        return self["directory"]

    @property
    def digest(self) -> str:
        the_digest = self.item["hash"]
        if the_digest is None:
            raise ValueError(f"{self.uid}: directory state hash is not set")
        return the_digest

    def _get_hash(self, _base: str, relative_file_path: str) -> str:
        digest = self._files[relative_file_path]
        assert digest is not None
        return digest

    def _hash_file(self, base: str, relative_file_path: str) -> str:
        file_path = os.path.join(base, relative_file_path)
        digest = hash_file(file_path)
        logging.debug("%s: file '%s' hash is %s", self.uid, file_path, digest)
        self._files[relative_file_path] = digest
        return digest

    def _add_hashes(self, base: str, hash_file_handler: Callable[[str, str],
                                                                 str]) -> str:
        overall_hash = hashlib.sha512()
        overall_hash.update(base.encode("utf-8"))
        for relative_file_path in sorted(self._files):
            digest = hash_file_handler(base, relative_file_path)
            overall_hash.update(relative_file_path.encode("utf-8"))
            overall_hash.update(digest.encode("utf-8"))
        self._update_item_files()
        digest = base64.urlsafe_b64encode(
            overall_hash.digest()).decode("ascii")
        logging.info("%s: directory '%s' hash is %s", self.uid, base, digest)
        self.item["hash"] = digest
        return digest

    def _directory_state_exclude(self, base: str, files: Set[str]) -> None:
        for exclude_item in self.item.parents("directory-state-exclude"):
            exclude_state = self.director[exclude_item.uid]
            assert isinstance(exclude_state, DirectoryState)
            exclude_files = files.intersection(
                os.path.relpath(path, base) for path in exclude_state)
            logging.info(
                "%s: exclude files of directory state %s: %s", self.uid,
                exclude_item.uid,
                [os.path.join(base, path) for path in sorted(exclude_files)])
            files.difference_update(exclude_files)

    def _load_from_patterns(self, base: str,
                            patterns: List[Dict[str, Any]]) -> None:
        logging.info("%s: load pattern defined directory state: %s", self.uid,
                     base)
        files: Set[str] = set()
        base_path = Path(base)
        for include_exclude in patterns:
            include = include_exclude["include"]
            logging.info("%s: add files matching '%s' in: %s", self.uid,
                         include, base)
            more = set(
                os.path.relpath(path, base) for path in base_path.glob(include)
                if not path.is_dir())
            for exclude in include_exclude["exclude"]:
                exclude_files = set(
                    path for path in more
                    if fnmatch.fnmatch(os.path.join("/", path), exclude))
                logging.info("%s: exclude files for pattern '%s': %s",
                             self.uid, exclude, [
                                 os.path.join(base, path)
                                 for path in sorted(exclude_files)
                             ])
                more.difference_update(exclude_files)
            files.update(more)
        self._directory_state_exclude(base, files)
        self._files = dict.fromkeys(files, None)

    def load(self) -> str:
        """ Loads the directory state and returns the overall hash. """
        base = self.directory
        patterns = self.item["patterns"]
        if patterns:
            self._load_from_patterns(base, patterns)
        else:
            logging.info("%s: load explicit directory state: %s", self.uid,
                         base)
        return self._add_hashes(base, self._hash_file)

    def lazy_load(self) -> str:
        """
        Loads the directory state if the overall hash is not present and
        returns the overall hash.
        """
        digest = self.item["hash"]
        if digest is not None:
            return digest
        return self.load()

    @property
    def file(self) -> str:
        """ Is the path of the first file of the file state. """
        return next(self.files())

    def files(self, base: Optional[str] = None) -> Iterator[str]:
        """ Yields the file paths of the directory state. """
        if base is None:
            base = self.directory
        for file_path in sorted(self._files):
            yield os.path.join(base, file_path)

    def files_and_hashes(
            self,
            base: Optional[str] = None) -> Iterator[Tuple[str, Optional[str]]]:
        """ Yields the file paths and hashes of the directory state. """
        if base is None:
            base = self.directory
        for file_path, file_hash in sorted(self._files.items()):
            yield os.path.join(base, file_path), file_hash

    def compact(self) -> None:
        """
        Removes the common prefix from the files and adds it to the base
        directory.
        """
        prefix = os.path.commonprefix(list(self._files.keys())).rstrip("/")
        if prefix and not os.path.isabs(prefix):
            self.item["directory"] = os.path.join(self.item["directory"],
                                                  prefix)
            self.item["hash"] = None
            self._files = dict(
                (os.path.relpath(path, prefix), None) for path in self._files)
            self._update_item_files()

    def _update_item_files(self):
        self.item["files"] = list({
            "file": path,
            "hash": digest
        } for path, digest in sorted(self._files.items()))

    def clear(self) -> None:
        """ Clears the file set of the directory state. """
        logging.info("%s: clear directory state", self.uid)
        self.item["hash"] = None
        self._files.clear()
        self._update_item_files()

    def invalidate(self) -> None:
        """ Invalidates the directory state. """
        logging.info("%s: invalidate directory state", self.uid)
        self.item["hash"] = None
        if self.item["patterns"]:
            self._files.clear()
        else:
            self._files = dict.fromkeys(self._files.keys(), None)
        self._update_item_files()

    def remove_files(self) -> None:
        """ Removes the files of the directory state. """
        for file in self.files():
            try:
                logging.info("%s: remove: %s", self.uid, file)
                os.remove(file)
            except FileNotFoundError:
                if self.item["patterns"]:
                    logging.warning("%s: file not found: %s", self.uid, file)
                else:
                    logging.debug("%s: file not found: %s", self.uid, file)

    def add_files(self, files: Iterable[_Path]) -> None:
        """ Adds the files to the file set of the directory state. """
        self.item["hash"] = None
        more = set(os.path.normpath(name) for name in files)
        self._directory_state_exclude(self.directory, more)
        self._files.update(dict.fromkeys(more, None))
        self._update_item_files()

    def set_files(self, files: Iterable[_Path]) -> None:
        """ Sets the file set of the directory state to the files. """
        self.clear()
        self.add_files(files)

    def _copy_file(self, source: _Path, target: _Path) -> None:
        logging.info("%s: copy '%s' to '%s'", self.uid, source, target)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)

    def _move_file(self, source: _Path, target: _Path) -> None:
        logging.info("%s: move '%s' to '%s'", self.uid, source, target)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.replace(source, target)

    def copy_file(self, source: _Path, target: _Path) -> None:
        """
        Copies the file from the source path to the target path.

        Adds the target file to the file set of the directory state.  The
        target path is relative to the base directory of the directory state.
        """
        self._copy_file(source, os.path.join(self.directory, target))
        self.add_files([target])

    def copy_files(self,
                   root_dir: _Path,
                   files: Iterable[_Path],
                   prefix: _Path = ".") -> None:
        """
        Copies the files relative to the root directory to the base directory
        of the directory state using the prefix.

        The base directory of the directory state and the prefix is prepended
        to the file path for each file before it is added to the directory
        state.  Adds the target files to the file set of the directory state.
        """
        file_list: List[str] = []
        base = self.directory
        for name in files:
            file_source = os.path.join(root_dir, name)
            file_list_path = os.path.join(prefix, name)
            file_list.append(file_list_path)
            file_target = os.path.join(base, file_list_path)
            self._copy_file(file_source, file_target)
        self.add_files(file_list)

    def _add_tree(self,
                  root_dir: _Path,
                  prefix: _Path,
                  file_op: Callable[[_Path, _Path], None],
                  excludes: Optional[List[str]] = None) -> None:
        file_list: List[str] = []
        base = self.directory
        for path, _, files in os.walk(os.path.abspath(root_dir)):
            for name in files:
                file_source = os.path.join(path, name)
                file_list_path = os.path.join(
                    prefix, os.path.relpath(file_source, root_dir))
                file_target = os.path.join(base, file_list_path)
                if excludes is None:
                    file_list.append(file_list_path)
                    file_op(file_source, file_target)
                else:
                    match_path = os.path.normpath(
                        os.path.join("/", file_list_path))
                    for exclude in excludes:
                        if fnmatch.fnmatch(match_path, exclude):
                            logging.info(
                                "%s: exclude file for pattern '%s': %s",
                                self.uid, exclude, file_target)
                            break
                    else:
                        file_list.append(file_list_path)
                        file_op(file_source, file_target)
        self.add_files(file_list)

    def add_tree(self,
                 root_dir: _Path,
                 prefix: _Path = ".",
                 excludes: Optional[List[str]] = None) -> None:
        """
        Adds the files of the directory tree starting at the root directory
        to the file set of the directory state.

        The added file path is relative to the root directory.  The prefix is
        prepended to the file path for each file before it is added to the
        directory state.  The files are not copied or moved.
        """
        self._add_tree(root_dir, prefix, _file_nop, excludes)

    def copy_tree(self,
                  root_dir: _Path,
                  prefix: _Path = ".",
                  excludes: Optional[List[str]] = None) -> None:
        """
        Adds the files of the directory tree starting at the root directory
        to the file set of the directory state.

        The added file path is relative to the root directory.  The prefix is
        prepended to the file path for each file before it is added to the
        directory state.  The files are copied.
        """
        self._add_tree(root_dir, prefix, self._copy_file, excludes)

    def move_tree(self,
                  root_dir: _Path,
                  prefix: _Path = ".",
                  excludes: Optional[List[str]] = None) -> None:
        """
        Adds the files of the directory tree starting at the root directory
        to the file set of the directory state.

        The added file path is relative to the root directory.  The prefix is
        prepended to the file path for each file before it is added to the
        directory state.  The files are moved.
        """
        self._add_tree(root_dir, prefix, self._move_file, excludes)

    def add_tarfile_members(self, archive: _Path, prefix: _Path,
                            extract: bool) -> None:
        """
        Appends the members of the archive to the file list of the directory
        state.

        For each member the prefix path and the member path are joined and then
        added to the file list of the directory state.  If extract is true,
        then the members of the archive are extracted to the prefix path.
        """
        extract_info = "and extract " if extract else ""
        logging.info("%s: add %smembers of '%s' using prefix '%s'", self.uid,
                     extract_info, archive, prefix)
        with tarfile.open(archive, "r") as tar_file:
            base = self.directory
            file_list = [
                os.path.relpath(os.path.join(prefix, info.name), base)
                for info in tar_file.getmembers() if not info.isdir()
            ]
            if extract:
                tar_file.extractall(prefix)
            self.add_files(file_list)

    def lazy_clone(self, other: "DirectoryState") -> str:
        """ Lazily clones the directory state. """
        logging.info("%s: lazy clone from: %s", self.uid, other.uid)
        # pylint: disable=protected-access
        current = set(self._files.keys())
        new = set(other._files.keys())
        base = self.directory
        other_base = other.directory
        for file in sorted(current.difference(new)):
            target = os.path.join(base, file)
            try:
                logging.info("%s: remove: %s", self.uid, target)
                os.remove(target)
            except FileNotFoundError:
                logging.warning("%s: file not found: %s", self.uid, target)
        for file in sorted(new.difference(current)):
            target = os.path.join(base, file)
            self._copy_file(os.path.join(other_base, file), target)
        for file in sorted(current.intersection(new)):
            target = os.path.join(base, file)
            if self._files[file] == other._files[file]:
                logging.info("%s: keep as is: %s", self.uid, target)
            else:
                self._copy_file(os.path.join(other_base, file), target)
        self._files = other._files.copy()
        return self._add_hashes(base, self._get_hash)

    def json_dump(self, data: Any) -> None:
        """ Dumps the data into the file of the directory state. """
        file_path = self.file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, sort_keys=True, indent=2)

    def json_load(self) -> Any:
        """ Loads the data from the file of the directory state. """
        with open(self.file, "r", encoding="utf-8") as file:
            return json.load(file)

    def save(self) -> None:
        """ Saves the directory state to the item file. """
        self.item.save()

    def has_changed(self, link: Link) -> bool:
        digest = self.digest
        return link["hash"] is None or digest != link["hash"]

    def discard(self) -> None:
        """ Discards the directory state. """
        logging.info("%s: discard", self.uid)
        self._discarded_files = set(self._files.keys())
        self.remove_files()
        self.invalidate()
        self.save()

    def refresh(self) -> None:
        """ Refreshes the directory state. """
        logging.info("%s: refresh", self.uid)
        self.load()
        self.commit("Update directory state")
