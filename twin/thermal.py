"""thermal.py -- heated-zone growth, wellbore delivery and Boberg-Lantz cooldown.

Three source models, in the order they are applied through a CSS cycle:

1. **Wellbore heat loss and downhole quality (T1-H).** Steam bought at the
   surface is not heat delivered at the sand face. At Baghewala's ~1,150 m the
   loss is a first-order term, not a correction: Ramey's method predicts ~45 %
   heat loss at 4,000 ft and a refined cement-sheath model ~31 %; uninsulated
   casing loses >25 % of energy input; and even WITH vacuum-insulated tubing
   (which OIL actually runs at Baghewala) published work shows downhole quality
   falling to 20-40 % from an 80 % wellhead quality.
   SOURCE: css_thermal_eor_deep_dive.md sections 2.3/2.4 (academia.edu/73339013;
   sciencedirect S0920410513002477; oil-india.com). Parameters live in
   `field_params.json` under "wellbore" so they are visible and arguable.
   rev 5: the heat delivered per kg is SENSIBLE + sandface-quality LATENT
   (`sandface_enthalpy_J_per_kg`); the tubing loss enters once, through the
   sandface quality, not a second time as a (1 - loss) multiplier.

2. **Marx & Langenheim (1959) heated-zone growth during injection.**
   Marx, C.M. and Langenheim, R.H., "Reservoir Heating by Hot Fluid Injection",
   Petroleum Transactions AIME, 216 (1959), 312-315:

       F(t_D)   = exp(t_D) * erfc(sqrt(t_D)) + 2*sqrt(t_D/pi) - 1
       E_h(t_D) = F(t_D) / t_D        (fraction of injected heat retained)

   with t_D = 4*alpha*t/h^2. The retained heat divided by rock heat capacity
   and (T_s - T_R) gives a swept volume, hence a heated-zone RADIUS. Under
   Marx-Langenheim that zone is (approximately) isothermal at the steam
   temperature -- which is why this module no longer blends the zone against
   an invented drainage disc (see the DELETED note below).

3. **Boberg & Lantz (1966) average heated-zone temperature after injection
   stops (T1-B),** replacing the previous invented `COOLDOWN_TAU_DAYS = 20`
   exponential:

       T_avg(t) = T_R + (T_s - T_R) * [ f_VD(t) * f_HD(t) * (1 - delta) - delta ]

   Boberg, D.L. and Lantz, R.B., "Calculation of the Production Rate of a
   Thermally Stimulated Well", JPT 18(12), 1966. `f_VD` and `f_HD` are the
   vertical and horizontal conduction-loss functions and `delta` is the
   energy-removed term (heat carried out of the zone by produced fluid), which
   is what couples HOW HARD YOU PRODUCE to HOW FAST THE WELL COOLS.
   SOURCE: css_thermal_eor_deep_dive.md sections 2.2 / 4-paper-1.

   **Stated uncertainty band:** the published Boberg-Lantz-vs-numerical
   temperature gap reaches **42 % over 300 days** (SOURCE: "Temperature profile
   estimation: a study on the Boberg and Lantz steam stimulation model",
   *Petroleum* (Elsevier) 2018, S2405656118301755). `BL_UNCERTAINTY_FRAC`
   below carries that number so the deck and the API can quote one constant.

   rev 5: `f_HD` is now the exact volume-average of a CYLINDER of radius r_h
   (`cylinder_theta`, Carslaw & Jaeger closed form); `f_VD` stays the exact
   slab of thickness h (`slab_theta`).

   Physics v3 (26 Sep 2026): `delta` is Boberg & Lantz's f_pD = (1/2Q) *
   integral(Qdot_p dt) (PEH Vol. V Eqs. 15.70/15.73/15.74), Q = injected heat
   remaining. The 1/2 (`BL_DELTA_FACTOR`) is sourced and energy-conservation
   fixed; Qdot_p is computed stream-by-stream by `produced_heat_J_per_day`.
   See docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md.

   Boberg-Lantz also assumes a **constant heated radius** once injection
   stops, which is exactly what this module already did -- we are accidentally
   Boberg-Lantz-compliant on that point.

DELETED in T1-A: `DRAINAGE_RADIUS_M = 8.0`. It was never a drainage radius (a
real single-well drainage radius here is 50-150 m); it was a saturation knob
retuned from 10 m to 8 m purely to move the SOR minimum back inside the tested
range (params/CHANGELOG.md). The real drainage radius now lives in
`reservoir.drainage_radius_m` (100 m) and is used by `ipr.py`'s composite-radial
productivity index, where it belongs.
"""
from __future__ import annotations

import math
import warnings

from scipy.special import i0e as _i0e, i1e as _i1e

# Published Boberg-Lantz vs numerical-simulator temperature gap over 300 days.
# SOURCE: Petroleum (Elsevier) 2018, S2405656118301755. [CONFIRMED]
# Shipped as the twin's stated uncertainty band -- never quote a bare number.
BL_UNCERTAINTY_FRAC = 0.42

# SOURCED (physics v3, 26 Sep 2026): the 1/2 in Boberg & Lantz's own definition
# of the produced-heat term,
#     delta = f_pD = (1 / 2Q) * integral_0^t Qdot_p dt,
#     Q = injected heat remaining in the reservoir (end of injection),
# Petroleum Engineering Handbook Vol. V ch. 15, Eqs. 15.70 / 15.73 + nomenclature
# (PetroWiki "PEH:Thermal Recovery by Steam Injection", reproducing Boberg & Lantz
# 1966, JPT 18(12) 1613-1623). It is NOT a tunable: with no conduction
# (f_VD = f_HD = 1) theta = 1 - 2*delta, and energy conservation (zone heat =
# Q - Q_produced) requires theta = 1 - Q_produced/Q, i.e. exactly 1/2. A value
# of 1.0 removes twice the heat the produced fluid actually carries.
# Full write-up: docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md.
# delta itself is COMPUTED every produce day from the simulated oil + water
# rates (produced_heat_J_per_day below, PEH Eq. 15.74).
BL_DELTA_FACTOR = 0.5


