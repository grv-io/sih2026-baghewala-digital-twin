"""ml/uq.py -- paired Monte Carlo uncertainty quantification (26 Sep 2026).

Runs the TRUE physics twin (`twin.cycle.simulate_css_cycle` + `summary`,
~0.5 ms per cycle -- not the XGBoost surrogate) at three fixed set-point
combinations, over N_DRAWS random draws of the model's UNCERTAIN inputs
(below), and reports p10/p50/p90 bands plus paired probabilities.

The three set-point combinations (docs/model-improvement/TIER1_PROGRESS_LOG.md
sections 4.4, 5b and 8; params/CHANGELOG.md rev 5/7/8/9), point values at the
physics-v3 + Economics-v2 twin, FY25 price deck (rev 9):
    reference    1,500 t / 7 d soak  / 1.2 m3/d cutoff / 5 spm -> SOR 4.03 (incr. 5.40)
    baseline_b   1,300 t / 10 d soak / 1.3 m3/d cutoff / 5 spm -> SOR 4.06 (incr. 5.50)
                 ("published-practice (b)", BGW-8 first-cycle job, 2018)
    recommended  1,600 t / 10 d soak (fixed) / 0.70 m3/d cutoff / 4 spm -> SOR 3.59 (incr. 5.00)
                 (rev 9 cascade recommendation: minimax-regret across both price
                 decks, TIER1_PROGRESS_LOG.md section 8.6; supersedes the rev-5
                 1,700/0.85/5 point)

Economics v2 (27 Sep 2026): the headline money metric is the INCREMENTAL
margin per cycle-day (oil over the cold, unstimulated baseline for the same
calendar window, inject + soak days included; daily opex = fixed well-site
opex + pumping-unit electricity). The gross rev-5 `margin_inr_per_cycle_day`
is still carried for continuity. Paired probabilities and the tornado use the
incremental metric.

"Paired": every draw samples ONE joint realisation of the fourteen uncertain
inputs and runs ALL THREE set-point combinations through that same
realisation (same deep-copied params dict, only steam_t/soak_days/
cutoff_m3d/spm differ). That is what makes P(recommended better than
baseline) a meaningful paired probability instead of comparing two
independently-noisy distributions -- e.g. if water_cut happens to be
high on a given draw, ALL THREE points see the same high value, so a
comparison between two of them isolates the effect of the SET-POINT choice,
not of drawing different physics by chance.

Uncertain inputs and ranges (each overrides a copy of params/field_params.json
-- engine defaults in twin/*.py are never edited; see field-by-field notes on
UNCERTAIN_INPUTS below for the source of every bound):

    fluid.water_cut          U[0.70, 0.90]   base 0.85  (now the delta input)
    reservoir.thickness_m    U[8, 20]        base 12.0  (m, net pay)
    diesel_bulk_discount_frac U[0.0, 0.30]   base 0.30  (steam Rs5,856-8,366/t)
    oil_price_inr_per_bbl    +/-15% of the running deck's base (rev 9: FY25 deck
                             base Rs5,992/bbl [U 5,093-6,891]; FY26-floor deck
                             base Rs4,840/bbl [U 4,114-5,566] -- see "decks" below)
    fluid.mu_ref_cP          U[8,000, 15,000] base 11,500
    srp_geometry_scale       U[0.90, 1.10]   base 1.0   (stroke_m, plunger_d_m)
    opex_inr_per_day         U[2,500, 7,500] base 5,000 (+/-50 %, [ASSUMPTION])

rev 10 (hardening after the external technical review, 27 Sep 2026) adds the
unsourced physics constants that were module globals until now -- the review
showed "P(rec > base) = 100 %" held only because they were not sampled:

    ipr.s_cold               U[0, 8]         base 5    (cold damage skin, [ASSUMPTION])
    srp.k_visc               U[5, 15]        base 10   (rod-drag coefficient, +/-50 %)
    reservoir.pressure_boost_kPa_per_t U[0.5, 2.0] base 1.0 ([CALIBRATED], no mechanism)
    fluid.mu_anchor_cP       U[30, 80]       base 50   (mu at 150 C, SPEC placeholder)
    economics.fixed_cost_inr_per_cycle U[7.5 L, 22.5 L] base 15 L (+/-50 %)
    reservoir.P_current_kPa  U[7,400, 11,400] base 11,400 (the PS says "low
                             reservoir pressure"; the base is the virgin value,
                             i.e. the OPTIMISTIC edge -- stated, not hidden)
    fluid.emulsion_inversion_wc U[0.60, 0.75] base 0.70 (produced-stream W/O -> O/W)

The new inputs are drawn AFTER the original seven, so the original seven
columns of the draw matrix are unchanged for a given seed.

rev 11 (physics wave 3, 27 Sep 2026): water cut is a STATE (condensate
flowback + formation water, twin/cycle.py), so the constant `fluid.water_cut`
is no longer read. Its slot (first column, same uniform draws) now samples
the formation water cut; the condensate recovery fraction is appended:

    fluid.formation_water_cut U[0.30, 0.60]  base 0.45 ([ASSUMPTION], replaces water_cut)
    fluid.condensate_recovery_frac U[0.50, 0.90] base 0.70 ([ASSUMPTION], appended)
    reservoir.P_current_kPa  U[7,400, 9,400] base 9,400 (rev 11 default = the
                             injectivity-derived upper edge, still the
                             OPTIMISTIC edge; above ~9.45 MPa steam cannot be
                             injected at 85 kgf/cm2)
    fluid.emulsion_inversion_wc U[0.60, 0.75] (unchanged)

Set-points now carry the two rev-11 controls (`stroke_in`, API stroke in
inches; `p_wellhead_kgf_cm2`). The srp_geometry_scale draw scales the stroke
of every point (and the plunger), as before.

rev 12 (physics wave 4, 27 Sep 2026): every cycle ends on the params'
produce-end rule (default "either": rate cutoff OR 3 consecutive float-alarm
days, twin/cycle.py); the W/O drag branch is Pal-Rhodes capped at 10x, and one
input is appended (so every earlier column's draws are unchanged):

    fluid.emulsion_phi_star  U[0.65, 1.00]   base 0.84 ([ASSUMPTION], mu_r(45 %) ~9x -> 3.3x)

"recommended" = the rev-12 canonical 5-D point (1,000 t / 10 d / cutoff 0.60 /
3 spm / 64 in / 85 kgf/cm2); "conservative" (the same settings operated with
the alarm line at 0.5: pull once FI > 0.5 persists 3 d -- a per-point
`fi_alarm` override), "conservative_fixed_cutoff" (FI <= 0.5 all cycle at base
physics by ending on a 1.55 m3/d cutoff: the fragile alternative) and the
rev-11 point are added. Per point the summary also
reports the robustness metrics of TIER1 section 11: P(ended by the float-onset
rule), P(any float-alarm day), P(alarm days > css.fi_alarm_days) and the
FRAGILITY P(produce phase ends within 5 days of the peak) -- 41 % for the
rev-11 point under rev-11 physics.

rev 13 (physics wave 5, 27 Sep 2026): the operating policy is a control and
the structural choices that carried the rev-12 gain are now sampled. Appended
(earlier columns' draws unchanged):

    fluid.emulsion_mu_r_max      U[5, 20]      base 10 (the W/O cap)
    css.fi_alarm_days            U[1, 14] -> whole days, base 3
    fluid.emulsion_inversion_band_wc U[0.05, 0.10] base 0.075 (smooth inversion)
    fluid.flowback_mobility_ratio DISCRETE {1, 3, 10} (equal probability), base 1
    css.cold_counterfactual      DISCRETE {policy, pumpable} (50/50), base policy
(K_VISC was already U[5, 15].) The diesel-discount base is now 0.15 (mid of
U[0, 0.30]). Every point carries a `float_policy`; POINTS holds the rev-13
recommendation (VFD-hold), baseline (b) under VFD-hold / pull / none and the
best point WITHIN each of those policies (SAME_POLICY_POINTS), so the
same-policy comparison -- the only fair one -- is reported
(`P_gt_baseline_same_policy`, `gain_vs_baseline_bands`). Paired "beats the
baseline" probabilities use GAIN_METRIC = net cash per cycle-day
(`margin_with_opex_inr_per_cycle_day`), in which the cold counterfactual
cancels. New per-point metrics: `injection_ok` (P_sandface - P_current >=
steam.min_injection_margin_kPa), `cold_shut_in`, `alarm_days_exceed_rule`
(against the draw's own fi_alarm_days).

rev 9 (27 Sep 2026): the bake now runs multiple passes -- the FY25 realisation
deck (`economics.oil_price_inr_per_bbl` as shipped in field_params.json,
Rs5,992/bbl) and the FY26 planning-floor deck
(`economics.oil_price_presets.fy26_floor_65`, Rs4,840/bbl) -- each with its
own +/-15% oil-price band centred on that deck's own base. The primary
(top-level) result is the FY25 deck; the other decks are additionally nested
under `decks.<name>`, and the FY25 pass is also mirrored under
`decks.fy25_realisation` for a uniform access pattern. Use `--deck <name>` to
run (and print) just one pass standalone; with no `--deck`, `main()` runs
every deck in DECKS and writes the combined summary.

rev 13 (wave 5): a THIRD deck, `fy25_net_of_levies`
(`economics.oil_price_presets.fy25_net_of_levies`, ~Rs3,600/bbl -- OIL's FY25
realisation net of royalty + OID cess, TIER1_PROGRESS_LOG.md section 12.10),
is added (DECKS = fy25_realisation / fy26_floor / fy25_net_of_levies); its
+/-15% oil-price band is centred on ITS OWN Rs3,600/bbl base, same convention
as the other two.

NOT varied: `bl_delta_factor`. Physics v3 (params/CHANGELOG.md rev 7,
docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md) showed it is the 1/2 in
Boberg & Lantz's own delta (PEH Eqs. 15.70/15.73) and the only value that
conserves energy with no conduction -- a definition, not an uncertain input.
It is held at thermal.BL_DELTA_FACTOR = 0.5. The remaining delta uncertainty
lives in `fluid.water_cut`, which stays at U[0.70, 0.90].

Usage:
    python ml/uq.py [--draws 1500] [--seed 42] [--params params/field_params.json]
                     [--out-json ml/models/uq_summary.json] [--out-csv ml/models/uq_samples.csv]

Writes `ml/models/uq_summary.json` and `ml/models/uq_samples.csv`, and prints
a readable table. Deterministic: seed 42 (docs/SPEC.md "Deterministic with
seed 42").
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

# Allow `python ml/uq.py` (run directly) to find the `twin` package regardless
# of process cwd, same pattern as twin/generate_data.py and ml/optimize.py.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from twin import cycle  # noqa: E402  (see sys.path shim above)

SEED = 42
N_DRAWS = 1500

PARAMS_PATH = _ROOT / "params" / "field_params.json"
OUT_JSON = Path(__file__).resolve().parent / "models" / "uq_summary.json"
OUT_CSV = Path(__file__).resolve().parent / "models" / "uq_samples.csv"

# --------------------------------------------------------------------------
# The three set-point combinations under uncertainty. Order matters only for
# display; POINT order below is the order tables are printed in.
# --------------------------------------------------------------------------
_MID = dict(stroke_in=86.0, p_wellhead_kgf_cm2=91.0)   # rev 11: baseline controls
_BASE_B = dict(steam_t=1300, soak_days=10, cutoff_m3d=1.3, spm=5.0, **_MID)
POINTS: dict[str, dict[str, float]] = {
    # rev 13: every point carries its float policy; points without one run the
    # params' css.float_policy (vfd_hold; recommended, but the shipped params
    # default stays `pull` -- the calibration anchor was made under `pull`)
    "reference":   dict(steam_t=1500, soak_days=7,  cutoff_m3d=1.2,  spm=5.0, **_MID),
    "baseline_b":  dict(_BASE_B, float_policy="vfd_hold"),
    # rev 13: canonical 5-D + policy recommendation (ml/recommend_physics.py
    # best_settings_physics_5d over pull / vfd_hold / vfd_then_pull, injection
    # margin >= 400 kPa, minimax regret FY25 + $65) -- TIER1 section 12.
    "recommended": dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=4.5,
                        stroke_in=64.0, p_wellhead_kgf_cm2=89.0, float_policy="vfd_hold"),
    # the same settings, the VFD holding FI at 0.5 and pulling at 0.5 (conservative level)
    "conservative": dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=4.5,
                         stroke_in=64.0, p_wellhead_kgf_cm2=89.0, float_policy="vfd_hold", fi_alarm=0.5),
    # SAME-POLICY pairs (the only fair comparison): baseline (b) and the best point
    # WITHIN that policy, both operated under it
    "baseline_b__pull": dict(_BASE_B, float_policy="pull"),
    "recommended__pull": dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=3.0,
                              stroke_in=64.0, p_wellhead_kgf_cm2=89.0, float_policy="pull"),
    "baseline_b__none": dict(_BASE_B, float_policy="none"),
    "recommended__none": dict(steam_t=1000, soak_days=10, cutoff_m3d=1.45, spm=3.0,
                              stroke_in=64.0, p_wellhead_kgf_cm2=89.0, float_policy="none"),
    # rev-12 canonical point, as operated in rev 12 (pull); fails the rev-13 injection margin
    "recommended_rev12": dict(steam_t=1000, soak_days=10, cutoff_m3d=0.60, spm=3.0,
                              stroke_in=64.0, p_wellhead_kgf_cm2=85.0, float_policy="pull"),
}
POINT_LABELS = {
    "reference": "Reference cycle (1,500 t / 7 d / 1.2 m3/d / 5 spm / 86 in / 91 kgf/cm2, params policy)",
    "baseline_b": "Baseline (b), VFD-hold (1,300 t / 10 d / 1.3 m3/d / 5 spm / 86 in / 91 kgf/cm2)",
    "recommended": "Recommendation, rev 13 (1,000 t / 10 d / 0.60 m3/d / 4.5 spm / 64 in / 89 kgf/cm2, VFD-hold)",
    "conservative": "Conservative, rev 13 (rec settings, VFD holds and pulls at FI 0.5)",
    "baseline_b__pull": "Baseline (b), pull policy (rev 12 operation)",
    "recommended__pull": "Best point under the pull policy (1,000 / 0.60 / 3 spm / 64 in / 89)",
    "baseline_b__none": "Baseline (b), no float response (rods float to the 1.3 cutoff)",
    "recommended__none": "Best float-safe point with no float response (1,000 / 1.45 / 3 spm / 64 in / 89)",
    "recommended_rev12": "Recommendation, rev 12 (1,000 / 0.60 / 3 spm / 64 in / 85, pull)",
}
# rev 13: (recommended point, baseline point) per float policy for the same-policy comparison
SAME_POLICY_POINTS = {
    "vfd_hold": ("recommended", "baseline_b"),
    "pull": ("recommended__pull", "baseline_b__pull"),
    "none": ("recommended__none", "baseline_b__none"),
}
# rev 13 (wave 5 bake): the 5 points the coordinator asked for the per-counterfactual
# P(incremental > 0) breakdown at -- reference / baseline (b) VFD-hold / the
# canonical recommendation / its conservative (FI 0.5) variant / baseline (b) pull.
FOCUS_POINTS_CF = ["reference", "baseline_b", "recommended", "conservative", "baseline_b__pull"]

# Metrics pulled from cycle.summary() for every draw, at every point.
METRICS = [
    "SOR_t_per_m3", "SOR_incremental", "oil_bbl", "oil_incremental_bbl",
    "margin_inr_per_cycle_day", "margin_incremental_inr_per_cycle_day",
    "co2_t", "max_floating_index",
    # rev 11
    "water_cut_start", "water_cut_end", "failures_expected",
    # rev 12: produce-end rule and fragility
    "ended_by_float_onset", "produce_days", "produce_end_days_after_peak",
    # rev 13: net cash per cycle-day (the counterfactual-free GAIN metric), the
    # injectivity gate and the counterfactual's status
    "margin_with_opex_inr_per_cycle_day", "injection_ok", "cold_shut_in",
    "alarm_days_exceed_rule",
]
# rev 13: paired "beats the baseline" comparisons use the net cash per cycle-day:
# the cold counterfactual cancels (equal to the incremental difference when both
# points share one counterfactual, and still correct when their float policies --
# hence their counterfactuals under css.cold_counterfactual "policy" -- differ).
GAIN_METRIC = "margin_with_opex_inr_per_cycle_day"
# rev 12: fragility threshold -- a produce phase that ends within this many
# days of its own peak never earned back the steam (TIER1 10.9 / 11).
FRAGILE_DAYS_AFTER_PEAK = 5.0
# Economics v2: the money metric every probability / tornado uses.
MONEY_METRIC = "margin_incremental_inr_per_cycle_day"


def _set_water_cut(p: dict, v: float) -> None:
    p["fluid"]["water_cut"] = float(v)


def _set_thickness_m(p: dict, v: float) -> None:
    p["reservoir"]["thickness_m"] = float(v)


def _set_diesel_bulk_discount(p: dict, v: float) -> None:
    p["economics"]["diesel_bulk_discount_frac"] = float(v)


def _set_oil_price(p: dict, v: float) -> None:
    p["economics"]["oil_price_inr_per_bbl"] = float(v)


def _set_mu_ref(p: dict, v: float) -> None:
    p["fluid"]["mu_ref_cP"] = float(v)


def _set_opex_per_day(p: dict, v: float) -> None:
    p["economics"]["opex_inr_per_day"] = float(v)


def _set_s_cold(p: dict, v: float) -> None:
    p.setdefault("ipr", {})["s_cold"] = float(v)


def _set_k_visc(p: dict, v: float) -> None:
    p["srp"]["k_visc"] = float(v)


def _set_pressure_boost(p: dict, v: float) -> None:
    p["reservoir"]["pressure_boost_kPa_per_t"] = float(v)


def _set_mu_anchor(p: dict, v: float) -> None:
    p["fluid"]["mu_anchor_cP"] = float(v)


def _set_fixed_cost(p: dict, v: float) -> None:
    p["economics"]["fixed_cost_inr_per_cycle"] = float(v)


def _set_p_current(p: dict, v: float) -> None:
    p["reservoir"]["P_current_kPa"] = float(v)


def _set_inversion_wc(p: dict, v: float) -> None:
    p["fluid"]["emulsion_inversion_wc"] = float(v)


def _set_srp_geometry_scale(p: dict, v: float, base_stroke: float, base_plunger: float) -> None:
    p["srp"]["stroke_m"] = base_stroke * float(v)
    p["srp"]["plunger_d_m"] = base_plunger * float(v)
    p["srp"]["_uq_geometry_scale"] = float(v)   # rev 11: applied to each point's stroke too


def _set_formation_water_cut(p: dict, v: float) -> None:
    p["fluid"]["formation_water_cut"] = float(v)


def _set_condensate_recovery(p: dict, v: float) -> None:
    p["fluid"]["condensate_recovery_frac"] = float(v)


def _set_phi_star(p: dict, v: float) -> None:
    p["fluid"]["emulsion_phi_star"] = float(v)


# ---- rev 13 (wave 5) --------------------------------------------------------
FLOWBACK_M_LEVELS = (1.0, 3.0, 10.0)
COLD_CF_LEVELS = ("policy", "pumpable")


def _discrete(v: float, n: int) -> int:
    """Index of a U[0, n) draw into n equally likely levels (clamped)."""
    return min(max(int(np.floor(float(v))), 0), n - 1)


def _set_mu_r_max(p: dict, v: float) -> None:
    p["fluid"]["emulsion_mu_r_max"] = float(v)


def _set_fi_alarm_days(p: dict, v: float) -> None:
    p.setdefault("css", {})["fi_alarm_days"] = float(int(round(float(v))))


def _set_inversion_band(p: dict, v: float) -> None:
    p["fluid"]["emulsion_inversion_band_wc"] = float(v)


def _set_flowback_M(p: dict, v: float) -> None:
    p["fluid"]["flowback_mobility_ratio"] = FLOWBACK_M_LEVELS[_discrete(v, len(FLOWBACK_M_LEVELS))]


def _set_cold_cf(p: dict, v: float) -> None:
    p.setdefault("css", {})["cold_counterfactual"] = COLD_CF_LEVELS[_discrete(v, len(COLD_CF_LEVELS))]


def _cold_cf_level_mask(draws: dict[str, np.ndarray], level: str) -> np.ndarray:
    """rev 13: boolean mask of which draws sampled `level` ("policy" or
    "pumpable") for the cold_counterfactual uncertain input -- decodes the
    same U[0, len(COLD_CF_LEVELS)) draw `_set_cold_cf` itself discretises."""
    idx = COLD_CF_LEVELS.index(level)
    vals = draws["cold_counterfactual"]
    levels = np.array([_discrete(v, len(COLD_CF_LEVELS)) for v in vals])
    return levels == idx


def _shut_in_incremental_positive(
    base_params: dict, uncertain: dict[str, dict[str, Any]], draws: dict[str, np.ndarray],
    points: list[str],
) -> dict[str, float]:
    """rev 13: P(incremental margin/cycle-day > 0) at `points`, forcing the
    cold counterfactual to "shut_in" on EVERY draw (rather than the 50/50
    policy/pumpable split `cold_counterfactual` itself samples) -- the third
    counterfactual level for the P(incremental > 0) per-counterfactual
    breakdown. Every OTHER uncertain input is applied from the SAME draws as
    the main paired MC pass (paired, not a fresh sample)."""
    n = len(next(iter(draws.values())))
    incr: dict[str, list[float]] = {pt: [] for pt in points}
    for i in range(n):
        p_i = copy.deepcopy(base_params)
        for name, spec in uncertain.items():
            if name == "cold_counterfactual":
                continue
            spec["setter"](p_i, draws[name][i])
        p_i.setdefault("css", {})["cold_counterfactual"] = "shut_in"
        for pt in points:
            if pt not in POINTS:
                continue
            out = _run_point(p_i, POINTS[pt])
            incr[pt].append(out[MONEY_METRIC])
    return {pt: (float(np.mean(np.asarray(v) > 0)) if v else float("nan")) for pt, v in incr.items()}


def build_uncertain_inputs(base_params: dict) -> dict[str, dict[str, Any]]:
    """Name -> {low, high, base, setter(params, value)}.

    Every bound is sourced from docs/model-improvement/TIER1_PROGRESS_LOG.md
    section 4.3/4.6 (one-at-a-time sensitivities and the porosity/thickness
    open item) and params/CHANGELOG.md rev 4/rev 5, cross-referenced in the
    module docstring above. `base` is the field_params.json value the point
    estimate (non-UQ) runs use, so the UQ draw distribution is centred, not
    necessarily symmetric, around it.
    """
    base_stroke = base_params["srp"]["stroke_m"]
    base_plunger = base_params["srp"]["plunger_d_m"]
    fixed_cost = float(base_params["economics"].get("fixed_cost_inr_per_cycle", 1.5e6))
    res = base_params["reservoir"]
    p_virgin = float(res["P_initial_kPa"])
    p_now = res.get("P_current_kPa")
    wc_state = cycle.water_cut_model(base_params) == "state"
    return {
        # rev 11: first slot (same draws) = the water-cut driver the physics reads
        ("formation_water_cut" if wc_state else "water_cut"): ({
            "low": 0.30, "high": 0.60,
            "base": float(base_params["fluid"].get("formation_water_cut", 0.45)),
            "setter": _set_formation_water_cut,
            "why": (
                "fluid.formation_water_cut [ASSUMPTION, rev 11]: native water cut of the reservoir "
                "liquid (cold well; non-condensate part of the stimulated stream). No Baghewala "
                "figure (OIL_DATA_REQUEST item 2). 0.30-0.60 is the stated assumption band; it "
                "decides when the late-cycle stream falls below the W/O inversion."
            ),
        } if wc_state else {
            "low": 0.70, "high": 0.90, "base": 0.85,
            "setter": _set_water_cut,
            "why": (
                "fluid.water_cut. CHANGELOG rev 4: 'ASSUMPTION, no field datum ... "
                "flagged as the third recalibration knob (lowering to ~0.75 lengthens "
                "cycles)'; rev 5 CHANGELOG: 'implies ~139% of injected water produced "
                "back at the reference (high for a first cycle). Open item.' TIER1 4.3: "
                "0.75/0.90 -> SOR 2.11/4.08, the second-largest one-at-a-time swing. "
                "Physics v3 (CHANGELOG rev 7): with bl_delta_factor fixed at the sourced "
                "0.5, water_cut is where the Boberg-Lantz delta uncertainty lives."
            ),
        }),
        "thickness_m": {
            "low": 8.0, "high": 20.0, "base": 12.0,
            "setter": _set_thickness_m,
            "why": (
                "reservoir.thickness_m (net pay). TIER1 4.6 / CHANGELOG rev 5 open item: "
                "Yasin et al. 2022 gives 16-25% porosity and ~50 m GROSS Jodhpur Fm "
                "thickness vs the 0.09/12 m kept; 'thickness_m is first-order ... the "
                "BGW-8 5-6x uplift is only reproduced for net pay of roughly 8-20 m.' "
                "That reproduction band is used directly as the UQ range."
            ),
        },
        "diesel_bulk_discount_frac": {
            "low": 0.0, "high": 0.30,
            "base": float(base_params["economics"].get("diesel_bulk_discount_frac", 0.15)),
            "setter": _set_diesel_bulk_discount,
            "why": (
                "economics.diesel_bulk_discount_frac. At the fixed Rajasthan retail "
                "pump price (Rs97.80/L), discount 0.30 (bulk, base case) gives Rs5,856/t "
                "steam and discount 0.0 (full retail) gives Rs8,366/t -- the exact "
                "documented Rs5,900-8,400/t band (ECON plan section 0.2), and the "
                "'[CALIBRATED, UNSOURCED]' discount CHANGELOG rev 5 flags as the single "
                "judgement call the headline margin SIGN depends on."
            ),
        },
        "oil_price_inr_per_bbl": {
            "low": base_params["economics"]["oil_price_inr_per_bbl"] * 0.85,
            "high": base_params["economics"]["oil_price_inr_per_bbl"] * 1.15,
            "base": base_params["economics"]["oil_price_inr_per_bbl"],
            "setter": _set_oil_price,
            "why": (
                "economics.oil_price_inr_per_bbl. rev 9: base case is OIL's CONFIRMED "
                "FY25 realisation (US$78.09/bbl, Annual Report 2024-25) minus a $10/bbl "
                "heavy-oil discount [ASSUMPTION] = Rs5,992/bbl; the $65 FY26 planning "
                "floor (Rs4,840/bbl) is kept as a named preset deck, run as a separate "
                "UQ pass (see `decks.fy26_floor`). +/-15% is a generic commodity-price "
                "uncertainty band around whichever deck's base is centred, not "
                "field-specific."
            ),
        },
        "mu_ref_cP": {
            "low": 8000.0, "high": 15000.0, "base": 11500.0,
            "setter": _set_mu_ref,
            "why": (
                "fluid.mu_ref_cP. params/CHANGELOG.md: 'CONFIRMED viscosity "
                "10,000-13,000 cP at 50C (OIL internal PPT), 8,000-15,000 cP at 50C "
                "(SPE-23APOG-535203); midpoint of the tighter PPT range used.' The wider "
                "published SPE range is used here as the UQ band, since it is the "
                "documented literature spread, not just the tighter internal-deck one."
            ),
        },
        "opex_inr_per_day": {
            "low": 2500.0, "high": 7500.0, "base": 5000.0,
            "setter": _set_opex_per_day,
            "why": (
                "economics.opex_inr_per_day (Economics v2, CHANGELOG rev 8): fixed "
                "well-site opex excluding power, [ASSUMPTION] -- no per-well Indian "
                "lifting-cost datum was found (OIL AR 2024-25 reports no per-bbl lifting "
                "cost). +/-50 % is the stated uncertainty. It is paid by the stimulated "
                "AND the cold well, so it cancels in the incremental margin unless the "
                "cold well becomes uneconomic (opex > ~Rs 12.5k/d); it moves only the "
                "with-opex gross figures."
            ),
        },
        "srp_geometry_scale": {
            "low": 0.90, "high": 1.10, "base": 1.0,
            "setter": lambda p, v: _set_srp_geometry_scale(p, v, base_stroke, base_plunger),
            "why": (
                "srp.stroke_m and srp.plunger_d_m scaled together +/-10% (TYPICAL pump "
                "geometry, CHANGELOG: 'not Baghewala data -- top data request'; rev 5 "
                "sized the pump to bracket the ~2.5 m3/d peak rate, so a +/-10% geometry "
                "shift is a plausible as-built tolerance, not a re-selection of pump class)."
            ),
        },
        # ---- rev 10: unsourced physics constants, now params-level -------------
        "s_cold": {
            "low": 0.0, "high": 8.0,
            "base": float(base_params.get("ipr", {}).get("s_cold", 5.0)),
            "setter": _set_s_cold,
            "why": (
                "ipr.s_cold, cold-well asphaltene/wax damage skin removed by heat [ASSUMPTION, "
                "magnitude unsourced]. External review: S = 0 gives uplift ~3.3x and a negative "
                "incremental margin; S = 8 gives ~7x. 0 (undamaged) to 8 (heavily damaged) spans "
                "the usual damaged-well range; a pre-CSS build-up test would pin it."
            ),
        },
        "k_visc": {
            "low": 5.0, "high": 15.0,
            "base": float(base_params["srp"].get("k_visc", 10.0)),
            "setter": _set_k_visc,
            "why": (
                "srp.k_visc, lumped rod-drag coefficient [ASSUMPTION, tuned in T1-E]. +/-50 %; "
                "Couette 2*pi/ln(Dt/Dr) ~ 6-7 for 2-7/8 in tubing x 7/8-1 in rods sits inside."
            ),
        },
        "pressure_boost_kPa_per_t": {
            "low": 0.5, "high": 2.0,
            "base": float(res.get("pressure_boost_kPa_per_t", 1.0)),
            "setter": _set_pressure_boost,
            "why": (
                "reservoir.pressure_boost_kPa_per_t [CALIBRATED, no mechanism]: tuned 2.0 -> 1.0 in "
                "rev 5 to land the BGW-8 uplift band; physically unsupported at the params' own P-T "
                "state (thermal.steam_state_check). Range = the rev-5 tuning history either side."
            ),
        },
        "mu_anchor_cP": {
            "low": 30.0, "high": 80.0,
            "base": float(base_params["fluid"].get("mu_anchor_cP", 50.0)),
            "setter": _set_mu_anchor,
            "why": (
                "fluid.mu_anchor_cP, Walther high-T anchor mu(150 C) [ASSUMPTION - SPEC "
                "placeholder]. 30-80 cP brackets 15-16 API heavy-oil curves at 150 C; a two-point "
                "lab measurement (100/200 C) is the top fluid data ask."
            ),
        },
        "fixed_cost_inr_per_cycle": {
            "low": 0.5 * fixed_cost, "high": 1.5 * fixed_cost, "base": fixed_cost,
            "setter": _set_fixed_cost,
            "why": (
                "economics.fixed_cost_inr_per_cycle, rig / pump pull per CSS job [ASSUMPTION]. "
                "+/-50 % (Rs 7.5-22.5 L); the review found doubling it alone costs ~Rs 900/cycle-day."
            ),
        },
        "P_current_kPa": {
            "low": 7400.0, "high": float(p_now) if p_now is not None else p_virgin,
            "base": float(p_now) if p_now is not None else p_virgin,
            "setter": _set_p_current,
            "why": (
                "reservoir.P_current_kPa [ASSUMPTION - derived from the injectivity requirement; "
                "UNKNOWN; top data ask]. rev 11: the default 9,400 kPa is the highest pressure that "
                "admits injection over the CONFIRMED 85-97 kgf/cm2 wellhead range (sandface "
                "9.45-10.79 MPa, IF97 two-phase column); 7.4 MPa is the depleted end already used by "
                "the P_res benchmark. The base is the optimistic (highest-rate) edge of the range."
            ),
        },
        "emulsion_inversion_wc": {
            "low": 0.60, "high": 0.75,
            "base": float(base_params["fluid"].get("emulsion_inversion_wc", 0.70)),
            "setter": _set_inversion_wc,
            "why": (
                "fluid.emulsion_inversion_wc [ASSUMPTION]: water cut at which the produced W/O "
                "emulsion inverts to water-continuous (heavy-oil literature 0.6-0.75). Decides "
                "whether the rods see a ~1 cP water-continuous stream or a Brinkman-thickened "
                "W/O emulsion, i.e. whether the rod-float constraint exists at all (rev 10)."
            ),
        },
        # ---- rev 11: water-cut state --------------------------------------------
        "condensate_recovery_frac": {
            "low": 0.50, "high": 0.90,
            "base": float(base_params["fluid"].get("condensate_recovery_frac", 0.70)),
            "setter": _set_condensate_recovery,
            "why": (
                "fluid.condensate_recovery_frac [ASSUMPTION, rev 11]: fraction of the injected "
                "steam mass produced back as condensate within the cycle (Prats SPE Monograph 7; "
                "Butler 1991: most injected water returns). Sets how long the stream stays "
                "water-continuous and how much hot water carries heat out."
            ),
        },
        # ---- rev 12: W/O emulsion law constant (appended: earlier draws unchanged)
        "emulsion_phi_star": {
            "low": 0.65, "high": 1.00,
            "base": float(base_params["fluid"].get("emulsion_phi_star", 0.84)),
            "setter": _set_phi_star,
            "why": (
                "fluid.emulsion_phi_star [ASSUMPTION, rev 12]: Pal & Rhodes (1989) phi* (water "
                "fraction at mu_r = 100) of the W/O branch. 0.65 -> ~9x, 1.0 -> 3.3x the oil "
                "viscosity at 45 % water, spanning the published heavy-oil 2-10x band; relative "
                "viscosity capped at fluid.emulsion_mu_r_max (10x; sampled from rev 13)."
            ),
        },
        # ---- rev 13 (wave 5): the structural / operating choices that carried the
        # rev-12 gain, appended (earlier draws unchanged) --------------------------
        "emulsion_mu_r_max": {
            "low": 5.0, "high": 20.0,
            "base": float(base_params["fluid"].get("emulsion_mu_r_max") or 10.0),
            "setter": _set_mu_r_max,
            "why": (
                "fluid.emulsion_mu_r_max [ASSUMPTION]: cap on the W/O relative viscosity. 10x = the top "
                "of the published 2-10x band at 40-50 % water; 5x (shear-thinning at rod-annulus shear "
                "rates) to 20x (~Brinkman at 69 % water) brackets it. The rev-12 gain moved "
                "Rs 3.8k -> 14.9k/d over cap 5 -> 20 (external re-score probe 3)."
            ),
        },
        "fi_alarm_days": {
            "low": 1.0, "high": 14.0,
            "base": float(base_params.get("css", {}).get("fi_alarm_days", 3.0)),
            "setter": _set_fi_alarm_days,
            "why": (
                "css.fi_alarm_days [ASSUMPTION - operating rule, no Baghewala SOP]: consecutive alarm days "
                "before the pull (rounded to whole days). 1 (pull on the first confirmed card) to 14 "
                "(two weeks to schedule a rig)."
            ),
        },
        "emulsion_inversion_band_wc": {
            "low": 0.05, "high": 0.10,
            "base": float(base_params["fluid"].get("emulsion_inversion_band_wc") or 0.075),
            "setter": _set_inversion_band,
            "why": (
                "fluid.emulsion_inversion_band_wc [ASSUMPTION, rev 13]: width of the W/O <-> O/W "
                "transition band (log-linear blend) replacing the rev-12 binary inversion; inversion "
                "of crude emulsions is hysteretic / gradual over a range of cuts."
            ),
        },
        "flowback_mobility_ratio": {
            "low": 0.0, "high": float(len(FLOWBACK_M_LEVELS)),
            "base": float(FLOWBACK_M_LEVELS.index(float(
                base_params["fluid"].get("flowback_mobility_ratio") or 1.0))) + 0.5,
            "setter": _set_flowback_M,
            "discrete_levels": list(FLOWBACK_M_LEVELS),
            "why": (
                "fluid.flowback_mobility_ratio M, DISCRETE {1, 3, 10} with equal probability "
                "[ASSUMPTION - structural]: condensate share of the mixing cell's liquid "
                "c = M W / (M W + V_p). 1 = volume-weighted (rev 11/12); 3 and 10 = hot condensate more "
                "mobile than the oil-bearing pore fluid (fractional-flow proxy). The re-score found the "
                "rev-12 rec's sign flips between M = 3 and M = 10."
            ),
        },
        "cold_counterfactual": {
            "low": 0.0, "high": float(len(COLD_CF_LEVELS)),
            "base": float(COLD_CF_LEVELS.index(str(
                base_params.get("css", {}).get("cold_counterfactual") or "policy"))) + 0.5
            if str(base_params.get("css", {}).get("cold_counterfactual") or "policy") in COLD_CF_LEVELS
            else 0.5,
            "setter": _set_cold_cf,
            "discrete_levels": list(COLD_CF_LEVELS),
            "why": (
                "css.cold_counterfactual, DISCRETE {policy, pumpable} 50/50 [structural choice, rev 13]: "
                "'policy' = the cold well obeys the same float policy at the 2-spm floor and is shut in "
                "when it cannot hold FI <= 0.6 there (the base case at 45 % formation water); "
                "'pumpable' = the field fact that the wells produced cold: slowed below the floor until "
                "FI <= 0.6, full IPR rate. Moves every absolute incremental Rs by the cold well's "
                "cash/day (~Rs 11k/d FY25); the paired set-point comparison is unaffected."
            ),
        },
    }


def _load_base_params(params_path: Path) -> dict:
    with open(params_path) as f:
        return json.load(f)


def _draw(rng: np.random.Generator, uncertain: dict[str, dict[str, Any]], n: int) -> dict[str, np.ndarray]:
    return {name: rng.uniform(spec["low"], spec["high"], n) for name, spec in uncertain.items()}


def _apply_draw(base_params: dict, uncertain: dict[str, dict[str, Any]], draws: dict[str, np.ndarray], i: int) -> dict:
    p = copy.deepcopy(base_params)
    for name, spec in uncertain.items():
        spec["setter"](p, draws[name][i])
    return p


def _run_point(p: dict, settings: dict[str, float]) -> dict[str, float]:
    st = dict(settings)
    fi_line = st.pop("fi_alarm", None)   # rev 12: per-point alarm line (conservative)
    if fi_line is not None:
        css = dict(p.get("css", {}), fi_alarm=float(fi_line))
        if css.get("vfd_hold_fi") is not None:   # rev 13: a VFD policy holds at the same line
            css["vfd_hold_fi"] = min(float(css["vfd_hold_fi"]), float(fi_line))
        p = dict(p, css=css)
    stroke_in = st.pop("stroke_in", None)
    p_wh = st.pop("p_wellhead_kgf_cm2", None)
    if stroke_in is not None:   # rev 11: the point's stroke, times the draw's geometry scale
        st["stroke_m"] = float(stroke_in) * 0.0254 * float(p["srp"].get("_uq_geometry_scale", 1.0))
    if p_wh is not None:
        st["p_wellhead_kgf_cm2"] = float(p_wh)
    df = cycle.simulate_css_cycle(params=p, **st)
    s = cycle.summary(df, p)
    # rev 12: numeric flag for what ended the cycle
    s["ended_by_float_onset"] = float(s.get("produce_end_reason") == "float_onset")
    s["injection_ok"] = float(s.get("injection_ok") is not False)                  # rev 13
    s["cold_shut_in"] = float(str(s.get("cold_status") or "").startswith("shut_in"))
    # rev 13: against THIS draw's css.fi_alarm_days (now sampled), not the base value
    s["alarm_days_exceed_rule"] = float(s["failures_expected"] > cycle.fi_alarm_days(p) + 1e-9)
    for k in ("produce_days", "produce_end_days_after_peak"):
        if s.get(k) is None:
            s[k] = float("nan")
    return {m: s[m] for m in METRICS}


def monte_carlo(
    base_params: dict,
    n_draws: int = N_DRAWS,
    seed: int = SEED,
) -> tuple[dict[str, dict[str, list[float]]], dict[str, np.ndarray], dict[str, dict[str, Any]]]:
    """Returns (results, draws, uncertain_spec).

    results[point_name][metric] is a length-n_draws list, paired across
    points (same draw index -> same underlying uncertain-input realisation).
    """
    uncertain = build_uncertain_inputs(base_params)
    rng = np.random.default_rng(seed)
    draws = _draw(rng, uncertain, n_draws)

    results: dict[str, dict[str, list[float]]] = {
        pt: {m: [] for m in METRICS} for pt in POINTS
    }
    for i in range(n_draws):
        p_i = _apply_draw(base_params, uncertain, draws, i)
        for pt_name, settings in POINTS.items():
            out = _run_point(p_i, settings)
            for m in METRICS:
                results[pt_name][m].append(out[m])

    return results, draws, uncertain


def oat_tornado(
    base_params: dict,
    uncertain: dict[str, dict[str, Any]],
    point_settings: dict[str, float],
    metric: str = MONEY_METRIC,
) -> list[dict[str, Any]]:
    """Classic one-at-a-time tornado: hold every uncertain input at its base
    value except one, swing that one from low to high, record the resulting
    change in `metric` at `point_settings` (the recommendation, by default).
    Ranked by |high - low|, descending -- the standard tornado-chart ordering.
    """
    rows = []
    for name, spec in uncertain.items():
        p_lo = copy.deepcopy(base_params)
        p_hi = copy.deepcopy(base_params)
        # Hold every OTHER uncertain input at its base (point-estimate) value.
        for other_name, other_spec in uncertain.items():
            other_spec["setter"](p_lo, other_spec["base"])
            other_spec["setter"](p_hi, other_spec["base"])
        # Then sweep just this one input from low to high.
        spec["setter"](p_lo, spec["low"])
        spec["setter"](p_hi, spec["high"])

        out_lo = _run_point(p_lo, point_settings)[metric]
        out_hi = _run_point(p_hi, point_settings)[metric]
        rows.append({
            "input": name,
            "low_input": spec["low"], "high_input": spec["high"],
            "metric_at_low": out_lo, "metric_at_high": out_hi,
            "swing": out_hi - out_lo, "abs_swing": abs(out_hi - out_lo),
        })
    rows.sort(key=lambda r: r["abs_swing"], reverse=True)
    return rows


def mc_correlation_ranking(
    draws: dict[str, np.ndarray],
    results: dict[str, dict[str, list[float]]],
    point: str = "recommended",
    metric: str = MONEY_METRIC,
) -> list[dict[str, Any]]:
    """Secondary cross-check: Pearson correlation of each MC input draw
    against the same draw's `metric` at `point`, ranked by |r| descending."""
    y = np.asarray(results[point][metric], dtype=float)
    rows = []
    for name, x in draws.items():
        r = float(np.corrcoef(x, y)[0, 1])
        rows.append({"input": name, "pearson_r": r, "abs_r": abs(r)})
    rows.sort(key=lambda r: r["abs_r"], reverse=True)
    return rows


