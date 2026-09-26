/* =========================================================================
   TWIN CONSOLE — the operator page.
   Set-points, simulation, replay, cross-section, dynamometer, floating-risk
   alarm. Every result computed here is written back to the state bus so the
   overview and optimiser pages report on the same run.
   ========================================================================= */
bootChrome("__PAGE_KEY__", "__NAV_KEY__");

const wait = (ms) => new Promise(function(r){ setTimeout(r, ms); });

/* ---------- fallback physics for off-reference set-points ---------------- */
function mu_cP(T_C){
  const k = Math.log(P.mu_ref_cP / 50) / (150 - P.T_ref_C);
  return P.mu_ref_cP * Math.exp(-k * (T_C - P.T_ref_C));
}
function summarize(rows){
  const produce = rows.filter(function(r){ return r.phase === "produce"; });
  const oil_total = produce.reduce(function(s, r){ return s + r.oil_m3d; }, 0);
  const steam_total = rows.length ? rows[rows.length - 1].steam_t_cum : 0;
  const energy_total = rows.reduce(function(s, r){ return s + r.energy_kWh; }, 0);
  const max_fi = rows.reduce(function(m, r){ return Math.max(m, r.floating_index); }, 0);
  return {
    oil_total_m3: oil_total,
    SOR_t_per_m3: oil_total > 0 ? steam_total / oil_total : NaN,
    energy_per_m3_kWh: oil_total > 0 ? energy_total / oil_total : NaN,
    days_total: rows.length ? rows[rows.length - 1].day : 0,
    max_floating_index: max_fi,
    failures_expected: max_fi > RISK_LIMIT ? 1 : 0
  };
}
/* Retuned for physics rev 5 magnitudes (was tuned to v1's ~75 m³/d peaks and
   61-day cycles): peak oil ~2-4 m³/d, cycles ~150-300 days, SOR in the
   3-8 range, floating index rising with SPM and crossing the 0.60 alarm
   threshold only well past the practice band (~12 spm) — same qualitative
   shape as before (pump-limited plateau, then viscosity-driven decline),
   just rescaled. Stays an "Approximate run", not a physics substitute. */
function mockSimulate(steam_t, soak_days, cutoff, spm, stroke_in, p_wellhead_kgf_cm2, floatPolicy){
  const policy = floatPolicy || "vfd_hold";
  const baked = bakedFor(steam_t, soak_days, cutoff, spm, stroke_in, p_wellhead_kgf_cm2, policy);
  if (baked) return { summary: baked.summary, series: baked.series, baked: true };
  const rows = [];
  const injectDays = Math.max(1, Math.round(steam_t / P.steam_injection_rate_tpd));
  const soakD = Math.round(soak_days);
  /* ASSUMPTION: peak heated-zone temperature scales with steam volume, capped
     near injection temperature; anchored so 1,300 t peaks ~223 °C, in the
     ballpark of the baked real-twin run at reference settings. */
  const Tpeak = Math.min(P.T_injection_C, P.T_initial_C + 192 * (steam_t / 1300));
  let day = 0, steamCum = 0, TatSoakEnd = Tpeak;

  for (let d = 1; d <= injectDays; d++){
    day = d;
    const T = P.T_initial_C + (Tpeak - P.T_initial_C) * (d / injectDays);
    const stepSteam = Math.min(P.steam_injection_rate_tpd, Math.max(0, steam_t - steamCum));
    steamCum += stepSteam;
    rows.push({ day: day, phase: "inject", T_res_C: T, mu_cP: mu_cP(T), P_res_kPa: P.P_initial_kPa,
      oil_m3d: 0, steam_t_cum: steamCum, energy_kWh: stepSteam * 1000 * P.latent_heat_Jkg / 3.6e6,
      rod_load_kN: 0, floating_index: 0 });
  }
  const tauSoak = 40;
  for (let i = 1; i <= soakD; i++){
    day++;
    const T = P.T_initial_C + (Tpeak - P.T_initial_C) * Math.exp(-i / tauSoak);
    TatSoakEnd = T;
    rows.push({ day: day, phase: "soak", T_res_C: T, mu_cP: mu_cP(T), P_res_kPa: P.P_initial_kPa,
      oil_m3d: 0, steam_t_cum: steamCum, energy_kWh: 0, rod_load_kN: 0, floating_index: 0 });
  }
  /* Longer viscosity-driven decline (rev-5 cycles run 150-300 d, not 50-60):
     the decline time constant grows with the steam charge, same as a bigger
     heated zone taking longer to cool. Pump ceiling ~2.6 m³/d at the
     practice-band reference (5 spm), rescaled from the old v1 ~75 m³/d. */
  const tauProd = 120 + steam_t / 8;
  let oil = Infinity, p = 0;
  /* rev 13.1: the "Rod-float response" selector now actually drives this
     approximate model (it previously only relabelled the banner/explanation
     text — re-score item 6/N6). "none" runs on unmodified, exactly as
     before; "pull" ends the cycle 3 days after the float alarm first fires;
     the two VFD policies throttle the EFFECTIVE spm down each produce day to
     hold the floating index at the 0.60 line, to a floor (2 spm for
     vfd_hold, half the requested speed for vfd_then_pull), then pull 3 days
     after even the floor can no longer hold the line. */
  const vfdFloor = policy === "vfd_then_pull" ? Math.max(2, spm / 2) : 2;
  let alarmStreak = 0;
  while (oil >= cutoff && p < 500){
    p++; day++;
    const T = P.T_initial_C + (TatSoakEnd - P.T_initial_C) * Math.exp(-p / tauProd);
    const mu = mu_cP(T);
    const muFactor = Math.min(1, mu / 4000);
    /* Floating index: rises with SPM across the full slider range (3-12,
       not just the 3-6 practice band the optimiser searches) and with
       viscosity as the heated zone cools. Stays under the 0.60 alarm
       threshold through the practice band even at high viscosity, and
       reliably crosses it only well past it (~12 spm) — same demo the
       "Try high speed (12 SPM)" stress test always relied on. */
    let effSpm = spm;
    if (policy === "vfd_hold" || policy === "vfd_then_pull"){
      const target = Math.max(0, (RISK_LIMIT - 0.3 * muFactor) / 0.9);
      const maxSpmFactor = Math.pow(target, 1 / 1.5);
      const desiredSpm = SPM_SLIDER.min + maxSpmFactor * (SPM_SLIDER.max - SPM_SLIDER.min);
      effSpm = Math.max(vfdFloor, Math.min(spm, desiredSpm));
    }
    const pumpCap = 2.2 * (effSpm / RANGES.spm.default);
    oil = Math.max(0, Math.min(pumpCap, 165 / mu));
    const spmFactor = (effSpm - SPM_SLIDER.min) / (SPM_SLIDER.max - SPM_SLIDER.min);
    const floating = Math.max(0, Math.min(1, 0.9 * Math.pow(spmFactor, 1.5) + 0.3 * muFactor));
    const rodLoad = 52 + effSpm * 1.4 + muFactor * 24;
    rows.push({ day: day, phase: "produce", T_res_C: T, mu_cP: mu, P_res_kPa: P.P_initial_kPa,
      oil_m3d: oil, steam_t_cum: steamCum, energy_kWh: rodLoad * P.stroke_m * effSpm * 1440 * 0.4 / 3600,
      rod_load_kN: rodLoad, floating_index: floating, spm: effSpm });
    if (floating > RISK_LIMIT) alarmStreak++; else alarmStreak = 0;
    if ((policy === "pull" || policy === "vfd_then_pull") && alarmStreak >= 3) break;
    if (policy === "vfd_hold" && effSpm <= vfdFloor + 0.05 && alarmStreak >= 3) break;
    if (oil < cutoff) break;
  }
  return { summary: summarize(rows), series: rows };
}
async function apiSimulate(steam_t, soak_days, cutoff, spm, stroke_in, p_wellhead_kgf_cm2, floatPolicy){
  /* stroke_in/p_wellhead_kgf_cm2 are now real controls on /simulate (and
     /api/simulate) -- api/routers/simulate.py validates stroke_in against
     the six API sizes and p_wellhead_kgf_cm2 against the CONFIRMED 85-97
     range, then passes them through to twin.cycle.simulate_css_cycle, so a
     live-API run honours both sliders exactly like MOCK (file://)'s
     bakedFor()/mockSimulate() above already did.
     rev 13.1: float_policy is sent too, matching the console's "Rod-float
     response" selector -- but api/routers/simulate.py does not declare or
     read this parameter yet, so a live-API run still simulates under the
     params' own default policy (pull) regardless of the selector; FastAPI
     silently ignores an undeclared query parameter rather than erroring, so
     this is forward-compatible and costs nothing today. See
     dashboard/README.md §6 and re-score item 6 -- fixing this for real needs
     a twin/cycle.py-side change, which is out of scope here. */
  const res = await fetch(API_BASE + "/simulate?steam_t=" + steam_t + "&soak_days=" + soak_days +
                          "&cutoff=" + cutoff + "&spm=" + spm +
                          "&stroke_in=" + stroke_in + "&p_wellhead_kgf_cm2=" + p_wellhead_kgf_cm2 +
                          "&float_policy=" + encodeURIComponent(floatPolicy || "vfd_hold"));
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}

