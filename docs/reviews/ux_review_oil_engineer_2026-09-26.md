# UX review — "the Baghewala production engineer" · 26 Sep 2026

**Persona:** a 52-year-old OIL production engineer, 25 years at Baghewala. He runs CSS jobs and pumpjacks and is at home with SCADA and Excel, but not with ML. He reads English and speaks Hindi natively. He views on a laptop, a projector or a tablet, and in 8 s he wants to know: which well, what to set, what it saves, what could break.
**Method:** the Chrome extension was not connected (2 tries), so the fallback was headless Edge screenshots (README §9 method) at 1600 px and 1024 px, EN and हिं, fresh and shared profiles, plus the `?qc=alarm | staged | loadstaged` flow and Edge console logging, plus a read of `dashboard/src/*`. No JS errors came from page code. The only console noise was Edge "Tracking Prevention" notices for the Plotly CDN. Screenshots are described in words, not embedded.

---

## 0. Two defects to fix before anyone from OIL sees this

1. **The stress test poisons the Overview and Optimiser.** After *Stress test (12 spm)*, the console saves that run as the run "on the books" (`page-console.js` L559 `saveRun`). The Overview then shows **"− −47.9%"** in green (a double minus), **"₹-0.30–-0.43 crore"** and **"-116 tCO₂"**. The Optimiser shows its own recommendation as **+47.9% worse** (red) than "current". Cause: `page-overview.js` L38 hard-codes the `"−"` prefix, and `page-overview.html` L37 hard-codes the class `good`. Any presenter who demos the alarm and then clicks *Overview* shows negative savings to OIL.
2. **The in-browser approximation disagrees with the baked twin.** At 12 spm it reports SOR **0.61** with 2,415 m³ of oil, which is *better* than the recommended 0.91, and energy intensity **229.9 kWh/m³** against 20.6 for the baked run. An engineer will ask at once: "then why not run 12 SPM?" The only answer on screen is the alarm banner. The SOR is shown as if it were achievable.

---

## 1. Overview (`index.html`)

**(a) The 8-second test.** He can see "BGW-07", "1.29 → 0.91", "−30%" and "₹0.40–0.57 crore". He **cannot see what to set.** The recommended set-points appear only as 11 px grey text (`1,600 t / 3 d / 8.0 m³/d / 10.0 spm`) under the SOR figure and in a table header. Four figures carry equal weight and no card says "do this". The 58,617 L of diesel, the number he actually thinks in, is 11 px sub-text.
**(b) Jargon on the first screen:** "ML optimum", "ML-optimised (as applied)", "as-applied optimum", "Optimiser midpoint baseline", "iso-oil counterfactual", "surrogate MAE", "Run provenance", "XGBoost surrogate · R² 0.72", "params/field_params.json rev 3", "21/24 physics tests", "twin.cycle.simulate_css_cycle", "SIM-20260926-01", "controller grid", "Max floating index".
**(c) Missing or buried:**
- There is no recommendation card and no "what to do next" sentence.
- Diesel litres are sub-text.
- The rod risk is a table row near the bottom ("Max floating index 0.54 → 0.25") with no plain statement such as "rod-float risk falls from elevated to low".
- *Print* exists but untranslated. The date sits only in the grey status bar.
**(d) Visual:**
- It looks like an instrument (navy chrome, ruled tables, 2 px radii), which is good. It is **dense and small**: body text is 13 px, meta and units 11 px, table sub-heads 10 px. That is unreadable on a projector at 4 m.
- The left column below the fold is three stacked tables plus two paragraphs of argument ("Why per cycle…", "Why diesel…") and the right column holds a 12-row provenance table. That reads like an audit trail, not an operator screen.
- Colour is mostly disciplined: green means better and red means worse. But the result strip's green is hard-coded (defect 0.1).
**(e) Broken:**
- Defect 0.1.
- In Hindi, the SOR chart's category label "एमएल-अनुकूलित (लागू)" is clipped at the left edge.

## 2. Twin console (`console.html`)

