"""twin/calibrate.py -- fit the twin's most uncertain constants to observed
field cycles ("ingest -> recalibrate -> re-recommend").

Today the twin is a simulator with fixed constants -- the biggest uncertain
ones, per `ml/uq.py`'s own tornado ranking, are `fluid.water_cut` (0.85, no
field datum), `reservoir.thickness_m` (12 m, "NOT FOUND for Baghewala" per
`params/CHANGELOG.md`) and `ipr.AOF_REF_M3D` (0.46, hand-tuned against a
single published uplift ratio). `thermal.BL_DELTA_FACTOR` is NO LONGER a
default free parameter (27 Sep 2026): physics v3 sourced it as the 1/2 in
Boberg & Lantz's own delta (PEH Eqs. 15.70/15.73; params/CHANGELOG.md rev 7),
so it is a definition, not a fit knob. It is still ACCEPTED in `free` (e.g. to
test a hypothesis), just off by default. rev 10 (27 Sep 2026): the cold-well
damage skin `s_cold` (params["ipr"]["s_cold"], [ASSUMPTION] 5, decides ~40 %
of the modelled uplift) is ACCEPTED as an optional free parameter, bounds
0-8, also off by default: with oil/days/peak totals it trades off against
`aof_ref_m3d` (both set the stimulated-to-cold productivity ratio), so free
it only with a peak rate AND a cold (pre-CSS) rate per well, or a build-up
test. Oil India records per-well cycle data (the
PS says so); this module is the loop that turns that data into a recalibrated
twin, closing the gap between "simulator" and "digital twin".

Observed-cycles CSV schema (one row per completed CSS cycle)
--------------------------------------------------------------
Required columns:
    well_id        str    -- well identifier, e.g. "BGW-8" (reporting only).
    steam_t        float  -- steam injected this cycle, tonnes.
    soak_days      float  -- shut-in soak duration, days.
    spm            float  -- sucker-rod pump start speed, strokes/minute.
    oil_m3         float  -- TOTAL oil produced over the cycle's produce
                              phase, m3 (matches `summary()["oil_total_m3"]`).
    produce_days   float  -- length of the produce phase, days (matches
                              `summary()["days_total"]`, i.e. the day the well
                              was shut in / cycle ended minus the day the
                              produce phase started).
Optional columns:
    cutoff_m3d     float  -- economic cutoff oil rate, m3/d, that ended the
                              produce phase. If absent, the midpoint of
                              `params["css"]["cutoff_rate_m3d_range"]` is used
                              to run the matching simulated cycle (documented
                              in the fit report's `assumed_cutoff_m3d` field).
    peak_oil_m3d   float  -- peak (first-day) produce-phase oil rate, m3/d.
                              Used as a third residual quantity when present.
    sor            float  -- steam-oil ratio. Not used by `fit()` (it is
                              algebraically implied by steam_t/oil_m3); kept
                              only so a field spreadsheet's own SOR column can
                              be carried into the residual table for a sanity
                              cross-check. Derived as steam_t/oil_m3 if absent.

See `data/templates/observed_cycles_template.csv` for a filled-in example.

What `fit()` does
------------------
Runs `twin.cycle.simulate_css_cycle` at each observed cycle's set-points
(steam_t, soak_days, cutoff_m3d, spm), varying the FREE parameters (default:
`water_cut`, `aof_ref_m3d`, `thickness_m`; `bl_delta_factor` optional) through
`scipy.optimize.least_squares` (bounded, deterministic -- no randomness),
minimising normalised residuals of oil_m3, produce_days (and peak_oil_m3d
when present) between the observed rows and the simulated cycles. Each
residual evaluation is a handful of `simulate_css_cycle` calls (~1-20 ms
each), so a fit over a few dozen cycles is a fast, interactive operation.

Identifiability. With only oil_m3/produce_days per cycle (no downhole
temperature or pressure logs), free parameters can trade off against each
other -- e.g. `aof_ref_m3d` and `thickness_m` both scale how much the heated
zone delivers, so a fit can push one up and the other down and land on a
similar cycle shape. With `bl_delta_factor` fixed at its sourced 0.5,
`water_cut` is identifiable on its own (it sets the produced-heat rate AND
the pump's oil capacity); freeing `bl_delta_factor` as well brings back the
near-degenerate bl / water_cut trade-off. `fit()` reports two identifiability
diagnostics: (1) any fitted value sitting at (or within 1% of) its bound, and
(2) the correlation matrix implied by the Jacobian at the solution (J^T J,
inverted) -- a |correlation| > 0.8 between two parameters means the data
cannot tell them apart on its own.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from twin import cycle, ipr, thermal  # noqa: E402  (see sys.path shim above)

REQUIRED_COLUMNS = ["well_id", "steam_t", "soak_days", "spm", "oil_m3", "produce_days"]
OPTIONAL_COLUMNS = ["cutoff_m3d", "peak_oil_m3d", "sor"]
NUMERIC_COLUMNS = [c for c in REQUIRED_COLUMNS if c != "well_id"] + OPTIONAL_COLUMNS


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Force the numeric schema columns to numeric dtype (errors='coerce').

    `pd.read_csv` already infers these correctly, but a caller building the
    DataFrame another way (e.g. api/main.py's JSON-rows `/calibrate` path,
    where a client may send stringified numbers) can hand back object-dtype
    columns that `fit()`'s arithmetic would otherwise choke on."""
    df = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# 27 Sep 2026: bl_delta_factor removed from the defaults (sourced, fixed at
