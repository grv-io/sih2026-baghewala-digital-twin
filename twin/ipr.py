"""ipr.py -- inflow performance for the Baghewala producer (composite-radial PI).

Two source models, composed:

**1. Vogel (1968) shape.** Vogel, J.V., "Inflow Performance Relationships for
Solution-Gas Drive Wells", JPT (1968):

    q / q_max = 1 - 0.2*(Pwf/Pr) - 0.8*(Pwf/Pr)**2

with `q_max = J * P_res / 1.8`, the standard Vogel absolute-open-flow relation.
Writing q_max that way is what makes **reservoir pressure live**: `q_max` is
linear in `P_res`. (Before T1-A/T1-C, `cycle.py` set `P_wf = 0.4 * P_res`, so
`Pwf/Pr` was always exactly 0.4 and `P_res` cancelled algebraically out of the
rate equation -- `P_initial_kPa = 11400` was an inert parameter that appeared
on the dashboard and changed nothing. See
`docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md` section 3.7 FAIL 3.)

**2. Boberg & Lantz (1966) step 2 -- the composite-radial productivity index
(T1-A).** This REPLACES the old `mobility_factor = mu_ref / mu`, a global
multiplier that scaled the ENTIRE drainage volume by the near-well mobility
ratio. At the demo point that factor was **5,750x**, and the twin's peak rate
came out at 471 bbl/d for a single well against a whole-field total of
655 bbl/d across 34 producers -- roughly **25x too high**.

The physics: only a ring of radius `r_h` around the well is hot. Everything
from `r_h` out to the drainage radius is still at `mu_ref` (11,500 cP), and it
is that cold annulus that controls the pressure drop. Boberg & Lantz solve the
two-region radial flow resistance:

    R_hot  = mu_cold * ln(r_e / r_h) + mu_hot * ( ln(r_h / r_w) + s(T) )
    R_cold = mu_cold * ( ln(r_e / r_w) + S_COLD )
    uplift = R_cold / R_hot          (>= 1; this is the *uplift*, not 5,750x)

SOURCE: css_thermal_eor_deep_dive.md section 2.2 (UPC Global 2021, *Artificial
Lift Performance Coupled with Boberg & Lantz Model*) and section 4-paper-1
(Boberg & Lantz, JPT 1966): "steam-zone radius from Marx-Langenheim, then an
average heated-zone temperature that decays ... to give viscosity -> PI ->
rate". The temperature-dependent skin `s(T)` is css section 1.2's fourth CSS
mechanism -- "heat dissolves wax and asphaltene deposits near the perforations"
-- which is not optional for a born-heavy asphaltic Type II-S crude.

**The counter-intuitive result this produces, and it is a genuine one:** the
uplift is nearly flat in temperature (2.62x at 240 degC vs 2.56x at 120 degC at
r_h = 7.2 m, skin off) because the cold annulus dominates the denominator.
Past a point, more heat does almost nothing -- **more heated RADIUS is what
pays.** That is the correct CSS mental model and it is what the twin now says.
"""
from __future__ import annotations

import math

from twin import thermal

# ASSUMPTION: asphaltene/wax skin on a cold, unstimulated Baghewala well.
# SOURCE (mechanism, not magnitude): css_thermal_eor_deep_dive.md section 1.2,
# CSS mechanism 4 -- "heat dissolves wax and asphaltene deposits near the
# perforations". Magnitude 5.0 is [ASSUMPTION]: a moderate, defensible
# damaged-well skin. It is removed in proportion to how hot the near-well rock
# is, which is what makes cleanup part of the first-cycle uplift.
#
# rev 10 (external review, 27 Sep): this constant decides the economics (S = 0
# gives uplift ~3x, not ~5.7x, and a negative incremental margin), so it now
# lives in params["ipr"]["s_cold"] [ASSUMPTION, range 0-8, sampled U[0, 8] in
# ml/uq.py, optional free parameter in twin/calibrate.py]. This module value is
# only the FALLBACK when that key is absent. A pre-CSS pressure build-up test on
# a BGW well would measure it directly -- top data ask.
S_COLD = 5.0

# ASSUMPTION: hard ceiling on the composite uplift. The two-region resistance
# ratio is unbounded as r_h -> r_e and mu_hot -> the floor, but real reservoirs
# do not deliver unbounded productivity gain: relative permeability, the finite
# perforated interval and near-well pressure support all bind first. 10x is
# comfortably above the 5-6x first-cycle uplift OIL published for BGW-8, so it
# never binds at field-realistic settings -- it is a guard, not a tuning knob.
MAX_UPLIFT = 10.0

