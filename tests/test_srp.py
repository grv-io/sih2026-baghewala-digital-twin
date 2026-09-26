import copy

import pytest

from twin import srp


def _oil_drag(params):
    """rev-9 drag rule: the rods see the reservoir-oil viscosity itself."""
    p = copy.deepcopy(params)
    p["fluid"]["tubing_viscosity_model"] = "oil"
    return p


def test_floating_index_increases_with_viscosity(params):
    """Drag mechanics at a given drag viscosity (rev-9 rule; rev 10's emulsion
    model makes FI independent of oil viscosity in a water-continuous stream,
    see the emulsion tests below)."""
    params = _oil_drag(params)
    stroke = params["srp"]["stroke_m"]
    s_cold = srp.pump_state(8, stroke, 2000.0, 5.0, params)
    s_mid = srp.pump_state(8, stroke, 200.0, 5.0, params)
    s_hot = srp.pump_state(8, stroke, 20.0, 5.0, params)
    assert s_hot["floating_index"] < s_mid["floating_index"] < s_cold["floating_index"]


def test_floating_index_increases_with_spm(params):
    stroke = params["srp"]["stroke_m"]
    s_low = srp.pump_state(4, stroke, 2000.0, 5.0, params)
    s_mid = srp.pump_state(8, stroke, 2000.0, 5.0, params)
    s_high = srp.pump_state(12, stroke, 2000.0, 5.0, params)
    assert s_low["floating_index"] < s_mid["floating_index"] < s_high["floating_index"]


def test_floating_index_bounded_0_1(params):
    stroke = params["srp"]["stroke_m"]
    for mu in [1.0, 50.0, 500.0, 2000.0, 50000.0]:
        for spm in [4, 8, 12]:
            state = srp.pump_state(spm, stroke, mu, 5.0, params)
            assert 0.0 <= state["floating_index"] <= 1.0


def test_peak_rod_load_positive_and_plausible(params):
    stroke = params["srp"]["stroke_m"]
    state = srp.pump_state(8, stroke, 200.0, 5.0, params)
    assert 0.0 < state["peak_rod_load_kN"] < 200.0


def test_prod_rate_capped_by_pump_capacity(params):
    stroke = params["srp"]["stroke_m"]
    # Ask for an absurdly large IPR rate; srp must cap it at mechanical capacity.
    state = srp.pump_state(8, stroke, 20.0, 1.0e6, params)
    assert state["prod_rate_m3d"] < 1.0e6


def test_energy_scales_with_load_stroke_and_spm(params):
    stroke = params["srp"]["stroke_m"]
    s_low_spm = srp.pump_state(4, stroke, 200.0, 5.0, params)
    s_high_spm = srp.pump_state(12, stroke, 200.0, 5.0, params)
    assert s_high_spm["energy_kWh_d"] > s_low_spm["energy_kWh_d"]


def test_pump_lifts_liquid_not_oil(params):
    """rev 5: the plunger displaces oil + water; oil capacity is the liquid
    displacement times (1 - water_cut)."""
    stroke = params["srp"]["stroke_m"]
    wc = params["fluid"]["water_cut"]
    s = srp.pump_state(5, stroke, 20.0, 1.0e6, params)
    assert s["oil_capacity_m3d"] == pytest.approx(s["pump_capacity_m3d"] * (1 - wc))
    assert s["prod_rate_m3d"] == pytest.approx(s["oil_capacity_m3d"])
    assert s["pump_limited"] is True


def test_pump_capacity_at_practice_spm_is_comparable_to_well_rate(params):
    """Pump sized for a ~20 bbl/d heavy-oil well (1.75 in x 86 in stroke):
    oil capacity over the published 3-6 spm practice band must bracket a
    15-25 bbl/d (2.4-4.0 m3/d) stimulated peak, so SPM is a real lever. The
    rev-4 2.25 in x 118 in pump gave ~75 m3/d at 8 spm on an oil basis."""
    stroke = params["srp"]["stroke_m"]
    lo, hi = params["srp"]["spm_practice_band"]
    cap_lo = srp.pump_state(lo, stroke, 20.0, 1e6, params)["oil_capacity_m3d"]
    cap_hi = srp.pump_state(hi, stroke, 20.0, 1e6, params)["oil_capacity_m3d"]
    assert cap_lo < 2.4 and cap_hi > 3.0


# ---------------------------------------------------------------------------
# Economics v2 (27 Sep 2026): polished-rod energy = card area
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("spm, mu_cP, q_oil_m3d", [
    (5.0, 50.0, 2.5),      # early hot day, reservoir-limited, part-full pump
    (4.0, 2000.0, 1.0),    # mid-cycle, drag starting to matter
    (2.0, 11500.0, 0.447), # the cold well at the keep-moving floor (cold baseline)
])
def test_srp_energy_matches_dyno_card_area(params, spm, mu_cP, q_oil_m3d):
    """srp's daily energy is the closed-loop polished-rod work (rod weight
    credited back on the downstroke) and must agree with the Gibbs
    wave-equation card area (twin/dyno.py) within 15 % at the same liquid
    rate. The pre-v2 peak-load x stroke x spm estimate was 1.4-3.6x the card."""
    from twin import dyno
    stroke = params["srp"]["stroke_m"]
    st = srp.pump_state(spm, stroke, mu_cP, q_oil_m3d, params)
    card = dyno.card_for_row({"oil_m3d": st["prod_rate_m3d"], "mu_cP": mu_cP, "spm": spm}, params)
    card_kWh_d = card["polished_rod_kW"] * 24.0
    assert st["energy_kWh_d"] == pytest.approx(card_kWh_d, rel=0.15)
    # and the old estimate really was far off (regression guard on the fix)
    old = st["peak_rod_load_kN"] * 1e3 * stroke * spm * 1440.0 / 3.6e6
    assert old > 1.3 * card_kWh_d


