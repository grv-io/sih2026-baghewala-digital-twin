/* =========================================================================
   BAGHEWALA DIGITAL TWIN — v4 core script
   Inlined verbatim into every page by build.js. Owns: config contracts,
   field constants, formatting, the bilingual dictionary, the theme system,
   the cross-page state bus and the app chrome (nav + status bar).
   ========================================================================= */

/* ---------- CONFIG --------------------------------------------------------
   Deploy kit, 27 Sep 2026: MOCK now AUTO-DETECTS instead of a hand-set
   `true`/`false` literal. `?mock=1`/`?mock=0` in the URL always wins (QC/demo
   override); MOCK_OVERRIDE below is the old "hand-edit the constant" escape
   hatch, kept for a developer who wants to force one mode locally without a
   query string; absent both, file:// (opened straight off the filesystem)
   serves the baked reference data and anything else (served by
   `uvicorn api.main:app`, i.e. Render/Railway/Fly/a VPS, or a local dev
   server) is live. API_BASE is the empty string (same origin) whenever the
   FastAPI process is the one serving this page; the file:// fallback still
   points at a local dev server for manual `?mock=0` testing off the
   filesystem. See dashboard/README.md "Data source". */
const MOCK_OVERRIDE = null; // true | false | null (null = auto-detect)
const MOCK = (function(){
  const forced = new URLSearchParams(location.search).get("mock");
  if (forced === "1") return true;
  if (forced === "0") return false;
  if (MOCK_OVERRIDE !== null) return MOCK_OVERRIDE;
  return location.protocol === "file:";
})();
const API_BASE = (location.protocol === "file:") ? "http://localhost:8000" : "";

/* Slider ranges mirror params/field_params.json rev 13 (css.*_range,
   srp.spm_practice_band — the optimiser's own search band, not the wider
   srp.spm_range — since that is the band an operator would actually dial
   in). Defaults = baseline (b), published-practice, so the console opens
   on the same run the overview and optimiser compare against.
   rev 11/12: two more controls the 6-D physics search optimises --
   stroke_in (discrete API sizes, srp.stroke_in_options) and
   p_wellhead_kgf_cm2 (steam.P_wellhead_range_kgf_cm2, CONFIRMED 85-97).
   rev 13 adds a 7th, categorical control (float_policy) not represented as
   a slider -- see the console's "Rod-float response" selector. */
const RANGES = {
  steam_t:   { min: 500,  max: 3000, step: 50,   default: 1300 },
  soak_days: { min: 3,    max: 15,   step: 1,    default: 10   },
  cutoff:    { min: 0.6,  max: 2.0,  step: 0.05, default: 1.3  },
  spm:       { min: 3,    max: 6,    step: 0.5,  default: 5.0  },
  p_wellhead: { min: 85,  max: 97,   step: 1,    default: 91   }
};
/* Discrete API pumping-unit stroke lengths (srp.stroke_in_options) -- a
   <select>, not a continuous slider; the twin only has a physics model for
   these six sizes (twin/generate_data.py sampled_stroke_options()). */
const STROKE_OPTIONS_IN = [64, 74, 86, 100, 120, 144];
const STROKE_DEFAULT_IN = 86;
/* The twin console's SPM slider intentionally covers the full mechanical
   range (srp.spm_range in field_params.json, 4-12 widened to 3-12 so the
   practice-band floor is included), not just the practice band above — an
   operator needs to be able to dial past the recommended band to see the
   rod-floating alarm fire (the "Try high speed (12 SPM)" stress test).
   RANGES.spm (the practice band) is what the optimiser actually searches
   and what its constraint report bounds-checks against. */
const SPM_SLIDER = { min: 3, max: 12, step: 0.5, default: 5.0 };

/* REAL Baghewala values — params/field_params.json rev 9. Feeds only the
   in-browser mockSimulate() approximation (page-console.js); the baked
   scenarios below are verbatim twin output and do not use these. */
const P = {
  T_initial_C: 50.0, mu_ref_cP: 11500.0, T_ref_C: 50.0,
  T_injection_C: 290.0, steam_injection_rate_tpd: 74.0,
  latent_heat_Jkg: 1.4e6, steam_quality: 0.65,
  stroke_m: 2.18, depth_m: 1150, P_initial_kPa: 11400,
  api_gravity: 15.5, thickness_m: 12.0, porosity: 0.09,
  k_thermal_W_mK: 2.5, rock_heat_capacity_Jm3K: 2.3e6,
  rod_mass_kgm: 3.8, plunger_d_m: 0.0445
};

/* Published-practice baseline (b) — BGW-8 first CSS cycle (Dec 2018),
   docs/research/baghewala_facts.md §4. NOT OIL's current operating
   practice — one documented first-cycle job, used as an external
   reference point (ml/optimize.py PUBLISHED_PRACTICE_BASELINE). This is
   what the console, overview and optimiser all open on and compare
   against — it replaces the old "optimiser midpoint baseline".
   rev 13 (wave 5): run under the VFD-HOLD operating policy — the operator
   slows the unit to hold the float index at 0.6 down to a 2-spm floor,
   pulling only after 3 alarm days there — NOT the rev-12 "pull on first
   alarm" operation, which understated this baseline by ~₹15k/cycle-day
   (TIER1_PROGRESS_LOG.md §12). Still the CONFIRMED BGW-8 wellhead pressure
   (91 kgf/cm2) and the assumed 86-in unit. margin_incremental == net cash
   here (margin_with_opex_inr_per_cycle_day) because the cold counterfactual
   is SHUT IN at the base 45% formation water cut under every float policy
   except "none" (css.cold_counterfactual "policy") — see the Model-basis
   cold-well note. */
const BASELINE_PUBLISHED = { steam_t: 1300, soak_days: 10, cutoff: 1.3, spm: 5.0,
                             stroke_in: 86, p_wellhead_kgf_cm2: 91, float_policy: "vfd_hold",
                             SOR: 3.2878, SOR_incremental: 3.2878,
                             margin_inr_per_cycle_day: 18432.86,
                             margin_incremental_inr_per_cycle_day: 12063.76,
                             margin_incremental_inr_per_cycle_day_fy26: -581.76,
                             margin_incremental_inr_per_cycle_day_levies: -14193.26,
                             /* rev-12 operation (pull on first alarm), same set-points — the
                                "if the baseline pulls" second-line comparison. */
                             margin_incremental_inr_per_cycle_day_pull: -2893.80,
                             margin_incremental_inr_per_cycle_day_none: 12774.10,
                             SOR_pull: 4.35, SOR_none: 3.18,
                             water_cut_start: 0.8709, water_cut_end: 0.5586,
                             produce_end_reason: "float_onset", produce_days: 199 };
/* ml/models/metrics.json, rev 13 retrain (600 LHS cycles incl. a 7th,
   float_policy dimension, seed 42, 80/20 holdout, 6 numeric controls +
   float_policy one-hot). margin_r2/margin_mae is now the NET-CASH regressor
   (margin_with_opex_inr_per_cycle_day, counterfactual-free -- the
   optimiser's actual rev-13 objective); margin_gross_r2/margin_gross_mae is
   the gross regressor, kept for continuity. Both overall and in-envelope
   (1,000-2,000 t) figures are carried, per the metrics.json "truthful"
   convention -- the headline numbers below are the in-envelope ones (the
   operating range the recommendation actually sits in). rev 13: the float
   classifier is retrained on float_premature_pull (the pull happened AND
   the oil rate was still >=1.5x cutoff when it did) -- a healthy ~41%
   positive-class share, replacing the rev-12 label's ~95% imbalance (which
   amounted to penalising the pull rule itself once float response became
   an operating policy, ml/README.md, TIER1_PROGRESS_LOG.md §12.12). */
const SURROGATE  = {
  oil_r2: 0.9946, oil_mae: 8.18, oil_r2_overall: 0.9946, oil_mae_overall: 8.18,
  oil_r2_envelope: 0.9833, oil_mae_envelope: 8.17,
  sor_r2: 0.3739, sor_mae: 0.304,
  /* rev 13: the optimiser's OWN objective is now margin_with_opex_inr_per_cycle_day
     (net cash, counterfactual-free) -- margin_r2/mae below IS that regressor
     (identical numbers to net_cash_r2/mae; the incremental regressor is kept
     for continuity/reporting, ml/models/metrics.json margin_incremental_regressor). */
  margin_r2: 0.9527, margin_mae: 1205, margin_r2_overall: 0.9372, margin_mae_overall: 1524,
  net_cash_r2: 0.9527, net_cash_mae: 1205, net_cash_r2_overall: 0.9372, net_cash_mae_overall: 1524,
  margin_gross_r2: 0.9349, margin_gross_mae: 1283, margin_gross_r2_overall: 0.9413, margin_gross_mae_overall: 1522,
  float_auc: 0.9994, float_acc: 0.9817, floatPositiveShare: 0.4133,
  n: 600, calls: 60, floatLimit: 0.30
};
const TWIN_VERSION = "twin v1.0 (physics rev 13)";
const PARAMS_REV = "params/field_params.json rev 13";
/* rev 13.1 (item 7): the footer's physics-rev/date used to be hand-typed
   text in footer.html, which is exactly how it went stale ("physics rev 12
   · 27 Sep 2026" surviving into the rev-13 build). These are now the ONE
   place both live -- bump PHYSICS_REV_SHORT alongside TWIN_VERSION on every
   re-bake, and BUILD_DATE on every rebuild -- and bootChrome() below writes
   them into the footer's #footPhysicsRev/#footBuildDate spans on every page
   load, so the footer can no longer disagree with these constants. */
const PHYSICS_REV_SHORT = "rev 13";
const BUILD_DATE = "26 Sep 2026";
const RISK_LIMIT = 0.60;
const M3_TO_BBL = 6.2898;
const ROD_HANG_KN = 43;

/* Canonical baked results (full series live in console.html only).
   reference = baseline (b) published-practice; optimized = the rev 13
   cascade recommendation (6-D: 5 controls + float policy; minimax-regret
   across pull/vfd_hold/vfd_then_pull and both price decks, soak fixed at
   10 d field practice, injection margin >= 400 kPa). Both now run under the
   VFD-HOLD operating policy, so they are a FAIR, same-policy comparison —
   docs/model-improvement/TIER1_PROGRESS_LOG.md §12, params/CHANGELOG.md
   rev 13. margin_inr_per_cycle_day is GROSS (headline SOR convention, steam
   over ALL oil); margin_with_opex_inr_per_cycle_day is NET CASH per cycle-day
   (counterfactual-free — this is the optimiser's actual rev-13 objective);
   margin_incremental_inr_per_cycle_day nets out the cold-well counterfactual
   (== net cash here, since the cold well is SHUT IN at the base 45% water
   cut under the "policy" convention — see the Model-basis cold-well note). */
const REF_SUMMARY = {"oil_total_m3":395.407,"SOR_t_per_m3":3.2878,"energy_per_m3_kWh":55.3408,"days_total":225.5676,"max_floating_index":0.6198,"failures_expected":3,"rod_float_damage_index":15.9149,"days_rods_in_compression":0,"min_fillage":0.85,"mean_fillage":0.85,"descent_violation_days":0,"mean_spm":4.3868,"min_spm":2.0,"max_spm":5.0,"pump_limited_days":0,"oil_bbl":2487.0347,"peak_oil_m3d":2.3243,"peak_oil_bbl_d":14.6192,"steam_cost_inr":9244456.6265,"cost_inr_per_bbl":3717.0598,"co2_t":290.9166,"co2_kg_per_bbl":116.9733,"revenue_inr":14902311.922,"margin_inr":4157855.2955,"margin_inr_per_cycle_day":18432.8596,"bl_uncertainty_frac":0.42,"window_days":226.5676,"electric_kWh":36470.2284,"electric_kWh_per_m3":92.2347,"power_cost_inr":291761.8269,"opex_fixed_inr":1132837.8378,"opex_inr":1424599.6647,"margin_with_opex_inr":2733255.6308,"margin_with_opex_inr_per_cycle_day":12063.755,"cold_rate_m3d":0.445,"cold_counterfactual_rate_m3d":0.0,"cold_well_economic":false,"oil_cold_baseline_m3":0.0,"oil_incremental_m3":395.407,"oil_incremental_bbl":2487.0347,"SOR_incremental":3.2878,"margin_incremental_inr":2733255.6308,"margin_incremental_inr_per_cycle_day":12063.755,"margin_incremental_inr_per_t_steam":2102.5043,"water_cut_start":0.8709,"water_cut_end":0.5586,"water_cut_liquid_weighted":0.7467,"water_total_m3":1165.4579,"condensate_produced_m3":841.9431,"max_floating_index_produce_day":198,"max_floating_index_cycle_day":225.5676,"water_cut_at_max_floating_index":0.5586,"first_float_alarm_produce_day":196,"max_peak_prl_kN":91.4205,"produce_days":199,"peak_oil_produce_day":0,"produce_end_days_after_peak":198,"max_prl_kN":113.9,"prl_cap_exceeded_days":0,"water_cut_model":"state","stroke_m":2.1844,"P_wellhead_kgf_cm2":91,"T_wellhead_C":303.5489,"P_sandface_kPa":10121.1428,"T_sandface_C":311.8859,"steam_fuel_factor":1.0,"cold_water_cut":0.45,"cold_floating_index":1,"cold_peak_prl_kN":189.4032,"cold_mu_drag_cP":51261.2233,"produce_end_rule":"either","produce_end_reason":"float_onset","fi_alarm_days_rule":3,"float_policy":"vfd_hold","cold_counterfactual":"policy","cold_status":"shut_in_float","injection_margin_kPa":721.1428,"min_injection_margin_kPa":400,"injection_ok":true,"days_at_schedule_floor":3,"days_vfd_slowed":62};
const REF_INPUTS  = { steam_t:1300, soak_days:10, cutoff:1.3, spm:5.0, stroke_in:86, p_wellhead_kgf_cm2:91, float_policy:"vfd_hold" };
const OPT_SUMMARY = {"oil_total_m3":353.1806,"SOR_t_per_m3":2.8314,"energy_per_m3_kWh":47.9357,"days_total":218.5135,"max_floating_index":0.6217,"failures_expected":3,"rod_float_damage_index":15.9917,"days_rods_in_compression":0,"min_fillage":0.85,"mean_fillage":0.85,"descent_violation_days":0,"mean_spm":4.0641,"min_spm":2.0,"max_spm":4.5,"pump_limited_days":14,"oil_bbl":2221.439,"peak_oil_m3d":2.1407,"peak_oil_bbl_d":13.4648,"steam_cost_inr":7108019.215,"cost_inr_per_bbl":3199.7364,"co2_t":223.6844,"co2_kg_per_bbl":100.6935,"revenue_inr":13310862.41,"margin_inr":4702843.1949,"margin_inr_per_cycle_day":21521.9788,"bl_uncertainty_frac":0.42,"window_days":219.5135,"electric_kWh":28216.5878,"electric_kWh_per_m3":79.8928,"power_cost_inr":225732.7021,"opex_fixed_inr":1097567.5676,"opex_inr":1323300.2697,"margin_with_opex_inr":3379542.9252,"margin_with_opex_inr_per_cycle_day":15395.6031,"cold_rate_m3d":0.445,"cold_counterfactual_rate_m3d":0.0,"cold_well_economic":false,"oil_cold_baseline_m3":0.0,"oil_incremental_m3":353.1806,"oil_incremental_bbl":2221.439,"SOR_incremental":2.8314,"margin_incremental_inr":3379542.9252,"margin_incremental_inr_per_cycle_day":15395.6031,"margin_incremental_inr_per_t_steam":3379.5429,"water_cut_start":0.8688,"water_cut_end":0.5293,"water_cut_liquid_weighted":0.7295,"water_total_m3":952.3772,"condensate_produced_m3":663.4113,"max_floating_index_produce_day":195,"max_floating_index_cycle_day":218.5135,"water_cut_at_max_floating_index":0.5293,"first_float_alarm_produce_day":193,"max_peak_prl_kN":91.2538,"produce_days":196,"peak_oil_produce_day":14,"produce_end_days_after_peak":181,"max_prl_kN":113.9,"prl_cap_exceeded_days":0,"water_cut_model":"state","stroke_m":1.6256,"P_wellhead_kgf_cm2":89,"T_wellhead_C":301.9753,"P_sandface_kPa":9898.397,"T_sandface_C":310.2497,"steam_fuel_factor":0.9996,"cold_water_cut":0.45,"cold_floating_index":1,"cold_peak_prl_kN":189.4032,"cold_mu_drag_cP":51261.2233,"produce_end_rule":"either","produce_end_reason":"float_onset","fi_alarm_days_rule":3,"float_policy":"vfd_hold","cold_counterfactual":"policy","cold_status":"shut_in_float","injection_margin_kPa":498.397,"min_injection_margin_kPa":400,"injection_ok":true,"days_at_schedule_floor":3,"days_vfd_slowed":58};
/* rev 13: the recommendation's net cash (== incremental, shut-in cf) at the
   $65 FY26-floor deck and the net-of-royalty-and-cess deck ("Your prices"
   presets 2 and 3) -- baked once here since it needs the SAME econ re-run as
   OPT_SUMMARY above (params/field_params.json economics.oil_price_presets),
   not the in-browser re-pricer. */
