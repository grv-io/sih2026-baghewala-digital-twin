# Dashboard — Baghewala Digital Twin (PS SIH26120)

A four-page browser application. No server, no framework, no npm install. Open
`dashboard/index.html` in Edge or Chrome and everything works off the filesystem;
Plotly is bundled locally (`dashboard/vendor/plotly.min.js`, same version — 2.35.3 —
cdnjs served before) so a conference room with no internet still gets charts, and
every font is a system font (Segoe UI for Latin, **Nirmala UI** for Devanagari —
both ship with Windows 8–11, so nothing is fetched for Hindi either).

---

## 1. Pages

| File | Page | Who it is for | Contains |
|---|---|---|---|
| `index.html` | **Overview** | A GM, in eight seconds | Result strip (SOR, improvement, fuel value, CO₂), cycle-comparison table, fuel/cost/carbon arithmetic, three-bar SOR chart, run provenance |
| `console.html` | **Twin console** | The operator | Set-point toolbar, simulate, telemetry strip, cycle time series + replay + scrub cursor, well cross-section, computed dynamometer card (surface + pump) with a measured-card upload/paste fault check, rod-floating risk meter, ISA-101 alarm with ACK, stress test |
| `optimizer.html` | **Optimiser** | The engineer reviewing a recommendation | Recommendation table (current / recommended / as-applied / change), constraint report, uncertainty and model quality, two-stage audited apply, optimisation history |
| `methodology.html` | **Model basis** | The judges | The four physics models with equations, field parameters, fuel/cost/carbon basis, data lineage, surrogate and search, uncertainty, **calibrate from field data (demo + your own CSV)**, **field-level steam scheduling across wells (demo, 12 synthetic wells)**, validation status *and what is not validated*, recalibration plan, source citations |

Each page is **self-contained** — the shared CSS and JS core is inlined into all
four at build time, so any one of them can be opened, copied or emailed on its own.

---

## 2. Build

`index.html`, `console.html`, `optimizer.html` and `methodology.html` are
**generated**. Edit `dashboard/src/`, never the built HTML.

```
node dashboard/build.js
```

```
dashboard/
  build.js                    assembles the four pages
  vendor/
    plotly.min.js              bundled Plotly 2.35.3 — same build cdnjs served
  src/
    core.css                  tokens, both themes, chrome, tables, buttons  — shared
    core.js                   config, constants, formatting, i18n, theme, state bus — shared
    chrome.html               app bar + status bar                          — shared
    footer.html               colophon                                      — shared
    data.js                   BAKED physics series (console only)
    dyno-data.js               DYNO_CARDS -- baked dynamometer cards (console only)
    page-overview.{html,js}
    page-console.{html,css,js}
    page-optimizer.{html,css,js}
    page-methodology.{html,css,js}
```

