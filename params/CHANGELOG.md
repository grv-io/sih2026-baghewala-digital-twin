# params/field_params.json — Changelog

Merge of research-agent-confirmed real field values (from
`docs/research/field_params_recommended.json` and `docs/research/baghewala_facts.md`)
into the schema previously populated with docs/SPEC.md placeholder defaults.
Schema (key names/nesting) is unchanged — only values changed. Full
citation detail lives in `docs/research/field_params_recommended.json`'s
`_sources` block and `docs/research/baghewala_facts.md`; this file summarizes
what changed and why, one line per field.

## reservoir

- `T_initial_C`: 47.0 -> **50.0**. CONFIRMED bottom-hole temperature for
  Jodhpur Sandstone, Baghewala (OIL internal PPT, 12.07.2025).
- `P_initial_kPa`: 6000 -> **11400**. CONFIRMED reservoir pressure ~116
  kgf/cm² (OIL internal PPT). Cross-check: 116 kgf/cm² / 1150 m ≈ 0.101
  kgf/cm²/m, consistent with a near-hydrostatic gradient.
- `depth_m`: 500 -> **1150**. CONFIRMED average depth of the Jodhpur
  Sandstone producing zone, ~1100-1150 m (oil-india.com; SPE-23APOG-535203;
  OIL internal PPT). The 500 m placeholder had no supporting source.
- `thickness_m`: unchanged (12.0). NOT FOUND for Baghewala; kept as
  unconfirmed placeholder.
- `porosity`: 0.28 -> **0.09**. CONFIRMED upper bound <10% for Jodhpur
  sandstone (Basha et al., GEOHORIZONS Jan 2015); set to representative
  point estimate 0.09.
- `k_thermal_W_mK`: unchanged (2.5). TYPICAL sandstone value, no
  field-specific number found.
- `rock_heat_capacity_Jm3K`: unchanged (2.3e6). TYPICAL sandstone value, no
  field-specific number found.

## fluid

- `api_gravity`: 18.0 -> **15.5**. CONFIRMED current producing crude is
  14-17 API (SPE-23APOG-535203; OIL internal PPT); midpoint used. (Original
  1991 discovery-test API at well A1 was ~19.5-20, i.e. much lighter than
  current production — not used.)
- `mu_ref_cP`: 2000.0 -> **11500.0**. CONFIRMED viscosity 10,000-13,000 cP
  at 50°C (OIL internal PPT), 8,000-15,000 cP at 50°C (SPE-23APOG-535203);
  midpoint of the tighter PPT range used. This is the single most important
  correction — placeholder was off by ~5.7x.
- `T_ref_C`: 47.0 -> **50.0**. Matches the 50°C anchor temperature at which
  the confirmed mu_ref_cP was measured/reported; kept aligned with
  `reservoir.T_initial_C`.
- `andrade_A` / `andrade_B_K`: kept **null** (research agent's recommended
  file computed explicit FITTED values 1.164e-6 / 7436.6, solving
  mu = A*exp(B/T_K) through (mu_ref_cP=11500 @ T_ref_C=50, CONFIRMED) and
  the SPEC's own ASSUMPTION high-T fallback anchor of 50 cP @ 150°C -- no
  Baghewala high-T viscosity measurement was found). Integration kept
  these null instead of copying in the rounded values: viscosity.py
  already fits A/B at runtime from the exact same two anchor points
  (mu_ref_cP, T_ref_C, and its own hardcoded 150C/50cP fallback anchor)
  whenever andrade_A/B are null, so setting them explicitly only
  introduced float-rounding drift (mu(T_ref_C) came out to 11489.6 instead
  of exactly 11500, failing test_reference_point_recovered) with no
  modeling benefit. Mathematically equivalent either way; null gives full
  precision. If a real high-T lab data point is ever found, replace the
  150C/50cP anchor in viscosity.py (not the null here) and refit.
- `bubble_point_kPa`: unchanged (3000). TYPICAL, not found.

## steam

- `quality`: 0.75 -> **0.65**. CONFIRMED first CSS cycle (well BGW-08) used
  60-70% steam quality (OIL internal PPT); midpoint used.
- `T_injection_C`: 250.0 -> **290.0**. CONFIRMED BGW-08 steam temperature
  280-305°C (steam pressure 85-97 kgf/cm², consistent with saturated steam
  at that T/P); near-midpoint used.
- `latent_heat_Jkg`: 1.7e6 -> **1.3e6**. CALCULATED from standard steam
  tables for saturated steam at ~8.5-9.7 MPa (matching the CONFIRMED
  injection pressure above), vs ~1.7e6 J/kg at the placeholder's implied
  ~250°C/4 MPa condition.
- `injection_rate_tpd`: 100 -> **74.0**. CONFIRMED BGW-08 first-cycle steam
  injection rate ~3100 kg/hr = ~74.4 t/d (OIL internal PPT); rounded 74.0.

## srp

- `stroke_m`, `plunger_d_m`, `rod_mass_kgm`: unchanged. TYPICAL, no
  Baghewala-specific SRP mechanical spec found.
- `spm_range`: unchanged ([4, 12]). TYPICAL, consistent with standard
  heavy-oil SRP practice (low-moderate SPM to limit rod/tubing wear).
- `rod_length_m`: 500 -> **1150**. CONFIRMED by association: rod string
  length in an SRP installation is set by pump setting depth, which tracks
  the CONFIRMED reservoir depth above (SRP is the confirmed artificial-lift
  method at Baghewala per oil-india.com).

## css

- `steam_volume_t_range`, `soak_days_range`, `cutoff_rate_m3d_range`:
  unchanged. TYPICAL (kept as SPEC defaults); BGW-08's actual first-cycle
  numbers (~1040-1560 t injected, ~7-13 day soak) fall comfortably inside
  these ranges, so no change was needed.

---

# twin/ physics retuning (Task 2)

The ASSUMPTION constants below were tuned by the physics agent against the
OLD placeholder params (mu_ref_cP=2000 @ 47°C, depth=500 m). With the real
field params merged above (mu_ref_cP=11500, ~5.75x higher; depth/rod_length
1150 m, 2.3x higher; hotter/lower-quality steam), several of them produced
non-physical or degenerate behavior. Each retune below is the *minimal*
change found to restore all required sanity properties (see acceptance
criteria in the integration task) without changing any module contract.

See inline `# ASSUMPTION` / `# RETUNED` comments in the source files for
the exact same notes, kept in sync with this log.

- `twin/ipr.py` `AOF_REF_M3D`: **1.0 -> 0.7** m3/d. With mu_ref_cP now
  11500 (vs 2000 placeholder) and mobility scaling as mu_ref/mu, the
  mobility ratio at heated conditions (viscosity.py's Andrade fit
  extrapolates to well under 1 cP near T_injection_C=290) became extreme
  enough that the reservoir-limited rate pinned at the sucker-rod pump's
  mechanical capacity for most of a produce phase regardless of steam_t.
  That flattened oil_total_m3 across steam_t and killed the SOR-vs-steam_t
  interior optimum (test_SOR_has_interior_optimum_over_steam_volume).
  Lowering AOF_REF_M3D to 0.7 keeps the cold/reference rate comfortably
  below the whole `css.cutoff_rate_m3d_range` (the physical CSS premise
  the module docstring describes) while de-rating the heated rate enough
  that cycles stay reservoir/thermally limited across most of the design
  range instead of pump-capacity limited.
