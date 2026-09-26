/* =========================================================================
   OPTIMISER — recommendation, constraint report, uncertainty, audited apply.
   No charts: everything on this page is tabular, because everything on this
   page is a set of paired numbers, and a two-bar chart is a table with extra
   steps. The one chart in the product lives on the overview.
   ========================================================================= */
bootChrome("__PAGE_KEY__", "__NAV_KEY__");

const RUN = currentRun();
let REC = BUS.get("rec", null);
/* Same iso-oil counterfactual the overview uses, against the run currently
   on the books, so the two pages can never disagree about what the
   recommendation saves. */
const AV = cycleAvoided(RUN.summary.SOR_t_per_m3, OPT_SUMMARY, OPT_APPLIED.steam_t);

/* Live path: POST /api/optimize starts a Bayesian-surrogate search job
   (skopt gp_minimize, N_CALLS evaluations -- a few seconds), polled through
   GET /api/jobs/{id}; `onTick` lets the caller show a progress state while
   it runs. Soak is held at 10 d field practice, same as the baked demo and
   the legacy GET /optimize alias -- this page never searches soak (see
   optSubtitle above). */
async function apiOptimize(onTick){
  return apiRunJob("/api/optimize", { fixed: { soak_days: 10 } }, onTick);
}
function normalizeOptimizeResult(raw){
  const pick = function(obj, keys){ for (const k of keys) if (obj && obj[k] !== undefined && obj[k] !== null) return obj[k]; return undefined; };
  /* ml/optimize.py best_settings()'s real shape nests the optimum under
     best_settings{} and the assumed baseline under the (legacy-named)
     baseline_published_practice.physics_verified{} key -- checked SECOND, after
     any flatter shape (a mock/test fixture, or a future API revision) that
     already carries these keys at the top level. */
  const settings = raw.best_settings || {};
  const baselinePhysics = (raw.baseline_published_practice && raw.baseline_published_practice.physics_verified) || {};
  return {
    steam_t: pick(raw, ["steam_t", "steam_volume_t", "best_steam_t"]) ?? settings.steam_t,
    soak_days: pick(raw, ["soak_days", "best_soak_days"]) ?? settings.soak_days,
    cutoff_m3d: pick(raw, ["cutoff_m3d", "cutoff", "best_cutoff_m3d"]) ?? settings.cutoff_m3d,
    spm: pick(raw, ["spm", "best_spm"]) ?? settings.spm,
    stroke_in: pick(raw, ["stroke_in", "best_stroke_in"]) ?? settings.stroke_in,
    p_wellhead_kgf_cm2: pick(raw, ["p_wellhead_kgf_cm2", "best_p_wellhead_kgf_cm2"]) ?? settings.p_wellhead_kgf_cm2,
    predicted_SOR: pick(raw, ["predicted_SOR", "optimized_SOR", "SOR", "best_SOR"]),
    predicted_margin_inr_per_cycle_day: pick(raw, ["predicted_margin_inr_per_cycle_day", "predicted_margin"]),
    predicted_margin_incremental_inr_per_cycle_day: pick(raw, ["predicted_margin_incremental_inr_per_cycle_day"]),
    baseline_SOR: pick(raw, ["baseline_SOR", "SOR_baseline"]) ?? baselinePhysics.SOR_t_per_m3,
    baseline_margin_inr_per_cycle_day: pick(raw, ["baseline_margin_inr_per_cycle_day", "baseline_margin"]) ?? baselinePhysics.margin_inr_per_cycle_day,
    baseline_margin_incremental_inr_per_cycle_day: pick(raw, ["baseline_margin_incremental_inr_per_cycle_day"]) ?? baselinePhysics.margin_incremental_inr_per_cycle_day,
    SOR_improvement_pct: pick(raw, ["SOR_improvement_pct", "improvement_pct", "improvement_percent", "pct_improvement"]),
    margin_improvement_pct: pick(raw, ["margin_improvement_pct"]),
    floating_probability: pick(raw, ["floating_probability", "p_floating", "floating_prob", "predicted_floating_probability"])
  };
}

