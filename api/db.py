"""Persistence -- SQLModel over SQLite by default (Postgres via DATABASE_URL).

Tables:
    Run            -- one /api/simulate (or legacy /simulate) result.
    Recommendation -- one /api/optimize or /api/recommend/physics result.
    Calibration    -- one /api/calibrate (or .../demo) result.
    Job            -- background-job bookkeeping for api/jobs.py.

Kept deliberately simple: synchronous SQLModel `Session` per request via
`get_session()`, which is plenty for a single-process demo/hackathon
deployment (see docs/DEPLOY.md "known limits").
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from sqlmodel import Field, Session, SQLModel, create_engine

from .settings import ROOT, get_settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_database_url(url: str) -> str:
    """A relative `sqlite:///./data/twin.db` is resolved against ROOT (not
    the process cwd) and its parent directory is created up front, so the
    default works identically from a repo checkout, a Docker WORKDIR, or a
    test run from anywhere."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url
    raw = url[len(prefix):]
    if raw in (":memory:", ""):
        return url
    path = Path(raw)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return prefix + str(path).replace("\\", "/")


_settings = get_settings()
_DATABASE_URL = _resolve_database_url(_settings.database_url)
_connect_args = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(_DATABASE_URL, connect_args=_connect_args)


class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    steam_t: float
    soak_days: float
    cutoff_m3d: float
    spm: float
    summary_json: str
    source: str = "api"
    created_at: datetime = Field(default_factory=_utcnow)

    def summary(self) -> dict[str, Any]:
        return json.loads(self.summary_json)


class Recommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str  # "surrogate" | "physics"
    result_json: str
    created_at: datetime = Field(default_factory=_utcnow)

    def result(self) -> dict[str, Any]:
        return json.loads(self.result_json)


class Calibration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    n_cycles: int
    result_json: str
    created_at: datetime = Field(default_factory=_utcnow)

    def result(self) -> dict[str, Any]:
        return json.loads(self.result_json)


class Job(SQLModel, table=True):
    """One background job (`/api/optimize`, `/api/recommend/physics`,
    `/api/calibrate`, live `/api/uq`). Polled via `GET /api/jobs/{id}`."""
    id: str = Field(primary_key=True)
    kind: str
    status: str = "pending"  # pending -> running -> done | error
    request_json: str = "{}"
    result_json: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def result(self) -> Any:
        return json.loads(self.result_json) if self.result_json else None


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def database_ok() -> bool:
    try:
        from sqlalchemy import text

        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception:
        return False
