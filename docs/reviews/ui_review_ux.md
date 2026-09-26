# UX + Product Authenticity Review — `dashboard/index.html`

**Reviewer role:** senior UX / product-authenticity critic
**Target:** SIH 2026 · PS SIH26120 · Baghewala Well-to-Surface Digital Twin
**Build reviewed:** `dashboard/index.html`, 2029 lines, single file, `MOCK = true`
**Method:** headless Edge screenshots at 1600×2400 (idle), 1600×2400 with `?autoreplay`
(mid-replay, Day 1 / inject), 1366×768 (projector fold) and 1366×2600 (fold measurement);
full source read; cross-checked against `docs/guides/DEMO_SCRIPT.md`, `docs/guides/GLOSSARY.md`,
`docs/reviews/integration_report.md`.

**Headline verdict: the 8-second test FAILS.** The dashboard is competent, dense and
visually confident — and it does not tell a passer-by what it achieved. Every fix below
is in service of one sentence: *"AI cut steam-per-barrel 41% on a real Rajasthan heavy-oil
well."* Right now that sentence exists on screen as a 12.5 px green pill, 1,843 px down
the page at projector resolution.

---

## 1. First-8-seconds test — **FAILED**

### Evidence

Largest type on screen, in order, at 1600 px wide:

| Rank | Element | Size | Does it convey the takeaway? |
|---|---|---|---|
| 1 | Gauge number `0.54` | 30 px | No — a unitless risk index a judge cannot read |
| 2 | `<h1>` title | 22 px | Partially — says what it *is*, not what it *did* |
| 3 | KPI values (`1.29`, `1159`, `20.6`, `61`) | 22 px | No — four equal-weight numbers, no hierarchy |
| 4 | Bar-chart data labels `1.50` / `0.88` | ~13 px | The actual result, rendered smaller than the axis titles |
| 5 | `▼ 41.3% lower SOR vs baseline` | **12.5 px** | **This is the takeaway. It is the smallest text in its own panel.** |

The single most important number in the entire project is set at 12.5 px, in a pill, in
the fourth panel, below a table of six rows, at y ≈ 1,843 px on a 768 px-tall projector
screen. The biggest number on screen (`0.54`) is *floating index* — a number that means
nothing to anyone who has not read the glossary, and which reads as a **failure metric**
to someone who has not.

Second problem: **there is no visual hierarchy at all.** Five panels, identical
`#161b22` fill, identical 1 px `#30363d` border, identical 10 px radius, identical
uppercase 14 px grey `h2`. The layout says "here are five equally important things."
A judge's eye has no entry point, so it lands on the biggest chart (time series), which is
a *process* chart, not a *result* chart.

Third problem: the result the page *does* foreground contradicts itself. The KPI tile says
**SOR 1.29 t/m³**; the bar chart 500 px below says the baseline is **1.50**. Both are
labelled "baseline"-ish, neither explains the other. See §3.1 — this is the most dangerous
thing on the page.

### Fix — the hero-fact treatment

