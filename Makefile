PY_SRC_FILES = $(wildcard *.py) $(wildcard rtemsqual/*.py)
PY_ALL_FILES = $(PY_SRC_FILES) $(wildcard rtemsqual/tests/*.py)

all: $(PY_SRC_FILES) | check-env
	coverage run -m pytest rtemsqual/tests
	yapf -i $(PY_ALL_FILES)
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
