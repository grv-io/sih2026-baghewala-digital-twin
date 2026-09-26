"""rev 12 -- physics wave 4 (27 Sep 2026): Pal-Rhodes W/O emulsion with a
10x cap, the float-onset produce-end operating rule, AOF_REF_M3D re-tuned to
the field peak band, the rule-aware 5-D optimiser, the full-control LHS.

See docs/model-improvement/TIER1_PROGRESS_LOG.md section 11 and
params/CHANGELOG.md rev 12.
"""
import copy

import numpy as np
import pytest

from twin import cycle, ipr, srp, viscosity

REF = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5)
REC = dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=3,
           stroke_m=64 * 0.0254, p_wellhead_kgf_cm2=85)


def _run(params, **kw):
    return cycle.simulate_css_cycle(params=params, **dict(REF, **kw))


def _s(params, **kw):
    return cycle.summary(_run(params, **kw), params)


# ------------------------------------------------------------ switches ----
@pytest.mark.parametrize("pt,want", [
    (dict(REF, stroke_m=86 * 0.0254, p_wellhead_kgf_cm2=91),
     dict(SOR=3.899, oil=384.7, peak=12.43, incr=4246)),
    (dict(steam_t=1300, soak_days=10, cutoff_m3d=1.3, spm=5), dict(SOR=4.007, oil=324.5, peak=12.01, incr=1910)),
    (dict(steam_t=1000, soak_days=10, cutoff_m3d=1.25, spm=3, stroke_m=64 * 0.0254, p_wellhead_kgf_cm2=93),
     dict(SOR=3.799, oil=263.2, peak=10.89, incr=2153)),
])
def test_legacy_rev11_switches_reproduce_rev11(params, pt, want):
    """cycle.legacy_rev11_params (Brinkman, no cap, rate-cutoff rule, AOF 0.46)
    reproduces TIER1 section 10.4 to the digit."""
    q = cycle.legacy_rev11_params(params)
    s = cycle.summary(cycle.simulate_css_cycle(params=q, **pt), q)
    assert s["SOR_t_per_m3"] == pytest.approx(want["SOR"], abs=5e-4)
    assert s["oil_total_m3"] == pytest.approx(want["oil"], abs=0.05)
    assert s["peak_oil_bbl_d"] == pytest.approx(want["peak"], abs=0.005)
    assert s["margin_incremental_inr_per_cycle_day"] == pytest.approx(want["incr"], abs=1.0)
    assert s["produce_end_reason"] == "rate_cutoff"


# ------------------------------------------------------- emulsion law ----
def test_pal_rhodes_law_constants_and_brinkman_limit(params):
    """mu_r = [1 + (phi/phi*)/(1.187 - phi/phi*)]^2.49 (Pal & Rhodes 1989) =
    Brinkman on phi/(1.187 phi*); phi* = 1/1.187 is Brinkman (to the 2.49 vs
    2.5 exponent). At the shipped phi* = 0.84 the law is Brinkman within 1 %
    over 0-60 % water: the physics change of wave 4 is the CAP, not the law."""
    assert params["fluid"]["emulsion_law"] == "pal_rhodes"
    assert params["fluid"]["emulsion_phi_star"] == pytest.approx(0.84)
    assert params["fluid"]["emulsion_mu_r_max"] == pytest.approx(10.0)
    nocap = copy.deepcopy(params)
    nocap["fluid"]["emulsion_mu_r_max"] = None
    for phi in (0.1, 0.3, 0.45, 0.6):
        x = phi / 0.84
        assert srp.wo_relative_viscosity(phi, nocap) == pytest.approx((1 + x / (1.187 - x)) ** 2.49)
        assert srp.wo_relative_viscosity(phi, nocap) == pytest.approx((1 - phi) ** -2.5, rel=0.01)
    bk = copy.deepcopy(nocap)
    bk["fluid"]["emulsion_phi_star"] = 1 / 1.187
    assert srp.wo_relative_viscosity(0.45, bk) == pytest.approx(0.55 ** -2.49, rel=1e-9)
    assert srp.wo_relative_viscosity(0.0, params) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        q = copy.deepcopy(params)
        q["fluid"]["emulsion_law"] = "bogus"
        srp.wo_relative_viscosity(0.3, q)


