"""Bayesian optimization over CSS + SRP + policy settings using the trained
surrogate models.

`best_settings(params)` searches the 7 design inputs (steam_t, soak_days,
cutoff_m3d, spm, p_wellhead_kgf_cm2, stroke_in, float_policy) -- ranges taken
from `params["css"]`/`params["srp"]`/`params["steam"]`, `spm` restricted to
`params["srp"]["spm_practice_band"]` (heavy-oil SRP practice; falls back to
`srp.spm_range` if the band key is absent), `float_policy` restricted to
POLICY_LEVELS (pull / vfd_hold / vfd_then_pull -- twin/generate_data.py's LHS
never samples "none", so the surrogate never saw it) -- for the setting that
**maximises predicted margin_with_opex_inr_per_cycle_day** (net cash per
cycle-day, ml/models/margin_net_cash_model.joblib), subject to a hard
injectivity gate (predicted sandface pressure at the candidate
p_wellhead_kgf_cm2 must clear `steam.min_injection_margin_kPa` over the
params' own `reservoir.P_current_kPa`/`P_initial_kPa` -- computed from the
true steam-state physics, not a surrogate, since it needs no cycle
simulation), enforced as an additive penalty.

rev 13 (wave 5) change of objective and search space
(docs/model-improvement/TIER1_PROGRESS_LOG.md section 12.1/12.6/12.12; see
also ml/train.py's module docstring):
  - The operator's float response is now a control (`css.float_policy`), so
    it is searched as a 7th, categorical dimension alongside the rev-12 six.
  - The objective moves from the INCREMENTAL margin/cycle-day (rev 9-12,
    ml/models/margin_incremental_model.joblib, still trained and reported for
    continuity) to the NET CASH margin/cycle-day
    (margin_with_opex_inr_per_cycle_day): the incremental metric subtracts a
    cold-well counterfactual that itself depends on the float policy
    (css.cold_counterfactual "policy": shut in under the three float
    policies, pumped floating under "none"), so comparing it ACROSS policies
    would book that counterfactual switch as if it were part of the
    recommendation's own gain. Net cash has no such term and is the fair
    objective across a policy-inclusive search.
  - The rev-9/10/11/12 soft float-probability penalty (float_model.joblib
    predicting "risk of floating") is DROPPED: once the float response is a
    policy, the pull IS that policy's float response at every setting, so
    penalising "risk of floating" fights the physics rather than modelling a
    real cost (external re-score finding N7). float_model.joblib now predicts
    the rev-13 `float_premature_pull` label instead and is loaded/reported
    for information only (not a constraint).
  - A hard injectivity gate replaces it as the surrogate search's one
    constraint (the physics grid, ml/recommend_physics.py, already gates on
    this; TIER1 section 12.5/12.9: 85 kgf/cm2 gives only 53 kPa of margin and
    fails a 300-400 kPa gate).

rev 9 change of objective (Economics v2 + FY25 price deck, was: maximise
predicted GROSS margin_inr_per_cycle_day, ml/models/margin_model.joblib, still
loaded and reported for continuity). Per
docs/model-improvement/TIER1_PROGRESS_LOG.md section 8: gross margin credits
CSS with the oil the well would have made anyway (the cold, unstimulated
counterfactual); the incremental margin -- oil over that cold baseline for the
same calendar window, net of daily opex including pumping power -- is what
actually decides whether stimulating beats leaving the well alone. Gross SOR
stays the reported engineering yardstick (headline convention unchanged;
params/CHANGELOG.md rev 8 section 8.2), and gross margin is still reported at
every point for comparison.

rev 5 change of objective (was: minimise predicted SOR). Per
docs/model-improvement/TIER1_PROGRESS_LOG.md section 4 (the rev-5 calibration
log): SOR rises monotonically with steam -- honest physics, not a bug -- so
"minimise SOR" always pushes to the steam floor and is not the field's actual
goal. Margin per cycle-day has an interior optimum near 1,500 t (flat over
1,000-2,000 t) because it amortises the fixed cost of the inject+soak days
that earn nothing, which is the number that actually matters operationally.
SOR is still reported at every point (derived: SOR = steam_t / oil_pred),
because it stays the field's own engineering yardstick.

Every settings dict this module returns (the optimum and both baselines) is
also run through the **true physics twin** (`twin.cycle.simulate_css_cycle` +
`summary`) -- this file never reports a surrogate number without also
reporting what the physics actually gives at that point, and the gap between
the two. Note (rev 13): the physics GRID search (ml/recommend_physics.py's
`best_settings_physics_5d`, exhaustive over the same 6 continuous/discrete
levers x policy) is the canonical answer reported in the deck/docs -- this
surrogate optimizer is the faster, approximate cross-check; expect it to fall
short of the grid's optimum (a smaller search budget, N_CALLS Bayesian calls
vs an exhaustive grid), not to replace it.

Also runnable as a script:
    python optimize.py [--params path/to/field_params.json]
prints the result dict as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from skopt import gp_minimize
from skopt.space import Categorical, Integer, Real
from skopt.utils import use_named_args

# Allow `python ml/optimize.py` (run directly) to find the `twin` package
# regardless of process cwd, same pattern as twin/generate_data.py.
_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ROOT_FOR_IMPORT))

from twin import cycle  # noqa: E402  (see sys.path shim above)
from twin import generate_data as gendata  # noqa: E402 (rev 12: shared pressure/stroke range helpers)
from twin import thermal  # noqa: E402 (rev 13: cheap steam-state injectivity gate)

SEED = 42
# rev 12: the 6 continuous/discrete controls the physics grid
# (ml/recommend_physics.py best_settings_physics_5d) searches -- steam, soak
# (fixed 10 d via `fixed`, per TIER1_PROGRESS_LOG.md section 4.5/11.9: no
# interior optimum), cutoff, spm (practice band 3-6), plus the rev-11/12
# surface controls injection pressure and stroke length.
NUMERIC_FEATURES = ["steam_t", "soak_days", "cutoff_m3d", "spm", "p_wellhead_kgf_cm2", "stroke_in"]
# rev 13: the operator's float response, a 7th (categorical) control -- see
# the module docstring and ml/train.py. Order/levels must match ml/train.py's
# POLICY_LEVELS exactly (the one-hot columns a loaded model was fit on).
POLICY_LEVELS = ["pull", "vfd_hold", "vfd_then_pull"]
POLICY_FEATURES = [f"policy_{p}" for p in POLICY_LEVELS]
FEATURES = NUMERIC_FEATURES + POLICY_FEATURES
# The 7 raw search/settings dimensions (float_policy as ONE categorical key,
# not the 3 one-hot columns) -- what best_settings()'s `space`/`fixed`/
# returned "best_settings" dict are keyed on. _to_X() converts a settings
# dict on these keys into the one-hot FEATURES row a model was fit on.
SETTINGS_KEYS = NUMERIC_FEATURES + ["float_policy"]
# rev 13: injectivity gate penalty, Rs per kPa of shortfall below
# steam.min_injection_margin_kPa (400 by default). Calibrated so a candidate
# missing the gate by the 85-kgf/cm2 shortfall (~347 kPa short of 400, TIER1
# section 12.9) picks up a ~Rs 17k/d penalty -- comparable to the whole
# feasible net-cash spread, so the gate dominates without an absurd cliff.
INJECTION_PENALTY_SCALE = 50.0
N_CALLS = 60
N_INITIAL_POINTS = 15
# Honesty check (rev-5 task): flag any optimum variable sitting within this
# fraction of its search-range width from either bound.
PIN_TOL_FRAC = 0.02

ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = ML_DIR / "models"
DEFAULT_PARAMS_PATH = ML_DIR.parent / "params" / "field_params.json"

# Published-practice baseline (b): derived from the BGW-8 first-CSS-cycle job,
# docs/research/baghewala_facts.md section 4 -- injection ~74 t/d x 14-21 d =
# ~1,040-1,560 t (midpoint ~1,300 t), soak "50-60% of the injection-phase
# length (~7-13 days)" -- 10 d used as a round midpoint, cutoff left at the
# params-range midpoint (no published cutoff number), spm 5.0 (mid of the
# published/typical heavy-oil practice band). This is NOT OIL's current
# operating practice -- it is one documented first-cycle job, used as an
# external reference point.
PUBLISHED_PRACTICE_BASELINE = {
    "steam_t": 1300.0,
    "soak_days": 10.0,
    "cutoff_m3d": None,  # filled from params["css"]["cutoff_rate_m3d_range"] midpoint
    "spm": 5.0,
    # rev 12: the two new controls at the CONFIRMED BGW-8 wellhead reading
    # (91 kgf/cm2, the mid of 85-97) and the assumed-typical 86-in unit
    # (TIER1_PROGRESS_LOG.md section 10.4's "reference"/"baseline (b)" rows).
    "p_wellhead_kgf_cm2": 91.0,
    "stroke_in": 86.0,
    # rev 13: operated under the RECOMMENDED policy (VFD-hold, the fair
    # same-policy comparison, TIER1 section 12.6) rather than the params
    # default ("pull") -- see vs_baseline_published_practice's note.
    "float_policy": "vfd_hold",
}
PUBLISHED_PRACTICE_SOURCE = (
    "docs/research/baghewala_facts.md section 4, BGW-8 first CSS cycle "
    "(Dec 2018): injection rate ~3,100 kg/hr (~74.4 t/d) x 14-21 d injection "
    "-> ~1,040-1,560 t steam (1,300 t used as midpoint); soak 50-60% of the "
    "injection length (~7-13 d, 10 d used); cutoff not published, params-range "
    "midpoint used; spm not published, 5.0 (typical heavy-oil mid-practice) used."
)

_oil_model = None
_margin_model = None
_margin_incremental_model = None
_margin_net_cash_model = None
_float_model = None


def _load_models():
    global _oil_model, _margin_model, _margin_incremental_model, _margin_net_cash_model, _float_model
    if None in (_oil_model, _margin_model, _margin_incremental_model, _margin_net_cash_model, _float_model):
        for fname in (
            "oil_model.joblib", "margin_model.joblib", "margin_incremental_model.joblib",
            "margin_net_cash_model.joblib", "float_model.joblib",
        ):
            if not (MODELS_DIR / fname).exists():
                raise FileNotFoundError(f"{MODELS_DIR / fname} not found. Run train.py first.")
        _oil_model = joblib.load(MODELS_DIR / "oil_model.joblib")
        _margin_model = joblib.load(MODELS_DIR / "margin_model.joblib")
        _margin_incremental_model = joblib.load(MODELS_DIR / "margin_incremental_model.joblib")
        _margin_net_cash_model = joblib.load(MODELS_DIR / "margin_net_cash_model.joblib")
        _float_model = joblib.load(MODELS_DIR / "float_model.joblib")
    return _oil_model, _margin_model, _margin_incremental_model, _margin_net_cash_model, _float_model


def _stroke_options(params: dict) -> list[float]:
    """The discrete API stroke lengths (in) the 6-D search chooses from --
    same list twin/generate_data.py's LHS strata over (srp.stroke_in_options)."""
    return gendata.sampled_stroke_options(params)


