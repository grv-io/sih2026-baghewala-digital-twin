"""rev 10 -- hardening after the external technical review (27 Sep 2026).

Covers the parts of the hardening pass that are not a single module's unit
behaviour: constants moved to params keep their code fallbacks, the new UQ
inputs, P_current, the gain decomposition, the aggressive/conservative
recommendation levels, the LHS SPM range and the optional skin free parameter.
See docs/model-improvement/TIER1_PROGRESS_LOG.md section 9.
"""
import copy

import numpy as np
import pytest

from twin import calibrate, cycle, generate_data, ipr, srp, viscosity

REF = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5)

MOVED_KEYS = (
    ("ipr", "s_cold"),
    ("srp", "k_visc"),
    ("reservoir", "pressure_boost_kPa_per_t"),
    ("fluid", "mu_anchor_T_C"),
    ("fluid", "mu_anchor_cP"),
)


def _s(params, **kw):
    return cycle.summary(cycle.simulate_css_cycle(params=params, **dict(REF, **kw)), params)


def test_moved_constants_have_identical_code_fallbacks(params):
    """Deleting every constant moved to params in rev 10 reproduces the shipped
    run exactly: the JSON values equal the module fallbacks."""
    a = _s(params)
    q = copy.deepcopy(params)
    for block, key in MOVED_KEYS:
        q[block].pop(key)
    b = _s(q)
    for k in ("SOR_t_per_m3", "oil_total_m3", "days_total", "peak_oil_m3d",
              "margin_incremental_inr_per_cycle_day", "max_floating_index"):
        assert a[k] == b[k], k
    assert ipr.s_cold(q) == ipr.S_COLD and srp.k_visc(q) == srp.K_VISC
    assert cycle.pressure_boost_kPa_per_t(q) == cycle.PRESSURE_BOOST_PER_T_KPA
    assert viscosity.anchor_point(q) == (viscosity.ANCHOR_T_C, viscosity.ANCHOR_MU_CP)


@pytest.mark.parametrize("block,key,value", [
    ("ipr", "s_cold", 2.0),
    # rev 11: at the default 91 kgf/cm2 / P_current 9.4 MPa the recharge is capped at
    # the sandface pressure (0.72 MPa of room) for any boost above ~0.48 kPa/t at
    # 1,500 t, so liveness is checked below the cap (TIER1 section 10).
    ("reservoir", "pressure_boost_kPa_per_t", 0.3),
    ("fluid", "mu_anchor_cP", 80.0),
])
def test_moved_constants_are_live(params, block, key, value):
    q = copy.deepcopy(params)
    q[block][key] = value
    assert _s(q)["peak_oil_m3d"] != pytest.approx(_s(params)["peak_oil_m3d"], rel=1e-6)


def test_p_current_default_and_is_live(params):
    """rev 11: P_current defaults to 9,400 kPa [ASSUMPTION - derived from the
    injectivity requirement at 85-97 kgf/cm2]; null still means virgin."""
    assert params["reservoir"]["P_current_kPa"] == 9400.0
    assert cycle.reservoir_pressure_kPa(params) == 9400.0
    v = copy.deepcopy(params)
    v["reservoir"]["P_current_kPa"] = None
    assert cycle.reservoir_pressure_kPa(v) == params["reservoir"]["P_initial_kPa"]
    q = copy.deepcopy(params)
    q["reservoir"]["P_current_kPa"] = 7400.0
    lo = _s(q)
    base = _s(params)
    assert lo["cold_rate_m3d"] < base["cold_rate_m3d"]
    assert lo["SOR_t_per_m3"] > base["SOR_t_per_m3"]


