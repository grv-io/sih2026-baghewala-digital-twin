"""Validation of the computed dynamometer cards (twin/dyno.py).

(a) static limit: near-parallelogram, PPRL ~ W_rf + Fo, MPRL ~ W_rf
(b) peak PRL rises with SPM (inertia / stress waves), bracketed by Mills
(c) fillage 0.6 -> fluid-pound step on the downstroke; gas -> cushioned release
(d) 10,000 cP at 12 SPM -> rod float, consistent with srp.floating_index
(e) energy: card area = pump work + damping dissipation; hydraulic/PR power
(f) Gibbs FD stability: Courant number <= 1, bounded at extreme inputs

rev 10: these are tests of the SOLVER against a stated drag viscosity, so the
module-level `params` fixture below switches the tubing-viscosity model to
"oil" (the rev-9 rule: the rods see the viscosity passed in). The default
produced-stream (emulsion) model -- water-continuous at 85 % cut, so no float
-- is tested explicitly at the end with the shipped params.
"""
import time

import numpy as np
import pytest

from twin import cycle, dyno, srp

STROKE = 2.18


@pytest.fixture
def params(params):
    """Shipped params with the rev-9 drag rule (tubing fluid = oil viscosity).
    rev 11: on the rev-10 switches (constant water cut, legacy steam, virgin
    pressure, 2.18-m stroke) -- these are solver-mechanics tests on that stream."""
    from twin import cycle as _cycle
    p = _cycle.legacy_rev10_params(params)
    p["fluid"]["tubing_viscosity_model"] = "oil"
    return p


@pytest.fixture
def shipped_params():
    import json
    from pathlib import Path
    from twin import cycle as _cycle
    # rev 11: the rev-10 switches (constant 85 % cut) -- the finding below is about that stream;
    # the water-cut-state float finding is in tests/test_physics_wave3.py.
    with open(Path(__file__).resolve().parents[1] / "params" / "field_params.json") as f:
        return _cycle.legacy_rev10_params(json.load(f))


def _wc(params):
    return params["fluid"]["water_cut"]


def _card(params, spm=5.0, mu=5.0, fill=1.0, **kw):
    return dyno.compute_cards(spm, params["srp"]["stroke_m"], mu, fill, _wc(params), params, **kw)


def _mu_for_ratio(ratio, spm, params):
    """Viscosity (cP) giving srp's v_stroke/v_fall = ratio at this SPM."""
    w_b = srp._buoyant_rod_weight_N(params)
    v_avg = 2.0 * params["srp"]["stroke_m"] * spm / 60.0
    return ratio * w_b / (srp.k_visc(params) * params["srp"]["rod_length_m"] * v_avg) * 1e3


def _branch_mean(x, f, upstroke, lo=0.25, hi=0.75):
    (xu, fu), (xd, fd) = dyno._branches(np.asarray(x), np.asarray(f))
    xs, fs = (xu, fu) if upstroke else (xd, fd)
    q = np.min(x) + (np.max(x) - np.min(x)) * np.linspace(lo, hi, 21)
    return float(np.mean(np.interp(q, xs, fs)))


# --------------------------------------------------------------------------
# rod string / static references
# --------------------------------------------------------------------------
def test_rod_taper_carries_srp_rod_weight(params):
    """The 1" x 7/8" taper is split so both models carry the same rod weight."""
    s = params["srp"]
    mean_mass = sum(f * m for f, m in zip(s["rod_taper_frac"], s["rod_taper_mass_kgm"]))
    assert mean_mass == pytest.approx(s["rod_mass_kgm"], rel=0.005)
    st = dyno.static_loads(_wc(params), params)
    # dyno buoys the rods in the tubing MIXTURE (85 % water), srp in oil.
    assert st["W_rf_N"] == pytest.approx(srp._buoyant_rod_weight_N(params), rel=0.01)
    rs = dyno.rod_string(params)
    for t in rs["tapers"]:
        assert 4800.0 < t["wave_speed_ms"] < 5100.0  # coupled steel rods ~16,000 ft/s


def test_fluid_load_matches_net_lift(params):
    """Fo = (P_discharge - P_intake) * A_p, within a few % of srp's rho*g*L*A_p."""
    st = dyno.static_loads(_wc(params), params)
    a_p = np.pi / 4 * params["srp"]["plunger_d_m"] ** 2
    srp_fo = srp._fluid_density_kgm3(params["fluid"]["api_gravity"]) * srp.G * params["srp"]["rod_length_m"] * a_p
    assert st["Fo_N"] == pytest.approx(srp_fo, rel=0.08)
    assert st["P_intake_Pa"] == pytest.approx(cycle._pump_intake_pressure_kPa(params) * 1e3)


