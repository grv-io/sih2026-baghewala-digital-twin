"""GET /api/schedule/demo -- the baked ml/models/field_schedule_demo.json
(12 synthetic wells, see ml/schedule.py), cached in-process after first read.
POST /api/schedule -- run the field-level generator-constrained scheduler
(synchronous) on caller-supplied wells (JSON list or CSV text).
"""
from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..deps import load_params
from ..schemas import ScheduleRequest
from ..settings import ROOT
from ..utils import to_native

router = APIRouter(prefix="/api/schedule", tags=["schedule"])

DEMO_PATH = ROOT / "ml" / "models" / "field_schedule_demo.json"
_demo_cache: dict[str, Any] | None = None

REQUIRED_WELL_COLUMNS = {"well_id", "days_since_last_cycle"}


@router.get("/demo", summary="Baked field schedule demo (12 synthetic wells)")
def get_schedule_demo():
    global _demo_cache
    if _demo_cache is None:
        try:
            with open(DEMO_PATH, "r", encoding="utf-8") as f:
                _demo_cache = json.load(f)
        except FileNotFoundError:
            return JSONResponse(
                status_code=503,
                content={
                    "error": f"{DEMO_PATH} not found. Run `python -m ml.schedule "
                    "--wells data/external/field_wells_synthetic.csv "
                    "--out ml/models/field_schedule_demo.json` first."
                },
            )
        except json.JSONDecodeError as exc:
            return JSONResponse(status_code=500, content={"error": f"field_schedule_demo.json is not valid JSON: {exc}"})
    return _demo_cache


@router.post("", summary="Run the scheduler on caller-supplied wells (synchronous)")
def post_schedule(body: ScheduleRequest):
    from ml import schedule as ml_schedule

    try:
        if body.csv_text:
            wells_df = pd.read_csv(io.StringIO(body.csv_text))
        elif body.wells:
            wells_df = pd.DataFrame(body.wells)
        else:
            return JSONResponse(status_code=400, content={"error": "Provide either `wells` (list of dicts) or `csv_text`."})
    except Exception as exc:
        return JSONResponse(status_code=400, content={"error": f"could not parse wells: {exc}"})

    missing = REQUIRED_WELL_COLUMNS - set(wells_df.columns)
    if missing:
        return JSONResponse(status_code=400, content={"error": f"wells is missing required columns: {sorted(missing)}"})

    try:
        params = load_params()
        result = ml_schedule.build_schedule(wells_df, params, grid=body.grid, horizon=body.horizon_days)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return to_native(result)
