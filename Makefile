PY_SRC_FILES = $(wildcard *.py) $(wildcard rtemsspec/*.py)
PY_ALL_FILES = $(PY_SRC_FILES) $(wildcard rtemsspec/tests/*.py)

all: check format analyse coverage-report

check: check-env
	coverage run --branch -m pytest -vv rtemsspec/tests

format: $(PY_ALL_FILES) | check-env
	yapf -i --parallel $^

analyse: $(PY_SRC_FILES) | check-env
	flake8 $^
	mypy $^
	pylint --disable=no-self-use $^

check-env:
	test -n "$$VIRTUAL_ENV"

EMPTY :=
SPACE := $(EMPTY) $(EMPTY)
COMMA := ,

coverage-report:
	coverage report -m --fail-under=100 --include=$(subst $(SPACE),$(COMMA),$(PY_SRC_FILES))

.PHONY: env

env:
	test -z "$$VIRTUAL_ENV"
	python3 -m venv env
	. env/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	echo -e "#!/bin/sh\n$$(which python3-config) "'$$@' > env/bin/python3-config
	chmod +x env/bin/python3-config
