/* =========================================================================
   OVERVIEW — the executive result page.
   Reads the run on the books from the state bus (whatever the twin console
   last computed) and reports it against the ML optimum. Every figure here
   is derived; nothing is a typed literal.
   ========================================================================= */
bootChrome("__PAGE_KEY__", "__NAV_KEY__");

/* QC hook: ?qcprice=retail forces "Your prices" to full retail (0% bulk
   discount) before the first render, so the "at retail, the baseline goes
   loss-making" claim (methodology > Uncertainty, README §7.1) can be
   screenshotted without a live click-through. Same pattern as console's
   ?qc=alarm / optimizer's ?qc=optimized. */
(function qcPriceHook(){
  const qcp = new URLSearchParams(location.search).get("qcprice");
  if (qcp === "retail") setPrices({ diesel: ECON.hsd_inr_per_l, discount: 0, oilBbl: ECON.oil_price_inr_per_bbl });
})();

const RUN = currentRun();
const REC = BUS.get("rec", null);

/* Column A is the run being replaced once the optimum has been applied,
   otherwise the run currently on the books. Column B is always the optimum. */
const APPLIED = !!(RUN.applied && RUN.preApplySummary && RUN.preApplyControls);
const A = APPLIED
  ? { key: "manualRun",    sum: RUN.preApplySummary, ctl: RUN.preApplyControls }
  : { key: "currentCycle", sum: RUN.summary,         ctl: RUN.controls };
const B = { key: "mlOptimum", sum: OPT_SUMMARY, ctl: OPT_APPLIED };

/* Iso-oil counterfactual, per cycle. No annualisation anywhere on this page:
   days_total is a simulated producing-cycle length, not a field re-visit
   interval, so 365/days_total would manufacture a cycle count no CSS
   operation achieves. Programme figures multiply by OIL's own FY2025-26
   CSS job count and say so. */
const AV  = cycleAvoided(A.sum.SOR_t_per_m3, B.sum, B.ctl.steam_t);
const PRG = scaleToProgramme(AV, ECON.css_jobs_fy26);

