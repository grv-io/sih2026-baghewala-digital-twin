"""FastAPI backend + dashboard host for the Baghewala CSS + sucker-rod-pump
digital twin (SIH26120).

`create_app()` builds the app: a thin `/api/...` HTTP wrapper around the
`twin` (cycle simulation) and `ml` (Bayesian optimizer) packages -- this
file (and every module under `api/`) must not reimplement any physics or ML
logic, only call into those packages and shape their output as JSON -- plus
a static mount that serves `dashboard/` at `/`, so one process is both the
API and the web app. See docs/SPEC.md for the full module/API contract and
docs/DEPLOY.md for how to run/deploy this.

Old (v0.1) paths -- `/params`, `/simulate`, `/optimize`, `POST /calibrate`,
`GET /calibrate/demo` -- are kept as thin, synchronous aliases (hidden from
/docs) so the already-built dashboard keeps working unchanged; the `/api/...`
routes are the actively documented contract.
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Lets `python api/main.py` work directly: run as a plain script, this
    # module has no package context, so the relative imports just below
    # (`from .db import ...`) would raise "attempted relative import with no
    # known parent package". Insert the repo root onto sys.path and tell
    # Python this module is really `api.main`, so those imports resolve
    # exactly as they do under `python -m api.main` / `uvicorn api.main:app`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "api"

import threading
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import calibrate, dyno, health, jobs, optimize, params, runs, schedule, simulate, uq
from .settings import ROOT, get_settings

TAGS_METADATA = [
    {"name": "health", "description": "Liveness/readiness and version/provenance."},
    {"name": "params", "description": "The single-source-of-truth field parameters file."},
    {"name": "simulate", "description": "Run one CSS cycle through the physics twin (synchronous, ~ms)."},
    {"name": "optimize", "description": "Surrogate-assisted and true-physics set-point search (async jobs)."},
    {"name": "jobs", "description": "Poll a background job started by optimize/recommend/calibrate/uq."},
    {"name": "calibrate", "description": "Ingest observed field cycles -> recalibrate -> re-recommend."},
    {"name": "uq", "description": "Uncertainty quantification -- baked bands and a live quick run."},
    {"name": "dyno", "description": "Live dynamometer card (surface + downhole) at given set-points."},
    {"name": "runs", "description": "Simulate-run history."},
    {"name": "schedule", "description": "Field-level generator-constrained steam scheduling across wells."},
]


def _self_ping_loop(url: str, minutes: int, stop: threading.Event) -> None:
    """Hit our own public /api/health so a free-tier host sees inbound traffic
    and never idles the service (see Settings.self_ping_url)."""
    target = url.rstrip("/") + "/api/health"
    # Give uvicorn time to bind before the first ping.
    stop.wait(60)
    while not stop.is_set():
        try:
            with urllib.request.urlopen(target, timeout=30) as r:
                print(f"[self-ping] {target} -> {r.status}", flush=True)
        except Exception as exc:  # noqa: BLE001 - never let the pinger die
            print(f"[self-ping] {target} failed: {exc}", flush=True)
        stop.wait(max(1, minutes) * 60)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    stop = threading.Event()
    if settings.self_ping_url:
        threading.Thread(
            target=_self_ping_loop,
            args=(settings.self_ping_url, settings.self_ping_minutes, stop),
            name="self-ping",
            daemon=True,
        ).start()
    try:
        yield
    finally:
        stop.set()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Baghewala Digital Twin API",
        version="0.2.0",
        description="Physics + ML backend for the Baghewala CSS/SRP digital twin, and host for its dashboard.",
        openapi_tags=TAGS_METADATA,
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- /api/... (documented contract) ---
    app.include_router(health.router, prefix="/api")
    app.include_router(params.router, prefix="/api")
    app.include_router(simulate.router, prefix="/api")
    app.include_router(dyno.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(optimize.router)   # paths already carry /api/...
    app.include_router(calibrate.router)  # paths already carry /api/...
    app.include_router(uq.router)         # prefix already /api/uq
    app.include_router(jobs.router)       # prefix already /api/jobs
    app.include_router(schedule.router)   # prefix already /api/schedule

    # --- old (v0.1) paths, thin synchronous aliases, hidden from /docs ---
    app.include_router(params.router, include_in_schema=False)
    app.include_router(simulate.router, include_in_schema=False)
    app.include_router(optimize.legacy_router)
    app.include_router(calibrate.legacy_router)

    # --- dashboard static files ---
    # data/templates/observed_cycles_template.csv is linked from
    # dashboard/*.html as a relative "../data/templates/..." path -- served
    # from the repo's data/ directory, a sibling of dashboard/, not inside it.
    data_dir = ROOT / "data"
    if data_dir.is_dir():
        app.mount("/data", StaticFiles(directory=data_dir), name="data")

    # Mounted LAST: a catch-all for "/", so every /api/... route above is
    # matched first. html=True serves index.html for "/" and lets
    # console.html/optimizer.html/methodology.html and vendor/plotly.min.js
    # resolve as plain relative paths, exactly as they do from file://.
    dashboard_dir = ROOT / "dashboard"
    if dashboard_dir.is_dir():
        app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    # String form (not the `app` object) so uvicorn imports `api.main` as a
    # proper package module even when this file was launched directly.
    uvicorn.run("api.main:app", host="0.0.0.0", port=settings.port, reload=False)