def _ranges_from_params(params: dict) -> dict:
    """Extract the 6 input ranges from params. spm uses the practice band;
    stroke_in is reported as (min, max) of its discrete option list for
    pin-checking / baseline-midpoint purposes -- the actual search space
    (best_settings' `space` list) uses the discrete set via Categorical."""
    css = params["css"]
    srp = params["srp"]
    spm_band = srp.get("spm_practice_band", srp["spm_range"])
    strokes = _stroke_options(params)
    return {
        "steam_t": tuple(css["steam_volume_t_range"]),
        "soak_days": tuple(css["soak_days_range"]),
        "cutoff_m3d": tuple(css["cutoff_rate_m3d_range"]),
        "spm": tuple(spm_band),
        # rev 12: the two rev-11/12 surface controls.
        "p_wellhead_kgf_cm2": gendata.sampled_pressure_range(params),
        "stroke_in": (min(strokes), max(strokes)),
    }


def _predict_margin(margin_model, X: np.ndarray) -> np.ndarray:
    return margin_model.predict(X)


def _predict_oil(oil_model, X: np.ndarray) -> np.ndarray:
    return oil_model.predict(X)


def _predict_float_prob(float_model, X: np.ndarray) -> np.ndarray:
    """Predicted P(float_premature_pull) (rev 13 label) -- informational only
    as of rev 13; see the module docstring (no longer a search constraint)."""
    return float_model.predict_proba(X)[:, 1]


