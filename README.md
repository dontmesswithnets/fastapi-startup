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

`DATABASE_URL` uses the psycopg 3 dialect, for example:

```text
postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/DBNAME
```

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
make format
make typecheck
```

`db`, `sync`, `alembic upgrade head`, and `run` match the Getting started commands. `lint` and `typecheck` are read-only. `format` rewrites files under `src/`.

New model changes need a revision, then the same `upgrade`:

```bash
uv run alembic revision --autogenerate -m "short message"
```

Review the generated file under `alembic/versions/` before applying it.