/* ---------- controls ------------------------------------------------------ */
/* rev 12: two more surface controls the 5-D physics search now optimises --
   stroke length (a <select> over the 6 discrete API sizes, not a slider:
   the twin only has a physics model for these sizes) and injection
   (wellhead) pressure (a continuous slider, 85-97 kgf/cm2, CONFIRMED range).
   Defaults = baseline (b): 86 in / 91 kgf/cm2. */
function readControls(){
  return {
    steam_t: Number($("in_steam_t").value),
    soak_days: Number($("in_soak_days").value),
    cutoff: Number($("in_cutoff").value),
    spm: Number($("in_spm").value),
    stroke_in: Number($("in_stroke").value),
    p_wellhead_kgf_cm2: Number($("in_pressure").value)
  };
}
function writeControls(c){
  $("in_steam_t").value = c.steam_t;
  $("in_soak_days").value = c.soak_days;
  $("in_cutoff").value = c.cutoff;
  $("in_spm").value = c.spm;
  $("in_stroke").value = c.stroke_in || STROKE_DEFAULT_IN;
  $("in_pressure").value = c.p_wellhead_kgf_cm2 || RANGES.p_wellhead.default;
  ["in_steam_t", "in_soak_days", "in_cutoff", "in_spm", "in_stroke", "in_pressure"].forEach(function(id){
    $(id).dispatchEvent(new Event("input", { bubbles: true }));
  });
}
function wireSliderReadout(inputId, outId, decimals){
  const input = $(inputId), out = $(outId);
  const update = function(){ out.textContent = nf(Number(input.value), decimals); };
  input.addEventListener("input", update);
  update();
}
wireSliderReadout("in_steam_t", "out_steam_t", 0);
wireSliderReadout("in_soak_days", "out_soak_days", 0);
wireSliderReadout("in_cutoff", "out_cutoff", 2);
wireSliderReadout("in_spm", "out_spm", 1);
wireSliderReadout("in_pressure", "out_pressure", 0);

function updatePumpDuration(){
  const spm = Number($("in_spm").value);
  const t = (spm - SPM_SLIDER.min) / (SPM_SLIDER.max - SPM_SLIDER.min);
  document.documentElement.style.setProperty("--pump-duration", (3.2 - t * 2.0).toFixed(2) + "s");
}
$("in_spm").addEventListener("input", updatePumpDuration);
updatePumpDuration();

/* ---------- page state ---------------------------------------------------- */
const STATE = {
  ready: false, sim: null, controls: null, row: null,
  phase: "produce", replayPhaseKey: "idle",
  riskFI: 0, riskFailures: 0, riskProb: null,
  runSeq: 0, computedAt: null, alarmAcked: false,
  applied: false, preApplySummary: null, preApplyControls: null,
  /* rev 13 (wave 5): the operator's float response, a simulator control.
     Only VFD-hold is baked to full physics precision (data.js); the other
     three options relabel the mechanism (banner text, plain-language note)
     without changing the baked numbers -- see floatPolicyBakedNote. */
  floatPolicy: "vfd_hold"
};

/* ---------- rod-float response selector ----------------------------------- */
const FLOAT_POLICY_DESC_KEYS = {
  pull: "floatPolicyPullDesc", vfd_hold: "floatPolicyVfdHoldDesc",
  vfd_then_pull: "floatPolicyVfdThenPullDesc", none: "floatPolicyNoneDesc"
};
function renderFloatPolicyDesc(){
  const el = $("floatPolicyDesc");
  if (!el) return;
  const descKey = FLOAT_POLICY_DESC_KEYS[STATE.floatPolicy] || "floatPolicyVfdHoldDesc";
  const extra = STATE.floatPolicy === "vfd_hold" ? "" : " " + T("floatPolicyBakedNote");
  el.innerHTML = '<span lang="' + langAttr() + '">' + T(descKey) + extra + "</span>";
}
(function wireFloatPolicySelect(){
  const sel = $("in_floatPolicy");
  if (!sel) return;
  sel.addEventListener("change", function(){
    STATE.floatPolicy = sel.value;
    renderFloatPolicyDesc();
    redrawAll();
  });
})();
/* The optimiser's classifier probability travels with the recommendation. */
(function(){
  const rec = BUS.get("rec", null);
  if (rec && rec.result) STATE.riskProb = rec.result.floating_probability;
})();

/* ---------- charts -------------------------------------------------------- */
function phaseSegments(series){
  const segs = []; let i = 0;
  while (i < series.length){
    const phase = series[i].phase; let j = i;
    while (j < series.length && series[j].phase === phase) j++;
    segs.push({ phase: phase, startDay: series[i].day, endDay: series[j - 1].day });
    i = j;
  }
  return segs;
}

function renderTimeSeries(series){
  const th = chartTheme();
  const x = series.map(function(r){ return r.day; });
  /* rev 12: water cut (state model) + floating index get their own sub-band
     (y4) between the reservoir/viscosity band and the oil-rate band, so the
     late-cycle emulsion inversion and the float-onset alarm are visible on
     the SAME chart as the rest of the cycle, not just in the telemetry
     strip. water_cut is only on baked (state-model) series -- an off-baked
     approximate run draws floating_index alone. */
  const hasWaterCut = series.some(function(r){ return Number.isFinite(r.water_cut) && r.water_cut > 0; });
  const traces = [
    { x: x, y: series.map(function(r){ return r.T_res_C; }), yaxis: "y", mode: "lines", name: "T",
      line: { color: th.t, width: 1.8, shape: "spline", smoothing: 0.3 },
      hovertemplate: "D+%{x:.1f} · %{y:.1f} °C<extra></extra>" },
    { x: x, y: series.map(function(r){ return r.mu_cP; }), yaxis: "y2", mode: "lines", name: "mu",
      line: { color: th.mu, width: 1.6 },
      hovertemplate: "D+%{x:.1f} · %{y:,.0f} cP<extra></extra>" },
    { x: x, y: series.map(function(r){ return r.oil_m3d; }), yaxis: "y3", mode: "lines", name: "q",
      line: { color: th.q, width: 1.8 },
      hovertemplate: "D+%{x:.1f} · %{y:.1f} m³/d<extra></extra>" },
    { x: x, y: series.map(function(r){ return r.floating_index || 0; }), yaxis: "y4", mode: "lines", name: "fi",
      line: { color: th.red, width: 1.6 },
      hovertemplate: "D+%{x:.1f} · FI %{y:.2f}<extra></extra>" }
  ];
  if (hasWaterCut){
    traces.push({ x: x, y: series.map(function(r){ return Number.isFinite(r.water_cut) ? r.water_cut : null; }),
      yaxis: "y4", mode: "lines", name: "wc", line: { color: th.q, width: 1.4, dash: "dot" },
      hovertemplate: "D+%{x:.1f} · water cut %{y:.2f}<extra></extra>" });
  }
  const colors = { inject: th.bandInject, soak: th.bandSoak, produce: th.bandProduce };
  const segs = phaseSegments(series);
  const layout = {
    xaxis: { title: { text: T("day"), font: { family: FONT_FAMILY, size: 11, color: th.axis }, standoff: 4 },
      domain: [0, 1], anchor: "y3", gridcolor: th.grid, zeroline: false, tickfont: CFONT(), linecolor: th.line },
    yaxis: { domain: [0.56, 1], anchor: "x", gridcolor: th.grid, zeroline: false,
      tickfont: CFONT(th.t), ticksuffix: " °C", linecolor: th.line },
    yaxis2: { type: "log", overlaying: "y", side: "right", anchor: "x", showgrid: false,
      tickmode: "array", tickvals: [1, 10, 100, 1000, 10000], ticktext: ["1", "10", "100", "1k", "10k"],
      ticksuffix: " cP", tickfont: CFONT(th.mu) },
    yaxis3: { domain: [0, 0.28], anchor: "x", gridcolor: th.grid, zeroline: false, rangemode: "tozero",
      tickfont: CFONT(th.q), ticksuffix: " m³/d", nticks: 4, linecolor: th.line },
    yaxis4: { domain: [0.34, 0.50], anchor: "x", gridcolor: th.grid, zeroline: false, range: [0, 1],
      tickfont: CFONT(th.red), nticks: 3, linecolor: th.line },
    shapes: segs.map(function(s){
      return { type: "rect", xref: "x", yref: "paper", x0: s.startDay - 0.5, x1: s.endDay + 0.5,
        y0: 0, y1: 1, fillcolor: colors[s.phase], line: { width: 0 }, layer: "below" };
    }).concat([{ type: "line", xref: "x", x0: x[0] || 0, x1: x[x.length - 1] || 1, yref: "y4",
      y0: RISK_LIMIT, y1: RISK_LIMIT, line: { color: th.red, width: 1, dash: "dot" } }]),
    annotations: segs.map(function(s){
      return { x: (s.startDay + s.endDay) / 2, y: 1.06, xref: "x", yref: "paper",
        text: T(s.phase).toUpperCase(), showarrow: false,
        font: { family: FONT_FAMILY, size: 10, color: th.tick } };
    }).concat([{ x: 0, y: 0.50, xref: "paper", yref: "paper", xanchor: "left", yanchor: "bottom",
      text: T("floatIndexTm") + (hasWaterCut ? " / " + T("waterCutTm") : ""), showarrow: false,
      font: { family: FONT_FAMILY, size: 9.5, color: th.tick } }]),
    showlegend: false, hovermode: "x unified", hoverlabel: hoverLabel(th),
    paper_bgcolor: th.paper, plot_bgcolor: th.paper, font: CFONT(),
    margin: M({ r: 52, t: 22 })
  };
  Plotly.react("chartTimeseries", traces, layout, PLOTLY_CONFIG);
  $("lgT").style.background = th.t;
  $("lgMu").style.background = th.mu;
  $("lgQ").style.background = th.q;
}