def test_emulsion_cap_binds_only_near_inversion(params):
    """The [ASSUMPTION] 10x cap: it binds above ~60 % water (Brinkman 10-19x
    at 60-69 %), never at 30-50 %."""
    mu_r = {phi: srp.wo_relative_viscosity(phi, params) for phi in (0.3, 0.45, 0.5, 0.6, 0.65, 0.69)}
    assert mu_r[0.3] < mu_r[0.45] < mu_r[0.5] < 10.0
    assert mu_r[0.65] == pytest.approx(10.0) and mu_r[0.69] == pytest.approx(10.0)
    assert 9.5 < mu_r[0.6] <= 10.0


@pytest.mark.parametrize("phi_star", [0.65, 0.84, 1.0])
def test_phi_star_uq_range_spans_the_published_band(params, phi_star):
    """UQ U[0.65, 1.0]: mu_r at 45 % water stays inside the published heavy-oil
    W/O band of ~2-10x at 40-50 % water."""
    q = copy.deepcopy(params)
    q["fluid"]["emulsion_phi_star"] = phi_star
    assert 2.0 <= srp.wo_relative_viscosity(0.45, q) <= 10.0


def test_legacy_params_without_the_keys_run_brinkman(params):
    q = copy.deepcopy(params)
    for k in ("emulsion_law", "emulsion_phi_star", "emulsion_mu_r_max"):
        q["fluid"].pop(k)
    assert srp.wo_relative_viscosity(0.65, q) == pytest.approx(0.35 ** -2.5)


# ------------------------------------------------------------ cold well ----
def test_cold_well_numbers(params):
    """The unstimulated counterfactual at the formation cut (45 %) on the
    params' own pump (86 in, 2 spm): the W/O stream is 4.46x the 11,500 cP
    oil (Pal-Rhodes at phi* 0.84 == Brinkman there, below the cap), so the
    wave-4 law change leaves it where rev 11 had it: 51,000 cP, FI 1.0,
    PRL 189 kN, ~433 kWh/d grid. Rate 0.445 m3/d with AOF 0.56."""
    c = cycle.cold_baseline(params)
    assert c["mu_drag_cP"] == pytest.approx(51260.0, rel=0.002)
    assert c["floating_index"] == pytest.approx(1.0)
    assert c["peak_prl_kN"] == pytest.approx(189.4, abs=0.5)
    assert c["electric_kWh_d"] == pytest.approx(433.5, abs=1.0)
    assert c["oil_m3d"] == pytest.approx(0.445, abs=0.002)
    legacy = cycle.cold_baseline(cycle.legacy_rev11_params(params))
    assert c["electric_kWh_d"] == pytest.approx(legacy["electric_kWh_d"], rel=0.005)  # artefact unchanged


def test_cold_well_is_not_pumpable_at_2_spm_and_the_counterfactual_says_so(params):
    """rev 12 strict xfail, UN-XFAILED in rev 13. The physical finding stands:
    at the 45 % formation cut the cold well is NOT pumpable at >= 2 spm on the
    assumed 86-in unit (FI 1.0, Mills PRL 189 kN > 113.9 kN; Pal-Rhodes over the
    published phi* range gives 3.3-9x at 45 % water, pumpability needs mu_r <=
    ~1.9). What the xfail flagged -- a counterfactual that is unpumpable yet
    produces its full rate -- is resolved: the counterfactual now obeys the float
    policy and is consistently SHUT IN (css.cold_counterfactual "policy") or
    produced slowly within FI <= 0.6 ("pumpable"). TIER1 sections 11.2 and 12."""
    c = cycle.cold_baseline(params)
    assert c["spm"] >= 2.0 and c["floating_index"] >= 1.0
    assert c["peak_prl_kN"] > srp.max_prl_kN(params)
    cf = cycle.cold_counterfactual_well(params)
    assert cf["status"] == "shut_in_float" and cf["oil_m3d"] == 0.0
    slow = cycle.cold_counterfactual_well(params, mode="pumpable")
    assert slow["floating_index"] <= 0.6 + 1e-9 and slow["peak_prl_kN"] <= srp.max_prl_kN(params)
    assert slow["oil_m3d"] == pytest.approx(c["oil_m3d"])


