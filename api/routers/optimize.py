"""POST /api/optimize -- Bayesian-surrogate search (async job).
POST /api/recommend/physics -- true-physics grid search (async job).

Both jobs poll through GET /api/jobs/{id} (api/routers/jobs.py). The
GET /optimize route (no /api prefix, no body) is the pre-existing v0.1
contract kept as a thin, synchronous alias so the built dashboard's
`apiOptimize()` (dashboard/src/page-optimizer.js) keeps working unchanged.
"""
from __future__ import annotations

import copy
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from ..deps import load_params
from ..jobs import create_job, get_cached_job_id, run_job
from ..schemas import JobCreatedResponse, OptimizeRequest, RecommendPhysicsRequest
from ..utils import to_native

router = APIRouter(tags=["optimize"])
legacy_router = APIRouter(tags=["legacy"], include_in_schema=False)


def _apply_spm_band(params: dict, spm_band: tuple[float, float] | list[float] | None) -> dict:
    if not spm_band:
        return params
    params = copy.deepcopy(params)
    params.setdefault("srp", {})["spm_practice_band"] = list(spm_band)
    return params


def _run_optimize(payload: dict[str, Any]) -> Any:
    from ml import optimize as ml_optimize

    params = load_params()
    params = _apply_spm_band(params, payload.get("spm_band"))
    return ml_optimize.best_settings(params, fixed=payload.get("fixed") or {})


def _run_recommend_physics(payload: dict[str, Any]) -> Any:
    from ml import recommend_physics

    params = load_params()
    params = _apply_spm_band(params, payload.get("spm_band"))
    return recommend_physics.best_settings_physics(
        params,
        fixed=payload.get("fixed") or {},
        grid=payload.get("grid"),
        objective=payload.get("objective") or "margin_incremental_inr_per_cycle_day",
    )


@router.post(
    "/api/optimize",
    response_model=JobCreatedResponse,
    status_code=202,
    summary="Start a Bayesian-surrogate optimization job",
)
def start_optimize(body: OptimizeRequest, background_tasks: BackgroundTasks):
    payload = body.model_dump(exclude_none=True)
    cached = get_cached_job_id("optimize", payload)
    if cached:
        return JobCreatedResponse(job_id=cached, status_url=f"/api/jobs/{cached}")
    job = create_job("optimize", payload)
    background_tasks.add_task(run_job, job.id, "optimize", payload, _run_optimize)
    return JobCreatedResponse(job_id=job.id, status_url=f"/api/jobs/{job.id}")


@router.post(
    "/api/recommend/physics",
    response_model=JobCreatedResponse,
    status_code=202,
    summary="Start a true-physics grid-search recommendation job",
)
def start_recommend_physics(body: RecommendPhysicsRequest, background_tasks: BackgroundTasks):
    payload = body.model_dump(exclude_none=True)
    cached = get_cached_job_id("recommend_physics", payload)
    if cached:
        return JobCreatedResponse(job_id=cached, status_url=f"/api/jobs/{cached}")
    job = create_job("recommend_physics", payload)
    background_tasks.add_task(run_job, job.id, "recommend_physics", payload, _run_recommend_physics)
    return JobCreatedResponse(job_id=job.id, status_url=f"/api/jobs/{job.id}")


@legacy_router.get("/optimize", summary="Legacy synchronous optimize (v0.1 contract)")
def optimize_legacy():
    """Run the Bayesian optimizer synchronously, no request body -- the exact
    v0.1 contract `dashboard/src/page-optimizer.js`'s `apiOptimize()` calls.
    Returns 503 with an {"error": ...} body if ml/optimize.py or its trained
    models aren't available yet."""
    try:
        from ml import optimize as ml_optimize

        params = load_params()
        result = ml_optimize.best_settings(params)
        return to_native(result)
    except Exception as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