def bl_delta_factor(params: dict) -> float:
    """BL_DELTA_FACTOR, overridable per-run via params["thermal"]["bl_delta_factor"].

    Added for ml/uq.py (Monte Carlo uncertainty quantification, 26 Sep 2026),
    when the 1/2 was still unverified. Physics v3 sourced it (see the constant
    above): it is fixed by energy conservation, so the override is kept ONLY for
    backward compatibility of ml/uq.py and for sensitivity illustration. The
    physical uncertainty in delta lives in the produced WATER rate
    (`fluid.water_cut`), which Boberg & Lantz say must be supplied from outside
    the model -- vary that, not this.
    """
    thermal_params = params.get("thermal") if isinstance(params, dict) else None
    if thermal_params and thermal_params.get("bl_delta_factor") is not None:
        return float(thermal_params["bl_delta_factor"])
    return BL_DELTA_FACTOR


# --- PEH Eq. 15.74: heat carried out of the zone by produced fluids -----------
# Saturated-liquid enthalpy h_f(T) of water, kJ/kg. SOURCE: standard steam
# tables (IAPWS-IF97 saturation table values, rounded). [CONFIRMED] Linear
# interpolation between 25 degC nodes is within ~0.2 % of the table.
_HF_TABLE_C = (0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0,
               225.0, 250.0, 275.0, 300.0, 325.0)
_HF_TABLE_KJKG = (0.0, 104.8, 209.3, 314.0, 419.1, 525.0, 632.2, 741.2, 852.3,
                  966.8, 1085.8, 1210.9, 1344.8, 1493.3)
# Density of produced water at stock-tank conditions (kg per stock-tank m3).
# Boberg-Lantz rates are stock-tank rates. [DEFINITION, ~15 degC fresh water]
RHO_W_STOCK_KGM3 = 1000.0


def water_enthalpy_kJkg(T_C: float) -> float:
    """Saturated-liquid water enthalpy h_f(T) (kJ/kg) from the steam table above."""
    xs, ys = _HF_TABLE_C, _HF_TABLE_KJKG
    if T_C <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if T_C <= xs[i]:
            w = (T_C - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + w * (ys[i] - ys[i - 1])
    # beyond the table: extrapolate the last segment (never reached at T_s = 290 C)
    return ys[-1] + (T_C - xs[-1]) * (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])


def oil_heat_capacity_Jm3K(T_mean_C: float, api_gravity: float) -> float:
    """Volumetric heat capacity M_o of stock-tank oil (J per stock-tank m3 per K).

    rho_o from API gravity (SG = 141.5/(131.5 + API)); specific heat from
    Gambill's correlation c_o [Btu/lb F] = (0.388 + 0.00045 T_F)/sqrt(SG)
    (Gambill 1957, Chem. Eng. 64; the correlation Prats, SPE Monograph 7, and
    PEH ch. 15 use for crude oil), i.e. c_o [kJ/kg K] = (1.685 + 0.00339 T_C)/sqrt(SG).
    Evaluated at the MEAN of T_R and T_avg because c_o is linear in T, so
    c_o(T_mean) * (T_avg - T_R) is the exact enthalpy rise.
    """
    sg = 141.5 / (131.5 + api_gravity)
    c_o_kJkgK = (1.685 + 0.00339 * T_mean_C) / math.sqrt(sg)
    return 1000.0 * sg * c_o_kJkgK * 1000.0


def produced_heat_J_per_day(q_oil_m3d: float, q_water_m3d: float, T_avg_C: float,
                            params: dict) -> float:
    """Boberg-Lantz produced-heat rate Qdot_p (J/day), PEH Eq. 15.74:

        Qdot_p = [ q_o M_o + q_wh M_w + q_s M_w + q_s rho_w h_fv / dT + q_gh M_g ] * dT,
        dT = T_avg - T_R  (fluids leave the zone at the zone's average temperature)

    implemented for the two streams the twin simulates: oil (M_o from
    oil_heat_capacity_Jm3K) and hot water (enthalpy rise from the steam table,
    so M_w*dT = rho_w * [h_f(T_avg) - h_f(T_R)] exactly).
    [ASSUMPTION] steam (q_s) and gas (q_gh) terms are zero. Boberg & Lantz: "the
    model does not predict steam, gas, or water producing rates, which must be
    estimated from some other source" (PEH ch. 15). rev 11: the water rate
    passed in is the day's simulated produced water (condensate flowback +
    formation water, twin/cycle.py). Produced free steam is still not
    modelled: the zone is at T_avg well below T_sat(P_res) through production,
    so steam flashing happens in the tubing, after the fluid has left the zone
    (counted here at T_avg).
    Replaces rev 4/5's lumped `cycle.CP_LIQUID_JM3K = 4.0e6` liquid blend.
    """
    T_R = params["reservoir"]["T_initial_C"]
    dT = max(T_avg_C - T_R, 0.0)
    if dT <= 0.0:
        return 0.0
    M_o = oil_heat_capacity_Jm3K(0.5 * (T_avg_C + T_R), params["fluid"]["api_gravity"])
    dh_w_J_per_m3 = RHO_W_STOCK_KGM3 * 1000.0 * (water_enthalpy_kJkg(T_avg_C) - water_enthalpy_kJkg(T_R))
    return max(q_oil_m3d, 0.0) * M_o * dT + max(q_water_m3d, 0.0) * dh_w_J_per_m3

