"""rev 13 -- physics wave 5 (27 Sep 2026): the operator's response to rod float
as a control (css.float_policy), applied alike to baseline, recommendation and
the cold counterfactual; a smooth W/O <-> O/W inversion band; the injectivity
margin gate; the royalty/cess deck and the mid-range diesel discount;
mobility-weighted flowback; the rev-13 ML labels.

See docs/model-improvement/TIER1_PROGRESS_LOG.md section 12 and
params/CHANGELOG.md rev 13.
"""
import copy
import math

import numpy as np
import pytest

from twin import cycle, srp, thermal

IN = 0.0254
REF = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5)
BASE = dict(steam_t=1300, soak_days=10, cutoff_m3d=1.3, spm=5, stroke_m=86 * IN, p_wellhead_kgf_cm2=91)
REC = dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=4.5, stroke_m=64 * IN, p_wellhead_kgf_cm2=89)
REC12 = dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=3, stroke_m=64 * IN, p_wellhead_kgf_cm2=85)
NET = "margin_with_opex_inr_per_cycle_day"
INC = "margin_incremental_inr_per_cycle_day"


def _sim(params, pt, **kw):
    return cycle.simulate_css_cycle(params=params, **dict(pt, **kw))


def _s(params, pt, **kw):
    return cycle.summary(_sim(params, pt, **kw), params)


# ------------------------------------------------------------- switches ----
@pytest.mark.parametrize("pt,want", [
    (REF, dict(SOR=4.499, incr=-1690, days=152)),
    (dict(BASE), dict(SOR=4.351, incr=-1601, days=140)),
    (REC12, dict(SOR=3.191, incr=7973, days=180)),
])
def test_legacy_rev12_switches_reproduce_rev12(params, pt, want):
    """cycle.legacy_rev12_params (pull policy, rev-12 cold well, sharp inversion,
    M = 1, no injection gate, 0.30 diesel discount) reproduces TIER1 11.5."""
    q = cycle.legacy_rev12_params(params)
    s = _s(q, pt)
    assert s["SOR_t_per_m3"] == pytest.approx(want["SOR"], abs=5e-4)
    assert s[INC] == pytest.approx(want["incr"], abs=1.0)
    assert s["produce_days"] == want["days"] and s["produce_end_reason"] == "float_onset"
    assert s["float_policy"] == "pull" and s["cold_status"] == "pumped"


def test_rev13_defaults(params):
    css = params["css"]
    assert css["float_policy"] == "pull" and css["cold_counterfactual"] == "policy"
    assert css["vfd_hold_fi"] == pytest.approx(0.6) and css["vfd_spm_floor"] == pytest.approx(2.0)
    assert params["fluid"]["emulsion_inversion_band_wc"] == pytest.approx(0.075)
    assert params["fluid"]["flowback_mobility_ratio"] == pytest.approx(1.0)
    assert params["steam"]["min_injection_margin_kPa"] == pytest.approx(400.0)
    assert params["economics"]["diesel_bulk_discount_frac"] == pytest.approx(0.15)
    assert cycle._DEFAULT_ECONOMICS["diesel_bulk_discount_frac"] == pytest.approx(0.15)
    with pytest.raises(ValueError):
        _sim(params, REF, float_policy="bogus")
    q = copy.deepcopy(params)
    q["css"].pop("float_policy")
    assert cycle.float_policy_of(q) == "pull"                     # absent key = rev 12
    assert _s(q, REF)[NET] == pytest.approx(_s(params, REF)[NET])
    q["css"]["produce_end_rule"] = "rate_cutoff"
    assert cycle.float_policy_of(q) == "none"


# -------------------------------------------------------- float policies ----
def test_pull_policy_is_rev12_operation(params):
    """pull: no slowing (the unit stays at its start speed), the alarm trips
    and the well is pulled on the 3rd consecutive alarm day."""
    df = _sim(params, REF, float_policy="pull")
    s = cycle.summary(df, params)
    pr = df[df["phase"] == "produce"]
    assert s["min_spm"] == pytest.approx(5.0) and s["days_vfd_slowed"] == 0
    fi = pr["floating_index"].to_numpy()
    assert (fi[-3:] > 0.6).all() and (fi[:-3] <= 0.6).all()
    assert s["produce_end_reason"] == "float_onset" and s["failures_expected"] == 3