**(a) The 8-second test.** He can see sliders for steam, soak, cutoff and SPM, and he likes them because they are his own four knobs. The chart is readable. **The rod-floating risk, his "what could break", is at the bottom-right below the fold.** At 1024 px it is at the very bottom, after the full-height well cross-section.
**(b) Jargon:** "Twin console", "Telemetry" (it is simulated, not telemetry), `T_res`, `μ`, `q_o`, `sim D+61.3`, "baked twin output", "in-browser approximation", "Classifier p(float) — not run", "ISA-101 · ALM-02", "lumped API RP 11L approximation", "Stress test".
**(c) Missing:** a plain risk sentence ("Rods safe at 8 SPM — 0.54 of 0.60 limit"), a viscosity unit on the right axis (it shows 10/100/1k/10k with no "cP"), and a "Day 61 of 61" in words.
**(d) Visual:**
- The **dynamometer card is a smooth lens shape** (`buildDynoLoop`, L195). Anyone who reads real dynacards every week will see it is not one. Titled "Dynamometer card", it costs credibility.
- The default run shows telemetry **"OK"** (green) while the risk meter says **"ELEVATED"** (amber, 0.54). The two signals conflict.
- The set-point "readout" boxes look like input fields but cannot be typed into.
**(e) Behaviour:**
- Alarm and ACK work: the banner is fixed at the foot, the ACK tag changes, and the dyno and risk panels turn red.
- Load-staged works: a green "ML SET-POINTS APPLIED" tag appears and the status bar shows APPLIED.
- The stress test leaks into the other pages (defect 0.1) and shows an unachievable SOR (defect 0.2).

## 3. Optimiser (`optimizer.html`)

**(a) The 8-second test.** On a first visit the page is **almost empty**: one note and an empty history table. The subtitle reads "Surrogate-assisted search … soft constraint: p(float) ≤ 0.30 · Bayesian search (skopt `gp_minimize`, 60 calls, seed 42) over an XGBoost surrogate". He stops reading there. After *Run*, the answer is buried in a 6-column table: Current / Recommended *continuous optimum* / As applied *controller grid* / Change. Two "recommended" columns (7.76 vs 8.0, 10.22 vs 10.0) make him ask which one to set.
**(b) Jargon:** the whole *Uncertainty and model quality* block (XGBoost regressor/classifier, Latin-hypercube, 80/20 seed 42, hold-out R²/MAE, skopt, residual), "SOR (surrogate prediction)", "p(float)", "penalty × 1,000", "Search bounds — css / srp blocks", "continuous optimum", "controller grid", "REC-20260926-01", "staged".
**(c) Missing:** a one-line verdict ("Set 1,600 t · 3 days · 8.0 m³/d · 10 SPM. Saves ~58,600 L diesel per cycle. Rod risk low.") and a clear next step after *Confirm*. The only way on is a small inline link in the footer text.
**(d) Visual:** the page is tables only, well ruled, but everything carries equal weight. The history table headers are not translated.
**(e) Behaviour:**
- The Stage → Confirm → staged flow works.
- **The confirm prompt says "Send these set-points to the BGW-07 controller?"**, and the idle target line says "→ BGW-07 controller". Nothing is sent anywhere. An OIL engineer will either be alarmed or conclude the team is overclaiming a SCADA link.
- The history keeps older runs tagged "STAGED" for ever.
- History shows "−41.3" while every other page says −30%. The label exists elsewhere but not here.

## 4. Model basis (`methodology.html`)

**(a) The 8-second test.** This page is for judges, and that is fine: it is honest, well cited, and has "What this cannot do". The persona will not read equations. He needs a 5-line "in plain words" box at the top.
**(b) Jargon:** acceptable here. This is where the folded material from the other pages should land.
**(c)–(e)** At 1024 px the contents list wraps to two lines, which is acceptable. Nothing is broken.

## 5. Cross-cutting