def _derived_sor(steam_t: float, oil_m3: float) -> float:
    return float(steam_t / oil_m3) if oil_m3 > 1e-9 else float("inf")


def _injection_margin_kPa(p_wellhead_kgf_cm2: float, params: dict) -> float:
    """rev 13: sandface pressure minus the pre-cycle reservoir pressure at a
    given wellhead pressure -- the injectivity gate's own quantity
    (twin.cycle summary()'s `injection_margin_kPa`), computed directly from
    the steam-state physics (twin.thermal.steam_state) with NO cycle
    simulation, so it is cheap enough to call once per Bayesian-search
    candidate."""
    st = thermal.steam_state(params, p_wellhead_kgf_cm2=float(p_wellhead_kgf_cm2))
    P_sf = st.get("P_sandface_kPa")
    if P_sf is None:   # "legacy_T" steam-state model: no pressure state, no gate
        return float("inf")
    return float(P_sf) - cycle.reservoir_pressure_kPa(params)


def _physics_verify(settings: dict, params: dict) -> dict:
    """Run the true twin at a settings dict and pull the reported metrics.

    rev 12: also passes the two surface controls (stroke_m, converted from
    the settings dict's stroke_in; p_wellhead_kgf_cm2) through to the twin
    when present, so a 6-D settings dict is verified at the SAME point the
    surrogate/grid search chose, not silently at the twin's own defaults
    (86 in / 91 kgf/cm2). Falls back to those defaults for any 4-D settings
    dict a caller still passes without the two new keys (backward compat).
    rev 13: also passes float_policy when present.
    """
    df = cycle.simulate_css_cycle(
        steam_t=settings["steam_t"],
        soak_days=settings["soak_days"],
        cutoff_m3d=settings["cutoff_m3d"],
        spm=settings["spm"],
        params=params,
        stroke_m=(float(settings["stroke_in"]) * 0.0254 if "stroke_in" in settings else None),
        p_wellhead_kgf_cm2=settings.get("p_wellhead_kgf_cm2"),
        float_policy=settings.get("float_policy"),
    )
    s = cycle.summary(df, params=params)
    return {
        "SOR_t_per_m3": s["SOR_t_per_m3"],
        "oil_total_m3": s["oil_total_m3"],
        "days_total": s["days_total"],
        "margin_inr": s["margin_inr"],
        "margin_inr_per_cycle_day": s["margin_inr_per_cycle_day"],
        # Economics v2 (27 Sep 2026, additive): incremental-over-cold basis.
        "SOR_incremental": s["SOR_incremental"],
        "oil_incremental_m3": s["oil_incremental_m3"],
        "margin_with_opex_inr_per_cycle_day": s["margin_with_opex_inr_per_cycle_day"],
        "margin_incremental_inr": s["margin_incremental_inr"],
        "margin_incremental_inr_per_cycle_day": s["margin_incremental_inr_per_cycle_day"],
        "max_floating_index": s["max_floating_index"],
        "alarm_days": s["days_rods_in_compression"],
        "steam_cost_inr": s["steam_cost_inr"],
        "co2_t": s["co2_t"],
        # rev 12: what actually ended the produce phase (float onset vs rate
        # cutoff) -- material context for any 6-D optimum (TIER1 section 11).
        "produce_end_reason": s.get("produce_end_reason"),
        # rev 13: the operating policy and the injectivity gate.
        "float_policy": s.get("float_policy"),
        "injection_margin_kPa": s.get("injection_margin_kPa"),
        "injection_ok": s.get("injection_ok"),
    }