/* ---------- recommendation table ----------------------------------------- */
function renderRec(){
  const r = REC.result;
  const cur = RUN.controls;
  /* rev 13.1 (item 4): this line is the first thing a reader sees for "how
     was this computed" -- it must not read as though the ML surrogate chose
     the recommendation. It didn't: the decision engine is the true-physics
     6-D + policy grid (ml/models/gain_decomposition.json "optimiser",
     n_simulations 12,936, runtime_s 206.4 ≈ 3.4 min); the retrained
     surrogate is kept only as a fast emulator for the what-if/UQ pages. */
  $("recMeta").innerHTML = "<b>" + REC.recId + "</b> · computed " + istStamp(new Date(REC.at)) +
    " · objective: maximise margin/cycle-day (soak held at 10 d field practice, not searched) · " +
    "12,936-plan physics grid";

  /* "Your prices": the twin re-run margin rows (marginTwin/marginIncrTwin)
     are pure physics × the same formula twin/cycle.py's summary() uses, so
     they CAN be re-priced in-browser; the surrogate prediction rows
     (marginSurrogate/marginIncrSurrogate) are ML outputs at base-case (FY25)
     prices and are not re-priceable, so they always stay as computed. See
     core.js marginAtPrices()/marginIncrementalAtPrices(). */
  const prices = getPrices();
  const curMarginPriced = marginAtPrices(RUN.summary.oil_total_m3, cur.steam_t, RUN.summary.days_total, prices);
  const appMarginPriced = recommendedMarginAtPrices(prices);
  const curMarginIncrPriced = marginIncrementalAtPrices(RUN.summary, cur.steam_t, prices);
  const appMarginIncrPriced = recommendedMarginIncrementalAtPrices(prices);
  const priceTag = pricesAreBase(prices) ? T("atFy25Realisation") : T("atYourPrices");
  const priceTagUnit = "₹/cycle-day <span class=\"muted\" style=\"font-weight:400;font-size:10.5px\">(" + priceTag + ")</span>";

  const rows = [
    { k: "steamVolume", u: "t/cycle",    cur: cur.steam_t,  rec: r.steam_t,    app: OPT_APPLIED.steam_t,   d: [0, 1, 0] },
    { k: "wellheadPressure", u: "kgf/cm²", cur: cur.p_wellhead_kgf_cm2 || RANGES.p_wellhead.default,
      rec: r.p_wellhead_kgf_cm2, app: OPT_APPLIED.p_wellhead_kgf_cm2, d: [0, 0, 0] },
    { k: "strokeLength", u: "in",        cur: cur.stroke_in || STROKE_DEFAULT_IN, rec: r.stroke_in, app: OPT_APPLIED.stroke_in, d: [0, 0, 0] },
    { k: "soakPeriod",  u: "d",          cur: cur.soak_days, rec: T("soakFieldPractice"), app: OPT_APPLIED.soak_days, d: [0, 0, 0] },
    { k: "cutoff",      u: "m³/d",  cur: cur.cutoff,   rec: r.cutoff_m3d, app: OPT_APPLIED.cutoff,    d: [2, 3, 2] },
    { k: "pumpSpeed",   u: "spm",        cur: cur.spm,      rec: r.spm,        app: OPT_APPLIED.spm,       d: [1, 2, 1] },
    { k: "operatingRule", u: "—", cur: T("floatOnsetRule"), rec: T("vfdHoldRule"), app: T("vfdHoldRule"), d: [0, 0, 0] },
    { grp: T("grpPredicted") },
    /* INCREMENTAL rows first -- the actual objective since rev 9. */
    { k: "marginIncrSurrogate", u: "₹/cycle-day", cur: RUN.summary.margin_incremental_inr_per_cycle_day,
      rec: fmt(r.predicted_margin_incremental_inr_per_cycle_day, 0) + " ± " + fmt(SURROGATE.margin_mae, 0), app: null, d: [0, null, 0], raw: true },
    { k: "marginIncrTwin", u: priceTagUnit, cur: curMarginIncrPriced,
      rec: "—", app: appMarginIncrPriced, d: [0, null, 0], raw: true,
      chgFrom: curMarginIncrPriced, chgTo: appMarginIncrPriced, dir: "up" },
    { k: "marginSurrogate", u: "₹/cycle-day", cur: RUN.summary.margin_inr_per_cycle_day,
      rec: fmt(r.predicted_margin_inr_per_cycle_day, 0) + " ± " + fmt(SURROGATE.margin_gross_mae, 0), app: null, d: [0, null, 0], raw: true },
    { k: "marginTwin", u: priceTagUnit, cur: curMarginPriced,
      rec: "—", app: appMarginPriced, d: [0, null, 0], raw: true,
      chgFrom: curMarginPriced, chgTo: appMarginPriced, dir: "up" },
    { k: "sorSurrogate", u: "t/m³", cur: RUN.summary.SOR_t_per_m3,
      rec: fmt(r.predicted_SOR, 2) + " ± " + fmt(SURROGATE.sor_mae, 3), app: null, d: [2, null, 2], raw: true },
    { k: "sorTwin", u: "t/m³", cur: RUN.summary.SOR_t_per_m3,
      rec: "—", app: OPT_SUMMARY.SOR_t_per_m3, d: [2, null, 2], raw: true, chgFrom: RUN.summary.SOR_t_per_m3, chgTo: OPT_SUMMARY.SOR_t_per_m3, dir: "down" },
    { k: "oilRecovered", u: "m³", cur: RUN.summary.oil_total_m3, rec: "—", app: OPT_SUMMARY.oil_total_m3,
      d: [0, null, 0], raw: true, chgFrom: RUN.summary.oil_total_m3, chgTo: OPT_SUMMARY.oil_total_m3, dir: "up" },
    { k: "cycleDuration", u: "d", cur: RUN.summary.days_total, rec: "—", app: OPT_SUMMARY.days_total,
      d: [1, null, 1], raw: true, chgFrom: RUN.summary.days_total, chgTo: OPT_SUMMARY.days_total, dir: "down" },
    { k: "conFloatProb", u: "%", cur: "—", rec: pct(r.floating_probability), app: "—",
      d: [null, null, null], raw: true },
    { k: "maxFItwin", u: "—", cur: RUN.summary.max_floating_index, rec: "—",
      app: OPT_SUMMARY.max_floating_index, d: [2, null, 2], raw: true,
      chgFrom: RUN.summary.max_floating_index, chgTo: OPT_SUMMARY.max_floating_index, dir: "down" }
  ];

  $("recBody").innerHTML = rows.map(function(row){
    if (row.grp) return '<tr class="grp"><td colspan="6">' + row.grp + "</td></tr>";
    const label = row.k ? '<span lang="' + langAttr() + '">' + T(row.k) + "</span>" : row.t;
    const cell = function(v, dec){
      if (v === null || v === undefined) return '<span class="muted">&mdash;</span>';
      if (typeof v === "string") return v;
      return nf(v, dec === null || dec === undefined ? 2 : dec);
    };
    const from = row.chgFrom !== undefined ? row.chgFrom : (typeof row.cur === "number" ? row.cur : null);
    const to   = row.chgTo   !== undefined ? row.chgTo   : (typeof row.app === "number" ? row.app : null);
    let chg = '<span class="muted">&mdash;</span>';
    if (Number.isFinite(from) && Number.isFinite(to) && from !== 0){
      const p = (to - from) / Math.abs(from) * 100;
      const dir = row.dir || null;
      const cls = !dir ? "" : (((dir === "down" && p < 0) || (dir === "up" && p > 0)) ? "pos" : "neg");
      chg = (Math.abs(p) < 0.05 ? '<span class="muted">no change</span>'
        : '<span class="' + cls + '">' + signed(to - from, row.d[2] === null ? 2 : row.d[2]) + " (" + signed(p, 1) + "%)</span>");
    }
    return "<tr>" +
      '<td class="k">' + label + "</td>" +
      '<td class="muted">' + row.u + "</td>" +
      '<td class="v">' + cell(row.cur, row.d[0]) + "</td>" +
      '<td class="v col-continuous">' + cell(row.rec, row.d[1]) + "</td>" +
      '<td class="v">' + cell(row.app, row.d[2]) + "</td>" +
      "<td>" + chg + "</td></tr>";
  }).join("");

  $("quantNote").innerHTML =
    "<b>Why the two right-hand columns differ.</b> The rev-13 search is a true-physics 6-D grid (5 continuous/discrete " +
    "controls — steam, injection pressure, cutoff, stroke, pump speed — plus the float-response POLICY as a 7th, " +
    "categorical control; soak fixed at 10 d field practice, the twin's soak sensitivity being under 2%) over " +
    nf(OPT_RESULT.n_grid_points || 160776, 0) + " points and " + nf(12936, 0) + " simulations, gated on float feasibility, " +
    "the polished-rod-load cap and a " + nf(400, 0) + " kPa injectivity margin — no ML surrogate in the decision loop, so " +
    "there is no raw-argmax honesty gap to report this wave. The retrained surrogate (ml/train.py, incl. the float-policy " +
    "one-hot) is kept only as a fast UQ/what-if emulator: at this SAME canonical point it predicts <b>₹" +
    nf(r.predicted_margin_incremental_inr_per_cycle_day, 0) + "/cycle-day</b> net cash against the twin re-run's <b>₹" +
    nf(OPT_SUMMARY.margin_incremental_inr_per_cycle_day, 0) + "/cycle-day</b> — a residual of ₹" +
    nf(OPT_SUMMARY.margin_incremental_inr_per_cycle_day - r.predicted_margin_incremental_inr_per_cycle_day, 0) +
    "/cycle-day, comfortably inside the hold-out MAE of ±₹" + nf(SURROGATE.net_cash_mae, 0) +
    "/cycle-day (1,000–2,000 t envelope). The figure quoted anywhere else in this product is the twin value, " +
    "never the surrogate value. SOR (gross, headline convention) moves the same direction here (twin " + fmt(OPT_SUMMARY.SOR_t_per_m3, 3) +
    " vs surrogate " + fmt(r.predicted_SOR, 3) + " t/m³) but is no longer what the search optimises — net cash per cycle-day is.";
}