- **Hindi.** Several strings are transliterated or odd:
  - "एमएल अनुकूलतम" (ML), "ट्विन कंसोल", "सरोगेट अनुमान", "टेलीमेट्री", "मैनुअल संचालन".
  - "छड़" for rod reads as "iron bar"; the field says **रॉड**.
  - "तनाव परीक्षण" means "tension test".
  - "Print" and "crore" are not translated.
  - The history headers are English only.
- **Status bar.** `params/field_params.json rev 3 · 21/24 physics tests · SIM-… · SIMULATED · TWIN V1.0` sits on every page's first line: build-session detail in the most prominent strip.
- **Offline venue risk.** Plotly loads from cdnjs. In a conference room without internet every chart is blank.
- **1024 px.** Nothing breaks horizontally. The status bar wraps to two lines, and the console's risk panel drops to the very bottom.

---

## 6. SPEC for the implementation agent

Edit `dashboard/src/*` only, then run `node dashboard/build.js`. After each item, check at 1600 and 1024 px in both EN and हिं, and run the `?qc=alarm` → `index.html` sequence in the same profile.

### P0 — must (10)

| # | Page | Element (src · line) | Change | EN copy | HI copy |
|---|---|---|---|---|---|
| P0-1 | Console → all | `page-console.js` L559 `saveRun(...)`; `page-overview.js` L38, L44–56; `page-overview.html` L37 | (a) Only publish runs where `data.baked` or the API is live. Approx runs stay on the console, with a chip next to `toolbarMeta`. (b) The Overview formats the delta with `signed()` and toggles `good`/`bad`. If `AV.steamT <= 0`, the money and CO₂ cells show the "no saving" copy instead of negative numbers. | Chip: "Approximate run — not carried to Overview". No saving: "No saving against this run" | "अनुमानित रन — सारांश पर नहीं भेजा गया" / "इस रन की तुलना में कोई बचत नहीं" |
| P0-2 | Console | `page-console.js` L552–554 `toolbarMeta` | When `max_floating_index > RISK_LIMIT`, strike through the SOR and append a warning. | "SOR not achievable — rods would float at this SPM" | "यह SOR संभव नहीं — इस SPM पर रॉड फ्लोट करेगी" |
| P0-3 | Overview | new `<section id="recCard">` in `page-overview.html` between `.pagehead` (L20) and `.resultstrip` (L23); render in `page-overview.js` from `OPT_APPLIED`, `AV`, `OPT_SUMMARY` | One full-width card with a navy left rule and 20 px+ type. Line 1 is the action (4 set-points, each with a unit). Line 2 is the saving. Line 3 is the risk. Line 4 holds 2 buttons. | "Recommended for BGW-07, next CSS cycle: Steam **1,600 t** · Soak **3 days** · Cutoff **8.0 m³/d** · Pump **10 SPM**" / "Saves per cycle: **58,617 L diesel** (685 t steam) · ₹0.40–0.57 crore · 153 t CO₂" / "Rod-float risk: **low** — 0.25 against a 0.60 limit (now 0.54)" / buttons "Check in simulator" · "See full recommendation" | "BGW-07 के अगले CSS चक्र हेतु सुझाव: भाप **1,600 t** · सोक **3 दिन** · कटऑफ़ **8.0 m³/d** · पंप **10 SPM**" / "प्रति चक्र बचत: **58,617 L डीज़ल** (685 t भाप) · ₹0.40–0.57 करोड़ · 153 t CO₂" / "रॉड फ्लोटिंग जोखिम: **कम** — सीमा 0.60, अनुमान 0.25 (अभी 0.54)" / "सिम्युलेटर में जाँचें" · "पूरी सिफ़ारिश देखें" |
| P0-4 | Overview strip | `page-overview.html` L35–45 + `page-overview.js` L38–50 | Cell 2: rename. Cell 3: the headline becomes litres, with ₹ as the second line at `--t-kpi`. | "Steam saved per m³ oil" · "Diesel not burned, per cycle" → "58,617 L" / "₹0.40–0.57 crore" | "प्रति m³ तेल भाप बचत" · "प्रति चक्र बचा डीज़ल" → "58,617 L" / "₹0.40–0.57 करोड़" |
| P0-5 | Optimiser | `core.js` L177, L246 `stagePrompt`; `page-optimizer.js` L196 `→ BGW-07 controller`; `page-optimizer.html` L94–95 section title | Remove every claim that anything is sent to a controller. | Title "Check in simulator"; prompt "Load these settings into the simulator for a check run? Nothing is sent to the well."; target "→ simulator check" | "सिम्युलेटर में जाँचें"; "क्या ये सेटिंग जाँच हेतु सिम्युलेटर में लोड करें? कूप को कुछ नहीं भेजा जाता।"; "→ सिम्युलेटर जाँच" |
| P0-6 | Optimiser | `page-optimizer.html` L6–9 `.ph-sub`; L30–54; L79–88 | (a) Replace the subtitle with plain copy. (b) Put the same recommendation card as P0-3 above `#recBody`. (c) Wrap the *Uncertainty and model quality* section and the `quantNote` in `<details>` (closed). (d) Hide the "Recommended / continuous optimum" column behind that `<details>`, leaving Current / Recommended (= as applied) / Change. (e) After Confirm, show a primary button. | Subtitle "Finds the steam, soak, cutoff and pump speed that use the least steam per m³ of oil, while keeping rods safe." · `<summary>` "Model details (for specialists) ▸" · button "Open simulator and load →" | "रॉड सुरक्षित रखते हुए प्रति m³ तेल सबसे कम भाप वाली भाप, सोक, कटऑफ़ और पंप गति खोजता है।" · "मॉडल विवरण (विशेषज्ञों हेतु) ▸" · "सिम्युलेटर खोलें और लोड करें →" |
| P0-7 | Console | `page-console.html` L79–88; `page-console.js` L285–294; L142–273 order; `page-console.css` @1120 | (a) Relabel telemetry as simulated readings with plain keys. (b) The status chip uses the same 3-level scale as the risk meter (≤0.40 OK, ≤0.60 WATCH, >0.60 ALARM), so it never disagrees. (c) Put `#panelRisk` **before** `#panelXsec` in `.col-side`. At ≤1120 px the risk panel comes directly after the telemetry row. (d) Add a risk sentence under `#rmValue`. | "Simulated readings" · "Day" · "Reservoir temp" · "Viscosity" · "Oil rate" · "Rod load" · "Pump" · chip "OK / WATCH / ALARM" · "Rods safe at {spm} SPM — {fi} of 0.60 limit" / "Rods will float at {spm} SPM — reduce speed" | "अनुकरित रीडिंग" · "दिन" · "भंडार ताप" · "श्यानता" · "तेल दर" · "रॉड भार" · "पंप" · "ठीक / ध्यान दें / चेतावनी" · "{spm} SPM पर रॉड सुरक्षित — सीमा 0.60 में {fi}" / "{spm} SPM पर रॉड फ्लोट करेगी — गति घटाएँ" |
| P0-8 | Console | `page-console.html` L125–126 (panelDyno title/meta); L69–71 `#btnStress`; L269 classifier row | Relabel the dyno as indicative. Rename the stress test. Rename the classifier row, and show "—" when it has not run (`page-console.js` L262). | "Rod load vs stroke (indicative)" · meta "illustrative shape — not a measured dynacard" · "Try high speed (12 SPM)" · "Model float probability" | "रॉड भार बनाम स्ट्रोक (सांकेतिक)" · "सांकेतिक आकार — मापा गया डायनाकार्ड नहीं" · "उच्च गति आज़माएँ (12 SPM)" · "मॉडल फ्लोटिंग प्रायिकता" |
| P0-9 | All | `core.css` L24–33, L373 (`th .u` 10px), L492 (`.range-scale` 10px), L448 (`.btn-sm` 24px) | Projector-readable type: `--t-micro` 12.5, `--t-label` 12.5, `--t-small` 13.5, `--t-body` 15, `--t-title` 16, `--t-h1` 22, `--t-num` 20 px; `th .u` and `.range-scale` 11.5 px; `.btn-sm` height 32 px; `.btn` height ≥ 36 px. Also raise the `@media (max-width:1440px)` hero override (L579) by the same step. Acceptance: no horizontal scroll at 1024 px. | — | — |
| P0-10 | All | `core.js` STR `hi` L220–283 + `chrome.html` L17 + `page-overview.html` L18 | Replace the transliterations. Key → new HI: `navConsole` → "कूप अनुकरण", `pgConsole` → "कूप अनुकरण — BGW-07" · `navOptimizer` → "सिफ़ारिश" · `navOverview` → "सारांश" · `mlOptimum` → "सुझाई गई सेटिंग" · `mlOptimised` → "सुझाई गई सेटिंग (लागू)" · `manualRun` → "पिछला रन (बदला गया)" · `sorSurrogate` → "भाप-तेल अनुपात (त्वरित मॉडल अनुमान)" · `stress` → "उच्च गति आज़माएँ" · every "छड़" → "रॉड" · `telemetry` → "अनुकरित रीडिंग" · Print → "प्रिंट करें" · "crore" → "करोड़" when `LANG==="hi"` | EN nav: "Overview · Simulator · Recommendation · Model basis" | "सारांश · कूप अनुकरण · सिफ़ारिश · मॉडल आधार" (use "कूप अनुकरण" for console; "सिम्युलेटर" only in body copy) |