def test_vfd_hold_holds_the_line_and_pulls_only_at_the_floor(params):
    """vfd_hold: FI never exceeds 0.6 while the VFD still has room (SPM above
    the 2-spm floor); the alarm fires only at the floor and the well is pulled
    after css.fi_alarm_days alarm days there; the cycle runs longer than pull."""
    df = _sim(params, REF, float_policy="vfd_hold")
    s = cycle.summary(df, params)
    pr = df[df["phase"] == "produce"]
    above = pr["spm"] > 2.0 + 1e-9
    assert (pr.loc[above, "floating_index"] <= 0.6 + 1e-9).all()
    alarm = pr["floating_index"] > 0.6 + 1e-9
    assert (pr.loc[alarm, "spm"] <= 2.0 + 1e-9).all() and int(alarm.sum()) == 3
    assert s["produce_end_reason"] == "float_onset" and s["min_spm"] == pytest.approx(2.0)
    assert s["days_vfd_slowed"] > 30 and s["days_at_schedule_floor"] >= 3
    held = pr.loc[above & (pr["spm"] < 5.0 - 1e-9), "floating_index"]
    assert len(held) > 0 and np.allclose(held, 0.6, atol=1e-9)    # held exactly on the line
    pull = _s(params, REF, float_policy="pull")
    assert s["produce_days"] > pull["produce_days"] + 40
    assert s["SOR_t_per_m3"] < pull["SOR_t_per_m3"]


def test_vfd_then_pull_turns_down_only_to_half_speed(params):
    """vfd_then_pull: the VFD slows to max(2 spm, 0.5 x start) = 2.5 spm from a
    5-spm start, then pulls: between pull and vfd_hold."""
    s = _s(params, REF, float_policy="vfd_then_pull")
    hold = _s(params, REF, float_policy="vfd_hold")
    pull = _s(params, REF, float_policy="pull")
    assert s["min_spm"] == pytest.approx(2.5) and s["schedule_floor_spm"] == pytest.approx(2.5)
    assert pull["produce_days"] < s["produce_days"] < hold["produce_days"]
    assert s["failures_expected"] == 3 and s["produce_end_reason"] == "float_onset"
    # from a 3-spm start the turndown floor is below the keep-moving floor: = vfd_hold
    a = _s(params, REC12, float_policy="vfd_then_pull")
    b = _s(params, REC12, float_policy="vfd_hold")
    assert a[NET] == pytest.approx(b[NET])


def test_none_policy_runs_floating_rods_to_the_cutoff(params):
    s = _s(params, REF, float_policy="none")
    assert s["produce_end_reason"] == "rate_cutoff" and s["max_floating_index"] == pytest.approx(1.0)
    assert s["failures_expected"] > 60
    rc = _s(params, REF, produce_end_rule="rate_cutoff")          # the rev <= 11 override keeps its meaning
    assert rc["float_policy"] == "none" and rc["produce_days"] == s["produce_days"]


def test_policies_keep_the_cutoff_prefix_property(params):
    from ml import recommend_physics as rp
    decks = rp.price_decks(params)
    for pol in ("vfd_hold", "vfd_then_pull"):
        full = _sim(params, REC, float_policy=pol)
        cuts = [0.6, 1.2, 1.6]
        tab = rp._cutoff_table(full, cuts, {d: decks[d]["economics"] for d in decks})
        for j, c in enumerate(cuts):
            direct = _sim(params, dict(REC, cutoff_m3d=c), float_policy=pol)
            assert len(rp._truncate_at_cutoff(full, c)) == len(direct)
            for d in decks:
                assert tab[d][j] == pytest.approx(cycle.summary(direct, decks[d])[INC], rel=1e-9, abs=1e-6)