/* ---------- result strip ------------------------------------------------- */
function renderStrip(){
  const drop = (A.sum.SOR_t_per_m3 - B.sum.SOR_t_per_m3) / A.sum.SOR_t_per_m3 * 100;

  $("rsFrom").textContent = fmt(A.sum.SOR_t_per_m3, 2);
  $("rsSor").textContent  = fmt(B.sum.SOR_t_per_m3, 2);
  $("rsSorSub").innerHTML =
    L(A.key) + " → " + L("asApplied") + '<span class="l2 num">' +
    settingsLabel(A.ctl) + " → " + settingsLabel(B.ctl) + "</span>";

  /* Sign and colour are DERIVED, never hard-coded — a run where the applied
     scenario is not actually better must never render as green savings. */
  const deltaEl = $("rsDelta");
  deltaEl.textContent = signed(drop, 1) + "%";
  deltaEl.classList.remove("good", "bad");
  deltaEl.classList.add(drop >= 0 ? "good" : "bad");
  $("rsDeltaSub").innerHTML =
    '<span lang="' + langAttr() + '">' + T("asAppliedOptimum") + "</span>" +
    /* rev 13.1 (item 6): SOR_improvement_pct is already negative (a SOR
       drop) -- signed() supplies its own minus sign, so a hand-typed "−"
       in front of fmt() double-signed it ("−-13.9%"). */
    '<span class="l2 num">' + signed(OPT_RESULT.SOR_improvement_pct, 1) + "% " +
    T("vsFieldPractice") + " (SOR " + fmt(BASELINE_PUBLISHED.SOR, 2) + ")</span>";

  /* Margin per cycle-day — the optimiser's actual objective (rev 9:
     INCREMENTAL over the cold, unstimulated well, at OIL's FY25 realisation
     by default). Headline is now the ROBUST paired delta (re-priced
     in-browser from "Your prices"); the sub-line spells out the
     "from → to" absolute pair the delta is built from, tagged base case /
     at your prices. */
  const prices = getPrices();
  const baseM = baselineMarginIncrementalAtPrices(prices);
  const recM  = recommendedMarginIncrementalAtPrices(prices);
  const deltaM = recM - baseM;
  const tag = pricesAreBase(prices) ? T("atFy25Realisation") : T("atYourPrices");
  const marginPct = Math.abs(baseM) > 1e-6 ? (recM - baseM) / Math.abs(baseM) * 100 : null;

  const deltaEl2 = $("rsMarginDelta");
  deltaEl2.innerHTML = inrSignedPlus(deltaM) + '<span class="u">/d</span>';
  deltaEl2.classList.remove("good", "bad");
  deltaEl2.classList.add(deltaM >= 0 ? "good" : "bad");

  /* Uncertainty sub-line -- ml/uq.py paired Monte Carlo (1,500 draws, seed
     42) at the recommended set-points, NET-CASH basis, SAME (VFD-hold)
     policy on both sides; UQ constant in core.js. Pick the deck that
     matches whichever price is actually active, and label it, so the
     number and the tag next to it always agree (rev-12 printed a $65
     probability under an FY25 label -- see UQ's own header comment). */
  const isLeviesPreset = Math.abs(prices.oilBbl - OIL_PRICE_PRESETS.fy25_net_of_levies.inr_per_bbl) < 1e-6;
  const isFy26FloorPreset = !isLeviesPreset && Math.abs(prices.oilBbl - OIL_PRICE_PRESETS.fy26_floor_65.inr_per_bbl) < 1e-6;
  const uqDeck = isLeviesPreset ? UQ.decks.fy25_net_of_levies : (isFy26FloorPreset ? UQ.decks.fy26_floor : UQ.decks.fy25_realisation);
  const uqDeckLabel = isLeviesPreset ? "levies" : (isFy26FloorPreset ? "$65" : "FY25");
  const uqRange = inrSigned(uqDeck.recommended.netCash_p10) + "–" + inrSigned(uqDeck.recommended.netCash_p90);
  const uqProb = pct(uqDeck.pGtBaselineSamePolicy.vfd_hold);
  const uqSub = (LANG === "hi")
    ? "अनिश्चितता सीमा (" + uqDeckLabel + " deck): " + uqRange + " · समान नीति (VFD-hold) पर आधार रेखा से बेहतर होने की संभावना = " + uqProb
    : "Range (uncertainty, " + uqDeckLabel + " deck): " + uqRange + " · P(better than baseline, same policy) = " + uqProb;
  const pctLine = marginPct === null
    ? (LANG === "hi" ? "आधार रेखा निकट-शून्य/ऋणात्मक है, % परिवर्तन सार्थक नहीं" : "baseline is small/negative — a % change is not meaningful")
    : signed(marginPct, 1) + "%";
  $("rsMarginSub").innerHTML =
    '<span class="num">' + inrSigned(baseM) + " → " + inrSigned(recM) + ' (<span lang="' + langAttr() + '">' + tag + "</span>)</span>" +
    '<span class="l2 num">' + pctLine + " · " + T("baselineFootnote") + "</span>" +
    '<span class="l2 num" lang="' + langAttr() + '">' + uqSub + "</span>";

  /* Per-m³ intensity tiles (rev 12) — replace the old "diesel not burned /
     CO₂ avoided per cycle" framing, which read as self-contradictory once
     the recommendation started using LESS steam than the baseline in
     absolute terms (1,000 t vs 1,300 t): a smaller absolute number of
     litres "not burned" does not read as a saving. Per-m³ intensity is
     unambiguous either way, and derives its own sign/colour rather than
     assuming the direction. Absolute steam/diesel/CO₂ per cycle stays in
     the details table below (renderValue()), correctly labelled either way. */
  const dieselPerM3A = A.ctl.steam_t * ECON.hsd_l_per_t_steam / A.sum.oil_total_m3;
  const dieselPerM3B = B.ctl.steam_t * ECON.hsd_l_per_t_steam / B.sum.oil_total_m3;
  const co2PerM3A = A.ctl.steam_t * ECON.co2_kg_per_t_steam / A.sum.oil_total_m3;
  const co2PerM3B = B.ctl.steam_t * ECON.co2_kg_per_t_steam / B.sum.oil_total_m3;
  $("rsDieselFrom").textContent = nf(dieselPerM3A, 0);
  $("rsDieselTo").textContent = nf(dieselPerM3B, 0);
  $("rsDieselTo").classList.remove("good", "bad");
  $("rsDieselTo").classList.add(dieselPerM3B <= dieselPerM3A ? "good" : "bad");
  $("rsCo2From").textContent = nf(co2PerM3A, 0);
  $("rsCo2To").textContent = nf(co2PerM3B, 0);
  $("rsCo2To").classList.remove("good", "bad");
  $("rsCo2To").classList.add(co2PerM3B <= co2PerM3A ? "good" : "bad");
  const dieselPct = dieselPerM3A > 0 ? (dieselPerM3B - dieselPerM3A) / dieselPerM3A * 100 : null;
  $("rsMoneySub").innerHTML = (dieselPct === null ? "" : signed(dieselPct, 1) + "% ") +
    '<span class="l2 num">' + nf(B.ctl.steam_t, 0) + " t steam / " + nf(B.sum.oil_total_m3, 0) +
    " m³ oil at the recommendation (" + nf(A.ctl.steam_t, 0) + " t / " + nf(A.sum.oil_total_m3, 0) + " m³ " + T(A.key) + ")</span>";
  const co2Pct = co2PerM3A > 0 ? (co2PerM3B - co2PerM3A) / co2PerM3A * 100 : null;
  $("rsCo2Sub").innerHTML = (co2Pct === null ? "" : signed(co2Pct, 1) + "% ") +
    '<span class="l2 num">IPCC diesel default 74.1 kgCO₂/GJ &middot; absolute steam/CO₂ per cycle in the table below</span>';
}