const OPT_SUMMARY_FY26_INCREMENTAL = 3737.56;
const OPT_SUMMARY_LEVIES_INCREMENTAL = -8811.03;
const CONSERVATIVE_SUMMARY = {"oil_total_m3":339.2053,"SOR_t_per_m3":2.9481,"energy_per_m3_kWh":40.6866,"days_total":206.5135,"max_floating_index":0.5223,"failures_expected":0,"margin_inr_per_cycle_day":20222.0871,"window_days":207.5135,"margin_with_opex_inr_per_cycle_day":14237.8769,"cold_rate_m3d":0.445,"oil_incremental_m3":339.2053,"SOR_incremental":2.9481,"margin_incremental_inr_per_cycle_day":14237.8769,"water_cut_start":0.8688,"water_cut_end":0.5376,"produce_days":184,"produce_end_reason":"float_onset","max_peak_prl_kN":85.3851};
const CONSERVATIVE_SUMMARY_FY26_INCREMENTAL = 2393.66;
const CONSERVATIVE_SUMMARY_LEVIES_INCREMENTAL = -10355.32;
/* rev 13 (wave 5): "conservative" = the SAME 6-D recommendation, VFD-hold,
   operated with the hold-and-pull line at floating_index > 0.5 instead of
   0.6 (still 3 consecutive alarm days at the floor) -- NOT a different
   set-point, and not "never alarm" (that fixed-cutoff reading is the
   fragile rule wave 4 removed; see TIER1_PROGRESS_LOG.md §11.9 item 5). */
const CONSERVATIVE = { steam_t:1000, soak_days:10, cutoff:0.60, spm:4.5, stroke_in:64, p_wellhead_kgf_cm2:89, float_policy:"vfd_hold", fi_alarm:0.5 };
/* rev 13: the 6-D cascade recommendation (minimax-regret across pull /
   vfd_hold / vfd_then_pull and both price decks) -- 1,000 t is a multiple of
   50, 0.60 m³/d backstop cutoff, a stock API stroke, 89 kgf/cm2 (the
   injection-margin gate rejects 85), 4.5 spm start under VFD-HOLD. It
   replaces the rev-12 1,000/0.60/3/64/85 (pull) point.
   The operating rule (not just a set-point): a variable-speed drive slows
   the unit to hold the float index at 0.6, down to a 2-spm floor, and pulls
   only after the float alarm has persisted 3 consecutive days AT that floor
   — not on the first alarm. The 0.60 m³/d cutoff is a rate backstop that
   never actually binds first. */
const OPT_APPLIED = { steam_t:1000, soak_days:10, cutoff:0.60, spm:4.5, stroke_in:64, p_wellhead_kgf_cm2:89, float_policy:"vfd_hold" };
/* rev 13 (wave 5): the CANONICAL recommendation is a true-physics 6-D grid
   search (5 controls + float policy; ml/recommend_physics.py /
   ml/models/gain_decomposition.json "optimiser" -- 160,776 grid points,
   12,936 simulations under the injectivity/PRL/float-feasibility gates),
   minimax-regret across the FY25 and FY26-floor decks, over the policies
   pull / vfd_hold / vfd_then_pull. It replaces the rev-12 1,000/0.60/3/64/85
   (pull) point. The retrained ML surrogate (ml/train.py, 600-row LHS incl.
   float_policy one-hot, ml/models/metrics.json physics_rev 13) is an
   emulator for UQ/what-if speed, not the decision engine -- see
   ml/README.md "the physics grid is the decision engine". OPT_RESULT
   reports the physics-verified numbers AT the canonical point, the
   gross/net-cash/incremental SOR and margin the optimiser page needs, the
   Shapley gain decomposition vs baseline (b) UNDER EACH baseline operating
   policy (the fair-gain block wave 5 added), and the surrogate's own
   prediction at that same point for the residual/honesty note. */
const OPT_RESULT = {
  steam_t:1000, soak_days:10, cutoff_m3d:0.60, spm:4.5, stroke_in:64, p_wellhead_kgf_cm2:89, float_policy:"vfd_hold",
  /* surrogate predictions AT the canonical point (oil/margin/float models,
     ml/models/*.joblib, retrained rev 13 incl. float_policy one-hot) -- what
     the "Predicted outcome" row shows; the twin re-run (OPT_SUMMARY) is the
     number quoted everywhere else. margin_net_cash_inr_per_cycle_day is the
     model's actual rev-13 training target (== incremental at this point). */
  predicted_SOR:2.9404, predicted_margin_inr_per_cycle_day:21166.71,
  predicted_margin_net_cash_inr_per_cycle_day:14862.49,
  predicted_margin_incremental_inr_per_cycle_day:14862.49,
  floating_probability:0.9131,
  floating_probability_note:"P(float_premature_pull) -- the VFD-hold policy IS the float response by design, so a high value here describes the mechanism, not a risk to avoid (TIER1_PROGRESS_LOG.md §12.12).",
  residual_inr_per_cycle_day:533.11,
  baseline_SOR:3.2878, baseline_margin_inr_per_cycle_day:18432.86,
  baseline_margin_incremental_inr_per_cycle_day:12063.76,
  baseline_SOR_incremental:3.2878,
  SOR_incremental:2.8314,
  SOR_improvement_pct:-13.88,
  margin_improvement_pct:16.76,
  /* rev 13: the headline delta is now the SAME-POLICY (VFD-hold) gain --
     the fair comparison (TIER1_PROGRESS_LOG.md §12.6). The old rev-12
     "+Rs9,574" figure mixed a pulling baseline against a VFD-hold-adjacent
     rec; 68% of that number was the operating-rule switch, not the
     set-point (see fairGain.pull below). */
  margin_incremental_inr_per_cycle_day_delta:3331.85,
  margin_incremental_inr_per_cycle_day_delta_fy26:4319.34,
  margin_incremental_inr_per_cycle_day_delta_levies:5382.24,
  margin_incremental_pct_change_note:"the fair (same-policy) gain is a modest, operational ~5% of the recommendation's own gross revenue per day -- see the baseline-policy toggle for what changes if the baseline is instead operated differently.",
  /* THE FAIR-GAIN BLOCK (wave 5): the SAME canonical (VFD-hold) recommendation
     vs baseline (b) operated under each of three assumptions about what the
     baseline DOES about rod float -- "Compare against a baseline that..."
     toggle reads this. Net cash == incremental here (shut-in cold cf).
     ml/models/gain_decomposition.json decomposition_to_canonical_rec_by_
     baseline_policy (vfd_hold/none) and decomposition_rev12_rec_vs_baseline_
     pull (pull, historical rev-12 comparison point). */
  fairGain: {
    vfd_hold: { fy25:3331.85, fy26:4319.34, levies:5382.24,
                baseline_fy25:12063.76, baseline_fy26:-581.76, baseline_levies:-14193.26,
                note:"the fair comparison: our assumed baseline, run the SAME way (VFD-hold) — but 84-96% of scenarios and ~87% of this gain trace to the baseline's own 1.3 m³/d cutoff and 2-spm VFD floor, not new physics." },
    pull:     { fy25:12917, fy26:14694, levies:16606,
                baseline_fy25:-2893.80, baseline_fy26:-15812.22, baseline_levies:-29717.53,
                note:"if the baseline is instead pulled at the first alarm -- 68% of this gain is the operating-rule switch, not the set-point (Shapley, §12.6)." },
    /* rev 13.1 (re-score N2/item 5): FIXED -- these three numbers were the
       "best rec within that policy" row of TIER1_PROGRESS_LOG.md §12.6, a
       DIFFERENT, more radical float-safe plan (1,000/89/1.45/64/3, "none")
       compared against a baseline that also does nothing. That is not what
       this toggle is for: the toggle asks "what if the SAME canonical
       recommendation (1,000/89/0.60/64/4.5, VFD-hold, the one on the card
       and staged into the console) faced a baseline that does nothing about
       float" -- the "mixed" row of §12.6, +2,622/+3,484/+4,413. The −3,865
       figure must not appear on this dashboard; it belongs to that other
       plan and was never the canonical recommendation's number. */
    none:     { fy25:2621.54, fy26:3484.11, levies:4412.56,
                baseline_fy25:12774.10, baseline_fy26:253.51, baseline_levies:-13223.62,
                note:"if the baseline's rods are simply left floating (no response) -- the recommendation still gains here, mostly from ordinary steam and cutoff savings, because we do not price rod failures; a plan actually built to avoid floating rods would instead lose money against this baseline (TIER1_PROGRESS_LOG.md §12.6)." }
  },
  /* Shapley decomposition of the SAME-POLICY (VFD-hold) gain vs baseline (b),
     120 orderings, ml/models/gain_decomposition.json
     decomposition_to_canonical_rec_by_baseline_policy.vfd_hold. Stroke is now
     the dominant lever (a shorter stroke lets the VFD hold the float line
     longer at the 2-spm floor); cutoff is interaction (with the 64-in
     stroke, the baseline's 1.3 m3/d cutoff would bind before the float pull
     under a naive OAT read); SPM is no longer a lever once the VFD does the
     slowing (TIER1_PROGRESS_LOG.md §12.6). */
  decomposition: {
    fy25: { stroke_in:1906.58, cutoff_m3d:985.83, steam_t:354.22, p_wellhead_kgf_cm2:49.41, spm:35.81 },
    fy25_share: { stroke_in:0.5722, cutoff_m3d:0.2959, steam_t:0.1063, p_wellhead_kgf_cm2:0.0148, spm:0.0107 },
    fy26: { stroke_in:2178.34, cutoff_m3d:1112.30, steam_t:890.86, p_wellhead_kgf_cm2:64.05, spm:73.44 },
    fy26_share: { stroke_in:0.5043, cutoff_m3d:0.2575, steam_t:0.2064, p_wellhead_kgf_cm2:0.0149, spm:0.0170 },
    levies: { stroke_in:2470.13, cutoff_m3d:1248.63, steam_t:1470.28, p_wellhead_kgf_cm2:80.36, spm:113.55 },
    levies_share: { stroke_in:0.4590, cutoff_m3d:0.2320, steam_t:0.2731, p_wellhead_kgf_cm2:0.0149, spm:0.0211 }
  },
  /* Baseline-lever sensitivity (OIL's real spm/stroke are unknown) -- NOT
     re-run this wave against the VFD-hold baseline (TIER1_PROGRESS_LOG.md
     §12.15 "not done / open"); these are the rev-12 (pulling-baseline)
     figures, kept only as a rough shape indicator, and labelled as such on
     the page rather than silently re-used. */
  baselineSpmSensitivity_rev12_pull_baseline:
    [ { spm:4, improvement:6076.79 }, { spm:5, improvement:9573.91 }, { spm:6, improvement:12653.95 } ],
  baselineStrokeSensitivity_rev12_pull_baseline:
    [ { stroke_in:74, improvement:7197.14 }, { stroke_in:86, improvement:9573.91 }, { stroke_in:100, improvement:12232.44 } ]
};

/* Uncertainty quantification -- ml/uq.py, paired Monte Carlo over the twin's
   uncertain inputs (21 inputs incl. formation water cut, net-pay thickness,
   diesel discount, oil price, mu_ref_cP, cold-well skin s_cold, condensate
   recovery, flowback mobility ratio M, the cold counterfactual convention),
   1,500 draws, seed 42, run through the TRUE physics twin at the reference,
   baseline (b) and recommended set-points (plus the same-policy pull/none
   variants), paired per draw. Baked from ml/models/uq_summary.json (rev 13,
   wave 5) -- re-run `python ml/uq.py` after any physics/economics change and
   re-paste here.
   THREE price decks (ml/models/uq_summary.json .decks): fy25_realisation
   (base case), fy26_floor ("$65" preset), fy25_net_of_levies ("levies").
   money_metric is margin_with_opex_inr_per_cycle_day (NET CASH per
   cycle-day, counterfactual-free) -- ml/uq.py's gain_vs_baseline_bands.metric;
   the *_incremental_* fields net out the cold-well counterfactual under the
   default "policy" convention (shut in at the base 45% water cut).
   ---- THE RESOLVED COUNTERFACTUAL STATISTIC (wave 5) ----
   An earlier draft printed "P(incremental margin/day > 0) = 0.034" right next
   to the FY25 net-cash p50 of +Rs1,132/day -- inconsistent on its face (p50
   near zero implies roughly half the draws are positive, not 3.4%). Computed
   directly from ml/models/uq_samples.csv (1,500 draws) at the recommended
   point:
     FY25:    P(net cash > 0) = 0.537   P(incremental > 0, vs shut-in cf) = 0.377
     $65:     P(net cash > 0) = 0.252   P(incremental > 0, vs shut-in cf) = 0.167
     levies:  P(net cash > 0) = 0.034   P(incremental > 0, vs shut-in cf) = 0.018
   The 0.034 in the original draft was the NET-OF-LEVIES deck's P(net cash>0)
   figure, mis-paired against the FY25 rupee line AND against the wrong
   metric (net cash, not incremental) -- the same species of deck-mixing bug
   rev 12's headline had (dashboard/README.md §7.2). Column definitions:
     net cash        = margin_with_opex_inr_per_cycle_day: revenue - steam
                        cost - fixed workover cost - power cost - opex, per
                        cycle-day. NO cold-well counterfactual is subtracted;
                        this is "positive cash vs a SHUT-IN cold well".
     incremental      = margin_incremental_inr_per_cycle_day: net cash MINUS
                        the cold well's own cash for the same window (0 if
                        the policy convention shuts it in, which it does at
                        every draw where the cold well's floating index
                        exceeds the alarm line under its own float policy).
   Convention adopted here: **P(net cash > 0)** is quoted everywhere on the
   dashboard as "positive cash vs a shut-in cold well" (pNetCashPositive,
   always labelled as such); **P(recommended > baseline, SAME policy)** is
   the robust headline (it is a PAIRED comparison, so the shared uncertainty
   cancels -- see below). P(incremental > 0) is shown alongside as a stricter,
   unpaired reading, never as the headline. */
const UQ = {
  nDraws: 1500, seed: 42,
  /* Paired: P(recommended net cash/day > baseline (b) net cash/day), SAME
     float policy on both sides. This is the number that should be quoted as
     "better in N% of scenarios" -- ml/uq.py P_gt_baseline_same_policy. */
  pRecommendedSorLtBaseline: 1.00,
  decks: {
    fy25_realisation: {
      label: "OIL FY25 realisation ($78.09/bbl − $10 discount = ₹5,992/bbl)",
      recommended: { netCash_p10:-14757, netCash_p50:1132, netCash_p90:16962,
                     incremental_p10:-18913, incremental_p50:-3491, incremental_p90:12597,
                     pNetCashPositive: 0.537, pIncrementalPositive: 0.377 },
      baseline_b:  { netCash_p10:-170853, netCash_p50:-13524, netCash_p90:13792,
                     incremental_p10:-177516, incremental_p50:-18020, incremental_p90:8758,
                     pNetCashPositive: 0.288 },
      pGtBaselineSamePolicy: { vfd_hold: 0.9653, pull: 0.9527, none: 0.1647 },
      gain_p10: 2175, gain_p50: 12101, gain_p90: 161014,
      pInjectable: 1.0
    },
    fy26_floor: {
      label: "FY26 planning floor ($65/bbl = ₹4,840/bbl)",
      recommended: { netCash_p10:-20830, netCash_p50:-6940, netCash_p90:6530,
                     incremental_p10:-23929, incremental_p50:-10382, incremental_p90:3104,
                     pNetCashPositive: 0.252, pIncrementalPositive: 0.167 },
      baseline_b:  { netCash_p10:-174422, netCash_p50:-22751, netCash_p90:973,
                     incremental_p10:-178261, incremental_p50:-26176, incremental_p90:-2633,
                     pNetCashPositive: null },
      pGtBaselineSamePolicy: { vfd_hold: 0.992, pull: 0.9847, none: 0.176 },
      gain_p10: 3597, gain_p50: 13390, gain_p90: 158528,
      pInjectable: 1.0
    },
    fy25_net_of_levies: {
      label: "FY25 net of royalty + OID cess (~₹3,600/bbl)",
      recommended: { netCash_p10:-27812, netCash_p50:-15621, netCash_p90:-4547,
                     incremental_p10:-29309, incremental_p50:-17610, incremental_p90:-6730,
                     pNetCashPositive: 0.034, pIncrementalPositive: 0.018 },
      baseline_b:  { netCash_p10:-177452, netCash_p50:-32896, netCash_p90:-12564,
                     incremental_p10:-179339, incremental_p50:-34681, incremental_p90:-14728,
                     pNetCashPositive: null },
      pGtBaselineSamePolicy: { vfd_hold: 0.9993, pull: 1.0, none: 0.2473 },
      gain_p10: 5256, gain_p50: 14805, gain_p90: 155230,
      pInjectable: 1.0
    }
  },
  /* Top-3 by one-at-a-time swing on the recommendation's net cash/cycle-day
     (ml/uq.py oat_tornado(): hold every OTHER input at its base value, sweep
     just this one from low to high), FY25 deck, 1,500-draw bake. mu_ref_cP
     (the cold heavy-oil viscosity) is now #1 -- it sets how hard the cold
     well is to beat AND how much the produce phase itself yields; s_cold
     (the cold well's skin factor) is #2. */
  topDrivers: [
    { en: "Cold heavy-oil viscosity (mu_ref_cP)",
      hi: "ठंडे भारी तेल की श्यानता (mu_ref_cP)",
      swing: -29482, atLow: 32595, atHigh: 3112, corr: -0.324 },
    { en: "Cold-well skin factor (s_cold)",
      hi: "ठंडे कूप का त्वचा गुणांक (skin, s_cold)",
      swing: 26850, atLow: -2941, atHigh: 23908, corr: 0.397 },
    { en: "Oil price",
      hi: "तेल मूल्य",
      swing: 18191, atLow: 6300, atHigh: 24491, corr: 0.260 }
  ]
};
/* =========================================================================
   CALIBRATION DEMO — twin/calibrate.py's ingest -> recalibrate -> re-
   recommend loop, baked verbatim from ml/models/calibration_demo_report.json
   (regenerate: `python -m twin.generate_pseudo_real` then
   `python -m twin.calibrate data/external/pseudo_real_cycles.csv --out
   ml/models/calibrated_params.json --report
   ml/models/calibration_demo_report.json`, both deterministic, seed 42 —
   see dashboard/README.md §"Calibrate from field data").
   The demo dataset (data/external/pseudo_real_cycles.csv, 8 cycles, 3
   FICTIONAL wells BGW-D1..D3) is SYNTHETIC — generated by running the twin's
   own physics against a hidden "true" params set, +/-8% multiplicative
   noise, seed 42. It is NOT Oil India field data (data/external/SOURCE.md).
   CALIB_DEFAULTS are the twin's current module-constant values for the four
   parameters twin/calibrate.py fits (ml/README.md §"Calibrate from field
   data") — the "before" column applies to ANY calibration run, demo or a
   real upload, since they are the fixed starting point every fit begins
   from, not something the fit result reports back. */