def _percentiles(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"p10": float("nan"), "p50": float("nan"), "p90": float("nan")}
    p10, p50, p90 = np.percentile(arr, [10, 50, 90])
    return {"p10": float(p10), "p50": float(p50), "p90": float(p90)}


def summarize(
    results: dict[str, dict[str, list[float]]],
    draws: dict[str, np.ndarray],
    uncertain: dict[str, dict[str, Any]],
    base_params: dict,
) -> dict[str, Any]:
    bands = {
        pt: {m: _percentiles(results[pt][m]) for m in METRICS}
        for pt in POINTS
    }

    rec_margin = np.asarray(results["recommended"][GAIN_METRIC])      # rev 13: counterfactual-free
    base_margin = np.asarray(results["baseline_b"][GAIN_METRIC])
    rec_sor = np.asarray(results["recommended"]["SOR_t_per_m3"])
    base_sor = np.asarray(results["baseline_b"]["SOR_t_per_m3"])

    probabilities = {
        "P_recommended_margin_gt_baseline": float(np.mean(rec_margin > base_margin)),
        "P_recommended_rev12_margin_gt_baseline": (
            float(np.mean(np.asarray(results["recommended_rev12"][GAIN_METRIC]) > base_margin))
            if "recommended_rev12" in results else None),
        # rev 13: P(the VFD-hold recommendation beats baseline (b) IF the
        # baseline instead pulls on the alarm, rev-12 operation) -- the
        # "mixed" comparison TIER1 section 12.6 calls the rev-12 structure
        # again (most of it is the policy lever, not the set-point).
        "P_recommended_gt_baseline_if_baseline_pulls": (
            float(np.mean(rec_margin > np.asarray(results["baseline_b__pull"][GAIN_METRIC])))
            if "baseline_b__pull" in results else None
        ),
        # rev 11: the float constraint is part of the recommendation, so report how
        # often each point keeps FI <= 0.6 under the drawn physics
        "P_float_ok": {
            pt: float(np.mean(np.asarray(results[pt]["max_floating_index"]) <= 0.6))
            for pt in POINTS
        },
        "P_recommended_SOR_lt_baseline": float(np.mean(rec_sor < base_sor)),
        # rev 12: robustness of each point under the produce-end rule
        "P_gt_baseline": {
            pt: float(np.mean(np.asarray(results[pt][GAIN_METRIC]) > base_margin))
            for pt in POINTS if pt != "baseline_b"
        },
        # rev 13: the SAME-POLICY comparison -- the recommendation's settings vs baseline
        # (b) when both are operated under the same float policy (points
        # "<name>__<policy>"), and the gain distribution (net cash / cycle-day)
        "P_gt_baseline_same_policy": {
            pol: float(np.mean(np.asarray(results[r][GAIN_METRIC]) > np.asarray(results[b][GAIN_METRIC])))
            for pol, (r, b) in SAME_POLICY_POINTS.items() if r in results and b in results
        },
        "gain_vs_baseline_bands": {
            **{f"same_policy__{pol}": _percentiles(list(
                np.asarray(results[r][GAIN_METRIC]) - np.asarray(results[b][GAIN_METRIC])))
               for pol, (r, b) in SAME_POLICY_POINTS.items() if r in results and b in results},
            **{f"recommended_vs_{b}": _percentiles(list(
                np.asarray(results["recommended"][GAIN_METRIC]) - np.asarray(results[b][GAIN_METRIC])))
               for _, b in SAME_POLICY_POINTS.values() if b in results},
            "metric": GAIN_METRIC,
        },
        "P_injection_ok": {pt: float(np.mean(np.asarray(results[pt]["injection_ok"]) > 0.5)) for pt in POINTS},
        "P_cold_shut_in": {pt: float(np.mean(np.asarray(results[pt]["cold_shut_in"]) > 0.5)) for pt in POINTS},
        "P_ended_by_float_onset": {
            pt: float(np.mean(np.asarray(results[pt]["ended_by_float_onset"]) > 0.5)) for pt in POINTS
        },
        "P_any_float_alarm_day": {
            pt: float(np.mean(np.asarray(results[pt]["failures_expected"]) > 0)) for pt in POINTS
        },
        "P_alarm_days_exceed_rule": {
            pt: float(np.mean(np.asarray(results[pt]["alarm_days_exceed_rule"]) > 0.5))
            for pt in POINTS
        },
        "P_fragile_end_within_5d_of_peak": {
            pt: float(np.mean(np.asarray(results[pt]["produce_end_days_after_peak"], dtype=float)
                              <= FRAGILE_DAYS_AFTER_PEAK)) for pt in POINTS
        },
        "P_margin_positive": {
            pt: float(np.mean(np.asarray(results[pt][MONEY_METRIC]) > 0))
            for pt in POINTS
        },
        "P_gross_margin_positive": {
            pt: float(np.mean(np.asarray(results[pt]["margin_inr_per_cycle_day"]) > 0))
            for pt in POINTS
        },
        "money_metric": MONEY_METRIC,
    }

    # rev 13 (wave 5 bake): P(incremental margin/cycle-day > 0) broken down by
    # the cold counterfactual level -- "policy" (shut in under every float
    # policy at base) and "pumpable" (the field fact, 0.53 spm at base) are
    # read directly off the main paired draws (cold_counterfactual is itself
    # one of the 50/50-sampled uncertain inputs); "shut_in" (forced on every
    # draw, always cash 0) needs the dedicated paired pass below, since the
    # sampled discrete set never includes it (TIER1 section 12.4/12.13: shut_in
    # IS the "policy" level at the model's own base water cut, but the levels
    # can diverge elsewhere in the UQ box).
    _cf_masks = {lvl: _cold_cf_level_mask(draws, lvl) for lvl in COLD_CF_LEVELS}
    _shut_in = _shut_in_incremental_positive(base_params, uncertain, draws, FOCUS_POINTS_CF)
    p_incremental_positive_by_cf: dict[str, dict[str, float]] = {}
    for pt in FOCUS_POINTS_CF:
        if pt not in results:
            continue
        incr = np.asarray(results[pt][MONEY_METRIC])
        row = {
            lvl: (float(np.mean(incr[mask] > 0)) if mask.any() else float("nan"))
            for lvl, mask in _cf_masks.items()
        }
        row["shut_in"] = _shut_in.get(pt, float("nan"))
        p_incremental_positive_by_cf[pt] = row
    probabilities["P_incremental_positive_by_counterfactual"] = p_incremental_positive_by_cf
    probabilities["P_incremental_positive_by_counterfactual_note"] = (
        "P(margin_incremental_inr_per_cycle_day > 0) at each of "
        + ", ".join(FOCUS_POINTS_CF)
        + ", split by the cold-well counterfactual: 'policy' / 'pumpable' are "
        "the draws where css.cold_counterfactual sampled that level (paired, "
        "off the main MC); 'shut_in' forces it on EVERY draw (a separate "
        "paired pass, same other-input draws). 'policy' coincides with "
        "'shut_in' whenever the model's own base formation water cut (45%) "
        "shuts the cold well in under the draw's float policy, which is most "
        "of the box (TIER1_PROGRESS_LOG.md section 12.4)."
    )

    oat = oat_tornado(base_params, uncertain, POINTS["recommended"])
    corr = mc_correlation_ranking(draws, results, point="recommended")

    return {
        "meta": {
            "n_draws": len(next(iter(draws.values()))),
            "seed": SEED,
            "points": POINTS,
            "point_labels": POINT_LABELS,
            "method": (
                "Paired Monte Carlo: one joint draw of the uncertain inputs below is "
                "run through all three set-point combinations (same physics/economics "
                "realisation, different steam_t/soak_days/cutoff_m3d/spm), via the true "
                "twin.cycle.simulate_css_cycle + summary (not the ML surrogate)."
            ),
            "money_metric": MONEY_METRIC,
            "economics_basis": (
                "Economics v2: incremental oil over the cold (unstimulated) well for "
                "the same calendar window, inject+soak days included; daily opex = "
                "fixed well-site opex + pumping-unit electricity (corrected "
                "polished-rod energy / surface efficiency x tariff). Gross SOR "
                "(steam/all oil) is still the headline SOR; SOR_incremental is the "
                "economic one."
            ),
            "fixed_inputs": {
                "bl_delta_factor": (
                    "0.5, sourced (Boberg & Lantz delta = (1/2Q) integral Qp dt, "
                    "PEH Eqs. 15.70/15.73; energy conservation). Not varied."
                ),
            },
        },
        "uncertain_inputs": {
            name: {"low": spec["low"], "high": spec["high"], "base": spec["base"], "why": spec["why"]}
            for name, spec in uncertain.items()
        },
        "bands": bands,
        "probabilities": probabilities,
        "tornado_oat_swing_on_recommendation_margin": oat,
        "tornado_mc_correlation_with_recommendation_margin": corr,
    }


