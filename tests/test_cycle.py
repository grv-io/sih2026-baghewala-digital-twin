"""Unit tests for twin/cycle.py.

Reference cycle (rev 5 calibration, 26 Sep 2026): 1,500 t / 7 d soak /
cutoff 1.2 m3/d / 5 spm. The v1-era cutoff literal 3.0 m3/d sat ABOVE the honest
v2 peak rate (~2.5 m3/d) and ended every cycle on produce day 1, which is why
three of these tests were red or passing vacuously before rev 5.
"""
import numpy as np

from twin import cycle

REF = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5)


def _run(params, **kw):
    args = dict(REF, **kw)
    return cycle.simulate_css_cycle(params=params, **args)


def test_full_cycle_smoke(params):
    df = _run(params)

    # The 10 docs/SPEC.md columns are a fixed PREFIX; Tier-1/rev-5 columns are
    # appended after them, never inserted.
    assert list(df.columns)[:10] == cycle.SPEC_COLUMNS
    assert len(df) > 0

    phases_in_order = list(dict.fromkeys(df["phase"]))
    assert phases_in_order == ["inject", "soak", "produce"]

    s = cycle.summary(df, params)
    assert s["oil_total_m3"] > 0
    assert 3.0 < s["SOR_t_per_m3"] < 8.0      # literature CSS band
    assert s["days_total"] > 0


def test_cycle_ends_at_or_below_cutoff(params):
    """The cycle must actually PRODUCE for a while and then end on a genuine
    cutoff crossing (not on day 1, which is how this test passed vacuously
    under the rev-4 literals).
    rev 12: the RATE-CUTOFF branch of the produce-end rule; the float-onset
    branch is tested in test_physics_wave4.py."""
    cutoff = REF["cutoff_m3d"]
    df = _run(params, produce_end_rule="rate_cutoff")
    assert df.attrs["produce_end_reason"] == "rate_cutoff"
    produce = df[df["phase"] == "produce"]
    assert len(produce) >= 30
    assert produce["oil_m3d"].iloc[-1] < cutoff
    assert produce["oil_m3d"].iloc[-2] >= cutoff
    assert len(produce) < cycle.MAX_PRODUCE_DAYS


def _decline_after_pump_limit(df):
    produce = df[df["phase"] == "produce"].reset_index(drop=True)
    limited = produce["pump_limited"].to_numpy(dtype=bool)
    # first day on which the reservoir, not the pump, sets the rate
    first_free = int(np.argmin(limited)) if limited.any() else 0
    return produce["oil_m3d"].to_numpy()[first_free:], first_free, len(produce)


def test_oil_rate_declines_monotonically_during_produce_after_pump_limit(params):
    """Once the well is no longer pump-capacity-limited, oil rate must fall
    day over day as the heated zone cools and the pressure recharge bleeds."""
    rates, _, n = _decline_after_pump_limit(_run(params))
    assert n >= 30 and len(rates) >= 30
    assert np.all(np.diff(rates) <= 1e-9)


def test_pump_limited_plateau_then_decline_at_low_spm(legacy_params):
    """At 3 spm the pump, not the reservoir, sets the early rate (a flat
    plateau), after which the reservoir-limited decline takes over.
    rev 11: a FLAT plateau needs a constant water cut, so this runs the rev-10
    switches (conftest.legacy_rev10); with the water-cut state the pump-limited
    oil rate RISES as the condensate is recovered (tests/test_physics_wave3.py)."""
    params = legacy_params
    df = _run(params, spm=3)
    rates, first_free, _ = _decline_after_pump_limit(df)
    assert first_free >= 30
    produce = df[df["phase"] == "produce"]
    plateau = produce["oil_m3d"].to_numpy()[:first_free]
    assert np.ptp(plateau) < 0.05 * plateau.max()
    assert np.all(np.diff(rates) <= 1e-9)


