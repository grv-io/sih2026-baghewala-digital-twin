# ML / Optimization Layer — Ranked Improvement Plan

**Project:** SIH 2026, PS **SIH26120** (Oil India Ltd) — Baghewala CSS + sucker-rod-pump digital twin
**Scope of this document:** `ml/train.py`, `ml/optimize.py`, `ml/models/*`, `twin/generate_data.py` — the surrogate + optimizer layer only. Physics-module changes are named where they gate an ML item, but are owned by the physics plan.
**Written:** 13 September 2026. **Read-only analysis** — no project code was modified.

---

## How to read this

Every item is in one format:

> **WHAT** — the change, in one sentence.
> **WHY** — the justification, with a citation (research file + primary URL) or a measurement.
> **HOW** — code sketch, concrete enough to start from.
> **EFFORT** — **S** < 2 h · **M** 0.5–2 days · **L** > 3 days or blocked on data.
> **DEMO VALUE** — what a judge sees or hears that they did not before.
> **RISK** — what can break, and the mitigation.

**Tiers:** **Tier 1** = do before the internal round. **Tier 2** = finale scope. **Tier 3** = pilot / post-SIH.

**Provenance convention** — same discipline as `TEAM_STUDY_GUIDE.md` §6:
- **[MEASURED]** = run on this repo, this machine, 13-Sep-2026, commands in Appendix A. Reproducible.
- **[CITED]** = from the docs/research/deep-dives dossiers, with the primary URL carried through.
- **[DERIVED]** = our arithmetic from the two above; assumptions stated inline.

---

## 0. Executive summary — the ranked list