Insert a **result bar** as a first-class band immediately under the tricolor rule and
**above** the telemetry ticker and controls. Full width, ~120 px tall, three cells,
separated by hairlines. Not a panel — a *banner*, visually distinct from the panel system
(darker inset, or a 1 px amber top rule) so the eye is told "this is the answer, the rest
is the evidence."

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  STEAM PER m³ OIL          RESULT OF THIS CYCLE       ANNUAL VALUE, ONE WELL      │
│                                                                                   │
│   1.29 → 0.88            ▼ 41%                       ≈ ₹0.5 crore                │
│   t steam / m³ oil        less steam per m³ oil        3,700 t steam not burned    │
│   ────────────────        ML-optimised set-points      @ ₹1,300/t · 6 cycles/yr    │
│   Well BGW-07 · Baghewala (Bikaner), Rajasthan · Oil India Limited                │
└──────────────────────────────────────────────────────────────────────────────────┘
```

Specifics that matter:

1. **`41%` at 64–72 px, weight 700–800, in green.** Nothing else on the page above 30 px.
   Demote the gauge number to 22 px and label it `FLOATING RISK INDEX · limit 0.60` —
   it should never again be the largest thing on screen.
2. **`1.29 → 0.88` as a single morph unit**, arrow included, 40 px. The before-number must
   be present; a lone "0.88" is a claim, "1.29 → 0.88" is a result.
3. **Convert to money, and cite the conversion inline.** An Oil India jury converts
   tonnes of steam to rupees automatically; do it for them and you look like a product,
   fail to and you look like a science fair. Compute your own defensible figure
   (steam t/cycle × cycles/yr × ₹/t of steam) and print the assumption *in the cell* at
   10.5 px: `6 cycles/yr · ₹1,300/t steam (source)`. A stated, checkable assumption is
   more credible than a big round number with none.
4. **Round the hero.** `41%`, not `41.3%`. Print `41.3%` once, in the optimizer table,
   where precision belongs. Hero numbers round; instrument readouts don't.
5. Keep the well identity line inside the hero bar. It is the "real Rajasthan well" half
   of the takeaway and currently lives in a 13 px grey subtitle nobody reads.
6. The hero bar must render **before Simulate is clicked** in its baseline state
   (`1.29 t/m³ · baseline cycle · press Optimize to improve`), then animate to the
   two-number form on Apply. Never blank.

---

## 2. Demo-flow ergonomics

### 2.1 Click count on the 3-minute path

`docs/guides/DEMO_SCRIPT.md` prescribes: simulate → dyno → force the floating alert → optimize →
point at the improvement. Measured against the build:

| Step | Actions required | Verdict |
|---|---|---|
| Simulate | 1 click | OK |
| Show dyno card | scroll ~600 px at 1366 | **fold problem** |
| Alert theatre | drag SPM slider **+** click Simulate = 2 actions, then scroll back to see the banner | **fragile** |
| Optimize | 1 click — **but the panel is already populated on page load** | **broken reveal** |
| Apply | 1 click, then scroll up 1,500 px to see the SOR change | **fold problem** |

**The Optimize reveal is dead on arrival.** `index.html:2019` calls `runOptimize()` at
boot, so `1.50 / 0.88 / ▼41.3% / Apply Optimized Settings` are all on screen before the
presenter says a word. At 2:10 the presenter clicks a button that produces a 400 ms
shimmer and no new information. The dramatic beat the whole script is built around
does not exist.

> **Fix (P0-3):** delete the boot-time `runOptimize()` call. Leave the optimizer panel in
> a deliberate empty state — a dashed placeholder reading
> `Optimizer idle — 3,000-cycle XGBoost surrogate ready · press ⚙ Optimize Settings`,
> with the baseline bar (1.29) drawn alone and greyed. The Optimize click then *adds* the
> amber bar with a 600 ms grow-up transition and reveals the delta. That is the wow moment,
> and it currently costs nothing to restore.

**The alert theatre needs one click, not two.** Add a small `⚡ Stress Test (12 SPM)`
button next to Optimize that sets SPM to max *and* re-simulates in one action. In a
3-minute pitch under lights, "drag the fourth slider to the far right, then click
Simulate, then scroll down" is where demos die.

**The alert banner has no acknowledge affordance** — see §3.6.

### 2.2 The fold at 1366×768 (the projector case)

This is the most actionable finding in the review. Measured from the 1366-wide capture,
converted to CSS pixels; the fold is at **y = 768**:

| Element | Top edge (px) | Above the fold? |
|---|---|---|
| Header + subtitle | 20 | yes |
| Badge row | 105 | yes |
| `MOCK DATA` pill | 145 | yes — **and visually broken, see below** |
| Telemetry ticker | 205 | yes |
| Controls + Simulate / Optimize | 258 | yes |
| Time-series chart (plot area) | 470 | top half only |
| Time-series x-axis + legend | 800 / 822 | **NO** |
| **Replay bar (play button, scrubber hint)** | **885** | **NO** |
| Dyno card panel | 955 | NO |
| Floating-risk gauge | 1,157 | NO |
| **SOR KPI tile (`1.29 t/m³`)** | **1,305** | **NO** |
| Optimizer panel | 1,512 | NO |
| **`▼ 41.3% lower SOR vs baseline`** | **1,843** | **NO — 2.4 screens down** |
| Apply Optimized Settings | 1,900 | NO |

At the resolution the demo will actually run on, a judge sees: a title, three badges, four
sliders, and the top half of one chart. **No result, no KPI, no optimizer, no replay
control.** The demo script's own setup checklist says *"Zoom the browser to a size where
all four dashboard panels are visible without scrolling"* — at 1366×768 that requires
roughly 50% browser zoom, at which the 12.5 px improvement pill becomes ~6 px and the
axis labels are unreadable from the third row. The checklist is asking for something the
layout cannot deliver.

Also visible at 1366: the header wraps and the **`MOCK DATA` pill detaches from the
top-right corner and lands centred under the badge row** (see capture). It reads as a
layout bug, which is exactly the wrong first impression for a "real product."

**What must move above the fold at 1366×768:**

1. The **hero result bar** from §1 — non-negotiable, this is the whole point.
2. The **SOR + oil KPI pair**. Move the four KPI tiles out of the gauge panel and into a
   compact strip directly under the hero bar (or into the hero bar itself as cells 4–6).
   The gauge panel keeps the gauge and the dyno stats.
3. The **replay play button**. Currently at 885 px — a judge never learns it exists.
4. Compress the header to buy the space: it currently costs 185 px for a title, a 3-line
   subtitle, and three badges.
   - Drop `Smart India Hackathon 2026` and `PS SIH26120` from the badge row into the
     footer. The judge knows which hackathon they are judging.
   - Collapse the 3-line subtitle to one line; move `Depth 1,150 m · 11,500 cP @ 50 °C ·
     P_res 11.4 MPa · steam 290 °C @ 74 t/d` into the well-identity block (§3.3), where a
     real product puts it.
   - Header target: **≤ 96 px**.
5. Fix the header wrap so `MOCK DATA` stays pinned right at every width
   (`.header-meta{margin-left:auto}` plus a `flex-wrap` guard at ≥1200 px).

Budget check at 768 px: header 96 + tricolor 21 + hero bar 120 + controls 100 +
KPI strip 90 = **427 px**, leaving 340 px for the top of the time-series chart. Everything
that answers "did it work?" fits on one projector screen. The ticker moves below the
controls or is cut entirely (§5).

### 2.3 Is the replay discoverable?

**No.** Three compounding reasons:

1. It is below the fold at 1366 (885 px).
2. The affordance is a 34 px amber circle with a `▶` glyph inside a low-contrast inset
   strip, visually subordinate to the two large buttons 600 px above it. Nothing indicates
   it drives the *entire dashboard* — the cross-section, gauge, dyno and KPIs all follow it.
3. The scrub hint `drag the amber cursor to scrub` is 11 px, `#586069` on `#0d1117` — that
   is roughly **2.6:1 contrast, below WCAG's 4.5:1 minimum**, and it sits at the far right
   of the bar, 700 px from the cursor it refers to.

