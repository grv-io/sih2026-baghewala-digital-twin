"""cycle.py -- day-by-day CSS (Cyclic Steam Stimulation) cycle simulator.

Orchestrates thermal.py, viscosity.py, ipr.py and srp.py through the three
classical CSS phases -- inject, soak, produce (Butler, R.M., "Thermal Recovery
of Oil and Gas", 1991, ch. 1-2) -- and returns a day-by-day pandas.DataFrame
plus a cycle-level summary().

Tier-1 physics changes carried by this module
---------------------------------------------

**T1-C -- `P_res` is a state, not a constant.** Injection *charges* near-well
pressure; it *bleeds off* through soak and produce. SOURCE:
css_thermal_eor_deep_dive.md section 1.2 lists "Pressure re-charge. Injecting
steam raises near-well pressure, giving drive energy for the first weeks of the
puff phase" as one of the four CSS mechanisms -- the twin modelled none of it.
Section 2.5 gives the soak argument in full: "Too long: the heat you paid for
keeps bleeding into cap rock while the well makes zero revenue, **and near-well
pressure -- a real part of the drive -- decays.**" Without that second half,
soak had a cost and *zero* benefit, so the optimizer could only ever return the
range minimum (3 days), and it did. Now conduction keeps spreading the heat you
already bought (good, and slow in a <10 % porosity shaly sand) while the
pressure recharge bleeds away (bad), so an interior soak optimum exists.

`P_wf` is also no longer `0.4 * P_res`. That fixed fraction made `Pwf/Pres`
constant, which cancelled reservoir pressure algebraically out of the rate
equation (MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md section 3.7 FAIL 3). It is
now an ABSOLUTE pump-intake pressure from fluid submergence over the pump.

**T1-D -- `spm` is a schedule, not a constant.** srp_dynamometer_ml_deep_dive.md
section 5.2: "The optimal SPM is not constant within a single CSS cycle; it
should decline as the well cools. This is precisely the schedule our twin
computes." It now does: each produce day the pump runs at the highest speed the
rods' drag-limited fall velocity allows, capped by `spm` (the start speed) and
floored at the ~2 SPM keep-moving limit.

**T1-E -- rod float costs barrels.** See srp.py; the graded damage index and
fillage statistics are reported in summary() alongside the legacy
`failures_expected` key (kept for api/ and dashboard/ compatibility).

**T1-G -- rupees and CO2 in the summary.** Every result comes out in bbl, INR
and kg CO2 at once (css deep dive section 7). The optimizer's objective moves
from raw SOR to `margin_inr_per_cycle_day`, which carries the fixed cost of the
inject + soak days when the well earns nothing -- and which is what restores an
interior optimum after T1-A removes the SOR one.

**Economics v2 (27 Sep 2026) -- incremental oil, daily opex, corrected energy.**
A CSS cycle is judged against what the SAME well would have made UNSTIMULATED
over the SAME calendar window ("with vs without" -- the cold baseline). The
simulator now also runs that counterfactual (appended columns `oil_cold_m3d`,
`electric_cold_kWh`) and summary() adds incremental keys next to the gross ones:

* Convention: the cold well produces at its cold rate for the WHOLE window,
  including the injection + soak days when the stimulated well is shut in
  (that forgone cold oil is a real cost of stimulating). This is the standard
  "stimulated minus unstimulated production over the same time period"
  definition of incremental CSS oil (Boberg, *Thermal Methods of Oil Recovery*,
  1988, and the PEH ch. 15 CSS discussion; recalled, not re-retrieved -- see
  params/CHANGELOG.md rev 8). Window = `window_days` = soak end + produce days
  (= legacy `days_total` + one step, because the last produce row is a full
  producing day).
* If the cold well would not cover its own daily opex, the counterfactual well
  is shut in (baseline cash 0) -- an operator does not produce at a loss.
* Headline SOR stays GROSS (`SOR_t_per_m3` = steam / all oil): that is how the
  field and every benchmark in this repo quote SOR (CalGEM field SOR =
  steam / total oil; Cold Lake "SOR ~4" is cumulative steam / cumulative
  bitumen). `SOR_incremental` is the ECONOMIC ratio.
* Optimiser objective SHOULD be `margin_incremental_inr_per_cycle_day`
  (see TIER1_PROGRESS_LOG.md section 8). The gross `margin_inr*` keys keep
  their rev-5 definition (steam + rig, no opex) for backward compatibility.
* Daily opex = a fixed well-site cost (`economics.opex_inr_per_day`,
  [ASSUMPTION]) + electricity for the pumping unit from the corrected
  polished-rod energy (srp.py) / surface efficiency x tariff. The fixed part
  is incurred in both cases, so it cancels in the incremental margin unless
  the cold well is uneconomic.

**rev 12 (physics wave 4) -- what ends the produce phase is an operating
rule.** `css.produce_end_rule` "either" (default): the rate cutoff (past the
peak) OR the float alarm (FI > `css.fi_alarm` 0.6) persisting
`css.fi_alarm_days` (3) consecutive days, after which the operator pulls the
well / re-steams instead of running floating rods. df.attrs and summary()
report `produce_end_reason` ("rate_cutoff" / "float_onset" / "max_days").
"rate_cutoff" is the rev <= 11 behaviour (`legacy_rev11_params`).

**rev 13 (wave 5) -- the operator's response to rod float is a CONTROL, and
it is applied to every well alike.** `css.float_policy`:
  "pull"          rev 12: the SPM schedule runs at the physical keep-up limit
                  (SPM_MARGIN = 1.0, FI <= 1) and the well is pulled once
                  FI > css.fi_alarm has persisted css.fi_alarm_days days;
  "vfd_hold"      the VFD slows the unit to HOLD FI at css.vfd_hold_fi (0.6)
                  through the same declining-SPM schedule, down to
                  css.vfd_spm_floor (2 spm); the float alarm can then only
                  fire at the floor, and the well is pulled after
                  css.fi_alarm_days alarm days there;
  "vfd_then_pull" as vfd_hold, but the VFD turns the unit down only to
                  css.vfd_turndown_frac (0.5) x the start SPM (motor cooling /
                  torque limit of a standard NEMA-D motor on a VFD without
                  forced cooling [ASSUMPTION]) -- never below the floor --
                  and pulls after the alarm days there;
  "none"          no float response: rods float until the rate cutoff (the
                  rev <= 11 behaviour, = produce_end_rule "rate_cutoff").
The unstimulated counterfactual obeys the SAME policy
(`css.cold_counterfactual` "policy", default): it is run at the policy floor
on the params' own unit and, if it cannot keep FI <= the alarm line there,
it is SHUT IN (cash 0). "pumpable" = the field fact that these wells were
produced cold: the cold well is slowed (below the keep-moving floor if
needed, down to css.cold_pumpable_min_spm) until FI <= the hold target, and
produces min(IPR, pump capacity) there. "shut_in" / "legacy" (rev 12: the
2-spm floor whatever the float index, full IPR rate) are explicit choices.
Other rev-13 switches: `fluid.flowback_mobility_ratio` M (condensate share of
the cell's liquid c = M W / (M W + V_p); 1 = rev 11/12 volume weighting) and
`steam.min_injection_margin_kPa` (summary `injection_ok`; the optimiser
rejects set-points below it). `legacy_rev12_params` reproduces rev 12.
"""
from __future__ import annotations

import math

import pandas as pd

from twin import thermal, viscosity, ipr, srp

# ASSUMPTION: rod-floating risk threshold, per docs/SPEC.md ("floating_index"
# description: ">0.6 = floating risk"). Retained for `failures_expected`.
FLOATING_RISK_THRESHOLD = 0.6

# ASSUMPTION: safety cap on the produce phase so a pathological input
# (e.g. cutoff_m3d effectively unreachable) cannot loop forever.
MAX_PRODUCE_DAYS = 730.0

# --- T1-C: near-well pressure storage -------------------------------------
# ASSUMPTION [CALIBRATED, no field data]: lumped near-well pressure storage.
# A 1,500 t slug charges the near-well region by PRESSURE_BOOST_PER_T_KPA *
# 1,500 = 1,500 kPa over the base reservoir pressure (11.4 -> 12.9 MPa).
# rev 5 (26 Sep 2026): 2.0 -> 1.0 kPa/t. Tuned to: first-cycle peak/cold uplift
# inside OIL's published 5-6x for BGW-8 (2.0 gave 6.2x). Physical note: a
# wet-steam column at 85-97 kgf/cm2 wellhead gives only ~9-10 MPa bottomhole,
# BELOW the 11.4 MPa virgin pressure (PHYSICS plan section 0), so a large boost
# over virgin pressure is not physically supportable either; the smaller value
# is the more defensible one. This is one of TWO free constants with no field
# data behind them; always report soak/pressure answers as a range.
# rev 10: now params["reservoir"]["pressure_boost_kPa_per_t"] [CALIBRATED /
# ASSUMPTION, UQ U[0.5, 2.0]]; this constant is the FALLBACK. See
# thermal.steam_state_check: at the params' own P and T the sandface fluid is
# subcooled water (p_sat(290 C) = 7.44 MPa < 11.4 MPa), so the mechanism has
# no physical carrier unless the near-well region is depleted.
# rev 11: with the steam state set by the wellhead pressure (thermal.steam_state)
# and P_current 9.4 MPa, the carrier exists (saturated steam at P_sandface >
# P_res) and the charge is CAPPED at P_sandface - P_res (0.72 MPa at 91
# kgf/cm2): the near-well region cannot be charged above the injection pressure.
PRESSURE_BOOST_PER_T_KPA = 1.0

# ASSUMPTION [CALIBRATED, no field data]: near-well pressure bleed-off time
# constant (days). Low permeability => slow bleed-off => a long soak is
# affordable, which is the twin's physical explanation for why Baghewala's
# 7-13 d practice beats the generic 2-7 d guideline (css section 2.5).
TAU_BLEED_D = 25.0

