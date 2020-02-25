# RTEMS Specification Items and Qualification Tools

This repository contains a prototype of the RTEMS specification and tools to
generate content from the specification.  It demonstrates the use of Python
development tools such as yapf, flake8, mypy, pylint, pytest, and coverage.

## Repository Overview

* env - contains the Python environment (created by `make env`)

* spec - contains the specification items

* rtemsqual - contains the `rtemsqual` Python package

* tests - contains Python unit tests

* external - contains Git submodules

  * rtems - contains the RTEMS sources as a Git submodule

  * rtems-docs - contains the RTEMS documentation sources as a Git submodule

* `rtems_spec_to_x.py` - a command line tool to generate content from the
  specification

## Getting Started

Run
```
git submodule init
git submodule update
```
to initialize the Git submodules.  Run
```
make env
```
to set up the Python environment.  Activate the Python environment afterwards
with
```
. env/bin/activate
```

## Specification Items

The
[specification items](https://docs.rtems.org/branches/master/eng/req-eng.html#specification-items)
are located in the `spec` directory.  You can use doorstop to work with them,
e.g.
```
$ doorstop
building tree...
loading documents...
validating items...

RTEMS
│
└── RTEMS-GLOS
    │
    └── RTEMS-GLOS-TERM
```

## Specification-To-X Tool

The command line tool `rtems_spec_to_x.py` generates content from the
specification.  The tool is configured by the `config.ini` configuration file.
This is a prototype implementation.  It demonstrates the generation of a
project-wide glossary (`external/rtems-docs/c-user/glossary.rst`) and
document-specific glossaries (`external/rtems-docs/eng/glossary.rst`) from
glossary specification items (glossary groups and terms in `spec/glos`).

Example:
```
$ ./rtems_spec_to_x.py
$ git status
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean
$ sed -i 's/Binary/Boom/' spec/glos/term/RTEMS-GLOS-TERM-ABI.yml
$ ./rtems_spec_to_x.py
$ git status
On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes in working directory)
  (commit or discard the untracked or modified content in submodules)

        modified:   external/rtems-docs (modified content)
        modified:   spec/glos/term/RTEMS-GLOS-TERM-ABI.yml

no changes added to commit (use "git add" and/or "git commit -a")
$ cd external/rtems-docs
$ git diff
diff --git a/c-user/glossary.rst b/c-user/glossary.rst
index d0996e8..dfac60c 100644
--- a/c-user/glossary.rst
+++ b/c-user/glossary.rst
@@ -10,7 +10,7 @@ Glossary
     :sorted:
 
     ABI
-        An acronym for Application Binary Interface.
+        An acronym for Application Boom Interface.
 
     active
         A term used to describe an object which has been created by an
diff --git a/eng/glossary.rst b/eng/glossary.rst
index c58e67f..ac2c8f8 100644
--- a/eng/glossary.rst
+++ b/eng/glossary.rst
@@ -9,7 +9,7 @@ Glossary
     :sorted:
 
     ABI
-        An acronym for Application Binary Interface.
+        An acronym for Application Boom Interface.
 
     API
         An acronym for Application Programming Interface.
```

## Unit Tests and Static Analysers

Run the unit tests and static analysers with:
```
make
```
You can get a coverage report with:
```
$ make coverage-report 
coverage report -m --omit 'env/*'
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
rtemsqual/__init__.py        5      0   100%
rtemsqual/content.py       120      0   100%
rtemsqual/glossary.py       73      0   100%
rtemsqual/items.py          93      0   100%
tests/test_content.py      114      0   100%
tests/test_glossary.py      33      0   100%
tests/test_items.py         47      0   100%
------------------------------------------------------
TOTAL                      485      0   100%
```

## Contributing

Please read
[Support and Contributing](https://docs.rtems.org/branches/master/user/support/index.html).

## License

This project is licensed under the
[BSD-2-Clause](https://spdx.org/licenses/BSD-2-Clause.html) or
[CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html).