/* Grid (electric) kWh/m³ — the "corrected" energy figure (polished-rod
   energy / surface efficiency), rev 12. Baked scenarios carry
   electric_kWh_per_m3 verbatim from twin.cycle.summary(); the in-browser
   approximation (page-console.js mockSimulate()) only computes the raw
   polished-rod energy_per_m3_kWh, so fall back to dividing by the params'
   surface efficiency (0.60) rather than showing "—" for an off-baked run. */
function gridKWhPerM3(sum){
  if (Number.isFinite(sum.electric_kWh_per_m3)) return sum.electric_kWh_per_m3;
  return Number.isFinite(sum.energy_per_m3_kWh) ? sum.energy_per_m3_kWh / 0.60 : NaN;
}

/* ---------- comparison table --------------------------------------------- */
function renderCompare(){
  $("cmpHeadA").textContent = T(A.key);
  $("cmpHeadA").setAttribute("lang", langAttr());
  $("cmpSetA").textContent = settingsLabel(A.ctl);
  $("cmpHeadB").textContent = T(B.key);
  $("cmpHeadB").setAttribute("lang", langAttr());
  $("cmpSetB").textContent = settingsLabel(B.ctl);

  const rows = [
    { k: "sorLong",         u: "t/m³",  a: A.sum.SOR_t_per_m3,        b: B.sum.SOR_t_per_m3,        d: 2, dir: "down" },
    { k: "oilRecovered",    u: "m³",    a: A.sum.oil_total_m3,        b: B.sum.oil_total_m3,        d: 0, dir: "up"   },
    { k: "oilBbl",          u: "bbl",        a: A.sum.oil_total_m3 * M3_TO_BBL, b: B.sum.oil_total_m3 * M3_TO_BBL, d: 0, dir: "up", sub: true },
    { k: "energyIntensity", u: "kWh/m³", a: gridKWhPerM3(A.sum),  b: gridKWhPerM3(B.sum),   d: 1, dir: "down" },
    { k: "cycleDuration",   u: "d",          a: A.sum.days_total,          b: B.sum.days_total,          d: 1, dir: "down" },
    { k: "steamInjected",   u: "t",          a: A.ctl.steam_t,             b: B.ctl.steam_t,             d: 0, dir: "flat" },
    { grp: T("grpFuelCycle") },
    { k: "hsdBurned",       u: "L",       a: A.ctl.steam_t * ECON.hsd_l_per_t_steam,
                                             b: B.ctl.steam_t * ECON.hsd_l_per_t_steam,                  d: 0, dir: "flat" },
    { k: "co2Steam", u: "t", a: A.ctl.steam_t * ECON.co2_kg_per_t_steam / 1000,
                                             b: B.ctl.steam_t * ECON.co2_kg_per_t_steam / 1000,          d: 1, dir: "flat" },
    { k: "co2Intensity", u: "kgCO₂/bbl",
      a: A.ctl.steam_t * ECON.co2_kg_per_t_steam / (A.sum.oil_total_m3 * M3_TO_BBL),
      b: B.ctl.steam_t * ECON.co2_kg_per_t_steam / (B.sum.oil_total_m3 * M3_TO_BBL),                     d: 1, dir: "down" },
    { grp: T("grpMech") },
    { k: "maxFI", u: "—",  a: A.sum.max_floating_index,  b: B.sum.max_floating_index,  d: 2, dir: "down" },
    { k: "expectedFailures", u: "count",     a: A.sum.failures_expected,   b: B.sum.failures_expected,   d: 0, dir: "down" }
  ];

  /* Hygiene (rev 12): a percent change is only meaningful against a
     POSITIVE baseline — a near-zero or negative baseline (e.g. a margin
     row) can produce a nonsense "+711%"-style figure. Every row here
     happens to have a positive physical baseline, but the guard is kept
     general so a future row (margin, say) fails safe to an absolute delta
     with an explicit sign instead of a misleading percentage. */
  $("cmpBody").innerHTML = rows.map(function(r){
    if (r.grp) return '<tr class="grp"><td colspan="5">' + r.grp + "</td></tr>";
    const label = r.k ? '<span lang="' + langAttr() + '">' + T(r.k) + "</span>" : r.t;
    let chg = "<span class='muted'>&mdash;</span>";
    if (r.a === r.b){
      chg = "<span class='muted'>no change</span>";
    } else if (Number.isFinite(r.a) && Number.isFinite(r.b) && r.a > 0){
      const p = (r.b - r.a) / r.a * 100;
      const good = (r.dir === "down" && p < 0) || (r.dir === "up" && p > 0);
      const cls = r.dir === "flat" ? "muted" : (good ? "pos" : "neg");
      chg = '<span class="' + cls + '">' + signed(p, 1) + "%</span>";
    } else if (Number.isFinite(r.a) && Number.isFinite(r.b)){
      const d = r.b - r.a;
      const good = (r.dir === "down" && d < 0) || (r.dir === "up" && d > 0);
      const cls = r.dir === "flat" ? "muted" : (good ? "pos" : "neg");
      chg = '<span class="' + cls + '">' + signed(d, r.d) + " " + r.u + "</span>";
    }
    return "<tr>" +
      '<td class="k"' + (r.sub ? ' style="padding-left:20px"' : "") + ">" + label + "</td>" +
      '<td class="muted">' + r.u + "</td>" +
      '<td class="v">' + nf(r.a, r.d) + "</td>" +
      '<td class="v">' + nf(r.b, r.d) + "</td>" +
      "<td>" + chg + "</td></tr>";
  }).join("");
}