# ASSUMPTION: fluid submergence over the pump intake (m). field_params.json
# carries no fluid-level or pump-setting-depth datum. 100 m of produced-fluid
# column plus a nominal casing head pressure sets an ABSOLUTE P_wf, which is
# what makes reservoir pressure live in ipr.py (see module docstring).
PUMP_SUBMERGENCE_M = 100.0
CASING_HEAD_PRESSURE_KPA = 200.0

# --- T1-B: Boberg & Lantz energy-removed term ------------------------------
# Physics v3 (26 Sep 2026): the lumped `CP_LIQUID_JM3K = 4.0e6` blend is
# DELETED. The produced heat is now computed stream by stream with Boberg &
# Lantz's own Eq. (PEH Eq. 15.74) in thermal.produced_heat_J_per_day: oil at
# M_o(API, T) + hot water at its steam-table enthalpy rise.
# ASSUMPTION: early-CSS water cut, flagged. Overridable via fluid.water_cut.
# rev 11: used only by fluid.water_cut_model = "constant" (the rev <= 10
# behaviour); the default "state" model computes the cut every day (below).
DEFAULT_WATER_CUT = 0.85

# --- rev 11 (T2-A): water cut as a state variable --------------------------
# Produced water = CONDENSATE FLOWBACK + FORMATION WATER.
#  * Condensate: a fraction `fluid.condensate_recovery_frac` [ASSUMPTION
#    0.5-0.9; Prats, SPE Monograph 7, and Butler 1991 ch. 7: most of the
#    injected water is produced back within the cycle] of the injected steam
#    mass (1 t = 1 stock-tank m3) is mobile and returns. It sits in a
#    well-mixed near-well cell (a lumped "tank", the standard mixing-cell /
#    CSTR idealisation) whose other contents are the heated zone's own pore
#    fluids, V_p = phi * pi * r_h^2 * h. The condensate share of the liquid the
#    cell delivers is c = W_c / (W_c + V_p), and each day the cell loses
#    c * (liquid produced). So dW_c/dt = -q_L * W_c / (W_c + V_p): exponential
#    decay with time constant (heated-zone pore volume + condensate) / liquid
#    rate, i.e. faster when the pump lifts more.
#    [ASSUMPTION - structural] volume-weighted, not mobility-weighted: hot
#    water is ~100x more mobile than 300 C oil, so a fractional-flow split
#    would push the early cut higher and the flowback faster.
#  * Formation water: the rest of the liquid (1 - c) carries the reservoir's
#    native cut `fluid.formation_water_cut` [ASSUMPTION 0.3-0.6; no
#    Baghewala figure found -- baghewala_facts.md, OIL_DATA_REQUEST #2].
#  Day water cut wc = c + (1 - c) * f_w: ~0.9 at first production, falling to
#  f_w as the condensate is recovered. It feeds the pump (liquid = oil /
#  (1 - wc) against displacement), the produced-stream emulsion viscosity
#  (srp.rod_drag_viscosity_cP -> drag, float index, SPM ceiling, energy), the
#  Boberg-Lantz produced heat (hot water at T_avg), the tubing column density
#  (pump work, PRL) and hence the power bill. No water-handling cost key
#  exists in params; the lifting energy of the water is in the power cost.
#  The cold (unstimulated) well produces at f_w.
WATER_CUT_MODELS = ("state", "constant")
DEFAULT_CONDENSATE_RECOVERY_FRAC = 0.7
DEFAULT_FORMATION_WATER_CUT = 0.45

# --- rev 12 (physics wave 4): produce-end OPERATING rule --------------------
# Until rev 11 the produce phase ended only on the rate cutoff, so a cycle whose
# late, oil-continuous stream floated the rods kept pumping floating rods for
# 76-210 days (TIER1 section 10.5), and the optimiser's only way to respect
# FI <= 0.6 was a HIGH fixed cutoff that ended the cycle before the inversion --
# which failed in 41 % of UQ draws where the peak never cleared it (10.9).
# An operator does not run floating rods for months: once the float alarm has
# persisted he pulls the well / re-steams. The rule makes that explicit:
#   "rate_cutoff": end when the oil rate (past its peak) < cutoff (rev <= 11);
#   "float_onset": end when floating_index > css.fi_alarm (0.6, the SPEC line)
#                  on css.fi_alarm_days CONSECUTIVE produce days;
#   "either"     : whichever comes first (DEFAULT).
# `css.fi_alarm_days` = 3 [ASSUMPTION -- an operator would pull / re-steam
# rather than run floating rods; 3 d = a dyno-card confirmation plus a rig
# call-out, no Baghewala SOP found]. The last produce row is the 3rd alarm day.
PRODUCE_END_RULES = ("rate_cutoff", "float_onset", "either")
DEFAULT_PRODUCE_END_RULE = "rate_cutoff"   # key absent -> rev <= 11 behaviour
DEFAULT_FI_ALARM_DAYS = 3.0


def produce_end_rule_of(params: dict, override: str | None = None) -> str:
    """`css.produce_end_rule` (rev 12; absent -> "rate_cutoff", i.e. rev <= 11)."""
    r = str(override or params.get("css", {}).get("produce_end_rule")
            or DEFAULT_PRODUCE_END_RULE).lower()
    if r not in PRODUCE_END_RULES:
        raise ValueError(f"css.produce_end_rule must be one of {PRODUCE_END_RULES}, got {r!r}")
    return r


def fi_alarm(params: dict) -> float:
    """Float-alarm line for the produce-end rule (css.fi_alarm, default the SPEC 0.6)."""
    v = params.get("css", {}).get("fi_alarm")
    return float(v) if v is not None else FLOATING_RISK_THRESHOLD


def fi_alarm_days(params: dict) -> float:
    """Consecutive alarm days before the operator pulls the well (css.fi_alarm_days)."""
    v = params.get("css", {}).get("fi_alarm_days")
    return float(v) if v is not None else DEFAULT_FI_ALARM_DAYS


# --- rev 13 (wave 5): the float response as an operating policy --------------
FLOAT_POLICIES = ("pull", "vfd_hold", "vfd_then_pull", "none")
# Float-index comparisons against the alarm line use this tolerance: under the
# VFD-hold policies the schedule puts FI exactly on the hold target (0.6) up to
# round-off, and such a held day is not an alarm day.
ALARM_TOL = 1e-9
# [ASSUMPTION] VFD turndown before an operator pulls (vfd_then_pull): a standard
# NEMA-D beam-pump motor on a VFD without forced cooling is commonly limited to
# ~50 % of its base speed at full torque (self-cooled fan). No Baghewala VFD spec.
DEFAULT_VFD_TURNDOWN_FRAC = 0.5
COLD_COUNTERFACTUALS = ("policy", "pumpable", "shut_in", "legacy")
# Absent-key default is "legacy" ON PURPOSE (bit-exact rev<=12 behaviour for any
# caller that hasn't been updated to pass a counterfactual explicitly) -- this
# is a compatibility default, not a recommendation; current call sites (uq.py,
# recommend_physics.py) pass "policy" explicitly. Do not change this default's
# behaviour; if it ever needs to change, do it as its own reviewed commit.
DEFAULT_COLD_COUNTERFACTUAL = "legacy"   # key absent -> rev <= 12 behaviour


def float_policy_of(params: dict, override: str | None = None) -> str:
    """`css.float_policy` (rev 13). Absent -> derived from the produce-end rule:
    "rate_cutoff" -> "none", otherwise "pull" (the rev-12 behaviour)."""
    v = override or params.get("css", {}).get("float_policy")
    if v is None:
        return "none" if produce_end_rule_of(params) == "rate_cutoff" else "pull"
    v = str(v).lower()
    if v not in FLOAT_POLICIES:
        raise ValueError(f"css.float_policy must be one of {FLOAT_POLICIES}, got {v!r}")
    return v


def vfd_hold_fi(params: dict) -> float:
    """FI the VFD holds under the vfd policies (css.vfd_hold_fi, default the alarm line)."""
    v = params.get("css", {}).get("vfd_hold_fi")
    return float(v) if v is not None else fi_alarm(params)


def vfd_spm_floor(params: dict, spm_floor: float | None = None) -> float:
    """Lowest SPM the VFD policies slow to (css.vfd_spm_floor, default the
    keep-moving floor srp.spm_floor / the caller's spm_floor)."""
    v = params.get("css", {}).get("vfd_spm_floor")
    if v is not None:
        return float(v)
    if spm_floor is not None:
        return float(spm_floor)
    return float(params["srp"].get("spm_floor", DEFAULT_SPM_FLOOR))


def vfd_turndown_frac(params: dict) -> float:
    v = params.get("css", {}).get("vfd_turndown_frac")
    return float(v) if v is not None else DEFAULT_VFD_TURNDOWN_FRAC


def policy_schedule(params: dict, policy: str, spm_start: float,
                    spm_floor: float) -> tuple[float, float]:
    """(schedule margin phi = target v_stroke/v_fall, effective SPM floor) of a policy.

    pull / none: the physical keep-up limit SPM_MARGIN (1.0) and the keep-moving
    floor (rev 5-12). vfd_hold: the hold target (0.6) down to the VFD floor.
    vfd_then_pull: the hold target down to max(VFD floor, turndown x start)."""
    if policy in ("pull", "none"):
        return SPM_MARGIN, float(spm_floor)
    floor = vfd_spm_floor(params, spm_floor)
    if policy == "vfd_then_pull":
        floor = max(floor, vfd_turndown_frac(params) * float(spm_start))
    return vfd_hold_fi(params), floor


def cold_counterfactual_of(params: dict, override: str | None = None) -> str:
    v = str(override or params.get("css", {}).get("cold_counterfactual")
            or DEFAULT_COLD_COUNTERFACTUAL).lower()
    if v not in COLD_COUNTERFACTUALS:
        raise ValueError(f"css.cold_counterfactual must be one of {COLD_COUNTERFACTUALS}, got {v!r}")
    return v


