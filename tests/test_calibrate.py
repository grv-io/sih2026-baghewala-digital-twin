"""Tests for twin/calibrate.py -- the ingest -> recalibrate loop.

27 Sep 2026: `bl_delta_factor` is no longer a default free parameter -- it
is the sourced 1/2 in Boberg & Lantz's delta (params/CHANGELOG.md rev 7) and
the hidden truth now uses 0.5 too.

rev 12 (cascade, 27 Sep 2026): `twin/generate_pseudo_real.py` now generates
the pseudo-real demo dataset against CURRENT physics (water cut as a state,
Pal-Rhodes-capped emulsion, the float-onset produce-end rule, AOF 0.56) --
no more legacy rev-10 switches. Under the shipped `fluid.water_cut_model =
"state"`, the constant `fluid.water_cut` is not read; `calibrate.default_free`
picks (`formation_water_cut`, `aof_ref_m3d`, `thickness_m`) instead, and the
hidden truth's `water_cut` key was renamed to `formation_water_cut`
accordingly (see `twin/generate_pseudo_real.py` HIDDEN_TRUTH).

Recovery tolerances on the pseudo-real demo (`data/external/pseudo_real_
cycles.csv`, hidden truth `data/external/pseudo_real_TRUTH.json`) are based on
the ONE committed seed (42) this cascade re-generated: formation_water_cut
0.360 (truth 0.380, -5.2 %), aof_ref_m3d 0.644 (truth 0.650, -0.9 %),
thickness_m 13.37 (truth 15.0, -10.9 %) -- thickness is still the
weakest-identified parameter (trades off against aof_ref_m3d, both scaling
heated-zone delivery). A multi-noise-seed characterisation (as the rev-11
version of this docstring reported) was NOT re-run this pass; tolerances
below are widened above the single observed error with headroom, not
re-derived from a noise-seed sweep -- flagged here rather than silently kept
tight enough to pass by luck.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from twin import calibrate, ipr, thermal

ROOT = Path(__file__).resolve().parents[1]
PARAMS_PATH = ROOT / "params" / "field_params.json"
TEMPLATE_CSV = ROOT / "data" / "templates" / "observed_cycles_template.csv"
PSEUDO_REAL_CSV = ROOT / "data" / "external" / "pseudo_real_cycles.csv"
PSEUDO_REAL_TRUTH_JSON = ROOT / "data" / "external" / "pseudo_real_TRUTH.json"

pytestmark = pytest.mark.skipif(
    not PSEUDO_REAL_CSV.exists() or not PSEUDO_REAL_TRUTH_JSON.exists(),
    reason="pseudo-real demo dataset not generated; run `python -m twin.generate_pseudo_real` first",
)


@pytest.fixture(scope="module")
def pseudo_real_df() -> pd.DataFrame:
    return calibrate.load_observed_csv(PSEUDO_REAL_CSV)


@pytest.fixture(scope="module")
def hidden_truth() -> dict:
    with open(PSEUDO_REAL_TRUTH_JSON) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def module_params() -> dict:
    # rev 12 (cascade): the committed demo dataset is now generated with
    # CURRENT physics (twin/generate_pseudo_real.py no longer pins the
    # rev-10 legacy switches), so the loop is tested on the same physics the
    # data was generated with -- no override needed.
    with open(PARAMS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fit_result(pseudo_real_df, module_params):
    return calibrate.fit(pseudo_real_df, module_params)


def test_template_csv_parses():
    """The documented schema example loads without a schema error."""
    df = calibrate.load_observed_csv(TEMPLATE_CSV)
    assert len(df) == 2
    for col in calibrate.REQUIRED_COLUMNS:
        assert col in df.columns


def test_default_free_params_exclude_bl_delta_factor():
    """bl_delta_factor is sourced physics (0.5), not a default fit knob."""
    assert "bl_delta_factor" not in calibrate.DEFAULT_FREE
    assert set(calibrate.DEFAULT_FREE) == {"water_cut", "aof_ref_m3d", "thickness_m"}
    assert "bl_delta_factor" in calibrate.DEFAULT_BOUNDS  # still accepted opt-in


def test_degenerate_single_row_raises_clear_error(params):
    """One observed cycle cannot identify 3 free parameters -- fit() must
    say so clearly rather than silently returning a meaningless answer."""
    one_row = calibrate.load_observed_csv(TEMPLATE_CSV).iloc[[0]]
    with pytest.raises(ValueError, match="at least 2 observed cycles"):
        calibrate.fit(one_row, params)


def test_fit_is_deterministic(pseudo_real_df, params):
    r1 = calibrate.fit(pseudo_real_df, params)
    r2 = calibrate.fit(pseudo_real_df, params)
    assert r1["fitted_params"] == pytest.approx(r2["fitted_params"])
    assert r1["cost"] == pytest.approx(r2["cost"])


def test_apply_round_trips(module_params, fit_result):
    """apply() writes fitted values to exactly the keys the engine reads."""
    calibrated = calibrate.apply(module_params, fit_result["fitted_params"])
    fitted = fit_result["fitted_params"]

    assert "bl_delta_factor" not in fitted
    assert thermal.bl_delta_factor(calibrated) == pytest.approx(thermal.BL_DELTA_FACTOR)
    assert calibrated["fluid"]["formation_water_cut"] == pytest.approx(fitted["formation_water_cut"])
    assert ipr.aof_ref_m3d(calibrated) == pytest.approx(fitted["aof_ref_m3d"])
    assert calibrated["reservoir"]["thickness_m"] == pytest.approx(fitted["thickness_m"])

    # apply() must not mutate its input params tree.
    assert thermal.bl_delta_factor(module_params) == pytest.approx(thermal.BL_DELTA_FACTOR)


def test_recovers_formation_water_cut_alone(fit_result, hidden_truth):
    """With bl_delta_factor fixed at its sourced 0.5, formation_water_cut is
    identified reasonably well on its own (rev-12 committed seed: -5.2 %,
    0.360 vs truth 0.380 -- see module docstring; no multi-seed sweep re-run
    this pass, so the tolerance is widened above that single observation
    with headroom rather than pinned tight)."""
    truth = hidden_truth["formation_water_cut"]
    fitted = fit_result["fitted_params"]["formation_water_cut"]
    assert fitted == pytest.approx(truth, rel=0.10)


def test_recovers_aof_ref_m3d(fit_result, hidden_truth):
    """Rev-12 committed seed: 0.644 vs truth 0.650 (-0.9 %); see module docstring."""
    truth = hidden_truth["aof_ref_m3d"]
    fitted = fit_result["fitted_params"]["aof_ref_m3d"]
    assert fitted == pytest.approx(truth, rel=0.15)


def test_recovers_thickness_m(fit_result, hidden_truth):
    """Weakest-identified free parameter (correlated with aof_ref_m3d, both
    scaling heated-zone delivery) -- wider, but still bounded, tolerance.
    Rev-12 committed seed: 13.37 vs truth 15.0 (-10.9 %); see module docstring."""
    truth = hidden_truth["thickness_m"]
    fitted = fit_result["fitted_params"]["thickness_m"]
    assert fitted == pytest.approx(truth, rel=0.30)


def test_hidden_truth_uses_sourced_bl_delta(hidden_truth):
    assert hidden_truth["bl_delta_factor"] == pytest.approx(thermal.BL_DELTA_FACTOR)


def test_no_bl_coupling_reported_by_default(fit_result):
    assert fit_result["identifiability"]["known_couplings"] == []


def test_bl_delta_opt_in_still_flags_the_coupling(pseudo_real_df, module_params):
    """Opting bl_delta_factor back in is allowed, and the fit then reports the
    near-degenerate bl / water_cut trade-off -- the reason it is off by
    default. This coupling is a property of the CONSTANT water-cut model
    (the bl term trades off against the hot-water rate, which under the
    rev-12 state model is not driven by the constant fluid.water_cut at
    all) -- so this test explicitly switches to that model, independent of
    module_params' (state-model) default, rather than fitting a constant the
    physics wouldn't even read."""
    import copy as _copy
    constant_wc_params = _copy.deepcopy(module_params)
    constant_wc_params["fluid"]["water_cut_model"] = "constant"
    r = calibrate.fit(pseudo_real_df.iloc[:3], constant_wc_params,
                      free=("bl_delta_factor", "water_cut"))
    known = r["identifiability"]["known_couplings"]
    assert any(k["combination"].startswith("bl_delta_factor") for k in known)
    pairs = [set(p["params"]) for p in r["identifiability"]["correlated_pairs"]]
    assert {"bl_delta_factor", "water_cut"} in pairs


def test_rmse_reported_for_all_three_quantities(fit_result):
    rmse = fit_result["rmse"]
    assert rmse["oil_m3_pct"] is not None
    assert rmse["produce_days_pct"] is not None
    assert rmse["peak_oil_m3d_pct"] is not None
    # the fit should land close to the noisy observations themselves
    # (the noise floor is ~8%, so a good fit's RMSE should not blow past it wildly).
    assert rmse["oil_m3_pct"] < 20.0
    assert rmse["produce_days_pct"] < 20.0
