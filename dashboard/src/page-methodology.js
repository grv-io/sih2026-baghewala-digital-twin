/* =========================================================================
   MODEL BASIS — a reference document. The only dynamic content is the
   parameter table (rendered from the same constants the twin uses, so it
   cannot drift from the rest of the product) and the TOC highlight.
   ========================================================================= */
bootChrome("__PAGE_KEY__", "__NAV_KEY__");

/* This page carries no charts in build.js (plotly:false — the doc-body is
   entirely tabular/typeset, see README §2) EXCEPT the two small calibration
   charts added below, which are the one chart this reference document
   needs. Rather than change build.js's per-page Plotly flag, the two charts
   load the SAME vendor-then-cdnjs script build.js's own PLOTLY constant
   uses, on demand, the first time a chart actually needs it — so every
   other page's byte count and load path is unaffected. */
const PLOTLY_WAITERS = [];
function ensurePlotly(cb){
  if (window.Plotly){ cb(); return; }
  PLOTLY_WAITERS.push(cb);
  if (ensurePlotly._loading) return;
  ensurePlotly._loading = true;
  const flush = function(){ PLOTLY_WAITERS.splice(0).forEach(function(fn){ try { fn(); } catch (e){ console.error(e); } }); };
  const s = document.createElement("script");
  s.src = "vendor/plotly.min.js";
  s.onload = flush;
  s.onerror = function(){
    const s2 = document.createElement("script");
    s2.src = "https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.3/plotly.min.js";
    s2.onload = flush;
    document.head.appendChild(s2);
  };
  document.head.appendChild(s);
}

const PARAM_ROWS = [
  { g: "Reservoir" },
  ["Initial temperature",      P.T_initial_C,        "°C",     "OIL internal presentation"],
  ["Initial pressure",         P.P_initial_kPa,      "kPa",         "OIL internal presentation"],
  ["Depth (TD)",               P.depth_m,            "m",           "SPE-23APOG-535203"],
  ["Net thickness",            P.thickness_m,        "m",           "GEOHORIZONS 2015 (net pay; PS gross column ~50 m — conflict noted below)"],
  ["Porosity",                 P.porosity,           "—",      "GEOHORIZONS 2015"],
  ["Thermal conductivity",     P.k_thermal_W_mK,     "W/m·K",  "literature-typical sandstone"],
  ["Rock heat capacity",       P.rock_heat_capacity_Jm3K, "J/m³·K", "literature-typical sandstone"],
  ["Drainage radius",          100.0,                "m",           "rev 5 — composite-radial inflow outer boundary (calibrated)"],
  ["Well radius",              0.1,                  "m",           "rev 5 — typical, not Baghewala-specific"],
  { g: "Fluid" },
  ["API gravity",              P.api_gravity,        "°API",   "SPE-23APOG-535203 (PS states 17–19°)"],
  ["Reference viscosity",      P.mu_ref_cP,          "cP",          "SPE-23APOG-535203"],
  ["Reference temperature",    P.T_ref_C,            "°C",     "SPE-23APOG-535203"],
  ["Walther A, B",             null,                 "—",      "rev 5 — null, fitted from two points at run time (current default)"],
  ["Andrade A, B",             null,                 "—",      "superseded 26 Sep — reachable only for the A1 benchmark comparison"],
  ["Formation water cut",      0.45,                 "—",      "[ASSUMPTION] no field datum — native water cut of the reservoir liquid (rev 11/12 water-cut STATE model; the produced-stream water cut declines from ~0.87 toward this as condensate flows back, driving the emulsion inversion and the float-onset timing)"],
  ["Condensate recovery fraction", 0.7,              "—",      "[ASSUMPTION] fraction of injected steam mass produced back as condensate — #2 UQ driver on the recommendation's incremental margin"],
  { g: "Thermal (physics v3, rev 7)" },
  ["Boberg–Lantz δ factor",    0.5,                  "—",      "SOURCED, not a free calibration knob: the ½ in Boberg &amp; Lantz's own δ = (1/2Q)∫Q̇ₚdt (SPE PEH Vol. V ch. 15, Eqs. 15.70/15.73); also the only energy-conserving value with no conduction"],
  { g: "Steam" },
  ["Injection temperature",    P.T_injection_C,      "°C",     "OIL internal presentation"],
  ["Quality",                  P.steam_quality,      "—",      "OIL internal presentation"],
  ["Latent heat",              P.latent_heat_Jkg,    "J/kg",        "steam tables at 290 °C (rev 5)"],
  ["Injection rate",           P.steam_injection_rate_tpd, "t/d",   "OIL internal presentation"],
  { g: "Wellbore (rev 5)" },
  ["Heat loss per 1,000 m",    0.18,                 "frac",        "VIT-insulated tubing, typical"],
  ["Quality at sandface",      0.55,                 "frac of wellhead", "typical for VIT over this depth"],
  { g: "Economics (rev 8/9, Economics v2 + FY25 price deck)" },
  ["Oil price — FY25 realisation (base case)", 5992.0, "₹/bbl", "CONFIRMED OIL India Annual Report 2024-25 ($78.09/bbl) − $10/bbl heavy-oil discount [ASSUMPTION], × ₹88/$"],
  ["Oil price — FY26 planning floor (preset)", 4840.0, "₹/bbl", "the CMD's forward planning number ($65/bbl), not a realisation — kept as a named downside preset"],
  ["Fixed opex per day",       5000.0,               "₹/d",    "[ASSUMPTION] well-site opex excl. power; cancels in the incremental margin unless the cold well itself is uneconomic"],
  ["Surface efficiency",       0.60,                 "—",      "[TYPICAL] prime-mover-to-polished-rod efficiency, converts polished-rod kWh to grid kWh"],
  ["Steam cost — bulk (base case)", 5856.0,          "₹/t",    "diesel bulk-purchase price, −30% off Rajasthan retail [CALIBRATED, UNSOURCED discount]"],
  ["Steam cost — full retail",  8366.0,              "₹/t",    "Rajasthan retail pump price, no discount — a named sensitivity preset"],
  ["Fixed cost per cycle",     1.5e6,                "₹",      "[ASSUMPTION] rig/workover cost per CSS cycle"],
  { g: "Sucker-rod pump" },
  ["Stroke length",            P.stroke_m,           "m",           "rev 5 — OIL internal presentation"],
  ["Rod length",               P.depth_m,            "m",           "= pump setting depth (assumption)"],
  ["Rod mass",                 P.rod_mass_kgm,       "kg/m",        "API grade-D rod string"],
  ["Plunger diameter",         P.plunger_d_m,        "m",           "rev 5 — typical, not Baghewala-specific"],
  ["Pump speed range",         null,                 "spm",         "4.0 – 12.0, mechanical envelope"],
  ["Pump speed practice band", null,                 "spm",         "3.0 – 6.0 — what the optimiser actually searches"],
  ["Pump-speed floor",         2.0,                  "spm",         "rev 5 — declining schedule never drops below this"],
  { g: "Cycle design ranges" },
  ["Steam volume range",       null,                 "t",           nf(RANGES.steam_t.min) + " – " + nf(RANGES.steam_t.max)],
  ["Soak period range",        null,                 "d",           RANGES.soak_days.min + " – " + RANGES.soak_days.max + " (held at 10 d in the current recommendation)"],
  ["Economic cutoff range",    null,                 "m³/d",   fmt(RANGES.cutoff.min, 2) + " – " + fmt(RANGES.cutoff.max, 2)]
];

function renderParams(){
  $("paramBody").innerHTML = PARAM_ROWS.map(function(r){
    if (r.g) return '<tr class="grp"><td colspan="4">' + r.g + "</td></tr>";
    const val = (r[1] === null) ? '<span class="muted">&mdash;</span>'
      : (Math.abs(r[1]) >= 1e5 ? Number(r[1]).toExponential(2) : nf(r[1], (r[1] % 1 === 0) ? 0 : (Math.abs(r[1]) < 1 ? 3 : 1)));
    return '<tr><td class="k">' + r[0] + '</td><td class="v">' + val +
      '</td><td class="muted">' + r[2] + '</td><td class="k">' + r[3] + "</td></tr>";
  }).join("");
}

/* ml/uq.py build_uncertain_inputs() -- ranges and one-line "why", kept in
   sync with that module's docstrings by hand (re-copy after any range
   change there). */
