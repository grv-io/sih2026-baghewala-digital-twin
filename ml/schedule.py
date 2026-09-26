"""ml/schedule.py -- field-level steam scheduling across many wells under a
SINGLE generator constraint (PS SIH26120's actual field-level ask: which well
gets steam next, how much, and when, to maximise field incremental margin per
day, given ~33 operational Baghewala wells sharing one ~74 t/d (3.1 t/h)
steam generator -- see docs/research/baghewala_facts.md section 4/5 and
README.md Status for the "one generator is the bottleneck" framing).

This module sits ONE LEVEL ABOVE `ml/recommend_physics.py`: that module finds
the physics-optimal steam_t/cutoff_m3d/spm for ONE well in isolation. Here we
(1) run that per-well optimum for every well in the field (reusing
`recommend_physics.best_settings_physics` unmodified), turning each well into
one fixed candidate "job" -- a total steam volume, a total incremental ₹, and
a generator-occupancy duration -- then (2) solve the separate combinatorial
problem of ORDERING those jobs on the one shared generator within a finite
horizon, subject to a per-well re-cycle gate (>=180 days since the well's
last cycle) and the horizon deadline.

Three schedules are produced, in increasing sophistication:
  * naive       -- the counterfactual an operator with no optimizer might
                   run: steam every well the SAME fixed 1,500 t (roughly the
                   field's own recent per-job scale), same soak/cutoff/spm,
                   visited in ascending current-cold-rate order (worst
                   producers first) -- no per-well tuning, no generator-time
                   awareness beyond "go until it doesn't fit".
  * greedy      -- per-well PHYSICS-OPTIMAL settings (recommend_physics),
                   jobs inserted in descending value-per-generator-day order.
                   A fast, non-exact heuristic.
  * exact       -- per-well physics-optimal settings, but the SUBSET and
                   ORDER of jobs on the generator is chosen by exhaustive
                   bitmask search over all 2^n_wells subsets (n_wells=12 here
                   -> 4,096 subsets, each evaluated in O(n) -- microseconds
                   total, no MILP solver needed). For a FIXED subset, the
                   feasibility-optimal order is "sort by earliest eligible
                   start day" (Earliest-Release-Date, ERD): this is the
                   textbook-optimal rule for 1|r_j|C_max -- minimising a
                   single machine's makespan under per-job release dates
                   with no preemption (any other order can only tie or
                   increase the completion time of the last job, by a
                   standard adjacent-swap exchange argument) -- so bitmask
                   x ERD-per-subset is a PROVABLY OPTIMAL search over
                   (subset, order) jointly, not just a good heuristic.
                   pulp/OR-Tools are not installed in this environment; this
                   avoids needing either.

All three report the same KPIs (field ₹ total/day, generator utilisation %,
steam/CO2 totals, wells served/deferred + why) so they are directly
comparable. Deterministic (seed 42 everywhere data is synthesised); runtime
budget: ~12 wells x a REDUCED physics grid (144 pts/well vs
recommend_physics's own 1,575-pt default) keeps the whole CLI run under the
required 60 s (empirically ~25 s on this machine; see module docstring of
`recommend_physics.py` for the ~8 ms/cycle base rate this is scaled from).

CLI:
    python -m ml.schedule --make-wells                         # (re)generate
        data/external/field_wells_synthetic.csv (seed 42, 12 synthetic wells)
    python -m ml.schedule --wells data/external/field_wells_synthetic.csv \\
        --out ml/models/field_schedule_demo.json                # full run
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ml import optimize as ml_optimize  # noqa: E402
from ml import recommend_physics as rp  # noqa: E402
from twin import cycle  # noqa: E402
from twin import ipr  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_PARAMS_PATH = ml_optimize.DEFAULT_PARAMS_PATH
DEFAULT_WELLS_CSV = _ROOT / "data" / "external" / "field_wells_synthetic.csv"
DEFAULT_OUT_PATH = _ROOT / "ml" / "models" / "field_schedule_demo.json"

# The field's ONE steam generator: ~3.1 t/h ~= 74.4 t/d, rounded to the same
# 74.0 t/d already used as `steam.injection_rate_tpd` in field_params.json --
# this is deliberately the SAME number, not a second sourced constant: the
# per-well twin already assumes the field's one generator feeds it at this
# rate, so the scheduler treats "generator occupied" as exactly the well's
# own injection duration.
GENERATOR_RATE_TPD = 74.0
MOVE_DAYS = 1.0                 # hose/rig-up move time between wells [ASSUMPTION]
MIN_RECYCLE_DAYS = 180.0        # re-cycle gate: task brief, "cycles 6-18 months apart"
HORIZON_DAYS = 365.0
SOAK_DAYS_FIXED = 10.0          # held fixed field-wide, matching recommend_physics
SEARCH_GRID = {"steam_t": 6, "cutoff_m3d": 6, "spm": 4}  # 144 pts/well (reduced from 1,575)
N_WELLS = 12
SEED = 42
START_DATE = date(2026, 10, 1)  # horizon start, for calendar-date display only

NAIVE_STEAM_T = 1500.0          # "steam every well the same" counterfactual
NAIVE_SPM = 5.0                 # published-practice mid-band value

WELL_RANGES = {
    "thickness_m": (8.0, 20.0),
    "mu_ref_cP": (8000.0, 15000.0),
    "aof_mult": (0.7, 1.3),          # +-30% skin/AOF variation around AOF_REF_M3D
    "water_cut": (0.7, 0.9),
    "days_since_last_cycle": (30.0, 400.0),
    "last_cycle_sor": (3.0, 8.0),    # descriptive only (literature CSS SOR band)
}


# ---------------------------------------------------------------------------
# Params I/O + per-well params tree
# ---------------------------------------------------------------------------
def _load_params(path: str | Path = DEFAULT_PARAMS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_well_params(base_params: dict, well_row: dict) -> dict:
    """A per-well params tree: base_params with this well's
    thickness_m/mu_ref_cP/water_cut/aof_ref_m3d overridden. Everything else
    (steam quality, generator rate, economics, srp geometry) is field-wide
    and shared, matching the brief ("one steam generator... cycles per
    well").

    rev 13 (wave 5): every well is operated VFD-hold (`css.float_policy`) --
    the recommended policy (TIER1_PROGRESS_LOG.md section 12.2/12.5), rather
    than the params default "pull" (the rev-12 pull-rule operation the
    external re-score found erases most of the headline gain, section 12.1).
    `rp.best_settings_physics` (the per-well grid this module calls) reads
    float_policy only from the params tree, not from a settings kwarg, so it
    is set here rather than passed through a settings dict."""
    p = copy.deepcopy(base_params)
    if "thickness_m" in well_row and well_row["thickness_m"] is not None:
        p["reservoir"]["thickness_m"] = float(well_row["thickness_m"])
    if "mu_ref_cP" in well_row and well_row["mu_ref_cP"] is not None:
        p["fluid"]["mu_ref_cP"] = float(well_row["mu_ref_cP"])
    if "water_cut" in well_row and well_row["water_cut"] is not None:
        p["fluid"]["water_cut"] = float(well_row["water_cut"])
    if "aof_mult" in well_row and well_row["aof_mult"] is not None:
        p.setdefault("ipr", {})
        p["ipr"]["aof_ref_m3d"] = float(ipr.AOF_REF_M3D) * float(well_row["aof_mult"])
    p.setdefault("css", {})["float_policy"] = "vfd_hold"
    return p


# ---------------------------------------------------------------------------
# 1. Synthetic field data
# ---------------------------------------------------------------------------
def make_synthetic_wells(n: int = N_WELLS, seed: int = SEED, base_params: dict | None = None) -> pd.DataFrame:
    """12 synthetic wells BGW-S01..BGW-S12 -- SYNTHETIC, seed 42, no real
    Baghewala well data (see data/external/SOURCE.md)."""
    rng = np.random.default_rng(seed)
    base_params = base_params if base_params is not None else _load_params()
    rows = []
    for i in range(n):
        well_row = {
            "well_id": f"BGW-S{i + 1:02d}",
            "thickness_m": float(rng.uniform(*WELL_RANGES["thickness_m"])),
            "mu_ref_cP": float(rng.uniform(*WELL_RANGES["mu_ref_cP"])),
            "aof_mult": float(rng.uniform(*WELL_RANGES["aof_mult"])),
            "water_cut": float(rng.uniform(*WELL_RANGES["water_cut"])),
            "days_since_last_cycle": float(rng.uniform(*WELL_RANGES["days_since_last_cycle"])),
            "last_cycle_sor": float(rng.uniform(*WELL_RANGES["last_cycle_sor"])),
        }
        well_params = build_well_params(base_params, well_row)
        cold = cycle.cold_baseline(well_params)
        well_row["current_cold_rate_m3d"] = float(cold["oil_m3d"])
        rows.append({k: (round(v, 3) if isinstance(v, float) else v) for k, v in well_row.items()})
    return pd.DataFrame(rows)


SOURCE_MD = """# data/external/ -- source note

`field_wells_synthetic.csv` is **SYNTHETIC**. It contains NO real Baghewala
well data. It was generated by `ml.schedule.make_synthetic_wells()`
(`python -m ml.schedule --make-wells`), `numpy.random.default_rng(seed=42)`,
deterministic and reproducible.

12 wells (`BGW-S01`..`BGW-S12`), each an independent draw of:

| column | range | meaning |
|---|---|---|
| `thickness_m` | 8-20 m | net pay thickness override (`reservoir.thickness_m`) |
| `mu_ref_cP` | 8,000-15,000 cP | reference oil viscosity override (`fluid.mu_ref_cP`) -- the field's own published band (docs/research/baghewala_facts.md) |
| `aof_mult` | 0.7-1.3 | +-30% multiplier on `ipr.AOF_REF_M3D` (0.46), standing in for well-to-well skin/AOF variation |
| `water_cut` | 0.7-0.9 | fluid water cut override (`fluid.water_cut`) |
| `current_cold_rate_m3d` | derived | `twin.cycle.cold_baseline()` at this well's params -- NOT randomly drawn, computed from the physics so it stays internally consistent |
| `days_since_last_cycle` | 30-400 d | synthetic "well state at schedule day 0"; gates the >=180-day re-cycle rule |
| `last_cycle_sor` | 3-8 | descriptive only (literature CSS SOR band); not used by the scheduler |

Every other field parameter (steam quality, generator rate, srp geometry,
economics) is shared field-wide from `params/field_params.json` -- only the
six per-well columns above vary. Used by `ml/schedule.py` to demonstrate a
field-level, generator-constrained scheduler on top of the per-well twin;
see `ml/README.md` section "Field-level steam scheduling".
"""


# ---------------------------------------------------------------------------
# 2. Per-well candidate jobs
# ---------------------------------------------------------------------------
def _earliest_start_day(days_since_last_cycle: float) -> float:
    return max(0.0, MIN_RECYCLE_DAYS - float(days_since_last_cycle))


def well_candidate_job(well_row: dict, base_params: dict, grid: dict | None = None,
                        soak_days: float = SOAK_DAYS_FIXED) -> dict:
    """The physics-optimal candidate job for one well: reuses
    `recommend_physics.best_settings_physics` (FI <= 0.6 feasibility, soak
    fixed) unmodified, then packages the result as a fixed generator job."""
    well_params = build_well_params(base_params, well_row)
    res = rp.best_settings_physics(well_params, fixed={"soak_days": soak_days}, grid=grid or SEARCH_GRID)
    return _job_from_physics(
        well_id=well_row["well_id"],
        settings=res["best_settings"],
        phys=res["physics_verified_optimum"],
        days_since_last_cycle=well_row["days_since_last_cycle"],
        feasible=res["feasible_point_found"],
    )


def naive_candidate_job(well_row: dict, base_params: dict, soak_days: float = SOAK_DAYS_FIXED) -> dict:
    """The counterfactual: same 1,500 t / same soak / same spm for every
    well, cutoff at the well's own range midpoint (no published cutoff
    number exists to hold fixed instead) -- NO per-well optimisation."""
    well_params = build_well_params(base_params, well_row)
    ranges = ml_optimize._ranges_from_params(well_params)
    cutoff_m3d = (ranges["cutoff_m3d"][0] + ranges["cutoff_m3d"][1]) / 2.0
    settings = {"steam_t": NAIVE_STEAM_T, "soak_days": soak_days, "cutoff_m3d": cutoff_m3d, "spm": NAIVE_SPM}
    phys = ml_optimize._physics_verify(settings, well_params)
    return _job_from_physics(
        well_id=well_row["well_id"], settings=settings, phys=phys,
        days_since_last_cycle=well_row["days_since_last_cycle"], feasible=None,
    )


def _job_from_physics(well_id: str, settings: dict, phys: dict, days_since_last_cycle: float,
                       feasible: bool | None) -> dict:
    steam_t = float(settings["steam_t"])
    steam_days = steam_t / GENERATOR_RATE_TPD
    duration_days = steam_days + MOVE_DAYS
    cycle_days = float(phys["days_total"])
    margin_per_cycle_day = float(phys["margin_incremental_inr_per_cycle_day"])
    margin_total_inr = margin_per_cycle_day * cycle_days
    return {
        "well_id": well_id,
        "steam_t": steam_t,
        "cutoff_m3d": float(settings["cutoff_m3d"]),
        "spm": float(settings["spm"]),
        "soak_days": float(settings["soak_days"]),
        "steam_days": steam_days,
        "move_days": MOVE_DAYS,
        "duration_days": duration_days,
        "cycle_days": cycle_days,
        "margin_incremental_inr_per_cycle_day": margin_per_cycle_day,
        "margin_incremental_inr_total": margin_total_inr,
        "co2_t": float(phys["co2_t"]),
        "max_floating_index": float(phys["max_floating_index"]),
        "feasible_point_found": feasible,
        "earliest_start_day": _earliest_start_day(days_since_last_cycle),
        "value_per_generator_day": margin_total_inr / duration_days if duration_days > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# 3. Scheduling: greedy, exact (bitmask + ERD), naive fixed-order
# ---------------------------------------------------------------------------
def _place_in_order(jobs_in_order: list[dict], horizon: float = HORIZON_DAYS) -> list[dict]:
    """Place jobs one at a time in the given order: each starts at
    max(generator-free-time, its own earliest_start_day); a job that would
    finish past the horizon is SKIPPED (left unscheduled/deferred), and the
    next job in the order is still tried in the gap. Used by both the greedy
    heuristic (order = value density) and the naive policy (order = cold
    rate)."""
    free_at = 0.0
    scheduled = []
    for job in jobs_in_order:
        start = max(free_at, job["earliest_start_day"])
        end = start + job["duration_days"]
        if end > horizon + 1e-9:
            continue
        j = dict(job)
        j["start_day"] = start
        j["end_day"] = end
        scheduled.append(j)
        free_at = end
    return scheduled


def _evaluate_subset_erd(subset: list[dict], horizon: float = HORIZON_DAYS) -> tuple[list[dict], float] | None:
    """Feasibility + value of scheduling EVERY job in `subset` (none may be
    dropped), in Earliest-Release-Date order -- the makespan-optimal order
    for 1|r_j|C_max. Returns None if the subset cannot all fit in the
    horizon in ANY order (ERD being optimal, if ERD fails, no order
    succeeds)."""
    ordered = sorted(subset, key=lambda j: j["earliest_start_day"])
    free_at = 0.0
    scheduled = []
    for job in ordered:
        start = max(free_at, job["earliest_start_day"])
        end = start + job["duration_days"]
        if end > horizon + 1e-9:
            return None
        j = dict(job)
        j["start_day"] = start
        j["end_day"] = end
        scheduled.append(j)
        free_at = end
    total_value = sum(j["margin_incremental_inr_total"] for j in scheduled)
    return scheduled, total_value


def schedule_exact(jobs: list[dict], horizon: float = HORIZON_DAYS) -> dict:
    """Exhaustive bitmask search over all 2^n subsets of `jobs` (n<=12 here
    -> 4,096 subsets); each subset's value is its ERD-ordered feasible
    placement (see `_evaluate_subset_erd`). Provably optimal: every possible
    subset is tried, and for each, the makespan-minimal order is used, so no
    (subset, order) pair beats the returned one."""
    n = len(jobs)
    best_value = 0.0
    best_scheduled: list[dict] = []
    for mask in range(1, 1 << n):
        subset = [jobs[i] for i in range(n) if mask & (1 << i)]
        result = _evaluate_subset_erd(subset, horizon)
        if result is None:
            continue
        scheduled, value = result
        if value > best_value:
            best_value = value
            best_scheduled = scheduled
    return _finalize_schedule(
        best_scheduled, jobs, horizon,
        method="exact_bitmask_subset_search (2^n subsets x ERD-optimal per-subset order)",
    )


def schedule_greedy(jobs: list[dict], horizon: float = HORIZON_DAYS) -> dict:
    """Heuristic: visit jobs in descending value-per-generator-day order,
    placing each as early as the generator and the well's own re-cycle gate
    allow. Fast, NOT guaranteed optimal (unlike `schedule_exact`)."""
    ordered = sorted(jobs, key=lambda j: j["value_per_generator_day"], reverse=True)
    scheduled = _place_in_order(ordered, horizon)
    return _finalize_schedule(scheduled, jobs, horizon, method="greedy_value_density (desc Rs/generator-day)")


def schedule_naive(jobs: list[dict], wells_df: pd.DataFrame, horizon: float = HORIZON_DAYS) -> dict:
    """The counterfactual: same fixed 1,500 t job for every well (see
    `naive_candidate_job`), visited in ascending current-cold-rate order
    (worst producers steamed first) -- no per-well tuning, no
    value-density awareness."""
    order_ids = list(wells_df.sort_values("current_cold_rate_m3d")["well_id"])
    by_id = {j["well_id"]: j for j in jobs}
    ordered = [by_id[w] for w in order_ids if w in by_id]
    scheduled = _place_in_order(ordered, horizon)
    return _finalize_schedule(scheduled, jobs, horizon, method="naive_fixed_1500t_cold_rate_order (counterfactual)")


def _deferred_reason(job: dict, horizon: float) -> str:
    if job["earliest_start_day"] + job["duration_days"] > horizon + 1e-9:
        return (
            f"cannot fit even alone: {MIN_RECYCLE_DAYS:.0f}-day re-cycle gate "
            f"(eligible day {job['earliest_start_day']:.0f}) + {job['duration_days']:.1f} d "
            f"generator time exceeds the {horizon:.0f}-day horizon"
        )
    return "generator time committed to higher-value jobs ahead of it in this schedule"


def _finalize_schedule(scheduled: list[dict], all_jobs: list[dict], horizon: float, method: str) -> dict:
    scheduled_sorted = sorted(scheduled, key=lambda j: j["start_day"])
    served_ids = {j["well_id"] for j in scheduled_sorted}
    jobs_out = []
    for order, j in enumerate(scheduled_sorted, start=1):
        start_date = START_DATE + timedelta(days=j["start_day"])
        end_date = START_DATE + timedelta(days=j["end_day"])
        jobs_out.append({
            "order": order, "well_id": j["well_id"],
            "start_day": round(j["start_day"], 1), "end_day": round(j["end_day"], 1),
            "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
            "steam_t": round(j["steam_t"], 1), "cutoff_m3d": round(j["cutoff_m3d"], 3),
            "spm": round(j["spm"], 2), "soak_days": j["soak_days"],
            "cycle_days": round(j["cycle_days"], 1), "steam_days": round(j["steam_days"], 2),
            "margin_incremental_inr_per_cycle_day": round(j["margin_incremental_inr_per_cycle_day"], 1),
            "margin_incremental_inr_total": round(j["margin_incremental_inr_total"], 0),
            "co2_t": round(j["co2_t"], 2),
        })
    generator_days_used = sum(j["duration_days"] for j in scheduled_sorted)
    field_margin_total = sum(j["margin_incremental_inr_total"] for j in scheduled_sorted)
    deferred = [
        {"well_id": j["well_id"], "reason": _deferred_reason(j, horizon)}
        for j in all_jobs if j["well_id"] not in served_ids
    ]
    return {
        "method": method,
        "horizon_days": horizon,
        "jobs": jobs_out,
        "generator_utilisation_pct": round(100.0 * generator_days_used / horizon, 1) if horizon > 0 else 0.0,
        "generator_days_used": round(generator_days_used, 1),
        "field_margin_inr_total": round(field_margin_total, 0),
        "field_margin_inr_per_day": round(field_margin_total / horizon, 1) if horizon > 0 else 0.0,
        "steam_t_total": round(sum(j["steam_t"] for j in scheduled_sorted), 1),
        "co2_t_total": round(sum(j["co2_t"] for j in scheduled_sorted), 1),
        "n_wells_total": len(all_jobs),
        "n_wells_served": len(scheduled_sorted),
        "n_wells_deferred": len(deferred),
        "wells_served": sorted(served_ids),
        "wells_deferred": deferred,
    }


# ---------------------------------------------------------------------------
# 4. Top-level build
# ---------------------------------------------------------------------------
def build_schedule(wells_df: pd.DataFrame, base_params: dict | None = None, grid: dict | None = None,
                    horizon: float = HORIZON_DAYS) -> dict:
    """Runs the per-well physics optimum for every well, then all three
    schedules (naive, greedy, exact), and returns one combined result dict --
    the shape written to `ml/models/field_schedule_demo.json` and served by
    `GET /api/schedule/demo`."""
    base_params = base_params if base_params is not None else _load_params()
    if "current_cold_rate_m3d" not in wells_df.columns:
        # API callers may not supply this (it's derived, not a free input) --
        # compute it from each well's own params so schedule_naive's
        # cold-rate ordering always has something to sort by.
        wells_df = wells_df.copy()
        wells_df["current_cold_rate_m3d"] = [
            cycle.cold_baseline(build_well_params(base_params, w))["oil_m3d"]
            for w in wells_df.to_dict(orient="records")
        ]
    wells = wells_df.to_dict(orient="records")

    optimized_jobs = [well_candidate_job(w, base_params, grid=grid) for w in wells]
    naive_jobs = [naive_candidate_job(w, base_params) for w in wells]

    exact = schedule_exact(optimized_jobs, horizon)
    greedy = schedule_greedy(optimized_jobs, horizon)
    naive = schedule_naive(naive_jobs, wells_df, horizon)

    def _gain(a: dict, b: dict) -> dict:
        return {
            "margin_inr_total_delta": a["field_margin_inr_total"] - b["field_margin_inr_total"],
            "margin_inr_per_day_delta": a["field_margin_inr_per_day"] - b["field_margin_inr_per_day"],
            "pct_gain": (
                None if abs(b["field_margin_inr_total"]) < 1e-6 else
                round(100.0 * (a["field_margin_inr_total"] - b["field_margin_inr_total"])
                      / abs(b["field_margin_inr_total"]), 1)
            ),
        }

    return {
        "generated_at": date.today().isoformat(),
        "seed": SEED,
        "n_wells": len(wells),
        "generator_rate_tpd": GENERATOR_RATE_TPD,
        "move_days": MOVE_DAYS,
        "min_recycle_days": MIN_RECYCLE_DAYS,
        "horizon_days": horizon,
        "search_grid": grid or SEARCH_GRID,
        "candidate_jobs": [
            {
                "well_id": j["well_id"], "steam_t": round(j["steam_t"], 1),
                "cutoff_m3d": round(j["cutoff_m3d"], 3), "spm": round(j["spm"], 2),
                "cycle_days": round(j["cycle_days"], 1), "steam_days": round(j["steam_days"], 2),
                "margin_incremental_inr_per_cycle_day": round(j["margin_incremental_inr_per_cycle_day"], 1),
                "earliest_start_day": round(j["earliest_start_day"], 1),
                "feasible_point_found": j["feasible_point_found"],
            }
            for j in optimized_jobs
        ],
        "exact": exact,
        "greedy": greedy,
        "naive": naive,
        "comparison": {
            "exact_vs_naive": _gain(exact, naive),
            "greedy_vs_naive": _gain(greedy, naive),
            "exact_vs_greedy": _gain(exact, greedy),
        },
        "assumptions": [
            "rev 13: every well is operated VFD-hold (css.float_policy), the recommended policy "
            "(TIER1_PROGRESS_LOG.md section 12.2/12.5) -- not the params default 'pull'.",
            "12 wells are SYNTHETIC (data/external/SOURCE.md); no real Baghewala per-well data used.",
            f"Single shared generator at {GENERATOR_RATE_TPD:.0f} t/d; jobs occupy it sequentially "
            f"for steam_t/{GENERATOR_RATE_TPD:.0f} days plus a {MOVE_DAYS:.0f}-day move -- no parallel injection.",
            f"A well is eligible to start a new cycle only >= {MIN_RECYCLE_DAYS:.0f} days after its last cycle.",
            "Interference between wells (pressure communication, shared facilities beyond the "
            "generator) is NOT modelled -- each well's physics is independent.",
            "soak_days held fixed at 10 (field practice), matching recommend_physics.py; not searched.",
            f"Per-well search grid reduced to {SEARCH_GRID} (144 pts) from recommend_physics's own "
            "1,575-pt default, to keep the 12-well run inside the 60 s CLI budget.",
        ],
    }


# ---------------------------------------------------------------------------
# 5. CLI
# ---------------------------------------------------------------------------
def _to_native(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--wells", default=str(DEFAULT_WELLS_CSV), help="Path to the field wells CSV.")
    parser.add_argument("--out", default=None, help="Write the schedule JSON here (default: stdout).")
    parser.add_argument("--params", default=str(DEFAULT_PARAMS_PATH))
    parser.add_argument("--make-wells", action="store_true",
                         help="(Re)generate the synthetic wells CSV at --wells and exit.")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    params = _load_params(args.params)

    if args.make_wells:
        wells_path = Path(args.wells)
        wells_path.parent.mkdir(parents=True, exist_ok=True)
        df = make_synthetic_wells(seed=args.seed, base_params=params)
        df.to_csv(wells_path, index=False)
        source_path = wells_path.parent / "SOURCE.md"
        if not source_path.exists():
            source_path.write_text(SOURCE_MD, encoding="utf-8")
        print(f"wrote {len(df)} synthetic wells to {wells_path}")
        return

    wells_df = pd.read_csv(args.wells)
    result = build_schedule(wells_df, params)
    payload = json.dumps(_to_native(result), indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(f"wrote schedule to {out_path}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