def flowback_mobility_ratio(params: dict) -> float:
    """`fluid.flowback_mobility_ratio` M (rev 13): condensate share of the
    mixing cell's liquid c = M W / (M W + V_p). 1 = volume-weighted (rev 11/12);
    M > 1 = the hot condensate is more mobile than the cell's oil-bearing pore
    fluid (fractional-flow proxy). [ASSUMPTION; UQ discrete {1, 3, 10}]"""
    v = params.get("fluid", {}).get("flowback_mobility_ratio")
    return max(float(v), 1e-6) if v is not None else 1.0


def min_injection_margin_kPa(params: dict) -> float:
    """`steam.min_injection_margin_kPa` (rev 13) [ASSUMPTION 300-500 kPa: tubing
    friction of the two-phase column + a safety margin, which the IF97
    column-head calculation neglects]. Absent -> 0 (rev 12: any positive margin)."""
    v = params.get("steam", {}).get("min_injection_margin_kPa")
    return float(v) if v is not None else 0.0


# --- T1-D: SPM schedule ----------------------------------------------------
# Published heavy-oil keep-moving floor: 2 SPM absolute minimum (srp deep dive
# section 5.1; US Patent 4,406,597). Overridable via srp.spm_floor.
DEFAULT_SPM_FLOOR = 2.0
# Target v_stroke/v_fall ratio for the scheduled speed. rev 5 (26 Sep 2026):
# 0.6 -> 1.0. The schedule now enforces the PHYSICAL limit -- the pumping unit
# never commands the rods down faster than they can fall (no lost stroke, no
# carrier-bar separation) -- while the SPEC's 0.6 alarm line stays a RISK
# indicator counted by summary()["failures_expected"]. With 0.6 the schedule
# clamped every day exactly onto the alarm line, so floating_index could never
# exceed 0.6 anywhere in the design space and the ML float classifier had no
# positive examples (a decorative alarm). With 1.0 the alarm trips only in the
# high-SPM / low-cutoff (cold-tail) corner, which is where the physics puts it.
SPM_MARGIN = 1.0

# --- T1-G: economics defaults ----------------------------------------------
# Used only when the caller does not pass `params` to summary(). Values and
# their sources are the "economics" block of params/field_params.json; see
# MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md section 1.2 for every citation.
_DEFAULT_ECONOMICS = {
    "diesel_kg_per_t_steam": 71.0,        # DERIVED: OIL deck BGW-08, 220 kg/h HSD -> 3,100 kg/h steam
    "diesel_density_kg_per_l": 0.83,      # TYPICAL
    "diesel_price_inr_per_l": 97.8,       # CONFIRMED Rajasthan retail (upper bound; bulk is lower)
    "diesel_bulk_discount_frac": 0.15,    # [CALIBRATED, UNSOURCED] rev 13: mid of U[0, 0.30] (was 0.30, rev 5-12), see steam_cost_inr_per_t
    "diesel_co2_kg_per_GJ": 74.1,         # CONFIRMED IPCC default
    "steam_energy_GJ_per_t": 3.02,        # DERIVED, inside the published 2.6-4.0 GJ/t band
    "oil_price_inr_per_bbl": 5992.0,       # rev 9: CONFIRMED OIL FY25 realisation $78.09/bbl (AR 2024-25) - $10 heavy discount [ASSUMPTION], x Rs 88/$
    "fixed_cost_inr_per_cycle": 1.5e6,    # ASSUMPTION: rig/workover per cycle
    "electricity_inr_per_kWh": 8.0,       # UNSOURCED PLACEHOLDER
    "opex_inr_per_day": 5000.0,           # ASSUMPTION (Economics v2): fixed well-site opex excl. power
    "bbl_per_m3": 6.28981,                # DEFINITION
}

# The 10 columns docs/SPEC.md fixes. Post-Tier-1 columns are APPENDED after these,
# never inserted, so `list(df.columns)[:10] == SPEC_COLUMNS` always holds.
SPEC_COLUMNS = [
    "day", "phase", "T_res_C", "mu_cP", "P_res_kPa", "oil_m3d",
    "steam_t_cum", "energy_kWh", "rod_load_kN", "floating_index",
]
EXTRA_COLUMNS = ["spm", "fillage", "v_fall_ms", "heated_radius_m", "uplift", "pump_limited"]
# Economics v2 (appended): grid electricity of the stimulated well, and the
# unstimulated (cold) counterfactual's oil rate and grid electricity on the
# same day. Constant cold columns, one per row, so summary(df) needs no params.
ECON_COLUMNS = ["electric_kWh", "oil_cold_m3d", "electric_cold_kWh"]
# rev 11 (appended): the day's produced-stream water cut, total water and its
# condensate part (m3/d), and the dynamic peak polished-rod load (Mills) that
# the unit-rating cap is checked against. 0 on shut-in rows.
WATER_COLUMNS = ["water_cut", "water_m3d", "condensate_m3d", "peak_prl_kN"]
_COLUMNS = SPEC_COLUMNS + EXTRA_COLUMNS + ECON_COLUMNS + WATER_COLUMNS


def pressure_boost_kPa_per_t(params: dict) -> float:
    """Near-well pressure charge per tonne injected (rev 10: from params)."""
    v = params.get("reservoir", {}).get("pressure_boost_kPa_per_t")
    return float(v) if v is not None else PRESSURE_BOOST_PER_T_KPA


def reservoir_pressure_kPa(params: dict) -> float:
    """Current (pre-cycle) reservoir pressure the IPR sees (rev 10).

    `reservoir.P_current_kPa` [ASSUMPTION -- depleted, UNKNOWN; top data ask]
    if set, else the virgin `reservoir.P_initial_kPa` (so the shipped params,
    which leave it null, behave exactly as before). The problem statement
    describes Baghewala as "low reservoir pressure"; ml/uq.py samples
    P_current U[7.4, 11.4] MPa. Not silently re-tuned: the default stays virgin.
    """
    res = params["reservoir"]
    v = res.get("P_current_kPa")
    return float(v) if v is not None else float(res["P_initial_kPa"])


def water_cut_model(params: dict) -> str:
    """`fluid.water_cut_model`: "state" (rev 11) or "constant" (rev <= 10).

    A params tree without the key runs "constant" (backward compatible); the
    shipped params/field_params.json sets "state"."""
    m = str(params.get("fluid", {}).get("water_cut_model") or "constant").lower()
    if m not in WATER_CUT_MODELS:
        raise ValueError(f"fluid.water_cut_model must be one of {WATER_CUT_MODELS}, got {m!r}")
    return m


def formation_water_cut(params: dict) -> float:
    """Native (formation) water cut of the reservoir liquid, rev 11 [ASSUMPTION]."""
    v = params.get("fluid", {}).get("formation_water_cut")
    return min(max(float(v if v is not None else DEFAULT_FORMATION_WATER_CUT), 0.0), 0.99)


def condensate_recovery_frac(params: dict) -> float:
    """Fraction of the injected steam mass produced back as condensate (rev 11)."""
    v = params.get("fluid", {}).get("condensate_recovery_frac")
    return min(max(float(v if v is not None else DEFAULT_CONDENSATE_RECOVERY_FRAC), 0.0), 1.0)


def cold_water_cut(params: dict) -> float:
    """Water cut of the unstimulated well: formation water only (state model),
    the constant fluid.water_cut otherwise."""
    if water_cut_model(params) == "state":
        return formation_water_cut(params)
    return srp.params_water_cut(params)


def legacy_rev10_params(params: dict) -> dict:
    """Deep copy of params with the rev-10 physics switches (rev 11 changelog).

    Constant water cut (fluid.water_cut), temperature-specified steam
    ("legacy_T": T_injection_C + latent_heat_Jkg), virgin reservoir pressure
    (P_current_kPa null), the 2.18-m stroke and no PRL cap. Reproduces every
    rev-10 number exactly (tests/test_physics_wave3.py). Used by the calibration
    demo, whose committed dataset was generated with the rev-10 physics."""
    import copy
    q = copy.deepcopy(params)
    q["fluid"]["water_cut_model"] = "constant"
    q["steam"]["state_model"] = "legacy_T"
    q["reservoir"]["P_current_kPa"] = None
    q["srp"]["stroke_m"] = 2.18
    q["srp"].pop("max_prl_kN", None)
    # rev 12 switches off too (Brinkman W/O, no cap, rate-cutoff rule, AOF 0.46)
    q["fluid"]["emulsion_law"] = "brinkman"
    q["fluid"].pop("emulsion_mu_r_max", None)
    q.setdefault("css", {})["produce_end_rule"] = "rate_cutoff"
    q.setdefault("ipr", {})["aof_ref_m3d"] = REV11_AOF_REF_M3D
    _rev13_switches_off(q)
    q.pop("_steam_state", None)
    return q


# rev 12: the AOF_REF_M3D in force through rev 11 (ipr.py history).
REV11_AOF_REF_M3D = 0.46
# rev 13: the diesel bulk discount in force through rev 12 (moved to the 0.15 mid-range).
REV12_DIESEL_BULK_DISCOUNT = 0.30


def _rev13_switches_off(q: dict) -> dict:
    """In place: the rev-13 (wave 5) switches off -- pull policy, rev-12 cold
    well, sharp inversion, volume-weighted flowback, no injection margin, the
    rev <= 12 diesel discount."""
    css = q.setdefault("css", {})
    css["float_policy"] = "none" if css.get("produce_end_rule") == "rate_cutoff" else "pull"
    css["cold_counterfactual"] = "legacy"
    q["fluid"].pop("emulsion_inversion_band_wc", None)
    q["fluid"].pop("flowback_mobility_ratio", None)
    q.get("steam", {}).pop("min_injection_margin_kPa", None)
    if "economics" in q:
        q["economics"]["diesel_bulk_discount_frac"] = REV12_DIESEL_BULK_DISCOUNT
    return q


