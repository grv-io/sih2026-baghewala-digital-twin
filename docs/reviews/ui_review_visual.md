# Visual Design Review — Baghewala Digital Twin Dashboard

**Target:** `dashboard/index.html` (single file, 1,910 lines)
**Reviewed at:** 1600×2400, 1920×2600, 1280×2200 (headless Edge, virtual-time 9s)
**Reviewer stance:** senior visual/product design critic. Brutal on purpose.
**Date:** 13 Sep 2026

---

## 0. Verdict in one paragraph

The engineering underneath this is real and the physics reads as real. The **surface does not**. What a judge sees in the first three seconds is: five identical rounded cards, evenly spaced, each with an identical uppercase grey header strip, filled with unmodified Plotly output, topped by a scrolling marquee and a full-width animated tricolour stripe, with the single biggest number on the page being `0.54` — the *floating index*, which is not your product's claim. Your product's claim, **−41.3% SOR**, is rendered at 12.5px inside a green stadium pill at the bottom of a table. That inversion, plus the uniformity, plus the decoration-without-information, is exactly what "bahut AI lag raha hai" means. It is not a vibe problem; it is a **hierarchy, rhythm and restraint** problem, and every instance is listed below with a line number.

The "cramped" feeling is also diagnosable and it is *not* mainly "gaps too small". It is that **every gap is 16px**. Header→ticker 16, ticker→controls 16, controls→grid 16, grid gap 16, panel→panel 16. When every distance is equal, nothing is grouped, the eye gets no rest points, and a page reads as a dense wall even at 1920px. Meanwhile the actual text is 11–13.5px against a declared `body{font-size:15px}` that almost nothing inherits — so the page is simultaneously *small-text cramped* and, in the cross-section panel at 1920, *300px of dead void*. Both problems, same root cause: no scale, no system.

The India theming is a sticker, not an identity. A 3px full-bleed saffron/white/green bar with an animated white sweep, plus a "DIGITAL INDIA · MAKE IN INDIA" pill, is the visual equivalent of putting a flag emoji in a filename. Real Indian energy-PSU product design does one thing above all others: **it is bilingual**, in a formal Devanagari-over-Latin lockup, with a title-block/plate structure borrowed from engineering drawings. Section C gives you that, with the actual Hindi strings.

**Counts:** 61 numbered findings — **19 × P0**, 26 × P1, 16 × P2.

---

# A. "AI-generated" tells

Each finding: **verdict → evidence → exact fix.**

### A1. Uniform border-radius everywhere — and eight of them **[P0]**
**Verdict:** The single loudest template tell on the page. Not just "everything is rounded" — everything is rounded *differently*, which proves no one chose.
**Evidence:** eight distinct radii in one stylesheet — `2px` (L85 tricolor), `3px` (L215 range track), `6px` (L647 stamp), `7px` (L243 `.btn`), `8px` (L164 ticker, L388 kpi-tile, L440 opt-note, L606 replay-bar), `10px` (L198 controls, L272 alert, L308 panel, L356 h2), `20px` (L134 badge, L145 status-pill, L450 improvement-tag, L551 phase-chip, L665 sor-delta), `50%` (dots, thumbs, replay button), plus `1.5px`/`2px`/`3px` inline `rx` on SVG rects (L737, L883, L905, L920).
The `20px` stadium pill used five times is the worst offender: stadium pills are the #1 signature of generated UI. Real instrumentation software does not have stadium pills; it has plates and tags.
**Fix — three radii, no exceptions:**
```css
--r-1: 2px;  /* chips, tags, phase-chip, badge, status pill, table accents */
--r-2: 4px;  /* buttons, kpi tiles, inputs, inset boxes, ticker, replay bar */
--r-3: 6px;  /* panels, controls bar, alert banner */
```
Circles (`50%`) survive **only** on the status dot (L151) and the scrub grip (L637). Kill `border-radius:20px` in all five places; kill `7px` and `10px` entirely. Set every SVG `rx` to `1` or remove it.

### A2. Five identical cards, evenly spaced, identical chrome **[P0]**
**Verdict:** The template grid. Same background, same 1px `#30363d` border, same radius, same `18px 20px 20px` padding, same frosted uppercase header strip, same 16px gap. Nothing on the page is more important than anything else *structurally*, so the eye has no entry point.
**Evidence:** L304–311 `.panel`, applied identically to all five `<section class="panel">`; grid gap L302 `gap:16px`; identical `h2` treatment L344–357. Confirmed in all three screenshots — the 1600 shot reads as a spreadsheet of boxes.
**Fix — purposeful density variation.** Three tiers, visually distinct:
- **Tier 0 — result band** (new, see D2): no card at all. Full-bleed on the page background, separated by a 1px rule above and below, 32px vertical padding. Absence of a card *is* the emphasis.
- **Tier 1 — primary panels** (`#panelTimeseries`, `#panelXsec`): `background:#161b22`, `border:1px solid #30363d`, `--r-3`, padding `20px 24px 24px`.
- **Tier 2 — support panels** (`#panelDyno`, `#panelGauge`, `#panelOptimize`): **no border**, `background:#12171e` (one step off the page ground), `--r-2`, padding `16px 20px 20px`. Supporting material should recede, not compete.
Also break the even grid: `grid-template-columns: minmax(0,1.35fr) minmax(0,1fr) 360px` so the time-series column is visibly dominant instead of two equal halves.

### A3. Staggered card fade-up entrance animation **[P0]**
**Verdict:** `panelIn` with `.02s/.08s/.12s/.2s/.3s` delays is *the* motion signature of a generated dashboard. Every AI-built dashboard in 2024–2026 does exactly this. It also actively hurts you: a judge screenshotting or a projector dropping frames sees panels sliding in for 900ms before the data is readable.
**Evidence:** L310 `animation:panelIn .6s ...`, L312–315 the four delay rules, L316–319 keyframes.
**Fix:** Delete `panelIn`, all four delay rules, and the `both` fill. Panels are present at t=0. If you want load feedback, animate **only the data**: Plotly already has `transition:{duration:450}` (L1418) — that's your motion budget, spend it there and nowhere else.

### A4. Decoration-only gradient/glow/shimmer stack — 17 effects, 0 bits of information **[P0]**
**Verdict:** Glow overuse is the second-loudest AI tell, and it costs you the one thing glow should buy: alarm salience. When the header shimmers, the tricolour sweeps, the background drifts, the panel header is frosted, buttons shimmer, thumbs have 3px halo rings in four colours, KPIs flash, and the page has an ambient diagonal-stripe overlay — then when a real alarm glows red, it is just one more glowing thing.
**Evidence (full inventory):** L38–47 `body::before` ambient "steam" stripes; L49–52 `ambientDrift` 34s; L66–78 `header::after` shimmer 6s; L92–102 tricolour white sweep 4.5s; L151–157 `dotBlink`; L220/225 thumb glow rings ×4 accent variants (L502–515); L250/252 button hover glow; L254–264 `btnShimmer`; L278/289–292 alert `pulse-glow`; L284–288 `alertIconPulse`; L321–328 `sirenGlow`; L330–342 `panelComputing` shimmer; L344–357 `backdrop-filter:blur(6px)` glass strip; L398–406 `kpiFlash`; L518–526 `#bgGrid` parallax; L529–538 `alarmVignette`; L645–659 stamp glow + `stampIn`; L676–686 `sparkFly` particles.
**Fix — motion/glow budget of exactly three:**
1. **Alarm** — vignette + red panel border + banner. Keep (L529–538, L321–328). This is the only thing allowed to pulse.
2. **Liveness** — the status dot (L151). Keep, but slow to `3s` and drop the `box-shadow` glow; a 6px dot that fades 100%→55% is enough.
3. **Twin state** — the cross-section flow particles during replay. Keep.
**Delete:** `body::before` + `ambientDrift`, `header::after` + `headerShimmer`, tricolour sweep, `btnShimmer`, `panelComputing`, `kpiFlash`, `sparkFly` + `.spark`, `#bgGrid`, `backdrop-filter` on `h2`, all four thumb glow-ring variants (replace with a 1px `#30363d` ring, no colour). Net: ~110 lines of CSS deleted, and the page instantly reads more expensive.