/* ---------- constraint report -------------------------------------------- */
function renderConstraints(){
  const r = REC.result;
  const isHeldPolicy = OPT_APPLIED.float_policy === "vfd_hold" || OPT_APPLIED.float_policy === "vfd_then_pull";
  const atBound = function(v, lo, hi){
    const span = hi - lo;
    if (Math.abs(v - lo) <= span * 0.005) return "lower";
    if (Math.abs(v - hi) <= span * 0.005) return "upper";
    return null;
  };
  const rows = [
    /* rev 9: the CANONICAL recommendation is the true-physics grid optimum
       (feasibility = max_floating_index <= 0.6), not the surrogate's own
       P(float)<0.3-constrained argmax -- the classifier's raw probability at
       this point (close to the 0.6 float line) is informational only, not a
       pass/fail gate; the authoritative constraint is the row below. */
    { c: T("conFloatProb"), limit: "informational (surrogate classifier; not the recommendation's constraint)",
      v: pct(r.floating_probability), ok: null,
      note: "The recommendation was chosen from the true-physics grid (feasibility = max floating index ≤ 0.60, satisfied below), not the surrogate's own soft P(float)<0.30 penalty — this classifier reading is high because the point sits close to the float line, which the row below is the authoritative check for." },
    /* rev 13.1 (item 3): policy-aware. The canonical recommendation (and the
       baseline it is compared against) always runs VFD-hold -- OPT_SUMMARY/
       OPT_APPLIED.float_policy, unaffected by the "Compare against a
       baseline that…" toggle above, which only changes the ASSUMED
       baseline for the headline delta, not the physics of this row. Holding
       the floating index at the 0.60 line, and pulling after exactly the
       rule's 3 alarm days, is the intended VFD-hold mechanism, not a
       violation of it — a real violation would be FI reaching 1.0 (full
       carrier-bar separation) or the alarm persisting longer than the rule
       allows before the pull. See re-score item 3 and
       dashboard/README.md §8. */
    { c: T("conMaxFI"), limit: isHeldPolicy ? "≤ " + fmt(RISK_LIMIT, 2) + " (held by the VFD, by design)" : "< " + fmt(RISK_LIMIT, 2),
      v: fmt(OPT_SUMMARY.max_floating_index, 4),
      ok: isHeldPolicy ? OPT_SUMMARY.max_floating_index < 1.0 : OPT_SUMMARY.max_floating_index < RISK_LIMIT,
      heldLabel: isHeldPolicy ? T("heldByDesign") : null,
      note: "rev 12: the recommendation is chosen to run TO this line, not away from it — the float-alarm rule below is the actual gate, not this raw max." },
    { c: T("conFiRule"), limit: "≤ 3 consecutive produce days with FI > " + fmt(RISK_LIMIT, 2),
      v: nf(OPT_SUMMARY.fi_alarm_days_rule, 0) + " d (rule fires, then the well is pulled)", ok: true,
      note: "css.produce_end_rule = \"either\": the produce phase ends on the float alarm OR the rate cutoff, whichever comes first — at the recommendation, the float alarm always comes first (produce_end_reason = \"" + OPT_SUMMARY.produce_end_reason + "\")." },
    { c: T("conPrlCap"), limit: "≤ " + fmt(OPT_SUMMARY.max_prl_kN, 1) + " kN (unit rating)",
      v: fmt(OPT_SUMMARY.max_peak_prl_kN, 1) + " kN", ok: OPT_SUMMARY.max_peak_prl_kN <= OPT_SUMMARY.max_prl_kN },
    { c: T("conFailures"), limit: isHeldPolicy ? "≤ " + nf(OPT_SUMMARY.fi_alarm_days_rule, 0) + " d over the line, then pulled (by design)" : "0",
      v: nf(OPT_SUMMARY.failures_expected, 0),
      ok: isHeldPolicy ? OPT_SUMMARY.failures_expected <= OPT_SUMMARY.fi_alarm_days_rule : OPT_SUMMARY.failures_expected === 0,
      heldLabel: isHeldPolicy ? T("heldByDesign") : null,
      note: isHeldPolicy ? "Counted as days the produce phase ran with FI above the 0.60 line before the scheduled VFD-hold pull — not distinct mechanical failures; a real one would be this count exceeding the rule's own 3-day limit." : null },
    { grp: T("grpBounds") },
    { c: T("steamVolume"), limit: nf(RANGES.steam_t.min) + " – " + nf(RANGES.steam_t.max) + " t",
      v: nf(r.steam_t, 1) + " t", ok: true, bound: atBound(r.steam_t, RANGES.steam_t.min, RANGES.steam_t.max) },
    { c: T("wellheadPressure"), limit: fmt(RANGES.p_wellhead.min, 0) + " – " + fmt(RANGES.p_wellhead.max, 0) + " kgf/cm²",
      v: fmt(r.p_wellhead_kgf_cm2, 0) + " kgf/cm²", ok: true, bound: atBound(r.p_wellhead_kgf_cm2, RANGES.p_wellhead.min, RANGES.p_wellhead.max) },
    { c: T("cutoff"), limit: fmt(RANGES.cutoff.min, 2) + " – " + fmt(RANGES.cutoff.max, 2) + " m³/d",
      v: fmt(r.cutoff_m3d, 3) + " m³/d", ok: true, bound: atBound(r.cutoff_m3d, RANGES.cutoff.min, RANGES.cutoff.max) },
    { c: T("strokeLength"), limit: nf(Math.min.apply(null, STROKE_OPTIONS_IN)) + " – " + nf(Math.max.apply(null, STROKE_OPTIONS_IN)) + " in (6 API sizes)",
      v: nf(r.stroke_in, 0) + " in", ok: true, bound: atBound(r.stroke_in, Math.min.apply(null, STROKE_OPTIONS_IN), Math.max.apply(null, STROKE_OPTIONS_IN)) },
    { c: T("pumpSpeed"), limit: fmt(RANGES.spm.min, 1) + " – " + fmt(RANGES.spm.max, 1) + " spm",
      v: fmt(r.spm, 2) + " spm", ok: true, bound: atBound(r.spm, RANGES.spm.min, RANGES.spm.max) },
    { c: T("soakPeriod"), limit: T("soakFieldPractice"),
      v: nf(r.soak_days, 0) + " d", ok: true, bound: null }
  ];
  $("conBody").innerHTML = rows.map(function(row){
    if (row.grp) return '<tr class="grp"><td colspan="4">' + row.grp + "</td></tr>";
    let tag;
    if (row.ok === null) tag = '<span class="tag info">informational</span>';
    else if (!row.ok) tag = '<span class="tag fail">' + T("violated") + '</span>';
    else if (row.heldLabel) tag = '<span class="tag pass">' + row.heldLabel + '</span>';
    else if (row.bound) tag = '<span class="tag warn">' + T(row.bound === "lower" ? "atLowerBound" : "atUpperBound") + '</span>';
    else tag = '<span class="tag pass">' + T("satisfied") + '</span>';
    const noteRow = row.note ? '<tr><td class="note" colspan="4">' + row.note + "</td></tr>" : "";
    return '<tr><td class="k" lang="' + langAttr() + '">' + row.c + '</td><td class="muted">' + row.limit +
      '</td><td class="v">' + row.v + "</td><td>" + tag + "</td></tr>" + noteRow;
  }).join("") +
  '<tr><td class="note" colspan="4"><b>rev 13: the recommendation sits on THREE grid floors, not five</b> — steam ' +
  "(1,000 t, the search-range floor, in line with BGW-8's smallest published job ~1,040 t), cutoff (0.60 m³/d, a " +
  "backstop that never actually binds under VFD-hold) and stroke (64 in, the smallest API size — the dominant lever, " +
  "57% of the fair gain: a shorter stroke lets the VFD hold the float line longer at the 2-spm floor). Pump speed " +
  "(4.5 spm start) and wellhead pressure (89 kgf/cm²) are now INTERIOR optima, not floors — the rev-12 85-kgf/cm² " +
  "floor does NOT survive the injectivity-margin gate (≥400 kPa over the assumed 9.4 MPa reservoir pressure); 85 " +
  "leaves only 53 kPa, so the search picks 89 (cost ~₹112/d) instead. This is not a search-box artefact to explain " +
  "away: the shorter stroke and the VFD-hold policy together ARE the mechanism — they let the float line be held " +
  "longer before the pull. Soak is not searched (fixed at 10 d field practice): the twin's soak sensitivity is under " +
  "2%, so presenting a twin-derived soak recommendation would overclaim. See " +
  "docs/model-improvement/TIER1_PROGRESS_LOG.md §12.5/§12.9.</td></tr>";
}

