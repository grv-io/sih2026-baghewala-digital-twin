"""viscosity.py -- temperature-dependent heavy-oil viscosity (ASTM D341 / Walther).

Source model (T1-F): the **Walther equation**, the double-log
viscosity-temperature law that underlies the ASTM D341 viscosity-temperature
charts used across the petroleum industry:

    log10( log10( nu_cSt + 0.6 ) ) = A - B * log10( T_K )

where `nu` is KINEMATIC viscosity in cSt. We report DYNAMIC viscosity in cP,
so the law is evaluated in cSt and converted with the oil's specific gravity
(from `fluid.api_gravity`, the same API->SG conversion `srp.py` uses).

WHY Walther and not Andrade (`mu = A*exp(B/T_K)`, the previous model):
`docs/research/deep-dives/css_thermal_eor_deep_dive.md` section 2.6 states that Walther /
ASTM D341 is "the industry standard relationship", and that "the simpler
Andrade form ... is a one-exponential approximation that is fine over a narrow
window but under-predicts the collapse over the 50 -> 300 degC span CSS
actually covers". Measured symptom of that under-prediction in this very
codebase: the Andrade fit through the same two anchors returned
**mu(290 degC) = 0.63 cP -- thinner than liquid water**, roughly 8x below the
5 cP at 304 degC reported for a real cyclic-solvent/steam field case
(css deep dive section 2.6). The Walther fit through the identical two anchors
returns **mu(290 degC) ~= 4.1 cP**, which lands on that published field number
without being tuned to it.

Parameter resolution order (all three paths keep `mu_cP(T_C, params)`'s
signature unchanged):
  1. `fluid.walther_A` / `fluid.walther_B` if both non-null -> use them.
  2. else `fluid.andrade_A` / `fluid.andrade_B_K` if both non-null -> Andrade
     (kept so an explicitly-supplied lab Andrade fit still works, and so the
     historical behaviour is reproducible).
  3. else fit Walther A/B exactly through two (T, mu) anchors: the field
     reference point (`mu_ref_cP` at `T_ref_C`) and the high-T anchor
     (`fluid.mu_anchor_T_C` / `fluid.mu_anchor_cP`, rev 10; module fallback
     150 C / 50 cP).

`params/CHANGELOG.md`'s note on why `andrade_A/B` are kept null applies
verbatim to `walther_A/B`: **keep them null and fit at runtime**, because
writing rounded fitted values back into the JSON introduces float drift that
breaks exact recovery of `mu_ref_cP` at `T_ref_C`.
"""
from __future__ import annotations

import math

# ASSUMPTION: high-temperature anchor point used only when neither the
# walther_A/B nor the andrade_A/B pair is supplied in field_params.json.
# 50 cP at 150 degC is the example anchor suggested in docs/SPEC.md for a heavy oil
# of this API gravity. NOTE (honesty label): [ASSUMPTION - SPEC placeholder].
# `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md` section 3.2 (A5)
# names a two-point lab viscosity measurement at 100 degC and 200 degC as the
# single most valuable data request to OIL; that measurement would replace
# this anchor.
#
# rev 10 (hardening after external review): the anchor now lives in
# params["fluid"]["mu_anchor_T_C"] / ["mu_anchor_cP"] (tagged [ASSUMPTION],
# UQ range mu(150 C) U[30, 80] cP in ml/uq.py). These module constants are the
# FALLBACK used only when those keys are absent, so old params trees still run.
ANCHOR_T_C = 150.0
ANCHOR_MU_CP = 50.0

# Walther / ASTM D341 additive constant inside the double log. 0.6 is the
# classical D341 value for petroleum liquids. SOURCE: ASTM D341. [CONFIRMED]
WALTHER_C = 0.6

# ASSUMPTION: physical high-temperature floor on oil viscosity, in cP. Any
# viscosity-temperature correlation extrapolated hundreds of degrees past its
# anchors can be driven below the viscosity of liquid water (~0.13 cP at
# 290 degC, ~0.89 cP at 25 degC), which is non-physical for a C7+ crude.
# Overridable via `fluid.mu_floor_cP`. [ASSUMPTION - physical bound, not fitted]
DEFAULT_MU_FLOOR_CP = 1.0


def anchor_point(params: dict) -> tuple[float, float]:
    """(T_C, mu_cP) high-temperature Walther anchor in force for this params tree.

    rev 10: read from `fluid.mu_anchor_T_C` / `fluid.mu_anchor_cP`, falling back
    to the module constants ANCHOR_T_C / ANCHOR_MU_CP. [ASSUMPTION - SPEC
    placeholder; a two-point lab measurement at 100/200 C would replace it.]
    """
    fluid = params.get("fluid", {}) if isinstance(params, dict) else {}
    T = fluid.get("mu_anchor_T_C")
    mu = fluid.get("mu_anchor_cP")
    return (float(T) if T is not None else ANCHOR_T_C,
            float(mu) if mu is not None else ANCHOR_MU_CP)