def legacy_rev12_params(params: dict) -> dict:
    """Deep copy of params with the rev-13 (wave 5) switches off: float policy
    "pull" (produce_end_rule "either"), the rev-12 cold well (2-spm floor, full
    IPR rate whatever its float index), the sharp W/O -> O/W inversion,
    volume-weighted flowback, no injection-margin gate and the 0.30 diesel
    discount. Reproduces the rev-12 numbers (TIER1 section 11;
    tests/test_physics_wave5.py)."""
    import copy
    q = copy.deepcopy(params)
    q.setdefault("css", {})["produce_end_rule"] = "either"
    _rev13_switches_off(q)
    q.pop("_steam_state", None)
    return q


def legacy_rev11_params(params: dict) -> dict:
    """Deep copy of params with the rev-12 (wave 4) switches off: Brinkman W/O
    drag with no cap, the rate-cutoff-only produce-end rule and AOF 0.46.
    Reproduces the rev-11 numbers (TIER1 section 10; tests/test_physics_wave4.py)."""
    import copy
    q = copy.deepcopy(params)
    q["fluid"]["emulsion_law"] = "brinkman"
    q["fluid"].pop("emulsion_mu_r_max", None)
    q.setdefault("css", {})["produce_end_rule"] = "rate_cutoff"
    q.setdefault("ipr", {})["aof_ref_m3d"] = REV11_AOF_REF_M3D
    _rev13_switches_off(q)
    q.pop("_steam_state", None)
    return q


def with_controls(params: dict, stroke_m: float | None = None,
                  p_wellhead_kgf_cm2: float | None = None) -> dict:
    """Copy of params with the rev-11 surface controls written in.

    `stroke_m` -> srp.stroke_m (a discrete API stroke in the optimiser),
    `p_wellhead_kgf_cm2` -> steam.P_wellhead_kgf_cm2 (injection pressure).
    Copies only the touched blocks; the input is never mutated."""
    p = dict(params)
    if stroke_m is not None:
        p["srp"] = dict(params["srp"], stroke_m=float(stroke_m))
    if p_wellhead_kgf_cm2 is not None:
        p["steam"] = dict(params["steam"], P_wellhead_kgf_cm2=float(p_wellhead_kgf_cm2))
    p.pop("_steam_state", None)
    return p


def _row_dt_days(df: pd.DataFrame) -> float:
    """Timestep of a simulate_css_cycle frame (days).

    rev 10 dt fix: every per-day rate column (oil_m3d, energy_kWh,
    electric_kWh) is a RATE; totals are sum(rate) * dt. Read from
    df.attrs["dt_days"] (set by simulate_css_cycle), else inferred from the
    produce-row spacing, else 1.0.
    """
    dt = df.attrs.get("dt_days") if hasattr(df, "attrs") else None
    if dt:
        return float(dt)
    produce = df[df["phase"] == "produce"] if len(df) else df
    if len(produce) > 1:
        return float(produce["day"].diff().median())
    if len(df) > 1:
        return float(df["day"].diff().median())
    return 1.0


def steam_cost_inr_per_t(econ: dict) -> float:
    """Rupees per tonne of steam from OIL's own diesel burn (T1-G).

    rev 5: the base case applies `diesel_bulk_discount_frac` (0.30) to the
    CONFIRMED Rajasthan retail pump price, giving ~Rs 5,860/t -- the low end of
    the project's documented Rs 5,900-8,400/t band (ECON plan section 0.2; the
    -30 % row of its sensitivity table). [CALIBRATED, UNSOURCED discount]
    Calibration target: revealed preference -- OIL ran 19 CSS jobs in FY2025-26,
    so at the field's real fuel and oil prices a sensible cycle must pay. At
    retail (discount 0) a SOR ~4 cycle loses money (breakeven SOR ~3.6 before
    fixed cost); that sign flip is the fuel-price finding, not a bug. Set the
    discount to 0 to reproduce the retail upper bound.
    rev 13: the base discount moved to 0.15 (Rs 7,111/t), the MID of the
    U[0, 0.30] range, after the external review flagged 0.30 as the best edge;
    0.30 and 0 are kept as params presets (economics.diesel_discount_presets).
    """
    litres_per_t = econ["diesel_kg_per_t_steam"] / econ["diesel_density_kg_per_l"]
    discount = float(econ.get("diesel_bulk_discount_frac", 0.0) or 0.0)
    return litres_per_t * econ["diesel_price_inr_per_l"] * (1.0 - discount)


def co2_kg_per_t_steam(econ: dict) -> float:
    """kg CO2 per tonne of steam (diesel-fired, IPCC default factor)."""
    return econ["steam_energy_GJ_per_t"] * econ["diesel_co2_kg_per_GJ"]


def _pump_intake_pressure_kPa(params: dict) -> float:
    """Absolute flowing bottomhole pressure set by pump submergence (T1-C)."""
    rho = srp._fluid_density_kgm3(params["fluid"]["api_gravity"])
    return CASING_HEAD_PRESSURE_KPA + rho * srp.G * PUMP_SUBMERGENCE_M / 1000.0


def cold_baseline(params: dict, spm_floor: float | None = None) -> dict:
    """The unstimulated well: cold oil rate and daily energy (Economics v2).

    Same IPR (uplift 1, pre-cycle P_res -- rev 10: reservoir_pressure_kPa,
    virgin unless reservoir.P_current_kPa is set -- the absolute pump-intake P_wf) and the
    same pump as the stimulated cycle. [ASSUMPTION] the cold well is run at the
    keep-moving floor speed (`srp.spm_floor`, 2 spm): its ~3 m3/d of liquid
    needs well under 1 spm of displacement, and slow strokes are heavy-oil
    practice (srp deep dive section 5.1). Returns oil_m3d, energy_kWh_d
    (polished rod), electric_kWh_d, spm.

    rev 12 FINDING (TIER1 section 11; strict xfail in test_physics_wave4.py):
    at the 45 % formation cut the cold stream is a W/O emulsion at ~4.5x the
    11,500 cP oil under ANY published law (Pal-Rhodes over its phi* range
    3.3-9x; Brinkman 4.46x), i.e. ~51,000 cP: FI 1.0 and Mills PRL 189 kN
    at 2 spm x 86 in, above the 113.9 kN rating, drawing ~433 kWh/d. It is
    pumpable at 2 spm x 86 in only for mu_r <= ~1.9 and at 1 spm x 64 in at
    the base emulsion (~90 kWh/d). Not changed here (the 2-spm floor is a
    stated assumption); the ~Rs 2.7k/d of cold power it charges inflates
    every incremental margin by that amount.
    """
    if spm_floor is None:
        spm_floor = params["srp"].get("spm_floor", DEFAULT_SPM_FLOOR)
    T0 = params["reservoir"]["T_initial_C"]
    mu = viscosity.mu_cP(T0, params)
    p_wf = _pump_intake_pressure_kPa(params)
    q_ipr = ipr.oil_rate_m3d(reservoir_pressure_kPa(params), p_wf, mu, params)
    stroke_m = params["srp"]["stroke_m"]
    spm_c = float(spm_floor)
    wc = cold_water_cut(params)   # rev 11: formation water only
    st = srp.pump_state(spm_c, stroke_m, mu, q_ipr, params, intake_pressure_kPa=p_wf, T_C=T0,
                        water_cut=wc)
    return {"oil_m3d": st["prod_rate_m3d"], "energy_kWh_d": st["energy_kWh_d"],
            "electric_kWh_d": st["electric_kWh_d"], "spm": spm_c, "ipr_rate_m3d": q_ipr,
            "water_cut": wc, "floating_index": st["floating_index"], "fillage": st["fillage"],
            "peak_prl_kN": st["peak_prl_kN"], "mu_drag_cP": st["mu_drag_cP"]}