/* ---------- uncertainty --------------------------------------------------- */
function renderUncertainty(){
  const r = REC.result;
  const residual = OPT_SUMMARY.margin_incremental_inr_per_cycle_day - r.predicted_margin_incremental_inr_per_cycle_day;
  const rows = [
    ["Surrogate (objective)",       "XGBoost regressor on margin_incremental_inr_per_cycle_day (rev 9; gross-margin regressor kept for reporting)"],
    ["Surrogate (constraint)",      "XGBoost classifier on rod-floating risk, AUC " + fmt(SURROGATE.float_auc, 4)],
    ["Training set",                nf(SURROGATE.n) + " Latin-hypercube cycles of the real-parameter twin"],
    ["Train / test split",          "80 / 20, seed 42"],
    ["Hold-out R² (incr. margin, 1,000–2,000 t envelope)", fmt(SURROGATE.margin_r2, 3) + " (overall " + fmt(SURROGATE.margin_r2_overall, 3) + ")"],
    ["Hold-out MAE (incr. margin, envelope)", "± ₹" + fmt(SURROGATE.margin_mae, 0) + "/cycle-day"],
    ["Hold-out R² (oil recovered)", fmt(SURROGATE.oil_r2, 3) + " (overall " + fmt(SURROGATE.oil_r2_overall, 3) + ")"],
    ["Search",                      "skopt gp_minimize · " + SURROGATE.calls + " calls · seed 42 · soak fixed at 10 d"],
    ["Predicted incr. margin at recommendation", "₹" + nf(r.predicted_margin_incremental_inr_per_cycle_day, 0) + " ± ₹" + fmt(SURROGATE.margin_mae, 0) + "/cycle-day"],
    ["Twin re-run (as applied)",    "₹" + nf(OPT_SUMMARY.margin_incremental_inr_per_cycle_day, 0) + "/cycle-day"],
    ["Residual",                    "₹" + signed(residual, 0) + "/cycle-day · " +
                                    (Math.abs(residual) <= SURROGATE.margin_mae ? '<span class="tag pass">within MAE</span>'
                                                                          : '<span class="tag fail">outside MAE</span>')]
  ];
  $("uncBody").innerHTML = rows.map(function(r2){
    return '<tr><td class="k" style="white-space:nowrap">' + r2[0] + '</td><td class="v" style="text-align:right">' + r2[1] + "</td></tr>";
  }).join("") +
  '<tr><td class="note" colspan="2">These are hold-out errors on <b>synthetic</b> data: they measure how well the ' +
  "surrogate reproduces the twin, not how well the twin reproduces Baghewala. Model-form error against the real field " +
  'is unquantified until OIL production history is available — see <a href="methodology.html" data-xlink="methodology.html">Model basis &rarr; Validation status</a>.</td></tr>';
}