def _pct_change(baseline: float, new: float) -> float | None:
    """(new - baseline) / |baseline| * 100. None if baseline is ~0."""
    if baseline is None or abs(baseline) < 1e-9:
        return None
    return float((new - baseline) / abs(baseline) * 100.0)


def _pinned_variables(best_x: dict, ranges: dict) -> dict:
    pinned = {}
    for f, v in best_x.items():
        lo, hi = ranges[f]
        width = hi - lo
        if width <= 0:
            continue
        if (v - lo) <= PIN_TOL_FRAC * width:
            pinned[f] = "lower"
        elif (hi - v) <= PIN_TOL_FRAC * width:
            pinned[f] = "upper"
    return pinned


def best_settings(params: dict, fixed: dict[str, float] | None = None) -> dict[str, Any]:
    """Find CSS+SRP+policy settings that maximise predicted net cash per
    cycle-day, subject to a hard injectivity gate, SPM restricted to the
    practice band and float_policy restricted to POLICY_LEVELS.

    Args:
        params: the loaded contents of params/field_params.json.
        fixed: optional {feature_name: value} to hold constant, collapsing
            that dimension out of the search entirely (it is never passed to
            `gp_minimize`, just spliced into every candidate's feature vector
            and into the reported `best_settings`). E.g. `{"soak_days": 10}`
            to search only steam/cutoff/spm/pressure/stroke/policy because
            field practice fixes soak and the twin has no interior optimum in
            it (TIER1_PROGRESS_LOG.md section 4.5/5.3/12.5: "small monotone
            benefit only -- do not present 'the twin says soak N days'").
            Default (None / {}) searches every one of the 7 raw inputs
            (SETTINGS_KEYS) -- existing callers (api/main.py) are unaffected
            except that float_policy is now also free unless fixed.

    Returns:
        dict -- see module docstring. Keeps the top-level "best_settings" key
        (the optimized input dict) for backward compatibility with any caller
        that reads only that field; everything else is additive.
    """
    fixed = dict(fixed) if fixed else {}
    oil_model, margin_model, margin_incremental_model, margin_net_cash_model, float_model = _load_models()
    ranges = _ranges_from_params(params)
    strokes = _stroke_options(params)
    min_inj_margin = cycle.min_injection_margin_kPa(params)

    free_features = [f for f in SETTINGS_KEYS if f not in fixed]

    def _dim(f: str):
        if f == "soak_days":
            return Integer(int(ranges[f][0]), int(ranges[f][1]), name=f)
        if f == "stroke_in":
            # rev 12: stroke is a discrete API size, not a continuous range --
            # searched as a Categorical over the same options
            # twin/generate_data.py's LHS strata over (srp.stroke_in_options).
            return Categorical(strokes, name=f)
        if f == "float_policy":
            # rev 13: the operator's float response, categorical.
            return Categorical(POLICY_LEVELS, name=f)
        return Real(*ranges[f], name=f)

    space = [_dim(f) for f in free_features]

    def _to_X(full: dict) -> np.ndarray:
        """Numeric features, then the one-hot float_policy columns -- the
        exact FEATURES column order ml/train.py's models were fit on."""
        row = [float(full[f]) for f in NUMERIC_FEATURES]
        row += [1.0 if full["float_policy"] == p else 0.0 for p in POLICY_LEVELS]
        return np.array([row])

    @use_named_args(space)
    def objective(**kwargs) -> float:
        full = {**fixed, **kwargs}
        X = _to_X(full)
        # rev 13: objective is NET CASH margin/cycle-day (counterfactual-free;
        # see module docstring).
        margin_pred = float(_predict_margin(margin_net_cash_model, X)[0])
        # rev 13: hard injectivity gate replaces the rev-9/12 float-probability
        # penalty (dropped -- see module docstring). Computed from the true
        # steam-state physics, not a surrogate.
        inj_margin = _injection_margin_kPa(full["p_wellhead_kgf_cm2"], params)
        penalty = 0.0
        if inj_margin < min_inj_margin:
            penalty = INJECTION_PENALTY_SCALE * (min_inj_margin - inj_margin)
        # gp_minimize minimises -> maximise margin by minimising its negative,
        # plus the constraint penalty (which only makes candidates worse).
        return -margin_pred + penalty

    result = gp_minimize(
        objective,
        space,
        n_calls=N_CALLS,
        n_initial_points=N_INITIAL_POINTS,
        random_state=SEED,
    )

    best_free: dict[str, Any] = {}
    for f, v in zip(free_features, result.x):
        if f == "soak_days":
            best_free[f] = int(v)
        elif f == "float_policy":
            best_free[f] = str(v)
        else:
            best_free[f] = float(v)
    best_x = {f: (fixed[f] if f in fixed else best_free[f]) for f in SETTINGS_KEYS}
    if "soak_days" in best_x:
        best_x["soak_days"] = int(best_x["soak_days"])
    X_best = _to_X(best_x)
    predicted_margin_net_cash = float(_predict_margin(margin_net_cash_model, X_best)[0])
    predicted_margin_incremental = float(_predict_margin(margin_incremental_model, X_best)[0])
    predicted_margin_gross = float(_predict_margin(margin_model, X_best)[0])
    predicted_oil = float(_predict_oil(oil_model, X_best)[0])
    predicted_sor = _derived_sor(best_x["steam_t"], predicted_oil)
    predicted_premature_pull_prob = float(_predict_float_prob(float_model, X_best)[0])
    _pin_free = {f: v for f, v in best_free.items() if f != "float_policy"}
    _pin_ranges = {f: ranges[f] for f in free_features if f != "float_policy"}
    pinned = _pinned_variables(_pin_free, _pin_ranges)

    physics_optimum = _physics_verify(best_x, params)
    surrogate_vs_physics_gap = {
        "margin_with_opex_inr_per_cycle_day_pct": _pct_change(
            physics_optimum["margin_with_opex_inr_per_cycle_day"], predicted_margin_net_cash
        ),
        "margin_incremental_inr_per_cycle_day_pct": _pct_change(
            physics_optimum["margin_incremental_inr_per_cycle_day"], predicted_margin_incremental
        ),
        "margin_inr_per_cycle_day_pct": _pct_change(
            physics_optimum["margin_inr_per_cycle_day"], predicted_margin_gross
        ),
        "SOR_t_per_m3_pct": _pct_change(physics_optimum["SOR_t_per_m3"], predicted_sor),
        "surrogate_margin_with_opex_inr_per_cycle_day": predicted_margin_net_cash,
        "physics_margin_with_opex_inr_per_cycle_day": physics_optimum["margin_with_opex_inr_per_cycle_day"],
        "surrogate_margin_incremental_inr_per_cycle_day": predicted_margin_incremental,
        "physics_margin_incremental_inr_per_cycle_day": physics_optimum["margin_incremental_inr_per_cycle_day"],
        "surrogate_margin_inr_per_cycle_day": predicted_margin_gross,
        "physics_margin_inr_per_cycle_day": physics_optimum["margin_inr_per_cycle_day"],
        "surrogate_SOR_t_per_m3": predicted_sor,
        "physics_SOR_t_per_m3": physics_optimum["SOR_t_per_m3"],
    }

    # --- Baseline (a): param-midpoint of the same search ranges (spm band
    # included) -- same methodology as the pre-rev5 optimizer's baseline.
    # rev 12: stroke_in has no continuous midpoint (it is a discrete API
    # size) -- snap the numeric range midpoint to the nearest option.
    # rev 13: float_policy is left unset (the params' own default, "pull") --
    # a categorical control has no "midpoint".
    def _midpoint(f: str) -> float:
        lo, hi = ranges[f]
        mid = (lo + hi) / 2.0
        if f == "soak_days":
            return round(mid)
        if f == "stroke_in":
            return min(strokes, key=lambda s: abs(s - mid))
        return mid

    baseline_a_settings = {f: _midpoint(f) for f in NUMERIC_FEATURES}
    physics_baseline_a = _physics_verify(baseline_a_settings, params)

    # --- Baseline (b): published-practice (BGW-8 first cycle), NOT OIL's
    # current operating practice -- see PUBLISHED_PRACTICE_SOURCE.
    baseline_b_settings = dict(PUBLISHED_PRACTICE_BASELINE)
    baseline_b_settings["cutoff_m3d"] = (ranges["cutoff_m3d"][0] + ranges["cutoff_m3d"][1]) / 2.0
    physics_baseline_b = _physics_verify(baseline_b_settings, params)

    def _vs_baseline(physics_baseline: dict) -> dict:
        return {
            "SOR_pct_change": _pct_change(
                physics_baseline["SOR_t_per_m3"], physics_optimum["SOR_t_per_m3"]
            ),
            "margin_inr_per_cycle_day_pct_change": _pct_change(
                physics_baseline["margin_inr_per_cycle_day"],
                physics_optimum["margin_inr_per_cycle_day"],
            ),
            "margin_incremental_inr_per_cycle_day_delta": (
                physics_optimum["margin_incremental_inr_per_cycle_day"]
                - physics_baseline["margin_incremental_inr_per_cycle_day"]
            ),
            # rev 13: the FAIR delta when the optimum and this baseline are run
            # under DIFFERENT float policies -- net cash has no cold-baseline
            # term, so it never books the counterfactual switch (css.
            # cold_counterfactual "policy") as if it were the recommendation's
            # own gain (TIER1_PROGRESS_LOG.md section 12.1/12.6). When both
            # sides share one policy the two deltas are identical by
            # construction.
            "margin_with_opex_inr_per_cycle_day_delta": (
                physics_optimum["margin_with_opex_inr_per_cycle_day"]
                - physics_baseline["margin_with_opex_inr_per_cycle_day"]
            ),
            "same_float_policy": (physics_optimum.get("float_policy") == physics_baseline.get("float_policy")),
            "note": "% change of the physics-verified optimum vs this physics-verified baseline; negative SOR_pct_change = lower (better) SOR. Both incremental and net-cash margin are reported as absolute Rs/cycle-day deltas (a negative baseline makes a % change misleading); net cash is the fair one when float_policy differs (same_float_policy False).",
        }

    return {
        # --- kept for backward compatibility: raw optimizer inputs ---
        "best_settings": best_x,
        "objective": "margin_with_opex_inr_per_cycle_day",
        "predicted_margin_with_opex_inr_per_cycle_day": predicted_margin_net_cash,
        "predicted_margin_incremental_inr_per_cycle_day": predicted_margin_incremental,
        "predicted_margin_inr_per_cycle_day": predicted_margin_gross,
        "predicted_SOR": predicted_sor,
        "predicted_oil_total_m3": predicted_oil,
        "predicted_float_premature_pull_probability": predicted_premature_pull_prob,
        "predicted_float_premature_pull_probability_note": (
            "Informational only as of rev 13 (float_model.joblib's rev-13 label "
            "float_premature_pull) -- NOT a search constraint. See the module "
            "docstring: penalising float risk once the float response is an "
            "operating policy fights the physics (re-score N7)."
        ),
        "injection_margin_gate_kPa": min_inj_margin,
        "spm_search_band": list(ranges["spm"]),
        "policy_search_levels": list(POLICY_LEVELS),
        "fixed_variables": fixed,
        "pinned_variables": pinned,
        "pinned_variables_note": (
            "Variables within 2% of a search-range bound (float_policy excluded, "
            "categorical). An optimum on a bound is a statement about the search "
            "box, not necessarily about the field -- see "
            "docs/model-improvement/TIER1_PROGRESS_LOG.md section 4."
            if pinned else "No variables at a search-range bound."
        ),
        # --- physics-verified optimum ---
        "physics_verified_optimum": physics_optimum,
        "surrogate_vs_physics_gap": surrogate_vs_physics_gap,
        # --- baseline (a): param-midpoint ---
        "baseline_param_midpoint": {
            "settings": baseline_a_settings,
            "physics_verified": physics_baseline_a,
        },
        "vs_baseline_param_midpoint": _vs_baseline(physics_baseline_a),
        # --- baseline (b): published-practice (BGW-8), explicitly NOT current practice ---
        "baseline_published_practice": {
            "settings": baseline_b_settings,
            "physics_verified": physics_baseline_b,
            "source": PUBLISHED_PRACTICE_SOURCE,
            "warning": "Derived from one published first-cycle job, not OIL's current operating practice.",
        },
        "vs_baseline_published_practice": _vs_baseline(physics_baseline_b),
        "search_ranges": {k: list(v) for k, v in ranges.items()},
        "n_calls": N_CALLS,
        "n_initial_points": N_INITIAL_POINTS,
        "seed": SEED,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--params",
        default=str(DEFAULT_PARAMS_PATH),
        help="Path to field_params.json (default: params/field_params.json)",
    )
    args = parser.parse_args()

    with open(args.params) as f:
        params = json.load(f)

    result = best_settings(params)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