def cold_counterfactual_well(params: dict, spm_floor: float | None = None,
                        policy: str | None = None, mode: str | None = None) -> dict:
    """The unstimulated counterfactual the incremental economics compare with (rev 13).

    `mode` = css.cold_counterfactual:
      "legacy"   rev <= 12: cold_baseline() -- the params' unit at the 2-spm
                 floor, full IPR rate whatever the float index (at the 45 %
                 formation cut: FI 1.0, PRL 189 kN, 433 kWh/d -- unpumpable
                 yet producing; TIER1 section 11.2).
      "policy"   the cold well obeys the SAME float policy as the stimulated
                 cycle: run at the policy floor (pull / vfd_hold / vfd_then_pull:
                 the keep-moving / VFD floor -- the cold well's start speed is
                 already the floor) on the params' own unit; if FI there is
                 above the alarm line the operator would pull it, i.e. it is
                 SHUT IN (status "shut_in_float"). Policy "none" = legacy.
      "pumpable" the field fact that these wells were produced cold at ~2-3
                 bbl/d: the VFD slows the cold well below the keep-moving floor
                 if needed (down to css.cold_pumpable_min_spm, default 0.1 spm
                 [ASSUMPTION]) until FI <= the hold target; it produces
                 min(IPR, pump capacity) there. Shut in only if even that speed
                 cannot hold FI.
      "shut_in"  no counterfactual production (cash 0).
    Returns oil_m3d / electric_kWh_d of the COUNTERFACTUAL (0 when shut in),
    status, spm, and the physical cold-well keys of cold_baseline()."""
    mode = cold_counterfactual_of(params, mode)
    base = cold_baseline(params, spm_floor=spm_floor)
    if spm_floor is None:
        spm_floor = params["srp"].get("spm_floor", DEFAULT_SPM_FLOOR)
    pol = float_policy_of(params, policy)
    out = dict(base, mode=mode, policy=pol, status="pumped", physical_oil_m3d=base["oil_m3d"])
    if mode == "legacy" or (mode == "policy" and pol == "none"):
        return out
    if mode == "shut_in":
        return dict(out, oil_m3d=0.0, energy_kWh_d=0.0, electric_kWh_d=0.0, status="shut_in")
    T0 = params["reservoir"]["T_initial_C"]
    mu = viscosity.mu_cP(T0, params)
    p_wf = _pump_intake_pressure_kPa(params)
    stroke_m = params["srp"]["stroke_m"]
    wc = base["water_cut"]
    q_ipr = base["ipr_rate_m3d"]
    if mode == "policy":
        _, floor = policy_schedule(params, pol, spm_floor, spm_floor)
        st = srp.pump_state(floor, stroke_m, mu, q_ipr, params, intake_pressure_kPa=p_wf, T_C=T0,
                            water_cut=wc)
        info = {"spm": float(floor), "floating_index": st["floating_index"], "fillage": st["fillage"],
                "peak_prl_kN": st["peak_prl_kN"], "mu_drag_cP": st["mu_drag_cP"]}
        if st["floating_index"] > fi_alarm(params) + ALARM_TOL:
            return dict(out, **info, oil_m3d=0.0, energy_kWh_d=0.0, electric_kWh_d=0.0,
                        status="shut_in_float")
        return dict(out, **info, oil_m3d=st["prod_rate_m3d"], energy_kWh_d=st["energy_kWh_d"],
                    electric_kWh_d=st["electric_kWh_d"])
    # "pumpable": the highest speed <= the floor that holds FI at the hold target
    target = vfd_hold_fi(params)
    s = min(float(spm_floor), srp.max_spm_for_viscosity(mu, stroke_m, params, margin=target,
                                                         T_C=T0, water_cut=wc))
    s_min = params.get("css", {}).get("cold_pumpable_min_spm")
    s_min = 0.1 if s_min is None else float(s_min)
    if s < s_min - 1e-12:
        return dict(out, spm=s_min, oil_m3d=0.0, energy_kWh_d=0.0, electric_kWh_d=0.0,
                    status="shut_in_float")
    st = srp.pump_state(s, stroke_m, mu, q_ipr, params, intake_pressure_kPa=p_wf, T_C=T0, water_cut=wc)
    return dict(out, spm=float(s), floating_index=st["floating_index"], fillage=st["fillage"],
                peak_prl_kN=st["peak_prl_kN"], mu_drag_cP=st["mu_drag_cP"],
                oil_m3d=st["prod_rate_m3d"], energy_kWh_d=st["energy_kWh_d"],
                electric_kWh_d=st["electric_kWh_d"],
                status="pumped_slow" if s < float(spm_floor) - 1e-12 else "pumped")


