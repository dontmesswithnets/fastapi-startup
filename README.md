# fastapi-startup

HTTP API built with FastAPI, SQLAlchemy 2, Pydantic v2, Jinja2, and PostgreSQL 17. Schema changes go through Alembic. The root path serves an HTML page; health checks remain JSON. User creation is JSON under `/api`.

The application runs in Docker. Docker Compose starts PostgreSQL, applies migrations, and starts the API in one command.

## Requirements

- Docker and Docker Compose
- Python 3.14+ and [uv](https://docs.astral.sh/uv/) for running lint, type checks, tests, and Alembic from the host

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

Fill in `.env`:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — Compose passes these to the Postgres container, which creates that user and database on first start. Compose also builds the `DATABASE_URL` for the `migrate` and `app` containers from them, so nothing else needs to match by hand.
- `DATABASE_URL` — used by tools you run **from the host**: `make migrate`, `make migration`. It must describe the same user, password, and database as the `POSTGRES_*` values, with host `127.0.0.1`.
- `TEST_DATABASE_URL` — read only by pytest. Must point to a **separate** database whose name ends with `_test`. The app never uses it. See Tests below.

Both URLs use the psycopg 3 dialect:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/DBNAME
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/DBNAME_test
```

Settings are loaded with pydantic-settings: environment variables take precedence over `.env`. On the host everything comes from `.env`. Inside containers there is no `.env`; Compose sets `DATABASE_URL` with host `postgres`, the service name on the Compose network.

### Start the stack

```bash
make up
```

Same as `docker compose up -d --build`. This builds the application image and starts three services in order:

1. `postgres` — PostgreSQL 17, published on `127.0.0.1:5432` only, data in the `pg_data` volume.
2. `migrate` — runs `alembic upgrade head` against `POSTGRES_DB` once Postgres is healthy, then exits.
3. `app` — starts `uvicorn` once `migrate` has exited successfully. Published on `127.0.0.1:8000`.

Check the result:

```bash
docker compose ps -a          # migrate should be "Exited (0)", app "Up"
docker compose logs migrate   # Alembic output
curl -s http://127.0.0.1:8000/health/db
```

Then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

### Install host tooling

```bash
make sync
```

Same as `uv sync --group dev`. Needed for `make check`, `make migrate`, and `make migration`. Not needed to run the API.

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

## Docker

### Image

`Dockerfile` builds the image in two stages:

- `builder` (based on `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`) copies `pyproject.toml` and `uv.lock` first and runs `uv sync --frozen --no-dev --no-install-project`, so the dependency layer is cached until the lock file changes. It then copies `src/`, `alembic/`, and `alembic.ini` and runs `uv sync --frozen --no-dev` to install the `app` package itself. `UV_COMPILE_BYTECODE=1` precompiles `.pyc` files so containers start faster.
- The final stage (based on `python:3.14-slim-bookworm`, no uv) copies `/app` from `builder`, puts `.venv/bin` on `PATH`, and runs as the unprivileged user `app`. Default command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

`.dockerignore` keeps `.env*`, `.venv/`, `tests/`, `.git/`, and IDE/cache directories out of the build context. Only the paths named in `COPY` end up in the image.

### Compose services

`migrate` and `app` share the same image (`fastapi-startup`); `migrate` overrides the command with `alembic upgrade head`. Their `DATABASE_URL` is defined once in the `x-app-environment` YAML anchor and reused by both.

Useful commands:

```bash
make up                       # build and start everything
docker compose ps -a          # include the exited migrate container
docker compose logs -f app    # follow application logs
docker compose down           # stop and remove containers, keep data
docker compose down -v        # also remove the pg_data volume (all data is lost)
```

After changing application code, run `make up` again; `--build` rebuilds only the layers that changed.

## Development

```bash
make up
make sync
make migrate
make migration m="short message"
make lint
make format-check
make format
make typecheck
make test
make check
```

`up` and `sync` match the Getting started commands.

`migrate` is `uv run alembic upgrade head` from the host against `DATABASE_URL`. The `migrate` container already does this on every `make up`; use `make migrate` when you have a new revision and do not want to rebuild the image to apply it.

`migration` is `uv run alembic revision --autogenerate -m "$(m)"`. Run it after changing a model, then review the generated file under `alembic/versions/` before applying it. Commit the model change and the revision together.

`lint` (`ruff check`), `format-check` (`ruff format --check`), and `typecheck` (`mypy`) are read-only. `format` rewrites files under `src/` and `tests/`. `test` is `uv run pytest`; see Tests below. `check` runs `lint`, `format-check`, `typecheck`, and `test` in that order; it is the same command CI runs, so run it before pushing.

## Tests

Pytest covers `POST /api/users/` (201, duplicate email 409, short password 422) and checks that the models match the migrations (`alembic check`). Tests use FastAPI `TestClient` and the Postgres container from `make up`, but a **second database** given by `TEST_DATABASE_URL`. They never touch the database in `DATABASE_URL`.

Create that database once. The name must match the last path segment of `TEST_DATABASE_URL` and end with `_test`; the example uses `startup_test`:

```bash
make up
docker compose exec postgres psql -U "$POSTGRES_USER" -d postgres -c 'CREATE DATABASE startup_test;'
```

If `$POSTGRES_USER` is empty in the shell, pass the same user as in `.env`. List databases with `\l` inside `psql` to confirm both databases exist. The database lives in the `pg_data` volume; after `docker compose down -v` you have to create it again.

Then:

```bash
make test
```

Same as `uv run pytest`. How the fixtures in `tests/conftest.py` work:

- `alembic_config` (once per session) builds an Alembic `Config` pointed at `TEST_DATABASE_URL`.
- `engine` (once per session) creates a SQLAlchemy engine for `TEST_DATABASE_URL` and runs `alembic upgrade head` against it. You do not run Alembic on the test database by hand.
- `session` (per test) opens a connection, begins a transaction, and yields a `Session` bound to it. After the test the transaction is rolled back, so tests leave no rows behind and do not depend on each other.
- `client` (per test) overrides the app's `get_session` dependency with that session via `app.dependency_overrides` and yields a `TestClient`. Requests made through the client run inside the test transaction.

`tests/test_migrations.py` runs `alembic check` against the migrated test database and fails if a model change has no matching revision.

Postgres must be healthy (`docker compose ps`). If `TEST_DATABASE_URL` is unset or its database name does not end with `_test`, pytest fails at collection with a `RuntimeError`.

## CI

GitHub Actions runs `.github/workflows/ci.yml` on every push to `main` and on every pull request targeting `main`. The job starts a `postgres:17-alpine` service with a database named `startup_test`, installs dependencies with `uv sync --group dev`, and runs `make check`.

There is no `.env` in CI. `DATABASE_URL` and `TEST_DATABASE_URL` are set in the workflow `env` block. `DATABASE_URL` points to a database that does not exist on purpose: the app engine is never used by tests, and if something reaches it the run fails loudly instead of writing to the test database.

Run `make check` locally before pushing; it is the same command CI runs.

The job also runs docker build . so a broken Dockerfile fails the pull request

