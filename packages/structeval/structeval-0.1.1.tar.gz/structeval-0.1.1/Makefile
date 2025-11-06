.PHONY: help install lint type test cov precommit docs serve format

help:
	@echo "Targets: install, lint, type, test, cov, precommit, docs, serve, format"

install:
	uv pip install -e .[dev,docs]

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-fix:
	uv run ruff check . --fix

format:
	uv run ruff format .

type:
	uv run mypy .

test:
	uv run pytest -q

cov:
	uv run pytest --cov=structeval --cov-report=term-missing

precommit:
	uv run pre-commit run --all-files

docs:
	uv run mkdocs build

serve:
	uv run mkdocs serve -a 127.0.0.1:8000

venv:
	uv venv