const UQ_INPUT_ROWS = [
  ["srp.s_cold (cold-well skin factor)", "0 – 8", "5",
    "#1 tornado driver (rev 12). No field datum; decides how productive -- and how expensive to beat -- the cold, unstimulated counterfactual is."],
  ["fluid.condensate_recovery_frac", "0.5 – 0.9", "0.7",
    "#2 tornado driver (rev 12). Fraction of injected steam mass produced back as condensate — sets WHEN the produced stream crosses the emulsion-inversion point."],
  ["fluid.formation_water_cut", "0.30 – 0.60", "0.45",
    "#3 tornado driver (rev 12). No field datum; native water cut of the reservoir liquid — the other input that sets when the float onset happens. bl_delta_factor itself is FIXED at 0.5 (sourced physics v3), not varied."],
  ["reservoir.thickness_m", "8 – 20 m", "12.0 m",
    "TIER1_PROGRESS_LOG.md §4.6/§11.4: the net-pay band over which BGW-8's 5–6× uplift and 15–40 bbl/d peak band are reproduced (AOF retuned to 0.56 at 12.0 m)."],
  ["economics.diesel_bulk_discount_frac", "0.0 – 0.30", "0.30",
    "Spans bulk (₹5,856/t) to full-retail (₹8,366/t) steam cost."],
  ["economics.oil_price_inr_per_bbl", "±15% of the running deck's base", "₹5,992/bbl (FY25) or ₹4,840/bbl (FY26 floor)",
    "±15% around whichever price deck is being baked (FY25 realisation is the base case; the $65 FY26 floor is a second, separately-baked UQ pass)."],
  ["economics.opex_inr_per_day", "₹2,500 – 7,500", "₹5,000",
    "±50% around the [ASSUMPTION] fixed well-site opex; cancels in the incremental margin unless the cold well itself is uneconomic (opex &gt; ~₹12.5k/d)."],
  ["fluid.mu_ref_cP", "8,000 – 15,000 cP", "11,500 cP",
    "SPE-23APOG-535203's full published range (base is the tighter internal-deck midpoint)."],
  ["reservoir.P_current_kPa", "7,400 – 9,400 kPa", "9,400 kPa",
    "[ASSUMPTION, injectivity-derived, optimistic edge] current (pre-cycle) reservoir pressure — no Baghewala datum (top OIL data ask)."],
  ["srp.stroke_m + plunger_d_m", "±10%", "×1.0",
    "Pump geometry is typical, not Baghewala-specific; ±10% is a plausible as-built tolerance."]
];

function renderUncertaintyInputs(){
  $("uqInputBody").innerHTML = UQ_INPUT_ROWS.map(function(r){
    return "<tr><td class=\"v\"><code>" + r[0] + "</code></td><td class=\"v\">" + r[1] +
      "</td><td class=\"muted\">" + r[2] + "</td><td class=\"k\">" + r[3] + "</td></tr>";
  }).join("");
}

function uqBandRow(label, b){
  const cell = function(v){ return (v === null || v === undefined) ? "<span class=\"muted\">—</span>" : inrSigned(v); };
  return "<tr><td class=\"k\">" + label + "</td><td class=\"v\">" + cell(b && b.netCash_p10) +
    "</td><td class=\"v\">" + cell(b && b.netCash_p50) + "</td><td class=\"v\">" + cell(b && b.netCash_p90) + "</td></tr>";
}
function renderUncertaintyBands(){
  const decks = UQ.decks;
  $("uqBandBody").innerHTML =
    uqBandRow("Baseline (b), published-practice, VFD-hold (1,300 t / 10 d / 1.3 m³/d / 5 spm / 86 in / 91 kgf/cm²)", decks.fy25_realisation.baseline_b) +
    uqBandRow("Recommendation, rev 13 (1,000 t / 10 d / 0.60 m³/d backstop / 4.5 spm start / 64 in / 89 kgf/cm², VFD-hold)", decks.fy25_realisation.recommended);
  const floorBody = $("uqBandBodyFloor");
  if (floorBody){
    floorBody.innerHTML =
      uqBandRow("Baseline (b)", decks.fy26_floor.baseline_b) +
      uqBandRow("Recommendation", decks.fy26_floor.recommended);
  }
  const leviesBody = $("uqBandBodyLevies");
  if (leviesBody){
    leviesBody.innerHTML =
      uqBandRow("Baseline (b)", decks.fy25_net_of_levies.baseline_b) +
      uqBandRow("Recommendation", decks.fy25_net_of_levies.recommended);
  }

  const pFy25 = decks.fy25_realisation, pFy26 = decks.fy26_floor, pLevies = decks.fy25_net_of_levies;
  $("uqProbLine").innerHTML =
    "<b>Paired probabilities</b> (" + nf(UQ.nDraws) + " draws, seed " + UQ.seed + ", SAME float policy on both sides — the robust headline): " +
    "P(recommended net cash/cycle-day &gt; baseline (b), both VFD-hold) = <b>" + pct(pFy25.pGtBaselineSamePolicy.vfd_hold) +
    "</b> (FY25) / <b>" + pct(pFy26.pGtBaselineSamePolicy.vfd_hold) + "</b> ($65) / <b>" + pct(pLevies.pGtBaselineSamePolicy.vfd_hold) + "</b> (levies) &middot; " +
    "P(recommended SOR &lt; baseline (b) SOR) = <b>" + pct(UQ.pRecommendedSorLtBaseline) +
    "</b> (holds on every deck — the SOR comparison is price-independent). If the baseline instead pulls on the first alarm: <b>" +
    pct(pFy25.pGtBaselineSamePolicy.pull) + "</b> (FY25); if it has no float response at all: <b>" + pct(pFy25.pGtBaselineSamePolicy.none) +
    "</b> — a minority of scenarios, since a float-safe recommendation is compared against a baseline that is not paying the (unpriced) cost of floating rods.";

  $("uqCounterfactualNote").innerHTML =
    "<b>The counterfactual statistic, resolved (wave 5).</b> An earlier draft printed &ldquo;P(incremental margin/day &gt; 0) = 0.034&rdquo; " +
    "right next to a FY25 net-cash p50 of +₹1,132/day — inconsistent on its face. Computed directly from the 1,500-draw sample at the " +
    "recommended point: <b>P(net cash &gt; 0)</b> = " + pct(pFy25.recommended.pNetCashPositive) + " (FY25) / " + pct(pFy26.recommended.pNetCashPositive) +
    " ($65) / " + pct(pLevies.recommended.pNetCashPositive) + " (levies); <b>P(incremental &gt; 0, vs a shut-in cold well)</b> = " +
    pct(pFy25.recommended.pIncrementalPositive) + " (FY25) / " + pct(pFy26.recommended.pIncrementalPositive) + " ($65) / " + pct(pLevies.recommended.pIncrementalPositive) +
    " (levies). The 0.034 was the <b>net-of-levies deck's</b> P(net cash &gt; 0) figure, mis-paired against the FY25 rupee line and against the wrong " +
    "metric (net cash, not incremental) — the same species of deck-mixing bug the rev-12 headline had. <b>Convention adopted:</b> P(net cash &gt; 0) is the " +
    "&ldquo;positive cash vs a shut-in cold well&rdquo; statistic, always labelled as such; P(recommended &gt; baseline, same policy) is the robust headline " +
    "(above); P(incremental &gt; 0) is the stricter, unpaired reading, shown but never the headline. Net cash (<code>margin_with_opex_inr_per_cycle_day</code>) " +
    "is revenue − steam cost − fixed workover cost − power cost − opex, per cycle-day, with NO cold-well counterfactual subtracted; incremental additionally " +
    "nets out the cold well's own cash for the same window (0 under the default &ldquo;policy&rdquo; convention, since the cold well's floating index exceeds " +
    "the alarm line under its own float policy at the base 45% water cut).";

  /* Why the product's headline leads with the paired delta, not the absolute
     net cash — this is the one place that states the reasoning, not just the
     numbers (English-only prose, per the Tier-3 policy in README §4: units,
     acronyms and this kind of engineering argument are never translated). */
  $("uqHeadlineNote").innerHTML =
    "<b>Why the headline leads with the paired delta, not the absolute net cash.</b> P(recommended &gt; baseline, same policy) reads " +
    pct(pFy25.pGtBaselineSamePolicy.vfd_hold) + " (FY25) / " + pct(pFy26.pGtBaselineSamePolicy.vfd_hold) + " ($65) / " + pct(pLevies.pGtBaselineSamePolicy.vfd_hold) +
    " (levies) because it is a PAIRED comparison — both set-points see the same draw's physics under the SAME operating policy, so the shared uncertainty " +
    "(formation water cut, condensate recovery, diesel discount, oil price, the cold well's own skin factor, …) cancels out of the difference. P(net cash " +
    "&gt; 0) at the recommendation alone reads only " + pct(pFy25.recommended.pNetCashPositive) + " (FY25 deck) because that is an UNPAIRED question about one " +
    "absolute number, which does not get to cancel anything — it is exposed to every input at once, above all the cold heavy-oil viscosity and the cold " +
    "well's own skin factor (the #1/#2 drivers, mu_ref_cP and s_cold). The overview and recommendation pages' headline is therefore the robust figure (the " +
    "same-policy delta and its high win-rate), with the absolute net-cash ₹/day printed underneath, muted, as a base-case (FY25) reference alongside the " +
    "$65 and net-of-levies figures. The “Your prices” panel on the overview page re-runs this same net-cash formula, in-browser, at whatever diesel price, " +
    "bulk discount and oil realisation an engineer enters (including the named presets) — it re-PRICES the physics (unchanged); it does not re-run the " +
    "optimiser, so the recommended set-points themselves never move.";
}