def water_mu_cP(T_C: float) -> float:
    """Dynamic viscosity of liquid water (cP) -- Vogel-Fulcher-Tammann fit.

    mu_w [mPa.s] = exp(-3.7188 + 578.919 / (T_K - 137.546))
    (Vogel 1921 form with the standard coefficients for water, e.g. as tabulated
    in Viswanath & Natarajan, *Data Book on the Viscosity of Liquids*, 1989).
    Checks against the IAPWS saturated-liquid table: 0.89 cP at 25 C, 0.55 at
    50 C, 0.18 at 150 C, 0.094 at 290 C (all within ~3 %). Used by
    srp.rod_drag_viscosity_cP for the water-continuous produced stream (rev 10).
    [SOURCED - standard correlation]
    """
    T_K = max(T_C + 273.15, 150.0)
    return math.exp(-3.7188 + 578.919 / (T_K - 137.546))


def _sg_from_api(api_gravity: float) -> float:
    """Standard API-gravity to specific-gravity conversion (same as srp.py)."""
    return 141.5 / (131.5 + api_gravity)


def _fit_andrade(mu1_cP: float, T1_C: float, mu2_cP: float, T2_C: float) -> tuple[float, float]:
    """Solve mu = A*exp(B/T_K) exactly through two (T, mu) points.

    ln(mu1) = ln(A) + B/T1 ; ln(mu2) = ln(A) + B/T2
    => B = ln(mu1/mu2) / (1/T1 - 1/T2) ; A = mu1 / exp(B/T1)

    Retained (a) for the `fluid.andrade_A/andrade_B_K` code path and (b) so
    tests/benchmarks can compare the two laws over the CSS temperature span
    (benchmark group A1).
    """
    T1_K = T1_C + 273.15
    T2_K = T2_C + 273.15
    B = math.log(mu1_cP / mu2_cP) / (1.0 / T1_K - 1.0 / T2_K)
    A = mu1_cP / math.exp(B / T1_K)
    return A, B


def _fit_walther(nu1_cSt: float, T1_C: float, nu2_cSt: float, T2_C: float) -> tuple[float, float]:
    """Solve log10(log10(nu + 0.6)) = A - B*log10(T_K) exactly through two points."""
    T1_K = T1_C + 273.15
    T2_K = T2_C + 273.15
    z1 = math.log10(math.log10(nu1_cSt + WALTHER_C))
    z2 = math.log10(math.log10(nu2_cSt + WALTHER_C))
    l1 = math.log10(T1_K)
    l2 = math.log10(T2_K)
    B = (z1 - z2) / (l2 - l1)
    A = z1 + B * l1
    return A, B


def _walther_nu_cSt(T_C: float, A: float, B: float) -> float:
    """Evaluate the Walther law: nu(T) in cSt."""
    T_K = max(T_C + 273.15, 1.0)
    z = A - B * math.log10(T_K)
    # nu + 0.6 = 10 ** (10 ** z)
    inner = 10.0 ** z
    # Guard the double exponential against overflow at absurdly low T.
    inner = min(inner, 300.0)
    return 10.0 ** inner - WALTHER_C


def walther_coefficients(params: dict) -> tuple[float, float]:
    """The (A, B) actually in force for this params tree (explicit or fitted)."""
    fluid = params["fluid"]
    A = fluid.get("walther_A")
    B = fluid.get("walther_B")
    if A is not None and B is not None:
        return float(A), float(B)
    sg = _sg_from_api(fluid["api_gravity"])
    anchor_T, anchor_mu = anchor_point(params)
    nu_ref = fluid["mu_ref_cP"] / sg
    nu_anchor = anchor_mu / sg
    return _fit_walther(nu_ref, fluid["T_ref_C"], nu_anchor, anchor_T)


def mu_cP(T_C: float, params: dict) -> float:
    """Dynamic viscosity (centipoise) at temperature T_C.

    Walther / ASTM D341 by default (see module docstring); Andrade only if
    `fluid.andrade_A` / `fluid.andrade_B_K` are explicitly supplied and
    `fluid.walther_A/B` are not. Result is floored at `fluid.mu_floor_cP`
    (default 1.0 cP) -- a physical bound, not a fit.

    Both laws are strictly monotone decreasing in T for the calibration points
    we use (higher-T anchor has lower viscosity), which is always the physical
    case for heavy oil.

    Args:
        T_C: temperature in degrees Celsius.
        params: field_params.json tree (reads params["fluid"]).
    """
    fluid = params["fluid"]
    floor_cP = float(fluid.get("mu_floor_cP") or DEFAULT_MU_FLOOR_CP)

    wA = fluid.get("walther_A")
    wB = fluid.get("walther_B")
    aA = fluid.get("andrade_A")
    aB = fluid.get("andrade_B_K")

    if wA is None and wB is None and aA is not None and aB is not None:
        # Explicit Andrade fit supplied -- honour it (legacy / lab-fit path).
        T_K = max(T_C + 273.15, 1.0)
        return max(aA * math.exp(aB / T_K), floor_cP)

    A, B = walther_coefficients(params)
    sg = _sg_from_api(fluid["api_gravity"])
    nu = _walther_nu_cSt(T_C, A, B)
    mu = nu * sg
    return max(mu, floor_cP)
