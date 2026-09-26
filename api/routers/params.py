"""GET /api/params -- the single-source-of-truth field parameters file, as-is."""
from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..deps import load_params
from ..schemas import ParamsResponse

router = APIRouter(tags=["params"])


@router.get(
    "/params",
    response_model=ParamsResponse,
    summary="Field parameters (params/field_params.json, verbatim)",
    responses={503: {"description": "params file not found"}, 500: {"description": "params file is not valid JSON"}},
)
def get_params():
    try:
        return load_params()
    except FileNotFoundError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    except json.JSONDecodeError as exc:
        return JSONResponse(status_code=500, content={"error": f"params file is not valid JSON: {exc}"})