function renderUncertaintyTornado(){
  $("uqTornadoBody").innerHTML = UQ.topDrivers.map(function(d, i){
    return "<tr><td class=\"v\">" + (i + 1) + "</td><td class=\"k\" lang=\"" + langAttr() + "\">" +
      (LANG === "hi" ? d.hi : d.en) + "</td><td class=\"v\">" + inrSigned(d.atLow) + " → " + inrSigned(d.atHigh) +
      " (swing " + (d.swing > 0 ? "+" : "−") + "₹" + nf(Math.abs(d.swing), 0) + "/cycle-day, r = " +
      (d.corr > 0 ? "+" : "") + d.corr.toFixed(2) + ")</td></tr>";
  }).join("");

  const top = UQ.topDrivers[0];
  $("uqHonestLine").innerHTML =
    "<b>Honest read.</b> The single largest driver of the recommendation's NET CASH variance is <b>" + top.en +
    "</b> — the cold heavy-oil viscosity, which sets both how hard the cold-well counterfactual is to beat and how " +
    "much the produce phase itself yields. The 2nd driver (the cold well's own skin factor, s_cold) is a well-level " +
    "ASSUMPTION about the unstimulated well, not a price; oil price is 3rd. Structural choices the wave-5 re-score " +
    "flagged as unsampled — the flowback mobility ratio M and the cold-well counterfactual convention (policy vs " +
    "pumpable) — rank #7/#8, comparable to the diesel discount; the injection-margin gate and the alarm-days rule " +
    "barely move it once the VFD does the slowing.";
}

function renderSurrogate(){
  const rows = [
    ["Design of experiments", "Latin hypercube, " + nf(SURROGATE.n) + " samples over all 6 controls the physics grid searches, plus float_policy as a 7th (one-hot) — steam volume, soak period, economic cutoff, pump speed, injection (wellhead) pressure and stroke length (twin/generate_data.py, physics rev 13, retrained 26 Sep 2026)"],
    ["Label generation",      "each sample run through twin.cycle.simulate_css_cycle, physics rev 13 (wave 5: operating policy as a control, fair baseline, injectivity, levies deck; produce-end rule = float onset)"],
    ["Oil regressor",         "XGBoost — target log(oil_total_m3); SOR is derived, SOR = steam_t / oil_pred, not separately trained"],
    ["Margin regressor, incremental", "XGBoost — target margin_incremental_inr_per_cycle_day (the optimiser's objective since rev 9)"],
    ["Margin regressor, gross", "XGBoost — target margin_inr_per_cycle_day (kept for reporting/continuity, not the objective)"],
    ["Classifier",            "XGBoost — target: rod-floating risk (max FI &gt; 0.60 OR alarm days &gt; 0). <b>rev 12:</b> positive-class share is ~" + pct(SURROGATE.floatPositiveShare) + " under the float-onset rule (nearly every design point runs long enough to float before its rate cutoff binds) — a genuine physics finding, treat the classifier as a weak risk-ranking signal, not a reliable binary flag"],
    ["Split",                 "80 / 20 hold-out, random_state 42, single split — no cross-validation run"],
    ["Hold-out R² (oil)",             fmt(SURROGATE.oil_r2, 3) + " overall (in-envelope, 1,000–2,000 t: " + fmt(SURROGATE.oil_r2_envelope, 3) + ")"],
    ["Hold-out R² (net cash, 1,000–2,000 t envelope)", fmt(SURROGATE.net_cash_r2, 3) + " (overall " + fmt(SURROGATE.net_cash_r2_overall, 3) + ")"],
    ["Hold-out MAE (net cash, envelope)", "± ₹" + fmt(SURROGATE.net_cash_mae, 0) + "/cycle-day"],
    ["Hold-out R² (gross margin, envelope)", fmt(SURROGATE.margin_gross_r2, 3) + " (overall " + fmt(SURROGATE.margin_gross_r2_overall, 3) + ")"],
    ["Hold-out R²/MAE (SOR, derived check)", fmt(SURROGATE.sor_r2, 3) + " / ± " + fmt(SURROGATE.sor_mae, 3) + " t/m³ (SOR = steam_t / oil_model.predict(X), not a separately trained model — a low R² here reflects the ratio's own noise, not a bad oil model)"],
    ["Classifier AUC / accuracy", fmt(SURROGATE.float_auc, 4) + " / " + fmt(SURROGATE.float_acc, 3) + " (rev 13 label: float_premature_pull — the float pull happened AND the oil rate was still ≥1.5× cutoff when it did; positive share " + pct(SURROGATE.floatPositiveShare) + ", a healthy balance, not the rev-12 label's ~95%)"],
    ["Search algorithm",      "rev 13: true-physics 6-D grid (5 controls + float policy as a 7th, categorical control) — ml/recommend_physics.py, 160,776 grid points, 12,936 simulations, no ML surrogate in the decision loop"],
    ["Objective",             "maximise margin_with_opex_inr_per_cycle_day (net cash per cycle-day, counterfactual-free) — since rev 13"],
    ["Fixed dimension",       "soak_days held at 10 d (field practice) — the twin has no interior soak optimum, so it is not searched"],
    ["Constraint",            "float feasibility under the chosen policy (alarm days ≤ css.fi_alarm_days), the polished-rod-load cap, and an injectivity margin ≥ 400 kPa (steam.min_injection_margin_kPa) — this last gate rejects every 85-kgf/cm² point, which is why the recommendation moved to 89"],
    ["Post-processing",       "the retrained ML surrogate (ml/train.py, incl. the float-policy one-hot) is kept as a fast UQ/what-if emulator, not the decision engine — at the canonical point it predicts ₹" + nf(OPT_RESULT.predicted_margin_incremental_inr_per_cycle_day, 0) + "/cycle-day net cash against the twin's ₹" + nf(OPT_SUMMARY.margin_incremental_inr_per_cycle_day, 0) + " (residual ₹" + nf(OPT_RESULT.residual_inr_per_cycle_day, 0) + ", inside the envelope MAE) — <b>the physics grid is the decision engine, the surrogate is a fast UQ / what-if emulator</b>"]
  ];
  $("surrBody").innerHTML = rows.map(function(r){
    return '<tr><td class="k" style="width:26%;white-space:nowrap">' + r[0] + '</td><td class="v">' + r[1] + "</td></tr>";
  }).join("");
}