/* rev 9: bl_delta_factor is SOURCED physics (physics v3, CHANGELOG rev 7 --
   the 1/2 in Boberg & Lantz's own delta), no longer a free calibration
   knob -- twin/calibrate.py's DEFAULT_FREE is now (water_cut, aof_ref_m3d,
   thickness_m). It is kept here only as the fixed "before" value the fit
   starts from (and the demo's hidden truth), not as something fit() varies. */
const CALIB_DEFAULTS = { bl_delta_factor: 0.5, formation_water_cut: 0.45, thickness_m: 12.0, aof_ref_m3d: 0.56 };
const CALIB_DEMO = {
  date: "27 Sep 2026",
  nCycles: 8, nWells: 3,
  wells: ["BGW-D1", "BGW-D2", "BGW-D3"],
  /* rev 12: the hidden-truth key formerly called "water_cut" is now
     "formation_water_cut" -- the free parameter the water-cut STATE model
     (fluid.water_cut_model = "state") actually reads (see Model basis, the
     Formation water cut param row). aof_ref_m3d truth moved to 0.65, clear
     of the retuned base 0.56 (was 0.46). */
  hiddenTruth: { bl_delta_factor: 0.5, formation_water_cut: 0.38, thickness_m: 15.0, aof_ref_m3d: 0.65 },
  /* bl_delta_factor is fixed at 0.5 (not fitted -- see fitted.bl_delta_factor
     note below); the three FREE parameters below are recovered from 8
     synthetic cycles, seed 42. */
  fitted: { bl_delta_factor: 0.5, formation_water_cut: 0.3602099485999942,
            thickness_m: 13.371872885725733, aof_ref_m3d: 0.6439776531534391 },
  fittedIsFixed: { bl_delta_factor: true, formation_water_cut: false, thickness_m: false, aof_ref_m3d: false },
  bounds: { formation_water_cut: [0.3, 0.6], aof_ref_m3d: [0.3, 0.9], thickness_m: [8.0, 20.0] },
  rmse: { oil_m3_pct: 2.945306647399237, produce_days_pct: 4.795748544336921, peak_oil_m3d_pct: 5.659938230903442 },
  identifiability: {
    /* rev 12: with bl fixed, formation_water_cut is identified ALONE even
       though its Jacobian-implied correlation against aof_ref_m3d/
       thickness_m stays high (0.97-0.999) -- high correlation here means
       "the data move these together", not "unrecoverable"; see the
       plain-language note the page prints alongside this table.
       aof_ref_m3d vs thickness_m is the genuinely weak split (thickness_m
       recovered only to -10.9%, the least-identified of the three). */
    correlatedPairs: [
      { params: ["formation_water_cut", "aof_ref_m3d"], correlation: 0.9773503689576066 },
      { params: ["formation_water_cut", "thickness_m"], correlation: 0.9704797524177656 },
      { params: ["aof_ref_m3d", "thickness_m"], correlation: 0.998718361701895 }
    ],
    /* No known_couplings as of rev 9 -- that field only appears when
       bl_delta_factor is opted back into `free` (twin/calibrate.py), which
       this demo does not do (see fitted.bl_delta_factor above). */
    knownCouplings: []
  },
  /* per-cycle residual table -- obs vs FITTED (post-calibration) twin output,
     the same table the chart below plots. */
  residualTable: [
    { well_id: "BGW-D1", steam_t: 1200.0, soak_days: 7.0, cutoff_m3d: 0.9, spm: 4.5,
      obs_oil_m3: 396.47, sim_oil_m3: 388.6368438333205, oil_pct_error: -1.9757248131458984 },
    { well_id: "BGW-D1", steam_t: 1500.0, soak_days: 10.0, cutoff_m3d: 0.85, spm: 5.0,
      obs_oil_m3: 443.93, sim_oil_m3: 435.8545399365775, oil_pct_error: -1.8190841041205814 },
    { well_id: "BGW-D1", steam_t: 1800.0, soak_days: 12.0, cutoff_m3d: 0.75, spm: 5.5,
      obs_oil_m3: 486.38, sim_oil_m3: 470.69580337047904, oil_pct_error: -3.224679598158015 },
    { well_id: "BGW-D2", steam_t: 1000.0, soak_days: 8.0, cutoff_m3d: 1.0, spm: 4.0,
      obs_oil_m3: 341.12, sim_oil_m3: 353.82936336488774, oil_pct_error: 3.725774907624219 },
    { well_id: "BGW-D2", steam_t: 1600.0, soak_days: 9.0, cutoff_m3d: 0.8, spm: 5.0,
      obs_oil_m3: 461.08, sim_oil_m3: 454.27359115369643, oil_pct_error: -1.47618826370772 },
    { well_id: "BGW-D2", steam_t: 2000.0, soak_days: 11.0, cutoff_m3d: 0.7, spm: 5.5,
      obs_oil_m3: 478.74, sim_oil_m3: 500.10606057796895, oil_pct_error: 4.462977937496123 },
    { well_id: "BGW-D3", steam_t: 1300.0, soak_days: 10.0, cutoff_m3d: 0.9, spm: 4.5,
      obs_oil_m3: 424.81, sim_oil_m3: 412.6401312143182, oil_pct_error: -2.8647792626543125 },
    { well_id: "BGW-D3", steam_t: 1900.0, soak_days: 13.0, cutoff_m3d: 0.75, spm: 6.0,
      obs_oil_m3: 451.22, sim_oil_m3: 463.66080984292705, oil_pct_error: 2.7571494709735878 }
  ],
  /* recommendation before/after -- ml/recommend_physics.py grid search
     (steam_t x cutoff_m3d x spm, 15x15x7, soak_days fixed at 10 d) directly
     on the twin, no ML surrogate, physics rev 12 (float-onset produce-end
     rule). Objective = margin_incremental_inr_per_cycle_day; the pseudo-real
     hidden truth (thicker pay, lower formation water cut, higher AOF) makes
     the well far more productive, so both before/after are interior points
     (cutoff/spm pinned at their lower bound, not steam_t at the upper bound
     as in the rev-9 demo -- pinned_variables in the raw report). */
  before: { steam_t: 857.1428571428571, soak_days: 10.0, cutoff_m3d: 0.6, spm: 3.0,
            SOR_t_per_m3: 3.3046858614124788, oil_total_m3: 259.3719624462277,
            days_total: 158.58301158301157, margin_inr_per_cycle_day: 20530.17208746202,
            margin_incremental_inr_per_cycle_day: 6271.639455215083,
            max_floating_index: 0.6249977391656664 },
  after:  { steam_t: 1392.857142857143, soak_days: 10.0, cutoff_m3d: 0.6, spm: 3.0,
            SOR_t_per_m3: 2.820025861690722, oil_total_m3: 493.9164430293797,
            days_total: 250.82239382239382, margin_inr_per_cycle_day: 35714.98038923427,
            margin_incremental_inr_per_cycle_day: 18060.50073507427,
            max_floating_index: 0.6148530594073899, pinnedSteamAtUpperBound: false }
};

/* Field-level steam scheduler demo (rev 12, physics wave 4, 27 Sep 2026) --
   baked output of `python -m ml.schedule --wells
   data/external/field_wells_synthetic.csv --out
   ml/models/field_schedule_demo.json` (seed 42, 12 SYNTHETIC wells,
   data/external/SOURCE.md; NOT real Baghewala per-well data). Live mode
   re-fetches the same shape from GET /api/schedule/demo. `jobs` here is
   the EXACT (bitmask-subset x ERD-order) schedule only -- the greedy and
   naive policies are summarised as comparison KPIs, not shown as separate
   Gantts, to keep this page's one new section simple.
   rev 12: under the float-onset produce-end rule the NAIVE (no per-well
   tuning, fixed 1,500 t / 1.3 m³/d / 5 spm / 86 in / 91 kgf/cm² for every
   well) policy now LOSES money field-wide (fieldMarginInrPerDay negative,
   -₹13.3k/d) -- greedy/exact (which tune per well) turn it profitable
   (+₹42.3k/d / +₹46.6k/d). Say so; do not silently show only the upside.
   See ml/schedule.py and ml/README.md section "Field-level steam
   scheduling". */
const FIELD_SCHEDULE_DEMO = {"generatedAt":"2026-09-26","nWells":12,"horizonDays":365,"generatorRateTpd":74,"minRecycleDays":180,"moveDays":1,"exact":{"fieldMarginInrTotal":17018614,"fieldMarginInrPerDay":46626.3,"generatorUtilisationPct":52.4,"steamTTotal":13500,"co2TTotal":3021.1,"nWellsServed":9,"nWellsDeferred":3,"jobs":[{"order":1,"well":"BGW-S03","start":"2026-10-01","end":"2026-10-22","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":749.6,"cycleDays":235.3},{"order":2,"well":"BGW-S04","start":"2026-10-22","end":"2026-11-12","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":7773.4,"cycleDays":229.3},{"order":3,"well":"BGW-S09","start":"2026-11-12","end":"2026-12-03","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":8298.5,"cycleDays":242.3},{"order":4,"well":"BGW-S11","start":"2026-12-03","end":"2026-12-25","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":8177.9,"cycleDays":232.3},{"order":5,"well":"BGW-S08","start":"2026-12-25","end":"2027-01-15","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":16788.3,"cycleDays":242.3},{"order":6,"well":"BGW-S12","start":"2027-01-15","end":"2027-02-05","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":1040.9,"cycleDays":241.3},{"order":7,"well":"BGW-S05","start":"2027-02-05","end":"2027-02-26","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":12719.3,"cycleDays":244.3},{"order":8,"well":"BGW-S10","start":"2027-02-26","end":"2027-03-20","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":1391.7,"cycleDays":235.3},{"order":9,"well":"BGW-S01","start":"2027-03-20","end":"2027-04-10","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":14258.1,"cycleDays":238.3}],"deferred":[{"well":"BGW-S02","reason":"generatorCommitted"},{"well":"BGW-S06","reason":"generatorCommitted"},{"well":"BGW-S07","reason":"generatorCommitted"}]},"greedy":{"fieldMarginInrTotal":15430910,"fieldMarginInrPerDay":42276.5,"generatorUtilisationPct":68.1,"steamTTotal":17500,"co2TTotal":3916.2,"nWellsServed":12,"nWellsDeferred":0,"jobs":[{"order":1,"well":"BGW-S08","start":"2026-10-07","end":"2026-10-28","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":16788.3,"cycleDays":242.3},{"order":2,"well":"BGW-S01","start":"2027-01-24","end":"2027-02-14","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":14258.1,"cycleDays":238.3},{"order":3,"well":"BGW-S05","start":"2027-02-14","end":"2027-03-07","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":12719.3,"cycleDays":244.3},{"order":4,"well":"BGW-S09","start":"2027-03-07","end":"2027-03-28","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":8298.5,"cycleDays":242.3},{"order":5,"well":"BGW-S11","start":"2027-03-28","end":"2027-04-19","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":8177.9,"cycleDays":232.3},{"order":6,"well":"BGW-S04","start":"2027-04-19","end":"2027-05-10","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":7773.4,"cycleDays":229.3},{"order":7,"well":"BGW-S10","start":"2027-05-10","end":"2027-05-31","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":1391.7,"cycleDays":235.3},{"order":8,"well":"BGW-S12","start":"2027-05-31","end":"2027-06-22","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":1040.9,"cycleDays":241.3},{"order":9,"well":"BGW-S03","start":"2027-06-22","end":"2027-07-13","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":749.6,"cycleDays":235.3},{"order":10,"well":"BGW-S07","start":"2027-07-13","end":"2027-07-27","steam_t":1000,"cutoff":0.6,"spm":3,"marginPerCycleDay":-820.2,"cycleDays":162.5},{"order":11,"well":"BGW-S06","start":"2027-07-27","end":"2027-08-18","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":-2384.6,"cycleDays":247.3},{"order":12,"well":"BGW-S02","start":"2027-08-18","end":"2027-09-08","steam_t":1500,"cutoff":0.6,"spm":3,"marginPerCycleDay":-3401,"cycleDays":254.3}],"deferred":[]},"naive":{"fieldMarginInrTotal":-4855776,"fieldMarginInrPerDay":-13303.5,"generatorUtilisationPct":69.9,"steamTTotal":18000,"co2TTotal":4028.1,"nWellsServed":12,"nWellsDeferred":0,"jobs":[{"order":1,"well":"BGW-S12","start":"2026-12-10","end":"2026-12-31","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":-5126.5,"cycleDays":209.3},{"order":2,"well":"BGW-S02","start":"2026-12-31","end":"2027-01-22","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":-16070.6,"cycleDays":194.3},{"order":3,"well":"BGW-S09","start":"2027-01-22","end":"2027-02-12","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":1227.6,"cycleDays":197.3},{"order":4,"well":"BGW-S07","start":"2027-02-12","end":"2027-03-05","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":-9801.8,"cycleDays":175.3},{"order":5,"well":"BGW-S06","start":"2027-03-05","end":"2027-03-26","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":-8276.7,"cycleDays":217.3},{"order":6,"well":"BGW-S03","start":"2027-03-26","end":"2027-04-17","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":-5693.4,"cycleDays":205.3},{"order":7,"well":"BGW-S10","start":"2027-04-17","end":"2027-05-08","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":-4991.2,"cycleDays":205.3},{"order":8,"well":"BGW-S05","start":"2027-05-08","end":"2027-05-29","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":5220.4,"cycleDays":189.3},{"order":9,"well":"BGW-S11","start":"2027-05-29","end":"2027-06-20","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":1040.9,"cycleDays":191.3},{"order":10,"well":"BGW-S04","start":"2027-06-20","end":"2027-07-11","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":1088.5,"cycleDays":192.3},{"order":11,"well":"BGW-S08","start":"2027-07-11","end":"2027-08-01","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":11650.5,"cycleDays":186.3},{"order":12,"well":"BGW-S01","start":"2027-08-01","end":"2027-08-22","steam_t":1500,"cutoff":1.3,"spm":5,"marginPerCycleDay":6764.9,"cycleDays":183.3}],"deferred":[]},"comparison":{"exactVsNaivePctGain":450.5,"exactVsNaiveDeltaInr":21874390}};
/* Identifiability tag for a fitted parameter, from a fit()/calibrate/demo
   response's own identifiability.correlated_pairs -- so the tag is derived
   from THIS dataset's Jacobian-implied covariance, not hard-coded to the
   demo. |r| >= 0.95 -> only jointly identifiable ("as a ratio"); 0.8-0.95 ->
   partly; otherwise well identified. Mirrors ml/README.md's own thresholds. */
function calibIdentTag(paramKey, correlatedPairs){
  const pairs = correlatedPairs || [];
  let best = null;
  pairs.forEach(function(p){
    if (p.params.indexOf(paramKey) === -1) return;
    const other = p.params[0] === paramKey ? p.params[1] : p.params[0];
    const a = Math.abs(p.correlation);
    if (!best || a > best.a) best = { a: a, other: other };
  });
  if (!best) return { sym: "✓", cls: "pass", key: "idWell", withParam: null };
  if (best.a >= 0.95) return { sym: "✗", cls: "warn", key: "idRatio", withParam: best.other };
  if (best.a >= 0.8)  return { sym: "~",      cls: "warn", key: "idPartly", withParam: best.other };
  return { sym: "✓", cls: "pass", key: "idWell", withParam: null };
}

/* Normalises a twin.calibrate.fit()-shaped result to one shape regardless of
   its source: the baked CALIB_DEMO constant, GET /calibrate/demo (before +
   after, hidden truth) or POST /calibrate (a single, after-only,
   "recommendation" -- a real upload has no default-params baseline to
   compare against, since /calibrate never re-runs the search on the
   UN-calibrated params). Every renderer below reads only this shape. */
function normalizeCalibResidualRow(row){
  return {
    well_id: row.well_id,
    obs_oil_m3: row.obs_oil_m3,
    sim_oil_m3: row.sim_oil_m3,
    oil_pct_error: (row.oil_pct_error !== undefined) ? row.oil_pct_error : row.oil_m3_pct_error
  };
}
function normalizeCalibRecommendation(rec){
  if (!rec) return null;
  const bs = rec.best_settings || rec;
  const pv = rec.physics_verified_optimum || rec;
  const ranges = rec.search_ranges || null;
  const pinnedAtUpper = !!(rec.pinned_variables && rec.pinned_variables.steam_t === "upper");
  return {
    steam_t: bs.steam_t, soak_days: bs.soak_days, cutoff_m3d: bs.cutoff_m3d, spm: bs.spm,
    SOR_t_per_m3: pv.SOR_t_per_m3, oil_total_m3: pv.oil_total_m3, days_total: pv.days_total,
    margin_inr_per_cycle_day: pv.margin_inr_per_cycle_day,
    margin_incremental_inr_per_cycle_day: pv.margin_incremental_inr_per_cycle_day,
    max_floating_index: pv.max_floating_index,
    pinnedSteamAtUpperBound: rec.pinnedSteamAtUpperBound !== undefined ? rec.pinnedSteamAtUpperBound : pinnedAtUpper
  };
}
function normalizeCalibResult(raw){
  const idf = raw.identifiability || {};
  return {
    fitted: raw.fitted_params || raw.fitted,
    bounds: raw.bounds,
    rmse: raw.rmse,
    correlatedPairs: idf.correlated_pairs || idf.correlatedPairs || [],
    knownCouplings: idf.known_couplings || idf.knownCouplings || [],
    hiddenTruth: raw.hidden_truth || raw.hiddenTruth || null,
    residualTable: (raw.residual_table || raw.residualTable || []).map(normalizeCalibResidualRow),
    nCycles: raw.n_cycles !== undefined ? raw.n_cycles : raw.nCycles,
    before: raw.recommendation_before_calibration ? normalizeCalibRecommendation(raw.recommendation_before_calibration)
      : (raw.before || null),
    after: raw.recommendation_after_calibration ? normalizeCalibRecommendation(raw.recommendation_after_calibration)
      : (raw.recommendation ? normalizeCalibRecommendation(raw.recommendation) : (raw.after || null))
  };
}

