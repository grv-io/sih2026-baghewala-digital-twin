"""twin/generate_pseudo_real.py -- pseudo-real demo dataset for twin/calibrate.py.

**This is SYNTHETIC data, not Oil India field data.** It exists to demonstrate
the ingest -> recalibrate -> re-recommend loop end to end before real
Baghewala per-well cycle records are available. See
`data/external/SOURCE.md` for the same disclosure alongside the CSV.

What this script does
----------------------
1. Builds a HIDDEN "true" params tree that differs from
   `params/field_params.json`'s defaults on the three parameters
   `twin/calibrate.py` fits by default under the shipped rev-12
   `fluid.water_cut_model = "state"` (`twin.calibrate.default_free`):
   `formation_water_cut` 0.45 -> 0.38, `reservoir.thickness_m` 12 -> 15,
   `AOF_REF_M3D` 0.56 -> 0.65. `bl_delta_factor` is 0.5 in the truth as well
   (27 Sep 2026: it is sourced physics -- PEH Eqs. 15.70/15.73, CHANGELOG
   rev 7 -- not an unknown; the earlier demo hid 0.72, which the physics now
   rules out). rev 12 (cascade): the demo now runs CURRENT physics (water cut
   as a state, Pal-Rhodes emulsion, the float-onset produce-end rule, AOF
   0.56) instead of pinning the rev-10 legacy switches -- the old
   `fluid.water_cut` 0.78 hidden-truth value is retired since that constant
   is not read under the state model; `formation_water_cut` is the analogous
   free parameter now.
2. Runs `twin.cycle.simulate_css_cycle` at 8 varied set-points (within the
   practice ranges) across 3 fictional wells BGW-D1/D2/D3 against that hidden
   params tree, producing "true" oil_m3/produce_days/peak_oil_m3d.
3. Adds seed-42, +/-8% multiplicative noise to oil_m3, produce_days and
   peak_oil_m3d (independently per row) -- observed field measurements are
   never exact.
4. Writes `data/external/pseudo_real_cycles.csv` (the observed-cycles CSV,
   `twin/calibrate.py`'s schema), `data/external/pseudo_real_TRUTH.json` (the
   hidden truth, for grading the recovery) and `data/external/SOURCE.md`.
5. Runs `twin.calibrate.fit` on the noisy CSV against the DEFAULT (unaware)
   params, and `ml.recommend_physics.best_settings_physics` before and after
   applying the fit, writing `ml/models/calibration_demo_report.json` -- the
   recovered-vs-truth table and the before/after recommendation, all
   physics-verified.

Run: `python -m twin.generate_pseudo_real`
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from twin import calibrate, cycle  # noqa: E402  (see sys.path shim above)
from ml import recommend_physics  # noqa: E402

SEED = 42
NOISE_FRAC = 0.08  # +/- 8% uniform multiplicative noise

PARAMS_PATH = _ROOT / "params" / "field_params.json"
OUT_DIR = _ROOT / "data" / "external"
OUT_CSV = OUT_DIR / "pseudo_real_cycles.csv"
TRUTH_JSON = OUT_DIR / "pseudo_real_TRUTH.json"
SOURCE_MD = OUT_DIR / "SOURCE.md"
DEMO_REPORT_JSON = _ROOT / "ml" / "models" / "calibration_demo_report.json"

HIDDEN_TRUTH = {
    "bl_delta_factor": 0.5,   # sourced physics, NOT fitted (see docstring)
    "formation_water_cut": 0.38,   # rev 12: within DEFAULT_BOUNDS (0.30, 0.60); base default is 0.45
    "thickness_m": 15.0,
    "aof_ref_m3d": 0.65,   # rev 12: base default retuned to 0.56 (AOF peak-band retune, TIER1 section 11.4);
                           # chosen clearly away from that new base so the fit has a real signal to recover
}

# 8 cycles across 3 fictional wells, set-points inside the practice ranges
# (css.steam_volume_t_range [500,3000], css.soak_days_range [3,15],
# css.cutoff_rate_m3d_range [0.6,2.0], srp.spm_practice_band [3,6]).
SETPOINTS = [
    {"well_id": "BGW-D1", "steam_t": 1200.0, "soak_days": 7.0, "cutoff_m3d": 0.90, "spm": 4.5},
    {"well_id": "BGW-D1", "steam_t": 1500.0, "soak_days": 10.0, "cutoff_m3d": 0.85, "spm": 5.0},
    {"well_id": "BGW-D1", "steam_t": 1800.0, "soak_days": 12.0, "cutoff_m3d": 0.75, "spm": 5.5},
    {"well_id": "BGW-D2", "steam_t": 1000.0, "soak_days": 8.0, "cutoff_m3d": 1.00, "spm": 4.0},
    {"well_id": "BGW-D2", "steam_t": 1600.0, "soak_days": 9.0, "cutoff_m3d": 0.80, "spm": 5.0},
    {"well_id": "BGW-D2", "steam_t": 2000.0, "soak_days": 11.0, "cutoff_m3d": 0.70, "spm": 5.5},
    {"well_id": "BGW-D3", "steam_t": 1300.0, "soak_days": 10.0, "cutoff_m3d": 0.90, "spm": 4.5},
    {"well_id": "BGW-D3", "steam_t": 1900.0, "soak_days": 13.0, "cutoff_m3d": 0.75, "spm": 6.0},
]


def _true_params(base_params: dict) -> dict:
    # rev 12 (cascade): run CURRENT physics (water cut as a state,
    # Pal-Rhodes-capped emulsion, the float-onset produce-end rule, AOF 0.56)
    # -- no legacy switches. The hidden truth differs from field_params.json's
    # defaults only on the three parameters twin.calibrate.default_free()
    # picks for the state water-cut model (formation_water_cut, aof_ref_m3d,
    # thickness_m); bl_delta_factor is sourced physics, held at the same 0.5
    # in both the truth and the default (see module docstring).
    p = copy.deepcopy(base_params)
    p.setdefault("thermal", {})["bl_delta_factor"] = HIDDEN_TRUTH["bl_delta_factor"]
    p["fluid"]["formation_water_cut"] = HIDDEN_TRUTH["formation_water_cut"]
    p["reservoir"]["thickness_m"] = HIDDEN_TRUTH["thickness_m"]
    p.setdefault("ipr", {})["aof_ref_m3d"] = HIDDEN_TRUTH["aof_ref_m3d"]
    return p


def generate_dataset(base_params: dict) -> pd.DataFrame:
    true_params = _true_params(base_params)
    rng = np.random.default_rng(SEED)

    rows = []
    for sp in SETPOINTS:
        df = cycle.simulate_css_cycle(
            steam_t=sp["steam_t"], soak_days=sp["soak_days"],
            cutoff_m3d=sp["cutoff_m3d"], spm=sp["spm"], params=true_params,
        )
        s = cycle.summary(df, true_params)

        oil_factor = 1.0 + rng.uniform(-NOISE_FRAC, NOISE_FRAC)
        days_factor = 1.0 + rng.uniform(-NOISE_FRAC, NOISE_FRAC)
        peak_factor = 1.0 + rng.uniform(-NOISE_FRAC, NOISE_FRAC)

        oil_m3 = s["oil_total_m3"] * oil_factor
        produce_days = s["days_total"] * days_factor
        peak_oil_m3d = s["peak_oil_m3d"] * peak_factor

        rows.append({
            "well_id": sp["well_id"],
            "steam_t": sp["steam_t"],
            "soak_days": sp["soak_days"],
            "cutoff_m3d": sp["cutoff_m3d"],
            "spm": sp["spm"],
            "oil_m3": round(float(oil_m3), 2),
            "produce_days": round(float(produce_days), 1),
            "peak_oil_m3d": round(float(peak_oil_m3d), 3),
            "sor": round(float(sp["steam_t"] / oil_m3), 4),
        })
    return pd.DataFrame(rows)


def _write_source_md() -> None:
    SOURCE_MD.write_text(
        "# data/external/ -- SOURCE\n\n"
        "`pseudo_real_cycles.csv` is **SYNTHETIC, pseudo-real demonstration "
        "data, NOT Oil India field data.** It was generated by "
        "`twin/generate_pseudo_real.py` by running the twin's own physics "
        "engine (`twin.cycle.simulate_css_cycle`) against a HIDDEN 'true' "
        "params set that deliberately differs from "
        "`params/field_params.json`'s defaults on the three constants "
        "`twin/calibrate.py` fits by default under the shipped rev-12 "
        "state water-cut model (formation_water_cut, thickness_m, "
        "aof_ref_m3d; bl_delta_factor is the sourced 0.5 in the truth too -- "
        "see `pseudo_real_TRUTH.json`), at 8 "
        "varied set-points across 3 fictional wells (BGW-D1..D3), with "
        "seed-42 +/-8% multiplicative noise added to oil_m3/produce_days/"
        "peak_oil_m3d to imitate measurement noise on a real field record.\n\n"
        "Its only purpose is to demonstrate the ingest -> recalibrate -> "
        "re-recommend loop end to end (`twin/calibrate.py` + "
        "`ml/recommend_physics.py`) before real Baghewala per-well cycle "
        "records are available. Do not cite it, or `pseudo_real_TRUTH.json`, "
        "as a field measurement anywhere in the deck or docs.\n\n"
        "`pseudo_real_TRUTH.json` holds the hidden true values, for grading "
        "how well `twin.calibrate.fit` recovers them "
        "(`ml/models/calibration_demo_report.json` is the recovered-vs-truth "
        "table). Regenerate with `python -m twin.generate_pseudo_real` "
        "(deterministic, seed 42).\n"
    )


def _recovery_table(fitted: dict, truth: dict, base_params: dict) -> list[dict]:
    rows = []
    for name, truth_value in truth.items():
        is_free = name in fitted
        value = fitted[name] if is_free else calibrate._current_value(name, base_params)
        pct_error = (
            100.0 * (value - truth_value) / abs(truth_value)
            if value is not None and truth_value != 0 else None
        )
        rows.append({
            "param": name,
            "truth": truth_value,
            "fitted": value,
            "free": is_free,
            "pct_error": pct_error,
        })
    return rows


def run_demo(base_params: dict, observed_df: pd.DataFrame) -> dict:
    # rev 12 (cascade): fit against CURRENT physics (same physics the data was
    # generated with in _true_params -- no legacy switches). calibrate.fit's
    # default `free` set auto-selects (formation_water_cut, aof_ref_m3d,
    # thickness_m) for the shipped water_cut_model="state" params tree.
    fit_result = calibrate.fit(observed_df, base_params)
    calibrated_params = calibrate.apply(base_params, fit_result["fitted_params"])

    recommendation_before = recommend_physics.best_settings_physics(
        base_params, fixed={"soak_days": 10.0}
    )
    recommendation_after = recommend_physics.best_settings_physics(
        calibrated_params, fixed={"soak_days": 10.0}
    )

    return {
        "hidden_truth": HIDDEN_TRUTH,
        "recovered_vs_truth": _recovery_table(fit_result["fitted_params"], HIDDEN_TRUTH, base_params),
        "fitted_params": fit_result["fitted_params"],
        "bounds": fit_result["bounds"],
        "rmse": fit_result["rmse"],
        "residual_table": fit_result["residual_table"],
        "identifiability": fit_result["identifiability"],
        "n_cycles": fit_result["n_cycles"],
        "recommendation_before_calibration": recommendation_before,
        "recommendation_after_calibration": recommendation_after,
    }


def main() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        base_params = json.load(f)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    observed_df = generate_dataset(base_params)
    observed_df.to_csv(OUT_CSV, index=False)
    with open(TRUTH_JSON, "w", encoding="utf-8") as f:
        json.dump(HIDDEN_TRUTH, f, indent=2)
    _write_source_md()
    print(f"Wrote {OUT_CSV} ({len(observed_df)} rows)")
    print(f"Wrote {TRUTH_JSON}")
    print(f"Wrote {SOURCE_MD}")

    demo = run_demo(base_params, observed_df)
    DEMO_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(DEMO_REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(calibrate._to_jsonable(demo), f, indent=2)
    print(f"Wrote {DEMO_REPORT_JSON}")

    print("\n=== Recovered vs truth ===")
    for row in demo["recovered_vs_truth"]:
        pct = row["pct_error"]
        pct_str = f"{pct:+.1f}%" if pct is not None else "n/a"
        tag = "" if row["free"] else "  [fixed, not fitted]"
        print(f"  {row['param']:16s} truth={row['truth']:>8.3f}  fitted={row['fitted']:>8.3f}  ({pct_str}){tag}")

    print("\n=== Recommendation before vs after calibration ===")
    for label, rec in (("before", demo["recommendation_before_calibration"]),
                       ("after", demo["recommendation_after_calibration"])):
        opt = rec["physics_verified_optimum"]
        print(
            f"  {label:7s} best_settings={rec['best_settings']}  "
            f"SOR={opt['SOR_t_per_m3']:.3f}  SOR_incr={opt['SOR_incremental']:.3f}  "
            f"incr. margin/day={opt['margin_incremental_inr_per_cycle_day']:,.0f}  "
            f"(gross {opt['margin_inr_per_cycle_day']:,.0f})"
        )


if __name__ == "__main__":
    main()
