# SPDX-License-Identifier: BSD-2-Clause
""" This module provides the default build item factory. """

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

from rtemsspec.archiver import Archiver
from rtemsspec.directorystate import DirectoryState
from rtemsspec.gcdaproducer import GCDAProducer
from rtemsspec.membenchcollector import MembenchCollector
from rtemsspec.packagebuild import BuildItemFactory, PackageVariant
from rtemsspec.packagechanges import PackageChanges
from rtemsspec.packagemanual import PackageManualBuilder
from rtemsspec.reposubset import RepositorySubset
from rtemsspec.rtems import RTEMSItemCache
from rtemsspec.runactions import RunActions
from rtemsspec.runtests import RunTests, TestLog
from rtemsspec.sphinxbuilder import SphinxBuilder, SphinxSection
from rtemsspec.sreldbuilder import SRelDBuilder
from rtemsspec.testrunner import DummyTestRunner, GRMONManualTestRunner, \
    SubprocessTestRunner


def create_build_item_factory() -> BuildItemFactory:
    """ Creates the default build item factory. """
    factory = BuildItemFactory()
    factory.add_constructor("qdp/build-step/archive", Archiver)
    factory.add_constructor("qdp/build-step/gcda-producer", GCDAProducer)
    factory.add_constructor("qdp/build-step/membench-collector",
                            MembenchCollector)
    factory.add_constructor("qdp/build-step/repository-subset",
                            RepositorySubset)
    factory.add_constructor("qdp/build-step/rtems-item-cache", RTEMSItemCache)
    factory.add_constructor("qdp/build-step/run-actions", RunActions)
    factory.add_constructor("qdp/build-step/run-tests", RunTests)
    factory.add_constructor("qdp/build-step/sphinx/ddf-sreld", SRelDBuilder)
    factory.add_constructor("qdp/build-step/sphinx/generic", SphinxBuilder)
    factory.add_constructor("qdp/build-step/sphinx/package-manual",
                            PackageManualBuilder)
    factory.add_constructor("qdp/directory-state/generic", DirectoryState)
    factory.add_constructor("qdp/directory-state/repository", DirectoryState)
    factory.add_constructor("qdp/directory-state/test-log", TestLog)
    factory.add_constructor("qdp/directory-state/unpacked-archive",
                            DirectoryState)
    factory.add_constructor("qdp/package-changes", PackageChanges)
    factory.add_constructor("qdp/sphinx-section", SphinxSection)
    factory.add_constructor("qdp/test-runner/dummy", DummyTestRunner)
    factory.add_constructor("qdp/test-runner/grmon-manual",
                            GRMONManualTestRunner)
    factory.add_constructor("qdp/test-runner/subprocess", SubprocessTestRunner)
    factory.add_constructor("qdp/variant", PackageVariant)
    return factory