def test_margin_has_interior_optimum_over_steam_volume(params):
    """Replaces test_SOR_has_interior_optimum_over_steam_volume (T1-A made SOR
    honestly monotone in steam). The optimum lives in Rs margin per cycle-day,
    which carries the inject+soak days when the well earns nothing.

    rev 9: the FY25 oil-price deck (Rs5,992/bbl, up from Rs4,840/bbl) shifts
    the hump outward -- 3,000 t now beats 1,000 t on GROSS margin (higher
    revenue per barrel makes the extra steam pay), so the comparison uses the
    grid's middle point (1,500 t) against both edges instead of 1,000 vs
    3,000. The interior optimum itself (now ~2,000 t) is unaffected."""
    # rev 13: at the bulk-discount preset (0.30) this statement was written for;
    # at the 0.15 base the gross optimum is ~750 t (test_benchmarks finding)
    params = copy.deepcopy(params)
    params["economics"]["diesel_bulk_discount_frac"] = 0.30
    grid = (500, 1000, 1500, 2000, 3000)
    m = {}
    for steam_t in grid:
        df = _run(params, steam_t=steam_t)
        m[steam_t] = cycle.summary(df, params)["margin_inr_per_cycle_day"]
    assert m[1500] > m[500]
    assert m[1500] > m[3000]
    best = max(m, key=m.get)
    assert best not in (grid[0], grid[-1])


def test_SOR_rises_monotonically_with_steam_volume(params):
    """Composite-radial physics: each extra tonne buys a smaller increment of
    heated radius, so SOR increases with slug size (PHYSICS plan F2)."""
    sors = [cycle.summary(_run(params, steam_t=s), params)["SOR_t_per_m3"]
            for s in (500, 1000, 1500, 2000, 3000)]
    assert all(a < b for a, b in zip(sors, sors[1:]))


def test_summary_keys(params):
    s = cycle.summary(_run(params), params)
    for key in (
        "oil_total_m3", "SOR_t_per_m3", "energy_per_m3_kWh",
        "days_total", "max_floating_index", "failures_expected",
        "rod_float_damage_index", "mean_fillage", "pump_limited_days",
        "peak_oil_bbl_d", "margin_inr", "margin_inr_per_cycle_day",
        "co2_kg_per_bbl", "bl_uncertainty_frac",
    ):
        assert key in s


def test_summary_without_params_matches_json_economics(params):
    """summary(df) (api/ and ml/ call it without params) must use the same
    economics as summary(df, params)."""
    df = _run(params)
    a = cycle.summary(df)
    b = cycle.summary(df, params)
    assert a["margin_inr"] == b["margin_inr"]
    assert a["steam_cost_inr"] == b["steam_cost_inr"]


def test_delta_is_computed_from_simulated_production(params):
    """Physics v3: Boberg-Lantz delta is accumulated from the simulated oil +
    water stream (PEH Eq. 15.74), so a wetter produced stream removes more heat
    and ends the cycle with less oil; the produced heat at the reference cycle
    is a plausible fraction (20-50 %) of the heat delivered to the sand face."""
    import copy
    from twin import thermal
    # rev 13: a statement about Boberg-Lantz heat removal, so run to the rate
    # cutoff (under the float rule the wetter stream sits nearer the smoothed
    # inversion band, floats LATER and runs longer -- a float effect, not heat)
    ref = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5, produce_end_rule="rate_cutoff")
    df = cycle.simulate_css_cycle(params=params, **ref)
    pr = df[df["phase"] == "produce"]
    # rev 11: the produced water is the day's simulated stream (condensate +
    # formation water), carried in the frame.
    q_p = sum(thermal.produced_heat_J_per_day(q, w, T, params)
              for q, w, T in zip(pr["oil_m3d"], pr["water_m3d"], pr["T_res_C"]))
    q_inj = 1500e3 * thermal.sandface_enthalpy_J_per_kg(params)
    assert 0.20 <= q_p / q_inj <= 0.50

    wet = copy.deepcopy(params)
    wet["fluid"]["formation_water_cut"] = 0.60
    oil_ref = df["oil_m3d"].sum()
    oil_wet = cycle.simulate_css_cycle(params=wet, **ref)["oil_m3d"].sum()
    assert oil_wet < oil_ref
    # the rev <= 10 constant-cut model keeps the same behaviour
    legacy = copy.deepcopy(params)
    legacy["fluid"]["water_cut_model"] = "constant"
    wet_l = copy.deepcopy(legacy)
    wet_l["fluid"]["water_cut"] = 0.90
    assert (cycle.simulate_css_cycle(params=wet_l, **ref)["oil_m3d"].sum()
            < cycle.simulate_css_cycle(params=legacy, **ref)["oil_m3d"].sum())