/* ---------- fuel, cost and carbon, shown as arithmetic -------------------- */
function renderValue(){
  const rows = [
    { grp: T("grpSteamAvoided") },
    [T("oilAtOptimum"),        nf(B.sum.oil_total_m3, 1) + " m³"],
    [T("steamNeeded"),
                                  nf(B.sum.oil_total_m3, 1) + " × " + fmt(A.sum.SOR_t_per_m3, 4) +
                                  " = <b>" + nf(AV.counterfactualSteamT, 0) + " t</b>"],
    [T("steamInjectedOpt"), nf(B.ctl.steam_t, 0) + " t"],
    [T("steamAvoided"),          "<b>" + nf(AV.steamT, 0) + " t</b>"],
    { grp: T("grpFuelGen") },
    [T("dieselPerT"), nf(ECON.hsd_kg_per_t_steam, 0) + " kg = " + fmt(ECON.hsd_l_per_t_steam, 1) + " L"],
    [T("dieselAvoided"),          "<b>" + nf(AV.dieselL, 0) + " L</b> (" + fmt(AV.dieselT, 1) + " t)"],
    [T("priceBand"),           "₹" + nf(ECON.inr_per_t_steam_low, 0) + "–" + nf(ECON.inr_per_t_steam_high, 0) +
                                  " / t steam<span class='sub'>₹" + fmt(ECON.hsd_inr_per_l, 2) +
                                  "/L pump price; −30% bulk sensitivity</span>"],
    [T("valueAvoidedCycle"),  "<b>₹" + fmt(AV.crLow, 2) + "–" + fmt(AV.crHigh, 2) + " " + T("crore") + "</b>"],
    { grp: T("grpCarbon") },
    [T("energyAvoided"),       nf(AV.energyGJ, 0) + " GJ"],
    [T("co2AvoidedCycle"), "<b>" + nf(AV.co2T, 0) + " tCO₂</b>"],
    { grp: T("grpProgramme") + " — × " + ECON.css_jobs_fy26 + " CSS jobs, OIL FY2025-26" },
    [T("steamAvoided"),          nf(PRG.steamT, 0) + " t"],
    [T("dieselAvoided"),         nf(PRG.dieselL, 0) + " L"],
    [T("valueAvoided"),          "<b>₹" + fmt(PRG.crLow, 1) + "–" + fmt(PRG.crHigh, 1) + " " + T("crore") + "</b>"],
    [T("co2AvoidedShort"),       "<b>" + nf(PRG.co2T, 0) + " tCO₂</b>"]
  ];
  $("valueBody").innerHTML = rows.map(function(r){
    if (r.grp) return '<tr class="grp"><td colspan="2">' + r.grp + "</td></tr>";
    return '<tr><td class="k" lang="' + langAttr() + '">' + r[0] +
      '</td><td class="v" style="text-align:right">' + r[1] + "</td></tr>";
  }).join("") +
  '<tr><td class="note" colspan="2"><b>Why per cycle, and not per year.</b> The cycle duration above is the ' +
  "<i>simulated producing cycle</i>, not the interval between field CSS jobs — real CSS cycles are re-visited " +
  "months to years apart, and Baghewala banked 39 cycles in about 6.5 years across a 34-well field. Dividing 365 " +
  "by the simulated duration would manufacture a cycle count no CSS operation achieves, so this product never does it. " +
  "The programme block above is an explicit multiplication by a number Oil India itself published: " + ECON.css_jobs_fy26 +
  " CSS jobs in FY2025-26.<br><br><b>Why diesel.</b> Baghewala's steam generators burn HSD, not gas — OIL's own " +
  "operations deck records ~220 kg/hr of diesel against ~3,100 kg/hr of steam on BGW-08, and there is no gas supply " +
  "to the field (the crude leaves by road tanker). The upper price is Rajasthan retail pump price, which a bulk " +
  "industrial buyer would beat; the lower bound carries a −30% sensitivity for that. Every physical quantity above " +
  "is unaffected by the price argument.</td></tr>";
}