# ------------------------------------------------------ cold counterfactual ----
def test_cold_counterfactual_obeys_the_policy_consistently(params):
    """The rev-12 double standard is gone: under every float policy the cold
    well is either shut in (it cannot hold FI <= 0.6 at the 2-spm floor -- the
    base case, FI 1.0, PRL 189 kN) or produced within the policy; it is never
    'unpumpable yet producing'. (Replaces the rev-12 strict xfail
    test_cold_well_pumpable_at_2_spm_on_the_assumed_unit, whose physical
    finding -- FI 1.0 at 2 spm x 86 in -- is pinned by
    test_physics_wave4.test_cold_well_numbers.)"""
    cap = srp.max_prl_kN(params)
    for pol in ("pull", "vfd_hold", "vfd_then_pull"):
        c = cycle.cold_counterfactual_well(params, policy=pol)
        assert c["status"] == cycle.cold_counterfactual_well(params, policy=pol, mode="policy")["status"]
        assert c["status"] == "shut_in_float" and c["oil_m3d"] == 0.0 and c["electric_kWh_d"] == 0.0
        assert c["floating_index"] > 0.6
        s = _s(params, REC, float_policy=pol)
        assert s["cold_status"] == "shut_in_float" and s["oil_cold_baseline_m3"] == 0.0
        assert s[INC] == pytest.approx(s[NET])                     # counterfactual cash 0
        assert s["cold_rate_m3d"] == pytest.approx(0.445, abs=0.002)   # physical cold rate kept (uplift)
    # a cold well that CAN hold the line at the floor is produced (formation cut 0)
    dry = copy.deepcopy(params)
    dry["fluid"]["formation_water_cut"] = 0.0
    c = cycle.cold_counterfactual_well(dry, policy="vfd_hold")
    assert c["status"] == "pumped" and c["floating_index"] <= 0.6 and c["peak_prl_kN"] <= cap
    assert c["oil_m3d"] == pytest.approx(c["ipr_rate_m3d"])
    # "none" = the operator ignores float for the cold well too: rev-12 cold well
    legacy = cycle.cold_baseline(params)
    c = cycle.cold_counterfactual_well(params, policy="none")
    assert c["status"] == "pumped" and c["electric_kWh_d"] == pytest.approx(legacy["electric_kWh_d"])


def test_pumpable_counterfactual_is_the_field_fact(params):
    """'pumpable': slowed below the keep-moving floor until FI <= 0.6 (0.53 spm
    at base), full IPR rate, PRL inside the rating, ~49 kWh/d."""
    c = cycle.cold_counterfactual_well(params, policy="vfd_hold", mode="pumpable")
    assert c["status"] == "pumped_slow" and 0.4 < c["spm"] < 0.7
    assert c["floating_index"] <= 0.6 + 1e-9 and c["peak_prl_kN"] <= srp.max_prl_kN(params)
    assert c["oil_m3d"] == pytest.approx(c["ipr_rate_m3d"]) and 30 < c["electric_kWh_d"] < 80
    q = copy.deepcopy(params)
    q["css"]["cold_pumpable_min_spm"] = 1.0
    assert cycle.cold_counterfactual_well(q, policy="vfd_hold", mode="pumpable")["status"] == "shut_in_float"
    # the paired gain does not depend on the counterfactual choice
    g = {}
    for mode in ("policy", "pumpable", "legacy"):
        r = _s(params, REC, cold_counterfactual=mode, float_policy="vfd_hold")
        b = _s(params, BASE, cold_counterfactual=mode, float_policy="vfd_hold")
        g[mode] = (r[INC] - b[INC], r[NET] - b[NET])
    for mode in g:
        assert g[mode][0] == pytest.approx(g["policy"][1], abs=1e-6)


# ------------------------------------------------------- smooth inversion ----
def test_inversion_band_is_smooth_and_the_sharp_switch_is_its_zero_width_limit(params):
    q = copy.deepcopy(params)
    T = 110.0
    mu_o = 300.0
    wo = mu_o * srp.wo_relative_viscosity(0.6625, q)
    ow = srp._ow_branch_cP(0.7375, q, T)
    # band edges are the two branches; the centre is the geometric mean
    assert srp.rod_drag_viscosity_cP(mu_o, q, water_cut=0.6625, T_C=T) == pytest.approx(wo)
    assert srp.rod_drag_viscosity_cP(mu_o, q, water_cut=0.7375, T_C=T) == pytest.approx(ow)
    mid = srp.rod_drag_viscosity_cP(mu_o, q, water_cut=0.70, T_C=T)
    wo_c = mu_o * srp.wo_relative_viscosity(0.70, q)
    ow_c = srp._ow_branch_cP(0.70, q, T)
    assert mid == pytest.approx(math.sqrt(wo_c * ow_c), rel=1e-9)
    wcs = np.linspace(0.60, 0.80, 401)
    mu = np.array([srp.rod_drag_viscosity_cP(mu_o, q, water_cut=w, T_C=T) for w in wcs])
    assert (np.diff(np.log(mu))[wcs[1:] > 0.66] <= 1e-12).all()   # monotone through the band
    sharp = copy.deepcopy(q)
    sharp["fluid"]["emulsion_inversion_band_wc"] = 0.0
    assert srp.rod_drag_viscosity_cP(mu_o, sharp, water_cut=0.699, T_C=T) / \
        srp.rod_drag_viscosity_cP(mu_o, sharp, water_cut=0.700, T_C=T) > 1000.0
    sharp["fluid"].pop("emulsion_inversion_band_wc")
    assert srp.inversion_band_wc(sharp) == 0.0


