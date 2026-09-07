import os
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
env = dotenv_values(ROOT / ".env")

database_url = env.get("DATABASE_URL")
postgres_db = env.get("POSTGRES_DB")

if not database_url or not postgres_db:
    raise RuntimeError("DATABASE_URL and POSTGRES_DB must be set in .env")

parsed_url = urlparse(database_url)

if parsed_url.path != f"/{postgres_db}":
    raise RuntimeError("DATABASE_URL database name must match POSTGRES_DB")

test_database_url = urlunparse(parsed_url._replace(path=f"/{postgres_db}_test"))

if not isinstance(test_database_url, str):
    raise TypeError("DATABASE_URL must be a string")

os.environ["DATABASE_URL"] = test_database_url
config = Config(str(ROOT / "alembic.ini"))


from app.core.config import settings
from app.core.database import SessionFactory
from app.main import app
from app.models import User

if settings.database_url.path != f"/{postgres_db}_test":
    raise RuntimeError("Tests must only be run using the test database!")


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    command.upgrade(config, "head")


@pytest.fixture
def client(apply_migrations: None) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    with SessionFactory() as session:
        session.execute(delete(User))
        session.commit()
