"""ml/recommend_physics.py -- re-recommend directly against the TRUE physics.

`ml/optimize.py::best_settings()` searches through the trained XGBoost
surrogates (`ml/models/*.joblib`), which were trained on data generated from
the DEFAULT physics params (`params/field_params.json`). Once
`twin/calibrate.py` has recalibrated a params tree from observed field
cycles, the surrogates are stale for that params tree -- they would score
candidate set-points using a margin/oil model fit to the OLD physics, silently
mismatched to the NEW (calibrated) one.

This module sidesteps the surrogate entirely and re-recommends by grid-search
directly on `twin.cycle.simulate_css_cycle` + `summary` -- the same "true
physics" verification `ml/optimize.py` already uses to check its own
surrogate optimum, just used as the objective instead of only a check. A
15 (steam) x 15 (cutoff) x 7 (spm) grid is ~1,575 evaluations at roughly
1-20 ms each (`docs/model-improvement/TIER1_PROGRESS_LOG.md` section 5.1: ~8
ms/cycle averaged over the full design space) -- comfortably a few-to-fifteen
second operation, no surrogate needed.

`soak_days` is held FIXED (not gridded), matching
`docs/model-improvement/TIER1_PROGRESS_LOG.md` section 5b: the twin's soak
sensitivity is small and monotone (no interior optimum), so treating it as a
free search variable just lands on a search-box edge with no physical
meaning. Pass `fixed={"soak_days": <field practice value>}`; if omitted it
defaults to 10.0 (the same published-practice value `ml/optimize.py`'s own
baseline (b) uses).

Feasibility (a physics-native analog of `ml/optimize.py`'s "P(float) < 0.3"
ML-classifier constraint, which has no meaning without a trained classifier
that matches the running params tree): a grid point is feasible if
`summary()["max_floating_index"] <= twin.cycle.FLOATING_RISK_THRESHOLD`
(0.6) -- the SAME raw-physics threshold the classifier's own training label
uses (`ml/train.py`: `(max_floating_index > 0.6) OR (alarm_days > 0)`), so
this constraint is not looser than the one the surrogate path enforces just
because there is no probability to threshold. If no grid point is feasible,
the unconstrained margin-maximiser is returned with a `warning`.

rev 10 (hardening after external review, 27 Sep 2026): TWO feasibility
levels are reported side by side on the SAME grid --
  * `aggressive`   : max_floating_index <= 0.6 (AGGRESSIVE_FI_MAX; the SPEC
                     alarm line, = the rev-9 behaviour and the top-level keys),
  * `conservative` : max_floating_index <= 0.5 (CONSERVATIVE_FI_MAX),
each with its settings, physics-verified metrics and, for the conservative
one, the objective given up versus the aggressive one. With the rev-10
produced-stream (emulsion) drag viscosity the float index is ~0 at the shipped
85 % water cut, so the two usually coincide; they separate when the stream is
oil-continuous (water cut below `fluid.emulsion_inversion_wc`) or with
`fluid.tubing_viscosity_model = "oil"`. `grid_values` lets a caller pass
explicit grid arrays (e.g. the TIER1 section 8.6 grid used by ml/decompose.py).

rev 11 (27 Sep 2026, physics wave 3): `best_settings_physics_5d` searches the
five levers the twin now has -- steam, injection (wellhead) pressure, cutoff,
stroke length (API sizes) and SPM -- under FI <= 0.6 / 0.5 and the unit's
peak-PRL rating, on both price decks, and returns the minimax-regret point
plus `controls_coverage` (which of the problem statement's controls are
optimised, fixed or represented by another lever: the VFD is the SPM
schedule). `best_settings_physics` (3-D) is kept for the /calibrate API; it
runs at the params' pressure and stroke and also reports `controls_coverage`.

rev 12 (27 Sep 2026, physics wave 4): the twin's produce phase now ends on an
OPERATING RULE (`css.produce_end_rule`, default "either": rate cutoff OR the
float alarm FI > 0.6 persisting `css.fi_alarm_days` = 3 consecutive days, after
which the operator pulls / re-steams -- twin/cycle.py). Both optimisers run the
params' default rule. Feasibility (`_level_feasible`): the aggressive level
(FI line 0.6 = the rule's own alarm line) allows FI above 0.6 ONLY on the alarm
days the rule needs to trigger -- alarm_days <= fi_alarm_days, an additional
check that catches non-consecutive alarm days the rule would not see; the
conservative level (0.5) is the SAME rule run with its alarm line at 0.5 (the
operator pulls once FI > 0.5 persists; own grid / own simulations, params copy
with css.fi_alarm = 0.5) and the same alarm-days test. The "never alarm, end
on a fixed cutoff" reading of conservative is the fragile rule this wave
removed (TIER1 section 11.8). With the rate-cutoff-only rule (rev <= 11
params) both levels reduce to the old max-FI tests.

rev 13 (27 Sep 2026, physics wave 5): the operator's response to rod float is
a control (`css.float_policy`: pull / vfd_hold / vfd_then_pull / none,
twin/cycle.py) and `best_settings_physics_5d(..., policies=...)` searches it as
a sixth, categorical dimension; baseline (b) is evaluated under every policy and
the SAME-POLICY gain (the best point within policy P minus baseline (b) under P,
as net cash per cycle-day -- the cold counterfactual cancels) is reported. Every
level also requires injectivity: P_sandface - P_current >=
`steam.min_injection_margin_kPa` (400 kPa [ASSUMPTION]); 85 kgf/cm2 (53 kPa at
P_current 9.4 MPa) no longer qualifies. `price_decks` adds the FY25
net-of-royalty-and-cess deck (reported; the minimax stays over FY25 + $65).

Returns the same result SHAPE as `ml.optimize.best_settings()`'s output where
it makes sense to share it (physics_verified_optimum, baseline comparisons,
pinned_variables, search_ranges), so a caller (the `/calibrate` API) can
treat both the same way; fields specific to the ML surrogate path (predicted_*,
surrogate_vs_physics_gap) are absent, and `method`/`grid_shape` are added
instead.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ROOT_FOR_IMPORT))

from ml import optimize as ml_optimize  # noqa: E402  (see sys.path shim above)
from twin import cycle  # noqa: E402
from twin import srp as srp_mod  # noqa: E402

DEFAULT_PARAMS_PATH = ml_optimize.DEFAULT_PARAMS_PATH
DEFAULT_SOAK_DAYS = 10.0
DEFAULT_GRID = {"steam_t": 15, "cutoff_m3d": 15, "spm": 7}
# Economics v2 (27 Sep 2026): the objective is the INCREMENTAL margin per
# cycle-day (oil over the cold well for the same window; daily opex incl.
# power) -- docs/model-improvement/TIER1_PROGRESS_LOG.md section 8. On a
# per-cycle-day objective the constant cold baseline cannot move the argmax
# (it is a per-day offset), only the SIGN, which is the point: a negative
# optimum means stimulating does not beat producing the well cold.
DEFAULT_OBJECTIVE = "margin_incremental_inr_per_cycle_day"
FREE_FEATURES = ["steam_t", "cutoff_m3d", "spm"]
# rev 10: two float-risk feasibility levels (see module docstring).
AGGRESSIVE_FI_MAX = cycle.FLOATING_RISK_THRESHOLD   # 0.6, SPEC alarm line
CONSERVATIVE_FI_MAX = 0.5                            # [ASSUMPTION] extra margin


def _uses_float_rule(params: dict) -> bool:
    """True when the cycle can end on the float alarm: the produce-end rule
    includes float onset AND the float policy is not "none" (rev 13)."""
    return (cycle.produce_end_rule_of(params) in ("float_onset", "either")
            and cycle.float_policy_of(params) != "none")


def _with_policy(params: dict, policy: str | None) -> dict:
    """Shallow copy of params with css.float_policy set (rev 13)."""
    if policy is None:
        return params
    return dict(params, css=dict(params.get("css", {}), float_policy=str(policy)))


def _level_params(params: dict, fi_max: float) -> dict:
    """The params a feasibility level runs (rev 12/13): a level whose FI limit is
    below the float rule's alarm line is the SAME policy operated at that line
    -- the operator pulls once FI > fi_max persists, and a VFD policy holds FI
    at min(hold target, fi_max)."""
    if _uses_float_rule(params) and fi_max < cycle.fi_alarm(params) - 1e-12:
        css = dict(params["css"], fi_alarm=float(fi_max))
        css["vfd_hold_fi"] = min(cycle.vfd_hold_fi(params), float(fi_max))
        return dict(params, css=css)
    return params


def _injection_ok(margin_kPa, params: dict):
    """rev 13 injectivity gate: sandface - P_current >= steam.min_injection_margin_kPa
    (scalar or array; a None margin -- legacy_T steam state -- passes)."""
    if margin_kPa is None:
        return True
    return np.asarray(margin_kPa, dtype=float) >= cycle.min_injection_margin_kPa(params) - 1e-9


def _level_feasible(max_fi, alarm_days, fi_max: float, params: dict):
    """rev 12 float feasibility of a level (works on scalars or numpy arrays).

    If the params' produce-end rule includes the float-onset rule and the
    level's FI limit is at or above the rule's alarm line (the aggressive
    0.6), FI may exceed the line only on the alarm days that trigger the pull:
    alarm_days <= css.fi_alarm_days. Otherwise (conservative 0.5, or the
    rev <= 11 rate-cutoff rule): max FI <= fi_max on every produce day."""
    if _uses_float_rule(params) and fi_max >= cycle.fi_alarm(params) - 1e-12:
        return alarm_days <= cycle.fi_alarm_days(params) + 1e-9
    return max_fi <= fi_max + 1e-12


def _verify(settings: dict, params: dict) -> dict:
    """ml.optimize._physics_verify plus the rev-12 float/produce-end keys
    (one simulation; ml/optimize.py is out of this module's edit scope)."""
    df = cycle.simulate_css_cycle(settings["steam_t"], settings["soak_days"], settings["cutoff_m3d"],
                                  settings["spm"], params)
    s = cycle.summary(df, params=params)
    keys = ("SOR_t_per_m3", "oil_total_m3", "days_total", "margin_inr", "margin_inr_per_cycle_day",
            "SOR_incremental", "oil_incremental_m3", "margin_with_opex_inr_per_cycle_day",
            "margin_incremental_inr", "margin_incremental_inr_per_cycle_day", "max_floating_index",
            "steam_cost_inr", "co2_t", "failures_expected", "produce_end_reason",
            "float_policy", "cold_status", "injection_margin_kPa", "injection_ok")
    out = {k: s.get(k) for k in keys}
    out["alarm_days"] = s["days_rods_in_compression"]
    out["float_alarm_days"] = s["failures_expected"]
    return out


def best_settings_physics(
    params: dict,
    fixed: dict[str, float] | None = None,
    grid: dict[str, int] | None = None,
    objective: str = DEFAULT_OBJECTIVE,
    grid_values: dict[str, Any] | None = None,
    fi_levels: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Grid-search steam_t/cutoff_m3d/spm directly against the true physics.

    Args:
        params: the (possibly calibrated) field_params.json tree.
        fixed: values to hold constant. `soak_days` is always held fixed (it
            is never gridded); defaults to `DEFAULT_SOAK_DAYS` if not given.
            Any other key is ignored (only steam_t/cutoff_m3d/spm are
            searched).
        grid: optional {"steam_t": n, "cutoff_m3d": n, "spm": n} point counts,
            default 15/15/7 (~1,575 evaluations).
        objective: key of ml.optimize._physics_verify's output to maximise;
            default `margin_incremental_inr_per_cycle_day` (Economics v2).
            Pass "margin_inr_per_cycle_day" for the rev-5 gross objective.
        grid_values: optional explicit arrays {"steam_t": [...], "cutoff_m3d":
            [...], "spm": [...]} overriding the linspace grid (rev 10).
        fi_levels: optional {"aggressive": 0.6, "conservative": 0.5} override.

    Returns:
        dict -- see module docstring.
    """
    fixed = dict(fixed) if fixed else {}
    soak_days = float(fixed.get("soak_days", DEFAULT_SOAK_DAYS))
    grid = {**DEFAULT_GRID, **(grid or {})}

    ranges = ml_optimize._ranges_from_params(params)
    steam_grid = np.linspace(*ranges["steam_t"], grid["steam_t"])
    cutoff_grid = np.linspace(*ranges["cutoff_m3d"], grid["cutoff_m3d"])
    spm_grid = np.linspace(*ranges["spm"], grid["spm"])
    if grid_values:
        steam_grid = np.asarray(grid_values.get("steam_t", steam_grid), dtype=float)
        cutoff_grid = np.asarray(grid_values.get("cutoff_m3d", cutoff_grid), dtype=float)
        spm_grid = np.asarray(grid_values.get("spm", spm_grid), dtype=float)
        grid = {"steam_t": len(steam_grid), "cutoff_m3d": len(cutoff_grid), "spm": len(spm_grid)}
    levels = {"aggressive": AGGRESSIVE_FI_MAX, "conservative": CONSERVATIVE_FI_MAX,
              **(fi_levels or {})}

    best_unconstrained: tuple[float, dict, dict] | None = None
    best_feasible: tuple[float, dict, dict] | None = None
    best_level: dict[str, tuple[float, dict, dict] | None] = {k: None for k in levels}

    # rev 12: as in the 5-D search, a level whose FI limit is below the float
    # rule's alarm line runs the same rule with that line (css.fi_alarm).
    level_params = {name: _level_params(params, fi_max) for name, fi_max in levels.items()}
    for name, q in level_params.items():
        if q is params:
            continue
        for steam_t in steam_grid:
            for cutoff_m3d in cutoff_grid:
                for spm in spm_grid:
                    settings = {"steam_t": float(steam_t), "soak_days": soak_days,
                                "cutoff_m3d": float(cutoff_m3d), "spm": float(spm)}
                    phys = _verify(settings, q)
                    if _level_feasible(phys["max_floating_index"], phys["float_alarm_days"],
                                       levels[name], q) and phys["injection_ok"] is not False:
                        cur = best_level[name]
                        if cur is None or phys[objective] > cur[0]:
                            best_level[name] = (phys[objective], settings, phys)

    for steam_t in steam_grid:
        for cutoff_m3d in cutoff_grid:
            for spm in spm_grid:
                settings = {
                    "steam_t": float(steam_t), "soak_days": soak_days,
                    "cutoff_m3d": float(cutoff_m3d), "spm": float(spm),
                }
                phys = _verify(settings, params)
                margin = phys[objective]
                if best_unconstrained is None or margin > best_unconstrained[0]:
                    best_unconstrained = (margin, settings, phys)
                inj = phys["injection_ok"] is not False     # rev 13 injectivity gate
                if inj and _level_feasible(phys["max_floating_index"], phys["float_alarm_days"],
                                           cycle.FLOATING_RISK_THRESHOLD, params):
                    if best_feasible is None or margin > best_feasible[0]:
                        best_feasible = (margin, settings, phys)
                for name, fi_max in levels.items():
                    if level_params[name] is not params:
                        continue
                    if inj and _level_feasible(phys["max_floating_index"], phys["float_alarm_days"],
                                               fi_max, params):
                        cur = best_level[name]
                        if cur is None or margin > cur[0]:
                            best_level[name] = (margin, settings, phys)

    warning = None
    if best_feasible is not None:
        _, best_x, physics_optimum = best_feasible
    else:
        _, best_x, physics_optimum = best_unconstrained
        warning = (
            "No grid point had zero rod-float alarm days at this params tree; "
            "returning the unconstrained margin-maximiser instead. Treat the "
            "floating-risk numbers below as informational, not enforced."
        )

    free_ranges = {f: ranges[f] for f in FREE_FEATURES}
    pinned = ml_optimize._pinned_variables(
        {f: best_x[f] for f in FREE_FEATURES}, free_ranges
    )

    # --- baseline (a): param-midpoint of the free ranges, soak as fixed ------
    baseline_a_settings = {
        f: (ranges[f][0] + ranges[f][1]) / 2.0 for f in FREE_FEATURES
    }
    baseline_a_settings["soak_days"] = soak_days
    physics_baseline_a = _verify(baseline_a_settings, params)

    # --- baseline (b): published-practice (BGW-8), independent of `fixed` ----
    baseline_b_settings = dict(ml_optimize.PUBLISHED_PRACTICE_BASELINE)
    baseline_b_settings["cutoff_m3d"] = (ranges["cutoff_m3d"][0] + ranges["cutoff_m3d"][1]) / 2.0
    physics_baseline_b = _verify(baseline_b_settings, params)

    def _vs_baseline(physics_baseline: dict) -> dict:
        return {
            "SOR_pct_change": ml_optimize._pct_change(
                physics_baseline["SOR_t_per_m3"], physics_optimum["SOR_t_per_m3"]
            ),
            "margin_inr_per_cycle_day_pct_change": ml_optimize._pct_change(
                physics_baseline["margin_inr_per_cycle_day"],
                physics_optimum["margin_inr_per_cycle_day"],
            ),
            "margin_incremental_inr_per_cycle_day_delta": (
                physics_optimum["margin_incremental_inr_per_cycle_day"]
                - physics_baseline["margin_incremental_inr_per_cycle_day"]
            ),
            "note": "% change of the physics-verified optimum vs this physics-verified baseline; negative SOR_pct_change = lower (better) SOR.",
        }

    # --- rev 10: aggressive (FI <= 0.6) and conservative (FI <= 0.5) -------
    by_level: dict[str, Any] = {}
    for name, fi_max in levels.items():
        hit = best_level[name]
        if hit is None:
            by_level[name] = {"fi_max": fi_max, "feasible_point_found": False,
                              "best_settings": None, "physics_verified_optimum": None}
            continue
        by_level[name] = {
            "fi_max": fi_max,
            "fi_alarm_line": cycle.fi_alarm(level_params[name]),
            "feasible_point_found": True,
            "best_settings": hit[1],
            "physics_verified_optimum": hit[2],
            "objective_value": hit[0],
        }
    agg = by_level.get("aggressive", {})
    for name, entry in by_level.items():
        if entry.get("feasible_point_found") and agg.get("feasible_point_found"):
            entry["objective_given_up_vs_aggressive"] = agg["objective_value"] - entry["objective_value"]

    return {
        "aggressive": by_level.get("aggressive"),
        "conservative": by_level.get("conservative"),
        "fi_levels": levels,
        "method": (
            "Grid search directly on twin.cycle.simulate_css_cycle + summary "
            "(steam_t x cutoff_m3d x spm); no ML surrogate used. soak_days "
            "held fixed."
        ),
        "objective": objective,
        "grid_shape": grid,
        "n_grid_points_evaluated": int(np.prod(list(grid.values()))),
        "best_settings": best_x,
        "fixed_variables": {"soak_days": soak_days},
        "pinned_variables": pinned,
        "pinned_variables_note": (
            "Variables within 2% of a search-range bound. An optimum on a bound "
            "is a statement about the search box, not necessarily about the field."
            if pinned else "No variables at a search-range bound."
        ),
        "feasible_point_found": best_feasible is not None,
        "produce_end_rule": cycle.produce_end_rule_of(params),
        "feasibility_note": (
            "rev 12: under the float-onset / 'either' produce-end rule the aggressive level "
            "requires float-alarm days (FI > 0.6) <= css.fi_alarm_days (FI may cross the line only "
            "on the days that trigger the pull); the conservative level, and every level under "
            "the rate-cutoff rule (rev <= 11): "
            f"summary()['max_floating_index'] <= "
            f"{cycle.FLOATING_RISK_THRESHOLD} at the grid point -- the same "
            "raw-physics threshold the ML classifier's own training label "
            "uses (ml/train.py: (max_floating_index > 0.6) OR "
            "(alarm_days > 0)), used directly here because the trained "
            "classifier does not match a recalibrated params tree."
        ),
        "warning": warning,
        "physics_verified_optimum": physics_optimum,
        "baseline_param_midpoint": {
            "settings": baseline_a_settings,
            "physics_verified": physics_baseline_a,
        },
        "vs_baseline_param_midpoint": _vs_baseline(physics_baseline_a),
        "baseline_published_practice": {
            "settings": baseline_b_settings,
            "physics_verified": physics_baseline_b,
            "source": ml_optimize.PUBLISHED_PRACTICE_SOURCE,
            "warning": "Derived from one published first-cycle job, not OIL's current operating practice.",
        },
        "vs_baseline_published_practice": _vs_baseline(physics_baseline_b),
        "search_ranges": {k: list(v) for k, v in free_ranges.items()},
        # rev 11: which PS controls this 3-D search covers (the 5-D one covers all)
        "controls_coverage": dict(CONTROLS_COVERAGE, injection_pressure="modelled-fixed",
                                  stroke_length="modelled-fixed"),
        "controls_coverage_note": CONTROLS_COVERAGE_NOTE + (
            " This 3-D search holds pressure and stroke at params; best_settings_physics_5d "
            "optimises them."),
    }


# ===========================================================================
# rev 11: 5-D physics optimiser (steam, injection pressure, cutoff, stroke, SPM)
# ===========================================================================
# What the problem statement lists as controls, and how the twin covers each.
# `vfd` is not a separate lever: a VFD's job on a beam pump is to set the SPM
# set-point, and the twin's declining SPM schedule (T1-D: start speed `spm`,
# lowered day by day to the rods' fall-velocity limit, floored at 2 spm) IS
# that set-point trajectory over the cycle. The intra-stroke speed profile a
# VFD can also shape (slow downstroke) is out of scope (no intra-stroke
# kinematics in the day-by-day model; the dyno card uses a fixed crank
# motion). Soak is modelled but held at practice (TIER1 5b/7.4: no
# meaningful interior optimum; strict xfail).
CONTROLS_COVERAGE = {
    "steam_volume": "optimised",
    "injection_pressure": "optimised",
    "soak": "modelled-fixed",
    "cutoff": "optimised",
    "stroke_length": "optimised",
    "spm": "optimised",
    "vfd": "modelled-as-spm-schedule",
}
CONTROLS_COVERAGE_NOTE = (
    "VFD = the SPM set-point over the cycle: the twin's declining SPM schedule (start speed = the "
    "'spm' lever, lowered daily to the rods' fall-velocity limit, 2-spm floor) is what a VFD "
    "executes; the intra-stroke speed profile is out of scope. Soak is simulated but held at the "
    "10-d practice value (no meaningful interior optimum, TIER1_PROGRESS_LOG 5b/7.4).")

LEVERS_5D = ("steam_t", "p_wellhead_kgf_cm2", "cutoff_m3d", "stroke_in", "spm")
GRID_5D = {
    "steam_t": [float(x) for x in np.arange(1000.0, 2000.1, 100.0)],
    "p_wellhead_kgf_cm2": [85.0, 89.0, 93.0, 97.0],
    "cutoff_m3d": [round(float(x), 2) for x in np.arange(0.60, 2.0001, 0.05)],
    "stroke_in": [64.0, 74.0, 86.0, 100.0, 120.0, 144.0],
    "spm": [float(x) for x in np.arange(3.0, 6.001, 0.5)],
}
# rev 13: the float policy is the sixth (categorical) optimiser dimension. The
# canonical recommendation is chosen over the canonical policies (default: the
# searched policies minus "none"); "none" (no float response: FI <= the level's
# line on every day, i.e. a float-safe fixed cutoff) is searched only for the
# same-policy comparison against a baseline that does nothing about float.
POLICIES_5D = ("pull", "vfd_hold", "vfd_then_pull")
ALL_POLICIES = POLICIES_5D + ("none",)
# rev 13: three price decks are evaluated; the minimax regret is taken over the
# two national-value decks (FY25 realisation, FY26 $65 floor) as in rev 11/12.
# The net-of-levies deck (royalty + OID cess, OIL's company basis) is reported.
MINIMAX_DECKS = ("fy25_realisation", "fy26_floor")
# Baseline (b) as evaluated (published practice where published, ours where not):
BASELINE_B_5D = {"steam_t": 1300.0, "soak_days": 10.0, "cutoff_m3d": 1.30, "spm": 5.0,
                 "stroke_in": 86.0, "p_wellhead_kgf_cm2": 91.0}
SUMMARY_KEYS = (
    "margin_incremental_inr_per_cycle_day", "SOR_t_per_m3", "SOR_incremental", "oil_total_m3",
    "oil_incremental_m3", "days_total", "peak_oil_bbl_d", "peak_oil_m3d", "max_floating_index",
    "max_floating_index_produce_day", "first_float_alarm_produce_day", "failures_expected",
    "water_cut_start", "water_cut_end", "max_peak_prl_kN", "prl_cap_exceeded_days",
    "margin_inr_per_cycle_day", "cold_rate_m3d", "T_sandface_C", "P_sandface_kPa",
    "recharge_kPa", "recharge_capped", "pump_limited_days", "cadp_resteam_rate_m3d",
    # rev 12
    "produce_end_rule", "produce_end_reason", "produce_days", "peak_oil_produce_day",
    "produce_end_days_after_peak", "cold_floating_index", "cold_peak_prl_kN", "cold_mu_drag_cP",
    # rev 13
    "float_policy", "min_spm", "mean_spm", "days_at_schedule_floor", "days_vfd_slowed",
    "cold_counterfactual", "cold_status", "cold_spm", "cold_counterfactual_rate_m3d",
    "injection_margin_kPa", "injection_ok", "margin_with_opex_inr_per_cycle_day",
)


def price_decks(params: dict, levies: bool = True) -> dict[str, dict]:
    """{deck: params copy}: FY25 realisation (as shipped), the FY26 $65 floor and
    (rev 13, `levies`) the FY25 realisation net of royalty + OID cess."""
    import copy as _copy
    presets = params.get("economics", {}).get("oil_price_presets", {})
    out = {"fy25_realisation": _copy.deepcopy(params), "fy26_floor": _copy.deepcopy(params)}
    out["fy26_floor"]["economics"]["oil_price_inr_per_bbl"] = float(
        presets.get("fy26_floor_65", {}).get("inr_per_bbl", 4840.0))
    if levies and "fy25_net_of_levies" in presets:
        out["fy25_net_of_levies"] = _copy.deepcopy(params)
        out["fy25_net_of_levies"]["economics"]["oil_price_inr_per_bbl"] = float(
            presets["fy25_net_of_levies"]["inr_per_bbl"])
    return out


def _truncate_at_cutoff(df, cutoff: float):
    """The frame simulate_css_cycle would have returned at a HIGHER cutoff.

    The produce loop stops at the first row with oil < cutoff that is below
    the running peak (cycle.py rev 11); nothing before that row depends on the
    cutoff, so a run at the lowest cutoff contains every higher-cutoff run as
    a prefix (tests/test_hardening.py checks prefix == direct simulation).
    rev 13: the float policies (SPM schedule margin / floor, pull at the floor)
    do not depend on the cutoff either, so the property holds for all of them."""
    prod_mask = (df["phase"] == "produce").to_numpy()
    n_shut = int((~prod_mask).sum())
    oil = df["oil_m3d"].to_numpy()[n_shut:]
    peak = -1.0
    k_end = len(oil) - 1
    hit = False
    # rev 12: the rate cutoff applies only under the "rate_cutoff" / "either"
    # rules; the float-onset end (if any) does not depend on the cutoff, so it
    # is the frame's own last row and every higher cutoff is still a prefix.
    if df.attrs.get("produce_end_rule", "rate_cutoff") != "float_onset":
        for k, q in enumerate(oil):
            if q < cutoff and q < peak:
                k_end, hit = k, True
                break
            peak = max(peak, q)
    out = df.iloc[: n_shut + k_end + 1]
    out.attrs.update(df.attrs)
    if hit:
        out.attrs["produce_end_reason"] = "rate_cutoff"
    return out


class PhysicsEvaluator:
    """Cached true-physics evaluation of 5-D settings on several price decks.

    One simulation per (steam, pressure, stroke, spm) at the lowest cutoff;
    every cutoff is a prefix of it (_truncate_at_cutoff)."""

    def __init__(self, params: dict, soak_days: float = DEFAULT_SOAK_DAYS,
                 decks: dict[str, dict] | None = None, min_cutoff: float | None = None):
        self.params = params
        self.soak = float(soak_days)
        self.decks = decks or price_decks(params)
        self.min_cutoff = float(min_cutoff if min_cutoff is not None
                                else min(GRID_5D["cutoff_m3d"]))
        self.prl_cap = srp_mod.max_prl_kN(params)
        self._sims: dict = {}
        self._evals: dict = {}
        self.n_sims = 0

    def _sim(self, steam, p_wh, stroke_in, spm):
        key = (steam, p_wh, stroke_in, spm)
        if key not in self._sims:
            self._sims[key] = cycle.simulate_css_cycle(
                steam, self.soak, self.min_cutoff, spm, self.params,
                stroke_m=stroke_in * srp_mod.INCH_M, p_wellhead_kgf_cm2=p_wh)
            self.n_sims += 1
        return self._sims[key]

    def evaluate(self, x: dict) -> dict:
        key = tuple(float(x[k]) for k in LEVERS_5D)
        if key in self._evals:
            return self._evals[key]
        steam, p_wh, cut, stroke_in, spm = key
        if cut < self.min_cutoff - 1e-12:
            df = cycle.simulate_css_cycle(steam, self.soak, cut, spm, self.params,
                                          stroke_m=stroke_in * srp_mod.INCH_M,
                                          p_wellhead_kgf_cm2=p_wh)
        else:
            df = _truncate_at_cutoff(self._sim(steam, p_wh, stroke_in, spm), cut)
        out: dict = {"settings": dict(zip(LEVERS_5D, key), soak_days=self.soak)}
        for name, dp in self.decks.items():
            s = cycle.summary(df, dp)
            out[name] = {k: s.get(k) for k in SUMMARY_KEYS}
        first = out[next(iter(self.decks))]
        out["max_floating_index"] = first["max_floating_index"]
        out["float_alarm_days"] = first["failures_expected"]
        out["prl_ok"] = (self.prl_cap is None or first["max_peak_prl_kN"] <= self.prl_cap + 1e-9)
        out["injection_ok"] = first["injection_ok"] is not False
        self._evals[key] = out
        return out

    def feasible(self, e: dict, fi_max: float) -> bool:
        return (bool(_level_feasible(e["max_floating_index"], e["float_alarm_days"], fi_max,
                                     self.params)) and e["prl_ok"] and e["injection_ok"])


def _cutoff_table(df, cutoffs, deck_econ: dict[str, dict]) -> dict:
    """Objective and constraints for EVERY cutoff from one lowest-cutoff run.

    Re-implements, vectorised over the cutoff prefixes, exactly the
    summary() arithmetic the optimiser needs: incremental Rs per cycle-day
    (Economics v2: gross margin - power - fixed opex - the cold well's net cash
    over the same window, or 0 if the cold well is uneconomic or -- rev 13 --
    shut in by the float policy), max floating index and max Mills PRL over the
    prefix. tests/test_hardening.py checks it against cycle.summary() on
    truncated frames; the reported points are re-evaluated with summary()."""
    dt = cycle._row_dt_days(df)
    prod = (df["phase"] == "produce").to_numpy()
    n_s = int((~prod).sum())
    oil = df["oil_m3d"].to_numpy()[n_s:]
    elec = df["electric_kWh"].to_numpy()
    day = df["day"].to_numpy()
    fi = df["floating_index"].to_numpy()[n_s:]
    prl = df["peak_prl_kN"].to_numpy()[n_s:]
    fi_line = float(df.attrs.get("fi_alarm", cycle.FLOATING_RISK_THRESHOLD))
    rate_rule = df.attrs.get("produce_end_rule", "rate_cutoff") != "float_onset"
    steam_t = float(df["steam_t_cum"].max())
    q_cold = float(df["oil_cold_m3d"].iloc[0])
    e_cold = float(df["electric_cold_kWh"].iloc[0])
    fuel = float(df.attrs.get("steam_fuel_factor", 1.0))
    runmax_prev = np.concatenate([[-1.0], np.maximum.accumulate(oil)[:-1]])
    cum_oil = np.cumsum(oil) * dt
    cum_elec = (np.cumsum(elec) * dt)[n_s:]
    cum_fi = np.maximum.accumulate(fi)
    cum_prl = np.maximum.accumulate(prl)
    # rev 12: float-alarm day count (FI > the rule's alarm line) over each
    # prefix, and the index of the running peak (fragility: end - peak)
    cum_alarm = np.cumsum(fi > fi_line + cycle.ALARM_TOL) * dt
    idx = np.arange(len(oil))
    k_peak = np.maximum.accumulate(np.where(oil > runmax_prev, idx, 0))
    ks = []
    for c in cutoffs:
        hit = np.nonzero((oil < c) & (oil < runmax_prev))[0] if rate_rule else []
        ks.append(int(hit[0]) if len(hit) else len(oil) - 1)
    ks = np.asarray(ks)
    days_total = day[n_s + ks] - day[0]
    window = days_total + dt
    out = {"k_end": ks, "max_fi": cum_fi[ks], "max_prl": cum_prl[ks],
           "alarm_days": np.round(cum_alarm[ks], 6),
           "end_days_after_peak": (ks - k_peak[ks]) * dt,
           "oil_total_m3": cum_oil[ks], "days_total": days_total}
    for name, econ0 in deck_econ.items():
        econ = dict(cycle._DEFAULT_ECONOMICS, **econ0)
        price_m3 = econ["oil_price_inr_per_bbl"] * econ["bbl_per_m3"]
        tariff = float(econ.get("electricity_inr_per_kWh", 0.0) or 0.0)
        opex_d = float(econ.get("opex_inr_per_day", 0.0) or 0.0)
        margin = (cum_oil[ks] * price_m3 - steam_t * cycle.steam_cost_inr_per_t(econ) * fuel
                  - econ["fixed_cost_inr_per_cycle"])
        m_opex = margin - cum_elec[ks] * tariff - opex_d * window
        cold_cash = q_cold * price_m3 - e_cold * tariff - opex_d
        cold_net = cold_cash * window if cold_cash > 0.0 else 0.0 * window
        out[name] = (m_opex - cold_net) / window
    return out


def best_settings_physics_5d(
    params: dict,
    soak_days: float = DEFAULT_SOAK_DAYS,
    grid: dict | None = None,
    fi_levels: dict[str, float] | None = None,
    objective: str = DEFAULT_OBJECTIVE,
    return_table: bool = False,
    policies: tuple[str, ...] | list[str] | None = None,
    canonical_policies: tuple[str, ...] | list[str] | None = None,
    minimax_decks: tuple[str, ...] = MINIMAX_DECKS,
) -> dict[str, Any]:
    """rev 11-13: 5-D (+ float policy) true-physics optimiser, minimax regret.

    Levers: steam_t (1,000-2,000 t, 100-t steps), p_wellhead_kgf_cm2 (85/89/
    93/97, CONFIRMED range), cutoff_m3d (0.60-2.00, 0.05), stroke_in (API 64/
    74/86/100/120/144 in) and spm (3-6, 0.5); soak held at `soak_days`.
    rev 13: `policies` adds the operator's float response as a categorical
    dimension ("pull" / "vfd_hold" / "vfd_then_pull" / "none"; default: the
    params' own css.float_policy only, i.e. a plain 5-D search). The canonical
    point is chosen over `canonical_policies` (default: `policies` minus
    "none"); every policy also gets its own minimax point (`by_policy`), and
    baseline (b) is evaluated under every policy searched plus "none", with the
    SAME-POLICY gain (best point within policy P minus baseline (b) under P)
    reported in `gain_vs_baseline_b_same_policy`.
    Constraints (every level): float feasibility under the policy
    (`_level_feasible`: alarm days <= css.fi_alarm_days when the policy can
    pull on float, else max FI <= the level's line), the Mills peak PRL <=
    srp.max_prl_kN on every produce day, and -- rev 13 -- injectivity:
    P_sandface - P_current >= steam.min_injection_margin_kPa.
    Objective: incremental Rs per cycle-day on every deck of price_decks();
    the minimax regret is over `minimax_decks` (FY25 realisation + FY26 floor).

    Search: EXHAUSTIVE over the full grid (11 x 4 x 29 x 6 x 7 = 53,592
    points per policy), one simulation per (steam, pressure, stroke, spm,
    policy[, level line]) at the lowest cutoff, every cutoff read off as its
    prefix (_truncate_at_cutoff / _cutoff_table); the reported points are
    re-evaluated with cycle.summary(). `objective` is fixed to the
    incremental margin.
    """
    import time as _time
    if objective != DEFAULT_OBJECTIVE:
        raise ValueError("best_settings_physics_5d optimises margin_incremental_inr_per_cycle_day only")
    t0 = _time.time()
    grid = {k: list(v) for k, v in (grid or GRID_5D).items()}
    levels = {"aggressive": AGGRESSIVE_FI_MAX, "conservative": CONSERVATIVE_FI_MAX, **(fi_levels or {})}
    policies = tuple(policies) if policies else (cycle.float_policy_of(params),)
    for pol in policies:
        cycle.float_policy_of(params, pol)            # validates
    if canonical_policies is None:
        canonical_policies = tuple(p for p in policies if p != "none") or policies
    canonical_policies = tuple(canonical_policies)
    decks = price_decks(params)
    dnames = list(decks)
    nd = len(dnames)
    mm_idx = [dnames.index(d) for d in minimax_decks if d in dnames]
    deck_econ = {d: decks[d]["economics"] for d in dnames}
    cutoffs = np.asarray(grid["cutoff_m3d"], dtype=float)
    c_min = float(cutoffs.min())
    cap = srp_mod.max_prl_kN(params)
    C_ALARM, C_END, C_POL, C_INJ = 7 + nd, 8 + nd, 9 + nd, 10 + nd

    n_sims = 0

    def _table(p_run: dict, pol_idx: int) -> np.ndarray:
        """Rows (steam, p, stroke, spm, cutoff, fi, prl, v_deck..., alarm_days,
        end_days_after_peak, policy index, injection margin kPa)."""
        nonlocal n_sims
        rows = []
        for steam in grid["steam_t"]:
            for p_wh in grid["p_wellhead_kgf_cm2"]:
                for s_in in grid["stroke_in"]:
                    for spm in grid["spm"]:
                        df = cycle.simulate_css_cycle(steam, soak_days, c_min, spm, p_run,
                                                      stroke_m=s_in * srp_mod.INCH_M,
                                                      p_wellhead_kgf_cm2=p_wh)
                        n_sims += 1
                        tab = _cutoff_table(df, cutoffs, deck_econ)
                        inj = df.attrs.get("injection_margin_kPa")
                        inj = np.inf if inj is None else float(inj)
                        for j, c in enumerate(cutoffs):
                            rows.append((steam, p_wh, s_in, spm, float(c), tab["max_fi"][j],
                                         tab["max_prl"][j], *(tab[d][j] for d in dnames),
                                         tab["alarm_days"][j], tab["end_days_after_peak"][j],
                                         float(pol_idx), inj))
        return np.asarray(rows, dtype=float)

    # level x policy params and tables (a level below the policy's alarm line
    # is the same policy operated at that line: its own simulations)
    lp: dict[tuple[str, str], dict] = {}
    tables: dict[tuple[str, float, float], np.ndarray] = {}
    for pi, pol in enumerate(policies):
        base_p = _with_policy(params, pol)
        for level, fi_max in levels.items():
            q = _level_params(base_p, fi_max)
            lp[(level, pol)] = q
            key = (pol, cycle.fi_alarm(q), cycle.vfd_hold_fi(q))
            if key not in tables:
                tables[key] = _table(q, pi)

    def _tab(level: str, pol: str) -> np.ndarray:
        q = lp[(level, pol)]
        return tables[(pol, cycle.fi_alarm(q), cycle.vfd_hold_fi(q))]

    def _feas(T: np.ndarray, level: str, pol: str) -> np.ndarray:
        q = lp[(level, pol)]
        prl_ok = np.ones(len(T), bool) if cap is None else T[:, 6] <= cap + 1e-9
        inj_ok = T[:, C_INJ] >= cycle.min_injection_margin_kPa(q) - 1e-9
        return np.asarray(_level_feasible(T[:, 5], T[:, C_ALARM], levels[level], q)) & prl_ok & inj_ok

    def settings_of(T, i):
        r = T[i]
        return {"steam_t": float(r[0]), "p_wellhead_kgf_cm2": float(r[1]),
                "cutoff_m3d": round(float(r[4]), 2), "stroke_in": float(r[2]), "spm": float(r[3]),
                "float_policy": policies[int(r[C_POL])]}

    def _search(level: str, pols: tuple[str, ...]) -> dict[str, Any]:
        T = np.concatenate([_tab(level, p) for p in pols])
        feas = np.concatenate([_feas(_tab(level, p), level, p) for p in pols])
        V = T[:, 7:7 + nd]
        entry: dict[str, Any] = {"fi_max": levels[level], "n_feasible": int(feas.sum()),
                                 "policies": list(pols), "feasible_point_found": bool(feas.any())}
        q0 = lp[(level, pols[0])]
        entry["fi_alarm_line"] = cycle.fi_alarm(q0)
        entry["produce_end_rule"] = cycle.produce_end_rule_of(q0)
        entry["feasibility"] = {
            p: (f"alarm_days(FI > {cycle.fi_alarm(lp[(level, p)])}) <= css.fi_alarm_days "
                f"({cycle.fi_alarm_days(lp[(level, p)]):g})" if _uses_float_rule(lp[(level, p)])
                and levels[level] >= cycle.fi_alarm(lp[(level, p)]) - 1e-12
                else f"max_floating_index <= {levels[level]}") + " + PRL cap + injection margin"
            for p in pols}
        entry["n_failing_injection_margin"] = int(sum(
            (_tab(level, p)[:, C_INJ] < cycle.min_injection_margin_kPa(lp[(level, p)]) - 1e-9).sum()
            for p in pols))
        if not feas.any():
            return entry
        best = {d: float(V[feas, j].max()) for j, d in enumerate(dnames)}
        entry["best_value_by_deck"] = best
        entry["optimum_by_deck"] = {}
        for j, d in enumerate(dnames):
            i = int(np.flatnonzero(feas)[np.argmax(V[feas, j])])
            entry["optimum_by_deck"][d] = {"settings": settings_of(T, i), "value": float(V[i, j])}
        regret = np.max(np.stack([best[dnames[j]] - V[:, j] for j in mm_idx]), axis=0)
        regret[~feas] = np.inf
        i = int(np.argmin(regret))
        entry["minimax_regret"] = {"settings": settings_of(T, i),
                                   "max_regret_inr_per_day": float(regret[i]),
                                   "minimax_decks": [dnames[j] for j in mm_idx],
                                   "value_by_deck": {d: float(V[i, j]) for j, d in enumerate(dnames)},
                                   "end_days_after_peak": float(T[i, C_END])}
        entry["_T"], entry["_feas"] = T, feas
        return entry

    results = {level: _search(level, canonical_policies) for level in levels}
    by_policy = {pol: {level: _search(level, (pol,)) for level in levels} for pol in policies}
    agg, con = results.get("aggressive"), results.get("conservative")
    if agg and con and agg.get("feasible_point_found") and con.get("feasible_point_found"):
        con["objective_given_up_vs_aggressive"] = {
            d: agg["best_value_by_deck"][d] - con["best_value_by_deck"][d] for d in dnames}
    # the aggressive grid with NO float / PRL / injection constraint
    A = agg["_T"] if agg.get("feasible_point_found") else np.concatenate(
        [_tab("aggressive", p) for p in canonical_policies])
    V = A[:, 7:7 + nd]
    unconstrained = {}
    for j, d in enumerate(dnames):
        i = int(np.argmax(V[:, j]))
        unconstrained[d] = {"settings": settings_of(A, i), "value": float(V[i, j]),
                            "max_floating_index": float(A[i, 5]), "max_peak_prl_kN": float(A[i, 6]),
                            "injection_margin_kPa": float(A[i, C_INJ])}

    # full summary() re-evaluation of the reported points
    def _reeval(entry: dict, level: str) -> None:
        entry.pop("_T", None)
        entry.pop("_feas", None)
        if not entry.get("feasible_point_found"):
            return
        mm = entry["minimax_regret"]
        q = lp[(level, mm["settings"]["float_policy"])]
        mm["evaluation"] = _evaluate_off_grid(q, dict(mm["settings"], soak_days=soak_days), price_decks(q))
        for d, o in entry["optimum_by_deck"].items():
            q = lp[(level, o["settings"]["float_policy"])]
            o["evaluation"] = _evaluate_off_grid(q, dict(o["settings"], soak_days=soak_days),
                                                 price_decks(q))

    for level, entry in results.items():
        _reeval(entry, level)
    for pol in policies:
        for level, entry in by_policy[pol].items():
            _reeval(entry, level)

    canonical = agg["minimax_regret"]["settings"] if agg.get("feasible_point_found") else None
    pinned = ([f"{k}={canonical[k]} (grid {'floor' if canonical[k] == grid[k][0] else 'ceiling'})"
               for k in LEVERS_5D if canonical[k] in (grid[k][0], grid[k][-1])] if canonical else [])
    # baseline (b) under every policy searched, plus "none" (does nothing about float)
    base_pols = tuple(dict.fromkeys(tuple(policies) + ("none",)))
    base_by_policy = {pol: _evaluate_off_grid(_with_policy(params, pol), dict(BASELINE_B_5D, float_policy=pol),
                                              decks, soak_days) for pol in base_pols}
    base = _evaluate_off_grid(params, BASELINE_B_5D, decks, soak_days)
    # GAINS are differences of net cash per cycle-day (margin_with_opex_inr_per_cycle_day):
    # the counterfactual cancels by construction. (Incremental margins differ by the
    # cold well's cash/day, and under css.cold_counterfactual "policy" the cold well of
    # an operator who ignores float ("none") is pumped floating while under the three
    # float policies it is shut in -- comparing incremental figures across those would
    # book the counterfactual switch as gain.)
    G = "margin_with_opex_inr_per_cycle_day"
    same_policy_gain = {}
    for pol in policies:
        e = by_policy[pol]["aggressive"]
        if not e.get("feasible_point_found"):
            same_policy_gain[pol] = None
            continue
        rec_e = e["minimax_regret"]["evaluation"]
        same_policy_gain[pol] = {
            "recommendation": e["minimax_regret"]["settings"],
            **{d: rec_e[d][G] - base_by_policy[pol][d][G] for d in dnames}}
    canonical_vs_base = ({pol: {d: agg["minimax_regret"]["evaluation"][d][G] - base_by_policy[pol][d][G]
                                for d in dnames}
                          for pol in base_pols} if canonical else None)
    return {
        "method": ("Exhaustive 5-D grid x float policy on twin.cycle.simulate_css_cycle + summary (true "
                   "physics, no surrogate): one simulation per (steam, pressure, stroke, spm, policy) at the "
                   "lowest cutoff, every cutoff read off as its prefix; soak fixed."),
        "objective": objective,
        "decks": {d: decks[d]["economics"]["oil_price_inr_per_bbl"] for d in dnames},
        "minimax_decks": [dnames[j] for j in mm_idx],
        "grid": grid,
        "policies": list(policies),
        "canonical_policies": list(canonical_policies),
        "n_grid_points": int(len(A)),
        "n_simulations": n_sims,
        "soak_days_fixed": float(soak_days),
        "produce_end_rule": cycle.produce_end_rule_of(params),
        "fi_alarm_days": cycle.fi_alarm_days(params),
        "constraints": {"fi_levels": levels, "max_prl_kN": cap,
                        "min_injection_margin_kPa": cycle.min_injection_margin_kPa(params),
                        "n_points_failing_prl_cap": int((A[:, 6] > cap + 1e-9).sum()) if cap is not None else 0,
                        "n_points_failing_injection_margin": agg.get("n_failing_injection_margin")},
        "levels": results,
        "by_policy": by_policy,
        "unconstrained_optimum_by_deck": unconstrained,
        "price_of_constraints_by_deck": (
            {d: unconstrained[d]["value"] - agg["best_value_by_deck"][d] for d in dnames}
            if agg.get("feasible_point_found") else None),
        "canonical_recommendation": {
            "settings": (dict(canonical, soak_days=float(soak_days),
                              stroke_m=canonical["stroke_in"] * srp_mod.INCH_M) if canonical else None),
            "rule": ("aggressive (float feasibility under the policy, PRL cap, injection margin) "
                     "minimax-regret across the FY25 and FY26-floor decks, over the float policies "
                     + ", ".join(canonical_policies)),
            "evaluation": (agg["minimax_regret"]["evaluation"] if canonical else None),
            "pinned_at_grid_edge": pinned,
        },
        "baseline_b": {"settings": BASELINE_B_5D, "evaluation": base,
                       "note": ("steam 1,300 t / soak 10 d BGW-8-derived; 91 kgf/cm2 = mid of the "
                                "CONFIRMED 85-97; cutoff 1.3 and 5 spm / 86 in are the team's "
                                "assumptions, not OIL practice; its float policy is the params' "
                                "css.float_policy (see baseline_b_by_policy).")},
        "baseline_b_by_policy": base_by_policy,
        "gain_metric": "difference of margin_with_opex_inr_per_cycle_day (net cash per cycle-day; counterfactual-free)",
        "gain_vs_baseline_b_same_policy": same_policy_gain,
        "canonical_gain_vs_baseline_b_by_baseline_policy": canonical_vs_base,
        "controls_coverage": dict(CONTROLS_COVERAGE, **(
            {"vfd": "optimised-as-float-policy"} if len(canonical_policies) > 1 else {})),
        "controls_coverage_note": CONTROLS_COVERAGE_NOTE + (
            " rev 13: the VFD's float response (pull / vfd_hold / vfd_then_pull) is searched as a "
            "categorical dimension." if len(canonical_policies) > 1 else ""),
        "runtime_s": round(_time.time() - t0, 1),
        **({"table": A, "table_columns": ["steam_t", "p_wellhead_kgf_cm2", "stroke_in", "spm",
                                          "cutoff_m3d", "max_floating_index", "max_peak_prl_kN",
                                          *dnames, "float_alarm_days", "end_days_after_peak",
                                          "policy_index", "injection_margin_kPa"]}
           if return_table else {}),
    }


def _evaluate_off_grid(params: dict, settings: dict, decks: dict[str, dict],
                       soak_days: float | None = None) -> dict:
    """One direct simulation (no cutoff-prefix cache), priced on every deck.
    rev 13: `settings["float_policy"]` (optional) overrides css.float_policy."""
    df = cycle.simulate_css_cycle(
        settings["steam_t"], settings.get("soak_days", soak_days or DEFAULT_SOAK_DAYS),
        settings["cutoff_m3d"], settings["spm"], params,
        stroke_m=settings["stroke_in"] * srp_mod.INCH_M,
        p_wellhead_kgf_cm2=settings["p_wellhead_kgf_cm2"],
        float_policy=settings.get("float_policy"))
    out: dict = {"settings": dict(settings)}
    for name, dp in decks.items():
        s = cycle.summary(df, dp)
        out[name] = {k: s.get(k) for k in SUMMARY_KEYS}
    first = out[next(iter(decks))]
    out["max_floating_index"] = first["max_floating_index"]
    out["float_alarm_days"] = first["failures_expected"]      # rev 12
    cap = srp_mod.max_prl_kN(params)
    out["prl_ok"] = cap is None or first["max_peak_prl_kN"] <= cap + 1e-9
    out["injection_ok"] = first["injection_ok"] is not False  # rev 13
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--params", default=str(DEFAULT_PARAMS_PATH))
    parser.add_argument("--soak-days", type=float, default=DEFAULT_SOAK_DAYS)
    parser.add_argument("--three-d", action="store_true",
                        help="run the rev-10 3-D grid (steam x cutoff x spm) instead of the 5-D search")
    parser.add_argument("--policies", default=",".join(ALL_POLICIES),
                        help="rev 13: comma-separated float policies to search (canonical over all but 'none')")
    args = parser.parse_args()

    with open(args.params, encoding="utf-8") as f:
        params = json.load(f)

    if args.three_d:
        result = best_settings_physics(params, fixed={"soak_days": args.soak_days})
    else:
        result = best_settings_physics_5d(params, soak_days=args.soak_days,
                                          policies=[p.strip() for p in args.policies.split(",") if p.strip()])
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
