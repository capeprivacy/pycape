.PHONY: pydep
pydep:
	pip install -r requirements.txt -r requirements-dev.txt
	cd hpke_spec && maturin develop

.PHONY: pylib
pylib:
	python setup.py develop

.PHONY: pydep-upgrade
pydep-upgrade:
	pip install -U pip-tools
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=requirements.txt requirements.in
	CUSTOM_COMPILE_COMMAND="make pydep-upgrade" pip-compile --output-file=requirements-dev.txt requirements-dev.in
	pip install -r requirements.txt -r requirements-dev.txt
	cd hpke_spec && maturin develop

.PHONY: install
install: pydep pylib

.PHONY: install-release
install-release:
	pip install maturin -r requirements.txt
	maturin build -m hpke_spec/Cargo.toml --release -o ./wheelhouse
	pip install --no-index --find-links wheelhouse hpke_spec
	rm -R wheelhouse

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