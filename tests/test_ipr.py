import pytest

from twin import cycle, ipr


def _pwf(params):
    # The engine's REAL flowing bottomhole pressure: absolute pump-intake
    # pressure from submergence (T1-C). The old P_wf = 0.4 * P_res relation was
    # retired in rev 4 and must not be used to test the engine.
    return cycle._pump_intake_pressure_kPa(params)


def test_rate_increases_as_viscosity_falls(params):
    P_res = params["reservoir"]["P_initial_kPa"]
    P_wf = _pwf(params)
    p = dict(params, heated_radius_m=8.0, T_avg_C=150.0)
    q_cold = ipr.oil_rate_m3d(P_res, P_wf, 2000.0, p)
    q_warm = ipr.oil_rate_m3d(P_res, P_wf, 200.0, p)
    q_hot = ipr.oil_rate_m3d(P_res, P_wf, 20.0, p)
    assert q_cold < q_warm < q_hot


def test_cold_rate_is_uneconomically_low(params):
    """At reference (cold, unstimulated) conditions the well must sit below the
    whole CSS cutoff_rate_m3d_range -- the physical premise of CSS for heavy
    oil -- and at or below ~0.5 m3/d (~3 bbl/d).

    COUPLED: ipr.AOF_REF_M3D and css.cutoff_rate_m3d_range[0] must be changed
    together, or this test lies.

    rev 12 (AOF 0.46 -> 0.56): evaluated at the pressure the IPR actually sees
    (cycle.reservoir_pressure_kPa: P_current 9.4 MPa since rev 11; the same
    cold rate cycle.cold_baseline and the benchmark suite use) -> 0.445 m3/d.
    The virgin-pressure figure (0.544 m3/d) must still clear the cutoff floor."""
    from twin import cycle as _cycle
    q_cold = ipr.oil_rate_m3d(_cycle.reservoir_pressure_kPa(params), _pwf(params),
                              params["fluid"]["mu_ref_cP"], params)
    assert q_cold < params["css"]["cutoff_rate_m3d_range"][0]
    assert q_cold <= 0.5
    q_virgin = ipr.oil_rate_m3d(params["reservoir"]["P_initial_kPa"], _pwf(params),
                                params["fluid"]["mu_ref_cP"], params)
    assert q_virgin < params["css"]["cutoff_rate_m3d_range"][0]


def test_unstimulated_well_has_unit_uplift(params):
    mu_ref = params["fluid"]["mu_ref_cP"]
    T0 = params["reservoir"]["T_initial_C"]
    assert ipr.composite_uplift(mu_ref, 0.0, T0, params) == 1.0


def test_uplift_monotone_in_heated_radius_and_bounded(params):
    Ts = params["steam"]["T_injection_C"]
    ups = [ipr.composite_uplift(5.0, r, Ts, params) for r in (2, 5, 10, 20, 40)]
    assert all(a < b for a, b in zip(ups, ups[1:]))
    assert all(1.0 <= u <= ipr.MAX_UPLIFT for u in ups)


def test_rate_zero_at_full_drawdown_to_zero_pressure_ratio(params):
    P_res = params["reservoir"]["P_initial_kPa"]
    q = ipr.oil_rate_m3d(P_res, P_res, 200.0, params)  # Pwf == Pres -> no drawdown
    assert q == 0.0


def test_rate_non_negative(params):
    P_res = params["reservoir"]["P_initial_kPa"]
    q = ipr.oil_rate_m3d(P_res, 0.0, 2000.0, params)
    assert q >= 0.0


def test_cold_rate_scales_with_cold_viscosity(params):
    """rev 10 (external review): AOF_REF_M3D is defined at mu_ref 11,500 cP and
    cold productivity scales with Darcy mobility, so a 15,000 cP oil is slower
    cold than an 8,000 cP one (before rev 10 all three gave 0.447 m3/d). The
    reference cold rate is unchanged."""
    import copy
    P_res = params["reservoir"]["P_initial_kPa"]
    q = {}
    for mu in (8000.0, 11500.0, 15000.0):
        p = copy.deepcopy(params)
        p["fluid"]["mu_ref_cP"] = mu
        q[mu] = ipr.oil_rate_m3d(P_res, _pwf(p), mu, p)
    assert q[15000.0] < q[11500.0] < q[8000.0]
    assert q[11500.0] == pytest.approx(0.447 * 0.56 / 0.46, abs=0.002)   # rev 12: AOF 0.56
    assert q[8000.0] / q[11500.0] == pytest.approx(11500.0 / 8000.0, rel=1e-9)


def test_skin_is_a_params_value_with_code_fallback(params):
    """S_COLD moved to params["ipr"]["s_cold"]; the module constant is the fallback."""
    import copy
    Ts = params["steam"]["T_injection_C"]
    assert ipr.s_cold(params) == params["ipr"]["s_cold"] == ipr.S_COLD
    up = ipr.composite_uplift(5.0, 10.0, Ts, params)
    p0 = copy.deepcopy(params)
    p0["ipr"]["s_cold"] = 0.0
    assert ipr.composite_uplift(5.0, 10.0, Ts, p0) < up
    p0["ipr"].pop("s_cold")
    assert ipr.composite_uplift(5.0, 10.0, Ts, p0) == pytest.approx(up)


def test_rate_is_live_in_reservoir_pressure(params):
    """ECON plan FAIL 3: P_res must not cancel out of the rate equation."""
    P_wf = _pwf(params)
    mu = params["fluid"]["mu_ref_cP"]
    assert ipr.oil_rate_m3d(7400, P_wf, mu, params) < ipr.oil_rate_m3d(11400, P_wf, mu, params)