const TEST_ROWS = [
  ["twin/thermal.py",   15, 15, 0, [], "Temperature rises during injection; heated radius grows then freezes; temperature decays toward reservoir after injection stops; more steam gives a hotter or equal peak zone; sandface enthalpy includes sensible heat; wellbore params describe the same joules; delivered heat less than wellhead heat; cylinder theta matches the numerical source integral; heated radius is a near-wellbore bubble. Physics v3 additions: BL δ's ½ is exact energy conservation with no conduction; produced-heat water enthalpy matches steam tables; oil heat capacity is about half of water's; produced heat follows PEH Eq. 15.74's stream-by-stream structure. rev 11: saturated-steam P–T state (IF97) and its consistency-warning path."],
  ["twin/viscosity.py", 5, 5, 0, [], "Reference point recovered exactly; strictly monotonic decrease with temperature; cold viscosity in thousands of cP; hot viscosity in tens of cP or less; explicit Andrade parameters honoured when supplied (kept for the A1 benchmark)."],
  ["twin/ipr.py",       9, 9, 0, [], "Rate increases as viscosity falls; cold rate uneconomically low; unstimulated well has unit uplift; uplift monotone in heated radius and bounded; zero rate at full drawdown; rate never negative; rate is live in reservoir pressure; rev 10: pressure-boost recharge and its cap at the sandface pressure."],
  ["twin/srp.py",       15, 15, 0, [], "Floating index increases with viscosity and with SPM; index bounded to [0,1]; peak rod load positive and plausible; produced rate capped by pump capacity; energy scales with load, stroke and SPM; pump lifts liquid, not oil; pump capacity at practice SPM is comparable to well rate; plus dynamometer-card support checks. rev 10/11: Pal–Rhodes emulsion drag with its 10× cap; stroke-length lever; Mills dynamic PRL against the unit rating."],
  ["twin/cycle.py",     20, 20, 0, [], "Full-cycle smoke test; cycle terminates at or below cutoff; oil rate declines monotonically once past the pump limit; pump-limited plateau then decline at low SPM; margin has an interior optimum over steam volume; SOR rises monotonically with steam volume; summary keys present; summary without params matches JSON economics; δ is computed from simulated production. Economics v2 additions: v2 keys present and gross keys unchanged; incremental basis is harsher than gross; cold baseline = cold rate × window; incremental-margin identity holds; an uneconomic cold well is shut in, in the counterfactual; energy intensity uses the corrected polished-rod energy. rev 12: the float-onset produce-end rule ends a cycle on 3 consecutive alarm days; produce_end_reason is reported correctly."],
  ["twin/dyno.py (computed dynamometer cards)", 25, 25, 0, [], "Rod taper carries the same rod weight srp.py uses; fluid load matches net lift; static limit near the ideal parallelogram; peak PRL rises with SPM; fluid-pound step appears on the downstroke; gas interference is cushioned, not sharp; rod-float signature at 10,000 cP / 12 SPM; float onset brackets the srp.py threshold; min PRL falls monotonically with viscosity; card area equals pump work plus damping (energy check); hydraulic vs. polished-rod power; CFL-bounded finite-difference scheme; grid convergence; API shape and runtime; FD peak vs. srp.py's static peak; cards trace consistently along a full cycle, hot to cold; baked-JSON structure (schema dyno_cards/v1). rev 12: the float_onset scenario key (was late_cold) picks the day the float-alarm rule first fires."],
  ["ml/dyno_classifier.py (measured-card classifier)", 18, 18, 0, [], "RandomForest trained only on physics-generated cards classifies each of the 8 baked reference cards as its own label (rev 12: rod_float / heavy_oil_viscous now both reachable at practice speeds); feature extraction is stable to resampling/noise; the model-caveat string is always attached to a result."],
  ["twin/calibrate.py (field-data recalibration loop)", 12, 12, 0, [], "Template CSV parses; default free params (rev 9: excludes bl_delta_factor — sourced physics, not a calibration knob) are formation_water_cut, aof_ref_m3d, thickness_m; a degenerate single-row upload raises a clear error; the fit is deterministic (seed 42); apply() round-trips into a fresh params copy; all three free parameters are recovered from the pseudo-real demo; the demo's hidden truth uses the sourced bl = 0.5; no bl/water-cut coupling is reported by default; opting bl back into `free` still flags the coupling; RMSE is reported for all three fitted quantities."],
  ["tests/test_hardening.py (external-review hardening)", 10, 10, 0, [], "dt-correct integration (rate columns are per-day, not summed raw); skin/K_VISC/pressure-boost sourced from params, not hard-coded; emulsion (Pal–Rhodes) viscosity feeds rod drag; P–T consistency warns rather than silently disagreeing; LHS sampling covers the full declared range; the gain-decomposition Shapley terms sum exactly to the total; the conservative-level recommendation is reported alongside the aggressive one."],
  ["tests/test_physics_wave3.py (water-cut state, pressure/stroke levers)", 24, 24, 0, [], "Water cut declines from the formation value as condensate flows back and rises again as the tank drains (a genuine state, not a constant); the emulsion-inversion water cut is respected; injection (wellhead) pressure changes the saturated-steam T–P state consistently (thermal.steam_state); stroke length changes the rod string's static loads and energy the way a longer lever should; the 5-D physics optimiser (best_settings_physics_5d) returns a feasible point on both price decks; controls_coverage correctly reports which of the 7 problem-statement controls are optimised, fixed, or represented via the SPM schedule."],
  ["tests/test_physics_wave4.py (Pal–Rhodes cap, float-onset rule, AOF retune)", 25, 25, 0, [], "Pal–Rhodes emulsion viscosity IS Brinkman below 60% water, with the 10× cap binding only near inversion; the cold well's own drag/PRL/power are reproduced to the published band; the float-onset produce-end rule (css.produce_end_rule=\"either\") ends a cycle after 3 consecutive alarm days and reports produce_end_reason correctly; the AOF retune (0.46→0.56) clears the peak-rate (15–40 bbl/d) and reference-SOR (3.0–4.6) bands simultaneously; the 5-D recommendation under the (then-default) rule is feasible (0 PRL-cap violations, 0 non-consecutive-alarm violations) on both price decks. <b>rev 13:</b> the rev-12 cold-well-pumpability xfail here is now a PASSING test — see test_physics_wave5.py's cold-counterfactual coverage below."],
  ["tests/test_physics_wave5.py (wave 5: operating policy, fair baseline, injectivity, levies deck)", 22, 21, 1,
    ["test_steam_optimum_at_the_mid_range_diesel_price_is_within_bgw8 — at the calibration-anchor diesel discount (0.15, the mid of the U[0,0.30] UQ range), the gross-margin-optimum steam slug is below BGW-8's published 1,040–1,560 t (it clears the band only at the 0.30 bulk-preset discount) — TIER1_PROGRESS_LOG.md §12.2. Read as revealed preference, OIL's actual slug sizes argue its steam is cheaper than the mid-range; not re-specified to make the test pass."],
    "The four float policies (pull/vfd_hold/vfd_then_pull/none) each drive a distinct SPM schedule and pull rule; the cold counterfactual obeys the SAME policy as the stimulated well and is correctly SHUT IN at the base 45% water cut (the rev-12 xfail's double standard is gone — this supersedes it); the smooth inversion band changes no cycle-ending day; the injectivity margin gate correctly rejects 85 kgf/cm² and selects 89; cycle.legacy_rev12_params reproduces the rev-12 bake to the digit (three cases); Shapley gain-decomposition terms sum exactly under every baseline policy; the VFD-hold reference SOR and a 500-t slug are pinned as findings against the literature band (test_vfd_hold_takes_small_slugs_below_the_literature_sor_band, not an xfail — a characterisation test) — plus the one xfail at right."],
  ["tests/test_schedule.py (field-level steam scheduler)", 21, 21, 0, [], "Exact (bitmask-subset × ERD-order) schedule is provably optimal against brute force on small instances; a well cannot start before its min-recycle window; the generator never double-books; greedy is feasible and within a bounded gap of exact; the naive fixed-set-point counterfactual is computed with no per-well tuning (rev 12: this can and does go negative field-wide under the float-onset rule) — comparison KPIs (utilisation, field margin, deferred wells) are internally consistent."],
  ["tests/test_api.py (FastAPI endpoints)", 15, 15, 0, [], "/simulate, /api/optimize (background job + poll), /api/dyno/cards, /api/dyno/classify, /calibrate and /api/schedule/demo all return the documented contract shape; a background optimise job reaches a terminal state; CORS and health/version endpoints report the current TESTS_BADGE."],
  ["tests/test_benchmarks.py", 29, 28, 1,
    ["test_soak_optimum_is_interior_in_5_to_15_days — the twin shows a small, flat, monotone soak benefit peaking at ~18 d then declining slowly, not an interior optimum inside the 5–15 d search box with a ≥2% margin over both ends (TIER1 §7.4); this is why soak is held fixed, not searched, in the current recommendation."],
    "Published-benchmark checks against Baghewala facts and analogue-field literature: reference SOR in the calibration band; SOR stays in the literature band over the steam range; first-cycle uplift matches BGW-8; uplift at BGW-8 reported slugs; peak rate inside the field envelope (rev 12: AOF retuned to clear it under the float-onset rule); produce phase is months not weeks; cycle oil in the plan envelope; steam volume has an interior margin optimum; SPM is a real lever; floating constraint binds in the high-SPM cold-tail corner; soak has a small benefit (plus the weak-lever margin-plateau check, now passing); depletion worsens SOR and no longer over-responds; depletion response is Darcy-proportional (re-specification of the old Liaohe xfail — resolved by re-deriving the expected band from Vogel/Darcy drawdown, not by widening a guess, now measured on a fixed produce window under the float-onset rule); margin positive at reference; retail diesel flips the sign; steam cost in the documented band; CO₂ per bbl reproduces published intensity; plus 3 CalGEM cross-checks and a new reference-steam-per-cycle p10–p90 check — plus the one xfail at right."]
];
/* [module, tests, passing, xfailed, [xfail name — one-line reason, ...], what is asserted].
   263 passed, 2 xfailed, 265 collected (27 Sep 2026, physics rev 13 / wave 5 —
   operating policy as a control, fair baseline, injectivity, levies deck).
   The two DECLARED gaps: soak (no meaningful interior optimum in 5–15 d,
   test_benchmarks.py) and the steam optimum at the mid-range (0.15) diesel
   discount sitting below BGW-8's published slug-size band
   (test_physics_wave5.py) — see docs/model-improvement/TIER1_PROGRESS_LOG.md
   §7.4 and §12.2. The rev-12 cold-well-pumpability xfail is RESOLVED (now a
   passing test, test_physics_wave4.py) — the cold counterfactual obeys the
   same float policy as the stimulated well, so it is correctly shut in at
   the base water cut, not "unpumpable yet producing". */
