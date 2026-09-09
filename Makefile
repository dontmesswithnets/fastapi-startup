.PHONY: lint format-check format check typecheck test db sync run migrate migration

db:
	docker compose up -d

sync:
	uv sync --group dev

run:
	uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

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