/* ---------- dynamometer card (computed) -----------------------------------
   Replaces the old illustrative lens shape with the baked surface + pump
   cards from twin.dyno.compute_cards() (DYNO_CARDS, dashboard/src/dyno-data.js).
   The card shown follows the replay/scrub day: nearest of the 3 baked days
   (early/mid/late) within the active scenario (baseline vs recommendation,
   matched on steam_t/soak_days/cutoff — spm is ignored so the 12-SPM stress
   test still resolves to its scenario's baked stress card). An off-baked
   (approximate) run falls back to the nearest baked card by (spm, mu) across
   all 8 baked cards — never an invented shape. */
const CARD_TYPE_META = {
  full_pump:         { label: "cardTypeFullPump",   mean: "meanFullPump",   cls: "pass" },
  fluid_pound:       { label: "cardTypeFluidPound", mean: "meanFluidPound", cls: "warn" },
  heavy_oil_viscous: { label: "cardTypeViscous",     mean: "meanViscous",   cls: "warn" },
  gas_interference:  { label: "cardTypeGas",         mean: "meanGas",       cls: "warn" },
  rod_float:         { label: "cardTypeRodFloat",    mean: "meanRodFloat",  cls: "fail" }
};
/* Same set-points as BASELINE_PUBLISHED / OPT_APPLIED (core.js), spm ignored
   on purpose: the stress test only ever changes spm, never the CSS set-points.
   rev 12: stroke/pressure now matched too (a baseline run at the rec's stroke
   would otherwise wrongly resolve to the baseline's own dyno card). */
const DYNO_SCENARIO_SETTINGS = {
  baseline: { steam_t: 1300, soak_days: 10, cutoff: 1.3, stroke_in: 86, p_wellhead_kgf_cm2: 91 },
  /* rev 13: recommendation moved to 89 kgf/cm2 (injection-margin gate) and a
     4.5-spm VFD-hold start, both under the wave-5 policy control (spm is
     still ignored here on purpose -- see the comment above). */
  recommendation: { steam_t: 1000, soak_days: 10, cutoff: 0.60, stroke_in: 64, p_wellhead_kgf_cm2: 89 }
};
function matchDynoScenario(c){
  const near = function(a, b, eps){ return Math.abs(a - b) <= eps; };
  const keys = Object.keys(DYNO_SCENARIO_SETTINGS);
  for (let i = 0; i < keys.length; i++){
    const s = DYNO_SCENARIO_SETTINGS[keys[i]];
    if (near(c.steam_t, s.steam_t, 1) && near(c.soak_days, s.soak_days, 0.01) && near(c.cutoff, s.cutoff, 0.01) &&
        near(c.stroke_in || STROKE_DEFAULT_IN, s.stroke_in, 0.5) &&
        near(c.p_wellhead_kgf_cm2 || RANGES.p_wellhead.default, s.p_wellhead_kgf_cm2, 0.5)) return keys[i];
  }
  return null;
}
function pickDynoCard(controls, day, mu, spmActual){
  const scenario = matchDynoScenario(controls);
  const stress = spmActual >= (SPM_SLIDER.max - 0.6);
  if (scenario){
    const cards = DYNO_CARDS.scenarios[scenario].cards;
    if (stress){
      const sc = cards.filter(function(x){ return x.key === "stress_12spm"; })[0];
      if (sc) return { card: sc, scenario: scenario, exact: true, byDay: false, stress: true };
    }
    const pool = cards.filter(function(x){ return x.key !== "stress_12spm"; });
    let best = pool[0];
    for (let i = 1; i < pool.length; i++){
      if (Math.abs(pool[i].day - day) < Math.abs(best.day - day)) best = pool[i];
    }
    return { card: best, scenario: scenario, exact: true, byDay: true, stress: false };
  }
  /* Approximate run: nearest baked card by (spm, mu) over every scenario's cards. */
  const pool = [];
  Object.keys(DYNO_CARDS.scenarios).forEach(function(s){
    DYNO_CARDS.scenarios[s].cards.forEach(function(c){ pool.push(Object.assign({ _scenario: s }, c)); });
  });
  const dist = function(c){
    return Math.abs(spmActual - c.spm) / 12 + Math.abs(Math.log10(mu + 1) - Math.log10(c.mu_cP + 1));
  };
  let best = pool[0], bd = dist(pool[0]);
  for (let i = 1; i < pool.length; i++){
    const d = dist(pool[i]);
    if (d < bd){ bd = d; best = pool[i]; }
  }
  return { card: best, scenario: best._scenario, exact: false, byDay: false, stress: false };
}
function closedLoop(pos, load){
  const x = pos.slice(), y = load.slice();
  if (x.length){ x.push(x[0]); y.push(y[0]); }
  return { x: x, y: y };
}
function dynoCardTraces(card, th){
  const pump = closedLoop(card.downhole.position_m, card.downhole.load_kN);
  const surf = closedLoop(card.surface.position_m, card.surface.load_kN);
  const traces = [
    { x: pump.x, y: pump.y, mode: "lines", line: { color: th.t, width: 1.8 },
      hovertemplate: T("atPump") + " · %{x:.2f} m · %{y:.0f} kN<extra></extra>" },
    { x: surf.x, y: surf.y, mode: "lines", line: { color: th.mu, width: 2 },
      hovertemplate: T("atSurface") + " · %{x:.2f} m · %{y:.0f} kN<extra></extra>" }
  ];
  /* Rod float: highlight the near-zero (clamp-separated) segment of the
     surface card so the "strongest 15 seconds" of the demo reads at a glance. */
  if (card.card_type === "rod_float"){
    const xs = [], ys = [];
    let inSeg = false;
    const thresh = Math.max(1.0, card.min_prl_kN + 1.0);
    for (let i = 0; i < surf.x.length; i++){
      if (surf.y[i] <= thresh){ xs.push(surf.x[i]); ys.push(surf.y[i]); inSeg = true; }
      else if (inSeg){ xs.push(null); ys.push(null); inSeg = false; }
    }
    if (xs.length) traces.push({ x: xs, y: ys, mode: "lines", line: { color: th.red, width: 5 },
      hoverinfo: "skip", showlegend: false });
  }
  return traces;
}
/* rev 12: stroke length is now a lever (64-144 in) -- DYNO_CARDS.stroke_m is
   only params' GLOBAL default (86 in), wrong for a recommendation card
   baked at 64 in. Read the actual stroke off the card's own surface curve
   (position_m runs 0 -> that scenario's real stroke) instead. */
