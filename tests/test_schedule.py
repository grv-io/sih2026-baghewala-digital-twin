"""Tests for ml/schedule.py -- the field-level, generator-constrained steam
scheduler built on top of ml/recommend_physics.py's per-well optimum.

Uses a heavily reduced physics search grid (18 pts/well vs the module's own
144-pt default) purely to keep this test module fast; correctness of the
scheduling logic itself (generator non-overlap, the >=180-day re-cycle gate,
exact >= greedy >= naive) does not depend on grid resolution.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from ml import schedule as sch

ROOT = Path(__file__).resolve().parents[1]
WELLS_CSV = ROOT / "data" / "external" / "field_wells_synthetic.csv"
FAST_GRID = {"steam_t": 3, "cutoff_m3d": 3, "spm": 2}  # 18 pts/well


@pytest.fixture(scope="module")
def wells_df() -> pd.DataFrame:
    assert WELLS_CSV.exists(), f"{WELLS_CSV} missing -- run `python -m ml.schedule --make-wells` first"
    return pd.read_csv(WELLS_CSV)


@pytest.fixture(scope="module")
def params_module() -> dict:
    # Module-scoped counterpart of conftest.py's function-scoped `params`
    # fixture (needed because `result` below is module-scoped for speed --
    # one 12-well schedule build shared across every test in this class).
    return sch._load_params()


@pytest.fixture(scope="module")
def result(params_module, wells_df):
    return sch.build_schedule(wells_df, params_module, grid=FAST_GRID)


def _assert_no_overlap(jobs: list[dict]) -> None:
    ordered = sorted(jobs, key=lambda j: j["start_day"])
    for prev, cur in zip(ordered, ordered[1:]):
        assert cur["start_day"] + 1e-6 >= prev["end_day"], (
            f"generator double-booked: {prev['well_id']} ends {prev['end_day']}, "
            f"{cur['well_id']} starts {cur['start_day']}"
        )


def _assert_recycle_gate(jobs: list[dict], jobs_by_well: dict[str, dict]) -> None:
    for j in jobs:
        earliest = jobs_by_well[j["well_id"]]["earliest_start_day"]
        # start_day in the output is rounded to 1 decimal for display; allow
        # that much slack against the un-rounded earliest-eligible day.
        assert j["start_day"] + 0.05 >= earliest, (
            f"{j['well_id']} started at day {j['start_day']} before its "
            f">=180-day re-cycle gate ({earliest})"
        )


class TestSyntheticWells:
    def test_twelve_wells_no_real_data_flag(self, wells_df):
        assert len(wells_df) == 12
        assert set(wells_df["well_id"]) == {f"BGW-S{i:02d}" for i in range(1, 13)}

    def test_deterministic_seed_42(self, params):
        a = sch.make_synthetic_wells(seed=42, base_params=params)
        b = sch.make_synthetic_wells(seed=42, base_params=params)
        pd.testing.assert_frame_equal(a, b)

    def test_ranges(self, wells_df):
        assert wells_df["thickness_m"].between(8.0, 20.0).all()
        assert wells_df["mu_ref_cP"].between(8000.0, 15000.0).all()
        assert wells_df["water_cut"].between(0.7, 0.9).all()


class TestBuildSchedule:
    def test_deterministic(self, params, wells_df):
        r1 = sch.build_schedule(wells_df, params, grid=FAST_GRID)
        r2 = sch.build_schedule(wells_df, params, grid=FAST_GRID)
        assert r1["exact"]["field_margin_inr_total"] == r2["exact"]["field_margin_inr_total"]
        assert r1["exact"]["wells_served"] == r2["exact"]["wells_served"]
        assert r1["naive"]["field_margin_inr_total"] == r2["naive"]["field_margin_inr_total"]

    @pytest.mark.parametrize("method", ["exact", "greedy", "naive"])
    def test_generator_never_double_booked(self, result, method):
        _assert_no_overlap(result[method]["jobs"])

    @pytest.mark.parametrize("method", ["exact", "greedy"])
    def test_recycle_gate_respected(self, result, method):
        by_well = {j["well_id"]: j for j in result["candidate_jobs"]}
        _assert_recycle_gate(result[method]["jobs"], by_well)

    def test_naive_recycle_gate_respected(self, result, wells_df):
        by_well = {
            row["well_id"]: {"earliest_start_day": sch._earliest_start_day(row["days_since_last_cycle"])}
            for row in wells_df.to_dict(orient="records")
        }
        _assert_recycle_gate(result["naive"]["jobs"], by_well)

    def test_each_well_at_most_one_job(self, result):
        for method in ("exact", "greedy", "naive"):
            ids = [j["well_id"] for j in result[method]["jobs"]]
            assert len(ids) == len(set(ids))

    def test_jobs_fit_in_horizon(self, result):
        for method in ("exact", "greedy", "naive"):
            for j in result[method]["jobs"]:
                assert j["end_day"] <= result["horizon_days"] + 1e-6

    def test_exact_at_least_as_good_as_greedy_at_least_as_good_as_naive(self, result):
        exact = result["exact"]["field_margin_inr_total"]
        greedy = result["greedy"]["field_margin_inr_total"]
        naive = result["naive"]["field_margin_inr_total"]
        assert exact >= greedy >= naive, (exact, greedy, naive)
        # And the optimized policies should genuinely beat the counterfactual,
        # not just tie it.
        assert exact > naive
        assert greedy > naive

    def test_served_plus_deferred_covers_all_wells(self, result):
        for method in ("exact", "greedy", "naive"):
            s = result[method]
            assert s["n_wells_served"] + s["n_wells_deferred"] == s["n_wells_total"]
            served_and_deferred = set(s["wells_served"]) | {d["well_id"] for d in s["wells_deferred"]}
            assert served_and_deferred == set(result["candidate_jobs"][i]["well_id"] for i in range(len(result["candidate_jobs"])))

    def test_deferred_reason_present(self, result):
        for method in ("exact", "greedy", "naive"):
            for d in result[method]["wells_deferred"]:
                assert d["reason"]

    def test_result_has_expected_top_level_keys(self, result):
        for key in ("candidate_jobs", "exact", "greedy", "naive", "comparison", "assumptions",
                    "generator_rate_tpd", "min_recycle_days", "horizon_days"):
            assert key in result

    def test_comparison_gain_signs(self, result):
        comp = result["comparison"]
        assert comp["exact_vs_naive"]["margin_inr_total_delta"] >= 0
        assert comp["greedy_vs_naive"]["margin_inr_total_delta"] >= 0
        assert comp["exact_vs_greedy"]["margin_inr_total_delta"] >= 0


@pytest.fixture(scope="module")
def api_client(tmp_path_factory):
    """Isolated-DB TestClient, same pattern as tests/test_api.py's `client`
    fixture (schedule routes don't touch the DB, but the app's lifespan
    still calls init_db(), so isolate it to avoid touching data/twin.db)."""
    pytest.importorskip("fastapi")
    db_path = tmp_path_factory.mktemp("api_schedule") / "test_twin.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    from fastapi.testclient import TestClient

    import api.main as main_module

    with TestClient(main_module.app) as c:
        yield c


class TestApiRoute:
    def test_demo_route_200_expected_keys(self, api_client):
        resp = api_client.get("/api/schedule/demo")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        for key in ("exact", "greedy", "naive", "comparison", "candidate_jobs"):
            assert key in body

    def test_post_route_200_with_minimal_wells(self, api_client):
        wells = [
            {"well_id": "T1", "days_since_last_cycle": 0.0},
            {"well_id": "T2", "days_since_last_cycle": 300.0},
        ]
        resp = api_client.post("/api/schedule", json={"wells": wells, "grid": FAST_GRID, "horizon_days": 365.0})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["n_wells"] == 2
        for key in ("exact", "greedy", "naive"):
            assert key in body

    def test_post_route_400_on_missing_required_columns(self, api_client):
        resp = api_client.post("/api/schedule", json={"wells": [{"well_id": "T1"}]})
        assert resp.status_code == 400

    def test_post_route_400_on_no_wells(self, api_client):
        resp = api_client.post("/api/schedule", json={})
        assert resp.status_code == 400
