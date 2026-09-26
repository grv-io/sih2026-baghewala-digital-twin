> **UPDATE 27 Sep 2026 — Economics v2 on branch `physics-v3`.** See §8: incremental oil over the cold well (SOR_incr 5.40 at the reference vs gross 4.03), daily opex, srp energy fixed (3× lower). At the base price deck incremental margin is negative everywhere; cascade recommendation 1,600 t / 10 d / 0.70 m³/d / 4 spm. `pytest -q` → 116 passed, 1 xfailed.

> **UPDATE 26–27 Sep 2026 — physics v3 on branch `physics-v3`.** See §7: BL δ sourced (½ is Boberg–Lantz's own, energy-fixed) and computed per PEH Eq. 15.74; P_res benchmark re-specified (Darcy band); soak xfail kept. Reference SOR 4.03, margin +₹10.6 L. `pytest -q` → 67 passed, 1 xfailed.

> **UPDATE 26 Sep 2026 — rev 5 calibration done on branch `physics-v2`.** See §4 below.
> Reference 1,500 t / 7 d / 1.2 m³/d / 5 spm → SOR 4.09, uplift 5.66×, peak 15.9 bbl/d,
> 182-d produce phase, margin +₹8.8 L at bulk diesel. `pytest -q` → 57 passed, 2 xfailed
> (strict; P_res sensitivity and soak optimum are recorded misses). `ml/`, `data/`,
> `dashboard/`, `ppt/` are **not** regenerated yet — still v1.

# Tier-1 physics implementation — progress log (interrupted mid-task)

**SAFE TO COMMIT: yes** — all modules import, no syntax errors, `pytest tests -q` →
**21 passed / 3 failed** (two of the three are *by-design* breaks the plan predicted; the third
is a real calibration gap, see §Gotchas). The engine runs end to end and is already far more
honest than the old one (peak 13–23 bbl/d vs the old 471 bbl/d), but it is **not yet calibrated**
and no new test files were written. Do not quote these numbers in the deck yet.

Written 2026-09-13 by the Tier-1 physics implementer, stopped on user request partway through.
Spec being executed: `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_PHYSICS.md` (T1-A … T1-H).

---

## 1. Status per item

| Item | Status | Files / functions touched |
|---|---|---|
| **T1-A** composite-radial PI | **DONE** | `twin/ipr.py`: new `composite_uplift()`, rewritten `oil_rate_m3d()`; constants `S_COLD=5.0`, `MAX_UPLIFT=10.0`, `P_CAL_KPA=11400`, `AOF_REF_M3D` 0.7→**0.60**. `twin/thermal.py`: `DRAINAGE_RADIUS_M` **deleted**. `twin/cycle.py`: produce loop sets `params_run["heated_radius_m"]` / `["T_avg_C"]`. `params/field_params.json`: `reservoir.drainage_radius_m=100`, `reservoir.well_radius_m=0.1`. |
| **T1-B** Boberg–Lantz cooldown | **DONE** | `twin/thermal.py`: `slab_theta()`, `boberg_lantz_theta()`, `retained_heat_J()`, rewritten `steam_zone_temperature()`; `COOLDOWN_TAU_DAYS` **deleted**; `BL_UNCERTAINTY_FRAC=0.42` added. `twin/cycle.py`: δ accumulator `params_run["Q_removed_J"]`, `CP_LIQUID_JM3K=4.0e6`, `fluid.water_cut=0.85`. |
| **T1-C** `P_res(t)` recharge/bleed | **DONE (uncalibrated)** | `twin/cycle.py`: `_p_res_at()`, `_pump_intake_pressure_kPa()`, `PRESSURE_BOOST_PER_T_KPA=2.0`, `TAU_BLEED_D=25.0`, `PUMP_SUBMERGENCE_M=100`, `CASING_HEAD_PRESSURE_KPA=200`; `PWF_DRAWDOWN_FRACTION` **deleted** (P_wf is now absolute → P_res is live). |
| **T1-D** declining-SPM schedule | **DONE** | `twin/srp.py`: `max_spm_for_viscosity()`, `fall_velocity_ms()`, `_fall_velocity_ms()`. `twin/cycle.py`: produce-loop `spm_cap`/`spm_t`, `SPM_MARGIN=0.6`, `DEFAULT_SPM_FLOOR=2.0`, new `spm_floor` kwarg on `simulate_css_cycle`. `params`: `srp.spm_floor=2.0`, `srp.spm_practice_band=[3,6]`. |
| **T1-E** fillage / graded damage | **DONE** | `twin/srp.py`: `FILLAGE_MAX=0.85` replaces `VOLUMETRIC_EFFICIENCY`; new keys `fillage`, `v_fall_ms`, `v_stroke_ms`, `descent_violation`, `pump_capacity_m3d`. `twin/cycle.py::summary()`: `rod_float_damage_index`, `days_rods_in_compression`, `min_fillage`, `mean_fillage`, `descent_violation_days` (legacy `failures_expected` kept). |
| **T1-F** Walther / ASTM D341 + floor | **DONE** | `twin/viscosity.py` rewritten: `_fit_walther()`, `_walther_nu_cSt()`, `walther_coefficients()`, `_sg_from_api()`; `mu_cP()` resolution order walther → explicit andrade → fitted walther, floored at `fluid.mu_floor_cP=1.0`. `params`: `fluid.walther_A/B=null`, `mu_floor_cP=1.0`. **Verified: μ(290 °C)=4.13 cP** (was 0.63 cP), μ(240)=7.58, μ(130)=97.7, μ(50)=11500 exactly. |
| **T1-G** ₹/CO₂/margin in summary | **DONE (objective side only)** | `params/field_params.json`: new `economics` block (constants copied from ECON plan §1.2 with sources). `twin/cycle.py`: `steam_cost_inr_per_t()`, `co2_kg_per_t_steam()`, `_DEFAULT_ECONOMICS`, and summary keys `oil_bbl`, `peak_oil_m3d`, `peak_oil_bbl_d`, `steam_cost_inr`, `cost_inr_per_bbl`, `co2_t`, `co2_kg_per_bbl`, `revenue_inr`, `margin_inr`, `margin_inr_per_cycle_day`. `summary()` gained an optional `params=None` arg (backward compatible). **NOT done:** `ml/optimize.py` re-target (out of scope for this agent — Phase 2). |
| **T1-H** wellbore loss + latent heat | **DONE** | `twin/thermal.py`: `wellbore_delivery()`, applied in `_retained_heat_J_at()`. `params`: new `wellbore` block (`VIT`, `heat_loss_frac_per_1000m=0.10`, `quality_at_sandface_frac_of_wellhead=0.55`), `steam.latent_heat_Jkg` 1.3e6→**1.40e6**. |
| **Recalibration pass** | **DONE 26 Sep (rev 5)** | see §4; `params/CHANGELOG.md` rev 5 |
| `tests/test_field_plausibility.py` | **NOT STARTED** | |
| `tests/test_benchmarks.py` | **DONE 26 Sep** (22 benchmark tests incl. 2 strict xfails) | |
| Old-test replacements (4) | **DONE 26 Sep** + the 2 vacuous tests and the retired-P_wf IPR test fixed | |
| `twin/generate_data.py` new columns / 300-cycle sample | **NOT STARTED** | file untouched |
| `params/CHANGELOG.md` update | **DONE** (rev 4 on main; rev 5 on `physics-v2`) | |
| `docs/research/deep-dives/…PHYSICS.md` IMPLEMENTATION NOTES | **NOT STARTED** | |

`api/`, `dashboard/`, `ml/`, `ppt/`, `docs/`, `docs/reviews/` — **not touched**, as instructed.
`requirements.txt` — unchanged, no new dependency needed (`math.erf` is stdlib).

---

## 2. Current pytest state — **3 failed, 21 passed in 0.87 s**

| Failing test | By design? | What to do |
|---|---|---|
| `test_cycle.py::test_full_cycle_smoke` | **Yes (2 reasons)** | (a) `assert list(df.columns) == EXPECTED_COLUMNS` — 5 columns were appended (`spm`, `fillage`, `v_fall_ms`, `heated_radius_m`, `uplift`). Replace with `list(df.columns)[:10] == cycle.SPEC_COLUMNS` per plan §Tests. (b) `1.0 < SOR < 15.0` currently *passes* at cutoff 3.0? No — at the test's `cutoff_m3d=3.0` the cycle ends immediately (peak is now ~2.8 m³/d), so SOR is huge. **The test's `cutoff_m3d=3.0` is a stale, pre-recalibration literal** — it must come down to ~1.0–1.5 in every test that hardcodes it (`test_cycle.py` uses 3.0 in five places). |
| `test_cycle.py::test_SOR_has_interior_optimum_over_steam_volume` | **Yes** | Delete; replace with `test_margin_has_interior_optimum_over_steam_volume` (margin_inr_per_cycle_day at 1,000 t > at 500 t and > at 3,000 t). Plan §Tests row 1. **Currently margin is monotone-ish decreasing (see §3) so this replacement will NOT pass until recalibration is done.** |
| `test_thermal.py::test_temperature_decays_toward_reservoir_after_injection_stops` | **Yes** | Only the last assertion. Measured now: `(T+90 − T0)/(T_peak − T0) = 119.79/240 = 0.499`. Replace the `< 0.2` magnitude check with `0.3 < ratio < 0.8` and add "slower than a τ=20 d exponential at 30 d" (θ(30) ≈ 0.69 vs exp(−1.5)=0.223). The three monotone assertions already pass. |

All 21 others pass unchanged, including every `test_srp.py` monotonicity/bounds test (the
`floating_index` value is algebraically identical after the rename) and
`test_viscosity.py::test_reference_point_recovered` (Walther two-point fit is exact).

---

## 3. THE ONE BLOCKER: recalibration (do this first)

Measured sweep at `soak_days=7, cutoff_m3d=1.5, spm=8` on the real params, **today**:

| steam_t | oil m³ | SOR t/m³ | produce d | peak bbl/d | max uplift | r_h m | margin ₹/cycle-day |
|---|---|---|---|---|---|---|---|
| 500 | 55.9 | 8.94 | 29 | 13.4 | 3.43 | 3.11 | −95,327 |
| 1,000 | 106.7 | 9.37 | 50 | 15.8 | 3.79 | 4.31 | −95,216 |
| 1,500 | 152.6 | 9.83 | 67 | 17.8 | 4.03 | 5.21 | −100,833 |
| 3,000 | 275.6 | 10.88 | 108 | 23.3 | 4.51 | 7.15 | −117,815 |

**What is already right:** peak rate 13–23 bbl/d (target 15–40 ✔ at ≥1,000 t), uplift 3.4–4.5×
(target 4–8, close), r_h 3–7 m, SOR monotone increasing in steam_t exactly as the plan predicted,
viscosity floor honoured.

**What is wrong:** oil per cycle is ~2.2× too low, so **SOR is 9–11 against the 3–8 target**, and
**produce phase is 29–108 d against the 60–220 d target**. Both are the same single defect:
the well produces too little for too short a time.

**Recommended next step, in order (each is one constant, re-run the sweep after each):**

1. **Raise `ipr.AOF_REF_M3D` 0.60 → ~1.3–1.5.** This is the primary knob; oil and produce-days
   both scale with it roughly linearly. Target: SOR ≈ 4.4 at 1,500 t, i.e. oil ≈ 340 m³
   (the plan's own prototype number).
2. **Then re-set `css.cutoff_rate_m3d_range` (currently `[0.5, 2.5]`) so that
   `cutoff_lo > cold_rate`.** The coupling is exact and it is a trap:
   `test_ipr.py::test_cold_rate_is_uneconomically_low` computes
   `q_cold = AOF_REF_M3D × 0.792` (uplift = 1 when no `heated_radius_m` is in params) and asserts
   `q_cold < cutoff_rate_m3d_range[0]`. At AOF 1.4 → q_cold = 1.11, so the range must become
   about `[1.2, 4.0]`. **Change both in the same commit or that test lies** (plan §Tests row 3).
   Note raising `cutoff_lo` shortens cycles again — expect one or two iterations.
3. **If produce-days are still short after 1+2, lower `fluid.water_cut` 0.85 → 0.75.** δ (the
   Boberg–Lantz energy-removed term) is proportional to `1/(1−water_cut)`, so 0.85 is what is
   currently collapsing the tail of the cycle. It is a flagged ASSUMPTION param with no field
   datum, so moving it is legitimate — but say so in the CHANGELOG.
4. **Only then check the margin interior optimum.** Right now margin/cycle-day is essentially
   flat-to-declining in steam_t (−95k at 500 t and 1,000 t, worse above), so
   `test_margin_has_interior_optimum_over_steam_volume` would fail. It should appear once oil per
   cycle roughly doubles, because revenue grows with oil while `fixed_cost_inr_per_cycle` is
   amortised over more days. If it still does not appear, the honest fix is to re-check
   `economics.oil_price_inr_per_bbl` (4,840) and `fixed_cost_inr_per_cycle` (1.5e6), **not** to
   reintroduce a saturation fudge.
5. **Do the recalibration ONCE**, as the plan's dependency graph insists — not per item.

---

## 4. Calibration log — 26 Sep 2026 (rev 5, branch `physics-v2`)

Harness: scratch benchmark script (reference row + steam / soak / SPM / P_res / cutoff
sweeps; columns SOR, oil, produce days, peak bbl/d, peak/cold uplift, composite uplift,
μ_min, FI_max, fillage, mean SPM, float damage, ₹/cycle-day, margin). Every change was
re-run through the full table. Values changed are listed old → new in
`params/CHANGELOG.md` rev 5.

### 4.1 Before (rev 4, as committed)

| Case | SOR | oil m³ | produce d | peak bbl/d | peak/cold | FI_max | ₹/cycle-day |
|---|---|---|---|---|---|---|---|
| 1500/7/**3.0**/8 (old reference) | **529.7** | 2.8 | 1 | 17.8 | 4.86 | 0.00 | −512,017 |
| 1500/7/1.5/8 | 9.83 | 152.6 | 67 | 17.8 | 4.86 | 0.58 | −100,833 |
| steam 500 / 1000 / 1500 / 3000 (cutoff 1.5) | 8.94 / 9.37 / 9.83 / 10.88 | | 29–108 | 13–23 | | | all negative, no interior optimum |
| soak 3 → 15 | 9.86 → 9.76 (flat) | | | | | | |
| spm 2 → 12 | 9.83 identical at every SPM (pump ~75 m³/d vs 2.8 m³/d well) | | | | | 0.15–0.60 | |
| P_res 11.4 → 7.4 MPa | +92 % | | | | | | |

### 4.2 Diagnosis (before tuning) — three internal inconsistencies

1. **Heat balance missed the sensible heat.** `thermal._retained_heat_J_at` credited only
   `x_sf·L_v` = 443 kJ/kg delivered. Marx–Langenheim's heat-injection rate is
   `C_w·ΔT + x_sf·L_v` = 1,581 kJ/kg at 36 % sandface quality — 3.6× more heat.
2. **Wellbore loss counted twice**: degraded sandface quality *and* a further `(1 − loss)`.
3. **Pump compared against oil only** while the δ term treats the produced stream as
   `oil/(1 − water_cut)`; at 85 % cut the pump's oil capacity was overstated 6.7×.

Also found: the Boberg–Lantz `f_HD` used a slab of thickness 2·r_h (documented Tier-3
approximation); the exact cylinder loses heat ~2× faster early. Closed form
`1 − e^{−x}[I0(x)+I1(x)]`, `x = r_h²/(2αt)`, verified numerically.

### 4.3 Iterations (reference row unless stated; cutoff / spm as given)

| # | Change | SOR | oil | prod d | peak | uplift | note |
|---|---|---|---|---|---|---|---|
| 0 | rev 4, 1.5/8 | 9.83 | 153 | 67 | 17.8 | 4.86 | baseline |
| 1 | + sensible heat, no double loss, liquid-basis pump (old pump), 1.5/5 | 3.05 | 491 | 186 | 22.7 | 6.19 | margin/day interior optimum appears (~1,000 t); P_res +46 % |
| 2 | + pump 1.75 in × 2.18 m, AOF 0.50, 1.0/5 | 3.02 | 497 | 239 | 18.9 | 6.19 | SPM now matters: 2 spm → 370 d, SOR 3.29 |
| 3 | + exact cylinder f_HD | 3.69 | 406 | 194 | 18.9 | 6.19 | energy-limited cycle shortens honestly |
| 4 | AOF 0.46, bulk diesel, 1.2/5 | 4.09 | 367 | 179 | 17.4 | 6.19 | margin +₹8.9 L; steam optimum 1,500 t; P_res +60 % |
| 5 | SPM_MARGIN 0.6 → 1.0 | 4.09 | 367 | 179 | 17.4 | 6.19 | FI > 0.6 now reachable (0.83 at 10 spm/cutoff 1.0) |
| 6 | PRESSURE_BOOST 2.0 → 1.0 kPa/t — **final** | **4.09** | **367** | **182** | **15.9** | **5.66** | uplift into BGW-8 band |

One-at-a-time sensitivities measured at iteration 2–4 (reference SOR response):
`BL_DELTA_FACTOR` 0.5 → 1.0: 3.02 → 5.07 (largest; left at 0.5, source not retrievable) ·
`water_cut` 0.75 / 0.90: 2.11 / 4.08 · AOF 0.4 / 0.7: 3.42 / 2.58 · S_COLD 2 / 8: 3.29 / 2.87 ·
r_e 60 / 150 m: 2.88 / 3.12 · TAU_BLEED 10 / 60 d: ±1 % · boost 0 / 4 kPa/t: ±0.3 % ·
sandface-quality ratio 0.3: 3.46 · cutoff 1.0 / 1.5 / 2.0: 3.02 / 3.43 / 4.15 (iteration 2).

### 4.4 After (rev 5 final; reference 1,500 t / 7 d / 1.2 m³/d / 5 spm)

Cold rate 0.447 m³/d (2.8 bbl/d); μ(50 °C) 11,500 exactly; μ(290 °C) 4.13 cP; r_h 9.8 m.

| Case | SOR | oil m³ | produce d | peak bbl/d | peak/cold | FI_max | ₹/cycle-day | margin ₹ L |
|---|---|---|---|---|---|---|---|---|
| **Reference** | **4.09** | **367** | **182** | **15.9** | **5.66** | 0.30 | **+4,245** | **+8.84** |
| steam 500 | 3.64 | 137 | 80 | 12.2 | 4.34 | 0.24 | −2,718 | −2.52 |
| steam 1,000 | 3.88 | 258 | 136 | 14.3 | 5.07 | 0.28 | +3,147 | +4.89 |
| steam 1,500 | 4.09 | 367 | 182 | 15.9 | 5.66 | 0.30 | **+4,245** ← max | +8.84 |
| steam 2,000 | 4.27 | 468 | 222 | 17.4 | 6.19 | 0.31 | +4,080 | +10.41 |
| steam 3,000 | 4.60 | 652 | 289 | 19.6 | 6.96 | 0.33 | +2,354 | +7.90 |
| soak 3 / 7 / 15 | 4.11 / 4.09 / 4.06 | | 180–185 | | | | 4,062 / 4,245 / 4,402 | |
| spm 2 | 4.76 | 315 | 253 | 7.8 | 2.78 | 0.12 | −2,510 | −7.01 |
| spm 3 | 4.20 | 357 | 202 | 11.7 | 4.18 | 0.18 | +2,556 | +5.83 |
| spm 4 / 6 | 4.09 | 367 | 182 | 15.7 / 15.9 | | 0.24 / 0.36 | +4,237 / +4,245 | |
| spm 12 | 4.09 | 367 | 182 | 15.9 | | **0.71** (9 alarm days) | +4,245 | |
| cutoff 0.6 (5 spm) | 3.55 | 423 | 247 | | | **0.88** (26 alarm days) | +9,484 | +25.9 |
| cutoff 1.0 / 1.5 / 2.0 | 3.88 / 4.48 / 5.90 | | 200 / 158 / 112 | | | | +6,540 / −495 / −18,430 | |
| P_res 9.4 / 7.4 MPa | +17 % / **+61 %** | | | | | | | |

Space-wide (400-row LHS over the params ranges, in memory — `data/` untouched):
median SOR 4.36, 32 % of cycles carry float-alarm days, 57 % margin-positive.

### 4.5 Verdict per target

- SOR 4–6 at reference: **4.09** ✔ (lower edge; 3.6–4.6 over 500–3,000 t, inside 3–8).
- Uplift 5–6×: **5.66** ✔ (5.1–5.7 over BGW-8's 1,040–1,560 t). Peak 15.9 bbl/d ✔ (edge).
- Produce phase 3–8 months: **182 d** ✔. Cold ≤ 0.5 m³/d: **0.447** ✔. μ bands ✔.
- Steam lever: SOR monotone ↑ (honest composite-radial result); **₹/cycle-day interior
  optimum at ~1,500 t** (1,000–2,000 t plateau) — on top of BGW-8's 1,040–1,560 t. ✔
- SPM lever: pump oil capacity 1.9 / 3.1 / 3.7 m³/d at 3 / 5 / 6 spm vs ~2.5 m³/d peak;
  3 spm is pump-limited for 141 days (SOR +3 %, ₹/day −40 %), 2 spm much worse; ≥4 spm
  no oil benefit but more float exposure. ✔
- FI binds: alarm trips at 12 spm (9 d) and at low cutoff (cold tail), never at the
  reference. ✔ This is the counterweight to the optimiser pushing the cutoff down
  (₹/cycle-day rises monotonically as cutoff falls, because cold-tail barrels still earn).
- Margin positive at reference: ✔ at bulk diesel (₹5,856/t); **−₹28.8 L at retail**.
- **P_res: +61 % ✘** vs +20–40 %. Rate ∝ drawdown and the cutoff is absolute, so a
  lower-pressure cycle hits it sooner; Liaohe's weak response comes from drive
  mechanisms we do not model (gravity drainage, compaction, solution gas). Strict xfail.
- **Soak: small monotone benefit only ✘** (SOR −1.2 % from 3 → 15 d; ₹/day argmax at the
  15-d edge). Boberg–Lantz has no soak benefit beyond conduction; heat redistribution
  into the pay and in-situ flashing on early production are not modelled. Strict xfail.
  Do **not** present "the twin says soak N days".

### 4.6 Porosity / thickness conflict (coordinator request, 26 Sep)

Yasin et al. 2022 (*Sci. Rep.* 12:11086) gives Baghewala-1 porosity 16–25 % and gross
Jodhpur Fm ~50 m vs our 0.09 and 12 m net. **Kept 0.09 / 12 m.**
- `reservoir.porosity` is **inert** (not read in `twin/`): 0.09 vs 0.20 → identical
  table. Propagated into a derived bulk heat capacity it moves SOR −0.3 %, r_h −1 %.
  Calibration is reachable at either value.
- `thickness_m` is first-order: 12 / 20 / 30 / 50 m → SOR 4.09 / 4.05 / 4.38 / 5.27,
  uplift 5.66 / 5.16 / 4.81 / 4.42, margin +8.8 / +9.8 / +1.3 / −16.3 L; at ≥30 m the
  steam response inverts. BGW-8's 5–6× is reproduced only for ~8–20 m net pay, so 50 m
  gross must not be used as steam-contacted thickness. Open item: net-pay datum.

### 4.7 Judgement calls the team should know before presenting

1. Base-case fuel is **bulk diesel (−30 %, unsourced discount)**, justified by revealed
   preference (19 CSS jobs in FY26). At retail every sensible cycle loses money. Say so.
2. `SPM_MARGIN` 0.6 → 1.0 changes the T1-D story: the VFD schedule now enforces the
   rods' physical limit; the 0.6 line is an alarm, not the schedule's target.
   `docs/study/*` still say "margin 0.6" (out of scope here).
3. `BL_DELTA_FACTOR = 0.5` is unverified against the 1966 paper and is the most
   sensitive constant (1.0 → SOR ≈ 5).
4. `water_cut = 0.85` implies ~139 % of injected water produced back in cycle 1 (high).
5. Pump geometry (1.75 in × 86 in) is TYPICAL, not Baghewala data — top data request.
6. Pressure boost has no physical anchor (injection BHP < virgin P_res); halved to 1.0.
7. ML surrogate, synthetic CSV, dashboard `BAKED` series and the deck are still v1.

---

## 5. Gotchas hit (read before touching anything)

- **`cutoff_m3d=3.0` is hardcoded in five places in `tests/test_cycle.py`.** With honest physics
  the peak rate is ~2.8 m³/d, so a 3.0 m³/d cutoff ends the cycle on produce day 1. Every test
  literal must be rescaled alongside `css.cutoff_rate_m3d_range`. This is the single most
  confusing failure mode — it looks like a physics bug and is not.
- **`P_wf` is now absolute (~1,144 kPa from 100 m submergence), not `0.4 × P_res`.** That is what
  makes the P_res sweep live (kills the inert-P_res bug, ECON §3.7 FAIL 3). `ipr.oil_rate_m3d`
  additionally scales `q_max` linearly with `P_res / P_CAL_KPA` (Vogel's `q_max = J·Pr/1.8`), so
  a P_res sweep now moves output **strongly** — verify the magnitude against the Liaohe D3
  benchmark (+24 % SOR for 7.4 → 2.9 MPa) before claiming it; it may over-respond.
- **`ipr.composite_uplift` returns exactly 1.0 when `heated_radius_m` is absent** (r_h clamps to
  `r_w·1.01`, skin `s = S_COLD`, the numerator and denominator coincide). That is deliberate: it
  makes the cold-well reference case exact and keeps `test_ipr.py` meaningful. Do not "fix" it.
- **`MAX_UPLIFT = 10.0` exists only to satisfy the plan's `1 ≤ uplift ≤ 10` bound test** — the
  composite ratio is unbounded as `r_h → r_e` and `μ → floor`. It never binds at field settings
  (max observed 4.5).
- **Walther is fitted at runtime, `walther_A/B` kept `null`** — same reason the CHANGELOG gives
  for `andrade_A/B`: writing rounded values back to JSON breaks
  `test_reference_point_recovered` by float drift.
- **Andrade is still reachable** (explicit `andrade_A`/`andrade_B_K`, both non-null, with
  `walther_A/B` null) purely so `test_explicit_andrade_params_used_when_not_null` keeps passing
  and so benchmark A1 can compare the two laws.
- **Documented deviation in `srp.py`:** the plan's literal
  `descent_violation = v_avg_ms > DESCENT_LIMIT_MS` is True for every pumping unit ever built
  (3 m stroke at 4 SPM already gives 0.4 m/s vs the 0.0508 m/s limit), so it was implemented as
  `v_avg_ms > max(v_fall_ms, DESCENT_LIMIT_MS)`. Rationale is in the source comment.
- **Documented deviation on T1-D's optimizer exposure:** `spm` remains a single positional arg
  (= schedule start) and `spm_floor` was added as an optional keyword rather than making
  `generate_data.py` 5-D. Reason: `ml/train.py` has `FEATURES = [steam_t, soak_days, cutoff_m3d,
  spm]` and is owned by the Phase-2 agent; a 5th sampled input would add unexplained variance to
  a 4-feature model. The schedule itself (the physics deliverable) is fully implemented.
- **`summary()` gained an optional second arg `params=None`.** `api/main.py` calls
  `cycle.summary(df)` and still works (module-default economics constants are identical to the
  JSON block). Pass `params` from `generate_data.py` when that file is updated.
- **`thermal.steam_zone_temperature` during injection** now reports an area-weighted ramp over the
  *final* zone footprint (T₀ → T_s), purely so `test_temperature_rises_during_injection` keeps its
  intent; the well is shut in through inject+soak so it affects reported columns only. Marked as
  a reporting-only ASSUMPTION in the source.
- **Effective delivered-heat multiplier from T1-H is ≈0.52** ((0.3575/0.65 quality) ×
  (1.40/1.30 latent) × (1 − 0.115 loss)), which shrinks r_h by ≈0.72×. That is the intended
  direction (SOR up, honesty up) but it stacks with T1-A — which is exactly why the
  recalibration must be done once, at the end.

---

## 5. ML retrain on rev 5 (26 Sep 2026, branch `physics-v2`)

`data/synthetic_cycles.csv` and `ml/models/*` were v1 (pre-Tier-1 physics, frozen since
13 Sep). This pass regenerated the data against the calibrated rev-5 twin and retrained
the surrogate + optimizer per `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ML.md`'s
T1-level recommendations (log-oil instead of direct-SOR, kept float classifier, added a
margin/day regressor as the optimiser objective).

### 5.1 Data — `twin/generate_data.py`, 3,000 rows, seed 42

- **3,000 rows written, 0 dropped** (all cycles finite — no degenerate zero-oil corners
  in this LHS draw), **0 NaN** anywhere in the CSV.
- SOR: min **3.02**, median **4.33**, mean **4.74**, max **269.5**. **0.0 %** of rows
  below 3 (expected: `AOF_REF_M3D` calibration keeps the cold/near-cold tail above 3),
  **0.57 %** above 8 (a handful of high-cutoff/low-steam corners — not dropped, per the
  rev-5 CHANGELOG's honest-tail policy).
- **12.7 %** of rows have `alarm_days > 0`; **31.1 %** of rows have `max_floating_index >
  0.6` (superset, as expected — `alarm_days>0` implies `FI >= 1.0 > 0.6`).
- **58.2 %** of rows are margin-positive (`margin_inr > 0`) at bulk-diesel pricing.
- Reference-neighbourhood sanity check (steam_t 1,350–1,650 t, soak 5–9 d, cutoff
  1.05–1.35 m³/d, spm 4–6, 5 rows landed there by the LHS): SOR **3.90–4.26**, bracketing
  the calibrated reference SOR **4.09**. Confirms the generator is drawing from the same
  physics as the calibration log.
- Columns: the original 10 SPEC columns kept first (unchanged order), then appended
  `produce_days, alarm_days, margin_inr, margin_inr_per_cycle_day, co2_t,
  pump_limited_days` (see `twin/generate_data.py` docstring for exact provenance of each).
- Wall time: 3,000 cycles in ~24 s (~8 ms/cycle wall — slower than the 0.55 ms/cycle
  quoted in the old ML plan, which was measured on the pre-Tier-1 physics; still cheap).

### 5.2 ML retrain — `ml/train.py`

Single 80/20 holdout, seed 42, XGBoost family (n_estimators=300, max_depth=4,
learning_rate=0.05, subsample/colsample=0.9), **no cross-validation run or claimed**.

| Model | Target | R² overall | MAE overall | R² in 1,000–2,000 t envelope | MAE in envelope |
|---|---|---|---|---|---|
| `oil_model.joblib` | log(oil_total_m3) → m³ | **0.998** | 4.38 m³ | **0.996** | 3.55 m³ |
| `margin_model.joblib` | margin_inr_per_cycle_day | **0.833** | ₹642/day | **0.998** | ₹214/day |
| (derived check) SOR = steam_t/oil_pred | — | 0.891 | 0.081 t/m³ | — | — |

The margin regressor's overall R² (0.833) is pulled down by the heavy negative tail
outside the operating envelope (thin-steam, high-cutoff corners can lose >₹300k/cycle-day)
— exactly the region nobody would run; inside the 1,000–2,000 t plateau it fits almost
exactly (R² 0.998), consistent with the calibration log's "flat 1,000–2,000" finding.

Floating-risk classifier: label = `(max_floating_index > 0.6) OR (alarm_days > 0)`
(reduces to `max_floating_index > 0.6` in this dataset, since `alarm_days>0` is a strict
subset). Positive-class share **31.5 % train / 29.3 % test** (inside the requested
10–40 % band). **AUC 0.9995, accuracy 0.990**, n=600 (test).

`ml/models/metrics.json` carries `physics_rev: 5`, `trained_on`, `n_rows`, `seed`, and
both overall + envelope metrics for each regressor. The stale `sor_model.joblib` (v1,
direct-SOR target) was deleted on retrain.

### 5.3 Optimizer — `ml/optimize.py`

Objective changed from **minimise predicted SOR** to **maximise predicted
margin_inr_per_cycle_day**, `spm` restricted to `srp.spm_practice_band` (3–6, was the
full `[4,12]` `spm_range`), other 3 inputs ranged from `params["css"]`. Constraint
P(float) ≥ 0.3 penalised (penalty scale rescaled from the old SOR-scale 1000× to
30,000 ₹/day per unit of overage — comparable to the feasible margin/day spread).
`gp_minimize`, 60 calls / 15 initial points / seed 42, unchanged.

**Results table (all physics-verified — `twin.cycle.simulate_css_cycle` + `summary`,
not the surrogate):**

| | steam_t | soak_d | cutoff m³/d | spm | SOR | oil m³ | cycle d | margin ₹/cycle-day | max FI | alarm d | steam ₹ | CO₂ t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Optimum** | 1,707.7 | **15 (bound)** | 0.847 | 4.11 | 3.79 | 450 | 277 | **7,974** | 0.45 | 0 | 10.00 L | 382 |
| Baseline (a) param-midpoint | 1,750 | 9 | 1.3 | 4.5 | 4.30 | 407 | 226 | 2,902 | 0.23 | 0 | 10.25 L | 392 |
| Baseline (b) published-practice (BGW-8-derived) | 1,300 | 10 | 1.3 | 5.0 | 4.11 | 316 | 185 | 2,739 | 0.24 | 0 | 7.61 L | 291 |

- Optimum vs baseline (a): SOR **−11.7 %**, margin/cycle-day **+174.8 %**.
- Optimum vs baseline (b): SOR **−7.8 %**, margin/cycle-day **+191.1 %**.
- Surrogate-vs-physics gap at the optimum: margin **−1.33 %** (surrogate 7,868 vs
  physics 7,974 ₹/day), SOR **+1.13 %** (surrogate 3.835 vs physics 3.792 t/m³). Both
  small, in the direction the old T1-2 plan expected.

Baseline (b) is **derived from the BGW-8 first-cycle job** (`docs/research/
baghewala_facts.md` §4: ~74 t/d × 14–21 d injection ≈ 1,040–1,560 t, midpoint 1,300 t
used; soak "50–60 % of injection length" ≈7–13 d, 10 d used; cutoff and spm not
published for that job, so the params-range midpoint and 5.0 spm were used) — it is
**one documented first-cycle job, not OIL's current operating practice**, and is
labelled as such in the optimizer's own output (`warning` field).

**Honesty notes:**
- **`soak_days` pins to the search-range upper bound (15 d).** This matches the
  calibration log's own finding (§4.4: "soak 3/7/15 → 4,062/4,245/4,402 ₹/cycle-day" —
  a small, flat, monotone increase, not an interior optimum) and §4.5's explicit
  instruction: *"Soak: small monotone benefit only ✘ ... Do not present 'the twin says
  soak N days.'"* The optimizer is correctly reporting that within the 3–15 d search box
  more soak is (marginally) better, not that 15 d is a physically meaningful optimum —
  `pinned_variables` flags this in the output.
  - No other variable is pinned: `steam_t` (1,708 t) sits inside the 1,000–2,000 t
    plateau, not at 500 or 3,000; `cutoff_m3d` (0.847) is well above the 0.6 floor —
    the float-risk constraint (P(float) < 0.3) is the counterweight that stops cutoff
    from being driven to the bound, as the calibration log predicted it would be;
    `spm` (4.11) sits inside the 3–6 practice band, not at either edge.
- This run's headline result is **both** SOR down (−7.8 to −11.7 %) **and** margin up
  (+175 to +191 %) versus both baselines — not the "SOR flat/worse, margin better" case
  the task flagged as acceptable-but-must-be-reported-plainly. Reported as found; no
  tuning was done to produce this combination — it falls out of `cutoff_m3d` being
  pulled down from the baselines' 1.3 m³/d to 0.847 (more oil, same steam) plus `soak_days`
  drifting to the search-box edge (a few % more margin, physically non-meaningful per
  above).

### 5.4 API smoke test

`uvicorn api.main:app` started as a subprocess, all 3 endpoints hit with `urllib`, then
killed: `GET /params` → 200 (full field_params.json). `GET /simulate?steam_t=1500&
soak_days=7&cutoff=1.2&spm=5` → 200, reproduces the calibrated reference (SOR 4.089,
margin/day ₹4,245). `GET /optimize` → 200 in ~31 s, returns the table above.
`api/main.py` was **not modified** — it forwards `ml.optimize.best_settings(params)`'s
return dict unchanged, and never destructures specific keys, so the new (additive) shape
needed no API changes.

### 5.5 pytest

`pytest -q` → **57 passed, 2 xfailed** (unchanged from the rev-5 physics calibration —
the ML retrain touches no `twin/` or `tests/` files).

---

## 5b. Recommendation to bake — soak held at practice (26 Sep 2026, branch `physics-v2`)

Section 5.3's optimum pinned `soak_days` to the search-range upper bound (15 d), which
that section's own honesty note says is **not a real optimum** — the twin's soak
sensitivity is <2 % (§4.4, §4.5), so "the model recommends 15-day soak" would be an
overclaim. The recommendation to present is therefore built by giving the optimizer
authority only over the controls it actually has an interior opinion on (steam, cutoff,
SPM) and **holding soak fixed at 10 days**, the same published-practice value baseline
(b) already uses — so soak stops being a free variable instead of landing on a
meaningless bound.

`ml/optimize.py:best_settings()` gained an optional `fixed: dict[str, float] | None`
argument (e.g. `{"soak_days": 10}`) that removes the named feature(s) from the
`gp_minimize` search space entirely — the fixed value is spliced into every candidate's
feature vector for the ML surrogate calls, and into the reported `best_settings`,
`physics_verified_optimum`, `pinned_variables` (now computed only over the remaining
free dimensions), etc. Default call (`fixed=None`) is the unmodified 4-D search, so
`api/main.py`'s existing `best_settings(params)` call is unaffected.

**Run: `best_settings(params, fixed={"soak_days": 10})`, physics-verified
(`twin.cycle.simulate_css_cycle` + `summary`):**

| | steam_t | soak_d | cutoff m³/d | spm | SOR | oil m³ | margin ₹/cycle-day |
|---|---|---|---|---|---|---|---|
| Raw optimum (unrounded) | 1,692.0 | 10 (fixed) | 0.8604 | 4.751 | 3.820 | 442.98 | 7,812 |

Rounded to operator-friendly set-points (steam → nearest 50 t, cutoff → nearest
0.05 m³/d, spm → nearest 0.5) and **re-verified with the physics twin at the rounded
point** (this re-verified run, not the raw optimum, is what gets baked into the
dashboard):

- steam_t: 1,691.98 → **1,700 t**
- soak_days: **10 d** (fixed — field practice, not searched)
- cutoff_m3d: 0.8604 → **0.85 m³/d**
- spm: 4.751 → **5.0** (4.751 is 0.249 from 5.0 vs 0.251 from 4.5 — rounds up)

**Final table — recommendation (rounded, physics-verified) vs baseline (b)
published-practice, both from `simulate_css_cycle` + `summary`:**

| | steam_t | soak_d | cutoff m³/d | spm | SOR | oil m³ | cycle d | margin ₹/cycle-day | max FI | alarm d | steam ₹/cycle | tCO₂/cycle | diesel L/cycle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Recommended (rounded)** | **1,700** | **10 (practice)** | **0.85** | **5.0** | **3.81** | 445.78 | 268.0 | **7,893** | 0.545 | 0 | 99,55,569 | 380.4 | 145,422 |
| Baseline (b) published-practice | 1,300 | 10 | 1.3 | 5.0 | 4.11 | 315.96 | 184.6 | 2,739 | 0.244 | 0 | 76,13,082 | 290.9 | 111,205 |

- Recommended vs baseline (b): SOR **−7.31 %**, margin/cycle-day **+188.17 %**.
- Rounding happened to land on a *better* point than the raw optimum (margin/day 7,893
  vs 7,812 for the raw optimum) — coincidence of the surrogate's local flatness near the
  optimum plus this being a maximisation objective, not a sign rounding is systematically
  favourable.
- `pinned_variables` on this run: **none** — with soak removed from the search, `steam_t`
  (1,692 t), `cutoff_m3d` (0.860), and `spm` (4.751) all sit inside their ranges, not at a
  bound. This is the clean result the old 4-D search couldn't produce because soak's
  flat-monotone drift to 15 d was masking it.
- `diesel_litres` = `steam_t_cum.max() * economics.diesel_kg_per_t_steam /
  economics.diesel_density_kg_per_l` (not a `summary()` key; computed the same way for
  both rows above for the dashboard bake).
- This is what gets baked as **OPTIMISED** in `dashboard/src/data.js` / `core.js`
  (§6 below); baseline (b) above is baked as **REFERENCE**. Soak is presented as
  "field practice, model insensitive, not optimised" per the coordinator's decision —
  never as a twin-derived recommendation.

---

## 6. Calibration loop (26 Sep night) — ingest → recalibrate → re-recommend

Today the twin is a simulator with fixed constants. `ml/uq.py`'s own tornado
ranking already names the biggest uncertain ones: `thermal.BL_DELTA_FACTOR`
(0.5, unverified against the 1966 paper), `fluid.water_cut` (0.85, no field
datum), `reservoir.thickness_m` (12 m, "NOT FOUND for Baghewala"), and
`ipr.AOF_REF_M3D` (0.46, hand-tuned against one published uplift ratio). Oil
India has per-well cycle records (the PS says so). `twin/calibrate.py` closes
the loop: it fits those four constants to observed cycles
(`scipy.optimize.least_squares`, bounded, deterministic) and
`ml/recommend_physics.py` re-recommends set-points directly against the
recalibrated physics (the trained XGBoost surrogates were fit on the OLD
physics, so `ml.optimize.best_settings()` would silently score candidates
with a stale surrogate for a recalibrated params tree).

**New override point:** `twin.ipr.aof_ref_m3d(params)`, reading
`params["ipr"]["aof_ref_m3d"]` and falling back to the module constant
`AOF_REF_M3D` — same additive pattern as the existing
`twin.thermal.bl_delta_factor(params)`. `oil_rate_m3d` now calls
`aof_ref_m3d(params)` instead of the bare module constant. Every existing
caller (which passes no `"ipr"` block) is unaffected; verified by the full
`pytest -q` suite staying green.

### 6.1 Observed-cycles schema and CLI

One row per completed CSS cycle: `well_id, steam_t, soak_days, spm, oil_m3,
produce_days` required; `cutoff_m3d, peak_oil_m3d, sor` optional (missing
`cutoff_m3d` defaults to the params-range midpoint; `sor` is derived, not
used by the fit). Documented in `twin/calibrate.py`'s module docstring and
`data/templates/observed_cycles_template.csv` (header + 2 example rows, one
per BGW-8/BGW-9-style cycle).

```
python -m twin.calibrate observed.csv --out ml/models/calibrated_params.json --report ml/models/calibration_report.json
```

`fit()` minimises normalised residuals of `oil_m3`, `produce_days` (and
`peak_oil_m3d` when present) between the observations and
`twin.cycle.simulate_css_cycle` run at the same set-points; ~1-20 ms per
cycle evaluation, so a fit over a few dozen cycles is interactive (the
8-cycle pseudo-real demo below fits in well under a second). `apply(params,
fitted)` writes the fitted values into a deep copy at
`thermal.bl_delta_factor`, `fluid.water_cut`, `ipr.aof_ref_m3d`,
`reservoir.thickness_m`. A 1-row CSV raises a clear `ValueError` (a single
cycle cannot identify 4 free parameters — 2-3 residuals for 4 unknowns is
degenerate, not merely poorly conditioned).

### 6.2 Pseudo-real demo — recovered vs truth

**This is SYNTHETIC data, NOT Oil India field data** — see
`data/external/SOURCE.md`. `python -m twin.generate_pseudo_real` runs the
twin against a HIDDEN true params set (`bl_delta_factor=0.72,
water_cut=0.78, thickness_m=15, aof_ref_m3d=0.55` vs the shipped
defaults 0.5/0.85/12/0.46) at 8 set-points across 3 fictional wells
(BGW-D1..D3, within the practice ranges), adds seed-42 ±8% multiplicative
noise to oil/days/peak, and fits the default (unaware) params against the
result. Full report: `ml/models/calibration_demo_report.json`.

| Parameter | Truth | Fitted | Error | Identifiability |
|---|---|---|---|---|
| `aof_ref_m3d` | 0.550 | 0.536 | **−2.6%** | best-identified |
| `bl_delta_factor/(1−water_cut)` | 3.273 | 2.974 | **−9.1%** | the only jointly-identifiable combination of the next two rows |
| `bl_delta_factor` (raw) | 0.720 | 0.498 | −30.8% | not separable from `water_cut` alone |
| `water_cut` (raw) | 0.780 | 0.833 | +6.7% | not separable from `bl_delta_factor` alone |
| `thickness_m` | 15.0 | 11.93 | −20.4% | weakest-identified (r=0.997 with `aof_ref_m3d`) |

Fit quality (RMSE, obs vs sim at the fitted point): oil_m3 3.2%, produce_days
4.4%, peak_oil_m3d 5.7% — all inside the ±8% noise floor, i.e. the fit
explains the noisy data well even where the underlying parameters are
confounded.

**Honest identifiability finding (Jacobian-implied correlation at the
solution, |r| reported to 4 decimals in the report):**
`bl_delta_factor`↔`water_cut` = **−0.99999996** (numerically −1: they enter
the physics ONLY through the ratio `bl_delta_factor/(1−water_cut)`, because
`twin.thermal`'s Boberg-Lantz energy-removed term is `bl_delta_factor ×
Q_removed/Q_retained` and `twin.cycle` computes the produced-liquid
heat-carry rate as `oil_m3d/(1−water_cut)`); `aof_ref_m3d`↔`thickness_m` =
**+0.9965** (both change how a heated-zone-size effect turns into rate,
under-determined by oil/days totals alone). Neither pair is a fitting
failure — even a NOISE-FREE fit against the hidden truth reproduces this
exact degeneracy (verified separately: noise-free RMSE ≈0, yet
`bl_delta_factor`/`water_cut` still land away from truth while their ratio
matches truth almost exactly, and `thickness_m`/`aof_ref_m3d` land close to
exact only because the noise-free case has no residual noise to amplify the
r=0.994 confound). With only oil_m3/produce_days/peak_oil_m3d per cycle, a
downhole temperature or pressure log would be needed to separate these
pairs further — flagged, not hidden.

### 6.3 Re-recommendation, physics-verified, before vs after calibration

`ml/recommend_physics.py::best_settings_physics(params, fixed={"soak_days":
10})` grid-searches steam_t × cutoff_m3d × spm (15×15×7 = 1,575 points, ~10 s
wall) directly on `twin.cycle.simulate_css_cycle` + `summary` — no surrogate.
Feasibility: `max_floating_index <= 0.6` (`twin.cycle.FLOATING_RISK_
THRESHOLD`, the same raw threshold the ML classifier's own training label is
built from — `ml/train.py`: `(max_floating_index > 0.6) OR (alarm_days >
0)`), used directly because there is no trained-classifier probability to
threshold against a recalibrated params tree. `soak_days` held fixed per
§5b (no interior optimum in soak).

| | steam_t | cutoff_m3d | spm | SOR | oil m³ | margin ₹/cycle-day | max FI |
|---|---|---|---|---|---|---|---|
| Before calibration (default params) | 1,571 | 0.70 | 4.0 | 3.63 | 432 | **9,000** | 0.578 |
| After calibration (pseudo-real fit applied) | 1,571 | 0.80 | 4.0 | 3.19 | 492 | **15,919** | 0.589 |

Both feasible (max FI < 0.6, same grid resolution both sides so the
comparison is apples-to-apples). The calibrated params (net effect: higher
`aof_ref_m3d`, lower effective `bl_delta_factor/(1−water_cut)`, lower
`thickness_m`) make the well more productive per tonne of steam at the same
steam_t/spm — cutoff nudges up from 0.70 to 0.80 m³/d and margin/cycle-day
**+77%** — this is exactly why re-recommending against the OLD (default-
physics-trained) surrogate after a recalibration would silently mismatch the
new physics: `ml.optimize.best_settings()` was never re-trained for this
params tree.

### 6.4 Limits, honestly

1. `bl_delta_factor` and `water_cut` are reported here as INDIVIDUALLY
   uncalibratable from cycle totals alone — only their ratio is. Any future
   presentation of "the twin recalibrated water_cut to X" from oil/days data
   alone is overclaiming; say "the ratio recalibrated to X" instead, or add a
   downhole log.
2. `thickness_m` recovery (−20.4%) is inside a documented, generous tolerance
   (see `tests/test_calibrate.py`'s docstring), not a tight one — it is the
   weakest-identified of the four here, for the reason in §6.2.
3. `ml/recommend_physics.py`'s grid (15×15×7) is coarser than
   `ml.optimize.best_settings()`'s `gp_minimize` (60 calls, continuous) — the
   before/after comparison in §6.3 uses the SAME grid both sides, so the
   ±77% delta is not a grid-resolution artefact, but do not compare a
   `recommend_physics` output number-for-number against an existing
   `ml.optimize.best_settings()` table entry without noting the different
   search method.
4. The pseudo-real dataset is SYNTHETIC (`data/external/SOURCE.md`) — this
   entire section demonstrates the LOOP working, not a real Baghewala
   recalibration. When real per-well cycle records arrive, re-run
   `twin.calibrate.fit` on them directly; nothing else in this section
   changes.

---

## 7. Physics v3 (26–27 Sep 2026, branch `physics-v3`)

Scope: (1) source `BL_DELTA_FACTOR`; (2) close the two rev-5 xfails if that can be defended;
(3) tests and docs. `pytest -q` → **67 passed, 1 xfailed** (strict, soak).

### 7.1 BL δ — sourced, and computed from production
`BL_DELTA_FACTOR = 0.5` is the **½ in Boberg & Lantz's own δ**:
`f_pD = (1/2Q)∫Q̇_p dt`, Q = injected heat remaining in the reservoir (SPE PEH Vol. V
ch. 15, Eqs. 15.70/15.73/15.74, reproducing JPT 1966). Energy conservation fixes it: with no
conduction θ = 1 − 2δ must equal 1 − Q_p/Q. It is not a free constant, and UQ should stop
sampling it over 0.35–1.0. δ was already accumulated from simulated production. v3 replaces
the unsourced `CP_LIQUID_JM3K = 4.0e6` blend with Eq. 15.74 stream by stream:
- oil: M_o from API gravity plus Gambill's c_o;
- water: steam-table Δh_f.

Details and citations: `BL_DELTA_FACTOR_SOURCE.md`. The remaining δ uncertainty is
`fluid.water_cut`.

### 7.2 Before / after (rev 5 → v3; all at 5 spm unless stated)
| Case | SOR | oil m³ | prod d | peak bbl/d | uplift | ₹/cycle-day | margin ₹ L |
|---|---|---|---|---|---|---|---|
| **Reference** 1500/7/1.2/5 | 4.089 → **4.027** | 366.9 → 372.5 | 182 → 185 | 15.9 | 5.66 | 4,245 → **4,998** (+18 %) | 8.84 → **10.56** (+19 %) |
| **Baseline (b)** 1300/10/1.3/5 | 4.114 → 4.061 | 316.0 → 320.1 | 158 → 160 | 15.1 | 5.38 | 2,739 → 3,391 (+24 %) | 5.06 → 6.33 (+25 %) |
| **Recommendation** 1700/10/0.85/5 | 3.814 → 3.754 | 445.8 → 452.8 | 236 → 240 | 16.3 | 5.80 | 7,893 → **8,565** (+9 %) | 21.15 → 23.29 (+10 %) |
| steam 500 / 1000 / 2000 / 3000 | 3.60 / 3.83 / 4.22 / 4.53 (each −1 to −2 %) | | | | | −2,096 / 3,831 / 4,779 / 3,214 (each up ₹620–860/d) | |
| cutoff 0.6 / 1.0 / 1.5 / 2.0 | 3.49 / 3.83 / 4.42 / 5.81 | | | | | 10,090 / 7,205 / **207 (was −495)** / −17,240 | |
| spm 3 | 4.20 → 4.14 | | 202 → 205 | 11.7 | | 2,556 → 3,218 (+26 %) | |
| P_res 9.4 / 7.4 MPa, ΔSOR | +17.4 % → +17.9 % / +60.8 % → +61.4 % | | | | | | |

**Every number that moved more than 5 % is a margin (₹ or ₹/day).** SOR, oil, produce days,
peak, uplift, FI and alarm days all moved less than 2 %. The margin is a thin difference
(₹111 L revenue − ₹88 L steam − ₹15 L fixed), so +1.5 % oil becomes ≈ +19 % margin.
Knob re-tune: **none** (reference SOR 4.03 is inside 3.8–4.6). All rev-5 bands hold:
- SOR 3.6–4.5 over 500–3,000 t;
- uplift 5.66 (5.12 / 5.72 at the BGW-8 slug ends of 1,040 / 1,560 t);
- peak 15.9 bbl/d;
- 185 produce days;
- CalGEM band 3.47–8.24.

### 7.3 P_res — resolved by re-specifying the benchmark (option iii), not by a mechanism
**The diagnosis "the cutoff makes it over-respond" is mostly wrong.** Rate follows Vogel's
q_max = J·P_res/1.8 at the absolute pump-intake P_wf = 1,144 kPa. At 7.4 MPa the well
therefore makes r = 0.634 of the rate at 11.4 MPa on every day. A fixed-duration cycle then
gives ΔSOR = 1/r − 1 = **+57.6 %**, and the rate cutoff adds only ~4 pp (the twin gives
+61.4 %). The rev-5 xfail threshold was therefore not a missing-cutoff bug.

Options checked:
- **(i) Economic cutoff.** A no-op. Daily opex in the model is electricity only
  (~250 kWh/d ≈ ₹2,000/d), which gives q_EL ≈ 0.07 m³/d. That is below the 0.447 m³/d cold
  rate, so it never binds. The published CADP rule (Rivero & Heintz, via PEH ch. 15:
  re-steam when daily cash flow < cumulative average daily profit) is exactly the margin/day
  objective. It also never triggers, because a cold well earns ≈ ₹13.6k/d against a cycle
  CADP of ₹5–10k/d.
- **(ii) Extra drive terms.** Not defensible for Baghewala:
  - gravity head ρgh over 12 m = 0.11 MPa, ≈ 1 % of the drawdown;
  - 7.4–11.4 MPa is far above the 3 MPa bubble point, so there is no solution-gas drive;
  - there are no compaction data.
- **(iii) Chosen.** Liaohe's +24 % (7.4 → 2.9 MPa over ~20 years) is a field life-cycle
  drift with operator re-design and CO₂ assist, in a gravity/solution-gas setting. It is not
  a same-design single-cycle sensitivity. The strict xfail is replaced by
  `test_depletion_response_is_darcy_proportional`, which asserts the twin sits in the
  derived Darcy band [1/r − 1 − 5 pp, + 15 pp].

For reference: at an identical low cutoff (0.6 m³/d) the response is +30 %. The response
depends on how deep the cutoff sits in the tail.

### 7.4 Soak — no defensible mechanism; xfail kept (strict)
Mechanisms tried and bounded:
1. **Soak-only conductive spreading** (heated radius r² = r_h² + 8αt, energy conserved,
   prototyped). Rejected. It counts horizontal conduction as a loss during production
   (Boberg–Lantz f_HD) but as retained during soak. Soak therefore becomes a free lunch:
   monotone, +12 % oil at 30 d, ₹/day still rising at 30 d. The consistent version (keep the
   spread heat in both phases) replaces Boberg–Lantz's f_HD for the whole cycle and does not
   favour soak specifically. That is a Tier-3 numerical radial-conduction model, not a small
   mechanism.
2. **Uncondensed-steam flashback.** Pore volume of the heated zone ≈ 330 m³ at φ = 0.09.
   Even full of 290 °C vapour (39 kg/m³) it holds ≤ 19 GJ, under 1 % of Q = 2.0 TJ. The
   params also put near-well pressure above p_sat(290 °C), so there is no free steam to
   condense.
3. **Gravity segregation.** Irrelevant to productivity at a 0.11 MPa head against ~10 MPa
   drawdown.
4. **Pressure bleed-off** (already modelled). A ±1 % effect (rev 5).

Result with v3 physics: SOR falls ~1 % from 3 to 15 d. ₹/cycle-day rises to a peak at
**~18 d** (same at dt = 1 d and 0.25 d), then declines slowly. The plateau is < 3 % deep over
7–30 d, and the dt = 1 d sawtooth (±1.5 %) is as large as the signal. This is the
Boberg–Lantz answer: soak acts only through conduction timing, via the δ·F term. It matches
the literature's "little impact" (PEH ch. 15: soak "should be as short as possible"; CSS
simulation studies put the optimum at ~3–4 d).
- `test_soak_optimum_is_interior_in_5_to_15_days` stays a **strict xfail**: argmax 18 d, not
  ≥ 2 % above the 30-d end.
- New passing `test_soak_is_a_weak_lever_margin_plateau` pins the plateau.

Baghewala's 7–13 d practice is not explained by reservoir physics in this model. A plausible
**operational** reason (unverified, a question to ask OIL): with rod-pump lift, the
injection string has to be pulled and the pump re-run after steaming, so "soak" includes
workover time.

### 7.5 Is the rev-5 recommendation still near-optimal? (true-physics grid, not ML)
Grid: steam 1,000–2,000 (step 100) × cutoff 0.60–2.00 (step 0.05) × spm 3–6 (step 0.5) ×
soak {5, 7, 10, 13, 15}. 11,165 cycles per revision. Constraint: max FI ≤ 0.6 (no alarm).

| | rev 5 | v3 |
|---|---|---|
| grid optimum (soak free) | 1,400 / **15** / 0.65 / 3.5 → ₹9,155/d, SOR 3.50 | 1,400 / **15** / 0.65 / 3.5 → ₹9,752/d, SOR 3.44 |
| grid optimum, soak held at 10 | 1,400 / 10 / 0.65 / 3.5 → ₹9,100/d | 1,400 / 10 / 0.65 / 3.5 → ₹9,696/d |
| rev-5 recommendation 1,700 / 10 / 0.85 / 5 | ₹7,893/d (−13 %) | ₹8,565/d (−12 %) |
| unconstrained | 1,500 / 15 / 0.60 (FI 0.7–1.0, 13–40 alarm days) | same |

**v3 does not move the optimum.** Its location is identical in both revisions, and soak
still pins to the top of the box. The recommendation was already ~12–13 % below the
true-physics grid optimum under rev 5. That gap belongs to the ML optimizer's
float-probability penalty and surrogate; v3 did not cause it. The grid optimum rides the
float line (FI 0.55) with cutoff near the range floor, as §4.5 predicted. **Re-cascade
needed for ₹ values only:** `data/`, the margin regressor and the dashboard ₹ figures
(margins +9 to +25 %). The optimiser location does not change. Whether to move the
recommendation towards 1,400 t / 0.65 / 3.5 spm is a separate ML/ops call.

### 7.6 Judgement calls the team must know
1. The P_res benchmark was **re-specified**, not met. Liaohe is now cited only as a
   direction check.
2. The soak optimum is still **not** a twin output. Keep "soak held at practice, model
   insensitive".
3. **Economics gap found:** the margin has no daily opex and no cold-production baseline.
   The cold well alone would produce ≈ 95 m³ over the reference cycle's 212 days, so the
   incremental SOR is **5.4**, not 4.0. This is why "lower cutoff is always better" and why
   CADP never triggers. This is for the economics owner, not changed here.
4. UQ should fix `bl_delta_factor` at 0.5 and vary `water_cut` instead.
   `docs/study/*` and `dashboard/src/core.js` still call BL "unverified / most sensitive".

### 7.7 Not closed
- Soak optimum (xfail).
- `water_cut` as a state variable (T2-A).
- Steam and gas terms of Eq. 15.74.
- Opex and incremental-oil economics.

---

## 8. Economics v2: incremental oil, opex, srp energy (27 Sep)

Scope: close §7.6 item 3 (no daily opex, no cold baseline) and item 4 (UQ/calibration
still treating BL δ as free); fix `srp.energy_kWh_d`. Physics is untouched: every SOR, oil,
produce-day, peak, uplift and FI value below equals §7.2. `pytest -q` → **116 passed,
1 xfailed**. CHANGELOG rev 8 has the key-by-key record.

### 8.1 What was built
- **Cold baseline** (`cycle.cold_baseline`): the same well unstimulated (uplift 1, virgin
  P_res, same absolute P_wf) at the 2-spm keep-moving floor. It gives 0.447 m³/d
  (2.8 bbl/d) at 97.6 kWh/d polished rod.
- **Convention:** the cold well produces over the **whole calendar window, inject and soak
  days included**. The shut-in forgoes cold oil. This is "stimulated minus unstimulated
  over the same time period" (Boberg 1988 / PEH ch. 15; recalled, not re-retrieved).
  Window = `days_total` + 1 d. If the cold well cannot pay its own opex, the counterfactual
  well is shut in.
- **Daily opex:**
  - `economics.opex_inr_per_day` = ₹5,000 [ASSUMPTION; no Indian per-well lifting cost
    found; OIL AR 2024-25 checked];
  - plus pumping power = corrected polished-rod kWh ÷ `srp.surface_efficiency` 0.60
    [TYPICAL] × ₹8/kWh.

  The fixed part cancels in the incremental margin.
- **srp energy:** closed-loop card work, with the rod weight credited back on the
  downstroke: pump ΔP × liquid, 2F_fr·S, and drag + Gibbs damping ⟨v²⟩ terms. It matches
  the dyno card area within −1 to +9 % in 7 cases from 5 cP to 11,500 cP (float included).
  Three of those cases are tested within 15 %.
- **Keys:** the gross `margin_inr*` keys are unchanged. New: `margin_with_opex_*`,
  `*_incremental*`, `cold_*`, `cadp_*`, `electric_kWh*`, `power_cost_inr`, `opex_*`,
  `window_days`.

### 8.2 Literature SOR convention → headline SOR stays gross
Every benchmark this repo compares against is gross: steam ÷ all oil produced.
- CalGEM field SOR = (cyclic + steamflood) ÷ field oil.
- Cold Lake "≈ 4" and CSS "life-cycle ~6" are cumulative ÷ cumulative.
- The css deep dive §1 defines OSR as oil produced per unit steam.

So `SOR_t_per_m3` stays the headline and keeps every rev-5/v3 band. `SOR_incremental` is
reported next to it and drives the ₹. **Optimiser/dashboard ₹ objective:
`margin_incremental_inr_per_cycle_day`.** It is already the objective in
`ml/recommend_physics.py`. The ML surrogate needs the cascade re-bake.

### 8.3 Before → after (5 spm unless stated; soak as listed)
| Case | SOR gross | **SOR incr** | oil m³ | **incr oil m³** (cold) | prod d | peak bbl/d | uplift | gross ₹/d | with-opex ₹/d | **incr ₹/d** (₹ L/cycle) | max FI | kWh/m³ PR (was) | grid kWh/m³ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference 1500/7/1.2/5 | 4.027 | **5.40** | 372.5 | **277.6** (94.9) | 185 | 15.9 | 5.66 | 4,998 | −1,019 | **−8,328** (−17.7) | 0.30 | 42.5 (123.4) | 70.8 |
| Baseline (b) 1300/10/1.3/5 | 4.061 | **5.50** | 320.1 | **236.3** (83.9) | 160 | 15.1 | 5.38 | 3,391 | −2,543 | **−9,851** (−18.5) | 0.24 | 40.2 (123.3) | 67.1 |
| Rec (rev 5) 1700/10/0.85/5 | 3.754 | **5.14** | 452.8 | **330.8** (122.0) | 240 | 16.3 | 5.80 | 8,565 | 2,290 | **−5,019** (−13.7) | 0.55 | 56.2 (136.6) | 93.7 |
| Grid best (base) 1400/10/0.65/3.5 | 3.466 | 4.94 | 403.9 | 283.7 (120.2) | — | 13.7 | — | 9,696 | 3,719 | −3,590 (−9.7) | 0.55 | — | — |
| **Minimax-regret 1600/10/0.70/4** | 3.590 | 5.00 | 445.6 | 319.7 (125.9) | 250 | 15.7 | 5.57 | 9,610 | 3,504 | −3,804 (−10.7) | 0.58 | 50.8 (116.2) | 84.6 |

- "was" = the pre-v2 peak-load × stroke × spm energy.
- Pumping energy at the reference fell from 248.5 to 85.5 kWh/d polished rod; grid power
  is ₹2.1 L per cycle.
- All rev-5/v3 bands still pass: SOR 3.6–4.5, uplift, peak, CalGEM, Darcy P_res.

### 8.4 The finding: at the base price deck CSS does not beat the cold well
- Break-even incremental SOR (before the ₹15 L rig) is ₹30,443/m³ ÷ ₹5,856/t = **5.20**;
  the twin's best is ~4.9.
- **Incremental margin is negative at all 1,993 feasible grid points.** The rev-5
  "revealed preference" calibration (19 jobs in FY26 ⇒ a sensible cycle must pay) was done
  on the gross basis, which credits CSS with oil the well makes anyway.
- Break-even at the rec: oil ≥ **₹5,498/bbl** ($62.5 net; ~$72.5 before the heavy
  discount), or steam ≤ **₹5,050/t**.
- OIL's own **FY25 realisation of US$78.09/bbl** (Annual Report 2024-25, CONFIRMED) − $10
  = ₹5,992/bbl. That turns the rec to **+₹3,761/d** and the grid best to +₹4,514/d.
- The $65 in the params is the CMD's FY26 planning floor. **Deck not changed: team call.**
  Also unmodelled: royalty (₹2,987 cr) and OID cess (₹2,567 cr) in FY25. The ₹ basis is
  pre-levy.

### 8.5 Does "lower cutoff is always better" survive? Does a re-steam point appear?
- **The incremental basis alone does not move the optimum.** Per cycle-day, the cold
  baseline is a constant offset (cold cash/day), so it changes the sign, not the argmax.
  Incremental and gross argmax coincide at 1,400/0.65/3.5 on the base deck. The CADP rule
  is the same inequality on both bases: q·P < A_gross ⇔ (q − q_c)·P < A_incr. So §7.6's
  "missing baseline ⇒ CADP never triggers" was half right: the missing piece was price
  level, not the baseline.
- **Base deck:** the CADP average is negative, so the rule never triggers (q\* = 0.457, the
  cold rate). "Lower cutoff is better" survives: the feasible optimum sits at the lowest
  cutoff the float limit allows.
- **FY25 deck:** an economic re-steam point **appears**, at q\* ≈ **0.62 m³/d** (4 spm, day
  ~300) or 0.54 (3 spm). It sits just under the float line, though: FI reaches 0.67 before
  q\* at 4 spm. In practice the FI ≤ 0.6 constraint (cutoff ≈ 0.70) binds first, and
  economics and rod mechanics agree within ~0.1 m³/d.
- Per-tonne-of-steam view (`margin_incremental_inr_per_t_steam`; the field has one skid,
  ~90 % utilised): best at 1,800/0.70/4 (base) and 1,400/0.65/3.5 (FY25). Reported, not
  used as the objective. Under a steam constraint the post-cutoff tail keeps adding
  incremental oil, so a cutoff-based per-tonne number is only indicative.

### 8.6 New optimum vs 1,700/10/0.85/5 (true-physics grid)
Grid: steam 1,000–2,000 (100) × cutoff 0.60–2.00 (0.05) × spm 3–6 (0.5), soak 10.
2,233 cycles, 1,993 with FI ≤ 0.6. Objective: incremental margin/cycle-day.

| Deck | Optimum | incr ₹/d | 1,700/0.85/5 | gap |
|---|---|---|---|---|
| Base (₹4,840/bbl, ₹5,856/t) | 1,400 / 0.65 / 3.5 | −3,590 | −5,019 | ₹1,429/d |
| FY25 realisation (₹5,992/bbl) | 1,800 / 0.70 / 4.0 | +4,514 | +3,761 | ₹753/d |
| **Minimax regret, both decks** | **1,600 / 0.70 / 4.0** | −3,804 / +4,422 | | ≤ ₹214/d from either optimum |

`recommend_physics` (15×15×7 grid) at the default params independently lands on
1,571/0.70/4.0.
- **1,700/0.85/5 is not near the optimum** on either deck (−₹0.75–1.4k/d).
- The lever is **spm 5 → 4 with cutoff 0.85 → 0.70**. Lower SPM keeps the rods ahead of
  the horsehead further into the cold tail, so the cycle can run longer before FI hits 0.6.
- Steam 1,500–1,800 t is flat within ~₹200/d.
- **Cascade recommendation: 1,600 t / 10 d / 0.70 m³/d / 4 spm**, soak held at practice as
  before.

### 8.7 UQ and calibration
- `ml/uq.py`:
  - `bl_delta_factor` fixed at 0.5 and no longer varied;
  - `water_cut` U[0.70, 0.90];
  - new `opex_inr_per_day` U[2.5k, 7.5k];
  - probabilities and tornados on the incremental margin.

  100-draw smoke test (not the bake): P(incr margin/day > 0) = 0.22 / 0.16 / 0.31 (ref /
  base / rec) against gross 0.68 / 0.62 / 0.79; P(rec > base) = 1.00. The #1 driver is now
  water_cut (OAT swing ~₹29k/d), then diesel discount, then oil price.
- `twin/calibrate.py` default free = water_cut, aof_ref_m3d, thickness_m. On the
  pseudo-real demo with bl = 0.5 in the truth, recovered vs truth is:

  | Parameter | Recovered | Truth | Error | Range over 5 noise seeds |
  |---|---|---|---|---|
  | water_cut | 0.778 | 0.78 | −0.2 % | 0.770–0.790 |
  | aof | 0.559 | 0.55 | +1.6 % | 0.541–0.578 |
  | thickness | 15.13 | 15 | +0.9 % | 13.9–20.0 |

  So water_cut is now identifiable alone. The Jacobian correlations stay at 0.97–0.99, so
  thickness vs aof is still the weak split.

### 8.8 Judgement calls (economics owner / coordinator)
1. Cold-baseline convention: whole window, inject + soak included; window = days_total + 1.
2. Headline SOR gross; ₹ on incremental; gross `margin_inr*` keys kept at the rev-5
   definition.
3. **Price deck not changed.** The model says CSS loses against the cold well at $65 − $10,
   and pays at OIL's confirmed FY25 $78.09 − $10. Pick one, or show both.
4. ₹5,000/d fixed opex, η_surface 0.60, cold well at 2 spm, ₹8/kWh: all labelled
   assumptions. Fixed opex does not affect any incremental number.
5. Royalty/cess not modelled (national-value basis).
6. Recommendation for the cascade: 1,600/10/0.70/4 (robust across both decks).

---

## 9. Hardening after external review (27 Sep)

Scope: fix what the external technical review (petroleum engineer plus data scientist, 52/100)
found wrong or unsampled in the rev-9 twin. The review file is `REVIEW.md` in the session
scratchpad, with `probe1-4.py`. All four probes were re-run on `main` @ 591a16f before
starting, and each finding reproduced:
- SOR is 4.03 / 2.02 / 1.01 at dt = 1 / 0.5 / 0.25;
- S_COLD 0 → 8 gives uplift 3.28 → 6.96;
- boost 0 → 2 gives uplift 5.13 → 6.19;
- the cold rate is the same at every μ_ref.

Branch `harden`. `params/CHANGELOG.md` rev 10 has the key-by-key record.
`pytest -q` → **148 passed, 1 xfailed**.

**Calibration knobs: none changed.** `AOF_REF_M3D` stays 0.46, skin 5, boost 1.0. Every rev-5/7
band passes without a fudge:

| Band | Result |
|---|---|
| Reference SOR | 4.027 |
| SOR over 500–3,000 t | 3.60–4.53 |
| Uplift | 5.66 |
| Peak | 15.9 bbl/d |
| Produce phase | 185 d |
| CalGEM band | pass |
| Darcy P_res band | pass |
| Gross margin at reference | +₹37.6 L |

### 9.1 What changed

1. **dt bug fixed.** `summary()` summed daily rates without × dt. Now every total and day count is
   Σ(rate)·dt; dt comes from `df.attrs` or is inferred.
   - Reference at dt = 1 / 0.5 / 0.25: SOR 4.0267 / 4.0327 / 4.0325, oil 372.5 / 372.0 / 372.0 m³
     (≤ 0.15 %). Tested for two points within 1 %.
   - §7.4's "same at dt = 0.25" was computed through the broken summary. Re-checked with the fixed
     one on the FY25 deck: soak argmax over 3–30 d is **3 d** (the box floor) at both dt = 1 and
     0.25, gross and incremental, and the two dt agree within 0.7 %. The "~18 d" peak of §7.4
     belonged to the $65 deck. Soak is still a weak lever and still not a twin output; the strict
     xfail stands.
2. **Constants moved to params with code fallbacks.** Values are unchanged:
   - `ipr.s_cold` 5;
   - `srp.k_visc` 10;
   - `reservoir.pressure_boost_kPa_per_t` 1.0;
   - `fluid.mu_anchor_T_C` / `mu_anchor_cP` 150 °C / 50 cP;
   - `economics.fixed_cost_inr_per_cycle`, which gained a tag and range.

   A test deletes all of them and gets an identical run. All are sampled in `ml/uq.py`, with
   `P_current_kPa` U[7.4, 11.4] MPa and `emulsion_inversion_wc` U[0.60, 0.75]. `s_cold` is an
   opt-in free parameter in `twin/calibrate.py`, bounds 0–8.
3. **Cold rate depends on viscosity.** `AOF_REF_M3D` is defined at 11,500 cP and scaled by Darcy
   mobility 11,500/μ_ref.

   | μ_ref (cP) | Cold rate m³/d | Reference incr ₹/d (FY25) | Reference SOR |
   |---|---|---|---|
   | 8,000 | 0.643 | +8,406 | 3.30 |
   | 11,500 | 0.447 (unchanged) | +346 | 4.03 |
   | 15,000 | 0.343 | −7,581 | 4.91 |

   Before rev 10 all three had the same cold rate, and the 15,000 cP oil *earned more*. The uplift
   band holds at the reference (5.66). At 8,000 cP the uplift is 4.84 because the 5-spm pump caps
   the peak.
4. **Emulsion viscosity for rod drag** (§9.5). The rods are dragged by the produced stream, using
   Brinkman μ_c(1 − φ)^−2.5 on the continuous phase with inversion at water cut 0.70
   [ASSUMPTION].
5. **Steam P–T consistency check.** It warns and never fails (§9.6). `reservoir.P_current_kPa` is
   added, null = virgin.
6. **LHS SPM range** = union of `spm_range` and `spm_practice_band` = **3–12** (was 4–12). The
   surrogate's training data now cover the optimiser's 3–6 box. `data/` and `ml/models/*.joblib`
   were **not** regenerated; that is the cascade's job.
7. **Aggressive and conservative recommendations** in `ml/recommend_physics.py`, plus the new
   `ml/decompose.py` → `ml/models/gain_decomposition.json`.
8. **Wording.** Kern River is now "a shallow, predominantly steamflood field with a cyclic-steam
   subset; field-level SOR band only" (tests/test_benchmarks.py).

### 9.2 Before / after (true physics, soak as listed; FY25 = ₹5,992/bbl, $65 = ₹4,840/bbl)

**Before (rev 9, `main` @ 591a16f):**

| Case | SOR gross | SOR incr | oil m³ | days | peak bbl/d | uplift | incr ₹/d FY25 | incr ₹/d $65 | max FI |
|---|---|---|---|---|---|---|---|---|---|
| Reference 1500/7/1.2/5 | 4.027 | 5.40 | 372.5 | 211.3 | 15.91 | 5.66 | +1,149 | −8,328 | 0.297 |
| Baseline (b) 1300/10/1.3/5 | 4.061 | 5.50 | 320.1 | 186.6 | 15.13 | 5.38 | −724 | −9,851 | 0.241 |
| Rec aggressive (FI ≤ 0.6) 1600/10/0.70/4 | 3.590 | 5.00 | 445.6 | 280.6 | 15.66 | 5.57 | +4,423 | −3,804 | 0.577 |
| Rec conservative (FI ≤ 0.5) 1400/10/0.70/3.5 | 3.507 | 4.96 | 399.2 | 260.9 | 13.70 | 4.87 | +3,966 | −3,839 | 0.500 |

The conservative row applies the same minimax-regret rule to the same §8.6 grid under the rev-9
physics. It gives up ₹248/d (FY25 optimum 1800/0.80/4: 4,266 vs 4,514) and ₹249/d ($65) against
the aggressive optima.

**After (rev 10):**

| Case | SOR gross | SOR incr | oil m³ | days | peak bbl/d | uplift | incr ₹/d FY25 | incr ₹/d $65 | max FI |
|---|---|---|---|---|---|---|---|---|---|
| Reference 1500/7/1.2/5 | 4.027 | 5.40 | 372.5 | 211.3 | 15.91 | 5.66 | +346 | −9,130 | 0.000 |
| Baseline (b) 1300/10/1.3/5 | 4.061 | 5.50 | 320.1 | 186.6 | 15.13 | 5.38 | −1,587 | −10,715 | 0.000 |
| rev-9 rec 1600/10/0.70/4 (re-run) | 3.590 | 5.00 | 445.6 | 280.6 | 15.66 | 5.57 | +3,806 | −4,421 | 0.000 |
| **Rec aggressive = conservative 1700/10/0.60/4** | 3.550 | 5.00 | 478.9 | 309.0 | 15.66 | 5.57 | **+4,044** | **−3,911** | 0.000 |

- **Oil, SOR, days, peak and uplift are identical.** At dt = 1 d the SPM ceiling never bound at
  these points, so the emulsion change moves no barrels there.
- **Every incremental ₹/d fell by ₹620–860.** The counterfactual cold well used to pay for dragging
  rods through 11,500 cP oil: 162.7 kWh/d grid. In a water-continuous stream it pays 22.7 kWh/d.
  The cold well is ~₹1,100/d richer, so the stimulated well's increment is smaller.
- The CO₂ and gross columns are unchanged apart from power.

### 9.3 Canonical recommendation (§8.6 grid, soak 10, 2,233 cycles, both decks)

| Level | FY25 optimum | $65 optimum | Minimax-regret (both decks) | Regret |
|---|---|---|---|---|
| Aggressive, FI ≤ 0.6 | 1900/0.60/4.5 → +₹4,081 | 1500/0.60/4 → −₹3,890 | **1700/10/0.60/4** | ₹37/d |
| Conservative, FI ≤ 0.5 | identical | identical | identical | 0 given up |

- **1,600/10/0.70/4 does not survive as the canonical point.** Its reason is gone: FI 0.577 set the
  0.70 cutoff, and FI is now 0. It is still ₹275/d (FY25) and ₹531/d ($65) below the optimum,
  which is inside model uncertainty but not the argmax.
- **The cutoff now sits on the search floor** (`css.cutoff_rate_m3d_range[0]` = 0.60, coupled to
  the 0.447 cold rate). The floor is set by **economics**, not rod mechanics:
  - the FY25 CADP re-steam rate is ≈ 0.56–0.60 m³/d;
  - off-grid, cutoff 0.55 gives +₹4,054 and 0.50 gives +₹4,009, so the FY25 optimum is ~0.55,
    just below the box.
- **SPM is flat from 4 to 6** (₹140/d spread). Below 4 spm the pump capacity bites: 3 spm costs
  ₹2.6k/d. Steam 1,500–1,900 t is flat within ₹200/d. The recommendation is really
  "≥ 4 spm, produce to the economic re-steam rate, 1.5–1.9 kt".
- **Pinned:** cutoff (grid floor), recorded in the JSON.

### 9.4 Gain decomposition, baseline (b) → recommendation (incremental ₹/cycle-day)

| Target | Deck | Total | Cutoff OAT / Shapley | SPM OAT / Shapley | Steam OAT / Shapley |
|---|---|---|---|---|---|
| rev-9 rec 1600/0.70/4, **rev-9 physics** | FY25 | +5,147 | +4,357 / +4,287 (83 %) | +158 / +250 (5 %) | +784 / +611 (12 %) |
| same | $65 | +6,048 | +5,603 / +5,568 (92 %) | +158 / +251 (4 %) | +366 / +229 (4 %) |
| rev-9 rec 1600/0.70/4, rev 10 | FY25 | +5,393 | +4,876 / +4,711 (87 %) | +66 / +61 (1 %) | +799 / +621 (12 %) |
| same | $65 | +6,294 | +6,122 / +5,992 (95 %) | +66 / +62 (1 %) | +380 / +240 (4 %) |
| rev-10 rec 1700/0.60/4, rev 10 | FY25 | +5,632 | +5,080 / +4,885 (87 %) | +66 / +53 (1 %) | +922 / +693 (12 %) |
| same | $65 | +6,804 | +6,677 / +6,533 (96 %) | +66 / +64 (1 %) | +378 / +207 (3 %) |

- OAT = change one lever from baseline. Shapley = average marginal contribution over all 6 orders;
  it sums exactly to the total.
- **The review's finding 1 stands, and gets stronger in rev 10:** 83–96 % of the headline gain is
  the cutoff moving from our assumed 1.3 m³/d. SPM is 1–5 % and steam 3–12 %.

### 9.5 Baseline-cutoff sensitivity (OIL's real cutoff is unknown; steam/soak/spm as baseline (b))

| Baseline cutoff | Baseline incr ₹/d FY25 / $65 | Gain of rev-9 rec FY25 / $65 | Gain of rev-10 rec FY25 / $65 |
|---|---|---|---|
| 1.0 m³/d | +1,623 / −7,021 | **+2,183** / +2,600 | **+2,422** / +3,110 |
| 1.3 m³/d (our assumption) | −1,587 / −10,715 | +5,393 / +6,294 | +5,632 / +6,804 |
| 1.6 m³/d | −6,966 / −16,366 | +10,773 / +11,946 | +11,011 / +12,455 |

**The improvement is a function of an unknown.** It is ~₹2.2–2.4k/d if OIL already produces down
to 1.0 m³/d, and ~₹11k/d if they stop at 1.6. Say "₹2–11k/d depending on OIL's current cutoff";
never quote a single "+₹5k/d".

### 9.6 Emulsion effect on the float index, and the verdict on the rod-float thesis

The produced stream at 85 % water cut is above the [ASSUMPTION] 0.70 inversion, so it is
water-continuous. μ_drag = μ_w(T)·0.85^−2.5 ≈ 0.4–0.8 cP, independent of the oil's viscosity.

FI along the rev-9 rec cycle (1600/10/0.70/4), at 0 / 25 / 50 / 75 / 100 % of the produce phase
(μ_res 7 → 6,493 cP):

| Drag rule | FI | Alarm days | Min fillage |
|---|---|---|---|
| rev 9 (reservoir oil) | 0.001 / 0.007 / 0.051 / 0.211 / **0.577** | 0 | 0.85 |
| rev 10, wc 0.85 (water-continuous) | 0 / 0 / 0 / 0 / **0.000** | 0 | 0.85 |
| rev 10, wc 0.65 (oil-continuous) | 0.009 / 0.13 / **0.87** / 1.0 / 1.0 | 249 of 448 | 0.22 |
| rev 10, wc 0.69 (oil-continuous) | 0.012 / 0.13 / 0.77 / 1.0 / 1.0 | 197 of 366 | 0.23 |

- **The 12 spm / cutoff-0.6 corner:** rev-9 rule, FI 1.0 with 76 alarm days; rev 10 at 85 % cut,
  max FI 0.0002 and 0 alarm days; rev 10 at 65 % cut, 325 alarm days.
- **Late cycle, FI fell 0.577 → 0.000.** It dropped everywhere, not just late.

**Honest verdict: the rod-float thesis does NOT survive at the base water cut.**
- At the shipped 85 % cut the stream is water-continuous. The float constraint then binds nowhere
  in the design space, not even at 12 spm in the cold tail.
- It sets neither the cutoff nor the SPM. The dyno cards at 85 % show no float.
  - `tests/test_benchmarks.py` now asserts this finding.
  - The ML float classifier will have **no positive class** on regenerated data at the base
    params. That is a cascade issue, flagged, not fixed.

**Where the thesis still binds: only in an oil-continuous (W/O) stream,** i.e. water cut below
the inversion.
- There it binds **harder** than rev 9 claimed. FI crosses 0.6 in the **late, cool half** of the
  cycle: produce day ~150–200, once μ_res passes ~500 cP.
- The SPM schedule floors at 2 spm and fillage collapses to ~0.2.
- The early, hot part of the cycle never floats, at any water cut (FI ≤ 0.13 in the first quarter).
- Higher SPM only moves the onset earlier (day 109–131 at 12 spm).

A real CSS cycle's water cut is not constant. It is high early (condensate flowback) and falls
late. So the physically interesting case is the late-cycle, oil-rich, cool stream: exactly the
W/O branch.
- The twin cannot represent that yet: water cut is a constant (T2-A, not done).
- **What to say:** "rod float is a real risk *if* the late-cycle stream is an oil-continuous
  emulsion; whether it is depends on the water-cut profile and the inversion point, both unknown.
  A measured Baghewala dyno card and a water-cut-vs-time record from one cycle decide it."
- **Do not present FI as the constraint that sets the recommendation.**

The emulsion law is also not verified for Baghewala crude (Brinkman, no fitted constants). Tight
asphaltene-stabilised W/O emulsions can be several times more viscous than Brinkman. That only
matters on the W/O branch.

### 9.7 Steam state: the P–T inconsistency (documented, not re-tuned)

**Wellhead.**
- Saturated steam at 290 °C is at **7.44 MPa** (IAPWS-IF97).
- The OIL deck's BGW-08 wellhead pressure is 85–97 kgf/cm² g, i.e. 8.44–9.61 MPa abs. There
  T_sat = **298.7–308.1 °C**.
- So "290 °C at 85–97 kgf/cm²" is not one saturated state. The deck's own 280–305 °C range
  overlaps T_sat only at its top.

**Sandface.**
- Virgin P_res is **11.4 MPa**, where T_sat = 320.8 °C. With the 1.5 MPa boost the near-well
  pressure is 12.9 MPa, where T_sat = 330.3 °C.
- Injection needs BHP > P_res. Above 7.44 MPa, 290 °C water cannot be steam. So at the params'
  own P and T the sandface fluid is **subcooled hot water**:
  - the latent-heat credit x_sf·L_v (≈ 500 kJ/kg of the 1,580 delivered) has no physical carrier;
  - the pressure-boost mechanism has none either (review finding 10).
- The heated **volume** is roughly right because the heat balance uses total enthalpy. The
  **phase** is wrong.

**Resolution.**
- The PS itself says Baghewala has "**low reservoir pressure**". If the near-well region is
  depleted below ~7.4 MPa, 290 °C steam can exist at the sandface and the state is consistent.
- Nothing was re-tuned. Added:
  - `reservoir.P_current_kPa` [ASSUMPTION – depleted, UNKNOWN; **top data ask**], default null =
    virgin, so behaviour is unchanged;
  - UQ samples it at U[7.4, 11.4] MPa;
  - `thermal.steam_state_check()` warns on every cycle run until `T_inj ≤ T_sat(P_wellhead)` and
    `P_res < p_sat(T_inj)`.
- At P_current = 7.4 MPa the reference SOR is +61 % (the Darcy band test).

**Data asks.** A static BHP survey on one BGW well, and the actual wellhead P and T logged
together during one injection.

### 9.8 UQ smoke run (300 draws, FY25 deck, 14 inputs; not the bake)

**Paired probabilities.**
- P(rev-9 rec > baseline) = **0.987** (was 1.00).
- P(rev-10 rec > baseline) = 0.983.

**P(incremental > 0).**

| Point | P |
|---|---|
| Reference | 0.22 |
| Baseline | 0.16 |
| rev-9 rec | 0.38 |
| rev-10 rec | 0.40 |

**Rev-10 rec incremental ₹/d.** p10 −18.7k, p50 −2.5k, p90 +10.7k.

**OAT tornado on the rev-9 rec.**
1. water_cut ₹30.1k/d
2. **s_cold ₹15.7k/d**
3. diesel discount ₹14.3k/d

**MC correlation.** water_cut −0.49, s_cold +0.36, P_current +0.32.

**Caveats.**
- The reference and baseline p10 cycles are degenerate: ~30 bbl. Low P_current plus high water cut
  puts their peak below their 1.2–1.3 cutoff, so the cycle ends on day 1. That is honest: a fixed
  rate cutoff above the achievable peak.
- The "100 %" is gone once the skin, pressure and emulsion are sampled. The recommendation still
  wins in ~98 % of draws, **within these ranges**. Structural model error is still not sampled.

### 9.9 What we now say / stop saying

| Stop saying | Say instead |
|---|---|
| "The engine reproduces Baghewala's published benchmarks" | "It is **calibrated to** one Baghewala benchmark (the 5–6× uplift, via an assumed skin and pressure boost); SOR sits in a loose literature band." |
| "Verified improvement" / "OIL's published-practice baseline" | "Improvement against **our assumed** baseline (1.3 m³/d cutoff, 5 spm are ours). 83–96 % of it is the cutoff. It is ₹2–11k/d depending on OIL's real cutoff." |
| "+₹4,423/day, better in 100 % of draws" | "+₹4.0k/d on the FY25 deck at 1,700/0.60/4, negative on the $65 floor; better than our baseline in ~98 % of draws within our parameter ranges. Structural error not sampled." |
| "Recovers thickness within 0.9 %" | "On synthetic data from the same model, thickness came back 13.9–20.0 m across noise seeds (truth 15). An inverse-crime demo of the loop, not validation." |
| "v1 was about 25 % optimistic" | "v1 was about **25×** too high on peak rate (471 bbl/d vs ~19 field average)." |
| "Rod float sets the cutoff" / "two pieces of physics agree on 0.6" | "At 85 % water cut the produced stream is water-continuous and rods do not float in the model. Float is a late-cycle risk only if the stream is an oil-continuous emulsion; the 0.6 agreement is 2/π kinematics on one drag law." |
| "Kern River is true huff-and-puff like Baghewala" / "9,692 real cycles validate the SOR" | "A shallow, predominantly steamflood field with a cyclic-steam subset; three field-annual SORs, a loose sanity band only." |
| "290 °C steam at the sandface" | "At our assumed pressures the sandface fluid is hot water, not steam, unless the near-well region is depleted below 7.4 MPa (unknown, top data ask)." |
| "Cold rate 0.475 m³/d" | "0.447 m³/d (2.8 bbl/d) at 11,500 cP; it now scales with viscosity." |
| "116 of 117 tests" | "148 passed, 1 xfailed" |

### 9.10 Not done / open (handed to the cascade or to data)

1. **Downstream regeneration.** `data/synthetic_cycles.csv`, `ml/models/*.joblib`,
   `ml/models/uq_summary.json`, `ml/models/dyno_cards.json`, the dashboard and the deck were not
   regenerated. `ml/train.py`, `ml/optimize.py`, `dashboard/`, `ppt/` and `docs/study/` are out of
   scope. The ML float classifier will have no positive class at the base params.
2. **Water cut as a state variable (T2-A).** It decides whether the float branch exists at all.
3. **Tubing temperature profile.** The rods still see the heated-zone temperature.
4. **Density mismatch.** `srp.peak_rod_load` uses oil density, `dyno` the mixture (review §7);
   not changed.
5. **Company-basis economics.** Royalty and cess are still not modelled.

   | Basis | Oil price | Rev-10 rec incr ₹/d |
   |---|---|---|
   | Pre-levy (current twin) | FY25 deck | +₹4.0k |
   | ~20 % + 20 % levies (review estimate) | ~₹3,600/bbl | negative |

---

## 10. Water cut state, injection-pressure and stroke levers (27 Sep)

Scope: close T2-A (water cut as a state, §9.10 item 2), fix the §9.7 steam P–T inconsistency by
making the injection pressure a control with the sandface temperature at T_sat, and add the
stroke length. Then re-optimise over five levers.

- Branch `harden`. `params/CHANGELOG.md` rev 11 has the key-by-key record.
- `pytest -q` → **171 passed, 2 xfailed (soak + peak band, both strict)**.
- Every change sits behind a switch that reproduces rev 10 to the digit
  (`cycle.legacy_rev10_params`, tested on three cases).
- **Calibration knobs: none changed.** `AOF_REF_M3D` stays 0.46.

### 10.1 What changed (physics; details in CHANGELOG rev 11)

1. **Water cut is a state.**
   - Produced water = condensate flowback + formation water.
   - Condensate:
     - `condensate_recovery_frac` 0.7 [ASSUMPTION 0.5–0.9, Prats/Butler] of the injected mass;
     - held in a well-mixed cell with the heated-zone pore volume φπr_h²h;
     - its share of the liquid is c = W/(W + V_p), so it decays exponentially with
       τ = (V_p + W)/q_L.
   - The rest of the liquid is at `formation_water_cut` 0.45 [ASSUMPTION 0.3–0.6; no
     Baghewala figure].
   - The day's water cut drives:
     - pump liquid;
     - the Brinkman emulsion viscosity (inversion 0.70), and through it drag, FI, the SPM
       ceiling and energy;
     - the Boberg–Lantz produced heat;
     - the column density;
     - power.
   - There is no water-handling cost key; lifting energy is in the power bill.
   - The cold well produces at the formation cut on the params' own pump.
2. **Injection pressure sets the steam state** (IAPWS-IF97).
   - T_wh = T_sat(P_wh).
   - P_sf = P_wh + homogeneous two-phase column (~1.0–1.2 MPa); T_sf = T_sat(P_sf).
   - h_del = x_sf·h_fg + h_f(P_sf) − h_f(T_R).
   - Fuel per tonne scales with wellhead enthalpy (±0.2 %). There is no compression cost: the
     generator sets the pressure.
   - The near-well recharge is **capped at P_sf**.
3. **Stroke length** takes the API sizes 64–144 in.
   - Displacement, drag velocity, FI, energy and Mills peak PRL all respond.
   - PRL cap `srp.max_prl_kN` = 113.9 kN: the C-320D-256-120 rating [TYPICAL, API 11E].
4. **Cutoff rule.** The rate cutoff applies only past the peak. Without this, the rising
   flowback limb would end a cycle on day 1. It is unchanged for every rev-10 cycle.

### 10.2 The P–T fix and the pressure default

At the CONFIRMED 85–97 kgf/cm² wellhead:

| Wellhead kgf/cm² | T_wh °C | P_sf MPa | T_sf °C | h_del MJ/kg | Recharge room at P_current 9.4 MPa |
|---|---|---|---|---|---|
| 85 | 298.7 | 9.45 | 306.9 | 1.658 | 0.05 MPa |
| 91 (default, baseline) | 303.5 | 10.12 | 311.9 | 1.672 | 0.72 MPa |
| 97 | 308.1 | 10.79 | 316.6 | 1.686 | 1.39 MPa |
| rev 10 | 290 (set) | – | 290 | 1.580 | uncapped 1.5 MPa |

**Why the pressure default had to change.**
- Injection needs P_sf > P_res. At the virgin 11.4 MPa, steam cannot enter at ANY published
  pressure, so `reservoir.P_current_kPa` null had to go.
- Default **9,400 kPa** [ASSUMPTION — derived from the injectivity requirement; top data ask]. It
  is the largest value that admits injection over the whole range, i.e. the optimistic
  (highest-rate) edge.
- It also reads BGW-08's 85 → 97 kgf/cm² record as the near-well region charging ~1.3 MPa over a
  1,040–1,560 t job. That is consistent with the calibrated 1.0 kPa/t boost. It is an
  interpretation, not proof.
- UQ samples U[7,400, 9,400].

**Checks.**
- `steam_state_check` now **passes at the default** with a 0.72 MPa injection margin and no
  warnings. This is tested.
- It warns only when P_res ≥ P_sf (tested at 11.4 MPa).

**Sensitivity of the reference to P_current:**
- 9.4 → 8.4 MPa: SOR +16 %;
- 9.4 → 7.4 MPa: SOR +46 % at the 1.2 cutoff, +26 % at a 0.8 cutoff. The Darcy limit is +29 %;
  the extra 17 pp at 1.2 is the cutoff truncating a cycle whose peak (1.68 m³/d) is only 40 %
  above it.

**The pressure lever itself is nearly flat.**
- On the reference, 85 → 97 kgf/cm² moves incremental ₹/d by −₹300.
- Two opposing channels:
  - hotter steam at an almost unchanged h_del gives a *smaller* heated zone (V = Q/(M_RΔT)):
    oil −1 %;
  - more recharge room (+₹100–240/d).
- Every unconstrained optimum in §10.6 picks 85.

### 10.3 Water-cut profile of the reference cycle (1,500 / 7 / 1.2 / 5 spm, 86 in, 91 kgf/cm²)

| Produce day | T_avg °C | μ_oil cP | oil m³/d | water cut | water m³/d | of which condensate | spm | FI |
|---|---|---|---|---|---|---|---|---|
| 0 | 269 | 5 | 1.98 | **0.872** | 13.46 | 11.84 | 5.00 | 0.00 |
| 14 | 223 | 10 | 1.93 | 0.856 | 11.44 | 9.86 | 5.00 | 0.00 |
| 30 | 191 | 18 | 1.89 | 0.837 | 9.68 | 8.13 | 5.00 | 0.00 |
| 60 | 152 | 47 | 1.85 | 0.797 | 7.28 | 5.77 | 5.00 | 0.00 |
| 90 | 127 | 109 | 1.81 | 0.756 | 5.59 | 4.11 | 5.00 | 0.00 |
| 120 | 110 | 226 | 1.74 | 0.714 | 4.34 | 2.92 | 5.00 | 0.00 |
| **131** | 104 | 290 | – | **< 0.70: stream turns oil-continuous** | | | | |
| 150 | 96 | 432 | 1.64 | 0.674 | 3.39 | 2.05 | 5.00 | **0.79** |
| 170 | 89 | 637 | 1.54 | 0.650 | 2.87 | 1.61 | 5.00 | 0.98 |
| 180 | 86 | 765 | 1.49 | 0.639 | 2.64 | 1.42 | 4.58 | 1.00 |
| 227 (end) | 74 | 1,654 | 1.19 | **0.597** | 1.77 | 0.79 | 2.80 | 1.00 |

- 934 of the 1,050 m³ of mobile condensate returns (62 % of the injected mass).
- Total water is 1,249 m³, against 2,111 m³ under the constant 85 % cut.
- The cut is monotone (the tank only drains), starts at 0.87 and ends at 0.60. This is tested.
- It does not start at 0.9+:
  - the mixing cell is volume-weighted, not mobility-weighted;
  - hot water is ~100× more mobile than 300 °C oil, so a fractional-flow split would start it
    higher and drain it faster.

  That is a stated structural assumption, not tuned.

### 10.4 Before / after

"Before" = rev 10 (§9.2, 290 °C steam, virgin pressure, constant 85 % cut). "After" = rev 11.
FY25 = ₹5,992/bbl, $65 = ₹4,840/bbl. Uplift = peak / cold rate at the pressure the IPR sees.

| Case | SOR gross | SOR incr | oil m³ | days (produce) | peak bbl/d | uplift | wc start → end | FI max @ produce day (alarm d) | incr ₹/d FY25 | incr ₹/d $65 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Before:** Reference 1500/7/1.2/5 | 4.027 | 5.40 | 372.5 | 211.3 (185) | 15.91 | 5.66 | 0.85 const | 0.000 (0) | +346 | −9,130 |
| **Before:** Baseline (b) 1300/10/1.3/5 | 4.061 | 5.50 | 320.1 | 186.6 | 15.13 | 5.38 | 0.85 const | 0.000 (0) | −1,587 | −10,715 |
| **Before:** rev-10 rec 1700/10/0.60/4 | 3.550 | 5.00 | 478.9 | 309.0 | 15.66 | 5.57 | 0.85 const | 0.000 (0) | +4,044 | −3,911 |
| **After:** Reference, 86 in / 91 | 3.899 | 5.15 | 384.7 | 254.3 (228) | **12.43** | 5.41 | 0.872 → 0.597 | **1.000 @ d172 (97; first d131)** | +4,246 | −4,025 |
| **After:** Baseline (b), 86 in / 91 | 4.007 | 5.33 | 324.5 | 219.6 (193) | 12.01 | 5.22 | 0.871 → 0.605 | **1.000 @ d163 (76; first d117)** | +1,910 | −6,101 |
| **After:** rev-10 rec 1700/10/0.60/4, 86 in / 91 | 3.239 | 4.46 | 524.8 | 393.0 (361) | 12.66 | 5.51 | 0.873 → 0.553 | **1.000 @ d205 (210)** | +8,941 | +1,939 |
| **After: rev-11 rec 1000/10/1.25/3 spm/64 in/93** | 3.799 | 5.22 | 263.2 | 194.5 (172) | 10.89 | 4.74 | 0.869 → 0.594 | 0.594 @ d171 (0) | **+2,153** | **−4,953** |
| After: rev-11 conservative (FI ≤ 0.5) 1000/10/1.35/3/64/85 | 4.075 | 5.58 | 245.4 | 180.5 (158) | 10.79 | 4.69 | 0.868 → 0.613 | 0.500 @ d157 (0) | −403 | −7,552 |

**Reading the table.**
- **Physics got worse for oil rate and better for heat.**
  - Peak −22 %: P_current 9.4 MPa plus the capped recharge.
  - The cycle runs 40 days longer on less hot water, so SOR is ~−3 % at the reference.
- **Attribution at the reference.**
  - The water-cut state alone takes SOR 4.03 → 3.15 (less heat carried out).
  - P_current alone takes it to 4.75 (peak 13.3).
  - IF97 steam plus the cap takes the peak to 12.4.
- **The incremental ₹ rose for a counterfactual reason.**
  - The cold well is now 0.366 m³/d (was 0.447).
  - At the 45 % formation cut its stream is an oil-continuous 51,000 cP emulsion. It pulls
    433 kWh/d grid (was 23), its FI is 1.0 and its PRL is 189 kN.
  - That lowers cold cash by ~₹6.3k/d (FY25) / ₹5.8k/d ($65). Every incremental margin rises by
    that amount; the argmax does not move.
  - The model is saying that a cold Baghewala well at 45 % water cannot be rod-pumped at 2 spm on
    the assumed unit. That is a **consistency flag on the Brinkman W/O branch (or on f_w below
    inversion)**, not a result to bank. A cold-well dyno card decides.
- **Bands.**
  - Reference SOR 3.90 is in the coordinator's 3.8–4.6 (the brief's AOF re-tune trigger did not
    fire).
  - SOR 3–8 over 500–3,000 t: pass. Uplift at 1,040 / 1,500 / 1,560 t: 5.04 / 5.41 / 5.45×.
  - Produce 228 d. CalGEM: pass. Darcy: pass, re-specified base, §10.2. dt invariance: pass.
  - **Peak 15–40 bbl/d FAILS (12.4)** and is kept as a strict xfail. AOF cannot rescue both
    bands:

    | AOF_REF_M3D | 0.46 | 0.50 | 0.55 | 0.58 |
    |---|---|---|---|---|
    | Peak bbl/d | 12.4 | 13.5 | 14.9 | 15.7 |
    | Reference SOR | 3.90 | 3.56 | 3.24 | 3.09 |

    **Team call:** either the depleted P_current is too low, or the 15 bbl/d floor (a field
    average over all 34 wells and all lift modes) is not a stimulated-well peak floor.

### 10.5 The honest rod-float verdict now

**The thesis binds again, at the base assumptions, in exactly the phase §9.6 predicted.**
- Once the condensate is produced back, the cut crosses the 0.70 inversion. That is produce day
  ~117–150 (131 at the reference), with T_avg ~100 °C and μ_oil ~300 cP.
- The stream turns oil-continuous. The Brinkman W/O viscosity is 20× the oil's.
- FI jumps from 0 to 0.8–1.0 within days at 5 spm / 86 in.
- The early, hot, water-continuous part never floats (FI < 0.05, tested).

**Every earlier recommendation now violates FI ≤ 0.6:**
- baseline (b): 76 alarm days;
- rev-9 point: 181 alarm days;
- rev-10 point: 210 alarm days.

**What it costs.**
- The feasible optimum is +₹2.2k/d FY25.
- The same grid unconstrained gives +₹9.6k/d at 1,500/85/0.60/64 in/4 spm.
- **The float constraint costs ~₹7.4k/d (FY25) / ₹8.0k/d ($65).**

**How the constraint is satisfied.** Only by stopping near the inversion (cutoff 1.25) with the
slowest rods on the grid (64 in × 3 spm).

**It is conditional on three assumptions.** f_w < inversion, the Brinkman W/O law, and the SPEC
0.6 line.

| Case | Canonical point | FY25 / $65 ₹/d | Price of FI constraint (FY25) |
|---|---|---|---|
| base | 1000/93/1.25/64/3 | +2,153 / −4,953 | 7,419 |
| f_w 0.30 | 1000/85/1.00/64/3 | +10,033 / +2,783 | 1,911 |
| f_w 0.60 | 2000/89/1.30/74/3 | −3,254 / −10,565 | 10,932 |
| inversion 0.60 | 1900/85/1.15/86/3.5 | +6,617 / −1,768 | 3,560 |
| inversion 0.75 | 1000/93/1.25/64/3 | +2,084 / −5,022 | 7,382 |
| condensate 0.9 | 2000/85/1.35/64/3 | −7,236 / −13,757 | 12,712 |
| AOF 0.556 (peak restored) | 1100/85/1.45/64/3 | +7,036 / −979 | 7,166 |
| constant 85 % cut (rev-10 stream, rev-11 steam/P) | 1600/85/0.60/86/3 | +514 / −6,359 | 0 |

**Say:** "With water cut as a state, the late-cycle stream turns oil-continuous around produce day
~130. In our model the rods then float at practice speeds, and staying under the SPEC float line
costs ~₹7k/day/well. Whether that is real depends on the inversion point, the late-cycle water
cut and the emulsion viscosity. All three are unmeasured. One late-cycle dyno card plus a
water-cut log settles it."

**Still do not:** present FI as a measured constraint.

**Structural caveats.**
- There is still no tubing temperature profile. The rods see T_avg, so a cooler tubing would make
  the W/O drag worse.
- The VFD schedule engages only at the rod-fall limit (ratio 1, §10.7).

### 10.6 New recommendation (5-D, exhaustive), decomposition

**Search.** `recommend_physics.best_settings_physics_5d`.
- Grid:
  - steam 1,000–2,000 (100);
  - wellhead pressure 85 / 89 / 93 / 97;
  - cutoff 0.60–2.00 (0.05);
  - stroke 64 / 74 / 86 / 100 / 120 / 144 in;
  - spm 3–6 (0.5);
  - soak fixed at 10 d.
- That is 53,592 points **exhaustively**: 1,848 simulations, each cutoff read off a lowest-cutoff
  run as a prefix. The prefix is proven equal to direct simulation and to `summary()`.
- Runtime 33 s alone (36–48 s with three runs in parallel).
- Coordinate descent was tried first. It stalled from the FI-infeasible rev-10 start on the
  constraint edge, hence the exhaustive search.
- Constraints: FI ≤ 0.6 (aggressive) / 0.5 (conservative), and the Mills PRL ≤ 113.9 kN on every
  day. 33,579 points fail the PRL cap; all of them are also FI-infeasible, so the PRL cap never
  binds separately below FI 0.6.

**Recommendations.**
- **Canonical (aggressive, minimax regret, both decks): 1,000 t / 10 d / cutoff 1.25 m³/d /
  3 spm / 64 in / 93 kgf/cm².**
  - FY25 +₹2,153/d, $65 −₹4,953/d. Regret 0: it is the optimum on both decks.
  - **Pinned at three grid edges:** steam floor, stroke floor, spm floor. The float constraint
    wants slower rods and smaller slugs than the box allows.
  - The 93 kgf/cm² is a float-edge artefact: 85 gives +₹2,445 at FI 0.601. **Operator reading:
    "85–93 kgf/cm², flat within ₹300/d".**
- **Conservative (FI ≤ 0.5):** 1,000 / 1.35 / 3 spm / 64 in / 85 → −₹403 / −₹7,552. It gives up
  ₹2.6k/d.

**Decomposition vs baseline (b) (1,300/10/1.3/5 spm/86 in/91), incremental ₹/d:**

| Target | Deck | Total | cutoff | spm | steam | stroke | pressure |
|---|---|---|---|---|---|---|---|
| rev-11 rec | FY25 | **+243** | +1,147 | +237 | −1,084 | −35 | −22 |
| rev-11 rec | $65 | +1,147 | +1,184 | +524 | −726 | +196 | −31 |
| rev-10 rec (FI-infeasible) | FY25 | +7,032 | +6,410 (91 %) | +307 | +315 | 0 | 0 |
| rev-9 rec (FI-infeasible) | FY25 | +6,934 | +6,342 (91 %) | +324 | +267 | 0 | 0 |

Values are Shapley over 5! orders and sum exactly.

**The gain over baseline (b) is tiny because baseline (b) itself floats** (FI 1.0, 76 alarm days).
- The rec buys "the same money with no float days", not more money.
- Against baselines that do not float the picture differs. Baseline-cutoff sensitivity: rec vs a
  1.6 cutoff baseline (FI 0.76) is +₹12.5k/d, and vs a 1.0 cutoff baseline (FI 1.0) −₹4.4k/d.
- **Never quote a single gain number.**

**Controls coverage** (`controls_coverage` in both optimiser outputs):
`{steam_volume: optimised, injection_pressure: optimised, soak: modelled-fixed, cutoff: optimised,
stroke_length: optimised, spm: optimised, vfd: modelled-as-spm-schedule}`.

### 10.7 VFD = the SPM schedule

The PS lists a VFD as a control.

**What a VFD does on a beam pump:** it sets the SPM set-point, and the twin's declining SPM
schedule IS that set-point trajectory.
- The cycle starts at the `spm` lever.
- Each day the schedule lowers it to the rods' drag-limited fall velocity.
- The floor is 2 spm.

The intra-stroke speed profile a VFD can also shape (slow downstroke) is out of scope: the
day-by-day model has no intra-stroke kinematics.

**One honest limit.** The schedule targets v_stroke/v_fall = 1 (rev 5), i.e. it engages *above*
the 0.6 alarm line. So under an FI ≤ 0.6 policy the set-point is effectively constant.
- A VFD policy that holds the alarm line (margin 0.6) was tested on six points. It gives the same
  oil (the pump is not the constraint) and ₹0.4–0.8k/d less power.
- It still exceeds 0.6 at the 2-spm floor in the W/O tail, so it does not relax the float
  constraint.
- Not adopted. The margin stays a code constant (`cycle.SPM_MARGIN`).

### 10.8 SPM and stroke now act through float and power, not oil

- At the reference, cycle oil moves < 1 % across 3–6 spm (tested). The IPR, not the pump, limits
  the rate from ~4 spm.
- Incremental ₹/d rises as SPM falls: 3 spm +₹4.9k vs 6 spm +₹4.0k, from less drag power and fewer
  float days.
- Only S·N matters for FI and capacity. So a shorter stroke works as a finer-grained lower SPM:
  64 in × 3 spm is 86 in × 2.2 spm, below the practice band.
- Strokes above 86 in never help. They also need a bigger unit than the assumed C-228 (capex not
  costed).

### 10.9 UQ smoke (300 draws, seed 42, 16 inputs; not the bake; outputs in the scratchpad, `ml/models` untouched)

**Paired probabilities, FY25 deck** (the $65 deck in brackets where different):

| Quantity | Value |
|---|---|
| P(rev-11 rec > baseline) | **0.64** (0.79) |
| P(rev-9 rec > baseline) | 0.997 |
| P(rev-10 rec > baseline) | 0.99 |

**P(FI ≤ 0.6) by point:**

| Point | P(FI ≤ 0.6) |
|---|---|
| Rec | **0.88** |
| Baseline | 0.69 |
| Reference | 0.56 |
| rev-9 | 0.23 |
| rev-10 | 0.20 |

**P(incremental > 0) by point:**

| Point | P(incr > 0) |
|---|---|
| Rec | 0.12 |
| Baseline | 0.13 |
| rev-10 | 0.41 |

**Robustness failure of a fixed high cutoff.**
- In **41 %** of draws the rec's 1.25 m³/d cutoff sits at or above the achievable peak (low skin,
  low P_current, high μ). The cycle then ends right after its peak (< 600 bbl) and the per-day
  margin collapses to −₹0.1–0.36 M.
- The baseline has the same problem in 39 % of draws; the reference in 29 %.
- Excluding those draws, P(rec > baseline) = 0.50.
- **A float-driven fixed cutoff is fragile.** A cutoff tied to the float onset (water cut
  crossing the inversion) or to CADP would be the robust operating rule. That is not built.

**OAT tornado on the rec.**
1. s_cold ₹307k/d (degenerate at S = 0)
2. μ_ref ₹33k/d
3. P_current ₹24k/d
4. diesel discount ₹13k/d
5. condensate_recovery ₹12k/d

**MC correlation.** s_cold +0.67, μ_ref −0.46, P_current +0.22.

### 10.10 Judgement calls (team must know)

1. **P_current 9.4 MPa default** (injectivity-derived, optimistic edge). It moves the peak below
   the field band. The alternative, AOF 0.556, restores the peak and puts SOR at 3.2.
2. **AOF not re-tuned** (brief rule: SOR 3.90 is inside 3.8–4.6). Peak band → strict xfail.
3. **Mixing-cell (volume-weighted) flowback.** It is not fractional flow; it is conservative on
   early water cut.
4. **Recharge capped at P_sf.** It makes the calibrated boost non-binding above ~0.48 kPa/t.
5. **Cold well at the formation cut on the baseline pump.**
   - The W/O cold stream is unpumpable in the model (PRL 189 kN).
   - It inflates every incremental ₹ by ~₹6k/d.
6. **Cutoff past-peak rule.**
7. **Reference SOR band re-specified to the coordinator's 3.8–4.6.**
8. **Darcy band evaluated at cutoff 0.8.**

### 10.11 What we now say / stop saying

| Stop saying | Say instead |
|---|---|
| "Water cut 85 %" | "Water cut is a state: ~0.87 at first production (condensate flowback), falling to ~0.60 late (formation cut 0.45, assumed)." |
| "At 85 % water cut the rods never float" (§9) | "With a realistic falling water cut the late-cycle stream turns oil-continuous around produce day ~130; in our model the rods then float at practice speeds. Conditional on the inversion point and emulsion law — unmeasured." |
| "Recommendation 1,700 / 0.60 / 4" | "1,000 t / cutoff 1.25 / 3 spm / 64-in stroke / 85–93 kgf/cm² keeps FI under the SPEC line (+₹2.2k/d FY25, −₹5.0k/d at $65). It sits on three grid edges and fails in ~40 % of UQ draws where the peak never clears the cutoff." |
| "290 °C steam" / "the sandface fluid is hot water" (§9) | "Steam state follows the wellhead pressure: 299–308 °C at the wellhead, 307–317 °C saturated at the sandface, given a near-well pressure ≤ 9.4 MPa (assumed; top data ask)." |
| "Injection pressure / stroke are not modelled" | "Both are levers. Pressure is nearly flat (≤ ₹300/d over 85–97). Stroke matters only through S × SPM and float; longer strokes need a bigger unit." |
| "VFD not covered" | "The VFD is the SPM set-point schedule the twin already computes; intra-stroke speed shaping is out of scope." |
| "+₹4.0k/d at 1,700/0.60/4" (§9) | "That point floats the rods for 210 days in the rev-11 model; the float-feasible optimum is +₹2.2k/d, and the float line costs ~₹7k/d." |
| "148 passed, 1 xfailed" | "171 passed, 2 xfailed (soak + peak band, both strict)" |

### 10.12 Not done / open

1. **Downstream not regenerated.** `data/`, `ml/models/*` (incl. `gain_decomposition.json`,
   `uq_summary.json`, `dyno_cards.json`), the dashboard, the deck and the ML surrogate.
   - `twin/generate_data.py` does not sample pressure or stroke; the cascade decides.
   - The API `/calibrate/demo` fits rev-11 physics against the rev-10 demo CSV (`data/` is out of
     scope). The tests pin the rev-10 switches for the demo.
2. **Mobility-weighted (fractional-flow) flowback**, and a float-onset / CADP cutoff rule (the
   robust fix for §10.9).
3. **Tubing temperature profile.** It is still missing, and it matters more now: W/O drag at
   tubing T.
4. **Unit gearbox torque rating.** Only the PRL cap is modelled. Capex for longer-stroke units is
   not modelled either.
5. **Data asks, in priority order:**
   1. a water-cut-vs-time log for one CSS cycle;
   2. one late-cycle dyno card and one cold-well card;
   3. a static BHP survey (P_current);
   4. the wellhead P and T logged together during one injection.

---

## 11. Wave 4: emulsion law, float-onset rule, AOF/peak band (27 Sep)

Scope: the three coordinator decisions after §10.
1. Replace the Brinkman W/O branch with a published law plus a cap, and re-check the cold well.
2. End the produce phase on an operating rule: rate cutoff **or** float onset.
3. Re-tune only `AOF_REF_M3D` to the field peak band, and re-specify the reference-SOR band.

Then re-optimise, re-decompose, re-run UQ, and extend the LHS.

- Branch `harden`. `params/CHANGELOG.md` rev 12 has the key-by-key record.
- `pytest -q` → **197 passed, 2 xfailed**:
  - soak: still a strict xfail;
  - peak band: now **passes** (un-xfailed);
  - new strict xfail: the cold well is not pumpable at 2 spm.
- `cycle.legacy_rev11_params` reproduces every §10.4 number to the digit (tested on three cases).
  `legacy_rev10_params` sets the rev-12 switches off too.
- UQ and decomposition outputs are in the session scratchpad. `ml/models/` is untouched.

### 11.1 The emulsion law: what the physics said

The brief's premise was that Brinkman (1 − φ)^−2.5 over-predicts at 30–50 % water for deformable
droplets. **It does not.**

**Pal & Rhodes (1989) is Brinkman on a solvated fraction.**
- Pal & Rhodes: μ_r = [1 + (φ/φ*)/(1.187 − φ/φ*)]^2.49.
- Algebraically that is μ_r = (1 − φ/(1.187 φ*))^−2.49.
- Brinkman is therefore the special case φ* = 1/1.187 = 0.842, with no solvation.
- Fitting φ* to the centre of the brief's published heavy-oil band (√(2·10) = 4.5× at 45 % water)
  gives **φ* = 0.84**. That is Brinkman to within 1 % below 60 % water.
- Pal & Rhodes' own fitted emulsions (φ* ~0.6–0.85, recalled, not re-retrieved in full) are *more*
  viscous than Brinkman.
- Over the UQ range φ* 0.65–1.0 the law gives 9× → 3.3× at 45 % water. Brinkman's 4.46× sits
  inside the published band.

**Deformable droplets.**
- Taylor's (1932) intrinsic viscosity for clean droplets in a much more viscous continuous phase
  (λ = μ_w/μ_o ≈ 5×10⁻⁵) is ~1, not 2.5. That gives ~1.8× at 45 %.
- Asphaltene-stabilised crude W/O interfaces behave rigid, and the published 2–10× data agree with
  [η] ≈ 2.5, not 1.

**What changes the physics is the 10× cap** [ASSUMPTION = the top of the band]. Brinkman gave:

| Water cut | 0.30 | 0.45 | 0.50 | 0.60 | 0.65 | 0.69 |
|---|---|---|---|---|---|---|
| Brinkman μ_r | 2.44 | 4.46 | 5.66 | 9.88 | 13.8 | 18.7 |
| Pal–Rhodes φ* 0.84, capped | 2.44 | 4.46 | 5.66 | 9.90 | **10.0** | **10.0** |

The late-cycle stream sits at wc 0.60–0.70, which is exactly where the cap binds.
- Float onset moves later: first alarm at the reference is produce day 131 → **149**.
- FI rises more gently: 0.63 on the 3rd alarm day, where it was 1.0 within days.

### 11.2 Cold-well sanity check

The brief asked that the cold well be pumpable at ≥ 2 spm on the assumed unit. **It is not, and
the law change does not touch it.**

| | rev 11 (Brinkman) | rev 12 (Pal–Rhodes + cap, AOF 0.56) |
|---|---|---|
| Stream | 45 % water, W/O, 4.46 × 11,500 cP | same (below the cap) |
| μ_drag | 51,261 cP | 51,261 cP |
| FI / fillage | 1.00 / 0.37 | 1.00 / 0.37 |
| Mills PRL (rating 113.9 kN) | 189.4 kN | 189.4 kN |
| Polished-rod / grid energy | 260 / 432.8 kWh/d | 260 / 433.5 kWh/d |
| Oil rate | 0.366 m³/d (2.30 bbl/d) | **0.445 m³/d (2.80 bbl/d)**, from the AOF |
| Cold cash FY25 / $65 | ₹5,315 / ₹2,667 per day | ₹8,305 / ₹5,080 per day |

**Pumpability threshold** (FI < 1 and PRL ≤ 113.9 kN):

| Unit | Pumpable if |
|---|---|
| 2 spm × 86 in (assumed unit) | μ_r ≤ ~1.9 (dead oil 84.8 kN; 2× already 115 kN) |
| 2 spm × 64 in | μ_r ≤ ~2.6 |
| 1 spm × 64 in | the base emulsion (FI 0.85, PRL 104.5 kN, 90 kWh/d) |

**What that means.**
- Under any published W/O law in its published constant range, the model cannot rod-pump a cold
  Baghewala well at 45 % water at the 2-spm keep-moving floor.
- The field did produce these wells cold at ~2–3 bbl/d. So one of four things is wrong:
  - the emulsion factor at the cold well (only a Taylor-limit, i.e. unstabilised, emulsion
    passes);
  - the formation cut (f_w ≥ ~0.25 already fails);
  - the lumped rod drag (K_VISC);
  - the 2-spm floor for the cold well.
- A cold-well dyno card decides. Recorded as a strict xfail
  (`test_cold_well_pumpable_at_2_spm_on_the_assumed_unit`).

**The "+₹6.3k/d counterfactual artefact" shrank by ₹0** from the emulsion change: cold power
432.8 → 433.5 kWh/d.
- The AOF retune separately makes the cold well more productive: cold cash +₹3.0k/d FY25. That
  *lowers* every incremental margin by ~₹3.0k/d, legitimately.
- The part of the artefact still standing: the cold well pays ~₹2.7k/d more power than a
  pumpable 1-spm × 64-in cold well would. Every incremental margin below is inflated by that
  amount. The rec's FY25 +₹7,973 would be ~+₹5.2k against a 1-spm cold well, and its $65 +₹40
  would be ~−₹2.7k.

### 11.3 The float-onset rule, and why it is the honest operator model

**What the rule is.** `css.produce_end_rule = "either"` (default). The produce phase ends when
either:
- the oil rate (past its peak) is below the cutoff; or
- FI > 0.6 on **3 consecutive days** (`fi_alarm_days` [ASSUMPTION]).

The last produce day is the 3rd alarm day. `rate_cutoff` = rev 11; `float_onset` = the float rule
only.

**Why it is honest.** Until rev 11 the model had two choices, both dishonest.
- It let the cycle run floating rods for 76–210 days (the rate cutoff never looks at the rods).
- Or it forbade any float day, which made the optimiser pick a **high fixed cutoff** that ends the
  cycle before the inversion. That cutoff is fragile:
  - in 41 % of UQ draws the peak never cleared it (§10.9);
  - an operator would never write such a rule, because it encodes "stop before a water-cut event
    you can't see" as a rate.

A real operator watches the dyno card.
- When it shows float (carrier-bar separation, a compressed downstroke), he first slows the unit.
  The SPM schedule already slows to the fall-velocity limit.
- If float persists he pulls the well, i.e. ends the produce phase and re-steams. He does not run
  floating rods for months (rod fatigue, a parted string, a workover).

So the rule is the observable the operator acts on, applied the way he would apply it: a
confirmation window, then stop. The rate cutoff stays as the economic backstop. The FI ≤ 0.6
feasibility check stays too, as an *additional* test that the cycle sees no more alarm days than
the rule needs to trigger (it catches non-consecutive alarms). With the rule it never bound:
P(alarm days > 3) = 0 in every UQ draw at every point.

**Which rule ends each cycle** (base physics):

| Case | Ends by | Produce day | Days after peak | Rate at end |
|---|---|---|---|---|
| Reference 1500/7/1.2/5/86/91 | **float onset** (first alarm d149) | 151 | 151 | ~1.9 m³/d (cutoff 1.2 never reached) |
| Baseline (b) 1300/10/1.3/5/86/91 | **float onset** | 139 | 139 | > 1.6 (cutoff 1.0/1.3/1.6 give the identical cycle) |
| rev-12 rec 1000/10/0.6/3/64/85 | **float onset** (first alarm d177) | 179 | 120 | 1.40 (any cutoff 0.6–1.4 is identical) |
| rev-12 conservative (pull at FI > 0.5) | float onset at the 0.5 line | 165 | 106 | |
| Fixed-cutoff alternative 1000/10/1.55/3/64/85 | rate cutoff | 162 | 103 | |
| rev-11 rec re-run 1000/10/1.25/3/64/93 | float onset | 179 | 119 | |

**What the rule costs at the practice points.**
- Reference: rate-cutoff rule SOR 3.18 / 240 produce days → `either` 4.50 / 152 days.
- **Ending 88 days early costs the reference ₹14.3k/d of incremental margin** (FY25 +₹12,600 →
  −₹1,690), because the late oil is cheap. Baseline (b): +₹11,268 → −₹1,601 (ends at 1.87 m³/d
  instead of 1.30).
- **At 5 spm × 86 in, the practice-band speed, the late oil is not reachable without running
  floating rods.** That is the new physics finding. The whole optimisation below is about
  delaying the float onset.

### 11.4 Peak band vs SOR band: AOF retune

Reference (either rule), AOF sweep:

| AOF_REF_M3D | 0.46 (rev 11) | 0.50 | 0.54 | 0.55 | **0.56** | 0.57 | 0.58 | 0.60 |
|---|---|---|---|---|---|---|---|---|
| Peak bbl/d (15–40) | 12.43 ✗ | 13.51 ✗ | 14.59 ✗ | 14.86 ✗ | **15.13** | 15.40 | 15.68 | 16.22 |
| Reference SOR (3.0–4.6) | 5.05 ✗ | 4.82 ✗ | 4.60 (edge) | 4.55 | **4.50** | 4.45 | 4.40 | 4.34 |
| Uplift 1500 / 1040 / 1560 t | 5.41 / 5.04 / 5.45 at every AOF | | | | | | | |
| Produce days (≥ 90) | 165 | 159 | 154 | 153 | **152** | 151 | 150 | 147 |
| SOR 500–3,000 t (3–8) | 4.04–6.11 | 3.86–5.82 | 3.67–5.56 | 3.60–5.51 | **3.54–5.45** | 3.48–5.40 | 3.42–5.34 | 3.32–5.25 |
| Cold rate at P_current / virgin | 0.366 / 0.447 | 0.397 / 0.486 | 0.429 / 0.525 | 0.437 / 0.535 | **0.445 / 0.544** | 0.453 / 0.554 | 0.461 / 0.564 | 0.477 / 0.583 |
| Bands failed | 2 | 2 | 1 | 1 | **0** | 0 | 0 | 0 |

- The uplift is AOF-invariant: peak and cold rate both scale with AOF. The brief's worry
  ("uplift may fall outside 5–6×") does not arise.
- **0.56 is the smallest AOF that passes every band.** It keeps the cold rate lowest, i.e. the
  least departure from the rev-5 calibration.
- Reference-SOR band re-specified to **3.0–4.6**:
  - literature CSS 3–8;
  - Kern River 2021 field SOR 3.47 (CalGEM);
  - the old 3.8–4.6 was our plan target, not data.
- The rate-cutoff reference at 0.56 (SOR 3.18) would also pass it.

**Other bands at 0.56:**
- CalGEM: pass.
- dt: pass (1 vs 0.25 d within 0.2 %).
- P–T check: pass (unchanged).
- Steam margin optimum over 500–3,000 t: 1,000 t (interior, inside 1,000–2,000).
- Cold rate < the 0.6 cutoff floor at both pressures: pass.
- Produce ≥ 3 months: 152 d, pass.

**Darcy band.** Its measurement was re-specified; the band itself is unchanged.

| How the depletion response (9.4 → 7.4 MPa) is measured | ΔSOR | Band [23.9 %, 43.9 %] |
|---|---|---|
| Darcy limit 1/r − 1 | +28.9 % | |
| `either` rule | +15.5 % | fails: the depleted cycle floats later, because its slower liquid drains the condensate tank more slowly, so the rule lengthens it |
| Rate cutoff 0.8 at AOF 0.56 | +22.5 % | 1.4 pp under the lower edge (Boberg–Lantz: the slower well carries less heat out) |
| **Fixed 120-d produce window** (the derivation's literal "fixed-duration cycle") | **+25.4 %** | pass, at every AOF and either rule |

The test now uses the fixed window. The rule's own effect (+15.5 %) is reported, not hidden.

### 11.5 Before / after

FY25 = ₹5,992/bbl, $65 = ₹4,840/bbl. Before = rev 11 (§10.4). Uplift = peak / cold rate.
Settings are written steam/soak/cutoff/spm/stroke in/kgf/cm².

| | Case | SOR gross | SOR incr | oil m³ | days (produce) | peak bbl/d | uplift | wc start → end | FI max (alarm d) | ended by (produce day; days after peak) | incr ₹/d FY25 | incr ₹/d $65 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Before | Reference 1500/7/1.2/5/86/91 | 3.899 | 5.15 | 384.7 | 254.3 (228) | 12.43 | 5.41 | 0.872 → 0.597 | 1.000 (97) | rate cutoff (d227; +227) | +4,246 | −4,025 |
| Before | Baseline (b) 1300/10/1.3/5/86/91 | 4.007 | 5.33 | 324.5 | 219.6 (193) | 12.01 | 5.22 | 0.871 → 0.605 | 1.000 (76) | rate cutoff (d192; +192) | +1,910 | −6,101 |
| Before | rev-11 rec 1000/10/1.25/3/64/93 | 3.799 | 5.22 | 263.2 | 194.5 (172) | 10.89 | 4.74 | 0.869 → 0.594 | 0.594 (0) | rate cutoff (d171; +129) | +2,153 | −4,953 |
| Before | rev-11 conservative 1000/10/1.35/3/64/85 | 4.075 | 5.58 | 245.4 | 180.5 (158) | 10.79 | 4.69 | 0.868 → 0.613 | 0.500 (0) | rate cutoff (d157; +117) | −403 | −7,552 |
| After | Reference | 4.499 | 5.91 | 333.4 | 178.3 (152) | **15.13** | 5.41 | 0.872 → 0.631 | 0.635 (3) | **float onset** (d151; +151) | −1,690 | −11,941 |
| After | Baseline (b) | 4.351 | 5.80 | 298.8 | 166.6 (140) | 14.62 | 5.22 | 0.871 → 0.625 | 0.634 (3) | **float onset** (d139; +139) | −1,601 | −11,295 |
| After | **rev-12 rec 1000/10/0.60/3/64/85** | **3.191** | **4.49** | 313.4 | 202.5 (180) | 13.00 | 4.65 | 0.868 → 0.556 | 0.622 (3) | **float onset** (d179; +120) | **+7,973** | **+40** |
| After | rev-12 conservative, same settings, pull at FI > 0.5 | 3.413 | 4.79 | 293.0 | 188.5 (166) | 13.00 | 4.65 | 0.868 → 0.571 | 0.517 (0) | float onset @0.5 (d165; +106) | +5,609 | −2,369 |
| After | Fixed-cutoff alternative (FI ≤ 0.5 all cycle) 1000/10/1.55/3/64/85 | 3.467 | 4.87 | 288.4 | 185.5 (163) | 13.00 | 4.65 | 0.868 → 0.575 | 0.497 (0) | rate cutoff (d162; +103) | +5,008 | −2,972 |
| After | rev-11 rec re-run | 3.200 | 4.51 | 312.5 | 202.5 (180) | 13.05 | 4.66 | 0.869 → 0.555 | 0.625 (3) | float onset (d179; +119) | +7,758 | −143 |

**Reading the table.**
- **The rec's uplift is 4.65, below the 5–6× band.** 3 spm × 64 in is pump-limited for its first
  59 produce days, so the peak is clipped. The reference, where the band is tested, is 5.41.
- **The incremental ₹ at the practice points went down** (reference −₹5.9k/d, baseline (b)
  −₹3.5k/d). Three causes:
  - float onset truncates the cheap late oil;
  - AOF raises the cold well's cash (₹3.0k/d);
  - the higher peak partly offsets both.
- **The rec's went up** (+₹2.2k → +₹8.0k/d FY25) because it is the only kind of point that
  exploits the rule: slow rods, float late.

### 11.6 Re-optimisation (5-D, both decks, `either` rule, soak 10)

**Search.** `best_settings_physics_5d` over the §10.6 grid, 53,592 points.
- 3,696 simulations, 36 s: the conservative level now has its own grid (see below).
- The cutoff-prefix trick still holds: the float-onset end does not depend on the cutoff (tested).

**Aggressive.**
- Feasible = float-alarm days ≤ 3 and PRL ≤ 113.9 kN on every day. **All 53,592 points pass.**
- The rule ends every cycle before the PRL cap or extra alarm days can bind (0 PRL failures,
  against 33,579 in rev 11).

**Canonical (minimax regret, both decks): 1,000 t / 10 d / 85 kgf/cm² / 64 in / 3 spm, cutoff
0.60 m³/d as a backstop.**
- It is the optimum on both decks, regret 0.
- FY25 **+₹7,973/d**, $65 **+₹40/d**. Gross SOR 3.19, incremental 4.49.

**Operator-rounded:** "1,000 t at 85 kgf/cm², soak 10 d, 64-in stroke at 3 spm, produce until the
float alarm has persisted 3 days. Keep a 0.6 m³/d rate backstop; any cutoff 0.6–1.4 gives the
identical cycle at base physics, and the low one is what keeps it robust."

**Pinned at five grid floors:** steam 1,000, pressure 85, cutoff 0.60, stroke 64 and spm 3. The
float onset is what ends the cycle, so every lever that delays it is pushed to its slow/small
end:
- **SPM** (at 64 in, 1000/85):

  | SPM | 3 | 3.5 | 4 | 5 |
  |---|---|---|---|---|
  | FY25 ₹/d | +7,973 | +7,589 | +6,317 | +2,647 |

- **Stroke** (at 3 spm):

  | Stroke | 64 in | 74 in | 86 in |
  |---|---|---|---|
  | FY25 ₹/d | +7,973 | +7,483 | +6,158 |

- **Pressure:** 85 → 97 costs ₹480/d.
- **Steam:** 1,000 → 1,500 t costs ₹2.6k/d.

**Steam floor.** With the steam grid opened to 700 t (68,208 points):
- the aggressive optimum is **interior**: 900 t on FY25 (+₹8,080) and 800 t on $65 (+₹296);
- minimax is 900 t: +₹8,080 / +₹266, regret ₹30;
- 1,000 → 900 t is worth ₹107/d (FY25) and ₹226/d ($65), inside model noise.

BGW-8's smallest published job was ~1,040 t, so **1,000 t stays the recommended floor**. The
conservative level runs to the 700-t floor.

**Conservative variant: the same settings, operated with the pull line at FI 0.5.** This is the
conservative level of the optimiser: the rule with `fi_alarm` 0.5 on its own grid. Its minimax
point is the identical 1000/85/64/3.
- FY25 +₹5,609 / $65 −₹2,369. It gives up ₹2.36k/d, ends on produce day 165, and never sees an
  FI > 0.6 day at base physics.
- The *fixed-cutoff* reading of "conservative" (FI ≤ 0.5 all cycle, ending on a 1.55 cutoff) is
  +₹5,008 / −₹2,972. It is **fragile** (§11.8): it brings back the §10.9 failure mode. Do not
  present it.

**The price of the rule vs the old constraint** (same new physics, rate-cutoff rule):

| Operating model | Settings | FY25 ₹/d | $65 ₹/d |
|---|---|---|---|
| Rate-cutoff rule, FI ≤ 0.6 feasible optimum | 1000/85/1.45/64/3 | +7,207 | −748 |
| Rate-cutoff rule, unconstrained optimum (runs floating rods, FI 1.0; 40,660 grid points over the PRL cap) | 1700/85/0.80/64/5 | +14,517 | +6,497 at 1300/85/0.60/64/4.5 |
| Rec settings, rate-cutoff rule (floats 100+ days) | 1000/85/0.60/64/3 | +12,336 | +5,829 |
| **Float-onset rule** | rec | **+7,973** | **+40** |

- The rule is **₹766/d better** than the FI-constrained rate-cutoff optimum at base physics, and
  robust where that one is not.
- The "price of the float line" of §10.5 (~₹7.4k/d) is now ~₹6.5k/d (FY25): the unconstrained
  minus the rule optimum. It is only reachable by running floating rods for months.

### 11.7 Decomposition vs baseline (b), and baseline-cutoff sensitivity

Shapley over 120 orders; the terms sum exactly. Baseline (b) = 1300/10/1.3/5 spm/86 in/91.

| Target | Deck | Total | cutoff | spm | steam | stroke | pressure |
|---|---|---|---|---|---|---|---|
| **rev-12 rec** | FY25 | **+9,574** | **0** | +5,966 (62 %) | +593 (6 %) | +3,039 (32 %) | −23 |
| rev-12 rec | $65 | +11,335 | 0 | +6,767 (60 %) | +1,030 (9 %) | +3,530 (31 %) | +8 |
| rev-11 rec (re-run) | FY25 | +9,359 | 0 | +5,754 | +662 | +2,959 | −17 |
| rev-9 rec 1600/0.70/4 | FY25 / $65 | +2,828 / +2,408 | 0 | +3,424 / +3,445 | −596 / −1,037 | 0 | 0 |
| rev-10 rec 1700/0.60/4 | FY25 / $65 | +2,545 / +2,006 | 0 | +3,492 / +3,520 | −947 / −1,514 | 0 | 0 |

**The gain moved from the cutoff to the rods.** In rev 10/11, 83–96 % of the headline was the
cutoff moving from our assumed 1.3 m³/d (review finding 1, which still holds under the rev-11
switches; tested).
- Under the `either` rule, both baseline (b) and the rec end on float onset, long before either
  cutoff binds. The cutoff contributes **exactly 0**.
- The whole gain is "slow the rods so the float onset comes later" (SPM + stroke ≈ 94 %).

**Baseline-cutoff sensitivity (1.0 / 1.3 / 1.6).** Baseline (b) is −₹1,601/d FY25 (−₹11,295 $65)
at **every** cutoff, because float onset ends it at produce day 139 with the rate still above 1.6.
- The gain is +₹9.6k/d (FY25) / +₹11.3k/d ($65) whatever OIL's real cutoff is.
- **The "₹2–11k/d depending on OIL's cutoff" caveat (§9.5) no longer describes the model.** The
  unknown that now carries the gain is **OIL's real SPM and stroke**, and whether their rods
  float late in the cycle. Our baseline 5 spm × 86 in is an assumption.

### 11.8 Robustness: UQ smoke

300 draws, seed 42, 17 inputs (+ `emulsion_phi_star` U[0.65, 1.0] appended). Outputs in the
scratchpad. FY25 deck; $65 in brackets where different.

| Point | P(beats baseline) | P(any FI > 0.6 day before the rule ends it) | P(alarm days > 3) | P(ended by float-onset rule) | **P(ends ≤ 5 d after peak)** | P(incr > 0) |
|---|---|---|---|---|---|---|
| **rev-12 rec** | **0.930** (0.967) | 0.947 | 0 | 0.947 | **0.000** | 0.350 (0.140) |
| rev-12 conservative (pull at 0.5) | 0.920 (0.957) | 0.197 | 0 | 0.947 | 0.000 | 0.287 (0.120) |
| Fixed-cutoff alternative 1.55 | 0.367 (0.423) | 0.083 | 0 | 0.070 | **0.397** | 0.153 (0.057) |
| rev-11 rec, rev-12 physics | 0.743 (0.840) | 0.300 | 0 | 0.280 | 0.177 | 0.237 |
| Reference | 0.620 (0.527) | 0.650 | 0 | 0.643 | 0.057 | 0.173 |
| Baseline (b) | – | 0.553 | 0 | 0.550 | 0.127 | 0.170 (0.047) |

Same metric, **rev-11 physics** (`legacy_rev11_params`, same draws):
- rev-11 rec 0.337;
- baseline 0.293;
- reference 0.180;
- P(rev-11 rec > baseline) 0.637.

**The fragility metric fell from 34 % (41 % on §10.9's "cutoff ≥ peak" definition) to 0.0 %.**
The rec never ends within 5 days of its peak in any draw: produce phase p10/p50/p90 = 161/202/269
d, 120+ days past the peak at base.
- The rule is what does it. The same settings with a fixed 1.55 cutoff are fragile in 40 % of
  draws.

**The "P(FI-alarm before rule)" column.** For the rec, 95 % of draws see float alarm days, but
never more than the 3 the rule needs to act. That is the design: the rule *is* the float response.
The conservative pull line cuts the FI > 0.6 exposure to 20 %.

**Incremental ₹/d of the rec:**

| Deck | p10 | p50 | p90 |
|---|---|---|---|
| FY25 | −14.8k | −4.1k | +10.7k |
| $65 | −19.8k | −10.2k | +2.5k |

**The base case is optimistic within the UQ ranges** (P_current at its top edge, skin 5 of 0–8).
The rec beats the baseline robustly (93–97 %), but CSS itself beats the cold well in only 35 %
(FY25) / 14 % ($65) of draws. That is before the ~₹2.7k/d cold-power artefact of §11.2 is
removed.

**OAT tornado on the rec** (FY25):
1. s_cold ₹24.1k/d
2. condensate_recovery_frac ₹19.1k/d
3. formation_water_cut ₹17.2k/d
4. μ_ref ₹13.5k/d
5. oil price ₹12.4k/d
6. diesel discount ₹12.3k/d

**MC correlation.** s_cold +0.48, oil price +0.33, condensate_recovery −0.33, diesel discount
+0.32. The two water-cut-state inputs are now 2nd and 3rd: they set *when* the inversion and the
float onset happen.

### 11.9 Judgement calls (team must know)

1. **Emulsion.** Pal–Rhodes at φ* 0.84 is Brinkman below 60 % water. The operative change is the
   [ASSUMPTION] 10× cap. The brief's "Brinkman over-predicts at 30–50 %" was not borne out and is
   recorded as such.
2. **Cold well.** Left unpumpable (2-spm floor, 86 in). It is a strict xfail finding, not fixed.
   Every incremental ₹ carries ~₹2.7k/d of cold-well power that a pumpable (1-spm) cold well would
   not pay.
3. **`fi_alarm_days` = 3** [ASSUMPTION]. It is an operating rule, not physics; OIL's SOP would
   replace it.
4. **The mechanism the rec exploits.** Slow rods delay float onset partly because a pump-limited
   well lifts liquid more slowly. The condensate tank drains more slowly, so the stream crosses
   the inversion later (rec: first alarm d177 vs d149 at the reference).
   - This rides on the §10.3 mixing-cell (volume-weighted) flowback.
   - A fractional-flow flowback would drain condensate faster early and could shorten that
     benefit.
5. **Conservative = the same rule with the pull line at 0.5,** not "never alarm". The fixed-cutoff
   form of "never alarm" is the fragile rule this wave removed.
6. **AOF 0.56 and the reference-SOR band 3.0–4.6.**
7. **Darcy band measured on a fixed produce window.** Under the rule it reads +15.5 %, which is
   reported.
8. **Soak.**
   - Under the float rule, margin per cycle-day falls ~0.6–0.7 % per day of soak beyond 5 d
     (10 d practice costs ~₹520/d of gross margin per cycle-day vs 5 d at the reference).
   - Still no meaningful interior optimum (strict xfail). Soak is held at 10 d.
   - The plateau benchmark is evaluated under the rate-cutoff rule.
9. **The rec sits on four or five grid floors.** 3 spm is the practice-band floor and 64 in the
   smallest API stroke. The model would go slower if allowed, which is the float-onset mechanism
   again. 1,000 t is kept although 800–900 t is ~₹0.1–0.2k/d better.
10. **The rec's 4.65× uplift is below the 5–6× band.** That is a property of slow rods clipping the
    peak, not of the calibration. The reference is 5.41×.

### 11.10 What we now say / stop saying

| Stop saying | Say instead |
|---|---|
| "Recommendation 1,000 t / cutoff 1.25 / 3 spm / 64 in / 93 kgf/cm²" (§10) | "1,000 t at 85 kgf/cm², 64-in stroke at 3 spm, soak 10 d; produce until the rod-float alarm has persisted 3 days (0.6 m³/d rate backstop). +₹8.0k/d FY25, ≈ break-even at $65 in the model, before the cold-well power caveat." |
| "It fails in ~40 % of draws where the peak never clears the cutoff" | "Ending on the float alarm instead of a fixed cutoff removed that failure: 0 % of 300 draws end within 5 days of the peak; P(beats our baseline) 93 % (FY25) / 97 % ($65)." |
| "83–96 % of the gain is the cutoff" / "₹2–11k/d depending on OIL's cutoff" | "Under the float-onset rule the gain is slower rods (SPM ~60 %, stroke ~30 %) delaying the late-cycle float; the cutoff contributes nothing. It depends on OIL's real SPM/stroke and whether their rods float late, both unknown." |
| "The float constraint costs ~₹7k/d" | "The ~₹6.5k/d beyond our rec is only reachable by running floating rods; pulling on the alarm is ₹0.8k/d better than the best float-safe fixed cutoff." |
| "Brinkman over-predicts the W/O emulsion" | "Pal–Rhodes at the published-band centre IS Brinkman below 60 % water; we cap the relative viscosity at 10× near inversion [assumption]." |
| "The cold well is modelled as an unpumpable 51,000 cP emulsion" (as a flag) | "Still true under any published emulsion law: the model cannot rod-pump the cold well at 2 spm on an 86-in unit (PRL 189 kN vs 114 kN). The field did produce these wells cold, so the drag/emulsion/cold-pump assumptions are wrong somewhere; this inflates every incremental figure by ~₹2.7k/d. One cold-well dyno card settles it." |
| "Peak band fails at 12.4 bbl/d" | "AOF re-tuned 0.46 → 0.56 to the field peak band: reference peak 15.1 bbl/d, uplift unchanged 5.4×, reference SOR 4.5 (band 3.0–4.6)." |
| "Reference SOR 3.9" | "Reference SOR 4.5: it now ends on float onset at produce day 151; it would be 3.2 if the rods were allowed to float to the rate cutoff." |
| "171 passed, 2 xfailed" | "197 passed, 2 xfailed" |

### 11.11 Not done / open

1. **Downstream not regenerated.** `data/`, `ml/models/*` (incl. `gain_decomposition.json`,
   `uq_summary.json`), the dashboard, the deck and the surrogate.
   - `twin/generate_data.py` now samples pressure and stroke; **not run**.
   - ml/train.py FEATURES still has four inputs; the cascade decides whether to add the two
     controls.
2. **Cold-well pumpability.** Unresolved: a strict xfail plus a data ask (one cold-well dyno card).
3. **Fractional-flow flowback.** It decides how much of the slow-rod benefit is real (§11.9 item 4).
4. **VFD policy at the 0.6 line** (§10.7). Not adopted. With the cap, a 0.6-margin schedule might
   delay the onset further; untested this wave.
5. **Tubing temperature profile.** Still missing.
6. **Data asks, in priority order:**
   1. a water-cut-vs-time log for one CSS cycle;
   2. one late-cycle dyno card and one **cold-well** card;
   3. OIL's current SPM / stroke / pull criteria (the gain now rides on these, not on the
      cutoff);
   4. a static BHP survey;
   5. a lab W/O viscosity at 30 / 45 / 60 % water (fixes φ* and the cap).


## 12. Wave 5: operating policy as a control, fair baseline, smooth inversion, injectivity, levies deck (27 Sep)

Scope: the technical re-score (58/100). Its top finding was that the rev-12 +₹9,574/d came from the
**pull rule** ending baseline (b) on produce day 139 at 1.87 m³/d. The twin's own VFD-hold erased
it.

This wave:
1. makes the float response an operating **policy** and an optimiser dimension;
2. applies it alike to the baseline, the recommendation and the cold counterfactual;
3. smooths the inversion cliff;
4. gates injectivity;
5. adds a royalty/cess deck;
6. moves the diesel discount to mid-range.

It reports what the physics says. **No calibration knob moved.**

- Branch `wave5`. `params/CHANGELOG.md` rev 13 has the key-by-key record.
- `pytest -q` → **263 passed, 2 xfailed**:
  - soak: still a strict xfail;
  - the rev-12 cold-well strict xfail is **un-xfailed** (§12.4);
  - new strict xfail: the steam optimum at the mid-range diesel price, §12.2.
- `cycle.legacy_rev12_params` reproduces rev 12 to the digit (three cases, tested).
- Optimiser, decomposition and a 300-draw UQ smoke were run into the session scratchpad
  (`scratchpad/w5/`). **`ml/models/` and `data/` are untouched.**

### 12.1 What was built

**The four policies** (`css.float_policy`, `simulate_css_cycle(..., float_policy=)`):

| Policy | SPM schedule | When the well is pulled |
|---|---|---|
| `pull` (rev 12) | physical keep-up limit (margin 1.0); in practice the start speed | FI > 0.6 on `fi_alarm_days` (3) consecutive days |
| `vfd_hold` | VFD holds FI **at 0.6** (`vfd_hold_fi`) down to 2 spm (`vfd_spm_floor`) | only at the floor, after 3 alarm days there |
| `vfd_then_pull` | holds FI at 0.6 but only down to max(2, 0.5 × start SPM) (`vfd_turndown_frac` [ASSUMPTION]: a self-cooled NEMA-D motor on a VFD) | after 3 alarm days at that floor |
| `none` | margin 1.0 | never on float; rate cutoff only (rods float) |

**Cold counterfactual** (`css.cold_counterfactual`, default `policy`). The unstimulated well obeys
the same policy on the params' own unit at the policy floor.
- If FI there is above 0.6, it is shut in.
- `pumpable` = the field fact: the VFD slows it below the keep-moving floor until FI ≤ 0.6, and it
  produces its IPR rate.
- `legacy` = rev 12.

**Other additions:**
- a smooth inversion band (`fluid.emulsion_inversion_band_wc` 0.075);
- flowback mobility ratio M (`fluid.flowback_mobility_ratio`, 1);
- the injectivity margin (`steam.min_injection_margin_kPa` 400);
- the levies deck (₹3,600/bbl);
- diesel discount 0.15, with presets 0.30 and 0.

**What gains are measured in.** Every **gain** below is a difference of net cash per cycle-day
(`margin_with_opex_inr_per_cycle_day`).
- The counterfactual cancels. That matters because under `policy`, an operator who does nothing
  about float (`none`) also runs his cold well floating, i.e. pumped. The three float policies
  shut it in.
- Comparing *incremental* figures across policies would book that switch (₹8.3k/d) as gain.

### 12.2 The default policy stays `pull`, and why

`vfd_hold` is the operator model §11.3 describes ("he first slows the unit"), and it is the
**recommended** policy. It was tried as the params default.

Under it, two benchmark bands fail:
- **Reference SOR:** 3.4645, which is **0.0005 below the CalGEM floor of 3.465**.
- **500-t slug:** SOR 2.65, below the 3–8 literature band. The rec itself is 2.83.

Re-specifying the bands would be the "calibration by re-specification" the re-score criticised. So:
- the default stays `pull`, the rev-12 operation the calibration anchor was made under, and every
  band passes there;
- the `vfd_hold` misses are pinned as a finding test
  (`test_vfd_hold_takes_small_slugs_below_the_literature_sor_band`).

First cycles are the most efficient, so SOR < 3 is not implausible. But no Baghewala datum
supports it.

**Knock-on of the 0.15 discount.**
- At 0.15 the **gross-margin optimum slug is ~750 t**, below BGW-8's 1,040–1,560 t. At 0.30 it is
  1,000 t.
- New strict xfail `test_steam_optimum_at_the_mid_range_diesel_price_is_within_bgw8`. Read as
  revealed preference, OIL's slug size argues that its steam is cheaper than the mid-range.
- The soak/steam **relative (%)** margin tests are evaluated at the `bulk_0.30` preset they were
  calibrated at (`_bulk()`, disclosed). At 0.15 the reference's gross margin per cycle-day is only
  ~₹2.2k, so a 2 % criterion is noise.

### 12.3 Four cases × the policies (base physics, FY25 unless stated)

**Columns:**
- incr = incremental ₹/cycle-day against the default `policy` counterfactual. The cold well is
  shut in under the three float policies and pumped floating under `none`.
- net = net cash per cycle-day (counterfactual-free).
- pumpable = incremental against the pumpable cold well.

| Case | Policy | SOR gross | SOR incr | oil m³ | produce d (window) | ended by | min spm | incr FY25 | incr $65 | incr levies | net FY25 | incr FY25 vs pumpable cold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference 1500/7/1.2/5/86/91 | pull | 4.50 | 4.50 | 333 | 152 (179) | float | 5.0 | −3,727 | −17,203 | −31,708 | −3,727 | −15,110 |
| | vfd_hold | 3.46 | 3.46 | 433 | 211 (238) | float at floor | 2.0 | +11,159 | −2,008 | −16,180 | +11,159 | −224 |
| | vfd_then_pull | 3.71 | 3.71 | 404 | 192 (219) | float at 2.5 | 2.5 | +7,725 | −5,626 | −19,996 | +7,725 | −3,658 |
| | *none* | 3.18 | 4.26 | 471 | 240 (267) | rate cutoff (91 d FI > 0.6) | 2.32 | +5,663 | −3,883 | −14,157 | +13,968 | +2,585 |
| Baseline (b) 1300/10/1.3/5/86/91 | pull | 4.35 | 4.35 | 299 | 140 (168) | float | 5.0 | −2,894 | −15,812 | −29,717 | −2,894 | −14,277 |
| | vfd_hold | 3.29 | 3.29 | 395 | 199 (227) | float at floor | 2.0 | +12,064 | −582 | −14,193 | +12,064 | +681 |
| | vfd_then_pull | 3.52 | 3.52 | 369 | 181 (209) | float at 2.5 | 2.5 | +8,913 | −3,908 | −17,708 | +8,913 | −2,470 |
| | *none* | 3.18 | 4.28 | 409 | 209 (237) | rate cutoff (72 d FI > 0.6, 42 d FI = 1) | 2.84 | +4,469 | −4,827 | −14,833 | +12,774 | +1,391 |
| rev-12 rec 1000/10/0.60/3/64/85 | pull | 3.19 | 3.19 | 313 | 180 (204) | float | 3.0 | +10,141 | −1,016 | −13,026 | +10,141 | −1,242 |
| | vfd_hold | 2.84 | 2.84 | 352 | 211 (235) | float at floor | 2.0 | +14,204 | +3,322 | −8,391 | +14,204 | +2,821 |
| | vfd_then_pull | = vfd_hold (0.5 × 3 < 2) | | | | | | | | | | |
| | *none* | 2.42 | 3.62 | 413 | 284 (308) | rate cutoff (107 d) | 2.0 | +8,275 | +1,768 | −5,236 | +16,580 | +5,197 |
| **rev-13 rec 1000/10/0.60/4.5/64/89** | pull | 3.60 | 3.60 | 278 | 141 (165) | float | 4.5 | +5,443 | −6,783 | −19,943 | +5,443 | −5,941 |
| | **vfd_hold** | **2.83** | **2.83** | **353** | **196 (220)** | float at floor | 2.0 | **+15,396** | **+3,738** | **−8,811** | **+15,396** | **+4,013** |
| | vfd_then_pull | 2.91 | 2.91 | 344 | 188 (212) | float at 2.25 | 2.25 | +14,577 | +2,792 | −9,893 | +14,577 | +3,194 |
| | *none* | 2.45 | 3.56 | 408 | 262 (286) | rate cutoff (124 d, 86 d FI = 1) | 2.0 | +8,884 | +1,758 | −5,912 | +17,189 | +5,806 |

**Reading the table.**
1. **The policy moves more money than any set-point.**
   - Baseline (b): −₹2.9k (pull) → +₹12.1k (VFD-hold), i.e. +₹15k/d from slowing the unit
     instead of pulling.
   - Under VFD-hold every case ends at the 2-spm floor, 196–211 produce days, at 2.3–4.5× the cold
     rate.
2. **The pull rule pulls early at every setting.** Reference, baseline and the rec all end at 3–5×
   the cold rate. §11's "the late oil is unreachable without floating rods" is true only for an
   operator who never slows down.
3. **SOR:**
   - baseline (b) 4.35 (pull) → 3.29 (VFD-hold);
   - rev-13 rec 2.83;
   - rods floating to the cutoff (`none`): 3.18 / 2.45. The model gives floating rods no failure
     cost.
4. **VFD-hold holds FI at exactly 0.6 for 58–62 days.** The graded damage index Σ FI³ is ~16 vs 3
   under pull. That is the price of the extra oil, and it is unpriced in ₹ (a rod-string failure
   cost is not modelled).

**Float exposure (days FI > 0.6 / days FI ≥ 1):**
- VFD-hold: 3 / 0 at every case (the pull confirmation at the floor).
- `none`: 72 / 42 (baseline) and 124 / 86 (rec settings).

### 12.4 The cold well under each policy (45 % formation water, params unit 86 in)

| Policy | `policy` counterfactual | `pumpable` counterfactual | rev-12 `legacy` |
|---|---|---|---|
| pull / vfd_hold / vfd_then_pull | **shut in** (FI 1.0, PRL 189 kN at the 2-spm floor): cash 0 (opex not paid) | 0.53 spm, FI 0.60, PRL 90 kN, 0.445 m³/d, 49 kWh/d: cash **+₹11,383/d** | 2 spm, FI 1.0, PRL 189, 0.445 m³/d, 433 kWh/d: +₹8,305/d |
| none | = legacy (pumped floating) | as above | as above |

- **The double standard is gone.** The cold well is never "unpumpable yet producing" under a float
  policy.
- The strict xfail `test_cold_well_pumpable_at_2_spm_on_the_assumed_unit` is replaced by a
  passing test. It asserts the physical finding (FI 1.0, 189 kN at 2 spm) and the consistent
  counterfactual.
- **The model's cold well is shut in at base, so every absolute incremental ₹ is an UPPER bound.**
  The field did produce these wells cold. The `pumpable` column is ~₹11.4k/d lower, and it is the
  field-consistent one.
- The paired gain between two set-points does not depend on this choice (tested).

### 12.5 Re-optimisation (5-D + policy, soak 10, both decks, minimax regret)

**Search.** `best_settings_physics_5d(params, policies=ALL_POLICIES)`: 4 policies × 53,592
points, 12,936 simulations, 172 s.

**Feasibility:**
- float feasibility under the policy (alarm days ≤ 3 when it can pull; max FI ≤ 0.6 for `none`);
- PRL ≤ 113.9 kN;
- **injection margin ≥ 400 kPa**. This rejects every 85-kgf/cm² point: 40,194 of 53,592 remain
  per policy.

**Canonical (over pull / vfd_hold / vfd_then_pull): 1,000 t / 10 d / 89 kgf/cm² / 64 in /
4.5 spm start / cutoff 0.60 (backstop) / VFD-hold.**
- FY25 **+₹15,396/d**, $65 **+₹3,738/d**, net of levies **−₹8,811/d** (shut-in counterfactual).
- Max regret ₹48/d. The FY25 optimum is the same point at 5 spm (+₹15,414); the $65 optimum is 4
  spm (+₹3,786).
- SOR 2.83. Ends on the float pull at the 2-spm floor on produce day 196.
- Pinned at the grid floors: steam 1,000, stroke 64, cutoff 0.60. **Not pinned: SPM (4.5, interior)
  and pressure (89).**

**Operator rounding:** "1,000 t at 89 kgf/cm², soak 10 d, 64-in stroke, start at 4–5 spm; let the
VFD slow the unit to keep the float index at 0.6; pull only after 3 alarm days at 2 spm (0.6 m³/d
rate backstop)."

**Best point within each policy:**

| Policy | Minimax point (steam / p / cutoff / stroke / spm) | FY25 | $65 | levies | SOR |
|---|---|---|---|---|---|
| pull | 1000 / 89 / 0.60 / 64 / 3 | +10,023 | −1,118 | −13,111 | 3.20 |
| **vfd_hold** | **1000 / 89 / 0.60 / 64 / 4.5** | **+15,396** | **+3,738** | **−8,811** | **2.83** |
| vfd_then_pull | 1000 / 89 / 0.60 / 64 / 4 | +15,308 | +3,786 | −8,617 | 2.83 |
| none (FI ≤ 0.6 every day) | 1000 / 89 / **1.45** / 64 / 3 | +604 (net +8,909) | −7,340 | −15,890 | 3.29 |
| conservative (hold & pull at 0.5), vfd_hold | same settings | +14,238 | +2,394 | −10,355 | 2.95 |

- VFD-hold and VFD-then-pull are within ₹0.1k/d. **The policy that matters is "slow before you
  pull"; the turndown limit hardly does.**
- Under VFD-hold the start SPM is a weak lever (4, 4.5 and 5 spm are the per-deck optima, within
  ~₹0.2k); **stroke is what matters** (§12.6).

### 12.6 THE GAIN vs baseline (b), under the SAME policy (net cash ₹/cycle-day)

| Baseline (b) is operated… | Best rec within that policy | FY25 | $65 | net of levies |
|---|---|---|---|---|
| **pulls on the alarm** (rev-12 operation) | 1000/89/0.60/64/3, pull | +12,917 | +14,694 | +16,606 |
| **VFD-holds** (slows first) | **1000/89/0.60/64/4.5, VFD-hold (canonical)** | **+3,332** | **+4,319** | **+5,382** |
| **does nothing (rods float to its 1.3 cutoff)** | 1000/89/1.45/64/3, float-safe | **−3,865** | −2,513 | −1,057 |
| *(mixed: canonical VFD-hold rec vs a baseline that does nothing)* | canonical | +2,622 | +3,484 | +4,413 |
| *(mixed: canonical vs a baseline that pulls)* | canonical | +18,289 | +19,550 | +20,906 |

**Honest gain statement.**
- **Against a baseline operated the same way (VFD-hold), the recommendation gains ₹3.3k/d at
  FY25** (₹4.3k at $65, ₹5.4k net of levies).
  - At the old 0.30 bulk discount it is **₹1.8k/d**.
  - It is positive in every one-at-a-time sensitivity (§12.7) and in 95 % of UQ draws (§12.10).
  - It is a modest, operational gain: ~5 % of the recommendation's gross revenue per day.
- The ₹12.9k "vs a pulling baseline" is the rev-12 structure again. It is the pull rule, not the
  set-point: the policy lever alone is 68 % of the canonical-vs-pulling-baseline gain.
- **Against a baseline that does nothing about float, a float-safe recommendation LOSES ₹3.9k/d.**
  The model charges nothing for running floating rods: no rod-failure or workover cost is
  modelled. What float avoidance buys (72 → 3 alarm days, 42 → 0 days at FI = 1) is not in the ₹.

**Decomposition, canonical vs baseline (b) under VFD-hold.** Shapley over 120 orders; the terms
sum exactly.

| Deck | Total | stroke 86→64 in | cutoff 1.3→0.6 | steam 1300→1000 t | spm 5→4.5 | pressure 91→89 |
|---|---|---|---|---|---|---|
| FY25 | +3,332 | **+1,907 (57 %)** | +986 (30 %) | +354 (11 %) | +36 (1 %) | +49 (1 %) |
| $65 | +4,319 | +2,178 (50 %) | +1,112 (26 %) | +891 (21 %) | +73 (2 %) | +64 (1 %) |
| levies | +5,382 | +2,470 (46 %) | +1,248 (23 %) | +1,470 (27 %) | +114 (2 %) | +80 (1 %) |

**What each lever does:**
- **Stroke.** A shorter stroke means a lower rod velocity at the 2-spm floor, so the VFD can hold
  FI ≤ 0.6 longer.
- **Cutoff.** Its OAT is 0 and its Shapley value is interaction: with the 64-in stroke the baseline's
  1.3 m³/d cutoff would bind before the float pull.
- **SPM** is no longer a lever once the VFD does the slowing.

**Other decompositions.**
- Canonical vs a *pulling* baseline (6 levers): policy +12,352 (68 %), stroke +3,617, spm +960.
- Canonical vs a baseline doing *nothing* (6 levers, +2,622): cutoff +2,711, stroke +1,260, policy
  **−1,441** (holding the float line costs oil when floating is free).
- rev-12 rec vs baseline, both pulling (+13,035): spm 58 %, stroke 30 %, steam 11 %. That is the
  rev-12 decomposition under rev-13 economics.

### 12.7 Sensitivity after smoothing (net-cash gain, ₹/cycle-day, FY25; OAT around base)

| Input | Same-policy gain, VFD-hold | same policy, pull | same policy, none | rec (VFD) vs base none | rec incr (policy cf) | rec incr (pumpable cf) | SOR rec / base (VFD) |
|---|---|---|---|---|---|---|---|
| base | **+3,332** | +12,917 | −3,865 | +2,622 | +15,396 | +4,013 | 2.83 / 3.29 |
| cap 5× / 20× / none | +3,279 / +3,331 / +3,331 | +6,102 / +19,049 / +19,049 | −4,007 / −3,770 / −3,770 | +3,601 / +2,699 | +16,653 / +15,353 | +5,270 / +3,970 | 2.70–2.83 |
| K_VISC 5 / 15 | +4,318 / +5,959 | +6,752 / +13,090 | −4,074 / −4,153 | +4,487 / −1,153 | +17,620 / +11,762 | +6,600 / +259 | 2.51 / 3.14 |
| band 0 (sharp) / 0.05 / 0.10 | +3,398 / +3,359 / +3,299 | +13,035 / +12,964 / +12,861 | ≈ −3.8k | ≈ +2.6k | ≈ 15.4k | ≈ 4.0k | 2.83 |
| flowback M 3 / 10 | +5,377 / +6,603 | +7,696 / +8,385 | −6,024 / −6,342 | +5,664 / +6,861 | +8,947 / +4,005 | −2,436 / −7,378 | 3.11 / 3.43 |
| diesel discount 0 / 0.30 | +4,818 / **+1,846** | +16,489 / +9,345 | −3,320 / −4,410 | +3,803 / +1,440 | +9,681 / +21,110 | −1,702 / +9,727 | 2.83 |
| s_cold 2 / 8 | +6,459 / **+1,161** | +11,027 / +10,168 | −14,212 / −5,397 | +6,854 / +762 | +4,715 / +23,908 | −6,669 / +12,525 | 3.43 / 2.51 |
| f_w 0.3 / 0.6 | +3,013 / +3,083 | +10,099 / −613 | −2,199 / −6,409 | +3,436 / −781 | +21,580 / +4,614 | +10,490 / +4,614 | 2.29 / 3.61 |
| fi_alarm_days 1 / 7 / 14 | +3,445 / +3,111 / +2,857 | +13,341 / +12,104 / +10,789 | −3,865 | +2,433 / +2,969 / +3,487 | 15.2–16.3k | 3.8–4.9k | 2.74–2.85 |
| condensate recovery 0.5 / 0.9 | +2,162 / +3,432 | +9,462 / +3,309 | −2,112 / −6,081 | +2,649 / −414 | +21,693 / +6,500 | +10,310 / −4,883 | 2.37 / 3.48 |
| VFD floor 1.5 / 2.5 spm | +3,390 / +4,806 | +12,917 | −3,865 | +4,032 / +945 | +16,806 / +13,719 | +5,423 / +2,336 | 2.68 / 2.98 |

**Findings on the cap and K_VISC after smoothing.**
- **The VFD-hold gain no longer depends on the 10× cap**: ₹3.28–3.33k over cap 5 → ∞. Under the
  VFD policies FI is held at 0.6, so the cap only moves *when* the floor is reached, equally for
  both points.
- The **pull-policy gain still swings ₹6.1k → ₹19.0k with the cap**. That is re-score N4, and it
  is one more reason not to quote the pull-based number.
- K_VISC 5 → 15 moves the VFD-hold gain ₹4.3k → ₹6.0k (same sign; base ₹3.3k sits below both). The
  absolute rec margin moves ₹17.6k → ₹11.8k.
- **The gain's smallest values are at s_cold 8 (+₹1.2k) and the 0.30 discount (+₹1.8k).** Its sign
  never flips in this table. The biggest mover is the flowback law (M 10: +₹6.6k).
- The **absolute** rec margin flips sign against the pumpable counterfactual at M 3/10, s_cold 2,
  condensate 0.9 and retail diesel.

### 12.8 The inversion band

| Band width | Max drag-μ ratio day-to-day at the reference crossing | Max FI step / day | Reference SOR / produce d (pull) |
|---|---|---|---|
| 0 (rev 12) | **3,365×** | 0.228 | 4.499 / 152 |
| 0.05 | 1.34× | 0.079 | 4.499 / 152 |
| **0.075 (base)** | **1.22×** | **0.068** | 4.499 / 152 |
| 0.10 | 1.17× | 0.060 | 4.499 / 152 |

**The cliff was cosmetic for the economics.**
- The float onset that ends every cycle happens at water cut 0.55–0.63, *below* the band. The band
  changes the ₹ by < ₹0.1k/d and no cycle end moves.
- The one exception: with the formation cut at 0.60 the late stream sits near the band and floats
  later. The heat test in `test_cycle.py` now runs to the rate cutoff because of this.

UQ OAT swing of the band width on the rec: **₹30/d**.

### 12.9 Injectivity (P_current 9.4 MPa)

| Wellhead kgf/cm² | 85 | 87 | 89 | 91 | 93 | 97 |
|---|---|---|---|---|---|---|
| Sandface − P_current (kPa) | **53** | 276 | **498** | 721 | 944 | 1,391 |
| rec incr FY25 (₹/d) | 15,508 | 15,495 | 15,396 | 15,386 | 15,284 | 15,069 |

**The 85 kgf/cm² floor does NOT survive.**
- A margin of ≥ 300–400 kPa selects **89** (cost ₹112/d FY25, ₹131 $65). ≥ 500 kPa selects 93
  (cost ₹224/d). A zero margin gives 85 back (tested).
- 85 passes 400 kPa only if P_current ≤ 9,053 kPa. That holds in 84 % of UQ draws, so the rev-12
  rec is injectable in 84 %; the rev-13 rec in 100 %.
- The pressure lever is economically near-inert. Its role is feasibility, and the static BHP survey
  decides it.

### 12.10 Three decks and the diesel discount (rec vs baseline (b), both VFD-hold)

| Discount | Counterfactual | FY25 rec / base / gain | $65 rec / base / gain | net of levies rec / base / gain |
|---|---|---|---|---|
| **0.15 (base)** | policy (shut in) | +15,396 / +12,064 / **+3,332** | +3,738 / −582 / +4,319 | −8,811 / −14,193 / +5,382 |
| 0.15 | pumpable | +4,013 / +681 / +3,332 | −4,421 / −8,740 / +4,319 | −13,498 / −18,881 / +5,382 |
| 0.30 (bulk preset) | policy | +21,110 / +19,264 / +1,846 | +9,452 / +6,619 / +2,833 | −3,097 / −6,993 / +3,896 |
| 0.30 | pumpable | +9,727 / +7,881 / +1,846 | +1,293 / −1,540 / +2,833 | −7,784 / −11,680 / +3,896 |
| 0 (retail) | policy | +9,681 / +4,863 / +4,818 | −1,977 / −7,782 / +5,805 | −14,525 / −21,394 / +6,868 |
| 0 (retail) | pumpable | −1,702 / −6,520 / +4,818 | −10,135 / −15,941 / +5,805 | −19,213 / −26,081 / +6,868 |

**Net of royalty + cess (₹3,600/bbl, OIL's company basis), every feasible grid point is
negative.**
- The best is 1000/89/0.60/64/3.5 VFD-hold at −₹8.6k/d, even against a shut-in cold well.
- The recommendation's edge over the baseline **grows** on the levies deck (+₹5.4k), because it
  saves steam.
- The ER-policy 50 % cess waiver (~₹4,200/bbl if CSS output qualifies) is not netted.

**Deck basis:** ₹5,992 × (1 − 0.20 − 0.20) ≈ ₹3,600. The OIL AR 2024-25 exchequer table (royalty
₹2,986.84 cr + cess ₹2,567.04 cr on ₹15,710 cr of crude sales) caps the levy share at 35 %, i.e.
₹3,890/bbl.

### 12.11 UQ smoke (300 draws, seed 42, 21 inputs, both decks; scratchpad, not the bake)

Inputs appended:
- cap U[5, 20];
- fi_alarm_days U[1, 14];
- band U[0.05, 0.10];
- M {1, 3, 10};
- counterfactual {policy, pumpable} (50/50).

The diesel base is 0.15. Gains are net cash per cycle-day.

| Comparison | P(rec > base) FY25 ($65) | gain p10 / p50 / p90 FY25 | same, draws where the baseline is not fragile (n = 254) |
|---|---|---|---|
| **same policy, VFD-hold (canonical vs baseline (b))** | **0.957 (0.983)** | +2.2k / +11.8k / +217k | **+1.9k / +9.4k / +56k; P > 0 0.949** |
| same policy, pull | 0.940 (0.983) | +2.5k / +13.9k / +213k | +2.1k / +11.4k / +53k |
| same policy, none (float-safe rec vs floating base) | **0.207** (0.217) | −42k / −8.5k / +93k | −48k / −9.6k / −2.4k; P > 0 0.063 |

**Where the gain comes from in the draws.**
- **The base point (+₹3.3k) is the low side of the distribution.** Base physics has M = 1, where
  the baseline does comparatively well. Median gain by M: +₹6.3k (M 1), +₹12.7k (M 3), +₹14.6k
  (M 10).
- The p90 tail (> ₹200k) is the baseline's fragility: in 15 % of draws its 1.3 cutoff sits above its
  own peak and it ends within 5 days, the §10.9 failure mode on the *baseline*. Quote the median
  and p10, not the mean.

**The rec itself.**
- P(incr > 0): **0.387 FY25 / 0.160 $65**.
  - Policy (shut-in) counterfactual draws: 0.53.
  - Pumpable-counterfactual draws: 0.21.
- incr p10/p50/p90: −19.1k / −3.3k / +13.0k FY25.
- SOR p10/p50/p90: 2.55 / 3.78 / 5.33, against baseline (b) VFD-hold 3.18 / 5.26 / 78.6.
  **P(rec SOR < base SOR) = 1.000.**
- **Fragility of the rec: 0.000.** P(alarm days > the draw's rule) = 0. P(injection ok) = 1.0 (rev-12
  rec: 0.843).

**OAT tornado on the rec** (FY25, incr):

| Rank | Input | Swing ₹/d |
|---|---|---|
| 1 | μ_ref | 29.5k |
| 2 | s_cold | 26.9k |
| 3 | oil price | 18.2k |
| 4 | formation cut | 17.0k |
| 5 | condensate recovery | 15.2k |
| 6 | diesel discount | 11.4k |
| 7 | **flowback M** | 11.4k |
| 8 | **counterfactual** | 11.4k |
| 9 | P_current | 10.7k |
| … | K_VISC | 5.9k |
| … | **cap** | **1.3k** |
| … | fi_alarm_days | 1.1k |
| … | band | 0.03k |

**MC correlation:** s_cold +0.39, μ_ref −0.36, M −0.36, counterfactual −0.36.

The structural choices the re-score listed as unsampled now rank: M and the counterfactual are
#7–8. The cap and alarm days barely matter once the unit slows instead of pulling.

### 12.12 ML label (for the cascade; `ml/train.py` and `ml/README.md` untouched)

`twin/generate_data.py` (not run) now:
- samples `float_policy` as a 7th LHS column (equal strata over pull / vfd_hold / vfd_then_pull);
- runs every row under its policy;
- appends four label columns.

Positive-class shares on a 450-row sample of this design:

| Column | Definition | Share (pull / vfd_hold / vfd_then_pull) | Verdict |
|---|---|---|---|
| `fi_gt_alarm_any` | max FI > 0.6 on any day | 82 % (97 / 73 / 75) | not informative |
| `float_forced_pull` | the float pull, not the cutoff, ended the cycle | 80 % (96 / 71 / 73) | = the rev-12 label's structure |
| alarm while the VFD still had room | FI > 0.6 with SPM above the floor | 32 % (97 / 0 / 0) | degenerate: a function of the policy |
| **`float_premature_pull`** | float_forced_pull AND the oil rate ≥ 1.5 × the cutoff at the pull | **41 % (55 / 32 / 37)** | **recommended label** |

**Cascade instructions:**
1. Add `p_wellhead_kgf_cm2`, `stroke_in` and `float_policy` (one-hot) to FEATURES.
2. Train the classifier on `float_premature_pull` ("the rods, not the economics, ended a
   still-productive cycle"; the 1.5× threshold is a label choice, `FLOAT_PREMATURE_RATIO`).
3. Drop the optimiser's P(float) ≥ 0.3 penalty. Under every policy the pull *is* the float response,
   so penalising it fights the physics (re-score N7).
4. Update `ml/README.md` accordingly.

### 12.13 Judgement calls (team must know)

1. **Default `float_policy` = `pull`**, although the recommendation is `vfd_hold`. See §12.2: the
   benchmark anchor was calibrated under pull, and VFD-hold misses two bands by a hair and by a
   finding.
2. **The default counterfactual is `policy` → shut in at base.** Every absolute incremental ₹ is an
   upper bound. The `pumpable` numbers (~₹11.4k/d lower) are field-consistent. **Quote both, or
   quote the paired gain.**
3. **`vfd_then_pull` turndown 0.5** [ASSUMPTION]. It barely matters (≤ ₹0.1k/d at the rec).
4. **The VFD holds FI exactly on the 0.6 alarm line for ~60 days.** It is not an alarm by the SPEC's
   strict ">" and the rods keep up, but the graded exposure Σ FI³ is 5× that of the pull policy.
   With a rod-failure cost this would trade against the extra oil. None is modelled.
5. **Injection margin 400 kPa** [ASSUMPTION 300–500]. At 500 the rec moves to 93 kgf/cm² (−₹112/d).
6. **The diesel discount moved to 0.15.** It costs every steam-heavy cycle ₹5–10k/d, and it pushes
   the gross slug optimum below BGW-8 practice (strict xfail). Read as revealed preference, the
   field's slug sizes favour 0.30.
7. **Gains are net-cash differences.** They equal incremental differences whenever both sides share
   one counterfactual.

### 12.14 What we now say / stop saying

| Stop saying | Say instead |
|---|---|
| "+₹9,574/day vs baseline; 62 % SPM, 32 % stroke" | "Against a baseline run the same way (slowing its unit on the float alarm before pulling), our recommendation gains ~₹3.3k/day at FY25 prices (₹1.8k at bulk diesel; positive in 95 % of UQ draws, median ~₹9k). Most of it is the 64-in stroke, which lets the VFD hold the float line longer." |
| "Pull the well when the float alarm persists 3 days" (as the rec) | "Operate with the VFD: start at 4–5 spm on a 64-in stroke, let the drive slow the unit to hold the float index at 0.6, and pull only after 3 alarm days at 2 spm. This is the model's best policy." |
| "1,000 t at 85 kgf/cm²" | "1,000 t at 89 kgf/cm². 85 leaves only 53 kPa of injection margin over our assumed 9.4 MPa reservoir pressure; the pressure choice is worth ~₹0.1k/day." |
| "SOR 4.35 → 3.19" | "SOR 3.3 → 2.8 at the same operating policy (4.35 → 2.8 against a baseline that pulls on the alarm). Below 3 is outside the literature band; first cycles are the most efficient, but we have no Baghewala datum." |
| "Float avoidance is worth ₹X" | "Float avoidance is not priced: the model gives a rod failure no cost. Against a baseline that lets rods float (72 days above the line, 42 at FI = 1), a float-safe recommendation earns LESS (−₹3.9k/day). The case for avoiding float is rod life, which one rod-failure cost from OIL would price." |
| "The model's cold well is unpumpable yet producing" / "the idealised pumpable cold well" | "The cold counterfactual obeys the same float policy: at 45 % water it is shut in (upper-bound ₹); if pumped slowly at 0.5 spm (as the field did) every absolute ₹ drops ~₹11k/day. The paired gain does not change." |
| "Stimulated well is positive on OIL's basis" | "Net of royalty and cess (~₹3,600/bbl) every feasible set-point is negative in our model (best −₹8.6k/day), even against a shut-in cold well; the recommendation loses ₹5.4k/day less than the baseline." |
| "The inversion cliff" | "Inversion is a 0.075-wide band (1.2× per day, not 3,400×); it changed nothing that matters: the float onset happens below it." |
| "263 tests" etc. | "263 passed, 2 xfailed" |

### 12.15 Not done / open

1. **Downstream not regenerated:** `data/`, `ml/models/*` (uq_summary, gain_decomposition,
   surrogates), the dashboard, the deck, `ml/README.md`.
   - `generate_data.py` has the policy column and the labels; not run.
   - The full UQ bake (1,500 draws) was not run; the smoke is in the scratchpad.
2. **Rod-failure cost.** The ₹ has no failure term, so "float avoidance" cannot show up as money.
   One OIL rod-failure / workover cost and frequency would close it.
3. **Cold well.** Its pumpability is still a model defect at 2 spm. It is now handled consistently,
   not resolved. A cold-well dyno card is the ask.
4. **Tubing temperature profile.** Still missing.
5. **Data asks** (the re-ordered list; the gain now rides on stroke and policy):
   1. OIL's actual SPM / stroke / VFD practice and pull criteria;
   2. a water-cut log for one cycle (decides M, the #1 structural driver of the gain);
   3. a late-cycle and a cold-well dyno card;
   4. a static BHP survey (decides 85 vs 89 kgf/cm²);
   5. one rod-failure cost;
   6. whether CSS output gets the ER cess waiver.
