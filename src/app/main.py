from fastapi import FastAPI
from sqlalchemy import literal, select

from app.core.database import SessionDep

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db(session: SessionDep) -> dict[str, str]:
    session.execute(select(literal(1))).scalar_one()
    return {"status": "ok"}
