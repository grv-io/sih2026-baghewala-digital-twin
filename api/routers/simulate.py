"""GET /api/simulate -- one CSS cycle through twin.cycle, synchronous (~ms).

Also persists the run to the `Run` table so `/api/runs` has history to list.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from ..db import Run, engine
from ..deps import load_params
from ..schemas import SimulateResponse
from ..utils import to_native

router = APIRouter(tags=["simulate"])


@router.get(
    "/simulate",
    response_model=SimulateResponse,
    summary="Run one CSS cycle (synchronous, ~ms)",
    responses={503: {"description": "twin package or params unavailable"}, 500: {"description": "simulation error"}},
)
def simulate(
    steam_t: float = Query(..., description="Steam volume injected, tonnes", examples=[1300.0]),
    soak_days: float = Query(..., description="Soak period, days", examples=[10.0]),
    cutoff: float = Query(..., description="Economic cutoff oil rate, m3/d", examples=[1.3]),
    spm: float = Query(..., description="Sucker-rod pump strokes per minute", examples=[5.0]),
    stroke_in: float | None = Query(
        None,
        description="Polished-rod stroke length, in -- one of the six API Spec 11E "
        "sizes (64/74/86/100/120/144, or params.srp.stroke_in_options if set). "
        "Omit to use the params' own stroke (srp.stroke_m).",
        examples=[64.0],
    ),
    p_wellhead_kgf_cm2: float | None = Query(
        None,
        ge=85.0,
        le=97.0,
        description="Injection (wellhead) pressure, kgf/cm2 g -- CONFIRMED range "
        "85-97 (OIL deck, BGW-08). Omit to use the params' own pressure "
        "(steam.P_wellhead_kgf_cm2).",
        examples=[85.0],
    ),
):
    try:
        from twin import cycle, srp
    except Exception as exc:  # twin/ not present/importable yet
        return JSONResponse(status_code=503, content={"error": f"twin package unavailable: {exc}"})

    try:
        params = load_params()

        stroke_m = None
        if stroke_in is not None:
            allowed_in = params.get("srp", {}).get("stroke_in_options") or list(srp.API_STROKES_IN)
            if not any(abs(float(stroke_in) - float(a)) < 1e-6 for a in allowed_in):
                return JSONResponse(status_code=422, content={
                    "error": f"stroke_in must be one of {list(allowed_in)}, got {stroke_in}"
                })
            stroke_m = float(stroke_in) * srp.INCH_M

        df = cycle.simulate_css_cycle(
            steam_t=steam_t, soak_days=soak_days, cutoff_m3d=cutoff, spm=spm, params=params,
            stroke_m=stroke_m, p_wellhead_kgf_cm2=p_wellhead_kgf_cm2,
        )
        summary = cycle.summary(df)
    except FileNotFoundError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    summary_native = to_native(summary)
    try:
        with Session(engine) as session:
            session.add(Run(
                steam_t=steam_t, soak_days=soak_days, cutoff_m3d=cutoff, spm=spm,
                summary_json=json.dumps(summary_native), source="api",
            ))
            session.commit()
    except Exception:
        pass  # history is best-effort; never fail a simulate call over it

    return {"summary": summary_native, "series": to_native(df.to_dict(orient="records"))}