### A5. The rotated "OPTIMIZED" rubber stamp **[P0]**
**Verdict:** A skeuomorphic rotated rubber stamp with a spring-scale entrance is pure novelty-app. No control-room product has ever shipped this. It also lands *on top of the controls bar*, obscuring the inputs the judge just moved.
**Evidence:** L644–659 `.stamp` (`transform:rotate(-8deg)`, `letter-spacing:0.22em`, `stampIn` cubic-bezier overshoot, green glow), positioned against `.controls{position:relative}` added as an afterthought at L660.
**Fix:** Delete `.stamp`, `@keyframes stampIn`, and L660. Replace the affordance with an honest state change on the controls bar: when optimized settings are applied, add a 2px left border in `--green` to `.controls` and put the text **`Settings: ML-optimised · applied 17:04`** at 12px in the bar's top-right. State, not theatre.

### A6. Scrolling telemetry marquee **[P0]**
**Verdict:** An infinitely scrolling ticker is a "look, it's live!" gesture, not an ops instrument. You cannot read a moving number, you cannot compare two of them, and the mask gradient (L177) clips the leftmost record mid-word — visible in all three screenshots as `⁄01:27 · T_res 80.5°C` and `80.5°C · µ 1577 cP` with the timestamp shorn off. Also: 22s loop × infinite = permanent CPU/compositor churn during a projected demo.
**Evidence:** L160–188, markup L771–779. Screenshot 1600 y≈122; screenshot 1280 y≈201 shows the truncation clearly.
**Fix:** Replace the marquee with a **static last-value strip**: one row, four fixed slots, right-aligned monospace-tabular values that *change in place* with a 200ms colour flash on update — `17:01:47 │ T_res 76.3 °C │ μ 2,037 cP │ SPM 8.0 │ produce │ OK`. Same information, one-tenth the noise, and it is what a real DCS status line looks like. Keep the `TELEMETRY` tag but restyle per A7.

### A7. Badge/chip overuse — 11 pill-shaped objects, 4 of which are decorative **[P0]**
**Verdict:** Badge soup. Three header badges + status pill + phase chip (×2 instances) + improvement tag + sor-delta + ticker tag + replay "CYCLE COMPLETE" chip. Two of the three header badges are pure sloganeering and one duplicates the `<h1>`.
**Evidence:** L753–765 — `SMART INDIA HACKATHON 2026`, `PS SIH26120` (already inside the `<h1>` at L731), `DIGITAL INDIA · MAKE IN INDIA` (unearned; neither programme has any relationship to this deliverable). Plus L766 status pill, L838/849 phase chips, L446–451 improvement tag, L663–670 sor-delta, L171–176 ticker tag.
**Fix:**
- Delete both `Smart India Hackathon 2026` and `Digital India · Make in India` badges. The SIH provenance belongs in the **title block** (C3) as a field, not a sticker.
- Keep `PS SIH26120` but move it into the title block and **remove it from the `<h1>`**.
- Status pill: this is the only one that carries state — make it *not* a pill. `--r-1`, 1px border, `MOCK DATA` in 11px/600/uppercase with a 6px dot. It must look different from decorative tags, because it is the only one that isn't.
- Phase chip: keep (it is genuinely a state tag), but `--r-1` and drop the tinted background — border + text colour only.
- `improvement-tag` and `sor-delta`: both die in D2 when −41.3% is promoted to the result band.

### A8. Glyph/emoji soup — six unrelated character sets used as icons **[P0]**
**Verdict:** `▶` `⚙` `⇩` `⚠` `▼` are Unicode dingbats from five different blocks, rendered at whatever optical weight the fallback font gives them, on mismatched baselines. `⇩` (L1015) is a rare arrow with poor coverage — **it renders as a broken/substituted glyph in the 1600 and 1280 captures** ("ᶀ Apply Optimized Settings"). That is a live rendering bug on the demo machine, not just a taste issue.
**Evidence:** L803 `▶ Simulate Cycle`, L804 `⚙ Optimize Settings`, L1015 `⇩ Apply Optimized Settings`, L809 `⚠`, L1584 `▼ ${pct}%`, L835 `▶` replay button, L839 `press ▶ to replay`.
**Fix:** Delete every dingbat. Use **four inline SVG icons at 14×14, `stroke-width:1.5`, `currentColor`, `stroke-linecap:round`** — play (triangle), tune (two-slider glyph, not a gear), download-apply (arrow into tray), warning (triangle). Draw them yourself in 20 lines; they must all share the same 14px box, 1.5 stroke and 2px optical padding. `▼` in the delta becomes a proper `↓` set in the same SVG family, or better: no icon at all, just `−41.3%` (the minus sign does the work).