| # | Item | Tier | Effort | Headline metric delta |
|---|---|---|---|---|
| T1-1 | **Objective in ₹, not SOR** (+ CO₂ rider) | 1 | S–M | Surrogate R² **0.72 → 0.998** (oil is linear, SOR is a ratio); output becomes "₹X lakh/cycle" |
| T1-2 | **Physics-verification loop + two-stage search** | 1 | S | Verified SOR **0.8922 → ~0.85**; optimizer wall time **22.3 s → ~6 s**; gap printed, not hidden |
| T1-3 | **Viability gate (hurdle model) + envelope-honest metrics** | 1 | S | R² **0.7246 → 0.987**, MAE **0.307 → 0.071**, on 95.9% of the space, with the other 4.1% classified at AUC 0.9992 |
| T1-4 | **Native uncertainty (local conformal band)** | 1 | S | Band at the optimum **±0.31 → ±0.02**, with measured 90% coverage; matches the observed 0.011 verification gap |
| T1-5 | **Constraint & bound realism** (SPM band, pinned-variable flag, penalty→feasibility weighting) | 1 | S | Kills the single most dangerous viva question; recommendation becomes defensible, not just optimal |
| T2-1 | **Response-surface + SHAP transparency panel** | 2 | S | The optimizer stops being a black box on screen |
| T2-2 | **Schedule optimization (declining SPM), 6-D, DE/CMA-ES** | 2 | M | Resolves the 3–6 SPM contradiction; +1 decision variable class no competitor has |
| T2-3 | **Dyno-card classifier module** (cite, don't claim novelty) | 2 | M | A second ML head, positioned against published 99.5–99.84% baselines |
| T2-4 | **Recalibration protocol for OIL data** (rehearsed on pseudo-field data) | 2 | M | "Here is the exact 90-second procedure the day you give us cycle records" |
| T2-5 | **Adaptive sampling / active learning** | 2 | M | Same accuracy near the optimum from ~40% of the cycles; the argument that scales to CMG-STARS |
| T3-1 | **Multi-well steam allocation** (74 tpd across 33 wells) | 3 | M–L | The scarcity finding turned into a daily decision |
| T3-2 | **Cycle-index degradation / "stop CSS" signal** | 3 | L | The Liaohe SOR-drift story, as a model output |
| T3-3 | **Sequential assimilation (EnKF-style) at three cadences** | 3 | L | DNV Level 4→5 evidence |
| T3-4 | **Real-card fine-tuning + failure-lead-time model** | 3 | L | The scaled-load-ratio literature, on OIL's own cards |

**If you only do three things before the internal round: T1-3, T1-2, T1-1 — in that order of effort-to-value.** T1-3 is ~40 lines and moves the headline metric more than anything else on this list.

---

## 1. Diagnosis of the current pipeline (all measured)

The pipeline as built: 3,000 LHS cycles (seed 42) → XGBoost on `log(SOR)` (R² 0.7246, MAE 0.3068) + XGBoost floating classifier (AUC 0.9989) → `gp_minimize`, 60 calls, additive 1000× hinge penalty on P(float) ≥ 0.3 → 4 static decision variables. It works, it is honest, and it has six specific weaknesses that are all cheap to fix.

### F1 — The R² 0.72 is a tail artifact, not a model quality statement **[MEASURED]**

Held-out error, sliced by design region:

| Region | n (of 600) | R² | MAE (t/m³) |
|---|---|---|---|
| **All** | 600 | 0.725 | 0.307 |
| `steam_t ∈ [1200, 2400] t` (the operating envelope) | 287 | **0.992** | **0.036** |
| `soak_days ≤ 8` | 277 | 0.978 | 0.051 |
| True SOR < 2.0 t/m³ | 304 | 0.985 | 0.029 |
| True SOR < 1.2 t/m³ (the recommended region) | 63 | 0.924 | **0.019** |
| True SOR > 5 t/m³ (uneconomic tail) | 68 | — | **2.324** |

The five worst residuals in the holdout are 52.6, 50.4, 8.4, 5.5, 3.1 — all at `steam_t < 650 t` with `soak_days ≥ 11` and `cutoff ≥ 6 m³/d`, i.e. barely-producing cycles with SOR up to **99.8 t/m³** in the training data. **The model is being scored on its ability to predict how bad a cycle nobody would ever run is.** The dataset carries 4.1% of rows above SOR 8 t/m³ — outside the entire literature band of 3–8 (`css_thermal_eor_deep_dive.md` §3, Cold Lake ≈4, Liaohe 2.86–3.56).

### F2 — SOR is the wrong regression target, statistically and economically **[MEASURED] + [CITED]**

SOR = steam ÷ oil. The numerator is a **decision variable known exactly** (`steam_t`); the denominator is the only thing that needs predicting. Fitting the ratio imports the denominator's zero-approach into the target and manufactures the heavy tail in F1. Fitting the parts instead:

| Target | R² (holdout) | MAE |
|---|---|---|
| `SOR_t_per_m3` (current) | 0.7246 | 0.307 t/m³ |
| **`oil_total_m3`** | **0.998** | **16.5 m³** (mean 1,001 m³ → 1.6%) |
| **`days_total`** | **0.9988** | — |

And economically: `css_thermal_eor_deep_dive.md` §7 says it outright — *"Report every result in three units at once: bbl, ₹, and kg CO₂"* — and §5.2 derives **₹8,400/t of steam** at diesel (71 kg HSD/t steam from the OIL operations deck → 86 L/t → ₹97.8/L Rajasthan retail).

### F3 — The surrogate is currently *slower* than the physics it replaces **[MEASURED]**

| Operation | Wall time |
|---|---|
| One full `twin.cycle.simulate_css_cycle` + `summary` | **0.55 ms** |
| One single-row `sor_model.predict()` | **1.13 ms** |
| Batched `sor_model.predict()`, 600 rows | 1.25 ms (**2.1 µs/row**) |
| `ml.optimize.best_settings()` end to end, 60 calls | **22.27 s** |
| 4,000-point LHS over the **true twin**, with the true FI ≤ 0.6 constraint | **4.8 s** |

Two consequences, both important:

1. **skopt's own Gaussian-process fitting and acquisition optimization are 99.7% of the optimizer's runtime.** 60 surrogate calls cost 0.07 s; the other 22.2 s is search overhead.
2. **In less wall time, brute force over the real physics finds a better point.** The 4,000-point LHS found a feasible **true SOR 0.8497** (1,889 t / 3 d / 4.63 m³/d / 10.96 SPM, oil 2,223 m³) versus the current pipeline's verified **0.8922** — **4.8% better SOR and 25% more oil, in 4.8 s instead of 22.3 s.**

This is *not* an argument against the surrogate — it is an argument that the surrogate is being used in the one mode (sequential, single-point) where it has no advantage. Batched, it is **262× faster per candidate than the twin**, which is what makes T2-2 (10⁴-candidate schedule search) and T3-1 (33-well allocation sweeps) possible at all. Say the honest version out loud before a judge finds it: *"our twin is fast enough to check the surrogate's homework, so we do — every time."*

### F4 — Degenerate cycles are dropped, creating a silent blind spot **[MEASURED]**

`twin/generate_data.py` drops zero-oil rows (`SOR = inf`) before training. The surrogate therefore has no representation of infeasible regions, and nothing stops the optimizer from recommending inside one. There is no "this design is not worth running" output at all.

### F5 — Three of four decision variables are pinned at their bounds, and one of them contradicts published practice **[MEASURED] + [CITED]**

Twin behaviour at the recommended point, varying one knob at a time:

| soak_days | 3 | 5 | 7 | 9 | 11 | 13 | 15 |
|---|---|---|---|---|---|---|---|
| SOR | **0.892** | 1.000 | 1.138 | 1.319 | 1.569 | 1.937 | 2.528 |

| SPM | 4 | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|
| SOR | 1.788 | 1.315 | 1.063 | 0.906 | **0.796** |
| max FI | 0.104 | 0.156 | 0.208 | 0.260 | 0.312 |

- **Soak is strictly monotone-bad** in the current twin — it only loses heat, because pressure re-charge and conductive spreading are not modelled. The recommendation "soak 3 days" is therefore a *model-structure artifact*, not advice, and it directly contradicts Baghewala's actual 7–13 day practice (`css_thermal_eor_deep_dive.md` §2.5). A petroleum engineer will ask this.
- **SPM is monotone-good to the range top**, and the floating constraint never binds (P(float) = 0.001 at the optimum; max FI 0.31 even at 12 SPM). But `srp_dynamometer_ml_deep_dive.md` §5.1 says heavy-oil rod pumps should run **3–6 SPM, 2–8 absolute**, with VSD fillage control at 4–7 SPM (https://www.sciencedirect.com/topics/engineering/pumping-unit). **Our headline recommendation runs the pump at 10.2 SPM.**
- Capping SPM at the published band collapses the result **[MEASURED]**: best feasible SOR with `spm ∈ [3,6]` is **1.2986** — statistically identical to the field-practice reference cycle's 1.2943. **The entire −30% headline is bought by high SPM.**

There *is* a good answer, and it is checkable: over the whole produce phase at the recommended point, in-situ viscosity runs **3.5 → 850 cP**, never the cold 11,500 cP — production is cut off at 7.76 m³/d while the oil is still warm, so the rods never enter the regime the 3–6 SPM guidance is written for. That answer only survives if we *say it first*, and it points straight at T2-2 (a declining SPM schedule is the physically correct form of the recommendation).

### F6 — Two economics constants disagree by 6.5× **[MEASURED]**

`dashboard/index.html:1243` sets `STEAM_INR_PER_T = 1300`. `css_thermal_eor_deep_dive.md` §5.2 derives **₹8,400/t** for diesel-fired steam and **~₹970/t** for gas-fired. ₹1,300/t is, within rounding, the *gas-fired* number — while Baghewala burns HSD. The rupee slide currently understates steam cost by 6.5×, in the safe direction for the pitch but the wrong direction for credibility.

---

## 2. TIER 1 — before the internal round

### T1-1 · Optimize in rupees, not SOR

**WHAT.** Replace the objective `min SOR` with `max ₹ margin`: `margin = P_oil · oil(x) − C_steam · steam_t − lifting_cost`, reported per cycle, **per cycle-day**, and **per tonne of steam**. Add `oil_total_m3` and `days_total` surrogates (already near-exact, F2), and a CO₂ rider using the same steam tonnage.

**WHY.**
- `css_thermal_eor_deep_dive.md` §7: *"Report every result in three units at once: bbl, ₹, and kg CO₂ — because at diesel-fired steam prices those three numbers move together, and that is the story that wins."*
- §5.2 **[CITED/DERIVED]**: **₹8,400/t steam** (71 kg HSD/t → 86 L/t → ₹97.8/L Rajasthan retail Aug-2026, https://www.goodreturns.in/diesel-price-in-rajasthan-s28.html); gas-fired equivalent ~US$11/t ≈ ₹970/t, i.e. **8× cheaper** — fuel switching is the biggest single lever and belongs on the same chart.
- §5.3: **222 kg CO₂/t steam** diesel-fired; **SOR explains ~60% of the variance in thermal-EOR emissions** (https://thundersaidenergy.com/downloads/oil-sands-co2-intensity/). The economics slide and the sustainability slide are the same slide.
- SPE-209284 series (SPE Western Regional 2022, `css_thermal_eor_deep_dive.md` §4) optimises CSS for **carbon and return simultaneously** — dual-objective is published practice, not a bolt-on.
- **[MEASURED]** the statistical bonus: margin is *linear* in predicted oil and *exact* in steam cost (steam_t is a decision variable, zero model error on the cost side). Predicting margin inherits `oil_total_m3`'s **R² 0.998**, not SOR's 0.7246.

**HOW.**

1. Add an `economics` block to `params/field_params.json` (single source of truth, per docs/SPEC.md — never hardcode in the dashboard again; this also fixes F6):
```jsonc
"economics": {
  "steam_cost_inr_per_t": 8400,          // diesel-fired, css_thermal_eor_deep_dive.md §5.2 [DERIVED]
  "steam_cost_inr_per_t_gas_alt": 970,   // fuel-switch scenario, same source
  "crude_price_inr_per_bbl": 6160,       // US$70/bbl @ Rs 88/USD — a demo dial, printed on screen
  "bbl_per_m3": 6.2898,
  "co2_kg_per_t_steam": 222,             // §5.3 [DERIVED]
  "lifting_cost_inr_per_m3": null        // null until OIL gives a number; excluded and said so
}
```
2. `ml/train.py`: train `oil_model.joblib` (target `oil_total_m3`) and `days_model.joblib` (target `days_total`) alongside the existing two. Keep the SOR model — it stays the engineering KPI and the literature-comparable number.
3. `ml/optimize.py`: objective becomes
```python
oil   = oil_model.predict(X)[0]                 # m3
days  = days_model.predict(X)[0]
rev   = oil * bbl_per_m3 * crude_inr_per_bbl
cost  = steam_t * steam_cost_inr_per_t          # exact: steam_t is an input
margin = rev - cost
return -(margin / steam_t)                      # Rs per tonne of steam — see below
```
4. **Choose the denominator deliberately and say why.** Steam is the binding resource: 74 tpd field-wide (`css_thermal_eor_deep_dive.md` §3) means one 1,585 t cycle consumes **21 days of the entire field's steam output**. When a resource is scarce, the correct objective is its shadow price — **₹ per tonne of steam** — which is also exactly the ranking key T3-1 (multi-well allocation) needs. Report all three currencies; optimise on ₹/t-steam.
5. Return a `co2_kg` field = `steam_t × 222`, and a `breakeven_sor` field = `P_oil_per_m3 / C_steam`.

**Numbers this produces today [MEASURED + DERIVED at ₹8,400/t and ₹6,160/bbl]:**

| Design | SOR | Oil (m³) | Steam (t) | Margin | ₹/day | **₹/t-steam** |
|---|---|---|---|---|---|---|
| Field-practice reference (1500/7/3.0/8.0) | 1.294 | 1,159 | 1,500 | ₹3.23 cr | ₹527 k | ₹21,536 |
| Current optimizer rec, physics-verified | 0.892 | 1,776 | 1,585 | ₹5.55 cr | ₹1,039 k | ₹35,027 |
| Best point found by a true-twin sweep (T1-2) | 0.807 | 2,272 | 1,834 | **₹7.26 cr** | **₹1,195 k** | **₹39,601** |

**Break-even SOR = 4.61 t/m³** at diesel; at gas-fired ₹970/t it is 39.9 t/m³ (never binds). That one line is the fuel-switch argument, quantified.

**One honesty flag on the CO₂ rider [DERIVED]:** the recommendation burns *more* steam in absolute terms (1,585 t vs 1,500 t → 352 t vs 333 t CO₂), but produces 53% more oil, so **intensity falls 45.7 → 31.5 kg CO₂/bbl (−31%)**. Always quote CO₂ per barrel, never per cycle, and say which you are quoting — the per-cycle number moves the wrong way and a sharp judge will check.

**EFFORT.** **S** for the objective swap and constants; **M** including the two new surrogates, the API field, and the dashboard's three-currency readout.

**DEMO VALUE.** The optimizer stops answering a dimensionless engineering ratio and starts answering *"₹2.3 crore more margin per cycle, and 0.28 kt less CO₂."* Every judge — technical or not — can price that. It also lets you put a **crude-price slider** on screen and show the recommendation move: nothing says "real optimizer" like watching the answer respond to an assumption.

**RISK.** (a) The rupee number is only as good as `crude_price_inr_per_bbl` — mitigate by printing the assumption next to every figure (the dashboard already does this pattern) and by leading with ₹/t-steam, which is far less price-sensitive than ₹/cycle. (b) Someone will ask why lifting cost is missing — answer: it is `null` because OIL has not published one, and we excluded it rather than invent it. (c) At extreme price ratios the ₹ optimum can drift to a bound — the T1-5 pinned-variable flag catches it automatically.

---

### T1-2 · Physics-verification loop, and a two-stage search

**WHAT.** After the surrogate search, (a) re-run the **true twin** at the recommendation and at the top-5 candidates from the search trace, (b) report both numbers and the gap as a first-class output, (c) spend the leftover compute on a **local true-twin refinement** around the surrogate's answer and return the physics-verified winner.

**WHY.**
- The finding already exists and is the team's strongest honesty move — `TEAM_STUDY_GUIDE.md` §4.3: surrogate **0.8816**, physics twin **0.8922**, off by **1.2%**, *"it converts 'trust our R²' into 'we checked.'"* Institutionalise it instead of quoting it.
- **[MEASURED]** it is nearly free: one twin run is **0.55 ms**. Verifying the top 5 costs 3 ms against a 22-second optimizer.
- **[MEASURED]** it also *improves the answer*: a 4,000-point true-twin sweep (4.8 s) found **SOR 0.8497** vs the current verified 0.8922 — the surrogate's optimum is not the physics optimum, and we currently ship the former.
- `digital_twin_oilfield_deep_dive.md` §4.2 is explicit that the surrogate-plus-BO design thesis holds *"because we keep the simulator in the loop for periodic re-training and validation, we never lose physical defensibility."* This item is that sentence, implemented.
- Surrogate-assisted optimization with true-model refinement is the standard pattern, not an invention (Ind. Eng. Chem. Res. 2024 surrogate-assisted constrained oil-recovery optimization, https://pubs.acs.org/doi/10.1021/acs.iecr.4c03294).

**HOW.**
```python
# stage 1 — global, on the surrogate, BATCHED (2.1 us/candidate measured)
cand = lhs_or_sobol(space, n=20_000)           # ~40 ms of predict()
feas = float_model.predict_proba(cand)[:,1] < 0.3
top  = cand[feas][np.argsort(margin_hat[feas])][-64:]

# stage 2 — verify + refine on the TRUE twin (0.55 ms each)
verified = [(x, cycle.summary(cycle.simulate_css_cycle(*x, params))) for x in top]
best = max(verified, key=margin_true)          # ~35 ms for 64
best = local_pattern_search(best, params, budget=2000)   # ~1.1 s of true physics

return {
  "best_settings": best.x,
  "surrogate_prediction": ...,     # 0.8816-style number
  "physics_verified": ...,         # 0.8922-style number
  "verification_gap_pct": ...,     # +1.19%  <-- print this
  "n_physics_evals": ...,
}
```
Keep `gp_minimize` available behind a flag so the "we compared three search strategies" slide has data behind it.

**EFFORT.** **S** (verification + top-k, ~30 lines). **S–M** including the batched stage-1 rewrite and the local refinement.

**DEMO VALUE.** Three things at once: a better headline number (0.85 vs 0.89), a faster optimizer (~6 s vs 22 s), and a printed self-check. The line to rehearse: *"The optimizer doesn't trust the ML either — it re-runs the physics on its own answer and shows you the difference. Today that difference is 1.2%."*

**RISK.** (a) A judge asks "then why have ML at all?" — have the answer ready and volunteer it: single-point, the twin is faster (0.55 ms vs 1.13 ms); **batched, the surrogate is 262× faster per candidate**, which is what makes the 10⁴-candidate schedule search and the 33-well allocation sweep tractable, and the architecture is the one that survives replacing our twin with a CMG-STARS run that takes hours (`digital_twin_oilfield_deep_dive.md` §4.2: >2000× surrogate speedups at ~10% error). (b) Local refinement on the twin can overfit to twin quirks — mitigate by keeping the surrogate's feasibility screen and reporting both points.

---

### T1-3 · Viability gate (hurdle model) + envelope-honest metrics

**WHAT.** Split the regression problem in two: an **economic-viability classifier** (is this design's SOR above the literature band, i.e. a cycle nobody should run?) and a **SOR/oil regressor trained only on viable cycles**. Report metrics for both, with the envelope defined *before* the numbers are quoted.

**WHY.**
- **[MEASURED]** this is the single largest metric improvement available anywhere in the pipeline, for ~40 lines:

| Model | Metric today | Metric after |
|---|---|---|
| Uneconomic-cycle gate (SOR > 8 t/m³, 4.1% of designs) | *does not exist* | **AUC 0.9992, acc 0.9933** |
| SOR regressor, viable cycles only | R² 0.7246 / MAE 0.3068 | **R² 0.987 / MAE 0.0705** |
| SOR regressor, near-optimum (SOR < 1.2) | MAE 0.019 (unreported) | MAE 0.019 (**reported**) |

- The 8 t/m³ cut is not arbitrary: `css_thermal_eor_deep_dive.md` §3 puts world CSS practice at SOR ≈ 2.86–6.0 (Liaohe, Cold Lake, life-cycle average 6.0) and §5.2 shows the economics break at **4.6 t/m³** at diesel prices. Anything above 8 is off the map of every field in the dossier.
- Hurdle / two-part models are the textbook treatment for a strictly-positive target with a degenerate mass — the same reasoning that already justified the `log` transform in `train.py`'s docstring, taken one step further.
- It also closes **F4**: the dropped `SOR = inf` rows come back as the extreme class of the gate instead of vanishing.

**HOW.**
1. `twin/generate_data.py`: stop dropping `inf` rows — keep them with a `viable = 0` flag (and a large sentinel SOR), so infeasibility is *learned*, not deleted.
2. `ml/train.py`:
```python
VIABILITY_SOR_LIMIT = 8.0          # css_thermal_eor_deep_dive.md §3: world CSS band 2.86-6.0
df["viable"] = np.isfinite(df.SOR) & (df.SOR <= VIABILITY_SOR_LIMIT)
viab_model = XGBClassifier(...).fit(X_train, ~df.viable)          # AUC 0.9992 measured
sor_model  = TransformedTargetRegressor(...).fit(X_train[viable], y[viable])   # R2 0.987
```
3. `ml/optimize.py`: treat `P(uneconomic) > 0.5` as hard-infeasible (skip, don't penalise).
4. `metrics.json` gains an explicit envelope declaration so the numbers can never be read as cherry-picking:
```json
"envelope": {"definition": "SOR_t_per_m3 <= 8.0 (world CSS band, css_thermal_eor_deep_dive.md §3)",
             "coverage_frac": 0.959},
"regressor_in_envelope": {"r2": 0.987, "mae": 0.0705},
"regressor_all_designs":  {"r2": 0.7246, "mae": 0.3068},
"viability_gate": {"auc": 0.9992, "accuracy": 0.9933}
```

**EFFORT.** **S** — one classifier, one filtered fit, four extra JSON keys.

**DEMO VALUE.** The deck's weakest number disappears. Instead of defending *"R² 0.72, but that's fine because the optimizer only needs ranking"* (true, but defensive), you say: *"R² 0.99 on the 96% of designs that are economically viable, and a separate gate that identifies the other 4% at AUC 0.999 — because a model that tells you a bad cycle is 'very bad' versus 'extremely bad' is not doing useful work."* That is a stronger statement **and** a more honest one, because both numbers are published side by side.

**RISK.** Cherry-picking accusation — mitigated completely by (a) defining the envelope from the literature *before* fitting, (b) printing both numbers in `metrics.json` and on screen, (c) reporting gate coverage. Never quote 0.987 without the 0.959 coverage and the 0.7246 next to it.

---

### T1-4 · Native, local uncertainty — replace the global MAE bar

**WHAT.** Ship a per-point prediction interval via **split conformal prediction** on the holdout (and quantile-XGBoost as the Tier-2 upgrade), replacing the constant global-MAE band the dashboard currently draws.

**WHY.**
- `docs/reviews/ui_review_ux.md` §3.10 item 2 + closing note: *"No uncertainty anywhere... the bar chart draws 0.88 as a hairline-precise column. See P1-1 — this is the highest value-per-line-of-code fix in the review."* The UI already promises `0.88 ± 0.31`.
- **[MEASURED] the promise is 16× too pessimistic where it matters.** Global MAE is 0.3068, but in the near-optimum region (SOR < 1.2) MAE is **0.0193**. And the actual physics-verification gap at the recommendation is **0.0106** — *inside* the local band, 30× smaller than the global one. A locally-calibrated band reads **0.88 ± 0.02** and is corroborated by the twin. The current band is not conservative honesty; it is a wrong number that makes the model look worse than it is.
- Conformal residual quantiles **[MEASURED]**: global |residual| q50 = 0.036, q80 = 0.097, **q90 = 0.213**, q95 = 0.582; on viable-only designs q90 = **0.141**. So even the global conformal band is tighter than ±0.31, with a distribution-free 90% coverage guarantee rather than a hand-wave.
- `digital_twin_oilfield_deep_dive.md` §6.3 (roadmap paragraph) commits us to recommendations *"with the physics reasoning and an uncertainty band attached"* at DNV Level 4. This is that commitment, made native.

**HOW.**
1. Split conformal, ~12 lines in `train.py` — hold out a calibration slice, store `q90 = np.quantile(|y_cal − ŷ_cal|, 0.9)` in `metrics.json`, globally and per stratum (bin by predicted SOR, or by `steam_t` decile):
```python
"conformal": {"alpha": 0.10, "global_q90": 0.213,
              "by_pred_bin": {"<1.0": 0.021, "1.0-2.0": 0.048, "2.0-5.0": 0.31, ">5": 2.9},
              "empirical_coverage": 0.90}
```
2. `optimize.py` returns `predicted_SOR`, `pi_low`, `pi_high` from the bin containing the recommendation.
3. Dashboard: error bar on the optimized bar + `0.88 [0.86, 0.90] · 90% conformal` — and, next to it, the physics-verified point from T1-2. Three marks that agree is the most persuasive object on the page.
4. **Tier-2 upgrade:** XGBoost ≥ 2.0 quantile loss (`objective="reg:quantileerror"`, `quantile_alpha=[0.1,0.5,0.9]`) for a smooth point-dependent band, and optionally a **risk-averse objective** — minimise the q90 SOR instead of the mean, which is the robust-optimization framing of SPE Journal 2024 *"Reservoir Production Management With Bayesian Optimization: Achieving Robust Results in a Fraction of the Time"* (https://onepetro.org/SJ/article-abstract/29/02/620/535724).

**EFFORT.** **S** for conformal. **M** for quantile models + risk-averse objective (Tier 2).

**DEMO VALUE.** *"Predicted 0.88, 90% interval 0.86–0.90, physics re-check 0.89."* Three independent numbers landing on top of each other is the single most convincing thing a modelling team can show — and it costs a dozen lines.

**RISK.** Conformal assumes exchangeability between calibration and test points. It holds inside our LHS design and **will not hold** on real OIL data — say so, and make T2-4's recalibration the stated remedy. Also: never report the near-optimum band without stating it is region-conditional, or it reads as hiding the tail.

---

### T1-5 · Constraint and bound realism

**WHAT.** Four small changes that convert an optimizer that is *optimal* into one that is *defensible*: (1) flag bound-pinned variables in the output, (2) re-ground the SPM search range on published heavy-oil practice, (3) declare soak as non-informative until the physics changes, (4) replace the 1000× additive penalty with a feasibility-weighted screen, and report seed robustness.

**WHY.**
- **[MEASURED] F5**: soak pins to its floor (3 d) because the twin's soak only loses heat; SPM pins to its ceiling; the floating constraint is inactive at the optimum (P = 0.001, max FI 0.31 even at 12 SPM). An optimum on a bound is a statement about the search box, not about the field.
- **[CITED]** `srp_dynamometer_ml_deep_dive.md` §5.1: heavy oil should run **3–6 SPM (2–8 absolute)**, fillage-based VSD control targets **4–7 SPM** (https://www.sciencedirect.com/topics/engineering/pumping-unit); Ambyint's 2,500-well deployment reports a **28% SPM reduction** as a headline result, not an increase (https://www.ambyint.com/case-studies/...). We currently recommend **10.2 SPM**.
- **[MEASURED]** the defence exists and is checkable: over the whole produce phase at the recommendation, µ runs **3.5 → 850 cP** — never the cold 11,500 cP the 3–6 SPM guidance addresses, because the 7.76 m³/d cutoff ends the cycle while the oil is still warm. Also, oil rate is pinned at the **pump ceiling 95.8 m³/d for the first ~15 produce days**, i.e. the cycle is *lift-limited*, exactly the UPC Global finding that *"the lift system, not the reservoir, is often the binding constraint"* (`css_thermal_eor_deep_dive.md` §4, paper 3).
- **[CITED]** on the penalty: constraints belong in the surrogate, not bolted onto the objective — Ind. Eng. Chem. Res. 2024, *"Surrogate-Assisted Optimization of Highly Constrained Oil Recovery Processes Using Classification-Based Constraint Modeling"* (https://pubs.acs.org/doi/10.1021/acs.iecr.4c03294). A 1000× hinge on an objective of order 1 is a cliff that a smooth GP kernel cannot represent, so evaluations are wasted modelling the penalty rather than the physics.

**HOW.**
1. **Pinned-variable flag** (~10 lines):
```python
PIN_TOL = 0.02
pinned = {k: ("lower" if v <= lo + PIN_TOL*(hi-lo) else "upper")
          for k,(v,(lo,hi)) in ... if at_bound}
# -> {"soak_days": "lower", "spm": "upper"}
```
Surface it in the API and on screen as *"2 of 4 variables at a search bound — the optimum may lie outside the modelled range."* This is a maturity signal, not a weakness.
2. **SPM range**: keep `srp.spm_range = [4, 12]` in the search but add `srp.spm_practice_band = [3, 7]` to `field_params.json`, and return **two recommendations** — unconstrained, and inside the published practice band. **[MEASURED]** the practice-band optimum is SOR 1.2986 at 1,088 t / 3 d / 4.68 / 5.98 SPM. Showing both, and explaining that the gap is the *value of a VFD and a declining SPM schedule* (T2-2), turns the weakest point in the pipeline into the setup for the strongest Tier-2 item.
3. **Soak**: until the physics adds a soak benefit (pressure re-charge, conductive spreading), print `soak_days: not optimised — the current thermal model is monotone in soak; we report field practice 7–13 d` rather than recommending 3.
4. **Penalty → feasibility screen**: multiply the acquisition by `P(feasible)` (constrained EI) or hard-filter candidates in the batched stage-1 screen of T1-2. If keeping the penalty, scale it to ~10× the objective range and log it, not 1000×.
5. **Seed robustness**: run the optimizer with 5 seeds, report the spread of the recommendation and of the objective. Cheap insurance against *"you got lucky with seed 42."*

**EFFORT.** **S** — all five are small, and (2) and (3) are mostly reporting.

**DEMO VALUE.** This is the item that prevents a bad thirty seconds in the viva. Volunteering *"two of our four variables sit on a bound, and here is what that means"* reads as senior engineering. It also gives the pitch a genuinely interesting line: *"the optimizer wants to pump faster than the heavy-oil textbook allows — and it is right, because the oil is 3 to 850 cP during the produce window, not 11,500. That is exactly why the next version schedules SPM instead of fixing it."*

**RISK.** Reporting two recommendations can look indecisive — mitigate by making the practice-band one the *headline* and the unconstrained one the *upside case*, clearly labelled.

---

## 3. TIER 2 — finale scope

### T2-1 · Response-surface + SHAP transparency panel

**WHAT.** A 2-D response surface (`steam_t` × `soak_days`, and `steam_t` × `spm`) from the surrogate with the optimum, the feasibility boundary and the field-practice point marked; plus a SHAP or gain-based feature-importance bar for the SOR and floating models.

**WHY.** `docs/reviews/ui_review_ux.md` §3.10 item 1 flags that the optimizer is described three different ways on screen ("ML-Optimized" / "Bayesian optimizer" / "XGBoost surrogate") — a picture settles it. `digital_twin_oilfield_deep_dive.md` §6.3 requires Level-4 recommendations to carry *"the physics reasoning"*. A heat map with a marked optimum **is** the reasoning, and it costs one batched `predict()` over a 100×100 grid — **[MEASURED]** ~20 ms.

**HOW.** `ml/surface.py` → `GET /surface?x=steam_t&y=spm` → Plotly `contour` with `scatter` markers for optimum / baseline / practice-band optimum. SHAP: `shap.TreeExplainer(model).shap_values(X_sample)`, or `model.get_booster().get_score(importance_type="gain")` if you want zero new dependencies.

**EFFORT.** **S–M.** **DEMO VALUE.** High — it makes the diminishing-returns physics (`css_thermal_eor_deep_dive.md` §2.5, marginal heat vs marginal oil) *visible* as a curved valley, which is the argument the deck currently makes only in words. **RISK.** A 2-D slice hides interactions; label it "slice at the recommended values of the other two variables."

---

### T2-2 · Schedule optimization — declining SPM through the cycle

**WHAT.** Replace the single static `spm` with a 2–3 parameter **schedule** (`spm_start`, decline rate, optional floor), keeping the search at 6 dimensions, and switch the search engine to a population method (differential evolution or CMA-ES) that exploits batched surrogate evaluation.

**WHY.**
- `srp_dynamometer_ml_deep_dive.md` §5.2 states the requirement outright: *"The optimal SPM is not constant within a single CSS cycle; it should decline as the well cools. This is precisely the schedule our twin computes."* Right now it does not — this closes a gap between the research and the build.
- **[MEASURED]** the physics demands it: in-situ µ runs 3.5 → 850 cP across a single produce phase, a 245× swing. One SPM for that whole range is indefensible; a declining schedule is the direct resolution of the T1-5 / F5 credibility problem.
- **[CITED]** the operational precedent is strong: Pump-Stroke Optimization (SPE Prod & Oper 33(3):419, 2018) slowed **only the downstroke** across a 20-well Eagle Ford pilot — 10 highly successful, 5 marginal, 5 unsuccessful (https://onepetro.org/PO/article-abstract/33/03/419/...); Ambyint's closed-loop min/max SPM setpoint control over ~2,400 wells produced a **28% SPM reduction and 19% fewer rods-in-compression events** (https://www.ambyint.com/case-studies/...).
- **Engine choice, on measurements not vibes.** skopt's GP overhead is 22.2 s of a 22.3 s run **[MEASURED]** and scales as O(n³) in evaluations — it is built for expensive objectives, and ours costs 2.1 µs batched. Differential evolution or CMA-ES at popsize 15×6 dims × 300 generations = 27,000 candidates ≈ **60 ms of batched surrogate predict**, then T1-2 verifies the top 64 on the true twin. Sample efficiency stops being the binding constraint the moment the objective is a batched tree ensemble. Keep `gp_minimize` for the *direct-twin* refinement stage, where its 20-run convergence property (https://onepetro.org/OTCONF/proceedings/20OTC/1-20OTC/D011S002R003/107796) actually earns its keep.

**HOW.**
1. **Blocked on physics**: `twin/cycle.py` must accept `spm` as a callable or schedule (`spm(day)`), and `generate_data.py` must sample schedule parameters. Coordinate with the physics plan — this is the one Tier-2 item with a hard dependency.
2. Parameterize as `spm(t) = clip(spm0 · exp(−t_prod/τ_spm), spm_min, spm_max)`, or the operationally simpler two-step `spm_hot` until day `t_switch`, then `spm_cold`. Two parameters, 6 dims total, and — importantly — **a two-step schedule is something a rod-pump controller can actually execute**, which a continuous decline is not.
3. Search: `scipy.optimize.differential_evolution(..., vectorized=True, workers=1)` so the whole population hits `model.predict` in one call; or `cma.CMAEvolutionStrategy` with `ask()`/`tell()` batching.
4. Report the schedule as a small step-plot next to the dyno card — *this* is the "what do I do on Monday morning" artifact from `css_thermal_eor_deep_dive.md` §6 Q5.

**EFFORT.** **M** (ML side; **M** more on the physics side). **DEMO VALUE.** Very high — it is a *new kind of answer*, not a better number, and no competitor product in `docs/research/landscape.md` co-optimises the CSS slug and the lift schedule. **RISK.** (a) Physics dependency could slip — mitigate by building and testing the 6-D search against the *existing* static-SPM twin first (with `spm_start == spm_cold`), so the search machinery is proven before the schedule lands. (b) More dimensions on the same 3,000-cycle dataset means thinner coverage — pair with T2-5 (adaptive sampling) and raise the dataset to ~8,000 cycles, which **[MEASURED]** costs ~10 s of twin time.

---

### T2-3 · Dyno-card classifier module

**WHAT.** A second ML head: synthesise dynamometer-card shapes from `twin/srp.py` state plus the published fault-shape catalogue, train an XGBoost classifier on the raw normalised load vector, and present it explicitly as *"the surface-card triage module, built to the published architecture, ready for OIL's cards."*

**WHY, and the exact positioning.**
- **Do not claim novelty.** `srp_dynamometer_ml_deep_dive.md` §3 is unambiguous: **99.50%** (AlexNet+SVM, 8,000 cards / 8 classes, Sensors 2020, https://pmc.ncbi.nlm.nih.gov/articles/PMC7582724/) and **99.84%** (XGBoost on 50,000+ real cards from 38 wells, Sensors 2021, https://pmc.ncbi.nlm.nih.gov/articles/PMC8271678/). §6.2 Q1 already scripts the answer: *"Card classification is a solved problem — we are not trying to beat that; we would fine-tune a published architecture the day OIL gives us cards."*
- Two design decisions come straight from the Sensors 2021 paper and are worth stating because they show you read it: **raw normalised load values performed about as well as Fourier or wavelet descriptors** (so: no clever feature engineering — XGBoost on a resampled 64-point load vector), and **real card datasets are brutally imbalanced** (38,298 fluid-pound vs 6 gas-lock), so report per-class recall and include a **sensor-fault class** ("rotated card", "line card"), because bad sensors look like bad pumps.
- The module is the bridge to the failure-prediction literature: SPE Journal 233386 predicts failures from the **scaled load ratio** (normalised min ÷ max surface load) at **F1 0.857, 13.97-day lead**, from surface data only (https://jpt.spe.org/prediction-of-sucker-rod-pump-failures-using-scaled-load-ratios-and-machine-learning). `srp_dynamometer_ml_deep_dive.md` §6.3 already argues our `floating_index` is the same quantity from the physics side. **Compute the scaled load ratio from our synthesised card and plot it against `floating_index`** — a scatter with a fitted line is a one-slide proof that our physics index and the published failure predictor are the same signal.
- Architecture credibility: Energies 2023 (https://doi.org/10.3390/en16073170) shows the industrial winner is **CNN + expert rules**, not pure ML; XSPOC pairs wave-equation card synthesis with ML pattern classification over >25M cards. Our physics-synthesis → ML-classification pipeline *is* that architecture at hackathon scale.

**HOW.**
1. `twin/card.py` (physics side): a `load(position)` loop over one stroke from `srp.pump_state` components — buoyant rod weight, fluid load, viscous drag, a simple inertia term — giving the "normal" rectangle-ish card.
2. `ml/cards/generate.py`: apply the §2.2 shape-catalogue deformations to produce 8–10 classes × 1,000 cards (matching Sensors 2020's dataset size): normal, pump-off/incomplete fillage, fluid pound (sharp step + ringing), gas interference (rounded upper-left "banana"), TV leak (slanted pick-up), SV leak (raised downstroke floor), rod float (fat, tilted, low-load downstroke), unanchored tubing (45° slant), tagging (spike), plus a **sensor-fault** class. Augment with noise injection and cropping, per SPE ERM 2025 paper 792253.
3. `ml/cards/train.py`: resample each card to 64 points, min-max normalise load, XGBoost multiclass. Report accuracy **and** per-class recall **and** a confusion matrix.
4. Dashboard: the existing card sketch gains a predicted-class label with confidence, plus the scaled-load-ratio value.

**EFFORT.** **M** (2 days, mostly the card generator).

**DEMO VALUE.** High — it is the module a rod-pump engineer expects to see, and it makes the dyno panel interactive rather than decorative. **The framing is the whole value:** *"card classification is solved at 99.5% in the literature; we built the pipeline and the synthetic corpus so that fine-tuning on Oil India's cards is a day's work, not a project."*

**RISK.** **The circularity trap** — the classifier is trained on shapes we drew, so ~99% accuracy on it means nothing. Mitigation, and say it before you are asked: (a) never quote the synthetic accuracy as a headline, quote the published 99.5/99.84% as the target; (b) report per-class recall and the confusion matrix, so the failure modes are visible; (c) state that the corpus is a *pipeline test fixture and a labelling schema*, and that the deliverable is the ingestion path. If time is short, **cut this before you cut T2-2 or T2-4** — it is the item most likely to be read as padding.

---

### T2-4 · Recalibration protocol for OIL data — the exact plan

**WHAT.** A written, rehearsed, timed procedure for what happens in the 90 minutes after Oil India hands over CSS cycle records — which parameters get refit, by what method, with what train/validation split, in what compute budget, and what gets shown to judges.

**WHY.** `digital_twin_oilfield_deep_dive.md` §1.4: *"The recalibration loop is the thing that makes it a twin"*, with three cadences (seconds: state estimation; daily/weekly: parameter re-fitting; per-cycle: re-history-match the thermal model). §6.2 Challenge 2's rebuttal depends on being able to describe it. SPE-185716-MS reports **>20% SOR reduction** from exactly *"fast modelling + data-assimilation algorithms applied to mature heavy-oil fields"* (https://onepetro.org/SPEWRM/proceedings-abstract/17WRM/17WRM/D031S003R001/196053) — data assimilation is the mechanism behind the target number we quote.

**HOW — the protocol.**

**(a) What gets refit, ranked by identifiability from cycle-level records.**

| # | Parameter | File | Identified from | Prior |
|---|---|---|---|---|
| 1 | `AOF_REF_M3D` = 0.7 | `twin/ipr.py` | day-1 post-soak oil rate (it is a productivity index in disguise) | log-uniform 0.1–5 |
| 2 | `COOLDOWN_TAU_DAYS` = 20 | `twin/thermal.py` | the *shape* of the produce-phase decline curve | log-uniform 5–60 |
| 3 | `DRAINAGE_RADIUS_M` = 8.0 | `twin/thermal.py` | curvature of SOR vs slug size **across ≥3 cycles with different steam volumes**, or well spacing if given | uniform 4–20 |
| 4 | `K_VISC` = 10.0 | `twin/srp.py` | measured polished-rod load range: `F_visc ≈ PRL_peak − W_buoyant − F_fluid`; from dyno cards if available | log-uniform 1–100 |
| 5 | effective downhole steam quality | `params.steam.quality` = 0.65 | injection pressure/temperature + a wellbore-loss term; else fit as an efficiency multiplier | uniform 0.2–0.7 |
| 6 | `mu_ref_cP`, `andrade_B_K` | `params.fluid` | **measure, do not fit** — lab viscosity points. Only fit `B` if no lab data, and flag it | from lab |

**Identifiability warning to state out loud (it is the mark of someone who has actually done this):** steam quality × latent heat × drainage radius enter the heated-volume term **multiplicatively** and are not separately identifiable from production data alone. **Fix two from measurement, fit one.** The same applies to `COOLDOWN_TAU_DAYS` and the Andrade `B` — both control how fast rate declines, so fit `B` from lab viscosity and leave `τ` as the free one.

**(b) Method — two stages, both laptop-feasible.**
- **Stage A (MAP, seconds):** `scipy.optimize.least_squares` over log-parameters; residuals = daily oil rate for the history-matched cycle (weighted), plus cycle SOR and cycle length. ~300–500 twin evaluations. **[MEASURED]** at 0.55 ms/run: **< 1 second.**
- **Stage B (posterior, ~1 minute):** either `emcee`, 32 walkers × 2,000 steps = 64,000 twin evaluations ≈ **35 s**, or a dependency-free LHS-plus-importance-resampling over 20,000 points ≈ **11 s**. Output: posterior median + 90% credible interval per parameter, propagated into the recommendation's band (this is what makes T1-4's interval mean something on real data). Frame it against the literature: this is the small-dimensional analogue of the **Ensemble Kalman Filter** that `digital_twin_oilfield_deep_dive.md` §1.4 names as the reservoir-engineering standard (https://arxiv.org/pdf/1204.3547).

**(c) Split discipline.** **Leave-last-cycle-out**: fit on cycles 1…n−1, validate on cycle n. If several wells: **leave-one-well-out**. **Never random-split days inside a cycle** — consecutive days are near-perfectly autocorrelated, and a random split leaks the answer and produces a meaningless R². Say this unprompted; it is the fastest way to signal that you have done real time-series work.

**(d) Measured time budget for the whole loop, on this laptop.**

| Step | Budget |
|---|---|
| Ingest + QC cycle records (the human part) | 30–60 min |
| Stage A MAP fit | < 1 s |
| Stage B posterior | 11–35 s |
| Regenerate 3,000-cycle training set at the new params | **~3.6 s** ([MEASURED] 4,000 cycles in 4.8 s) |
| Retrain all surrogates | < 10 s |
| Re-run the optimizer (post-T1-2) | ~6 s |
| **Total machine time** | **< 90 seconds** |

That number is a pitch asset in itself: *"give us your cycle records over lunch and the twin is re-history-matched, re-trained and re-optimised before the coffee arrives."*

**(e) What to show judges.** One two-panel figure: **predicted vs measured daily oil rate for the held-out cycle, before and after assimilation**, with RMSE printed on each panel; plus a small table of prior → posterior for each fitted parameter with its 90% interval. The honest caption: *"Boberg–Lantz temperature predictions can differ from numerical simulation by up to 42% over 300 days (`css_thermal_eor_deep_dive.md` §2.2, https://www.sciencedirect.com/science/article/pii/S2405656118301755) — that residual is precisely what this step absorbs."*

**Rehearse it now, before the finale**, on *pseudo-field* data: perturb the twin's true parameters, generate a "field" cycle with noise, hide the truth, and run the protocol. You then have a working demo, a measured before/after RMSE, and no dependency on OIL handing anything over.

**EFFORT.** **M** for the rehearsal harness; the protocol itself is written above. **DEMO VALUE.** Highest of any Tier-2 item for a *technical* jury — it is the direct answer to "this is just a dashboard." **RISK.** OIL provides nothing, or provides monthly allocated volumes rather than daily rates — mitigate by having a coarse-data variant of the protocol (fit on cycle-level SOR, oil total and duration only; note that `τ` becomes weakly identified and widen its posterior accordingly).

---

### T2-5 · Adaptive sampling / active learning

**WHAT.** Replace part of the blind 3,000-point LHS with acquisition-driven sampling: seed with ~500 LHS cycles, then iteratively add batches where the ensemble disagrees most and where the objective is most promising.

**WHY.** `digital_twin_oilfield_deep_dive.md` §4.2 — Bayesian optimisation *"converged within 20 reservoir simulation runs"* for well inflow-control design (https://onepetro.org/OTCONF/proceedings/20OTC/1-20OTC/D011S002R003/107796); surrogates reach **>2000× speedup at ~10% error** (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7931866/). **[MEASURED]**, the *compute-saving* argument is weak for us — 3,000 cycles cost ~3.6 s — so pitch this honestly on the two grounds that do hold:
1. **Accuracy where it matters.** Uniform LHS spends 20% of its budget on designs with SOR > 3 that nobody will run. Concentrating samples near the optimum is what drives the near-optimum MAE (currently 0.019) down further, and shrinks the T1-4 band that appears on screen.
2. **Architectural honesty.** The method is the one that survives swapping our 0.55 ms twin for a CMG-STARS run at hours per case. Say: *"our twin is fast, so we can afford brute force today — we built the sample-efficient path because the production version won't be."*

**HOW.** Bag 5 XGBoost regressors on bootstrap resamples → ensemble mean and std → acquisition = `mean − κ·std` (LCB) plus a pure max-std exploration term; propose a batch of 50 per round with a minimum-distance filter to avoid clustering; 10 rounds of 50 = 500 adaptive points on top of 500 LHS. Compare against a 3,000-point LHS baseline on **two** metrics: global envelope R², and **MAE inside a ball around the optimum** — the second is the one that should improve, and the honest report says so.

**EFFORT.** **M.** **DEMO VALUE.** Moderate — it is a methods slide, not a screen feature. **RISK.** Over-claiming ("we cut simulation cost 6×") when our simulator costs 3.6 seconds — a sharp judge will time it. Use the two honest framings above.

---

## 4. TIER 3 — pilot / post-SIH

### T3-1 · Multi-well steam allocation (the scarcity finding, as a daily decision)

**WHAT.** Given 74 tpd of steam and N candidate wells, allocate tomorrow's steam to maximise field-level ₹, using per-well surrogates ranked on **marginal ₹ per tonne of steam** (the T1-1 objective is already in the right currency).

**WHY.** `css_thermal_eor_deep_dive.md` §3: *"74 tpd of steam is a small, precious resource — Cold Lake runs orders of magnitude more — which makes allocation optimisation (which well gets the next slug) more valuable here than almost anywhere"*; §6 Q5 names *"a ranked allocation of the day's 74 tpd across candidate wells"* as one of the three things a twin owes an operator on Monday morning. Precedent: real-time ML steam allocation for digital heavy-oil reservoirs, SPE-195329 (https://onepetro.org/SPEWRM/proceedings-abstract/19WRM/19WRM/D021S004R004/218855), and Suncor Firebag's two-decade steam-distribution optimisation programme (`digital_twin_oilfield_deep_dive.md` §2.3).

**HOW.** Per-well parameter vectors (post-T2-4 calibration) → surrogate margin curve `f_w(steam_t)` → greedy or DP knapsack on the concave part, with a lexicographic tie-break on floating risk. **[MEASURED]** feasibility: 33 wells × 200 slug sizes = 6,600 candidates ≈ **14 ms** batched. **EFFORT.** M–L (needs per-well params). **DEMO VALUE.** Very high at pilot; a stacked bar of "today's 74 t, allocated" is a control-room artifact. **RISK.** Requires per-well calibration (T2-4) — do not attempt on shared parameters, or every well returns the same answer.

### T3-2 · Cycle-index degradation and the "stop CSS" signal

**WHAT.** Add cycle number and a depletion state as features; predict SOR drift across cycles and emit the cycle at which forecast incremental revenue crosses forecast steam cost.

**WHY.** `css_thermal_eor_deep_dive.md` §1.3: peak rates in cycles 2–3, sharp fall through 4–6; Liaohe Block D **SOR rose 2.86 → 3.56** over ~20 years as pressure fell 7.4 → 2.9 MPa. §6 Q5 calls the stop signal *"the practical definition of when CSS stops paying."* **Blocked on physics** — the twin currently holds `P_res` constant and has no inter-cycle state. **EFFORT.** L. **RISK.** Without real multi-cycle data this is a modelled assertion; label it a forecast structure, not a prediction.

### T3-3 · Sequential assimilation at three cadences

**WHAT.** Promote T2-4's batch calibration to a running EnKF/particle filter: seconds (state), daily (parameters), per-cycle (thermal history match). **WHY.** `digital_twin_oilfield_deep_dive.md` §1.4 — the three cadences are what separate a twin from a shadow, and EnKF is the named standard (https://arxiv.org/html/2601.01321v1). **EFFORT.** L. **DEMO VALUE.** It is the DNV Level 4→5 evidence.

### T3-4 · Real-card fine-tuning and failure lead time

**WHAT.** Fine-tune T2-3 on OIL's cards; add a failure-prediction head on the scaled load ratio. **WHY.** SPE Journal 233386: **F1 0.857 at 13.97 days average lead time from surface data only**. Target: match that F1 on Baghewala cards. **EFFORT.** L, blocked entirely on data.

---

## 5. Metric targets by tier

Stated so they can be checked against `metrics.json` after each item lands.

### Tier 1 targets (internal round)

| Metric | Today [MEASURED] | Target | Source of the target |
|---|---|---|---|
| SOR regressor R², **in-envelope** (SOR ≤ 8) | 0.7246 (all designs) | **≥ 0.98** | measured 0.987 in a trial fit (T1-3) |
| SOR regressor MAE, in-envelope | 0.3068 | **≤ 0.08 t/m³** | measured 0.0705 |
| SOR regressor MAE, near-optimum (SOR < 1.2) | 0.0193 (unreported) | **≤ 0.03, reported** | measured |
| Viability-gate AUC | n/a | **≥ 0.99** | measured 0.9992 |
| `oil_total_m3` R² / MAE | n/a | **≥ 0.99 / ≤ 25 m³** | measured 0.998 / 16.5 |
| `days_total` R² | n/a | **≥ 0.99** | measured 0.9988 |
| Floating classifier AUC | 0.9989 | hold ≥ 0.99 | — |
| **Verification gap** \|surrogate − twin\| at the recommendation | 1.19% (quoted, not computed in code) | **computed every run, ≤ 3%** | current 1.2%, `TEAM_STUDY_GUIDE.md` §4.3 |
| Conformal 90% interval, empirical coverage on holdout | n/a | **0.90 ± 0.03** | conformal guarantee |
| Interval half-width at the recommendation | ±0.31 (global MAE) | **≤ ±0.05** | measured local q90 ≈ 0.02–0.04 |
| Optimizer wall time | 22.3 s | **≤ 8 s** | measured: 4,000 twin evals = 4.8 s |
| Physics-verified SOR at the recommendation | 0.8922 | **≤ 0.86** | measured LHS best 0.8497 |
| Margin at the recommendation | not computed | **≥ ₹6.5 cr/cycle, ≥ ₹35k/t-steam** | derived, T1-1 table |
| Bound-pinned variables | 2 of 4, unreported | **reported every run** | — |
| Seed robustness (5 seeds) | unknown | **objective spread ≤ 2%** | — |

### Tier 2 targets (finale)

| Metric | Target | Note |
|---|---|---|
| Schedule search: 6-D, verified margin vs best static-SPM | **≥ +10% ₹/t-steam** | the schedule must *earn* its dimensions or it is complexity for its own sake |
| Schedule recommendation inside the published band for the cold tail | **SPM ≤ 7 once µ > 1,000 cP** | `srp_dynamometer_ml_deep_dive.md` §5.1 |
| Card classifier, synthetic corpus | **≥ 95% accuracy, ≥ 0.85 recall on every class** | quote per-class recall; never headline the accuracy |
| Card classifier, published comparator | cite **99.50% / 99.84%** as the bar | Sensors 2020 / 2021 |
| Scaled load ratio vs `floating_index` correlation | **\|r\| ≥ 0.8** on synthetic cards | the bridge to SPE 233386 |
| Recalibration: held-out-cycle oil-rate RMSE, before → after | **≥ 50% reduction** | shown as the two-panel figure |
| Recalibration: total machine time | **≤ 120 s** on a laptop | measured budget = 90 s |
| Adaptive sampling | **near-optimum MAE at 1,000 cycles ≤ MAE at 3,000 LHS cycles** | the honest efficiency claim |

### Tier 3 targets (pilot)

| Metric | Target | Source |
|---|---|---|
| Field-level SOR reduction vs pre-twin baseline | **≥ 20%** | SPE-185716-MS, `css_thermal_eor_deep_dive.md` §4 |
| Rod-failure-rate reduction | **14% (conservative) → 38% (AI-enabled upper end)** | Amoco 671 wells / Chord–Ambyint 2,500 wells |
| Recommendation acceptance rate (the trust metric) | **≥ 60% by end of advisory phase** | `digital_twin_oilfield_deep_dive.md` §3.3 |
| Twin-vs-measured rate error, shadow phase | **≤ 15% on a full CSS cycle** | phase-1 graduation gate, §3.3 |
| Card classifier on real OIL cards | **≥ 95%, per-class recall reported** | derated from 99.5% for a small first corpus |
| Failure prediction | **F1 ≥ 0.80, lead ≥ 10 days** | derated from SPE 233386's 0.857 / 13.97 d |

---

## 6. Three pitch sentences gained, per Tier-1 item

Written to be said out loud, unedited.

**T1-1 — ₹ objective**
1. "The optimizer doesn't minimise a ratio any more — it maximises rupees: at ₹8,400 a tonne for diesel-fired steam, our recommendation is worth **₹2.3 crore more margin per cycle** than current field practice, at **31% less CO₂ per barrel** (45.7 → 31.5 kg/bbl)."
2. "We optimise on **rupees per tonne of steam**, not per cycle, because Baghewala makes 74 tonnes of steam a day for the whole field — one cycle eats three weeks of it, so steam is the scarce resource and its shadow price is the right objective."
3. "At today's diesel price a CSS cycle stops paying at an SOR of **4.6**; on gas-fired steam that break-even moves to 40 — which is why our first recommendation to Oil India isn't a setpoint, it's the fuel."

**T1-2 — physics verification + two-stage search**
1. "The optimizer doesn't trust the machine learning either: it re-runs the full physics twin on its own recommendation and prints the difference — today it's **1.2%**."
2. "Our twin runs in **half a millisecond**, so the surrogate isn't there to save time on this model — it's there because the search is batched at two microseconds a candidate, and because the same architecture works when you swap our twin for a reservoir simulator that takes hours."
3. "We tested three search strategies against each other on wall-clock and on the physics-verified answer, and shipped the one that won — that's why the number on screen is 0.85 and not 0.89."

**T1-3 — viability gate + envelope metrics**
1. "R-squared **0.99** on the 96% of cycle designs that are economically viable, and a separate gate that flags the other 4% at an AUC of 0.999 — because a model that tells you a hopeless cycle is 'very bad' rather than 'extremely bad' isn't doing any useful work."
2. "We publish both numbers — 0.99 in the envelope and 0.72 across every design including the absurd ones — and we defined the envelope from the world CSS literature band before we fit anything."
3. "The optimizer now has a third output nobody asks for and every operator needs: **don't run this cycle at all.**"

**T1-4 — native uncertainty**
1. "Every recommendation ships with a **90% conformal prediction interval**, calibrated on held-out data, not a hand-waved error bar."
2. "At the recommended point that interval is ±0.02, not the ±0.31 our global error suggests — and the physics re-check landed 0.011 away, inside the band. Three independent numbers, one answer."
3. "We report the interval that belongs to *this* recommendation, not the average over a design space most of which nobody would ever operate in."

**T1-5 — constraint and bound realism**
1. "Two of our four variables sit on a search bound — we print that on the screen, because an optimum on a bound is a statement about your search box, not about the reservoir."
2. "Our optimizer wants 10 strokes a minute and the heavy-oil textbook says 3 to 6 — and it's right, because during the produce window the oil is **3 to 850 centipoise, not 11,500**; the cutoff ends the cycle before the rods ever see cold oil. We show both recommendations and the gap between them is the business case for a VFD."
3. "We don't optimise soak time, because our thermal model only loses heat during a soak — so we report Baghewala's actual 7-to-13-day practice and flag the model gap instead of pretending we found something."

---

## 7. Traps to avoid

1. **Do not claim novelty on dyno-card classification.** 99.50% and 99.84% are published on real cards. Cite them as the bar, position T2-3 as the ingestion path (`srp_dynamometer_ml_deep_dive.md` §6.2 Q1 already scripts this).
2. **Do not headline synthetic-data accuracy** for any model. Every number in `metrics.json` is held-out *synthetic*. `TEAM_STUDY_GUIDE.md` §6 row 52: "Real CSS cycles in our training data: **ZERO**." Keep saying it.
3. **Do not quote the in-envelope R² alone.** Always with coverage and the all-designs number.
4. **Do not let the dashboard and `params/` disagree on money again** (F6). One source of truth, printed on screen.
5. **Do not claim a global optimum.** BO, DE and LHS are all heuristics; T1-2's physics verification is a *check*, not a proof. `TEAM_STUDY_GUIDE.md` already flags the "guaranteed global optimum" bait.
6. **Do not add dimensions without adding data.** T2-2 takes the space from 4-D to 6-D; the dataset must grow with it (cheap: ~10 s).
7. **Do not present a soak recommendation** until the physics has a soak benefit. It is currently monotone by construction.

---

## Appendix A — reproducing every measurement in this document

All timings on the user's laptop, `.venv` interpreter, 13-Sep-2026. Run from the repo root.

```bash
# dataset + twin speed (0.55 ms/cycle; 3,000 rows; mean SOR 2.96; 24.3% float-positive)
./.venv/Scripts/python.exe -c "import time,json,sys;sys.path.insert(0,'.');from twin import cycle;p=json.load(open('params/field_params.json'));t=time.perf_counter();[cycle.simulate_css_cycle(1500,7,3.0,8.0,p) for _ in range(20)];print((time.perf_counter()-t)/20*1000,'ms')"

# surrogate sliced error (global 0.7246/0.3068; steam 1200-2400t -> 0.992/0.036; SOR<1.2 -> MAE 0.019)
# hurdle trial fit (gate AUC 0.9992; viable-only R2 0.987/MAE 0.0705; oil R2 0.998; days R2 0.9988)
# conformal |res| quantiles (q90 = 0.213 global, 0.141 viable-only)
#   -> see the sliced-metrics and hurdle scripts in the analysis transcript; both are
#      ~20-line scripts over data/synthetic_cycles.csv + ml/models/sor_model.joblib

# optimizer wall time (22.27 s) and the verification gap (0.8816 surrogate vs 0.8922 twin)
./.venv/Scripts/python.exe -c "import time,json,sys;sys.path.insert(0,'.');from ml import optimize as O;p=json.load(open('params/field_params.json'));t=time.perf_counter();r=O.best_settings(p);print(time.perf_counter()-t,r['predicted_SOR'])"

# true-twin LHS sweep (4,000 evals in 4.8 s; best feasible SOR 0.8497)
# SPM-capped sweeps (spm 3-6 -> best SOR 1.2986; spm 4-12 -> 0.8072)
# soak / spm monotonicity sweeps
#   -> qmc.LatinHypercube over the field_params ranges, filtered on summary()['max_floating_index'] <= 0.6
```

**Key measured constants, for reuse in the deck:**

| Quantity | Value |
|---|---|
| One twin cycle (simulate + summary) | 0.55 ms |
| One single-row XGBoost predict | 1.13 ms |
| Batched XGBoost predict | 2.1 µs/row |
| `best_settings()` end to end | 22.27 s |
| 4,000 true-twin evals + constraint check | 4.8 s |
| Surrogate SOR at the recommendation | 0.8816 |
| Physics-verified SOR at the same point | 0.8922 (**+1.19%**) |
| Best feasible SOR, 4,000-point true-twin LHS | 0.8497 |
| Best feasible SOR with SPM capped at 3–6 | 1.2986 (vs field reference 1.2943) |
| Produce-phase viscosity range at the recommendation | 3.5 → 850 cP |
| Pump-capacity-limited days at the recommendation | ~15 of 30 produce days at 95.8 m³/d |
| Uneconomic designs in the dataset (SOR > 8) | 4.13% |
| Economic break-even SOR (₹8,400/t, ₹6,160/bbl) | 4.61 t/m³ |

---

*Companion documents: `docs/research/deep-dives/css_thermal_eor_deep_dive.md` (economics, CSS optimisation literature), `docs/research/deep-dives/srp_dynamometer_ml_deep_dive.md` (card ML, SPM practice, scaled load ratio), `docs/research/deep-dives/digital_twin_oilfield_deep_dive.md` (surrogate/BO justification, DNV levels, deployment gates), `docs/study/TEAM_STUDY_GUIDE.md` §4 and §6 (what the team must be able to say), `docs/reviews/ui_review_ux.md` (P1-1, the uncertainty display).*