The replay is the most impressive thing in the build and it is the least discoverable.

> **Fix:** promote it to a labelled control next to Simulate/Optimize —
> `▶ Replay Cycle (61 days in 14 s)`. The duration in the label is what makes a judge press
> it. Keep the small transport button in the chart strip as a secondary control. Raise the
> hint to `#8b949e` and move it directly beneath the cursor grip. Add an idle nudge: after
> 6 s with no interaction, pulse the cursor grip twice.

Also: **the replay cannot reproduce the alert.** `applyReplayRow()` (line 1678) calls
`renderGauge()` but never `renderAlert()`. If a presenter follows the script — force the
floating alarm, then hit replay — the red banner, the panel siren-glow and the full-screen
red vignette **stay on for the entire replay** while the gauge underneath sweeps through
0.00. Two contradicting alarm states on screen at once, in the exact order the demo script
prescribes. See P1-4.

---

## 3. Authenticity and trust — every fake-feeling detail

### 3.1 Two different baselines on one screen (**the worst problem in the build**)

- KPI tile: `STEAM / OIL RATIO — 1.29 t/m³` (the cycle actually simulated: 1500 t / 7 d /
  3.0 m³/d / 8 SPM).
- Bar chart 500 px below: `Baseline (mid-range settings) — 1.50`.
- Per `docs/reviews/integration_report.md` §4, the optimizer's baseline is a *different scenario
  entirely*: **1750 t / 9 d / 4.5 m³/d / 8 SPM**. That scenario is never simulated, never
  shown, and never labelled.

So the page simultaneously asserts a 1.29 baseline and a 1.50 baseline, and the headline
41.3% is computed against the one the judge cannot see. Against the cycle actually on
screen the improvement is **(1.29 − 0.88) / 1.29 = 31.7%**, and against the cycle Apply
actually produces (`BAKED.optimized`, SOR 0.906) it is **30.0%**.

An Oil India reservoir engineer will do that subtraction in their head during the pitch.
When the numbers do not reconcile, everything else on the screen becomes suspect —
including the parts that are genuinely rigorous.

> **Fix (P0-2), and be scrupulous about it.** Three bars, not two, explicitly labelled:
> `Field practice (1750 t / 9 d / 4.5 / 8 SPM) — 1.50` · `Today's run (1500 t / 7 d / 3.0 /
> 8 SPM) — 1.29` · `ML-optimised (as applied) — 0.91`. Then state **both** deltas in words:
> `−41% vs field practice · −30% vs today's manual run`. Two honest numbers beat one
> unexplained one. Whichever you lead with in the hero bar, the other must be visible on
> the same screen with its settings printed.

### 3.2 The telemetry ticker is the single most fake-feeling element

Source: `updateTicker()`, lines 1185–1201. It takes the last five *simulation rows* and
stamps them with **wall-clock timestamps 4 seconds apart** (`now - (n-i)*4000`).

What that produces on screen, verbatim from the captures:

- Idle: `17:01:01 · T_res 79.0 °C · μ 1724 cP` … `17:01:05 · T_res 77.6 °C · μ 1877 cP`.
  **The reservoir cools 1.4 °C and the crude thickens by 153 cP in four seconds.** These
  are day-58 and day-59 rows. A petroleum engineer reads that line and knows instantly
  the feed is synthetic — 1,150 m of rock does not change temperature on a 4-second tick.
- Mid-replay (Day 1): `17:01:18 · T_res 50.0 °C` then `17:01:22 · T_res 60.9 °C` — now it
  *heats* 10.9 °C in 4 s. And because only two rows exist at Day 1, the marquee shows
  **the same two timestamps twice inside one viewport width**. Duplicate clock readings,
  visible simultaneously.
- Every line prints `SPM 8.0` — **including during `phase inject` and `phase soak`, when
  the well is shut in and the pump is not stroking.** A live feed from a shut-in well
  reports `PUMP OFF` / `SHUT-IN`, not a stroke rate.
- The ticker's newest row is day 60 (`T_res 76.3 °C · μ 2037 cP`) while the cross-section
  HUD 200 px to the right reads day 61 (`T 75 °C · μ 2203 cP`). **Two "current" states,
  different numbers, same screen.** You asked me to check this specifically: confirmed,
  the ticker and the panels disagree.
- Status word is `OK` / `ALERT`. Real SCADA/DCS tags read `OK` / `ALM` / `SHUTIN` / `BAD`.

> **Fix (P0-4).** Either delete the ticker (the page loses nothing and gains 45 px of fold
> budget) or re-found it on cycle time:
> `D+58.3 · T_res 79.0 °C · μ 1,724 cP · pump 8.0 SPM · q_o 3.7 m³/d · OK`
> with a single honest header stamp elsewhere:
> `SIMULATED CYCLE · twin v1.0 · run 13-Sep-2026 17:02 IST`.
> Cycle-relative day stamps are what a CSS engineer expects, cost nothing, and remove the
> impossibility. Suppress SPM during inject/soak and print `SHUT-IN` instead.

