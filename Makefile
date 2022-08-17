# Dependency Management

.PHONY: pydep
pydep:
	pip install -r requirements/base.txt -r requirements/dev.txt

.PHONY: pylib
pylib:
	pip install -e .

.PHONY: pydep-upgrade
pydep-upgrade:
	pip install -U pip-tools
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=serdio/requirements.txt serdio/pyproject.toml
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=requirements/base.txt requirements/base.in
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=requirements/dev.txt requirements/dev.in
	pip install -r requirements/base.txt -r requirements/dev.txt

.PHONY: install
install: pydep pylib

.PHONY: install-release
install-release:
	pip install -r requirements/base.txt
	pip install .

# CI

.PHONY: fmt
fmt:
	isort .
	black .

.PHONY: lint
lint:
	flake8 .

.PHONY: test
test:
	pytest pycape

.PHONY: test-ci
test-ci: test
	pytest serdio

.PHONY: ci-ready
ci-ready: fmt lint test

# Releasing

.PHONY: bump-prep
bump-prep:
	pip install -U bumpver

.PHONY: bump-patch
bump-patch: bump-prep
	bumpver update --tag=final
	bumpver update --patch --tag=rc --no-tag-commit

.PHONY: bump-minor
bump-minor: bump-prep
	bumpver update --minor --tag=final
	bumpver update --patch --tag=rc --no-tag-commit

.PHONY: bump-major
bump-major: bump-prep
	bumpver update --major --tag=final
	bumpver update --patch --tag=rc --no-tag-commit