# ---------------------------------------------------------------------------
# Economics v2 (27 Sep 2026): incremental oil over the cold baseline, opex
# ---------------------------------------------------------------------------
import copy  # noqa: E402

import pytest  # noqa: E402

from twin import ipr, viscosity  # noqa: E402

V2_KEYS = (
    "window_days", "electric_kWh", "electric_kWh_per_m3", "power_cost_inr", "opex_fixed_inr",
    "opex_inr", "margin_with_opex_inr", "margin_with_opex_inr_per_cycle_day",
    "cold_rate_m3d", "cold_well_economic", "oil_cold_baseline_m3", "oil_incremental_m3",
    "oil_incremental_bbl", "SOR_incremental", "margin_incremental_inr",
    "margin_incremental_inr_per_cycle_day", "margin_incremental_inr_per_t_steam",
    "cadp_resteam_day", "cadp_resteam_rate_m3d", "cadp_margin_incremental_inr_per_cycle_day",
)
POINTS = (
    dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5),    # reference
    dict(steam_t=1300, soak_days=10, cutoff_m3d=1.3, spm=5),   # baseline (b)
    dict(steam_t=1700, soak_days=10, cutoff_m3d=0.85, spm=5),  # rev-5 recommendation
)


def test_v2_keys_present_and_gross_keys_unchanged(params):
    df = _run(params)
    s = cycle.summary(df, params)
    for key in V2_KEYS:
        assert key in s
    # gross keys keep the rev-5 definition: revenue - steam - rig, no opex
    assert s["margin_inr"] == pytest.approx(
        s["revenue_inr"] - s["steam_cost_inr"] - params["economics"]["fixed_cost_inr_per_cycle"])
    assert s["margin_inr_per_cycle_day"] == pytest.approx(s["margin_inr"] / s["days_total"])
    n_w = len(cycle.WATER_COLUMNS)
    assert list(df.columns)[-3 - n_w:-n_w] == cycle.ECON_COLUMNS
    assert list(df.columns)[-n_w:] == cycle.WATER_COLUMNS   # rev 11, appended last


def _producing_cold(params):
    """rev 13: the incremental-vs-gross identities need a counterfactual that
    produces; under the shipped css.cold_counterfactual "policy" the cold well
    is shut in (FI 1.0 at the 2-spm floor) and incremental == net cash."""
    q = copy.deepcopy(params)
    q["css"]["cold_counterfactual"] = "pumpable"
    return q


@pytest.mark.parametrize("pt", POINTS)
def test_incremental_is_harsher_than_gross(params, pt):
    shut = cycle.summary(cycle.simulate_css_cycle(params=params, **pt), params)
    assert shut["SOR_incremental"] == pytest.approx(shut["SOR_t_per_m3"])
    assert shut["margin_incremental_inr"] == pytest.approx(shut["margin_with_opex_inr"])
    params = _producing_cold(params)
    s = cycle.summary(cycle.simulate_css_cycle(params=params, **pt), params)
    assert s["SOR_incremental"] > s["SOR_t_per_m3"]
    assert s["margin_incremental_inr"] < s["margin_with_opex_inr"] < s["margin_inr"]
    assert s["margin_incremental_inr_per_cycle_day"] < s["margin_inr_per_cycle_day"]
    assert 0.0 < s["oil_incremental_m3"] < s["oil_total_m3"]