def _print_table(summary: dict[str, Any]) -> None:
    print("\n=== UQ bands (p10 / p50 / p90) ===")
    for pt in POINTS:
        print(f"\n-- {POINT_LABELS[pt]} --")
        for m in METRICS:
            b = summary["bands"][pt][m]
            print(f"  {m:28s} p10={b['p10']:>12,.3f}  p50={b['p50']:>12,.3f}  p90={b['p90']:>12,.3f}")

    print("\n=== Paired probabilities ===")
    p = summary["probabilities"]
    print(f"  money metric: {p['money_metric']}")
    print(f"  P(recommended margin/day > baseline margin/day) = {p['P_recommended_margin_gt_baseline']:.3f}")
    if p.get("P_recommended_rev12_margin_gt_baseline") is not None:
        print(f"  P(rev-12 rec net cash/day > baseline net cash/day) = "
              f"{p['P_recommended_rev12_margin_gt_baseline']:.3f}")
    for pol, v in p.get("P_gt_baseline_same_policy", {}).items():
        g = p["gain_vs_baseline_bands"].get(f"same_policy__{pol}", {})
        print(f"  SAME POLICY {pol:<9s}: P(rec > base) = {v:.3f}   gain p10/p50/p90 = "
              f"{g.get('p10', float('nan')):,.0f} / {g.get('p50', float('nan')):,.0f} / {g.get('p90', float('nan')):,.0f}")
    print(f"  P(recommended SOR < baseline SOR)                = {p['P_recommended_SOR_lt_baseline']:.3f}")
    if p.get("P_recommended_gt_baseline_if_baseline_pulls") is not None:
        print(f"  P(rec net cash/day > base net cash/day, IF base pulls) = "
              f"{p['P_recommended_gt_baseline_if_baseline_pulls']:.3f}")
    print("\n=== P(incremental margin/day > 0) by cold counterfactual ===")
    for pt, row in p.get("P_incremental_positive_by_counterfactual", {}).items():
        print(f"  {pt:<18s} policy={row.get('policy', float('nan')):.3f}"
              f"  pumpable={row.get('pumpable', float('nan')):.3f}"
              f"  shut_in={row.get('shut_in', float('nan')):.3f}")
    for pt in POINTS:
        print(f"  P(incr. margin/day > 0) at {pt:<18s}  = {p['P_margin_positive'][pt]:.3f}"
              f"   (gross: {p['P_gross_margin_positive'][pt]:.3f})"
              f"   P(FI <= 0.6): {p['P_float_ok'][pt]:.3f}")
    print("\n=== rev 12 robustness (per point) ===")
    for pt in POINTS:
        print(f"  {pt:<18s} P(>base) {p['P_gt_baseline'].get(pt, float('nan')):.3f}"
              f"  P(float-onset end) {p['P_ended_by_float_onset'][pt]:.3f}"
              f"  P(any alarm) {p['P_any_float_alarm_day'][pt]:.3f}"
              f"  P(alarm > rule) {p['P_alarm_days_exceed_rule'][pt]:.3f}"
              f"  P(end <= 5 d after peak) {p['P_fragile_end_within_5d_of_peak'][pt]:.3f}")

    print("\n=== Tornado -- OAT swing on recommendation incremental margin/cycle-day (top 3) ===")
    for row in summary["tornado_oat_swing_on_recommendation_margin"][:3]:
        print(f"  {row['input']:28s} swing = Rs{row['swing']:>10,.0f}/cycle-day  "
              f"(low={row['metric_at_low']:>10,.0f}  high={row['metric_at_high']:>10,.0f})")

    print("\n=== Tornado -- MC correlation with recommendation incremental margin/cycle-day (top 3) ===")
    for row in summary["tornado_mc_correlation_with_recommendation_margin"][:3]:
        print(f"  {row['input']:28s} r = {row['pearson_r']:+.3f}")
    print()


