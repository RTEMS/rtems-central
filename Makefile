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

PREFIX = /opt/rtems

PACKAGE_VERSION = 0

RTEMS_API = 6

LOG_LEVEL = DEBUG

GR712RC_SMP_PKG = $(PREFIX)/rtems-$(RTEMS_API)-sparc-gr712rc-smp-$(PACKAGE_VERSION)

GR712RC_SMP_LOG = $(GR712RC_SMP_PKG)-log.txt

gr712rc-smp-clean:
	rm -rf $(GR712RC_SMP_PKG) $(GR712RC_SMP_LOG)

gr712rc-smp-update:
	./qdp_workspace.py --prefix $(PREFIX) --log-file=$(GR712RC_SMP_LOG) --log-level=$(LOG_LEVEL) config/base.yml config/variant-sparc-gr712rc-smp.yml

gr712rc-smp-new: gr712rc-smp-clean gr712rc-smp-update

GR712RC_UNI_PKG = $(PREFIX)/rtems-$(RTEMS_API)-sparc-gr712rc-uni-$(PACKAGE_VERSION)

GR712RC_UNI_LOG = $(GR712RC_UNI_PKG)-log.txt

gr712rc-uni-clean:
	rm -rf $(GR712RC_UNI_PKG) $(GR712RC_UNI_LOG)

gr712rc-uni-update:
	./qdp_workspace.py --prefix $(PREFIX) --log-file=$(GR712RC_UNI_LOG) --log-level=$(LOG_LEVEL) config/base.yml config/variant-sparc-gr712rc-uni.yml

gr712rc-uni-new: gr712rc-uni-clean gr712rc-uni-update

GR740_SMP_PKG = $(PREFIX)/rtems-$(RTEMS_API)-sparc-gr740-smp-$(PACKAGE_VERSION)

GR740_SMP_LOG = $(GR740_SMP_PKG)-log.txt

gr740-smp-clean:
	rm -rf $(GR740_SMP_PKG) $(GR740_SMP_LOG)

gr740-smp-update:
	./qdp_workspace.py --prefix $(PREFIX) --log-file=$(GR740_SMP_LOG) --log-level=$(LOG_LEVEL) config/base.yml config/variant-sparc-gr740-smp.yml

gr740-smp-new: gr740-smp-clean gr740-smp-update

GR740_UNI_PKG = $(PREFIX)/rtems-$(RTEMS_API)-sparc-gr740-uni-$(PACKAGE_VERSION)

GR740_UNI_LOG = $(GR740_UNI_PKG)-log.txt

gr740-uni-clean:
	rm -rf $(GR740_UNI_PKG) $(GR740_UNI_LOG)

gr740-uni-update:
	./qdp_workspace.py --prefix $(PREFIX) --log-file=$(GR740_UNI_LOG) --log-level=$(LOG_LEVEL) config/base.yml config/variant-sparc-gr740-uni.yml

gr740-uni-new: gr740-uni-clean gr740-uni-update
