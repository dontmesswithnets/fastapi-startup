# fastapi-startup

HTTP API built with FastAPI, SQLAlchemy 2, Pydantic v2, and PostgreSQL 17.

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
docker compose up -d
```

Postgres is published on `127.0.0.1:5432` only. Wait until the service is healthy (`docker compose ps`).

### Install dependencies

```bash
uv sync --group dev
```

### Run the API

From the repository root:

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Process liveness. Does not touch the database. |
| `GET` | `/health/db` | Opens a SQLAlchemy session and runs `SELECT 1`. |

Interactive OpenAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/health/db
```

Both return `{"status":"ok"}` when the corresponding check succeeds.

## Development

```bash
make lint
make format
make typecheck
```

`lint` and `typecheck` are read-only. `format` rewrites files under `src/`.