def test_cold_well_pumpability_threshold(params):
    """Where the cold well IS pumpable (FI < 1, PRL <= rating): dead-oil drag
    (mu_r = 1) at 2 spm x 86 in, and the base emulsion at 1 spm x 64 in."""
    T0 = params["reservoir"]["T_initial_C"]
    mu_o = viscosity.mu_cP(T0, params)
    pwf = cycle._pump_intake_pressure_kPa(params)
    q = cycle.cold_baseline(params)["ipr_rate_m3d"]
    cap = srp.max_prl_kN(params)
    oil_drag = copy.deepcopy(params)
    oil_drag["fluid"]["tubing_viscosity_model"] = "oil"
    a = srp.pump_state(2.0, 86 * 0.0254, mu_o, q, oil_drag, intake_pressure_kPa=pwf, T_C=T0, water_cut=0.45)
    assert a["floating_index"] < 1.0 and a["peak_prl_kN"] <= cap
    b = srp.pump_state(2.0, 86 * 0.0254, 2.0 * mu_o, q, oil_drag, intake_pressure_kPa=pwf, T_C=T0,
                       water_cut=0.45)
    assert b["floating_index"] >= 1.0 or b["peak_prl_kN"] > cap     # 2x already fails
    c = srp.pump_state(1.0, 64 * 0.0254, mu_o, q, params, intake_pressure_kPa=pwf, T_C=T0, water_cut=0.45)
    assert c["floating_index"] < 1.0 and c["peak_prl_kN"] <= cap and c["prod_rate_m3d"] == pytest.approx(q)


# ------------------------------------------------------ produce-end rule ----
def test_produce_end_rule_defaults_and_validation(params):
    assert params["css"]["produce_end_rule"] == "either"
    assert cycle.fi_alarm(params) == pytest.approx(0.6) and cycle.fi_alarm_days(params) == 3
    q = copy.deepcopy(params)
    q["css"].pop("produce_end_rule")
    assert cycle.produce_end_rule_of(q) == "rate_cutoff"          # absent key = rev <= 11
    with pytest.raises(ValueError):
        _run(params, produce_end_rule="bogus")


def test_either_rule_float_branch_ends_the_reference(params):
    """Reference (5 spm / 86 in): the float alarm trips on produce day 149 and
    the rule ends the cycle on the 3rd consecutive alarm day (day 151), with
    the oil rate still above the 1.2 cutoff."""
    df = _run(params)
    s = cycle.summary(df, params)
    pr = df[df["phase"] == "produce"]
    assert df.attrs["produce_end_reason"] == "float_onset" == s["produce_end_reason"]
    assert s["failures_expected"] == 3
    fi = pr["floating_index"].to_numpy()
    assert (fi[-3:] > 0.6).all() and (fi[:-3] <= 0.6).all()
    assert pr["oil_m3d"].iloc[-1] > REF["cutoff_m3d"]
    assert 140 <= s["produce_days"] <= 165
    assert s["water_cut_end"] < params["fluid"]["emulsion_inversion_wc"]


def test_either_rule_rate_branch_when_the_cutoff_comes_first(params):
    """A high cutoff on slow rods: the rate cutoff ends the cycle before any
    float alarm (the "either" rule's other branch)."""
    s = cycle.summary(cycle.simulate_css_cycle(params=params, **dict(REC, cutoff_m3d=1.6)), params)
    assert s["produce_end_reason"] == "rate_cutoff"
    assert s["failures_expected"] == 0 and s["max_floating_index"] <= 0.6


def test_rate_cutoff_rule_is_rev11_behaviour_and_float_only_ignores_the_cutoff(params):
    rc = _s(params, produce_end_rule="rate_cutoff")
    ei = _s(params)
    assert rc["produce_end_reason"] == "rate_cutoff"
    assert rc["failures_expected"] > 3 and rc["produce_days"] > ei["produce_days"] + 50
    fo_lo = _s(params, produce_end_rule="float_onset", cutoff_m3d=0.6)
    fo_hi = _s(params, produce_end_rule="float_onset", cutoff_m3d=1.9)
    assert fo_lo["produce_end_reason"] == fo_hi["produce_end_reason"] == "float_onset"
    assert fo_lo["oil_total_m3"] == pytest.approx(fo_hi["oil_total_m3"])


def test_float_rule_is_dt_invariant(params):
    a = cycle.summary(_run(params, dt_days=1.0), params)
    b = cycle.summary(_run(params, dt_days=0.25), params)
    assert b["produce_end_reason"] == "float_onset"
    assert b["SOR_t_per_m3"] == pytest.approx(a["SOR_t_per_m3"], rel=0.01)
    assert b["failures_expected"] == 3


