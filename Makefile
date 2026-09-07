.PHONY: lint format typecheck test db sync run

db:
	docker compose up -d

sync:
	uv sync --group dev

run:
	uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000


lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check src tests --fix

typecheck:
	uv run mypy

test:
	uv run pytest