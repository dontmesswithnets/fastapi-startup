from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(str(settings.database_url))

SessionFactory = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session]:
    with SessionFactory() as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]