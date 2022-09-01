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

# Docs
.PHONY: install-docs
install-docs:
	pip install -U sphinx myst-parser sphinx-book-theme sphinx_autodoc_typehints

.PHONY: docs-clean
docs-clean:
	find docs/source -name "*.rst" ! -name "index.rst" -exec rm {} \+
	find docs/source -name "*.md" ! -name "walkthrough.md" -exec rm {} \+
	cd docs && \
	make clean && \
	cd ..

.PHONY: docs-prep
docs-prep: install-docs install-release docs-clean
	cp README.md docs/source/pycape-readme.md && \
	cp serdio/README.md docs/source/serdio-readme.md && \
	cd docs && \
	sphinx-apidoc -f -o source ../pycape "../pycape/*_test*" --separate && \
	sphinx-apidoc -f -o source ../serdio "../serdio/*_test*" --separate && \
	rm source/modules.rst && \
	cd ..

.PHONY: docs
docs: docs-prep
	cd docs && \
	make html && \
	cd ..