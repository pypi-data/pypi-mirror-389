# Contributing to structeval

Thanks for your interest in contributing!

## Setup

```bash
# optional: create a local venv
uv venv
. .venv/bin/activate  # optional; you can also use `uv run`

# install developer extras
uv pip install -e .[dev,docs]
uv run pre-commit install
```

## Workflow

- Create a feature branch
- Add tests for new behavior
- Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest`
- Submit a PR with a clear description

## Commit style

- Use conventional commits where possible: `feat:`, `fix:`, `docs:`, etc.

## Code style

- Functional-first design: prefer pure, stateless functions and immutability
- Strong typing: keep `mypy` happy with explicit types on public APIs


