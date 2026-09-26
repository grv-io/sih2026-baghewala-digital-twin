"""GET /api/uq -- the baked ml/models/uq_summary.json (1,500-draw bake, both
price decks). POST /api/uq -- run a quick LIVE Monte Carlo (n_draws <= 300)
against the true physics twin, as an async job (a few seconds at 300 draws).
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from ..deps import load_params
from ..jobs import create_job, get_cached_job_id, run_job
from ..schemas import JobCreatedResponse, UqLiveRequest
from ..settings import ROOT
from ..utils import to_native

router = APIRouter(prefix="/api/uq", tags=["uq"])

UQ_SUMMARY_PATH = ROOT / "ml" / "models" / "uq_summary.json"


@router.get("", summary="Baked UQ summary (both price decks, 1,500 draws)")
def get_uq():
    try:
        with open(UQ_SUMMARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return JSONResponse(
            status_code=503,
            content={"error": f"{UQ_SUMMARY_PATH} not found. Run `python ml/uq.py` first."},
        )
    except json.JSONDecodeError as exc:
        return JSONResponse(status_code=500, content={"error": f"uq_summary.json is not valid JSON: {exc}"})


def _run_live_uq(payload: dict[str, Any]) -> Any:
    from ml import uq as ml_uq

    params = load_params()
    n_draws = min(int(payload.get("n_draws", 200)), 300)
    seed = int(payload.get("seed", 42))
    summary, _results, _draws = ml_uq.run_deck("fy25_realisation", params, n_draws=n_draws, seed=seed)
    return summary


@router.post("", response_model=JobCreatedResponse, status_code=202, summary="Start a quick live UQ run (n_draws<=300)")
def start_live_uq(body: UqLiveRequest, background_tasks: BackgroundTasks):
    payload = body.model_dump()
    cached = get_cached_job_id("uq", payload)
    if cached:
        return JobCreatedResponse(job_id=cached, status_url=f"/api/jobs/{cached}")
    job = create_job("uq", payload)
    background_tasks.add_task(run_job, job.id, "uq", payload, _run_live_uq)
    return JobCreatedResponse(job_id=job.id, status_url=f"/api/jobs/{job.id}")