def test_cutoff_prefix_holds_under_the_either_rule(params):
    """The optimiser's one-run-per-cutoff-sweep trick: the float-onset end does
    not depend on the cutoff, so every higher-cutoff cycle is still a prefix
    of the lowest-cutoff run, and the truncated frame reports why it ended."""
    from ml import recommend_physics as rp
    kw = dict(REC)
    full = cycle.simulate_css_cycle(params=params, **kw)
    decks = rp.price_decks(params)
    cuts = [0.6, 1.2, 1.5, 1.6, 1.9]
    tab = rp._cutoff_table(full, cuts, {d: decks[d]["economics"] for d in decks})
    for j, c in enumerate(cuts):
        direct = cycle.simulate_css_cycle(params=params, **dict(kw, cutoff_m3d=c))
        trunc = rp._truncate_at_cutoff(full, c)
        assert len(trunc) == len(direct)
        assert trunc.attrs["produce_end_reason"] == direct.attrs["produce_end_reason"]
        s = cycle.summary(direct, params)
        assert tab["alarm_days"][j] == s["failures_expected"]
        assert tab["end_days_after_peak"][j] == pytest.approx(s["produce_end_days_after_peak"])
        for d in decks:
            assert tab[d][j] == pytest.approx(cycle.summary(direct, decks[d])["margin_incremental_inr_per_cycle_day"],
                                              rel=1e-9, abs=1e-6)


def test_spm_acts_through_float_onset_timing(params):
    """rev 12 FINDING: under the "either" rule slower rods (lower S x N) delay
    the float onset -- the slower liquid rate also drains the condensate tank
    more slowly, so the stream crosses the inversion later -- and the cycle
    runs longer on the same steam: oil and incremental margin rise as SPM falls."""
    s = {spm: cycle.summary(cycle.simulate_css_cycle(params=params, **dict(REC, spm=spm)), params)
         for spm in (3, 4, 5)}
    assert s[3]["produce_days"] > s[4]["produce_days"] > s[5]["produce_days"]
    assert s[3]["oil_total_m3"] > s[5]["oil_total_m3"] * 1.1
    assert (s[3]["margin_incremental_inr_per_cycle_day"] > s[4]["margin_incremental_inr_per_cycle_day"]
            > s[5]["margin_incremental_inr_per_cycle_day"])


def test_robust_rule_vs_fragile_fixed_cutoff(params):
    """The TIER1 10.9 fragility, in one pessimistic draw (P_current 7.4 MPa,
    mu_ref 15,000 cP, skin 2): the peak (~1.03 m3/d) never clears a 1.55
    cutoff, so the fixed-cutoff point ends the day after its peak; the rec
    (float-onset rule, 0.6 backstop) still produces ~200 days past its peak."""
    q = copy.deepcopy(params)
    q["reservoir"]["P_current_kPa"] = 7400.0
    q["fluid"]["mu_ref_cP"] = 15000.0
    q["ipr"]["s_cold"] = 2.0
    rec = cycle.summary(cycle.simulate_css_cycle(params=q, **REC), q)
    fix = cycle.summary(cycle.simulate_css_cycle(params=q, **dict(REC, cutoff_m3d=1.55)), q)
    assert fix["produce_end_days_after_peak"] <= 5 and fix["produce_end_reason"] == "rate_cutoff"
    assert rec["produce_end_days_after_peak"] > 100
    assert rec["margin_incremental_inr_per_cycle_day"] > fix["margin_incremental_inr_per_cycle_day"] + 1e5


# ------------------------------------------------------------ AOF / bands ----
def test_aof_retuned_to_the_peak_band_and_uplift_is_aof_invariant(params):
    assert ipr.AOF_REF_M3D == pytest.approx(0.56)
    assert ipr.aof_ref_m3d(params) == pytest.approx(0.56)
    s = _s(params)
    assert s["peak_oil_bbl_d"] >= 15.0
    lo = copy.deepcopy(params)
    lo["ipr"]["aof_ref_m3d"] = 0.46
    s_lo = _s(lo)
    up = s["peak_oil_m3d"] / s["cold_rate_m3d"]
    assert up == pytest.approx(s_lo["peak_oil_m3d"] / s_lo["cold_rate_m3d"], rel=1e-3)
    assert 5.0 <= up <= 6.0
    assert s_lo["peak_oil_bbl_d"] < 15.0                          # 0.46 was the rev-11 failure