### P1 — should (10)

1. **Fold the audit material on the Overview.** In `page-overview.html`, wrap the L81–89 (*Fuel, cost and carbon* table + notes) and L107–119 (*Run provenance* + `claimNote`) sections in `<details>`, closed on screen and open in `@media print` (`core.css` L607). Summary text: "How these numbers are calculated ▸" / "ये आँकड़े कैसे निकले ▸".
2. **Simplify the status bar.** In `renderStatusBar()`, `core.js` L406–421, keep: page · BGW-07 · date/time · set-points · APPLIED/STAGED. Change the chip to "Simulation — not live well data" / "अनुकरण — कूप का लाइव डेटा नहीं". Move `PARAMS_REV`, "21/24 physics tests" and the run ID to `footer.html` ("Data lineage" column), keeping the exact wording.
3. **Make the set-point readouts typeable.** Turn `.readout` spans (`page-console.html` L37/43/49/55) into `<input type="number">` two-way synced with the sliders (clamp to min/max, same step). If that is too much work, remove the input-like border so they stop looking editable.
4. **Change the optimiser idle state** (`page-optimizer.html` L25–28) to a centred panel with one large button. Copy: "Find the best settings for BGW-07 — takes about 2 seconds" / "BGW-07 की सर्वोत्तम सेटिंग खोजें — लगभग 2 सेकंड". Move the surrogate sentence into P0-6's `<details>`.
5. **Fix the optimiser history** (`page-optimizer.html` L134–140; `page-optimizer.js` L228+). Add `data-en`/`data-hi` to the headers. Mark older rows `superseded` / "पुराना" once a newer one is staged. Rename "Improvement" → "vs midpoint baseline" / "मध्य-बिंदु आधार की तुलना में" so −41.3 is never read as the headline.
6. **Plain console subtitle** (`page-console.html` L6–9): "Try settings for the next CSS cycle and see temperature, oil rate and rod load day by day." / "अगले CSS चक्र की सेटिंग आज़माएँ — दिन-प्रतिदिन तापमान, तेल दर और रॉड भार देखें।" Also relabel `#btnReplay2` "Replay (61 d in 14 s)" → "Play the cycle (14 s)" / "चक्र चलाकर देखें (14 s)".
7. **Chart hygiene.**
   - Add `ticksuffix:" cP"` to `yaxis2` (`page-console.js` L171).
   - Set `yaxis.automargin` plus left margin ≥ 150 px on the Overview SOR chart in HI (`page-overview.js` L219/228) so the labels are not clipped.
   - Raise the chart font `CHART_FS` from 11 to 13.