# Pressure at which AOF_REF_M3D below was calibrated (kPa). Kept as a module
# constant rather than read from params so that sweeping
# `reservoir.P_initial_kPa` genuinely moves the rate (Vogel's q_max = J*Pr/1.8
# is linear in reservoir pressure) instead of silently cancelling.
# SOURCE for the value: params/field_params.json reservoir.P_initial_kPa
# (~116 kgf/cm^2, OIL internal PPT). [CONFIRMED]
P_CAL_KPA = 11400.0

# [CALIBRATED] absolute open-flow rate (m3/d) of the COLD, UNSTIMULATED well at
# P_CAL_KPA -- i.e. the pre-CSS productivity that the composite uplift above
# multiplies. History: 1.0 (v1) -> 0.7 (integration) -> 0.60 (rev 4, T1-A)
# -> 0.46 (rev 5 calibration, 26 Sep 2026).
#
# Tuned to: cold producing rate <= ~0.5 m3/d. At the real absolute pump-intake
# P_wf (~1,144 kPa, cycle._pump_intake_pressure_kPa) Vogel gives
# 0.46 * 0.972 = 0.447 m3/d = 2.8 bbl/d cold. With the rev-5 composite uplift
# (~5.1x at 1,500 t) plus pressure recharge this puts the stimulated peak at
# ~16 bbl/d and peak/cold at ~5.7x -- OIL's published 5-6x first-cycle uplift
# for BGW-8 -- against a field average of ~19 bbl/d/well (655 bbl/d, 34 wells,
# Jul-2025, all lift/stimulation modes). Also: AOF barely moves SOR once the
# cycle is energy-limited (Boberg-Lantz delta); it mainly sets rate and length.
#
# COUPLED CONSTANT: `css.cutoff_rate_m3d_range` lower bound (0.6 m3/d) must stay
# above the cold rate. tests/test_ipr.py::test_cold_rate_is_uneconomically_low
# checks exactly that, at the engine's real P_wf.
#
# rev 12 (physics wave 4, 27 Sep 2026): 0.46 -> **0.56** [CALIBRATED], also
# written to params["ipr"]["aof_ref_m3d"]. Re-tuned to the FIELD observable:
# the reference first-cycle peak must sit in the 15-40 bbl/d envelope (field
# average ~19 bbl/d/well). Since rev 11 the IPR sees the depleted P_current
# (9.4 MPa) and the recharge is capped at the sandface pressure, which put the
# reference peak at 12.4 bbl/d; 0.56 is the smallest 0.01 step that restores
# >= 15 (15.1 bbl/d). The uplift (peak / cold rate) is AOF-invariant (5.41x),
# so the BGW-8 5-6x band is untouched; the reference SOR moves to 4.50 under
# the rev-12 produce-end rule, inside the re-specified 3.0-4.6 band (the old
# 3.8-4.6 was our own plan target, not data; literature 3-8, Kern River 3.47).
# Cold rate at P_current 9.4 MPa: 0.445 m3/d (2.8 bbl/d); at virgin 11.4 MPa
# 0.544 m3/d -- still below the 0.6 cutoff floor. Trade-off table: TIER1 s. 11.
AOF_REF_M3D = 0.56

# rev 10: the viscosity at which AOF_REF_M3D is defined (cP). Darcy: cold
# productivity J is proportional to k/mu, so the cold AOF of a well whose cold
# reservoir oil has viscosity mu_res is AOF_REF_M3D * MU_AOF_REF_CP / mu_res.
# Before rev 10 the cold rate did not depend on mu_ref_cP at all (a 15,000 cP
# oil produced exactly as fast cold as an 8,000 cP one, and so earned MORE
# incremental margin under UQ -- counter-physical; external review finding).
# Kept as a module constant (like P_CAL_KPA) so that sweeping
# `fluid.mu_ref_cP` genuinely moves the cold rate. SOURCE for the value:
# params/field_params.json fluid.mu_ref_cP (11,500 cP at 50 C, OIL PPT).
# [CONFIRMED anchor; the Darcy scaling is textbook]
MU_AOF_REF_CP = 11500.0


def aof_ref_m3d(params: dict) -> float:
    """AOF_REF_M3D, overridable per-run via params["ipr"]["aof_ref_m3d"].

    Added for twin/calibrate.py (26 Sep 2026): the cold-well absolute-open-flow
    rate is one of the biggest uncertain constants in the twin (rev 5's own
    CHANGELOG: 0.60 -> 0.46 by hand-tuning against a single BGW-8 uplift
    ratio) and is exactly the kind of thing per-well cycle records should
    recalibrate. Same additive-override pattern as
    `twin.thermal.bl_delta_factor`: falls back to the module constant so
    every existing caller (which passes no "ipr" block) is unaffected.
    """
    ipr_params = params.get("ipr") if isinstance(params, dict) else None
    if ipr_params and ipr_params.get("aof_ref_m3d") is not None:
        return float(ipr_params["aof_ref_m3d"])
    return AOF_REF_M3D


