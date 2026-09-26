"""rev 11 -- physics wave 3 (27 Sep 2026): water cut as a state, injection
pressure with T_sat coupling, stroke length, 5-D optimiser, controls coverage.

See docs/model-improvement/TIER1_PROGRESS_LOG.md section 10 and
params/CHANGELOG.md rev 11.
"""
import copy
import warnings

import numpy as np
import pytest

from twin import cycle, dyno, srp, thermal

REF = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5)


def _run(params, **kw):
    return cycle.simulate_css_cycle(params=params, **dict(REF, **kw))


def _s(params, **kw):
    return cycle.summary(_run(params, **kw), params)


# ------------------------------------------------------------ switches ----
@pytest.mark.parametrize("pt,want", [
    (REF, dict(SOR=4.027, oil=372.5, peak=15.91, incr=346)),
    (dict(steam_t=1300, soak_days=10, cutoff_m3d=1.3, spm=5), dict(SOR=4.061, oil=320.1, peak=15.13, incr=-1587)),
    (dict(steam_t=1700, soak_days=10, cutoff_m3d=0.60, spm=4), dict(SOR=3.550, oil=478.9, peak=15.66, incr=4044)),
])
def test_legacy_switches_reproduce_rev10(legacy_params, pt, want):
    s = cycle.summary(cycle.simulate_css_cycle(params=legacy_params, **pt), legacy_params)
    assert s["SOR_t_per_m3"] == pytest.approx(want["SOR"], abs=5e-4)
    assert s["oil_total_m3"] == pytest.approx(want["oil"], abs=0.05)
    assert s["peak_oil_bbl_d"] == pytest.approx(want["peak"], abs=0.005)
    assert s["margin_incremental_inr_per_cycle_day"] == pytest.approx(want["incr"], abs=1.0)


# ------------------------------------------------------ water-cut state ----
def test_water_cut_profile_starts_high_and_falls_to_formation(params):
    # rev 12: the full rate-driven cycle (the float-onset rule would stop it at
    # wc ~0.63, before the tail this test is about)
    df = _run(params, produce_end_rule="rate_cutoff")
    pr = df[df["phase"] == "produce"]
    wc = pr["water_cut"].to_numpy()
    assert wc[0] > 0.85                      # condensate flowback
    assert wc[-1] < 0.60                     # late cycle, oil-richer
    assert wc[-1] > cycle.formation_water_cut(params)   # bounded below by f_w
    assert np.all(np.diff(wc) <= 1e-9)       # monotone: the tank only drains
    s = cycle.summary(df, params)
    # most injected water returns (Prats/Butler), never more than was mobile
    assert 0.5 * 1500 < s["condensate_produced_m3"] <= s["condensate_initial_m3"] + 1e-6
    assert s["condensate_initial_m3"] == pytest.approx(cycle.condensate_recovery_frac(params) * 1500)
    # water = condensate + formation water; the pump lifts oil + water
    assert np.allclose(pr["water_m3d"], pr["oil_m3d"] * pr["water_cut"] / (1 - pr["water_cut"]))


def test_more_condensate_recovery_keeps_the_stream_wetter_longer(params):
    lo = copy.deepcopy(params)
    lo["fluid"]["condensate_recovery_frac"] = 0.5
    hi = copy.deepcopy(params)
    hi["fluid"]["condensate_recovery_frac"] = 0.9
    a, b = _s(lo), _s(hi)
    assert b["water_cut_start"] > a["water_cut_start"]
    assert b["water_total_m3"] > a["water_total_m3"]


def test_cold_well_runs_at_the_formation_cut(params):
    c = cycle.cold_baseline(params)
    assert c["water_cut"] == pytest.approx(cycle.formation_water_cut(params))
    const = copy.deepcopy(params)
    const["fluid"]["water_cut_model"] = "constant"
    assert cycle.cold_baseline(const)["water_cut"] == pytest.approx(0.85)