### 3.3 Well identity is treated as a subtitle, not as an identity

`Well BGW-07, Baghewala Field, Rajasthan` is currently a 13 px grey clause inside a
run-on subtitle, sharing a line with the modelling method. Real ops products give the
asset a bordered identity block, always in the same place, because the operator's first
question is always *"which well am I looking at?"*

> **Fix:** a persistent identity card at the left of the header or the top of the
> cross-section panel:
> ```
> WELL BGW-07                        ● CSS CYCLE 12 · PRODUCE
> बगेवाला क्षेत्र, बीकानेर, राजस्थान
> Oil India Limited · Baghewala Field · TD 1,150 m · 15.5° API
> 11,500 cP @ 50 °C · P_res 11.4 MPa · steam 290 °C, 0.65 quality @ 74 t/d
> ```
> This also absorbs the three subtitle lines currently eating header height (§2.2).

### 3.4 Units discipline — mostly good, five real slips

Credit where due: the build is consistently metric-SI and the units are correct
(`t/m³`, `m³/d`, `kWh/m³`, `cP`, `kN`, `SPM`, `°C`). That is better than most hackathon
dashboards. The slips:

1. **kPa vs MPa.** Header says `P_res 11.4 MPa`; the code, API and baked series all carry
   `P_res_kPa: 11400`. Pick one and use it everywhere the judge can see it. (MPa is the
   right choice for display.)
2. **Steam quality shown as `x0.65`** in the cross-section's steam-generator box. `x0.65`
   is not a unit anyone writes. Use `quality 0.65` or `65% quality`.
3. **API gravity conflict.** The dashboard prints `15.5° API`. `docs/guides/GLOSSARY.md` §4 states
   the official problem statement says **17–19° API**, with 14–17° from field literature.
   You are showing a number that contradicts the PS the jury wrote. Either show the PS
   range or annotate: `15.5° API (SPE-23APOG; PS states 17–19°)`. Do not silently pick one.
4. **No thousands separators anywhere.** `1159 m³`, `11500 cP`, `1585 t` should be
   `1,159 m³`, `11,500 cP`, `1,585 t`. The header subtitle already does this correctly
   (`1,150 m`, `~11,500 cP`) — the *live* readouts do not. That inconsistency between
   hand-written and generated text is itself a tell.
5. **The gauge has no unit and no label.** A bare `0.54` under a green/amber/red arc, with
   an unlabelled red threshold tick. Label it `FLOATING RISK INDEX` with `0.60 = failure
   threshold` printed at the tick.

Bonus authenticity, cheap: print oil totals in **both** m³ and bbl —
`1,159 m³ (7,290 bbl)`. Oil India reports in both; showing both says "we have read a
production report."

### 3.5 Number precision — the 2-decimal tell, itemised

You are right that this is an AI fingerprint. Current state and what a real gauge would
show:

| Readout | Now | Should be | Why |
|---|---|---|---|
| SOR | `1.29 t/m³` | `1.29` ✔ | 2 dp is genuinely how SOR is reported — keep |
| Total oil | `1159 m³` | `1,159 m³ (7,290 bbl)` | separators; dual units |
| Energy intensity | `20.6 kWh/m³` | ✔ | fine |
| Cycle duration | `61 days` | `61.3 d` | `days_total` is 61.27; the KPI silently truncates, and the replay HUD says `DAY 61` — pick one |
| Peak rod load | `85.6 kN` | `86 kN` | field dyno readouts do not carry 0.1 kN; the model's own MAE is far larger than 0.1 |
| Floating index | `0.54` | ✔ 2 dp | a dimensionless index; correct |
| **Floating probability** | **`0.0011`** | **`0.1%`** | **4 decimal places on a probability is the loudest AI tell on the page.** No operator reads `0.0011`. |
| Optimizer cutoff | `7.8 m³/d` | `7.8` ✔ | fine |
| Optimizer SPM | `10.2 spm` | `10.2` ✔ | VFDs do step in 0.1 SPM |
| Improvement | `41.3%` | `41%` in hero, `41.3%` in table | hero rounds, instruments don't |
| Stroke length | `3.0 m` | ✔ but it is **hardcoded in HTML** (line 975), not read from data — a static literal dressed as a reading. Bind it to `P.stroke_m`. |

Mid-replay the KPI tiles also render `— t/m³`, `— kWh/m³`, `0 m³` and **`1 days`**. The
em-dash placeholders are fine and honest; `1 days` is not. Pluralise, or use the unit
abbreviation `d` throughout and dodge it.

### 3.6 What a real ops product has that this lacks

**No timestamps anywhere.** Not one "last updated", "computed at", "data as of". The only
clock on the page is the fake ticker. A real dashboard stamps every derived number.
Add, under the hero bar, right-aligned, 11 px:
`Cycle simulated 13-Sep-2026 17:02 IST · twin v1.0 · params/field_params.json rev 3`.
That single line does more for perceived legitimacy than any animation on the page.

**No run/recommendation identity.** Real recommendations are objects an operator can refer
to in a phone call: `REC-2026-0913-07`. Add an ID to the optimizer output and print it in
the table header. It costs one line and reads as a system of record.

**No operator affordances.** The alert banner cannot be acknowledged or silenced. There is
no "export cycle report", no "send set-points to VFD", no confirmation step. `Apply
Optimized Settings` silently moves four sliders — in a real product, pushing set-points to
a controller is a **two-step, audited action**.