function cardStrokeM(card){
  return (card && card.surface && card.surface.position_m && card.surface.position_m.length)
    ? Math.max.apply(null, card.surface.position_m) : DYNO_CARDS.stroke_m;
}
function dynoLayout(card, th){
  const top = Math.max(20, card.peak_prl_kN * 1.15);
  const strokeM = cardStrokeM(card);
  return {
    xaxis: { title: { text: T("strokePos"), font: { family: FONT_FAMILY, size: 11, color: th.axis }, standoff: 4 },
      gridcolor: th.grid, zeroline: false, tickfont: CFONT(), dtick: 0.5, tickformat: ".1f",
      range: [-0.08, strokeM + 0.08], linecolor: th.line },
    yaxis: { title: { text: T("rodLoad"), font: { family: FONT_FAMILY, size: 11, color: th.axis }, standoff: 4 },
      gridcolor: th.grid, zeroline: false, tickfont: CFONT(), range: [0, top], linecolor: th.line },
    shapes: [
      { type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: card.reference.W_rf_kN, y1: card.reference.W_rf_kN,
        line: { color: th.faint, width: 1, dash: "dot" } },
      { type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: card.reference.static_peak_kN, y1: card.reference.static_peak_kN,
        line: { color: th.faint, width: 1, dash: "dot" } }
    ],
    paper_bgcolor: th.paper, plot_bgcolor: th.paper, font: CFONT(),
    margin: M({ t: 8, b: 36 }), showlegend: false, hoverlabel: hoverLabel(th)
  };
}
function separatedFraction(card){
  const y = card.surface.load_kN;
  const thresh = Math.max(1.0, card.min_prl_kN + 1.0);
  let n = 0;
  for (let i = 0; i < y.length; i++) if (y[i] <= thresh) n++;
  return y.length ? n / y.length : 0;
}
function buildDynoDetailsNote(card, pick){
  const sepFrac = card.carrier_separation ? separatedFraction(card) : 0;
  const strokeM = cardStrokeM(card);
  const plungerFrac = card.plunger_stroke_m / strokeM;
  const periodS = 60 / card.spm;
  /* hydraulic_kW derived from the JSON's own fields with compute_cards()'s own
     formula (Fo * plunger stroke * fillage / period) -- not baked separately. */
  const hydraulicKW = card.reference.Fo_kN * card.plunger_stroke_m * Math.min(card.pump_fillage, 1) / periodS;
  const energyRatio = card.polished_rod_kW > 0 ? hydraulicKW / card.polished_rod_kW : NaN;
  const scenarioTxt = pick.scenario ? pick.scenario : "nearest baked case (approximate run)";
  return "<b>" + card.card_label + "</b> · " + scenarioTxt + " · day " + fmt(card.day, 1) + " · " +
    fmt(card.spm, 1) + " SPM · &mu; " + nf(card.mu_cP, 0) + " cP. Peak/min PRL " + fmt(card.peak_prl_kN, 1) + " / " +
    fmt(card.min_prl_kN, 1) + " kN (reference W_rf " + fmt(card.reference.W_rf_kN, 1) + " kN, static peak W_rf+Fo " +
    fmt(card.reference.static_peak_kN, 1) + " kN). Pump fillage " + pct(card.pump_fillage) + " · plunger stroke " +
    fmt(card.plunger_stroke_m, 2) + " m of " + fmt(strokeM, 2) + " m surface stroke (" + pct(plungerFrac) +
    "). Clamp-separated " + pct(sepFrac) + " of the cycle" +
    (card.carrier_separation
      ? " — the carrier bar rides above the rods (load reads &asymp;0) until the rising carrier re-catches them."
      : " — no separation.") +
    " Hydraulic &divide; polished-rod power " + fmt(energyRatio, 2) + " (" + fmt(hydraulicKW, 2) + " / " +
    fmt(card.polished_rod_kW, 2) + " kW). Separation onset for this rod string is &asymp;0.6 v_stroke/v_fall " +
    "(docs/model-improvement/DYNO_CARD_MODEL.md &sect;2d) — the same 0.6 line the floating-risk meter and the SPEC alarm use.";
}
function renderDynoShutIn(){
  const th = chartTheme();
  const s = DYNO_CARDS.stroke_m, y = ROD_HANG_KN;
  const trace = { x: [0, s], y: [y, y], mode: "lines", line: { color: th.faint, width: 1.8, dash: "dot" }, hoverinfo: "skip" };
  Plotly.react("chartDyno", [trace],
    dynoLayout({ peak_prl_kN: y * 1.2, reference: { W_rf_kN: y, static_peak_kN: y } }, th), PLOTLY_CONFIG);
  $("lgSurf").style.background = th.faint;
  $("lgPump").style.background = "transparent";
  $("dynoDayLabel").textContent = "";
  $("dynoApproxNote").hidden = true;
  const badge = $("dynoTypeBadge");
  badge.textContent = T("shutIn"); badge.className = "tag"; badge.setAttribute("lang", langAttr());
  const meaning = $("dynoMeaning");
  meaning.textContent = T("dynoShutInNote"); meaning.className = "rm-sentence"; meaning.setAttribute("lang", langAttr());
  $("dynoPeak").textContent = "—";
  $("dynoMin").textContent = "—";
  $("dynoStroke").textContent = fmt(s, 2);
  $("dynoDetailsNote").innerHTML = "Pump shut in — no dynamometer card while the well is in the inject or soak phase.";
}
/* Live wiring, 27 Sep 2026: /api/dyno/cards runs twin.dyno.compute_cards()
   directly at the CURRENT set-points (<=50 ms) instead of picking the
   nearest of the 8 baked cards -- see dashboard/README.md "Data source".
   Its return shape (twin/dyno.py compute_cards()) is flatter than a baked
   DYNO_CARDS scenario card (dashboard/src/dyno-data.js), so it's adapted
   into the same {surface, downhole, reference, ...} shape dynoCardTraces()/
   buildDynoDetailsNote() already render, rather than teaching those
   renderers two shapes. */
const DEFAULT_WATER_CUT = 0.85; // fallback only -- an off-baked row has no water_cut column (constant tubing_liquid model)
function estimateFillage(oilM3d, spmActual, waterCut){
  const wc = Number.isFinite(waterCut) ? waterCut : DEFAULT_WATER_CUT;
  const qLiq = Math.max(0, Number(oilM3d) || 0) / Math.max(1 - wc, 1e-6);
  const aP = Math.PI / 4 * P.plunger_d_m * P.plunger_d_m;
  const disp = aP * P.stroke_m * Math.max(spmActual, 1e-6) * 1440;
  return Math.min(1, Math.max(0.05, qLiq / Math.max(disp, 1e-9)));
}
function liveCardToBakedShape(raw, day){
  return {
    key: "live", day: day, mu_cP: raw.inputs.mu_cP, spm: raw.inputs.spm,
    pump_fillage: raw.pump_fillage, card_type: raw.card_type, card_label: raw.card_label,
    signatures: raw.signatures, peak_prl_kN: raw.peak_prl_kN, min_prl_kN: raw.min_prl_kN,
    plunger_stroke_m: raw.plunger_stroke_m, carrier_separation: raw.carrier_separation,
    min_rod_force_kN: raw.min_rod_force_kN, polished_rod_kW: raw.polished_rod_kW,
    reference: { W_rf_kN: raw.buoyant_rod_weight_kN, Fo_kN: raw.fluid_load_kN, static_peak_kN: raw.static_peak_kN },
    surface: { position_m: raw.position_m, load_kN: raw.load_surface_kN },
    downhole: { position_m: raw.plunger_position_m, load_kN: raw.load_downhole_kN }
  };
}
let _dynoReqToken = 0;
async function fetchLiveDynoCard(spmActual, mu, oilM3d, waterCut){
  const wc = Number.isFinite(waterCut) ? waterCut : DEFAULT_WATER_CUT;
  const fillage = estimateFillage(oilM3d, spmActual, wc);
  const url = API_BASE + "/api/dyno/cards?spm=" + spmActual + "&mu_cP=" + mu +
              "&fillage=" + fillage + "&water_cut=" + wc;
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}
function paintDynoCard(card, pick, th){
  Plotly.react("chartDyno", dynoCardTraces(card, th), dynoLayout(card, th), PLOTLY_CONFIG);
  $("lgSurf").style.background = th.mu;
  $("lgPump").style.background = th.t;
  const meta = CARD_TYPE_META[card.card_type] || CARD_TYPE_META.fluid_pound;
  const badge = $("dynoTypeBadge");
  badge.textContent = T(meta.label);
  badge.className = "tag " + meta.cls;
  badge.setAttribute("lang", langAttr());
  const meaning = $("dynoMeaning");
  meaning.textContent = T(meta.mean);
  meaning.className = "rm-sentence" + (card.card_type === "rod_float" ? " neg" : "");
  meaning.setAttribute("lang", langAttr());
  $("dynoPeak").textContent = fmt(card.peak_prl_kN, 1);
  $("dynoMin").textContent = fmt(card.min_prl_kN, 1);
  $("dynoStroke").textContent = fmt(cardStrokeM(card), 2);
  const dayEl = $("dynoDayLabel");
  if (pick.live) dayEl.textContent = T("day") + " " + Math.round(card.day) + " · μ ≈ " + nf(card.mu_cP, 0) + " cP · computed live";
  else if (pick.stress) dayEl.textContent = T("dynoStressTest") + " · μ ≈ " + nf(card.mu_cP, 0) + " cP";
  else if (pick.byDay) dayEl.textContent = T("day") + " " + Math.round(card.day) + " · μ ≈ " + nf(card.mu_cP, 0) + " cP";
  else dayEl.textContent = "μ ≈ " + nf(card.mu_cP, 0) + " cP";
  dayEl.setAttribute("lang", langAttr());
  $("dynoApproxNote").hidden = pick.exact;
  $("dynoDetailsNote").innerHTML = buildDynoDetailsNote(card, pick);
}
async function renderDynoPanel(row, controls){
  if (!row || row.phase !== "produce"){ renderDynoShutIn(); return; }
  const th = chartTheme();
  const c = controls || STATE.controls || readControls();
  const spmActual = row.spm || c.spm;
  const mu = row.mu_cP;
  if (!MOCK){
    const token = ++_dynoReqToken;
    try {
      const raw = await fetchLiveDynoCard(spmActual, mu, row.oil_m3d, row.water_cut);
      if (token !== _dynoReqToken) return; // a newer request already landed
      paintDynoCard(liveCardToBakedShape(raw, row.day), { exact: true, live: true }, th);
      return;
    } catch (err){
      console.error("live dyno card unavailable, falling back to nearest baked:", err);
      if (token !== _dynoReqToken) return;
      // fall through to the baked/nearest pick below
    }
  }
  const pick = pickDynoCard(c, row.day, mu, spmActual);
  paintDynoCard(pick.card, pick, th);
}