# --- rev 10: steam-state consistency (IAPWS-IF97 region 4) -------------------
# Saturation line of water, IAPWS-IF97 (Wagner et al. 2000, J. Eng. Gas
# Turbines Power 122:150), region-4 basic equation and its backward form.
# [SOURCED - international standard]. Valid 273.15 K - 647.096 K.
_IF97_N = (0.11670521452767e4, -0.72421316703206e6, -0.17073846940092e2,
           0.12020824702470e5, -0.32325550322333e7, 0.14915108613530e2,
           -0.48232657361591e4, 0.40511340542057e6, -0.23855557567849,
           0.65017534844798e3)


def p_sat_kPa(T_C: float) -> float:
    """Saturation pressure of water (kPa, absolute) at T_C (IAPWS-IF97 Eq. 30)."""
    n = _IF97_N
    T = min(max(T_C + 273.15, 273.15), 647.096)
    th = T + n[8] / (T - n[9])
    A = th * th + n[0] * th + n[1]
    B = n[2] * th * th + n[3] * th + n[4]
    C = n[5] * th * th + n[6] * th + n[7]
    p_MPa = (2.0 * C / (-B + math.sqrt(B * B - 4.0 * A * C))) ** 4
    return p_MPa * 1000.0


def T_sat_C(p_kPa: float) -> float:
    """Saturation temperature of water (degC) at p_kPa absolute (IAPWS-IF97 Eq. 31)."""
    n = _IF97_N
    p = min(max(p_kPa / 1000.0, 611.213e-6), 22.064)
    b = p ** 0.25
    E = b * b + n[2] * b + n[5]
    F = n[0] * b * b + n[3] * b + n[6]
    G = n[1] * b * b + n[4] * b + n[7]
    D = 2.0 * G / (-F - math.sqrt(F * F - 4.0 * E * G))
    T = (n[9] + D - math.sqrt((n[9] + D) ** 2 - 4.0 * (n[8] + n[9] * D))) / 2.0
    return T - 273.15


KGF_CM2_TO_KPA = 98.0665  # DEFINITION
ATM_KPA = 101.325         # DEFINITION (gauge -> absolute)

# --- rev 11: saturated-steam properties (IAPWS-IF97) ---------------------------
# Saturated liquid / vapour specific volume and enthalpy of water every 10 degC,
# 200-350 degC (1.55-16.5 MPa, the whole CSS injection window). Values are
# IAPWS-IF97 (Wagner et al. 2000), generated with the reference implementation
# `iapws` 1.5.5 (IAPWS97(T, x=0/1)) and rounded; they agree with the Cengel /
# Rogers-Mayhew saturation tables to the printed digits. [SOURCED - standard]
# Columns: T_C, v_f (m3/kg), v_g (m3/kg), h_f (kJ/kg), h_fg (kJ/kg).
_SAT_TABLE = (
    (200.0, 0.001157, 0.127222, 852.4, 1939.7),
    (210.0, 0.001173, 0.104302, 897.7, 1899.6),
    (220.0, 0.001190, 0.086101, 943.6, 1857.4),
    (230.0, 0.001209, 0.071510, 990.2, 1812.8),
    (240.0, 0.001229, 0.059710, 1037.5, 1765.5),
    (250.0, 0.001252, 0.050087, 1085.7, 1715.3),
    (260.0, 0.001276, 0.042175, 1134.8, 1661.8),
    (270.0, 0.001303, 0.035622, 1185.1, 1604.6),
    (280.0, 0.001333, 0.030154, 1236.7, 1543.2),
    (290.0, 0.001366, 0.025557, 1289.8, 1476.8),
    (300.0, 0.001404, 0.021663, 1344.8, 1404.8),
    (310.0, 0.001448, 0.018339, 1402.0, 1325.9),
    (320.0, 0.001499, 0.015476, 1462.1, 1238.6),
    (330.0, 0.001561, 0.012984, 1525.7, 1140.5),
    (340.0, 0.001638, 0.010784, 1594.4, 1027.6),
    (350.0, 0.001740, 0.008801, 1670.9, 892.7),
)

# rev 11: the pressure at which the CONFIRMED fuel intensity (71 kg HSD per t
# steam, BGW-08: 220 kg/h HSD -> 3,100 kg/h steam) was measured -- the middle of
# the same job's 85-97 kgf/cm2 wellhead range. Fuel per tonne is scaled by the
# wellhead enthalpy at the chosen pressure over the enthalpy at this one.
FUEL_REF_P_WELLHEAD_KGF_CM2 = 91.0
# [ASSUMPTION] boiler feedwater temperature for the fuel-enthalpy ratio (degC).
# Only the RATIO of two wellhead enthalpies uses it; 20-40 degC moves the ratio
# by < 0.01 %.
FEEDWATER_T_C = 30.0
STEAM_STATE_MODELS = ("saturated_P", "legacy_T")


def sat_props_T(T_C: float) -> dict:
    """Saturated water/steam properties at T_C (IF97 table, 200-350 degC).

    Linear interpolation for v_f, h_f, h_fg; log-linear for v_g (which is
    close to exponential in T). Error vs full IF97 <= 0.36 % on every column
    inside the table, < 0.1 % over 280-320 degC (checked at the 5 degC
    mid-points with `iapws`).
    Clamped to the table ends outside 200-350 degC (never reached: the
    sandface state spans ~300-320 degC)."""
    tab = _SAT_TABLE
    T = min(max(float(T_C), tab[0][0]), tab[-1][0])
    for i in range(1, len(tab)):
        if T <= tab[i][0]:
            a, b = tab[i - 1], tab[i]
            w = (T - a[0]) / (b[0] - a[0])
            break
    lin = lambda k: a[k] + w * (b[k] - a[k])  # noqa: E731
    v_g = math.exp(math.log(a[2]) + w * (math.log(b[2]) - math.log(a[2])))
    return {"T_C": T, "v_f": lin(1), "v_g": v_g, "h_f_kJkg": lin(3), "h_fg_kJkg": lin(4),
            "rho_f": 1.0 / lin(1), "rho_g": 1.0 / v_g}