# 0.5 -- CHANGELOG rev 7). Still accepted in `free` with DEFAULT_BOUNDS below.
DEFAULT_FREE = ("water_cut", "aof_ref_m3d", "thickness_m")
# rev 11: under fluid.water_cut_model = "state" (the shipped default) the
# constant `water_cut` is not read by the physics; the water-cut driver the
# produced-heat term sees is the formation cut (plus the condensate flowback,
# whose recovery fraction is an opt-in free parameter). fit(free=None) picks
# the set that matches the params tree's model (default_free).
DEFAULT_FREE_STATE = ("formation_water_cut", "aof_ref_m3d", "thickness_m")


def default_free(params: dict) -> tuple[str, ...]:
    """The default free set for this params tree's water-cut model (rev 11)."""
    return DEFAULT_FREE_STATE if cycle.water_cut_model(params) == "state" else DEFAULT_FREE

# Bounds are deliberately wide-but-physical, not tight around the current
# defaults: a real recalibration has to be free to move. Sources: bl_delta_factor
# and water_cut spans are the ml/uq.py UQ ranges widened slightly; aof_ref_m3d
# spans the module's own v1->rev5 history (1.0 -> 0.46) plus headroom either
# side; thickness_m spans the TIER1_PROGRESS_LOG.md section 4.6 open item
# (8-20 m reproduces BGW-8 uplift) widened to allow the fit to speak for itself.
DEFAULT_BOUNDS = {
    "bl_delta_factor": (0.35, 1.00),   # opt-in only; the old ml/uq.py span
    "s_cold": (0.0, 8.0),              # rev 10, opt-in only; same span as ml/uq.py
    "water_cut": (0.70, 0.90),         # same span as ml/uq.py's UQ range
    "formation_water_cut": (0.30, 0.60),       # rev 11, [ASSUMPTION] range; ml/uq.py span
    "condensate_recovery_frac": (0.50, 0.90),  # rev 11, opt-in; ml/uq.py span
    "aof_ref_m3d": (0.30, 0.90),       # spans the module's own v1->rev5 history
    "thickness_m": (8.0, 20.0),        # TIER1_PROGRESS_LOG.md 4.6 open item
}

DEFAULT_WEIGHTS = {"oil_m3": 1.0, "produce_days": 1.0, "peak_oil_m3d": 1.0}

# Fraction of a bound's range within which a fitted value is flagged "at bound".
BOUND_TOL_FRAC = 0.01
# |Pearson correlation| (from the Jacobian-implied covariance) above which two
# free parameters are flagged as confounded by this data.
CORRELATION_FLAG_THRESHOLD = 0.8

ML_DIR = _ROOT / "ml"
DEFAULT_PARAMS_PATH = _ROOT / "params" / "field_params.json"
DEFAULT_OUT_PATH = ML_DIR / "models" / "calibrated_params.json"
DEFAULT_REPORT_PATH = ML_DIR / "models" / "calibration_report.json"


def load_observed_csv(path: str | Path) -> pd.DataFrame:
    """Read and schema-check an observed-cycles CSV (see module docstring)."""
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"observed cycles CSV '{path}' is missing required column(s) "
            f"{missing}. Required: {REQUIRED_COLUMNS}. See "
            "data/templates/observed_cycles_template.csv for the schema."
        )
    return coerce_numeric_columns(df)