# --------------------------------------------------------------------------
# (a) static limit
# --------------------------------------------------------------------------
def test_a_static_limit_is_near_parallelogram(params):
    c = _card(params, spm=2.0, mu=5.0, fill=1.0)
    w_rf, fo = c["buoyant_rod_weight_kN"], c["fluid_load_kN"]
    # extremes within RP 11L's own +/-10 %
    assert c["peak_prl_kN"] == pytest.approx(w_rf + fo, rel=0.10)
    assert c["min_prl_kN"] == pytest.approx(w_rf, rel=0.10)
    # the load LINES of the parallelogram sit on W_rf + Fo and W_rf
    fr = params["srp"]["plunger_friction_kN"]
    up = _branch_mean(c["position_m"], c["load_surface_kN"], True)
    dn = _branch_mean(c["position_m"], c["load_surface_kN"], False)
    assert up == pytest.approx(w_rf + fo + fr, rel=0.03)
    assert dn == pytest.approx(w_rf - fr, rel=0.05)
    # pump card is the textbook rectangle; plunger stroke = S - Fo rod stretch
    assert c["card_type"] == "full_pump"
    assert c["features"]["card_fillage"] > 0.97
    assert c["plunger_stroke_m"] == pytest.approx(STROKE - c["static_rod_stretch_m"], rel=0.03)
    assert max(c["load_downhole_kN"]) == pytest.approx(fo + fr, rel=0.02)


# --------------------------------------------------------------------------
# (b) inertia
# --------------------------------------------------------------------------
def test_b_peak_prl_rises_with_spm(params):
    cards = [_card(params, spm=s, mu=5.0) for s in (3.0, 6.0, 9.0, 12.0)]
    peaks = [c["peak_prl_kN"] for c in cards]
    mins = [c["min_prl_kN"] for c in cards]
    assert all(b > a for a, b in zip(peaks, peaks[1:]))
    assert all(b < a for a, b in zip(mins, mins[1:]))
    for c in cards:
        # Mills' rigid-rod acceleration factor is a lower bound; the elastic
        # string's stress waves add to it, but not wildly at N/No < 0.2.
        assert 1.0 <= c["peak_prl_kN"] / c["mills_peak_prl_kN"] <= 1.35
        assert c["dynamic_factor"] >= 1.0


# --------------------------------------------------------------------------
# (c) fluid pound vs gas interference
# --------------------------------------------------------------------------
def test_c_fluid_pound_step_on_downstroke(params):
    c = _card(params, spm=5.0, mu=5.0, fill=0.6)
    fo = c["fluid_load_kN"]
    assert c["card_type"] == "fluid_pound"
    assert c["features"]["card_fillage"] == pytest.approx(0.6, abs=0.03)
    assert c["features"]["release_travel_frac"] < 0.03  # sharp, liquid slam
    # pump card: full fluid load held for the first 40 % of the downstroke
    x = np.asarray(c["plunger_position_m"])
    f = np.asarray(c["load_downhole_kN"])
    (_, _), (xd, fd) = dyno._branches(x, f)
    s_p = x.max()
    assert np.interp(0.75 * s_p, xd, fd) > 0.85 * fo
    assert np.interp(0.45 * s_p, xd, fd) < 0.15 * fo
    # surface card carries the same step: high early downstroke, low late
    hi = _branch_mean(c["position_m"], c["load_surface_kN"], False, 0.70, 0.90)
    lo = _branch_mean(c["position_m"], c["load_surface_kN"], False, 0.15, 0.40)
    assert hi - lo > 0.6 * fo


def test_c_gas_interference_is_cushioned_not_sharp(params):
    c = _card(params, spm=5.0, mu=5.0, fill=0.6, gas_interference=True)
    assert c["card_type"] == "gas_interference"
    assert c["features"]["release_travel_frac"] > 0.10