function passTag(ok, n, xfailed){
  if (xfailed) return '<span class="tag warn" title="known gap, marked xfail — see below">' + ok + "/" + n + " (" + xfailed + " xfail)</span>";
  return '<span class="tag pass">pass</span>';
}
function renderTests(){
  const total = TEST_ROWS.reduce(function(s, r){ return s + r[1]; }, 0);
  const passed = TEST_ROWS.reduce(function(s, r){ return s + r[2]; }, 0);
  const xfailed = TEST_ROWS.reduce(function(s, r){ return s + r[3]; }, 0);
  $("testBody").innerHTML = TEST_ROWS.map(function(r){
    return '<tr><td class="v"><code>' + r[0] + '</code></td><td class="v">' + r[1] +
      '</td><td class="k">' + r[5] + "</td><td>" + passTag(r[2], r[1], r[3]) + "</td></tr>" +
      (r[4].length ? '<tr><td></td><td colspan="3" class="note">' +
        r[4].map(function(x){ return "<b>xfail</b> — " + x; }).join("<br>") + "</td></tr>" : "");
  }).join("") +
  '<tr class="grp"><td>Total</td><td>' + total + '</td><td>property-based and published-benchmark checks &middot; ' +
  xfailed + ' known gap' + (xfailed === 1 ? '' : 's') + ' marked xfail (reasons above), not silently skipped</td><td><span class="tag ' +
  (passed + xfailed === total ? "pass" : "warn") + '">' + passed + " passed, " + xfailed + " xfailed</span></td></tr>";
}

/* =========================================================================
   CALIBRATE FROM FIELD DATA — twin/calibrate.py, 26 Sep 2026.
   One generic renderer (renderCalibBlock) fills both the baked demo (CALIB_
   DEMO, run through normalizeCalibResult so it is shaped exactly like an API
   response) and the "Your own data" result, once a real /calibrate call
   returns. Both read the SAME twin.calibrate.fit() output shape -- see
   core.js normalizeCalibResult().
   ========================================================================= */
const CALIB_PARAM_LABELS = {
  bl_delta_factor: ["Boberg–Lantz energy-removed factor", "BL_DELTA_FACTOR"],
  formation_water_cut: ["Formation water cut", "formation_water_cut"],
  thickness_m:     ["Net-pay thickness", "thickness_m"],
  aof_ref_m3d:     ["Cold reference rate", "AOF_REF_M3D"]
};
const CALIB_PARAM_ORDER = ["bl_delta_factor", "formation_water_cut", "thickness_m", "aof_ref_m3d"];
const CALIB_PARAM_DEC   = { bl_delta_factor: 3, formation_water_cut: 3, thickness_m: 2, aof_ref_m3d: 3 };
const CALIB_REQUIRED_COLUMNS = ["well_id", "steam_t", "soak_days", "spm", "oil_m3", "produce_days"];