def _current_value(name: str, params: dict) -> float:
    if name == "bl_delta_factor":
        return thermal.bl_delta_factor(params)
    if name == "water_cut":
        return float(params["fluid"].get("water_cut", cycle.DEFAULT_WATER_CUT))
    if name == "aof_ref_m3d":
        return ipr.aof_ref_m3d(params)
    if name == "formation_water_cut":
        return cycle.formation_water_cut(params)
    if name == "condensate_recovery_frac":
        return cycle.condensate_recovery_frac(params)
    if name == "thickness_m":
        return float(params["reservoir"]["thickness_m"])
    if name == "s_cold":
        return ipr.s_cold(params)
    raise ValueError(f"unknown free parameter '{name}'")


def _write_value(p: dict, name: str, value: float) -> None:
    value = float(value)
    if name == "bl_delta_factor":
        p.setdefault("thermal", {})["bl_delta_factor"] = value
    elif name == "water_cut":
        p["fluid"]["water_cut"] = value
    elif name == "aof_ref_m3d":
        p.setdefault("ipr", {})["aof_ref_m3d"] = value
    elif name == "formation_water_cut":
        p["fluid"]["formation_water_cut"] = value
    elif name == "condensate_recovery_frac":
        p["fluid"]["condensate_recovery_frac"] = value
    elif name == "thickness_m":
        p["reservoir"]["thickness_m"] = value
    elif name == "s_cold":
        p.setdefault("ipr", {})["s_cold"] = value
    else:
        raise ValueError(f"unknown free parameter '{name}'")


def apply(params: dict, fitted: dict[str, float]) -> dict:
    """Deep-copy `params` with `fitted` values written into the right places
    so `simulate_css_cycle` (and everything downstream) uses them."""
    p = copy.deepcopy(params)
    for name, value in fitted.items():
        _write_value(p, name, value)
    return p


def _row_cutoff_m3d(row: pd.Series, params: dict) -> float:
    cutoff = row.get("cutoff_m3d", np.nan)
    if cutoff is None or (isinstance(cutoff, float) and np.isnan(cutoff)):
        lo, hi = params["css"]["cutoff_rate_m3d_range"]
        return (lo + hi) / 2.0
    return float(cutoff)


def _simulate_row(row: pd.Series, params: dict) -> dict:
    cutoff = _row_cutoff_m3d(row, params)
    df = cycle.simulate_css_cycle(
        steam_t=float(row["steam_t"]),
        soak_days=float(row["soak_days"]),
        cutoff_m3d=cutoff,
        spm=float(row["spm"]),
        params=params,
    )
    s = cycle.summary(df, params)
    s["_assumed_cutoff_m3d"] = cutoff
    return s


def _has_value(row: pd.Series, col: str) -> bool:
    if col not in row.index:
        return False
    v = row[col]
    return not (v is None or (isinstance(v, float) and np.isnan(v)))


