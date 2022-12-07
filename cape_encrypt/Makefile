# Make commands specific to cape_encrypt
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
	pytest cape_encrypt

.PHONY: ci-ready
ci-ready: fmt lint test

# Releasing
.PHONY: bump-prep
bump-prep:
	pip install --upgrade bump2version

.PHONY: bump-patch
bump-patch: bump-prep
	bump2version patch --verbose

.PHONY: bump-minor
bump-minor: bump-prep
	bump2version minor --verbose

.PHONY: bump-major
bump-major: bump-prep
	bump2version major --verbose


