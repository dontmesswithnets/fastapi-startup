# Typical flow: make format --> make lint --> make typecheck
# format rewrites files; lint and typecheck do not.
# check is read-only (lint + mypy), for before-commit / CI.

.PHONY: lint format typecheck check

lint:
	uv run ruff check src

format:
	uv run ruff format src
	uv run ruff check src --fix

typecheck:
	uv run mypy