def test_no_tenfold_drag_jump_per_day_through_the_crossing(params):
    """The rev-12 cliff: 3,400x in one day. With the band: < 10x (~1.2x) per
    day along the reference cycle, and the float index moves < 0.1 per day."""
    q = cycle.with_controls(params, stroke_m=86 * IN)
    df = _sim(params, REF, float_policy="pull")
    pr = df[df["phase"] == "produce"]
    mu = np.array([srp.rod_drag_viscosity_cP(m, q, water_cut=w, T_C=T)
                   for m, w, T in zip(pr["mu_cP"], pr["water_cut"], pr["T_res_C"])])
    ratio = np.maximum(mu[1:] / mu[:-1], mu[:-1] / mu[1:])
    assert ratio.max() < 10.0 and ratio.max() < 1.5
    assert np.max(np.abs(np.diff(pr["floating_index"].to_numpy()))) < 0.1
    sharp = cycle.legacy_rev12_params(params)
    df0 = _sim(sharp, REF)
    pr0 = df0[df0["phase"] == "produce"]
    assert np.max(np.diff(pr0["floating_index"].to_numpy())) > 0.2      # the cliff it replaces


# -------------------------------------------------------------- flowback ----
def test_flowback_mobility_ratio(params):
    base = _s(params, REF, float_policy="vfd_hold")
    q = copy.deepcopy(params)
    q["fluid"].pop("flowback_mobility_ratio")
    assert _s(q, REF, float_policy="vfd_hold")[NET] == pytest.approx(base[NET])   # absent = M 1
    q["fluid"]["flowback_mobility_ratio"] = 10.0
    s10 = _s(q, REF, float_policy="vfd_hold")
    assert s10["water_cut_start"] > base["water_cut_start"] + 0.08
    assert s10["water_cut_end"] < base["water_cut_end"]


# ------------------------------------------------------------ injectivity ----
def test_injection_margin_gate(params):
    """85 kgf/cm2 leaves 53 kPa over the 9.4 MPa P_current: below the 400 kPa
    [ASSUMPTION] margin; 89 leaves ~498 kPa."""
    s85 = _s(params, REC12, float_policy="vfd_hold")
    s89 = _s(params, REC, float_policy="vfd_hold")
    assert s85["injection_margin_kPa"] == pytest.approx(53.3, abs=1.0) and s85["injection_ok"] is False
    assert s89["injection_margin_kPa"] == pytest.approx(498.0, abs=3.0) and s89["injection_ok"] is True
    from ml import recommend_physics as rp
    grid = {"steam_t": [1000.0], "p_wellhead_kgf_cm2": [85.0, 89.0, 93.0], "cutoff_m3d": [0.6],
            "stroke_in": [64.0], "spm": [4.5]}
    res = rp.best_settings_physics_5d(params, grid=grid, policies=("vfd_hold",))
    mm = res["levels"]["aggressive"]["minimax_regret"]
    assert mm["settings"]["p_wellhead_kgf_cm2"] == 89.0 and mm["evaluation"]["injection_ok"]
    assert res["constraints"]["n_points_failing_injection_margin"] == 1
    loose = copy.deepcopy(params)
    loose["steam"]["min_injection_margin_kPa"] = 0.0
    res0 = rp.best_settings_physics_5d(loose, grid=grid, policies=("vfd_hold",))
    assert res0["levels"]["aggressive"]["minimax_regret"]["settings"]["p_wellhead_kgf_cm2"] == 85.0
    strict = copy.deepcopy(params)
    strict["steam"]["min_injection_margin_kPa"] = 500.0
    res5 = rp.best_settings_physics_5d(strict, grid=grid, policies=("vfd_hold",))
    assert res5["levels"]["aggressive"]["minimax_regret"]["settings"]["p_wellhead_kgf_cm2"] == 93.0