/* ---------- risk meter ---------------------------------------------------- */
function renderRisk(fi, failures, prob){
  const v = Math.max(0, Math.min(1, Number(fi) || 0));
  STATE.riskFI = v;
  if (failures !== undefined) STATE.riskFailures = failures;
  if (prob !== undefined) STATE.riskProb = prob;
  const el = $("rmValue");
  el.textContent = fmt(v, 2);
  el.classList.toggle("warn", v > 0.4 && v <= RISK_LIMIT);
  el.classList.toggle("alm", v > RISK_LIMIT);
  $("rmMarker").style.left = (v * 100).toFixed(1) + "%";
  $("riskFI").textContent = fmt(v, 2);
  $("riskFailures").textContent = (STATE.riskFailures === undefined || STATE.riskFailures === null) ? "—" : nf(STATE.riskFailures, 0);
  $("riskProb").textContent = (STATE.riskProb === undefined || STATE.riskProb === null) ? "—" : pct(STATE.riskProb);
  renderRiskState();
  renderRiskSentence(v);
}
function renderRiskSentence(fi){
  const el = $("rmSentence");
  if (!el) return;
  const spm = fmt((STATE.controls || readControls()).spm, 1);
  const fiTxt = fmt(fi, 2);
  const safe = fi <= RISK_LIMIT;
  el.innerHTML = LANG === "hi"
    ? (safe ? spm + " SPM पर " + T("rodsSafe") + " " + T("ofLimit") + " " + fiTxt
            : spm + " SPM पर " + T("rodsFloat") + " " + T("reduceSpeed"))
    : (safe ? T("rodsSafe") + " " + spm + " SPM — " + fiTxt + " " + T("ofLimit")
            : T("rodsFloat") + " " + spm + " SPM — " + T("reduceSpeed"));
  el.className = "rm-sentence" + (safe ? "" : " neg");
  el.setAttribute("lang", langAttr());
}
function renderRiskState(){
  const v = STATE.riskFI || 0;
  const key = v > RISK_LIMIT ? "exceeded" : (v > 0.4 ? "elevated" : "within");
  const el = $("rmState");
  el.textContent = T(key);
  el.setAttribute("lang", langAttr());
  el.style.color = v > RISK_LIMIT ? "var(--red)" : (v > 0.4 ? "var(--amber)" : "var(--text-dim)");
}

/* ---------- telemetry ----------------------------------------------------- */
function setSlot(id, html){
  const el = $(id).querySelector("b");
  if (el.innerHTML !== html) el.innerHTML = html;
}
function updateTelemetry(rowOrSeries, controls){
  const row = Array.isArray(rowOrSeries) ? rowOrSeries[rowOrSeries.length - 1] : rowOrSeries;
  if (!row) return;
  STATE.row = row;
  const c = controls || STATE.controls || readControls();
  const shutIn = row.phase !== "produce";
  setSlot("tmDay", "D+" + fmt(row.day, 1));
  setSlot("tmT", fmt(row.T_res_C, 1) + " °C");
  setSlot("tmMu", nf(row.mu_cP, 0) + " cP");
  setSlot("tmQ", shutIn ? "—" : fmt(row.oil_m3d, 1) + " m³/d");
  setSlot("tmRod", nf(shutIn ? ROD_HANG_KN : row.rod_load_kN, 0) + " kN");
  setSlot("tmPump", shutIn ? T("shutIn") : fmt(c.spm, 1) + " spm");
  /* rev 12: water cut and rod-float index readouts -- water_cut is only on
     baked (state-model) series (data.js); an off-baked approximate run has
     no such column, so these read "—" there rather than a fabricated number. */
  setSlot("tmWaterCut", (shutIn || !Number.isFinite(row.water_cut)) ? "—" : pct(row.water_cut));
  setSlot("tmFI", shutIn ? "—" : fmt(row.floating_index || 0, 2));
  const st = $("tmStatus");
  const fi = row.floating_index || 0;
  /* Same 3-level scale as the risk meter (<=0.40 OK, <=0.60 WATCH, >0.60
     ALARM) — a different threshold here is exactly what let the telemetry
     chip say "OK" while the risk meter said "ELEVATED" for the same run. */
  const alm = fi > RISK_LIMIT;
  const watch = !alm && fi > 0.4;
  st.textContent = alm ? T("chipAlarm") : (shutIn ? T("shutIn") : (watch ? T("chipWatch") : T("chipOk")));
  st.setAttribute("lang", langAttr());
  st.className = "tm-status" + (alm ? " alm" : ((shutIn || watch) ? " warn" : ""));
}

/* ---------- alarm --------------------------------------------------------- */
/* rev 12: at the day the produce-end rule actually fires (the last row of a
   baked run whose produce_end_reason is "float_onset"), the banner switches
   from the generic risk warning to the operating-rule message -- "the rods
   are floating and the operator is pulling the well", not a runaway alarm. */
function renderAlert(summary, atRuleEnd, duringHold){
  const banner = $("alertBanner");
  const fi = summary.max_floating_index || 0;
  const active = fi > RISK_LIMIT;
  if (!active) STATE.alarmAcked = false;
  const textEl = $("alertText");
  if (textEl) textEl.textContent = atRuleEnd ? T("floatBanner") : (duringHold ? T("vfdHoldBanner") : T("alarmDefaultText"));
  if (textEl) textEl.setAttribute("lang", langAttr());
  if (active){
    $("alertDetail").textContent = "FI " + fmt(fi, 2) + " > " + fmt(RISK_LIMIT, 2) +
      " · " + fmt(Number($("in_spm").value), 1) + " spm · " + istClock();
    $("alertTag").textContent = STATE.alarmAcked ? "ALM-02 · ACK" : "ALM-02";
    banner.hidden = false;
    banner.style.animation = STATE.alarmAcked ? "none" : "";
  } else {
    banner.hidden = true;
    banner.style.animation = "";
  }
  ["panelDyno", "panelRisk"].forEach(function(id){ $(id).classList.toggle("panel-alarm", active); });
}
/* True once the replay/scrub cursor reaches the last row of a baked cycle
   that actually ended on the float-alarm rule (produce_end_reason ===
   "float_onset") -- an off-baked approximation has no such field, so it
   never claims the rule fired. */
function isAtFloatOnsetEnd(row){
  if (!STATE.sim || !STATE.sim.summary || !STATE.sim.baked) return false;
  if (STATE.sim.summary.produce_end_reason !== "float_onset") return false;
  const series = STATE.sim.series;
  if (!series || !series.length) return false;
  return row && row.day >= series[series.length - 1].day - 1e-6;
}
/* rev 13 (wave 5): true while the VFD is actively holding the float index
   at its alarm line (down at the 2-spm floor, FI near 0.6) but BEFORE the
   final pull day -- drives the "VFD slows the pump" banner text. Only true
   for a baked run under a VFD policy; an off-baked approximation has no
   schedule_floor_spm field, so it never claims the hold state. */
function isDuringVfdHold(row, summary){
  if (!row || !summary) return false;
  if (summary.float_policy !== "vfd_hold" && summary.float_policy !== "vfd_then_pull") return false;
  const floor = summary.schedule_floor_spm;
  if (!Number.isFinite(floor)) return false;
  return (row.spm || 0) <= floor + 0.05 && (row.floating_index || 0) >= 0.55;
}
$("btnAck").addEventListener("click", function(){
  STATE.alarmAcked = true;
  $("alertTag").textContent = "ALM-02 · ACK";
  $("alertBanner").style.animation = "none";
});

/* ---------- cross-section ------------------------------------------------- */
const XS = { minT: 50, maxT: 290 };
function setChipText(el, key){
  el.dataset.en = STR.en[key] || key;
  el.dataset.hi = STR.hi[key] || STR.en[key] || key;
  el.textContent = T(key);
  el.setAttribute("lang", langAttr());
}
function setXsecState(row, isReplay){
  const svg = $("xsec");
  if (!svg || !row) return;
  const phase = row.phase || "produce";
  STATE.phase = phase;
  if (!svg.classList.contains("phase-" + phase)){
    svg.classList.remove("phase-inject", "phase-soak", "phase-produce");
    svg.classList.add("phase-" + phase);
  }
  const t = Math.max(0, Math.min(1, (row.T_res_C - XS.minT) / (XS.maxT - XS.minT)));
  const s = 0.15 + 0.95 * t;
  $("xsHalo").setAttribute("transform", "translate(170 524) scale(" + s.toFixed(3) + ") translate(-170 -524)");
  $("xsDay").textContent = "D+" + fmt(row.day, 1);
  setChipText($("xsPhase"), phase);
  $("xsPhase").className = "phase-chip chip-" + phase;
  $("xsTemp").textContent = "T " + fmt(row.T_res_C, 0) + " °C · μ " + nf(row.mu_cP, 0) + " cP";
  const meta = $("xsecMeta");
  meta.textContent = isReplay ? T("replayAt") + " D+" + fmt(row.day, 1) : T("cycleEndState");
  meta.setAttribute("lang", langAttr());
}

/* ---------- replay -------------------------------------------------------- */
const replay = { data: null, controls: null, playing: false, t: 0, raf: 0, lastTs: 0,
                 rowIdx: -1, day0: 0, day1: 1, durS: 14, oilCum: [], energyCum: [] };
const ICON_PLAY = '<path d="M16 10 L38 24 L16 38 Z"/>';
const ICON_PAUSE = '<line x1="18" y1="12" x2="18" y2="36"/><line x1="30" y1="12" x2="30" y2="36"/>';