/* ₹ with an explicit sign for a Monte Carlo band whose low end can be
   negative (unlike the always-positive iso-oil savings figures above). */
function inrSigned(n){
  const v = Math.round(Number(n));
  return (v < 0 ? "−₹" + nf(Math.abs(v), 0) : "₹" + nf(v, 0));
}
/* Same, but an explicit "+" on a non-negative value — for a delta headline,
   where "₹3,332" reads as an absolute figure and "+₹3,332" reads as a gain. */
function inrSignedPlus(n){
  const v = Math.round(Number(n));
  return (v < 0 ? "−₹" + nf(Math.abs(v), 0) : "+₹" + nf(v, 0));
}

/* =========================================================================
   FUEL, COST AND CARBON
   Baghewala's steam generators are DIESEL-fired. OIL's own operations deck
   (12-Jul-2025, BGW-08 first cycle) records ~220 kg/hr HSD against
   ~3,100 kg/hr of steam, so every tonne of steam costs ~71 kg of high-speed
   diesel. There is no gas supply to the field — crude leaves by road tanker.
   The dashboard previously carried an unsourced ₹1,300/t constant, which is
   a GAS-fired number and understates the real fuel cost by roughly 6.5×.
   Full derivation and citations:
     docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md §0, §1.2
     docs/research/baghewala_facts.md §4
   Accounting rule: PER CYCLE ONLY. There is no annualisation here, and
   there must never be a 365/days_total term anywhere in this product —
   days_total is the SIMULATED producing-cycle length, not the field
   re-visit interval. Published CSS cycles run 6–18 months apart; Baghewala
   banked 39 cycles in ~6.5 years across a 34-well field. Programme-scale
   figures multiply by OIL's own published FY2025-26 CSS job count, and are
   always labelled as a separate, explicit multiplication.
   ========================================================================= */
const ECON = {
  hsd_kg_per_t_steam: 71.0,    /* [DERIVED] 220 / 3.1, OIL ops deck 12-Jul-2025 */
  hsd_density_kg_l:   0.83,    /* [TYPICAL] high-speed diesel                   */
  hsd_l_per_t_steam:  85.54,   /* [DERIVED] 71 / 0.83                           */
  hsd_inr_per_l:      97.80,   /* [CONFIRMED] Rajasthan retail pump price, Aug 2026 — an UPPER bound */
  /* rev 13 (wave 5): base moved 0.30 -> 0.15, the MID of the U[0,0.30] UQ
     range (₹7,111/t at the ₹97.80/L retail price) — the external re-score
     flagged 0.30 as the best (bulk) edge of an unsourced range, not a base
     case. 0.30 and 0 (retail) are kept as named presets
     (params/field_params.json economics.diesel_discount_presets). */
  bulk_discount:      0.15,    /* [CALIBRATED, UNSOURCED] mid of the U[0,0.30] band */
  gj_per_t_steam:     3.02,    /* [DERIVED] 71 kg × 42.6 MJ/kg — inside the published 2.6–4.0 GJ/t band */
  co2_kg_per_t_steam: 223.8,   /* [DERIVED] 3.02 GJ/t × 74.1 kgCO2/GJ (IPCC diesel default) */
  css_jobs_fy26:      19,      /* [CONFIRMED] CSS jobs Oil India ran in FY2025-26, field-wide */
  /* --- margin-formula constants, params/field_params.json "economics" block,
     twin/cycle.py steam_cost_inr_per_t() + summary() — the three below plus
     hsd_kg_per_t_steam/hsd_density_kg_l/hsd_inr_per_l/bulk_discount above are
     EVERY term that formula uses. bbl_per_m3 is carried at full precision
     (not the display-rounded M3_TO_BBL) so an in-browser recompute at
     base-case prices lands on the exact same rupee as the baked
     REF_SUMMARY/OPT_SUMMARY margins.
     rev 9: base case is OIL's CONFIRMED FY25 realisation (Annual Report
     2024-25, US$78.09/bbl) minus a $10/bbl heavy-oil discount [ASSUMPTION],
     x Rs88/$ = Rs5,992/bbl. The old $65 placeholder (Rs4,840/bbl) — the
     CMD's FY26 planning floor, never a realisation — is kept as a named
     preset ("Your prices" panel), not deleted. */
  oil_price_inr_per_bbl:   5992.0,  /* [CONFIRMED - $10 ASSUMPTION discount] (78.09 - 10) x Rs88/$, OIL AR 2024-25 FY25 realisation */
  fixed_cost_inr_per_cycle: 1.5e6,  /* [ASSUMPTION] rig/workover per cycle — NOT a "Your prices" input, carried as a constant */
  bbl_per_m3:              6.28981, /* [DEFINITION] full precision */
  /* --- Economics v2 (rev 8/9): opex + cold-baseline constants for the
     INCREMENTAL re-price formula (marginIncrementalAtPrices() below). None
     of these are "Your prices" inputs — electricity tariff and opex are not
     user-adjustable on the panel, so they stay fixed at their baked values,
     exactly like fixed_cost_inr_per_cycle above. */
  opex_inr_per_day:        5000.0,  /* [ASSUMPTION] fixed well-site opex, excl. power */
  electricity_inr_per_kWh: 8.0,     /* [UNSOURCED PLACEHOLDER] */
  cold_electric_kWh_per_day: 162.659 /* [DERIVED] cold (unstimulated) well's own pumping power, 2-spm keep-moving floor — well-level constant, same at every scenario */
};
ECON.inr_per_t_steam_high = ECON.hsd_l_per_t_steam * ECON.hsd_inr_per_l;              /* ≈ ₹8,366/t */
ECON.inr_per_t_steam_low  = ECON.inr_per_t_steam_high * (1 - ECON.bulk_discount);     /* ≈ ₹5,856/t */

/* Named price-deck presets for the "Your prices" panel (params/field_params.json
   economics.oil_price_presets). fy25_realisation is the base case
   (ECON.oil_price_inr_per_bbl above); fy26_floor_65 is the prior placeholder,
   kept as a labelled downside preset; fy25_net_of_levies is the rev-13
   (wave 5) royalty + OID cess deck. */
const OIL_PRICE_PRESETS = {
  fy25_realisation: { inr_per_bbl: 5992.0, usd_net: 68.09, usd_gross: 78.09,
                       labelKey: "presetFy25", source: "OIL India Annual Report 2024-25, CONFIRMED FY25 realisation" },
  fy26_floor_65:    { inr_per_bbl: 4840.0, usd_net: 55.0,  usd_gross: 65.0,
                       labelKey: "presetFy26Floor", source: "CMD's FY26 planning floor — a budgeting number, not a realisation" },
  fy25_net_of_levies: { inr_per_bbl: 3600.0, usd_gross: 78.09,
                       labelKey: "presetLevies",
                       source: "rev 13 [ASSUMPTION on the rates; basis CONFIRMED]: FY25 base (₹5,992/bbl) x (1 − 0.20 royalty − 0.20 OID cess) ≈ ₹3,600/bbl — OIL's own company-basis price, not netting the ER-policy 50% cess waiver a qualifying CSS job might get." }
};
/* Diesel bulk-discount presets (params/field_params.json economics.diesel_discount_presets,
   rev 13): base is now the mid_0.15 value (ECON.bulk_discount above); 0.30
   (bulk) and 0 (retail) are named presets, not the base case. */
const DIESEL_DISCOUNT_PRESETS = { "mid_0.15": 0.15, "bulk_0.30": 0.30, "retail_0": 0.0 };

/* =========================================================================
   "YOUR PRICES" — in-browser re-pricing, NOT re-optimisation.
   The optimiser's argmax (OPT_RESULT / OPT_APPLIED) was computed once, at
   base-case prices — it is never recomputed here. What these three inputs
   change is only the ₹ figure the twin's own margin formula produces when
   applied to the BAKED physical quantities (oil_total_m3, steam_t,
   days_total — physics, from REF_SUMMARY/OPT_SUMMARY/OPT_APPLIED, unaffected
   by price). See dashboard/README.md §7.2 and twin/cycle.py
   steam_cost_inr_per_t() + summary(). ========================================================================= */
const PRICES_BASE = { diesel: ECON.hsd_inr_per_l, discount: ECON.bulk_discount, oilBbl: ECON.oil_price_inr_per_bbl };

function getPrices(){
  const p = BUS.get("prices", null);
  if (!p || !Number.isFinite(p.diesel) || !Number.isFinite(p.discount) || !Number.isFinite(p.oilBbl)){
    return Object.assign({}, PRICES_BASE);
  }
  return p;
}
function setPrices(p){ BUS.set("prices", p); }
function resetPrices(){ BUS.set("prices", null); }
function pricesAreBase(p){
  return Math.abs(p.diesel - PRICES_BASE.diesel) < 1e-9 &&
         Math.abs(p.discount - PRICES_BASE.discount) < 1e-9 &&
         Math.abs(p.oilBbl - PRICES_BASE.oilBbl) < 1e-9;
}

/* GROSS margin — replicates twin/cycle.py's steam_cost_inr_per_t() and
   summary()'s margin_inr_per_cycle_day exactly:
     revenue = (oil_total_m3 × bbl_per_m3) × oil_price_inr_per_bbl
     steam_cost = steam_t × (hsd_kg_per_t_steam / hsd_density_kg_l) × diesel_price × (1 − bulk_discount)
     margin = (revenue − steam_cost − fixed_cost_inr_per_cycle) / days_total
   Verified to the rupee against REF_SUMMARY.margin_inr_per_cycle_day (15,824.10)
   and OPT_SUMMARY.margin_inr_per_cycle_day (21,116.91) at PRICES_BASE. Kept for
   the "gross" reporting rows; the recommendation card and result strip use the
   INCREMENTAL functions below (rev 9). */
function marginAtPrices(oilTotalM3, steamTTotal, daysTotal, prices, fuelFactor, bakedSteamCostInr){
  const litresPerT = ECON.hsd_kg_per_t_steam / ECON.hsd_density_kg_l;   /* precise 85.5422 L/t */
  /* rev 13.1 (item 6): twin/cycle.py's steam_cost_inr = steam_t_total ×
     steam_cost_inr_per_t(econ) × fuel_factor -- a small (~0.04%) wellhead-
     pressure/steam-quality correction this re-pricer was missing, which is
     why "Your prices" at the untouched base case used to land ~₹14/cycle-day
     off the baked OPT_SUMMARY figure (tile "+₹3,318" vs the card's baked
     "+₹3,332"). fuelFactor defaults to 1 (REF_SUMMARY's own baked value) so
     an off-baked/legacy caller with no fuel-factor field is unaffected. At
     the untouched base case, use the BAKED steam_cost_inr verbatim instead
     of recomputing it -- the baked value carries fuel_factor at full
     precision, this constant only 4 decimal places, so recomputing would
     still leave a sub-rupee residual "verified to the rupee" should not
     have. */
  const ff = Number.isFinite(fuelFactor) ? fuelFactor : 1;
  const bbl = oilTotalM3 * ECON.bbl_per_m3;
  const revenue = bbl * prices.oilBbl;
  const steamCost = (pricesAreBase(prices) && Number.isFinite(bakedSteamCostInr))
    ? bakedSteamCostInr
    : steamTTotal * litresPerT * prices.diesel * (1 - prices.discount) * ff;
  const marginTotal = revenue - steamCost - ECON.fixed_cost_inr_per_cycle;
  return daysTotal > 0 ? marginTotal / daysTotal : NaN;
}
function baselineMarginAtPrices(prices){
  return marginAtPrices(REF_SUMMARY.oil_total_m3, REF_INPUTS.steam_t, REF_SUMMARY.days_total, prices, REF_SUMMARY.steam_fuel_factor, REF_SUMMARY.steam_cost_inr);
}
function recommendedMarginAtPrices(prices){
  return marginAtPrices(OPT_SUMMARY.oil_total_m3, OPT_APPLIED.steam_t, OPT_SUMMARY.days_total, prices, OPT_SUMMARY.steam_fuel_factor, OPT_SUMMARY.steam_cost_inr);
}

/* INCREMENTAL margin (Economics v2, rev 8/9) — mirrors twin/cycle.py
   summary()'s _incremental_economics() exactly, at whatever (diesel,
   discount, oilBbl) the panel is set to. Everything else that formula
   uses — daily opex, electricity tariff, the cold well's own rate and
   pumping power, and the calendar window — is PHYSICS, not a "Your
   prices" input, so it is carried as a baked constant (summary.window_days,
   .opex_fixed_inr, .power_cost_inr, .cold_rate_m3d, plus the well-level
   ECON.cold_electric_kWh_per_day and ECON.opex_inr_per_day /
   .electricity_inr_per_kWh) exactly like fixed_cost_inr_per_cycle above.
     margin_gross      = revenue(oilBbl) − steam_cost(diesel,discount) − fixed_cost
     margin_with_opex  = margin_gross − power_cost_inr − opex_fixed_inr
     cold_cash_per_day = cold_rate_m3d × (oilBbl × bbl_per_m3)
                         − cold_electric_kWh_per_day × electricity_inr_per_kWh
                         − opex_inr_per_day
     cold_net          = cold_cash_per_day × window_days, if cold_cash_per_day > 0, else 0
                         (an uneconomic cold well would be shut in — cash 0)
     margin_incremental_per_day = (margin_with_opex − cold_net) / window_days
   Verified to the rupee against REF_SUMMARY/OPT_SUMMARY's baked
   margin_incremental_inr_per_cycle_day at PRICES_BASE. */
function marginIncrementalAtPrices(summary, steamTTotal, prices){
  const litresPerT = ECON.hsd_kg_per_t_steam / ECON.hsd_density_kg_l;
  /* rev 13.1 (item 6): apply the same fuel_factor correction as
     marginAtPrices() above -- summary.steam_fuel_factor/.steam_cost_inr are
     already baked onto every REF_SUMMARY/OPT_SUMMARY/RUN.summary object, so
     this needed no new data. At the untouched base case, use the baked
     steam_cost_inr verbatim (full precision) rather than recomputing from
     the 4-decimal fuel_factor constant, so the tile (rsMarginDelta, "Margin
     vs baseline, per cycle-day") exactly matches the recommendation card's
     own baked headline instead of landing a few rupees off it. */
  const ff = Number.isFinite(summary.steam_fuel_factor) ? summary.steam_fuel_factor : 1;
  const bbl = summary.oil_total_m3 * ECON.bbl_per_m3;
  const revenue = bbl * prices.oilBbl;
  const steamCost = (pricesAreBase(prices) && Number.isFinite(summary.steam_cost_inr))
    ? summary.steam_cost_inr
    : steamTTotal * litresPerT * prices.diesel * (1 - prices.discount) * ff;
  const marginGross = revenue - steamCost - ECON.fixed_cost_inr_per_cycle;
  const marginWithOpex = marginGross - summary.power_cost_inr - summary.opex_fixed_inr;
  /* rev 13 (wave 5): the cold-well counterfactual's shut-in/pumped status is
     now a MECHANICAL fact under the "policy" convention (its floating index,
     at the params unit and the baked formation water cut, either exceeds the
     float-alarm line or does not) -- it is decided by physics, not by
     whether the cold cash flow happens to pencil out at whatever price the
     panel is set to. summary.cold_well_economic (false at every baked point
     here) carries that fact; when it is false, incremental == net cash (with
     opex) at ANY price, exactly like the baked REF_SUMMARY/OPT_SUMMARY. If a
     future re-bake ever carries a point where the cold well IS pumpable, its
     (price-dependent) cash is netted out the old way. */
  if (summary.cold_well_economic === false) {
    return summary.window_days > 0 ? marginWithOpex / summary.window_days : NaN;
  }
  const priceM3 = prices.oilBbl * ECON.bbl_per_m3;
  const coldCashPerDay = summary.cold_rate_m3d * priceM3
                       - ECON.cold_electric_kWh_per_day * ECON.electricity_inr_per_kWh
                       - ECON.opex_inr_per_day;
  const coldNet = coldCashPerDay > 0 ? coldCashPerDay * summary.window_days : 0;
  const marginIncremental = marginWithOpex - coldNet;
  return summary.window_days > 0 ? marginIncremental / summary.window_days : NaN;
}
function baselineMarginIncrementalAtPrices(prices){
  return marginIncrementalAtPrices(REF_SUMMARY, REF_INPUTS.steam_t, prices);
}
function recommendedMarginIncrementalAtPrices(prices){
  return marginIncrementalAtPrices(OPT_SUMMARY, OPT_APPLIED.steam_t, prices);
}

/* Iso-oil counterfactual: how much steam would the run on the books have
   burned to make the OPTIMISED cycle's oil? rev 12: the recommendation now
   injects LESS steam in absolute terms than the baseline (1,000 t vs
   1,300 t) as well as recovering more oil per tonne (better SOR), so a
   naive difference of the two fuel bills would already show a saving in
   the right direction here -- but the SOR-based iso-oil figure below is
   still the correct, and larger, comparison: it asks how much MORE steam
   the baseline's own (worse) efficiency would need to match the
   recommendation's oil, not just how many fewer tonnes were injected. */