# --------------------------------------------------------------------------
# (d) rod float
# --------------------------------------------------------------------------
def test_d_rod_float_signature_at_10000cP_12spm(params):
    c = _card(params, spm=12.0, mu=10000.0)
    st = srp.pump_state(12.0, STROKE, 10000.0, 1.0, params)
    assert st["floating_index"] == 1.0
    assert c["carrier_separation"]
    assert c["card_type"] == "rod_float"
    assert c["min_prl_kN"] <= 0.05 * c["buoyant_rod_weight_kN"]
    # the rods cannot follow the horsehead down: plunger travel is lost
    assert c["plunger_stroke_m"] < 0.7 * STROKE


def test_d_float_onset_brackets_spec_threshold(params):
    """Separation begins near srp v_stroke/v_fall ~ 0.6 (SPEC's alarm line;
    2/pi = 0.64 for harmonic motion), at both 5 and 12 SPM."""
    for spm in (5.0, 12.0):
        below = _card(params, spm=spm, mu=_mu_for_ratio(0.40, spm, params))
        above = _card(params, spm=spm, mu=_mu_for_ratio(0.75, spm, params))
        assert not below["carrier_separation"]
        assert below["min_prl_kN"] > 0.1 * below["buoyant_rod_weight_kN"]
        assert above["carrier_separation"]


def test_d_min_prl_falls_monotonically_with_viscosity(params):
    mins = [_card(params, spm=5.0, mu=m)["min_prl_kN"] for m in (100.0, 1000.0, 3000.0, 6000.0)]
    assert all(b < a for a, b in zip(mins, mins[1:]))
    assert mins[0] < dyno.static_loads(_wc(params), params)["W_rf_N"] / 1e3


# --------------------------------------------------------------------------
# (e) energy
# --------------------------------------------------------------------------
@pytest.mark.parametrize("spm,mu,fill", [(5.0, 5.0, 1.0), (5.0, 5.0, 0.6), (5.0, 2000.0, 1.0), (12.0, 5.0, 1.0)])
def test_e_card_area_equals_pump_work_plus_damping(params, spm, mu, fill):
    c = _card(params, spm=spm, mu=mu, fill=fill)
    assert abs(c["energy_balance_err"]) < 0.01
    assert c["polished_rod_kW"] == pytest.approx(c["card_area_kJ"] * spm / 60.0)


def test_e_hydraulic_vs_polished_rod_power(params):
    c = _card(params, spm=5.0, mu=5.0, fill=1.0)
    fr = params["srp"]["plunger_friction_kN"]
    # pump card of a full pump = (Fo + 2*friction) * plunger stroke
    assert c["pump_work_kJ"] == pytest.approx((c["fluid_load_kN"] + 2 * fr) * c["plunger_stroke_m"], rel=0.02)
    eff = c["hydraulic_kW"] / c["polished_rod_kW"]
    assert 0.70 < eff < 0.95  # thin oil: only Gibbs damping + plunger friction lost
    hot = eff
    cold = _card(params, spm=5.0, mu=3000.0, fill=1.0)
    assert cold["hydraulic_kW"] / cold["polished_rod_kW"] < hot  # drag costs power


# --------------------------------------------------------------------------
# (f) numerics
# --------------------------------------------------------------------------
@pytest.mark.parametrize("spm,mu,depth", [(2.0, 1.0, None), (12.0, 1.0, None), (12.0, 50000.0, None),
                                          (8.0, 500.0, 2000.0), (4.0, 11500.0, 600.0)])
def test_f_cfl_and_bounded(params, spm, mu, depth):
    c = dyno.compute_cards(spm, STROKE, mu, 1.0, _wc(params), params, depth_m=depth)
    assert 0.0 < c["cfl"] <= 1.0
    for key in ("load_surface_kN", "load_downhole_kN", "position_m", "plunger_position_m"):
        assert np.all(np.isfinite(c[key]))
    assert 0.0 <= c["min_prl_kN"] <= c["peak_prl_kN"] < 500.0
    assert min(c["position_m"]) >= -1e-9 and max(c["position_m"]) <= STROKE + 1e-9


def test_f_grid_convergence(params, monkeypatch):
    base = _card(params, spm=5.0, mu=5.0)
    monkeypatch.setattr(dyno, "N_SEGMENTS", 40)
    fine = _card(params, spm=5.0, mu=5.0)
    assert base["peak_prl_kN"] == pytest.approx(fine["peak_prl_kN"], abs=0.6)
    assert base["min_prl_kN"] == pytest.approx(fine["min_prl_kN"], abs=0.6)