def test_cold_baseline_is_cold_rate_times_window(params):
    """Convention: the cold well produces for the WHOLE calendar window,
    inject + soak days included; window = days_total + one daily step.
    rev 13: with a producing ("pumpable") counterfactual."""
    params = _producing_cold(params)
    s = cycle.summary(_run(params), params)
    # rev 11: at the pre-cycle pressure the IPR sees (reservoir.P_current_kPa,
    # 9.4 MPa [ASSUMPTION]); 0.447 m3/d at the virgin 11.4 MPa (rev 10).
    q_cold = ipr.oil_rate_m3d(cycle.reservoir_pressure_kPa(params),
                              cycle._pump_intake_pressure_kPa(params),
                              viscosity.mu_cP(params["reservoir"]["T_initial_C"], params), params)
    assert s["cold_rate_m3d"] == pytest.approx(q_cold)
    assert 0.30 <= q_cold <= 0.50                        # 2.3 bbl/d at 9.4 MPa (ipr.AOF_REF_M3D)
    assert s["window_days"] == pytest.approx(s["days_total"] + 1.0)
    assert s["cold_counterfactual_rate_m3d"] == pytest.approx(q_cold)
    assert s["oil_cold_baseline_m3"] == pytest.approx(q_cold * s["window_days"])
    assert s["oil_incremental_m3"] == pytest.approx(s["oil_total_m3"] - s["oil_cold_baseline_m3"])


def test_incremental_margin_identity(params):
    """margin_incremental = with-opex margin - cold well's net cash (it is
    economic at the base deck), so the fixed daily opex cancels exactly.
    rev 13: with a producing ("pumpable") counterfactual."""
    params = _producing_cold(params)
    df = _run(params)
    s = cycle.summary(df, params)
    e = params["economics"]
    assert s["cold_well_economic"] is True
    price_m3 = e["oil_price_inr_per_bbl"] * e["bbl_per_m3"]
    cold_cash_d = (s["cold_rate_m3d"] * price_m3
                   - df["electric_cold_kWh"].iloc[0] * e["electricity_inr_per_kWh"]
                   - e["opex_inr_per_day"])
    assert s["margin_incremental_inr"] == pytest.approx(
        s["margin_with_opex_inr"] - cold_cash_d * s["window_days"])
    q = copy.deepcopy(params)
    q["economics"]["opex_inr_per_day"] = 2.0 * e["opex_inr_per_day"]
    s2 = cycle.summary(df, q)
    assert s2["margin_incremental_inr"] == pytest.approx(s["margin_incremental_inr"])
    assert s2["margin_with_opex_inr"] < s["margin_with_opex_inr"]


def test_uneconomic_cold_well_is_shut_in_in_the_counterfactual(params):
    """If the cold well cannot pay its own opex the operator would shut it in:
    the baseline cash is 0 and incremental margin = with-opex margin."""
    q = copy.deepcopy(params)
    q["economics"]["opex_inr_per_day"] = 20000.0
    s = cycle.summary(_run(q), q)
    assert s["cold_well_economic"] is False
    assert s["margin_incremental_inr"] == pytest.approx(s["margin_with_opex_inr"])