# rev 12 (cascade, honesty): the CSV is the 4 points the coordinator asked
# UQ to bake -- reference / baseline (b) / recommended / conservative -- not
# every legacy point POINTS carries (rev-9/10/11 comparisons, kept for the
# JSON summary's history). Writing all 7 points' full draw-by-draw metrics
# pushed the CSV past the 2 MB budget at 1,500 draws; trimming to the 4
# requested points keeps it well under budget without losing anything asked
# for (the legacy points' bands/probabilities are still in uq_summary.json).
CSV_POINTS = ["reference", "baseline_b", "recommended", "conservative"]


def _write_samples_csv(
    results: dict[str, dict[str, list[float]]],
    draws: dict[str, np.ndarray],
    out_path: Path,
    points: list[str] | None = None,
) -> None:
    n = len(next(iter(draws.values())))
    data: dict[str, Any] = {"draw": np.arange(n)}
    for name, arr in draws.items():
        data[f"input__{name}"] = arr
    for pt in (points if points is not None else POINTS):
        if pt not in results:
            continue
        for m in METRICS:
            data[f"{pt}__{m}"] = results[pt][m]
    pd.DataFrame(data).to_csv(out_path, index=False, float_format="%.6g")


DECKS = ["fy25_realisation", "fy26_floor", "fy25_net_of_levies"]
DECK_LABELS = {
    "fy25_realisation": "OIL FY25 realisation ($78.09/bbl - $10 discount = Rs5,992/bbl)",
    "fy26_floor": "OIL FY26 planning floor ($65/bbl - $10 discount = Rs4,840/bbl)",
    # rev 13 (wave 5): third deck -- FY25 realisation net of royalty + OID cess
    # (params/CHANGELOG.md rev 13; TIER1_PROGRESS_LOG.md section 12.10).
    "fy25_net_of_levies": "OIL FY25 realisation net of royalty + OID cess (~Rs3,600/bbl)",
}
_DECK_FALLBACK_INR_PER_BBL = {"fy26_floor": 4840.0, "fy25_net_of_levies": 3600.0}