function calibIdentTagHtml(k, norm){
  const tag = calibIdentTag(k, norm.correlatedPairs);
  const withNote = tag.withParam
    ? " (" + (CALIB_PARAM_LABELS[tag.withParam] ? CALIB_PARAM_LABELS[tag.withParam][1] : tag.withParam) + ")"
    : "";
  return '<span class="tag ' + tag.cls + '">' + tag.sym + ' <span lang="' + langAttr() + '">' + T(tag.key) +
    "</span>" + withNote + "</span>";
}
function renderCalibRecoveredTable(bodyId, norm){
  $(bodyId).innerHTML = CALIB_PARAM_ORDER.map(function(k){
    const label = CALIB_PARAM_LABELS[k];
    const truthCell = norm.hiddenTruth
      ? fmt(norm.hiddenTruth[k], CALIB_PARAM_DEC[k])
      : '<span class="muted">not applicable — real data</span>';
    return '<tr><td class="k">' + label[0] + ' <code class="muted">' + label[1] + "</code></td>" +
      '<td class="v">' + fmt(CALIB_DEFAULTS[k], CALIB_PARAM_DEC[k]) + "</td>" +
      '<td class="v">' + fmt(norm.fitted[k], CALIB_PARAM_DEC[k]) + "</td>" +
      '<td class="v">' + truthCell + "</td>" +
      "<td>" + calibIdentTagHtml(k, norm) + "</td></tr>";
  }).join("");
}
function calibCouplingNoteHtml(norm){
  const parts = [];
  const kc = (norm.knownCouplings && norm.knownCouplings[0]) || null;
  if (kc){
    const truthPart = (norm.hiddenTruth && kc.truth !== undefined) ? " (hidden truth ratio " + fmt(kc.truth, 3) + ")" : "";
    parts.push("<b>Why BL_DELTA_FACTOR and water cut don&rsquo;t separate.</b> These two can only be told apart " +
      "with a downhole temperature log — that is on our data request to OIL. From oil/days data alone the fit " +
      "can only recover the combination <code>" + kc.combination + "</code> &asymp; " + fmt(kc.value, 3) + truthPart +
      "; the two raw values above are not independently identified from this dataset.");
  }
  /* Any OTHER pair the report's own correlation matrix flags as effectively
     un-split (|r| >= 0.95), not already explained above by a named formula
     -- e.g. thickness_m/aof_ref_m3d, which has no closed-form ratio but is
     just as hard to separate from oil/days data alone. Generic by design,
     so a real upload's own correlations get the same honest treatment. */
  (norm.correlatedPairs || []).forEach(function(p){
    const a = Math.abs(p.correlation);
    if (a < 0.95) return;
    if (kc && p.params.every(function(k){ return kc.combination.indexOf(k) !== -1; })) return;
    const names = p.params.map(function(k){ return (CALIB_PARAM_LABELS[k] || [k])[0]; });
    parts.push("<b>" + names[0] + " and " + names[1] + "</b> are similarly hard to split from this dataset " +
      "(r &asymp; " + fmt(p.correlation, 3) + ") — an independent estimate of one (e.g. net pay from a log) would " +
      "free the other.");
  });
  return parts.join(" ");
}
function calibFitQualityLineHtml(norm){
  const r = norm.rmse || {};
  return "<b>Fit quality</b> (RMSE, observed vs fitted) &mdash; oil " + fmt(r.oil_m3_pct, 1) + "% &middot; days " +
    fmt(r.produce_days_pct, 1) + "% &middot; peak rate " + fmt(r.peak_oil_m3d_pct, 1) + "% &middot; " +
    nf(norm.nCycles, 0) + " cycles.";
}
function calibBARowHtml(labelHtml, rec){
  if (!rec) return "";
  const pinNote = rec.pinnedSteamAtUpperBound
    ? ' <span class="tag warn" title="Search-range bound -- a statement about the search box, not a physically meaningful optimum">at bound</span>' : "";
  return "<tr><td class=\"k\">" + labelHtml + "</td>" +
    '<td class="v">' + nf(rec.steam_t, 0) + " t" + pinNote + "</td>" +
    '<td class="v">' + fmt(rec.cutoff_m3d, 2) + " m³/d</td>" +
    '<td class="v">' + fmt(rec.spm, 1) + " spm</td>" +
    '<td class="v">' + fmt(rec.SOR_t_per_m3, 2) + "</td>" +
    '<td class="v">' + nf(rec.oil_total_m3, 0) + " m³</td>" +
    '<td class="v">₹' + nf(rec.margin_inr_per_cycle_day, 0) + "</td>" +
    '<td class="v">' + (Number.isFinite(rec.margin_incremental_inr_per_cycle_day) ? inrSigned(rec.margin_incremental_inr_per_cycle_day) : "—") + "</td></tr>";
}
function calibBABodyHtml(norm){
  if (norm.before) return calibBARowHtml("Before calibration (default params)", norm.before) + calibBARowHtml("After calibration", norm.after);
  return calibBARowHtml("Calibrated recommendation (after)", norm.after);
}
function calibBANoteText(norm){
  const soak = norm.after ? fmt(norm.after.soak_days, 0) : "10";
  if (norm.before){
    return "Same grid search on the physics twin (steam_t × cutoff_m3d × spm, no ML surrogate); soak held at " + soak + " d.";
  }
  return "POST /calibrate returns only the calibrated (after) recommendation for your dataset — soak held at " + soak +
    " d (the median soak_days in your file). For a worked before → after comparison at the default parameters, see the demonstration above.";
}
function renderCalibCharts(ids, norm){
  if (!norm.residualTable || !norm.residualTable.length || !$(ids.chartFit) || !$(ids.chartResid)) return;
  const th = chartTheme();
  const wells = [];
  norm.residualTable.forEach(function(r){ if (wells.indexOf(r.well_id) === -1) wells.push(r.well_id); });
  const palette = [th.barHi, th.bar2, th.bar3, th.t, th.mu, th.q];
  const colorFor = function(w){ return palette[wells.indexOf(w) % palette.length]; };

  const fitTraces = wells.map(function(w){
    const rows = norm.residualTable.filter(function(r){ return r.well_id === w; });
    return {
      type: "scatter", mode: "markers", name: w,
      x: rows.map(function(r){ return r.obs_oil_m3; }), y: rows.map(function(r){ return r.sim_oil_m3; }),
      marker: { color: colorFor(w), size: 9 },
      hovertemplate: w + "<br>obs %{x:.1f} m³<br>sim %{y:.1f} m³<extra></extra>"
    };
  });
  const allVals = norm.residualTable.reduce(function(a, r){ return a.concat([r.obs_oil_m3, r.sim_oil_m3]); }, []);
  const lo = Math.min.apply(null, allVals) * 0.92, hi = Math.max.apply(null, allVals) * 1.06;
  fitTraces.push({ type: "scatter", mode: "lines", name: "1:1", x: [lo, hi], y: [lo, hi],
    line: { color: th.faint, dash: "dot", width: 1 }, hoverinfo: "skip", showlegend: false });

  Plotly.purge(ids.chartFit);
  Plotly.newPlot(ids.chartFit, fitTraces, {
    xaxis: { title: { text: T("calibAxisObs"), font: CFONT(th.axis) }, gridcolor: th.grid, tickfont: CFONT(), range: [lo, hi], linecolor: th.line },
    yaxis: { title: { text: T("calibAxisSim"), font: CFONT(th.axis) }, gridcolor: th.grid, tickfont: CFONT(), range: [lo, hi], linecolor: th.line },
    showlegend: true, legend: { font: CFONT(th.text2), orientation: "h", y: -0.26 },
    paper_bgcolor: th.paper, plot_bgcolor: th.paper, font: CFONT(), hoverlabel: hoverLabel(th),
    margin: M({ t: 8, b: 60 })
  }, PLOTLY_CONFIG);

  const residTraces = wells.map(function(w){
    const rows = norm.residualTable.filter(function(r){ return r.well_id === w; });
    return {
      type: "scatter", mode: "markers", name: w, showlegend: false,
      x: rows.map(function(r){ return r.oil_pct_error; }), y: rows.map(function(){ return w; }),
      marker: { color: colorFor(w), size: 10 },
      hovertemplate: w + "<br>%{x:.1f}% oil error<extra></extra>"
    };
  });
  Plotly.purge(ids.chartResid);
  Plotly.newPlot(ids.chartResid, residTraces, {
    xaxis: { title: { text: T("calibAxisErr"), font: CFONT(th.axis) }, zeroline: true,
      zerolinecolor: th.line, gridcolor: th.grid, tickfont: CFONT(), linecolor: th.line },
    yaxis: { type: "category", tickfont: CFONT(th.text2), automargin: true },
    paper_bgcolor: th.paper, plot_bgcolor: th.paper, font: CFONT(), hoverlabel: hoverLabel(th),
    margin: M({ t: 8, b: 40 })
  }, PLOTLY_CONFIG);

  if ($(ids.footFit)) $(ids.footFit).textContent =
    "Colour = well. Points on the dotted line are exact matches; RMSE " + fmt(norm.rmse.oil_m3_pct, 1) + "% overall.";
  if ($(ids.footResid)) $(ids.footResid).textContent =
    "Per-cycle oil_m3 residual, observed vs the FITTED (post-calibration) twin.";
}
function renderCalibBlock(ids, norm){
  renderCalibRecoveredTable(ids.recovered, norm);
  if ($(ids.coupling)) $(ids.coupling).innerHTML = calibCouplingNoteHtml(norm);
  if ($(ids.fitQuality)) $(ids.fitQuality).innerHTML = calibFitQualityLineHtml(norm);
  if ($(ids.ba)) $(ids.ba).innerHTML = calibBABodyHtml(norm);
  if ($(ids.baNote)) $(ids.baNote).textContent = calibBANoteText(norm);
  ensurePlotly(function(){ renderCalibCharts(ids, norm); });
}
const CALIB_DEMO_IDS = {
  recovered: "calibDemoRecoveredBody", coupling: "calibDemoCouplingNote", fitQuality: "calibDemoFitQualityLine",
  ba: "calibDemoBABody", baNote: "calibDemoBANote",
  chartFit: "chartCalibDemoFit", chartResid: "chartCalibDemoResid",
  footFit: "calibDemoFitChartFoot", footResid: "calibDemoResidChartFoot"
};
const CALIB_LIVE_IDS = {
  recovered: "calibLiveRecoveredBody", coupling: "calibLiveCouplingNote", fitQuality: "calibLiveFitQualityLine",
  ba: "calibLiveBABody", baNote: "calibLiveBANote",
  chartFit: "chartCalibLiveFit", chartResid: "chartCalibLiveResid",
  footFit: "calibLiveFitChartFoot", footResid: "calibLiveResidChartFoot"
};
const CALIB_DEMO_NORM = normalizeCalibResult(CALIB_DEMO);
let calibLiveResult = null;

function refreshCalibStaticText(){
  const set = function(id, key){ if ($(id)) $(id).textContent = T(key); };
  set("calibDemoHeading", "calibDemoTitle");
  set("calibWhatRecoveredHeading", "calibWhatRecovered");
  set("calibColBeforeHead", "calibColBefore");
  set("calibColFittedHead", "calibColFitted");
  set("calibColTruthHead", "calibColTruth");
  set("calibColIdentifiedHead", "calibColIdentified");
  set("calibDemoBAHeading", "calibBeforeAfterTitle");
  set("calibFitChartTitle", "calibChartTitle");
  set("calibResidChartTitle", "calibResidTitle");
  set("calibUseOwnHeading", "calibUseOwnTitle");
  set("calibTemplateLink", "calibDownloadTemplate");
  set("btnCalibrate", "calibLiveButton");
  set("calibResultHeading", "calibYourResultTitle");
  if ($("calibSchemaNote")) $("calibSchemaNote").innerHTML =
    "<b>" + T("calibSchemaTitle") + ":</b> <code>well_id</code> (well) &middot; <code>steam_t</code> (t) &middot; " +
    "<code>soak_days</code> (d) &middot; <code>spm</code> &middot; <code>oil_m3</code> (m³) &middot; " +
    "<code>produce_days</code> (d) — all required. Optional: <code>cutoff_m3d</code> (m³/d), " +
    "<code>peak_oil_m3d</code> (m³/d), <code>sor</code> (not used by the fit). Minimum 3 cycles.";
}