# ------------------------------------------------------------ optimiser ----
def test_5d_optimiser_prefers_slow_rods_under_the_rule(params):
    """Small grid around the rev-12 canonical point: the minimax point is the
    slowest rods, smallest slug, 85 kgf/cm2; cutoffs below the float-onset
    rate give the identical cycle (the cutoff is a backstop)."""
    from ml import recommend_physics as rp
    params = cycle.legacy_rev12_params(params)   # rev 13: the rev-12 statement (no injection gate)
    grid = {"steam_t": [1000.0, 1500.0], "p_wellhead_kgf_cm2": [85.0, 97.0],
            "cutoff_m3d": [0.6, 1.2, 1.6], "stroke_in": [64.0, 86.0], "spm": [3.0, 5.0]}
    res = rp.best_settings_physics_5d(params, grid=grid, return_table=True)
    assert res["produce_end_rule"] == "either"
    mm = res["levels"]["aggressive"]["minimax_regret"]["settings"]
    assert (mm["steam_t"], mm["p_wellhead_kgf_cm2"], mm["stroke_in"], mm["spm"]) == (1000.0, 85.0, 64.0, 3.0)
    assert mm["cutoff_m3d"] in (0.6, 1.2)
    A = res["table"]
    cols = res["table_columns"]
    sel = ((A[:, cols.index("steam_t")] == 1000) & (A[:, cols.index("p_wellhead_kgf_cm2")] == 85)
           & (A[:, cols.index("stroke_in")] == 64) & (A[:, cols.index("spm")] == 3))
    v = A[sel][:, cols.index("fy25_realisation")]
    assert v[0] == pytest.approx(v[1])                             # 0.6 == 1.2: float onset ends both
    con = res["levels"]["conservative"]
    assert con["fi_alarm_line"] == 0.5
    assert con["objective_given_up_vs_aggressive"]["fy25_realisation"] > 0


def test_gain_over_baseline_b_is_now_spm_and_stroke(params):
    """rev 12: under the "either" rule baseline (b) ends on float onset at
    produce day 139 whatever its cutoff, so the cutoff lever contributes 0 and
    the gain is slow rods (SPM + stroke > 80 %)."""
    from ml import decompose
    dp = decompose.decks(params)
    rec = {"steam_t": 1000.0, "soak_days": 10.0, "cutoff_m3d": 0.6, "spm": 3.0, "stroke_in": 64.0,
           "p_wellhead_kgf_cm2": 85.0}
    res = decompose.decompose(decompose.BASELINE_B, rec, dp)
    for deck in dp:
        e = res[deck]
        assert sum(e["shapley"].values()) == pytest.approx(e["total_gain"], rel=1e-9)
        assert e["shapley"]["cutoff_m3d"] == pytest.approx(0.0, abs=1.0)
        assert e["shapley"]["spm"] + e["shapley"]["stroke_in"] > 0.8 * e["total_gain"]
    sens = decompose.baseline_cutoff_sensitivity(rec, dp)["rows"]
    vals = [r["fy25_realisation"]["baseline_value"] for r in sens]
    assert max(vals) - min(vals) < 1.0


# --------------------------------------------------------------- ML data ----
def test_lhs_covers_pressure_and_stroke(params):
    from twin import generate_data
    df = generate_data._sample_inputs(params, 120, 42)
    assert list(df.columns) == ["steam_t", "soak_days", "cutoff_m3d", "spm", "p_wellhead_kgf_cm2", "stroke_in",
                                "float_policy"]                    # rev 13: + float policy
    assert 85.0 <= df["p_wellhead_kgf_cm2"].min() < 86.0 and 96.0 < df["p_wellhead_kgf_cm2"].max() <= 97.0
    assert sorted(df["stroke_in"].unique()) == [64.0, 74.0, 86.0, 100.0, 120.0, 144.0]
    counts = df["stroke_in"].value_counts()
    assert counts.min() == counts.max() == 20                      # LHS strata carry over
    assert df["spm"].min() < 3.2 and df["spm"].max() > 11.8


def test_uq_appends_phi_star_and_reports_fragility(params):
    from ml import uq
    spec = uq.build_uncertain_inputs(params)
    names = list(spec)
    assert names[names.index("condensate_recovery_frac") + 1] == "emulsion_phi_star"   # rev 13: more appended
    assert (spec["emulsion_phi_star"]["low"], spec["emulsion_phi_star"]["high"]) == (0.65, 1.0)
    assert uq.POINTS["recommended"]["cutoff_m3d"] == 0.60 and uq.POINTS["conservative"]["fi_alarm"] == 0.5
    params = cycle.legacy_rev12_params(params)   # rev 13: the rev-12 conservative operation (pull at 0.5)
    out = uq._run_point(params, dict(uq.POINTS["recommended_rev12"], fi_alarm=0.5))
    assert out["ended_by_float_onset"] == 1.0 and out["failures_expected"] == 0
    assert np.isfinite(out["produce_end_days_after_peak"])