> **Fix:** make Apply a two-stage control:
> `⇩ Stage Set-Points` → an inline confirm strip
> `Send steam 1,600 t · soak 3 d · cutoff 8.0 m³/d · 10.0 SPM to BGW-07 controller?
> [Confirm] [Cancel] — requires operator authorisation`
> → then the OPTIMIZED stamp, plus an audit line
> `Applied by operator · 17:04 IST · REC-2026-0913-07`.
> This is 20 lines of code and it is the difference between a chart and a product. It also
> converts the Apply click into a second dramatic beat for the pitch.

Give the alert banner the same treatment: severity tag, timestamp, and an `ACK` button.
`⚠ ALM-02 · ROD FLOATING RISK · FI 0.85 > 0.60 · D+42.1 · [ACKNOWLEDGE]`.

**Nothing surfaces `failures_expected`.** The twin computes it (`summarize()`, line 1336);
it never reaches the screen. `Expected rod failures this cycle: 0` is exactly the kind of
line that makes a maintenance engineer lean forward.

### 3.7 Data-source honesty — done timidly, should be done proudly

Current state: a `MOCK DATA` pill, and a 12 px grey footer reading *"Digital-twin
approximation for demonstration purposes."* Worse, `docs/guides/DEMO_SCRIPT.md` line 58 coaches
the presenter that the pill *"is not visible from a distance and the script never draws
attention to it."*

That instinct is backwards and it is a jury risk. If a judge notices unprompted — and one
will, the pill is amber and blinking — the read is concealment, and concealment is fatal
in a room of engineers. Honesty volunteered is credibility; honesty discovered is a
finding.

Also, `MOCK DATA` is the wrong *register*. It is developer jargon that sounds apologetic
("fake"). What the page actually contains is far more defensible: **verbatim output of a
validated physics simulator running real Baghewala field parameters, with 24/24 physics
tests passing.**

> **Fix (P1).** Replace the pill with a two-line provenance chip, always visible, never
> apologetic:
> ```
> ● SIMULATED · physics twin v1.0
>   real Baghewala params · 24/24 tests · no live SCADA link
> ```
> and give it a hover/click that opens a small provenance panel: parameter sources
> (OIL internal PPT, SPE-23APOG-535203, GEOHORIZONS 2015), model list (Marx-Langenheim,
> Andrade, Vogel IPR), test count, ML training set (3,000 LHS cycles), surrogate metrics
> (R² 0.72, MAE 0.31). Then coach the presenter to say it out loud at 0:25:
> *"Everything on this screen is our own physics simulator running Oil India's published
> Baghewala parameters — no SCADA feed, and we'll show you the parameter sources."*
> Volunteering it makes the rest of the numbers land harder.

### 3.8 The 0.88 that is never actually achieved

The optimizer table recommends `1585 t / 3 days / 7.8 m³/d / 10.2 spm → 0.88 t/m³`.
`OPT_APPLIED` (line 1242) snaps to `1600 / 3 / 8.0 / 10.0` because the sliders step in
50 t / 0.5 m³/d / 0.5 SPM, and `BAKED.optimized` for those settings yields **SOR 0.9062**.

So when the presenter clicks Apply in front of the jury, the SOR morph animates to
**0.91**, while the recommendation table three inches away still reads **0.88** and the
improvement pill still reads **41.3%**. Nobody explains the gap. It looks like the model
missed.

> **Fix (P0-6).** Add an "as applied" row to the table and reconcile it in the open:
> `Recommended (continuous) 1,585 t · 7.8 m³/d · 10.2 SPM → 0.88 t/m³`
> `As applied (controller steps) 1,600 t · 8.0 m³/d · 10.0 SPM → 0.91 t/m³`
> Then the drift is not an error, it is **domain literacy** — real set-points are
> quantised by what the controller can actually command. Handled this way, a landmine
> becomes one of the most credible details on the page.

### 3.9 Two instruments disagreeing during replay (visible in the capture)

In the `?autoreplay` screenshot at Day 1 / inject: the gauge reads **0.54** while the dyno
stat line 250 px to its left reads **Floating index: 0.00** — same instant, same quantity,
two values. Cause: `renderGauge()` (line 1493) keeps its 450 ms Plotly transition, and
during replay it is re-invoked on every row change (several per second), so the gauge is
permanently mid-tween and never settles on the true value. It lags the rest of the
dashboard for the whole replay.

> **Fix (P0-7):** mirror `renderDynoLive()` — a `renderGaugeLive()` with no transition for
> replay frames, keeping the 450 ms version for discrete Simulate/Optimize renders.

### 3.10 Smaller tells, in descending order

1. **Optimizer panel titled "ML-Optimized"; the demo script says "Bayesian optimizer"; the
   code comment says "XGBoost surrogate trained on 3000 LHS cycles."** Three different
   claims for one component. A judge who asks *"which is it?"* mid-pitch is a bad moment.
   Settle on the truth (surrogate-assisted search over an XGBoost model) and make the
   panel title, the script and the comment agree.
2. **No uncertainty anywhere**, despite `metrics.json` reporting R² = 0.72, MAE = 0.31.
   The bar chart draws `0.88` as a hairline-precise column. See P1-1 — this is the highest
   value-per-line-of-code fix in the review.
3. `Baseline (mid-range settings)` as an x-axis category label is developer shorthand.
   Field practice is not "mid-range settings."