# ---------------------------------------------------------------------------
# rev 10: produced-stream (emulsion) drag viscosity
# ---------------------------------------------------------------------------
def test_emulsion_viscosity_on_the_continuous_phase(params):
    """rev 12: the W/O branch is Pal & Rhodes (1989) with phi* = 0.84, capped
    at 10x; `emulsion_law = "brinkman"` (no cap) is the rev-10/11 rule."""
    from twin import viscosity
    inv = params["fluid"]["emulsion_inversion_wc"]
    mu_o = 1000.0
    # oil-continuous: mu_o * mu_r(wc), = mu_o at zero water
    assert srp.rod_drag_viscosity_cP(mu_o, params, water_cut=0.0) == pytest.approx(mu_o)
    x = 0.5 / 0.84
    pal_rhodes = (1.0 + x / (1.187 - x)) ** 2.49
    assert srp.rod_drag_viscosity_cP(mu_o, params, water_cut=0.5) == pytest.approx(mu_o * pal_rhodes)
    assert srp.rod_drag_viscosity_cP(mu_o, params, water_cut=0.65) == pytest.approx(10.0 * mu_o)  # cap
    brink = copy.deepcopy(params)
    brink["fluid"]["emulsion_law"] = "brinkman"
    brink["fluid"].pop("emulsion_mu_r_max")
    assert srp.rod_drag_viscosity_cP(mu_o, brink, water_cut=0.5) == pytest.approx(mu_o * 0.5 ** -2.5)
    # water-continuous above the inversion: mu_w(T) * wc^-2.5, independent of mu_o
    hi = srp.rod_drag_viscosity_cP(mu_o, params, water_cut=0.85, T_C=50.0)
    assert hi == pytest.approx(viscosity.water_mu_cP(50.0) * 0.85 ** -2.5)
    assert hi == pytest.approx(srp.rod_drag_viscosity_cP(50000.0, params, water_cut=0.85, T_C=50.0))
    assert hi < 1.5
    # inversion is a jump down by orders of magnitude -- the rev 10-12 sharp
    # switch (band 0); rev 13 spreads it over a band (tests/test_physics_wave5.py)
    params = copy.deepcopy(params)
    params["fluid"]["emulsion_inversion_band_wc"] = 0.0
    below = srp.rod_drag_viscosity_cP(mu_o, params, water_cut=inv - 0.01)
    above = srp.rod_drag_viscosity_cP(mu_o, params, water_cut=inv + 0.01)
    assert below > 1000.0 * above
    # the rev-9 rule is still available
    assert srp.rod_drag_viscosity_cP(mu_o, _oil_drag(params), water_cut=0.85) == mu_o
    with pytest.raises(ValueError):
        q = copy.deepcopy(params)
        q["fluid"]["tubing_viscosity_model"] = "bogus"
        srp.rod_drag_viscosity_cP(mu_o, q)


def test_water_continuous_stream_does_not_float_the_rods(params):
    """At the shipped 85 % cut even cold 11,500 cP oil at 12 spm leaves the
    floating index ~0 (rev 10 finding); with an oil-continuous stream (65 %
    water) the same point floats hard."""
    stroke = params["srp"]["stroke_m"]
    st = srp.pump_state(12, stroke, 11500.0, 1.0, params)
    assert st["floating_index"] < 0.05 and st["mu_drag_cP"] < 1.5
    wo = copy.deepcopy(params)
    wo["fluid"]["water_cut"] = 0.65
    assert srp.pump_state(12, stroke, 11500.0, 1.0, wo)["floating_index"] == 1.0


def test_k_visc_is_a_params_value_with_code_fallback(params):
    stroke = params["srp"]["stroke_m"]
    p = _oil_drag(params)
    base = srp.pump_state(5, stroke, 2000.0, 1.0, p)["floating_index"]
    q = copy.deepcopy(p)
    q["srp"]["k_visc"] = 2.0 * p["srp"]["k_visc"]
    assert srp.pump_state(5, stroke, 2000.0, 1.0, q)["floating_index"] == pytest.approx(2.0 * base)
    q["srp"].pop("k_visc")
    assert srp.k_visc(q) == srp.K_VISC == p["srp"]["k_visc"]


def test_electric_energy_is_polished_rod_over_surface_efficiency(params):
    stroke = params["srp"]["stroke_m"]
    st = srp.pump_state(5.0, stroke, 50.0, 2.0, params)
    eta = srp.surface_efficiency(params)
    assert 0.5 <= eta <= 0.75
    assert st["electric_kWh_d"] == pytest.approx(st["energy_kWh_d"] / eta)
    assert 0.0 < st["hydraulic_kWh_d"] < st["energy_kWh_d"]