/* ---------- provenance --------------------------------------------------- */
function renderProvenance(){
  const stamp = RUN.computedAt ? istStamp(new Date(RUN.computedAt)) : istStamp(BOOT_TIME);
  const rows = [
    [T("runId"),         RUN.runId],
    [T("computedAt"),    stamp],
    [T("setpoints"),     settingsLabel(RUN.controls)],
    [T("simulator"),     TWIN_VERSION + " · twin.cycle.simulate_css_cycle"],
    [T("parameters"),    PARAMS_REV],
    [T("validation"),    "263/265 physics & benchmark tests (2 declared gaps: soak; steam optimum at the mid-range diesel price, marked xfail) · synthetic data only, no history match"],
    [T("dataSource"),    MOCK ? "Baked twin output · no live SCADA link" : "Live API · " + API_BASE],
    [T("recCol"),        REC ? REC.recId + " · " + istStamp(new Date(REC.at)) : "<span class='muted'>optimiser not yet run this session</span>"],
    [T("optimiserCol"),  "12,936-plan physics grid (~3 min), maximising INCREMENTAL margin/cycle-day, no surrogate in the decision loop; ML emulator (XGBoost) kept for what-if / uncertainty speed only · oil R² " +
                       fmt(SURROGATE.oil_r2, 3) + " · incr. margin R² " + fmt(SURROGATE.margin_r2, 3) + " (in-envelope) · n = " + nf(SURROGATE.n)],
    [T("fuelBasisRow"),  "HSD diesel · " + nf(ECON.hsd_kg_per_t_steam, 0) + " kg/t steam (OIL ops deck, BGW-08) · ₹" +
                       nf(ECON.inr_per_t_steam_low, 0) + "–" + nf(ECON.inr_per_t_steam_high, 0) + "/t"],
    [T("carbonBasis"),   fmt(ECON.co2_kg_per_t_steam, 1) + " kgCO₂/t steam · IPCC diesel default 74.1 kgCO₂/GJ"],
    [T("programmeScale"), nf(ECON.css_jobs_fy26, 0) + " CSS jobs, OIL FY2025-26 (published) — explicit multiplication, never annualised from cycle length"],
    [T("calibrationRow"), '<span lang="' + langAttr() + '">' + T("calibrationDefault") + '</span> &middot; <a id="calibOverviewLink" href="methodology.html#calib" lang="' +
      langAttr() + '">' + T("calibrateLink") + "</a>"]
  ];
  $("provBody").innerHTML = rows.map(function(r){
    return '<tr><td class="k" style="white-space:nowrap" lang="' + langAttr() + '">' + r[0] +
      '</td><td class="v" style="text-align:right">' + r[1] + "</td></tr>";
  }).join("");
  updateCalibLink();

  $("claimNote").innerHTML =
    "<b>How to read the headline.</b> The figures above are measured between two cycles you can see on this page: the " +
    "run on the books (SOR " + fmt(A.sum.SOR_t_per_m3, 2) + ", gross margin ₹" + nf(A.sum.margin_inr_per_cycle_day, 0) +
    "/cycle-day) and the twin re-run at the set-points a controller would actually accept (SOR " +
    fmt(B.sum.SOR_t_per_m3, 2) + ", gross margin ₹" + nf(B.sum.margin_inr_per_cycle_day, 0) + "/cycle-day). The " +
    signed(OPT_RESULT.SOR_improvement_pct, 1) + "% SOR / +" + fmt(OPT_RESULT.margin_improvement_pct, 1) +
    "% gross-margin quoted underneath is the optimiser's own figure against the " + T("fieldPractice") + " (" +
    settingsLabel(BASELINE_PUBLISHED) + " → SOR " + fmt(BASELINE_PUBLISHED.SOR, 2) + ", gross margin ₹" +
    nf(BASELINE_PUBLISHED.margin_inr_per_cycle_day, 0) + "/cycle-day), " + T("baselineFootnote") + " — this is not the " +
    "cycle on screen. Both are printed so neither can be mistaken for the other. <b>SOR stays gross</b> (steam ÷ all " +
    "oil — the literature convention every benchmark here is quoted in); the result strip's money figure above, and " +
    "the optimiser's actual objective, is the <b>INCREMENTAL</b> margin — oil over the cold, unstimulated well for " +
    "the same window, net of daily opex (soak is held at 10 d field practice, not searched — the twin's soak " +
    "sensitivity is under 2%). See <a href=\"methodology.html\" data-xlink=\"methodology.html\">Model basis</a> for " +
    "why gross and incremental differ.<br><br>" +
    "<b>How to read the money.</b> It is stated per optimised cycle, in a band, on a diesel fuel basis, against an " +
    "iso-oil counterfactual — how much steam the current practice would have burned to make the same oil. " +
    "Nothing here is annualised from the simulated cycle length. The programme figure is a separate, explicit " +
    "multiplication by Oil India's own published FY2025-26 CSS job count.";
}

