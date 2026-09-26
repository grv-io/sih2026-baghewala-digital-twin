# ml/

Surrogate models + Bayesian optimizer over CSS/SRP/policy settings, retrained
on the calibrated twin -- currently **rev 13** (physics wave 5: operating
policy as a control, fair net-cash baseline, smooth inversion, injectivity
gate, three price decks -- see `params/CHANGELOG.md` rev 13 and
`docs/model-improvement/TIER1_PROGRESS_LOG.md` section 12).

## Honest ML role (rev 13 cascade)

**The physics grid (`ml/recommend_physics.py`'s `best_settings_physics_5d`) is
the decision engine. The ML surrogate here is not.** Read section 12 of
TIER1_PROGRESS_LOG.md before quoting anything from this directory as "the
recommendation" -- it isn't; the exhaustive physics grid's canonical point
(1,000 t / soak 10 / 89 kgf/cm2 / 64-in / start 4.5 spm / cutoff 0.60 backstop
/ VFD-hold, +₹15,396/d FY25 net cash) is.

What the surrogate is *for*:
- **Fast what-if / UQ support.** `ml/uq.py` and the dashboard's live sliders
  need a sub-millisecond response; the true twin is ~8 ms/cycle, cheap enough
  for a 1,500-draw UQ bake or a 40,194-point-per-policy exhaustive grid, but
  too slow for an interactive per-keystroke UI. The XGBoost regressors (oil,
  gross margin, incremental margin, net-cash margin) are that fast emulator,
  re-verified against the true twin at every reported point
  (`surrogate_vs_physics_gap`) so no surrogate number is ever presented
  un-checked.
- **A `float_premature_pull` risk surface.** `float_model.joblib` gives a
  continuous probability, across the 7-D space, that "the rods, not the
  economics, ended a still-productive cycle" -- useful for gradient-based
  what-if exploration, informational only (see "Objective" below: it is
  **not** a search constraint as of rev 13).

What it is emphatically **not**: a second optimiser competing with the
physics grid. `ml/optimize.py`'s Bayesian search over the surrogate is kept
(for continuity / a second, faster method to sanity-check against), but its
result is reported *as a surrogate optimum with a stated physics gap*, never
as an alternative recommendation -- see "Optimizer vs physics grid" below.

## What is trained (rev 13)

`ml/train.py` reads `data/synthetic_cycles.csv` (3,000 LHS cycles, seed 42,
from `twin/generate_data.py` against the rev-13 physics -- the LHS now has a
7th, categorical column, the operator's float response `float_policy` in
{pull, vfd_hold, vfd_then_pull}, equal strata) and trains models, all
XGBoost, single 80/20 holdout, seed 42 (**no cross-validation**):

| Model | File | Target | Notes |
|---|---|---|---|
| Oil regressor | `oil_model.joblib` | `log(oil_total_m3)`, inverse-transformed on `predict()` | `steam_t` is a known decision variable, so only the denominator (oil) needs predicting -- SOR is *derived*: `SOR = steam_t / oil_model.predict(X)`. Rev-13 holdout: R2 0.995 overall; the derived-SOR check drops to R2 0.37 (was 0.99 at rev 12) -- a genuine finding, not a bug: the `pull` policy's LHS rows now include a fat right tail (SOR up to ~142, cycles that float almost immediately at high spm/steam corners), and a few of those dominate the derived-SOR variance even though the underlying oil regressor stays accurate (see `metrics.json`). |
| Margin regressor | `margin_model.joblib` | `margin_inr_per_cycle_day` (gross) | Kept for continuity/reporting; **not** the optimizer objective. |
| Incremental-margin regressor | `margin_incremental_model.joblib` | `margin_incremental_inr_per_cycle_day` | Economics v2 basis (over the cold, unstimulated well). Optimizer objective rev 9-12; kept for continuity, **not** the rev-13 objective (see below). In this LHS design the cold well is shut in at every sampled point (`css.cold_counterfactual` "policy" default, base 45% formation water cut shuts it in under all three sampled policies -- TIER1 section 12.4), so `margin_incremental_inr_per_cycle_day` == `margin_with_opex_inr_per_cycle_day` EXACTLY for every training row; the two regressors' metrics are identical for that reason, not a bug. |
| **Net-cash regressor** | `margin_net_cash_model.joblib` | `margin_with_opex_inr_per_cycle_day` | **rev 13: this is the optimizer's objective.** Counterfactual-free (no cold-baseline subtraction), so it never books a float-policy switch's cold-well counterfactual change as if it were the recommendation's own gain (see "Objective" below). |
| Floating-risk classifier | `float_model.joblib` | `float_premature_pull` (twin/generate_data.py: the float-onset pull happened AND the oil rate was still >= 1.5x the cutoff when it did -- "the rods, not the economics, ended a still-productive cycle") | **Supersedes the rev-12 label** `(max_floating_index > 0.6) OR (alarm_days > 0)`, whose ~95% positive share was uninformative and, once float response became a policy, amounted to penalising the operating rule itself (external re-score finding N7). This label sits at **~41% positive** (train 0.415 / test 0.413 on the rev-13 dataset), inside the healthy 10-60% band. AUC 0.999 / accuracy 0.982. |

`sor_model.joblib` (the pre-rev5 model) is deleted by `train.py` on retrain --
SOR is now a derived quantity, not a separately trained model.

Metrics (`ml/models/metrics.json`) report R2/MAE for every regressor
**overall** and **inside the 1,000-2,000 t steam envelope** (the margin/
cycle-day plateau documented in `TIER1_PROGRESS_LOG.md` section 4.4), plus
AUC/accuracy and the positive-class share for the classifier, and
`physics_rev`/`trained_on` provenance fields.

## Objective, features and baselines (rev 13)

`ml/optimize.py`'s `best_settings(params)` **maximises predicted
margin_with_opex_inr_per_cycle_day** (net cash per cycle-day,
counterfactual-free), subject to a **hard injectivity gate**: the candidate's
sandface pressure at its own `p_wellhead_kgf_cm2` must clear
`steam.min_injection_margin_kPa` (400 by default) over the reservoir's
pre-cycle pressure -- computed directly from the steam-state physics
(`twin.thermal.steam_state`, no cycle simulation needed), not gated on a
surrogate.

This is a rev-13 change of objective (was: `margin_incremental_inr_per_
cycle_day`, Economics v2, rev 9-12) and of constraint (was: a soft penalty if
predicted P(float) >= 0.3, rev 9-12, now DROPPED). Both changes follow from
the same fact: the operator's float response is now a control
(`css.float_policy`), so (a) the incremental metric's cold-well counterfactual
itself depends on the policy (shut in under the three float policies, pumped
floating under "none" -- TIER1 section 12.1), so comparing it ACROSS policies
would book that counterfactual switch as if it were the recommendation's own
gain -- net cash has no such term; and (b) under every policy the pull IS that
policy's float response, so penalising "risk of floating" fights the physics
rather than pricing a real cost (re-score N7) -- the injectivity gate is a
real, physical constraint (steam cannot enter the formation below it) and
replaces it.

**Features (7, rev 13):** `steam_t`, `soak_days`, `cutoff_m3d`, `spm`
(restricted to `params["srp"]["spm_practice_band"]`), `p_wellhead_kgf_cm2`
(`params["steam"]["P_wellhead_range_kgf_cm2"]`, 85-97), `stroke_in` (the
discrete API sizes in `params["srp"]["stroke_in_options"]`, searched as a
`skopt.space.Categorical`), and `float_policy` (pull / vfd_hold /
vfd_then_pull, also a `Categorical` -- "none" is never in the LHS, so the
surrogate never saw it and it is excluded from the search). One-hot encoded
to 9 model columns (`policy_pull`/`policy_vfd_hold`/`policy_vfd_then_pull`,
all three kept). `soak_days` has no interior optimum (TIER1 section 4.5/11.9/
12.5) and is typically held fixed via `fixed={"soak_days": 10}`. Search:
`skopt.gp_minimize`, 60 calls / 15 initial points / seed 42.

### Optimizer vs physics grid (rev 13 cascade finding)

Running `best_settings(params, fixed={"soak_days": 10})` lands the surrogate
optimum at **500 t / 10 d / cutoff 0.60 m3/d / 3 spm / 97 kgf/cm2 / 74 in /
vfd_hold** -- policy, cutoff and stroke roughly agree with the physics grid's
canonical point in kind (VFD-hold, backstop cutoff, a short-ish stroke), but
**steam and pressure both pin to a search-box edge** (steam at its 500 t
floor, pressure at the 97 kgf/cm2 ceiling) rather than the grid's interior
1,000 t / 89 kgf/cm2. Physics-verified net cash at the surrogate optimum:
**+₹11,635/d FY25**, against the physics grid's **+₹15,396/d** -- a **~24%
shortfall** (the surrogate/physics gap on the *predicted* net cash at its own
optimum is **+28%**: surrogate predicts ₹14,928/d, physics delivers
₹11,635/d). Expected: 60 Bayesian-search calls over a 7-D mixed continuous/
discrete/categorical space is a much smaller budget than the grid's
40,194-points-per-policy exhaustive search, so the steam/pressure dimensions
(the two the grid itself finds are the weakest levers economically -- TIER1
section 12.5/12.9) are the ones the surrogate under-resolves. **The canonical
recommendation stays the physics-grid point; this surrogate result is
reported as a cross-check, not an alternative.**

The optimum and **two baselines** are all re-run through the true physics twin
(`twin.cycle.simulate_css_cycle` + `summary`), not just the surrogate:
- **(a) param-midpoint** -- midpoint of each search range (spm midpoint of the
  practice band; `stroke_in`'s midpoint is snapped to the nearest API size).
- **(b) published-practice** -- derived from the BGW-8 first-CSS-cycle job
  (`docs/research/baghewala_facts.md` section 4): ~1,300 t steam, 10 d soak,
  cutoff at the params-range midpoint (not published), 5 spm, 91 kgf/cm2 /
  86 in (the CONFIRMED wellhead mid and the assumed-typical unit). Explicitly
  labelled as one documented first-cycle job, **not** OIL's current operating
  practice.

The return dict reports, for the optimum and both baselines: settings, SOR,
oil, cycle days, margin/day, max FI, alarm days, steam cost (₹), CO2 (t), what
ended the produce phase (`produce_end_reason`), and the % change in SOR and
margin/day of the optimum vs each baseline. It also reports which search
variables (if any) are pinned to a bound, and the surrogate-vs-physics gap at
the optimum.

## Retrain on real data
Once `twin/generate_data.py` has produced `data/synthetic_cycles.csv`:
```
python ml/train.py --data data/synthetic_cycles.csv
python ml/optimize.py --params params/field_params.json
```
`train.py` defaults `--data` to `data/synthetic_cycles.csv` and `optimize.py` defaults
`--params` to `params/field_params.json`, so once those real files exist you can just
run both scripts with no arguments.

## File map
- `train.py` — trains `oil_model.joblib`, `margin_model.joblib`,
  `margin_incremental_model.joblib`, `margin_net_cash_model.joblib`,
  `float_model.joblib`; 80/20 split, seed 42; writes `models/metrics.json`.
- `optimize.py` — `best_settings(params)`: skopt `gp_minimize` maximising
  predicted net-cash margin/cycle-day, subject to a hard injectivity gate;
  spm restricted to the practice band, float_policy restricted to
  {pull, vfd_hold, vfd_then_pull}; physics-verifies the optimum and both
  baselines; also a CLI printing JSON.
- `uq.py` — paired Monte Carlo uncertainty quantification (below); writes
  `models/uq_summary.json` and `models/uq_samples.csv`.
- `decompose.py` — Shapley/OAT gain decomposition of the canonical
  recommendation vs baseline (b), under every float policy and price deck;
  writes `models/gain_decomposition.json`.
- `recommend_physics.py` — `best_settings_physics(params, fixed=...)` (3-D
  grid, no policy dimension) and `best_settings_physics_5d(params,
  policies=...)` (the 6-lever x policy exhaustive grid -- the canonical
  decision engine, see "Honest ML role" above): both grid-search directly on
  `twin.cycle.simulate_css_cycle` + `summary`, no ML surrogate; used to
  re-recommend after a recalibration (below).
- `models/` — `oil_model.joblib`, `margin_model.joblib`,
  `margin_incremental_model.joblib`, `margin_net_cash_model.joblib`,
  `float_model.joblib`, `metrics.json`, `uq_summary.json`, `uq_samples.csv`,
  `gain_decomposition.json`, `dyno_cards.json`, `dyno_clf.joblib`,
  `dyno_clf_metrics.json`, `field_schedule_demo.json`,
  `calibration_demo_report.json` (the pseudo-real demo report),
  `calibrated_params.json` and `calibration_report.json` (CLI output, not
  committed by default).
- `../twin/calibrate.py` — `fit()`/`apply()`, the field-data recalibration
  loop (below); `../twin/generate_pseudo_real.py` generates the synthetic
  demo dataset and report.

## Uncertainty quantification (`ml/uq.py`, 26 Sep 2026; rev 13 wave-5 bake 27 Sep)

**What.** A paired Monte Carlo sweep over the model's 21 UNCERTAIN inputs
(below), run through the **true physics twin**
(`twin.cycle.simulate_css_cycle` + `summary`, not the surrogate -- a cycle is
~13 ms, so 1,500 draws x 9 points x 3 decks is a few minutes), at fixed
set-point/policy combinations, over **three price decks** (rev 13: FY25
realisation ~Rs5,992/bbl, the FY26 $65/bbl planning floor ~Rs4,840/bbl, and
FY25 net of royalty + OID cess ~Rs3,600/bbl -- each deck's own +/-15%
oil-price band centred on its own base):

| Point | Settings | Policy |
|---|---|---|
| `reference` | 1,500 t / 7 d / 1.2 m3/d / 5 spm / 86 in / 91 kgf/cm2 | params default |
| `baseline_b` | 1,300 t / 10 d / 1.3 m3/d / 5 spm / 86 in / 91 kgf/cm2 | VFD-hold |
| **`recommended`** | 1,000 t / 10 d / 0.60 m3/d / 4.5 spm / 64 in / 89 kgf/cm2 | **VFD-hold (canonical)** |
| `conservative` | same as `recommended` | VFD holds/pulls at FI 0.5 (not 0.6) |
| `baseline_b__pull` | same as `baseline_b` | pull (rev-12 operation) |
| `recommended__pull` / `baseline_b__none` / `recommended__none` / `recommended_rev12` | same-policy / historical comparison points | pull / none / none / pull |

**Paired** means every draw samples ONE joint realisation of the uncertain
inputs and runs every point through that same realisation (one deep-copied
`params` dict per draw; only the set-point/policy differ between twin calls).
That is what makes "P(recommended net cash/day > baseline net cash/day)" a
meaningful paired probability -- it isolates the effect of the SET-POINT/
POLICY choice, holding the shared physics/economics judgement calls fixed per
draw, rather than comparing two independently-noisy distributions.

**Money metric (rev 13): net cash per cycle-day**
(`margin_with_opex_inr_per_cycle_day`, counterfactual-free) for every paired
"beats the baseline" comparison -- equal to the incremental-margin
difference whenever both sides share one float policy, and still correct
when they don't (the incremental metric's cold-baseline subtraction itself
changes with the policy under `css.cold_counterfactual` "policy", so
comparing IT across policies would book that switch as if it were the
recommendation's own gain -- TIER1 section 12.1/12.6). The SAME-POLICY
comparison (`recommended` vs `baseline_b`, both VFD-hold) is the one
reported as "the gain"; `P_gt_baseline_same_policy` and
`gain_vs_baseline_bands` carry it per policy.

**Uncertain inputs (21, rev 13):** the rev-9/10/11/12 fourteen (water cut/
formation water cut, thickness, diesel discount, oil price, mu_ref, srp
geometry scale, opex/day, s_cold, K_VISC, pressure-boost, mu_anchor, fixed
cost, P_current, inversion water cut) plus condensate recovery and emulsion
phi* (rev 11/12), plus five rev-13 additions: `emulsion_mu_r_max` U[5,20],
`css.fi_alarm_days` U[1,14], `emulsion_inversion_band_wc` U[0.05,0.10],
`flowback_mobility_ratio` DISCRETE {1,3,10}, `cold_counterfactual` DISCRETE
{policy, pumpable} (50/50). See `ml/uq.py`'s `build_uncertain_inputs()`
docstrings for the exact citation/source on each.

**Output** (`ml/models/uq_summary.json`, primary = FY25 deck, every deck
nested under `decks.<name>`): per point, p10/p50/p90 of every `METRICS`
entry (SOR, oil, net cash, incremental margin, CO2, max FI, injectivity,
etc.); paired probabilities `P_gt_baseline_same_policy` (per policy),
`P_recommended_gt_baseline_if_baseline_pulls`, `P_recommended_SOR_lt_
baseline`, `P_injection_ok`, `P_margin_positive`; the rev-13
**`P_incremental_positive_by_counterfactual`** breakdown (policy / pumpable
read off the sampled 50/50 draws, `shut_in` from a dedicated paired
supplementary pass forcing it every draw) at the 5 focus points (reference,
baseline_b, recommended, conservative, baseline_b__pull); an OAT tornado and
an MC-correlation tornado on the recommendation's net cash/day; plus
`ml/models/uq_samples.csv` (FY25 deck draws only, capped under 2 MB).

**As of the rev-13 bake** (1,500 draws, seed 42, all 3 decks;
`ml/models/uq_summary.json` 219 KB, `ml/models/uq_samples.csv` 929 KB, FY25
deck draws only): `P(injectable) = 1.000` at every point in every deck (the
89 kgf/cm2 canonical clears the gate everywhere in the box). Same-policy
`P(rec > base)`: **vfd_hold 0.965 / 0.992 / 0.999** (FY25 / $65 / levies),
pull 0.953-1.000, but **none only 0.16-0.25** (the point estimate's −₹3.9k/d
against a float-safe baseline is the median of a wide, mostly-negative
distribution, not a fluke -- TIER1 section 12.6). VFD-hold gain (net cash,
canonical vs baseline (b), same policy) p10/p50/p90: **+₹2,175/+12,101/
+161,014** FY25 (+₹3,597/+13,390/+158,528 $65; +₹5,256/+14,805/+155,230
levies) -- the point estimate (+₹3,332) sits toward the LOW side of a
right-skewed distribution whose p90 tail is the baseline's own fragility
(a cycle that ends within days of its peak). `P(rec net cash/day > base net
cash/day, IF base pulls)` = 0.991/0.999/1.000. The per-counterfactual
`P(incremental margin/day > 0)` breakdown at the recommendation: policy 0.034
/ pumpable 0.003 / shut_in 0.034 (policy and shut_in coincide almost exactly,
confirming TIER1 12.4's "policy IS shut_in over most of the box"; pumpable's
credited cold cash pulls the absolute incremental figure down, so its
positive share is lower). Top tornado drivers on the recommendation's
incremental margin: `mu_ref_cP`, `formation_water_cut`,
`condensate_recovery_frac` (OAT); `condensate_recovery_frac`,
`formation_water_cut`, `flowback_mobility_ratio` (MC correlation).

**Rerun:**
```
python ml/uq.py [--draws 1500] [--seed 42] [--params params/field_params.json]
                [--out-json ml/models/uq_summary.json] [--out-csv ml/models/uq_samples.csv]
                [--deck fy25_realisation|fy26_floor|fy25_net_of_levies]
```

## Calibrate from field data (`twin/calibrate.py`, 26 Sep 2026; rev 12 cascade update 27 Sep, re-run under rev 13)

> The formation-water-cut/AOF/thickness identifiability story below is
> unchanged by rev 13 (wave 5): this demo's grid (`recommend_physics.
> best_settings_physics`, 3-D) does not search the policy/stroke/pressure
> levers, so it runs at the params' own default `css.float_policy` ("pull").
> Only the numbers were regenerated against the rev-13 physics (smooth
> inversion, Pal-Rhodes cap sampling, etc.) -- the recovered-vs-truth
> percentages move by under 1 point.

**What.** `ml/uq.py`'s own tornado ranking names the twin's biggest uncertain
constants: `thermal.BL_DELTA_FACTOR` (0.5, sourced -- not fitted by default),
`fluid.formation_water_cut` (0.45, no field datum -- rev 11/12: under the
shipped `fluid.water_cut_model = "state"`, this native reservoir-liquid cut
is the free parameter, not the legacy constant `fluid.water_cut`),
`reservoir.thickness_m` (12 m, "NOT FOUND for Baghewala" per
`params/CHANGELOG.md`) and `ipr.AOF_REF_M3D` (0.56 as of the rev-12 peak-band
retune, hand-tuned against one published uplift ratio). Oil India has
per-well cycle records (the PS says so). `twin/calibrate.py` is the loop
that fits those constants to observed cycles and hands back a recalibrated
params tree -- turning the simulator into a twin.
`twin.calibrate.default_free(params)` picks the free set that matches the
params tree's own water-cut model: `("formation_water_cut", "aof_ref_m3d",
"thickness_m")` under "state" (the shipped default), or the legacy
`("water_cut", "aof_ref_m3d", "thickness_m")` under "constant". `s_cold`
(cold-well damage skin) is an additional opt-in free parameter (bounds
0-8), off by default -- free it only with a peak rate AND a cold (pre-CSS)
rate per well, since it trades off against `aof_ref_m3d`.

**Observed-cycles CSV schema** (one row per completed CSS cycle; see
`twin/calibrate.py`'s module docstring for the full field-by-field spec and
`data/templates/observed_cycles_template.csv` for a filled-in example):

| Column | Required | Meaning |
|---|---|---|
| `well_id` | yes | reporting only |
| `steam_t`, `soak_days`, `spm` | yes | the cycle's set-points |
| `oil_m3` | yes | total oil produced over the produce phase |
| `produce_days` | yes | length of the produce phase |
| `cutoff_m3d` | no | defaults to the params-range midpoint if absent |
| `peak_oil_m3d` | no | used as a third residual quantity when present |
| `sor` | no | not used by the fit (implied by steam_t/oil_m3); carried into the residual table for a sanity check |

**`fit(observed_df, params, free=(...), bounds=..., weights=...)`** runs
`scipy.optimize.least_squares` (bounded, deterministic -- `method="trf"`, no
randomness) minimising normalised residuals of `oil_m3`, `produce_days` (and
`peak_oil_m3d` when present) between the observations and
`twin.cycle.simulate_css_cycle` run at the same set-points. Each residual
evaluation is a handful of cycle simulations (~1-20 ms each), so a fit over a
few dozen cycles is a fast, interactive operation (the 8-cycle demo below
fits in well under a second). Returns fitted values, the bounds used, a
per-cycle residual table (obs vs sim), RMSE per quantity, and an
**identifiability report** (below). `apply(params, fitted)` writes the fitted
values into a deep copy of `params` at the right keys
(`fluid.formation_water_cut` / `fluid.water_cut` depending on the model,
`ipr.aof_ref_m3d`, `reservoir.thickness_m`, and `thermal.bl_delta_factor` /
`ipr.s_cold` if opted in) so `simulate_css_cycle` picks them up.

> **Rev-12 cascade update (27 Sep 2026):** `twin/generate_pseudo_real.py` now
> generates the pseudo-real demo against CURRENT (rev-12) physics -- no more
> legacy rev-10 switches -- so `default_free` resolves to
> `("formation_water_cut", "aof_ref_m3d", "thickness_m")`. `bl_delta_factor`
> is sourced physics (0.5, CHANGELOG rev 7) and is off by default -- still
> accepted in `free` to test a hypothesis (against a `water_cut_model =
> "constant"` params tree, where the bl / water_cut coupling below applies;
> it does not arise under the state model, since the bl term there trades off
> against `formation_water_cut` + `condensate_recovery_frac` jointly, not a
> single constant). The bullet list and the recovered-vs-truth table below
> are the CURRENT (rev-12) results.

CLI:
```
python -m twin.calibrate observed.csv --out ml/models/calibrated_params.json --report ml/models/calibration_report.json
```

**What is identifiable and what isn't.** Two override points were added so
these constants are settable per-run without editing `twin/*.py`'s module
defaults: `twin.thermal.bl_delta_factor(params)` (already existed for
`ml/uq.py`) and the new `twin.ipr.aof_ref_m3d(params)`, both reading an
optional `params["thermal"]`/`params["ipr"]` block and falling back to the
module constant. But not everything the physics is sensitive to is
separable from oil/days data alone:

- **`formation_water_cut`** (bl fixed): recovered at 0.360 against a truth of
  0.380 (-5.2 %) on the rev-12 committed seed (42) -- weaker than the old
  rev-10 constant-`water_cut` case (which was identified almost alone; see
  history below), since under the state model it now trades off against
  `aof_ref_m3d`/`thickness_m` too (no multi-seed sweep re-run this pass).
- **`aof_ref_m3d`**: 0.644 against 0.650 (-0.9 %).
- **`thickness_m` is the weakest-identified** (13.37 against 15.0, -10.9 %).
  It trades off against `aof_ref_m3d`: both scale what the heated zone
  delivers.
- The Jacobian-implied correlations stay high between all three free
  parameters -- so `correlated_pairs` flags them -- yet the recovery above is
  still directionally sound. Read the correlation as "the data move these
  together", not as "unrecoverable".
- **If `bl_delta_factor` is opted back in against a `water_cut_model =
  "constant"` params tree**, it and `water_cut` trade off almost one-for-one
  (Jacobian r ~ -1.0); `known_couplings` then reports
  `bl_delta_factor / (1 - water_cut)`. That is why it is off by default (and
  why it does not arise under the shipped state model -- see
  `tests/test_calibrate.py::test_bl_delta_opt_in_still_flags_the_coupling`).
- `fit()`'s `identifiability` dict also flags any fitted value sitting at (or
  within 1%) of its bound -- a sign the data wants to go further than the
  bound allows.

**Pseudo-real demo** (`python -m twin.generate_pseudo_real`,
`data/external/pseudo_real_cycles.csv` -- **SYNTHETIC, NOT field data**, see
`data/external/SOURCE.md`): 8 cycles across 3 fictional wells BGW-D1..D3,
generated by running the CURRENT (rev-12) twin against a HIDDEN true params
set (`formation_water_cut=0.38, thickness_m=15, aof_ref_m3d=0.65`,
`bl_delta_factor=0.5` -- the sourced value, not hidden -- vs the rev-12
defaults' 0.45/12/0.56), seed-42 +/-8% multiplicative noise added to
oil/days/peak. Recovered vs truth (report:
`ml/models/calibration_demo_report.json`, regenerated for the rev-12
cascade):

| Parameter | Truth | Fitted | Error | Identifiability |
|---|---|---|---|---|
| `formation_water_cut` | 0.380 | 0.360 | -5.2% | trades off against aof_ref_m3d/thickness_m under the state model |
| `aof_ref_m3d` | 0.650 | 0.644 | -0.9% | recovers well |
| `thickness_m` | 15.0 | 13.37 | -10.9% | weakest; trades off against aof_ref_m3d |
| `bl_delta_factor` | 0.5 | 0.5 | -- | fixed (sourced), not fitted |

(Historical rev-10/11 result, constant water-cut model, bl fixed: water_cut
0.770-0.790 vs truth 0.78 over 5 noise seeds -- identified almost alone,
since it was the SOLE driver of both the produced-heat rate and the pump's
oil capacity under that model. The rev-12 state model splits that role across
`formation_water_cut` + `condensate_recovery_frac`, so the single fitted
`formation_water_cut` is not as tightly pinned by oil/days data alone.)

RMSE on the fit: see `ml/models/calibration_demo_report.json`'s `rmse` key
(regenerated with the rest of this cascade; inside the +/-8% noise floor on
this seed).

**Re-recommend without a stale surrogate (`ml/recommend_physics.py`).**
`ml.optimize.best_settings()`'s XGBoost surrogates were trained on data
generated from the DEFAULT physics -- once a params tree is recalibrated,
those surrogates silently mismatch it. `recommend_physics.best_settings_
physics(params, fixed={"soak_days": 10})` grid-searches steam_t x cutoff_m3d
x spm (15x15x7 = 1,575 points, ~10s) directly against
`twin.cycle.simulate_css_cycle` + `summary` -- no surrogate, ever. Feasibility
uses `max_floating_index <= 0.6` (the same raw threshold the ML classifier's
own training label is built from), since there is no trained-classifier
probability to threshold against a recalibrated params tree. `soak_days` is
held fixed, matching `TIER1_PROGRESS_LOG.md` section 5b (no interior optimum
in soak). Returns the same result shape as `best_settings()` (physics-
verified optimum, both baselines, pinned variables) minus the
surrogate-specific fields.

**Before/after calibration, physics-verified** (pseudo-real demo, soak fixed
at 10 d; rev-13 cascade regeneration -- `recommend_physics.best_settings_
physics` (3-D grid, no policy/stroke/pressure search -- this demo predates
those levers) runs at the params' own default `css.float_policy` ("pull") --
objective is the INCREMENTAL margin per cycle-day):

| | steam_t | cutoff_m3d | spm | SOR gross / incr. | incr. margin ₹/cycle-day (gross) |
|---|---|---|---|---|---|
| Before calibration (default params) | 857 | 0.60 | 3.0 | 3.31 / 3.31 | +7,868 (13,747) |
| After calibration (pseudo-real fit applied) | 1,214 | 0.60 | 3.0 | 2.71 / 2.71 | +23,124 (29,138) |

The pseudo-real truth (a lower formation water cut, thicker pay and a higher
AOF than the shipped defaults) makes the well substantially more productive
per tonne of steam, so the re-recommendation moves to nearly double the
steam slug and the incremental margin nearly triples -- illustrating why
re-recommending against a stale surrogate/params tree after a recalibration
would be misleading. Both points are float-onset-rule cycles at the 4-D
grid's own cutoff/spm floor (`recommend_physics.best_settings_physics`
does not yet search the stroke/pressure controls -- see "Re-recommend"
above); rerun `python -m twin.generate_pseudo_real` to reproduce.

**API:** `POST /calibrate` (multipart CSV or `{"rows": [...]}` JSON; runs
fit + apply + physics re-recommendation, stateless -- never writes to
`params/field_params.json`) and `GET /calibrate/demo` (runs the same loop on
the pseudo-real dataset, returns fitted params vs hidden truth, and the
before/after recommendation). See `api/main.py`.

**Rerun:**
```
python -m twin.generate_pseudo_real     # regenerates the demo dataset + report, deterministic (seed 42)
python -m twin.calibrate <observed.csv> --out ml/models/calibrated_params.json --report ml/models/calibration_report.json
python -m ml.recommend_physics --params ml/models/calibrated_params.json --soak-days 10
```

## Measured dynamometer-card classifier (`ml/dyno_classifier.py`, 27 Sep 2026)

**What.** PS SIH26120 asks the twin to ingest a MEASURED surface dynamometer card
(position vs. load) and return a fault read. Oil India has not handed over a real
card, so this is trained entirely on SYNTHETIC cards swept from
`twin.dyno.compute_cards()` (the same physics-based card computed live for the
console's "Dynamometer card (computed)" panel — `docs/model-improvement/
DYNO_CARD_MODEL.md` has the fault signatures) — never on field data. A
`RandomForestClassifier` predicts one of `full_pump`, `fluid_pound`,
`gas_interference`, `heavy_oil_viscous`, `rod_float` from shape features of the
SURFACE card alone (what a beam-inclinometer dynamometer actually records); the
downhole/pump card `compute_cards()` also returns is used only to derive each
training row's ground truth (`card_type`), never fed to the model.

> **Domain-shift caveat (repeated in every classification result as
> `model_caveat`).** This classifier has NEVER seen a real dynamometer card. It
> is trained on a `[TYPICAL]` 1" x 7/8" rod string over 1,150 m, a crank-pitman
> surface unit and a single viscous-drag law (`twin/dyno.py`'s own docstring,
> `DYNO_CARD_MODEL.md` §6 "Known limits") — a real Baghewala string, unit
> geometry and valve wear will differ. Every prediction is a first read to
> confirm with a pump specialist, not a diagnosis — re-fit against the first
> real cards Oil India shares (`python -m ml.dyno_classifier --train`), the same
> idea as `twin/calibrate.py`'s field recalibration of the reservoir model.

**Training set.** `generate_dataset()` stratified-samples 3,200 cards (seed 42)
across spm 2–12, oil viscosity 5–15,000 cP (log-spaced), pump fillage 0.4–1.0,
water cut 0.6–0.95, the gas-interference option, and small rod-string geometry
perturbations (stroke ±10%, depth ±15%) — five strata (general / low-μ /
gas / viscous / rod-float corner) so every label is well represented, since
`rod_float` and `gas_interference` live in corners of the box a plain uniform
draw under-covers. Each card is then corrupted to imitate a real card reader:
1–3% multiplicative load noise, 0.5%-of-stroke position noise, and an irregular
(jittered-index) resampling down to ~100 points, rather than the simulator's
clean 200-point crank-angle grid.

**Features** (`card_features()`, `FEATURE_NAMES`, 143 total — see the module
docstring for the full derivation) computed AFTER converting to canonical units
(m, kN) and normalising the card's own bounding box to `[0,1]x[0,1]`, so they
depend on card SHAPE, not a particular well's absolute stroke/load scale:
- **128** — normalised load vs. normalised position, resampled to 64 points on
  each of the up-stroke and down-stroke branches (split at the position
  argmax/argmin, mirroring `twin.dyno._branches`'s own convention).
- **area_frac, aspect_ratio_kN_per_m** — loop area / bounding-box area, and load
  range / position range.
- **min_over_max, mean_over_max, min_over_mean** — load ratios (scale-free).
- **downstroke_slope_mid** — linear-fit slope over the middle 25–75% of the
  normalised downstroke (inertia peaks at the stroke ends, drag at mid-stroke).
- **zero_load_frac** — fraction of the loop at/below 5% of the load range (the
  rod-float / carrier-separation tell).
- **fourier_mag_1..8** — magnitudes of the first 8 non-DC Fourier coefficients
  of the closed contour, resampled to a uniform ARC-LENGTH parametrisation
  (robust to the irregular sampling above).

**Model and metrics** (`ml/models/dyno_clf.joblib`, `ml/models/
dyno_clf_metrics.json`). `RandomForestClassifier(n_estimators=400,
class_weight="balanced_subsample")`, single 80/20 stratified holdout, seed 42
(deterministic — re-running `--train` with the same seed reproduces the same
accuracy/confusion matrix). As of the current retrain (3,200 cards, 0 generation
failures):

| Metric | Value |
|---|---|
| Accuracy (hold-out, n=640) | **0.9484** |
| F1 — full_pump | 0.863 |
| F1 — fluid_pound | 0.939 |
| F1 — gas_interference | 0.899 |
| F1 — heavy_oil_viscous | 0.956 |
| F1 — rod_float | 1.000 |

All 8 baked cards in `ml/models/dyno_cards.json` (both scenarios' `early_hot`/
`mid`/`vfd_hold_day`/`stress_12spm` -- rev 13: `vfd_hold_day` replaces the
rev-12 `float_onset` pick, now that the baseline and recommendation scenarios
both run VFD-hold, TIER1 section 12.3/12.5) classify as their own
physics-derived `card_type` (`tests/test_dyno_classifier.py`).

**`classify_card(position, load, units=None)`** → `{card_type, probabilities,
fillage_est, peak_kN, min_kN, sentence_en, sentence_hi, quality_flags,
model_caveat}`. `units` is `None` (auto-detect both axes by magnitude — a
position range over 12 "metres" is almost certainly inches, a load whose max
magnitude is under 40 "kN" is almost certainly klbf), a `"position,load"` string
(e.g. `"in,klbf"`), or a `{"position":.., "load":..}` dict. `fillage_est` is a
rule (not a regression): downstroke travel, from the top of the stroke, before
the normalised load first drops below its own mid-range — the same idea as
`twin.dyno.classify_card`'s `card_fill`, using a relative threshold since a
measured card carries no `Fo`/`W_rf` physics reference. Raises `ValueError` on
malformed input (mismatched lengths, < 6 points, NaN/inf, a zero-range axis).
`parse_card_table(text)` parses a CSV (with header, position_m/in +
load_kN/klbf column names recognised) or a headerless pasted two-column table
(comma/tab/whitespace-separated).

**API.** `POST /api/dyno/classify` — JSON `{"position":[...], "load":[...],
"units"?: ...}` or a multipart CSV upload (field `file`) — returns the
`classify_card` dict. `GET /api/dyno/classify/demo` — runs it on the 4
`baseline`-scenario baked cards, returns predicted vs. true `card_type` for
each. See `api/routers/dyno.py`.

**Template.** `data/templates/dyno_card_template.csv` — 21 rows (a closed loop)
from a baked `fluid_pound` card, header `position_m,load_kN`;
`position_in,load_klbf` is accepted too (auto-detected by header name or, if
absent, by magnitude).

**Retrain:**
```
python -m ml.dyno_classifier --train                 # regenerate the synthetic set + retrain (seed 42, ~1 min)
python -m ml.dyno_classifier --demo                   # classify the 8 baked cards vs. their true label
```
## Field-level steam scheduling (`ml/schedule.py`, 27 Sep 2026)

**Why.** PS SIH26120 asks for optimisation across the FIELD, not one well:
Baghewala runs ~33 operational wells (`docs/research/baghewala_facts.md`
section 5) off **one** steam generator (~3.1 t/h ~= 74 t/d -- the same rate
already used as `steam.injection_rate_tpd`; 19 CSS jobs in FY2025-26), with
cycles 6-18 months apart per well. `ml/recommend_physics.py` already finds
the physics-optimal set-points for ONE well; this module answers the actual
field decision OIL makes -- **which well gets steam next, how much, and
when** -- to maximise the field's total incremental margin per day under
that one-generator constraint.

**Model.**
1. **Per-well candidate job.** For each well, `well_candidate_job()` builds a
   per-well params tree (`build_well_params()` overrides
   `reservoir.thickness_m`, `fluid.mu_ref_cP`, `fluid.water_cut`,
   `ipr.aof_ref_m3d`) and calls `recommend_physics.best_settings_physics()`
   UNMODIFIED (`soak_days` fixed at 10, FI <= 0.6 feasibility) with a reduced
   6x6x4 = 144-point grid (vs that module's own 1,575-pt default -- keeps a
   12-well run inside a 60 s CLI budget; ~1.9 s/well measured). The result is
   a fixed job: `{well_id, steam_t, cutoff_m3d, spm, margin_incremental_inr_
   per_cycle_day, cycle_days, steam_days = steam_t / 74, duration_days =
   steam_days + 1-day move, earliest_start_day = max(0, 180 - days_since_
   last_cycle)}`.
2. **Scheduling the generator.** Jobs are sequential on the ONE generator
   (`duration_days` occupies it; the rest of the well's `cycle_days` -- soak
   + produce -- does not). Three policies, all respecting the >=180-day
   re-cycle gate and a 365-day horizon:
   - **naive** (counterfactual): every well gets the SAME fixed 1,500 t
     (soak 10, cutoff at the range midpoint, spm 5.0 -- no per-well tuning),
     visited worst-cold-rate-first.
   - **greedy**: per-well optimum jobs, inserted in descending
     Rs/generator-day (`margin_incremental_inr_total / duration_days`) order.
     Fast, not guaranteed optimal.
   - **exact**: bitmask enumeration over all 2^n_wells subsets (n=12 ->
     4,096 subsets, microseconds total -- no MILP solver needed; pulp/
     OR-Tools are not installed). For a FIXED subset, jobs are placed in
     **Earliest-Release-Date (ERD)** order -- provably makespan-optimal for
     1|r_j|C_max (single machine, release dates, no preemption: an
     adjacent-swap exchange argument shows any other order can only tie or
     worsen the last job's completion time). Bitmask x per-subset ERD is
     therefore a jointly optimal search over (subset, order), not a
     heuristic.

**Demo result, rev-13 physics** (`data/external/field_wells_synthetic.csv`, 12
SYNTHETIC wells, seed 42, every well operated **VFD-hold**
(`build_well_params` sets `css.float_policy = "vfd_hold"` field-wide, the
rev-13 recommended policy -- TIER1 section 12.2/12.5); `python -m ml.schedule
--wells data/external/field_wells_synthetic.csv --out
ml/models/field_schedule_demo.json`):

| Policy | Wells served / deferred | Generator util. | Field incr. ₹/day | Field incr. ₹ (1 yr) | Steam / CO₂ |
|---|---|---|---|---|---|
| naive (same 1,500 t / 86 in / 5 spm, worst-first) | 12 / 0 | 69.9% | **+₹72,320** | **+₹26,396,705** | 18,000 t / 4,028 t |
| greedy (per-well optimum jobs, value-density order) | 12 / 0 | 66.2% | +₹104,403 | +₹38,107,103 | 17,000 t / 3,804 t |
| **exact** (bitmask subsets x ERD) | 10 / 2 | 54.6% | **+₹109,799** | **+₹40,076,550** | 14,000 t / 3,133 t |

**rev-13 cascade finding: VFD-hold turns the naive counterfactual from a
field-wide LOSS (rev 12: −₹13,304/d) into a modest GAIN (+₹72,320/d).**
The rev-12 finding was that a fixed-job "no per-well tuning" counterfactual
floated the rods late in most wells' cycles under the pull rule, and floating
rods (the pull-onset produce-end rule) made it lose money outright. Once
every well slows its unit instead of pulling on the float alarm (the SAME
lesson as the single-well analysis, TIER1 section 12.1/12.6: "the policy
lever alone is 68% of the canonical-vs-pulling-baseline gain"), the naive
schedule is merely sub-optimal, not negative. Per-well physics optimisation
(greedy) still adds +₹32,083/d over naive (+44%); exact scheduling on top
adds a further +₹5,396/d (+5.2%) by DECLINING 2 low-value wells that would
otherwise tie up the one shared generator (10 served at 55% utilisation beats
12 served at 66-70%) -- fewer, better-chosen jobs beat "steam everything".
exact >= greedy holds by construction (exact searches every feasible subset
including greedy's own choice).

**Assumptions / limits** (also printed in the JSON's `assumptions` list):
12 wells are synthetic (`data/external/SOURCE.md`, no real Baghewala
per-well data); generator capacity (~74 t/d) and a 1-day move time between
wells are asserted, not fitted; interference between wells (pressure
communication, shared surface facilities beyond the one generator) is not
modelled; `soak_days` stays fixed at 10 (matching `recommend_physics.py`,
not searched); a job's `cycle_days` is the well's own FULL production cycle
(until its economic cutoff), which routinely extends past the 1-year
scheduling horizon -- only the injection + move time occupies the shared
generator, so "wells served this year" undercounts each well's eventual
payoff, it does not overcount it.

**CLI:**
```
python -m ml.schedule --make-wells                                     # (re)generate the synthetic wells CSV, seed 42
python -m ml.schedule --wells data/external/field_wells_synthetic.csv \
    --out ml/models/field_schedule_demo.json                           # full run, ~42 s
```

**API:** `POST /api/schedule` (JSON `{"wells": [...]}` or `{"csv_text": "..."}`,
optional `grid`/`horizon_days`; synchronous) and `GET /api/schedule/demo`
(serves the baked `ml/models/field_schedule_demo.json`, cached in-process
after first read). See `api/routers/schedule.py`.

**Dashboard:** Model basis page, section "Field view: which well gets steam
next" -- a Plotly Gantt of the exact schedule's generator timeline, the job
table, and KPIs (field ₹/yr vs naive, generator utilisation, wells
served/deferred). See `dashboard/README.md`.
