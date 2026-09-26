# Live Demo Script (dashboard v4, four pages, about 2:45 spoken)

> **Status 27 Sep 2026 — physics wave 5, operating policy as a control (rev 13).** A
> technical re-score of the rev-12 engine (58/100) found its headline gain was mostly a
> **pull-rule artefact** — the baseline was compared while it got pulled off the well the
> moment its rods floated, which is not the only thing an operator can do. Wave 5 makes
> the operator's **response to rod float itself a policy**: `pull` (end the cycle
> immediately), **`vfd_hold`** (slow the pump with a VFD to hold the float index at a safe
> 0.6 instead of pulling — the **recommended** policy), `vfd_then_pull`, or `none`. The
> SAME policy is now applied to the baseline, the recommendation, and the cold
> counterfactual, so every ₹ comparison names which policy the baseline is assumed to run.
> ₹ decisions run on **net cash per cycle-day** at OIL's own confirmed FY25 crude
> realisation, with the older $65/bbl planning floor and a new **net-of-royalty-and-cess**
> deck both shown as comparison presets. **263 tests pass, 2 are known, disclosed gaps
> marked xfail** (no interior soak optimum; the steam optimum at the mid-range diesel
> price sits below the BGW-8 slug range). **The dashboard's own baked scenarios are being
> re-baked to match this cascade** (see `docs/PROJECT_LOG.md` §16.7) — by demo time the
> screen and this script should agree; if they still don't, say so honestly and name the
> gap rather than reading a stale number. If a judge pushes on anything not covered here, use the safe-to-say block in
> `docs/study/viva_prep.md` / `docs/study/hinglish-pack/06_JUDGE_KE_SAWAAL.md`.

**Goal, in order:** (1) we understand the problem, (2) we can simulate the coupled
steam and pump physics, (3) we can flag a rod-floating failure before it happens,
(4) the optimiser gives an **advisory** recommendation that an engineer confirms, and
(5) we are honest about what is and isn't validated. Keep sentences short and say
the bolded terms out loud, because judges listen for domain vocabulary.

---

## Before you start (setup checklist, in order)

- [ ] **MOCK mode only.** `const MOCK = true;` is at `dashboard/src/core.js:9` and is
      already `true` in the four built pages — it serves baked physics output. **Note:**
      the dashboard team is re-baking the scenarios to match rev 13 (`docs/PROJECT_LOG.md`
      §16.7); rehearse against the current build and confirm the screen matches this
      script before you go on. If it still doesn't by demo time, name the gap plainly
      rather than reading a stale number. If you ever edit `src/`, rebuild with
      `node dashboard/build.js`; never edit
      the built HTML. A live API demo is safe to run from the current branch if a judge
      insists — see the Appendix — but MOCK stays the default for the main walkthrough.
- [ ] **Console "Rod-float response" selector may be hidden.** It's cosmetic (it only
      changes explanation text, not the physics shown) and the dashboard team may hide it
      pending a real fix — don't gesture at it or promise it does something if it isn't on
      screen.
- [ ] **Clear the demo state** so the optimiser history is empty and the console starts on
      **our assumed baseline** (1,300 t / 10 d / 91 kgf/cm² / 86-in / 5 spm,
      **VFD-hold** policy). Either use a fresh browser profile, or open DevTools on any of
      the pages → Console → `localStorage.removeItem("bgw.v4")` → reload.
- [ ] **Pre-open all four tabs** from `dashboard/` in Edge or Chrome, in this order:
      `index.html` (Overview) · `console.html` (Twin console) · `optimizer.html`
      (Optimiser) · `methodology.html` (Model basis, including the field-view scheduler
      section if built).
- [ ] **Plotly is bundled locally** (`dashboard/vendor/plotly.min.js`), so the charts draw
      with no internet. Pre-opening the tabs still warms the browser cache. Check that the
      time-series chart and the dyno card actually draw on the console tab.
- [ ] Zoom so the console's time-series, cross-section, dyno card and risk meter are all
      visible without scrolling (the alarm banner is fixed to the bottom of the viewport).