def simulate_css_cycle(
    steam_t: float,
    soak_days: float,
    cutoff_m3d: float,
    spm: float,
    params: dict,
    dt_days: float = 1.0,
    spm_floor: float | None = None,
    stroke_m: float | None = None,
    p_wellhead_kgf_cm2: float | None = None,
    produce_end_rule: str | None = None,
    float_policy: str | None = None,
    cold_counterfactual: str | None = None,
) -> pd.DataFrame:
    """Simulate one CSS cycle: inject -> soak -> produce (until cutoff).

    Args:
        steam_t: total steam mass injected this cycle (tonnes).
        soak_days: shut-in soak duration after injection (days).
        cutoff_m3d: economic cutoff oil rate (m3/d); production ends once the
            pumped rate is below this AND past its peak (rev 11: the cutoff is
            not applied while the rate is still rising through the condensate
            flowback -- no operator shuts a well in on its way up).
        spm: sucker-rod pump speed at the START of the produce phase
            (strokes/minute). From T1-D the pump no longer runs at a single
            speed: this is the ceiling of a declining schedule -- which is
            also how the VFD lever is represented (rev 11 docs).
        params: field_params.json tree (read-only; not mutated).
        dt_days: simulation timestep (days). Default 1.0 (daily steps).
        spm_floor: keep-moving floor for the schedule. Defaults to
            `srp.spm_floor` in params, else 2.0. Exposed as a keyword so the
            optimizer can search (spm_start, spm_floor) as two variables.
        stroke_m: rev 11 control -- polished-rod stroke (m), overrides
            srp.stroke_m (the optimiser uses the API sizes 64-144 in).
        p_wellhead_kgf_cm2: rev 11 control -- injection (wellhead) pressure,
            kgf/cm2 g, overrides steam.P_wellhead_kgf_cm2 (CONFIRMED 85-97).
        produce_end_rule: rev 12 operating policy, overrides
            css.produce_end_rule: "rate_cutoff" (rev <= 11), "float_onset"
            (floating_index > css.fi_alarm on css.fi_alarm_days consecutive
            produce days) or "either" (the shipped default: whichever first).
            df.attrs["produce_end_reason"] records what ended the cycle
            ("rate_cutoff", "float_onset" or "max_days").
        float_policy: rev 13 operator response to rod float, overrides
            css.float_policy: "pull" / "vfd_hold" / "vfd_then_pull" / "none"
            (module docstring). The float-onset end applies only when the
            produce-end rule includes it and the policy is not "none".
        cold_counterfactual: rev 13, overrides css.cold_counterfactual
            ("policy" / "pumpable" / "shut_in" / "legacy"); the cold well
            obeys the same float policy as this cycle.

    Returns:
        pandas.DataFrame with one row per timestep. The first 10 columns are
        exactly the docs/SPEC.md set (day, phase, T_res_C, mu_cP, P_res_kPa,
        oil_m3d, steam_t_cum, energy_kWh, rod_load_kN, floating_index);
        Tier-1 additions (spm, fillage, v_fall_ms, heated_radius_m, uplift,
        pump_limited) follow, then the Economics v2 columns (electric_kWh,
        oil_cold_m3d, electric_cold_kWh), then rev 11 (water_cut, water_m3d,
        condensate_m3d, peak_prl_kN). phase in {"inject", "soak", "produce"}.
        `energy_kWh` is polished-rod energy (srp.py v2). df.attrs carries
        dt_days, the steam state, the pressure recharge and the controls.
    """
    # rev 11: the unstimulated counterfactual runs the params' OWN pump (stroke,
    # 2-spm floor) whatever stroke/pressure this cycle uses: a lever must not
    # raise the incremental margin by handicapping the cold well (at the
    # formation water cut the cold stream is an oil-continuous emulsion, whose
    # rod-drag power grows with stroke).
    params_cold = params
    params = with_controls(params, stroke_m=stroke_m, p_wellhead_kgf_cm2=p_wellhead_kgf_cm2)
    # rev 11: one steam state per cycle (IF97 sandface state from the wellhead
    # pressure, or the rev-10 legacy T state), cached for thermal/ipr.
    steam_st = thermal.steam_state(params)
    params["_steam_state"] = steam_st
    steam_params = params["steam"]
    reservoir_params = params["reservoir"]
    injection_rate_tpd = steam_params["injection_rate_tpd"]
    # rev 10/11: warn (never fail) on an inconsistent steam state (rev 11:
    # injection impossible because P_sandface <= P_res) -- see
    # thermal.steam_state_check and TIER1_PROGRESS_LOG.md s. 9-10.
    thermal.warn_steam_state(params)
    stroke_m = params["srp"]["stroke_m"]
    if spm_floor is None:
        spm_floor = params["srp"].get("spm_floor", DEFAULT_SPM_FLOOR)
    wc_model = water_cut_model(params)
    end_rule = produce_end_rule_of(params, produce_end_rule)
    # rev 13: the float policy. Explicit override > an explicit
    # produce_end_rule="rate_cutoff" override (= "run floating rods to the rate
    # cutoff", the rev <= 11 behaviour, so such calls keep their meaning) >
    # css.float_policy > derived from css.produce_end_rule when absent.
    if float_policy is not None:
        policy = float_policy_of(params, float_policy)
    elif produce_end_rule is not None and end_rule == "rate_cutoff":
        policy = "none"
    else:
        policy = float_policy_of(params)
    use_rate_rule = end_rule in ("rate_cutoff", "either")
    use_float_rule = end_rule in ("float_onset", "either") and policy != "none"
    fi_line = fi_alarm(params)
    fi_days_needed = fi_alarm_days(params)
    sched_margin, sched_floor = policy_schedule(params, policy, spm, spm_floor)
    mob_M = flowback_mobility_ratio(params)
    water_cut_const = srp.params_water_cut(params)
    f_w = formation_water_cut(params)

    # thermal.py needs the per-cycle steam volume; field_params.json has no
    # such per-cycle key, so we extend a shallow copy. ipr.py reads the heated
    # radius and zone temperature from the same copy (T1-A), and thermal.py
    # reads the running produced-fluid enthalpy from it (T1-B delta).
    params_run = dict(params)
    params_run["steam_t"] = steam_t
    params_run["Q_retained_J"] = thermal.retained_heat_J(params_run)
    params_run["Q_removed_J"] = 0.0

    # T1-C: near-well pressure state.
    P_res_base = reservoir_pressure_kPa(params)
    P_boost_kPa = pressure_boost_kPa_per_t(params) * steam_t
    # rev 11: the near-well pressure cannot be charged above the pressure the
    # steam is injected at (the sandface pressure is its only source). With
    # P_sandface <= P_res nothing is injected against the reservoir: no charge
    # (and thermal.steam_state_check warns).
    P_sf = steam_st.get("P_sandface_kPa")
    recharge_capped = False
    if P_sf is not None:
        room = max(P_sf - P_res_base, 0.0)
        if P_boost_kPa > room:
            P_boost_kPa = room
            recharge_capped = True
    P_wf_kPa = _pump_intake_pressure_kPa(params)

    inject_days = steam_t / injection_rate_tpd
    soak_end_day = inject_days + soak_days
    # rev 13: the counterfactual obeys the same float policy (css.cold_counterfactual)
    cold = cold_counterfactual_well(params_cold, spm_floor=spm_floor, policy=policy,
                                    mode=cold_counterfactual)
    T0 = reservoir_params["T_initial_C"]

    def _p_res_at(day: float) -> float:
        """Charged linearly through injection, bleeding exponentially after."""
        if day <= 0.0:
            return P_res_base
        if day < inject_days:
            return P_res_base + P_boost_kPa * (day / inject_days)
        return P_res_base + P_boost_kPa * math.exp(-(day - inject_days) / TAU_BLEED_D)

    rows: list[dict] = []
    day = 0.0

    # --- inject + soak: well is not producing (shut in). ---
    while day < soak_end_day - 1e-9:
        phase = "inject" if day < inject_days - 1e-9 else "soak"
        T_avg_C, r_h = thermal.steam_zone_temperature(day, params_run)
        mu = viscosity.mu_cP(T_avg_C, params)
        steam_cum = min(injection_rate_tpd * day, steam_t) if phase == "inject" else steam_t

        rows.append({
            "day": day,
            "phase": phase,
            "T_res_C": T_avg_C,
            "mu_cP": mu,
            "P_res_kPa": _p_res_at(day),
            "oil_m3d": 0.0,
            "steam_t_cum": steam_cum,
            "energy_kWh": 0.0,
            "rod_load_kN": 0.0,
            "floating_index": 0.0,
            "spm": 0.0,
            "fillage": 0.0,
            "v_fall_ms": srp.fall_velocity_ms(mu, params, T_C=T_avg_C),
            "heated_radius_m": r_h,
            "uplift": 1.0,
            "pump_limited": False,
            "electric_kWh": 0.0,
            "oil_cold_m3d": cold["oil_m3d"],
            "electric_cold_kWh": cold["electric_kWh_d"],
            "water_cut": 0.0,
            "water_m3d": 0.0,
            "condensate_m3d": 0.0,
            "peak_prl_kN": 0.0,
        })
        day += dt_days

    # --- rev 11: condensate tank (mixing cell) for the water-cut state ------
    _, r_h_end = thermal.steam_zone_temperature(max(inject_days, 1e-9), params_run)
    res = params["reservoir"]
    V_pore = res["porosity"] * math.pi * r_h_end ** 2 * res["thickness_m"]
    W_cond = condensate_recovery_frac(params) * steam_t if wc_model == "state" else 0.0
    W_cond0 = W_cond

    # --- produce: pump runs, oil rate declines as the heated zone cools. ---
    day = soak_end_day
    produce_days_elapsed = 0.0
    peak_oil = -1.0
    alarm_run_days = 0.0          # rev 12: consecutive float-alarm days
    end_reason = "max_days"
    while produce_days_elapsed < MAX_PRODUCE_DAYS:
        T_avg_C, r_h = thermal.steam_zone_temperature(day, params_run)
        mu = viscosity.mu_cP(T_avg_C, params)

        # T1-A: hand the composite-radial IPR the heated geometry/temperature.
        params_run["heated_radius_m"] = r_h
        params_run["T_avg_C"] = T_avg_C
        P_res_kPa = _p_res_at(day)
        ipr_rate_m3d = ipr.oil_rate_m3d(P_res_kPa, P_wf_kPa, mu, params_run)
        uplift = ipr.composite_uplift(mu, r_h, T_avg_C, params_run)

        # rev 11: the day's produced-stream water cut.
        if wc_model == "state":
            # rev 13: mobility-weighted share (M = 1: rev 11/12 volume weighting)
            denom = mob_M * W_cond + V_pore
            c_frac = mob_M * W_cond / denom if denom > 0.0 else 0.0
            wc_t = min(c_frac + (1.0 - c_frac) * f_w, 0.99)
        else:
            c_frac = 0.0
            wc_t = water_cut_const

        # T1-D: declining SPM schedule, bounded by the rods' fall velocity.
        # rev 10: the ceiling uses the produced-stream (emulsion) drag viscosity;
        # rev 11: at the day's water cut.
        # rev 13: margin and floor come from the float policy (pull/none: the
        # physical keep-up limit and the keep-moving floor, as rev 5-12;
        # vfd_hold / vfd_then_pull: hold FI at the target down to the VFD floor)
        spm_cap = min(spm, srp.max_spm_for_viscosity(mu, stroke_m, params, margin=sched_margin,
                                                     T_C=T_avg_C, water_cut=wc_t))
        spm_t = max(sched_floor, spm_cap)

        state = srp.pump_state(spm_t, stroke_m, mu, ipr_rate_m3d, params,
                               intake_pressure_kPa=P_wf_kPa, T_C=T_avg_C, water_cut=wc_t)
        q_oil = state["prod_rate_m3d"]
        q_liq = q_oil / max(1.0 - wc_t, 1e-6)
        q_water = q_liq - q_oil
        q_cond = min(q_liq * c_frac, W_cond / dt_days) if wc_model == "state" else 0.0

        rows.append({
            "day": day,
            "phase": "produce",
            "T_res_C": T_avg_C,
            "mu_cP": mu,
            "P_res_kPa": P_res_kPa,
            "oil_m3d": q_oil,
            "steam_t_cum": steam_t,
            "energy_kWh": state["energy_kWh_d"],
            "rod_load_kN": state["peak_rod_load_kN"],
            "floating_index": state["floating_index"],
            "spm": spm_t,
            "fillage": state["fillage"],
            "v_fall_ms": state["v_fall_ms"],
            "heated_radius_m": r_h,
            "uplift": uplift,
            "pump_limited": state["pump_limited"],
            "electric_kWh": state["electric_kWh_d"],
            "oil_cold_m3d": cold["oil_m3d"],
            "electric_cold_kWh": cold["electric_kWh_d"],
            "water_cut": wc_t,
            "water_m3d": q_water,
            "condensate_m3d": q_cond,
            "peak_prl_kN": state["peak_prl_kN"],
        })

        # T1-B: energy carried out of the heated zone by the produced oil and
        # hot water (Boberg-Lantz Qdot_p, PEH Eq. 15.74; physics v3). This is
        # what makes producing harder cool the well faster. rev 11: the water
        # is the day's actual produced water (condensate + formation).
        params_run["Q_removed_J"] += (
            thermal.produced_heat_J_per_day(q_oil, q_water, T_avg_C, params) * dt_days
        )
        W_cond = max(W_cond - q_cond * dt_days, 0.0)

        # Rate cutoff, applied past the peak (rev 11). For a rate that declines
        # from the first produce day (every rev <= 10 cycle whose first-day
        # rate clears the cutoff) this is exactly the old rule.
        if use_rate_rule and q_oil < cutoff_m3d and q_oil < peak_oil:
            end_reason = "rate_cutoff"
            break
        peak_oil = max(peak_oil, q_oil)
        # rev 12: float-onset operating rule -- the operator pulls the well /
        # re-steams once the alarm has persisted fi_alarm_days in a row.
        alarm_run_days = (alarm_run_days + dt_days
                          if state["floating_index"] > fi_line + ALARM_TOL else 0.0)
        if use_float_rule and alarm_run_days >= fi_days_needed - 1e-9:
            end_reason = "float_onset"
            break

        day += dt_days
        produce_days_elapsed += dt_days

    out = pd.DataFrame(rows, columns=_COLUMNS)
    out.attrs["dt_days"] = float(dt_days)
    out.attrs["water_cut_model"] = wc_model
    out.attrs["stroke_m"] = float(stroke_m)
    out.attrs["steam_state"] = {k: v for k, v in steam_st.items()}
    out.attrs["steam_fuel_factor"] = float(steam_st.get("fuel_factor", 1.0))
    out.attrs["P_res_base_kPa"] = float(P_res_base)
    out.attrs["recharge_kPa"] = float(P_boost_kPa)
    out.attrs["recharge_capped"] = bool(recharge_capped)
    out.attrs["condensate_initial_m3"] = float(W_cond0)
    out.attrs["heated_pore_volume_m3"] = float(V_pore)
    out.attrs["max_prl_kN"] = srp.max_prl_kN(params)
    out.attrs["cold_water_cut"] = float(cold["water_cut"])
    out.attrs["cold_floating_index"] = float(cold["floating_index"])
    out.attrs["cold_peak_prl_kN"] = float(cold["peak_prl_kN"])
    out.attrs["cold_mu_drag_cP"] = float(cold["mu_drag_cP"])
    out.attrs["produce_end_rule"] = end_rule
    out.attrs["produce_end_reason"] = end_reason
    out.attrs["fi_alarm"] = float(fi_line)
    out.attrs["fi_alarm_days"] = float(fi_days_needed)
    # rev 13
    out.attrs["float_policy"] = policy
    out.attrs["spm_start"] = float(spm)
    out.attrs["schedule_margin"] = float(sched_margin)
    out.attrs["schedule_floor_spm"] = float(sched_floor)
    out.attrs["cold_counterfactual"] = cold["mode"]
    out.attrs["cold_status"] = cold["status"]
    out.attrs["cold_spm"] = float(cold["spm"])
    out.attrs["cold_ipr_rate_m3d"] = float(cold["ipr_rate_m3d"])
    out.attrs["flowback_mobility_ratio"] = float(mob_M)
    P_sf_st = steam_st.get("P_sandface_kPa")
    out.attrs["injection_margin_kPa"] = (float(P_sf_st - P_res_base) if P_sf_st is not None else None)
    out.attrs["min_injection_margin_kPa"] = float(min_injection_margin_kPa(params))
    return out