def sat_props_P(p_kPa: float) -> dict:
    """Saturated properties at absolute pressure p_kPa (T_sat from IF97 Eq. 31)."""
    out = sat_props_T(T_sat_C(p_kPa))
    out["p_kPa"] = float(p_kPa)
    return out


def steam_state_model(params: dict) -> str:
    """`steam.state_model`: "saturated_P" (rev 11 default) or "legacy_T" (rev <= 10)."""
    m = str((params.get("steam") or {}).get("state_model") or "legacy_T")
    if m not in STEAM_STATE_MODELS:
        raise ValueError(f"steam.state_model must be one of {STEAM_STATE_MODELS}, got {m!r}")
    return m


def wellhead_pressure_kgf_cm2(params: dict) -> float:
    """Injection (wellhead) pressure control, kgf/cm2 gauge (rev 11 lever).

    `steam.P_wellhead_kgf_cm2` [CONTROL; CONFIRMED range 85-97 from the OIL
    deck, BGW-08]; falls back to the middle of `wellhead_pressure_kgf_cm2_g`."""
    steam = params.get("steam", {})
    v = steam.get("P_wellhead_kgf_cm2")
    if v is not None:
        return float(v)
    rng = steam.get("wellhead_pressure_kgf_cm2_g") or [FUEL_REF_P_WELLHEAD_KGF_CM2] * 2
    if not isinstance(rng, (list, tuple)):
        rng = [rng, rng]
    return 0.5 * (float(rng[0]) + float(rng[-1]))


def _wet_enthalpy_kJkg(p_kPa: float, x: float) -> float:
    s = sat_props_P(p_kPa)
    return s["h_f_kJkg"] + x * s["h_fg_kJkg"]


def steam_state(params: dict, p_wellhead_kgf_cm2: float | None = None) -> dict:
    """Injected-steam state from the wellhead PRESSURE (rev 11, "saturated_P").

    Physics (all published; no fitted constant):
      * Wellhead: wet steam at P_wh is AT saturation, T_wh = T_sat(P_wh)
        (IAPWS-IF97); quality x_wh = `steam.quality` (CONFIRMED 60-70 %).
      * Tubing: sandface pressure = wellhead + hydrostatic head of the two-
        phase column, P_sf = P_wh + rho_m g D. rho_m is the HOMOGENEOUS
        (no-slip) mixture density, 1/rho_m = x/rho_g + (1 - x)/rho_f, i.e. the
        quality-weighted specific volume, at the column-average quality
        (x_wh + x_sf)/2 and column-average pressure (fixed-point, 4 passes).
        No-slip is an upper bound on downward-flow holdup; tubing friction
        (~0.1-0.2 MPa at 74 t/d in 2-7/8 in tubing) is NEGLECTED -- both
        biases make P_sf slightly high, stated.
      * Sandface quality degrades with the wellbore loss "as before":
        x_sf = x_wh * `wellbore.quality_at_sandface_frac_of_wellhead`.
      * Sandface temperature T_sf = T_sat(P_sf). This is the heated-zone
        (Marx-Langenheim / Boberg-Lantz) steam temperature.
      * Heat delivered per kg relative to the reservoir:
            h_del = x_sf * h_fg(P_sf) + h_f(P_sf) - h_f(T_R)
        (Prats, SPE Monograph 7, ch. 5; the rev-5 C_w*(T_s - T_R) + x*L_v form
        with both terms taken from the steam table at the sandface state).
      * Fuel: the steam generator sets the pressure (no separate compression
        cost; feed-pump work is ~0.1 kJ/kg per bar, < 0.1 % of the enthalpy).
        Fuel per tonne scales with the wellhead enthalpy over feedwater,
        relative to FUEL_REF_P_WELLHEAD_KGF_CM2 (`fuel_factor`, +/-0.2 % over
        85-97 kgf/cm2 at 65 % quality -- h_f rises as h_fg falls).
    In "legacy_T" mode the rev-10 numbers are returned (T_s = T_injection_C,
    h_del = C_w*(T_s - T_R) + x_sf*latent_heat_Jkg, fuel_factor 1).
    """
    steam = params["steam"]
    res = params["reservoir"]
    T_R = float(res["T_initial_C"])
    depth = float(res["depth_m"])
    _, x_sf = wellbore_delivery(params)
    x_wh = float(steam["quality"])
    model = steam_state_model(params)
    if model == "legacy_T":
        T_s = float(steam["T_injection_C"])
        h_del = CW_LIQUID_JKGK * max(T_s - T_R, 0.0) + x_sf * float(steam["latent_heat_Jkg"])
        return {"model": model, "T_sandface_C": T_s, "T_wellhead_C": T_s, "x_wellhead": x_wh,
                "x_sandface": x_sf, "h_delivered_J_per_kg": h_del, "fuel_factor": 1.0,
                "P_wellhead_kgf_cm2": None, "P_wellhead_kPa": None, "P_sandface_kPa": None,
                "rho_column_kgm3": None, "dP_column_kPa": None}
    p_g = wellhead_pressure_kgf_cm2(params) if p_wellhead_kgf_cm2 is None else float(p_wellhead_kgf_cm2)
    P_wh = p_g * KGF_CM2_TO_KPA + ATM_KPA
    x_mean = 0.5 * (x_wh + x_sf)
    P_sf = P_wh
    rho_m = 0.0
    for _ in range(4):
        s = sat_props_P(0.5 * (P_wh + P_sf))
        rho_m = 1.0 / (x_mean * s["v_g"] + (1.0 - x_mean) * s["v_f"])
        P_sf = P_wh + rho_m * 9.81 * depth / 1000.0
    sf = sat_props_P(P_sf)
    wh = sat_props_P(P_wh)
    h_del = 1000.0 * (x_sf * sf["h_fg_kJkg"] + sf["h_f_kJkg"] - water_enthalpy_kJkg(T_R))
    h_fw = water_enthalpy_kJkg(FEEDWATER_T_C)
    p_ref = FUEL_REF_P_WELLHEAD_KGF_CM2 * KGF_CM2_TO_KPA + ATM_KPA
    fuel_factor = ((_wet_enthalpy_kJkg(P_wh, x_wh) - h_fw)
                   / (_wet_enthalpy_kJkg(p_ref, x_wh) - h_fw))
    return {"model": model, "P_wellhead_kgf_cm2": p_g, "P_wellhead_kPa": P_wh,
            "T_wellhead_C": wh["T_C"], "x_wellhead": x_wh,
            "rho_column_kgm3": rho_m, "dP_column_kPa": P_sf - P_wh,
            "P_sandface_kPa": P_sf, "T_sandface_C": sf["T_C"], "x_sandface": x_sf,
            "h_fg_sandface_kJkg": sf["h_fg_kJkg"], "h_f_sandface_kJkg": sf["h_f_kJkg"],
            "h_delivered_J_per_kg": h_del,
            "h_wellhead_J_per_kg": 1000.0 * (_wet_enthalpy_kJkg(P_wh, x_wh) - water_enthalpy_kJkg(T_R)),
            "fuel_factor": fuel_factor}