/* ---------- "Use your own data" — CSV parse, MOCK preview / live POST ---- */
let calibRawText = null, calibRawFilename = "observed.csv";

function parseCsvSimple(text){
  const lines = String(text).replace(/\r/g, "").split("\n").filter(function(l){ return l.trim().length; });
  if (!lines.length) return { header: [], rows: [] };
  const header = lines[0].split(",").map(function(h){ return h.trim(); });
  const rows = lines.slice(1).map(function(line){
    const cells = line.split(",");
    const obj = {};
    header.forEach(function(h, i){ obj[h] = cells[i] !== undefined ? cells[i].trim() : ""; });
    return obj;
  });
  return { header: header, rows: rows };
}
function renderCalibPreview(header, rows){
  $("calibPreviewHead").innerHTML = header.map(function(h){ return "<th>" + h + "</th>"; }).join("");
  const shown = rows.slice(0, 8);
  $("calibPreviewBody").innerHTML = shown.map(function(r){
    return "<tr>" + header.map(function(h){ return '<td class="v">' + (r[h] === undefined ? "" : r[h]) + "</td>"; }).join("") + "</tr>";
  }).join("") + (rows.length > shown.length
    ? '<tr><td class="note" colspan="' + header.length + '">+ ' + (rows.length - shown.length) + " more row(s)</td></tr>"
    : "");
}
function handleCalibCsvText(text, filenameLabel){
  const parsed = parseCsvSimple(text);
  const missing = CALIB_REQUIRED_COLUMNS.filter(function(c){ return parsed.header.indexOf(c) === -1; });
  const statusEl = $("calibUploadStatus");
  $("btnCalibrate").disabled = true;
  $("calibPreviewWrap").hidden = true;
  calibRawText = null;
  if (missing.length){
    statusEl.className = "note warn";
    statusEl.innerHTML = "<b>Missing required column(s):</b> " + missing.join(", ") +
      ". Required: " + CALIB_REQUIRED_COLUMNS.join(", ") + ".";
    return;
  }
  if (parsed.rows.length < 3){
    statusEl.className = "note warn";
    statusEl.innerHTML = "<b>Not enough cycles.</b> Found " + parsed.rows.length + " row(s); the fit needs at least 3.";
    return;
  }
  calibRawText = text;
  calibRawFilename = filenameLabel || "observed.csv";
  renderCalibPreview(parsed.header, parsed.rows);
  $("calibPreviewWrap").hidden = false;
  $("btnCalibrate").disabled = false;
  statusEl.className = "note good";
  statusEl.innerHTML = "<b>" + nf(parsed.rows.length, 0) + " " + T("calibRowsParsed") + "</b>" +
    (filenameLabel ? " — " + filenameLabel : "") +
    (MOCK ? "<br>Fitting runs on the physics server — start the API to calibrate (see README)." : "");
}
$("calibFile").addEventListener("change", function(e){
  const f = e.target.files && e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = function(){ handleCalibCsvText(String(reader.result), f.name); };
  reader.onerror = function(){
    $("calibUploadStatus").className = "note warn";
    $("calibUploadStatus").textContent = "Could not read that file.";
  };
  reader.readAsText(f);
});
$("btnCalibrate").addEventListener("click", async function(){
  if (!calibRawText) return;
  const statusEl = $("calibUploadStatus");
  if (MOCK){
    statusEl.className = "note info";
    statusEl.innerHTML = "<b>Parsed and validated in-browser.</b> Fitting runs on the physics server — start the " +
      "API to calibrate: <code>python -m uvicorn api.main:app --port 8000</code>, set <code>MOCK = false</code> " +
      "in core.js, rebuild and reload (see README).";
    return;
  }
  const btn = this;
  btn.disabled = true;
  btn.classList.add("is-busy");
  statusEl.className = "note";
  statusEl.textContent = "Calibrating against the physics server…";
  try {
    const form = new FormData();
    form.append("file", new Blob([calibRawText], { type: "text/csv" }), calibRawFilename);
    const res = await fetch(API_BASE + "/calibrate", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
    calibLiveResult = normalizeCalibResult(data);
    renderCalibBlock(CALIB_LIVE_IDS, calibLiveResult);
    $("calibResultPanel").hidden = false;
    $("calibResultPanel").scrollIntoView({ behavior: "smooth", block: "start" });
    statusEl.className = "note good";
    statusEl.textContent = "Calibrated against " + nf(calibLiveResult.nCycles, 0) + " cycles — see your result below.";
  } catch (err){
    statusEl.className = "note warn";
    statusEl.innerHTML = "<b>Calibration failed.</b> " + err.message +
      " — is the API running? <code>python -m uvicorn api.main:app --port 8000</code> (see README).";
  } finally {
    btn.disabled = false;
    btn.classList.remove("is-busy");
  }
});
$("btnLoadCalibrated").addEventListener("click", function(){
  if (!calibLiveResult || !calibLiveResult.after) return;
  const a = calibLiveResult.after;
  BUS.set("staged", {
    steam_t: a.steam_t, soak_days: a.soak_days, cutoff: a.cutoff_m3d, spm: a.spm,
    recId: "CAL-" + istDateCode(), at: new Date().toISOString(), provenance: "calibrated"
  });
  location.href = "console.html?lang=" + LANG + "&theme=" + THEME;
});

/* ?qc=calibcsv — inject data/external/pseudo_real_cycles.csv verbatim (the
   same 8-cycle pseudo-real demo dataset baked into CALIB_DEMO above) as CSV
   text, so the parse -> validate -> preview path can be QC'd without a
   file-picker dialog. NOT re-derived from CALIB_DEMO.residualTable, which
   only carries the columns the chart needs -- this is the full file. */
const QC_CALIB_CSV =
  "well_id,steam_t,soak_days,cutoff_m3d,spm,oil_m3,produce_days,peak_oil_m3d,sor\n" +
  "BGW-D1,1200.0,7.0,0.9,4.5,508.58,260.6,2.888,2.3595\n" +
  "BGW-D1,1500.0,10.0,0.85,5.0,618.3,300.4,3.092,2.426\n" +
  "BGW-D1,1800.0,12.0,0.75,5.5,744.57,403.0,2.826,2.4175\n" +
  "BGW-D2,1000.0,8.0,1.0,4.0,403.81,217.9,2.778,2.4764\n" +
  "BGW-D2,1600.0,9.0,0.8,5.0,653.05,359.3,2.91,2.45\n" +
  "BGW-D2,2000.0,11.0,0.7,5.5,752.33,425.7,2.896,2.6584\n" +
  "BGW-D3,1300.0,10.0,0.9,4.5,552.63,290.6,2.878,2.3524\n" +
  "BGW-D3,1900.0,13.0,0.75,6.0,731.23,431.9,3.233,2.5984";
(function calibQcHook(){
  if (new URLSearchParams(location.search).get("qc") !== "calibcsv") return;
  handleCalibCsvText(QC_CALIB_CSV, "pseudo_real_cycles.csv (qc)");
})();

refreshCalibStaticText();
renderCalibBlock(CALIB_DEMO_IDS, CALIB_DEMO_NORM);

/* =========================================================================
   FIELD-LEVEL STEAM SCHEDULER (27 Sep 2026) -- ml/schedule.py.
   Baked FIELD_SCHEDULE_DEMO (core.js) paints immediately; if this page is
   NOT running from file:// (MOCK === false), a live GET /api/schedule/demo
   re-renders the section with the API's own current output. Only the
   EXACT (bitmask-subset x ERD-order) schedule is shown as a Gantt + table;
   greedy/naive appear only as comparison KPIs, to keep this one new
   section simple.
   ========================================================================= */
function normalizeScheduleResult(raw){
  if (!raw) return null;
  const live = !!(raw.exact && raw.exact.jobs && raw.exact.jobs.length && ("well_id" in raw.exact.jobs[0]));
  if (!live) return raw; // already the baked FIELD_SCHEDULE_DEMO shape
  const mapJobs = function(jobs){
    return (jobs || []).map(function(j){
      return { order: j.order, well: j.well_id, start: j.start_date, end: j.end_date,
        steam_t: j.steam_t, cutoff: j.cutoff_m3d, spm: j.spm,
        marginPerCycleDay: j.margin_incremental_inr_per_cycle_day, cycleDays: j.cycle_days };
    });
  };
  const mapPolicy = function(p){
    return {
      fieldMarginInrTotal: p.field_margin_inr_total, fieldMarginInrPerDay: p.field_margin_inr_per_day,
      generatorUtilisationPct: p.generator_utilisation_pct, steamTTotal: p.steam_t_total, co2TTotal: p.co2_t_total,
      nWellsServed: p.n_wells_served, nWellsDeferred: p.n_wells_deferred,
      jobs: mapJobs(p.jobs),
      deferred: (p.wells_deferred || []).map(function(d){ return { well: d.well_id, reason: d.reason }; })
    };
  };
  return {
    generatedAt: raw.generated_at, nWells: raw.n_wells, horizonDays: raw.horizon_days,
    generatorRateTpd: raw.generator_rate_tpd, minRecycleDays: raw.min_recycle_days, moveDays: raw.move_days,
    exact: mapPolicy(raw.exact), greedy: mapPolicy(raw.greedy), naive: mapPolicy(raw.naive),
    comparison: {
      exactVsNaivePctGain: raw.comparison.exact_vs_naive.pct_gain,
      exactVsNaiveDeltaInr: raw.comparison.exact_vs_naive.margin_inr_total_delta
    }
  };
}

let fieldScheduleNorm = normalizeScheduleResult(FIELD_SCHEDULE_DEMO);

function renderFieldGantt(ex){
  if (!$("chartFieldGantt") || !ex || !ex.jobs || !ex.jobs.length) return;
  const th = chartTheme();
  const palette = [th.barHi, th.bar2, th.bar3, th.t, th.mu, th.q, th.green, th.amber, th.red, th.bandInject, th.bandSoak, th.bandProduce];
  const traces = ex.jobs.map(function(j, i){
    const startMs = new Date(j.start + "T00:00:00Z").getTime();
    const endMs = new Date(j.end + "T00:00:00Z").getTime();
    return {
      type: "bar", orientation: "h", name: j.well, showlegend: false,
      x: [endMs - startMs], base: [j.start], y: ["Generator"],
      marker: { color: palette[i % palette.length], line: { color: th.line, width: 1 } },
      text: [j.well], textposition: "inside", insidetextanchor: "middle", textfont: { color: "#fff", size: 11 },
      hovertemplate: j.well + "<br>" + j.start + " → " + j.end + "<br>" + nf(j.steam_t) + " t &middot; " +
        fmt(j.cutoff, 2) + " m³/d &middot; " + fmt(j.spm, 1) + " spm<br>" +
        inrSigned(j.marginPerCycleDay) + "/cycle-day<extra></extra>"
    };
  });
  Plotly.purge("chartFieldGantt");
  Plotly.newPlot("chartFieldGantt", traces, {
    barmode: "overlay",
    xaxis: { type: "date", gridcolor: th.grid, tickfont: CFONT(), linecolor: th.line },
    yaxis: { type: "category", tickfont: CFONT(th.text2), automargin: true },
    paper_bgcolor: th.paper, plot_bgcolor: th.paper, font: CFONT(), hoverlabel: hoverLabel(th),
    margin: M({ t: 8, b: 40, l: 90 })
  }, PLOTLY_CONFIG);
}

function renderFieldSchedule(norm){
  if (!norm) return;
  fieldScheduleNorm = norm;
  const ex = norm.exact;
  if ($("fieldGanttFoot")) $("fieldGanttFoot").textContent = T("fieldGanttFoot");
  if ($("fieldKpiGainPct")) $("fieldKpiGainPct").textContent =
    (norm.comparison.exactVsNaivePctGain >= 0 ? "+" : "") + fmt(norm.comparison.exactVsNaivePctGain, 0) + "%";
  if ($("fieldKpiMarginPerYear")) $("fieldKpiMarginPerYear").textContent = inrSigned(ex.fieldMarginInrTotal);
  if ($("fieldKpiUtil")) $("fieldKpiUtil").textContent = fmt(ex.generatorUtilisationPct, 1);
  if ($("fieldKpiServed")) $("fieldKpiServed").textContent = ex.nWellsServed + " / " + ex.nWellsDeferred;
  if ($("fieldKpiSteamCo2")) $("fieldKpiSteamCo2").textContent = nf(ex.steamTTotal, 0) + " t / " + nf(ex.co2TTotal, 0) + " t";
  if ($("fieldKpiNaive") && norm.naive) $("fieldKpiNaive").textContent = inrSigned(norm.naive.fieldMarginInrPerDay);

  if ($("fieldScheduleBody")){
    $("fieldScheduleBody").innerHTML = ex.jobs.map(function(j){
      return "<tr><td>" + j.order + "</td><td>" + j.well + "</td><td>" + j.start + "</td>" +
        "<td class=\"num\">" + nf(j.steam_t, 0) + "</td><td class=\"num\">" + fmt(j.cutoff, 2) + "</td>" +
        "<td class=\"num\">" + fmt(j.spm, 1) + "</td><td class=\"num\">" + inrSigned(j.marginPerCycleDay) + "</td>" +
        "<td class=\"num\">" + nf(Math.round(j.cycleDays), 0) + "</td></tr>";
    }).join("");
  }
  if ($("fieldDeferredList")){
    $("fieldDeferredList").innerHTML = ex.deferred.map(function(d){
      const reason = (d.reason === "generatorCommitted")
        ? T("fieldDeferredReasonGeneratorCommitted") : d.reason;
      return "<li><b>" + d.well + "</b> — " + reason + "</li>";
    }).join("");
  }
  ensurePlotly(function(){ renderFieldGantt(ex); });
}

function initFieldSchedule(){
  renderFieldSchedule(fieldScheduleNorm);
  if (!MOCK){
    fetch(API_BASE + "/api/schedule/demo")
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(data){ if (data) renderFieldSchedule(normalizeScheduleResult(data)); })
      .catch(function(){ /* keep the baked render on any live-fetch failure */ });
  }
}