function rowIndexForDay(t){
  const s = replay.data.series;
  let lo = 0, hi = s.length - 1;
  while (lo < hi){ const mid = (lo + hi + 1) >> 1; if (s[mid].day <= t) lo = mid; else hi = mid - 1; }
  return lo;
}
function positionCursor(day){
  const gd = $("chartTimeseries"), cur = $("dayCursor");
  const fl = gd && gd._fullLayout;
  if (!fl || !fl.xaxis || !fl.yaxis || !replay.data){ cur.classList.remove("visible"); return; }
  const xa = fl.xaxis, ya = fl.yaxis, y3 = fl.yaxis3 || ya;
  const span = (xa.range[1] - xa.range[0]) || 1;
  const frac = Math.max(0, Math.min(1, (day - xa.range[0]) / span));
  const top = ya._offset;
  const bottom = (y3._offset || ya._offset) + (y3._length || ya._length);
  cur.style.top = top.toFixed(1) + "px";
  cur.style.height = Math.max(0, bottom - top).toFixed(1) + "px";
  cur.style.transform = "translateX(" + (xa._offset + frac * xa._length).toFixed(1) + "px)";
  cur.classList.add("visible");
}
function applyReplayRow(idx){
  const s = replay.data.series, row = s[idx];
  setXsecState(row, true);
  $("replayDay").textContent = "D+" + fmt(row.day, 1);
  STATE.replayPhaseKey = row.phase;
  setChipText($("replayPhase"), row.phase);
  $("replayPhase").className = "phase-chip chip-" + row.phase;
  const oil = replay.oilCum[idx];
  $("replayTelem").innerHTML =
    "SOR <b>" + (oil > 1e-6 ? fmt(row.steam_t_cum / oil, 2) : "—") + "</b> t/m³ · " +
    "oil <b>" + nf(oil, 0) + "</b> m³ · FI <b>" + fmt(row.floating_index || 0, 2) + "</b>";
  renderRisk(row.floating_index || 0, STATE.riskFailures, STATE.riskProb);
  renderDynoPanel(row, replay.controls || readControls());
  renderAlert({ max_floating_index: row.floating_index || 0 }, isAtFloatOnsetEnd(row),
    isDuringVfdHold(row, STATE.sim && STATE.sim.summary));
  updateTelemetry(row, replay.controls || readControls());
}
function replayAttach(data, controls){
  pauseReplay();
  replay.data = data; replay.controls = controls;
  const s = data.series;
  replay.day0 = s[0].day; replay.day1 = s[s.length - 1].day;
  let oc = 0, ec = 0;
  replay.oilCum = s.map(function(r){ return (oc += r.oil_m3d); });
  replay.energyCum = s.map(function(r){ return (ec += r.energy_kWh); });
  replay.t = replay.day1; replay.rowIdx = s.length - 1;
  $("replayDay").textContent = "D+" + fmt(replay.day1, 1);
  STATE.replayPhaseKey = "cycleComplete";
  setChipText($("replayPhase"), "cycleComplete");
  $("replayPhase").className = "phase-chip";
  $("replayTelem").innerHTML = '<span lang="' + langAttr() + '">' + fmt(data.summary.days_total, 1) + "-d " + T("cycleLoaded") + "</span>";
  $("replayDurLabel").textContent = "(" + replay.durS + " s)";
  setXsecState(s[s.length - 1], false);
  requestAnimationFrame(function(){ positionCursor(replay.t); });
}
function replayTick(ts){
  if (!replay.playing) return;
  if (!replay.lastTs) replay.lastTs = ts;
  const dt = Math.max(0, (ts - replay.lastTs) / 1000);
  replay.lastTs = ts;
  replay.t = Math.min(replay.day1, replay.t + dt * ((replay.day1 - replay.day0) / replay.durS));
  const idx = rowIndexForDay(replay.t);
  if (idx !== replay.rowIdx){ replay.rowIdx = idx; applyReplayRow(idx); }
  positionCursor(replay.t);
  if (replay.t >= replay.day1){ finishReplay(); return; }
  replay.raf = requestAnimationFrame(replayTick);
}
function pauseReplay(){
  replay.playing = false;
  if (replay.raf) cancelAnimationFrame(replay.raf);
  replay.raf = 0; replay.lastTs = 0;
  document.body.classList.remove("is-replaying");
  $("replayIcon").innerHTML = ICON_PLAY;
  $("btnReplay").classList.remove("playing");
}
function finishReplay(){
  pauseReplay();
  const d = replay.data;
  if (!d) return;
  renderDynoPanel(d.series[d.series.length - 1], replay.controls || readControls());
  renderRisk(d.summary.max_floating_index, d.summary.failures_expected, STATE.riskProb);
  renderAlert(d.summary, isAtFloatOnsetEnd(d.series[d.series.length - 1]), false);
  updateTelemetry(d.series, replay.controls || readControls());
  setXsecState(d.series[d.series.length - 1], false);
  STATE.replayPhaseKey = "cycleComplete";
  setChipText($("replayPhase"), "cycleComplete");
  $("replayPhase").className = "phase-chip";
  $("replayTelem").innerHTML = '<span lang="' + langAttr() + '">' + fmt(d.summary.days_total, 1) + "-d " + T("cycleLoaded") + "</span>";
}
function toggleReplay(){
  if (!replay.data) return;
  if (replay.playing){ pauseReplay(); return; }
  if (replay.t >= replay.day1 - 1e-9){ replay.t = replay.day0; replay.rowIdx = -1; }
  replay.playing = true; replay.lastTs = 0;
  document.body.classList.add("is-replaying");
  $("replayIcon").innerHTML = ICON_PAUSE;
  $("btnReplay").classList.add("playing");
  replay.raf = requestAnimationFrame(replayTick);
}
$("btnReplay").addEventListener("click", toggleReplay);
$("btnReplay2").addEventListener("click", function(){
  $("panelTimeseries").scrollIntoView({ block: "nearest" });
  toggleReplay();
});

(function wireCursorDrag(){
  const grip = $("cursorGrip");
  function dayFromClientX(clientX){
    const gd = $("chartTimeseries"), fl = gd._fullLayout;
    if (!fl || !fl.xaxis) return replay.t;
    const xa = fl.xaxis, rect = gd.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (clientX - rect.left - xa._offset) / xa._length));
    return xa.range[0] + frac * (xa.range[1] - xa.range[0]);
  }
  function scrubTo(clientX){
    if (!replay.data) return;
    replay.t = Math.max(replay.day0, Math.min(replay.day1, dayFromClientX(clientX)));
    const idx = rowIndexForDay(replay.t);
    if (idx !== replay.rowIdx){ replay.rowIdx = idx; applyReplayRow(idx); }
    positionCursor(replay.t);
  }
  grip.addEventListener("pointerdown", function(e){
    if (!replay.data) return;
    pauseReplay();
    document.body.classList.add("is-replaying");
    grip.setPointerCapture(e.pointerId);
    e.preventDefault();
    const move = function(ev){ scrubTo(ev.clientX); };
    const up = function(ev){
      grip.removeEventListener("pointermove", move);
      grip.removeEventListener("pointerup", up);
      document.body.classList.remove("is-replaying");
      try { grip.releasePointerCapture(ev.pointerId); } catch (_e) {}
    };
    grip.addEventListener("pointermove", move);
    grip.addEventListener("pointerup", up);
  });
})();

/* ---------- staged hand-off from the optimiser ---------------------------- */
function renderStagedBar(){
  const staged = BUS.get("staged", null);
  const bar = $("stagedBar");
  if (!staged){ bar.hidden = true; return; }
  bar.hidden = false;
  /* Staged set-points can come from the optimiser's recommendation OR from
     the Model basis page's "Calibrate from field data" section (staged.
     provenance === "calibrated") -- say which, so the source of a set-point
     is never ambiguous on the console. */
  const fromCalib = staged.provenance === "calibrated";
  $("stagedText").innerHTML =
    "<b>Set-points staged " + (fromCalib ? "from a field-data calibration" : "by the optimiser") + ".</b> " +
    settingsLabel(staged) +
    " · " + (staged.recId || "") + " · staged " + istStamp(new Date(staged.at)) +
    " — load them into the console and simulate to confirm the twin agrees.";
}
$("btnLoadStaged").addEventListener("click", async function(){
  const staged = BUS.get("staged", null);
  if (!staged) return;
  STATE.preApplySummary = STATE.sim ? STATE.sim.summary : null;
  STATE.preApplyControls = STATE.controls ? Object.assign({}, STATE.controls) : null;
  writeControls(staged);
  pendingApplied = true;
  await runSimulate();
  BUS.set("staged", null);
  renderStagedBar();
  renderStatusBar("__PAGE_KEY__");
});
$("btnDiscardStaged").addEventListener("click", function(){
  BUS.set("staged", null);
  renderStagedBar();
  renderStatusBar("__PAGE_KEY__");
});

/* ---------- run ----------------------------------------------------------- */
let pendingApplied = false;