def summary(df: pd.DataFrame, params: dict | None = None) -> dict:
    """Cycle-level summary metrics from a simulate_css_cycle() DataFrame.

    Args:
        df: the day-by-day frame.
        params: optional field_params.json tree. Only its "economics" block is
            read; if omitted the module defaults (identical values) are used,
            so `summary(df)` keeps working for api/ and ml/ callers.

    Returns a dict. The six original keys are unchanged:
            oil_total_m3, SOR_t_per_m3, energy_per_m3_kWh, days_total,
            max_floating_index, failures_expected
    plus, additively:
        T1-E: rod_float_damage_index, days_rods_in_compression, min_fillage,
              mean_fillage, descent_violation_days
        T1-D: mean_spm, min_spm, max_spm, pump_limited_days (rev 5)
        T1-G: oil_bbl, peak_oil_m3d, peak_oil_bbl_d, steam_cost_inr,
              cost_inr_per_bbl, co2_t, co2_kg_per_bbl, revenue_inr, margin_inr,
              margin_inr_per_cycle_day
        T1-B: bl_uncertainty_frac (the published 42 % band; never quote a bare
              number without it)
        Economics v2 (27 Sep 2026; all additive, gross keys unchanged):
              window_days, electric_kWh, electric_kWh_per_m3, power_cost_inr,
              opex_fixed_inr, opex_inr, margin_with_opex_inr,
              margin_with_opex_inr_per_cycle_day,
              cold_rate_m3d, cold_well_economic, oil_cold_baseline_m3,
              oil_incremental_m3, oil_incremental_bbl, SOR_incremental,
              margin_incremental_inr, margin_incremental_inr_per_cycle_day,
              margin_incremental_inr_per_t_steam, cadp_resteam_day,
              cadp_resteam_rate_m3d, cadp_margin_incremental_inr_per_cycle_day
        `energy_per_m3_kWh` is polished-rod kWh per m3 (srp.py v2 energy);
        `electric_kWh_per_m3` is the grid figure (/ surface efficiency).
    """
    econ = dict(_DEFAULT_ECONOMICS)
    if params and params.get("economics"):
        econ.update(params["economics"])

    # rev 10 dt fix (external review): the rate columns are per DAY, so every
    # total is sum(rate) * dt. Before rev 10 they were plain sums, which is
    # only right at dt = 1 d (SOR halved at dt = 0.5 d, quartered at 0.25 d).
    dt = _row_dt_days(df) if len(df) else 1.0
    oil_total_m3 = float(df["oil_m3d"].sum()) * dt
    steam_t_total = float(df["steam_t_cum"].max()) if len(df) else 0.0
    energy_total_kWh = float(df["energy_kWh"].sum()) * dt
    days_total = float(df["day"].max() - df["day"].min()) if len(df) else 0.0
    max_floating_index = float(df["floating_index"].max()) if len(df) else 0.0

    # ASSUMPTION: guard against a degenerate zero-oil cycle rather than
    # raising a ZeroDivisionError; SOR/energy-per-m3 are undefined (inf).
    if oil_total_m3 > 0:
        sor = steam_t_total / oil_total_m3
        energy_per_m3 = energy_total_kWh / oil_total_m3
    else:
        sor = float("inf")
        energy_per_m3 = float("inf")

    produce = df[df["phase"] == "produce"]
    # day counts are rows x dt (rev 10), rounded to whole days
    failures_expected = int(round((produce["floating_index"] > FLOATING_RISK_THRESHOLD + ALARM_TOL).sum()
                                  * dt))

    # --- T1-E: graded exposure instead of a threshold day-count -------------
    # A day-count returned 0 at the demo point, i.e. the alarm was decorative.
    # Rods fail by fatigue and the governing quantity is the STRESS RANGE,
    # which float widens from both ends at once (srp deep dive section 4.1), so
    # a cubed cumulative exposure at least has the right shape. Converted to
    # Miner's-rule damage in T2-E.
    if len(produce):
        fi = produce["floating_index"].clip(lower=0.0)
        float_damage = float((fi ** 3).sum()) * dt
        days_in_compression = int(round((fi >= 1.0).sum() * dt))
        min_fillage = float(produce["fillage"].min())
        mean_fillage = float(produce["fillage"].mean())
        mean_spm = float(produce["spm"].mean())
        min_spm = float(produce["spm"].min())
        max_spm = float(produce["spm"].max())
        peak_oil_m3d = float(produce["oil_m3d"].max())
        # Descent violations: days on which the commanded stroke velocity
        # exceeded the rods' drag-limited fall velocity (floating_index == 1),
        # i.e. the 2 in/s slow-descent guidance in srp.py is binding.
        descent_days = int(round((fi >= 1.0).sum() * dt))
        pump_limited_days = (int(round(produce["pump_limited"].sum() * dt))
                             if "pump_limited" in produce else 0)
    else:
        float_damage = 0.0
        days_in_compression = 0
        min_fillage = mean_fillage = 0.0
        mean_spm = min_spm = max_spm = 0.0
        peak_oil_m3d = 0.0
        descent_days = 0
        pump_limited_days = 0

    # --- T1-G: rupees and CO2 ----------------------------------------------
    bbl = oil_total_m3 * econ["bbl_per_m3"]
    # rev 11: fuel per tonne scales with the wellhead enthalpy at the chosen
    # injection pressure (thermal.steam_state fuel_factor; 1.0 at 91 kgf/cm2
    # and in legacy mode, +/-0.2 % over 85-97 kgf/cm2).
    fuel_factor = float(df.attrs.get("steam_fuel_factor", 1.0)) if hasattr(df, "attrs") else 1.0
    steam_cost_inr = steam_t_total * steam_cost_inr_per_t(econ) * fuel_factor
    co2_kg = steam_t_total * co2_kg_per_t_steam(econ) * fuel_factor
    revenue_inr = bbl * econ["oil_price_inr_per_bbl"]
    margin_inr = revenue_inr - steam_cost_inr - econ["fixed_cost_inr_per_cycle"]

    # --- Economics v2: opex, cold baseline, incremental ------------------
    econ_v2 = _incremental_economics(df, econ, steam_t_total, days_total, revenue_inr,
                                     steam_cost_inr, margin_inr, dt=dt)

    return {
        # --- original six, unchanged ---
        "oil_total_m3": oil_total_m3,
        "SOR_t_per_m3": sor,
        "energy_per_m3_kWh": energy_per_m3,
        "days_total": days_total,
        "max_floating_index": max_floating_index,
        "failures_expected": failures_expected,
        # --- T1-E ---
        "rod_float_damage_index": float_damage,
        "days_rods_in_compression": days_in_compression,
        "min_fillage": min_fillage,
        "mean_fillage": mean_fillage,
        "descent_violation_days": descent_days,
        # --- T1-D ---
        "mean_spm": mean_spm,
        "min_spm": min_spm,
        "max_spm": max_spm,
        # --- rev 5: days on which the pump, not the reservoir, set the rate ---
        "pump_limited_days": pump_limited_days,
        # --- T1-G ---
        "oil_bbl": bbl,
        "peak_oil_m3d": peak_oil_m3d,
        "peak_oil_bbl_d": peak_oil_m3d * econ["bbl_per_m3"],
        "steam_cost_inr": steam_cost_inr,
        "cost_inr_per_bbl": steam_cost_inr / bbl if bbl > 0 else float("inf"),
        "co2_t": co2_kg / 1000.0,
        "co2_kg_per_bbl": co2_kg / bbl if bbl > 0 else float("inf"),
        "revenue_inr": revenue_inr,
        "margin_inr": margin_inr,
        "margin_inr_per_cycle_day": margin_inr / days_total if days_total > 0 else float("-inf"),
        # --- T1-B ---
        "bl_uncertainty_frac": thermal.BL_UNCERTAINTY_FRAC,
        # --- Economics v2 ---
        **econ_v2,
        # --- rev 11: water-cut state, steam state, stroke, unit load ---
        **_water_and_controls(df, produce, dt),
    }


