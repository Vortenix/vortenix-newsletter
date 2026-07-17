.PHONY: install format lint typecheck test coverage docs check clean db-init demo release
install:
	python -m pip install -e ".[dev]"
format:
	ruff format .
lint:
	python -m ruff check src tests examples
typecheck:
	python -m mypy
test:
	python -m pytest
coverage:
	python -m pytest --cov=vortenix_newsletter --cov-report=term-missing --cov-report=xml
docs:
	python scripts/validate_docs.py
check: lint typecheck test docs
clean:
	python scripts/clean.py
db-init:
	python -m vortenix_newsletter.cli.app db init
demo: db-init
	python -m vortenix_newsletter.cli.app workflow run-daily --demo
release: check
	python -m pip wheel --no-deps --wheel-dir dist .