async function runSimulate(floatPolicyOverride){
  const v = readControls();
  /* The stress test always demonstrates the RAW risk at 12 SPM regardless of
     the "Rod-float response" selector -- that is the one thing the button
     has always promised ("drive the rod-floating alarm"), and now that the
     selector actually changes the physics (re-score item 6), leaving it on
     the operator's last pick could silently hide the alarm behind a VFD
     policy that holds the line. The dropdown itself is left untouched. */
  const floatPolicy = floatPolicyOverride || STATE.floatPolicy;
  $("btnSimulate").classList.add("is-busy");
  try {
    let data;
    if (MOCK){ await wait(320 + Math.random() * 180); data = mockSimulate(v.steam_t, v.soak_days, v.cutoff, v.spm, v.stroke_in, v.p_wellhead_kgf_cm2, floatPolicy); }
    else { data = await apiSimulate(v.steam_t, v.soak_days, v.cutoff, v.spm, v.stroke_in, v.p_wellhead_kgf_cm2, floatPolicy); }

    STATE.sim = data;
    STATE.controls = v;
    STATE.runSeq += 1;
    STATE.computedAt = new Date();
    STATE.ready = true;
    STATE.riskFailures = data.summary.failures_expected;
    if (pendingApplied){ STATE.applied = true; pendingApplied = false; }
    else if (STATE.applied){ /* keep flag until a slider is touched */ }

    renderTimeSeries(data.series);
    renderDynoPanel(data.series.length ? data.series[data.series.length - 1] : null, v);
    renderRisk(data.summary.max_floating_index, data.summary.failures_expected, STATE.riskProb);
    renderAlert(data.summary, isAtFloatOnsetEnd(data.series.length ? data.series[data.series.length - 1] : null), false);
    updateTelemetry(data.series, v);
    $("tsMeta").textContent = fmt(data.summary.days_total, 1) + " d · " + nf(data.series.length) + " rows · " +
      (data.baked ? "baked twin output" : "in-browser approximation");

    /* An off-reference set-point (e.g. the 12-SPM stress test) runs the
       in-browser approximation, not the baked twin. Its SOR can read lower
       than the real optimum without being achievable — never publish it as
       "the run on the books", and strike the SOR through with a plain
       warning when the rods would float.
       rev 13.1: "not achievable" is now policy-aware. Holding the floating
       index AT the 0.60 line by design (VFD-hold/vfd_then_pull) is not a
       violation — the recommendation and the baseline both end this way on
       purpose (dashboard/README.md §8). The strike-through now only fires
       when the alarm rule itself would have been breached: FI reaching 1.0
       (full carrier-bar separation) or more than the rule's 3 consecutive
       alarm days before a pull, exactly like the optimiser's constraint
       report below. An off-baked/legacy summary with no policy fields at
       all falls back to the old simple > 0.60 reading. */
    const heldPolicy = data.summary.float_policy === "vfd_hold" || data.summary.float_policy === "vfd_then_pull";
    const alarmDaysRule = data.summary.fi_alarm_days_rule;
    const overLimit = data.summary.max_floating_index >= 1.0 ||
      (heldPolicy && Number.isFinite(alarmDaysRule)
        ? (data.summary.failures_expected || 0) > alarmDaysRule
        : data.summary.max_floating_index > RISK_LIMIT);
    const isApprox = MOCK && !data.baked;
    const sorPart = overLimit
      ? "<s>SOR " + fmt(data.summary.SOR_t_per_m3, 2) + " t/m³</s> — <span class=\"neg\" lang=\"" + langAttr() + "\">" + T("sorNotAchievable") + "</span>"
      : "SOR <b>" + fmt(data.summary.SOR_t_per_m3, 2) + "</b> t/m³";
    $("toolbarMeta").innerHTML = sorPart + " · oil <b>" +
      nf(data.summary.oil_total_m3, 0) + "</b> m³ · <b>" + fmt(data.summary.days_total, 1) + "</b> d" +
      (STATE.applied ? ' · <span class="tag pass">' + T("settingsApplied") + " " + istClock(STATE.computedAt) + "</span>" : "") +
      (isApprox ? ' · <span class="tag warn" lang="' + langAttr() + '">' + T("approxChip") + "</span>" : "");
    $("toolbar").classList.toggle("is-optimised", STATE.applied);
    if (data.series.length) replayAttach(data, v);

    /* Publish to the other pages — but only a baked twin result or a live-API
       result. An approximate console run stays on the console; it must never
       become the Overview's or Optimiser's "current cycle". */
    if (!isApprox){
      saveRun({
        runId: "SIM-" + istDateCode(STATE.computedAt) + "-" + String(STATE.runSeq).padStart(2, "0"),
        computedAt: STATE.computedAt.toISOString(),
        controls: v,
        summary: data.summary,
        applied: STATE.applied,
        preApplySummary: STATE.preApplySummary,
        preApplyControls: STATE.preApplyControls,
        source: MOCK ? "baked" : "api"
      });
    }
    renderStatusBar("__PAGE_KEY__");
  } catch (err){
    console.error(err);
    const chip = document.querySelector("#statusBar .src-chip");
    if (chip){ chip.classList.add("error"); chip.lastChild.textContent = "Data source error · " + err.message; }
  } finally {
    $("btnSimulate").classList.remove("is-busy");
  }
}

$("btnSimulate").addEventListener("click", runSimulate);
$("btnStress").addEventListener("click", async function(){
  $("in_spm").value = SPM_SLIDER.max;
  $("in_spm").dispatchEvent(new Event("input", { bubbles: true }));
  await runSimulate("none");
});
$("btnReset").addEventListener("click", async function(){
  STATE.applied = false;
  STATE.preApplySummary = null;
  STATE.preApplyControls = null;
  writeControls(REF_INPUTS);
  await runSimulate();
});

/* Touching a slider by hand invalidates the "applied" state. */
["in_steam_t", "in_soak_days", "in_cutoff", "in_spm", "in_stroke", "in_pressure"].forEach(function(id){
  $(id).addEventListener("input", function(){
    if (STATE.applied){
      STATE.applied = false;
      $("toolbar").classList.remove("is-optimised");
    }
  });
});

/* ---------- redraw hooks -------------------------------------------------- */
function redrawAll(){
  if (!STATE.sim) return;
  renderTimeSeries(STATE.sim.series);
  if (replay.rowIdx >= 0 && replay.rowIdx < STATE.sim.series.length - 1) applyReplayRow(replay.rowIdx);
  else renderDynoPanel(STATE.sim.series.length ? STATE.sim.series[STATE.sim.series.length - 1] : null, STATE.controls);
  renderRiskState();
  const alertTextEl = $("alertText");
  if (alertTextEl){
    const atEnd = isAtFloatOnsetEnd(STATE.row);
    const duringHold = !atEnd && isDuringVfdHold(STATE.row, STATE.sim && STATE.sim.summary);
    alertTextEl.textContent = atEnd ? T("floatBanner") : (duringHold ? T("vfdHoldBanner") : T("alarmDefaultText"));
    alertTextEl.setAttribute("lang", langAttr());
  }
  if (STATE.row) updateTelemetry(STATE.row, STATE.controls);
  if (STATE.phase) setChipText($("xsPhase"), STATE.phase);
  if (STATE.replayPhaseKey) setChipText($("replayPhase"), STATE.replayPhaseKey);
  requestAnimationFrame(function(){ positionCursor(replay.t); });
}
onLangChange(function(){ renderStagedBar(); redrawAll(); renderFloatPolicyDesc(); });
renderFloatPolicyDesc();
onThemeChange(redrawAll);
window.addEventListener("resize", function(){
  if (replay.data) positionCursor(replay.t);
});

/* ---------- measured-card check (Simulator page), 27 Sep 2026 -------------
   Collapsed "Check a measured card" panel under the computed-card panel:
   upload a CSV or paste a two-column table from a MEASURED surface card and
   get a fault read from ml.dyno_classifier's RandomForest (classifier
   trained on physics-generated cards, never a real one -- see its module
   docstring and the caveat line rendered with every result).
   Live (MOCK=false): POSTs {position, load, units} to /api/dyno/classify.
   MOCK: a tiny in-browser NEAREST-NEIGHBOUR fallback against the 8 baked
   cards' own (bbox-normalised, arc-length-resampled) shape -- "approximate,
   offline", not the trained model; peak/min PRL are read off the pasted
   data directly, fillage is the matched baked card's own pump_fillage. */
const CLF_KN_PER_KLBF = 4.4482216152605;
function clfParseTable(text){
  const lines = String(text).replace(/\r/g, "").split("\n").map(function(l){ return l.trim(); }).filter(Boolean);
  if (!lines.length) throw new Error("empty input");
  const split = function(l){ return l.indexOf(",") >= 0 ? l.split(",") : (l.indexOf("\t") >= 0 ? l.split("\t") : l.split(/\s+/)); };
  const isNum = function(t){ return t !== undefined && t !== "" && !isNaN(Number(t)); };
  const first = split(lines[0]);
  const hasHeader = first.length >= 2 && !first.every(isNum);
  let posIdx = 0, loadIdx = 1, posUnit = null, loadUnit = null, rows = lines;
  if (hasHeader){
    first.map(function(s){ return s.trim().toLowerCase(); }).forEach(function(c, i){
      if (/pos/.test(c)){ posIdx = i; posUnit = /in/.test(c) ? "in" : "m"; }
      if (/klbf/.test(c)){ loadIdx = i; loadUnit = "klbf"; }
      else if (/load|prl/.test(c)){ loadIdx = i; loadUnit = loadUnit || "kn"; }
    });
    rows = lines.slice(1);
  }
  const position = [], load = [];
  rows.forEach(function(l){
    const c = split(l);
    if (c.length > Math.max(posIdx, loadIdx) && isNum(c[posIdx]) && isNum(c[loadIdx])){
      position.push(Number(c[posIdx])); load.push(Number(c[loadIdx]));
    }
  });
  if (position.length < 6) throw new Error("need at least 6 numeric rows (position, load)");
  const ptp = function(a){ return Math.max.apply(null, a) - Math.min.apply(null, a); };
  if (!posUnit) posUnit = ptp(position) > 12 ? "in" : "m";
  if (!loadUnit) loadUnit = Math.max.apply(null, load.map(Math.abs)) < 40 ? "klbf" : "kn";
  const posM = position.map(function(p){ return posUnit === "in" ? p * 0.0254 : p; });
  const loadKN = load.map(function(v){ return loadUnit === "klbf" ? v * CLF_KN_PER_KLBF : v; });
  return { position: posM, load: loadKN, posUnit: posUnit, loadUnit: loadUnit === "klbf" ? "klbf" : "kn" };
}
function clfResampleContour(x, f, n){
  const xa = x.slice(), fa = f.slice();
  if (Math.hypot(xa[xa.length - 1] - xa[0], fa[fa.length - 1] - fa[0]) > 1e-9){ xa.push(xa[0]); fa.push(fa[0]); }
  const xmin = Math.min.apply(null, xa), xmax = Math.max.apply(null, xa);
  const fmin = Math.min.apply(null, fa), fmax = Math.max.apply(null, fa);
  const xr = Math.max(xmax - xmin, 1e-9), fr = Math.max(fmax - fmin, 1e-9);
  const xn = xa.map(function(v){ return (v - xmin) / xr; });
  const fn = fa.map(function(v){ return (v - fmin) / fr; });
  const s = [0];
  for (let i = 1; i < xn.length; i++) s.push(s[i - 1] + Math.hypot(xn[i] - xn[i - 1], fn[i] - fn[i - 1]));
  const total = s[s.length - 1] || 1;
  const out = [];
  for (let k = 0; k < n; k++){
    const t = (k / n) * total;
    let j = 0; while (j < s.length - 2 && s[j + 1] < t) j++;
    const seg = (s[j + 1] - s[j]) || 1e-9, w = (t - s[j]) / seg;
    out.push(xn[j] + w * (xn[j + 1] - xn[j]), fn[j] + w * (fn[j + 1] - fn[j]));
  }
  return out;
}
/* Verified (rev 13.1, re-score item 8): this already compares the uploaded
   curve against ALL 8 baked cards, both scenarios included, on the same
   normalised (bounding-box, arc-length-resampled) feature vector -- so
   ?qc=cardcsv's self-test (the baseline's own "mid" card fed back in)
   correctly returns itself at distance 0 ("fluid_pound", fillage 30%, which
   IS that card's own transient fillage at day 126.6 -- a different, smaller
   quantity than the whole-cycle mean_fillage (85%) shown elsewhere; the two
   were never the same number). What was missing was a floor: nothing
   stopped a genuinely novel (real, non-baked-shaped) curve from being
   forced onto whichever baked card happened to be least-bad. bestD is now
   returned alongside the match so the caller can refuse to label a curve
   that does not actually resemble any baked card. */