/* Overview footer/provenance link to Model basis > "Calibrate from field
   data" (#calib) -- has to carry the current lang/theme itself (not a plain
   data-xlink, which strips the #fragment — see updateYourPricesLink's own
   comment on the optimiser page for the same ordering issue), so it is
   re-set on every language AND theme change, not just language. */
function updateCalibLink(){
  const a = $("calibOverviewLink");
  if (a) a.setAttribute("href", "methodology.html?lang=" + LANG + "&theme=" + THEME + "#calib");
}

/* ---------- the one chart ------------------------------------------------ */
function renderSorChart(){
  const th = chartTheme();
  const cats = [T("fieldPractice"), T(A.key), T("mlOptimised")];
  const vals = [BASELINE_PUBLISHED.SOR, A.sum.SOR_t_per_m3, B.sum.SOR_t_per_m3];
  const cols = [th.bar3, th.bar2, th.barHi];
  const hov  = [settingsLabel(BASELINE_PUBLISHED), settingsLabel(A.ctl), settingsLabel(B.ctl)];
  const errs = [0, 0, SURROGATE.sor_mae];

  const trace = {
    type: "bar", orientation: "h",
    y: cats, x: vals,
    marker: { color: cols },
    width: 0.46,
    customdata: hov,
    hovertemplate: "%{y}<br>SOR %{x:.2f} t/m³<br>%{customdata}<extra></extra>",
    cliponaxis: false,
    error_x: { type: "data", array: errs, visible: true, color: th.faint, thickness: 1, width: 4 }
  };
  /* Value labels are annotations, not bar text: the ML bar carries an error
     whisker, and Plotly's outside-text would sit inside it and read as a
     strikethrough. Each label is placed past the end of its own whisker. */
  const reach = vals.map(function(v, i){ return v + errs[i]; });
  const top = Math.max.apply(null, reach) * 1.22;
  const layout = {
    barmode: "overlay", bargap: 0.42,
    xaxis: { title: { text: T("sorAxis"), font: { family: FONT_FAMILY, size: 11, color: th.axis }, standoff: 4 },
      gridcolor: th.grid, zeroline: false, tickfont: CFONT(), range: [0, top],
      linecolor: th.line },
    yaxis: { type: "category", autorange: "reversed", tickfont: CFONT(th.text2), showgrid: false,
      automargin: "left+right+top+bottom" },
    annotations: vals.map(function(v, i){
      return { x: reach[i] + top * 0.02, y: cats[i], xref: "x", yref: "y",
        text: "<b>" + fmt(v, 2) + "</b>", showarrow: false, xanchor: "left",
        font: { family: FONT_FAMILY, size: 12, color: th.text } };
    }),
    showlegend: false,
    paper_bgcolor: th.paper, plot_bgcolor: th.paper, font: CFONT(),
    hoverlabel: hoverLabel(th),
    margin: { t: 6, r: 20, l: (LANG === "hi" ? 150 : 8), b: 40 }
  };
  Plotly.purge("chartSor");
  Plotly.newPlot("chartSor", [trace], layout, PLOTLY_CONFIG);

  $("sorChartFoot").innerHTML =
    "Published-practice baseline (BGW-8 job, 2018) " + settingsLabel(BASELINE_PUBLISHED) +
    " — derived from a published job, not OIL's current practice.<br>" +
    T(A.key) + " " + settingsLabel(A.ctl) + "<br>" +
    "Physics-grid optimum " + settingsLabel(B.ctl) + " (soak held at 10 d practice, not searched) — snapped to the controller " +
    "grid and re-run through the twin. Error bar = SOR surrogate MAE ±" + fmt(SURROGATE.sor_mae, 3) + " t/m³.";
  $("sorChartMeta").textContent = "lower is better";
}