def _deck_params(base_params: dict, deck: str) -> dict:
    """Return a deep copy of base_params with economics.oil_price_inr_per_bbl
    set to the named preset deck (rev 9: params["economics"]["oil_price_presets"];
    rev 13: DECKS also has "fy25_net_of_levies"). `deck="fy25_realisation"` is
    a no-op (it is field_params.json's shipped base case); the other deck
    names override to their preset price (or the fallback constant if the
    preset key is absent from an older params.json)."""
    p = copy.deepcopy(base_params)
    presets = p.get("economics", {}).get("oil_price_presets")
    if presets and deck in presets:
        p["economics"]["oil_price_inr_per_bbl"] = float(presets[deck]["inr_per_bbl"])
    elif deck in _DECK_FALLBACK_INR_PER_BBL:
        p["economics"]["oil_price_inr_per_bbl"] = _DECK_FALLBACK_INR_PER_BBL[deck]
    return p


def run_deck(deck: str, base_params: dict, n_draws: int, seed: int) -> dict:
    p = _deck_params(base_params, deck)
    results, draws, uncertain = monte_carlo(p, n_draws=n_draws, seed=seed)
    summary = summarize(results, draws, uncertain, p)
    summary["meta"]["n_draws"] = n_draws
    summary["meta"]["seed"] = seed
    summary["meta"]["deck"] = deck
    summary["meta"]["deck_label"] = DECK_LABELS.get(deck, deck)
    summary["meta"]["oil_price_inr_per_bbl_base"] = p["economics"]["oil_price_inr_per_bbl"]
    return summary, results, draws


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--params", type=Path, default=PARAMS_PATH)
    ap.add_argument("--out-json", type=Path, default=OUT_JSON)
    ap.add_argument("--out-csv", type=Path, default=OUT_CSV)
    ap.add_argument(
        "--deck", choices=DECKS, default=None,
        help="Run and print only this deck standalone (no combined write). "
             f"Default: run all of {DECKS} and write the combined ml/models/uq_summary.json.",
    )
    args = ap.parse_args()

    base_params = _load_base_params(args.params)

    if args.deck is not None:
        summary, results, draws = run_deck(args.deck, base_params, args.draws, args.seed)
        _print_table(summary)
        return

    # --- Default: every deck in DECKS, combined output ----------------------
    summaries: dict[str, dict] = {}
    primary_results = primary_draws = None
    for deck in DECKS:
        summary, results, draws = run_deck(deck, base_params, args.draws, args.seed)
        summaries[deck] = summary
        if deck == "fy25_realisation":
            primary_results, primary_draws = results, draws

    combined = dict(summaries["fy25_realisation"])  # primary (top-level) = FY25 realisation deck
    combined["decks"] = summaries

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(combined, f, indent=2)
    _write_samples_csv(primary_results, primary_draws, args.out_csv, points=CSV_POINTS)

    for deck in DECKS:
        print("=" * 30, DECK_LABELS.get(deck, deck), "=" * 30)
        _print_table(summaries[deck])
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_csv} (FY25 deck draws only)")


if __name__ == "__main__":
    main()
