CI_FILES=pycape

ci: lint test coverage

fmt:
	poetry run isort --atomic ${CI_FILES}
	poetry run black ${CI_FILES}

lint:
	poetry run flake8 ${CI_FILES}

test:
	poetry run pytest

bootstrap:
	pip install poetry
	poetry install

coverage:
	poetry run pytest --cov-report=xml --cov=pycape ${CI_FILES}
	poetry run coverage report