function cycleAvoided(baseSOR, optSummary, optSteamT){
  const counterfactual = optSummary.oil_total_m3 * baseSOR;
  const steam = counterfactual - optSteamT;
  return {
    counterfactualSteamT: counterfactual,
    steamT:   steam,
    dieselL:  steam * ECON.hsd_l_per_t_steam,
    dieselT:  steam * ECON.hsd_kg_per_t_steam / 1000,
    energyGJ: steam * ECON.gj_per_t_steam,
    co2T:     steam * ECON.co2_kg_per_t_steam / 1000,
    crLow:    steam * ECON.inr_per_t_steam_low  / 1e7,
    crHigh:   steam * ECON.inr_per_t_steam_high / 1e7
  };
}
/* Programme scale-up — the caller MUST pass a job count; nothing is implied. */
function scaleToProgramme(perCycle, nJobs){
  const out = {};
  Object.keys(perCycle).forEach(function(k){ out[k] = perCycle[k] * nJobs; });
  out.jobs = nJobs;
  return out;
}
const inrRange = (lo, hi) => "₹" + fmt(lo, 2) + "–" + fmt(hi, 2) + " cr";

/* ---------- FORMATTING --------------------------------------------------- */
const $ = (id) => document.getElementById(id);
const $$ = (sel, root) => Array.prototype.slice.call((root || document).querySelectorAll(sel));
const fmt = (n, d) => (n === undefined || n === null || Number.isNaN(Number(n)) || !Number.isFinite(Number(n)))
  ? "—" : Number(n).toFixed(d === undefined ? 2 : d);
const nf = (n, d) => (n === undefined || n === null || !Number.isFinite(Number(n)))
  ? "—" : Number(n).toLocaleString("en-US", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
const pct = (p) => (p === undefined || p === null || Number.isNaN(Number(p))) ? "—"
  : (p * 100 < 0.1 && p > 0 ? "<0.1%" : (p * 100).toFixed(1) + "%");
const signed = (n, d) => (!Number.isFinite(Number(n))) ? "—" : (n > 0 ? "+" : (n < 0 ? "−" : "")) + Math.abs(n).toFixed(d === undefined ? 2 : d);

function istStamp(date){
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false
  }).formatToParts(date || new Date()).reduce(function(a, p){ a[p.type] = p.value; return a; }, {});
  return parts.day + "-" + parts.month + "-" + parts.year + " " + parts.hour + ":" + parts.minute + " IST";
}
function istDateCode(date){
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" })
    .format(date || new Date()).replace(/-/g, "");
}
function istClock(date){
  return new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hour12: false })
    .format(date || new Date()) + " IST";
}
function settingsLabel(c){
  return nf(c.steam_t) + " t / " + nf(c.soak_days) + " d / " + fmt(c.cutoff, 2) + " m³/d / " + fmt(c.spm, 1) + " spm";
}

