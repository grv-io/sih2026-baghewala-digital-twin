import copy
import math

import pytest

from twin import thermal


def _params_run(params, steam_t):
    p = dict(params)
    p["steam_t"] = steam_t
    return p


def test_temperature_rises_during_injection(params):
    p = _params_run(params, 1500)
    T0, _ = thermal.steam_zone_temperature(0.0, p)
    T5, _ = thermal.steam_zone_temperature(5.0, p)
    T10, _ = thermal.steam_zone_temperature(10.0, p)
    assert T0 == params["reservoir"]["T_initial_C"]
    assert T5 > T0
    assert T10 > T5


def test_heated_radius_grows_during_injection_and_freezes_after(params):
    p = _params_run(params, 1500)
    inject_end = 1500 / params["steam"]["injection_rate_tpd"]
    _, r5 = thermal.steam_zone_temperature(5.0, p)
    _, r10 = thermal.steam_zone_temperature(10.0, p)
    _, r_end = thermal.steam_zone_temperature(inject_end, p)
    _, r_after = thermal.steam_zone_temperature(inject_end + 30.0, p)
    assert 0 < r5 < r10 <= r_end
    # ASSUMPTION in thermal.py: heated radius is frozen once injection stops.
    assert r_after == r_end


def test_temperature_decays_toward_reservoir_after_injection_stops(params):
    p = _params_run(params, 1500)
    inject_end = 1500 / params["steam"]["injection_rate_tpd"]
    T_peak, _ = thermal.steam_zone_temperature(inject_end, p)
    T_plus_10, _ = thermal.steam_zone_temperature(inject_end + 10.0, p)
    T_plus_30, _ = thermal.steam_zone_temperature(inject_end + 30.0, p)
    T_plus_90, _ = thermal.steam_zone_temperature(inject_end + 90.0, p)
    T0 = params["reservoir"]["T_initial_C"]

    assert T0 < T_plus_30 < T_plus_10 < T_peak
    # T1-B: Boberg-Lantz conduction cooldown (delta = 0, no production here).
    # The old "< 20 % after 90 d" was an artefact of the invented tau = 20 d
    # exponential; conduction over a 12 m pay is far slower (PHYSICS plan T1-B).
    ratio_90 = (T_plus_90 - T0) / (T_peak - T0)
    assert 0.3 < ratio_90 < 0.8
    # ...and slower than the retired tau = 20 d exponential at 30 d.
    ratio_30 = (T_plus_30 - T0) / (T_peak - T0)
    assert ratio_30 > math.exp(-30.0 / 20.0)


def test_more_steam_gives_hotter_or_equal_peak_zone(params):
    p_small = _params_run(params, 500)
    p_large = _params_run(params, 2500)
    inject_end_small = 500 / params["steam"]["injection_rate_tpd"]
    inject_end_large = 2500 / params["steam"]["injection_rate_tpd"]
    T_small, _ = thermal.steam_zone_temperature(inject_end_small, p_small)
    T_large, _ = thermal.steam_zone_temperature(inject_end_large, p_large)
    assert T_large >= T_small


def test_sandface_enthalpy_includes_sensible_heat(params):
    """rev 5: Marx-Langenheim heat injection = C_w*(T_s - T_R) + x_sf*L_v.
    The sensible term (~1.08 MJ/kg) was missing before rev 5."""
    h = thermal.sandface_enthalpy_J_per_kg(params)
    _, x_down = thermal.wellbore_delivery(params)
    latent_only = x_down * params["steam"]["latent_heat_Jkg"]
    assert h > 2.5 * latent_only
    assert 1.4e6 < h < 1.8e6


def test_wellbore_params_describe_the_same_joules(params):
    """The heat-loss fraction param and the sandface-quality ratio must agree
    (rev 5 removed the double count of the same condensed steam)."""
    implied = thermal.implied_wellbore_loss_frac(params)
    stated, _ = thermal.wellbore_delivery(params)
    assert implied == pytest.approx(stated, rel=0.10)


def test_delivered_heat_is_less_than_wellhead_heat(params):
    steam = params["steam"]
    dT = steam["T_injection_C"] - params["reservoir"]["T_initial_C"]
    h_wh = thermal.CW_LIQUID_JKGK * dT + steam["quality"] * steam["latent_heat_Jkg"]
    assert thermal.sandface_enthalpy_J_per_kg(params) < h_wh


def test_cylinder_theta_matches_numerical_source_integral():
    """f_HD closed form vs direct integration of the instantaneous cylindrical
    source (Carslaw & Jaeger), and cylinder cools faster than the slab stand-in."""
    import numpy as np
    from scipy.integrate import quad
    from scipy.special import i0e

    R, a, t = 10.0, 0.0939, 240.0
    k = 4 * a * t

    def u(r):
        f = lambda s: np.exp(-(r - s) ** 2 / k) * i0e(2 * r * s / k) * s
        return quad(f, 0, R, limit=200)[0] * 2 / k

    exact = quad(lambda r: u(r) * r, 0, R, limit=200)[0] * 2 / R ** 2
    assert thermal.cylinder_theta(R, a, t) == pytest.approx(exact, abs=1e-4)
    assert thermal.cylinder_theta(R, a, t) < thermal.slab_theta(2 * R, a, t)
    assert thermal.cylinder_theta(R, a, 0.0) == 1.0