def fit(
    observed_df: pd.DataFrame,
    params: dict,
    free: Sequence[str] | None = None,
    bounds: dict[str, tuple[float, float]] | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Least-squares calibration of `free` parameters against `observed_df`.

    Returns a dict:
        fitted_params: {name: value} for each name in `free`.
        bounds: {name: (lo, hi)} bounds actually used.
        initial_values: {name: value} the params tree's own value before fitting.
        residual_table: list of per-cycle dicts (well_id, set-points, obs vs
            sim for oil_m3/produce_days/peak_oil_m3d/sor).
        rmse: {"oil_m3": ..., "produce_days": ..., "peak_oil_m3d": ...} --
            root-mean-square of the RELATIVE (%) residual, over the rows
            where that quantity is available.
        identifiability: {"at_bound": [...], "correlated_pairs": [...],
            "correlation_matrix": [[...]] or None, "free_params": [...]}.
        n_cycles: number of observed cycles used.
        free_params: list(free), the order the above arrays follow.

    Raises ValueError if `observed_df` has fewer than 2 rows -- a single cycle
    cannot identify more than one free parameter (only 2-3 residuals per row
    for 3-4 unknowns), so this is a degenerate input, not merely a
    poorly-conditioned one.
    """
    free = tuple(free) if free is not None else default_free(params)
    if len(observed_df) < 2:
        raise ValueError(
            f"twin.calibrate.fit needs at least 2 observed cycles to fit "
            f"{len(free)} free parameter(s) {free}; got {len(observed_df)} "
            "row(s). This is a degenerate (underdetermined) input, not just "
            "a poorly-conditioned one -- provide more cycles or reduce `free`."
        )

    bounds = bounds or DEFAULT_BOUNDS
    for name in free:
        if name not in bounds:
            raise ValueError(f"no bounds given for free parameter '{name}'")
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    x0 = np.array([_current_value(name, params) for name in free], dtype=float)
    lb = np.array([bounds[name][0] for name in free], dtype=float)
    ub = np.array([bounds[name][1] for name in free], dtype=float)
    # least_squares requires lb < x0 < ub strictly; nudge a starting value
    # that sits exactly on a bound (shouldn't happen with the defaults above,
    # but a caller could pass a params tree whose value already sits there).
    x0 = np.clip(x0, lb + 1e-9, ub - 1e-9)

    rows = list(observed_df.itertuples(index=False, name=None))
    columns = list(observed_df.columns)

    def _residuals(x: np.ndarray) -> np.ndarray:
        p = copy.deepcopy(params)
        for name, value in zip(free, x):
            _write_value(p, name, value)
        out = []
        for row_tuple in rows:
            row = pd.Series(row_tuple, index=columns)
            sim = _simulate_row(row, p)
            obs_oil = float(row["oil_m3"])
            out.append(weights["oil_m3"] * (sim["oil_total_m3"] - obs_oil) / max(abs(obs_oil), 1e-6))
            obs_days = float(row["produce_days"])
            out.append(weights["produce_days"] * (sim["days_total"] - obs_days) / max(abs(obs_days), 1e-6))
            if _has_value(row, "peak_oil_m3d"):
                obs_peak = float(row["peak_oil_m3d"])
                out.append(
                    weights["peak_oil_m3d"] * (sim["peak_oil_m3d"] - obs_peak) / max(abs(obs_peak), 1e-6)
                )
        return np.array(out, dtype=float)

    result = least_squares(_residuals, x0=x0, bounds=(lb, ub), method="trf")
    fitted_params = {name: float(v) for name, v in zip(free, result.x)}

    # --- residual table (built once, at the fitted point) --------------------
    p_fit = apply(params, fitted_params)
    residual_table = []
    oil_pct_errs, days_pct_errs, peak_pct_errs = [], [], []
    for row_tuple in rows:
        row = pd.Series(row_tuple, index=columns)
        sim = _simulate_row(row, p_fit)
        obs_oil = float(row["oil_m3"])
        obs_days = float(row["produce_days"])
        entry: dict[str, Any] = {
            "well_id": row.get("well_id"),
            "steam_t": float(row["steam_t"]),
            "soak_days": float(row["soak_days"]),
            "cutoff_m3d_assumed": sim["_assumed_cutoff_m3d"],
            "spm": float(row["spm"]),
            "obs_oil_m3": obs_oil,
            "sim_oil_m3": sim["oil_total_m3"],
            "oil_m3_pct_error": 100.0 * (sim["oil_total_m3"] - obs_oil) / max(abs(obs_oil), 1e-6),
            "obs_produce_days": obs_days,
            "sim_produce_days": sim["days_total"],
            "produce_days_pct_error": 100.0 * (sim["days_total"] - obs_days) / max(abs(obs_days), 1e-6),
        }
        oil_pct_errs.append(entry["oil_m3_pct_error"])
        days_pct_errs.append(entry["produce_days_pct_error"])
        if _has_value(row, "peak_oil_m3d"):
            obs_peak = float(row["peak_oil_m3d"])
            entry["obs_peak_oil_m3d"] = obs_peak
            entry["sim_peak_oil_m3d"] = sim["peak_oil_m3d"]
            entry["peak_oil_m3d_pct_error"] = 100.0 * (sim["peak_oil_m3d"] - obs_peak) / max(abs(obs_peak), 1e-6)
            peak_pct_errs.append(entry["peak_oil_m3d_pct_error"])
        obs_sor = float(row["sor"]) if _has_value(row, "sor") else float(row["steam_t"]) / obs_oil
        entry["obs_sor"] = obs_sor
        entry["sim_sor"] = sim["SOR_t_per_m3"]
        residual_table.append(entry)

    def _rmse(errs: list[float]) -> float | None:
        if not errs:
            return None
        return float(np.sqrt(np.mean(np.square(errs))))

    rmse = {
        "oil_m3_pct": _rmse(oil_pct_errs),
        "produce_days_pct": _rmse(days_pct_errs),
        "peak_oil_m3d_pct": _rmse(peak_pct_errs),
    }

    # --- identifiability ------------------------------------------------------
    at_bound = []
    for name, value in fitted_params.items():
        lo, hi = bounds[name]
        width = hi - lo
        if width > 0:
            if (value - lo) <= BOUND_TOL_FRAC * width:
                at_bound.append({"param": name, "bound": "lower", "value": value})
            elif (hi - value) <= BOUND_TOL_FRAC * width:
                at_bound.append({"param": name, "bound": "upper", "value": value})

    correlation_matrix = None
    correlated_pairs = []
    jac = getattr(result, "jac", None)
    if jac is not None and jac.shape[0] >= jac.shape[1]:
        jtj = jac.T @ jac
        try:
            cov = np.linalg.inv(jtj)
            sd = np.sqrt(np.diag(cov))
            if np.all(sd > 0) and np.all(np.isfinite(sd)):
                corr = cov / np.outer(sd, sd)
                correlation_matrix = corr.tolist()
                for i in range(len(free)):
                    for j in range(i + 1, len(free)):
                        r = float(corr[i, j])
                        if abs(r) >= CORRELATION_FLAG_THRESHOLD:
                            correlated_pairs.append({"params": [free[i], free[j]], "correlation": r})
        except np.linalg.LinAlgError:
            pass

    # Known structural coupling (only when bl_delta_factor is opted in):
    # twin.thermal's Boberg-Lantz `delta` scales as bl_delta_factor x the
    # produced heat, and most of that heat is the hot water, whose rate is
    # oil x water_cut / (1 - water_cut). The two therefore trade off almost
    # one-for-one on oil_m3/produce_days data. Since physics v3 the coupling
    # is no longer an exact ratio (oil and water heat are separate streams,
    # PEH Eq. 15.74, and water_cut also sets the pump's oil capacity), but it
    # is still strong, so report the combination when both are free.
    known_couplings = []
    if "bl_delta_factor" in fitted_params and "water_cut" in fitted_params:
        denom = max(1.0 - fitted_params["water_cut"], 1e-9)
        known_couplings.append({
            "combination": "bl_delta_factor / (1 - water_cut)",
            "value": fitted_params["bl_delta_factor"] / denom,
            "reason": (
                "twin.thermal.steam_zone_temperature's Boberg-Lantz energy-"
                "removed term delta is bl_delta_factor * Q_removed / "
                "Q_retained, and Q_removed is dominated by the hot water, "
                "whose rate is oil_m3d * water_cut / (1 - water_cut). The two "
                "trade off almost one-for-one on oil_m3/produce_days data. "
                "bl_delta_factor is sourced (0.5) and off by default for this "
                "reason; free it only to test a hypothesis."
            ),
        })

    identifiability = {
        "free_params": list(free),
        "at_bound": at_bound,
        "correlated_pairs": correlated_pairs,
        "correlation_matrix": correlation_matrix,
        "known_couplings": known_couplings,
        "note": (
            "With only oil_m3/produce_days per cycle (no downhole temperature "
            "or pressure log), parameters that act through the same physical "
            "channel (e.g. aof_ref_m3d and thickness_m both scale what the "
            "heated zone delivers) can trade off against each other. 'correlated_pairs' lists any pair "
            "with |correlation| >= "
            f"{CORRELATION_FLAG_THRESHOLD} in the Jacobian-implied covariance "
            "at the solution; 'at_bound' lists any fitted value the data "
            "pushed to (or within 1% of) its bound, which means the data "
            "wants to go further than the bound allows and the value is not "
            "really identified by this dataset."
        ),
    }

    return {
        "fitted_params": fitted_params,
        "bounds": {name: list(bounds[name]) for name in free},
        "initial_values": {name: float(v) for name, v in zip(free, x0)},
        "residual_table": residual_table,
        "rmse": rmse,
        "identifiability": identifiability,
        "n_cycles": len(observed_df),
        "free_params": list(free),
        "success": bool(result.success),
        "cost": float(result.cost),
    }


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and np.isnan(obj):
        return None
    return obj


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("observed_csv", help="Path to an observed-cycles CSV (see module docstring for schema)")
    ap.add_argument("--params", default=str(DEFAULT_PARAMS_PATH), help="Path to field_params.json")
    ap.add_argument("--out", default=str(DEFAULT_OUT_PATH), help="Where to write the calibrated params JSON")
    ap.add_argument("--report", default=str(DEFAULT_REPORT_PATH), help="Where to write the calibration report JSON")
    ap.add_argument("--free", nargs="+", default=None,
                    help="Free parameter names to fit (default: calibrate.default_free(params))")
    args = ap.parse_args(argv)

    with open(args.params, encoding="utf-8") as f:
        params = json.load(f)
    observed_df = load_observed_csv(args.observed_csv)
    result = fit(observed_df, params, free=tuple(args.free) if args.free else None)
    calibrated_params = apply(params, result["fitted_params"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(calibrated_params, f, indent=2)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(_to_jsonable(result), f, indent=2)

    print(json.dumps(_to_jsonable(result), indent=2))
    print(f"\nWrote calibrated params to {out_path}")
    print(f"Wrote calibration report to {report_path}")


if __name__ == "__main__":
    main()