def test_cadp_resteam_point(params):
    """The CADP day's cumulative-average incremental margin is the maximum
    over the cycle, so it is >= the whole-cycle incremental margin per day.
    At the base deck it never triggers before the well is back near its cold
    rate; on a deck where CSS pays, an interior economic re-steam point
    appears above the cold rate.
    rev 12: a statement about the rate-driven cycle (produce_end_rule
    "rate_cutoff"); under "either" the float-onset rule ends the cycle first,
    so CADP sits on its last day."""
    params = copy.deepcopy(params)
    params["css"]["produce_end_rule"] = "rate_cutoff"
    s = cycle.summary(_run(params, cutoff_m3d=0.46, spm=4.0), params)
    assert s["cadp_margin_incremental_inr_per_cycle_day"] >= s["margin_incremental_inr_per_cycle_day"] - 1e-6
    assert s["cadp_resteam_day"] <= s["days_total"] + 1e-9
    q = copy.deepcopy(params)
    q["economics"]["oil_price_inr_per_bbl"] = 6000.0
    s2 = cycle.summary(_run(q, cutoff_m3d=0.46, spm=4.0), q)
    assert s2["cadp_resteam_day"] < s2["days_total"]
    # rev 12: AOF 0.46 -> 0.56 scales every rate by ~1.22 (the old bound was 0.8)
    assert s2["cold_rate_m3d"] < s2["cadp_resteam_rate_m3d"] < 0.8 * 0.56 / 0.46


def test_energy_intensity_uses_corrected_polished_rod_energy(params):
    """Rev-8 polished-rod energy: 30-80 kWh/m3 oil at the reference (was ~123
    with the peak-load estimate); electricity = that / surface efficiency.
    rev 10: with the produced-stream (emulsion) drag viscosity the rods see a
    ~1 cP water-continuous stream at 85 % cut, so the drag share of the card
    work disappears and the reference falls to ~29 kWh/m3 (hydraulic lift +
    Gibbs damping + plunger friction). Band lowered to 20-80; the rev-9 drag
    rule (tubing_viscosity_model "oil") still gives the rev-8 42.5.
    rev 11: the band is checked on the constant-cut (rev-10) stream; with the
    water-cut state the late-cycle stream turns oil-continuous and the rods
    drag through a W/O emulsion, so the reference rises to ~97 kWh/m3 -- still
    below the pre-v2 peak-load estimate (~123)."""
    rev10 = copy.deepcopy(params)
    rev10["fluid"]["water_cut_model"] = "constant"
    s = cycle.summary(_run(rev10), rev10)
    assert 20.0 <= s["energy_per_m3_kWh"] <= 80.0
    assert s["electric_kWh_per_m3"] > s["energy_per_m3_kWh"]
    legacy = copy.deepcopy(rev10)
    legacy["fluid"]["tubing_viscosity_model"] = "oil"
    s_old = cycle.summary(_run(legacy), legacy)
    assert 30.0 <= s_old["energy_per_m3_kWh"] <= 80.0
    assert s_old["energy_per_m3_kWh"] > s["energy_per_m3_kWh"]
    s_state = cycle.summary(_run(params), params)
    assert s["energy_per_m3_kWh"] < s_state["energy_per_m3_kWh"] < 123.0


# ---------------------------------------------------------------------------
# rev 10 (external review): totals are sum(rate) x dt
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pt", [REF, dict(steam_t=1600, soak_days=10, cutoff_m3d=0.70, spm=4)])
def test_summary_is_invariant_to_timestep(params, pt):
    """SOR, cycle oil, days and energy intensity agree within 1 % at dt = 1,
    0.5 and 0.25 d. Before rev 10 summary() summed daily RATES without x dt,
    so SOR halved at dt = 0.5 and quartered at dt = 0.25 (a latent bug: every
    shipped number was computed at dt = 1, where it is harmless)."""
    ref = cycle.summary(cycle.simulate_css_cycle(params=params, **pt), params)
    for dt in (0.5, 0.25):
        df = cycle.simulate_css_cycle(params=params, dt_days=dt, **pt)
        s = cycle.summary(df, params)
        for key in ("SOR_t_per_m3", "oil_total_m3", "days_total", "energy_per_m3_kWh",
                    "SOR_incremental", "electric_kWh_per_m3"):
            assert s[key] == pytest.approx(ref[key], rel=0.01), (dt, key)
        # the frame carries its own timestep; a copy without attrs still infers it
        assert df.attrs["dt_days"] == dt
        bare = df.copy()
        bare.attrs = {}
        assert cycle.summary(bare, params)["oil_total_m3"] == pytest.approx(s["oil_total_m3"])
