from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_session
from app.main import app

ROOT = Path(__file__).resolve().parents[1]

test_database_url = settings.test_database_url

if test_database_url is None:
    raise RuntimeError("TEST_DATABASE_URL must be set (environment or .env)")

if not str(test_database_url.path).endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must point to TEST database")

TEST_DATABASE_URL = str(test_database_url)


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = TEST_DATABASE_URL
    return config


@pytest.fixture(scope="session")
def engine(alembic_config: Config) -> Iterator[Engine]:
    engine = create_engine(TEST_DATABASE_URL)
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")

        yield session

        session.close()
        transaction.rollback()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