/* ---------- "Your prices" (re-pricing, not re-optimisation) --------------- */
function renderPricesPanel(){
  const p = getPrices();
  $("pxDiesel").value = fmt(p.diesel, 2);
  $("pxDiscount").value = nf(Math.round(p.discount * 100), 0);
  $("pxOilBbl").value = nf(Math.round(p.oilBbl), 0);
  const isBase = pricesAreBase(p);
  const tagEl = $("pxTag");
  tagEl.className = "tag" + (isBase ? "" : " info");
  tagEl.innerHTML = '<span lang="' + langAttr() + '">' + (isBase ? T("baseCase") : T("atYourPrices")) + "</span>";
  $("pxNote").innerHTML = '<span lang="' + langAttr() + '">' + T("notReoptimisedNote") + "</span>";
}
function readPricesFromInputs(){
  const diesel = parseFloat($("pxDiesel").value);
  const discount = parseFloat($("pxDiscount").value) / 100;
  const oilBbl = parseFloat($("pxOilBbl").value);
  if (!Number.isFinite(diesel) || !Number.isFinite(discount) || !Number.isFinite(oilBbl)) return;
  setPrices({ diesel: diesel, discount: discount, oilBbl: oilBbl });
  renderPricesPanel();
  renderRecCard("recCard", AV, A.sum.max_floating_index);
  renderStrip();
}
["pxDiesel", "pxDiscount", "pxOilBbl"].forEach(function(id){
  $(id).addEventListener("change", readPricesFromInputs);
});
$("pxReset").addEventListener("click", function(){
  resetPrices();
  renderPricesPanel();
  renderRecCard("recCard", AV, A.sum.max_floating_index);
  renderStrip();
});
/* rev 9: two named price-deck presets (params/field_params.json
   economics.oil_price_presets), diesel/discount left at the shipped base
   case -- only the oil realisation moves. */