def s_cold(params: dict) -> float:
    """Cold-well damage skin, overridable via params["ipr"]["s_cold"] (rev 10).

    Falls back to the module constant S_COLD, read at call time so a
    monkeypatch of the module constant still works for params trees that do
    not carry the key.
    """
    ipr_params = params.get("ipr") if isinstance(params, dict) else None
    if ipr_params and ipr_params.get("s_cold") is not None:
        return float(ipr_params["s_cold"])
    return S_COLD


def cold_mobility_factor(params: dict) -> float:
    """Darcy mobility of the cold reservoir oil relative to the AOF reference.

    = MU_AOF_REF_CP / fluid.mu_ref_cP (rev 10). Exactly 1.0 at the shipped
    11,500 cP, so the reference cold rate (0.447 m3/d) is unchanged; a
    15,000 cP oil is 0.77x as productive cold and an 8,000 cP oil 1.44x.
    `fluid.mu_ref_cP` is taken as the cold in-situ viscosity because T_ref_C
    equals the reservoir temperature (50 C) and composite_uplift already uses
    it as the cold-annulus viscosity -- one cold viscosity, used consistently.
    """
    mu_res = float(params["fluid"]["mu_ref_cP"])
    return MU_AOF_REF_CP / max(mu_res, 1e-9)


def composite_uplift(mu_hot_cP: float, r_h_m: float, T_avg_C: float, params: dict) -> float:
    """Boberg-Lantz composite-radial productivity uplift over the cold well.

    Args:
        mu_hot_cP: viscosity in the heated annulus (at T_avg_C).
        r_h_m: heated-zone radius (m). 0 or absent => unstimulated => 1.0.
        T_avg_C: average heated-zone temperature, used only for skin removal.
        params: field_params.json tree.

    Returns:
        uplift >= 1.0, capped at MAX_UPLIFT.
    """
    res = params["reservoir"]
    fluid = params["fluid"]
    r_e = res.get("drainage_radius_m", 100.0)
    r_w = res.get("well_radius_m", 0.1)
    mu_c = fluid["mu_ref_cP"]

    r_h = min(max(r_h_m, r_w * 1.01), r_e * 0.99)
    mu_h = max(mu_hot_cP, 1e-9)

    # Skin is removed in proportion to how hot the near-well rock is.
    T0 = res["T_initial_C"]
    # rev 11: the zone's steam temperature is T_sat(P_sandface) (thermal.py);
    # "legacy_T" returns steam.T_injection_C as before.
    Ts = thermal.zone_steam_temperature_C(params)
    span = max(Ts - T0, 1e-9)
    f = min(max((T_avg_C - T0) / span, 0.0), 1.0)
    skin0 = s_cold(params)
    s = skin0 * (1.0 - f)

    hot = mu_c * math.log(r_e / r_h) + mu_h * (math.log(r_h / r_w) + s)
    cold = mu_c * (math.log(r_e / r_w) + skin0)
    if hot <= 0.0:
        return MAX_UPLIFT
    return min(max(cold / hot, 1.0), MAX_UPLIFT)


def oil_rate_m3d(P_res_kPa: float, P_wf_kPa: float, mu_cP: float, params: dict) -> float:
    """Vogel IPR oil rate (m3/d) with a composite-radial productivity index.

    Args:
        P_res_kPa: current (near-well) reservoir pressure. Live: q_max is
            linear in it (Vogel's q_max = J*P_res/1.8).
        P_wf_kPa: flowing bottomhole pressure (pump intake condition).
        mu_cP: in-situ oil viscosity in the HEATED annulus (centipoise), e.g.
            from viscosity.mu_cP at the current heated-zone temperature.
        params: field_params.json tree, optionally extended by cycle.py with
            "heated_radius_m" and "T_avg_C" (same shallow-copy pattern as
            "steam_t"). Absent => the well is treated as unstimulated
            (uplift = 1.0), which is exactly the cold-well reference case.

    Returns:
        Oil rate in m3/d, clipped to >= 0.
    """
    if P_res_kPa <= 0.0:
        return 0.0

    pr_ratio = min(max(P_wf_kPa / P_res_kPa, 0.0), 1.0)
    vogel_shape = max(1.0 - 0.2 * pr_ratio - 0.8 * pr_ratio ** 2, 0.0)

    r_h = params.get("heated_radius_m", 0.0)
    T_avg = params.get("T_avg_C", params["reservoir"]["T_initial_C"])
    uplift = composite_uplift(mu_cP, r_h, T_avg, params)

    # rev 10: cold productivity scales with Darcy mobility (MU_AOF_REF_CP /
    # mu_ref_cP); the composite uplift then multiplies that cold well.
    q_max = (aof_ref_m3d(params) * cold_mobility_factor(params) * uplift
             * (P_res_kPa / P_CAL_KPA))
    return max(q_max * vogel_shape, 0.0)