def test_float_binds_late_in_the_oil_continuous_phase(params):
    """The rev-11 FINDING: once the condensate is recovered the stream falls
    below the [ASSUMPTION] 0.70 inversion, turns oil-continuous (Brinkman W/O),
    and the float alarm trips in the late, cool part of the reference cycle --
    never in the early, hot, water-continuous part."""
    df = _run(params)
    s = cycle.summary(df, params)
    pr = df[df["phase"] == "produce"].reset_index(drop=True)
    inv = params["fluid"]["emulsion_inversion_wc"]
    assert s["max_floating_index"] > 0.6 and s["failures_expected"] > 0
    first_alarm = s["first_float_alarm_produce_day"]
    assert first_alarm is not None and first_alarm > 0.5 * len(pr)
    assert (pr.loc[pr["water_cut"] >= inv, "floating_index"] < 0.05).all()
    assert pr["water_cut"].iloc[int(first_alarm)] < inv


def test_spm_acts_through_float_and_power_not_oil(params):
    """rev 11 FINDING: at the reference the stream is reservoir-limited from
    ~4 spm, so SPM moves cycle oil < 1 % over 3-6 spm; it moves the float
    exposure and the pumping power, so the incremental margin rises as SPM falls.
    rev 12: true for the rate-cutoff rule; under the "either" rule SPM also
    moves the float-onset DAY and therefore cycle oil (test_physics_wave4.py)."""
    s = {spm: _s(params, spm=spm, produce_end_rule="rate_cutoff") for spm in (3, 4, 5, 6)}
    oils = [s[k]["oil_total_m3"] for k in s]
    assert (max(oils) - min(oils)) / max(oils) < 0.01
    assert s[3]["failures_expected"] < s[6]["failures_expected"]
    assert s[3]["margin_incremental_inr_per_cycle_day"] > s[6]["margin_incremental_inr_per_cycle_day"]


# ---------------------------------------------------- steam P-T coupling ----
def test_PT_consistency_passes_at_the_default(params):
    chk = thermal.steam_state_check(params)
    assert chk["model"] == "saturated_P"
    assert chk["consistent"] and chk["warnings"] == []
    assert chk["injection_margin_kPa"] > 0.0
    thermal._WARNED_STEAM_STATES.clear()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        _run(params)
    assert not any("steam-state consistency" in str(w.message) for w in rec)


def test_higher_wellhead_pressure_is_hotter_steam(params):
    st = {p: thermal.steam_state(params, p) for p in (85, 91, 97)}
    for p in (85, 91, 97):
        s = st[p]
        assert s["P_sandface_kPa"] > s["P_wellhead_kPa"]          # column head adds
        assert s["T_sandface_C"] == pytest.approx(thermal.T_sat_C(s["P_sandface_kPa"]))
        assert 0.8e3 < s["dP_column_kPa"] < 1.4e3                   # ~90-105 kg/m3 wet column
    assert st[85]["T_sandface_C"] < st[91]["T_sandface_C"] < st[97]["T_sandface_C"]
    assert 298.0 <= st[85]["T_wellhead_C"] <= 300.0 and 307.0 <= st[97]["T_wellhead_C"] <= 309.0
    # heat delivered per kg rises only slightly (h_f up, h_fg down); fuel +/-0.2 %
    assert 0 < st[97]["h_delivered_J_per_kg"] / st[85]["h_delivered_J_per_kg"] - 1 < 0.05
    assert abs(st[97]["fuel_factor"] - 1) < 0.003 and st[91]["fuel_factor"] == pytest.approx(1.0)
    # the zone runs hotter at higher pressure
    a = _s(params, p_wellhead_kgf_cm2=85)
    b = _s(params, p_wellhead_kgf_cm2=97)
    assert b["T_sandface_C"] > a["T_sandface_C"] + 5.0


def test_if97_table_matches_the_saturation_line():
    for T in (250.0, 290.0, 310.0, 330.0):
        s = thermal.sat_props_T(T)
        assert s["h_f_kJkg"] == pytest.approx(thermal.water_enthalpy_kJkg(T), rel=0.01)
    assert thermal.sat_props_T(290.0)["h_fg_kJkg"] == pytest.approx(1476.8, rel=1e-3)