/* TOC highlight */
(function tocSpy(){
  const links = $$(".doc-toc a");
  const sections = links.map(function(a){ return document.querySelector(a.getAttribute("href")); }).filter(Boolean);
  if (!("IntersectionObserver" in window) || !sections.length){
    if (links[0]) links[0].classList.add("active");
    return;
  }
  const io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (!e.isIntersecting) return;
      links.forEach(function(a){ a.classList.toggle("active", a.getAttribute("href") === "#" + e.target.id); });
    });
  }, { rootMargin: "-100px 0px -70% 0px", threshold: 0 });
  sections.forEach(function(s){ io.observe(s); });
  if (links[0]) links[0].classList.add("active");
})();

$("btnPrint").addEventListener("click", function(){ window.print(); });
renderParams();
renderSurrogate();
renderUncertaintyInputs();
renderUncertaintyBands();
renderUncertaintyTornado();
renderTests();
initFieldSchedule();
onLangChange(function(){
  renderParams(); renderSurrogate();
  renderUncertaintyInputs(); renderUncertaintyBands(); renderUncertaintyTornado();
  renderTests();
  refreshCalibStaticText();
  renderCalibBlock(CALIB_DEMO_IDS, CALIB_DEMO_NORM);
  if (calibLiveResult) renderCalibBlock(CALIB_LIVE_IDS, calibLiveResult);
  renderFieldSchedule(fieldScheduleNorm);
});
onThemeChange(function(){
  ensurePlotly(function(){
    renderCalibCharts(CALIB_DEMO_IDS, CALIB_DEMO_NORM);
    if (calibLiveResult) renderCalibCharts(CALIB_LIVE_IDS, calibLiveResult);
    renderFieldGantt(fieldScheduleNorm && fieldScheduleNorm.exact);
  });
});
window.addEventListener("resize", function(){
  if (!window.Plotly) return;
  if ($("chartCalibDemoFit")) Plotly.Plots.resize($("chartCalibDemoFit"));
  if ($("chartCalibDemoResid")) Plotly.Plots.resize($("chartCalibDemoResid"));
  if (calibLiveResult){
    if ($("chartCalibLiveFit")) Plotly.Plots.resize($("chartCalibLiveFit"));
    if ($("chartCalibLiveResid")) Plotly.Plots.resize($("chartCalibLiveResid"));
  }
  if ($("chartFieldGantt")) Plotly.Plots.resize($("chartFieldGantt"));
});