def _cached_state(params: dict) -> dict:
    st = params.get("_steam_state") if isinstance(params, dict) else None
    return st if st is not None else steam_state(params)


def zone_steam_temperature_C(params: dict) -> float:
    """Steam temperature of the heated zone (degC): T_sat(P_sandface) in the
    rev-11 "saturated_P" model, `steam.T_injection_C` in "legacy_T"."""
    return float(_cached_state(params)["T_sandface_C"])


def steam_state_check(params: dict) -> dict:
    """Thermodynamic consistency of the injected-steam state. Never raises.

    rev 11 ("saturated_P", the default): the state is ONE saturated state by
    construction (T = T_sat(P) at wellhead and sandface), so the rev-10 P-T
    warnings cannot arise. What is checked instead:
      1. Injectivity: the sandface pressure must exceed the pre-cycle
         reservoir pressure (`reservoir.P_current_kPa`, else virgin). If not,
         steam cannot enter the formation at this wellhead pressure; the twin
         keeps running (heat delivered as if injected, no pressure recharge)
         and WARNS.
      2. The wellhead pressure lies inside the CONFIRMED 85-97 kgf/cm2 range
         (warning outside it: extrapolation).
      Informational (not a warning): T_wh against the deck's separately
      reported 280-305 degC (T_sat at 97 kgf/cm2 is 308 degC).
    "legacy_T" runs the rev-10 check below unchanged.
    """
    if steam_state_model(params) == "saturated_P":
        st = steam_state(params)
        res = params.get("reservoir", {})
        P_res = res.get("P_current_kPa")
        P_res = float(P_res if P_res is not None else res.get("P_initial_kPa", float("nan")))
        out = {"model": "saturated_P", **{k: v for k, v in st.items() if k != "model"},
               "P_reservoir_kPa": P_res,
               "injection_margin_kPa": st["P_sandface_kPa"] - P_res,
               "warnings": [], "info": []}
        if P_res >= st["P_sandface_kPa"]:
            out["warnings"].append(
                f"Reservoir pressure {P_res / 1000:.2f} MPa >= sandface injection pressure "
                f"{st['P_sandface_kPa'] / 1000:.2f} MPa at {st['P_wellhead_kgf_cm2']:.0f} kgf/cm2 "
                "wellhead: steam cannot enter the formation. The twin runs on with no pressure "
                "recharge (reservoir.P_current_kPa is an ASSUMPTION - top data ask).")
        rng = params.get("steam", {}).get("P_wellhead_range_kgf_cm2") or \
            params.get("steam", {}).get("wellhead_pressure_kgf_cm2_g")
        if rng:
            lo, hi = float(rng[0]), float(rng[-1])
            if not lo - 1e-9 <= st["P_wellhead_kgf_cm2"] <= hi + 1e-9:
                out["warnings"].append(
                    f"Wellhead pressure {st['P_wellhead_kgf_cm2']:.1f} kgf/cm2 is outside the "
                    f"CONFIRMED {lo:.0f}-{hi:.0f} kgf/cm2 range (extrapolation).")
        if st["T_wellhead_C"] > 305.0 + 0.5:
            out["info"].append(
                f"T_sat at {st['P_wellhead_kgf_cm2']:.0f} kgf/cm2 = {st['T_wellhead_C']:.1f} C is "
                "above the deck's separately reported 280-305 C steam temperature.")
        out["consistent"] = not out["warnings"]
        return out
    return _steam_state_check_legacy(params)


