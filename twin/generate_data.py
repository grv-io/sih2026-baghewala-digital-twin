"""generate_data.py -- synthetic CSS-cycle dataset generator for ml/train.py.

Runs `twin.cycle.simulate_css_cycle` + `twin.cycle.summary` over a Latin
Hypercube sample of the design inputs (steam_t, soak_days, cutoff_m3d,
spm; rev 12: plus p_wellhead_kgf_cm2 and stroke_in, see below), with ranges taken from `params/field_params.json`'s "css" and "srp"
blocks (per docs/SPEC.md; rev 10: spm is sampled over the UNION of
srp.spm_range and srp.spm_practice_band, i.e. 3-12, so the data cover the
optimiser's 3-6 search box), and writes one row per cycle to
data/synthetic_cycles.csv.

Columns:
    steam_t, soak_days, cutoff_m3d, spm,                        (inputs)
    oil_total_m3, SOR_t_per_m3, energy_per_m3_kWh,
    days_total, max_floating_index, failures_expected           (original 10 SPEC
                                                                  columns, kept
                                                                  first for
                                                                  backward
                                                                  compatibility)
    produce_days, alarm_days, margin_inr,
    margin_inr_per_cycle_day, co2_t, pump_limited_days           (rev-5 additions,
                                                                  appended -- see
                                                                  twin/cycle.py
                                                                  summary())

rev 12 (physics wave 4, 27 Sep 2026): the LHS covers the FULL control space
the 5-D optimiser searches, so a retrained surrogate is not extrapolating in
two of its five levers:
    p_wellhead_kgf_cm2   U-LHS over steam.P_wellhead_range_kgf_cm2 (CONFIRMED
                         85-97 kgf/cm2 g; the steam state follows it, IF97)
    stroke_in            one of srp.stroke_in_options (API 64/74/86/100/120/
                         144 in), the LHS column cut into six equal strata
    spm                  3-12 (union of spm_range and the practice band, rev 10)
The two new inputs are APPENDED as the last columns (after every summary
column), so the first 10 SPEC columns and ml/train.py's FEATURES
(steam_t, soak_days, cutoff_m3d, spm) are unchanged; the cascade decides
whether to add them to FEATURES. `produce_end_reason` (rev 12 operating rule:
"rate_cutoff" / "float_onset" / "max_days") and `float_alarm_days`
(= failures_expected, FI > 0.6) are appended too. Every cycle runs the
params' produce-end rule (default "either"). Adding two LHS dimensions
changes the design (and hence every row) for a given seed. NOT run here: the
data/ and ml/models/ regeneration is the cascade's job.

rev 13 (wave 5, 27 Sep 2026): the float POLICY is an optimiser dimension
(twin/cycle.py css.float_policy), so the LHS gets a 7th, categorical column
`float_policy` (pull / vfd_hold / vfd_then_pull, equal strata, appended after
`stroke_in`), and every cycle runs its row's policy. New label columns
(appended after the rule columns; NOT consumed by ml/train.py yet -- the
cascade decides):
    fi_gt_alarm_any      max FI > css.fi_alarm on any produce day (~82 % of rows:
                         too unbalanced to be informative);
    float_forced_pull    the float-onset pull, not the rate cutoff, ended the
                         cycle (~80 %; the rev-12 label's 95 % came from this);
    end_rate_over_cutoff oil rate on the last produce day / the row's cutoff;
    float_premature_pull RECOMMENDED CLASSIFIER LABEL: float_forced_pull AND the
                         oil rate was still >= FLOAT_PREMATURE_RATIO (1.5) x the
                         economic cutoff when the rods forced the pull -- "the
                         rods, not the economics, ended a still-productive
                         cycle". ~41 % positive on a 450-row sample of this
                         design (pull 55 %, vfd_hold 32 %, vfd_then_pull 37 %).
The legacy `max_floating_index` / `alarm_days` / `float_alarm_days` columns are
unchanged (ml/train.py's rev-12 label still reads them).

`alarm_days` = `summary()["days_rods_in_compression"]` (days the produce-phase
floating index reached >= 1.0, i.e. an actual rod-float alarm trip -- distinct
from the softer `failures_expected` count, which uses the >0.6 risk threshold).
`produce_days` is the count of produce-phase rows in the day-by-day frame
(distinct from `days_total`/`cycle_days`, which spans inject+soak+produce).

Deterministic: seed=42 (docs/SPEC.md "No network calls in twin/ or ml/.
Deterministic with seed 42").

Usage:
    python generate_data.py [--n-rows 3000] [--out path/to/synthetic_cycles.csv]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import json
import numpy as np
import pandas as pd
from scipy.stats import qmc

# Allow `python twin/generate_data.py` (run directly, not as `-m twin.generate_data`)
# to find the `twin` package regardless of the process cwd.
_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_ROOT_FOR_IMPORT))

from twin import cycle

SEED = 42
N_ROWS = 3000

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARAMS_PATH = ROOT / "params" / "field_params.json"
DEFAULT_OUT_PATH = ROOT / "data" / "synthetic_cycles.csv"

_INPUT_COLUMNS = ["steam_t", "soak_days", "cutoff_m3d", "spm"]
_SUMMARY_COLUMNS = [
    "oil_total_m3", "SOR_t_per_m3", "energy_per_m3_kWh",
    "days_total", "max_floating_index", "failures_expected",
]
# rev-5 additions (Phase-2 ML retrain), appended after the original 10 SPEC
# columns so any code that slices df.iloc[:, :10] / EXPECTED_COLUMNS[:10] still
# works unchanged. "days_total" here is the *summary()* key for total cycle
# days (inject+soak+produce); we also append "days_rods_in_compression" from
# summary() renamed to "alarm_days" and a produce-phase-only day count.
_EXTRA_SUMMARY_KEYS = [
    ("days_rods_in_compression", "alarm_days"),
    ("margin_inr", "margin_inr"),
    ("margin_inr_per_cycle_day", "margin_inr_per_cycle_day"),
    ("co2_t", "co2_t"),
    ("pump_limited_days", "pump_limited_days"),
    # Economics v2 (rev 8/9, 27 Sep 2026): opex, corrected (grid) energy, cold
    # baseline and incremental-oil keys -- all additive on top of the rev-5
    # columns above. margin_incremental_inr_per_cycle_day is the ML objective
    # trained in ml/train.py's margin regressor (replacing the gross target).
    ("window_days", "window_days"),
    ("electric_kWh", "electric_kWh"),
    ("electric_kWh_per_m3", "electric_kWh_per_m3"),
    ("power_cost_inr", "power_cost_inr"),
    ("opex_fixed_inr", "opex_fixed_inr"),
    ("opex_inr", "opex_inr"),
    ("margin_with_opex_inr", "margin_with_opex_inr"),
    ("margin_with_opex_inr_per_cycle_day", "margin_with_opex_inr_per_cycle_day"),
    ("cold_rate_m3d", "cold_rate_m3d"),
    ("cold_well_economic", "cold_well_economic"),
    ("oil_cold_baseline_m3", "oil_cold_baseline_m3"),
    ("oil_incremental_m3", "oil_incremental_m3"),
    ("oil_incremental_bbl", "oil_incremental_bbl"),
    ("SOR_incremental", "SOR_incremental"),
    ("margin_incremental_inr", "margin_incremental_inr"),
    ("margin_incremental_inr_per_cycle_day", "margin_incremental_inr_per_cycle_day"),
    ("margin_incremental_inr_per_t_steam", "margin_incremental_inr_per_t_steam"),
    ("cadp_resteam_day", "cadp_resteam_day"),
    ("cadp_resteam_rate_m3d", "cadp_resteam_rate_m3d"),
    ("cadp_margin_incremental_inr_per_cycle_day", "cadp_margin_incremental_inr_per_cycle_day"),
]
_EXTRA_COLUMNS = ["produce_days"] + [out_name for _, out_name in _EXTRA_SUMMARY_KEYS]
# rev 12: the two rev-11 surface controls, sampled in the LHS, and the
# produce-end diagnostics -- appended last.
_CONTROL_COLUMNS = ["p_wellhead_kgf_cm2", "stroke_in"]
_RULE_COLUMNS = ["produce_end_reason", "float_alarm_days"]
# rev 13: the float policy (7th LHS column) and the float labels
_POLICY_COLUMNS = ["float_policy"]
_LABEL_COLUMNS = ["fi_gt_alarm_any", "float_forced_pull", "end_rate_over_cutoff", "float_premature_pull"]
LHS_POLICIES = ("pull", "vfd_hold", "vfd_then_pull")
# [ASSUMPTION] "premature": the rods forced the pull while the oil rate was still
# at least this multiple of the economic cutoff (label threshold, not physics).
FLOAT_PREMATURE_RATIO = 1.5


def _load_params(params_path: Path) -> dict:
    with open(params_path, "r", encoding="utf-8") as f:
        return json.load(f)


def sampled_spm_range(params: dict) -> tuple[float, float]:
    """SPM range the LHS samples: the UNION of srp.spm_range and srp.spm_practice_band.

    rev 10 (external review, ML finding): the surrogates were trained on
    spm_range [4, 12] while ml/optimize.py searches the practice band [3, 6],
    so a third of the optimiser's box (3-4 spm, where the base-deck grid
    optimum sat) was tree-constant extrapolation. Sampling the union [3, 12]
    makes the training data cover the whole search space. The cutoff range is
    unchanged (css.cutoff_rate_m3d_range is already the search range).
    """
    srp = params["srp"]
    lo, hi = srp["spm_range"]
    band = srp.get("spm_practice_band")
    if band:
        lo, hi = min(lo, band[0]), max(hi, band[1])
    return float(lo), float(hi)


def sampled_pressure_range(params: dict) -> tuple[float, float]:
    """Wellhead injection-pressure range the LHS samples (rev 12): the CONFIRMED
    steam.P_wellhead_range_kgf_cm2 (85-97 kgf/cm2 g, OIL deck BGW-08)."""
    lo, hi = params.get("steam", {}).get("P_wellhead_range_kgf_cm2") or (85.0, 97.0)
    return float(lo), float(hi)


def sampled_stroke_options(params: dict) -> list[float]:
    """Discrete stroke lengths (in) the LHS samples (rev 12): srp.stroke_in_options."""
    opts = params.get("srp", {}).get("stroke_in_options") or [64, 74, 86, 100, 120, 144]
    return [float(x) for x in opts]


def _sample_inputs(params: dict, n_rows: int, seed: int) -> pd.DataFrame:
    """Latin-hypercube sample the design inputs over their field_params.json ranges.

    rev 12: six dimensions -- steam_t, soak_days, cutoff_m3d, spm, and the two
    rev-11 controls p_wellhead_kgf_cm2 (continuous) and stroke_in (discrete API
    sizes: the unit column is cut into len(options) equal strata, so each size
    gets ~n_rows/6 rows and the LHS balance carries over). rev 13: a seventh,
    categorical `float_policy` column (LHS_POLICIES, equal strata)."""
    css = params["css"]

    steam_lo, steam_hi = css["steam_volume_t_range"]
    soak_lo, soak_hi = css["soak_days_range"]
    cutoff_lo, cutoff_hi = css["cutoff_rate_m3d_range"]
    spm_lo, spm_hi = sampled_spm_range(params)
    p_lo, p_hi = sampled_pressure_range(params)
    strokes = sampled_stroke_options(params)

    # scipy.stats.qmc.LatinHypercube gives a space-filling design across the
    # unit cube, which we then rescale per-dimension to each input's
    # own range -- this covers the joint design space far more evenly than
    # independent uniform draws for the same sample count.
    sampler = qmc.LatinHypercube(d=7, seed=seed)
    unit_sample = sampler.random(n=n_rows)

    lo = np.array([steam_lo, soak_lo, cutoff_lo, spm_lo, p_lo])
    hi = np.array([steam_hi, soak_hi, cutoff_hi, spm_hi, p_hi])
    scaled = qmc.scale(unit_sample[:, :5], lo, hi)

    df = pd.DataFrame(scaled[:, :4], columns=_INPUT_COLUMNS)
    df["p_wellhead_kgf_cm2"] = scaled[:, 4]
    idx = np.minimum((unit_sample[:, 5] * len(strokes)).astype(int), len(strokes) - 1)
    df["stroke_in"] = np.asarray(strokes)[idx]
    # rev 13: float policy, categorical, equal strata of the 7th LHS column
    pidx = np.minimum((unit_sample[:, 6] * len(LHS_POLICIES)).astype(int), len(LHS_POLICIES) - 1)
    df["float_policy"] = np.asarray(LHS_POLICIES)[pidx]
    # ASSUMPTION: soak_days is specified as an integer-day range in
    # field_params.json (css.soak_days_range); round the continuous LHS
    # sample to the nearest whole day rather than leaving it fractional.
    df["soak_days"] = df["soak_days"].round().astype(float)
    return df


def _float_labels(df: pd.DataFrame, s: dict, cutoff_m3d: float, policy: str) -> dict:
    """rev 13 float label columns (see the module docstring)."""
    prod = df[df["phase"] == "produce"]
    end_rate = float(prod["oil_m3d"].iloc[-1]) if len(prod) else 0.0
    forced = s.get("produce_end_reason") == "float_onset"
    ratio = end_rate / cutoff_m3d if cutoff_m3d > 0 else float("inf")
    return {
        "float_policy": policy,
        "fi_gt_alarm_any": bool(s["max_floating_index"] > cycle.FLOATING_RISK_THRESHOLD + cycle.ALARM_TOL),
        "float_forced_pull": bool(forced),
        "end_rate_over_cutoff": ratio,
        "float_premature_pull": bool(forced and ratio >= FLOAT_PREMATURE_RATIO),
    }


def generate(params: dict, n_rows: int = N_ROWS, seed: int = SEED) -> pd.DataFrame:
    """Run n_rows CSS cycles over an LHS design and return the combined dataset."""
    inputs_df = _sample_inputs(params, n_rows, seed)

    rows: list[dict] = []
    for row in inputs_df.itertuples(index=False):
        steam_t, soak_days, cutoff_m3d, spm, p_wh, stroke_in, policy = row
        df = cycle.simulate_css_cycle(
            steam_t=steam_t,
            soak_days=soak_days,
            cutoff_m3d=cutoff_m3d,
            spm=spm,
            params=params,
            stroke_m=float(stroke_in) * 0.0254,     # rev 12: API stroke (in -> m)
            p_wellhead_kgf_cm2=float(p_wh),         # rev 12: injection pressure
            float_policy=str(policy),               # rev 13: operator float policy
        )
        # rev 5: pass params through so summary()'s economics block (₹/CO2/
        # margin) matches this run's field_params.json instead of the
        # module-default constants (identical today, but this keeps the
        # dataset honest if the economics block is ever edited independently).
        s = cycle.summary(df, params=params)
        produce_days = int((df["phase"] == "produce").sum()) if len(df) else 0
        row = {
            "steam_t": steam_t,
            "soak_days": soak_days,
            "cutoff_m3d": cutoff_m3d,
            "spm": spm,
            **{k: s[k] for k in _SUMMARY_COLUMNS},
            "produce_days": produce_days,
            **{out_name: s[src_key] for src_key, out_name in _EXTRA_SUMMARY_KEYS},
            "p_wellhead_kgf_cm2": float(p_wh),
            "stroke_in": float(stroke_in),
            "produce_end_reason": s.get("produce_end_reason"),
            "float_alarm_days": s["failures_expected"],
            **_float_labels(df, s, float(cutoff_m3d), str(policy)),
        }
        # rev 12 (cascade): append every summary() key not already captured
        # above, in summary()'s own insertion order, so the CSV carries the
        # FULL physics output -- water-cut start/end, float timing, PRL cap,
        # steam state, incremental economics, etc. (TIER1 section 11 asked
        # for "all summary keys"). `s["produce_days"]` (a float(len*dt) from
        # _water_and_controls) is intentionally skipped: it duplicates the
        # integer `produce_days` column above (row-count basis) to within
        # dt, and keeping only one avoids two near-identical, confusingly
        # named columns.
        _already = (set(row.keys()) | {k for k, _ in _EXTRA_SUMMARY_KEYS} | {"produce_days"}
                    | {"float_policy"})
        for k, v in s.items():
            if k in _already:
                continue
            row[k] = v
        rows.append(row)

    # rev 12: column order = the original spec/rev-5/rev-11/rev-12 columns
    # (unchanged, for backward compatibility) followed by every remaining
    # summary() key, in the first row's own dict order (stable across rows
    # because every cycle runs through the same summary() code path).
    _fixed_cols = (_INPUT_COLUMNS + _SUMMARY_COLUMNS + _EXTRA_COLUMNS
                   + _CONTROL_COLUMNS + _RULE_COLUMNS + _POLICY_COLUMNS + _LABEL_COLUMNS)
    _extra_cols = [c for c in (rows[0].keys() if rows else []) if c not in _fixed_cols]
    out_df = pd.DataFrame(rows, columns=(_fixed_cols + _extra_cols))

    # ASSUMPTION: a handful of pathological corners of the design space
    # (e.g. very low steam_t combined with a very low cutoff_m3d) can yield
    # a degenerate zero-oil cycle, for which cycle.summary() reports
    # SOR_t_per_m3 = inf and margin_inr_per_cycle_day = -inf (documented
    # ASSUMPTION in twin/cycle.py). Drop those rows rather than feed inf/NaN
    # into ml/train.py's regressors.
    n_before = len(out_df)
    finite_mask = (
        np.isfinite(out_df["SOR_t_per_m3"])
        & np.isfinite(out_df["margin_inr_per_cycle_day"])
        & np.isfinite(out_df["margin_incremental_inr_per_cycle_day"])
    )
    out_df = out_df[finite_mask].reset_index(drop=True)
    n_dropped = n_before - len(out_df)
    if n_dropped:
        print(f"Dropped {n_dropped} degenerate zero-oil cycle(s) (SOR/margin non-finite) out of {n_before}.")

    return out_df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--params", default=str(DEFAULT_PARAMS_PATH), help="Path to field_params.json")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH), help="Output CSV path")
    parser.add_argument("--n-rows", type=int, default=N_ROWS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    params = _load_params(Path(args.params))
    df = generate(params, n_rows=args.n_rows, seed=args.seed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path} (seed={args.seed})")


if __name__ == "__main__":
    main()
