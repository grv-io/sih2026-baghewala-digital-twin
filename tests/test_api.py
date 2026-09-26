"""FastAPI TestClient coverage for api/ -- health, params, simulate,
optimize job lifecycle, calibrate/demo, dyno cards, runs CRUD, and the
static dashboard mount. Uses a temporary sqlite DB (env DATABASE_URL) so
this suite never touches data/twin.db.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    # Isolated DB for the whole test session -- set BEFORE api.settings /
    # api.db is ever imported, so this suite never touches data/twin.db.
    # (Every api.routers.* submodule does `from ..db import engine` at
    # import time, so the env var must land before that first import, not
    # be swapped in per test via a reload -- reloading api.db would rebind
    # api.db.engine without updating the already-bound name in each
    # already-imported router module.)
    db_path = tmp_path_factory.mktemp("api") / "test_twin.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    from fastapi.testclient import TestClient

    import api.main as main_module

    with TestClient(main_module.app) as c:
        yield c


def _poll_job(client, job_id: str, timeout: float = 20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200
        body = r.json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db_ok"] is True
    assert "version" in body and "tests_badge" in body


def test_version(client):
    r = client.get("/api/version")
    assert r.status_code == 200
    assert "api_version" in r.json()


def test_params(client):
    r = client.get("/api/params")
    assert r.status_code == 200
    body = r.json()
    assert "css" in body and "srp" in body

    # legacy alias, same body
    r_legacy = client.get("/params")
    assert r_legacy.status_code == 200
    assert r_legacy.json() == body


def test_simulate_baseline_sor(client):
    r = client.get("/api/simulate", params={"steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0})
    assert r.status_code == 200
    body = r.json()
    # rev 12: the "either" produce-end rule ends baseline (b) on float onset
    # (produce day 139) and AOF 0.56 (was 4.007 in rev 11, 4.0608 in rev 10)
    assert body["summary"]["SOR_t_per_m3"] == pytest.approx(4.351, abs=0.01)
    assert len(body["series"]) > 0

    # legacy alias (note: query param is "cutoff", not "cutoff_m3d")
    r_legacy = client.get("/simulate", params={"steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0})
    assert r_legacy.status_code == 200
    assert r_legacy.json()["summary"]["SOR_t_per_m3"] == pytest.approx(4.351, abs=0.01)  # rev 12


def test_simulate_defaults_reproduce_baseline_without_new_controls(client):
    # Omitting stroke_in/p_wellhead_kgf_cm2 entirely must still reproduce the
    # baked baseline (b) gross SOR (dashboard/src/core.js REF_SUMMARY-derived
    # BASELINE_PUBLISHED.SOR_t_per_m3 == 4.3514) -- the new optional controls
    # must not change default behaviour on either the /api or legacy path.
    r = client.get("/api/simulate", params={"steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0})
    assert r.status_code == 200
    assert r.json()["summary"]["SOR_t_per_m3"] == pytest.approx(4.3514, abs=0.01)

    r_legacy = client.get("/simulate", params={"steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0})
    assert r_legacy.status_code == 200
    assert r_legacy.json()["summary"]["SOR_t_per_m3"] == pytest.approx(4.3514, abs=0.01)


def test_simulate_stroke_in_and_pressure_change_result(client):
    base_params = {"steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0}
    r_default = client.get("/api/simulate", params=base_params)
    assert r_default.status_code == 200
    default_summary = r_default.json()["summary"]

    # A shorter stroke (64 in, vs the params' own 86 in) changes rod/pump
    # behaviour and therefore the produced summary.
    r_stroke = client.get("/api/simulate", params={**base_params, "stroke_in": 64.0})
    assert r_stroke.status_code == 200
    stroke_summary = r_stroke.json()["summary"]
    assert stroke_summary["SOR_t_per_m3"] != pytest.approx(default_summary["SOR_t_per_m3"], abs=1e-9)

    # A different injection (wellhead) pressure (85 vs the params' own 91
    # kgf/cm2) changes the steam state and therefore the summary too.
    r_pressure = client.get("/api/simulate", params={**base_params, "p_wellhead_kgf_cm2": 85.0})
    assert r_pressure.status_code == 200
    pressure_summary = r_pressure.json()["summary"]
    assert pressure_summary["SOR_t_per_m3"] != pytest.approx(default_summary["SOR_t_per_m3"], abs=1e-9)

    # Legacy flat alias accepts the same two extra query params.
    r_legacy = client.get("/simulate", params={**base_params, "stroke_in": 64.0, "p_wellhead_kgf_cm2": 85.0})
    assert r_legacy.status_code == 200
    assert r_legacy.json()["summary"]["SOR_t_per_m3"] != pytest.approx(default_summary["SOR_t_per_m3"], abs=1e-9)

    # Legacy alias with only the original 4 args still works (backward compat).
    r_legacy_4arg = client.get("/simulate", params=base_params)
    assert r_legacy_4arg.status_code == 200
    assert r_legacy_4arg.json()["summary"]["SOR_t_per_m3"] == pytest.approx(default_summary["SOR_t_per_m3"], abs=1e-9)


def test_simulate_rejects_invalid_stroke_in(client):
    r = client.get("/api/simulate", params={
        "steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0, "stroke_in": 70.0,
    })
    assert r.status_code == 422


def test_simulate_rejects_out_of_range_pressure(client):
    r = client.get("/api/simulate", params={
        "steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0, "p_wellhead_kgf_cm2": 60.0,
    })
    assert r.status_code == 422


def test_optimize_job_lifecycle(client, monkeypatch):
    # Shrink the Bayesian search so the job finishes in well under 5s instead
    # of the full N_CALLS=60/N_INITIAL_POINTS=15 production search.
    import ml.optimize as ml_optimize

    monkeypatch.setattr(ml_optimize, "N_CALLS", 16)
    monkeypatch.setattr(ml_optimize, "N_INITIAL_POINTS", 8)

    started = time.time()
    r = client.post("/api/optimize", json={"fixed": {"soak_days": 10}})
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    body = _poll_job(client, job_id, timeout=10.0)
    assert body["status"] == "done", body.get("error")
    assert "physics_verified_optimum" in body["result"]
    assert time.time() - started < 10.0


def test_recommend_physics_job(client):
    r = client.post(
        "/api/recommend/physics",
        json={"fixed": {"soak_days": 10}, "grid": {"steam_t": 3, "cutoff_m3d": 3, "spm": 3}},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    body = _poll_job(client, job_id, timeout=15.0)
    assert body["status"] == "done", body.get("error")
    assert "best_settings" in body["result"]


def test_legacy_optimize_sync(client):
    r = client.get("/optimize")
    assert r.status_code == 200
    assert "physics_verified_optimum" in r.json()


def test_calibrate_demo(client):
    r = client.get("/api/calibrate/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["n_cycles"] == 8
    assert "recommendation_after_calibration" in body

    r_legacy = client.get("/calibrate/demo")
    assert r_legacy.status_code == 200
    assert r_legacy.json()["n_cycles"] == 8


def test_dyno_cards(client):
    r = client.get("/api/dyno/cards", params={"spm": 5.0, "mu_cP": 500.0, "fillage": 1.0, "water_cut": 0.85})
    assert r.status_code == 200
    body = r.json()
    assert "peak_prl_kN" in body
    assert "position_m" in body


def test_runs_crud(client):
    r = client.get("/api/simulate", params={"steam_t": 1300, "soak_days": 10, "cutoff": 1.3, "spm": 5.0})
    assert r.status_code == 200

    r_list = client.get("/api/runs")
    assert r_list.status_code == 200
    runs = r_list.json()
    assert len(runs) >= 1
    run_id = runs[0]["id"]

    r_get = client.get(f"/api/runs/{run_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == run_id

    r_del = client.delete(f"/api/runs/{run_id}")
    assert r_del.status_code == 200

    r_get2 = client.get(f"/api/runs/{run_id}")
    assert r_get2.status_code == 404


def test_static_dashboard(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"<html" in r.content.lower() or b"<!doctype html" in r.content.lower()

    r_plotly = client.get("/vendor/plotly.min.js")
    assert r_plotly.status_code == 200

    r_console = client.get("/console.html")
    assert r_console.status_code == 200