8. **Colour audit.** Red is used only for alarm and for "worse". The amber "ELEVATED" state stays amber. The risk-meter number goes green when ≤0.40. The status tags "staged"/"applied" use neutral navy and green, never amber, because amber reads as a warning to a SCADA user.
9. **Methodology "In plain words".** Add a box at the top of `page-methodology.html` (after L10) with five bullets, EN and HI:
   - what is simulated (one CSS cycle, BGW-07, day by day)
   - where the inputs come from (OIL presentations, SPE papers)
   - what the ML does (searches settings quickly)
   - what is **not** validated (no history match yet)
   - what would make it trustworthy (OIL production history).
10. **Print header.** In `@media print`, show well, date, run and "Simulation — not for operational use" at the top of page 1, and hide the app bar, status bar and buttons.

### P2 — nice

- Add a "Download CSV" of the day-by-day cycle on the console, since engineers live in Excel.
- Show oil in both m³ and bbl in the recommendation card.
- Offer Indian digit grouping (1,13,726) as a HI-mode option.
- Replace the dynacard with a textbook-shaped surface card (fluid-pound corner as FI rises), keeping the "indicative" label.
- Move the theme toggle into the footer. Engineers do not need it on the first screen.
- Add a keyboard shortcut and a big-touch-target layout for tablets (≥44 px) at ≤1024 px.