/* ---------- BILINGUAL — EN | हिं ----------------------------------------- */
let LANG = "en";
const STR = {
  en: {
    /* chrome + pages */
    navOverview:"Overview", navConsole:"Simulator", navOptimizer:"Recommendation", navMethod:"Model basis",
    pgOverview:"Cycle result — BGW-07", pgConsole:"Twin console — BGW-07",
    pgOptimizer:"Set-point optimisation — BGW-07", pgMethod:"Model basis and validation",
    theme:"Theme", light:"Light", dark:"Dark", language:"Language",
    well:"Well", cycle:"Cycle", computed:"computed", source:"Source",
    /* phases + states */
    inject:"Inject", soak:"Soak", produce:"Produce",
    cycleComplete:"Cycle complete", idle:"Idle",
    within:"Within limits", elevated:"Elevated", exceeded:"Threshold exceeded",
    shutIn:"SHUT-IN", ok:"OK", alm:"ALM",
    /* set-points */
    steamVolume:"Steam volume", soakPeriod:"Soak period", cutoff:"Economic cutoff", pumpSpeed:"Pump speed",
    setpoints:"Set-points", simulate:"Simulate cycle", optimise:"Run optimiser",
    replay:"Replay cycle", stress:"Try high speed (12 SPM)", reset:"Reset to reference",
    /* results */
    sorLong:"Steam/oil ratio", improvement:"Improvement",
    fuelAvoided:"Fuel not burned, per cycle", co2Avoided:"CO₂ avoided, per cycle",
    perCycle:"per optimised cycle, one well", programme:"programme-wide",
    fuelBasis:"HSD diesel basis", isoOil:"iso-oil counterfactual",
    oilRecovered:"Oil recovered", energyIntensity:"Energy intensity", cycleDuration:"Cycle duration",
    floatingRisk:"Floating risk", steamInjected:"Steam injected", expectedFailures:"Expected rod failures",
    metric:"Metric", currentCycle:"Current cycle", mlOptimum:"Physics-grid optimum", delta:"Change", unit:"Unit",
    /* optimiser */
    predictedSOR:"Predicted SOR (surrogate)", floatingProb:"Floating probability",
    recommended:"Recommended (continuous)", asApplied:"As applied (controller grid)",
    recommendation:"Recommendation", optimiserIdle:"Optimiser not yet run",
    optimiserIdleBody:"Surrogate-assisted search is ready. Run the optimiser to search the four-parameter set-point space and produce a recommendation.",
    fieldPractice:"Assumed baseline (BGW-8 job + our pump settings)", todaysRun:"Today's run", manualRun:"Manual run (replaced)",
    mlOptimised:"Physics-grid optimum (as applied)",
    baselineFootnote:"1,300 t is from a documented BGW-8 job; stroke, spm and cutoff are our own assumptions, not OIL's current practice",
    marginPerCycleDay:"Margin per cycle-day", soakFieldPractice:"Soak 10 d (field practice — model insensitive, not optimised)",
    sorAxis:"SOR (t steam / m³ oil)", vsFieldPractice:"vs assumed baseline",
    stagePrompt:"Load these settings into the simulator for a check run? Nothing is sent to the well.",
    appliedBy:"Applied by operator", settingsApplied:"Recommended set-points applied",
    asAppliedOptimum:"current cycle → as-applied optimum",
    runOptimiser:"run the optimiser to compare set-points",
    steamNotBurned:"of steam not burned per optimised cycle",
    stage:"Stage set-points", confirm:"Confirm", cancel:"Cancel",
    authNote:"requires operator authorisation",
    constraint:"Constraint", limit:"Limit", atRec:"At recommendation", status:"Status",
    /* console */
    cycleEndState:"cycle end-state", replayAt:"replay", telemetry:"Simulated readings",
    day:"Day", oilRate:"Oil rate (m³/d)", resT:"Reservoir T (°C)", visc:"Viscosity (cP)",
    strokePos:"Stroke position (m)", rodLoad:"Rod load (kN)",
    cycleLoaded:"cycle loaded — press play to sweep the twin",
    peakRodLoad:"Peak rod load", strokeLength:"Stroke length",
    wellheadPressure:"Injection (wellhead) pressure", operatingRule:"Produce-end rule",
    rateRuleCurrent:"Rate cutoff (as run)", floatOnsetRule:"Float onset (3 alarm days, 0.6 m³/d backstop)",
    vfdHoldRule:"VFD-hold (drive holds FI at 0.6 to a 2-spm floor, pull after 3 alarm days there)",
    waterCutTm:"Water cut", floatIndexTm:"Rod-float index", floatBanner:"Rods floating — operator pulls the well",
    alarmDefaultText:"Rod floating risk — reduce SPM",
    vfdHoldBanner:"VFD slows the pump — rods held at the limit",
    floatPolicyLabel:"Rod-float response",
    floatPolicyPull:"Pull after 3 alarm days",
    floatPolicyPullDesc:"The pump keeps running at speed; once the float alarm has fired 3 days running, the operator pulls the rods and re-steams.",
    floatPolicyVfdHold:"Slow the pump to hold the limit (VFD-hold)",
    floatPolicyVfdHoldDesc:"A variable-speed drive slows the unit to hold the float index at 0.6, down to a 2-spm floor; only pulled after 3 alarm days AT that floor. The recommended policy.",
    floatPolicyVfdThenPull:"Slow, then pull",
    floatPolicyVfdThenPullDesc:"As VFD-hold, but the drive only turns down to about half the start speed before the operator pulls.",
    floatPolicyNone:"No float response (rods float)",
    floatPolicyNoneDesc:"The pump keeps running at speed regardless of float; the cycle ends only on the rate cutoff — no failure cost is modelled.",
    floatPolicyBakedNote:"The physics shown here is always run VFD-hold (the recommended policy); the other options preview the operator explanation only.",
    conFiRule:"Float-alarm rule (consecutive days)", conPrlCap:"Peak PRL vs unit rating",
    floatingIndex:"Floating index", classifierP:"Classifier p(float)",
    failureThreshold:"failure threshold",
    /* table rows and group headings (Tier 2 — swapped by the toggle) */
    grpFuelCycle:"Fuel and carbon, this cycle", grpMech:"Mechanical integrity",
    hsdBurned:"HSD diesel burned", co2Steam:"CO₂ from steam generation", co2Intensity:"CO₂ intensity",
    maxFI:"Max floating index", oilBbl:"Oil recovered",
    grpSteamAvoided:"Steam avoided — iso-oil counterfactual",
    grpFuelGen:"Fuel — diesel-fired generators", grpCarbon:"Carbon", grpProgramme:"Programme scale",
    oilAtOptimum:"Oil at the optimum",
    steamNeeded:"Steam the current practice would need for that oil",
    steamInjectedOpt:"Steam actually injected at the optimum",
    steamAvoided:"Steam avoided", dieselPerT:"Diesel per tonne of steam", dieselAvoided:"Diesel avoided",
    priceBand:"Fuel price band", valueAvoidedCycle:"Value avoided, per cycle",
    energyAvoided:"Fuel energy avoided", co2AvoidedCycle:"CO₂ avoided, per cycle",
    valueAvoided:"Value avoided", co2AvoidedShort:"CO₂ avoided",
    runId:"Run ID", computedAt:"Computed", simulator:"Simulator", parameters:"Parameters",
    validation:"Validation", dataSource:"Data source", recCol:"Recommendation", optimiserCol:"Optimiser",
    fuelBasisRow:"Fuel basis", carbonBasis:"Carbon basis", programmeScale:"Programme scale",
    grpPredicted:"Predicted outcome", sorSurrogate:"SOR (surrogate prediction)",
    sorTwin:"SOR (twin re-run at applied set-points)", maxFItwin:"Max floating index (twin)",
    marginSurrogate:"Margin per cycle-day, gross (surrogate prediction)",
    marginTwin:"Margin per cycle-day, gross (twin re-run at applied set-points)",
    marginIncrSurrogate:"Margin per cycle-day, incremental — objective (surrogate prediction)",
    marginIncrTwin:"Margin per cycle-day, incremental — objective (twin re-run at applied set-points)",
    grpBounds:"Search bounds — css / srp blocks",
    conFloatProb:"Floating probability p(float)", conMaxFI:"Max floating index, twin",
    conFailures:"Expected rod failures",
    satisfied:"satisfied", violated:"violated", atLowerBound:"at lower bound", atUpperBound:"at upper bound",
    heldByDesign:"held at limit (by design)",
    /* misc */
    parameter:"Parameter", value:"Value", sourceCol:"Source", openConsole:"Open in twin console",
    reviewRec:"Review recommendation", readBasis:"Read the model basis",
    /* P0 additions — simplification pass, 26 Sep 2026 */
    approxChip:"Approximate run — not carried to Overview",
    noSaving:"No saving against this run",
    sorNotAchievable:"SOR not achievable — rods would float at this SPM",
    checkInSimulator:"Check in simulator",
    seeFullRec:"See full recommendation",
    riskLow:"low", riskHigh:"high",
    crore:"crore",
    simCheckTarget:"→ simulator check",
    openSimLoad:"Open simulator and load →",
    modelDetails:"Model details (for specialists) ▸",
    chipOk:"OK", chipWatch:"WATCH", chipAlarm:"ALARM",
    tmDayLabel:"Day", tmResLabel:"Reservoir temp", tmViscLabel:"Viscosity",
    tmOilLabel:"Oil rate", tmRodLabel:"Rod load", tmPumpLabel:"Pump",
    rodsSafe:"Rods safe at", rodsFloat:"Rods will float at", ofLimit:"of 0.60 limit", reduceSpeed:"reduce speed",
    dynoTitle:"Rod load vs stroke (indicative)", dynoMeta:"illustrative shape — not a measured dynacard",
    modelFloatProb:"Model float probability",
    printLabel:"Print",
    consoleSubtitle:"Try settings for the next CSS cycle and see temperature, oil rate and rod load day by day.",
    optSubtitle:"Finds the steam, wellhead pressure, cutoff, stroke length and pump speed that maximise incremental margin per cycle-day, while keeping rods safe. Soak is held at 10 d field practice.",
    replayShort:"Play the cycle (14 s)",
    howCalculated:"How these numbers are calculated ▸",
    checkInSimTitle:"Check in simulator",
    checkInSimBody:"Load these settings into the simulator for a check run? Nothing is sent to the well.",
    vsMidpoint:"vs midpoint baseline",
    superseded:"superseded",
    simChip:"Simulation — not live well data",
    /* "Your prices" — re-pricing panel, 26 Sep 2026 */
    yourPrices:"Your prices",
    dieselPriceLabel:"Diesel price ₹/L",
    bulkDiscountLabel:"Bulk discount %",
    oilRealisationLabel:"Oil realisation ₹/bbl",
    resetBaseCase:"Reset to base case",
    baseCase:"base case",
    atBaseCasePrices:"at base-case prices",
    atFy25Realisation:"at OIL's FY25 realisation",
    atYourPrices:"at your prices",
    incrementalTag:"incremental over cold production",
    presetFy25:"OIL FY25 realisation ($78.09)",
    presetFy26Floor:"FY26 planning floor ($65)",
    notReoptimisedNote:"Set-points were optimised at base-case prices; margins here are re-priced, not re-optimised.",
    pricesPanelIntro:"Recomputes margin below from these three prices. Steam, oil recovered, CO₂ and cycle length are physics — they do not change.",
    setPricesLink:"Set your prices → (Overview)",
    /* "Calibrate from field data" — twin/calibrate.py, 26 Sep 2026 */
    calibNav:"Calibrate from field data",
    calibDemoTitle:"Demonstration — synthetic data, not field data",
    calibWhatRecovered:"What the fit recovered",
    calibColBefore:"Before (default)", calibColFitted:"Fitted", calibColTruth:"Hidden truth (demo only)",
    calibColIdentified:"Identified",
    idWell:"well identified", idPartly:"partly identified", idRatio:"only as a ratio",
    calibFitQuality:"Fit quality (observed vs fitted)",
    calibBeforeAfterTitle:"Recommendation before → after calibration",
    calibBeforeAfterNote:"Same grid search on the physics twin; soak held at 10 d.",
    calibBefore:"Before calibration (default params)", calibAfter:"After calibration",
    calibChartTitle:"Observed vs simulated oil, per cycle",
    calibResidTitle:"Residual — oil, % error per cycle",
    calibUseOwnTitle:"Use your own data",
    calibSchemaTitle:"Required columns",
    calibDownloadTemplate:"Download template",
    calibChooseFile:"Choose CSV file",
    calibRowsParsed:"rows parsed",
    calibPreview:"Preview",
    calibLiveButton:"Calibrate",
    calibLoadIntoSim:"Load calibrated recommendation into Simulator",
    calibYourResultTitle:"Your calibration result",
    calibrationRow:"Calibration", calibrationDefault:"default constants (no field data yet)",
    calibrateLink:"Calibrate →",
    calibAxisObs:"Observed oil (m³)", calibAxisSim:"Simulated oil (m³)", calibAxisErr:"oil_m3 % error (obs vs fitted)",
    /* Computed dynamometer card (surface + pump), 26 Sep 2026 */
    cardTypeFullPump:"Full pump", cardTypeFluidPound:"Fluid pound",
    cardTypeViscous:"Heavy-oil viscous drag", cardTypeGas:"Gas interference",
    cardTypeRodFloat:"Rod float — clamp separated",
    meanFullPump:"Pump barrel fills completely each stroke — healthy operation.",
    meanFluidPound:"Pump outruns the well's inflow — the plunger falls through a partly empty barrel each stroke.",
    meanViscous:"Thick, cold oil drags on the rods through the stroke — higher load, not failure risk.",
    meanGas:"Free gas cushions the pump's release into a rounded card — effective fillage reads lower than the liquid alone.",
    meanRodFloat:"Rods cannot fall as fast as the unit drives them — reduce speed.",
    dynoStressTest:"12-SPM stress test",
    dynoShutInNote:"No card — pump is shut in (inject/soak phase).",
    /* Measured-card classifier ("Check a measured card"), 27 Sep 2026 */
    dynoClfNeedInput:"Choose a CSV file or paste rows first.",
    dynoClfBadTable:"Could not read that table.",
    dynoClfLiveOk:"Classified against the physics-trained model.",
    dynoClfMockOk:"Matched to the nearest baked card (approximate, offline).",
    dynoClfNoMatch:"Offline check unavailable — this curve does not resemble any baked card closely enough to label safely. Start the API for the trained classifier.",
    dynoClfFailed:"Could not classify that card.",
    dynoClfIsApiUp:"— is the API running? python -m uvicorn api.main:app --port 8000 (see README).",
    dynoClfFileError:"Could not read that file.",
    /* Field-level steam scheduler (27 Sep 2026) */
    fieldGanttFoot:"One row = the field's single steam generator; each coloured block is one well's injection + 1-day move. Hover a block for its well and settings.",
    fieldDeferredReasonGeneratorCommitted:"generator time committed to higher-value jobs ahead of it in this schedule",
    fieldDeferredHeading:"Deferred this year",
    fieldServedHeading:"Served this year"
  },
  hi: {
    navOverview:"सारांश", navConsole:"कूप अनुकरण", navOptimizer:"सिफ़ारिश", navMethod:"मॉडल आधार",
    pgOverview:"चक्र परिणाम — BGW-07", pgConsole:"कूप अनुकरण — BGW-07",
    pgOptimizer:"निर्धारित-मान अनुकूलन — BGW-07", pgMethod:"मॉडल आधार एवं सत्यापन",
    theme:"थीम", light:"उजला", dark:"गहरा", language:"भाषा",
    well:"कूप", cycle:"चक्र", computed:"गणना", source:"स्रोत",
    inject:"अंतःक्षेपण", soak:"सोख", produce:"उत्पादन",
    cycleComplete:"चक्र पूर्ण", idle:"निष्क्रिय",
    within:"सीमा के भीतर", elevated:"बढ़ा हुआ", exceeded:"सीमा पार",
    shutIn:"बंद कूप", ok:"ठीक", alm:"चेतावनी",
    steamVolume:"भाप मात्रा", soakPeriod:"सोख अवधि", cutoff:"आर्थिक सीमा", pumpSpeed:"पंप गति",
    setpoints:"निर्धारित मान", simulate:"चक्र अनुकरण", optimise:"अनुकूलक चलाएँ",
    replay:"चक्र दोहराएँ", stress:"उच्च गति आज़माएँ (12 SPM)", reset:"संदर्भ पर लौटें",
    sorLong:"भाप-तेल अनुपात", improvement:"सुधार",
    fuelAvoided:"प्रति चक्र न जला ईंधन", co2Avoided:"प्रति चक्र टाला गया CO₂",
    perCycle:"प्रति अनुकूलित चक्र, एक कूप", programme:"संपूर्ण कार्यक्रम",
    fuelBasis:"एचएसडी डीज़ल आधार", isoOil:"सम-तेल प्रतितथ्य",
    oilRecovered:"कुल प्राप्त तेल", energyIntensity:"ऊर्जा तीव्रता", cycleDuration:"चक्र अवधि",
    floatingRisk:"फ्लोटिंग जोखिम", steamInjected:"अंतःक्षेपित भाप", expectedFailures:"अपेक्षित रॉड विफलताएँ",
    metric:"मापक", currentCycle:"वर्तमान चक्र", mlOptimum:"भौतिकी-ग्रिड इष्टतम", delta:"परिवर्तन", unit:"इकाई",
    predictedSOR:"अनुमानित भाप-तेल अनुपात", floatingProb:"फ्लोटिंग प्रायिकता",
    recommended:"अनुशंसित (सतत)", asApplied:"लागू (नियंत्रक ग्रिड)",
    recommendation:"अनुशंसा", optimiserIdle:"अनुकूलक अभी नहीं चला",
    optimiserIdleBody:"सरोगेट-सहायित खोज तैयार है। चार-प्राचल निर्धारित-मान क्षेत्र की खोज हेतु अनुकूलक चलाएँ।",
    fieldPractice:"अनुमानित आधार रेखा (BGW-8 जॉब + हमारी पंप सेटिंग्स)", todaysRun:"आज का संचालन", manualRun:"पिछला रन (बदला गया)",
    mlOptimised:"भौतिकी-ग्रिड इष्टतम (लागू)",
    baselineFootnote:"1,300 टन एक दस्तावेज़ीकृत BGW-8 जॉब से; स्ट्रोक, spm और cutoff हमारी अपनी धारणाएं हैं, OIL के वर्तमान प्रचलन से नहीं",
    marginPerCycleDay:"प्रति चक्र-दिन मार्जिन", soakFieldPractice:"सोक 10 दिन (क्षेत्र प्रचलन — मॉडल असंवेदनशील, अनुकूलित नहीं)",
    sorAxis:"भाप-तेल अनुपात (t भाप / m³ तेल)", vsFieldPractice:"अनुमानित आधार रेखा की तुलना में",
    stagePrompt:"क्या ये सेटिंग जाँच हेतु सिम्युलेटर में लोड करें? कूप को कुछ नहीं भेजा जाता।",
    appliedBy:"संचालक द्वारा लागू", settingsApplied:"अनुशंसित सेट-पॉइंट लागू",
    asAppliedOptimum:"वर्तमान चक्र → लागू अनुकूलतम",
    runOptimiser:"मानों की तुलना हेतु अनुकूलक चलाएँ",
    steamNotBurned:"भाप प्रति अनुकूलित चक्र न जली",
    stage:"निर्धारित मान तैयार करें", confirm:"पुष्टि करें", cancel:"रद्द करें",
    authNote:"संचालक प्राधिकरण आवश्यक",
    constraint:"प्रतिबंध", limit:"सीमा", atRec:"अनुशंसा पर", status:"स्थिति",
    cycleEndState:"चक्र अंत-स्थिति", replayAt:"पुनरावर्तन", telemetry:"अनुकरित रीडिंग",
    day:"दिन", oilRate:"तेल दर (m³/d)", resT:"भंडार तापमान (°C)", visc:"श्यानता (cP)",
    strokePos:"स्ट्रोक स्थिति (m)", rodLoad:"रॉड भार (kN)",
    cycleLoaded:"चक्र लोड — ट्विन चलाने हेतु प्ले दबाएँ",
    peakRodLoad:"शिखर रॉड भार", strokeLength:"स्ट्रोक लंबाई",
    wellheadPressure:"इंजेक्शन (वेलहेड) दाब", operatingRule:"उत्पादन-अंत नियम",
    rateRuleCurrent:"दर कटऑफ़ (जैसा चलाया गया)", floatOnsetRule:"फ्लोट प्रारंभ (3 अलार्म दिन, 0.6 m³/d बैकस्टॉप)",
    vfdHoldRule:"VFD-hold (ड्राइव FI को 0.6 पर 2-spm सीमा तक रोकती है, वहाँ 3 अलार्म दिनों बाद कूप खींचें)",
    waterCutTm:"जल अंश", floatIndexTm:"रॉड-फ्लोट सूचकांक", floatBanner:"रॉड फ्लोट कर रहे हैं — संचालक कूप खींच रहा है",
    alarmDefaultText:"रॉड फ्लोटिंग जोखिम — SPM घटाएँ",
    vfdHoldBanner:"VFD पंप को धीमा करता है — रॉड सीमा पर रोके गए",
    floatPolicyLabel:"रॉड-फ्लोट प्रतिक्रिया",
    floatPolicyPull:"3 अलार्म दिनों बाद कूप खींचें",
    floatPolicyPullDesc:"पंप गति पर चलता रहता है; फ्लोट अलार्म लगातार 3 दिन बजने पर संचालक रॉड खींचकर पुनः भाप देता है।",
    floatPolicyVfdHold:"सीमा बनाए रखने हेतु पंप धीमा करें (VFD-hold)",
    floatPolicyVfdHoldDesc:"एक चर-गति ड्राइव यूनिट को धीमा कर फ्लोट सूचकांक को 0.6 पर बनाए रखती है, 2 spm की न्यूनतम सीमा तक; उस सीमा पर भी 3 अलार्म दिनों बाद ही कूप खींचा जाता है। अनुशंसित नीति।",
    floatPolicyVfdThenPull:"धीमा करें, फिर खींचें",
    floatPolicyVfdThenPullDesc:"VFD-hold जैसा, परंतु ड्राइव प्रारंभिक गति के लगभग आधे तक ही धीमी होती है, उसके बाद संचालक कूप खींचता है।",
    floatPolicyNone:"कोई फ्लोट प्रतिक्रिया नहीं (रॉड फ्लोट करते हैं)",
    floatPolicyNoneDesc:"फ्लोट की परवाह किए बिना पंप गति पर चलता रहता है; चक्र केवल दर-सीमा पर समाप्त होता है — कोई विफलता लागत मॉडल नहीं है।",
    floatPolicyBakedNote:"यहाँ दिखाई गई भौतिकी हमेशा VFD-hold (अनुशंसित नीति) पर चलाई जाती है; अन्य विकल्प केवल संचालक व्याख्या का पूर्वावलोकन हैं।",
    conFiRule:"फ्लोट-अलार्म नियम (लगातार दिन)", conPrlCap:"शिखर PRL बनाम इकाई रेटिंग",
    floatingIndex:"फ्लोटिंग सूचकांक", classifierP:"वर्गीकारक प्रायिकता",
    failureThreshold:"विफलता सीमा",
    grpFuelCycle:"इस चक्र में ईंधन एवं कार्बन", grpMech:"यांत्रिक अखंडता",
    hsdBurned:"एचएसडी डीज़ल खपत", co2Steam:"भाप उत्पादन से CO₂", co2Intensity:"CO₂ तीव्रता",
    maxFI:"अधिकतम फ्लोटिंग सूचकांक", oilBbl:"कुल प्राप्त तेल",
    grpSteamAvoided:"बची भाप — सम-तेल प्रतितथ्य",
    grpFuelGen:"ईंधन — डीज़ल-चालित जनित्र", grpCarbon:"कार्बन", grpProgramme:"कार्यक्रम स्तर",
    oilAtOptimum:"अनुकूलतम पर तेल",
    steamNeeded:"उतने तेल हेतु वर्तमान प्रचलन को आवश्यक भाप",
    steamInjectedOpt:"अनुकूलतम पर वास्तव में अंतःक्षेपित भाप",
    steamAvoided:"बची भाप", dieselPerT:"प्रति टन भाप डीज़ल", dieselAvoided:"बचा डीज़ल",
    priceBand:"ईंधन मूल्य परास", valueAvoidedCycle:"प्रति चक्र बचत मूल्य",
    energyAvoided:"बची ईंधन ऊर्जा", co2AvoidedCycle:"प्रति चक्र टाला गया CO₂",
    valueAvoided:"बचत मूल्य", co2AvoidedShort:"टाला गया CO₂",
    runId:"संचालन क्रमांक", computedAt:"गणना समय", simulator:"अनुकारक", parameters:"प्राचल फ़ाइल",
    validation:"सत्यापन", dataSource:"डेटा स्रोत", recCol:"अनुशंसा", optimiserCol:"अनुकूलक",
    fuelBasisRow:"ईंधन आधार", carbonBasis:"कार्बन आधार", programmeScale:"कार्यक्रम स्तर",
    grpPredicted:"अनुमानित परिणाम", sorSurrogate:"भाप-तेल अनुपात (त्वरित मॉडल अनुमान)",
    sorTwin:"भाप-तेल अनुपात (लागू मानों पर ट्विन पुनःगणना)", maxFItwin:"अधिकतम फ्लोटिंग सूचकांक (ट्विन)",
    marginSurrogate:"प्रति चक्र-दिन मार्जिन, सकल (त्वरित मॉडल अनुमान)",
    marginTwin:"प्रति चक्र-दिन मार्जिन, सकल (लागू मानों पर ट्विन पुनःगणना)",
    marginIncrSurrogate:"प्रति चक्र-दिन मार्जिन, वृद्धिशील — उद्देश्य (त्वरित मॉडल अनुमान)",
    marginIncrTwin:"प्रति चक्र-दिन मार्जिन, वृद्धिशील — उद्देश्य (लागू मानों पर ट्विन पुनःगणना)",
    grpBounds:"खोज सीमाएँ — css / srp खंड",
    conFloatProb:"फ्लोटिंग प्रायिकता p(float)", conMaxFI:"अधिकतम फ्लोटिंग सूचकांक, ट्विन",
    conFailures:"अपेक्षित रॉड विफलताएँ",
    satisfied:"संतुष्ट", violated:"उल्लंघन", atLowerBound:"निम्न सीमा पर", atUpperBound:"उच्च सीमा पर",
    heldByDesign:"सीमा पर बनाए रखा (डिज़ाइन अनुसार)",
    parameter:"प्राचल", value:"मान", sourceCol:"स्रोत", openConsole:"कूप अनुकरण में खोलें",
    reviewRec:"अनुशंसा देखें", readBasis:"मॉडल आधार पढ़ें",
    /* P0 additions — simplification pass, 26 Sep 2026 */
    approxChip:"अनुमानित रन — सारांश पर नहीं भेजा गया",
    noSaving:"इस रन की तुलना में कोई बचत नहीं",
    sorNotAchievable:"यह SOR संभव नहीं — इस SPM पर रॉड फ्लोट करेगी",
    checkInSimulator:"सिम्युलेटर में जाँचें",
    seeFullRec:"पूरी सिफ़ारिश देखें",
    riskLow:"कम", riskHigh:"उच्च",
    crore:"करोड़",
    simCheckTarget:"→ सिम्युलेटर जाँच",
    openSimLoad:"सिम्युलेटर खोलें और लोड करें →",
    modelDetails:"मॉडल विवरण (विशेषज्ञों हेतु) ▸",
    chipOk:"ठीक", chipWatch:"ध्यान दें", chipAlarm:"चेतावनी",
    tmDayLabel:"दिन", tmResLabel:"भंडार ताप", tmViscLabel:"श्यानता",
    tmOilLabel:"तेल दर", tmRodLabel:"रॉड भार", tmPumpLabel:"पंप",
    rodsSafe:"रॉड सुरक्षित —", rodsFloat:"रॉड फ्लोट करेगी —", ofLimit:"सीमा 0.60 में", reduceSpeed:"गति घटाएँ",
    dynoTitle:"रॉड भार बनाम स्ट्रोक (सांकेतिक)", dynoMeta:"सांकेतिक आकार — मापा गया डायनाकार्ड नहीं",
    modelFloatProb:"मॉडल फ्लोटिंग प्रायिकता",
    printLabel:"प्रिंट करें",
    consoleSubtitle:"अगले CSS चक्र की सेटिंग आज़माएँ — दिन-प्रतिदिन तापमान, तेल दर और रॉड भार देखें।",
    optSubtitle:"रॉड सुरक्षित रखते हुए प्रति चक्र-दिन वृद्धिशील मार्जिन अधिकतम करने वाली भाप, वेलहेड दाब, कटऑफ़, स्ट्रोक लंबाई और पंप गति खोजता है। सोक 10 दिन क्षेत्र प्रचलन पर स्थिर।",
    replayShort:"चक्र चलाकर देखें (14 s)",
    howCalculated:"ये आँकड़े कैसे निकले ▸",
    checkInSimTitle:"सिम्युलेटर में जाँचें",
    checkInSimBody:"क्या ये सेटिंग जाँच हेतु सिम्युलेटर में लोड करें? कूप को कुछ नहीं भेजा जाता।",
    vsMidpoint:"मध्य-बिंदु आधार की तुलना में",
    superseded:"पुराना",
    simChip:"अनुकरण — कूप का लाइव डेटा नहीं",
    /* "Your prices" — re-pricing panel, 26 Sep 2026 */
    yourPrices:"आपकी कीमतें",
    dieselPriceLabel:"डीज़ल कीमत ₹/लीटर",
    bulkDiscountLabel:"थोक छूट %",
    oilRealisationLabel:"तेल प्राप्ति ₹/बैरल",
    resetBaseCase:"आधार स्थिति पर रीसेट",
    baseCase:"आधार स्थिति",
    atBaseCasePrices:"आधार स्थिति पर",
    atFy25Realisation:"OIL की FY25 वास्तविक प्राप्ति पर",
    atYourPrices:"आपकी कीमतों पर",
    incrementalTag:"वृद्धिशील — ठंडे उत्पादन के ऊपर",
    presetFy25:"OIL FY25 वास्तविक प्राप्ति ($78.09)",
    presetFy26Floor:"FY26 योजना-न्यूनतम ($65)",
    notReoptimisedNote:"निर्धारित मान आधार स्थिति की कीमतों पर अनुकूलित थे; यहाँ मार्जिन को पुनः-मूल्यांकित किया गया है, पुनः-अनुकूलित नहीं।",
    pricesPanelIntro:"नीचे दी गई इन तीन कीमतों से मार्जिन की पुनर्गणना करता है। भाप, प्राप्त तेल, CO₂ और चक्र अवधि भौतिकी हैं — ये नहीं बदलतीं।",
    setPricesLink:"अपनी कीमतें तय करें → (अवलोकन)",
    /* "Calibrate from field data" — twin/calibrate.py, 26 सितंबर 2026 */
    calibNav:"क्षेत्र-डेटा से अंशांकन",
    calibDemoTitle:"प्रदर्शन — संश्लेषित डेटा, क्षेत्र डेटा नहीं",
    calibWhatRecovered:"फ़िट ने क्या पुनर्प्राप्त किया",
    calibColBefore:"पहले (डिफ़ॉल्ट)", calibColFitted:"फ़िट किया गया", calibColTruth:"छुपा सत्य (केवल डेमो)",
    calibColIdentified:"पहचान की स्थिति",
    idWell:"अच्छी तरह पहचाना गया", idPartly:"आंशिक रूप से पहचाना गया", idRatio:"केवल अनुपात के रूप में",
    calibFitQuality:"फ़िट गुणवत्ता (प्रेक्षित बनाम फ़िट)",
    calibBeforeAfterTitle:"अंशांकन से पहले → बाद की अनुशंसा",
    calibBeforeAfterNote:"भौतिकी ट्विन पर वही ग्रिड खोज; सोक 10 दिन पर स्थिर।",
    calibBefore:"अंशांकन से पहले (डिफ़ॉल्ट प्राचल)", calibAfter:"अंशांकन के बाद",
    calibChartTitle:"प्रति चक्र प्रेक्षित बनाम अनुकरित तेल",
    calibResidTitle:"अवशेष — तेल, प्रति चक्र % त्रुटि",
    calibUseOwnTitle:"अपना डेटा उपयोग करें",
    calibSchemaTitle:"आवश्यक कॉलम",
    calibDownloadTemplate:"टेम्पलेट डाउनलोड करें",
    calibChooseFile:"CSV फ़ाइल चुनें",
    calibRowsParsed:"पंक्तियाँ पढ़ी गईं",
    calibPreview:"पूर्वावलोकन",
    calibLiveButton:"अंशांकन करें",
    calibLoadIntoSim:"अंशांकित अनुशंसा सिम्युलेटर में लोड करें",
    calibYourResultTitle:"आपका अंशांकन परिणाम",
    calibrationRow:"अंशांकन", calibrationDefault:"डिफ़ॉल्ट स्थिरांक (अभी तक क्षेत्र डेटा नहीं)",
    calibrateLink:"अंशांकन करें →",
    calibAxisObs:"प्रेक्षित तेल (m³)", calibAxisSim:"अनुकरित तेल (m³)", calibAxisErr:"oil_m3 % त्रुटि (प्रेक्षित बनाम फ़िट)",
    /* Computed dynamometer card (surface + pump), 26 Sep 2026 */
    cardTypeFullPump:"पूर्ण पंपिंग", cardTypeFluidPound:"तरल आघात (फ्लुइड पाउंड)",
    cardTypeViscous:"गाढ़ा तेल — श्यान खिंचाव", cardTypeGas:"गैस हस्तक्षेप",
    cardTypeRodFloat:"रॉड फ्लोट — क्लैंप पृथक",
    meanFullPump:"हर स्ट्रोक में पंप बैरल पूरी तरह भरता है — सामान्य संचालन।",
    meanFluidPound:"पंप कुएँ की आवक दर से तेज़ चलता है — प्लंजर हर स्ट्रोक में आंशिक रूप से खाली बैरल में गिरता है।",
    meanViscous:"गाढ़ा, ठंडा तेल पूरे स्ट्रोक में रॉड पर खिंचाव डालता है — भार बढ़ता है, विफलता जोखिम नहीं।",
    meanGas:"मुक्त गैस पंप की रिहाई को नरम कर गोल आकार देती है — प्रभावी भराव अकेले तरल से कम दिखता है।",
    meanRodFloat:"रॉड यूनिट जितनी तेज़ी से चलाता है उतनी तेज़ी से गिर नहीं पातीं — गति घटाएँ।",
    dynoStressTest:"12-SPM तनाव परीक्षण",
    dynoShutInNote:"कोई कार्ड नहीं — पंप बंद है (इंजेक्शन/सोक चरण)।",
    /* Measured-card classifier ("मापा गया कार्ड जाँचें"), 27 Sep 2026 */
    dynoClfNeedInput:"पहले CSV फ़ाइल चुनें या पंक्तियाँ चिपकाएँ।",
    dynoClfBadTable:"वह तालिका पढ़ी नहीं जा सकी।",
    dynoClfLiveOk:"भौतिकी-प्रशिक्षित मॉडल के विरुद्ध वर्गीकृत।",
    dynoClfMockOk:"निकटतम बेक्ड कार्ड से मिलान (अनुमानित, ऑफ़लाइन)।",
    dynoClfNoMatch:"ऑफ़लाइन जाँच उपलब्ध नहीं — यह वक्र किसी भी बेक्ड कार्ड से पर्याप्त मेल नहीं खाता कि सुरक्षित रूप से लेबल किया जा सके। प्रशिक्षित वर्गीकारक हेतु API शुरू करें।",
    dynoClfFailed:"वह कार्ड वर्गीकृत नहीं किया जा सका।",
    dynoClfIsApiUp:"— क्या API चल रहा है? python -m uvicorn api.main:app --port 8000 (README देखें)।",
    dynoClfFileError:"वह फ़ाइल पढ़ी नहीं जा सकी।",
    /* Field-level steam scheduler (27 Sep 2026) */
    fieldGanttFoot:"एक पंक्ति = क्षेत्र का एकमात्र भाप जनरेटर; प्रत्येक रंगीन खंड एक कूप का इंजेक्शन + 1-दिन स्थानांतरण है। कूप एवं सेटिंग्स हेतु खंड पर होवर करें।",
    fieldDeferredReasonGeneratorCommitted:"जनरेटर समय इस अनुसूची में आगे के उच्च-मूल्य कार्यों हेतु प्रतिबद्ध है",
    fieldDeferredHeading:"इस वर्ष स्थगित",
    fieldServedHeading:"इस वर्ष सेवित"
  }
};
const T = (k) => (STR[LANG] && STR[LANG][k]) || STR.en[k] || k;
const langAttr = () => (LANG === "hi" ? "hi" : "en");
const L = (k) => '<span lang="' + langAttr() + '">' + T(k) + "</span>";