def test_heated_radius_is_a_near_wellbore_bubble(params):
    """ECON plan C3: 3 m <= r_h <= 30 m after a full 1,500 t injection."""
    p = _params_run(params, 1500)
    _, r = thermal.steam_zone_temperature(1500 / params["steam"]["injection_rate_tpd"], p)
    assert 3.0 <= r <= 30.0


# ------------------------------------------------ physics v3: sourced delta --
def test_bl_half_is_exact_energy_conservation_without_conduction():
    """PEH Eq. 15.70/15.73 (Boberg & Lantz 1966): delta = Q_p / (2Q). With no
    conduction (f_VD = f_HD = 1, t = 0) theta = 1 - 2*delta must equal the
    energy balance 1 - Q_p/Q -- which fixes BL_DELTA_FACTOR at exactly 1/2."""
    assert thermal.BL_DELTA_FACTOR == 0.5
    for frac_removed in (0.0, 0.1, 0.3, 0.6):
        delta = thermal.BL_DELTA_FACTOR * frac_removed
        theta = thermal.boberg_lantz_theta(0.0, 12.0, 10.0, 0.0939, delta)
        assert theta == pytest.approx(1.0 - frac_removed, abs=1e-12)


def test_water_enthalpy_matches_steam_tables():
    """h_f(100 C) = 419.1, h_f(290 C) = 1290.0 kJ/kg (IAPWS-IF97); the
    interpolated table must be within 0.5 %, and consistent with the rev-5
    CW_LIQUID_JKGK mean specific heat over 50-290 C."""
    assert thermal.water_enthalpy_kJkg(100.0) == pytest.approx(419.1, rel=0.005)
    assert thermal.water_enthalpy_kJkg(290.0) == pytest.approx(1290.0, rel=0.005)
    mean_cp = (thermal.water_enthalpy_kJkg(290.0) - thermal.water_enthalpy_kJkg(50.0)) / 240.0
    assert mean_cp * 1000.0 == pytest.approx(thermal.CW_LIQUID_JKGK, rel=0.01)


def test_oil_heat_capacity_is_about_half_of_water():
    """Gambill: a 15.5 API crude carries ~2.0-2.3 MJ/m3K at 100-200 C, about
    half of water's ~4.2 (PEH ch. 15: petroleum specific heat ~0.5)."""
    for T in (100.0, 150.0, 200.0):
        m_o = thermal.oil_heat_capacity_Jm3K(T, 15.5)
        assert 1.8e6 <= m_o <= 2.5e6


def test_if97_saturation_line():
    """rev 10: IAPWS-IF97 region-4 saturation line (steam-state check)."""
    assert thermal.p_sat_kPa(290.0) == pytest.approx(7441.6, rel=1e-4)
    assert thermal.p_sat_kPa(100.0) == pytest.approx(101.42, rel=1e-3)
    assert thermal.T_sat_C(9000.0) == pytest.approx(303.35, abs=0.02)
    for T in (150.0, 250.0, 290.0, 310.0):
        assert thermal.T_sat_C(thermal.p_sat_kPa(T)) == pytest.approx(T, abs=1e-6)


def test_steam_state_check_flags_the_params_PT_inconsistency(legacy_params):
    """rev 10: 290 C cannot be saturated steam at 85-97 kgf/cm2 wellhead
    (T_sat ~299-308 C) nor at a sandface above the 11.4 MPa virgin P_res
    (p_sat(290 C) = 7.44 MPa). The check WARNS, never fails.
    rev 11: this is the "legacy_T" steam model (conftest.legacy_rev10); the
    shipped "saturated_P" model passes the check (tests/test_physics_wave3.py)."""
    import copy
    import warnings
    params = legacy_params
    chk = thermal.steam_state_check(params)
    assert not chk["consistent"] and len(chk["warnings"]) == 2
    lo, hi = chk["T_sat_at_wellhead_C"]
    assert 297.0 <= lo <= 300.0 and 306.0 <= hi <= 309.0
    # a depleted near-well region below p_sat and a T consistent with the
    # wellhead pressure clear both warnings
    q = copy.deepcopy(params)
    q["reservoir"]["P_current_kPa"] = 6000.0
    q["steam"]["T_injection_C"] = 300.0
    assert thermal.steam_state_check(q)["consistent"]
    # simulate_css_cycle warns, and still runs
    from twin import cycle
    thermal._WARNED_STEAM_STATES.clear()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        df = cycle.simulate_css_cycle(1500, 7, 1.2, 5, params)
    assert len(df) > 0
    assert any("steam-state consistency" in str(w.message) for w in rec)


def test_produced_heat_follows_PEH_eq_15_74(params):
    """Qdot_p = (q_o M_o + q_w M_w) * (T_avg - T_R): zero at T_R, linear in
    the rates, and dominated by the water at an 85 % cut."""
    T_R = params["reservoir"]["T_initial_C"]
    assert thermal.produced_heat_J_per_day(2.0, 10.0, T_R, params) == 0.0
    q1 = thermal.produced_heat_J_per_day(1.0, 5.667, 200.0, params)
    q2 = thermal.produced_heat_J_per_day(2.0, 11.334, 200.0, params)
    assert q2 == pytest.approx(2.0 * q1, rel=1e-9)
    water_only = thermal.produced_heat_J_per_day(0.0, 5.667, 200.0, params)
    assert water_only / q1 > 0.9