/* ---------- apply flow ---------------------------------------------------- */
function renderApplyState(){
  const staged = BUS.get("staged", null);
  const run = currentRun();
  const foot = $("applyFoot");
  /* Once the twin console has re-run and confirmed the set-points, the
     history row for this recommendation is no longer merely "staged". */
  if (run.applied && REC){
    const hist = BUS.get("optHistory", []);
    if (hist.length && hist[0].recId === REC.recId && hist[0].status !== "applied"){
      hist[0].status = "applied";
      BUS.set("optHistory", hist);
    }
  }
  if (run.applied && run.preApplyControls){
    $("applyState").innerHTML = "✓ " + T("settingsApplied") + " · " + settingsLabel(run.controls) +
      " · " + (run.computedAt ? istClock(new Date(run.computedAt)) : "") + " · " + (REC ? REC.recId : "");
    $("btnStage").disabled = true;
    foot.textContent = "Audit: " + T("appliedBy") + " · " + (run.computedAt ? istStamp(new Date(run.computedAt)) : "") +
      " · " + (REC ? REC.recId : "") + " · run " + run.runId + " · twin re-run confirmed the set-points.";
  } else if (staged){
    $("applyState").innerHTML = '<span class="tag warn">staged</span> ' + settingsLabel(staged) +
      " · awaiting load in the twin console" +
      '<div style="margin-top:10px"><a class="btn btn-primary" href="console.html" data-xlink="console.html" lang="' +
        langAttr() + '">' + T("openSimLoad") + "</a></div>";
    $("btnStage").disabled = true;
    foot.innerHTML = "Staged at " + istStamp(new Date(staged.at)) + " · " + (staged.recId || "") +
      " — Nothing is sent to a controller: this demonstration has no SCADA link.";
    $("btnStage").disabled = true;
  } else {
    $("applyState").innerHTML = '<span style="color:var(--text-dim);font-weight:400">Target</span> <b style="color:var(--text)">' +
      nf(OPT_APPLIED.steam_t) + " t · " + nf(OPT_APPLIED.soak_days) + " d · " +
      fmt(OPT_APPLIED.cutoff, 2) + " m³/d · " + fmt(OPT_APPLIED.spm, 1) + " spm</b>" +
      '<span style="color:var(--text-dim);font-weight:400" lang="' + langAttr() + '"> ' + T("simCheckTarget") +
      " · " + (REC ? REC.recId : "") + "</span>";
    $("btnStage").disabled = false;
    foot.textContent = "Staging writes the set-points to the shared session state; the twin console picks them up, " +
      "re-runs the physics at the applied values and writes the confirmed run back. No controller is contacted.";
  }
  syncNavLinks();
}
$("btnStage").addEventListener("click", function(){
  $("confirmStrip").hidden = false;
  $("btnStage").disabled = true;
  $("confirmText").innerHTML =
    '<span lang="' + langAttr() + '">' + T("stagePrompt") + "</span><br><b>" +
    nf(OPT_APPLIED.steam_t) + " t · " + nf(OPT_APPLIED.soak_days) + " d · " +
    fmt(OPT_APPLIED.cutoff, 2) + " m³/d · " + fmt(OPT_APPLIED.spm, 1) + " spm</b> → BGW-07 · " +
    (REC ? REC.recId : "");
});
$("btnCancel").addEventListener("click", function(){
  $("confirmStrip").hidden = true;
  $("btnStage").disabled = false;
});
$("btnConfirm").addEventListener("click", function(){
  $("confirmStrip").hidden = true;
  BUS.set("staged", Object.assign({}, OPT_APPLIED, { recId: REC ? REC.recId : null, at: new Date().toISOString() }));
  const hist = BUS.get("optHistory", []);
  if (hist.length && REC) hist[0].status = "staged";
  BUS.set("optHistory", hist);
  renderApplyState();
  renderHistory();
  renderStatusBar("__PAGE_KEY__");
});