const CLF_MAX_MATCH_DIST = 6.5; /* calibrated off the 8x8 baked-card distance matrix -- see TIER1_PROGRESS_LOG.md re-score item 8 */
function clfNearestBaked(parsed){
  const N = 48, vec = clfResampleContour(parsed.position, parsed.load, N);
  let best = null, bestD = Infinity;
  Object.keys(DYNO_CARDS.scenarios).forEach(function(s){
    DYNO_CARDS.scenarios[s].cards.forEach(function(c){
      const cv = clfResampleContour(c.surface.position_m, c.surface.load_kN, N);
      let d = 0; for (let i = 0; i < cv.length; i++){ const e = cv[i] - vec[i]; d += e * e; }
      if (d < bestD){ bestD = d; best = c; }
    });
  });
  return { card: best, dist: bestD };
}

let _dynoClfFileText = "", _dynoClfLastResult = null;
function clfSetStatus(cls, html){ const el = $("dynoClfStatus"); el.className = "note " + cls; el.innerHTML = html; }
function clfRenderResult(o){
  $("dynoClfResult").hidden = false;
  const meta = CARD_TYPE_META[o.card_type] || CARD_TYPE_META.fluid_pound;
  const badge = $("dynoClfBadge");
  badge.textContent = T(meta.label); badge.className = "tag " + meta.cls; badge.setAttribute("lang", langAttr());
  $("dynoClfApproxTag").hidden = !o.approx;
  const sentEl = $("dynoClfSentence");
  sentEl.textContent = LANG === "hi" ? o.sentence_hi : o.sentence_en;
  sentEl.className = "rm-sentence" + (o.card_type === "rod_float" ? " neg" : "");
  sentEl.setAttribute("lang", langAttr());
  $("dynoClfFillage").textContent = fmt(100 * o.fillage_est, 0);
  $("dynoClfPeak").textContent = fmt(o.peak_kN, 1);
  $("dynoClfMin").textContent = fmt(o.min_kN, 1);
  const probs = o.probabilities || {};
  const keys = Object.keys(probs);
  $("dynoClfProbs").innerHTML = keys.map(function(k){
    const p = Math.round(100 * probs[k]);
    const lbl = (CARD_TYPE_META[k] || {}).label;
    return '<div class="dyno-clf-prob-row"><span class="lbl">' + (lbl ? T(lbl) : k) +
      '</span><span class="track"><span class="fill" style="width:' + p + '%"></span></span>' +
      '<span class="pct num">' + p + '%</span></div>';
  }).join("");
}
async function runDynoClassify(){
  const raw = ($("dynoClfPaste").value || "").trim() || _dynoClfFileText;
  if (!raw){ clfSetStatus("warn", T("dynoClfNeedInput")); return; }
  const btn = $("btnDynoClassify");
  btn.disabled = true; btn.classList.add("is-busy");
  try {
    let parsed;
    try { parsed = clfParseTable(raw); }
    catch (e){ clfSetStatus("warn", "<b>" + T("dynoClfBadTable") + "</b> " + e.message); return; }
    if (!MOCK){
      const res = await fetch(API_BASE + "/api/dyno/classify", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ position: parsed.position, load: parsed.load, units: parsed.posUnit + "," + parsed.loadUnit }),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || ("HTTP " + res.status));
      _dynoClfLastResult = Object.assign({ approx: false }, data);
      clfSetStatus("good", T("dynoClfLiveOk"));
    } else {
      const nn = clfNearestBaked(parsed);
      if (nn.dist > CLF_MAX_MATCH_DIST){
        $("dynoClfResult").hidden = true;
        clfSetStatus("warn", "<b>" + T("dynoClfNoMatch") + "</b>");
        return;
      }
      const best = nn.card;
      const meta = CARD_TYPE_META[best.card_type] || CARD_TYPE_META.fluid_pound;
      _dynoClfLastResult = {
        card_type: best.card_type, fillage_est: best.pump_fillage,
        peak_kN: Math.max.apply(null, parsed.load), min_kN: Math.min.apply(null, parsed.load),
        probabilities: {}, sentence_en: STR.en[meta.mean], sentence_hi: STR.hi[meta.mean], approx: true,
      };
      clfSetStatus("info", T("dynoClfMockOk"));
    }
    clfRenderResult(_dynoClfLastResult);
  } catch (err){
    clfSetStatus("warn", "<b>" + T("dynoClfFailed") + "</b> " + err.message + (MOCK ? "" : " " + T("dynoClfIsApiUp")));
  } finally {
    btn.disabled = false; btn.classList.remove("is-busy");
  }
}
$("dynoClfFile").addEventListener("change", function(e){
  const f = e.target.files && e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = function(){ _dynoClfFileText = String(reader.result); $("dynoClfPaste").value = ""; runDynoClassify(); };
  reader.onerror = function(){ clfSetStatus("warn", T("dynoClfFileError")); };
  reader.readAsText(f);
});
$("btnDynoClassify").addEventListener("click", function(){ runDynoClassify(); });
function _dynoClfSyncPlaceholder(){
  const ta = $("dynoClfPaste");
  ta.placeholder = LANG === "hi" ? ta.dataset.hiPlaceholder : ta.dataset.enPlaceholder;
}
onLangChange(function(){ _dynoClfSyncPlaceholder(); if (_dynoClfLastResult) clfRenderResult(_dynoClfLastResult); });
_dynoClfSyncPlaceholder();

/* ---------- boot ---------------------------------------------------------- */
(function boot(){
  const run = currentRun();
  writeControls(run.controls);
  STATE.applied = !!run.applied;
  STATE.preApplySummary = run.preApplySummary || null;
  STATE.preApplyControls = run.preApplyControls || null;
  renderStagedBar();
  renderRisk(0, 0, STATE.riskProb);
  runSimulate();
})();

/* Demo / QC hooks:
     ?autoreplay      start the replay once the first simulation lands
     ?lang=hi         Hindi-primary        ?theme=dark   control-room theme
     ?qc=alarm        stress test, so the alarm state renders
     ?qc=replay       mid-replay frame
     ?qc=cardcsv      inject a baked card's surface CSV into "Check a
                      measured card" and classify it, no file-picker dialog */
(function qcHook(){
  const q = new URLSearchParams(location.search);
  if (q.has("autoreplay") || q.get("qc") === "replay"){
    setTimeout(function(){ if (replay.data && !replay.playing) toggleReplay(); }, 1200);
  }
  if (q.get("qc") === "alarm"){
    setTimeout(function(){ $("btnStress").click(); }, 900);
  }
  if (q.get("qc") === "loadstaged"){
    setTimeout(function(){ if (!$("stagedBar").hidden) $("btnLoadStaged").click(); }, 900);
  }
  if (q.get("qc") === "cardcsv"){
    const c = DYNO_CARDS.scenarios.baseline.cards.filter(function(x){ return x.key === "mid"; })[0];
    const lines = ["position_m,load_kN"];
    c.surface.position_m.forEach(function(p, i){ lines.push(p.toFixed(3) + "," + c.surface.load_kN[i].toFixed(2)); });
    $("dynoClfDetails").open = true;
    $("dynoClfPaste").value = lines.join("\n");
    runDynoClassify();
  }
})();
