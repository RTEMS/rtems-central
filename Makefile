PY_SRC_FILES = $(wildcard *.py) $(wildcard rtemsqual/*.py)
PY_ALL_FILES = $(PY_SRC_FILES) $(wildcard rtemsqual/tests/*.py)

all: check format analyse coverage-report

check: check-env
	coverage run -m pytest -vv rtemsqual/tests

format: $(PY_ALL_FILES) | check-env
	yapf -i $^

analyse: $(PY_SRC_FILES) | check-env
	flake8 $^
	mypy $^
	pylint $^

check-env:
	test -n "$$VIRTUAL_ENV"

EMPTY :=
SPACE := $(EMPTY) $(EMPTY)
COMMA := ,

coverage-report:
	coverage report -m --include=$(subst $(SPACE),$(COMMA),$(PY_SRC_FILES))

.PONY: env

env:
	python3 -m venv env
	. env/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