def test_recharge_is_capped_at_the_sandface_pressure(params):
    s = _s(params)
    st = thermal.steam_state(params)
    assert s["recharge_capped"] is True
    assert s["recharge_kPa"] == pytest.approx(st["P_sandface_kPa"] - params["reservoir"]["P_current_kPa"])
    hi = _s(params, p_wellhead_kgf_cm2=97)
    assert hi["recharge_kPa"] > s["recharge_kPa"]


def test_injection_impossible_warns_and_runs(params):
    q = copy.deepcopy(params)
    q["reservoir"]["P_current_kPa"] = 11400.0   # virgin: above P_sf at 91 kgf/cm2
    chk = thermal.steam_state_check(q)
    assert not chk["consistent"] and "cannot enter" in chk["warnings"][0]
    thermal._WARNED_STEAM_STATES.clear()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        s = _s(q)
    assert any("steam-state consistency" in str(w.message) for w in rec)
    assert s["recharge_kPa"] == 0.0 and s["oil_total_m3"] > 0


# --------------------------------------------------------------- stroke ----
def test_stroke_lever_scales_displacement(params):
    opts = srp.stroke_options_m(params)
    assert [round(x / 0.0254) for x in opts] == [64, 74, 86, 100, 120, 144]
    caps = [srp.pump_state(4.0, S, 20.0, 1e6, params)["pump_capacity_m3d"] for S in opts]
    assert np.allclose(np.array(caps) / caps[2], np.array(opts) / opts[2])
    # longer stroke at the same SPM: faster rods, more float exposure
    fi = [srp.pump_state(4.0, S, 2000.0, 1.0, params, water_cut=0.5)["floating_index"] for S in opts]
    assert all(a <= b for a, b in zip(fi, fi[1:]))


def test_stroke_does_not_change_the_cold_counterfactual(params):
    a = _run(params, stroke_m=64 * 0.0254)
    b = _run(params, stroke_m=144 * 0.0254)
    assert a["electric_cold_kWh"].iloc[0] == b["electric_cold_kWh"].iloc[0]
    assert a.attrs["stroke_m"] == pytest.approx(64 * 0.0254)


@pytest.mark.parametrize("spm,stroke_in,mu,wc", [(5.0, 86, 50.0, 0.85), (6.0, 144, 50.0, 0.85),
                                                  (4.0, 120, 300.0, 0.5)])
def test_mills_peak_prl_tracks_the_wave_equation_card(params, spm, stroke_in, mu, wc):
    S = stroke_in * 0.0254
    mu_d = srp.rod_drag_viscosity_cP(mu, params, water_cut=wc, T_C=150.0)
    card = dyno.compute_cards(spm, S, mu, 0.85, wc, params, n_points=60, T_C=150.0)
    assert srp.peak_prl_kN(spm, S, mu_d, wc, params) == pytest.approx(card["peak_prl_kN"], rel=0.15)


def test_prl_cap_is_the_unit_rating_and_binds_in_the_float_regime(params):
    assert srp.max_prl_kN(params) == pytest.approx(113.9)
    # rev 12: an operator who keeps pumping floating rods (rate-cutoff rule)
    s = _s(params, spm=6, stroke_m=144 * 0.0254, cutoff_m3d=0.6, produce_end_rule="rate_cutoff")
    assert s["max_peak_prl_kN"] > srp.max_prl_kN(params) and s["prl_cap_exceeded_days"] > 0
    assert _s(params, spm=3, stroke_m=64 * 0.0254, cutoff_m3d=1.6)["prl_cap_exceeded_days"] == 0


# ------------------------------------------------------------ optimiser ----
def test_cutoffs_are_prefixes_of_one_run(params):
    from ml import recommend_physics as rp
    full = cycle.simulate_css_cycle(1600, 10, 0.6, 4, params, stroke_m=2.54, p_wellhead_kgf_cm2=93)
    decks = rp.price_decks(params)
    cuts = [0.6, 0.9, 1.3, 1.8]
    tab = rp._cutoff_table(full, cuts, {d: decks[d]["economics"] for d in decks})
    for j, c in enumerate(cuts):
        direct = cycle.simulate_css_cycle(1600, 10, c, 4, params, stroke_m=2.54, p_wellhead_kgf_cm2=93)
        assert len(rp._truncate_at_cutoff(full, c)) == len(direct)
        for d in decks:
            s = cycle.summary(direct, decks[d])
            assert tab[d][j] == pytest.approx(s["margin_incremental_inr_per_cycle_day"], rel=1e-9, abs=1e-6)
        assert tab["max_fi"][j] == pytest.approx(cycle.summary(direct, params)["max_floating_index"])


