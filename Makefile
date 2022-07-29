.PHONY: pydep
pydep:
	pip install -r requirements/base.txt -r requirements/dev.txt

.PHONY: pylib
pylib:
	pip install -e .

.PHONY: pydep-upgrade
pydep-upgrade:
	pip install -U pip-tools
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=requirements/base.txt requirements/base.in
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=requirements/dev.txt requirements/dev.in
	pip install -r requirements/base.txt -r requirements/dev.txt

.PHONY: install
install: pydep pylib

.PHONY: install-release
install-release:
	pip install -r requirements/base.txt
	pip install .

.PHONY: fmt
fmt:
	isort .
	black .

.PHONY: lint
lint:
	flake8 .

.PHONY: test
test:
	pytest

.PHONY: test-ci
test-ci: test


.PHONY: ci-ready
ci-ready: fmt lint test-ci