/* Pages register extra work the attribute walk cannot reach. */
const REFRESH_HOOKS = [];
function onLangChange(fn){ REFRESH_HOOKS.push(fn); }

function applyLang(l, persist){
  LANG = (l === "hi") ? "hi" : "en";
  document.documentElement.lang = LANG;
  $$("[data-en]").forEach(function(n){
    const en = n.dataset.en, hin = n.dataset.hi || en;
    if (n.classList.contains("bi")){
      const p = LANG === "hi" ? hin : en, s = LANG === "hi" ? en : hin;
      const pl = LANG === "hi" ? "hi" : "en", sl = LANG === "hi" ? "en" : "hi";
      n.innerHTML = '<span class="bi-p" lang="' + pl + '">' + p + '</span><span class="bi-s" lang="' + sl + '">' + s + "</span>";
    } else {
      n.textContent = LANG === "hi" ? hin : en;
      n.setAttribute("lang", LANG);
    }
  });
  const be = $("langEN"), bh = $("langHI");
  if (be) be.setAttribute("aria-pressed", String(LANG === "en"));
  if (bh) bh.setAttribute("aria-pressed", String(LANG === "hi"));
  if (persist) BUS.set("lang", LANG);
  syncNavLinks();
  REFRESH_HOOKS.forEach(function(fn){ try { fn(); } catch (e) { console.error(e); } });
}

/* ---------- THEME -------------------------------------------------------- */
let THEME = "light";
const THEME_HOOKS = [];
function onThemeChange(fn){ THEME_HOOKS.push(fn); }
function applyTheme(t, persist){
  THEME = (t === "dark") ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", THEME);
  const bl = $("themeLight"), bd = $("themeDark");
  if (bl) bl.setAttribute("aria-pressed", String(THEME === "light"));
  if (bd) bd.setAttribute("aria-pressed", String(THEME === "dark"));
  if (persist) BUS.set("theme", THEME);
  syncNavLinks();
  THEME_HOOKS.forEach(function(fn){ try { fn(); } catch (e) { console.error(e); } });
}
/* Read a live design token — the single source of truth for chart colours. */
function tok(name){
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/* ---------- CROSS-PAGE STATE BUS ----------------------------------------- */
/* localStorage under one namespaced key, so staged set-points, the last run,
   the recommendation and the optimiser history survive navigation. Every
   page still boots correctly with an empty store (file:// with storage
   blocked included) — see defaults in bootRun(). */
const BUS = {
  KEY: "bgw.v4",
  all: function(){
    try { return JSON.parse(localStorage.getItem(BUS.KEY) || "{}") || {}; }
    catch (e) { return {}; }
  },
  get: function(k, dflt){
    const v = BUS.all()[k];
    return (v === undefined || v === null) ? dflt : v;
  },
  set: function(k, v){
    const s = BUS.all();
    s[k] = v;
    try { localStorage.setItem(BUS.KEY, JSON.stringify(s)); } catch (e) {}
    return s;
  },
  clear: function(){ try { localStorage.removeItem(BUS.KEY); } catch (e) {} }
};

/* ---------- LIVE API: background-job polling ----------------------------
   /api/optimize, /api/recommend/physics and /api/calibrate all start an
   async job (a Bayesian search, a physics grid, or a fit can take a few
   seconds) and return {job_id, status_url}; the job is polled through
   GET /api/jobs/{id} until it lands on "done" or "error". Shared here so
   every page that starts a job (currently the optimiser; the console's
   apiSimulate() and the dyno panel stay synchronous, well under a second)
   polls and reports progress the same way. */
async function apiStartJob(path, body){
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || ("HTTP " + res.status));
  return data.job_id;
}
async function apiPollJob(jobId, onTick){
  const started = Date.now();
  for (;;){
    const res = await fetch(API_BASE + "/api/jobs/" + jobId);
    const job = await res.json();
    if (!res.ok) throw new Error(job.error || ("HTTP " + res.status));
    if (onTick) onTick(job, Date.now() - started);
    if (job.status === "done") return job.result;
    if (job.status === "error") throw new Error(job.error || "job failed");
    await new Promise(function(r){ setTimeout(r, 400); });
  }
}
/* Start a job at `path` and poll it to completion in one call. */
async function apiRunJob(path, body, onTick){
  const jobId = await apiStartJob(path, body);
  return apiPollJob(jobId, onTick);
}

/* The run currently "on the books" — what every page reports on. */
function currentRun(){
  const r = BUS.get("run", null);
  if (r && r.summary && r.controls) return r;
  return {
    runId: "SIM-" + istDateCode() + "-01",
    computedAt: null,
    controls: Object.assign({}, REF_INPUTS),
    summary: Object.assign({}, REF_SUMMARY),
    applied: false,
    preApplySOR: null,
    source: MOCK ? "baked" : "api"
  };
}
function saveRun(run){ BUS.set("run", run); }

/* ---------- HEADLINE MONEY LINES (shared: card + result strip) ----------
   Team-lead call, 26 Sep 2026: UQ found the recommendation beats the
   assumed baseline in 96% of 1,500 paired draws — but that baseline's own
   1.3 m³/d cutoff and 2-spm VFD floor carry most of that: give both sides
   the same 0.6 backstop and it is 84% (median ₹2.5k/day); let the VFD run
   below 2 spm, as our own cold well does, and the set-point gain is ≈ ₹0
   (technical re-score #2, 27 Sep 2026). Lead with what is ROBUST — the
   paired delta and P(better), WITH that caveat — and print the absolute ₹
   figure as "at these prices", with a live re-pricing panel underneath it.
   Never imply the recommendation itself changes with price: only its
   margin is re-priced. */
/* rev 13 (wave 5) headline convention (TIER1_PROGRESS_LOG.md §12.6/§12.14):
   the headline is now the SAME-POLICY net-cash gain — the recommendation
   vs the assumed baseline (b), BOTH operated the SAME way. The
   default baseline operation is VFD-hold (the recommended policy); a
   "Compare against a baseline that..." toggle (optimiser page only) can
   switch the assumed baseline operation to "pulls at the first alarm" or
   "does nothing about float", each pulling from OPT_RESULT.fairGain[policy].
   The overview page always shows the default (vfd_hold) card — the two
   pages can never disagree unless an engineer has deliberately toggled the
   optimiser's assumption. See UQ's own header comment for the resolved
   P(net cash>0) vs P(incremental>0) counterfactual statistic. */
const BASELINE_POLICY_TOGGLE = {
  vfd_hold: { en: "slows (VFD-hold)", hi: "धीमा करता है (VFD-hold)" },
  pull:     { en: "pulls",            hi: "कूप खींचता है" },
  none:     { en: "does nothing",     hi: "कुछ नहीं करता" }
};
function headlineDeltaLine(baselinePolicy){
  const policy = baselinePolicy || "vfd_hold";
  const g = OPT_RESULT.fairGain[policy];
  const p = pct(UQ.decks.fy25_realisation.pGtBaselineSamePolicy[policy]);
  const sorBase = policy === "pull" ? BASELINE_PUBLISHED.SOR_pull : (policy === "none" ? BASELINE_PUBLISHED.SOR_none : BASELINE_PUBLISHED.SOR);
  const sorPct = signed((OPT_SUMMARY.SOR_t_per_m3 - sorBase) / sorBase * 100, 0);
  if (policy === "vfd_hold"){
    return (LANG === "hi")
      ? inrSignedPlus(g.fy25) + " प्रति चक्र-दिन हमारी अनुमानित आधार रेखा की तुलना में (वही VFD-hold नीति) · उस आधार रेखा के 1.3 m³/d cutoff पर निर्भर होते हुए 84–96% परिदृश्यों में बेहतर · अगर ड्राइव 2 spm से नीचे चल सके (हमारे अपने cold well जैसा) तो लाभ ≈ ₹0 · भाप प्रति m³ तेल " +
        fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) + " (" + sorPct + "%)"
      : inrSignedPlus(g.fy25) + " per cycle-day vs our assumed baseline (same VFD-hold policy) · 84–96% of scenarios depending on that baseline's cutoff · ≈ ₹0 if the drive can run below 2 spm · steam per m³ oil " +
        fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) + " (" + sorPct + "%)";
  }
  /* rev 13.1 (re-score N5): "run the same way" is wrong once the baseline's
     assumed operation is deliberately NOT what the canonical recommendation
     does -- the whole point of the "pulls"/"does nothing" modes is that the
     baseline is operated DIFFERENTLY. Name the baseline's own operation
     instead. */
  if (policy === "pull"){
    return (LANG === "hi")
      ? inrSignedPlus(g.fy25) + " प्रति चक्र-दिन उस आधार रेखा की तुलना में जो पहले अलार्म पर कूप खींचती है (ज्यादातर संचालन नियम, सेट-पॉइंट नहीं) · " +
        nf(UQ.nDraws) + " परिदृश्यों में " + p + " में बेहतर · भाप प्रति m³ तेल " +
        fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) + " (" + sorPct + "%)"
      : inrSignedPlus(g.fy25) + " per cycle-day vs a baseline that pulls at the first alarm (mostly the operating rule, not the set-point) · better in " +
        p + " of " + nf(UQ.nDraws) + " scenarios · steam per m³ oil " +
        fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) + " (" + sorPct + "%)";
  }
  return (LANG === "hi")
    ? inrSignedPlus(g.fy25) + " प्रति चक्र-दिन उस आधार रेखा की तुलना में जो फ्लोट के बारे में कुछ नहीं करती · " +
      nf(UQ.nDraws) + " परिदृश्यों में " + p + " में बेहतर · भाप प्रति m³ तेल " +
      fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) + " (" + sorPct + "%)"
    : inrSignedPlus(g.fy25) + " per cycle-day vs a baseline that does nothing about float · better in " +
      p + " of " + nf(UQ.nDraws) + " scenarios · steam per m³ oil " +
      fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) + " (" + sorPct + "%)";
}
/* Second line: what changes if the baseline is instead assumed to be
   operated the OTHER two ways -- the honest "the operating rule moves more
   money than the set-point" finding, and the unpriced-risk caveat. Always
   shows both alternates regardless of which policy the toggle currently
   has selected (so an engineer sees the full three-way comparison even
   while looking at one of them). */
function baselinePolicyAltLine(baselinePolicy){
  const policy = baselinePolicy || "vfd_hold";
  const pullG = OPT_RESULT.fairGain.pull.fy25, noneG = OPT_RESULT.fairGain.none.fy25;
  if (policy === "pull"){
    return (LANG === "hi")
      ? "यदि आधार रेखा इसके बजाय VFD-hold से धीमी होती (उचित तुलना): " + inrSignedPlus(OPT_RESULT.fairGain.vfd_hold.fy25) +
        "। यदि उसके रॉड बस फ्लोट करते रहें: " + inrSignedPlus(noneG) + " — हम अभी रॉड विफलताओं की कीमत नहीं लगाते।"
      : "If that baseline instead slows on the VFD (the fair comparison): " + inrSignedPlus(OPT_RESULT.fairGain.vfd_hold.fy25) +
        ". If its rods are simply left floating: " + inrSignedPlus(noneG) + " — we do not price rod failures.";
  }
  if (policy === "none"){
    return (LANG === "hi")
      ? "यदि आधार रेखा इसके बजाय पहले अलार्म पर कूप खींचती: " + inrSignedPlus(pullG) + " (ज्यादातर संचालन नियम)। यदि वह VFD-hold से धीमी होती (उचित तुलना): " +
        inrSignedPlus(OPT_RESULT.fairGain.vfd_hold.fy25) + "।"
      : "If that baseline is instead pulled at the first alarm: " + inrSignedPlus(pullG) + " (mostly the operating rule). If it instead slows on the VFD (the fair comparison): " +
        inrSignedPlus(OPT_RESULT.fairGain.vfd_hold.fy25) + ".";
  }
  return (LANG === "hi")
    ? "यदि उस कार्य को इसके बजाय पहले अलार्म पर खींचा जाए: " + inrSignedPlus(pullG) + " (ज्यादातर संचालन नियम)। यदि उसके रॉड बस फ्लोट करते रहें: " +
      inrSignedPlus(noneG) + " — हम अभी रॉड विफलताओं की कीमत नहीं लगाते।"
    : "If that job is instead pulled at the first alarm: " + inrSignedPlus(pullG) + " (mostly the operating rule). If its rods are simply left floating: " +
      inrSignedPlus(noneG) + " — we do not price rod failures.";
}
/* "Where the gain comes from" — Shapley decomposition of the SAME-POLICY
   (VFD-hold) gain vs baseline (b), FY25 deck (ml/models/gain_decomposition.json
   decomposition_to_canonical_rec_by_baseline_policy.vfd_hold). Stroke now
   dominates (a shorter stroke lets the VFD hold the float line longer at
   the 2-spm floor); SPM is barely a lever once the VFD does the slowing. */
/* rev 13.1 (re-score item 5/N5): policy-aware. Under the default (vfd_hold)
   toggle mode the baseline and the recommendation run the SAME policy, so
   the gain decomposes over the 5 set-point levers only (ml/models/
   gain_decomposition.json decomposition_to_canonical_rec_by_baseline_policy.
   vfd_hold). In "pull" mode the baseline is operated DIFFERENTLY from the
   recommendation, so a 6th, dominant lever appears -- the operating-rule
   switch itself (.pull, float_policy share 67.5%) -- which is exactly the
   re-score's own finding ("68% of this gain is the operating-rule switch,
   not the set-point") and is shown as such. In "none" mode the same 6-lever
   split has a NEGATIVE, dominant policy term and a cutoff share over 100%
   (switching FROM "no response" TO VFD-hold costs oil, and the other levers
   more than make up for it) -- a 3-term percent breakdown would misstate
   that, so the line is hidden there per dashboard/README.md's own "else
   hide" rule; the alt line above already carries the +2,622 number. */