def _steam_state_check_legacy(params: dict) -> dict:
    """Thermodynamic consistency of the injected-steam state (rev 10). Never raises.

    Two checks, both against the saturation line (IAPWS-IF97):
      1. Wellhead: `steam.T_injection_C` must not exceed T_sat at the reported
         wellhead pressure (`steam.wellhead_pressure_kgf_cm2_g`; OIL deck
         BGW-08: 85-97 kgf/cm2). Wet steam at that pressure is AT T_sat
         (~298-307 C), so a 290 C "steam" at that pressure is not saturated.
      2. Sandface: to inject at all, bottomhole pressure must exceed the
         reservoir pressure (`reservoir.P_current_kPa`, else the virgin
         `P_initial_kPa`). Saturated steam at T_injection_C exists only up to
         p_sat(T_injection_C) (7.44 MPa at 290 C); above it the sandface fluid
         is subcooled water, so the latent-heat credit x_sf * L_v in
         sandface_enthalpy_J_per_kg has no physical carrier.
    Returns a dict with the numbers and a list of `warnings` (strings). The
    twin keeps running either way: the heat balance uses total enthalpy, so the
    heated VOLUME is unaffected to first order; what is unsupported is the
    phase (steam vs hot water) and therefore the pressure-boost mechanism.
    See docs/model-improvement/TIER1_PROGRESS_LOG.md section 9.
    """
    steam = params.get("steam", {})
    res = params.get("reservoir", {})
    T_inj = float(steam.get("T_injection_C", float("nan")))
    p_sat_Tinj = p_sat_kPa(T_inj)
    P_res = res.get("P_current_kPa")
    P_res = float(P_res if P_res is not None else res.get("P_initial_kPa", float("nan")))
    out = {
        "T_injection_C": T_inj,
        "p_sat_at_T_injection_kPa": p_sat_Tinj,
        "P_reservoir_kPa": P_res,
        "T_sat_at_P_reservoir_C": T_sat_C(P_res),
        "warnings": [],
    }
    whp = steam.get("wellhead_pressure_kgf_cm2_g")
    if whp:
        lo, hi = (float(whp[0]), float(whp[1])) if isinstance(whp, (list, tuple)) else (float(whp), float(whp))
        p_lo = lo * KGF_CM2_TO_KPA + ATM_KPA
        p_hi = hi * KGF_CM2_TO_KPA + ATM_KPA
        out["wellhead_pressure_kPa_abs"] = [p_lo, p_hi]
        out["T_sat_at_wellhead_C"] = [T_sat_C(p_lo), T_sat_C(p_hi)]
        if T_inj < T_sat_C(p_lo) - 1.0:
            out["warnings"].append(
                f"steam.T_injection_C = {T_inj:.0f} C is below T_sat = {T_sat_C(p_lo):.0f}-"
                f"{T_sat_C(p_hi):.0f} C at the reported wellhead pressure {lo:.0f}-{hi:.0f} "
                "kgf/cm2: wet steam at that pressure would be at T_sat, so T and P are not one "
                "saturated state.")
        elif T_inj > T_sat_C(p_hi) + 1.0:
            out["warnings"].append(
                f"steam.T_injection_C = {T_inj:.0f} C exceeds T_sat at the wellhead pressure "
                "(superheated): the quality-based enthalpy in this module does not apply.")
    if P_res >= p_sat_Tinj:
        out["warnings"].append(
            f"Reservoir pressure {P_res / 1000:.2f} MPa >= p_sat({T_inj:.0f} C) = "
            f"{p_sat_Tinj / 1000:.2f} MPa: injection needs BHP > P_res, where {T_inj:.0f} C "
            "water cannot be steam. The sandface fluid is hot (subcooled) water; the "
            "latent-heat credit and the pressure-boost term have no physical carrier "
            "unless the near-well region is depleted below "
            f"{p_sat_Tinj / 1000:.2f} MPa (reservoir.P_current_kPa, UNKNOWN - data ask).")
    out["consistent"] = not out["warnings"]
    return out


_WARNED_STEAM_STATES: set = set()


def warn_steam_state(params: dict) -> dict:
    """steam_state_check + one UserWarning per distinct state per process."""
    chk = steam_state_check(params)
    if chk["warnings"]:
        key = (chk.get("model", "legacy_T"), round(chk.get("T_injection_C", chk.get("T_sandface_C", 0.0)), 1),
               round(chk.get("P_wellhead_kgf_cm2") or 0.0, 1), round(chk["P_reservoir_kPa"], -2))
        if key not in _WARNED_STEAM_STATES:
            _WARNED_STEAM_STATES.add(key)
            warnings.warn("twin steam-state consistency: " + " | ".join(chk["warnings"]),
                          UserWarning, stacklevel=3)
    return chk


# Mean specific heat of liquid water between the reservoir temperature and the
# steam temperature, J/(kg K). SOURCE: saturated steam tables,
# [h_f(290 degC) - h_f(50 degC)] / 240 K = (1290.0 - 209.3) kJ/kg / 240 K
# = 4.50 kJ/(kg K). [CALCULATED] Used for the SENSIBLE heat the injected
# condensate carries into the formation (rev 5, see _retained_heat_J_at).
CW_LIQUID_JKGK = 4500.0


def _heat_loss_efficiency(t_dimensionless: float) -> float:
    """Marx-Langenheim thermal efficiency E_h(t_D) = F(t_D)/t_D.

    E_h -> 1 as t_D -> 0 (all injected heat stays in the zone); E_h falls
    as t_D grows (more heat lost by conduction to over/underburden).
    """
    if t_dimensionless < 1e-9:
        # ASSUMPTION: negligible heat loss in the first instants of injection.
        return 1.0
    sqrt_td = math.sqrt(t_dimensionless)
    f_td = math.exp(t_dimensionless) * math.erfc(sqrt_td) + 2.0 * math.sqrt(t_dimensionless / math.pi) - 1.0
    return f_td / t_dimensionless


def wellbore_delivery(params: dict) -> tuple[float, float]:
    """(heat_loss_fraction, downhole_steam_quality) for the injection string.

    T1-H. `wellbore.heat_loss_frac_per_1000m` is depth-scaled and capped at
    0.6; `wellbore.quality_at_sandface_frac_of_wellhead` degrades the wellhead
    quality. rev 5: only x_down enters the heat balance; the loss fraction is
    reported for transparency and is set to the value x_down implies
    (tests/test_thermal.py checks they agree within 10 %). If the "wellbore" block is absent the function degrades to the
    pre-T1-H behaviour (no loss, full wellhead quality) so old params trees
    still run.
    """
    steam = params["steam"]
    wb = params.get("wellbore")
    if not wb:
        return 0.0, float(steam["quality"])
    depth_m = params["reservoir"]["depth_m"]
    loss = min(wb.get("heat_loss_frac_per_1000m", 0.0) * depth_m / 1000.0, 0.6)
    x_down = steam["quality"] * wb.get("quality_at_sandface_frac_of_wellhead", 1.0)
    return loss, x_down