4. The `OPTIMIZED` rubber stamp rotates −8° over the *controls* panel, not over the result.
   Charming, but it is stamping the inputs. Move it to the optimizer panel, or over the
   hero bar.
5. Panel header hint text `(approximate, from peak rod load & floating index)` is honest
   and good — keep it. But `(live twin state)` on the cross-section is not accurate when
   the twin is sitting at cycle-complete; use `(cycle end-state)` / `(replay D+n)`.
6. Contrast: `#586069` on `#0d1117` (≈2.6:1) is used for the scrub hint, the depth ruler
   labels, the pay-zone caption and the footer. Below WCAG AA. Lift to `#8b949e`.
7. The cross-section's depth ruler labels `250 / 500 / 750 / 1000` omit the unit after the
   first tick, and `1150` is the TD, not a round tick — label it `1,150 m TD`.
8. The `Digital India · Make in India` badge with a tricolour dot, plus the animated
   tricolour sweep bar, is one flag gesture too many for a jury of engineers. Keep the
   thin static tricolour rule (it is tasteful); drop the badge and the sweep animation.
   Government juries respond to competence signalling, not patriotism signalling.

---

## 4. Regional / bilingual UX

Currently **zero Devanagari** on the page. For a Rajasthan-sited asset presented to an
Oil India jury, a small amount of Hindi reads as respect for the operating context. A lot
of it reads as decoration — and worse, a full EN/HI toggle invites a judge to click it and
find half the interface untranslated.

**Recommended pattern: English primary, Devanagari secondary, in exactly three places. No
toggle.** A toggle is a promise to translate everything, including axis titles, Plotly
tooltips and the glossary — a promise this build cannot keep before the deadline, and a
half-kept promise is worse than none.

### Where Hindi adds authenticity

1. **The well identity block** — the strongest and most genuine placement:
   ```
   WELL BGW-07 · कूप BGW-07
   बगेवाला क्षेत्र, बीकानेर, राजस्थान
   Baghewala Field, Bikaner, Rajasthan · Oil India Limited
   ```
   Naming the district (बीकानेर) is what makes it land as local knowledge rather than a
   translated string. "Rajasthan" alone is what an outsider says; "Bikaner" is what someone
   who has looked at the block map says.
2. **The three phase chips** — the CSS vocabulary is the domain vocabulary, and these are
   the words an operator at the wellhead actually uses:
   `INJECT / अंतःक्षेपण` · `SOAK / सोख` · `PRODUCE / उत्पादन`.
   English on the first line at current size, Hindi beneath at 11 px, 70% opacity.
3. **The alarm banner** — the one place bilingual text is functional rather than decorative,
   because alarms are read by whoever is nearest the screen:
   `⚠ ROD FLOATING RISK — REDUCE SPM`
   `रॉड फ्लोटिंग जोखिम — पंप गति घटाएँ`

### Where Hindi becomes noise — do not translate

Axis titles, units, KPI labels, the optimizer table, panel headers, button labels, the
telemetry ticker. Instrument labels in Indian oilfield practice are English; translating
`Steam / Oil Ratio` to `भाप/तेल अनुपात` in a KPI tile looks like machine translation to the
very people who use the English term daily. Technical register beats linguistic
completeness.

### Devanagari at small sizes on Windows (Nirmala UI) — concrete constraints

The current stylesheet will actively damage Devanagari if Hindi is dropped in as-is:

1. **Font stack.** The page declares `-apple-system, "Segoe UI", Roboto, Helvetica, Arial`
   — none of these carry Devanagari, so Windows silently falls back per-glyph and the
   Hindi renders in a different weight and baseline from its English sibling. Add:
   `font-family: "Nirmala UI", "Noto Sans Devanagari", "Mangal", sans-serif;` on the Hindi
   spans specifically.
2. **Minimum size 13 px.** Nirmala UI's matras (ि ी ु ू े ै ो ौ) and the shirorekha collide
   below ~12 px on a 1× projector. The 10.5–11 px used for `.kpi-label`, `.phase-chip` and
   `.badge` is **too small for Devanagari**. Any chip carrying Hindi needs its own rule at
   ≥13 px.
3. **`letter-spacing` must be `normal`.** `.phase-chip` uses `0.08em`, `.badge` `0.05em`,
   `.kpi-label` `0.06em`. Positive tracking breaks Devanagari conjuncts and detaches
   matras from their base glyphs. Override to `letter-spacing: normal` on every Hindi span.
4. **`text-transform: uppercase` is a no-op on Devanagari** but it is applied to all three
   of those classes — harmless, but it means the Hindi will look visually "unstyled" next
   to its all-caps English partner. Set the Hindi line in a distinct treatment (slightly
   dimmed, normal case, 13 px) rather than trying to match the caps.
5. **`line-height: 1.4` is too tight.** Devanagari needs ≥1.6 or descender matras clip
   against the next line. Set `line-height: 1.65` on Hindi spans.
6. **Cap weight at 600.** Nirmala UI has no true 700/800 — Windows synthesises the bold and
   the smearing destroys matras at small sizes. The page uses `font-weight: 700` on chips
   and labels.
7. **Mark it up properly:** `<span lang="hi">…</span>`. It fixes shaping and font
   selection, and it is the correct accessibility behaviour for screen readers.

### One Rajasthan-specific touch that lands as genuine