- [ ] **Confirm the Recommendation page's baseline-policy toggle is set to "VFD-hold"
      (fair comparison)** before you start, and **leave it there** through the honesty
      moment (1:40–2:15 below) — show only the fair number on screen; the other two
      baseline policies are said in one sentence, not shown live on the toggle.
- [ ] Status bar bottom-right should read the current test tag; **say "263 passed, 2 known
      gaps marked xfail"** out loud regardless of what the badge shows, and note honestly
      if the badge itself is pending its own re-bake.
- [ ] **Tabs don't live-sync.** After *Confirm* on the Optimiser, use that page's own
      **Twin console** button, or switch to the console tab and press **F5** so it picks
      up the staged set-points.
- [ ] Do a full dry run with a stopwatch. Target **2:45 spoken**. Clicks, the replay
      and pauses push the wall-clock time to about 3:00.

---

## Timeline

| Time | Page and click | What you say |
|---|---|---|
| **0:00–0:20** | **Overview** tab (`index.html`). Don't click. Gesture at the page title *Cycle result: BGW-07*. | "Baghewala's crude is **eight to fifteen thousand centipoise** at fifty degrees. It only flows because Oil India steams each well: **cyclic steam stimulation**, meaning inject, **soak**, produce. Every tonne of steam burns about seventy kilos of diesel. And the same thick oil that steam thins is what makes the **sucker rods float** and fail. So we built one twin that models both halves together." |
| **0:20–0:35 — the 15-second moment** | **Twin console** tab. Set-points are **our assumed baseline**, 1,300 t · 91 kgf/cm² · 86-in · 10 d · 5 spm, **VFD-hold** policy. Click **Simulate cycle**, then **Replay** and let it run to the late produce phase. Point at the water-cut trace and the floating-index trace together as they cross, then at the banner that fires when the index hits the line. | "Watch these two lines. Water cut — how much of what's produced is water, not oil — starts high, from steam condensate coming back, and falls all cycle. Right where it crosses this line, the stream flips from mostly water to mostly oil, and the rods start to **float** — the floating index climbs here. Now watch this banner: the unit doesn't just get pulled off the well. A **VFD slows the pump down** to hold that float index right at the safe limit instead. That's the moment I want you to notice: **the operator's response to floating rods is a real, watchable control action in this model**, not a background assumption." |
| **0:35–1:00** | Keep talking over the rest of the replay. | "Underneath, it steps real physics day by day: **Marx–Langenheim** for how far the heat goes, a viscosity-temperature law, **Vogel inflow**, rod-string mechanics, and now an **injection-pressure** and **stroke-length** model too. The same viscosity — and now the same water cut — drives both the oil rate and the rod load. That coupling is the whole project." |
| **1:00–1:20** | *(Optional, 30-second beat if time allows)* Click **Upload a card** on the dyno panel and load the sample measured-card CSV. | "This panel also takes a **measured** card straight from the field — position and load, nothing else — and a classifier reads off the fault type. It's never seen a real Baghewala card, so we call every result a first read to confirm with a specialist, not a diagnosis." |
| **1:20–1:40** | Click **Stress test (12 spm)**. The alarm banner *Rod floating risk: reduce SPM* fires. Click **ACK**. Point at the dynamometer card. Note out loud: this stress test currently runs the **approximate (baked) model**, not a fresh true-physics re-simulation at 12 spm — the dashboard team is fixing it so 12 spm actually changes the curve; if the screen looks identical to the 5-spm case, say so rather than narrate a change that isn't there. | "Push the pump faster and the same mechanism shows up sooner: more viscous drag on the downstroke, the rod string can't fall as fast as the unit drives it, it goes slack and buckles. This dynamometer card is **computed** — a rod wave-equation solve, not a sketch — and its separation onset uses the same drag law as the 0.6 alarm line, so it's not an independent check, just the same physics shown two ways. This particular stress-test view runs our fast, approximate model rather than a fresh physics run — the true twin agrees with this mechanism, but I'd want you to know which one you're looking at." |
| **1:40–2:15 — the honesty moment** | Click **Optimiser** in the app bar → **Run optimiser** → let the Recommendation table render — **leave the baseline-policy toggle on VFD-hold, the fair comparison; don't cycle through all three settings live, it takes too long to land** → **Stage set-points** → **Confirm** → the page's **Twin console** button → **Load into console**. | "Our recommendation: run the rods **slower**, starting at four-and-a-half strokes a minute against our assumed baseline's five, a shorter sixty-four-inch stroke against its eighty-six — both baseline numbers are our own pump-setting assumptions, not Oil India's practice — and let the VFD hold the float index instead of pulling — produce until it's been held at the floor for three days. Steam-oil ratio goes from **three-point-two-nine down to two-point-eight-three**, same policy both sides. Net cash gain: **three thousand, three hundred thirty-two rupees a cycle-day**, against a baseline that slows down the same way we do — that's the fair, apples-to-apples number, and it's the one on screen. If the baseline instead pulls the well the moment it floats, the number looks bigger — about twelve thousand nine hundred — and if it does nothing about float at all, the number is smaller still — those two compare us to a different baseline, so we lead with the fair one and mention the other two only to say they exist." |
| **2:15–2:30** | *(Optional, 30-second beat if time allows)* Click **Model basis** → **Field view**. | "Baghewala runs about thirty wells off one shared steam generator. This view answers which well gets steam next, every well on the same VFD-hold policy: a naive, same-for-every-well schedule now **earns** about seventy-two thousand rupees a day field-wide; optimising each well and then choosing which ones to steam adds another thirty-seven thousand a day on top of that." |
| **2:30–2:45** | Click **Model basis** (`methodology.html`). Scroll slowly past *Validation status* and *What has NOT been validated*. | "This is our honesty page. A technical re-score of our engine found that an earlier version's headline number was really the pull rule in disguise — we rebuilt the comparison so the operator's response to floating rods is its own control, applied fairly to both sides. Two hundred sixty-three of two hundred sixty-five tests pass; two are disclosed gaps — no interior soak optimum, and a steam-slug size that comes out smaller than what Oil India's own first job used at our assumed diesel price, which we flag rather than hide. This is synthetic, not field-validated. Our first ask of Oil India is now **whether operators actually slow the pump or pull the well when rods float** — the single measurement that would tell us which of the baseline-policy numbers I mentioned earlier is the real one." |