def _water_and_controls(df: pd.DataFrame, produce: pd.DataFrame, dt: float) -> dict:
    """rev 11 summary keys (additive): water-cut profile, float timing, PRL cap,
    and the steam/stroke controls the cycle ran at (from df.attrs)."""
    nan = float("nan")
    attrs = df.attrs if hasattr(df, "attrs") else {}
    out: dict = {}
    has_w = "water_cut" in df.columns and len(produce)
    if has_w:
        wc = produce["water_cut"].to_numpy()
        oil = produce["oil_m3d"].to_numpy()
        wat = produce["water_m3d"].to_numpy()
        cond = produce["condensate_m3d"].to_numpy()
        liq = float((oil + wat).sum()) * dt
        fi = produce["floating_index"].to_numpy()
        t0 = float(df["day"].iloc[0])
        t_prod0 = float(produce["day"].iloc[0])
        k = int(fi.argmax())
        alarm = fi > FLOATING_RISK_THRESHOLD + ALARM_TOL
        k_alarm = int(alarm.argmax()) if alarm.any() else None
        prl = produce["peak_prl_kN"].to_numpy()
        cap = attrs.get("max_prl_kN")
        out.update({
            "water_cut_start": float(wc[0]),
            "water_cut_end": float(wc[-1]),
            "water_cut_liquid_weighted": float(wat.sum() * dt / liq) if liq > 0 else nan,
            "water_total_m3": float(wat.sum()) * dt,
            "condensate_produced_m3": float(cond.sum()) * dt,
            "condensate_initial_m3": float(attrs.get("condensate_initial_m3", nan)),
            "max_floating_index_produce_day": float(produce["day"].iloc[k]) - t_prod0,
            "max_floating_index_cycle_day": float(produce["day"].iloc[k]) - t0,
            "water_cut_at_max_floating_index": float(wc[k]),
            "first_float_alarm_produce_day": (float(produce["day"].iloc[k_alarm]) - t_prod0
                                              if k_alarm is not None else None),
            "max_peak_prl_kN": float(prl.max()),
            # rev 12: timing of the produce end relative to the peak (the
            # fragility metric of TIER1 10.9/11: a cycle that ends within a few
            # days of its peak never had a produce phase worth the steam)
            "produce_days": float(len(produce)) * dt,
            "peak_oil_produce_day": float(produce["day"].iloc[int(oil.argmax())]) - t_prod0,
            "produce_end_days_after_peak": (float(produce["day"].iloc[-1])
                                            - float(produce["day"].iloc[int(oil.argmax())])),
            "max_prl_kN": cap,
            "prl_cap_exceeded_days": (int(round(float((prl > cap).sum()) * dt))
                                      if cap is not None else 0),
        })
    else:
        out.update({k: nan for k in ("water_cut_start", "water_cut_end", "water_cut_liquid_weighted",
                                     "water_total_m3", "condensate_produced_m3", "max_peak_prl_kN")})
        out.update({"prl_cap_exceeded_days": 0, "max_prl_kN": attrs.get("max_prl_kN")})
    st = attrs.get("steam_state") or {}
    out.update({
        "water_cut_model": attrs.get("water_cut_model"),
        "stroke_m": attrs.get("stroke_m"),
        "P_wellhead_kgf_cm2": st.get("P_wellhead_kgf_cm2"),
        "T_wellhead_C": st.get("T_wellhead_C"),
        "P_sandface_kPa": st.get("P_sandface_kPa"),
        "T_sandface_C": st.get("T_sandface_C"),
        "h_delivered_kJkg": (st["h_delivered_J_per_kg"] / 1000.0
                             if st.get("h_delivered_J_per_kg") is not None else None),
        "steam_fuel_factor": attrs.get("steam_fuel_factor", 1.0),
        "recharge_kPa": attrs.get("recharge_kPa"),
        "recharge_capped": attrs.get("recharge_capped"),
        "cold_water_cut": attrs.get("cold_water_cut"),
        "cold_floating_index": attrs.get("cold_floating_index"),
        "cold_peak_prl_kN": attrs.get("cold_peak_prl_kN"),
        "cold_mu_drag_cP": attrs.get("cold_mu_drag_cP"),
        # rev 12: produce-end operating rule and what actually ended the cycle
        "produce_end_rule": attrs.get("produce_end_rule"),
        "produce_end_reason": attrs.get("produce_end_reason"),
        "fi_alarm_days_rule": attrs.get("fi_alarm_days"),
        # rev 13: float policy, the counterfactual it implies, injectivity
        "float_policy": attrs.get("float_policy"),
        "schedule_floor_spm": attrs.get("schedule_floor_spm"),
        "cold_counterfactual": attrs.get("cold_counterfactual"),
        "cold_status": attrs.get("cold_status"),
        "cold_spm": attrs.get("cold_spm"),
        "flowback_mobility_ratio": attrs.get("flowback_mobility_ratio"),
        "injection_margin_kPa": attrs.get("injection_margin_kPa"),
        "min_injection_margin_kPa": attrs.get("min_injection_margin_kPa"),
        "injection_ok": (None if attrs.get("injection_margin_kPa") is None else
                         bool(attrs["injection_margin_kPa"]
                              >= float(attrs.get("min_injection_margin_kPa") or 0.0) - 1e-9)),
    })
    if has_w and attrs.get("schedule_floor_spm") is not None:
        spm_arr = produce["spm"].to_numpy()
        floor = float(attrs["schedule_floor_spm"])
        start = float(attrs.get("spm_start", spm_arr.max()))
        out["days_at_schedule_floor"] = int(round(float((spm_arr <= floor + 1e-9).sum()) * dt))
        out["days_vfd_slowed"] = int(round(float((spm_arr < start - 1e-9).sum()) * dt))
    return out


def _incremental_economics(df: pd.DataFrame, econ: dict, steam_t_total: float,
                           days_total: float, revenue_inr: float,
                           steam_cost_inr: float, margin_inr: float,
                           dt: float | None = None) -> dict:
    """Economics v2 keys for summary(): opex, cold baseline, incremental oil.

    Incremental cash on each day = (stimulated - cold) oil x price
    - (stimulated - cold) electricity x tariff; the fixed daily opex is paid
    in both cases and cancels, UNLESS the cold well cannot cover its own
    opex, in which case the counterfactual well is shut in (cash 0) and the
    incremental margin equals the with-opex gross margin. Upfront: steam +
    `fixed_cost_inr_per_cycle`.

    CADP (Rivero & Heintz, via PEH ch. 15): re-steam when the day's
    incremental cash falls below the cumulative-average incremental profit per
    elapsed day, i.e. at the argmax over produce days of cumulative
    incremental margin / elapsed days. `cadp_resteam_day` is that day (days
    from the start of injection); when it is the cycle's last day the rate
    cutoff ended the cycle before the economic re-steam point.
    """
    price_m3 = econ["oil_price_inr_per_bbl"] * econ["bbl_per_m3"]
    tariff = float(econ.get("electricity_inr_per_kWh", 0.0) or 0.0)
    opex_d = float(econ.get("opex_inr_per_day", 0.0) or 0.0)
    nan = float("nan")

    produce = df[df["phase"] == "produce"]
    if dt is None:
        dt = _row_dt_days(df) if len(df) else 1.0
    window_days = days_total + dt if len(df) else 0.0

    has_elec = "electric_kWh" in df.columns
    # rev 10 dt fix: daily kWh x dt
    electric_kWh = float(df["electric_kWh"].sum()) * dt if has_elec else nan
    power_cost_inr = electric_kWh * tariff if has_elec else nan
    opex_fixed_inr = opex_d * window_days
    opex_inr = power_cost_inr + opex_fixed_inr
    margin_with_opex = margin_inr - opex_inr
    oil_total_m3 = float(df["oil_m3d"].sum()) * dt

    out = {
        "window_days": window_days,
        "electric_kWh": electric_kWh,
        "electric_kWh_per_m3": electric_kWh / oil_total_m3 if oil_total_m3 > 0 else float("inf"),
        "power_cost_inr": power_cost_inr,
        "opex_fixed_inr": opex_fixed_inr,
        "opex_inr": opex_inr,
        "margin_with_opex_inr": margin_with_opex,
        "margin_with_opex_inr_per_cycle_day": (
            margin_with_opex / window_days if window_days > 0 else float("-inf")),
    }
    if "oil_cold_m3d" not in df.columns or not len(df):
        out.update({k: nan for k in (
            "cold_rate_m3d", "oil_cold_baseline_m3", "oil_incremental_m3", "oil_incremental_bbl",
            "SOR_incremental", "margin_incremental_inr", "margin_incremental_inr_per_cycle_day",
            "margin_incremental_inr_per_t_steam", "cadp_resteam_day", "cadp_resteam_rate_m3d",
            "cadp_margin_incremental_inr_per_cycle_day")})
        out["cold_well_economic"] = None
        return out

    q_cold = float(df["oil_cold_m3d"].iloc[0])      # the COUNTERFACTUAL's production (rev 13)
    e_cold = float(df["electric_cold_kWh"].iloc[0])
    # rev 13: the physical cold rate (the well's unstimulated capability, what
    # uplift = peak / cold is measured against) is kept separately from what the
    # counterfactual produces (0 when the float policy shuts the cold well in)
    attrs = df.attrs if hasattr(df, "attrs") else {}
    q_cold_phys = float(attrs.get("cold_ipr_rate_m3d", q_cold))
    cold_cash_d = q_cold * price_m3 - e_cold * tariff - opex_d
    cold_economic = cold_cash_d > 0.0
    oil_cold = q_cold * window_days
    oil_inc = oil_total_m3 - oil_cold

    # Incremental margin = (with-opex gross margin) - (cold well's net cash
    # over the window, or 0 if it would be shut in).
    cold_net = cold_cash_d * window_days if cold_economic else 0.0
    margin_inc = margin_with_opex - cold_net

    # --- CADP re-steam point on the incremental basis ------------------------
    upfront = steam_cost_inr + econ["fixed_cost_inr_per_cycle"]
    t0 = float(df["day"].iloc[0])
    if len(produce):
        soak_end = float(produce["day"].iloc[0]) - t0
        # Cash per day relative to the counterfactual (fixed opex cancels when
        # the cold well is economic; otherwise it is charged every day).
        base_d = cold_cash_d + opex_d if cold_economic else 0.0   # cold oil - cold power
        opex_charge = 0.0 if cold_economic else opex_d
        inc_d = (produce["oil_m3d"].to_numpy() * price_m3
                 - produce["electric_kWh"].to_numpy() * tariff
                 - base_d - opex_charge) * dt
        shut_in_cost = (base_d + opex_charge) * soak_end
        cum = -upfront - shut_in_cost + inc_d.cumsum()
        elapsed = soak_end + dt * (1 + pd.RangeIndex(len(produce)).to_numpy())
        avg = cum / elapsed
        k = int(avg.argmax())
        cadp_day = float(produce["day"].iloc[k]) - t0
        cadp_rate = float(produce["oil_m3d"].iloc[k])
        cadp_avg = float(avg[k])
    else:
        cadp_day = cadp_rate = cadp_avg = nan

    out.update({
        "cold_rate_m3d": q_cold_phys,
        "cold_counterfactual_rate_m3d": q_cold,
        "cold_well_economic": bool(cold_economic),
        "oil_cold_baseline_m3": oil_cold,
        "oil_incremental_m3": oil_inc,
        "oil_incremental_bbl": oil_inc * econ["bbl_per_m3"],
        "SOR_incremental": steam_t_total / oil_inc if oil_inc > 0 else float("inf"),
        "margin_incremental_inr": margin_inc,
        "margin_incremental_inr_per_cycle_day": (
            margin_inc / window_days if window_days > 0 else float("-inf")),
        "margin_incremental_inr_per_t_steam": (
            margin_inc / steam_t_total if steam_t_total > 0 else float("-inf")),
        "cadp_resteam_day": cadp_day,
        "cadp_resteam_rate_m3d": cadp_rate,
        "cadp_margin_incremental_inr_per_cycle_day": cadp_avg,
    })
    return out
