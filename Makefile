.PHONY: pydep
pydep:
	pip install -r requirements.txt
	cd hpke_spec && maturin develop

.PHONY: pylib
pylib:
	python setup.py develop

.PHONY: pydep-upgrade
pydep-upgrade:
	pip install -U pip-tools
	pip-compile --output-file=requirements.txt requirements.in
	pip install -r requirements.txt
	cd hpke_spec && maturin develop

.PHONY: install
install: pydep pylib

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