Beyond the district name, the highest-signal detail available: annotate the cross-section's
pay-zone band with the actual formation, not a generic label. It currently reads
`BAGHEWALA PAY ZONE · TD 1,150 m · 15.5° API HEAVY CRUDE`. Naming the geology
(Bikaner-Nagaur basin, Jodhpur/Bilara group — verify against `docs/research/baghewala_facts.md`
before printing it) tells a jury of Oil India geoscientists that the team read the field
literature rather than the problem statement. One line, correctly sourced, worth more than
every animation on the page.

Do **not** add: Rajasthani decorative motifs, jharokha borders, mandala patterns, or a
desert/dune background. Industrial dark-mode is the right register and the build already
gets that right — stay there.

---

## 5. Cognitive load — too many animations, and the wrong ones

Counted from source, **animations running simultaneously in the idle state** (no
interaction, cycle complete):

| # | Animation | Selector / line | Verdict |
|---|---|---|---|
| 1 | Ambient "steam" drift, 34 s | `body::before` :44 | **Keep** — 3.5% opacity, genuinely subliminal |
| 2 | Header shimmer sweep, 6 s | `header::after` :71 | **Cut** — a marketing-page gesture on an ops product |
| 3 | Tricolour sweep, 4.5 s | `.tricolor-bar::after` :97 | **Cut** — keep the static rule |
| 4 | Status-dot blink, 1.8 s | `.status-dot` :151 | **Keep** — a blinking status LED is genuine ops vocabulary |
| 5 | Telemetry marquee, 22 s | `.ticker-track` :180 | **Cut or gate** — see §3.2; a horizontally scrolling strip is the most attention-stealing element on the page and carries the least trustworthy data |
| 6 | Header pumpjack nod, 2.2 s | `.pj-beam/.pj-rod` :470 | **Gate** — it nods forever, including while the well is shut in during inject/soak. A pumpjack stroking during a soak phase is a physical impossibility a jury will catch |
| 7 | Cross-section pumpjack + rod bob | `#xsec.phase-produce` :562 | **Keep** — already correctly phase-gated. This is the model animation for the whole page |
| 8 | Oil droplets rising, 2.1 s | `.xs-oil` :581 | **Gate to replay** — at rest on Day 61 the well is producing 2.9 m³/d, near cutoff, and the animation streams at full rate. Modulate rate with `oil_m3d`, or freeze when idle |
| 9 | KPI droplet fall + ripple, 2.2 s | `.kpi-droplet` :410 | **Cut** — decorative, on a *cumulative total*, which does not drip |
| 10 | Well-schematic flow dashes | `.well-flow` :490 | **Cut** — a 26×60 px icon in a panel header, competing with the 340×600 px cross-section that shows the same thing properly |
| 11 | Micro-parallax grid | `wireParallax()` :1923 | **Cut** — a background that moves with the mouse is a portfolio-site signature. It is also the clearest single "AI-generated template" tell in the build |

**Nine continuously looping animations at rest** (excluding 7 and 8, which are legitimately
state-driven). Plus, on interaction: panel entry cascade, count-ups, KPI flash, 10 spark
particles, the rubber stamp, button shimmer, the SOR morph pill, and — when alarmed —
banner pulse + icon pulse + panel siren-glow + full-screen red vignette.

**The problem this creates:** with nine things moving, motion carries no information.
When the twin *actually* changes state — phase transition, alarm, optimizer result — the
motion that signals it is indistinguishable from the ambient noise. The page has spent its
entire motion budget on decoration and has none left for meaning.

### Motion policy — three tiers

- **Ambient (idle, ≤3 loops):** background steam drift, status LED, and the cross-section
  pumpjack *only when the twin state is `produce`*. Nothing else moves at rest.
- **State-driven (data leads):** phase chips, halo scaling, steam/oil particles, gauge
  needle, dyno redraw. All bound to twin state, all suppressed when the twin is idle.
- **Event (one at a time, then stop):** count-ups (650 ms), KPI flash, SOR morph, the
  stamp, the alarm. These are the page's punctuation — they only work if the ambient layer
  is quiet.

Removing 2, 3, 5, 9, 10 and 11 costs the page nothing a judge will miss and makes the
replay — the genuinely impressive thing — read as the main event instead of one more
moving object. It also removes a per-frame `pointermove` handler and a 22 s marquee
repaint from a projector-driven laptop.

Also: the `prefers-reduced-motion` block (line 714) is present and correct. Good — keep it,
and note it out loud if a judge asks about accessibility.

---

## 6. Prioritised fix list

### P0 — before the pitch (7 items)

**P0-1. Build the hero result bar.** Full-width band under the tricolour rule, above the
controls. `1.29 → 0.88 t/m³` at 40 px, `▼ 41%` at 64–72 px green, an annual-rupee cell with
its assumptions printed at 10.5 px, and the well identity line. Demote the gauge number
from 30 px to 22 px and label it. *Fixes the 8-second failure.* (§1)

**P0-2. Reconcile the two baselines.** Three labelled bars — field practice 1.50 (settings
printed), today's run 1.29, ML-optimised as-applied 0.91 — and state both deltas: `−41% vs
field practice · −30% vs today's manual run`. *The largest credibility hole in the build.*
(§3.1)

**P0-3. Delete the boot-time `runOptimize()` (line 2019).** Ship the optimizer panel empty
with a deliberate idle state so the Optimize click actually reveals something. *Restores
the demo's central dramatic beat, one line of code.* (§2.1)

