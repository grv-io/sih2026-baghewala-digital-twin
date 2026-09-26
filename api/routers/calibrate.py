"""POST /api/calibrate -- ingest observed field cycles, recalibrate, re-
recommend (async job: fitting + a physics grid search can take a few
seconds). GET /api/calibrate/demo -- same loop on the synthetic demo
dataset (fast enough to stay synchronous).

POST /calibrate and GET /calibrate/demo (no /api prefix) are kept as thin,
SYNCHRONOUS aliases -- the exact v0.1 contract `dashboard/src/page-
methodology.js` already POSTs to directly and renders inline, so they must
keep returning the body immediately rather than a job id.
"""
from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from ..db import Calibration, engine
from ..deps import load_params
from ..jobs import create_job, run_job
from ..schemas import JobCreatedResponse
from ..utils import to_native

router = APIRouter(tags=["calibrate"])
legacy_router = APIRouter(tags=["legacy"], include_in_schema=False)


async def _parse_observed_df(request: Request) -> pd.DataFrame | JSONResponse:
    from twin import calibrate as twin_calibrate

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is None:
            return JSONResponse(
                status_code=400,
                content={"error": "multipart upload must include a 'file' field holding the observed-cycles CSV"},
            )
        raw = (await upload.read()).decode("utf-8")
        observed_df = pd.read_csv(io.StringIO(raw))
    else:
        body = await request.json()
        rows = body.get("rows") if isinstance(body, dict) else body
        if not rows:
            return JSONResponse(
                status_code=400,
                content={"error": "JSON body must be a list of row objects, or {'rows': [...]}"},
            )
        observed_df = pd.DataFrame(rows)

    missing = [c for c in twin_calibrate.REQUIRED_COLUMNS if c not in observed_df.columns]
    if missing:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"observed cycles missing required column(s) {missing}. "
                f"Required: {twin_calibrate.REQUIRED_COLUMNS}"
            },
        )
    return twin_calibrate.coerce_numeric_columns(observed_df)


def _fit_and_recommend(observed_records: list[dict[str, Any]]) -> dict[str, Any]:
    """The actual (slow-ish) work -- runs off the request/response cycle for
    the async job path, and inline for the legacy sync alias."""
    from ml import recommend_physics
    from twin import calibrate as twin_calibrate

    observed_df = pd.DataFrame(observed_records)
    params = load_params()
    fit_result = twin_calibrate.fit(observed_df, params)
    calibrated_params = twin_calibrate.apply(params, fit_result["fitted_params"])
    soak_fixed = float(observed_df["soak_days"].median())
    recommendation = recommend_physics.best_settings_physics(calibrated_params, fixed={"soak_days": soak_fixed})

    result = {
        "fitted_params": fit_result["fitted_params"],
        "bounds": fit_result["bounds"],
        "residual_table": fit_result["residual_table"],
        "rmse": fit_result["rmse"],
        "identifiability": fit_result["identifiability"],
        "n_cycles": fit_result["n_cycles"],
        "recommendation": recommendation,
    }
    native = to_native(result)
    try:
        with Session(engine) as session:
            session.add(Calibration(n_cycles=native["n_cycles"], result_json=json.dumps(native)))
            session.commit()
    except Exception:
        pass
    return native


def _demo_result() -> dict[str, Any]:
    from ml import recommend_physics
    from twin import calibrate as twin_calibrate

    from ..settings import ROOT

    demo_csv = ROOT / "data" / "external" / "pseudo_real_cycles.csv"
    truth_path = ROOT / "data" / "external" / "pseudo_real_TRUTH.json"
    if not demo_csv.exists():
        raise FileNotFoundError(f"{demo_csv} not found. Run `python -m twin.generate_pseudo_real` first.")

    params = load_params()
    observed_df = pd.read_csv(demo_csv)
    fit_result = twin_calibrate.fit(observed_df, params)
    calibrated_params = twin_calibrate.apply(params, fit_result["fitted_params"])
    hidden_truth = json.loads(truth_path.read_text()) if truth_path.exists() else None

    recommendation_before = recommend_physics.best_settings_physics(params, fixed={"soak_days": 10.0})
    recommendation_after = recommend_physics.best_settings_physics(calibrated_params, fixed={"soak_days": 10.0})

    return to_native({
        "fitted_params": fit_result["fitted_params"],
        "hidden_truth": hidden_truth,
        "bounds": fit_result["bounds"],
        "residual_table": fit_result["residual_table"],
        "rmse": fit_result["rmse"],
        "identifiability": fit_result["identifiability"],
        "n_cycles": fit_result["n_cycles"],
        "recommendation_before_calibration": recommendation_before,
        "recommendation_after_calibration": recommendation_after,
    })


# --------------------------------------------------------------------------
# New: /api/calibrate (async job)
# --------------------------------------------------------------------------
@router.post("/api/calibrate", response_model=JobCreatedResponse, status_code=202,
             summary="Start an ingest -> recalibrate -> re-recommend job")
async def start_calibrate(request: Request, background_tasks: BackgroundTasks):
    observed_df = await _parse_observed_df(request)
    if isinstance(observed_df, JSONResponse):
        return observed_df
    payload = {"rows": observed_df.to_dict(orient="records")}
    job = create_job("calibrate", payload)
    background_tasks.add_task(run_job, job.id, "calibrate", payload, lambda p: _fit_and_recommend(p["rows"]))
    return JobCreatedResponse(job_id=job.id, status_url=f"/api/jobs/{job.id}")


@router.get("/api/calibrate/demo", summary="Ingest -> recalibrate -> re-recommend on the synthetic demo dataset")
def calibrate_demo_api():
    try:
        return _demo_result()
    except Exception as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})


# --------------------------------------------------------------------------
# Legacy: POST /calibrate, GET /calibrate/demo (synchronous, v0.1 contract)
# --------------------------------------------------------------------------
@legacy_router.post("/calibrate", summary="Legacy synchronous calibrate (v0.1 contract)")
async def calibrate_legacy(request: Request):
    try:
        observed_df = await _parse_observed_df(request)
        if isinstance(observed_df, JSONResponse):
            return observed_df
        return _fit_and_recommend(observed_df.to_dict(orient="records"))
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@legacy_router.get("/calibrate/demo", summary="Legacy synchronous calibrate/demo (v0.1 contract)")
def calibrate_demo_legacy():
    try:
        return _demo_result()
    except Exception as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