# ------------------------------------------------------------ price decks ----
def test_deck_presets(params):
    from ml import decompose, recommend_physics as rp
    ec = params["economics"]
    lev = ec["oil_price_presets"]["fy25_net_of_levies"]
    assert lev["inr_per_bbl"] == pytest.approx(3600.0)
    assert "2,986.84" in lev["source"] and "2,567.04" in lev["source"]
    assert ec["diesel_discount_presets"] == {"mid_0.15": 0.15, "bulk_0.30": 0.30, "retail_0": 0.0}
    assert cycle.steam_cost_inr_per_t(ec) == pytest.approx(71 / 0.83 * 97.8 * 0.85, rel=1e-9)
    d = rp.price_decks(params)
    assert list(d) == ["fy25_realisation", "fy26_floor", "fy25_net_of_levies"]
    assert [d[k]["economics"]["oil_price_inr_per_bbl"] for k in d] == [5992.0, 4840.0, 3600.0]
    assert list(decompose.decks(params)) == list(d)
    assert rp.MINIMAX_DECKS == ("fy25_realisation", "fy26_floor")


# ------------------------------------------------ optimiser: policy dimension ----
def test_optimiser_policy_dimension_and_same_policy_gain(params):
    """Small grid: the canonical point is a VFD policy; the same-policy gain is
    a net-cash difference (counterfactual-free); 'none' is searched with the
    max-FI test and loses to a floating baseline (rod failure is not priced)."""
    from ml import recommend_physics as rp
    grid = {"steam_t": [1000.0, 1300.0], "p_wellhead_kgf_cm2": [89.0], "cutoff_m3d": [0.6, 1.45],
            "stroke_in": [64.0, 86.0], "spm": [3.0, 4.5, 5.0]}
    res = rp.best_settings_physics_5d(params, grid=grid, policies=rp.ALL_POLICIES)
    c = res["canonical_recommendation"]["settings"]
    assert c["float_policy"] in ("vfd_hold", "vfd_then_pull") and c["stroke_in"] == 64.0
    assert res["canonical_policies"] == ["pull", "vfd_hold", "vfd_then_pull"]
    g = res["gain_vs_baseline_b_same_policy"]
    base = res["baseline_b_by_policy"]
    for pol in ("pull", "vfd_hold", "vfd_then_pull", "none"):
        rec_e = res["by_policy"][pol]["aggressive"]["minimax_regret"]["evaluation"]
        assert g[pol]["fy25_realisation"] == pytest.approx(
            rec_e["fy25_realisation"][NET] - base[pol]["fy25_realisation"][NET])
    assert g["pull"]["fy25_realisation"] > g["vfd_hold"]["fy25_realisation"] > 0
    assert g["none"]["fy25_realisation"] < 0
    none_rec = res["by_policy"]["none"]["aggressive"]["minimax_regret"]["evaluation"]
    assert none_rec["max_floating_index"] <= 0.6 and none_rec["fy25_realisation"]["produce_end_reason"] == "rate_cutoff"


def test_same_policy_gain_at_the_canonical_point(params):
    """TIER1 12: under the SAME VFD-hold policy the rev-13 rec beats baseline
    (b) by ~Rs 3.3k/d FY25 (net cash), and the SOR falls 3.29 -> 2.83. Under
    the pull policy the same comparison is ~Rs 12.9k/d (the rev-12 headline
    structure); with no float response the float-safe point loses ~Rs 3.9k/d."""
    r = _s(params, REC, float_policy="vfd_hold")
    b = _s(params, BASE, float_policy="vfd_hold")
    assert r[NET] - b[NET] == pytest.approx(3332.0, abs=60.0)
    assert r["SOR_t_per_m3"] == pytest.approx(2.831, abs=0.005)
    assert b["SOR_t_per_m3"] == pytest.approx(3.288, abs=0.005)
    rp_ = _s(params, dict(REC, spm=3.0), float_policy="pull")
    bp = _s(params, BASE, float_policy="pull")
    assert rp_[NET] - bp[NET] == pytest.approx(12917.0, abs=150.0)
    rn = _s(params, dict(REC, spm=3.0, cutoff_m3d=1.45), float_policy="none")
    bn = _s(params, BASE, float_policy="none")
    assert rn[NET] - bn[NET] == pytest.approx(-3865.0, abs=150.0)
    assert rn["max_floating_index"] <= 0.6 and bn["failures_expected"] > 60