### Do not touch

- Any value in `BAKED` (`data.js`) or `REF_*`, `OPT_*`, `FIELD_BASE`, `SURROGATE` or `ECON` in `core.js`. These are display changes only.
- The audited 26-Sep wording, character for character: "Prototype v1 physics (13 Sep) — self-audited; physics v2 recalibration in progress. Numbers are simulation outputs, not field measurements.", "21/24 physics tests (3 pending physics-v2 recalibration)", "Optimiser midpoint baseline", "−41.3% vs optimiser midpoint baseline", "per cycle, never per year" logic, and "Demonstration only — not for operational use". These may **move** (footer, `<details>`, methodology) but must not be reworded or deleted.
- The iso-oil arithmetic and its "Why per cycle / Why diesel" text: fold it, do not cut it.
- The Stage → Confirm → Load hand-off mechanics (`BUS` keys), the QC hooks, and methodology equations and sources.

### Principles (5 lines)

1. One primary action per page, and the answer before the evidence: recommendation card → numbers → "how calculated ▸".
2. One number per card, and every number has a unit and a plain label. Litres of diesel sit next to rupees.
3. Jargon (surrogate, R², MAE, XGBoost, LHS, p(float), run IDs, file paths, test counts) lives under "Details ▸" or on Model basis, never above the fold.
4. Say "simulation" wherever a reader could mistake it for live data. Never say "controller", "telemetry" or "applied to the well".
5. Hindi is real field Hindi (रॉड, सोक, कटऑफ़, SPM stay as the field says them; no "एमएल", "सरोगेट", "ट्विन"), and red means alarm or worse, nothing else.

### Needs a decision from the team lead

1. Should approximate (non-baked) console runs ever reach the Overview and Optimiser? Recommended: **no** (P0-1). The only other safe choice is to show them with a large "approximate" badge and never compute ₹ from them.
2. Should the EN nav rename "Twin console" → "Simulator" and "Optimiser" → "Recommendation"? The PS title says "digital twin", so the page heading could keep "Digital twin" as a subtitle.
3. Should Plotly be bundled locally for an offline venue? It adds about 3.5 MB per page if inlined, or ship `dashboard/vendor/plotly.min.js` beside the pages.
4. Should the Optimiser auto-run on load for engineer users, with `?demo=1` keeping the idle "presenter click"? README §8 says idle is deliberate.
5. The Overview's hero number: keep the SOR arrow (1.29 → 0.91), or lead with diesel litres saved per cycle? Recommended: litres + ₹ in the P0-3 card, with SOR kept in the strip.
