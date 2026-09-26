"""GET /api/dyno/cards -- live dynamometer card (surface + downhole) for the
CURRENT set-points, via twin.dyno.compute_cards (<=50 ms).

POST /api/dyno/classify and GET /api/dyno/classify/demo -- fault
classification of a MEASURED surface dynamometer card (position vs. load),
via ml.dyno_classifier.classify_card -- a RandomForestClassifier trained on
SYNTHETIC cards swept from twin.dyno.compute_cards() (ml/dyno_classifier.py,
ml/README.md "Measured dynamometer-card classifier"). Both routes run in a
few ms (a joblib RandomForest predict + feature extraction), so -- like
/api/dyno/cards -- they are synchronous, not a background job."""
from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ..deps import load_params
from ..utils import to_native

router = APIRouter(tags=["dyno"])


@router.get(
    "/dyno/cards",
    summary="Live dynamometer card at the given set-points",
    responses={503: {"description": "twin package or params unavailable"}, 500: {"description": "computation error"}},
)
def dyno_cards(
    spm: float = Query(..., description="Strokes per minute"),
    mu_cP: float = Query(..., description="Oil viscosity, cP"),
    fillage: float = Query(1.0, description="Plunger fill fraction (0-1]"),
    water_cut: float = Query(0.85, description="Tubing-liquid water cut"),
):
    try:
        from twin import dyno as twin_dyno
    except Exception as exc:
        return JSONResponse(status_code=503, content={"error": f"twin.dyno unavailable: {exc}"})

    try:
        params = load_params()
        card = twin_dyno.compute_cards(
            spm=spm, stroke_m=params["srp"]["stroke_m"], mu_cP=mu_cP,
            fillage=fillage, water_cut=water_cut, params=params,
        )
    except FileNotFoundError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return to_native(card)


# --------------------------------------------------------------------------
# Measured-card classifier, 27 Sep 2026
# --------------------------------------------------------------------------
async def _parse_classify_request(request: Request):
    """JSON {"position":[...], "load":[...], "units": ...} or a multipart CSV
    upload (field "file") -- returns (position, load, units) or a JSONResponse
    error. Mirrors api/routers/calibrate.py's `_parse_observed_df` pattern."""
    from ml import dyno_classifier as clf

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is None:
            return JSONResponse(
                status_code=400,
                content={"error": "multipart upload must include a 'file' field holding the card CSV/text"},
            )
        raw = (await upload.read()).decode("utf-8", errors="replace")
        try:
            position, load, units = clf.parse_card_table(raw)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"error": str(exc)})
        return position, load, units

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "body must be JSON or a multipart 'file' upload"})
    if not isinstance(body, dict) or "position" not in body or "load" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "JSON body must be {'position': [...], 'load': [...], 'units'?: ...}"},
        )
    return body["position"], body["load"], body.get("units")


@router.post(
    "/dyno/classify",
    summary="Classify a measured surface dynamometer card (JSON arrays or a multipart CSV upload)",
    responses={400: {"description": "malformed input"}, 503: {"description": "classifier model unavailable"},
                500: {"description": "computation error"}},
)
async def dyno_classify(request: Request):
    try:
        from ml import dyno_classifier as clf
    except Exception as exc:
        return JSONResponse(status_code=503, content={"error": f"ml.dyno_classifier unavailable: {exc}"})

    parsed = await _parse_classify_request(request)
    if isinstance(parsed, JSONResponse):
        return parsed
    position, load, units = parsed

    try:
        result = clf.classify_card(position, load, units=units)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except FileNotFoundError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return to_native(result)


@router.get(
    "/dyno/classify/demo",
    summary="Classify the 4 baseline-scenario baked cards vs. their physics-derived true label",
    responses={503: {"description": "classifier model or baked cards unavailable"}},
)
def dyno_classify_demo():
    try:
        from ml import dyno_classifier as clf

        rows = clf.classify_baked_demo("baseline")
    except FileNotFoundError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return to_native({"scenario": "baseline", "cards": rows})