- `twin/thermal.py` `DRAINAGE_RADIUS_M`: **10.0 -> 8.0** m. At radius=10 m
  the heated zone did not saturate the drainage disc until ~2000-2500 t of
  steam (vs the old placeholder's faster saturation), pushing the SOR
  interior optimum past the test's mid sample point (1500 t) -- SOR kept
  improving out to 3000 t instead of curving back up. Shrinking the disc
  to 8 m makes the heated fraction saturate around ~1750 t, restoring an
  interior optimum inside [500, 3000] t and landing the SOR at the range
  edges (500 t: ~6.0, 3000 t: ~2.0) inside the field-literature-typical
  ~3-8 t/m3 SOR band (baghewala_facts.md section 6), with the ~1500-1750 t
  sweet spot near the "thermally efficient" (<3) mark cited there.
- `twin/thermal.py` `COOLDOWN_TAU_DAYS` (20.0): **unchanged**. Verified
  test_thermal.py's decay-shape checks still hold at the real T_initial_C/
  T_injection_C/depth_m; no retune needed.
- `twin/srp.py` `K_VISC` (10.0): **unchanged**. Checked pump_state() across
  a mu grid (1 to 11500 cP) x spm grid (4-12) at the new rod_length_m=1150
  (2.3x the placeholder's 500 m): floating_index still spans from ~0.0001
  (hot, low spm) up to 1.0 (cold, mu near mu_ref, any spm), with a smooth
  transition zone around mu~300-3000 cP where spm materially changes the
  index (e.g. mu=1000: 0.12 at spm=4 vs 0.37 at spm=12) -- no saturation
  collapse, so no retune was needed here.

Verification after retuning: `pytest tests -q` -> 24 passed (see
docs/reviews/integration_report.md for the full run and the post-retune SOR/
floating_index sweep tables).

## Test literal updated (not a physics retune)

- `tests/test_viscosity.py::test_cold_viscosity_is_thousands_of_cP`
  hardcoded an absolute band (1500 < mu(47C) < 2500 cP) tuned to the OLD
  placeholder mu_ref_cP=2000 @ T_ref_C=47. With the real mu_ref_cP=11500 @
  T_ref_C=50, mu(47C) is correctly ~14,250 cP (viscosity.py logic is
  unchanged and still strictly monotonic in T -- this is not a physics
  bug). Updated the test to assert `0.5*mu_ref_cP < mu(47C) < 3.0*mu_ref_cP`
  (relative to the field's own confirmed reference viscosity) instead of a
  stale absolute literal, so it keeps testing the same intent ("cold
  viscosity near the reference point is thousands of cP, not tens or
  hundreds") without hardcoding a placeholder-era number.

---

# rev 4 — Tier-1 physics (13 Sep 2026 18:26, commit a82cfa7)

> **UNCALIBRATED — recalibration pending.** Every value in this revision was
> set to make the Tier-1 physics (T1-A … T1-H in
> `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_PHYSICS.md`) run end to end,
> not fitted to anything. With these params the engine currently gives SOR
> ~9–11 t/m³ and 29–108 d produce phases, against 3–8 t/m³ and 60–220 d
> targets (sweep in `docs/model-improvement/TIER1_PROGRESS_LOG.md` §3).
> Do not quote numbers from this revision. Every dashboard, deck and study
> figure still comes from rev 3 (the "prototype v1" physics above).

Provenance note: the `field_params.json` edits were committed in **8c6643b**
(13 Sep 18:19, bundled with the PROJECT_LOG commit); the physics code that
reads them landed seven minutes later in **a82cfa7**. They are one change.
This entry was written after the fact (26 Sep 2026) from
`TIER1_PROGRESS_LOG.md` §1 and `git show 8c6643b -- params/field_params.json`.

## reservoir

- `drainage_radius_m`: new, **100.0**. ASSUMPTION. Real drainage radius
  for the composite-radial PI (T1-A, `ipr.composite_uplift`). Replaces the
  deleted `twin/thermal.py` `DRAINAGE_RADIUS_M = 8.0` blend, which was a
  calibration knob rather than a drainage radius.
- `well_radius_m`: new, **0.1**. TYPICAL wellbore radius, r_w in
  ln(r_e/r_w) of the same PI.

## fluid

- `walther_A` / `walther_B`: new, kept **null**. Walther / ASTM D341
  (T1-F) is fitted at runtime from the same two anchors, for the same
  float-drift reason `andrade_A`/`andrade_B_K` are null (see §fluid above).
  Andrade is still reachable only via explicit non-null `andrade_A/B_K`.
- `mu_floor_cP`: new, **1.0**. ASSUMPTION. Viscosity floor; the old Andrade
  extrapolation gave 0.63 cP at 290 °C, Walther + floor gives 4.13 cP.
- `water_cut`: new, **0.85**. ASSUMPTION, no field datum. Used by the
  Boberg–Lantz energy-removal term δ ∝ 1/(1 − water_cut) (T1-B). Flagged
  as the third recalibration knob (lowering to ~0.75 lengthens cycles).

## steam

- `latent_heat_Jkg`: 1.3e6 -> **1.4e6**. CALCULATED. h_fg at ~9.0 MPa
  (the saturation pressure of the confirmed 280–305 °C injection) is
  ≈1.40 MJ/kg per steam tables; 1.3e6 was low (+8 % delivered heat).

## wellbore (new block, T1-H)

- `insulation`: **"VIT"**. OIL runs vacuum-insulated tubing.
- `heat_loss_frac_per_1000m`: **0.10**. ASSUMPTION (VIT; ~0.25 uninsulated,
  Ramey-anchored). At 1,150 m → 11.5 % heat loss down the tubing.
- `quality_at_sandface_frac_of_wellhead`: **0.55**. ASSUMPTION. Sandface
  quality = 0.65 × 0.55 ≈ 0.36. Together with the latent-heat change the
  delivered-heat multiplier is ≈0.52 vs rev 3.

## srp

- `spm_practice_band`: new, **[3, 6]**. TYPICAL. Published heavy-oil SRP
  band (2–8 SPM, most desirably 3–6); used to check the T1-D declining-SPM
  schedule.
- `spm_floor`: new, **2.0**. ASSUMPTION. Lower limit of the declining-SPM
  schedule (`simulate_css_cycle(..., spm_floor=)`).

## css

- `cutoff_rate_m3d_range`: [1, 8] -> **[0.5, 2.5]**. PROVISIONAL. Honest
  peak rates are now ~2.1–3.7 m³/d (13–23 bbl/d), so most of the old
  [1, 8] range sat above the peak and ended cycles on produce day 1. Must be re-set together with `AOF_REF_M3D` so that
  `cutoff_lo > q_cold` (`test_ipr.py::test_cold_rate_is_uneconomically_low`).

## economics (new block, T1-G)

- Constants copied with sources from
  `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md` §1.2:
  `diesel_kg_per_t_steam` 71.0, `diesel_density_kg_per_l` 0.83,
  `diesel_price_inr_per_l` 97.8, `diesel_co2_kg_per_GJ` 74.1,
  `gas_co2_kg_per_GJ` 56.1, `steam_energy_GJ_per_t` 3.02,
  `crude_realization_usd_per_bbl` 65.0, `heavy_oil_discount_usd_per_bbl`
  10.0, `inr_per_usd` 88.0, `oil_price_inr_per_bbl` 4840.0,
  `fixed_cost_inr_per_cycle` 1.5e6, `electricity_inr_per_kWh` 8.0,
  `bbl_per_m3` 6.28981. Read by `cycle.summary(df, params)` for ₹/CO₂/margin
  keys; `ml/optimize.py` does not use them yet.

## twin/ constants changed alongside (code, not JSON)

- `twin/ipr.py` `AOF_REF_M3D`: 0.7 -> **0.60** m³/d. PROVISIONAL — the
  progress log's first recalibration step is to raise it to ~1.3–1.5.
  New: `S_COLD = 5.0`, `MAX_UPLIFT = 10.0`, `P_CAL_KPA = 11400`.
- `twin/thermal.py` `DRAINAGE_RADIUS_M` (8.0) and `COOLDOWN_TAU_DAYS`
  (20.0): **deleted**, replaced by `reservoir.drainage_radius_m` (above)
  and the Boberg–Lantz cooldown (T1-B, `BL_UNCERTAINTY_FRAC = 0.42`).
- `twin/cycle.py`: `PWF_DRAWDOWN_FRACTION` deleted (P_wf now absolute);
  new `PRESSURE_BOOST_PER_T_KPA = 2.0`, `TAU_BLEED_D = 25.0`,
  `PUMP_SUBMERGENCE_M = 100`, `CASING_HEAD_PRESSURE_KPA = 200`,
  `CP_LIQUID_JM3K = 4.0e6`, `SPM_MARGIN = 0.6`, `DEFAULT_SPM_FLOOR = 2.0`.
- `twin/srp.py`: `VOLUMETRIC_EFFICIENCY` replaced by `FILLAGE_MAX = 0.85`.

Verification at this revision: `pytest tests -q` -> **21 passed, 3 failed**
(`test_cycle.py::test_full_cycle_smoke`,
`test_cycle.py::test_SOR_has_interior_optimum_over_steam_volume`,
`test_thermal.py::test_temperature_decays_toward_reservoir_after_injection_stops`).
All three encode rev-3 calibration literals and are expected to be replaced
in the recalibration pass (`TIER1_PROGRESS_LOG.md` §2). Re-verified 26 Sep 2026.

---

# rev 5 — calibration (26 Sep 2026, branch `physics-v2`)

> **CALIBRATED against published bands, with two recorded misses.** Reference cycle
> 1,500 t / 7 d / cutoff 1.2 m³/d / 5 spm → **SOR 4.09**, 367 m³ (2,308 bbl), 182-d
> produce phase, peak 15.9 bbl/d, peak/cold uplift **5.66×**, cold 0.447 m³/d,
> μ(290 °C) 4.13 cP, margin **+₹8.8 L/cycle** (+₹4,245/cycle-day) at bulk diesel.
> Misses kept as strict xfails in `tests/test_benchmarks.py`: P_res 11.4→7.4 MPa gives
> **+61 %** SOR (Liaohe band +20–40 %), and the soak-day optimum is **not interior**.
> Full before/after tables and iteration log: `docs/model-improvement/TIER1_PROGRESS_LOG.md` §4.
> `data/`, `ml/`, `dashboard/`, `ppt/` still carry v1 numbers — retrain before quoting.

Most of the rev-4 gap was **three internal inconsistencies**, not tuning. They were
fixed in code first; the constants below were then tuned against the benchmark table.

## Physics corrections (code)

- `twin/thermal.py` — **sensible heat of the injected water added** to the
  Marx–Langenheim heat balance: delivered heat per kg = `C_w·(T_s − T_R) + x_sf·L_v`
  (Marx & Langenheim 1959; Prats, SPE Monograph 7). rev 4 credited only
  `x_sf·L_v·(1−loss)` = 443 kJ/kg; correct value is 1,581 kJ/kg (3.6×). New
  constant `CW_LIQUID_JKGK = 4500` J/kg·K, CALCULATED from steam tables
  `[h_f(290 °C) − h_f(50 °C)]/240 K`. Effect: r_h at 1,500 t 5.2 m → 9.8 m.
- `twin/thermal.py` — **wellbore loss no longer double-counted.** The sandface quality
  ratio (0.55) already *is* the tubing condensation; the extra `(1 − loss)`
  multiplier removed the same joules twice. New helpers
  `sandface_enthalpy_J_per_kg()`, `implied_wellbore_loss_frac()`.
- `twin/thermal.py` — **Boberg–Lantz `f_HD` is now the exact cylinder**
  `1 − e^{−x}[I0(x)+I1(x)]`, `x = r_h²/(2αt)` (Carslaw & Jaeger), new `cylinder_theta()`,
  replacing the documented slab-of-thickness-2·r_h stand-in (which under-predicted
  horizontal loss ~2× early: 0.73 vs 0.50 at r_h 10 m, 240 d). Verified against
  numerical integration to 1e-4 (`tests/test_thermal.py`). `f_VD` (exact slab) unchanged.
  Effect: reference SOR 3.0 → 3.7 at equal settings.
- `twin/srp.py` — **the pump lifts liquid, not oil.** Oil capacity = displacement ×
  fillage × (1 − `fluid.water_cut`), the same stream `cycle.py` already uses for δ.
  rev 4 compared displacement with the oil rate alone (6.7× overstated at 85 % cut).
  New `pump_state` keys `oil_capacity_m3d`, `pump_limited`.
- `twin/cycle.py` — new DataFrame column `pump_limited` (appended after the SPEC
  columns) and summary key `pump_limited_days`. `steam_cost_inr_per_t()` applies
  `economics.diesel_bulk_discount_frac`.

## Values changed (old → new, benchmark tuned to)

| Where | Key | Old → new | Why / benchmark |
|---|---|---|---|
| `twin/ipr.py` | `AOF_REF_M3D` | 0.60 → **0.46** m³/d | [CALIBRATED] cold rate ≤ ~0.5 m³/d (now 0.447 at real P_wf) and peak/cold in BGW-8's 5–6× |
| `twin/cycle.py` | `PRESSURE_BOOST_PER_T_KPA` | 2.0 → **1.0** kPa/t | [CALIBRATED] uplift 6.2× → 5.7× (BGW-8 5–6×); also more defensible because wet-steam injection BHP (~9–10 MPa) is below virgin 11.4 MPa |
| `twin/cycle.py` | `SPM_MARGIN` | 0.6 → **1.0** | schedule now enforces the physical fall-velocity limit; the 0.6 alarm stays a risk flag. At 0.6 FI could never exceed 0.6 anywhere, so `failures_expected` was always 0 (decorative). Now trips in the high-SPM / cold-tail corner (32 % of a 400-row LHS) and not at the reference |
| `field_params.json` | `srp.stroke_m` | 3.0 → **2.18** m (86 in) | [TYPICAL – not Baghewala] heavy-oil pump sized to the well; ECON plan FAIL 2 asked for 1.7–2.5 m |
| `field_params.json` | `srp.plunger_d_m` | 0.057 → **0.0445** m (1.75 in) | [TYPICAL – not Baghewala]; ECON plan FAIL 2 asked for 1.5–1.75 in. Oil capacity at 3/5/6 spm = 1.9/3.1/3.7 m³/d, bracketing the ~2.5 m³/d peak, so SPM is a lever (3 spm → 141 pump-limited days, SOR +3 %) |
| `field_params.json` | `wellbore.heat_loss_frac_per_1000m` | 0.10 → **0.18** | now reporting-only; set to the loss implied by the 0.55 sandface-quality ratio (20.6 % at 1,150 m) so both params describe the same joules (test checks ±10 %) |
| `field_params.json` | `css.cutoff_rate_m3d_range` | [0.5, 2.5] → **[0.6, 2.0]** | lower bound above the cold rate (0.447); upper bound below the ~2.5 m³/d reference peak so the search space has few day-1 cycles |
| `field_params.json` | `economics.diesel_bulk_discount_frac` | new, **0.30** | [CALIBRATED, UNSOURCED] base-case steam ₹5,856/t (low end of the documented ₹5,900–8,400/t band; ECON plan's −30 % row). Target: revealed preference — OIL ran 19 CSS jobs in FY26, so a sensible cycle must pay. Retail (discount 0, ₹8,366/t) flips the reference margin to −₹28.8 L (tested) |

## Reviewed, deliberately **unchanged**

- `thermal.BL_DELTA_FACTOR = 0.5` — the single most sensitive constant (1.0 would give
  reference SOR ≈ 5.1). The original Boberg & Lantz (JPT 1966) text could not be
  retrieved to confirm the ½; left as implemented. **Open item.**
- `fluid.water_cut = 0.85` — implies ~139 % of injected water produced back at the
  reference (high for a first cycle). Lowering it (more oil per joule removed) lowers SOR.
  **Open item** (T2-A makes it a state).
- `ipr.S_COLD = 5`, `MAX_UPLIFT = 10` (never binds; max seen 6.0), `TAU_BLEED_D = 25`
  (±60 d moves SOR < 3 %), `srp.FILLAGE_MAX = 0.85`, `viscosity` 150 °C/50 cP anchor.

## Open item — porosity / thickness conflict (26 Sep data hunt)

Yasin et al. 2022, *Sci. Rep.* 12:11086 (doi 10.1038/s41598-022-14831-5) gives
Baghewala-1 Jodhpur Sandstone porosity **16–25 %** and gross Jodhpur Fm thickness
**~50 m**, against `reservoir.porosity = 0.09` (GEOHORIZONS 2015 "<10 %") and the
12 m net-pay placeholder. **Kept 0.09 / 12 m.** Sensitivity at the reference cycle:

- `porosity` is **not read anywhere in `twin/`** (productivity is carried by the
  field-anchored `AOF_REF_M3D`, heat capacity by `rock_heat_capacity_Jm3K`). 0.09 vs
  0.20 gives identical output. Propagating it into a derived bulk heat capacity
  (2.30 → 2.35 MJ/m³K at 0.20): SOR 4.09 → 4.08, r_h 9.84 → 9.74 m, uplift 5.66 → 5.63.
  **The calibration holds at either porosity.**
- `thickness_m` **is** first-order: h = 20 / 30 / 50 m → SOR 4.05 / 4.38 / 5.27,
  uplift 5.16 / 4.81 / 4.42, r_h 7.9 / 6.5 / 5.1 m, reference margin +9.8 / +1.3 / −16.3 L,
  and at ≥30 m the steam-volume response inverts (SOR falls with steam). 50 m is a
  *gross formation* thickness and must not be used as the steam-contacted net pay.
  The BGW-8 5–6× uplift is only reproduced for net pay of roughly 8–20 m.

Verification at this revision: `pytest -q` → **57 passed, 2 xfailed** (strict).

---

# rev 6 — computed dynamometer cards (26 Sep 2026, branch `dyno`)

New `twin/dyno.py` (Gibbs 1963 wave-equation surface + pump card) reads eight
**new, additive** keys in the `srp` block. No existing key or value changed; no
other module reads them, so every day-by-day cycle number is unchanged. Full
method and validation: `docs/model-improvement/DYNO_CARD_MODEL.md`.

## srp (additions only)

- `rod_taper_d_in` = **[1.0, 0.875]**, `rod_taper_frac` = **[0.485, 0.515]**,
  `rod_taper_mass_kgm` = **[4.322, 3.310]**. [TYPICAL – not Baghewala] API
  "87"-class 1″ × 7/8″ two-taper string (558 m over 592 m at 1,150 m); masses
  are the API RP 11B tabulated weights *with couplings* (2.904 / 2.224 lb/ft).
  The split is chosen so the mass-weighted mean equals the existing
  `rod_mass_kgm` = 3.8 kg/m, i.e. the card model and `srp.py` carry the same
  rod weight (42.9 kN air). An equal-top-stress design would put only ~30 % in
  1″ — ours is top-heavy/conservative. Wave speed from E and mass/area:
  4,926 m/s (the usual ~16,000 ft/s for coupled steel rods).
- `rod_E_Pa` = **2.07e11**. [TYPICAL] steel, 30 × 10⁶ psi.
- `gibbs_damping_nu` = **0.10**. [TYPICAL] Gibbs dimensionless damping factor,
  mid of the 0.05–0.15 normal-crude range; c = π·a·ν/(2L) = 0.67 s⁻¹. The
  heavy-oil excess is NOT in ν: it is `srp.K_VISC`·μ per metre of rod (the same
  drag law `srp.py` uses), so there is one viscous law in the twin, not two.
- `crank_pitman_ratio` = **0.25**. [TYPICAL] conventional-unit crank/pitman
  ratio for the SHM + second-harmonic (Mills) polished-rod motion; sets peak
  acceleration (1 ± 0.25)·(S/2)ω² at bottom/top of stroke.
- `tubing_head_pressure_kPa` = **300**. [TYPICAL, no field datum] flowline back
  pressure; with `cycle.py`'s 200 kPa CHP + 100 m submergence intake pressure
  (1.14 MPa) and a 994 kg/m³ 85 %-cut tubing column this gives
  Fo = (11.52 − 1.14) MPa × A_p = **16.1 kN** (srp.py's ρ_oil·g·L·A_p = 16.9 kN).
- `plunger_friction_kN` = **0.9**. [TYPICAL] ~200 lbf metal-plunger friction,
  opposing plunger motion; appears as the (Fo + 2·F_fr) height of the pump card.

Finding (not changed here, out of scope): `srp.pump_state`'s `energy_kWh_d`
(peak load × stroke × strokes) is **3.6×** the card-area polished-rod energy at
the hot baseline day (237.8 vs 65.4 kWh/d) and 2.0× at the cold end (277.7 vs
138.2), because it charges the rod weight on the upstroke without crediting it
back on the downstroke. `dyno.compute_cards()["polished_rod_kW"]` is the
energy-consistent number if the economics ever needs it.

---

# rev 7 — physics v3 (26–27 Sep 2026, branch `physics-v3`)

> *Renumbered rev 6 → rev 7 when `main` (which already carried rev 6 = computed
> dynamometer cards) was merged into `physics-v3` on 27 Sep. Content unchanged.*

> **No `field_params.json` value changed. No calibration knob was re-tuned.** Reference
> 1,500 t / 7 d / 1.2 m³/d / 5 spm → **SOR 4.027** (was 4.089, −1.5 %), 372.5 m³ (+1.5 %),
> 185-d produce phase, peak 15.9 bbl/d, uplift 5.66×, margin **+₹10.6 L** (+₹4,998/cycle-day;
> was +₹8.8 L / ₹4,245). SOR stays inside 3.8–4.6, so `AOF_REF_M3D` and
> `PRESSURE_BOOST_PER_T_KPA` are untouched. `pytest -q` → **67 passed, 1 xfailed** (strict,
> soak). Full tables are in `docs/model-improvement/TIER1_PROGRESS_LOG.md` §7.
> `ml/`, `data/`, `dashboard/`, `ppt/` still carry rev-5 ₹ numbers. Every margin rose by ₹0.6–1.2k/cycle-day (+6 to
> +38 %; see §7), so they need a re-bake before anyone quotes ₹.

## Sourced / code changes
- `twin/thermal.py` `BL_DELTA_FACTOR = 0.5` — **SOURCED; value unchanged.** It is the ½ in
  Boberg & Lantz's `f_pD = (1/2Q)∫Q̇_p dt`, Q = injected heat remaining in the reservoir
  (SPE *Petroleum Engineering Handbook* Vol. V ch. 15, Eqs. 15.70/15.73 + nomenclature,
  reproducing Boberg & Lantz 1966). It is also the only value that conserves energy when
  there is no conduction (θ = 1 − Q_p/Q). 1.0 double-counts the produced heat.
  `bl_delta_factor()` override kept only for `ml/uq.py` compatibility. Write-up:
  `docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md`.
- `twin/cycle.py` `CP_LIQUID_JM3K = 4.0e6` — **DELETED** (it was an unsourced blend). δ's
  produced heat now follows PEH Eq. 15.74 stream by stream, in the new
  `thermal.produced_heat_J_per_day()`:
  - oil: `M_o` from API gravity plus Gambill's c_o;
  - water: steam-table `h_f(T̄) − h_f(T_R)`. New helpers `water_enthalpy_kJkg()` and
    `oil_heat_capacity_Jm3K()`, new constant `RHO_W_STOCK_KGM3 = 1000` [DEFINITION];
  - steam and gas terms are zero, labelled [ASSUMPTION] (see the write-up).

  Effect: SOR −1.5 %. Every margin moves more (thin-margin leverage: +1.5 % oil ≈ +₹1.7 L).
- `tests/test_benchmarks.py`:
  - The **Liaohe P_res xfail is re-specified**, not widened, as
    `test_depletion_response_is_darcy_proportional`. The band comes from the Vogel/Darcy
    drawdown ratio: fixed-duration limit 1/r − 1 = +57.6 %, band −5/+15 pp. The twin gives
    +61.4 %.
  - The soak xfail is kept and tightened to "5–15 d and ≥ 2 % over both box ends, grid to
    30 d".
  - New `test_soak_is_a_weak_lever_margin_plateau`.
- New tests: 4 in `tests/test_thermal.py` (½ energy balance, steam table, oil heat capacity,
  Eq. 15.74 structure), 1 in `tests/test_cycle.py` (δ computed from production).

## Reviewed, deliberately unchanged (with reasons in TIER1 §7)
- **Soak.** No mechanism added. Soak-only conductive spreading was prototyped and rejected:
  it counts horizontal conduction as a loss during production but not during soak, which
  makes soak a monotone free lunch (+12 % oil at 30 d vs 7 d).
- **Cutoff rule.** Stays a rate cutoff. An economic cutoff is a no-op here:
  electricity-only opex (~250 kWh/d ≈ ₹2,000/d) gives q_EL ≈ 0.07 m³/d, below the 0.447 m³/d
  cold rate. The published CADP rule (Rivero & Heintz; PEH ch. 15) never triggers, because
  the margin carries no daily opex and no cold-production baseline. **Open item for the
  economics owner.**
- `TAU_BLEED_D`, `PRESSURE_BOOST_PER_T_KPA`, `AOF_REF_M3D`, `fluid.water_cut` (still the
  open δ input).

---

# rev 8 — Economics v2: incremental oil, daily opex, corrected srp energy (27 Sep 2026, branch `physics-v3`)

> **Physics unchanged:** every SOR, oil, produce-day, peak, uplift and FI number is identical
> to rev 7 (energy does not feed back into the reservoir). What changed is the money and
> the energy. At the base price deck, **incremental margin is negative at every feasible
> set-point** (best −₹3,590/cycle-day). That is a finding, not a bug; see "Judgement calls".
> `pytest -q` → **116 passed, 1 xfailed** (strict, soak). Full tables:
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §8.

## Added keys (all additive; no existing value changed)
- `economics.opex_inr_per_day` = **5,000**. [ASSUMPTION] Fixed well-site opex, **excluding
  power**: manpower, routine maintenance, chemicals, water handling. No per-well or per-bbl
  Indian onshore lifting-cost figure was found. The OIL Annual Report 2024-25 was checked:
  it gives a crude realisation of US$78.09/bbl, 294 workover jobs, and ₹2,987 cr royalty +
  ₹2,567 cr cess, but no lifting cost. Cross-check: ₹5,000/d is ~$3/bbl at the field
  average of ~19 bbl/d/well, or ~$20/bbl on this model well's own 2.8 bbl/d cold rate.
  UQ range ±50 %. Charged every calendar day of the window (shut-in days included). The cold
  well pays it too, so it **cancels in the incremental margin** unless the cold well becomes
  uneconomic (above ~₹12.5k/d).
- `srp.surface_efficiency` = **0.60**. [TYPICAL] Prime mover to polished rod:
  motor × belts × gearbox × structure, typically ~0.55–0.75 (Takacs, *Sucker-Rod Pumping
  Handbook*, 2015, ch. 4). Converts polished-rod kWh to grid kWh.
- `fixed_cost_inr_per_cycle` (₹15 L rig/pump pull per job) is **unchanged**. No better source
  was found; it sits inside the $15–50k workover band.

## Code
- **`twin/srp.py` energy fix.** `energy_kWh_d` is now the closed-loop polished-rod work,
  ∮F dx: the rod weight is lifted on the upstroke and credited back on the downstroke, and
  inertia integrates to zero. What remains:
  - pump ΔP × liquid lifted, with ΔP = THP + ρ_mix·g·L − P_intake (dyno's Fo/A_p);
  - plunger friction 2F_fr·S;
  - viscous drag plus Gibbs damping, (K_VISC·μ·L + m·c_G)·⟨v²⟩·T with
    ⟨v²⟩ = (π²/8)·v̄²·(1 + λ²/4);
  - downstroke damping work capped at W_rf·S (carrier-bar separation).

  It matches `dyno.compute_cards()` card area to within −1 to +9 % from hot to cold, float
  included. The old estimate (peak load × stroke × spm) was 1.4–3.6× the card. New keys:
  `electric_kWh_d` (÷ surface efficiency), `hydraulic_kWh_d`. `peak_rod_load_kN` and
  `floating_index` are unchanged. Reference cycle: 248.5 → **85.5 kWh/d** polished rod;
  **123 → 42.5 kWh/m³** oil (70.8 kWh/m³ at the grid).
- **`twin/cycle.py`:**
  - new `cold_baseline(params)`: IPR uplift 1, virgin P_res, same absolute P_wf, pump at
    the 2-spm keep-moving floor. Cold rate 0.447 m³/d; 97.6 kWh/d polished rod,
    163 kWh/d grid.
  - three appended columns: `electric_kWh`, `oil_cold_m3d`, `electric_cold_kWh`.
  - new `summary()` keys:
    - window and opex: `window_days`, `electric_kWh`, `electric_kWh_per_m3`,
      `power_cost_inr`, `opex_fixed_inr`, `opex_inr`, `margin_with_opex_inr`,
      `margin_with_opex_inr_per_cycle_day`;
    - cold baseline: `cold_rate_m3d`, `cold_well_economic`, `oil_cold_baseline_m3`;
    - incremental: `oil_incremental_m3`, `oil_incremental_bbl`, `SOR_incremental`,
      `margin_incremental_inr`, `margin_incremental_inr_per_cycle_day`,
      `margin_incremental_inr_per_t_steam`;
    - re-steam point: `cadp_resteam_day`, `cadp_resteam_rate_m3d`,
      `cadp_margin_incremental_inr_per_cycle_day`.

  The gross `margin_inr` / `margin_inr_per_cycle_day` keep the rev-5 definition (steam +
  rig, no opex) for backward compatibility.
- **`ml/recommend_physics.py`:** the objective is now `margin_incremental_inr_per_cycle_day`
  (`objective=` keyword; pass `"margin_inr_per_cycle_day"` for rev 5).
  `ml/optimize._physics_verify` returns the incremental keys (additive). The ML surrogate
  objective (`ml/optimize.py`) is **not** changed here; it needs the re-baked margin model
  (cascade).
- **`ml/uq.py`:**
  - `bl_delta_factor` is no longer varied (sourced 0.5, rev 7);
  - `water_cut` stays U[0.70, 0.90];
  - new input `opex_inr_per_day` U[2,500, 7,500];
  - money metric is the incremental margin/cycle-day, and gross is still reported;
  - SOR bands are reported gross and incremental;
  - 100-draw smoke test only; the bake is the cascade's job.
- **`twin/calibrate.py`:** `DEFAULT_FREE = ("water_cut", "aof_ref_m3d", "thickness_m")`.
  `bl_delta_factor` is still accepted, but off by default. `generate_pseudo_real.py` hides
  bl = 0.5. The regenerated demo recovers:
  - water_cut 0.778 (truth 0.78, −0.2 %);
  - aof 0.559 (+1.6 %);
  - thickness 15.13 (+0.9 %).

  Across 5 noise seeds water_cut stays at 0.770–0.790, so it is now identifiable alone.

## Conventions (decided here)
1. **Cold baseline window = the whole cycle, inject and soak days included.** The shut-in
   costs the cold oil the well would have made. This is the standard "stimulated minus
   unstimulated over the same time period" definition of incremental CSS oil. It is recalled
   from Boberg's *Thermal Methods of Oil Recovery* (1988) and the PEH ch. 15 CSS discussion,
   and was **not re-retrieved this session**. Window = `days_total` + 1 d, because the last
   produce row is a full day.
2. **SOR headline stays GROSS** (steam ÷ all oil). That is how every benchmark in this repo
   is quoted: CalGEM field SOR = (cyclic + steamflood steam) ÷ total field oil; Cold Lake
   "SOR ≈ 4" and the CSS "life-cycle SOR ~6" are cumulative steam ÷ cumulative oil; the css
   deep dive §1 defines OSR as oil produced per unit steam. `SOR_incremental` is the
   economic ratio: 5.40 at the reference, not 4.03.
3. **₹ decisions use the incremental margin per cycle-day.** Gross margin is still reported.
4. If the cold well cannot cover its own opex, the counterfactual well is **shut in**
   (baseline cash 0).

## Judgement calls the team must know
- **At the base deck, CSS loses money against producing the well cold.** The base deck is
  ₹4,840/bbl (= $65 − $10 heavy discount) and ₹5,856/t steam. Break-even incremental SOR
  before the rig cost is 5.20 t/m³; the twin's best is ~4.9. Incremental margin/cycle-day:
  - reference −₹8,328;
  - baseline (b) −₹9,851;
  - rev-5 recommendation −₹5,019;
  - grid best −₹3,590.

  This contradicts OIL's revealed preference (19 CSS jobs in FY26). The rev-5 revealed-
  preference calibration of `diesel_bulk_discount_frac` = 0.30 was done on the **gross**
  basis, which credits CSS with the cold well's own oil.
- **Break-even (incremental margin = 0) at the rec 1,700/10/0.85/5:** oil ≥ ₹5,498/bbl
  ($62.5 net, i.e. ~$72.5 before the $10 heavy discount), or steam ≤ ₹5,050/t.
  - OIL's **actual FY25 realisation of $78.09/bbl** (OIL AR 2024-25, CONFIRMED) − $10 gives
    ₹5,992/bbl. On that deck the rec makes **+₹3,761/cycle-day** and the grid best is
    +₹4,514.
  - The $65 in `economics` is the CMD's FY26 planning floor, not a realisation.
  - **Deck NOT changed here:** it moves every ₹ on the dashboard, so it is a team call.
    Recommended for the cascade: re-price at the confirmed $78.09 or show both decks.
- **Not modelled:** royalty and OID cess. The ₹ deck is a pre-levy (national-value) basis.
  OIL's own P&L view would net them out, and FY25 shows ₹2,987 cr royalty + ₹2,567 cr cess,
  so the company-basis margin is materially lower.
- **"Lower cutoff is always better" is NOT fixed by the incremental basis.** On a
  per-cycle-day objective the cold baseline is a constant per-day offset, so it moves the
  *sign*, not the argmax. The incremental and gross argmaxes coincide (1,400/0.65/3.5 at
  base). The CADP rule condition q·P < gross average ⇔ (q − q_c)·P < incremental average is
  also identical on both bases. What creates an economic re-steam point is the **price
  level**:
  - at base the CADP average is negative, so the rule never triggers: produce to the cold
    rate;
  - on the FY25 deck it triggers at **q\* ≈ 0.62 m³/d** (4 spm) or 0.54 (3 spm);
  - but FI > 0.6 is reached first (0.67 at 4 spm), so the float line (cutoff ≈ 0.70)
    binds before economics does.
- **Recommendation for the cascade** (true-physics grid, soak 10, FI ≤ 0.6):
  - minimax-regret across both decks: **1,600 t / 10 d / 0.70 m³/d / 4.0 spm**, ≤ ₹214/d
    from either deck's optimum;
  - 1,700/0.85/5 is ₹1,429/d (base) or ₹753/d (FY25) below the optimum;
  - the lever is **spm 5 → 4 plus cutoff 0.85 → 0.70**: lower SPM lets the cutoff go lower
    before the rods float. Steam 1,500–1,800 t is flat within ~₹200/d.
- Fixed opex, surface efficiency, cold-well SPM and the ₹8/kWh tariff are all labelled
  assumptions. Power is ~₹1.7–3.4 L/cycle, ~2–2.5 % of revenue.

---

# rev 9 — Price deck: OIL's confirmed FY25 realisation (27 Sep 2026, branch `physics-v3`)

> **Physics unchanged.** Only `economics.oil_price_inr_per_bbl` (and its two upstream
> USD components) moved. Every SOR, oil, produce-day, peak, uplift, FI and alarm-day
> number in this repo is identical to rev 8. `pytest -q` → **116 passed, 1 xfailed**
> (one test literal updated — see "Test updated" below). Full re-run tables:
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §9 (to be added by the cascade).

## economics

- `crude_realization_usd_per_bbl`: 65.0 → **78.09**. CONFIRMED — OIL India Annual
  Report 2024-25, FY25 average crude oil realisation. New key
  `crude_realization_usd_per_bbl_source` records the citation inline.
- `heavy_oil_discount_usd_per_bbl`: unchanged, **10.0**. [ASSUMPTION] — no
  Baghewala-specific heavy-crude marketing discount was found; kept as the same
  flat $10/bbl haircut used since rev 4. New key
  `heavy_oil_discount_usd_per_bbl_note` records this inline.
- `oil_price_inr_per_bbl`: 4,840.0 → **5,992.0**. = (78.09 − 10) × 88 = 5,991.92 ≈
  5,992. New key `oil_price_inr_per_bbl_source` records the derivation inline.
- New `oil_price_presets` block (nested object; not read by any existing code path —
  verified no module iterates `params["economics"]` generically, only pulls named
  scalar keys — so this is purely additive):
  - `fy25_realisation`: {usd_per_bbl_gross 78.09, usd_per_bbl_net 68.09,
    inr_per_bbl 5,992.0} — **the new base case**.
  - `fy26_floor_65`: {usd_per_bbl_gross 65.0, usd_per_bbl_net 55.0,
    inr_per_bbl 4,840.0} — the OLD base case (rev 4–8), kept as a named sensitivity
    preset labelled "OIL FY26 planning floor" (the CMD's forward planning number,
    not a market realisation).
  - `ml/uq.py`'s bake now runs both decks (see `ml/README.md`); the dashboard's
    "Your prices" panel exposes both as one-click presets.
- `twin/cycle.py`'s `_DEFAULT_ECONOMICS["oil_price_inr_per_bbl"]` updated to match
  (5,992.0), per `summary()`'s own docstring promise that the module default equals
  the shipped `field_params.json` value.

## Why this deck, not the other

Rev 8 (§8.4/§8.8) found the model pays at OIL's confirmed FY25 realisation and loses
against the cold well at the old $65 placeholder. $65 was never a realisation — it was
the CMD's FY26 *planning floor* (a conservative budgeting number), and the $78.09 FY25
actual is directly confirmed in the same Annual Report that gives OIL's royalty/cess
lines. The coordinator's call (rev 8 §8.8 flagged this as a team decision): make the
CONFIRMED, already-realised number the base case, keep the placeholder as a named
downside preset rather than deleting it — a reader who wants the conservative view can
still get it with one flag/preset click, and nothing computed from the base case
silently uses an unrealised number.

## Benchmark trio, re-run at rev 9 (FY25 deck; physics identical to rev 8)

Physics-verified (`twin.cycle.simulate_css_cycle` + `summary`), FY25 deck
(₹5,992/bbl) unless marked "$65 floor":

| | Reference 1500/7/1.2/5 | Baseline (b) 1300/10/1.3/5 | Rec 1600/10/0.70/4 |
|---|---|---|---|
| SOR gross | 4.027 | 4.061 | 3.590 |
| SOR incremental | 5.403 | 5.502 | 5.004 |
| oil m³ | 372.5 | 320.1 | 445.6 |
| incremental oil m³ | 277.6 | 236.3 | 319.7 |
| days | 211.3 | 186.6 | 280.6 |
| peak bbl/d | 15.91 | 15.13 | 15.66 |
| gross ₹/cycle-day | 17,774 | 15,824 | 21,117 |
| ₹/cycle-day with opex | 11,696 | 9,824 | 14,971 |
| **incremental ₹/cycle-day (FY25)** | **+1,149** | **−724** | **+4,423** |
| incremental ₹/cycle-day ($65 floor, for comparison) | −8,328 | −9,851 | −3,804 |
| max FI | 0.297 | 0.241 | 0.577 |
| alarm days | 0 | 0 | 0 |
| grid electric kWh/m³ | 70.8 | 67.1 | 84.6 |
| tCO₂/cycle | 335.7 | 290.9 | 358.1 |
| diesel L/cycle | 128,313 | 111,205 | 136,867 |

At the FY25 deck the reference and the cascade recommendation both turn incremental-
margin-positive (the recommendation clearing baseline (b) by ~₹5,147/cycle-day); at the
$65 floor every case is still negative, unchanged from rev 8 (physics is untouched, so
these numbers exactly reproduce rev 8 §8.3/§8.6).

## Test updated (not a physics retune)

- `tests/test_cycle.py::test_margin_has_interior_optimum_over_steam_volume` compared
  `margin_inr_per_cycle_day` (GROSS, no opex) at steam_t 1,000 vs 500 and 3,000. At the
  higher FY25 price, revenue per barrel is high enough that 3,000 t now beats 1,000 t
  on gross margin (17,306 vs 15,859 ₹/cycle-day) — the hump shifted outward (interior
  max now ~2,000 t, was ~1,500 t at the old price) but did not disappear. Rewrote the
  assertions to compare the grid's middle point (1,500 t) against both edges instead of
  1,000 vs 3,000; the "best is interior, not an edge" assertion is unchanged and still
  passes (best = 2,000 t on the (500, 1000, 1500, 2000, 3000) grid).

## Verification

`pytest -q` → **116 passed, 1 xfailed** (strict, soak — unchanged from rev 8).

---

# rev 10 — Hardening after the external technical review (27 Sep 2026, branch `harden`)

> **No calibration knob was re-tuned.** Every rev-5/7 band still passes with the shipped
> `AOF_REF_M3D` 0.46, skin 5 and boost 1.0 kPa/t:
> - reference 1,500 / 7 / 1.2 / 5: SOR **4.027** (incremental 5.40), 372.5 m³, peak 15.9 bbl/d,
>   uplift 5.66×, 185 produce days, all unchanged;
> - the CalGEM band and the Darcy P_res band are unchanged.
>
> What moved:
> - **Rod-float index.** It is now **~0 everywhere** at the shipped 85 % water cut, because the
>   produced stream is water-continuous.
> - **Incremental ₹/cycle-day.** Every value fell by ₹0.6–0.9k. The cold counterfactual well's
>   rod-drag power collapsed from 163 to 23 kWh/d.
> - **Canonical recommendation.** It moves from 1,600 / 10 / 0.70 / 4 to **1,700 / 10 / 0.60 / 4**.
>
> `pytest -q` → **148 passed, 1 xfailed** (strict soak xfail kept). Full write-up:
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §9. Review:
> `REVIEW.md` in the session scratchpad (52/100).

## Code fixes

1. **Latent dt bug** (`twin/cycle.py` `summary()` / `_incremental_economics`).
   - The oil, polished-rod energy and grid-electricity totals were `sum(daily rate)` with no × dt.
     At dt = 0.5 d the reference SOR read 2.02; at dt = 0.25 d it read 1.01.
   - Every total is now `sum(rate) × dt`. So are the day counts (`failures_expected`,
     `days_rods_in_compression`, `descent_violation_days`, `pump_limited_days`) and
     `rod_float_damage_index`.
   - dt comes from `df.attrs["dt_days"]`, which `simulate_css_cycle` now sets. It is inferred from
     the row spacing if absent.
   - At dt = 1 d nothing changes. TIER1 §7.4's "same at dt = 1 d and 0.25 d" soak claim was
     computed through the broken summary; §9 re-states it.
   - New test `tests/test_cycle.py::test_summary_is_invariant_to_timestep` covers dt = 1 / 0.5 /
     0.25 within 1 %; measured ≤ 0.15 %.
2. **μ-dependent cold rate** (`twin/ipr.py`).
   - `AOF_REF_M3D` is now defined at `MU_AOF_REF_CP = 11,500` cP. Cold productivity scales with
     Darcy mobility, `11,500 / fluid.mu_ref_cP` (`cold_mobility_factor`).
   - The reference cold rate is unchanged at 0.447 m³/d.
   - Across 8,000 / 11,500 / 15,000 cP:
     - cold rate is 0.643 / 0.447 / 0.343 m³/d (it used to be 0.447 for all three);
     - reference incremental margin is +₹8,406 / +₹346 / −₹7,581 per day. This was
       counter-physical before: the more viscous oil earned more.
   - The uplift band still holds at 11,500 cP (5.66×). At 8,000 cP the 5-spm pump caps the peak,
     so uplift is 4.8×.
3. **Produced-stream (emulsion) viscosity for rod drag** (`twin/srp.py` `rod_drag_viscosity_cP`;
   used by `pump_state`, `fall_velocity_ms`, `max_spm_for_viscosity`, the polished-rod energy and
   `twin/dyno.py`).
   - Brinkman (1952), μ_c·(1 − φ)^−2.5, applied to the continuous phase:
     - water cut < inversion (oil-continuous, W/O): μ_o·(1 − wc)^−2.5;
     - water cut ≥ inversion (O/W): μ_w(T)·wc^−2.5.
   - μ_w(T) is the Vogel water correlation, new in `viscosity.water_mu_cP`.
   - `fluid.tubing_viscosity_model = "oil"` restores the rev-9 rule, and reproduces rev 9 exactly.
   - `dyno.compute_cards` still takes the **oil** viscosity (API contract) and converts it
     internally. It echoes `inputs.mu_drag_cP`.
4. **Steam P–T consistency check** (`twin/thermal.py`: `p_sat_kPa`, `T_sat_C` from IAPWS-IF97
   region 4; `steam_state_check`, `warn_steam_state`).
   - `simulate_css_cycle` warns once per state and never fails.
   - It flags two things at the shipped params:
     - 290 °C is below T_sat 299–308 °C at the 85–97 kgf/cm² wellhead;
     - P_res 11.4 MPa > p_sat(290 °C) = 7.44 MPa, so the sandface fluid is subcooled water.
5. **Reservoir pressure state** (`twin/cycle.py` `reservoir_pressure_kPa`).
   - The IPR, the cycle's base pressure and the cold baseline all use `reservoir.P_current_kPa`
     when it is set, else the virgin `P_initial_kPa`.
6. **LHS SPM range** (`twin/generate_data.py` `sampled_spm_range`).
   - The sample now spans the union of `srp.spm_range` and `srp.spm_practice_band`, i.e.
     **3–12 spm** (was 4–12), so the training data cover the optimiser's 3–6 box.
   - The cutoff range is unchanged. `data/` was **not** regenerated (cascade).
7. **Skin as an optional calibration parameter** (`twin/calibrate.py`).
   - `"s_cold"` is accepted in `free` with bounds (0, 8). It is off by default because it trades
     off against `aof_ref_m3d`.
8. **Recommendations and gain decomposition** (`ml/recommend_physics.py`, new `ml/decompose.py`).
   - `best_settings_physics` returns `aggressive` (FI ≤ 0.6) and `conservative` (FI ≤ 0.5)
     side by side, and takes an optional explicit `grid_values`. The top-level keys stay
     aggressive.
   - `ml/decompose.py` writes `ml/models/gain_decomposition.json`, which holds:
     - OAT and Shapley attribution from baseline (b) to the rev-9 recommendation and to the rev-10
       canonical recommendation;
     - baseline-cutoff sensitivity at 1.0 / 1.3 / 1.6;
     - aggressive and conservative optima on the §8.6 grid for both decks.
9. **UQ** (`ml/uq.py`). Seven inputs are added **after** the original seven, so for a given seed
   the original seven draws are unchanged:

   | Input | Range |
   |---|---|
   | `s_cold` | U[0, 8] |
   | `k_visc` | U[5, 15] |
   | `pressure_boost_kPa_per_t` | U[0.5, 2.0] |
   | `mu_anchor_cP` | U[30, 80] |
   | `fixed_cost_inr_per_cycle` | ±50 % |
   | `P_current_kPa` | U[7,400, 11,400] |
   | `emulsion_inversion_wc` | U[0.60, 0.75] |

   - There is also a fourth point, `recommended_rev10` (1,700 / 10 / 0.60 / 4).
   - 300-draw FY25 smoke run (not the bake):
     - P(rev-9 rec > baseline) = **0.987**, P(rev-10 rec > baseline) = 0.983. Both were 1.00.
     - P(incremental > 0): 0.22 reference, 0.16 baseline, 0.38 rev-9 rec, 0.40 rev-10 rec.
     - OAT tornado on the rec: water_cut ₹30.1k/d, **s_cold ₹15.7k/d**, diesel discount
       ₹14.3k/d.
10. **Wording.** The Kern River docstring in `tests/test_benchmarks.py` now reads: "a shallow,
    predominantly steamflood field with a cyclic-steam subset; field-level SOR band only".

## Values moved to `field_params.json` (value unchanged; module constant kept as fallback)

| Key | Value | Tag, range (UQ) | Was |
|---|---|---|---|
| `ipr.s_cold` (new block) | 5.0 | [ASSUMPTION], 0–8 (U[0, 8]) | `ipr.S_COLD` |
| `srp.k_visc` | 10.0 | [ASSUMPTION], 5–15 (U[5, 15]) | `srp.K_VISC` |
| `reservoir.pressure_boost_kPa_per_t` | 1.0 | [CALIBRATED/ASSUMPTION], 0.5–2.0 (U) | `cycle.PRESSURE_BOOST_PER_T_KPA` |
| `fluid.mu_anchor_T_C`, `fluid.mu_anchor_cP` | 150 °C, 50 cP | [ASSUMPTION – SPEC placeholder], μ(150) 30–80 (U) | `viscosity.ANCHOR_*` |
| `economics.fixed_cost_inr_per_cycle` | 1.5e6 (already in params) | [ASSUMPTION], ±50 % (U[7.5e5, 2.25e6]) | tag + range added |

## New keys

| Key | Value | Tag |
|---|---|---|
| `reservoir.P_current_kPa` | **null** (= virgin 11,400) | [ASSUMPTION – depleted, UNKNOWN; top data ask]; UQ U[7,400, 11,400]. Not silently re-tuned. |
| `fluid.tubing_viscosity_model` | `"emulsion"` | model switch; `"oil"` = rev-9 rule |
| `fluid.emulsion_inversion_wc` | 0.70 | [ASSUMPTION], heavy-oil band 0.60–0.75 (U) |
| `steam.wellhead_pressure_kgf_cm2_g` | [85, 97] | [CONFIRMED – OIL deck BGW-08]; read only by the P–T check |

Each has a `*_note` string sibling carrying its tag and range inline, as rev 9 did for the price
keys.

New code constants:
- `ipr.MU_AOF_REF_CP = 11,500` [CONFIRMED anchor];
- `srp.DEFAULT_EMULSION_INVERSION_WC = 0.70` and `srp.BRINKMAN_EXP = 2.5` [SOURCED, Brinkman
  1952];
- `recommend_physics.CONSERVATIVE_FI_MAX = 0.5` [ASSUMPTION];
- `thermal._IF97_N` [SOURCED, IAPWS-IF97].

## Calibration knobs (item 9): **none changed**

`AOF_REF_M3D` stays at 0.46, skin at 5 and the boost at 1.0.

The reference is untouched because:
- the dt fix is a no-op at dt = 1 d;
- the mobility factor is exactly 1 at 11,500 cP;
- the emulsion model only changes production where the SPM ceiling bound, which it did not at the
  reference.

Every band passes without a fudge:

| Band | Result |
|---|---|
| SOR 3–8 over 500–3,000 t | 3.60–4.53 |
| Reference SOR (3.8–4.6) | 4.03 |
| Uplift | 5.66 (5.1 / 5.7 at the BGW-8 slug ends) |
| Peak | 15.9 bbl/d (still at the edge of 15–40) |
| Produce phase | 185 d |
| CalGEM band | pass |
| Darcy P_res band | pass |
| Gross margin at reference | +₹37.6 L |

## Tests changed (not tuned)

- `test_floating_constraint_binds_in_the_high_spm_cold_tail_corner` is **re-specified** as two
  tests:
  - `test_float_alarm_does_not_bind_in_a_water_continuous_stream` asserts the finding. At 85 %
    cut, FI < 0.05 even at 12 spm with a 0.6 cutoff.
  - `test_float_alarm_binds_when_the_stream_is_oil_continuous` covers the 65 % cut case and the
    rev-9 rule.
- `test_energy_intensity_uses_corrected_polished_rod_energy`: the band is 30–80 → 20–80 kWh/m³.
  Drag is gone, so the reference is 28.9. The rev-9 rule still gives 42.5, which the test also
  asserts.
- `tests/test_dyno.py` solver-mechanics tests run on the rev-9 rule via a local `params` fixture,
  because they test the solver at a stated drag viscosity. A new test covers the default emulsion
  model: no float at 85 %, float at 60 %.
- `test_srp.py::test_floating_index_increases_with_viscosity` runs on the rev-9 rule.
- New tests:
  - `tests/test_hardening.py`, 10 tests;
  - emulsion, K_VISC, skin, mobility, IF97, steam-check and dt tests in the existing files.

---

# rev 11 — Physics wave 3: water cut as a state, injection-pressure and stroke levers (27 Sep 2026, branch `harden`)

> Three published-physics changes, each behind a switch that reproduces rev 10 exactly
> (`cycle.legacy_rev10_params`: `fluid.water_cut_model = "constant"`,
> `steam.state_model = "legacy_T"`, `reservoir.P_current_kPa = null`, stroke 2.18 m, no PRL cap;
> `tests/test_physics_wave3.py::test_legacy_switches_reproduce_rev10` pins three rev-10 cases).
>
> **Calibration knobs: none changed.** `AOF_REF_M3D` stays 0.46. The reference SOR moved
> 4.027 → **3.899**, inside the coordinator's 3.8–4.6 band, so the brief's "re-tune AOF only if
> SOR leaves 3.8–4.6" rule did not fire. The peak band now fails (12.4 bbl/d < 15), and AOF
> cannot fix both bands (sweep in TIER1 §10). It is a strict xfail finding.
>
> `pytest -q` → **171 passed, 2 xfailed** (soak xfail kept; peak-band xfail added). Full write-up:
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §10.

## Physics changes

1. **Water cut as a state (T2-A)**, in `twin/cycle.py`.
   - Produced water = condensate flowback + formation water.
   - Condensate is a mixing-cell tank holding `condensate_recovery_frac` × steam mass
     (1 t = 1 m³). It mixes with the heated-zone pore volume V_p = φπr_h²h. Its share of the
     liquid is c = W/(W + V_p), and the tank loses c × liquid each day. That is an exponential
     decay with τ = (V_p + W)/q_L.
   - The rest of the liquid carries `formation_water_cut`. The day's water cut is
     wc = c + (1 − c)·f_w.
   - The day's water cut feeds:
     - pump liquid (oil capacity = displacement × fillage × (1 − wc));
     - the emulsion drag viscosity (Brinkman, inversion 0.70), and through it rod drag, FI, the
       SPM ceiling and polished-rod energy;
     - the Boberg–Lantz produced heat (actual water at T_avg);
     - the tubing column density;
     - the power cost.
   - No water-handling cost key exists. The lifting energy of the water is in the power bill.
   - The cold counterfactual produces at `formation_water_cut`. It runs the params' own pump
     (86 in, 2 spm), whatever stroke the stimulated cycle uses.
   - The rate cutoff now applies only past the peak (below the cutoff AND below the running
     peak). This is identical to the old rule for every cycle whose first produce day clears the
     cutoff.
2. **Injection pressure → steam state (P–T consistency)**, in `twin/thermal.py` `steam_state`.
   - Saturation properties come from an IAPWS-IF97 table, 200–350 °C, generated with `iapws`
     1.5.5. It is within 0.36 % of full IF97 (< 0.1 % over 280–320 °C).
   - The steam state:
     - T_wh = T_sat(P_wh);
     - P_sf = P_wh + the head of a homogeneous (no-slip) two-phase column at the mean quality;
     - T_sf = T_sat(P_sf);
     - x_sf = 0.55 · x_wh, as before;
     - h_del = x_sf·h_fg(P_sf) + h_f(P_sf) − h_f(T_R).

     Tubing friction is neglected (~0.1–0.2 MPa; stated).
   - Values across the pressure range:

     | Wellhead kgf/cm² | P_sf MPa | T_sf °C | h_del MJ/kg |
     |---|---|---|---|
     | 85 | 9.45 | 306.9 | 1.658 |
     | 91 | 10.12 | 311.9 | 1.672 |
     | 97 | 10.79 | 316.6 | 1.686 |
     | rev 10 | – | 290 | 1.580 |
   - Fuel per tonne is scaled by the wellhead-enthalpy ratio against 91 kgf/cm² (±0.2 %). There
     is no compression cost: the generator sets the pressure.
   - The near-well recharge is capped at P_sf. The injection pressure is its only source.
   - `steam_state_check` (saturated_P) warns only if P_res ≥ P_sf (injection impossible) or P_wh
     is outside 85–97. **It passes at the default** (margin 0.72 MPa).
3. **Stroke as a control**, in `twin/srp.py`.
   - Stroke takes the API sizes 64 / 74 / 86 / 100 / 120 / 144 in.
   - `peak_prl_kN` uses Mills: W_rf + F_o + W_r·α(1+λ) + peak drag + plunger friction, on the
     mixture density. It is checked against `srp.max_prl_kN`, and it tracks the wave-equation
     card peak within 15 % (tested).
   - The cycle takes `stroke_m=` and `p_wellhead_kgf_cm2=` overrides.

## New / changed keys

| Key | Value | Tag |
|---|---|---|
| `reservoir.P_current_kPa` | null → **9,400** | [ASSUMPTION — derived from the injectivity requirement; top data ask]. The largest P that admits injection over 85–97 kgf/cm² (P_sf(85) = 9.45 MPa). UQ U[7,400, 9,400]. |
| `fluid.water_cut_model` | **"state"** | rev 11 switch; "constant" = rev ≤ 10 |
| `fluid.condensate_recovery_frac` | **0.70** | [ASSUMPTION 0.5–0.9; Prats / Butler]; UQ U[0.5, 0.9] |
| `fluid.formation_water_cut` | **0.45** | [ASSUMPTION 0.3–0.6; no Baghewala figure]; UQ U[0.3, 0.6] |
| `fluid.water_cut` | 0.85 (kept) | read only by "constant" |
| `steam.state_model` | **"saturated_P"** | "legacy_T" = rev 10 |
| `steam.P_wellhead_kgf_cm2` | **91** | CONTROL; CONFIRMED range 85–97 |
| `steam.P_wellhead_range_kgf_cm2` | [85, 97] | CONFIRMED |
| `steam.T_injection_C`, `latent_heat_Jkg` | unchanged | read only by "legacy_T" (T is reporting-only now) |
| `srp.stroke_m` | 2.18 → **2.1844** | 86 in exactly (API) |
| `srp.stroke_in_options` | [64, 74, 86, 100, 120, 144] | API Spec 11E |
| `srp.max_prl_kN` | **113.9** | [TYPICAL] structure rating of a C-320D-256-120, 25,600 lb. For comparison, C-456D-305-144 is 135.7 kN and C-228D-213-86 is 94.7 kN. Strokes above 86 in need a larger unit than the assumed C-228; that capex is not costed. |

Unchanged, but note: `wellbore.heat_loss_frac_per_1000m` (reporting only) implies 0.207, against
the new IF97 implied 0.189 (−9 %, inside the 10 % test).

## Knock-ons (findings, not tuned)

- **Reference** 1,500 / 7 / 1.2 / 5 at 86 in / 91 kgf/cm²:

  | Metric | rev 11 | rev 10 |
  |---|---|---|
  | SOR | 3.899 | 4.027 |
  | Oil | 384.7 m³ | – |
  | Produce days | 228 | – |
  | Peak | **12.43 bbl/d** | 15.91 bbl/d |
  | Uplift | 5.41× | – |
  | Water cut | 0.872 → 0.597 | – |
  | Float-alarm days | **97** (first on produce day 131, once wc < 0.70) | – |
  | Incremental, FY25 | +₹4,246/d | – |

- **Attribution at the reference:**
  - the water-cut state alone moves SOR 4.03 → 3.15. The constant 85 % cut produced 2,111 m³ of
    hot water; the state produces 1,365 m³;
  - P_current 9.4 MPa alone moves SOR to 4.75 and the peak to 13.3;
  - the IF97 steam and the recharge cap move the peak to 12.4.
- **Cold counterfactual.**
  - The cold rate is 0.366 m³/d (was 0.447).
  - At the formation cut the cold stream is an oil-continuous 51,000 cP emulsion: FI 1.0,
    PRL 189 kN (above every listed unit rating), 433 kWh/d grid (was 23).
  - Every incremental margin rises by ~₹6.3k/d (FY25) from the counterfactual alone.
  - The model says a cold Baghewala well at 45 % water cannot be rod-pumped at 2 spm. That is a
    consistency flag on the Brinkman W/O branch, or on f_w < inversion. A cold-well dyno card
    decides.
- **Recharge.**
  - It is capped at 0.72 MPa of room at 91 kgf/cm² (1.39 MPa at 97).
  - `pressure_boost_kPa_per_t` no longer binds above ~0.48 kPa/t at 1,500 t, so the boost's UQ
    swing is now small.

## Optimiser, decomposition, UQ

- `ml/recommend_physics.py::best_settings_physics_5d`.
  - Exhaustive search over 11 × 4 × 29 × 6 × 7 = 53,592 points in ~33–48 s (1,848
    simulations).
  - Every cutoff is read off one lowest-cutoff run as a prefix. This was checked against direct
    simulation and against `summary()`.
  - Constraints: FI ≤ 0.6 / 0.5 plus the PRL cap. Minimax regret on both decks.
  - It reports `controls_coverage`, the unconstrained optimum and the price of the constraints.
  - Coordinate descent (the brief's fallback) was tried first. It stalled from the
    FI-infeasible rev-10 start.
- `ml/decompose.py`: five levers, Shapley over 120 orders. The canonical rec comes from the 5-D
  search.
- `ml/uq.py`:
  - `formation_water_cut` takes the old `water_cut` slot (same draws);
  - `condensate_recovery_frac` is appended;
  - P_current is U[7,400, 9,400];
  - points carry stroke and pressure;
  - new `P_float_ok`;
  - "recommended" = the rev-11 rec; the rev-9 and rev-10 recs are kept as extra points.
- `twin/calibrate.py`.
  - It accepts `formation_water_cut` and `condensate_recovery_frac`.
  - `fit(free=None)` uses `default_free(params)`: under the state model that is
    formation_water_cut, aof and thickness.
  - The committed pseudo-real demo is rev-10 physics. `twin/generate_pseudo_real.py` and the
    calibrate tests pin `legacy_rev10_params`, so the demo stays reproducible.
- `twin/dyno.py`: `card_for_row` uses the row's water cut and the cycle's stroke.

## Tests changed (not tuned)

- **Moved to the rev-10 switches** (the statement is about that stream):
  - `test_spm_is_a_real_lever`;
  - `test_float_alarm_does_not_bind_in_a_water_continuous_stream`;
  - the flat-plateau test;
  - the rev-10 steam-state test;
  - the energy-intensity band (the state-model value is asserted separately).
- **Re-specified:**
  - reference SOR band 4.0–6.0 → the coordinator's 3.8–4.6;
  - `_cold_rate` and the depletion tests use `P_current`. The base is 9.4 MPa and the Darcy limit
    is +29 %. The band is evaluated at cutoff 0.8; at 1.2 the truncation adds +17 pp (reported);
  - retail diesel asserts the 3–5 break-even band (4.50) instead of one cycle's sign;
  - boost liveness is tested at 0.3 kPa/t (below the cap);
  - the API baseline SOR pin moved 4.061 → 4.007.
- **Strict xfail added:** `test_peak_rate_inside_field_envelope` (12.4 < 15 bbl/d).
- **New:** `tests/test_physics_wave3.py`. It covers:
  - water-cut profile;
  - T_sat coupling;
  - P–T check passes;
  - injectivity warning;
  - recharge cap;
  - stroke displacement;
  - PRL vs card;
  - cutoff prefix;
  - 5-D optimiser;
  - controls coverage;
  - calibrate / UQ switches;
  - float binds late;
  - SPM acts via float and power.

---

# rev 12 — Physics wave 4: Pal–Rhodes emulsion with cap, float-onset produce-end rule, AOF retune to the peak band (27 Sep 2026, branch `harden`)

> Three coordinator decisions, implemented and reported as the physics says. Each sits behind a
> switch: `cycle.legacy_rev11_params` (Brinkman, no cap, rate-cutoff rule, AOF 0.46) reproduces
> the rev-11 numbers to the digit (`tests/test_physics_wave4.py`, three cases), and
> `legacy_rev10_params` now also sets those four switches, so the calibration demo is unchanged.
>
> **One calibration knob moved: `AOF_REF_M3D` 0.46 → 0.56**, to put the reference peak in the
> 15–40 bbl/d field band. The reference-SOR band was re-specified from 3.8–4.6 to **3.0–4.6**.
>
> `pytest -q` → **197 passed, 2 xfailed**. The soak xfail is kept. The peak xfail now passes and has been
> un-xfailed. A new strict xfail records that the cold well cannot be pumped at 2 spm. Full
> write-up: `docs/model-improvement/TIER1_PROGRESS_LOG.md` §11.

## Physics changes

1. **W/O emulsion law, in `twin/srp.py` `wo_relative_viscosity`.**
   - The law is Pal & Rhodes (1989, *J. Rheol.* 33:1021):
     μ_r = [1 + (φ/φ*)/(1.187 − φ/φ*)]^2.49, with φ = water cut and φ* = the water fraction at
     which μ_r = 100.
   - It is capped at `emulsion_mu_r_max`. The O/W branch is unchanged.
   - **The law is Brinkman in disguise:** μ_r = (1 − φ/(1.187 φ*))^−2.49. Brinkman is the case
     φ* = 0.842. Calibrating φ* to the centre of the published heavy-oil band (4.5× at 45 %
     water) gives φ* = 0.84, i.e. Brinkman within 1 % below 60 % water.
   - The fitted φ* of Pal and Rhodes (~0.6–0.85) are *more* viscous than Brinkman, not less. The
     brief's premise that Brinkman over-predicts at 30–50 % water is not supported: Brinkman
     gives 2.4–5.7× there, inside the 2–10× band.
   - **What changes the physics is the 10× cap.** It binds only above ~60 % water, where Brinkman
     gave 10–19×. That is where the late-cycle stream sits (wc 0.60–0.70).
2. **Produce-end operating rule, in `twin/cycle.py`.**
   - `css.produce_end_rule` ∈ {`rate_cutoff`, `float_onset`, `either`}; default **`either`**.
   - `float_onset` ends the cycle when FI > `css.fi_alarm` (0.6) on `css.fi_alarm_days` (3)
     consecutive produce days.
   - `simulate_css_cycle(..., produce_end_rule=)` overrides the params value.
   - `df.attrs` and `summary()` carry `produce_end_rule` and `produce_end_reason`. `summary()`
     also carries `produce_days`, `peak_oil_produce_day`, `produce_end_days_after_peak` and
     `cold_mu_drag_cP`.
   - A params tree without the key runs `rate_cutoff`, i.e. rev ≤ 11 behaviour.
   - It is dt-invariant (dt 1 vs 0.25: SOR within 0.2 %).
3. **AOF_REF_M3D 0.46 → 0.56**, in `twin/ipr.py`, also written to `params["ipr"]["aof_ref_m3d"]`.
   - This is the smallest 0.01 step that lifts the reference peak to ≥ 15 bbl/d (15.13).
   - The uplift is AOF-invariant (5.41×). The cold rate is 0.445 m³/d at P_current and 0.544 at
     virgin pressure; both stay below the 0.6 cutoff floor.

## New / changed keys

| Key | Value | Tag |
|---|---|---|
| `fluid.emulsion_law` | **"pal_rhodes"** | rev 12 switch; "brinkman" (or key absent) = rev 10/11 |
| `fluid.emulsion_phi_star` | **0.84** | [ASSUMPTION], calibrated to 4.5× at 45 % water (centre of the published 2–10× band); UQ U[0.65, 1.0] (≈ 9× → 3.3×). Pal & Rhodes fits ~0.6–0.85 (recalled, not re-retrieved in full). |
| `fluid.emulsion_mu_r_max` | **10.0** | [ASSUMPTION]: the top of the published band. Near-inversion extrapolation of the zero-shear divergence is not supported for shear-thinning crude W/O at rod-annulus shear rates. Not sampled. |
| `css.produce_end_rule` | **"either"** | rev 12 operating policy |
| `css.fi_alarm` | 0.6 | = the SPEC float-risk line |
| `css.fi_alarm_days` | **3** | [ASSUMPTION — an operator would pull / re-steam rather than run floating rods; one dyno confirmation plus a rig call-out; no Baghewala SOP] |
| `ipr.aof_ref_m3d` | **0.56** (was the module constant 0.46) | [CALIBRATED] to the 15–40 bbl/d peak band |
| `ipr.AOF_REF_M3D` (code) | 0.46 → 0.56 | same value as the params key |

## Knock-ons (findings, not tuned)

- **Reference** (1,500/7/1.2/5 spm/86 in/91):
  - rev 12 SOR is 4.50 and incremental margin **−₹1,690/d**. The cycle ends on **float onset on
    produce day 151**, with the rate still at ~1.9 m³/d.
  - Under the rate-cutoff rule it would be SOR 3.18, ending day 239.
  - The rule costs the reference 88 produce days of cheap late oil.
- **Baseline (b):** ends on float onset on day 139, SOR 4.35, −₹1,601/d FY25. Its cutoff no
  longer matters (1.0/1.3/1.6 give the identical cycle).
- **Cold well: unchanged by the law**, because Pal–Rhodes at φ* 0.84 equals Brinkman at 45 %
  water.
  - 51,261 cP, FI 1.0, PRL 189.4 kN, 433.5 kWh/d grid (432.8 in rev 11).
  - **Not pumpable at ≥ 2 spm on the 86-in unit** (new strict xfail).
  - Pumpable at 2 spm × 86 in only for μ_r ≤ ~1.9, which is the Taylor clean-interface limit
    and below the published band. It is pumpable at 1 spm × 64 in (90 kWh/d).
  - **The rev-11 "+₹6.3k/d counterfactual artefact" shrank by ₹0 from the emulsion change.**
  - AOF 0.56 separately raises cold cash by ₹3.0k/d FY25, which lowers every incremental margin
    by that amount.
  - The part of the artefact still standing (unpumpable-cold-well power vs a 1-spm cold well) is
    ~₹2.7k/d.
- **Darcy band:** under the `either` rule the depleted cycle floats later and the SOR response
  falls to +15.5 %. The test is now evaluated on a fixed 120-day produce window, which is the
  derivation's literal "fixed-duration" quantity: +25.4 % vs the +28.9 % limit, pass.
- **Soak:** under the float rule, margin per cycle-day falls ~0.6–0.7 % per day of soak beyond
  5 d. The plateau test moves to the rate-cutoff rule, and a new finding test is added. The soak
  xfail stands.

## Optimiser, decomposition, UQ

- **`ml/recommend_physics.py`.**
  - Both optimisers run the params' rule.
  - `_level_feasible`: the aggressive level requires alarm_days ≤ `fi_alarm_days`, plus the
    PRL cap on every day.
  - The conservative level runs **the same rule with its alarm line at 0.5** (own grid,
    `css.fi_alarm` = 0.5): the operator pulls once FI > 0.5 persists.
  - Under `rate_cutoff` both levels are the old max-FI tests.
  - `_truncate_at_cutoff` / `_cutoff_table` honour the rule, report alarm days and end-after-peak,
    and the prefix property still holds (tested).
  - The 3-D optimiser uses a local `_verify` (ml/optimize.py untouched) and the same levels.
- **Canonical rec (5-D, 53,592 points, 3,696 simulations, 36 s):**
  - Settings: **1,000 t / 10 d / 85 kgf/cm² / 64 in / 3 spm / cutoff 0.60 (backstop)**.
  - Value: FY25 **+₹7,973/d**, $65 **+₹40/d**, ending on float onset on produce day 179.
  - It is pinned at five grid floors. With the steam grid opened to 700 t the optimum is
    interior at 800–900 t (+₹107 FY25 / +₹226 $65 per day).
  - **Conservative** (pull at FI > 0.5): the same settings, +₹5,609 / −₹2,369.
- **`ml/decompose.py`.**
  - It adds the rev-11 point and rule-aware feasibility.
  - Gain vs baseline (b): +₹9,574/d FY25. SPM 62 %, stroke 32 %, steam 6 %, **cutoff 0 %**.
- **`ml/uq.py`.**
  - `fluid.emulsion_phi_star` U[0.65, 1.0] is appended.
  - Points:
    - rev-12 rec;
    - rule-based conservative (per-point `fi_alarm` override);
    - fixed-cutoff alternative;
    - rev-11 rec.
  - Robustness probabilities: P(> baseline), P(float-onset end), P(any alarm),
    P(alarm > rule), and fragility P(end ≤ 5 d after peak).
  - **Fragility of the rec: 0.000**. The rev-11 rec under rev-11 physics scored 0.337 on this
    metric (41 % on §10.9's "cutoff ≥ peak" metric).
- **`twin/generate_data.py`** (not run).
  - The LHS is 6-D and adds `p_wellhead_kgf_cm2` (85–97) and `stroke_in` (six API sizes, equal
    strata); SPM is 3–12.
  - The new inputs and `produce_end_reason` / `float_alarm_days` are appended last, so the SPEC
    columns and ml/train.py FEATURES are unchanged.

## Tests changed (not tuned)

- **Re-specified:**
  - reference SOR band 3.8–4.6 → **3.0–4.6**;
  - Darcy band on a fixed produce window;
  - soak plateau evaluated under `rate_cutoff`;
  - `test_cold_rate_is_uneconomically_low` at P_current, with the virgin-pressure rate still
    below the floor;
  - the cold-rate-viscosity pin 0.447 → 0.447·0.56/0.46;
  - the CADP re-steam upper bound scaled by the same AOF ratio;
  - the API baseline SOR pin 4.007 → 4.351.
- **Moved to the rate-cutoff rule** (the statement is about a rate-driven cycle):
  - the cutoff-crossing test;
  - CADP;
  - the rev-11 water-cut profile;
  - SPM-via-power;
  - the PRL-cap-binds test.
- **Moved to the rev-11 switches:** the review-finding-1 Shapley test (cutoff dominance).
- **The emulsion unit test** now checks Pal–Rhodes, the cap and the Brinkman switch.
- **Un-xfailed:** `test_peak_rate_inside_field_envelope`.
- **New strict xfail:** `test_cold_well_pumpable_at_2_spm_on_the_assumed_unit`.
- **New:** `tests/test_physics_wave4.py`. It covers:
  - rev-11 switch;
  - Pal–Rhodes/Brinkman identity;
  - cap;
  - φ* band;
  - cold-well numbers and pumpability threshold;
  - both rule branches;
  - float-only rule;
  - dt;
  - prefix under the rule;
  - SPM via float timing;
  - fragility;
  - AOF/uplift invariance;
  - optimiser;
  - decomposition;
  - LHS;
  - UQ.


---

# rev 13 — Physics wave 5: operating policy as a control, fair baseline, smooth inversion, injectivity gate, levies deck (27 Sep 2026, branch `wave5`)

> Response to the technical re-score (58/100). Its top finding: the rev-12 +₹9,574/d gain came from
> the **pull rule** ending baseline (b) on day 139 while it still made 1.87 m³/d. The twin's own
> VFD mode erased it.
>
> This rev makes the operator's float response a parameter and an optimiser dimension. It applies
> the same policy to the baseline, the recommendation and the cold counterfactual, and reports what
> the physics says.
>
> **No calibration knob was moved.**
> - AOF, K_VISC, φ\*, the cap, skin and P_current are unchanged.
> - The diesel discount **base** moved 0.30 → 0.15. This was the coordinator's instruction; it is
>   an economics input, not a physics fit.
>
> `cycle.legacy_rev12_params` reproduces rev 12 to the digit (tested on three cases).
>
> `pytest -q` → see TIER1 §12 for the count.
> - The rev-12 cold-well strict xfail is **un-xfailed**: the counterfactual now obeys the policy.
> - One **new strict xfail** records a finding: the steam optimum at the mid-range diesel price
>   sits below the BGW-8 slug range.
>
> Full write-up: `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12.

## Physics / model changes

1. **Float policy, in `twin/cycle.py`.**
   - Key: `css.float_policy` ∈ {`pull`, `vfd_hold`, `vfd_then_pull`, `none`}.
     - `pull` = rev 12: the SPM schedule runs at SPM_MARGIN 1.0, and the well is pulled after
       `fi_alarm_days` alarm days.
     - `vfd_hold`: the schedule holds FI at `css.vfd_hold_fi` (0.6) down to `css.vfd_spm_floor`
       (2 spm). The alarm can only fire at the floor; the well is pulled after `fi_alarm_days`
       there.
     - `vfd_then_pull`: as `vfd_hold`, but the floor is max(2, `css.vfd_turndown_frac` 0.5 ×
       start SPM).
     - `none`: no float response; the cycle runs to the rate cutoff (= the rev ≤ 11 rule).
   - `simulate_css_cycle(..., float_policy=)` overrides the params value.
   - An explicit `produce_end_rule="rate_cutoff"` override still means `none`.
   - FI comparisons against the alarm line use a 1e-9 tolerance (`cycle.ALARM_TOL`), so a day held
     exactly on 0.6 is not an alarm day.
2. **Cold counterfactual obeys the policy.** Key: `css.cold_counterfactual`; function
   `cycle.cold_counterfactual_well`.
   - `policy` (default): the cold well runs on the params' own unit at the policy floor. If FI
     there exceeds `fi_alarm` it is **shut in**.
     - At base it is shut in under every float policy (FI 1.0, PRL 189 kN at 2 spm × 86 in).
     - Under `none` it is the rev-12 cold well.
   - `pumpable`: the field fact that the wells produced cold. The VFD slows the cold well below the
     keep-moving floor (down to `css.cold_pumpable_min_spm`, 0.25) until FI ≤ 0.6.
     - At base: 0.53 spm, 0.445 m³/d, 49 kWh/d, PRL 90 kN.
   - `shut_in` and `legacy` are also available.
   - `summary()` keys:
     - `cold_rate_m3d` stays the PHYSICAL cold rate (uplift is measured against it);
     - new `cold_counterfactual_rate_m3d`, `cold_status`, `cold_spm`.
   - `cold_baseline()` is unchanged (`ml/schedule.py` reads it).
3. **Smooth inversion, in `twin/srp.py`.** Key: `fluid.emulsion_inversion_band_wc` = **0.075**
   [ASSUMPTION 0.05–0.10].
   - It is a band centred on the inversion cut. Inside it, ln μ_drag is blended linearly between
     the W/O and O/W branches (inversion is hysteretic/gradual: Salager et al. 2001; Pal 1993,
     recalled).
   - Absent or 0 gives the rev-12 switch.
   - Max day-to-day drag-viscosity ratio at the reference crossing: **3,365× → 1.22×**. Max FI
     step: 0.228 → 0.068 per day.
4. **Flowback mobility ratio.** Key: `fluid.flowback_mobility_ratio` M = **1.0** (c = M·W/(M·W +
   V_p); 1 = rev 11/12). Sampled {1, 3, 10} in UQ.
5. **Injectivity gate.** Key: `steam.min_injection_margin_kPa` = **400** [ASSUMPTION 300–500 kPa:
   two-phase tubing friction + control margin].
   - `summary()` gains `injection_margin_kPa` and `injection_ok`.
   - The optimisers reject set-points below the margin.
   - 85 kgf/cm² gives 53 kPa and fails. 87 gives 276 kPa, 89 gives 498 kPa, 93 gives 944 kPa.
6. **Economics.**
   - `economics.diesel_bulk_discount_frac` 0.30 → **0.15**: the mid of U[0, 0.30], steam
     ₹7,111/t. `cycle._DEFAULT_ECONOMICS` follows.
   - New `economics.diesel_discount_presets` {mid 0.15, bulk 0.30, retail 0}.
   - New deck `economics.oil_price_presets.fy25_net_of_levies` = **₹3,600/bbl**.
     - Derivation: ₹5,992 × (1 − 20 % royalty − 20 % OID cess) [ASSUMPTION on the rates].
     - Cross-checked against the OIL AR 2024-25 exchequer table: royalty ₹2,986.84 cr, cess
       ₹2,567.04 cr, crude sales ₹15,710 cr, i.e. ≤ 35 % → ₹3,890.
     - The ER-policy 50 % cess waiver is not netted.

## New / changed keys

| Key | Value | Tag |
|---|---|---|
| `css.float_policy` | **"pull"** | rev 13 operating policy. The default stays rev-12 operation, because it is what the benchmark calibration was made under (see TIER1 §12.2). The **recommended** policy is `vfd_hold`. |
| `css.vfd_hold_fi` / `css.vfd_spm_floor` / `css.vfd_turndown_frac` | 0.6 / 2.0 / 0.5 | the SPEC line; the keep-moving floor; [ASSUMPTION] VFD turndown |
| `css.cold_counterfactual` / `css.cold_pumpable_min_spm` | **"policy"** / 0.25 | rev 13; [ASSUMPTION] slowest credited VFD speed |
| `fluid.emulsion_inversion_band_wc` | **0.075** | [ASSUMPTION], UQ U[0.05, 0.10] |
| `fluid.flowback_mobility_ratio` | 1.0 | [ASSUMPTION - structural], UQ {1, 3, 10} |
| `fluid.emulsion_mu_r_max` | 10 (unchanged) | now **sampled** U[5, 20] |
| `steam.min_injection_margin_kPa` | **400** | [ASSUMPTION 300–500] |
| `economics.diesel_bulk_discount_frac` | **0.15** (was 0.30) | [CALIBRATED, UNSOURCED], mid-range |
| `economics.diesel_discount_presets` | {0.15, 0.30, 0} | presets |
| `economics.oil_price_presets.fy25_net_of_levies` | ₹3,600/bbl | [ASSUMPTION rates; basis CONFIRMED AR 2024-25] |

## Knock-ons (findings, not tuned)

- **At the shipped defaults (pull), the reference and baseline (b) cycles are unchanged.**
  - Reference SOR 4.50; baseline 4.35.
  - Their ₹ moved for two reasons, in opposite directions:
    - the discount costs −₹10.3k/d at the reference (1,500 t);
    - the counterfactual is now shut in, which removes the ₹8.3k/d cold cash from every
      incremental figure.
  - Net effect on the reference: −₹1,690 → −₹3,727/d FY25.
- **Under `vfd_hold` the reference SOR is 3.46.** That is 0.0005 below the CalGEM floor of 3.465.
  A 500-t slug gives 2.65, below the 3–8 literature band.
  - This is why the default stays `pull`. It is recorded as a finding
    (`test_vfd_hold_takes_small_slugs_below_the_literature_sor_band`).
- **Steam-slug optimum at the 0.15 discount is ~750 t** (gross ₹/cycle-day), below BGW-8's
  1,040–1,560 t. At 0.30 it is 1,000 t.
  - New strict xfail `test_steam_optimum_at_the_mid_range_diesel_price_is_within_bgw8`.
  - Read as revealed preference: OIL's slug size argues for cheaper steam than the mid-range.
- **Soak and steam-lever margin tests** with relative (%) criteria are evaluated at the
  `bulk_0.30` preset they were calibrated at (`_bulk()` in `tests/test_benchmarks.py`, disclosed).
  At 0.15 the reference gross margin per cycle-day falls to ~₹2.2k, and a 2 % criterion becomes
  noise.
- **The smooth band moves almost nothing.** Every cycle end and SOR in the policy table is
  identical to the sharp switch. The float onset happens at water cut 0.55–0.63, below the band.
  - The one visible effect: with the formation cut at 0.60 the late stream sits near the band and
    floats later. `test_delta_is_computed_from_simulated_production` now runs to the rate cutoff:
    it is a heat statement.

## Optimiser, decomposition, UQ, ML data

- **`ml/recommend_physics.py`.**
  - `best_settings_physics_5d(..., policies=)`: the float policy is a sixth, categorical
    dimension. By default only the params' policy is searched; the CLI searches all four.
  - Canonical minimax is over pull/vfd_hold/vfd_then_pull.
  - Output adds:
    - per-policy optima (`by_policy`);
    - baseline (b) under every policy;
    - `gain_vs_baseline_b_same_policy`, as a **net-cash** difference (the counterfactual
      cancels; `none` has a different counterfactual);
    - the injectivity gate;
    - the levies deck (reported; minimax over FY25 + $65 as before).
  - Full grid: 4 policies × 53,592 points, 12,936 simulations, 172 s.
  - **Canonical: 1,000 t / 10 d / 89 kgf/cm² / 64 in / 4.5 spm / cutoff 0.60 / `vfd_hold`.**
    FY25 +₹15,396, $65 +₹3,738, net of levies −₹8,811 per day (shut-in counterfactual).
- **`ml/decompose.py`.**
  - `float_policy` is a lever. It enters only when the two points' policies differ.
  - Attribution is on net cash per cycle-day.
  - The levies deck is added, and the canonical point is decomposed against baseline (b) under
    every policy.
- **`ml/uq.py`.**
  - Appended inputs: cap U[5, 20], `fi_alarm_days` U[1, 14] (whole days), band U[0.05, 0.10],
    M {1, 3, 10}, counterfactual {policy, pumpable}.
  - Diesel base 0.15.
  - POINTS now carry policies: rec, conservative (VFD-hold at 0.5), and same-policy pairs for
    `vfd_hold`/`pull`/`none`.
  - `P_gt_baseline*` uses net cash per cycle-day.
  - New metrics: `P_gt_baseline_same_policy`, `gain_vs_baseline_bands`, `P_injection_ok`,
    `P_cold_shut_in`, and a per-draw `alarm_days_exceed_rule`.
  - `ml/models/` was not regenerated.
- **`twin/generate_data.py`** (not run).
  - A 7th LHS column: `float_policy`, in equal strata.
  - New label columns: `fi_gt_alarm_any`, `float_forced_pull`, `end_rate_over_cutoff` and
    **`float_premature_pull`** (the recommended classifier label, ~41 % positive).

## Tests changed

- **New:** `tests/test_physics_wave5.py` (22 tests):
  - rev-12 switch;
  - defaults;
  - the four policies;
  - prefix under the VFD policies;
  - policy-consistent and pumpable counterfactual;
  - band smoothness and no > 10×/day jump;
  - flowback M;
  - injectivity gate at 0/400/500 kPa;
  - deck presets;
  - optimiser policy dimension;
  - same-policy gain pins;
  - decomposition with the policy lever;
  - UQ inputs;
  - LHS/labels;
  - the VFD-hold SOR-band finding.
- **Un-xfailed:** the wave-4 cold-well test. It is now
  `test_cold_well_is_not_pumpable_at_2_spm_and_the_counterfactual_says_so`: the physical finding
  (FI 1.0, 189 kN) is asserted, and the counterfactual is shut in or pumped within the policy.
- **Moved to `legacy_rev12_params`:** the wave-4 5-D slow-rods test (it is a statement without the
  injection gate) and the wave-4 UQ conservative check.
- **Moved to a producing (`pumpable`) counterfactual:** the incremental-vs-gross identities in
  `tests/test_cycle.py`. The shut-in equality is asserted alongside.
- **At the `bulk_0.30` preset:**
  - steam-slug interior optimum (benchmark + cycle);
  - soak plateau;
  - soak under the float rule;
  - the soak strict xfail;
  - retail-vs-bulk.
- **Sharp switch (band 0):** the srp inversion-jump assertion.
- **Updated:** LHS columns (7) and the UQ input order.