function gainDecompositionLine(baselinePolicy){
  const policy = baselinePolicy || "vfd_hold";
  if (policy === "none") return "";
  if (policy === "pull"){
    return (LANG === "hi")
      ? "लाभ कहाँ से आता है: संचालन-नियम बदलाव (पहले खींचने से VFD-hold) 68% · स्ट्रोक 20% · spm 5% · कटऑफ 4% · भाप 4% — ज्यादातर संचालन नियम, सेट-पॉइंट नहीं"
      : "Where the gain comes from: the operating-rule switch (pulling → VFD-hold) 68% · stroke 20% · spm 5% · cutoff 4% · steam 4% — mostly the operating rule, not the set-point";
  }
  const s = OPT_RESULT.decomposition.fy25_share;
  const strokePct = Math.round(s.stroke_in * 100), cutoffPct = Math.round(s.cutoff_m3d * 100), steamPct = Math.round(s.steam_t * 100);
  return (LANG === "hi")
    ? "लाभ कहाँ से आता है: स्ट्रोक " + strokePct + "% · कटऑफ " + cutoffPct + "% · भाप " + steamPct +
      "% — छोटा स्ट्रोक VFD को फ्लोट रेखा को देर तक बनाए रखने देता है"
    : "Where the gain comes from: stroke " + strokePct + "% · cutoff " + cutoffPct + "% · steam " + steamPct +
      "% — the shorter stroke lets the VFD hold the float line longer at the 2-spm floor";
}
/* Third line (muted): the absolute net-cash figures on all three decks, the
   recommendation's own uncertainty (p50 under the FY25 deck), and the
   injectivity gate that decided 89 over 85 kgf/cm². */
function absoluteMarginLine(){
  const fy25 = OPT_SUMMARY.margin_incremental_inr_per_cycle_day;
  const p65 = OPT_SUMMARY_FY26_INCREMENTAL;
  const levies = OPT_SUMMARY_LEVIES_INCREMENTAL;
  const p50 = UQ.decks.fy25_realisation.recommended.netCash_p50;
  const line1 = (LANG === "hi")
    ? "निरपेक्ष शुद्ध नकद: FY25 पर " + inrSignedPlus(fy25) + "/दिन (अनिश्चितता के तहत p50 " + inrSignedPlus(p50) + ") · $65 पर " +
      inrSignedPlus(p65) + " · रॉयल्टी + उपकर के बाद " + inrSignedPlus(levies) +
      " · 89 kgf/cm² पर इंजेक्शन-योग्य (मार्जिन ≥ 300 kPa)"
    : "Absolute: net cash " + inrSignedPlus(fy25) + "/d FY25 (p50 under uncertainty " + inrSignedPlus(p50) + ") · $65 " +
      inrSignedPlus(p65) + " · net of royalty + cess " + inrSignedPlus(levies) +
      " · injectable at 89 kgf/cm² (margin ≥ 300 kPa)";
  const uqRange = inrSigned(UQ.decks.fy25_realisation.recommended.netCash_p10) + "–" + inrSigned(UQ.decks.fy25_realisation.recommended.netCash_p90);
  const line2 = (LANG === "hi")
    ? "अनिश्चितता सीमा (शुद्ध नकद, FY25 deck): " + uqRange + " (1,500 परिदृश्य)"
    : "Range (uncertainty, net cash, FY25 deck): " + uqRange + " (1,500 scenarios)";
  return line1 + '<br><span style="opacity:0.8">' + line2 + "</span>";
}
/* Conservative variant — the SAME 6-D set-points, VFD-hold, operated with
   the hold-and-pull line at FI &gt; 0.5 instead of 0.6 (still 3 alarm days),
   NOT a different set-point and NOT "never alarm" (TIER1_PROGRESS_LOG.md
   §11.9 item 5). A small toggle row, off by default, so it never competes
   with the primary recommendation for attention. */
function conservativeToggleHtml(){
  const en = "Conservative (VFD holds and pulls at FI &gt; 0.5): " + inrSignedPlus(CONSERVATIVE_SUMMARY.margin_incremental_inr_per_cycle_day) + "/cycle-day (FY25) · " +
    inrSignedPlus(CONSERVATIVE_SUMMARY_FY26_INCREMENTAL) + "/cycle-day ($65) · " + inrSignedPlus(CONSERVATIVE_SUMMARY_LEVIES_INCREMENTAL) + "/cycle-day (levies)";
  const hi = "रूढ़िवादी (FI &gt; 0.5 पर VFD रोकता और खींचता है): " + inrSignedPlus(CONSERVATIVE_SUMMARY.margin_incremental_inr_per_cycle_day) + "/चक्र-दिन (FY25) · " +
    inrSignedPlus(CONSERVATIVE_SUMMARY_FY26_INCREMENTAL) + "/चक्र-दिन ($65) · " + inrSignedPlus(CONSERVATIVE_SUMMARY_LEVIES_INCREMENTAL) + "/चक्र-दिन (levies)";
  return '<details class="rc-conservative"><summary lang="' + langAttr() + '">' +
    (LANG === "hi" ? "रूढ़िवादी विकल्प ▸" : "Conservative variant ▸") + '</summary>' +
    '<div class="rc-line" lang="' + langAttr() + '">' + (LANG === "hi" ? hi : en) + "</div></details>";
}
/* SOR line — headline stays GROSS (steam / all oil, the literature
   convention every benchmark in this repo uses); incremental SOR (steam /
   oil OVER the cold baseline) is shown alongside as the economic ratio.
   rev 13: incremental == gross here (shut-in cold cf), so the two numbers
   are identical -- shown anyway, so the convention is visible. */
/* rev 13.1 (item 5): the SOR line now moves with the toggle too -- "pulls"
   and "does nothing" compare against that baseline's OWN SOR under that
   operation (BASELINE_PUBLISHED.SOR_pull / .SOR_none), exactly like
   headlineDeltaLine()'s sorBase, so the SOR printed here always matches the
   "steam per m³ oil" figure in the headline above it. */
function sorDeltaLine(baselinePolicy){
  const policy = baselinePolicy || "vfd_hold";
  const sorBase = policy === "pull" ? BASELINE_PUBLISHED.SOR_pull : (policy === "none" ? BASELINE_PUBLISHED.SOR_none : BASELINE_PUBLISHED.SOR);
  return (LANG === "hi")
    ? "भाप-तेल अनुपात " + fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) +
      " (सकल) · वृद्धिशील " + fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_incremental, 2)
    : "SOR " + fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_t_per_m3, 2) +
      " (gross) · incremental " + fmt(sorBase, 2) + " → " + fmt(OPT_SUMMARY.SOR_incremental, 2);
}

/* ---------- RECOMMENDATION CARD (shared: overview hero + optimiser) ------ */
/* One card, one action, one saving, one risk line — the answer before the
   evidence (SPEC principle 1). Shared so the overview and optimiser pages
   can never state the recommendation differently from each other. */
function riskWordKey(fi){
  return fi > RISK_LIMIT ? "exceeded" : (fi > 0.4 ? "elevated" : "riskLow");
}
/* rev 13: the 6-control recommendation + the VFD-hold operating rule, in
   plain words — steam, wellhead pressure, stroke, SPM, soak, and what ends
   the cycle. "The VFD slows the pump to hold the float line, pull only
   after 3 alarm days at the floor" is the mechanism the whole
   recommendation exploits (TIER1_PROGRESS_LOG.md §12), not an afterthought,
   so it is stated as plainly as the set-points themselves.
   baselinePolicy (optional, default "vfd_hold"): which baseline operation
   the headline delta is computed against -- the optimiser page's "Compare
   against a baseline that..." toggle passes this through; the overview
   page always calls with the default, so the two pages read the same
   unless an engineer has deliberately toggled the optimiser's assumption. */
function renderRecCard(elId, AV, currentFI, baselinePolicy){
  const el = $(elId);
  if (!el) return;
  const policy = baselinePolicy || "vfd_hold";
  const steam = nf(OPT_APPLIED.steam_t, 0), pressure = fmt(OPT_APPLIED.p_wellhead_kgf_cm2, 0),
        stroke = fmt(OPT_APPLIED.stroke_in, 0), spm = fmt(OPT_APPLIED.spm, 1),
        cutoff = fmt(OPT_APPLIED.cutoff, 2);
  const hi = LANG === "hi";
  const line1 = hi
    ? "BGW-07 के अगले CSS चक्र हेतु सुझाव: भाप <b>" + steam + " t</b> · <b>" + pressure + " kgf/cm²</b> वेलहेड · <b>" +
      stroke + "-इंच</b> स्ट्रोक · <b>" + spm + " SPM</b> शुरुआत · सोक <b>10 दिन</b> (क्षेत्र प्रचलन) · <b>VFD-hold</b>: पंप को फ्लोट सीमा (0.6) पर बनाए रखने हेतु धीमा करें, 2 spm तक, और वहाँ 3 अलार्म दिनों बाद ही कूप खींचें (" +
      cutoff + " m³/d बैकस्टॉप)"
    : "Recommended for BGW-07, next CSS cycle: Steam <b>" + steam + " t</b> · <b>" + pressure + " kgf/cm²</b> wellhead · <b>" +
      stroke + "-in</b> stroke · <b>" + spm + " SPM</b> start · Soak <b>10 d</b> (field practice) · <b>VFD-hold</b>: slow the pump to hold the float index at 0.6, down to a 2-spm floor, and pull only after 3 alarm days there (" +
      cutoff + " m³/d backstop)";
  const marginLine = headlineDeltaLine(policy);
  const altLine = baselinePolicyAltLine(policy);
  const decompLine = gainDecompositionLine(policy);
  const uqLine = absoluteMarginLine();
  const sorLine = sorDeltaLine(policy);
  const line2 = hi
    ? "प्रति चक्र बचत: <b>" + nf(AV.dieselL, 0) + " L डीज़ल</b> (" + nf(AV.steamT, 0) + " t भाप) · ₹" +
      fmt(AV.crLow, 2) + "–" + fmt(AV.crHigh, 2) + " करोड़ · " + nf(AV.co2T, 0) + " t CO₂"
    : "Saves per cycle: <b>" + nf(AV.dieselL, 0) + " L diesel</b> (" + nf(AV.steamT, 0) + " t steam) · ₹" +
      fmt(AV.crLow, 2) + "–" + fmt(AV.crHigh, 2) + " crore · " + nf(AV.co2T, 0) + " t CO₂";
  const line3 = hi
    ? "रॉड फ्लोट नियम: VFD जानबूझकर फ्लोट-अलार्म रेखा पर पंप को रोके रखता है — 2-spm सीमा पर 3 लगातार दिनों बाद खींचा जाता है (दिन " +
      OPT_SUMMARY.produce_days + ") — यह एक अनियंत्रित जोखिम नहीं, डिज़ाइन है"
    : "Rod-float rule: the VFD deliberately holds the pump at the float-alarm line — pulled after 3 consecutive alarm days at the 2-spm floor (day " +
      OPT_SUMMARY.produce_days + ") — by design, not a runaway risk";
  el.innerHTML =
    '<div class="rc-line rc-action" lang="' + langAttr() + '">' + line1 + "</div>" +
    '<div class="rc-line rc-margin" lang="' + langAttr() + '">' + marginLine + "</div>" +
    '<div class="rc-line rc-altbase" lang="' + langAttr() + '">' + altLine + "</div>" +
    (decompLine ? '<div class="rc-line rc-decomp" lang="' + langAttr() + '">' + decompLine + "</div>" : "") +
    '<div class="rc-line rc-uq muted" lang="' + langAttr() + '">' + uqLine + "</div>" +
    conservativeToggleHtml() +
    '<div class="rc-line" lang="' + langAttr() + '">' + sorLine + "</div>" +
    '<div class="rc-line" lang="' + langAttr() + '">' + line2 + "</div>" +
    '<div class="rc-line" lang="' + langAttr() + '">' + line3 + "</div>" +
    '<div class="rc-buttons">' +
      '<a class="btn btn-primary" href="console.html" data-xlink="console.html" lang="' + langAttr() + '">' + T("checkInSimulator") + "</a>" +
      '<a class="btn" href="optimizer.html" data-xlink="optimizer.html" lang="' + langAttr() + '">' + T("seeFullRec") + "</a>" +
    "</div>";
  syncNavLinks();
}

/* ---------- APP CHROME --------------------------------------------------- */
function syncNavLinks(){
  /* Carry language + theme in the URL as well as localStorage, so the demo
     survives a machine with site data disabled and QC can deep-link. */
  const q = "?lang=" + LANG + "&theme=" + THEME;
  $$(".ab-nav a").forEach(function(a){
    const base = (a.getAttribute("data-href") || a.getAttribute("href") || "").split("?")[0];
    a.setAttribute("data-href", base);
    a.setAttribute("href", base + q);
  });
  $$("a[data-xlink]").forEach(function(a){
    const base = a.getAttribute("data-xlink");
    a.setAttribute("href", base + q);
  });
}

function markActiveNav(page){
  $$(".ab-nav a").forEach(function(a){
    if (a.dataset.nav === page) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
}

/* status bar: BGW-07 · computed 17:47 IST · set-points · applied/staged · source.
   Build-session detail (params rev, physics-test tag, run ID) lives in the
   footer's Data lineage column instead — see footer.html — so the most
   prominent strip on every page carries only what an operator needs. */
function renderStatusBar(pageKey){
  const el = $("statusBar");
  const run = currentRun();
  const fr = $("footRunId");
  if (fr) fr.textContent = run.runId;
  /* Print-only header (P1-10): well, date, run and the operational-use
     caveat at the top of page 1 — the app bar, status bar and buttons are
     hidden in @media print (core.css §18). */
  const ph = $("printHeader");
  if (ph){
    const stamp = run.computedAt ? istStamp(new Date(run.computedAt)) : istStamp(BOOT_TIME);
    ph.innerHTML =
      "<b>BGW-07</b>" + " · " + stamp + " · " + run.runId +
      '<span class="ph-flag">Simulation — not for operational use</span>';
  }
  if (!el) return;
  const stamp = run.computedAt ? istStamp(new Date(run.computedAt)) : istStamp(BOOT_TIME);
  const sep = '<span class="sb-sep">/</span>';
  const staged = BUS.get("staged", null);
  el.innerHTML =
    '<span class="sb-page" lang="' + langAttr() + '">' + T(pageKey) + "</span>" + sep +
    "<span>BGW-07</span>" + sep +
    '<span>computed ' + stamp + "</span>" + sep +
    "<span>" + settingsLabel(run.controls) + "</span>" +
    (run.applied ? sep + '<span class="tag pass">applied</span>' : "") +
    (staged ? sep + '<span class="tag warn">staged</span>' : "") +
    '<span class="sb-right">' +
      '<span class="src-chip' + (MOCK ? "" : " live") + '"><span class="dot"></span>' +
        '<span lang="' + langAttr() + '">' + (MOCK ? T("simChip") : "Live API · " + TWIN_VERSION) + "</span>" +
      "</span>" +
    "</span>";
}

const BOOT_TIME = new Date();

/* ---------- PLOTLY THEME ------------------------------------------------- */
const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };
const FONT_FAMILY = '"Segoe UI",-apple-system,Roboto,Helvetica,Arial,sans-serif';
let CHART_FS = 13;
function chartTheme(){
  return {
    paper: tok("--bg-panel"), plot: tok("--bg-panel"),
    grid: tok("--rule"), line: tok("--border"),
    tick: tok("--text-faint"), axis: tok("--text-dim"),
    t: tok("--chart-t"), mu: tok("--chart-mu"), q: tok("--chart-q"),
    barHi: tok("--chart-bar-hi"), bar2: tok("--chart-bar-2"), bar3: tok("--chart-bar-3"),
    bandInject: tok("--chart-band-inject"), bandSoak: tok("--chart-band-soak"), bandProduce: tok("--chart-band-produce"),
    hoverBg: tok("--bg-panel"), hoverBorder: tok("--border"), hoverText: tok("--text"),
    text: tok("--text"), text2: tok("--text-2"),
    green: tok("--green"), amber: tok("--amber"), red: tok("--red"), faint: tok("--text-faint")
  };
}
const CFONT = (color) => ({ family: FONT_FAMILY, color: color || chartTheme().tick, size: CHART_FS });
const M = (over) => Object.assign({ t: 8, r: 12, l: (window.innerWidth >= 1600 ? 60 : 52), b: 38 }, over || {});
function hoverLabel(th){
  return { bgcolor: th.hoverBg, bordercolor: th.hoverBorder, font: { family: FONT_FAMILY, size: 11, color: th.hoverText } };
}

/* ---------- BOOT --------------------------------------------------------- */
function bootChrome(pageKey, navKey){
  const q = new URLSearchParams(location.search);
  const qTheme = q.get("theme");
  applyTheme(qTheme || BUS.get("theme", "light"), false);
  const qLang = q.get("lang");
  applyLang(qLang || BUS.get("lang", "en"), false);
  markActiveNav(navKey);
  renderStatusBar(pageKey);
  /* rev 13.1 (item 7): the footer's provenance/rev/date now come from these
     constants, not hand-typed HTML, so a re-bake can't leave a stale
     "physics rev 12 · 27 Sep" behind again (dashboard/README.md §11). */
  const fpr = $("footParamsRev"); if (fpr) fpr.textContent = PARAMS_REV;
  const fphr = $("footPhysicsRev"); if (fphr) fphr.textContent = PHYSICS_REV_SHORT;
  const fbd = $("footBuildDate"); if (fbd) fbd.textContent = BUILD_DATE;
  const bl = $("themeLight"), bd = $("themeDark"), be = $("langEN"), bh = $("langHI");
  if (bl) bl.addEventListener("click", function(){ applyTheme("light", true); });
  if (bd) bd.addEventListener("click", function(){ applyTheme("dark", true); });
  if (be) be.addEventListener("click", function(){ applyLang("en", true); });
  if (bh) bh.addEventListener("click", function(){ applyLang("hi", true); });
  onLangChange(function(){ renderStatusBar(pageKey); });
}