**Order, summarised:** problem → the water-cut/float "VFD-slowing" moment → coupled
physics → (optional) measured-card upload → forced rod-floating alarm → advisory
recommendation + the baseline-policy honesty moment → (optional) field view → honesty
page. If you are short on time, cut the two optional beats first, then the stress-test
narration — **never** cut the 15-second VFD moment, the fair-number honesty moment, or the
honesty page.

**Timing note.** The core (non-optional) script is about 2:15 spoken; the two optional
30-second beats bring it to 2:45–3:00 if time allows. If the dry run runs long, drop the
measured-card upload beat first, then the field-view beat.

---

## Wording rules (things older scripts said that are now wrong, or still apply)

- **Never** "the baseline the field is running today". The console's default and the
  overview's first column are **our assumed baseline** (1,300 t / 10 d /
  91 kgf/cm² / 86-in / 5 spm) — the 1,300 t is from Oil India's own **BGW-8 first CSS
  job (Dec 2018)**, one documented data point; the 86-in stroke, 5 spm and the 1.3
  m³/d cutoff are **our own pump-setting assumptions**, **not** OIL's current
  operating practice, and 87% of the fair same-policy gain comes from changing two of
  those (stroke and cutoff). It
  **itself floats its rods**, and how it responds to that (pull / VFD-hold / do nothing)
  is now a named toggle, not a fixed assumption. Say exactly that if asked.
- **Never** "a set-point an operator can act on today", or "feeds back to the steam and
  VFD controllers". Say **advisory mode**: there is no SCADA link, and the status bar
  says so. **As of rev 13 the VFD response IS modelled as its own control**
  (`css.float_policy`), not just the SPM set-point schedule — but it is still advisory,
  not a live SCADA hook.
- **The dynamometer card is computed** — a Gibbs (1963) rod wave-equation
  finite-difference solve (`twin/dyno.py`, baked via `dashboard/src/dyno-data.js`), not
  an illustrative sketch and not an RP-11L chart look-up. Separately, a **measured-card
  classifier** (`ml/dyno_classifier.py`) reads an uploaded, real card and flags a fault
  type — 94.8% hold-out accuracy on synthetic cards, but it has never seen a real one, so
  say "a first read, not a validated diagnosis" if asked.
