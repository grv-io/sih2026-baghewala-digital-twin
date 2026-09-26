"""In-process background jobs for the slow endpoints (`/api/optimize`,
`/api/recommend/physics`, `/api/calibrate`, live `/api/uq`).

FastAPI `BackgroundTasks` runs the work in the same process right after the
response is sent; job status/result live in the `Job` table (api/db.py) and
are polled via `GET /api/jobs/{id}`. This is deliberately single-process --
fine for a demo/hackathon deployment on one dyno/instance (see
docs/DEPLOY.md "known limits"); a real multi-worker deployment would need
Celery/RQ instead.

Results are cached by a hash of (kind, payload): an identical request
returns the SAME job id's result immediately instead of re-running the
optimizer/grid/calibration from scratch.
"""
from __future__ import annotations

import hashlib
import json
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from sqlmodel import Session, select

from .db import Job, engine
from .utils import to_native

# kind+payload hash -> completed job id. In-memory only (cleared on
# restart) -- results are cheap enough to recompute that this only saves a
# re-run of an in-flight-identical demo request, not a durable cache.
_cache: dict[str, str] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def cache_key(kind: str, payload: dict[str, Any]) -> str:
    blob = json.dumps({"kind": kind, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def get_cached_job_id(kind: str, payload: dict[str, Any]) -> str | None:
    job_id = _cache.get(cache_key(kind, payload))
    if job_id is None:
        return None
    # Only honour the cache if that job actually completed successfully --
    # an errored or since-deleted job should not be served as a hit.
    job = get_job(job_id)
    if job is None or job.status != "done":
        return None
    return job_id


def create_job(kind: str, payload: dict[str, Any]) -> Job:
    job = Job(id=str(uuid.uuid4()), kind=kind, status="pending", request_json=json.dumps(payload, default=str))
    with Session(engine) as session:
        session.add(job)
        session.commit()
        session.refresh(job)
    return job


def get_job(job_id: str) -> Job | None:
    with Session(engine) as session:
        return session.get(Job, job_id)


def list_jobs(limit: int = 50) -> list[Job]:
    with Session(engine) as session:
        stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
        return list(session.exec(stmt))


def run_job(job_id: str, kind: str, payload: dict[str, Any], fn: Callable[[dict[str, Any]], Any]) -> None:
    """Executed by FastAPI `BackgroundTasks` -- runs `fn(payload)` and writes
    the outcome back onto the Job row. Never raises out of the background
    task: exceptions are caught and stored on `Job.error` so a failing
    optimize/calibrate run surfaces as a job-status error, not a silently
    dropped background task."""
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        job.status = "running"
        job.updated_at = _now()
        session.add(job)
        session.commit()

    try:
        result = to_native(fn(payload))
        with Session(engine) as session:
            job = session.get(Job, job_id)
            job.status = "done"
            job.result_json = json.dumps(result)
            job.updated_at = _now()
            session.add(job)
            session.commit()
        _cache[cache_key(kind, payload)] = job_id
    except Exception as exc:  # noqa: BLE001 -- surfaced via job status, not raised
        with Session(engine) as session:
            job = session.get(Job, job_id)
            job.status = "error"
            job.error = f"{exc}\n{traceback.format_exc(limit=5)}"
            job.updated_at = _now()
            session.add(job)
            session.commit()


def job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "result": job.result(),
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