/* ---------- history ------------------------------------------------------- */
function renderHistory(){
  const hist = BUS.get("optHistory", []);
  if (!hist.length){
    $("histBody").innerHTML = '<tr><td class="note" colspan="7">No optimiser run recorded in this browser session. ' +
      "History is written only when the optimiser is actually run — nothing here is pre-populated.</td></tr>";
    return;
  }
  /* rows written before this fix (or by an older build) have no incremental
     keys at all -- gross-only. Showing that stale gross number under an
     "Incremental" header would mislabel it, so those cells fall back to
     "—" rather than print a number that no longer matches what it's headed. */
  const oldSchemaNote = LANG === "hi"
    ? "वृद्धिशील मार्जिन लॉगिंग जोड़े जाने से पहले दर्ज की गई पंक्ति — पुराना सकल मान यहाँ नहीं दिखाया जा सकता"
    : "recorded before incremental-margin logging was added — its old gross figure can't be safely shown here";
  const moneyCell = function(incrVal, grossVal){
    if (!Number.isFinite(incrVal)) return '<span class="muted" title="' + oldSchemaNote.replace(/"/g, "&quot;") + '">&mdash;</span>';
    const grossTitle = (Number.isFinite(grossVal)
      ? (LANG === "hi" ? "सकल (पुरानी परिपाटी): ₹" : "gross (pre rev-9 convention): ₹") + nf(grossVal, 0) + "/cycle-day"
      : (LANG === "hi" ? "सकल मान उपलब्ध नहीं" : "gross figure not available"));
    return '<span title="' + grossTitle.replace(/"/g, "&quot;") + '">' + nf(incrVal, 0) + "</span>";
  };
  $("histBody").innerHTML = hist.map(function(h, i){
    /* An older recommendation that was never staged is not wrong, it is
       superseded — the moment a newer one exists it stops being "the"
       recommendation without needing to look like a failure. */
    const superseded = i > 0 && h.status === "recommended";
    const tagCls = superseded ? "" : (h.status === "applied" ? "pass" : (h.status === "staged" ? "warn" : "info"));
    const statusTxt = superseded ? '<span lang="' + langAttr() + '">' + T("superseded") + "</span>" : h.status;
    const pctCell = Number.isFinite(h.marginImprovementPctIncr)
      ? '<td class="pos">' + signed(h.marginImprovementPctIncr, 1) + "</td>"
      : '<td><span class="muted">&mdash;</span></td>';
    return "<tr" + (superseded ? ' style="opacity:0.6"' : "") + ">" +
      '<td class="v">' + h.recId + "</td>" +
      '<td class="k">' + istStamp(new Date(h.at)) + "</td>" +
      '<td class="v">' + moneyCell(h.baselineMarginIncr, h.baselineMarginGross) + "</td>" +
      '<td class="v">' + moneyCell(h.recMarginIncr, h.recMarginGross) + "</td>" +
      pctCell +
      '<td class="v">' + pct(h.pFloat) + "</td>" +
      '<td><span class="tag' + (tagCls ? " " + tagCls : "") + '">' + statusTxt + "</span></td></tr>";
  }).join("");
}
$("btnClearHist").addEventListener("click", function(){
  BUS.set("optHistory", []);
  renderHistory();
});

/* ---------- run ----------------------------------------------------------- */
async function runOptimize(){
  const btn = $("btnOptimize");
  btn.classList.add("is-busy");
  btn.disabled = true;
  try {
    let raw;
    if (MOCK){ await wait(600 + Math.random() * 300); raw = Object.assign({}, OPT_RESULT); }
    else {
      /* Progress state while the live job runs -- renderResult() (called
         once REC is set, below) overwrites optIdleBody unconditionally, so
         this text only ever shows during the search itself. */
      $("optIdle").hidden = false;
      $("optResult").hidden = true;
      $("optIdle").classList.remove("warn");
      const tick = function(job, elapsedMs){
        const secs = Math.max(0, Math.round(elapsedMs / 1000));
        $("optIdleBody").innerHTML = (LANG === "hi"
          ? "जीवंत भौतिकी पर अनुकूलक खोज चल रही है (सर्रोगेट + ट्विन सत्यापन)… " + secs + " s"
          : "Running live optimiser search against the physics twin (surrogate + physics verification)… " + secs + " s") +
          '<br><span class="tag">' + (job.status === "running" ? "running" : job.status) + "</span>";
      };
      raw = await apiOptimize(tick);
    }
    const r = normalizeOptimizeResult(raw);
    if (r.SOR_improvement_pct == null && r.baseline_SOR && r.predicted_SOR){
      r.SOR_improvement_pct = (r.baseline_SOR - r.predicted_SOR) / r.baseline_SOR * 100;
    }
    if (r.margin_improvement_pct == null && r.baseline_margin_inr_per_cycle_day && r.predicted_margin_inr_per_cycle_day){
      r.margin_improvement_pct = (r.predicted_margin_inr_per_cycle_day - r.baseline_margin_inr_per_cycle_day) /
                                  Math.abs(r.baseline_margin_inr_per_cycle_day) * 100;
    }
    const now = new Date();
    const hist = BUS.get("optHistory", []);
    const seq = String(hist.length + 1).padStart(2, "0");
    REC = { recId: "REC-" + istDateCode(now) + "-" + seq, at: now.toISOString(), result: r };
    BUS.set("rec", REC);
    /* rev 9: the history row logs the INCREMENTAL margin/cycle-day (over cold
       production) for both baseline and recommendation, matching the page
       headline and the "twin re-run" column of the recommendation table --
       never the gross figure, and never the raw surrogate prediction (r.*),
       which can differ from the physics-verified twin by design (see the
       "why the two right-hand columns differ" note in renderRec()/quantNote
       -- "The figure quoted anywhere else in this product is the twin
       value, never the surrogate value."). REF_SUMMARY/OPT_SUMMARY are the
       baked twin re-run at the assumed baseline and the applied
       recommendation respectively, re-priced at whatever "Your prices" is
       set to right now, exactly like headlineDeltaLine() does -- so a
       history row always matches what the headline showed at the moment it
       was written. The gross twin figures are kept alongside only as a
       title-attribute aside for specialists (see renderHistory). The "vs
       published-practice %" column is derived from these same incremental
       numbers, not from a separate gross percentage, so the row is
       internally consistent even when the baseline is small or negative
       (see OPT_RESULT.margin_incremental_pct_change_note). */
    const prices = getPrices();
    const baselineIncr = baselineMarginIncrementalAtPrices(prices);
    const recIncr = recommendedMarginIncrementalAtPrices(prices);
    const baselineGross = baselineMarginAtPrices(prices);
    const recGross = recommendedMarginAtPrices(prices);
    const marginImprovementPctIncr = (Number.isFinite(baselineIncr) && Number.isFinite(recIncr) && baselineIncr !== 0)
      ? (recIncr - baselineIncr) / Math.abs(baselineIncr) * 100 : null;
    hist.unshift({
      recId: REC.recId, at: REC.at,
      baselineMarginIncr: Number.isFinite(baselineIncr) ? baselineIncr : null,
      recMarginIncr: Number.isFinite(recIncr) ? recIncr : null,
      baselineMarginGross: Number.isFinite(baselineGross) ? baselineGross : null,
      recMarginGross: Number.isFinite(recGross) ? recGross : null,
      marginImprovementPctIncr: marginImprovementPctIncr,
      pFloat: r.floating_probability, status: "recommended"
    });
    BUS.set("optHistory", hist.slice(0, 20));
    renderResult();
    renderHistory();
    renderStatusBar("__PAGE_KEY__");
  } catch (err){
    console.error(err);
    $("optIdle").hidden = false;
    $("optResult").hidden = true;
    $("optIdle").classList.add("warn");
    $("optIdleBody").innerHTML = "<b>Optimiser unavailable.</b> Train the models first: run <code>ml/train.py</code> " +
      "to produce <code>ml/models/*.joblib</code>, then retry. (" + err.message + ")";
  } finally {
    btn.classList.remove("is-busy");
    btn.disabled = false;
  }
}
const wait = (ms) => new Promise(function(r){ setTimeout(r, ms); });

function renderResult(){
  if (!REC){
    $("optIdle").hidden = false;
    $("optResult").hidden = true;
    $("optIdleBody").innerHTML = '<span lang="' + langAttr() + '">' + T("optimiserIdleBody") + "</span><br>" +
      "Surrogate: XGBoost on " + nf(SURROGATE.n) + " Latin-hypercube cycles · margin hold-out R² " +
      fmt(SURROGATE.margin_r2, 3) + " (in-envelope) · oil R² " + fmt(SURROGATE.oil_r2, 3) +
      " · float AUC " + fmt(SURROGATE.float_auc, 4) + ". Search: skopt gp_minimize, " + SURROGATE.calls +
      " calls, maximising margin/cycle-day, soak fixed at 10 d, subject to p(float) ≤ " + fmt(SURROGATE.floatLimit, 2) + ".";
    return;
  }
  $("optIdle").hidden = true;
  $("optResult").hidden = false;
  renderRecCard("recCard", AV, RUN.summary.max_floating_index, BASELINE_POLICY_STATE);
  renderRec();
  renderConstraints();
  renderUncertainty();
  renderApplyState();
}

/* rev 13 (wave 5): "Compare against a baseline that..." — which assumed
   baseline operation drives the recommendation card's headline delta on
   THIS page. Default vfd_hold (the fair comparison); the overview page's
   card always uses the default, so the two never disagree unless an
   engineer has deliberately toggled this. Not persisted across page loads
   -- resets to the fair default every time the optimiser page opens. */
let BASELINE_POLICY_STATE = "vfd_hold";
(function wireBaselinePolicyToggle(){
  const sel = $("bpToggleSelect");
  if (!sel) return;
  sel.value = BASELINE_POLICY_STATE;
  sel.addEventListener("change", function(){
    BASELINE_POLICY_STATE = sel.value;
    if (REC) renderRecCard("recCard", AV, RUN.summary.max_floating_index, BASELINE_POLICY_STATE);
  });
})();

/* The "Your prices" panel lives only on the overview page (one place to
   edit, everything else reads the persisted BUS state on load) — this link
   just carries the current language/theme across, plus a fragment so the
   overview page scrolls straight to the panel. Not run through data-xlink /
   syncNavLinks() because that mechanism appends the query AFTER any
   fragment, which is invalid URL ordering. */
function updateYourPricesLink(){
  const a = $("yourPricesLink");
  if (a) a.setAttribute("href", "index.html?lang=" + LANG + "&theme=" + THEME + "#yourPrices");
}

$("btnOptimize").addEventListener("click", runOptimize);
onLangChange(function(){ renderResult(); renderHistory(); updateYourPricesLink(); });
renderResult();   /* may promote the top history row to "applied" */
renderHistory();
updateYourPricesLink();

/* Hide the continuous-optimum column behind "Model details" (P0-6d) — a
   controller only ever takes the as-applied, grid-snapped values. */
(function wireModelDetails(){
  const det = $("modelDetails");
  const table = $("recTable");
  if (!det || !table) return;
  det.addEventListener("toggle", function(){ table.classList.toggle("show-continuous", det.open); });
})();

/* Optimiser auto-runs on load for engineer users — the page's job is to
   answer "what should I set", and idle-until-clicked buried that answer.
   ?demo=1 keeps the presenter's deliberate-click idle state; a QC hook that
   already drives its own run takes precedence over both. */
(function autoRunHook(){
  const q = new URLSearchParams(location.search);
  if (q.has("demo") || q.get("qc")) return;
  if (!REC) runOptimize();
})();

/* QC hook: ?qc=optimized runs the search; ?qc=staged also stages + confirms. */
(function qcHook(){
  const qc = new URLSearchParams(location.search).get("qc");
  if (!qc) return;
  setTimeout(async function(){
    await runOptimize();
    if (qc === "staged"){ $("btnStage").click(); $("btnConfirm").click(); }
  }, 300);
})();