def _alpha_m2_per_s(params: dict) -> float:
    """Thermal diffusivity.

    ASSUMPTION: over/underburden diffusivity approximated by the reservoir
    rock's own k/(rho*cp) -- field_params.json carries no separate caprock
    thermal properties.
    """
    reservoir = params["reservoir"]
    return reservoir["k_thermal_W_mK"] / reservoir["rock_heat_capacity_Jm3K"]


def injection_end_day(params: dict) -> float:
    """Day on which injection of `params["steam_t"]` tonnes finishes."""
    return params["steam_t"] / params["steam"]["injection_rate_tpd"]


def sandface_enthalpy_J_per_kg(params: dict) -> float:
    """Heat delivered to the formation per kg of steam injected (J/kg, rel. to T_R).

    Marx & Langenheim's heat-injection rate is  w_s * [ C_w*(T_s - T_R) + f_sd * L_v ]
    (Marx & Langenheim 1959; Prats, *Thermal Recovery*, SPE Monograph 7, ch. 5):
    the SENSIBLE heat of the hot liquid plus the LATENT heat of the vapour
    fraction that is still steam at the sand face.

    rev 5 (26 Sep 2026) corrected two errors in the T1-H version, which credited
    only `x_down * L_v * (1 - loss)` = 443 kJ/kg:
      1. The sensible term C_w*(T_s - T_R) ~= 1,081 kJ/kg was omitted. At 36 %
         sandface quality it is ~2/3 of the heat actually delivered.
      2. The wellbore loss was applied twice: condensation in the tubing IS the
         reason sandface quality is below wellhead quality, so multiplying the
         degraded-quality enthalpy by (1 - loss) again removed the same joules
         a second time. `wellbore.heat_loss_frac_per_1000m` is now reported by
         wellbore_delivery() for transparency but not multiplied in; its value
         is set to the loss that the sandface-quality ratio implies (see
         params/CHANGELOG.md rev 5).
    """
    # rev 11: steam_state() computes it -- from the IF97 sandface state in the
    # default "saturated_P" model, by the rev-5 formula below in "legacy_T".
    return float(_cached_state(params)["h_delivered_J_per_kg"])


def implied_wellbore_loss_frac(params: dict) -> float:
    """Fraction of wellhead enthalpy (rel. to T_R) lost in the tubing, as implied
    by the wellhead -> sandface quality drop. Used by tests to check that the
    two wellbore params describe the same joules."""
    st = _cached_state(params)
    if st["model"] == "legacy_T":
        steam = params["steam"]
        dT = max(steam["T_injection_C"] - params["reservoir"]["T_initial_C"], 0.0)
        h_wh = CW_LIQUID_JKGK * dT + steam["quality"] * steam["latent_heat_Jkg"]
    else:
        # rev 11: wellhead wet-steam enthalpy (IF97) relative to T_R, plus the
        # potential energy g*D the fluid gains on the way down.
        h_wh = st["h_wellhead_J_per_kg"] + 9.81 * params["reservoir"]["depth_m"]
    return 1.0 - sandface_enthalpy_J_per_kg(params) / h_wh


def _retained_heat_J_at(t_growth_days: float, params: dict) -> float:
    """Marx-Langenheim heat retained in the zone after t_growth_days of injection.

    Injected heat = mass * sandface_enthalpy_J_per_kg (sensible + downhole-quality
    latent; T1-H wellbore degradation enters through the sandface quality).
    """
    steam = params["steam"]
    reservoir = params["reservoir"]
    if t_growth_days <= 0.0:
        return 0.0
    alpha = _alpha_m2_per_s(params)
    h = reservoir["thickness_m"]
    t_growth_sec = t_growth_days * 86400.0
    t_dimensionless = 4.0 * alpha * t_growth_sec / (h ** 2)
    e_h = _heat_loss_efficiency(t_dimensionless)

    mass_injected_kg = steam["injection_rate_tpd"] * 1000.0 * t_growth_days
    q_injected_J = mass_injected_kg * sandface_enthalpy_J_per_kg(params)
    return q_injected_J * e_h


def retained_heat_J(params: dict) -> float:
    """Heat retained in the heated zone at the END of injection (J).

    This is the denominator of Boberg & Lantz's energy-removed term `delta`;
    cycle.py divides its running produced-fluid enthalpy total by it.
    """
    return _retained_heat_J_at(injection_end_day(params), params)


def _heated_radius_m(q_retained_J: float, params: dict) -> float:
    reservoir = params["reservoir"]
    delta_T = zone_steam_temperature_C(params) - reservoir["T_initial_C"]
    if q_retained_J <= 0.0 or delta_T <= 0.0:
        return 0.0
    heated_volume_m3 = q_retained_J / (reservoir["rock_heat_capacity_Jm3K"] * delta_T)
    heated_area_m2 = heated_volume_m3 / reservoir["thickness_m"]
    return math.sqrt(max(heated_area_m2, 0.0) / math.pi)


def slab_theta(L_m: float, alpha_m2_per_day: float, t_days: float) -> float:
    """Volume-averaged dimensionless temperature of a slab of thickness L.

    For a slab of thickness L initially at T_s embedded in an infinite medium
    at T_R with the same diffusivity, the volume-averaged dimensionless
    temperature is exactly

        f(L, t) = erf(X) - (1 - exp(-X^2)) / (X * sqrt(pi)),   X = L / (2*sqrt(alpha*t))

    (derives from 0.5*[erf((a-z)/beta) + erf((a+z)/beta)] integrated over the
    slab; f -> 1 as t -> 0 and f -> 0 as t -> inf). This is the closed form the
    Boberg-Lantz f_VD / f_HD charts encode, so no chart digitisation is needed.
    """
    if t_days <= 0.0 or L_m <= 0.0 or alpha_m2_per_day <= 0.0:
        return 1.0
    X = L_m / (2.0 * math.sqrt(alpha_m2_per_day * t_days))
    if X > 30.0:
        return 1.0
    if X < 1e-9:
        return 0.0
    return math.erf(X) - (1.0 - math.exp(-X * X)) / (X * math.sqrt(math.pi))