function applyOilPricePreset(presetKey){
  const preset = OIL_PRICE_PRESETS[presetKey];
  if (!preset) return;
  setPrices({ diesel: ECON.hsd_inr_per_l, discount: ECON.bulk_discount, oilBbl: preset.inr_per_bbl });
  renderPricesPanel();
  renderRecCard("recCard", AV, A.sum.max_floating_index);
  renderStrip();
}
$("pxPresetFy25").addEventListener("click", function(){ applyOilPricePreset("fy25_realisation"); });
$("pxPresetFy26Floor").addEventListener("click", function(){ applyOilPricePreset("fy26_floor_65"); });
$("pxPresetLevies").addEventListener("click", function(){ applyOilPricePreset("fy25_net_of_levies"); });
/* rev 13 (wave 5): the diesel bulk-discount preset -- moves ONLY the discount,
   at whatever oil deck is currently selected (does not reset oilBbl). */
const pxPresetDiscount30El = $("pxPresetDiscount30");
if (pxPresetDiscount30El) pxPresetDiscount30El.addEventListener("click", function(){
  const p = getPrices();
  setPrices({ diesel: p.diesel, discount: DIESEL_DISCOUNT_PRESETS["bulk_0.30"], oilBbl: p.oilBbl });
  renderPricesPanel();
  renderRecCard("recCard", AV, A.sum.max_floating_index);
  renderStrip();
});

/* ---------- wiring ------------------------------------------------------- */
function renderAll(){
  renderRecCard("recCard", AV, A.sum.max_floating_index);
  renderStrip();
  renderCompare();
  renderValue();
  renderProvenance();
  renderSorChart();
  renderPricesPanel();
}
onLangChange(renderAll);
onThemeChange(function(){ renderSorChart(); updateCalibLink(); });
window.addEventListener("resize", function(){ if (window.Plotly) Plotly.Plots.resize($("chartSor")); });
$("btnPrint").addEventListener("click", function(){ window.print(); });
renderAll();
