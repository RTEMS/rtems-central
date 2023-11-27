# SPDX-License-Identifier: BSD-2-Clause
""" This module provides a build item to run tests. """

# Copyright (C) 2022, 2023 embedded brains GmbH & Co. KG
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

import datetime
import logging
import multiprocessing
import os
import queue
import subprocess
from subprocess import run as subprocess_run
import tarfile
import time
import threading
from typing import Any, Dict, List, NamedTuple

from rtemsspec.items import Item, ItemGetValueContext
from rtemsspec.packagebuild import BuildItem, PackageBuildDirector

Report = Dict[str, Any]


class Executable(NamedTuple):
    """ This data class represents a test executable. """
    path: str
    digest: str
    timeout: int


class TestRunner(BuildItem):
    """ Runs the tests. """

    def __init__(self, director: PackageBuildDirector, item: Item):
        super().__init__(director, item)
        self._executable = "/dev/null"
        self._executables: List[Executable] = []
        self.mapper.add_get_value(f"{self.item.type}:/test-executable",
                                  self._get_test_executable)
        self.mapper.add_get_value(f"{self.item.type}:/test-executables-grmon",
                                  self._get_test_executables_grmon)

    def _get_test_executable(self, _ctx: ItemGetValueContext) -> Any:
        return self._executable

    def _get_test_executables_grmon(self, _ctx: ItemGetValueContext) -> Any:
        return " \\\n".join(
            os.path.basename(executable.path)
            for executable in self._executables)

    def run_tests(self, executables: List[Executable]) -> List[Report]:
        """
        Runs the test executables and produces a log file of the test run.
        """
        self._executables = executables
        return []


class DummyTestRunner(TestRunner):
    """ Cannot run the tests. """

    def run_tests(self, _executables: List[Executable]) -> List[Report]:
        """ Raises an exception.  """
        raise IOError("this test runner cannot run tests")


class GRMONManualTestRunner(TestRunner):
    """ Provides scripts to run the tests using GRMON. """

    def run_tests(self, executables: List[Executable]) -> List[Report]:
        super().run_tests(executables)
        base = self["script-base-path"]
        dir_name = os.path.basename(base)
        grmon_name = f"{base}.grmon"
        shell_name = f"{base}.sh"
        tar_name = f"{base}.tar.xz"
        os.makedirs(os.path.dirname(base), exist_ok=True)
        with tarfile.open(tar_name, "w:xz") as tar_file:
            with open(grmon_name, "w", encoding="utf-8") as grmon_file:
                grmon_file.write(self["grmon-script"])
            tar_file.add(grmon_name, os.path.join(dir_name, "run.grmon"))
            with open(shell_name, "w", encoding="utf-8") as shell_file:
                shell_file.write(self["shell-script"])
            tar_file.add(shell_name, os.path.join(dir_name, "run.sh"))
            for executable in executables:
                tar_file.add(
                    executable.path,
                    os.path.join(dir_name, os.path.basename(executable.path)))
        raise IOError(f"Run the tests provided by {tar_name}")


def _now_utc() -> str:
    return datetime.datetime.utcnow().isoformat()


class _Job:
    # pylint: disable=too-few-public-methods
    def __init__(self, executable: Executable, command: List[str]):
        self.report: Report = {
            "executable": executable.path,
            "executable-sha512": executable.digest,
            "command-line": command
        }
        self.timeout = executable.timeout


def _worker(work_queue: queue.Queue, item: BuildItem):
    with open(os.devnull, "rb") as devnull:
        while True:
            try:
                job = work_queue.get_nowait()
            except queue.Empty:
                return
            logging.info("%s: run: %s", item.uid, job.report["command-line"])
            job.report["start-time"] = _now_utc()
            begin = time.monotonic()
            try:
                process = subprocess_run(job.report["command-line"],
                                         check=False,
                                         stdin=devnull,
                                         stdout=subprocess.PIPE,
                                         timeout=job.timeout)
                stdout = process.stdout.decode("utf-8")
            except subprocess.TimeoutExpired as timeout:
                if timeout.stdout is not None:
                    stdout = timeout.stdout.decode("utf-8")
                else:
                    stdout = ""
            except Exception:  # pylint: disable=broad-exception-caught
                stdout = ""
            output = stdout.rstrip().replace("\r\n", "\n").split("\n")
            job.report["output"] = output
            job.report["duration"] = time.monotonic() - begin
            logging.debug("%s: done: %s", item.uid, job.report["executable"])
            work_queue.task_done()


class SubprocessTestRunner(TestRunner):
    """ Runs the tests in subprocesses. """

    def run_tests(self, executables: List[Executable]) -> List[Report]:
        super().run_tests(executables)
        work_queue: queue.Queue[_Job] = \
            queue.Queue()  # pylint: disable=unsubscriptable-object
        jobs: List[_Job] = []
        for executable in executables:
            self._executable = executable.path
            job = _Job(executable, self["command"])
            jobs.append(job)
            work_queue.put(job)
        for _ in range(min(multiprocessing.cpu_count(), len(executables))):
            threading.Thread(target=_worker,
                             args=(work_queue, self),
                             daemon=True).start()
        work_queue.join()
        return [job.report for job in jobs]
