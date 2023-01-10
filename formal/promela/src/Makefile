# SPDX-License-Identifier: BSD-2-Clause
# https://gitrepos.estec.esa.int/external/rtems-smp-qualification-qual/-/blob/ef082e24b0047790c38a9bef14414849a2ba6d5b/Makefile

DIR_SRC = src
DIR_TESTS = $(DIR_SRC)/tests
COCO_SRC_FILES = $(wildcard *.coco $(DIR_SRC)/*.coco $(DIR_TESTS)/*.coco)
PY_GEN_FILES = $(patsubst %.coco,%.py,$(COCO_SRC_FILES))

.PHONY: all py check format analyse metric git-hash-object-calculate sha512sum-calculate check-env coverage-report env clean

all: check format analyse coverage-report

%.py: %.coco | check-env
	coconut --target 3 $< $@

py: $(PY_GEN_FILES) | check-env

check: $(PY_GEN_FILES) | check-env
	coverage run --branch -m pytest --capture=tee-sys -vv -s $(DIR_TESTS)/test_coverage_testgen.py $(DIR_TESTS)/test_coverage_spin2test.py

format: $(PY_GEN_FILES) | check-env
	yapf -i --parallel $^

analyse: $(PY_GEN_FILES) | check-env
	flake8 $^
	mypy $^
	pylint --disable=duplicate-code --disable=unspecified-encoding --disable=consider-using-dict-items --disable=use-list-literal --disable=consider-using-with $^

metric: $(PY_GEN_FILES) | check-env
	python3 metrics.py $(PY_GEN_FILES)

git-hash-object-calculate:
	git hash-object $(COCO_SRC_FILES)

sha512sum-calculate:
	sha512sum $(COCO_SRC_FILES)

check-env:
	test -n "$$VIRTUAL_ENV"

EMPTY :=
SPACE := $(EMPTY) $(EMPTY)
COMMA := ,

coverage-report: | check-env
	coverage report -m --fail-under=100 --include=$(subst $(SPACE),$(COMMA),$(PY_GEN_FILES))

# sudo apt-get install python3-venv python3-dev
env:
	python3 -m venv env
	. env/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

clean:
	rm -rf $(PY_GEN_FILES) .coverage .mypy_cache .pytest_cache
	find $(DIR_SRC) -name __pycache__ -exec rm -rf '{}' +