- **Rod floating physics:** the rods **can't fall as fast as the pumping unit drives
  them** (viscous drag). They do **not** "fall faster than the fluid" or "free-fall".
  Floating is a **late-cycle** event driven by the water-cut inversion, not a risk
  present at every point in the cycle — and, as of rev 13, **what happens once it starts
  floating is a policy choice**, not a fixed rule.
- **The cycle now ends on a rule, under whichever float policy is active.** Under
  `vfd_hold`, the well is pulled only after 3 consecutive alarm days *at the 2-spm floor*
  (the VFD holds it there first); under `pull`, it is pulled after 3 alarm days outright;
  under `none`, it runs to the rate cutoff only. Say "we let the VFD hold the float line,
  and only pull after three days at the floor" for the recommended policy — not "we pull
  the well when the float alarm has persisted three days" (that is the `pull`-policy
  description, and is what the baseline does if you toggle it that way).
- **Money and carbon strip on the Overview:** if it shows a stale counterfactual pending
  re-bake, say so. The recommendation's **real** headline saving is net cash per
  cycle-day (below), and it must always be paired with which baseline policy it's
  measured against. Never annualise by dividing 365 by the simulated cycle length.
- **The primary claim (say this, not any single unlabelled number, and lead with this one
  on screen):** net cash per
  cycle-day, same policy (both VFD-hold): **+₹3,332** (FY25) / **+₹4,319** ($65) /
  **+₹5,382** (net of levies); SOR **3.29 → 2.83**. Say the other two baselines in one
  sentence, not as a second headline: if the baseline instead pulls at the
  first alarm: **+₹12,917** (FY25) — ~68% of that bigger number is
  the policy switch, not the set-points. If the baseline does nothing about float:
  **+₹2,622** (FY25, TIER1 §12.6 "mixed" row) — the canonical recommendation still gains
  there too; an earlier draft of this line said "−₹3,865, the recommendation loses" —
  that number belongs to a different, non-canonical plan and is retired. Either way, rod
  damage stays entirely unpriced.
  **Always name the baseline's policy** next to any gain number — never quote one alone.
  **Always add:** the same-policy decomposition — stroke 57%, cutoff 30%, steam 11%.
- **Never claim an absolute CO₂ reduction per cycle as a law of the physics, and never
  say "makes more oil"** — under the same VFD-hold policy the recommended cycle burns
  **23% less steam for 11% less oil** (1,000 vs 1,300 t steam; 353 vs 395 m³ oil), so
  SOR falls (steam per m³ 3.29 → 2.83) and CO₂ per m³ oil falls too, but that is a
  same-policy reading, not universal, and it is *less* oil, not more.
- **Never claim the model recommends a soak duration.** Soak is held fixed at 10 days,
  field practice — under the float-onset rule, margin per cycle-day actually falls
  slightly beyond about 5 days of soak, so an optimiser number for soak would be an
  overclaim. Say "field practice, model-insensitive, not optimised."
- **Tests:** say **"263 passed, 2 known gaps marked xfail"** — soak, and a mid-diesel-price
  steam optimum below the BGW-8 slug range — regardless of what badge the (pending
  re-bake) dashboard currently shows. There is no 21/24, 24/24, 57/57, 60, 116/127, or
  197/236/238 badge that is current.
- **Provenance line:** say "Physics rev 13 — operating policy as a control, fair
  same-policy baseline, calibrated to published Baghewala benchmarks and a real CalGEM
  field-SOR band; synthetic data, not field-validated" even if the page itself lags
  pending re-bake.
- **Well label:** the dashboard says **BGW-07**, a representative label for a single
  well. The field's first CSS well was **BGW-8** (Dec 2018), which is what the baseline
  scenario is derived from. If asked: "it's a label for one representative well; we
  don't have any single well's data."
- **Never say "the BL delta factor is unverified".** It's sourced: exactly the ½ inside
  Boberg & Lantz's own 1966 equation, forced by energy conservation.
