# SPDX-License-Identifier: BSD-2-Clause
""" Build step to package deployed components into archive. """

# Copyright (C) 2021 EDISOFT (https://www.edisoft.pt/)
# Copyright (C) 2020, 2021 embedded brains GmbH & Co. KG
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

import logging
import os
import stat
import tarfile
from typing import cast, Dict, List

from rtemsspec.packagebuild import BuildItem
from rtemsspec.directorystate import DirectoryState


def _check_for_duplicates(uid: str, members: List[DirectoryState]) -> None:
    logging.info("%s: check for duplicate files", uid)
    for index, dir_state in enumerate(members):
        logging.debug("%s: get files of: %s", uid, dir_state.uid)
        files = dict(dir_state.files_and_hashes())
        paths = set(files.keys())
        for file_path in files:
            assert os.path.isfile(file_path) or os.path.islink(file_path)
        for dir_state_2 in members[index + 1:]:
            logging.debug("%s: compare with files of: %s", uid,
                          dir_state_2.uid)
            files_2 = dict(dir_state_2.files_and_hashes())
            paths_2 = set(files_2.keys())
            duplicates = paths.intersection(paths_2)
            if duplicates:
                logging.info(
                    "%s: duplicate files in directory states "
                    "%s and %s", uid, dir_state.uid, dir_state_2.uid)
                for file_path in duplicates:
                    logging.info("%s: duplicate file: %s", uid, file_path)
                    value = files[file_path]
                    value_2 = files_2[file_path]
                    if value == value_2:
                        continue
                    logging.error(
                        "%s: inconsistent file hashes for '%s': %s != %s", uid,
                        file_path, value, value_2)


_SCRIPT_HEAD = """#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
\"\"\" Verifies the files of the package. \"\"\"

# Copyright (C) 2021, 2022 embedded brains GmbH & Co. KG
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
import binascii
import argparse
import hashlib
import logging
import os
import sys
from typing import Dict, List


_FILES = {
"""

_SCRIPT_TAIL = """}


def _hash_file(path: str) -> str:
    file_hash = hashlib.sha512()
    if os.path.islink(path):
        file_hash.update(os.readlink(path).encode("utf-8"))
    else:
        buf = bytearray(65536)
        memview = memoryview(buf)
        with open(path, "rb", buffering=0) as src:
            for size in iter(lambda: src.readinto(memview), 0):  # type: ignore
                file_hash.update(memview[:size])
    return base64.urlsafe_b64encode(file_hash.digest()).decode("ascii")


def _hex(digest: str) -> str:
    binary = base64.urlsafe_b64decode(digest)
    return binascii.hexlify(binary).decode('ascii')


def _check_file(file_path: str, expected_files: Dict[str, str]) -> int:
    expected_hash = expected_files[file_path]
    actual_hash = _hash_file(file_path)
    if expected_hash != actual_hash:
        logging.error(
            "expected hash is %s, actual hash is %s for file: %s",
            _hex(expected_hash), _hex(actual_hash), file_path)
        return 1
    return 0


def _verify_files(script: str, expected_files: Dict[str, str]) -> int:
    status = 0
    script = os.path.normpath(script)
    for path, dirs, files in os.walk("."):
        dirs.sort()
        for name in sorted(files):
            file_path = os.path.normpath(os.path.join(path, name))
            if file_path in expected_files:
                status = _check_file(file_path, expected_files)
                del expected_files[file_path]
            elif file_path != script:
                logging.warning("unexpected file: %s", file_path)
    for maybe_missing in expected_files.keys():
        if os.path.islink(maybe_missing):
            status = _check_file(maybe_missing, expected_files)
            continue
        logging.error("missing file: %s", maybe_missing)
        status = 1
    return status


def main(script: str, argv: List[str]) -> int:
    \"\"\" Verifies the files of the package. \"\"\"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        default="WARNING",
        help="log level")
    parser.add_argument("--log-file",
                        type=str,
                        default=None,
                        help="log to this file")
    parser.add_argument("--list-files",
                        action="store_true",
                        help="list the files of the package")
    parser.add_argument("--list-files-and-hashes",
                        action="store_true",
                        help="list the files of the package "
                        "with the SHA512 digest of each file")
    args = parser.parse_args(argv)
    logging.basicConfig(filename=args.log_file, level=args.log_level)
    expected_files = dict(
        zip(map(lambda x: os.path.normpath(x), _FILES.keys()),
            _FILES.values()))
    status = 0
    if args.list_files_and_hashes:
        for file_path, hash_value in expected_files.items():
            print(f"{file_path}\t{_hex(hash_value)}")
    elif args.list_files:
        for file_path in expected_files.keys():
            print(file_path)
    else:
        status = _verify_files(script, expected_files)
    return status



if __name__ == "__main__":
    status = main(sys.argv[0], sys.argv[1:])
    sys.exit(status)
"""


def _create_verification_script(script: str, archive_files: Dict[str,
                                                                 str]) -> None:
    with open(script, "w", encoding="utf-8") as out:
        out.write(_SCRIPT_HEAD)
        for file_path, hash_value in sorted(archive_files.items()):
            print(f"    \"{file_path}\": \"{hash_value}\",", file=out)
        out.write(_SCRIPT_TAIL)
    os.chmod(script, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


class Archiver(BuildItem):
    """
    The archiver adds the file of its directory state dependencies to an
    archive file.
    """

    def run(self) -> None:
        archive_file = self["archive-file"]
        archive_state = self.output("archive")
        assert isinstance(archive_state, DirectoryState)
        archive_state.set_files([archive_file])
        archive_file = os.path.join(archive_state.directory, archive_file)
        script_file = self["verification-script"]
        script_state = self.output("verify-package")
        assert isinstance(script_state, DirectoryState)
        script_state.set_files([script_file])
        script_file = os.path.join(script_state.directory, script_file)
        script_dir = os.path.dirname(script_file)
        logging.info("%s: create archive: %s", self.uid, archive_file)
        os.makedirs(os.path.dirname(archive_file), exist_ok=True)
        with tarfile.open(archive_file, "w:xz") as tar_file:
            members = cast(List[DirectoryState], list(self.inputs("member")))
            _check_for_duplicates(self.uid, members)
            strip_prefix = self["archive-strip-prefix"]
            archive_files: Dict[str, str] = {}
            for dir_state in members:
                logging.info("%s: add files of directory state: %s", self.uid,
                             dir_state.uid)
                for file_path, hash_value in dir_state.files_and_hashes():
                    verify_path = os.path.relpath(file_path, script_dir)
                    assert hash_value
                    archive_files[verify_path] = hash_value
                    tar_file.add(file_path,
                                 os.path.relpath(file_path, strip_prefix))
            _create_verification_script(script_file, archive_files)
            tar_file.add(script_file, os.path.relpath(script_file,
                                                      strip_prefix))
        logging.info("%s: finished to create archive: %s", self.uid,
                     archive_file)