def cylinder_theta(R_m: float, alpha_m2_per_day: float, t_days: float) -> float:
    """Volume-averaged dimensionless temperature of an infinite cylinder of radius R.

    Cylinder initially at T_s inside r < R, surrounding medium at T_R, same
    diffusivity (the Boberg-Lantz horizontal-loss geometry). Exact closed form
    (Carslaw & Jaeger, *Conduction of Heat in Solids*, 2nd ed., 1959, the
    instantaneous cylindrical source integrated over r < R):

        f_HD = 1 - exp(-x) * [ I0(x) + I1(x) ],     x = R^2 / (2*alpha*t)

    f_HD -> 1 as t -> 0 and -> 0 as t -> inf. Verified against direct numerical
    integration of the source solution to 4 decimals (rev 5 calibration log).

    rev 5 (26 Sep 2026): replaces the T1-B stand-in `slab_theta(2*R, ...)`. A
    cylinder has twice the surface-to-volume ratio of a slab of the same
    half-width, so the slab kernel under-predicted horizontal heat loss by
    ~2x early on (at R = 10 m, 240 d: slab 0.73 vs exact 0.50).
    """
    if t_days <= 0.0 or R_m <= 0.0 or alpha_m2_per_day <= 0.0:
        return 1.0
    x = R_m * R_m / (2.0 * alpha_m2_per_day * t_days)
    # i0e/i1e are the exponentially scaled Bessel functions: i0e(x) = exp(-x)*I0(x).
    return float(min(max(1.0 - (_i0e(x) + _i1e(x)), 0.0), 1.0))


def boberg_lantz_theta(
    t_since_end_days: float,
    thickness_m: float,
    heated_radius_m: float,
    alpha_m2_per_day: float,
    delta: float = 0.0,
) -> float:
    """Boberg-Lantz dimensionless average heated-zone temperature, clipped to [0, 1].

        theta = f_VD * f_HD * (1 - delta) - delta

    `f_VD = slab_theta(h, t)` is the vertical loss to over/underburden (exact
    for a slab of thickness h) and `f_HD = cylinder_theta(r_h, t)` the
    horizontal loss to the cold reservoir (exact for a cylinder of radius r_h;
    rev 5, replacing the slab-of-thickness-2*r_h approximation).
    """
    if t_since_end_days <= 0.0:
        f_vd = f_hd = 1.0
    else:
        f_vd = slab_theta(thickness_m, alpha_m2_per_day, t_since_end_days)
        f_hd = cylinder_theta(heated_radius_m, alpha_m2_per_day, t_since_end_days)
    d = min(max(delta, 0.0), 1.0)
    theta = f_vd * f_hd * (1.0 - d) - d
    return min(max(theta, 0.0), 1.0)


def steam_zone_temperature(t_days: float, params: dict) -> tuple[float, float]:
    """Average heated-zone temperature and heated radius at cycle day t_days.

    Args:
        t_days: days elapsed since the START of the cycle (day 0 = start of
            steam injection). The same clock runs through inject/soak/produce.
        params: the field_params.json tree, PLUS
            - "steam_t"     (tonnes injected this cycle; cycle.py adds it), and
            - optionally "Q_removed_J" and "Q_retained_J", the running
              produced-fluid enthalpy and the end-of-injection retained heat,
              which together form Boberg & Lantz's energy-removed term `delta`.
              Absent => delta = 0 => pure-conduction cooldown.

    Returns:
        (T_avg_C, heated_radius_m). The heated radius grows during injection
        and is frozen at its end-of-injection value afterwards (Boberg-Lantz's
        own constant-heated-radius assumption; the front does not retreat,
        only its temperature decays).
    """
    reservoir = params["reservoir"]
    T0 = reservoir["T_initial_C"]
    Ts = zone_steam_temperature_C(params)
    h = reservoir["thickness_m"]
    alpha_d = _alpha_m2_per_s(params) * 86400.0  # m^2/day

    t_inject_end = injection_end_day(params)
    t_growth = min(max(t_days, 0.0), t_inject_end)

    if t_growth <= 0.0:
        return T0, 0.0

    r_h_now = _heated_radius_m(_retained_heat_J_at(t_growth, params), params)

    if t_days <= t_inject_end:
        r_h_end = _heated_radius_m(_retained_heat_J_at(t_inject_end, params), params)
        # ASSUMPTION (reporting-only ramp): under Marx-Langenheim the swept
        # zone is isothermal at T_s, so the zone temperature is T_s from the
        # first day. What rises during injection is the fraction of the FINAL
        # zone footprint that has been swept, so we report the area-weighted
        # average over that final footprint. The well is shut in through
        # inject+soak, so this affects the reported T/mu columns only -- the
        # produce phase always starts from the Boberg-Lantz branch below.
        frac = (r_h_now / r_h_end) ** 2 if r_h_end > 0.0 else 0.0
        return T0 + (Ts - T0) * min(frac, 1.0), r_h_now

    r_h_end = r_h_now  # t_growth is clamped at t_inject_end here
    q_retained = params.get("Q_retained_J")
    if q_retained is None:
        q_retained = retained_heat_J(params)
    q_removed = params.get("Q_removed_J", 0.0)
    delta = bl_delta_factor(params) * q_removed / q_retained if q_retained > 0.0 else 0.0

    theta = boberg_lantz_theta(t_days - t_inject_end, h, r_h_end, alpha_d, delta)
    return T0 + (Ts - T0) * theta, r_h_end