Every page that charts (`index.html`, `console.html`) loads Plotly from
`vendor/plotly.min.js` — a **relative** path, so it resolves whether the page is
opened from the filesystem, a share, or a projector laptop with no network. If
that file is missing or fails to load, an `onerror` handler on the `<script>` tag
falls back to the cdnjs copy at the same version, so a networked machine still
works if the vendor file is ever deleted. `optimizer.html` carries no charts and
skips the tag entirely (`build.js`'s `plotly: true/false` per page). `methodology.html`
is also `plotly: false` in `build.js` — its doc-body is otherwise entirely tabular —
but its "Calibrate from field data" section (§7.3) carries two small charts, so that
page loads `vendor/plotly.min.js` itself, on demand, the first time one of those
charts actually draws (`ensurePlotly()` in `page-methodology.js`, the same
vendor-then-cdnjs fallback as above), rather than changing `build.js`'s per-page flag.

Output sizes (rev 13): index 198 KB · console 450 KB · optimizer 206 KB · methodology 319 KB
(the vendor Plotly file, ~4.5 MB, is not inlined — it is fetched once per page
load like any other script, from disk).
Only `console.html` carries the full day-by-day `BAKED` series; the other pages
carry the two cycle summaries from `core.js`, which is why they are much smaller.

---

## 3. Themes

`data-theme="light"` (**the default**) and `data-theme="dark"`.

- **Light** is the institutional register: `#f4f6f8` ground, `#ffffff` panels,
  `#16202b` text, OIL navy `#0f2540` chrome, desaturated saffron `#E08A3C` used
  only for the active-nav underline and the tricolour rule. **No glows at all** —
  the alarm pulses opacity, not shadow. Radii are `2px` everywhere; elevation is a
  single 1 px hairline shadow.
- **Dark** is the control-room option and keeps the v3 GitHub-dark palette.
- Chart colours are re-derived per theme (`--chart-t/-mu/-q/-bar-*`) and read at
  render time through `tok()`, so **Plotly is re-rendered on every theme change**
  rather than being left with a stale white paper colour.
- Selection order: `?theme=` → `localStorage` → light. A tiny pre-paint script in
  `<head>` sets the attribute before first paint, so the page never flashes.
- Toggle: `LIGHT | DARK` in the app bar.

## 4. Language — EN | हिं

Same three-tier policy as v3, extended for the new nav, page and table strings.

- **Tier 1** (`class="bi"` + `data-en`/`data-hi`) renders in **both** languages,
  stacked, in either mode — page titles, panel titles, the alarm.
- **Tier 2** (`data-en`/`data-hi`, or a `STR` key via `T()`) is swapped by the
  toggle: nav, buttons, field labels, table row labels, group headings, constraint
  names, status tags, chart axis titles and category names.
- **Tier 3** is never translated: units, `BGW-07`, `SIH26120`, acronyms, module
  paths, source citations, all numerals (Latin digits, as in Indian technical
  documents — Devanagari numerals would break `tabular-nums`), and the long
  explanatory prose blocks, which are engineering argument rather than interface.
- `[lang="hi"]` forces `letter-spacing:0`, `text-transform:none`, `line-height:1.62`
  and `1.05em`; uppercase-tracked label styles would otherwise mangle conjuncts
  and matras.
- Selection order: `?lang=` → `localStorage` → EN. Pages register extra redraw work
  through `onLangChange()`; `onThemeChange()` is the equivalent for charts.

## 5. State between pages

One namespaced `localStorage` key, `bgw.v4`, read and written through `BUS` in
`core.js`. Every page also boots correctly with an empty store (a fresh profile,
private browsing, or site data blocked) by falling back to the baked reference run.

| Key | Written by | Read by |
|---|---|---|
| `theme`, `lang` | app bar | all pages, pre-paint |
| `run` | twin console, after every simulation — run ID, timestamp, set-points, summary, applied flag, and the replaced run | overview, optimiser, status bar |
| `staged` | optimiser, on Confirm | twin console (staged banner), status bar |
| `rec` | optimiser, on run — recommendation ID, timestamp, raw result | overview provenance, console (classifier p(float)) |
| `optHistory` | optimiser | optimiser history table |
| `prices` | overview's "Your prices" panel — `{diesel, discount, oilBbl}`, or absent/`null` for base case | overview (card, result strip), optimiser (recommendation table margin rows) |

Nav links also carry `?lang=&theme=`, so the demo survives a machine with site data
disabled and QC can deep-link any state.

**The hand-off loop:** run the optimiser → *Stage set-points* → *Confirm* → the
status bar shows `STAGED` on every page → open the twin console → *Load into
console* → the twin re-runs the physics at the applied values → the status bar
shows `APPLIED`, the overview relabels its first column *Manual run (replaced)*,
and the optimiser prints the audit line. Nothing is sent to a controller; there
is no SCADA link.

---

## 6. Data source

**Deploy kit, 27 Sep 2026: `MOCK` now auto-detects instead of a hand-set
literal.** `core.js`'s `MOCK` is computed once at load: `?mock=1`/`?mock=0`
in the URL always wins (QC/demo override); otherwise `MOCK_OVERRIDE` (a
`true`/`false`/`null` constant at the top of `core.js`) is honoured if set;
otherwise it auto-detects from `location.protocol` — `file://` (opened
straight off the filesystem, no server) serves the baked reference data
below, and anything else (served by `uvicorn api.main:app`, i.e. this
repo's own FastAPI process on Render/Railway/Fly/a VPS, or a local dev
server) is live. `API_BASE` is the empty string (same origin) whenever
FastAPI is the one serving the page, since `api/main.py` mounts the whole
`dashboard/` directory at `/` — see `docs/DEPLOY.md` for how to run/deploy
that process. The `file://` fallback for `API_BASE` still points at
`http://localhost:8000` for a developer testing live mode off the
filesystem with `?mock=0` against a local server.

Baked data itself is re-baked for rev 12: `BAKED` in
`src/data.js` holds verbatim `twin.cycle.simulate_css_cycle` output at:

| scenario | set-points | result (FY25 price deck, base case) |
|---|---|---|
| `BAKED.reference` (baseline (b), published-practice, BGW-8-derived) | 1,300 t / 10 d / 91 kgf/cm² / 86-in / 1.3 m³/d / 5.0 spm | SOR **4.3514** t/m³ (incr. 5.799) · oil 298.75 m³ · 166.57 d (produce 140 d) · max FI 0.6343 · ended by **float onset** (day 139) · margin **₹12,886**/cycle-day gross, **&minus;₹1,601**/cycle-day incremental |
| `BAKED.optimized` (rev-12 5-D recommendation) | 1,000 t / 10 d / 85 kgf/cm² / 64-in / 0.60 m³/d backstop / 3.0 spm | SOR **3.1910** t/m³ (incr. 4.488) · oil 313.38 m³ · 202.51 d (produce 180 d) · max FI 0.6217 · ended by **float onset** (day 179) · margin **₹22,040**/cycle-day gross, **+₹7,973**/cycle-day incremental |

Economics v2 (rev 8/9): the objective and the headline ₹ figure are the **incremental** margin (oil
over the cold, unstimulated well for the same window, net of daily opex) — gross margin (steam ÷
ALL oil, still the headline SOR convention) is kept for comparison. At the $65 FY26-floor price
deck (a named preset, not the default) the recommendation is a near-break-even **+₹40**/cycle-day and
the baseline is **&minus;₹11,295**/cycle-day — see §7.2. **rev 12 (physics wave 4):** the produce phase
now ends on an OPERATING RULE, not just a rate cutoff — `css.produce_end_rule` (default `"either"`)
ends the cycle when the oil rate (past its peak) falls below the cutoff OR when
`floating_index > css.fi_alarm` (0.6) persists `css.fi_alarm_days` (3) consecutive produce days, i.e.
the operator pulls the well / re-steams rather than run floating rods for months. Both baked scenarios
above now end by float onset, not the rate cutoff — see `twin/cycle.py`'s `produce_end_reason` and
`docs/model-improvement/TIER1_PROGRESS_LOG.md` §11.3.

Any other slider combination falls back to an in-browser approximation tuned to the
same field parameters, and the panel meta says so (`in-browser approximation` vs
`baked twin output`). Force live mode with `?mock=0` (or serve the dashboard from
`uvicorn api.main:app` directly, which auto-detects) to drive everything from the
live twin + ML packages: `apiSimulate()` stays synchronous (same v0.1 contract, now
hitting `api/main.py`'s `/simulate` alias); `apiOptimize()` now starts a background
job (`POST /api/optimize`) and polls `GET /api/jobs/{id}`, showing a live progress
state in the optimiser page's idle panel until the search lands; and the
"Dynamometer card (computed)" panel calls `GET /api/dyno/cards` for the CURRENT
set-points (`twin.dyno.compute_cards()`, live, <=50 ms) instead of the nearest-baked
lookup below, adapting its flatter response shape into the same card shape
`dynoCardTraces()` already renders (`liveCardToBakedShape()` in `page-console.js`);
on a fetch error it falls back to the nearest-baked pick with a console warning
rather than breaking the panel. See `docs/DEPLOY.md` for how to run/deploy the
FastAPI process this all talks to, and the `api/` package's OpenAPI docs (`/docs`)
for the full endpoint contract.

**Dynamometer card (computed).** `src/dyno-data.js` holds `DYNO_CARDS`, the verbatim
export of `twin.dyno.bake()` (`ml/models/dyno_cards.json`, schema `dyno_cards/v1`) —
8 baked cards, `{baseline, recommendation} × {early_hot, mid, float_onset,
stress_12spm}` (rev 12: the `late_cold` key is renamed `float_onset` — the day the
float-alarm rule first fires, not a fixed last-row pick), each a surface (polished-rod) and downhole (pump) card at 200 points,
plus the fault classifier's `card_type`/`card_label`/`signatures` and the reference
peak/min PRL, plunger stroke, fillage, energy and separation figures. See
`docs/model-improvement/DYNO_CARD_MODEL.md` for the physics (predictive Gibbs (1963)
wave equation for the rod string + a valve state-machine for the pump) and the 4
reference card shapes. The panel picks a card as follows:
- **Baked baseline or recommendation run** (steam_t/soak_days/cutoff/stroke_in/
  p_wellhead_kgf_cm2 match `BASELINE_PUBLISHED` or `OPT_APPLIED`, spm ignored —
  rev 12: stroke/pressure are now matched too, so a baseline run at the
  recommendation's stroke doesn't wrongly resolve to the baseline's own card) —
  the card follows the replay/scrub day: nearest of the scenario's 3 sampled days
  (early/mid/float_onset), labelled "Day *N* · μ ≈ *X* cP".
- **12-SPM stress test** (`spm` at or near the slider max) on a matched scenario —
  the scenario's own baked `stress_12spm` card, labelled "12-SPM stress test".
  Baseline's is heavy-oil viscous drag with no separation; the recommendation's is
  **rod float with the carrier bar separated** (min PRL 0 kN) — the demo's clearest
  floating-risk moment, and the only case the panel draws a highlighted near-zero
  segment on the surface card for.
- **Any other (approximate, off-baked) set-point** — the nearest of all 8 baked
  cards by `(spm, μ)` (`pickDynoCard()` in `page-console.js`), tagged "card from
  nearest baked case" next to the existing "Approximate run" chip. The panel never
  invents a card shape for a set-point the twin hasn't actually been run at.

Regenerate after any physics/params change to `twin/dyno.py` or `params/field_params.json`:
```
.venv\Scripts\python.exe -m twin.dyno --bake ml/models/dyno_cards.json
```
then re-export `ml/models/dyno_cards.json` into `src/dyno-data.js` (verbatim,
200 points/curve — see the header comment in that file for the exact re-export
step) and `node dashboard/build.js`. `build.js` inlines `dyno-data.js` into
`console.html` only, immediately after `data.js`.

**Check a measured card (27 Sep 2026).** A collapsed `<details>` under the
computed-card panel — "Check a measured card ▸" / हिंदी "मापा गया कार्ड जाँचें ▸" —
lets an operator upload a CSV (`position_m`/`position_in`,
`load_kN`/`load_klbf` — header names recognised, or magnitude-guessed if
absent) or paste a two-column table from a MEASURED surface dynamometer card,
and get a fault read: card type (full pump / fluid pound / gas interference /
heavy-oil viscous / rod float), estimated fillage, peak/min PRL, a
plain-language bilingual sentence, and a probability bar per class — via
`ml.dyno_classifier.classify_card()`, a RandomForest trained ONLY on
physics-generated cards (`ml/README.md` "Measured dynamometer-card
classifier"; never a real one — the caveat line is always shown with the
result). A **Download template** link points at
`data/templates/dyno_card_template.csv`.
- **Live** (`MOCK = false`) — `POST`s `{position, load, units}` to
  `/api/dyno/classify` (or the raw file as multipart `form-data` when a CSV
  was uploaded) and renders the classifier's own probabilities, `fillage_est`,
  `sentence_en`/`sentence_hi` and `model_caveat`.
- **MOCK** — the trained classifier is a Python/joblib artifact, not
  something the browser can run, so this path is a tiny (~60-line) in-browser
  NEAREST-NEIGHBOUR fallback (`clfNearestBaked()` in `page-console.js`):
  parse → auto-detect units → close the loop → normalise the bounding box to
  `[0,1]x[0,1]` → resample to a uniform arc-length parametrisation (48
  points) → Euclidean-nearest of the 8 baked cards' own surface curves
  (`DYNO_CARDS`, already loaded). Tagged **"approximate, offline"**; fillage
  is read off the matched baked card's own `pump_fillage`, peak/min PRL
  straight from the parsed data — there are no real class probabilities in
  this path, so no probability bars render.
- **`?qc=cardcsv`** opens the panel and injects the baseline scenario's `mid`
  baked card's own surface curve as CSV text, then classifies it — no
  file-picker dialog, mirroring `?qc=calibcsv` on the Model-basis page (§7.3).

> **26 Sep, rev 5 re-bake:** physics rev 5 is calibrated to published Baghewala
> benchmarks (SOR 3–8, 5–6× uplift, 15–40 bbl/d); the unit-test tag shown across the
> dashboard (footer, methodology page) is **57/57 physics & benchmark tests (2 known
> gaps marked xfail)**, and every page carries a **"Physics rev 5 — calibrated to
> published Baghewala benchmarks; synthetic data, not field-validated"** provenance
> line. The optimiser's objective changed from minimising SOR to maximising **margin
> per cycle-day**, with soak held at 10 d field practice (the twin has no interior
> soak optimum). See `docs/model-improvement/TIER1_PROGRESS_LOG.md` §4–§5b for the
> full calibration and re-bake log. (History: the 13 Sep v1 bake used 1,500 t / 7 d /
> 3.0 m³/d / 8.0 spm → SOR 1.2943, with a v1 "field-practice midpoint" baseline at
> 1,750 t / 9 d / 4.5 m³/d / 8.0 spm → SOR 1.5022; those numbers no longer appear
> anywhere else in this product.)

> **27 Sep, rev 9 re-bake:** physics v3 + Economics v2, on OIL's CONFIRMED FY25 price
> deck (US$78.09/bbl, Annual Report 2024-25, minus a $10/bbl heavy-oil discount
> `[ASSUMPTION]` = ₹5,992/bbl; the old $65/₹4,840 deck is kept as a named "FY26
> planning floor" preset). The unit-test tag is now **116/117 physics & benchmark
> tests (1 known gap: soak, marked `xfail`)** — the rev-5 P<sub>res</sub>/Liaohe xfail
> was resolved in physics v3 by re-specifying the benchmark against a Darcy-derived
> band. The optimiser's objective is now the **INCREMENTAL** margin per cycle-day
> (oil over the cold, unstimulated well for the same window, net of daily opex) —
> gross margin (steam ÷ ALL oil, still the headline SOR convention) is kept for
> comparison. The cascade recommendation moved from 1,700 t / 10 d / 0.85 m³/d / 5.0
> spm (rev 5) to **1,600 t / 10 d / 0.70 m³/d / 4.0 spm** — the true-physics grid
> optimum (minimax-regret across both price decks), used directly because the raw
> ML surrogate argmax missed it by more than the ~₹300/cycle-day tolerance. See
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §8–§9 and `params/CHANGELOG.md`
> rev 8/9 for the full log.

> **27 Sep, rev 12 re-bake (physics wave 4):** the produce phase now ends on an
> OPERATING RULE (`css.produce_end_rule`, default `"either"`) — rate cutoff OR
> `floating_index > 0.6` persisting 3 consecutive produce days (the operator pulls /
> re-steams rather than run floating rods for months) — not a plain rate cutoff. Both
> baked scenarios now end by **float onset**, and the whole recommendation changes
> character: it exploits the rule by running the rods slower and shorter-stroke, which
> *delays* the float onset rather than avoiding it. The unit-test tag is now **236/238
> physics & benchmark tests (2 declared gaps: soak; cold-well pumpability, both marked
> `xfail`)** — the cold-well gap is new: the model's cold (unstimulated) well at the
> 45% formation water cut cannot be rod-pumped at ≥2 spm on the assumed 86-in unit
> under any published emulsion law, yet Baghewala's wells WERE produced cold
> historically, so every incremental-margin figure below carries an estimated
> ~₹2.7k/cycle-day of cold-well pumping power a genuinely pumpable cold well would not
> pay (§7.2's cold-well-vs-shut-in note). The 5-D cascade recommendation moved from
> 1,600 t / 10 d / 0.70 m³/d / 4.0 spm / 86-in / 91 kgf/cm² (rev 9, 4 controls) to
> **1,000 t / 10 d / 0.60 m³/d backstop / 3.0 spm / 64-in / 85 kgf/cm²** (rev 12, 6
> controls: injection pressure and stroke length are now optimised too) — the raw ML
> surrogate argmax physics-verified 51% below this point, because the float
> classifier's ~95% positive-class imbalance under the new rule leaves it unable to
> see that the cutoff is irrelevant once the rule ends the cycle first. See
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §11 and `params/CHANGELOG.md` rev
> 10–12 for the full log.

> **27 Sep, rev 13 re-bake (wave 5: operating policy as a control, fair baseline,
> smooth inversion, injectivity, levies deck):** the re-score's top finding was that
> the rev-12 headline (+₹9,574/cycle-day) came from a **pull-on-first-alarm baseline**
> against a recommendation that itself effectively slowed down — an unfair,
> different-policy comparison. rev 13 makes the operator's float response
> (`css.float_policy`: `pull` / **`vfd_hold`** / `vfd_then_pull` / `none`) an explicit
> control, applies it ALIKE to the baseline, the recommendation and the cold
> counterfactual, smooths the emulsion-inversion cliff into a 0.075-wide band, gates
> the wellhead pressure on injectivity (≥400 kPa margin), and adds a third price deck
> (net of royalty + OID cess, ~₹3,600/bbl). **The recommended policy is VFD-hold**
> (the drive slows the unit to hold the float index at 0.6 down to a 2-spm floor,
> pulling only after 3 alarm days there); the params default stays `pull`, since that
> is the operation the benchmark calibration was made under. Both the baseline and the
> recommendation are now baked and shown running VFD-hold, so the console's two
> scenarios are a FAIR, same-policy comparison for the first time.
> The 6-D cascade recommendation moved from **1,000 t / 10 d / 0.60 m³/d backstop /
> 3.0 spm / 64-in / 85 kgf/cm² (pull)** (rev 12) to **1,000 t / 10 d / 0.60 m³/d
> backstop / 4.5 spm start / 64-in / 89 kgf/cm² (VFD-hold)** (rev 13) — the 85-kgf/cm²
> floor does not survive the injectivity gate (only 53 kPa of margin over the assumed
> 9.4 MPa reservoir pressure), and pump speed is now a weak, interior lever once the
> VFD does the slowing. The unit-test tag is now **263/265 physics & benchmark tests
> (2 declared gaps: soak; the steam optimum at the mid-range (0.15) diesel discount
> sitting below BGW-8's published slug-size band, both marked `xfail`)** — the
> rev-12 cold-well-pumpability xfail is RESOLVED (now a passing test): the cold
> counterfactual obeys the same float policy as the stimulated well, so it is
> correctly SHUT IN at the base 45% water cut rather than "unpumpable yet producing".
> **The headline convention changed accordingly**: the card now leads with the
> SAME-POLICY gain, **+₹3,332/cycle-day** at OIL's FY25 realisation (+₹4,319 at $65,
> +₹5,382 net of levies) — a modest, ~5%-of-revenue operational gain, mostly the 64-in
> stroke (57%) letting the VFD hold the float line longer, not the pump-speed story
> rev 12 told. A **"Compare against a baseline that…"** toggle on the optimiser page
> shows what the number would be if the baseline were instead assumed to pull on the
> first alarm (+₹12,917 — 68% of THAT number is the operating-rule switch itself, not
> the set-point) or to do nothing about float at all (**+₹2,622** — the SAME canonical
> recommendation still gains here, mostly ordinary steam/cutoff savings, because the
> model prices no rod-failure cost. **rev 13.1 correction:** an earlier draft of this
> toggle printed −₹3,865 for "does nothing", which was the wrong row of
> `TIER1_PROGRESS_LOG.md` §12.6 — the best RE-OPTIMISED plan *within* that policy
> (a different, more float-safe set-point) compared against a baseline that also does
> nothing, not the canonical recommendation against it; that −₹3,865 number must not
> appear on this dashboard).
> **The UQ counterfactual statistic was also found and fixed**: an earlier draft
> printed "P(incremental margin/day > 0) = 0.034" beside a FY25 net-cash p50 of
> +₹1,132/day — inconsistent on its face. Computed directly from the 1,500-draw
> sample, the FY25 figures are P(net cash > 0) = 53.7% and P(incremental > 0, vs the
> shut-in cold well) = 37.7%; the 0.034 was the **net-of-levies deck's** P(net cash >
> 0) figure, mis-paired against the FY25 rupee line and against the wrong metric — the
> same species of deck-mixing bug the rev-12 headline itself had (§7.2). The dashboard
> now quotes P(net cash > 0), always labelled as such, as the "positive cash vs a
> shut-in cold well" statistic, and P(recommended > baseline, same policy) — 96.5%
> (FY25) / 99.2% ($65) / 99.9% (levies) — as the robust headline. See
> `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12 and `params/CHANGELOG.md` rev 13
> for the full log.

**Field-level steam scheduler (Model basis, 27 Sep 2026).** `src/core.js`
holds `FIELD_SCHEDULE_DEMO`, a trimmed baked export of `ml/models/
field_schedule_demo.json` (`python -m ml.schedule --wells data/external/
field_wells_synthetic.csv --out ml/models/field_schedule_demo.json`, 12
SYNTHETIC wells, seed 42 — see `ml/README.md` section "Field-level steam
scheduling" for the model and `data/external/SOURCE.md` for the data note).
The section renders immediately from that constant (Gantt of the exact
schedule's generator timeline, job table, KPIs vs the naive counterfactual);
if the page is NOT running from `file://` (`MOCK === false`), it then fetches
`GET /api/schedule/demo` and re-renders with the API's own current output
(`normalizeScheduleResult()` in `page-methodology.js` maps either shape to
the same internal one) — same "baked paints first, live replaces it"
pattern as everywhere else on this page. `POST /api/schedule` (JSON wells
list or CSV text) is not driven from the UI; it exists for programmatic use
— see `api/routers/schedule.py`.

---

## 7. The claim, and how it reconciles

Three labelled scenarios, two deltas, and a per-cycle economic figure — led since
rev 13 by **NET CASH per cycle-day** (`margin_with_opex_inr_per_cycle_day`,
counterfactual-free — the optimiser's actual objective as of rev 13), compared under
the **SAME operating policy** on both sides (VFD-hold by default); gross margin
(steam ÷ all oil, still the headline SOR convention) and incremental margin (net cash
minus the cold-well counterfactual — equal to net cash here, since the cold well is
shut in at the base water cut) are kept alongside for comparison.

| scenario | set-points | SOR (gross / incr.) | net cash / incr. ₹/cycle-day (FY25 deck) |
|---|---|---|---|
| Published-practice baseline (b) (BGW-8 job, 2018), VFD-hold — not OIL's current practice | 1,300 t / 10 d / 91 kgf/cm² / 86-in / 1.3 m³/d / 5.0 spm start | 3.29 / 3.29 | 12,064 / 12,064 |
| Current cycle / Manual run (replaced) | whatever the console last ran (same as baseline (b) by default) | 3.29 / 3.29 | 12,064 / 12,064 |
| Physics-grid optimum (as applied), VFD-hold | 1,000 t / 10 d / 89 kgf/cm² / 64-in / 0.60 m³/d backstop / 4.5 spm start | 2.83 / 2.83 | 15,396 / 15,396 |
| Conservative (VFD holds & pulls at FI > 0.5, same set-points) | 1,000 t / 10 d / 89 kgf/cm² / 64-in / 0.60 m³/d backstop / 4.5 spm start | 2.95 / 2.95 | 14,238 / 14,238 |

- **Primary claim:** net cash **+₹12,064 → +₹15,396 per cycle-day**
  (**+₹3,332/cycle-day**, at OIL's FY25 realisation, SAME policy on both sides); SOR
  (gross) **3.29 → 2.83 t/m³**, **−14%** — both cycles are on screen. At the $65
  FY26-floor deck the gain is +₹4,319; net of royalty and cess, +₹5,382 (the
  recommendation's edge over the baseline GROWS on the levies deck, since it saves
  steam) — shown alongside, not hidden.
- **What the toggle shows:** if the baseline is instead assumed to be operated
  differently, the number moves more than any set-point does. Pulling on the first
  alarm (the rev-12 comparison): **+₹12,917** — but 68% of that is the operating-rule
  switch, not the set-point (Shapley). Doing nothing about float at all: **+₹2,622** —
  the SAME canonical recommendation still gains, because the model prices no
  rod-failure cost, so avoiding float buys no ₹ against a baseline that never pays
  for floating rods either (see §"What is NOT validated"). *(A different, more
  float-safe re-optimised plan LOSES money against that same baseline —
  `TIER1_PROGRESS_LOG.md` §12.6's "best rec within that policy" row, −₹3,865 — but
  that is not the recommendation on this dashboard and that figure must not be
  quoted as if it were.)*
- **Gain decomposition** (Shapley, vs baseline (b), SAME policy, FY25 deck): stroke
  **57%**, cutoff **30%** (interaction — with the 64-in stroke, the baseline's 1.3
  m³/d cutoff would bind before its float pull), steam **11%**, pressure **1%**, pump
  speed **1%** (no longer a lever once the VFD does the slowing) — the whole gain is
  "a shorter stroke lets the VFD hold the float line longer".
- **Labelled secondary:** the retrained ML surrogate's prediction at the SAME
  canonical point — ₹14,862/cycle-day net cash vs the twin's ₹15,396 (a residual of
  ₹533, inside the ±₹1,205 hold-out MAE) — printed alongside, never confused with the
  twin figures above; it is an emulator for UQ/what-if speed, not the decision engine
  (rev 13's search is a true-physics 6-D + policy grid, no ML surrogate in the
  decision loop).

### 7.1 Fuel, cost and carbon — per cycle, never per year

**Baghewala's steam generators are diesel-fired.** OIL's own operations deck
(BGW-08 first cycle, 12 Jul 2025) records ~220 kg/hr HSD against ~3,100 kg/hr of
steam, so every tonne of steam costs ~71 kg of high-speed diesel. There is no gas
supply to the field.

The **iso-oil counterfactual** — how much steam the current practice would have
burned to make the *recommended cycle's* oil — is the honest comparison. rev 12: the
recommendation now injects LESS steam in absolute terms than the baseline (1,000 t vs
1,300 t) as well as recovering more oil per tonne, so a plain difference of the two
fuel bills would already show a saving in the right direction — but the SOR-based
figure below is still the larger, correct comparison, since it asks how much MORE
steam the baseline's own (worse) efficiency would need to match the recommendation's
oil, not just how many fewer tonnes were injected:

```
steam_counterfactual = 313.38 m³ × 4.3514 t/m³  =   1,364 t
steam_avoided        = 1,364 − 1,000             =     364 t   per optimised cycle
diesel_avoided       = 364 × 85.54 L/t           =  31,107 L   (25.8 t)
CO2_avoided          = 364 × 223.8 kg/t          =    81.4 tCO2
value_avoided        = 364 × ₹5,856–8,366/t      = ₹0.21–0.30 crore
programme (× 19 CSS jobs, OIL FY2025-26)         = ₹4.1–5.8 crore · 1,546 tCO2/yr
```

This iso-oil figure is physics only (steam/oil/SOR) — it does not use either price
deck and is unaffected by the "Your prices" panel. The rev-12 recommendation's real
headline saving is in **incremental margin per cycle-day** — see §7 above for the
primary claim. The overview's result strip leads with **per-m³ intensity** tiles
(diesel L/m³, CO₂ kg/m³, baseline → recommendation, sign/colour derived) rather than
an absolute "not burned/avoided per cycle" framing, precisely because the
recommendation using less steam in absolute terms made that framing read as
self-contradictory; the absolute steam/diesel/CO₂ per cycle numbers above are kept in
the details table.

Two things this deliberately does **not** do:

1. **No `365 / days_total`.** `days_total` is the *simulated producing-cycle*
   length (187–282 d at rev 9's baseline and recommended set-points), not the
   interval between field CSS jobs. Real CSS cycles are
   re-visited 6–18 months apart; Baghewala banked 39 cycles in ~6.5 years across a
   34-well field. Dividing 365 by the simulated duration manufactures more
   cycles/well/year than any CSS operation achieves, and inflates any rupee figure
   by roughly the same factor. Programme figures are an **explicit multiplication**
   by a published job count instead. `scaleToProgramme()` requires the caller to
   pass that count, so the error cannot be reintroduced by accident.
2. **No `STEAM_INR_PER_T = 1300`.** That v3 constant had no provenance anywhere in
   the repository and corresponds to roughly what *gas*-fired steam costs. It is
   deleted. The price is now derived: 85.54 L/t × ₹97.80/L = ₹8,366/t (Rajasthan
   retail *pump* price, an upper bound), with a −30% bulk-purchase sensitivity for
   the lower bound. The physical quantities — tonnes of steam, litres of diesel,
   tonnes of CO₂ — are unaffected by any argument about price.

Derivation and citations: `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md`
§0 and §1.2, `docs/research/baghewala_facts.md` §4. The constants live in `ECON` in
`core.js`, each with its source and an honesty label.

Nothing on any page is a hand-typed result: every value derives from `BAKED`,
`OPT_RESULT` (= the real `ml/optimize.py` output), `ECON`, or the live API.

### 7.2 The headline convention, and "Your prices" (26 Sep 2026; rewritten rev 13, wave 5)

`ml/uq.py`'s Monte Carlo (§ Uncertainty, `methodology.html`) found different answers
depending on which question is asked — and an earlier draft of this section's own
headline had a resolved bug, kept here as a worked example of the mistake:

- **P(recommended net cash/cycle-day > baseline (b) net cash/cycle-day), SAME
  policy (VFD-hold) = 96.5% (FY25) / 99.2% ($65) / 99.9% (net of levies)** — a
  *paired* comparison. Both set-points see the same draw's physics under the SAME
  operating policy on every one of 1,500 draws, so the shared uncertainty (formation
  water cut, condensate recovery, cold-well skin, diesel discount, oil price, …)
  cancels out of the *difference*. **This is the robust headline.** If the baseline
  is instead assumed to pull on the first alarm: 95.3% (FY25); if it has no float
  response at all: 16.5% (FY25) — a minority, since a float-safe recommendation is
  compared against a baseline not paying the (unpriced) cost of floating rods.
- **The resolved counterfactual statistic.** An earlier draft printed "P(incremental
  margin/day > 0) = 0.034" right next to a FY25 net-cash p50 of +₹1,132/day —
  inconsistent on its face (a p50 near zero implies roughly half the draws are
  positive, not 3.4%). Computed directly from `ml/models/uq_samples.csv` (1,500
  draws) at the recommended point: **P(net cash > 0) = 53.7% (FY25) / 25.2% ($65) /
  3.4% (net of levies)**; **P(incremental > 0, vs the shut-in cold well) = 37.7%
  (FY25) / 16.7% ($65) / 1.8% (net of levies)**. The 0.034 in the original draft was
  the **net-of-levies deck's** P(net cash > 0) figure, mis-paired against the FY25
  rupee line AND against the wrong metric (net cash, not incremental) — the same
  species of deck-mixing bug the rev-12 headline itself had (this section, above).
  **Column definitions:** net cash (`margin_with_opex_inr_per_cycle_day`) is revenue
  − steam cost − fixed workover cost − power cost − opex, per cycle-day, with NO
  cold-well counterfactual subtracted — a positive figure reads as "positive cash vs
  a SHUT-IN cold well". Incremental (`margin_incremental_inr_per_cycle_day`)
  additionally nets out the cold well's own cash for the same window — 0 under the
  default "policy" convention, since the cold well's floating index exceeds the
  alarm line under its own float policy at the base 45% water cut.
- **Convention adopted:** **P(net cash > 0)** is quoted everywhere on this dashboard
  as the "positive cash vs a shut-in cold well" statistic, always labelled as such;
  **P(recommended > baseline, same policy)** is the robust headline; P(incremental >
  0) is shown alongside as a stricter, unpaired reading, never as the headline.

The team's decision: **lead with what is robust (the same-policy paired delta and
P(better)), print the absolute net-cash figure as "at OIL's FY25 realisation" across
all three price decks, show a "Compare against a baseline that…" toggle rather than
silently picking one baseline-operation assumption, and let the engineer supply
their own prices.** So the recommendation card and the overview result strip's
margin cell now read, first, a headline built fresh every render from
`ECON`/`UQ`/`OPT_RESULT` — never a hand-typed string:

> **+₹3,332 per cycle-day vs the assumed baseline run the same way (VFD-hold)
> · better in 96.5% of 1,500 scenarios · steam per m³ oil 3.29 → 2.83 (−14%)**
> If that job is instead pulled at the first alarm: +₹12,917 (mostly the operating
> rule). If its rods are simply left floating: +₹2,622 — we do not price rod
> failures.
> Where the gain comes from: stroke 57% · cutoff 30% · steam 11% — the shorter
> stroke lets the VFD hold the float line longer at the 2-spm floor.
> Absolute: net cash +₹15,396/d FY25 (p50 under uncertainty +₹1,132) · $65 +₹3,738 ·
> net of royalty + cess −₹8,811 · injectable at 89 kgf/cm² (margin ≥ 300 kPa). Range
> (uncertainty, net cash, FY25 deck): −₹14,757–+₹16,962 (1,500 scenarios).
> *Conservative variant (VFD holds & pulls at FI > 0.5): +₹14,238/cycle-day (FY25) ·
> +₹2,394/cycle-day ($65) · −₹10,355/cycle-day (levies)*
> SOR 3.29 → 2.83 (gross) · incremental 3.29 → 2.83 (identical to gross here — the
> cold well is shut in)

The **"Compare against a baseline that…"** toggle lives on the optimiser page only
(default **slows (VFD-hold)**, the fair comparison above); the overview page's card
always shows the default, so the two pages can never disagree unless an engineer has
deliberately toggled the optimiser's assumption. Unlike the rev-9 headline, this one
is **static** (the three canonical decks above, not re-priced live) — the "Your
prices" panel still re-prices the overview result strip's own net-cash cells
in-browser, but no longer rewrites the recommendation card's headline text.

**"Your prices"** is a collapsed-by-default panel on the overview page (linked from
the recommendation page, `#yourPrices`) with three inputs, pre-filled at the base
case (the FY25 deck, discount 0.15): diesel price ₹/L, bulk discount %, oil
realisation ₹/bbl — plus four preset buttons, **"OIL FY25 realisation ($78.09)"**,
**"FY26 planning floor ($65)"**, **"Net of royalty + cess (~₹3,600)"** and **"Bulk
diesel discount (0.30)"** (`OIL_PRICE_PRESETS`/`DIESEL_DISCOUNT_PRESETS` in
`core.js`, mirroring `params/field_params.json economics.oil_price_presets` /
`.diesel_discount_presets`). On change (or *Reset to base case*), `core.js`'s
`marginIncrementalAtPrices()` recomputes the baseline and recommended INCREMENTAL
margins **in-browser**, replicating `twin/cycle.py`'s `summary()` /
`_incremental_economics()` formula exactly:

```
revenue        = (oil_total_m3 × bbl_per_m3) × oil_price_inr_per_bbl
steam_cost     = steam_t × (hsd_kg_per_t_steam / hsd_density_kg_l) × diesel_price × (1 − bulk_discount)
margin_gross   = revenue − steam_cost − fixed_cost_inr_per_cycle
margin_w_opex  = margin_gross − power_cost_inr − opex_fixed_inr
```

then, **rev 13:** if `summary.cold_well_economic === false` (the cold well is
mechanically SHUT IN under the policy convention — a physics fact, not a price-
dependent one, at every baked point today), `margin_incr = margin_w_opex / window_days`
directly; otherwise the old price-dependent cold-cash formula applies:

```
cold_cash_day  = cold_rate_m3d × (oil_price_inr_per_bbl × bbl_per_m3) − cold_electric_kWh_per_day × electricity_inr_per_kWh − opex_inr_per_day
cold_net       = cold_cash_day × window_days, if cold_cash_day > 0, else 0
margin_incr    = (margin_w_opex − cold_net) / window_days
```

`fixed_cost_inr_per_cycle` (₹15 lakh, rig/workover), the fixed daily opex
(₹5,000/d), the electricity tariff (₹8/kWh), the cold well's own rate/power
(`cold_rate_m3d`, `cold_electric_kWh_per_day` — physics, well-level constants) and
`bbl_per_m3` are **not** "Your prices" inputs; they stay constants, exactly like
`fixed_cost_inr_per_cycle` did in rev 5. The GROSS re-pricing function
(`marginAtPrices()`) is kept for the "gross" reporting rows. Verified to the rupee
against `REF_SUMMARY`/`OPT_SUMMARY`'s baked `margin_incremental_inr_per_cycle_day`
at base-case (FY25) prices, and at the $65 / net-of-levies decks against
`OPT_SUMMARY_FY26_INCREMENTAL` / `OPT_SUMMARY_LEVIES_INCREMENTAL`.

What is physics and what is re-priced:

| | source | changes with "Your prices"? |
|---|---|---|
| `oil_total_m3`, `steam_t`, `days_total`, `window_days`, `cold_rate_m3d`, `power_cost_inr`, `opex_fixed_inr`, `cold_well_economic` | baked twin output (`REF_SUMMARY`/`OPT_SUMMARY`/`OPT_APPLIED`) | never — these are the physics |
| diesel price, bulk discount, oil realisation | the panel (including the four named presets), persisted in `BUS` under `prices` (`localStorage`, wrapped in try/catch; absent ⇒ base case) | yes |
| the recommended set-points themselves (1,000 t / 10 d / 89 kgf/cm² / 64-in / 0.60 m³/d backstop / 4.5 spm start, VFD-hold) | the true-physics 6-D + policy grid optimum, computed once at base-case (FY25) prices | **never** — the optimiser is not re-run |

A value recomputed away from the base case is tagged "at your prices"; at the base
case it reads "at OIL's FY25 realisation" — never silently identical text with a
different number behind it. The optimiser page's recommendation table re-prices
only the **twin re-run** margin rows (pure physics + the formula above, both gross
and incremental); the **surrogate prediction** rows are ML outputs already tied to
base-case prices and are left alone, so the rows never quietly disagree about which
prices they used.

### 7.3 Calibrate from field data (Model basis, 26 Sep 2026; refreshed 27 Sep, rev 13)

Answers the judge question "what happens when OIL gives you real data?" —
`twin/calibrate.py`'s ingest → recalibrate → re-recommend loop, added to the Model
basis page after Uncertainty. `bl_delta_factor` is sourced physics (physics
v3) and is not in the default free set — `twin/calibrate.py`'s
`DEFAULT_FREE` is `(formation_water_cut, aof_ref_m3d, thickness_m)` (rev 12: the key
is `formation_water_cut`, not the old constant `water_cut`, since the water-cut
STATE model reads that parameter). With `bl` fixed, `formation_water_cut` is
identified ALONE, even though its Jacobian-implied correlation against
`aof_ref_m3d`/`thickness_m` stays high (0.97–0.999) — high correlation here means
"the data move these together", not "unrecoverable"; `thickness_m` is the
weakest-identified of the three (recovered only to within ~11% in the demo, vs ~1%
for `aof_ref_m3d` and ~5% for `formation_water_cut`). Two panels:

- **Demonstration** — baked from `ml/models/calibration_demo_report.json` into the
  `CALIB_DEMO` constant in `core.js` (plus `CALIB_DEFAULTS`, the twin's un-calibrated
  module constants, and `normalizeCalibResult()`/`calibIdentTag()`, shared with the
  live path below). Runs `twin/calibrate.py`'s fit on
  `data/external/pseudo_real_cycles.csv` — **8 synthetic cycles, 3 fictional wells,
  NOT field data** (`data/external/SOURCE.md`) — and shows: a "what the fit
  recovered" table (before/default, fitted, hidden truth, and an identifiability tag
  derived from the report's own `correlated_pairs`, not hard-coded — `✓ well
  identified` / `~ partly identified` / `✗ only as a ratio`); a plain-language note
  on the `formation_water_cut`/`aof_ref_m3d`/`thickness_m` correlations (only fully
  separable with a downhole temperature or pressure log — on the OIL data request)
  plus any other pair the correlation matrix flags the same way; the RMSE fit-quality line;
  a before → after calibration recommendation table (`ml/recommend_physics.py` grid
  search, objective = incremental margin/cycle-day, no ML
  surrogate, soak fixed at 10 d); and an observed-vs-simulated oil scatter (with a
  1:1 reference line) plus a residual strip, both coloured by well, reusing the
  page's chart theme/palette (`chartTheme()`, `CFONT`, `M()`).
  **Regenerate:**
  ```
  python -m twin.generate_pseudo_real
  python -m twin.calibrate data/external/pseudo_real_cycles.csv --out ml/models/calibrated_params.json --report ml/models/calibration_demo_report.json
  ```
  then re-copy `hidden_truth`, `recovered_vs_truth`/`fitted_params`, `bounds`, `rmse`,
  `identifiability`, `residual_table` and `recommendation_before/after_calibration`
  into `CALIB_DEMO` in `core.js`.
- **Use your own data** — a `.csv` file input plus a **Download template** link
  (`../data/templates/observed_cycles_template.csv`, a plain relative path so it
  resolves from `file://` with no build step) and a plain schema list
  (`well_id`, `steam_t` (t), `soak_days` (d), `spm`, `oil_m3` (m³), `produce_days`
  (d) required; `cutoff_m3d`, `peak_oil_m3d`, `sor` optional; minimum 3 cycles —
  `twin.calibrate.REQUIRED_COLUMNS`). In **MOCK**, the CSV is parsed and validated
  in-browser (`parseCsvSimple()` — a plain split, no quoting support, matching these
  simple numeric files), shows a row-count + preview table, and a notice that
  fitting itself needs the physics server. In **live API** mode (`MOCK = false`),
  *Calibrate* `POST`s the raw file as `multipart/form-data` to `/calibrate` and
  renders the SAME three blocks from the response via `normalizeCalibResult()` —
  which also handles the one real difference: `/calibrate` returns only an
  **after**-calibration recommendation (no default-params baseline is re-run for a
  real upload), so the before → after table falls back to a single "Calibrated
  recommendation (after)" row with a note pointing back at the worked demo above,
  and the hidden-truth column reads "not applicable — real data". A **Load
  calibrated recommendation into Simulator** button then stages the after-
  calibration set-points into `BUS` (`{steam_t, soak_days, cutoff, spm, recId, at,
  provenance:"calibrated"}`, same shape and staging key the optimiser's *Stage
  set-points* uses) and opens the twin console; the console's staged banner
  (`page-console.js`) reads `staged.provenance` and says "staged from a field-data
  calibration" instead of "by the optimiser" so the source is never ambiguous.
  Errors (missing columns, under 3 rows, unreachable server) are shown in plain
  language in the same status line, never a raw stack trace.
- **`?qc=calibcsv`** injects `data/external/pseudo_real_cycles.csv` verbatim as CSV
  text (`QC_CALIB_CSV` in `page-methodology.js`) so the parse → validate → preview
  path can be exercised headlessly, with no file-picker dialog.
- **Plotly on a `plotly:false` page.** `build.js` does not give `methodology.html` a
  `<script>` tag for Plotly (§2 above — the doc-body was entirely tabular before
  this section). Rather than change that per-page flag, the two calibration charts
  load `vendor/plotly.min.js` on demand the first time a chart is actually drawn
  (`ensurePlotly()` in `page-methodology.js`, same vendor-then-cdnjs fallback
  `build.js`'s own `PLOTLY` constant uses) — every other page's byte count and load
  path is unaffected.
- **Overview** carries one line in "Run provenance": *Calibration — default
  constants (no field data yet) · Calibrate →*, linking to `methodology.html#calib`
  with the current language/theme (`updateCalibLink()`, re-run on both language AND
  theme change, since it is a manual `href`, not a `data-xlink`).

---

## 8. Demo controls

**Overview** — read-only. *Open in twin console* and *Review recommendation* carry
the current language and theme across.

**Twin console**
- **rev 13: "Rod-float response" selector** — a `<select>` (Pull after 3 alarm days /
  Slow the pump to hold the limit (VFD-hold), default / Slow, then pull / No float
  response), each with a one-line plain-language explanation (EN + real Hindi) shown
  beneath it. Only VFD-hold is baked to full physics precision (`data.js`); the other
  three options relabel the mechanism (the alarm banner text, the explanation note)
  without changing the baked numbers — a `floatPolicyBakedNote` caveat says so
  whenever a non-default option is picked. The replay banner reads "VFD slows the
  pump — rods held at the limit" while the baked VFD-hold series is at its 2-spm
  floor with FI ≥ 0.55, and "Rods floating — operator pulls the well" at the actual
  pull day (`isDuringVfdHold()`/`isAtFloatOnsetEnd()` in `page-console.js`).
- **rev 12: two more sliders** — injection (wellhead) pressure, 85–97 kgf/cm² (a
  continuous slider, default 91), and stroke length, a `<select>` over the 6 discrete
  API sizes 64–144 in the twin has a physics model for (default 86). Both feed
  `bakedFor()`/`mockSimulate()`/`apiSimulate()` alongside the original four; the live
  `/simulate` endpoint has no stroke/pressure parameters yet, so a live-API run (not
  `file://`) still uses the params' own 86 in / 91 kgf/cm² regardless of these two
  sliders — MOCK (the default, `file://`) is unaffected.
- **Telemetry strip** adds **Water cut** and **Rod-float index** readouts; water cut
  reads "—" on an off-baked (approximate) run, since only the state-model baked
  series carries it. The cycle time-series chart gets a fourth sub-band (floating
  index, plus water cut when the run is baked) between the reservoir/viscosity band
  and the oil-rate band, with a dotted line at the 0.60 alarm threshold, so the
  late-cycle emulsion inversion and float onset are visible on the same chart as
  everything else, not just in the telemetry strip.
- **Rods-floating banner.** At the day the produce-end rule actually fires (the last
  row of a baked run whose `produce_end_reason` is `"float_onset"`), the alarm
  banner's text switches from the generic "Rod floating risk — reduce SPM" to "Rods
  floating — operator pulls the well" (हिन्दी "रॉड फ्लोट कर रहे हैं — संचालक कूप खींच
  रहा है") — since for the recommendation and the baseline alike, floating rods at
  the end of the cycle is now the intended mechanism, not a runaway risk. Both baked
  reference set-points now end this way by default, so a fresh page load already
  shows this banner rather than a hidden one.
- **Computed dynamometer card** now reads its stroke length off the CARD's own
  surface-position range (`cardStrokeM()`), not the single global `DYNO_CARDS.stroke_m`
  (which is only the params' 86-in default) — a rev-9-era bug that would have shown
  the recommendation's 64-in card on an 86-in-wide axis. Plunger diameter in the
  equations panel is the params value, 44.5 mm, not a hard-coded 57 mm.
- **Simulate cycle** — runs the twin at the current set-points and publishes the
  run, **unless** the set-points don't match either baked scenario. An off-baked
  run (e.g. the 12-SPM stress test at otherwise-reference set-points) runs the
  in-browser approximation, stays on the console with an "Approximate run — not
  carried to Overview" chip, and is never written to the shared state — so a
  presenter who demos the alarm and then clicks Overview or Recommendation can no
  longer see it there, and never sees a negative or backwards saving.
- **Play the cycle (14 s)** — sweeps the whole cycle; the cross-section, dyno card,
  risk meter, telemetry **and the alarm** all follow the replay frame. Drag the
  cursor grip on the chart to scrub to any day.
- **Try high speed (12 SPM)** — one click to drive the rod-floating alarm (an
  approximate, off-baked run — see above).
- **Reset** — back to the reference set-points.
- **ACK** on the alarm banner silences the pulse and tags it `ALM-02 · ACK`. The
  banner is fixed to the foot of the viewport, so nothing reflows when it fires.

**Recommendation (optimiser)**
- **rev 13: "Compare against a baseline that…" toggle** (`<select>`: slows (VFD-hold,
  default, the fair comparison) / pulls at the first alarm / does nothing about
  float) — re-renders the recommendation card's headline delta, second line and
  win-rate against `OPT_RESULT.fairGain[policy]`/`UQ.decks.*.pGtBaselineSamePolicy`
  without re-running the search. The overview page's card always uses the default,
  so the two pages never disagree unless an engineer has deliberately toggled this
  (not persisted across page loads).
- **Auto-runs on load.** An engineer opening the page wants the answer, not an
  empty page with a button — so unless `?demo=1` or a `?qc=` hook is present, and
  there is no recommendation already in this session's state, the search runs
  immediately and the recommendation card, constraint report and uncertainty
  block are all visible without a click.
- **`?demo=1`** keeps the old idle "presenter click" state — the note plus
  **Run optimiser** button — for a presenter who wants to narrate the search
  happening live.
- **Stage set-points → Confirm** — two-stage and audited; writes to session state
  and prints `Applied by operator · HH:MM IST · REC-YYYYMMDD-nn · run SIM-…`. The
  confirm prompt and every surrounding label say "check in simulator", never
  "controller" or "applied to the well" — nothing here has a SCADA link.
- **Optimisation history** starts empty and is written only when the optimiser is
  actually run. Nothing is pre-populated. Its Baseline/Recommended columns log the
  same INCREMENTAL margin/cycle-day (over cold production) as the headline and the
  recommendation table, never gross; the old gross figure is a title-attribute
  aside, and any row written before this convention shows "—" rather than a
  gross number under the "Incremental" header.

## 9. URL parameters (demo / QC)

| param | effect |
|---|---|
| `?theme=light` \| `?theme=dark` | force a theme |
| `?lang=en` \| `?lang=hi` | force a language |
| `?autoreplay` | console: start the replay once the first simulation lands |
| `?qc=replay` | console: same, for a mid-replay capture |
| `?qc=alarm` | console: run the stress test so the alarm state renders |
| `?qc=loadstaged` | console: load staged set-points and re-simulate |
| `?qc=cardcsv` | console: inject a baked card's surface CSV into "Check a measured card" and classify it — no file-picker dialog |
| `?qc=optimized` | optimiser: run the search |
| `?qc=staged` | optimiser: run, then stage and confirm |
| `?qc=calibcsv` | methodology: inject the pseudo-real demo CSV into "Use your own data" — parse/validate/preview with no file-picker dialog |
| `?demo=1` | optimiser: suppress auto-run, keep the idle "presenter click" state |

Headless QC command used for this build:

```
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu ^
  --user-data-dir=<tmp> --hide-scrollbars --force-device-scale-factor=1 ^
  --screenshot=<abs.png> --window-size=1600,2400 --virtual-time-budget=6000 ^
  "file:///.../dashboard/index.html?theme=dark&lang=hi"
```

Keep the same `--user-data-dir` across two runs to exercise the cross-page state
hand-off; use a fresh one to check the empty-store boot path. Under
`--virtual-time-budget` the 14-second replay fast-forwards, so a mid-replay capture
needs a budget of roughly 4,000 ms; 6,000 ms lands on the settled end state.

---

## 10. What changed from v3, and why

The verdict on v3 was that it still read as AI-made. The causes were structural,
not decorative, and all four are addressed:

1. **One infinite-scroll page of stacked cards → four pages with a real app bar,
   active states, breadcrumb/status bar and cross-page state.** Real products have
   navigation, and a page whose job is "everything" has no job.
2. **Dark-with-neon-accents → a light institutional default.** White ground, navy
   chrome, hairline rules, 2 px radii, no glows, one accent used for one thing.
   Dark survives as an explicitly labelled control-room option.
3. **Card grids of loose KPI tiles → ruled tables and definition lists.** Anything
   that is a set of paired numbers is now a table with units in a column and values
   left-aligned in `tabular-nums`. The optimiser page carries no chart at all,
   because everything on it was already tabular. The product has exactly one chart
   per page that needs one.
4. **Decorative uniformity → density and difference.** 13 px working type, 5 px
   table row padding, a 46 px app bar, a 28 px status bar, and a motion budget of
   three: the replay cursor, the phase-gated pumpjack, and the alarm.

Content changes in the same pass: the economics were re-founded on OIL's own diesel
burn and re-stated per cycle (§7.1); a constraint report was added, including the
honest "at lower bound" flag on soak period; the surrogate residual against the twin
is printed; the methodology page states what has *not* been validated and what would
have to happen to fix it; and the pay zone is named (Jodhpur sandstone,
Bikaner–Nagaur basin) rather than labelled generically.

---

## 11. Re-baking after physics changes

Run `.venv\Scripts\python.exe` with `twin.cycle.simulate_css_cycle(...)` +
`summary(...)` at the two settings in §6, round to the same precision, and replace:

- the `BAKED.reference` / `BAKED.optimized` JSON blobs in `src/data.js` — include the
  Tier-1 extra columns (`spm`, `fillage`, `v_fall_ms`, `heated_radius_m`, `uplift`,
  `pump_limited`), not just the original 10 SPEC columns, plus the Economics v2
  (rev 8/9) incremental/opex/corrected-energy keys (`SOR_incremental`,
  `oil_incremental_m3`, `margin_incremental_inr_per_cycle_day`,
  `margin_with_opex_inr_per_cycle_day`, `electric_kWh_per_m3`, `window_days`,
  `opex_inr`, `cold_rate_m3d`, …) in the `summary` block;
- `REF_SUMMARY`, `REF_INPUTS`, `OPT_SUMMARY`, `OPT_APPLIED` in `src/core.js`
  (the summaries the overview and optimiser pages use without loading the series) —
  include `margin_inr_per_cycle_day` (gross) alongside the original six summary
  keys, AND the incremental/opex/window keys `marginIncrementalAtPrices()` needs
  (`SOR_incremental`, `oil_incremental_m3`, `margin_with_opex_inr_per_cycle_day`,
  `margin_incremental_inr_per_cycle_day`, `electric_kWh_per_m3`, `window_days`,
  `opex_fixed_inr`, `power_cost_inr`, `cold_rate_m3d`);
- `OPT_RESULT` in `src/core.js` from `ml/optimize.py`'s `best_settings(params,
  fixed={"soak_days": N})` (or whatever dimensions are fixed at the time) —
  **rev 9:** if the surrogate's raw argmax differs from the true-physics grid
  optimum (`ml/recommend_physics.py`) by more than ~₹300/cycle-day incremental,
  use the physics-grid point (rounded to operator increments and re-verified) as
  the canonical `OPT_APPLIED`/`OPT_SUMMARY` instead, and carry the rejected raw
  surrogate point in `OPT_RESULT.surrogate_raw` for the optimiser page's honesty
  note;
- `BASELINE_PUBLISHED` and `SURROGATE` in `src/core.js` if the published-practice
  baseline or `ml/` retrains change (`SURROGATE` now carries `oil_r2`/`oil_r2_overall`,
  `sor_r2`/`sor_mae`, `margin_r2`/`margin_mae` (INCREMENTAL, in-envelope + overall),
  `margin_gross_r2`/`margin_gross_mae`, `float_auc`/`float_acc` — read them from
  `ml/models/metrics.json`, not by hand);
- `ECON` in `src/core.js` if the fuel basis, the price deck, or the published CSS
  job count changes — **rev 9:** also `OIL_PRICE_PRESETS` (mirrors
  `params/field_params.json economics.oil_price_presets`) and the
  `opex_inr_per_day`/`electricity_inr_per_kWh`/`cold_electric_kWh_per_day`
  constants `marginIncrementalAtPrices()` reads;
- `UQ` in `src/core.js` from `ml/models/uq_summary.json` — **rev 9:** now baked as
  TWO decks (`python ml/uq.py` runs both and writes `uq_summary.json` with the FY25
  deck at top level and `decks.{fy25_realisation,fy26_floor}` alongside); copy both
  decks' `bands`/`probabilities`/tornado into `UQ`/`UQ.decks` and the model-basis
  page's two band tables;
- `RANGES` (and, if the console's SPM slider still needs to demonstrate the alarm
  beyond the optimiser's own search band, `SPM_SLIDER`) in `src/core.js` if
  `params/field_params.json`'s `css`/`srp` ranges change;
- `CALIB_DEMO`/`CALIB_DEFAULTS` in `src/core.js` from
  `ml/models/calibration_demo_report.json` (regenerate per §7.3) —
  `bl_delta_factor` is fixed/sourced, not fitted; only `formation_water_cut`,
  `aof_ref_m3d`, `thickness_m` are free (rev 12: the hidden-truth key is
  `formation_water_cut`, not the old `water_cut`);
- `DYNO_CARDS` in `src/dyno-data.js` — re-run
  `.venv\Scripts\python.exe -m twin.dyno --bake ml/models/dyno_cards.json` and
  re-export the JSON into that file verbatim (see §6 and the file's own header
  comment); also update `DYNO_SCENARIO_SETTINGS` in `page-console.js` and
  `twin/dyno.py`'s own `BAKE_SCENARIOS` if the baseline/recommendation
  steam_t/soak_days/cutoff change.

Then `node dashboard/build.js`. The four pages read the same constants, so a value
changed in one place cannot disagree with itself on another page. Grep the built
HTML for any literal from the previous bake before calling a re-bake done — see
`docs/model-improvement/TIER1_PROGRESS_LOG.md` §5b/§6 for the rev-5 example and its
grep list.

**rev 9 re-bake grep list** (must NOT appear in the built HTML, except in an
explicit history/superseded line): `7,893`, `7893`, `2,739`, `2738`, `3.81` (bare,
old SOR), `3.754`, `1,700 t`, `0.85 m³/d` (as a live set-point, not a history
mention), `5,154` (old headline delta), `4,840` (only valid as the named FY26-floor
preset value, never as the default/base-case price), `57/57`, `60/60`, `rev 5`
(as an ACTIVE provenance/version string — historical "physics rev 5 (26 Sep)" notes
describing a past change are fine), `−₹1,201`, `−23,311` (old UQ recommended p50/p10
at rev 5). Verified clean by headless Edge + grep, 27 Sep 2026.

**rev 12 re-bake grep list** (must NOT appear in the built HTML, except in an
explicit history/superseded line): `1,600 t` (as a live set-point), `0.70 m` (as a
live cutoff), `4,423`, `5,147` (old rev-9 headline numbers), `2,739`, `7,893` (rev-8
numbers), `116` / `116/117` (old test count), `127/128` (an even older count),
`rev 9` / `rev 11` (as an ACTIVE provenance/version string — historical notes
describing a past change are fine), `late_cold` (as an active scenario key — the
explanatory "was late_cold" mention in the DYNO_CARDS header comment and the tests
table is fine), `CO₂ avoided` / `Diesel not burned` (as the OLD result-strip TILE
labels — the phrase survives correctly in the per-cycle DETAILS table, which is a
different, still-accurate use), `57 mm` (the plunger diameter is 44.5 mm), `₹₹`
(a doubled currency sign). Verified clean by headless Edge (`--dump-dom`, 4 pages ×
EN/HI, plus `?qc=alarm`, `?qc=staged` → `?qc=loadstaged`, `?qc=calibcsv`,
`?qc=cardcsv`, `?qcprice=retail`) + grep, 27 Sep 2026 — see the cascade rev-12
commit for the exact grep output.

**rev 13 re-bake grep list** (must NOT appear in the built HTML, except in an
explicit history/superseded line): `4.35` / `3.19` as bare, ACTIVE SOR values (the
pull-policy baseline's `SOR_pull: 4.35` and numeric substrings inside baked JSON are
fine — checked by context, not a bare substring match), `+₹9,574` / `+Rs9,574` as the
ACTIVE headline (the rev-12 comparison survives correctly as a labelled second-line
alternate, "+₹12,917"/"+₹2,622" — see the rev-13.1 list below for why not "−₹3,865" —
never as the primary card figure), `7,973` /
`22,040` (old rev-12 absolute margin figures), `1,000/0.60/3/64/85` or `3.0 spm` /
`85 kgf/cm²` as the CURRENT recommendation's own set-point (85 kgf/cm² survives only
as the rejected-by-injectivity honesty note), `236` / `236/238` (old test count —
now `263`/`263/265`), `rev 12` (as an ACTIVE provenance/version string — historical
notes describing a past change are fine; `Physics rev 12`/`Revision 2.4` as the
PRINTED page provenance must not appear), `62 %` / `32 %` (the old spm/stroke gain
decomposition — now stroke 57% / cutoff 30% / steam 11%), `pull after 3 alarm days`
as the DEFAULT/only policy (the console's selector default is now VFD-hold; "pull"
survives correctly as one of four selectable options and as the params.json default
policy note), `0.034` unlabelled (must always carry which deck/metric it is), `₹₹`
(a doubled currency sign). Verified clean by headless Edge (`--dump-dom`, index /
console / optimizer / methodology × EN/HI + EN/dark) + grep + a Node `new Function()`
syntax check on every `src/*.js` file, 27 Sep 2026.

---

## 12. rev 13.1 — stress-test isolation, policy-aware constraints, physics-grid
labels, toggle fix, card/table consistency (26 Sep 2026)

A second technical re-score (`docs/model-improvement/TIER1_PROGRESS_LOG.md`, panel
score 66/100) found the rev-13 physics and docs materially improved but the DASHBOARD
itself lost ground on four fronts. This pass fixes all four, plus the stale/cosmetic
items the same re-score flagged:

1. **`bakedFor()` (`src/data.js`) now matches on every control, including `spm` and
   `float_policy`.** Before this fix, the 12-SPM stress test (and any non-default
   "Rod-float response" pick) silently resolved to the 5-spm/VFD-hold baked reference
   series — labelled "baked twin output" and, because it counted as baked, published
   to the Overview as the run on the books. It now correctly falls through to the
   in-browser approximation and is never published (`page-console.js`'s
   `isApprox`/`saveRun()` gate, restored to how it read before this regression).
2. **The console's "Rod-float response" selector now drives the approximate model.**
   `mockSimulate()` (`src/page-console.js`) gained a policy branch: `pull` ends the
   cycle 3 days after the float alarm first fires; `vfd_hold`/`vfd_then_pull` throttle
   the EFFECTIVE spm down each produce day to hold the floating index at 0.60 (to a
   2-spm floor, or half the requested speed for `vfd_then_pull`); `none` is unchanged.
   `apiSimulate()` now also sends `float_policy` on the live `/simulate` call —
   `api/routers/simulate.py` does not declare or read it yet, so a live-API run still
   simulates under the params' own default policy regardless of the selector; FastAPI
   silently ignores an undeclared query parameter, so this costs nothing today and is
   forward-compatible. The stress-test button itself always demonstrates the RAW,
   uncontrolled risk (policy `none`) regardless of the selector's current value — that
   is the one thing "Try high speed (12 SPM)" has always promised, and leaving it on
   whatever the operator last picked could silently hide the alarm behind a VFD policy
   that holds the line.
3. **The optimiser's constraint report and the console's "not achievable"
   strike-through are now policy-aware.** Holding the floating index at 0.60 by design
   (VFD-hold/`vfd_then_pull`) is not a violation of the rule — it is the rule. Both
   read "held at limit (by design)" instead of a red VIOLATED badge when the policy is
   one of the VFD ones and FI stays under 1.0 (full carrier-bar separation) / the
   alarm-day count stays at or under the rule's own 3-day limit; a genuine breach of
   either still reads VIOLATED.
4. **"ML" labels that described the wrong decision engine are renamed to what actually
   decides** — the true-physics 6-D + policy grid (12,936 simulations, ~3 min), not the
   XGBoost/Bayesian-search emulator, which is kept only for what-if speed and
   uncertainty. Changed, EN + HI: "ML optimum" → "Physics-grid optimum"; "ML-optimised
   (as applied)" → "Physics-grid optimum (as applied)"; "ML set-points applied"/
   "ML-optimised set-points applied" → "Recommended set-points applied"; the overview's
   provenance row and SOR-chart footnote ("Bayesian search, 60 calls…"/"ML-optimised
   …") and the footer's data-lineage line ("rev 12 → 3,000 LHS cycles → XGBoost
   surrogate → Bayesian search") → "12,936-plan physics grid (~3 min); ML emulator
   (XGBoost) for what-if / uncertainty only". The optimiser page's `recMeta` line
   ("… · 60 surrogate evaluations") is the same fix. The Surrogate/UQ *tables*
   themselves are untouched — they correctly describe the emulator's own training and
   search configuration under an explicit "Surrogate" heading, never claiming to be
   the decision engine.
5. **Baseline-policy toggle wording and figures.** "Pulls" mode no longer says "run
   the same way" (it explicitly doesn't); it now reads "vs a baseline that pulls at
   the first alarm (mostly the operating rule, not the set-point)". "Does nothing"
   mode is now **+₹2,622** (was **−₹3,865**, WRONG — see the box below), with "we do
   not price rod failures". The "where the gain comes from" decomposition line is now
   policy-aware: `vfd_hold` keeps the 3-lever (stroke/cutoff/steam) split;
   `pull` shows the dominant operating-rule-switch lever (68%) from
   `ml/models/gain_decomposition.json`'s per-policy Shapley split; `none`'s 6-lever
   split has a negative, dominant policy term and a cutoff share over 100% (switching
   the operating rule costs oil there; the other levers more than compensate) — a
   3-term percent breakdown would misstate that, so the line is hidden for `none`
   rather than shown wrong. The SOR line now also moves with the toggle (each
   policy's own baseline SOR, matching the headline's own "steam per m³ oil" figure),
   and the table delta already did (it was never wrong).

   > **The −₹3,865 bug, precisely.** `OPT_RESULT.fairGain.none` (`src/core.js`) held
   > the "best rec within that policy" row of `TIER1_PROGRESS_LOG.md` §12.6 — a
   > DIFFERENT, more radical float-safe plan (1,000/89/1.45/64/3, policy `none`)
   > compared against a baseline that also does nothing about float. That is not what
   > the toggle is for: it asks what the SAME canonical recommendation (the one on the
   > card, staged into the console) would gain against a baseline operated that way —
   > the "mixed" row of §12.6, **+₹2,622** (**+₹3,484** at $65, **+₹4,412** net of
   > levies). Fixed to use that row; the −₹3,865/−₹2,513/−₹1,057 figures must not
   > appear on this dashboard again.
6. **Card vs table consistency, one source of truth from the baked summaries.**
   - The overview card and the per-cycle details table already shared one `AV`
     (`cycleAvoided()`) constant and always agreed (161 t steam / 13,788 L diesel /
     36 t CO₂, iso-oil basis) — no bug there once traced through; the apparent
     "25,662 L / 67 t" a reader can get instead is the PLAIN difference of the two
     cycles' own absolute steam burn (1,300 − 1,000 t) × the fuel constants, a
     different, narrower question ("how much less steam did this cycle use") than the
     iso-oil "how much steam would it have taken the old way to make the SAME oil"
     the card/table both actually answer — the "Fuel and carbon, this cycle" group
     that carries those two absolute numbers was already labelled as absolute burn,
     not "avoided", and is left as is.
   - **Tile ("+₹3,318") vs card ("+₹3,332") was a real bug**, in
     `marginAtPrices()`/`marginIncrementalAtPrices()` (`src/core.js`): both were
     missing `twin/cycle.py`'s `steam_cost_inr = steam_t × steam_cost_inr_per_t(econ)
     × fuel_factor` — a small (~0.04%) wellhead-pressure/steam-quality correction that
     is 1.0 at the baseline's 91 kgf/cm² but ~0.9996 at the recommendation's 89
     kgf/cm². Fixed two ways: the formula now multiplies by `summary.steam_fuel_factor`
     (so a genuinely re-priced "Your prices" figure is now correct to within a rupee
     instead of ~₹14 off), AND, at the untouched base case specifically, both
     functions now use the BAKED `summary.steam_cost_inr` verbatim (full precision)
     rather than recomputing from a 4-decimal-place constant — so the tile is now
     bit-for-bit identical to the card at the default view, not merely close.
   - The "−-13.9%" double-sign typo (`page-overview.js`, the SOR-drop sub-line and the
     "How to read the headline" note) was a hand-typed "−" in front of `fmt()` on an
     already-negative number; both now use `signed()`, which supplies its own sign.
7. **Stale bits.** Plunger diameter (`page-console.html`) was still `57 mm`
   (params value is `44.5 mm`, and the equations panel itself already read 44.5 —
   this was the one remaining hard-coded leftover). The footer's physics rev/date are
   now driven by two constants, `PHYSICS_REV_SHORT`/`BUILD_DATE` (`src/core.js`),
   written into the footer's own spans by `bootChrome()` on every page load, instead
   of hand-typed HTML — bump those two constants on every re-bake/rebuild and the
   footer cannot go stale on its own again. "Published-practice baseline" survived in
   two `page-optimizer.js` comments and one `page-methodology.html` paragraph after
   the term itself was retired dashboard-wide; changed to "assumed baseline" for
   consistency (none of the three were user-visible strings the panel would have
   actually seen, but they contradicted the product's own naming). The Surrogate
   table's "Design of experiments"/"Label generation" rows (`page-methodology.js`)
   still said "physics rev 12" for the SAME 600-sample, float-policy-included
   retrain its own next row ("Classifier AUC") already correctly calls "rev 13" —
   fixed to match. (The "Upload records → twin learns" wording the re-score flagged
   lives in `ppt/`, outside this pass's `dashboard/src/**` scope.)
8. **The offline card checker (`clfNearestBaked()`, `page-console.js`) was checked,
   not obviously broken, and hardened anyway.** Computed directly (Node,
   `dyno-data.js`'s own baked cards): feeding `?qc=cardcsv`'s injected curve — the
   baseline's own "mid" card — back through parse → normalise → resample → nearest-of-8
   returns that SAME card at distance 0 ("fluid_pound", fillage 30%), which is that
   card's own, correct, day-126.6 transient fillage — a different, smaller quantity
   than the whole-cycle `mean_fillage` (85%) shown elsewhere on the console; the two
   were never the same number, so this was not the mismatch it looked like. What the
   fallback WAS missing was a floor: nothing stopped a genuinely novel (non-baked-
   shaped) curve from being forced onto whichever of the 8 baked cards happened to be
   least-bad. `clfNearestBaked()` now also returns its match distance, and
   `runDynoClassify()` refuses to label a curve whose nearest baked match sits above
   `CLF_MAX_MATCH_DIST` (calibrated off the 8×8 baked-card distance matrix), showing
   "offline check unavailable — start the API for the classifier" instead.

**rev 13.1 re-bake grep list** (must NOT appear in the built HTML, except in an
explicit history/superseded line): `−₹3,865` / `-₹3,865` / `−Rs3,865` as the ACTIVE
"does nothing" toggle figure or headline alternate (it now reads `+₹2,622`; the old
figure survives ONLY inside an explicit "rev 13.1 correction"/history note, like this
file's own §12 above), `ML optimum` / `ML-optimised` / `ML set-points applied` /
`ML-optimised set-points applied` as an ACTIVE label (must read "Physics-grid
optimum"/"Recommended set-points applied"), `Bayesian search` describing the
DECISION engine (surviving correctly only inside a `Surrogate`-headed table row or
comment describing the emulator's own search config), `60 surrogate evaluations`,
`57 mm` (plunger; must be `44.5`), `physics rev 12` / `Rev 2.4 (v4, physics rev 12)`
/ `27 Sep 2026` as the PRINTED footer provenance (must read `rev 13` / `26 Sep 2026`,
now sourced from `PHYSICS_REV_SHORT`/`BUILD_DATE` in `src/core.js`, not hand-typed),
`published-practice baseline` (renamed to `assumed baseline` everywhere it survived),
`−-13.9` / `−-` (a doubled sign), `+₹3,318` beside a `+₹3,332` card on the same page
(tile/card must now agree to the rupee at the base case). Verified by headless Edge
(`--dump-dom`, 4 pages × EN/HI, EN/dark, 1600/1024) + grep, 26 Sep 2026.
