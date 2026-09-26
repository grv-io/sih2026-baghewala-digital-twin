import copy

import pytest

from twin import viscosity


def test_reference_point_recovered(params):
    fluid = params["fluid"]
    mu = viscosity.mu_cP(fluid["T_ref_C"], params)
    assert mu == pytest.approx(fluid["mu_ref_cP"], rel=1e-6)


def test_monotonic_decreasing_with_temperature(params):
    temps = [47, 60, 80, 100, 120, 150, 180, 200, 250]
    mus = [viscosity.mu_cP(t, params) for t in temps]
    for a, b in zip(mus, mus[1:]):
        assert b < a, "viscosity must fall strictly as temperature rises"


def test_cold_viscosity_is_thousands_of_cP(params):
    # Bounds are relative to the field's own mu_ref_cP/T_ref_C anchor
    # (params/field_params.json CHANGELOG: mu_ref_cP=11500 @ T_ref_C=50, real
    # Baghewala field data) rather than a hardcoded absolute band, so this
    # stays correct if the reference viscosity is refined further. 47C is
    # just below T_ref_C=50, so mu should be close to (and slightly above)
    # mu_ref_cP.
    mu = viscosity.mu_cP(47.0, params)
    mu_ref = params["fluid"]["mu_ref_cP"]
    assert 0.5 * mu_ref < mu < 3.0 * mu_ref


def test_hot_viscosity_is_tens_of_cP_or_less(params):
    mu = viscosity.mu_cP(180.0, params)
    assert mu < 100.0


def test_explicit_andrade_params_used_when_not_null(params):
    p = copy.deepcopy(params)
    p["fluid"]["andrade_A"] = 1.0
    p["fluid"]["andrade_B_K"] = 0.0
    # B=0 => mu = A = 1.0 regardless of T
    assert viscosity.mu_cP(100.0, p) == pytest.approx(1.0)
