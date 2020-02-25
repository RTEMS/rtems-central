all: *.py rtemsqual/*.py | check-env
	coverage run -m pytest tests
	yapf -i $^ tests/*.py
	flake8 $^
	mypy $^
	pylint $^

check-env:
	test -n "$$VIRTUAL_ENV"

coverage-report:
	coverage report -m --omit 'env/*'

.PONY: env

env:
	python3 -m venv env
	. env/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt
