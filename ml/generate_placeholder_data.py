"""Generate data/placeholder_cycles.csv — FAKE data for pipeline testing ONLY.

*** THIS IS NOT THE REAL DIGITAL TWIN OUTPUT. ***
The physics package `twin/` (thermal.py, viscosity.py, ipr.py, srp.py, cycle.py,
generate_data.py) is being built in parallel by another agent. Until
`twin/generate_data.py` exists and produces `data/synthetic_cycles.csv`, ml/train.py
and ml/optimize.py have nothing real to train/optimize against. This script fabricates
a CSV with the SAME SCHEMA and PHYSICALLY-PLAUSIBLE-SHAPED (but not physically derived)
relationships purely so the ml/ pipeline can be exercised end-to-end today.

DELETE / IGNORE this file's output once `data/synthetic_cycles.csv` exists — retrain
on that instead (see ml/README.md).

Fake relationships encoded below (chosen to be qualitatively realistic for a heavy-oil
CSS + sucker-rod-pump system, per docs/SPEC.md, but with arbitrary coefficients):
  - SOR_t_per_m3 is U-shaped in steam_t: too little steam wastes energy heating an
    inadequate zone (poor oil mobilization -> high SOR); too much steam over-heats /
    over-injects for marginal extra oil (also high SOR). A sweet spot exists mid-range.
  - max_floating_index rises with spm (faster pump strokes -> more downstroke drag
    against under-lubricated oil) and falls with steam_t (more heat -> lower oil
    viscosity -> less rod/tubing "floating").
  - oil_total_m3 rises with steam_t but with diminishing returns (sqrt-like growth):
    each extra tonne of steam mobilizes less incremental oil than the last.
  - energy_per_m3_kWh rises with spm (more pump cycles/energy) and falls with
    oil_total (fixed per-cycle overhead spread over more barrels).
  - days_total grows with soak_days (fixed offset) and with lower cutoff_m3d
    (a stricter/lower economic cutoff rate means the well produces longer before
    the operator calls the cycle over).
  - failures_expected is a small Poisson count whose rate scales with
    max_floating_index (floating/pump-off events are what damage rods).
All relationships include Gaussian noise. Seed = 42 for reproducibility.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Ranges straight from docs/SPEC.md params/field_params.json css + srp blocks.
STEAM_T_RANGE = (500.0, 3000.0)
SOAK_DAYS_RANGE = (3, 15)
CUTOFF_M3D_RANGE = (1.0, 8.0)
SPM_RANGE = (4.0, 12.0)

N_ROWS = 3000
SEED = 42


def generate(n_rows: int = N_ROWS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    steam_t = rng.uniform(*STEAM_T_RANGE, n_rows)
    soak_days = rng.integers(SOAK_DAYS_RANGE[0], SOAK_DAYS_RANGE[1] + 1, n_rows).astype(float)
    cutoff_m3d = rng.uniform(*CUTOFF_M3D_RANGE, n_rows)
    spm = rng.uniform(*SPM_RANGE, n_rows)

    # ---- SOR_t_per_m3: U-shaped in steam_t, minimum inside the range (~1650 t) ----
    steam_optimum = 1650.0
    sor = (
        2.6
        + 3.2e-6 * (steam_t - steam_optimum) ** 2  # U-shape driver
        + 0.015 * (soak_days - 9.0)  # slightly worse SOR if soak is far from ~9d
        - 0.03 * (cutoff_m3d - 4.5)  # lower cutoff -> produce longer -> marginally worse avg SOR
        + rng.normal(0, 0.12, n_rows)
    )
    sor = np.clip(sor, 1.0, None)

    # ---- floating_index: rises with spm, falls with steam_t ----
    floating_raw = (
        0.5
        + 0.05 * (spm - 8.0)
        - 0.0003 * (steam_t - 1750.0)
        + rng.normal(0, 0.10, n_rows)
    )
    # max over the cycle >= the "average" tendency above
    max_floating_index = np.clip(floating_raw + np.abs(rng.normal(0, 0.05, n_rows)), 0.0, 1.0)

    # ---- oil_total_m3: rises with steam_t, diminishing returns ----
    steam_norm = (steam_t - STEAM_T_RANGE[0]) / (STEAM_T_RANGE[1] - STEAM_T_RANGE[0])
    oil_total_m3 = (
        150.0
        + 900.0 * np.sqrt(steam_norm)
        + 8.0 * (soak_days - 3.0)
        - 15.0 * (cutoff_m3d - 1.0)
        + rng.normal(0, 25.0, n_rows)
    )
    oil_total_m3 = np.clip(oil_total_m3, 20.0, None)

    # ---- energy_per_m3_kWh: rises with spm, falls with scale of production ----
    energy_per_m3_kWh = (
        4.0
        + 0.9 * spm
        + 400.0 / oil_total_m3
        + rng.normal(0, 0.3, n_rows)
    )
    energy_per_m3_kWh = np.clip(energy_per_m3_kWh, 1.0, None)

    # ---- days_total: soak + production length (longer if cutoff is stricter/lower) ----
    days_total = (
        soak_days
        + 25.0
        + 60.0 / cutoff_m3d
        + 0.01 * steam_t
        + rng.normal(0, 3.0, n_rows)
    )
    days_total = np.clip(days_total, soak_days + 5.0, None)

    # ---- failures_expected: Poisson count driven by floating risk ----
    failures_expected = rng.poisson(lam=np.clip(3.0 * max_floating_index, 0.01, None))

    df = pd.DataFrame(
        {
            "steam_t": steam_t,
            "soak_days": soak_days,
            "cutoff_m3d": cutoff_m3d,
            "spm": spm,
            "oil_total_m3": oil_total_m3,
            "SOR_t_per_m3": sor,
            "energy_per_m3_kWh": energy_per_m3_kWh,
            "days_total": days_total,
            "max_floating_index": max_floating_index,
            "failures_expected": failures_expected,
        }
    )
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent.parent / "data" / "placeholder_cycles.csv"),
        help="Output CSV path (default: data/placeholder_cycles.csv)",
    )
    parser.add_argument("--n-rows", type=int, default=N_ROWS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    df = generate(args.n_rows, args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} PLACEHOLDER (fake) rows to {out_path}")
    print("This file is for ml/ pipeline testing only — see module docstring.")


if __name__ == "__main__":
    main()