# --------------------------------------------------------------------------
# API, comparison with srp.py, cycle integration, bake
# --------------------------------------------------------------------------
def test_api_shape_and_runtime(params):
    t0 = time.perf_counter()
    c = _card(params, spm=5.0, mu=500.0, fill=0.8)
    elapsed = time.perf_counter() - t0
    for key in ("position_m", "load_downhole_kN", "load_surface_kN", "plunger_position_m"):
        assert len(c[key]) == 200
    for key in ("peak_prl_kN", "min_prl_kN", "pump_fillage", "card_type", "fluid_load_kN",
                "buoyant_rod_weight_kN", "dynamic_factor"):
        assert key in c
    assert c["card_type"] in {"full_pump", "fluid_pound", "heavy_oil_viscous", "rod_float", "gas_interference"}
    assert elapsed < 0.25  # ~20-50 ms typical; loose bound for CI noise
    with pytest.raises(ValueError):
        _card(params, spm=0.0)


def test_fd_peak_vs_srp_static_peak(params):
    """srp.py's static peak omits stress waves/inertia: the FD card sits above
    it by a bounded dynamic margin, and both rise together with viscosity."""
    for mu in (5.0, 2000.0):
        c = _card(params, spm=5.0, mu=mu)
        s = srp.pump_state(5.0, STROKE, mu, 1.0, params)["peak_rod_load_kN"]
        assert 1.0 < c["peak_prl_kN"] / s < 1.25


def test_cards_along_cycle_hot_to_cold(params):
    df = cycle.simulate_css_cycle(1300.0, 10.0, 1.3, 5.0, params)
    tab = dyno.cards_along_cycle(df, params, n_days=5)
    assert len(tab) == 5
    assert tab["mu_cP"].iloc[-1] > tab["mu_cP"].iloc[0]
    assert tab["peak_prl_kN"].iloc[-1] > tab["peak_prl_kN"].iloc[0]
    assert tab["min_prl_kN"].iloc[-1] < tab["min_prl_kN"].iloc[0]
    assert tab["card_type"].iloc[0] != "heavy_oil_viscous"
    assert tab["card_type"].iloc[-1] == "heavy_oil_viscous"
    # the SPM schedule keeps v_stroke < v_fall, so no carrier separation
    assert not tab["carrier_separation"].any()
    # fillage follows the reservoir-limited liquid rate
    assert (tab["pump_fillage"] <= 1.0).all() and tab["pump_fillage"].iloc[-1] < tab["pump_fillage"].iloc[0]


def test_default_emulsion_model_cards_show_no_float_at_85pct_cut(shipped_params):
    """rev 10 finding on the dyno side: with the produced-stream viscosity the
    12-spm stress card of the recommendation is NOT a rod-float card at 85 %
    water cut (the rods see ~1 cP water-continuous fluid), and the drag
    viscosity actually used is echoed in the card inputs."""
    p = shipped_params
    c = dyno.compute_cards(12.0, STROKE, 10000.0, 1.0, p["fluid"]["water_cut"], p)
    assert not c["carrier_separation"] and c["card_type"] != "rod_float"
    assert c["inputs"]["mu_cP"] == 10000.0 and c["inputs"]["mu_drag_cP"] < 1.5
    # the same oil in an oil-continuous stream (60 % water) floats
    c_wo = dyno.compute_cards(12.0, STROKE, 10000.0, 1.0, 0.60, p)
    assert c_wo["carrier_separation"]
    data = dyno.bake(p, n_points=40)
    assert data["scenarios"]["recommendation"]["cards"][3]["card_type"] != "rod_float"


def test_bake_structure(params):
    data = dyno.bake(params, n_points=60)
    assert set(data["scenarios"]) == {"baseline", "recommendation"}
    for sc in data["scenarios"].values():
        keys = [c["key"] for c in sc["cards"]]
        assert keys == ["early_hot", "mid", "vfd_hold_day", "stress_12spm"]
        for c in sc["cards"]:
            assert len(c["surface"]["position_m"]) == 60 == len(c["downhole"]["load_kN"])
        assert sc["cards"][0]["card_type"] in {"full_pump", "fluid_pound"}
        assert sc["cards"][3]["spm"] == dyno.STRESS_SPM
        assert sc["cards"][3]["peak_prl_kN"] > sc["cards"][2]["peak_prl_kN"]
    assert data["scenarios"]["recommendation"]["cards"][3]["card_type"] == "rod_float"