### A9. "Everything has a label" syndrome **[P1]**
**Verdict:** The page explains itself to death. Nine explanatory strings that a competent operator does not need, each costing vertical space and adding grey noise.
**Evidence:** L772 `TELEMETRY` tag; L841 `drag the amber cursor to scrub`; L839 `Press play to sweep the twin through the whole CSS cycle`; L846 `(live twin state)`; L970 `(approximate, from peak rod load & floating index)`; L1011 `<th>Recommended Setting</th><th>Value</th>` (a two-column key/value table needs no header); L1557 x-tick `Baseline (mid-range settings)`; L975 `Stroke length: 3.0 m` (a constant, not a measurement); L1023 the 190-character footer.
**Fix:** Delete `drag the amber cursor to scrub` (the grip's `cursor:grab` and `title` already say it), delete the two `<th>`s and rule the table instead, shorten the dyno hint to `approximate`, move `Stroke length 3.0 m` into the panel's title-block metadata line, shorten the x-tick to `Baseline`. Keep `(live twin state)` but as a 11px right-aligned meta, not an inline parenthetical.

### A10. Default Plotly styling remnants **[P0]**
**Verdict:** Four charts, all recognisably "a Plotly figure with a dark paper_bgcolor". The dark theming was applied; the *typography and layout* were not. A judge who has ever used Plotly will recognise it in half a second.
**Evidence, specific:**
- **A10a** L1372 `const FONT = { color, family }` — **no `size`**. Every tick, axis title and legend entry is therefore Plotly's default 12px, at every viewport. At 1920 (screenshot B) the chart text is visibly undersized against the panel; at 1280 it's fine. Charts don't scale.
- **A10b** L1411–1413 uses the deprecated `titlefont` key and Plotly's **default rotated axis titles** — three colour-coded rotated titles on one figure (`Reservoir T (°C)` orange, `Viscosity (cP)` blue, `Oil Rate (m³/d)` green, screenshot A x≈55/825/935). This is the Plotly multi-axis demo, verbatim.
- **A10c** L1412 `type:"log"` with default minor ticks → the y2 axis prints `10k 5 2 1000 5 2 100 5 2 10 5 2` — twelve labels, nine of which are meaningless bare `5`/`2`. Screenshot A x≈795, y 355–535. This is the ugliest single region of the page.
- **A10d** L1413 `yaxis3 {anchor:"free", position:1}` paired with L1410 `xaxis.domain:[0,0.86]` — the classic third-axis hack, which reserves **14% of the widest panel on the page** as an empty gutter (screenshot B, x≈940–1130 is axis furniture only).
- **A10e** L1415 `legend:{orientation:"h", y:-0.2}` — Plotly's default centred horizontal legend with line-swatch glyphs, floating in 40px of its own whitespace below the plot (screenshot A y≈623).
- **A10f** L1459–1460 dyno chart — Plotly prints `0` on **both** axes at the origin, overlapping (screenshot A x≈83, y≈988 shows two stacked zeros).
- **A10g** L1476–1492 — a `type:"indicator"` gauge with default arc geometry, default `[0, 0.5, 1]` ticks and a 30px centred number. The Plotly indicator gauge is, along with the stadium pill, the most instantly recognisable generated-dashboard component in existence.
- **A10h** L1556–1565 — a two-category bar chart at default `bargap`, so each bar is ~28% of the plot width with `textposition:"outside"` numeric labels. Screenshot B: 55% of that panel is empty.
- **A10i** No `hovertemplate` anywhere → default hover boxes reading `(37, 4.82)` with a trace-colour border and Plotly's `<extra>` trace-name box. First thing a judge does is mouse over a line.
**Fix:**
```js
const FONT = { family:'"Segoe UI",-apple-system,Roboto,Helvetica,Arial,sans-serif',
               color:"#8b949e", size: 12 };
const FONT_BIG = { ...FONT, size: 13 };          // apply at innerWidth >= 1600
const AXTITLE  = { ...FONT, size: 12, color:"#7d8590" };
```
- Replace all `titlefont:{...}` with `title:{ text:"…", font:{...}, standoff:8 }`.
- **Kill the third y-axis.** Move Oil Rate into a **second stacked subplot** (`grid:{rows:2, columns:1, roworder:"top to bottom"}`, shared x, heights 0.62/0.38). Reclaim `xaxis.domain` to `[0,1]`. This alone reclaims 14% width and removes two rotated titles.
- Log axis: `yaxis2:{ type:"log", tickmode:"array", tickvals:[10,100,1000,10000], ticktext:["10","100","1k","10k"], showgrid:false }`.
- Legend: `showlegend:false` and draw your own legend in HTML above the chart — three 12px items, 10×2px colour rules, `gap:20px`, left-aligned with the panel title. HTML legends are the single fastest way to stop looking like Plotly.
- Dyno origin: `xaxis:{ ticks:"outside", ticklen:4, tickcolor:"#30363d" }` and `yaxis:{ ...rangemode:"tozero", tickformat:"d" }` with `xaxis.showticklabels` starting at 0.5, or set `yaxis.ticklabelposition:"outside top"`. Simplest: `yaxis:{ range:[0, peak*1.12], dtick:20 }` so the axes don't both label 0.
- Gauge: see D3 — replace with a linear risk bar. If you keep a dial, at minimum `gauge.axis.tickvals:[0,0.4,0.6,1]`, `number.font.size:22`, and `gauge.shape:"bullet"`.
- Bar chart: `bargap:0.55`, `width:[0.42,0.42]`, drop `textposition:"outside"` and put the two values as HTML `<figcaption>`-style labels you control. Or delete the chart entirely (D4).
- Add `hovertemplate` to every trace, ending in `<extra></extra>`, e.g. `"Day %{x}<br>%{y:.1f} °C<extra></extra>"`, plus `hovermode:"x unified"` on the time-series.

### A11. Centred-hero clichés **[P1]**
**Verdict:** Three centring decisions that all say "generated landing page".
**Evidence:** L454 `footer{text-align:center}`; the gauge's centred 30px number in an otherwise left-aligned panel (L1479); L875 the pay-zone caption `text-anchor="middle"` centred under the cutaway; L1557 centred bar-chart category labels.
**Fix:** Everything left-aligns to the panel's content edge. The footer becomes a two-column block (D5). Nothing on an instrument panel is centred except a dial's own numeral.

### A12. No brand mark of any kind **[P0]**
**Verdict:** There is no logo, no wordmark, no monogram, no lockup — just 22px bold system text. That is *the* reason it reads as a template: templates ship without identity, and the absence is what your eye is picking up as "AI".
**Evidence:** L730–733. The only graphic in the header is the pumpjack SVG (L735–750) which is `aria-hidden`, unbranded, and floats unanchored in the middle of the flex row (screenshot B x≈820: a grey clipart rig stranded in empty space; screenshot C: alone at top-right with nothing near it).
**Fix:** Build a real mark — see C3. Short version: a 32×32 monogram plate (the pumpjack silhouette reduced to 3 strokes in a bordered square), then a two-line bilingual wordmark, then a 1px vertical rule, then the client lockup. The pumpjack stops being decoration and becomes the mark.

### A13. Accidental asymmetry read as inconsistency **[P1]**
**Verdict:** Where the page *is* asymmetric, it looks like an oversight rather than a decision — the four KPI tiles have four different anatomies.
**Evidence:** L984 `tileSOR` = label + value. L985–998 `tileOil` = label + droplet icon + value + sparkline. L999 `tileEnergy` = label + value. L1000 `tileDays` = label + value. So one of four tiles has an animated icon (L409–424) and a sparkline (L425–427) for no stated reason; the other three are bare. That is decoration applied where it happened to fit.
**Fix:** Make the anatomy a **rule tied to data**: every KPI that has a time series gets a 24px sparkline (SOR, Oil, Energy all do; Duration does not). No KPI gets a decorative icon — delete the droplet (L988–991, L409–424). Result: three tiles with sparklines, one without, and the difference now *means* something.

### A14. Amber means ten different things **[P0]**
**Verdict:** The accent colour has no semantics, so it has no power. Amber is currently: the brand accent word in `<h1>`, the primary button, the ticker tag, all four KPI values, all five highlighted table values, the reservoir-temperature series, the steam particles, the optimized bar, the scrub cursor, the pumpjack rod, one slider's thumb, and the ticker's label. It is simultaneously "brand", "hot", "primary action", "any number" and "the optimized one".
**Evidence:** 36 occurrences of `--amber`/`#f59e0b` across CSS and JS. Plus four decorative slider accents (L501–515: amber/blue/green/violet) that encode *which control you're touching* — information the label already gives — while `#a78bfa` (violet) is hardcoded four times and **is not a token at all**. `--amber-dim:#b45309` (L17) is declared and **never used**.
**Fix — adopt ISA-101 discipline** (the HMI standard actual process-industry judges know): normal state is low-saturation grey/white; colour is reserved for meaning.
```
grey/white  #e6edf3  — all normal values, all normal process lines
amber       #f59e0b  — thermal/steam domain ONLY (T_res series, steam particles,
                       steam-volume control) + the one primary button
green       #10b981  — improvement / within-limits ONLY (delta, oil rate)
red         #ef4444  — alarm ONLY
blue        #60a5fa  — viscosity series ONLY
navy        #12386b  — structural identity bands (see C)
```
Concretely: KPI values become `#e6edf3` (only the SOR hero stays amber-free and white; the *delta* is green). Table `.hl` values become `#e6edf3` with `font-weight:600`. Delete all four `data-accent` slider colour blocks (L501–515) — one thumb colour, `#8b949e`, filled `--amber` only while `:active`. Delete `--amber-dim`. Add `--violet` as a token or delete violet entirely (recommended: delete).

### A15. Middot-and-em-dash prose **[P2]**
**Verdict:** The writing has the same tell as the layout: everything joined by ` · ` and ` — `. It reads as generated copy.
**Evidence:** `<h1>` (L731) has one em-dash and one middot; subtitle (L732) has six middots; footer (L1023) has six middots in one 190-char sentence; four of five `<h2>`s use an em-dash; the ticker record uses four; the pay-zone caption uses three.
**Fix:** Cap it at **one separator per line**. `<h2>`s become plain noun phrases (`Cycle time series`), with the variable list moved into the HTML legend where it belongs. Footer becomes a structured block (D5), not a sentence. Subtitle becomes a labelled metadata grid (C3), not prose.

---

# B. Compactness and density

## B1. Diagnosis: the problem is uniform gaps, not small gaps **[P0]**

**Evidence:** the vertical rhythm from `<body>` down is `20 → 16 → 18 → 16 → 16 → 16 → 16 → 22` (L32, L62, L84, L166, L200, L274, L302, L454). Six consecutive 16s. Grid gap 16, inter-panel 16, section margin 16 — the eye cannot tell where the command surface ends and the readout surface begins, so it processes the whole page as one dense field. **That is the "cramped" sensation**, and adding 4px to everything would not fix it.

**Fix:** gaps must encode grouping. Target rhythm:

| Boundary | Now | Proposed | Why |
|---|---|---|---|
| page top → identity | 20 | **28** | masthead needs air above it |
| identity → title-block rule | 16+18 | **20** | tight = same object |
| title block → command bar | 16 | **28** | new region |
| command bar → result band | 16 | **24** | related (inputs → outcome) |
| result band → grid | 16 | **36** | biggest break on the page |
| grid column gap | 16 | **20** | |
| grid row gap | 16 | **28** | rows need more than columns, always |
| grid → footer | 22 | **48** | |

## B2. No spacing system exists **[P0]**
**Evidence:** the paddings actually in use are `4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 40` px. Eighteen values, of which `7, 9, 11, 13, 15, 18, 22` are off any grid. Gaps: `5, 6, 8, 10, 12, 14, 16, 22, 24, 48`. Margins: `6, 7, 8, 10, 12, 16, 18, 22`.
**Fix — 4px base, 8px preferred:**
```css
--s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:20px;
--s6:24px; --s7:32px; --s8:40px; --s9:48px; --s10:64px;
```
Rule: `--s1` and `--s3` only *inside* a component; `--s4`+ only *between* components. Nothing may use a raw px value for spacing.

## B3. Body font-size is a lie **[P0]**
**Evidence:** L30 `body{font-size:15px}` — but the only things that inherit it are the slider `output` (L210, explicitly 15px anyway) and nothing else. Actual reading sizes: `8.5, 9, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14`. **Sixteen distinct font sizes** on the page, ten of them below 14px. The user is right that it's cramped: functionally this is a 12px page.
**Fix:** see B5. Body becomes a real 14px, and every 10.5/11.5/12.5/13.5 disappears.

## B4. Line-height 1.4 everywhere **[P1]**
**Evidence:** L31, global, no overrides. At 13px that's 18.2px leading for the header subtitle's two dense lines (L732) — visibly tight in screenshot A y≈53–70. Table rows are 13.5px text + 9px padding = 37px rows (L432–433), tight for an ops table a judge reads across.
**Fix:** `--lh-tight:1.25` (display numerals, KPI values, h1), `--lh-ui:1.45` (labels, chips), `--lh-text:1.6` (body, notes, footer, metadata). Devanagari adds `+0.15` — see C6.

## B5. Proposed type scale **[P0]**

```css
:root{
  --font-ui:"Segoe UI",-apple-system,Roboto,Helvetica,Arial,sans-serif;
  --font-num:"Segoe UI",ui-monospace,"Cascadia Mono",Consolas,monospace; /* tabular */
  --font-deva:"Nirmala UI","Noto Sans Devanagari","Mangal",var(--font-ui);

  /* size / line-height / weight / tracking / case */
  --t-micro:  11px;  /* 1.35  600  +0.08em  UPPER — axis ticks, depth labels, units    */
  --t-label:  12px;  /* 1.40  600  +0.06em  UPPER — field labels, table heads, chips   */
  --t-meta:   12px;  /* 1.60  400  0        sent. — hints, footnotes, title-block values*/
  --t-body:   14px;  /* 1.60  400  0        sent. — table cells, notes, footer          */
  --t-strong: 14px;  /* 1.60  600                                                       */
  --t-title:  15px;  /* 1.30  600  +0.01em  Sent. — PANEL TITLES (not uppercase)        */
  --t-h1:     26px;  /* 1.20  600  -0.01em                                              */
  --t-kpi:    28px;  /* 1.10  600  tabular  — secondary KPI values                      */
  --t-kpi-lg: 40px;  /* 1.05  600  tabular  — the two headline KPIs                     */
  --t-hero:   56px;  /* 1.00  600  -0.02em  tabular — SOR result only, exactly one use  */
  --t-delta:  28px;  /* 1.10  600  tabular  — the −41.3%                                */
}
```
Ten tokens replacing sixteen ad-hoc sizes. **Every number on the page gets `font-variant-numeric: tabular-nums`** — currently only five selectors have it (L211, L395, L435, L548, L618), so the ticker, table headers, chart labels and metadata jitter.

**The single most important change here:** `--t-title` at **15px sentence-case 600** replaces `14px uppercase +0.06em 700` (L344–351). Uppercase-tracked panel titles in dim grey are a generated-dashboard fingerprint; sentence-case semibold in near-white (`#c9d1d9`) reads as editorial and expensive. Compare: `CYCLE TIME SERIES — RESERVOIR TEMPERATURE · VISCOSITY · OIL RATE` versus **`Cycle time series`** with the three variables in the HTML legend beneath. The second is a product; the first is a template.

## B6. Panel breathing room **[P1]**
**Evidence:** L309 `.panel{padding:18px 20px 20px}` with L345 `h2{margin:-18px -20px 14px; padding:12px 20px 10px}` — so the gap from the header rule to the chart is 14px, while the chart's own Plotly `margin.t` is 15–46px, producing an inconsistent 29–60px optical gap that differs per panel.
**Fix:** `.panel{padding:0 var(--s6) var(--s6)}`; header strip `padding:var(--s4) var(--s6)`; then a **fixed `--s5` (20px)** between the header rule and content, with Plotly `margin.t:0` on every chart (the title is HTML, so Plotly needs no top margin at all). Uniform optical gap across all five panels.

## B7. Chart margins are hardcoded and don't respond **[P1]**
**Evidence:** `margin:{t:20,r:76,l:60,b:55}` (L1417), `{t:15,r:20,l:55,b:45}` (L1462), `{t:10,r:20,l:20,b:0}` (L1493), `{t:46,r:20,l:55,b:60}` (L1571). Four different margin objects, four different left gutters (`60/55/20/55`), so the four charts' plot areas do not align to any common edge. At 1920 the same 60px gutter is used as at 1280.
**Fix:** one shared object, `const M = {t:0, r:8, l:56, b:44}`, overridden only where a legend/subplot needs it. `l:56` becomes the page's chart content edge and all four charts align. Recompute on resize: `if (innerWidth>=1600) M.l = 64`.

## B8. Control bar spacing is inverted **[P0]**
**Verdict:** The most visibly "broken/cramped" region, and it's a Gestalt failure, not a size failure.
**Evidence:** L205 `.control label{display:flex; justify-content:space-between}` — so on a ~300px-wide control the label reads `STEAM VOLUME` … 190px of nothing … `(t / cycle)`. Meanwhile L194 sets the gap *between* adjacent controls to only 22px. **The gap inside one label is nine times the gap between two controls.** Screenshot A y≈172 shows it starkly. Then L202 `gap:8px` puts the value `1500 t` *below* the track — 22px from its own label and 22px from the neighbour's label, so ownership is ambiguous.
**Fix:**
```
[STEAM VOLUME  (t/cycle)]            1500          <- label left, value right, same line
[━━━━●━━━━━━━━━━━━━━━━━━━━━━]                      <- track full width, 10px below
```
`.control label{display:flex; gap:6px; justify-content:flex-start}` (unit sits 6px after the label, not 190px), value moves to a right-aligned `output` **on the label row** at `--t-kpi` (28px) tabular, track below at `margin-top:10px`. Inter-control gap goes to **32px**, and add a `1px` `#21262d` vertical rule between control groups. Now: unit belongs to label, value belongs to control, controls are separated. Reads instantly.

## B9. Alert banner causes a 60px layout jump **[P1]**
**Evidence:** L267–279 `.alert-banner{margin-bottom:16px}` + L808 `hidden`. When floating index crosses 0.6 mid-demo, everything below shifts down ~62px.
**Fix:** Reserve the row (`min-height:0` container that transitions to `56px`), or better — make the alarm an **overlay strip fixed to the top of the grid region** with `position:sticky; top:0; z-index:60`, so nothing reflows. Ops UIs never reflow on alarm.

## B10. Panel 5 is 300px of void at wide viewports **[P1]**
**Evidence:** L542 `.xsec-wrap svg{min-height:460px}` inside a grid area (`xs`) that spans two rows and therefore stretches to ~790px at 1600 and ~740px at 1920. `preserveAspectRatio="xMidYMid meet"` centres a 340×600 drawing in that box, leaving a visible empty band between the HUD row and the wellhead — screenshot B y≈300–440, screenshot A y≈300–470.
**Fix:** `align-self:start` on `#panelXsec` plus `.xsec-wrap svg{height:auto; aspect-ratio:340/600; max-height:640px}`; or extend the SVG viewBox to `0 0 340 640` and use the reclaimed 40 units for a **surface-facilities strip** (steam generator, separator, tank) — actual information in the space instead of void. Prefer the second: it makes the twin look complete "well-to-surface", which is literally your product name.

## B11. Optimize panel wastes ~55% of its area **[P2]**
**Evidence:** L429–431 `flex:1 1 340px` / `1 1 320px` in a full-width panel; at 1920 that's a 280px-tall two-bar chart in a ~700px column, and a 6-row table in another ~700px column with a 400px-wide empty `VALUE` column. Screenshot B y≈1040–1340.
**Fix:** see D4 — the bar chart should not exist at that size.

---

# C. India + PSU theme: from sticker to identity

## C0. Why the current treatment reads as kitsch **[P0]**

Three token gestures, all of them the *cheap* version of the idea:

1. **L81–102 `.tricolor-bar`** — 3px, full viewport width, saffron/white/green at full saturation (`#FF9933` / `#f4f4f4` / `#138808`), with an animated white sweep. At 1600px, the white third is a **530px band of near-white at 100% opacity on a #0d1117 page** — mathematically the brightest object on the screen, and it carries zero information. Screenshots A/B/C all show your eye going there first. Additionally: animating the national flag's colours is a **flag-etiquette problem**, not just a taste one; the Flag Code discourages decorative/animated use of the tricolour. A jury with a government member may notice.
2. **L756–764 "DIGITAL INDIA · MAKE IN INDIA"** — programme names invoked with no relationship to the deliverable. This is the exact register the user means by kitsch.
3. **`--saffron` / `--india-green` tokens used nowhere else** — the theme has no reach into the actual interface.

## C1. What an actual Indian energy-PSU product looks like

Look at how OIL, ONGC, IOCL and GAIL brand their real artefacts (annual reports, SCADA screens, plant signage, tender documents, control-room mimic boards). The consistent, learnable pattern:

- **Bilingual masthead, Devanagari first or above.** Every OIL/ONGC letterhead, signboard, report cover and statutory notice is Hindi-and-English, per the Official Languages Act §3(3). *This is the single most authentic Indian-PSU signal available to you, and you currently have zero Devanagari on the page.* It is also completely free of kitsch — it's law, not decoration.
- **Deep navy/indigo as the structural colour**, red or a muted orange as the single accent, white/off-white ground. Not tricolour. OIL's own house colour is a deep blue with red; ONGC is maroon-red; IOCL is navy + orange flame. None of them put a flag stripe on their products.
- **The title block.** Every engineering document a PSU issues — drawing, P&ID, well log, tender — carries a bordered plate: issuing authority / document number / revision / date / classification / scale. Your product *is* a digital well drawing. Adopting a title block is simultaneously the most authentic and the most beautiful move available, and it solves the "where does the metadata go" problem from A9/C3.
- **Restrained, official typography.** Humanist sans (Segoe UI is genuinely fine and is what half of Indian government intranet software runs on), semibold not black, sentence case for titles, uppercase reserved for field labels and document classifications.
- **Tricolour, when used at all, is a small rule under the emblem** — never full-bleed, never animated, never the brightest thing on the page.

## C2. Concrete palette revision **[P0]**

```css
:root{
  /* ground — unchanged, correct for a control room */
  --bg:#0d1117; --bg-panel:#161b22; --bg-sunken:#12171e; --border:#30363d;
  --rule:#21262d;

  /* text */
  --text:#e6edf3; --text-2:#c9d1d9; --text-dim:#8b949e;
  --text-faint:#7d8590;        /* REPLACES #586069 for text — see D11 */

  /* process semantics (ISA-101) */
  --amber:#f59e0b;  --green:#10b981;  --red:#ef4444;  --blue:#60a5fa;

  /* institutional identity — new */
  --oil-navy:#12386b;          /* header/footer bands, table heads, plate fills */
  --oil-navy-deep:#0b2645;
  --oil-red:#c0392b;           /* client accent, used at most twice on the page */
  --saffron:#E08A3C;           /* DESATURATED from #FF9933 — identity rule only */
  --india-green:#127A3B;       /* DESATURATED from #138808 */
  --tri-white:#D8DEE6;         /* NOT #f4f4f4 — never pure white on a dark ground */
}
```
The desaturation is the whole trick: `#FF9933` + `#138808` + `#f4f4f4` at full chroma on black is a flag sticker; `#E08A3C` + `#127A3B` + `#D8DEE6` at 12px scale is a *seal*.

**Tricolour rule, non-negotiable:**
- Max width **180px**, sitting **only** under the identity lockup, matching the wordmark's measure.
- Height 2px, `border-radius:0`.
- **No animation.** Delete L92–102 entirely.
- Never full-bleed, never repeated elsewhere.

## C3. The header lockup — replace the whole thing **[P0]**

Current (L729–768): an h1 that crams product + client + PS number, a two-line grey prose subtitle carrying nine facts, an orphaned pumpjack clipart, three badges and a status pill. Screenshot C shows it collapsing into a four-row stack with `MOCK DATA` stranded mid-page.

Proposed structure, three zones on one 88px-tall band, then a title block:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌────┐  बाघेवाला डिजिटल ट्विन                    │  ऑयल इंडिया लिमिटेड    ● MOCK  │
│ │ ▟▖ │  Baghewala Digital Twin                  │  Oil India Limited            │
│ └────┘  ███▏███▏███  well-to-surface CSS twin   │  नवाचार भागीदार · MNIT Jaipur │
└──────────────────────────────────────────────────────────────────────────┘
  PS SIH26120 · REV 1.4 · WELL BGW-07 · BAGHEWALA, RAJASTHAN · TD 1,150 m ·
  11,500 cP @ 50 °C · 15.5° API · P_res 11.4 MPa · STEAM 290 °C @ 74 t/d · MOCK
```

- **Mark (32×32):** the pumpjack from L736–749 reduced to three strokes — beam, post, base — in `--text-2` inside a 32×32 plate with a 1px `--border` and `--r-1`. It becomes a monogram, not clipart. Delete the animated version from the header (keep the animation only in the cutaway, where it means "producing").
- **Wordmark:** Devanagari line at `--t-title` in `--font-deva`, `--text-2`; Latin line at `--t-h1` (26px/600) in `--text`. **No amber accent word** — delete `.accent` (L115). A brand doesn't colour one word of its own name.
- **Tricolour rule:** 180px × 2px directly under the wordmark, static, desaturated.
- **Client lockup, right:** `ऑयल इंडिया लिमिटेड` / `Oil India Limited` stacked, 12px/14px, separated from the product by a `1px × 40px` vertical `--border` rule — the standard "in partnership with" typographic device. Under it, 11px: `नवाचार भागीदार · MNIT Jaipur` / `Innovation partner`.
- **Status:** the only badge, `--r-1`, top-right of the client zone.
- **Title block:** a full-width 1px-bordered strip beneath, `--bg-sunken`, `padding:10px 24px`, `--t-micro` uppercase, fields separated by `1px` vertical rules (not middots). This absorbs the entire subtitle prose from L732 plus the two deleted badges, and turns nine loose facts into a document header. It is the highest-value single change in section C.
- **Language toggle** sits at the far right of the title block. See C5.

Delete: `header::after` shimmer, `.badge` ×2, `.accent`, the free-floating pumpjack widget, the full-bleed tricolour bar.

## C4. Where the theme reaches into the interface (so it isn't just a hat) **[P1]**

- **Table head** (`table th`, L434): background `--oil-navy` at 22% (`#12386b38`), text `--text-2`, no uppercase tracking change. PSU tabular documents always band the header row.
- **Panel header strips:** replace the frosted white gradient (L352–354) with a flat `--bg-sunken` and a `1px --rule` bottom border. Then the *primary* two panels get a `2px` left border in `--oil-navy` — a quiet structural signature that repeats without shouting.
- **Footer band:** full-width `--oil-navy-deep` at 40% with a top `1px --oil-navy` rule. That single band is what makes a page feel institutionally issued.
- **The `--saffron` never appears outside the 180px rule and the tricolour dot in the seal.** That's the discipline that separates classy from kitsch.

## C5. Language toggle design **[P1]**

Not a switch, not a pill, not a globe icon. A **two-segment document control**, matching the title block's register:

```
┌──────┬──────┐
│  EN  │  हिं  │      22px tall · 11px/600 · --r-1 · 1px --border
└──────┴──────┘      active: bg --bg-panel, text --text, 2px --amber bottom rule
                     inactive: bg transparent, text --text-faint
```
- Position: far right of the title block strip, vertically centred.
- `width:auto`, each segment `padding:0 12px`, divider `1px --border`.
- Persist to `localStorage.setItem("bgw.lang", "hi")`; read on boot before first paint to avoid a flash.
- Implementation: every bilingual node carries `data-en` and `data-hi`; a single `applyLang(l)` walks `[data-en]` and swaps `textContent`, sets `document.documentElement.lang`, and toggles a `body.lang-hi` class.
- **Tier-1 strings are bilingual in *both* modes** (stacked, secondary line at 0.85× and `opacity:.62`); the toggle only decides which language is primary. That is how PSU signage works, and it means a Hindi-speaking judge is served even if nobody touches the toggle.
- Never machine-translate at runtime. All strings are authored, below.

## C6. Devanagari font stack + typographic rules for Windows **[P0]**

```css
--font-deva:"Nirmala UI","Noto Sans Devanagari","Mangal","Segoe UI",sans-serif;
```
- **Nirmala UI** is the correct primary: it ships with Windows 8 through 11 (so it is guaranteed on the demo laptop and on the jury's machine), has Regular/Semilight/Bold, and is designed as a *UI* face — correct shirorekha weight at small sizes.
- **Noto Sans Devanagari** as the web fallback (Google Fonts, if you're allowed a network dependency — otherwise drop it; do not make the demo depend on a CDN font).
- **Mangal** as the legacy floor — Regular only, older metrics, acceptable but not good.
- **Never** `Kokila`, `Utsaah`, `Aparajita` (calligraphic/italic display faces — instant amateur signal), and never `Sanskrit Text` for UI.

Mandatory CSS reset for Devanagari nodes — **your current label styles would mangle Hindi**:
```css
[lang="hi"], .lang-hi [data-hi]{
  font-family:var(--font-deva);
  letter-spacing:0 !important;    /* NEVER track Devanagari — it visually breaks conjuncts */
  text-transform:none !important; /* the script has no case; the class must not imply one   */
  line-height:1.60;               /* +0.15 over Latin: matras and shirorekha need headroom  */
  font-size:1.06em;               /* Nirmala UI's x-height runs small vs Segoe UI at the same px */
  font-weight:600;                /* Nirmala's Regular is light on dark grounds; 600 for labels */
}
```
This matters concretely: `.panel h2` (L348–349), `.kpi-label` (L392), `.badge` (L136–137), `.control label` (L204), `table th` (L434) and `.xsec-hud` (L545) all apply `text-transform:uppercase` + `letter-spacing:.05–.08em`. Applying those to Devanagari produces tracked-out, broken-looking Hindi. The reset above is not optional.

Also: **use Latin digits in Hindi mode** (`1,159 m³`, not `१,१५९`). Indian technical and PSU engineering documents use Latin numerals in Hindi text; Devanagari numerals would look archaic and would break your `tabular-nums`.

## C7. The strings — actual Hindi translations **[P0]**

**Tier 1 — always bilingual (stacked, both modes).** Identity, panel titles, KPI names, primary actions, alarms.

| # | English | हिन्दी | Where |
|---|---|---|---|
| 1 | Oil India Limited | ऑयल इंडिया लिमिटेड | header client lockup |
| 2 | Baghewala Digital Twin | बाघेवाला डिजिटल ट्विन | wordmark |
| 3 | Well-to-surface CSS twin | कूप-से-सतह सीएसएस ट्विन | wordmark subline |
| 4 | Innovation partner · MNIT Jaipur | नवाचार भागीदार · एमएनआईटी जयपुर | client lockup |
| 5 | Cycle time series | चक्र समय-श्रेणी | panel 1 title |
| 6 | Well cross-section | कूप अनुप्रस्थ काट | panel 2 title |
| 7 | Pump dynamometer card | पंप डायनामोमीटर कार्ड | panel 3 title |
| 8 | Floating risk & cycle KPIs | फ्लोटिंग जोखिम एवं चक्र संकेतक | panel 4 title |
| 9 | Baseline vs ML-optimised SOR | आधार रेखा बनाम एमएल-अनुकूलित भाप-तेल अनुपात | panel 5 title |
| 10 | **Steam/Oil Ratio (SOR)** | **भाप-तेल अनुपात** | hero KPI |
| 11 | Total oil recovered | कुल प्राप्त तेल | KPI |
| 12 | Energy intensity | ऊर्जा तीव्रता | KPI |
| 13 | Cycle duration | चक्र अवधि | KPI |
| 14 | Simulate cycle | चक्र अनुकरण करें | primary button |
| 15 | Optimise settings | सेटिंग अनुकूलित करें | secondary button |
| 16 | Apply optimised settings | अनुकूलित सेटिंग लागू करें | apply button |
| 17 | Rod floating risk — reduce SPM | रॉड फ्लोटिंग जोखिम — SPM घटाएँ | alarm banner |
| 18 | Injection | अंतःक्षेपण | phase chip / chart band |
| 19 | Soak | सोख | phase chip / chart band |
| 20 | Production | उत्पादन | phase chip / chart band |
| 21 | Mock data | नमूना डेटा | status pill |
| 22 | Live | सजीव | status pill |
| 23 | Demonstration only — not for operational use | केवल प्रदर्शन हेतु — परिचालन उपयोग हेतु नहीं | footer statutory line |
| 24 | Reservoir temperature | भंडार तापमान | legend / axis |
| 25 | Viscosity | श्यानता | legend / axis |
| 26 | Oil rate | तेल दर | legend / axis |

**Tier 2 — Hindi only when the toggle is on हिं.**

| # | English | हिन्दी |
|---|---|---|
| 27 | Steam volume | भाप मात्रा |
| 28 | Soak period | सोख अवधि |
| 29 | Economic cutoff | आर्थिक सीमा |
| 30 | Pump speed | पंप गति |
| 31 | Recommended setting | अनुशंसित सेटिंग |
| 32 | Value | मान |
| 33 | Predicted SOR | अनुमानित भाप-तेल अनुपात |
| 34 | Floating probability | फ्लोटिंग प्रायिकता |
| 35 | lower SOR vs baseline | आधार रेखा की तुलना में कम भाप-तेल अनुपात |
| 36 | Peak rod load | शिखर छड़ भार |
| 37 | Floating index | फ्लोटिंग सूचकांक |
| 38 | Stroke length | स्ट्रोक लंबाई |
| 39 | Day | दिन |
| 40 | Depth | गहराई |
| 41 | Pay zone | उत्पादक संस्तर |
| 42 | Heavy crude | भारी कच्चा तेल |
| 43 | Steam generator | भाप जनित्र |
| 44 | Wellhead | कूप-शीर्ष |
| 45 | Telemetry | टेलीमेट्री |
| 46 | Replay cycle | चक्र दोहराएँ |
| 47 | Drag to scrub | स्क्रब हेतु खींचें |
| 48 | Baghewala field, Rajasthan | बाघेवाला क्षेत्र, राजस्थान |
| 49 | Live twin state | सजीव ट्विन स्थिति |
| 50 | Smart India Hackathon 2026 | स्मार्ट इंडिया हैकथॉन 2026 |
| 51 | Cycle complete | चक्र पूर्ण |
| 52 | Within limits | सीमा के भीतर |

**Tier 3 — never translated.** Units (`t`, `m³/d`, `°C`, `cP`, `kN`, `SPM`, `kWh/m³`, `MPa`, `API`), well ID `BGW-07`, problem-statement ID `SIH26120`, all numerals, and the acronyms `SOR`, `CSS`, `ML`, `IPR`, `SPM` (give the Hindi expansion once, in the title block only).

---

# D. Professional-product feel

## D1. Information hierarchy is inverted **[P0]**

Ranked by rendered pixel height, the page currently says its most important facts are:

| Rank | Element | Size | Should it be? |
|---|---|---|---|
| 1 | `0.54` — floating index gauge numeral | **30px** (L1479) | No. It's a safety *check*, not the claim. |
| 2 | `<h1>` | 22px (L110) | Yes, roughly. |
| 2= | four KPI values | 22px (L395) | Only one of them. |
| 4 | bar chart bars | ~200px tall | No. |
| 5 | `▼ 41.3% lower SOR vs baseline` | **12.5px in a pill** (L450) | **This is the entire product claim.** |
| 6 | `0.88 t/m³` predicted SOR | 13.5px table cell (L432) | Ditto. |

Your `<h1>` is the same size as a KPI tile label's value, and your headline result is the fifth-smallest text on the page. This one table is why the dashboard reads as generic: a template distributes emphasis evenly because it doesn't know what the product is *for*.

## D2. Build the result band **[P0]**

A full-width, card-less band between the command bar and the grid — 1px rules top and bottom, `--s7` (32px) vertical padding, page-ground background:

```
 भाप-तेल अनुपात · STEAM/OIL RATIO          FLOATING RISK        RECOVERY
                                            ────────────         ────────
  0.88  t/m³        −41.3%                  0.11%  प्रायिकता      1,159 m³
  ↑56px tabular     ↑28px green             ↑14px, muted        ↑28px
  was 1.50 ↑12px struck, --text-faint       within limits        61 दिन / days
```
- Left cell: `--t-hero` (56px) tabular, `--text` (**not amber** — the hero is white; colour is reserved), unit at 16px `--text-dim`. Beneath it, `was 1.50` at 12px struck through in `--text-faint`.
- Second cell: `−41.3%` at `--t-delta` (28px) in `--green`, label `vs baseline` 11px. **No pill, no border, no icon.** A big green number with a small label is more confident than a badge.
- Third cell: floating risk, deliberately *small* (14px) and grey when within limits — it should only become visually loud when it isn't. That's ISA-101 behaviour and it will read as expert.
- Fourth cell: recovery + duration, `--t-kpi` (28px).
- Separated by `1px × 48px` vertical rules, not gaps.

This band is the answer to "what makes this look like a real product": **a real product states its result before it shows its work.** Everything below becomes evidence.

## D3. Demote the gauge **[P0]**
The Plotly indicator (L1473–1495) currently owns a whole panel column and the page's largest numeral, for a value that in the happy path is "fine". Replace with a **linear risk meter**: 8px-tall track, full panel width, `--bg-inset`, three zone segments at 40%/60%/100% in 14%-alpha green/amber/red, a 2px white marker at the current value, a 2px red threshold tick at 0.60, and the value as `0.54` at `--t-kpi` (28px) left-aligned above it. Half the ink, four times the legibility, and it stops looking like a Plotly demo. The freed space in `#panelGauge` lets the four KPI tiles go from a cramped 2×2 to a 4-across row.

## D4. Kill or shrink the two-bar chart **[P1]**
A bar chart with two bars is a table with extra steps (L1556–1574), and it's consuming half of the widest panel. Once D2 exists, `1.50 → 0.88` is already stated at 56px. Replace the chart with either (a) nothing — let the panel be the recommended-settings table at full width with proper 44px rows, or (b) a **12px-tall paired bullet bar** inline above the table. Recommended: (a).

## D5. Footer, done right **[P1]**
Current (L1022–1024, L453–456): one centred 12px line, 190 characters, six middots, `#586069` (contrast **2.7:1 — fails WCAG AA**). It's the "AI footer".
Replace with a three-column institutional band, `--oil-navy-deep` at 40%, top rule `1px --oil-navy`, `padding:24px 32px`, left-aligned:

```
MODEL BASIS                    DATA                        ISSUED BY
Marx–Langenheim thermal        MOCK · baked from           Team · SIH26120
Andrade viscosity              twin.cycle.simulate         Oil India Limited
Vogel IPR                      field_params.json           MNIT Jaipur
Sucker-rod load approx.        rev 1.4 · 13 Sep 2026       ─────────────
                                                           केवल प्रदर्शन हेतु
                                                           Demonstration only —
                                                           not for operational use
```
Three columns, `--t-micro` uppercase headers in `--text-dim`, `--t-meta` values in `--text-faint`, `gap: --s9`. Same facts, but it now reads as a colophon on an issued document rather than a disclaimer sentence.

## D6. Panel titles carry chart metadata they shouldn't **[P1]**
`Cycle Time Series — Reservoir Temperature · Viscosity · Oil Rate` (L817) is a title plus a legend. `Pump Dynamometer Card (approximate, from peak rod load & floating index)` (L970) is a title plus a methodology note — and at 1280 it **wraps to two lines, making that panel's header strip 22px taller than the adjacent panel's** (screenshot C, y≈870 vs y≈883: two side-by-side panels whose header rules do not align). That misalignment is a professionalism killer.
**Fix:** titles become bare noun phrases (`Cycle time series`, `Dynamometer card`). Series names move to the HTML legend; the methodology note moves to a right-aligned 11px meta on the same row, `white-space:nowrap`. Set `.panel h2{min-height:48px; display:flex; align-items:center}` so every header strip is exactly the same height regardless of content.

## D7. Consistency nits — full list from source **[P1 unless noted]**

**Corner radii (8 values):** see A1. **[P0]**

**Paddings (18 values):** `4/10` badge L133 · `5/12/5/8` status-pill L144 · `7/14` ticker L165 · `18/22` controls L199 · `11/24` btn L243 · `12/20` alert L273 · `18/20/20` panel L309 · `12/20/10` h2 L346 · `13/15` kpi-tile L389 · `9/10` table cell L433 · `14/16` opt-note L441 · `5/12` improvement-tag L450 · `3/10` phase-chip L551 · `9/12` replay-bar L603 · `6/16` stamp L647 · `3/9` sor-delta L665 · `20/28/40` body L32. **Seven of these are odd numbers.** **[P0]**

**Font sizes (16 values):** `8.5` L598 · `9` L597 · `10.5` L174/392/552 · `11` L135/146/204/434/545/622 · `11.5` L667 · `12` L126/168/358/396/454/607 · `12.5` L372/450 · `13` L117 · `13.5` L432/443 · `14` L244/276/347 · `15` L30/210/648 · `20` L284 · `22` L110/395 · `30` (Plotly L1479) · `7.5` (inline SVG L884/885). **[P0]**

**Casing collisions:**
- `.panel h2` forces uppercase (L348) but `.panel h2 .hint` forces none (L358) — **half-uppercase in one line**, five times.
- `.xsec-hud` forces uppercase (L546) but `#xsTemp` forces none (L549) — **half-uppercase in one row**.
- Buttons are Title Case; table `<th>` is UPPERCASE; KPI labels UPPERCASE; badges UPPERCASE; `.replay-hint` lowercase sentence; footer sentence case; `phase-chip` content is authored lowercase (`"idle"`, L838; `chip.textContent = phase`, L1606) then CSS-uppercased — so the same word is `produce` in the ticker and `PRODUCE` in the chip.
- **Pick one rule:** UPPERCASE + `--t-label` for field labels, table heads and chips **only**; sentence case for everything else, including panel titles. Nothing else uppercases.

**Naming collisions for one quantity:** `Steam / Oil Ratio` (L984, with spaces), `STEAM/OIL RATIO` (L1006, without), `SOR` (L1582), `SOR (t steam / m³ oil)` (L1568), `SCR`?? — the y-axis title in screenshot A reads `SOR (t steam / m³ oil)` but is set at a size where it is nearly illegible. **Standardise on `SOR` everywhere, expanded once in the result band as `Steam/Oil Ratio · भाप-तेल अनुपात`.** **[P0]**

**Unit spellings for one unit:** `(days)` L790 · `7 d` L790 output · `61 days` L1000 · `3 days` L1579 · `61 दिन`. Standardise: `d` in compact readouts, `days` in the result band and table, never `(days)` in a label when the value already carries it.
Same for SPM: label `(SPM)` L798 uppercase, output `8.0 spm` lowercase L800, ticker `SPM 8.0` L—. Standardise on `spm` lowercase in values, `SPM` uppercase only in labels/alarms.

**Colour tokens:** `--amber-dim` (L17) declared, **never used** — dead token. `#a78bfa` hardcoded ×4 (L511–515) — **not a token**. `#586069` serves three unrelated roles: body text (L207, 358, 454, 622), SVG hardware fill/stroke (L743, 748, 820, 883, 897, 905, 914–920), and a chart series colour (L1560, L1660). `#21262d`, `#1c2128`, `#12171f`, `#0e1219`, `#3a424c`, `#4b5563`, `#4a3c1a`, `#1a2029` all hardcoded, none tokenised. **[P1]**

**Border colours:** `--border` `#30363d` mostly, but L355 uses `rgba(240,246,252,0.07)` and L874 `#4a3c1a` and L910 `#3a424c` — three one-off border colours.

**`.btn` inconsistency:** `.btn-apply` (L687–690) sets `width:100%` and a `margin-top:12px` while the other two buttons are auto-width in a `gap:12px` flex row — so the apply button is a full-width block and the others are inline. Two different button systems.

## D8. Contrast failures **[P0]**
`#586069` on `--bg-panel` `#161b22` = **2.72:1**. WCAG AA needs 4.5:1 for normal text. It's used for four text elements: slider unit labels (L207), panel-title hints (L358), the footer (L454), the replay hint (L622). On a projector in a lit hall these will be **invisible**, which is worse than ugly — a judge literally cannot read your footer.
**Fix:** `--text-faint:#7d8590` = **4.66:1**. Reserve `#586069` for hairlines and SVG hardware only. Also check `.xs-depth-label`/`.xs-zone-label` at `#8b949e` on `#0e1219` — that passes (≈5.9:1) but at `8.5px`/`9px` (L597–598) it is below the practical legibility floor; raise to 10px and 10px.

## D9. Chart typography does not scale with viewport **[P1]**
See A10a/B7. At 1920 the charts are the same 12px as at 1280 while every panel got 45% wider — the figures look under-set. Add a resize handler that flips `FONT.size` between `12` and `13` at 1600 and calls `Plotly.relayout` on all four charts.

## D10. The `<h1>` contains the client's name **[P1]**
`Baghewala Well-to-Surface Digital Twin — SIH26120 · Oil India Limited` (L731). Three entities in one heading. Products don't put the customer inside the product name; they put the customer in a partner lockup. Fixed by C3.

## D11. Grid areas don't reflect importance **[P2]**
`grid-template-areas` (L298–301) gives the cross-section a 350px fixed column spanning two rows — so the *illustration* gets the most persistent screen real estate, while the optimisation result (the product's point) gets a bottom strip. Once D2 exists this is tolerable; if not, swap `p4` into the `xs` column position at wide viewports.

## D12. `title` attributes doing accessibility work **[P2]**
L735, L818, L831, L835 use `title=` as the only description. `title` doesn't surface on touch, doesn't surface reliably to screen readers, and is invisible on a projector. Move the load-bearing ones (`drag to scrub`) to visible 11px meta or `aria-label` + a visible affordance.

## D13. Reduced-motion block nukes transitions too **[P2]**
L714–721 sets `transition-duration:0.001ms !important` on `*` — which kills hover feedback and state transitions, not just animation. Reduced-motion means *no large/vestibular motion*, not *no feedback*. Scope it: keep `transition` on colour/opacity/box-shadow, kill only `transform`-based and infinite animations.

---

# E. Prioritised fix list

**P0 — do these before anyone sees it again (19).** These are the findings that produce "AI lag raha hai", "compact lag raha hai", or "theme weak hai".

| # | Ref | Fix | Effort |
|---|---|---|---|
| 1 | A1 | Collapse 8 border-radii to 3 tokens (`2/4/6`); delete every `20px` stadium pill | S |
| 2 | B2 | Introduce the 4px spacing scale; replace all 18 ad-hoc paddings | M |
| 3 | B1 | Differentiate region gaps (`28/20/28/24/36/48`) — kill the six consecutive 16s | S |
| 4 | B5 | Introduce the 10-token type scale; body 14px; **panel titles → 15px sentence case** | M |
| 5 | D1+D2 | Build the result band: SOR `0.88` at 56px, `−41.3%` at 28px green, `was 1.50` struck | M |
| 6 | D3 | Replace the Plotly indicator gauge with a linear risk meter | M |
| 7 | A14 | ISA-101 colour discipline; values go white; delete the 4 slider accent colours; delete `--amber-dim`; tokenise or delete violet | M |
| 8 | A4 | Delete 14 of 17 glow/shimmer effects (keep alarm, status dot, twin flow) | S |
| 9 | A3 | Delete the staggered `panelIn` entrance animation | S |
| 10 | A5 | Delete the rotated "OPTIMIZED" rubber stamp | S |
| 11 | A6 | Replace the scrolling marquee with a static last-value status line | M |
| 12 | A8 | Replace all 6 dingbats with one 14px inline-SVG icon set (`⇩` is **rendering broken today**) | S |
| 13 | B8 | Fix the control-bar spacing inversion: unit beside label, value on the label row, 32px between controls | S |
| 14 | C0+C2 | Kill the full-bleed animated tricolour; desaturate the palette; add the OIL-navy institutional tokens | S |
| 15 | C3 | Rebuild the header as mark + bilingual wordmark + 180px tricolour rule + client lockup + **title block** | L |
| 16 | C6 | Add the `--font-deva` stack and the `[lang="hi"]` reset (no tracking, no uppercase, 1.60 lh, 1.06em) | S |
| 17 | C7 | Author and wire the 26 Tier-1 bilingual strings | M |
| 18 | A10 | De-default Plotly: explicit font sizes, kill the 3rd y-axis (→ stacked subplot), fix the log-tick spam, HTML legend, `hovertemplate` | L |
| 19 | D8 | Fix the 2.72:1 contrast failure — `#586069` → `#7d8590` for all four text uses | S |

**P1 — do these before the final demo (26).**

20 A7 prune badges to one stateful status tag · 21 A9 delete the 9 explanatory strings · 22 A12 build the pumpjack monogram mark · 23 A13 sparkline rule tied to data, delete the droplet · 24 A11 un-centre the footer / gauge numeral / captions · 25 B4 three line-height tokens · 26 B6 uniform 20px header-rule-to-content gap, Plotly `margin.t:0` · 27 B7 one shared chart margin object; align all four left gutters at 56px · 28 B9 stop the 60px alarm reflow (sticky overlay) · 29 B10 fix the 300px void in the cross-section panel (or fill it with surface facilities) · 30 C4 push the theme into table heads, panel strips and the footer band · 31 C5 build the EN/हिं segmented toggle + `localStorage` · 32 C7-T2 wire the 26 Tier-2 strings · 33 D4 delete or shrink the two-bar chart · 34 D5 rebuild the footer as a 3-column colophon · 35 D6 titles → bare noun phrases; `min-height:48px` on header strips so adjacent panels align at 1280 · 36 D7 casing rule (uppercase only for labels/heads/chips) · 37 D7 standardise on `SOR` everywhere · 38 D7 standardise `days`/`d` and `spm`/`SPM` · 39 D7 tokenise the 8 hardcoded greys · 40 D7 unify the two button systems (`.btn-apply` width) · 41 D7 unify the 3 one-off border colours · 42 D9 chart font size responds at ≥1600 · 43 D10 client name out of the `<h1>` · 44 A2 three-tier panel treatment (border/no-border) · 45 A2 asymmetric grid columns `1.35fr / 1fr / 360px`

**P2 — polish (16).**

46 A15 one separator per line; rewrite `<h1>`, subtitle, footer, `<h2>`s · 47 B11 optimise-panel layout after D4 · 48 D11 grid-area importance at wide viewports · 49 D12 `title=` attributes → visible meta or `aria-label` · 50 D13 scope the reduced-motion block to transforms/infinite only · 51 raise `.xs-depth-label`/`.xs-zone-label` from 8.5–9px to 10px · 52 `tabular-nums` on every numeric node (currently 5 selectors) · 53 remove the duplicate `PS SIH26120` (h1 + badge) · 54 `--r-1` + no tint on phase chips · 55 slow the status dot to 3s, drop its glow · 56 delete `#bgGrid` parallax and its JS handler · 57 delete `.spark`/`sparkFly` particle system · 58 remove `backdrop-filter` (it costs compositor time for a 5%-alpha gradient) · 59 mask-gradient on the ticker no longer needed after A6 · 60 `cliponaxis`/`textposition` cleanup after D4 · 61 audit remaining `!important` and inline `style=` on the 12 animated SVG circles (L931–946) — move delays to a CSS `:nth-child` rule

---

## Appendix — the five worst tells, ranked

1. **The Plotly indicator gauge rendering `0.54` as the largest number on the page** (A10g + D1). One component that is simultaneously the most recognisable generated-dashboard artefact *and* the proof that the layout doesn't know what the product is about.
2. **Eight border-radii, five of them 20px stadium pills** (A1 + A7). Stadium pills are the visual fingerprint of generated UI, and having eight radii proves none was chosen.
3. **Seventeen glow/shimmer/gradient effects carrying zero information** (A4) — plus the staggered panel fade-up (A3) and the rotated rubber stamp (A5), which are motion tells of the same species.
4. **Uniform everything: five identical cards, six consecutive 16px gaps, four identical KPI tiles** (A2 + B1). This is what "compact" actually means here — undifferentiated, not small.
5. **The full-bleed animated tricolour bar + "DIGITAL INDIA · MAKE IN INDIA" pill standing in for an identity** (C0 + A12), on a page with no logo, no wordmark, and not one character of Devanagari.