def test_uq_samples_the_review_constants(params):
    from ml import uq
    spec = uq.build_uncertain_inputs(params)
    want = {
        "s_cold": (0.0, 8.0), "k_visc": (5.0, 15.0), "pressure_boost_kPa_per_t": (0.5, 2.0),
        "mu_anchor_cP": (30.0, 80.0), "P_current_kPa": (7400.0, 9400.0),   # rev 11 range
        "emulsion_inversion_wc": (0.60, 0.75),
        "fixed_cost_inr_per_cycle": (7.5e5, 2.25e6),
        # rev 11: water-cut state inputs
        "formation_water_cut": (0.30, 0.60), "condensate_recovery_frac": (0.50, 0.90),
    }
    for name, (lo, hi) in want.items():
        assert spec[name]["low"] == pytest.approx(lo) and spec[name]["high"] == pytest.approx(hi), name
        p = copy.deepcopy(params)
        spec[name]["setter"](p, 0.3 * lo + 0.7 * hi)   # off-base value
        assert p != params, name
    # the original seven come first, so their draws are unchanged for a seed
    # (rev 11: the first slot samples the formation water cut, the water-cut
    # driver the state model reads; constant-cut params still get "water_cut")
    assert list(spec)[:7] == ["formation_water_cut", "thickness_m", "diesel_bulk_discount_frac",
                              "oil_price_inr_per_bbl", "mu_ref_cP", "opex_inr_per_day",
                              "srp_geometry_scale"]


def test_shapley_decomposition_sums_to_the_total_gain(params):
    """Review finding 1 (rev 10/11 physics, rate-cutoff rule): the cutoff is
    the dominant lever of the rev-9 gain. rev 12: pinned to the rev-11
    switches (cycle.legacy_rev11_params); under the "either" rule both ends
    are set by float onset and the gain moves to SPM / stroke
    (test_physics_wave4.py)."""
    from ml import decompose
    dp = decompose.decks(cycle.legacy_rev11_params(params))
    res = decompose.decompose(decompose.BASELINE_B, decompose.REC_REV9, dp)
    for deck in dp:
        e = res[deck]
        assert sum(e["shapley"].values()) == pytest.approx(e["total_gain"], rel=1e-9)
        # the cutoff is the dominant lever (review finding 1), steam is second
        assert e["shapley"]["cutoff_m3d"] > 0.75 * e["total_gain"]
        assert abs(e["shapley"]["spm"]) < 0.05 * e["total_gain"]


def test_recommend_physics_reports_aggressive_and_conservative(params):
    from ml import recommend_physics as rp
    # rev 11: with the water-cut state the late stream is oil-continuous and
    # FI <= 0.6 needs an early stop / slow pump, so the tiny grid includes one.
    res = rp.best_settings_physics(params, grid_values={
        "steam_t": [1300.0, 1700.0], "cutoff_m3d": [1.3, 1.6], "spm": [3.0, 4.0]})
    assert res["n_grid_points_evaluated"] == 8
    agg, con = res["aggressive"], res["conservative"]
    assert agg["fi_max"] == 0.6 and con["fi_max"] == 0.5
    # rev 12: under the "either" produce-end rule FI may cross 0.6 only on the
    # alarm days that trigger the pull (<= css.fi_alarm_days); the conservative
    # level is the same rule with its alarm line at 0.5 (as in the 5-D search)
    assert res["produce_end_rule"] == "either"
    assert agg["physics_verified_optimum"]["float_alarm_days"] <= params["css"]["fi_alarm_days"]
    assert agg["fi_alarm_line"] == 0.6 and con["fi_alarm_line"] == 0.5
    assert con["physics_verified_optimum"]["produce_end_reason"] in ("float_onset", "rate_cutoff")
    assert con["objective_given_up_vs_aggressive"] >= 0.0
    assert res["best_settings"] == agg["best_settings"]   # backward-compatible top level


def test_lhs_spm_range_covers_the_optimiser_box(params):
    lo, hi = generate_data.sampled_spm_range(params)
    band = params["srp"]["spm_practice_band"]
    assert lo <= band[0] and hi >= band[1]
    assert (lo, hi) == (3.0, 12.0)
    df = generate_data._sample_inputs(params, 200, 42)
    assert df["spm"].min() < 3.2 and df["spm"].max() > 11.8
    assert np.mean(df["spm"] <= 6.0) > 0.25


def test_skin_is_an_optional_calibration_parameter(params):
    assert "s_cold" not in calibrate.DEFAULT_FREE
    assert calibrate.DEFAULT_BOUNDS["s_cold"] == (0.0, 8.0)
    assert calibrate._current_value("s_cold", params) == params["ipr"]["s_cold"]
    p = calibrate.apply(params, {"s_cold": 3.0})
    assert p["ipr"]["s_cold"] == 3.0 and params["ipr"]["s_cold"] == 5.0