def test_decomposition_with_policy_lever(params):
    from ml import decompose
    dp = decompose.decks(params)
    rec = {"steam_t": 1000.0, "soak_days": 10.0, "cutoff_m3d": 0.6, "spm": 4.5, "stroke_in": 64.0,
           "p_wellhead_kgf_cm2": 89.0, "float_policy": "vfd_hold"}
    same = decompose.decompose(dict(decompose.BASELINE_B, float_policy="vfd_hold"), rec, dp)
    assert "float_policy" not in same["levers"]
    e = same["fy25_realisation"]
    assert sum(e["shapley"].values()) == pytest.approx(e["total_gain"], rel=1e-9)
    assert e["shapley"]["stroke_in"] == max(e["shapley"].values())      # the 64-in stroke leads
    cross = decompose.decompose(dict(decompose.BASELINE_B, float_policy="pull"), rec, dp)
    assert "float_policy" in cross["levers"]
    e = cross["fy25_realisation"]
    assert sum(e["shapley"].values()) == pytest.approx(e["total_gain"], rel=1e-9)
    assert e["shapley"]["float_policy"] > 0.5 * e["total_gain"]          # switching policy is most of it


# ----------------------------------------------------------------- UQ / ML ----
def test_uq_rev13_inputs_and_points(params):
    from ml import uq
    spec = uq.build_uncertain_inputs(params)
    names = list(spec)
    assert names[names.index("emulsion_phi_star") + 1:] == [
        "emulsion_mu_r_max", "fi_alarm_days", "emulsion_inversion_band_wc", "flowback_mobility_ratio",
        "cold_counterfactual"]
    assert spec["diesel_bulk_discount_frac"]["base"] == pytest.approx(0.15)
    q = copy.deepcopy(params)
    for v, want in ((0.2, 1.0), (1.5, 3.0), (2.99, 10.0)):
        spec["flowback_mobility_ratio"]["setter"](q, v)
        assert q["fluid"]["flowback_mobility_ratio"] == want
    for v, want in ((0.3, "policy"), (1.7, "pumpable")):
        spec["cold_counterfactual"]["setter"](q, v)
        assert q["css"]["cold_counterfactual"] == want
    spec["fi_alarm_days"]["setter"](q, 6.6)
    assert q["css"]["fi_alarm_days"] == 7.0
    assert uq.POINTS["recommended"]["float_policy"] == "vfd_hold"
    assert set(uq.SAME_POLICY_POINTS) == {"vfd_hold", "pull", "none"}
    out = uq._run_point(params, uq.POINTS["conservative"])
    assert out["injection_ok"] == 1.0 and out["cold_shut_in"] == 1.0
    assert out["ended_by_float_onset"] == 1.0


def test_generate_data_policy_column_and_labels(params):
    from twin import generate_data
    df = generate_data._sample_inputs(params, 120, 42)
    assert list(df.columns)[-1] == "float_policy"
    assert df["float_policy"].value_counts().to_dict() == {"pull": 40, "vfd_hold": 40, "vfd_then_pull": 40}
    out = generate_data.generate(params, n_rows=12, seed=7)
    for c in ("float_policy", "fi_gt_alarm_any", "float_forced_pull", "end_rate_over_cutoff",
              "float_premature_pull"):
        assert c in out.columns
    assert (out["float_premature_pull"] <= out["float_forced_pull"]).all()
    assert ((out["end_rate_over_cutoff"] >= 1.5) | ~out["float_premature_pull"]).all()


def test_vfd_hold_takes_small_slugs_below_the_literature_sor_band(params):
    """rev 13 FINDING (why the shipped default stays "pull"): operated under
    vfd_hold, the reference cycle's SOR is 3.46 -- 0.0005 below the CalGEM
    field-band floor (Kern River 3.465) -- and a 500-t slug gives SOR ~2.65,
    below the 3-8 literature band; the rev-13 recommendation itself is 2.83.
    First cycles are the most efficient, but no Baghewala SOR datum confirms
    sub-3 values. Under "pull" (the calibration anchor's operation) every
    benchmark band still passes (tests/test_benchmarks.py)."""
    ref = _s(params, REF, float_policy="vfd_hold")
    assert ref["SOR_t_per_m3"] == pytest.approx(3.4645, abs=0.002)
    small = _s(params, dict(REF, steam_t=500), float_policy="vfd_hold")
    assert small["SOR_t_per_m3"] < 3.0
    assert _s(params, REC, float_policy="vfd_hold")["SOR_t_per_m3"] < 3.0
    assert 3.0 <= _s(params, REF)["SOR_t_per_m3"] <= 4.6            # default (pull) inside
