from sqlmodel import SQLModel, Field, create_engine
from typing import Optional
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[1] / "db" / "uw.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


class Case(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str
    status: str = "new"  # new|extracted|validated|scored|summarized
    created_ts: str
    updated_ts: str


class Extract(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int
    raw_text: str = ""
    json_blob: str = ""  # validated fields JSON


class RulesRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int
    rules_version: str
    result_json: str  # pass/fail/warn payload


class Score(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int
    scorecard_version: str
    score_json: str


class AuditEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: Optional[int] = None
    actor: str = "local_user"
    event_type: str  # e.g., CREATE_CASE, EDIT_FIELD, RUN_RULES, etc.
    payload: str = ""
    ts: str


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print(f"Initialized DB at {DB_PATH}")
