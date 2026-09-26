"""Train the digital-twin surrogate models (rev 13 retrain, physics wave 5).

Reads a CSV of simulated CSS cycles (default: data/synthetic_cycles.csv, produced
by twin/generate_data.py against the rev-13 physics -- see params/CHANGELOG.md
rev 13 and docs/model-improvement/TIER1_PROGRESS_LOG.md section 12) and trains
XGBoost models used by ml/optimize.py:

  1. oil_model.joblib    -- XGBRegressor predicting log(oil_total_m3), inverse-
                             transformed back to m3 on predict(). SOR is derived
                             from this (SOR = steam_t / oil_pred) rather than
                             fit directly: steam_t is a decision variable known
                             exactly, so only the denominator needs predicting
                             (docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ML.md
                             T1-1/F2). oil_total_m3 is strictly positive with a
                             right tail (thin-steam, low-cutoff corners), so the
                             log transform is the same remedy the old SOR model
                             docstring used, just applied to the quantity that
                             actually needs it.
  2. margin_model.joblib / margin_incremental_model.joblib -- kept for
                             continuity/reporting (gross margin, and the
                             incremental-over-cold-baseline margin used as the
                             objective rev 9-12). NEITHER is the optimizer's
                             objective as of rev 13 (see 3).
  3. margin_net_cash_model.joblib -- XGBRegressor predicting
                             margin_with_opex_inr_per_cycle_day. THIS is
                             ml/optimize.py's objective as of rev 13
                             (TIER1_PROGRESS_LOG.md section 12.1/12.12): it is
                             counterfactual-free (no cold-baseline subtraction),
                             so comparing it across two float policies never
                             books the cold well's shut-in/pumped switch
                             (css.cold_counterfactual "policy") as if it were
                             part of the recommendation's own gain -- exactly
                             the bug the incremental metric had when policy
                             became a control (section 12.1: "the counterfactual
                             cancels... comparing incremental figures across
                             policies would book that switch as gain").
  4. float_model.joblib   -- XGBClassifier predicting the rev-13 label
                             `float_premature_pull` ("the rods, not the
                             economics, ended a still-productive cycle": the
                             float-onset pull happened AND the oil rate was
                             still >= 1.5x the cutoff when it did --
                             twin/generate_data.py's FLOAT_PREMATURE_RATIO).
                             ~41% positive overall (rev-12's label was ~95%
                             positive -- see the rev-12 note this replaces,
                             below -- too unbalanced to be informative; this
                             one sits inside the healthy 10-60% band).
                             Supersedes the rev-12 label
                             `(max_floating_index > 0.6) OR (alarm_days > 0)`,
                             which TIER1_PROGRESS_LOG.md section 12.12 found
                             fights the physics once float response is a
                             policy (every policy's pull IS the float
                             response, so penalising "risk of floating" solely
                             penalises the operating rule itself, re-score N7).

rev 13 (physics wave 5, cascade instructions TIER1 section 12.12): the 6
rev-12 numeric features are joined by a 7th, categorical input, the operator's
float response (`css.float_policy` in {pull, vfd_hold, vfd_then_pull} --
twin/generate_data.py's LHS never samples "none"), one-hot encoded as three
boolean columns `policy_pull` / `policy_vfd_hold` / `policy_vfd_then_pull` (all
three kept, not drop-first: harmless redundancy for tree models, and keeps the
column set stable if a 4th policy is ever added to the LHS).

Single 80/20 holdout, seed=42 (no cross-validation is run or claimed). Metrics
are written to ml/models/metrics.json:
  - regressors: R2, MAE, both overall and inside the 1,000-2,000 t steam
    envelope (the plateau documented in TIER1_PROGRESS_LOG.md section 4.4,
    "flat 1,000-2,000")
  - classifier: AUC, accuracy, positive-class share
  - physics_rev / trained_on provenance fields

Usage:
    python train.py [--data path/to/cycles.csv]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor

SEED = 42
PHYSICS_REV = 13
# rev 12: the two rev-11/rev-12 surface controls (injection pressure, stroke
# length) -- twin/generate_data.py's LHS already covers the full space the
# physics grid (ml/recommend_physics.py) searches. Column names match the CSV
# exactly (p_wellhead_kgf_cm2 in kgf/cm2 g, stroke_in in inches -- the API
# discrete sizes 64/74/86/100/120/144, treated as a continuous feature for the
# tree models, same as steam_t/cutoff_m3d).
NUMERIC_FEATURES = ["steam_t", "soak_days", "cutoff_m3d", "spm", "p_wellhead_kgf_cm2", "stroke_in"]
# rev 13: the operator's float response, a 7th (categorical) input -- see the
# module docstring. twin/generate_data.py's LHS_POLICIES (pull / vfd_hold /
# vfd_then_pull) fixes the level order; "none" is never sampled.
POLICY_COL = "float_policy"
POLICY_LEVELS = ["pull", "vfd_hold", "vfd_then_pull"]
POLICY_FEATURES = [f"policy_{p}" for p in POLICY_LEVELS]
FEATURES = NUMERIC_FEATURES + POLICY_FEATURES

OIL_TARGET = "oil_total_m3"
MARGIN_TARGET = "margin_inr_per_cycle_day"
# rev 9 (Economics v2 + FY25 price deck): the incremental margin/cycle-day
# (oil over the cold, unstimulated well for the same calendar window;
# docs/model-improvement/TIER1_PROGRESS_LOG.md section 8) was the objective
# rev 9-12. Kept trained for continuity/reporting; NOT the optimizer objective
# as of rev 13 (see MARGIN_NET_CASH_TARGET below).
MARGIN_INCREMENTAL_TARGET = "margin_incremental_inr_per_cycle_day"
# rev 13: net cash per cycle-day, counterfactual-free (no cold-baseline
# subtraction) -- ml/optimize.py's objective as of rev 13. See the module
# docstring and TIER1_PROGRESS_LOG.md section 12.1/12.6.
MARGIN_NET_CASH_TARGET = "margin_with_opex_inr_per_cycle_day"
# rev 13: the float classifier's label -- see the module docstring. Replaces
# the rev-12 (max_floating_index > 0.6) OR (alarm_days > 0) label.
FLOAT_LABEL_COL = "float_premature_pull"

# rev-5 recalibration log (TIER1_PROGRESS_LOG.md section 4.5): "margin per
# cycle-day has an interior optimum near 1,500 t (flat 1,000-2,000)". This is
# the operating envelope both regressors are additionally scored inside.
ENVELOPE_STEAM_T_RANGE = (1000.0, 2000.0)

ML_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = ML_DIR.parent / "data" / "synthetic_cycles.csv"
MODELS_DIR = ML_DIR / "models"

_XGB_REG_PARAMS = dict(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=SEED,
    n_jobs=-1,
)
_XGB_CLF_PARAMS = dict(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=SEED,
    n_jobs=-1,
    eval_metric="logloss",
)


def load_data(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Training data not found at {csv_path}. "
            "Run twin/generate_data.py first (or pass --data)."
        )
    df = pd.read_csv(csv_path)
    required = (NUMERIC_FEATURES + [POLICY_COL, OIL_TARGET, MARGIN_TARGET,
                MARGIN_INCREMENTAL_TARGET, MARGIN_NET_CASH_TARGET, FLOAT_LABEL_COL])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")
    # rev 13: one-hot the categorical float_policy -- fixed level order/columns
    # (POLICY_LEVELS), so a level absent from a particular CSV (should not
    # happen with twin/generate_data.py's LHS, but keeps this robust) still
    # gets its all-zero column rather than silently shrinking FEATURES.
    unknown = sorted(set(df[POLICY_COL].unique()) - set(POLICY_LEVELS))
    if unknown:
        raise ValueError(f"Input CSV has float_policy levels outside POLICY_LEVELS: {unknown}")
    for p in POLICY_LEVELS:
        df[f"policy_{p}"] = (df[POLICY_COL] == p).astype(int)
    return df


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    return {"r2": float(r2_score(y_true, y_pred)), "mae": float(mean_absolute_error(y_true, y_pred)), "n": int(len(y_true))}


def _envelope_mask(steam_t: pd.Series) -> pd.Series:
    lo, hi = ENVELOPE_STEAM_T_RANGE
    return steam_t.between(lo, hi)


def _repo_relative(path: Path) -> str:
    """POSIX-style path relative to the repo root, so metrics.json's
    provenance is portable across machines/clones. Falls back to the raw
    (resolved) path if it is outside the repo root."""
    repo_root = ML_DIR.parent
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def train(csv_path: Path) -> dict:
    df = load_data(csv_path)

    X = df[FEATURES]
    y_oil = df[OIL_TARGET]
    y_margin = df[MARGIN_TARGET]
    y_margin_incr = df[MARGIN_INCREMENTAL_TARGET]
    y_net_cash = df[MARGIN_NET_CASH_TARGET]
    y_clf = df[FLOAT_LABEL_COL].astype(int)

    (
        X_train, X_test,
        y_oil_train, y_oil_test,
        y_margin_train, y_margin_test,
        y_margin_incr_train, y_margin_incr_test,
        y_net_cash_train, y_net_cash_test,
        y_clf_train, y_clf_test,
    ) = train_test_split(X, y_oil, y_margin, y_margin_incr, y_net_cash, y_clf,
                          test_size=0.2, random_state=SEED)

    steam_t_test = X_test["steam_t"]
    env_mask = _envelope_mask(steam_t_test)

    print(f"Loaded {len(df)} rows from {csv_path}")
    print(f"Train/test split: {len(X_train)} / {len(X_test)} (seed={SEED})")
    print(f"Test rows inside {ENVELOPE_STEAM_T_RANGE} t envelope: {int(env_mask.sum())}")
    print(f"float_premature_pull positive rate: train={y_clf_train.mean():.3f} test={y_clf_test.mean():.3f}")

    # ---- Regressor 1: log(oil_total_m3) ----
    oil_model = TransformedTargetRegressor(
        regressor=XGBRegressor(**_XGB_REG_PARAMS),
        func=np.log,
        inverse_func=np.exp,
    )
    oil_model.fit(X_train, y_oil_train)
    oil_pred_test = oil_model.predict(X_test)
    oil_metrics_overall = _regression_metrics(y_oil_test, oil_pred_test)
    oil_metrics_envelope = _regression_metrics(y_oil_test[env_mask], oil_pred_test[env_mask])

    # Derived SOR check (not a separate model): SOR = steam_t / oil_pred.
    sor_true_test = df.loc[y_oil_test.index, "SOR_t_per_m3"]
    sor_pred_test = steam_t_test.values / np.clip(oil_pred_test, 1e-9, None)
    sor_derived_metrics = _regression_metrics(sor_true_test, sor_pred_test)

    # ---- Regressor 2: margin_inr_per_cycle_day (gross; kept for continuity) ----
    margin_model = XGBRegressor(**_XGB_REG_PARAMS)
    margin_model.fit(X_train, y_margin_train)
    margin_pred_test = margin_model.predict(X_test)
    margin_metrics_overall = _regression_metrics(y_margin_test, margin_pred_test)
    margin_metrics_envelope = _regression_metrics(y_margin_test[env_mask], margin_pred_test[env_mask])

    # ---- Regressor 2b: margin_incremental_inr_per_cycle_day (rev 9 objective) ----
    # This is what ml/optimize.py's best_settings() now maximises (Economics v2:
    # oil over the cold, unstimulated well for the same window; the gross model
    # above is kept for reporting only).
    margin_incremental_model = XGBRegressor(**_XGB_REG_PARAMS)
    margin_incremental_model.fit(X_train, y_margin_incr_train)
    margin_incr_pred_test = margin_incremental_model.predict(X_test)
    margin_incr_metrics_overall = _regression_metrics(y_margin_incr_test, margin_incr_pred_test)
    margin_incr_metrics_envelope = _regression_metrics(
        y_margin_incr_test[env_mask], margin_incr_pred_test[env_mask]
    )

    # ---- Regressor 2c: margin_with_opex_inr_per_cycle_day (rev 13 objective) ----
    # Net cash per cycle-day, counterfactual-free -- this IS ml/optimize.py's
    # objective as of rev 13 (see module docstring).
    margin_net_cash_model = XGBRegressor(**_XGB_REG_PARAMS)
    margin_net_cash_model.fit(X_train, y_net_cash_train)
    margin_net_cash_pred_test = margin_net_cash_model.predict(X_test)
    margin_net_cash_metrics_overall = _regression_metrics(y_net_cash_test, margin_net_cash_pred_test)
    margin_net_cash_metrics_envelope = _regression_metrics(
        y_net_cash_test[env_mask], margin_net_cash_pred_test[env_mask]
    )

    # ---- Classifier: float_premature_pull (rev 13 label) ----
    float_model = XGBClassifier(**_XGB_CLF_PARAMS)
    float_model.fit(X_train, y_clf_train)
    clf_proba = float_model.predict_proba(X_test)[:, 1]
    clf_pred = (clf_proba >= 0.5).astype(int)
    auc = roc_auc_score(y_clf_test, clf_proba)
    acc = accuracy_score(y_clf_test, clf_pred)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(oil_model, MODELS_DIR / "oil_model.joblib")
    joblib.dump(margin_model, MODELS_DIR / "margin_model.joblib")
    joblib.dump(margin_incremental_model, MODELS_DIR / "margin_incremental_model.joblib")
    joblib.dump(margin_net_cash_model, MODELS_DIR / "margin_net_cash_model.joblib")
    joblib.dump(float_model, MODELS_DIR / "float_model.joblib")

    # Remove the stale v1/pre-rev5 sor_model.joblib if present -- SOR is now
    # derived from oil_model.predict(), not a separately trained model, and a
    # leftover sor_model.joblib would silently go stale.
    stale_sor_model = MODELS_DIR / "sor_model.joblib"
    if stale_sor_model.exists():
        stale_sor_model.unlink()
        print(f"Removed stale {stale_sor_model} (superseded by oil_model.joblib + derived SOR).")

    metrics = {
        "physics_rev": PHYSICS_REV,
        # Repo-relative (not absolute) so metrics.json stays reproducible
        # across machines/clones; falls back to the raw path if csv_path
        # lives outside the repo root.
        "trained_on": _repo_relative(csv_path),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_rows": len(df),
        "seed": SEED,
        "note": "Single 80/20 holdout, seed 42. No cross-validation was run.",
        "envelope_steam_t_range": list(ENVELOPE_STEAM_T_RANGE),
        "oil_regressor": {
            "target": f"log({OIL_TARGET}), inverse-transformed to m3 on predict()",
            "overall": oil_metrics_overall,
            "envelope_1000_2000t": oil_metrics_envelope,
        },
        "sor_derived_check": {
            "note": "SOR = steam_t / oil_model.predict(X); not a separately trained model.",
            "overall": sor_derived_metrics,
        },
        "margin_regressor": {
            "target": MARGIN_TARGET,
            "note": "Gross margin (no opex, no cold baseline). Kept for continuity/reporting; NOT the optimizer objective as of rev 9.",
            "overall": margin_metrics_overall,
            "envelope_1000_2000t": margin_metrics_envelope,
        },
        "margin_incremental_regressor": {
            "target": MARGIN_INCREMENTAL_TARGET,
            "note": "Economics v2 (rev 8/9): incremental over the cold, unstimulated well for the same window; with-opex. Optimizer objective rev 9-12; kept for continuity/reporting, NOT the objective as of rev 13.",
            "overall": margin_incr_metrics_overall,
            "envelope_1000_2000t": margin_incr_metrics_envelope,
        },
        "margin_net_cash_regressor": {
            "target": MARGIN_NET_CASH_TARGET,
            "note": (
                "rev 13 (wave 5): net cash per cycle-day, counterfactual-free "
                "(with opex, no cold-baseline subtraction). This IS "
                "ml/optimize.py's objective as of rev 13 -- comparing it across "
                "float policies never books the cold-well counterfactual switch "
                "(css.cold_counterfactual 'policy': shut in under the three "
                "float policies, pumped floating under 'none') as if it were "
                "part of the recommendation's own gain "
                "(TIER1_PROGRESS_LOG.md section 12.1/12.6)."
            ),
            "overall": margin_net_cash_metrics_overall,
            "envelope_1000_2000t": margin_net_cash_metrics_envelope,
        },
        "float_classifier": {
            "label_definition": f"{FLOAT_LABEL_COL} (twin/generate_data.py: float_forced_pull AND "
                                 "end_rate_over_cutoff >= FLOAT_PREMATURE_RATIO 1.5)",
            "label_note": (
                "rev 13 (TIER1_PROGRESS_LOG.md section 12.12): 'the rods, not the "
                "economics, ended a still-productive cycle' -- the float-onset "
                "pull happened (float_forced_pull) AND the oil rate was still "
                ">= 1.5x the row's own economic cutoff when it did. Supersedes "
                "the rev-12 label (max_floating_index > 0.6) OR (alarm_days > 0), "
                "whose ~95% positive share was too unbalanced to be informative "
                "and which, once the float response became an operating policy, "
                "amounted to penalising the pull rule itself (re-score N7: "
                "'under every policy the pull IS the float response')."
            ),
            "positive_class_share_train": float(y_clf_train.mean()),
            "positive_class_share_test": float(y_clf_test.mean()),
            "auc": float(auc),
            "accuracy": float(acc),
            "n": int(len(y_clf_test)),
        },
    }
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n--- Regressor: oil_total_m3 (log-transformed) ---")
    print(f"  overall            R2={oil_metrics_overall['r2']:.4f}  MAE={oil_metrics_overall['mae']:.2f} m3  (n={oil_metrics_overall['n']})")
    print(f"  1000-2000t envelope R2={oil_metrics_envelope['r2']:.4f}  MAE={oil_metrics_envelope['mae']:.2f} m3  (n={oil_metrics_envelope['n']})")
    print("--- Derived SOR check (steam_t / oil_pred) ---")
    print(f"  overall            R2={sor_derived_metrics['r2']:.4f}  MAE={sor_derived_metrics['mae']:.3f} t/m3")
    print("\n--- Regressor: margin_inr_per_cycle_day (gross) ---")
    print(f"  overall            R2={margin_metrics_overall['r2']:.4f}  MAE={margin_metrics_overall['mae']:.0f} inr/day  (n={margin_metrics_overall['n']})")
    print(f"  1000-2000t envelope R2={margin_metrics_envelope['r2']:.4f}  MAE={margin_metrics_envelope['mae']:.0f} inr/day  (n={margin_metrics_envelope['n']})")
    print("\n--- Regressor: margin_incremental_inr_per_cycle_day (optimizer objective, rev 9) ---")
    print(f"  overall            R2={margin_incr_metrics_overall['r2']:.4f}  MAE={margin_incr_metrics_overall['mae']:.0f} inr/day  (n={margin_incr_metrics_overall['n']})")
    print(f"  1000-2000t envelope R2={margin_incr_metrics_envelope['r2']:.4f}  MAE={margin_incr_metrics_envelope['mae']:.0f} inr/day  (n={margin_incr_metrics_envelope['n']})")
    print("\n--- Regressor: margin_with_opex_inr_per_cycle_day (net cash, optimizer objective, rev 13) ---")
    print(f"  overall            R2={margin_net_cash_metrics_overall['r2']:.4f}  MAE={margin_net_cash_metrics_overall['mae']:.0f} inr/day  (n={margin_net_cash_metrics_overall['n']})")
    print(f"  1000-2000t envelope R2={margin_net_cash_metrics_envelope['r2']:.4f}  MAE={margin_net_cash_metrics_envelope['mae']:.0f} inr/day  (n={margin_net_cash_metrics_envelope['n']})")
    print("\n--- Classifier: float_premature_pull (rev 13 label) ---")
    print(f"  positive share train/test = {y_clf_train.mean():.3f} / {y_clf_test.mean():.3f}")
    print(f"  AUC      = {auc:.4f}")
    print(f"  Accuracy = {acc:.4f}")
    print(f"\nSaved models + metrics to {MODELS_DIR}")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--data",
        default=str(DEFAULT_DATA),
        help="Path to cycles CSV (default: data/synthetic_cycles.csv)",
    )
    args = parser.parse_args()
    train(Path(args.data))


if __name__ == "__main__":
    main()