**P0-4. Fix or remove the telemetry ticker.** Wall-clock stamps 4 s apart on day-scale
reservoir physics; duplicate timestamps in one viewport during replay; `SPM 8.0` reported
while the well is shut in; disagrees with the cross-section HUD by a full day. Re-found on
`D+58.3` cycle time with a single honest run stamp, or cut it. (§3.2)

**P0-5. Fix the 1366×768 fold.** Header ≤96 px, KPI strip promoted above the fold, replay
control promoted to the button row, `MOCK DATA` pill pinned right at all widths. Target:
hero bar + controls + KPIs + top of the time-series chart all inside 768 px. (§2.2)

**P0-6. Add the "as applied" row to the optimizer table.** `Recommended (continuous)
1,585 t → 0.88` vs `As applied (controller steps) 1,600 t → 0.91`. Turns a visible
discrepancy into a display of domain literacy. (§3.8)

**P0-7. Add `renderGaugeLive()` with no Plotly transition for replay frames.** The gauge
currently reads 0.54 while the dyno stats read 0.00 at the same instant. (§3.9)

### P1 — high value, do if there is a day left

1. **Put an uncertainty band on the ML bar:** `0.88 ± 0.31 t/m³ (surrogate MAE, R² 0.72,
   n = 3,000)`. Highest credibility-per-line-of-code in this review — a stated error bar is
   the strongest possible signal that the team understands its own model.
2. **Two-stage, audited Apply** with a confirm strip and an audit line, plus `ACK` and a
   severity tag on the alarm banner. (§3.6)
3. **Reframe `MOCK DATA` as a proud provenance chip** with a sources popover, and change
   the demo script to volunteer it at 0:25 instead of hiding it. (§3.7)
4. **Call `renderAlert()` from `applyReplayRow()`** so the alarm state follows the replay —
   currently a forced alarm stays lit through an entire replay that reads 0.00. (§2.3)
5. **Add the run stamp:** `Cycle simulated 13-Sep-2026 17:02 IST · twin v1.0 · params rev 3`
   under the hero bar, plus a `REC-2026-0913-07` id on the optimizer output. (§3.6)
6. **Apply the motion policy:** delete the header shimmer, tricolour sweep, KPI droplet,
   panel-header flow icon and micro-parallax; gate the header pumpjack to `produce`. (§5)
7. **Well identity block** with `बगेवाला क्षेत्र, बीकानेर, राजस्थान`, absorbing the three
   subtitle lines. (§3.3, §4)
8. **Number formatting pass:** thousands separators everywhere, `0.1%` not `0.0011`,
   `86 kN` not `85.6`, `61.3 d` consistently, `1 day` not `1 days`, bind stroke length to
   `P.stroke_m`. (§3.5)
9. **Promote the replay** to `▶ Replay Cycle (61 days in 14 s)` in the main button row;
   raise the scrub hint to `#8b949e` and move it under the cursor grip. (§2.3)
10. **One-click `⚡ Stress Test (12 SPM)`** button so the alert theatre is one action, not
    three. (§2.1)

### P2 — polish

1. Bilingual phase chips (`INJECT / अंतःक्षेपण`) and bilingual alarm line, with the Nirmala
   UI rules from §4 (≥13 px, `letter-spacing: normal`, `line-height: 1.65`, weight ≤600,
   `lang="hi"`).
2. Resolve the API-gravity conflict on screen: `15.5° API (SPE-23APOG; PS states 17–19°)`.
3. Dual units on oil totals: `1,159 m³ (7,290 bbl)`.
4. Name the formation in the pay-zone band (verify against `docs/research/baghewala_facts.md`).
5. Surface `failures_expected: 0` as a KPI or a line in the dyno panel.
6. Fix contrast on `#586069` text (≈2.6:1) — lift to `#8b949e`.
7. Label the gauge threshold tick `0.60 — failure threshold`; fix `x0.65` → `quality 0.65`;
   fix `P_res` kPa/MPa consistency; `1,150 m TD` on the depth ruler.
8. Move the `OPTIMIZED` stamp off the controls panel and onto the result.
9. Retitle `Baseline (mid-range settings)` → `Field practice (current manual set-points)`.
10. Reconcile "Bayesian optimizer" (demo script) / "ML-Optimized" (panel title) / "XGBoost
    surrogate" (code comment) to one consistent claim.
11. Drop the `Digital India · Make in India` badge and the tricolour sweep; keep the static
    tricolour rule.
12. `(live twin state)` → `(cycle end-state)` / `(replay D+n)` on the cross-section header.

---

## Closing note

The engineering underneath this dashboard is real: baked verbatim simulator output, real
Baghewala parameters, 24/24 physics tests, a trained surrogate with published metrics, a
cross-section that is correctly phase-gated to the twin state. That is a genuinely strong
submission.

The UI does not currently *say* any of that. It says "a competent developer built a
dark-mode dashboard." The gap between what this project is and what it looks like is almost
entirely closable with P0-1 (make the result the biggest thing on screen), P0-2 (make the
numbers reconcile), and P1-1 (put an error bar on the prediction). Those three fixes convert
a good hackathon dashboard into something an Oil India engineer would believe came off an
internal tool — because the tell of a real product is not polish. It is that the numbers
agree with each other, that it admits what it does not know, and that it tells you when it
last looked.
