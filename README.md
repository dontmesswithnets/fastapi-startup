# fastapi-startup

HTTP API built with FastAPI, SQLAlchemy 2, Pydantic v2, Jinja2, and PostgreSQL 17. Schema changes go through Alembic. The root path serves an HTML page; health checks remain JSON. User creation is JSON under `/api`.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose

## Getting started

### Clone

```bash
git clone https://github.com/dontmesswithnets/fastapi-startup.git
cd fastapi-startup
```

### Configure

```bash
cp .env.example .env
```

Fill in `.env`. Compose reads `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to create the database. The app reads `DATABASE_URL`. Those values must describe the same user, password, and database.

`TEST_DATABASE_URL` is read only by pytest and must point to a **separate** database whose name ends with `_test`. The app never uses it. See Tests below.

Both URLs use the psycopg 3 dialect, for example:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/DBNAME
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/DBNAME_test
```

Settings are loaded with pydantic-settings: environment variables take precedence over `.env`. Locally everything comes from `.env`; in CI there is no `.env` and the values come from the workflow environment.

`POSTGRES_HOST` and `POSTGRES_PORT` document the host-side address (`127.0.0.1` and `5432`). They are not read by Compose or the application.

### Start PostgreSQL

```bash
make db
```

Same as `docker compose up -d`. Postgres is published on `127.0.0.1:5432` only. Wait until the service is healthy (`docker compose ps`).

### Install dependencies

```bash
make sync
```

Same as `uv sync --group dev`.

### Apply migrations

```bash
uv run alembic upgrade head
```

Applies files under `alembic/versions/` to Postgres. Alembic reads `DATABASE_URL` from `.env`, same as the app. The first revision creates the `users` table. Run this again after pulling new migrations.

### Run the API

From the repository root:

```bash
make run
```

Same as `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`. Then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | HTML homepage from `src/app/templates/index.html` (Jinja2). |
| `GET` | `/health` | Process liveness. Does not touch the database. |
| `GET` | `/health/db` | Opens a SQLAlchemy session and runs `SELECT 1`. |
| `POST` | `/api/users/` | Create a user. JSON body: `email` and `password` (8–64 characters). |

Homepage: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

Interactive OpenAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/health/db
curl -s -X POST http://127.0.0.1:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"your-password"}'
```

Both health routes return `{"status":"ok"}` when the corresponding check succeeds.

`POST /api/users/` returns `201` with `id`, `email`, and `created_at`. The password is stored hashed and is not in the response. A duplicate email returns `409`. Invalid email or password length returns `422`. The trailing slash is part of the path.

## Development

```bash
make db
make sync
uv run alembic upgrade head
make run
make lint
make format-check
make format
make typecheck
make test
make check
```

`db`, `sync`, `alembic upgrade head`, and `run` match the Getting started commands. `lint` (`ruff check`), `format-check` (`ruff format --check`), and `typecheck` (`mypy`) are read-only. `format` rewrites files under `src/` and `tests/`. `test` is `uv run pytest`; see Tests below. `check` runs `lint`, `format-check`, `typecheck`, and `test` in that order; it is the same command CI runs, so run it before pushing.

New model changes need a revision, then the same `upgrade`:

```bash
uv run alembic revision --autogenerate -m "short message"
```

Review the generated file under `alembic/versions/` before applying it.

## Tests

Pytest covers `POST /api/users/` (201, duplicate email 409, short password 422). Tests use FastAPI `TestClient` and the same Postgres server as `make db`, but a **second database** given by `TEST_DATABASE_URL`. They never touch the database in `DATABASE_URL`.

Create that database once. The name must match the last path segment of `TEST_DATABASE_URL` and end with `_test`; the example uses `startup_test`:

```bash
make db
docker compose exec postgres psql -U "$POSTGRES_USER" -d postgres -c 'CREATE DATABASE startup_test;'
```

If `$POSTGRES_USER` is empty in the shell, pass the same user as in `.env`. List databases with `\l` inside `psql` to confirm both databases exist.

Then:

```bash
make test
```

Same as `uv run pytest`. How the fixtures in `tests/conftest.py` work:

- `engine` (once per session) creates a SQLAlchemy engine for `TEST_DATABASE_URL` and runs `alembic upgrade head` against it. You do not run Alembic on the test database by hand.
- `session` (per test) opens a connection, begins a transaction, and yields a `Session` bound to it. After the test the transaction is rolled back, so tests leave no rows behind and do not depend on each other.
- `client` (per test) overrides the app's `get_session` dependency with that session via `app.dependency_overrides` and yields a `TestClient`. Requests made through the client run inside the test transaction.

Postgres must be healthy (`docker compose ps`). If `TEST_DATABASE_URL` is unset or its database name does not end with `_test`, pytest fails at collection with a `RuntimeError`.

## CI

GitHub Actions runs `.github/workflows/ci.yml` on every push to `main` and on every pull request targeting `main`. The job starts a `postgres:17-alpine` service with a database named `startup_test`, installs dependencies with `uv sync --group dev`, and runs `make check`.

There is no `.env` in CI. `DATABASE_URL` and `TEST_DATABASE_URL` are set in the workflow `env` block. `DATABASE_URL` points to a database that does not exist on purpose: the app engine is never used by tests, and if something reaches it the run fails loudly instead of writing to the test database.

Run `make check` locally before pushing; it is the same command CI runs.
