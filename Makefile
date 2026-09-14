.PHONY: lint format-check format check typecheck test up sync migrate migration

up:
	docker compose up -d --build

sync:
	uv sync --group dev

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(m)"

lint:
	uv run ruff check src tests

format-check:
	uv run ruff format --check src tests

format:
	uv run ruff format src tests
	uv run ruff check src tests --fix

typecheck:
	uv run mypy

test:
	uv run pytest

check: lint format-check typecheck test