def test_5d_optimiser_respects_constraints_and_reports_coverage(params):
    from ml import recommend_physics as rp
    grid = {"steam_t": [1000.0, 1500.0], "p_wellhead_kgf_cm2": [85.0, 97.0],
            "cutoff_m3d": [0.6, 1.25, 1.6], "stroke_in": [64.0, 144.0], "spm": [3.0, 6.0]}
    res = rp.best_settings_physics_5d(params, grid=grid)
    # rev 12: the conservative level (FI line 0.5) is the same rule run with
    # its own alarm line, so it has its own 16 simulations
    assert res["n_simulations"] == 32 and res["n_grid_points"] == 48
    assert res["controls_coverage"] == {
        "steam_volume": "optimised", "injection_pressure": "optimised", "soak": "modelled-fixed",
        "cutoff": "optimised", "stroke_length": "optimised", "spm": "optimised",
        "vfd": "modelled-as-spm-schedule"}
    for level, fi_max in (("aggressive", 0.6), ("conservative", 0.5)):
        e = res["levels"][level]["minimax_regret"]["evaluation"]
        assert res["levels"][level]["fi_alarm_line"] == fi_max
        assert e["prl_ok"] and e["float_alarm_days"] <= params["css"]["fi_alarm_days"]
    # under the rev-11 rate-cutoff rule both levels are the old max-FI tests
    rc = copy.deepcopy(params)
    rc["css"]["produce_end_rule"] = "rate_cutoff"
    res_rc = rp.best_settings_physics_5d(rc, grid=grid)
    assert res_rc["n_simulations"] == 16
    for level, fi_max in (("aggressive", 0.6), ("conservative", 0.5)):
        e = res_rc["levels"][level]["minimax_regret"]["evaluation"]
        assert e["max_floating_index"] <= fi_max and e["prl_ok"]
    assert res["price_of_constraints_by_deck"]["fy25_realisation"] >= 0.0
    assert rp.best_settings_physics(params, grid_values={"steam_t": [1300.0], "cutoff_m3d": [1.6],
                                                         "spm": [3.0]})["controls_coverage"]["vfd"] \
        == "modelled-as-spm-schedule"


def test_uq_constant_cut_params_keep_the_water_cut_input(legacy_params):
    from ml import uq
    assert list(uq.build_uncertain_inputs(legacy_params))[0] == "water_cut"


def test_calibrate_default_free_follows_the_water_cut_model(params, legacy_params):
    from twin import calibrate
    assert calibrate.default_free(params) == calibrate.DEFAULT_FREE_STATE
    assert calibrate.default_free(legacy_params) == calibrate.DEFAULT_FREE
    p = calibrate.apply(params, {"formation_water_cut": 0.5, "condensate_recovery_frac": 0.8})
    assert cycle.formation_water_cut(p) == 0.5 and cycle.condensate_recovery_frac(p) == 0.8


def test_dyno_cards_follow_the_days_water_cut(params):
    """dyno.card_for_row uses the frame's own produced-stream cut (rev 11): the
    early card is water-continuous, the late one oil-continuous and draggier."""
    df = _run(params)
    pr = df[df["phase"] == "produce"].reset_index(drop=True)
    early = dyno.card_for_row(pr.iloc[0], params, n_points=60, stroke_m=df.attrs["stroke_m"])
    late = dyno.card_for_row(pr.iloc[len(pr) - 1], params, n_points=60, stroke_m=df.attrs["stroke_m"])
    assert early["inputs"]["water_cut"] == pytest.approx(pr["water_cut"].iloc[0])
    assert late["inputs"]["water_cut"] < params["fluid"]["emulsion_inversion_wc"]
    assert late["inputs"]["mu_drag_cP"] > 100.0 * early["inputs"]["mu_drag_cP"]