- **Never quote gross margin, or any gain number, as profit without naming the baseline's
  float policy.** ₹ decisions run on net cash per cycle-day, counterfactual-free; the
  cold well is **shut in**, not pumpable, under every float policy in the current model
  (the old "idealised pumpable cold well" framing is the more conservative reading and
  can be mentioned, but is not the default one).
- **Never call the measured-card classifier "field-validated".** It's 94.8% accurate on
  synthetic cards only.
- **Numbers you may say, current build:** SOR 3.29 → 2.83 (same policy, VFD-hold); net
  cash/cycle-day gain +₹3,332/+4,319/+5,382 (FY25/$65/net-of-levies), same policy; if the
  baseline pulls +₹12,917 (68% is the policy switch); if it does nothing +₹2,622; gain
  decomposition stroke 57% / cutoff 30% / steam 11%; 263/265 tests, 2 disclosed xfails.
  **Never say:** −30%, −41.3%, rev-5's "+188% margin", rev-9's "+4,423/cycle-day",
  a lone **"−₹3,865/cycle-day"** for the recommendation vs. a do-nothing baseline (that
  number belongs to a different, non-canonical plan and is retired — the canonical
  recommendation gains +₹2,622 there),
  rev-12's **"+₹9,574/cycle-day"** or "**62% SPM**" (both retired — that headline was the
  pull-rule artefact) or "cutoff drives 83–96%" — all without their historical label —
  ₹0.61 cr/yr, 24/24, 116/127, 57/57, 60, or 197/236/238 passed, 471 bbl/d, "Baghewala's
  own SOR", any absolute CO₂ *reduction* per cycle, a soak-day recommendation,
  "cross-validation", gross margin as profit, "the BL factor is unverified", **"pull when
  rods float" as THE rule** (it's one of four policies), or a single gain number without
  naming the baseline's float policy.

---

## If something breaks mid-demo

There is **no automatic fallback.** If the data source fails, the status chip turns into
**"Data source error · …"** and the page does not silently switch to mock. In MOCK mode
there is no network call for data (Plotly is bundled locally, so no network is needed for
charts either), so the realistic failures are:

- **Charts blank:** keep talking from the tables. The Optimiser and Model basis pages
  are almost entirely tables. This should be rare now that Plotly ships in
  `dashboard/vendor/`, but say, once: "the numbers are in the table" if it happens.
- **Staged banner missing on the console:** you are on a stale tab. Press **F5**.
- **Something odd after a rehearsal:** `localStorage.removeItem("bgw.v4")` and reload.

Don't troubleshoot for more than ~10 seconds, and don't apologise more than once.

---

## Appendix: live API (only if a judge insists on seeing it run)

The live API runs the current rev-13 physics directly from the **current branch**
(`main`), no old commit or worktree needed.

```bat
cd "<repo>"
.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000
curl "http://localhost:8000/simulate?steam_t=1300&soak_days=10&cutoff=1.3&spm=5&float_policy=vfd_hold"
curl "http://localhost:8000/api/recommend/physics"
curl "http://localhost:8000/api/schedule/demo"
```

The first call reproduces our assumed baseline under VFD-hold (SOR ≈ 3.29,
net cash ₹/cycle-day ≈ +12,064 at OIL's FY25 price); the physics-grid recommend endpoint
reproduces the canonical recommendation (SOR ≈ 2.83, net cash ₹/cycle-day ≈ +15,396); the
schedule-demo endpoint serves the baked 12-well field-scheduler result (every well on
VFD-hold). Bare `python` on this machine is broken, so always use
`.venv\Scripts\python.exe` (3.13.3). To point the dashboard itself at the live API, set
`MOCK = false` at `dashboard/src/core.js:9`, run `node dashboard/build.js`, reload, and
revert both afterwards — **MOCK stays the default for the staged demo**; this is only for
a judge who wants to see the server respond live.

If a judge specifically wants the **old, superseded v1, rev-9, or rev-12 numbers**, those
require checking out an old commit/branch and are out of scope for this script — say
"that was an earlier version of our engine; a technical re-score and one more physics
wave later, you're looking at the current engine, where the operator's response to
floating rods is itself a modelled control," and move on.
