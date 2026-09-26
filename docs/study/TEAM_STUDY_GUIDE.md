# TEAM STUDY GUIDE — Baghewala CSS + SRP Digital Twin
### SIH 2026 · PS SIH26120 · Oil India Limited · Team MNIT Jaipur

**Read this end to end once. It won't make you a reservoir engineer, but it will let you
answer most judge questions honestly and know which teammate to hand the rest to.**

This is not a physics textbook. It explains *our* system: our equations, our code,
our constants, our numbers, and, importantly, which of our numbers are real and
which are ours. Nothing here is invented. Every figure traces to a file or a commit in
this repo, but since 13 Sep some of those files have changed underneath the numbers.
Read the banner first.

---

> ### STATUS BANNER: 27 Sep 2026 — physics wave 5, operating policy as a control (rev 13)
>
> - **Six engines now exist.** v1, rev 5, rev 9 are unchanged history (see the collapsed
>   summary two paragraphs down if you need it). **Rev 12** (physics wave 4) added the
>   float-onset produce-end rule and led with a **+₹9,574/cycle-day** headline gain
>   (SOR 4.35→3.19). **A technical re-score (58/100) found that headline was structural, not
>   physical**: it came entirely from the **pull rule** ending the baseline (b) on produce day
>   139 while it still made 1.87 m³/d of real oil — running the twin's own VFD-slowing mode on
>   that same baseline erased the gain to nothing. **Rev 13 (physics wave 5, current) fixes
>   this**: the operator's response to rod float is now itself a **control**,
>   `css.float_policy` ∈ `pull` / **`vfd_hold`** / `vfd_then_pull` / `none`, applied identically
>   to the baseline, the recommendation, *and* the cold counterfactual (which is now **shut
>   in**, not "idealised pumpable," once it floats under any policy). Also smoothed the
>   inversion cliff, added a hard injectivity gate, and added a net-of-royalty-and-cess price
>   deck. **No calibration knob moved** — only the diesel discount base (0.30→0.15, an
>   economics input, on the coordinator's instruction). Branch `wave5`; see
>   `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12 and `docs/PROJECT_LOG.md` §16.
> - **The single sentence that matters most:** *"our gain depends entirely on what the
>   baseline operator does about a floating rod — slow it down, or pull it — and we now
>   report all three answers, not the one that looked biggest."*
> - **The four policies.** `pull` (rev-12 style: run at the physical keep-up SPM limit, pull
>   after 3 consecutive alarm days) · **`vfd_hold`** (recommended: a VFD slows the pump to hold
>   the floating index at exactly 0.6, down to a 2-spm floor; pull only after 3 alarm days
>   *at* the floor) · `vfd_then_pull` (same idea, a shallower floor) · `none` (no float
>   response at all — the cycle rides to its rate cutoff). The shipped params **default stays
>   `pull`** (that's the operation the benchmark calibration bands were set against — switching
>   it would be calibration-by-respecification); the **recommendation is `vfd_hold`
>   regardless**.
> - **Canonical numbers, both sides VFD-hold** (reference set-point unchanged, still `pull`,
>   still SOR 4.50 gross): baseline (b) 1,300 t/10 d/91 kgf/cm²/86-in/5 spm → **SOR 3.29**,
>   395 m³ oil, net cash +₹12,064/+(-582)/(-14,193) (FY25/$65/net-of-levies), ends on the float
>   pull at the 2-spm floor. **Recommendation: 1,000 t / 10 d / 89 kgf/cm² / 64-in / start
>   4.5 spm / cutoff 0.60 m³/d backstop / VFD-hold → SOR 2.83**, 353 m³ oil, net cash
>   **+₹15,396 / +₹3,738 / −₹8,811** (FY25/$65/net-of-levies).
> - **The gain, naming the baseline's own policy (net cash ₹/cycle-day, FY25/$65/net-of-levies):**
>   same policy (VFD-hold, the fair comparison) **+3,332 / +4,319 / +5,382** — decomposes stroke
>   57% / cutoff 30% / steam 11%; if the baseline pulls at the first alarm **+12,917 / +14,694 /
>   +16,606** (**68% of this is the policy switch alone**, not the set-point — this IS the old
>   retired "+₹9,574" number, restated honestly); if the baseline does nothing about float, the
>   canonical recommendation still **GAINS +2,622 / +3,484 / +4,413** against it (TIER1 §12.6
>   "mixed" row) — an earlier pass of this banner said "LOSES −3,865/−2,513/−1,057" here, but
>   that number belongs to a different, non-canonical plan built specifically for a do-nothing
>   world, not to our recommendation, and is retired. What doesn't change: the model prices no
>   rod-failure or workover cost, so avoiding float — 72→3 alarm days, 42→0 days at FI=1.0,
>   **in-model with a perfectly known drag law** — isn't in any of these three ₹ figures; in the
>   UQ, where drag error is sampled, the recommendation is actually **more** float-exposed than
>   the baseline, median 6 alarm days vs 0.
>   **Never state a single gain number without naming which of these three it is.**
> - **Two honest gaps, both strict xfail, PLUS a third, new one:** (1) soak has no interior
>   optimum; (2) the steam optimum at the mid-range (0.15) diesel discount sits below the
>   BGW-8 slug range (~750 t vs 1,040–1,560 t — new this rev, read as revealed preference that
>   OIL's real steam is probably cheaper than we assumed). The rev-12 cold-well xfail is now
>   **un-xfailed**: the cold well obeys the policy and is correctly shut in, not "unpumpable
>   yet somehow pumped."
> - **Rod damage is now the honest cost of the recommendation.** VFD-hold holds the floating
>   index at the 0.6 alarm line for ~55–60 days a cycle (graded damage index ~5× the `pull`
>   policy's) — that is the price of the extra oil, and **it is unpriced in ₹** (no rod-string
>   failure/workover cost is modelled). That is exactly why a baseline doing nothing about
>   float "beats" the recommendation on paper (previous bullet).
> - **Net of royalty + OID cess (~₹3,600/bbl, ~35% levies, OIL's own FY25 Annual Report
>   basis), every feasible grid point is negative** — the recommendation's edge over the
>   baseline still grows on this deck (+₹5,382, it saves steam), but "is CSS profitable" is
>   answered by OIL's own price/levy deck, not by our assumptions.
> - **Tests: 263 passed, 2 xfailed.** **ML's honest role, unchanged in spirit, updated in
>   number:** the exhaustive 6-lever × policy physics grid (`ml/recommend_physics.py`'s
>   `best_settings_physics_5d`, 40,194 feasible points/policy after the injectivity gate, 4
>   policies) is the decision engine; the XGBoost surrogate (`ml/optimize.py`) now lands
>   **~24% below** it (+₹11,635/d vs +₹15,396/d FY25) and is reported only as a cross-check.
>   The float classifier (`float_premature_pull`, 41% positive, AUC 0.999) is informational
>   only — **not** a search constraint (a hard injectivity gate replaced the old soft
>   float-risk penalty).
> - **UQ (1,500 draws, seed 42, 3 price decks):** P(injectable) = 1.000 everywhere. Same-policy
>   P(rec > baseline), VFD-hold: **96% against a baseline whose 1.3 m³/d cutoff we chose; 84%
>   (median ₹2.5k/day) with the same 0.6 backstop; ≈ ₹0 if the VFD can run below 2 spm, as our
>   own cold well does** (raw draws 0.965/0.992/0.999, FY25/$65/net-of-levies); if baseline
>   pulls, 0.991–1.000; if baseline does nothing about float, only 0.16–0.25. Same-policy gain
>   p10/p50/p90 (FY25): +2,175/+12,101/+161,014 — right-skewed, our point estimate is
>   conservative, not cherry-picked.
> - **Field scheduler, re-run every-well-VFD-hold:** naive fixed-job policy is now
>   **+₹72,320/d** field-wide (was a **loss** of −₹13.3k/d under rev-12's pull-everywhere
>   default — the policy switch alone is the whole difference); exact scheduling reaches
>   +₹109,799/d, serving 10 of 12 wells.
> - **What to say on stage:** the safe-to-say block at the top of `docs/study/viva_prep.md`,
>   verbatim — it is now the **three-baseline-policy** story, not a single delta. **Never say
>   as current results:** −30%, −41.3%, rev-5's "+188% margin", rev-9's "+4,423/cycle-day" or
>   "83–96% of the gain" (retired twice over now), the rev-12 "**+₹9,574/cycle-day**" headline
>   **without naming that it assumed a pulling baseline**, "62% SPM / 32% stroke" (superseded
>   decomposition — it's stroke 57% / cutoff 30% / steam 11% now), "236 tests" / "197 tests"
>   (it's **263**), ₹0.61 cr/yr, 6.8 cycles/yr, ₹1,300/t, 24/24, 116/127 passed, 471 bbl/d,
>   μ 0.63 cP, "optimal soak N days", any Baghewala-specific SOR, an absolute CO₂ *reduction*
>   per cycle, "cross-validation", **gross margin as profit**, "the BL factor is unverified",
>   the measured-card classifier as field-validated, "verified improvement", or **any single
>   gain number without naming the baseline's own float policy**.

> ### Read this first if you know nothing
>
> - **Reservoir:** not an underground lake, but rock whose tiny pores hold oil. Baghewala's is
>   sandstone ~1,150 m down.
> - **Porosity** = how much of the rock is pore space (<10% here). **Permeability** = how easily
>   fluid moves through those pores.
> - **API gravity** = light vs heavy crude (higher is lighter). Baghewala is 14–19°: heavy.
>   **cP (centipoise)** measures viscosity. Water is ~1 cP; Baghewala crude is 8,000–15,000 cP
>   at 50 °C, like honey.
> - **CSS:** inject steam into a well, shut it in to **soak**, then pump the thinned oil out.
>   Repeat months later.
> - **Pumpjack / sucker-rod pump:** the see-saw on the surface drives a ~1,150 m steel rod
>   string that works a plunger at the bottom. Thick oil drags on the rods ("rod floating").
> - **IPR / drawdown:** the reservoir's supply curve. The lower the pressure at the bottom of
>   the well (more **drawdown**), the more oil flows in. Thinner oil flows in faster.
> - **SOR:** tonnes of steam per m³ of oil. Lower is better, and it's our headline metric.
>
> **Reading order:** Hinglish pack `hinglish-pack/00_START_HERE.md` →
> `01_PROBLEM_KYA_HAI.md` → `03_PHYSICS_SAMJHO.md`, then this guide's §1, §3 and §6,
> then `viva_prep.md`, then §4 and §5 here. Every term is in
> [`docs/guides/GLOSSARY.md`](../guides/GLOSSARY.md).

---

## Table of Contents

1. [The story in 90 seconds](#1-the-story-in-90-seconds)
2. [The physics, intuitively then precisely](#2-the-physics-intuitively-then-precisely)
   - 2.1 [`thermal.py` — how far does the heat go?](#21-thermalpy--how-far-does-the-heat-go)
   - 2.2 [`viscosity.py` — how thin does the oil get?](#22-viscositypy--how-thin-does-the-oil-get)
   - 2.3 [`ipr.py` — how fast does the reservoir give it up?](#23-iprpy--how-fast-does-the-reservoir-give-it-up)
   - 2.4 [`srp.py` — can the pump physically lift it?](#24-srppy--can-the-pump-physically-lift-it)
   - 2.5 [`cycle.py` — the conductor](#25-cyclepy--the-conductor)
   - 2.6 [`generate_data.py` — turning one cycle into 3,000](#26-generate_datapy--turning-one-cycle-into-3000)
3. [A CSS cycle walkthrough — day 0 to day 61](#3-a-css-cycle-walkthrough--day-0-to-day-61)
4. [The ML layer, honestly](#4-the-ml-layer-honestly)
5. [Code map — "if a judge asks X, the answer is in file Y"](#5-code-map--if-a-judge-asks-x-the-answer-is-in-file-y)
6. [Number discipline table](#6-number-discipline-table)
   - A. [Killer judge questions: one-line pointers](#a-killer-judge-questions--one-line-pointers)
7. [Each teammate's 10-minute mastery track](#7-each-teammates-10-minute-mastery-track)
8. [Self-test — 20 questions](#8-self-test--20-questions)
9. [Answers](#9-answers)
10. [Footnotes: build-session notes](#footnotes--build-session-notes)

---

## 1. The story in 90 seconds

> **v1 engine (commit 351a89b): prototype outputs, audited, superseded.** The problem and
> insight below are still right. The **result** numbers are v1, kept so you understand what
> the dashboard shows. What to say instead is under "The result" below.

**The problem.** Oil India's Baghewala field, in the Thar desert of Rajasthan, sits on
heavy crude in the Jodhpur Sandstone at about 1,150 m. The oil is 14–17° API and — the
number that defines the whole project — **8,000–15,000 cP at 50 °C**. That is roughly
90–100× thicker than a "normal" 18° API crude. At reservoir temperature it does not
flow. It is, effectively, cold honey in rock with 9% porosity.

So OIL uses **Cyclic Steam Stimulation (CSS)**, also called "huff and puff": inject
steam into the well for a few weeks, shut it in to soak, then produce until the well
goes cold and the rate dies, then repeat. India's first formal CSS ran at well BGW-8 in
December 2018 and produced a 5–6× uplift. OIL had done 39 cycles by June 2025, ran 19
CSS jobs in FY26, and the whole field makes roughly 655–1,202 bbl/d.

**The insight.** The problem statement lists more knobs than four: **steam volume,
injection pressure, soak time, production cut-off, stroke length, SPM and VFD settings.**
Our prototype optimises four of them (steam volume, soak time, cut-off rate and SPM) and
holds the rest at field values. Right now those knobs are set by experience. And the two halves of the
problem are physically coupled in a way no off-the-shelf tool handles: **steam decisions
change the oil's viscosity, and viscosity is exactly what determines whether the sucker
rods "float" and break on the downstroke.** Optimise the steam alone and you can wreck
the pump. Optimise the pump alone and you leave steam money on the table.

**The solution.** A single physics engine (`twin/`) that simulates a whole CSS cycle
day by day — heat in, viscosity down, oil out, rod load up — from four inputs. Run it
3,000 times over a Latin-hypercube design (`twin/generate_data.py`). Train two XGBoost
surrogates on the result (`ml/train.py`): one predicts steam-oil ratio, one predicts
rod-floating risk. Then run Bayesian optimisation over the four knobs
(`ml/optimize.py`) to minimise predicted SOR subject to floating probability < 0.3.
Serve it all through FastAPI (`api/main.py`) into a **four-page dashboard** (Overview ·
Twin console · Optimiser · Model basis), which runs in MOCK mode from baked physics.

**The result: what to say now.** Use the safe-to-say block from `viva_prep.md`
**verbatim, not this paraphrase** (an earlier draft of this section duplicated and
drifted from it — don't learn two versions). Short form, ≤120 words:
*"Our operating rule: slow the pump with a VFD as it nears the float limit, and
only pull if it stays there — the same rule on both sides of every comparison.
Under that rule, steam per cubic metre of oil falls from 3.29 to 2.83, a 14%
cut, and we beat our own assumed baseline in 84–96% of simulated runs. The
rupee gain is real but modest and uncertain: roughly ₹0 to ₹5,000 a cycle-day,
because it's set by two numbers we don't have — OIL's actual VFD minimum speed
and their real pull/produce cutoff — both now on our data request. Everything
here is physics-simulated, not field-validated; 263 of 265 tests pass."*
For the full version — five rounds of audit, all three baseline-policy numbers
(+3,332 same-policy / +12,917 if baseline pulls / +2,622 if baseline does nothing,
this last one corrected from an earlier, wrong −3,865) — see `viva_prep.md`'s
"safe-to-say block", full version.

**The v1 result (history: know it, don't claim it).** This used to be "the exact claim
framing, learn it word for word". It no longer is.

Our reference cycle — 1,500 t steam / 7 d soak / 3.0 m³/d cutoff / 8 spm — simulates to
**SOR 1.29 t/m³**, 1,159 m³ of oil over 61.3 days, peak rod load 85.6 kN, peak floating
index 0.539 (safe; threshold is 0.6). The optimiser recommends **1,585 t / 3 d / 7.76
m³/d / 10.2 spm** with a **predicted SOR of 0.88 t/m³** and floating probability 0.001.

The three v1 deltas (the dashboard still shows the first two):

| Comparison (v1 engine) | From → to | Delta |
|---|---|---|
| Dashboard headline: reference cycle vs the optimum as applied | 1.29 → 0.91 t/m³ | −30.0% |
| Optimiser's own internal number (surrogate vs midpoint baseline); deck slide 5 | 1.50 → 0.88 t/m³ | −41.3% |
| Optimum re-checked in the v1 physics twin, not the surrogate | 1.29 → 0.89 t/m³ | −31% |

If a judge points at them, say *"our v1 prototype simulation showed that; we have since
audited it."* The −41.3% compares against `ml/optimize.py`'s own midpoint scenario (1,750 t /
9 d / 4.5 / 8.0 → SOR 1.50), which is **not** OIL's field practice. Always say the unit:
**tonnes of steam per cubic metre of oil.**

**What v2 (Tier-1) changed, in one paragraph.** The audit found the v1 numbers were produced
by four artefacts. (1) A mobility factor μ_ref/μ that reached thousands, so the reservoir
out-supplied the pump and the well sat on a **pump-capacity plateau of 74.96 m³/d (471
bbl/d)** against a field average of ~19 bbl/d per well. (2) Andrade extrapolated to
**0.63 cP** at steam temperature. (3) An SOR optimum that existed only because of an **8 m
drainage radius** tuned to create one. (4) A win that came from **10 SPM** lifting more during
that plateau. Cap SPM at the 3–6 heavy-oil practice band and SOR ≈ baseline. Tier-1 replaced
the mobility factor with a capped composite-radial uplift, Andrade with Walther, the τ=20 d
cooldown with Boberg–Lantz, the fixed Pwf/Pr with an absolute P_wf and a live P_res, and added
wellbore heat loss. **At that point (13 Sep, uncalibrated) at 1,500 t / 7 d / cutoff 1.5 /
8 spm:** SOR 9.83, 152.6 m³, 93 d, peak 17.8 bbl/d, uplift ~4×. Field-plausible rates, but
pessimistic SOR against the 3–8 literature band.

**Then, 26 Sep evening: calibration (rev 5).** The team found and fixed three more internal
bugs in its own review — missing sensible heat in the Marx–Langenheim balance, wellbore loss
double-counted, and pump capacity compared against oil rate instead of liquid rate (85% water
cut overstated it 6.7×). Retuning `AOF_REF_M3D`, `PRESSURE_BOOST_PER_T_KPA` and `SPM_MARGIN`
against the same benchmark table then gave, at the reference set-point (1,500 t / 7 d /
1.2 m³/d / 5 spm): **SOR 4.09, oil 367 m³, 182 produce days, peak 15.9 bbl/d, uplift 5.66×,
μ(290 °C) 4.13 cP**. The rev-5 recommendation was **1,700 t / 10 d fixed / 0.85 m³/d / 5 spm →
SOR 3.81 vs 4.11 (−7.3%), margin ₹7,893 vs ₹2,739/cycle-day (+188%)** — but that ₹ was
**gross margin** (credited the cold well's own oil to CSS) and the heat-loss constant was
then unverified. **Both are now historical — do not quote them.**

**Then, 26–27 Sep: physics v3 + economics v2 (rev 9) — superseded.** `BL_DELTA_FACTOR = 0.5`
was sourced and δ is computed per produce-day from the simulated streams. ₹ moved onto an
**incremental** basis, forcing the price-deck decision (FY25 realisation base case, $65
named comparison preset). At the reference set-point: gross **SOR 4.027**, incremental
**SOR 5.403**. Recommendation **1,600 t / 10 d fixed / 0.70 m³/d / 4 spm**: gross SOR 3.590
vs baseline 4.061 (−11.6%), incremental ₹/cycle-day +4,423 vs −724 (FY25). **But** water cut
was still a constant 85% and the cycle still ended on the rate cutoff alone — an external
review found 83–96% of that gain was just the assumed baseline cutoff moving. **Do not
quote rev-9 numbers.**

**Then, 27 Sep: hardening → physics waves 3–4 (rev 10–12) — superseded same day.** External
reviews (61 judge / 52 technical, out of 100) drove three waves, all on `harden`, now merged:
**rev 10** fixed a `dt`-summation bug, moved hardcoded constants (skin, pressure boost,
viscosity anchor) into params + UQ, and made the cold rate viscosity-dependent. **Rev 11**
made water cut a **state** — condensate flowback decaying to a formation floor — so the
stream starts water-continuous (~0.87) and crosses an inversion (~0.70) late in the cycle,
turning oil-continuous; that is exactly when the rods float at practice speed, restoring a
rod-float thesis rev 10 had found didn't bind at a constant cut. It also added
injection-pressure (IAPWS-IF97 steam state) and stroke-length levers. **Rev 12** replaced the
emulsion law with Pal–Rhodes (capped 10×) and — the pivotal change at the time — introduced
`produce_end_rule = "either"`: the cycle ends on the rate cutoff **or** 3 consecutive
float-alarm days, whichever comes first. `AOF_REF_M3D` was retuned 0.46→0.56 to meet the
15–40 bbl/d field peak band. Rev 12's recommendation (1,000/10/85/64-in/3 spm) claimed gross
SOR 3.19 vs baseline 4.35 and **+₹9,574/cycle-day** — but a technical re-score found that
entire gain was the baseline's own **pull rule** ending it early, not the set-points.
**Superseded; do not quote the +₹9,574 number without the rev-13 caveat below.**

**Then, 27 Sep evening: physics wave 5 (rev 13) — CURRENT.** The re-score's fix: the
operator's float response is now a **policy control**, `css.float_policy` ∈ `pull` /
**`vfd_hold`** / `vfd_then_pull` / `none`, applied identically to the baseline, the
recommendation, and the cold counterfactual (now shut in, not "idealised pumpable," once it
floats). Also smoothed the inversion cliff, added a hard injectivity gate (≥400 kPa sandface
margin — rejects the old 85 kgf/cm² floor), and added a net-of-royalty-and-cess price deck.
**No calibration knob moved** except the diesel discount base (0.30→0.15, an economics
input).

At the reference set-point (still `pull`, unchanged): gross **SOR 4.50**. Both baseline (b)
and recommendation now compared under **VFD-hold**: baseline 1,300/10/91/86-in/5 spm → **SOR
3.29**, net cash +₹12,064/−₹582/−₹14,193 (FY25/$65/net-of-levies). **Recommendation: 1,000 t
/ 10 d / 89 kgf/cm² / 64-in / start 4.5 spm / cutoff 0.60 backstop / VFD-hold → SOR 2.83**,
net cash **+₹15,396/+₹3,738/−₹8,811**. **The gain depends on the baseline's own policy**:
same policy (fair) **+3,332/+4,319/+5,382**; if baseline pulls **+12,917/+14,694/+16,606**
(68% is just the policy switch — this is what the old "+₹9,574" number actually was); if
baseline does nothing about float, the canonical recommendation still **gains
+2,622/+3,484/+4,413** (TIER1 §12.6 "mixed" row — a different, non-canonical plan is what
actually loses −3,865/−2,513/−1,057, and that number is retired from this comparison). Rod
damage stays unpriced either way. Decomposition (same policy): stroke 57%, cutoff 30%, steam 11%. Three
honest gaps remain, disclosed as strict xfail: no interior soak optimum; the steam optimum
at the mid-range diesel price sits below the BGW-8 slug range (new); the rev-12 cold-well
xfail is now **un-xfailed** (the counterfactual correctly shuts in under a policy).
**This is the number set to use on stage now** — see the STATUS BANNER at the top of this
file.

---

## 2. The physics, intuitively then precisely

Four physics modules, each one paragraph of intuition, then the equation, then what the
code literally does, then what breaks if you delete it.

> **v1 engine (commit 351a89b): prototype outputs, audited, superseded.** The intuition and
> the core equations (Marx-Langenheim, Vogel, rod loads) still apply. Constants, retunes and
> sanity numbers are v1, and each subsection ends with a **"Now (Tier-1)"** note giving what the
> current code does. Source of truth for the current code: `twin/*.py` and
> `docs/model-improvement/TIER1_PROGRESS_LOG.md`.

### 2.1 `thermal.py` — how far does the heat go?

**Intuition.** Injecting steam is putting the reservoir on a stove. But the reservoir is
a thin pancake (12 m thick) sandwiched between cold rock above and below, and that cold
rock is constantly stealing your heat by conduction. **Marx-Langenheim (1959) is the
model that tells you what fraction of the heat you paid for actually stays in the
pancake, and therefore how wide the hot disc grows.** Early on almost all the heat
stays (the disc is small, so little surface to leak through). Later, the disc is wide,
the leak area is huge, and each extra tonne of steam buys you less new hot rock. That
fact, diminishing returns on heat, is the physical reason an optimum steam volume *can*
exist. Whether one exists inside the operating range depends on oil price, fuel cost and
fixed cost per cycle, which is why the honest objective is ₹ margin per cycle-day and not
SOR alone (see the Tier-1 note below).

**The equations.**

```
t_D  = 4 · α · t / h²                                  (dimensionless time)
F(t_D) = exp(t_D) · erfc(√t_D) + 2·√(t_D/π) − 1        (Marx-Langenheim function)
E_h(t_D) = F(t_D) / t_D                                (thermal efficiency, 0–1)
```

- `α` = thermal diffusivity of the confining rock, m²/s. In our code `α = k / (ρ·cp)` =
  2.5 / 2.3×10⁶ = **1.087×10⁻⁶ m²/s**.
- `h` = reservoir thickness = 12 m. Note `h²` in the denominator: a **thinner** reservoir
  loses heat much faster (more surface per unit volume). Squared, so it matters a lot.
- `t` = seconds of injection so far.
- `erfc` = complementary error function — the standard solution shape for heat
  conducting into a semi-infinite solid.
- `E_h` → 1 as t_D → 0 (nothing lost yet), and decays as t_D grows.

Then the heat bookkeeping:

```
m_injected = rate_tpd · 1000 · t_days          [kg]
Q_in       = m_injected · quality · L          [J]   (only latent heat is credited;
                                                      v1: wellhead quality 0.65, L 1.3 MJ/kg,
                                                      NO wellbore loss)
Q_kept     = Q_in · E_h
V_heated   = Q_kept / (ρcp_rock · ΔT)          [m³]  ΔT = T_steam − T_initial
A_heated   = V_heated / h ;  r_heated = √(A/π)
frac       = min(A_heated / (π · R_drainage²), 1)
T_avg      = T_initial + ΔT · frac
```

**What the code actually does.** `steam_zone_temperature(t_days, params)` in
`twin/thermal.py` returns `(T_avg_C, heated_radius_m)`. Note the *blend* step: rather
than pretending the produced fluid is all at steam temperature (the sharp isothermal
front Marx-Langenheim actually assumes), we area-weight the hot disc against the cold
remainder of the drainage disc. That gives a smooth day-by-day temperature curve instead
of a step function, which is what a day-stepped simulator needs.

**Key constants and why (v1):**

- **`DRAINAGE_RADIUS_M = 8.0` (v1 fudge; the constant is now deleted).** This was the disc of
  reservoir one well was assumed to drain. It was **retuned from 10.0 → 8.0** during
  integration for one reason: with 10 m, SOR kept improving to the top of the design range
  and `test_SOR_has_interior_optimum_over_steam_volume` failed. At 8 m the disc "saturates"
  at ~1,750–1,900 t, which *manufactured* the interior optimum. The edge SORs it produced
  (500 t → 5.96, 3,000 t → 2.03) did **not** land inside the 3–8 literature band: 2.03 is
  **below** it. Real drainage radii for a well like this are **~50–150 m**, and an 8 m disc
  is not a drainage area. **Say this honestly if asked:** "In v1 the optimum came from a
  tuned radius; we found it in our own review, deleted the constant, and the current engine
  uses 100 m (`reservoir.drainage_radius_m`)."
- **`COOLDOWN_TAU_DAYS = 20.0` (v1; now deleted).** Marx-Langenheim covers growth *during*
  injection only. v1 then relaxed exponentially toward reservoir temperature,
  `T = T0 + (T_peak − T0)·exp(−Δt/τ)`, with an arbitrary τ = 20 d. It has been replaced by
  **Boberg–Lantz** (see below).
- The heated **radius freezes** at its end-of-injection value, and only the temperature
  decays. Physically, the heat front does not retreat; it just cools.

**Sanity numbers at the v1 reference cycle (1,500 t):** injection lasts 1500/74 = 20.27 d;
t_D ≈ 0.053; E_h ≈ 0.85 (85% of the latent heat retained); heated radius **7.20 m**
inside the 8 m drainage disc; T_avg peaks at **244 °C**. At 2,000 t the 8 m disc is fully
"saturated" and T_avg pins at 290 °C. That saturation was the v1 optimum, and it was an
artefact of the 8 m fudge.

**Now (rev 9, physics v3).** Marx-Langenheim is unchanged for the injection phase, but
the heat going in is smaller and more honest: `wellbore_delivery()` applies VIT loss
(~10% per 1,000 m) and sandface quality = **0.55 × wellhead** (≈0.36), with latent heat
**1.40 MJ/kg** — plus, after the 26 Sep calibration pass, the **sensible heat** of the
injected water (`C_w·ΔT`) is now credited too, which the original Tier-1 balance had missed
entirely (≈3.6× more delivered heat once added). After injection, **Boberg–Lantz**
(`boberg_lantz_theta()`, exact-cylinder form) cools the zone by conduction to cap and base
rock *and* by heat carried out with produced fluids — and as of physics v3 (27 Sep), the
δ term in that equation is **computed per produce-day from the simulated oil/water
streams** (PEH Eq. 15.74) instead of one blended constant, and `BL_DELTA_FACTOR = 0.5` is
**sourced**: it's exactly the ½ inside Boberg & Lantz's own definition of δ, forced by
energy conservation, not a fitted number (see `docs/model-improvement/
BL_DELTA_FACTOR_SOURCE.md`). Since rev 11 the "water" stream feeding this term is itself a
**state** (condensate flowback decaying into a formation-water floor), not a constant 85%
cut — see §5b/§7 below for why that is this project's biggest recent finding. There is no
drainage-radius saturation any more, so SOR rises monotonically with steam volume under a
fixed produce-end rule — the honest interior optimum is in **incremental ₹ margin per
cycle-day** instead. At the reference set-point (1,500 t / 7 d / 1.2 m³/d / 5 spm / 86 in /
91 kgf/cm²) this gives gross **SOR 4.50** (rev 12; the cycle ends by float onset, not the
rate cutoff), inside the re-specified 3.0–4.6 band and the real CalGEM 3.47–8.24 band.

**Delete it and:** temperature becomes an input you have to guess, viscosity has no
driver, and there is no link between steam spent and oil gained. The project becomes a
pump calculator.

---

### 2.2 `viscosity.py` — how thin does the oil get?

**Intuition.** Heavy crude is a tangle of long chains and asphaltenes that have to slide
past each other. Sliding is thermally activated — like a reaction that has to hop an
energy barrier — so viscosity falls **exponentially**, not linearly, with temperature.
This is the single most leveraged relationship in the project. In **v1** (Andrade), heating
Baghewala crude from 50 °C to 244 °C dropped it from **11,500 cP to 2.04 cP**, a factor of
~5,600. That was too steep. The **current** Walther fit gives **7.2 cP** at 244 °C, a factor of
~1,600, which is still the whole reason CSS works.

**The equation (Andrade, 1930):**

```
μ(T) = A · exp(B / T_K)          T_K = T_C + 273.15
```

- `A` [cP] — a pre-exponential scale factor.
- `B` [K] — the activation-energy-like term. Bigger B = steeper curve. **B > 0 means μ
  falls strictly monotonically as T rises**, guaranteed analytically — that's why the
  monotonicity test can never flake.

**How A and B are found.** Two unknowns need two points, and taking logs makes it
linear in 1/T:

```
ln μ₁ = ln A + B/T₁ ;  ln μ₂ = ln A + B/T₂
B = ln(μ₁/μ₂) / (1/T₁ − 1/T₂) ;  A = μ₁ / exp(B/T₁)
```

`_fit_andrade()` does exactly this. Our two anchors are:
1. **11,500 cP at 50 °C** — CONFIRMED, midpoint of OIL's own reported 10,000–13,000 cP.
2. **50 cP at 150 °C** — `ANCHOR_MU_CP` / `ANCHOR_T_C`, an **ASSUMPTION**. No high-T lab
   measurement for Baghewala crude exists in any source we found.

That gives **A = 1.164×10⁻⁶ cP, B = 7,436.6 K**. You will be asked about that second
anchor. The honest answer: "one of our two calibration points is real field data, the
other is an assumed high-temperature anchor, and it's the first thing we'd replace with an
OIL lab measurement."

**Why v1's Andrade was retired.** Extrapolated past the 150 °C anchor, this A and B give
**2.04 cP at 244 °C and 0.63 cP at 290 °C**. That is thinner than water at room temperature
(1 cP), which is implausible for a 15° API crude. Heavy oils stay at several cP even at
steam temperature.

**Now (Tier-1).** `viscosity.py` fits the **same two anchors** with **Walther / ASTM D341**
(log log(ν + 0.7) linear in log T, the petroleum-standard form), converts cSt to cP with
the API-derived density, and floors the result at `fluid.mu_floor_cP = 1.0`. Verified values:
μ(50) = 11,500 exactly, μ(130) = 97.7, μ(150) = 50.0, μ(240) = 7.58, **μ(244) = 7.2, μ(290) = 4.13
cP**. Andrade is still reachable only if explicit `andrade_A/B` are set (kept for one test and
for benchmark comparison). `andrade_A/B` and `walther_A/B` are deliberately `null` in the
JSON; the reason is a float-precision detail, in the footnotes.

**Delete it and:** the thermal model produces a temperature nobody can use. Viscosity is
the translator between "the reservoir is hot" and "the oil moves" — and it feeds *both*
downstream modules, IPR (mobility) and SRP (rod drag). It is the hinge of the whole twin.

---

### 2.3 `ipr.py` — how fast does the reservoir give it up?

**Intuition.** IPR is the reservoir's supply curve. Pull harder (lower the pressure at
the bottom of the well) and you get more oil, but not linearly — the curve bends over.
Vogel's 1968 correlation is the industry-standard shape for that bend. On top of the
shape, v1 applied a **mobility factor**: Darcy's law says flow ∝ k/μ, so if you halve the
viscosity you double the flow. That's the one line of code where heat turns into money.
(Applied to the *whole* drainage area it is also where v1 went wrong; see the Tier-1 note
below.)

**The equation:**

```
q / q_max = 1 − 0.2·(Pwf/Pr) − 0.8·(Pwf/Pr)²        (Vogel 1968)
q = AOF_REF · vogel_shape · (μ_ref / μ)
```

All of the following is **v1**:

- `Pr` = average reservoir pressure = 11,400 kPa, held **constant** all cycle
  (no depletion modelled).
- `Pwf` = `PWF_DRAWDOWN_FRACTION · Pr` = 0.4 × 11,400 = 4,560 kPa. So Pwf/Pr = 0.4 →
  vogel_shape = 1 − 0.08 − 0.128 = **0.792**, constant all cycle. Everything that moved in
  the oil rate came from μ.
- `μ_ref / μ` = the mobility ratio. At 50 °C it's 1.0. At 244 °C (μ = 2.04 cP) it's
  11,500/2.04 ≈ **5,600**. That is the root of v1's problem: the effective uplift reached
  ~**135×** over the cold rate, against the **5–6×** BGW-8 actually saw, so the reservoir
  out-supplied the pump for much of the cycle.
- **`AOF_REF_M3D = 0.7`** (v1): absolute open flow at cold viscosity, calibrated because no
  measured productivity index exists. Cold rate 0.7 × 0.792 = 0.55 m³/d, below every value
  in the **v1** cutoff range [1, 8] m³/d, so a cold well is uneconomic. That premise is right
  and survives into Tier-1.
- It was **retuned 1.0 → 0.7** in integration because at 1.0 every cycle was pump-limited
  and the SOR optimum vanished. That was tuning to a test, not to data. (Details in the
  footnotes.)

**Now (rev 9, further retuned at rev 12).**
- The mobility factor is replaced by a **composite-radial uplift** (`composite_uplift()`):
  a hot inner zone of radius r_h inside a cold outer zone out to the drainage radius (100 m),
  capped at 10 and ≤ 5.8 in practice. At the reference set-point uplift is **5.41×** (was
  5.66× at rev 9; the uplift is AOF-invariant, so this small shift is from the water-cut/
  emulsion/pressure physics added at rev 11–12, not the AOF retune), matching BGW-8's
  published 5–6×.
- `Pwf` is **absolute**, so reservoir pressure matters. `P_res(t)` **charges** during
  injection and **bleeds** during production (τ = 25 d). Rev 11 made the near-well recharge
  cap out at the sandface pressure (now a function of the injection-pressure lever, IAPWS-IF97
  steam state) rather than uncapped.
- `AOF_REF_M3D` was retuned **0.46 → 0.56** at rev 12 (not 0.60 → 0.46 as at rev 9) — the
  smallest step that lifts the reference peak into the field's 15–40 bbl/d band. The cold
  rate is no longer a single number: it now scales with the oil's own viscosity (Darcy
  mobility), giving **~0.44–0.54 m³/d (≈2.8–3.4 bbl/d)** depending on reservoir pressure —
  still below the cutoff range.
- Peak rate at the reference set-point is now **15.1 bbl/d** (was 15.9 at rev 9; the drop is
  from the injection-pressure default and the capped recharge, offset by the AOF retune), in
  line with a field averaging ~19 bbl/d per well and squarely inside the 15–40 bbl/d band the
  reference-peak test checks.

**Delete it and:** you have a temperature and a viscosity but no production. There is
nothing to divide the steam by, so there is no SOR, so there is no objective function.

---

### 2.4 `srp.py` — can the pump physically lift it?

**Intuition.** A sucker-rod pump is a 1,150 m steel rod hanging down a well with a
piston on the end, see-sawed up and down by the pumpjack. On the **upstroke** the motor
lifts the rod's own weight plus a column of oil, plus it has to drag the rod through
viscous fluid — that's your peak load and your electricity bill. On the **downstroke**,
gravity is supposed to pull the rod back down on its own. But if the oil is thick
enough, viscous drag eats most of the rod's submerged weight, so **the rod string cannot fall
as fast as the pumping unit drives the polished rod down**. The rods go slack, fall behind,
can buckle in compression, and then get jerked or slapped when the unit catches up. (It is
*not* "the rod falls faster than the fluid".) Repeat that thousands of times a day and rods
wear, buckle and part. That is a workover: **$15k–$50k
industry-typical, plus lost production.**

**The equations:**

```
Buoyant rod weight:  W_b = (m'·L)·g · (1 − ρ_fluid/ρ_steel)
Fluid load:          F_f = ρ_fluid · g · L · A_plunger
Viscous drag:        F_v = K_VISC · μ[Pa·s] · v_avg · L        v_avg = 2·stroke·spm/60
Peak rod load:       P   = W_b + F_f + F_v
Energy/day:          E   = P · stroke · (spm · 1440) / 3.6e6   [kWh]
FLOATING INDEX:      FI  = min(F_v / W_b, 1)                   >0.6 = risk (our design threshold)
Pump capacity:       q_max = A_plunger · stroke · (spm·1440) · 0.85   (v1: VOLUMETRIC_EFFICIENCY;
                                                                  now FILLAGE_MAX, graded)
prod_rate = min(IPR rate, q_max)
```

**Work the numbers once and you own this module.** With rod_mass 3.8 kg/m × 1,150 m =
4,370 kg → 42.9 kN in air. API 15.5 → SG = 141.5/(131.5+15.5) = 0.9626 → ρ = 963 kg/m³.
Buoyancy factor = 1 − 963/7850 = 0.877 → **W_b = 37.6 kN**. Plunger area = π/4 × 0.057²
= 2.552×10⁻³ m². Fluid load = 963 × 9.81 × 1150 × 2.552e-3 = **27.7 kN**. Base load =
**65.3 kN**, and it never changes during the cycle. Every kilonewton above 65.3 is pure
viscous drag.

At the end of the v1 reference cycle: μ = 2,203 cP = 2.203 Pa·s, v_avg = 2×3×8/60 = 0.8
m/s, so F_v = 10 × 2.203 × 0.8 × 1150 = 20.3 kN → peak load **85.6 kN** and
**FI = 20.3/37.6 = 0.539**. Every number the dashboard shows, from two lines of algebra.

You can also invert it: at 8 spm the FI hits the 0.6 threshold at μ ≈ **2,450 cP**; at 12
spm it hits 0.6 at only **1,635 cP**. That's the whole risk story — run the pump faster
and you can tolerate less cold.

**Key constants.** `K_VISC = 10.0` is the lumped drag coefficient — not derived from
annular geometry (we have none in the params file), tuned so cold heavy oil at
mid-to-high spm crosses into the >0.6 band while hot oil gives negligible drag (see
footnote 4). It has never been fitted to a real dyno card, and that's the first thing we'd
calibrate. In v1, `VOLUMETRIC_EFFICIENCY = 0.85` accounted for slippage and gas
interference.

**Now (rev 9, since revised at rev 11–12).** The rod-load algebra and the floating index
were **unchanged in form** at rev 9 (FI is algebraically identical, so the 65.3 kN worked
example still holds), and the calibration pass fixed a real bug: pump **oil** capacity was
compared against the produced **liquid** rate (`oil_capacity_m3d = displacement × fillage ×
(1 − water_cut)`) instead of oil rate alone, which had overstated pump oil capacity **6.7×**
at the (then-constant) 85% water cut. `FILLAGE_MAX = 0.85`, and fillage drops when the oil
is too thick to fill the barrel. A **declining-SPM schedule** caps SPM at what the rods'
fall velocity allows (`max_spm_for_viscosity()`).

**Rev 11–12 changed the water-cut story itself.** Water cut is no longer a constant 85% —
it is a **state** that starts high (~0.87, condensate flowback) and falls toward a
formation floor (~0.45) late in the cycle. Rod drag now uses a **Pal–Rhodes emulsion
viscosity** (capped at 10×) evaluated at that day's water cut, not the reservoir oil's own
viscosity — so FI is **water-cut-dependent**, not just temperature-dependent. At the
reference set-point, FI stays near zero through most of the cycle and then **rises sharply
once the stream crosses its ~0.70 water-cut inversion**, late in the produce phase — this
is genuinely the rod-float thesis binding, not a margin of safety. The recommendation
(3 spm, 64-in stroke) reaches **max FI 0.622 on its 3rd alarm day** and the cycle **ends
there** — `produce_end_rule = "either"` stops the cycle on the rate cutoff or on 3
consecutive float-alarm days, whichever comes first, rather than letting it run floating
rods indefinitely. Floating damage is graded (`rod_float_damage_index`,
`days_rods_in_compression`) instead of a single count.

**The daily FI/load number is still a static, one-number-per-day approximation** — but as
of rev 6/9 it is no longer the whole dynamometer story. `twin/dyno.py` computes a full
surface + pump card at any day of the cycle from a Gibbs (1963) rod wave-equation
finite-difference solve (rod elasticity, wave propagation, carrier-bar separation), not an
RP 11L chart look-up. At a stress test of 12 SPM the computed card shows rod-float
carrier-bar separation whose onset independently reproduces the ≈0.6 FI alarm line — two
different pieces of physics agreeing. Say "the daily floating index is a lumped scalar;
the dynamometer card itself is now a full computed wave-equation solve, not an
illustrative shape" if asked which is which.

**Delete it and:** you lose the entire safety half of the problem statement. You'd
optimise SOR into a setting that destroys rod strings, which is exactly the failure mode
a pump-only commercial optimiser or a reservoir-only simulator each miss on their own.
This module is *why* our story is "coupled optimisation" and not "another SOR calculator".

---

### 2.5 `cycle.py` — the conductor

`simulate_css_cycle(steam_t, soak_days, cutoff_m3d, spm, params, dt_days=1.0)` walks a
single clock from day 0 and calls the four modules in order every step.

- **inject** while `day < steam_t/injection_rate_tpd`. Well is shut in: `oil_m3d`,
  `energy_kWh`, `rod_load_kN`, `floating_index` are all zero. `steam_t_cum` ramps.
- **soak** for `soak_days` after that. Still shut in, still zero production; temperature
  decays (v1: τ = 20 d exponential; now: Boberg–Lantz).
- **produce** from `soak_end_day` onward: thermal → viscosity → IPR → pump, every day.
  Through rev 11, the loop broke the first day `prod_rate < cutoff_m3d` (so the last row
  was always *below* cutoff). **Rev 12 changed this**: `produce_end_rule` (`"rate_cutoff"`,
  `"float_onset"` or `"either"`, default `"either"`) can instead end the cycle on 3
  consecutive days of `FI > css.fi_alarm` (0.6) — whichever condition fires first. A params
  tree without the key still runs `rate_cutoff`-only (rev ≤ 11 behaviour).
  `MAX_PRODUCE_DAYS = 730` is a runaway guard.

`summary(df)` collapses it to key numbers: `oil_total_m3`, `SOR_t_per_m3`,
`energy_per_m3_kWh`, `days_total`, `max_floating_index`, `failures_expected` (count of
produce days above 0.6 — a proxy for expected floating events, **not** a fatigue-life
calculation), plus, since rev 12, `produce_end_rule`, `produce_end_reason`,
`produce_days`, `peak_oil_produce_day` and `produce_end_days_after_peak`. Zero-oil cycles
return `SOR = inf` rather than crashing.

**Now (rev 9, extended at rev 11–12).** The produce loop also updates `P_res(t)` (charge
and bleed, now capped at the sandface pressure), passes the heated radius into the
composite uplift, applies the declining-SPM schedule and fillage, and tracks the
Boberg–Lantz energy-removed term. Rev 11 added **water cut as a state** (condensate
flowback + a formation floor, replacing the constant `fluid.water_cut`), an
**injection-pressure lever** (IAPWS-IF97 steam state from the wellhead pressure) and a
**stroke-length lever** (64–144 in, checked against a polished-rod-load cap). Rev 12 added
the **Pal–Rhodes emulsion law** (capped 10×) for rod drag and the **float-onset
produce-end rule** above. `summary(df, params)` also reports `peak_oil_bbl_d`,
`steam_cost_inr`, `co2_t`, `margin_inr_per_cycle_day` (gross, kept for continuity) and a
**cold-well baseline** (`cold_rate_m3d`, `oil_cold_baseline_m3` — an *idealised pumpable*
cold well; the real cold well is a disclosed xfail, see §"Honest limits") and
**incremental** keys (`SOR_incremental`, `margin_incremental_inr`,
`margin_incremental_inr_per_cycle_day`) plus daily-opex keys and the graded
floating-damage fields.

**Delete it and:** you have four functions and no system. `cycle.py` is where the
coupling that the whole pitch rests on physically happens.

### 2.6 `generate_data.py` — turning one cycle into 3,000

`scipy.stats.qmc.LatinHypercube(d=4, seed=42)` draws a space-filling design over the
4-D unit cube, `qmc.scale` stretches each dimension to its range from
`field_params.json` (`css.steam_volume_t_range` [500, 3000], `css.soak_days_range`
[3, 15] rounded to whole days, `css.cutoff_rate_m3d_range` [1, 8] *at the time*,
`srp.spm_range` [4, 12]). Each sample runs a full cycle; one row per cycle; rows with
SOR = inf are dropped (none were). Output: `data/synthetic_cycles.csv`, 3,000 rows,
10 columns, mean SOR ≈ 2.96 t/m³.

**This description of the CSV is v1-era and historical.** The current
`data/synthetic_cycles.csv` is regenerated against **rev-9 physics** (physics v3 +
economics v2), 3,000 rows, and is what `ml/models/*` are trained on — see the STATUS
BANNER. `generate_data.py` and `ml/train.py` are now **safe to run** on this branch; they
just take time and will overwrite the current baked artefacts, so don't run them casually
right before a demo.

**Why LHS and not random?** With 3,000 random draws in 4 dimensions you get clumps and
gaps. LHS guarantees each dimension is evenly stratified — every steam_t bucket, every
soak bucket, gets filled. Better coverage for the same compute. **Analogy for the CS
folks:** random sampling is throwing darts; LHS is a Sudoku constraint — one point per
row and column of the grid.

---

## 3. A CSS cycle walkthrough — day 0 to day 61

> **v1 engine (commit 351a89b): prototype outputs, historical, superseded.** This walkthrough
> is kept for **mechanism** — heat in, viscosity down, pump-limited then reservoir-limited,
> rod load rising as the zone cools — the shape is still right. **Don't quote its rates or
> SOR as current results**; the current (rev-9) numbers are at the end of this section,
> and the dashboard now shows those, not this replay.

**This was the demo replay under v1.** Set-points: **1,500 t steam · 7-day soak · 3.0 m³/d
cutoff · 8 spm.** The curl below reproduces these numbers **only from a git worktree of
commit 6bb604d** (v1 code + v1 params) — not needed for the current demo, only if someone
specifically wants the old numbers for comparison. On the current branch (`main`) the
live API runs the current rev-9 engine directly, no worktree needed, and agrees with the
dashboard (see `docs/guides/DEMO_SCRIPT.md`).

```
curl "http://localhost:8000/simulate?steam_t=1500&soak_days=7&cutoff=3&spm=8"
```

### Days 0 → 20.3 — INJECT (21 daily rows)

At 74 t/d, 1,500 t takes 20.27 days. The well is shut in and producing nothing.

| Day | T (°C) | μ (cP) | heated radius | note |
|---|---|---|---|---|
| 0 | 50.0 | 11,500 | 0 m | cold, virgin reservoir |
| 1 | 60.8 | 5,446 | 1.70 m | +11 °C already halves viscosity |
| 5 | 101.8 | 478 | 3.72 m | 24× thinner than day 0 |
| 10 | 150.3 | 49.3 | 5.17 m | past water's boiling point |
| 15 | 196.8 | 8.7 | 6.30 m | now thinner than motor oil |
| 20 | 241.8 | 2.18 | — | last whole-day row |
| 20.3 | **244.2** | **2.04** | **7.20 m** | injection ends |

(The old table paired 2.18 cP with 244.2 °C. 2.18 cP belongs to day 20 at 241.8 °C; at
244.2 °C v1's Andrade gives 2.04 cP. The current Walther fit gives 7.2 cP at 244 °C.)

**What to say (v1 replay):** "Twenty days of steam takes the near-wellbore zone from 50 to
about 244 °C and drops viscosity by orders of magnitude. The mechanism is exactly what CSS
relies on." **Don't** say "we've heated 80% of what this well drains" or "that's the physical
reason there's an optimum". Both depend on v1's 8 m drainage fudge.

### Days 20.3 → 27.3 — SOAK (7 rows)

Still shut in. No steam going in, no oil coming out. The exponential cooldown (τ = 20 d)
starts the moment injection stops.

| Day | T (°C) | μ (cP) |
|---|---|---|
| 21 | 237.2 | 2.48 |
| 22 | 228.1 | 3.23 |
| 25 | 203.3 | 7.00 |
| 27.3 | 186.8 | 12.2 |

**What to say:** "Soak is the well digesting the heat: condensation and conduction spread it
past the immediate wellbore instead of flashing straight back out." **Know, but don't
volunteer:** v1's twenty-day exponential modelled only the *cost* of soak (~57 °C lost over 7
days), never its benefit, which is why the v1 optimiser pinned soak at the 3-day floor. OIL
soaks 7–13 d. The current engine (Boberg–Lantz) is almost flat in soak.

### Days 27.3 → 61.3 — PRODUCE (35 rows)

The pump starts. Two distinct regimes here — knowing the difference is a high-value
detail.

**Regime 1: pump-capacity limited (day 27.3 → ~38).** The reservoir can supply more than
the pump can lift. Rate pins flat at **74.96 m³/d**, which is exactly
`A_plunger × stroke × spm×1440 × 0.85` at 8 spm (the 0.85 was `VOLUMETRIC_EFFICIENCY` in v1,
now `FILLAGE_MAX`). The oil "peak" in the chart is a *plateau*, not a spike, and it is the
pump's ceiling, not the reservoir's. **Audit flag:** 74.96 m³/d = **471 bbl/d from one well**.
The field averages **~19 bbl/d per well**, and the *whole field* made 655 bbl/d (Jul 2025) and a
record 1,202 bbl/d (2026). This plateau should not exist; it is the clearest symptom of v1's
~25× rate error.

**Regime 2: reservoir/thermally limited (day ~39 → 61.3).** The zone has cooled enough
that the IPR rate drops below pump capacity, and from there rate declines monotonically
every single day as viscosity climbs back up.

| Day | phase | T (°C) | μ (cP) | oil (m³/d) | rod load (kN) | FI |
|---|---|---|---|---|---|---|
| 27.3 | produce start | 186.8 | 12.2 | 74.96 | 65.4 | 0.003 |
| 34.3 | plateau | 146.4 | 58.1 | 74.96 | 65.9 | 0.014 |
| 39.3 | decline begins | 125.1 | 150.0 | 42.5 | 66.7 | 0.037 |
| 44.3 | declining | 108.5 | 338 | 18.9 | 68.4 | 0.083 |
| 49.3 | declining | 95.6 | 670 | 9.5 | 71.5 | 0.164 |
| 54.3 | declining | 85.5 | 1,181 | 5.4 | 76.2 | 0.289 |
| 59.3 | near cutoff | 77.6 | 1,877 | 3.40 | 82.6 | 0.459 |
| **61.3** | **cutoff hit** | **75.0** | **2,203** | **2.89** | **85.6** | **0.539** |

**What to say (mechanism, not rates):** "As the zone cools the decline is driven by
viscosity: as the oil thickens the rate falls and, at the same time, the rod load climbs,
because thicker oil means more drag on the rod string. Look at the two curves crossing:
that's the coupling this whole project is about. Floating risk is highest at the very end,
when the well is coldest." Don't read out "seventy-five cubic metres a day".

**v1 cycle totals:** oil **1,158.96 m³** · **SOR 1.2943 t/m³** · energy **20.59 kWh/m³** ·
**61.27 days** · max FI **0.539** · failures_expected **0**.

**The stress-test moment in the demo:** push spm to 12. Higher spm means higher rod
velocity, which means more drag at the same viscosity. In the v1 algebra the floating
threshold arrives at 1,635 cP instead of 2,450 cP, so the alarm fires. **On the dashboard
this is not a physics run.** Only the reference and the as-applied optimum are baked twin
output; the 12-spm stress test is the in-browser heuristic `mockSimulate`. The direction is
right, but say "approximation" if asked.

**And the v1 optimised cycle for contrast** (1,600 t / 3 d / 8 m³/d / 10 spm): oil
**1,765.6 m³**, **SOR 0.9062**, **53.6 days**, max FI **0.255**. The v1 story was "all four
knobs pull together". The audit showed otherwise: the **entire** gain came from **10 SPM**
lifting more during the pump-limited plateau. Cap SPM at the 3–6 practice band and SOR ≈
baseline. The 3-day soak was also an artefact (see the soak note above).

**v1 audit notes, in one place:**

| v1 said | Reality check |
|---|---|
| 471 bbl/d plateau (74.96 m³/d) | Field ~19 bbl/d per well; the whole field made 655–1,202 bbl/d |
| Uplift ~135× over cold | BGW-8 measured 5–6× |
| μ 2.04 cP at 244 °C, 0.63 cP at 290 °C | Heavy crude stays at several cP; now 7.2 and 4.13 cP |
| 3-day soak optimal | OIL practice 7–13 d; v1 didn't model any benefit of soak |
| 10 SPM | Heavy-oil practice 3–6 SPM; the whole gain came from here |
| 61-day cycle | Field CSS jobs are 6–18 months apart (never annualise with 365/61) |
| SOR 1.29 | Literature 3–8; Baghewala's own is unpublished |

**Current engine (rev 13), same well, its own reference set-point (1,500 t / 7 d /
1.2 m³/d / 5 spm / 86 in / 91 kgf/cm², policy `pull`, unchanged):** gross **SOR 4.50**.
Baseline (b) and recommendation are both compared under **VFD-hold**, the same policy:
baseline (1,300 t / 10 d / 91 kgf/cm² / 86-in / 5 spm) gives **SOR 3.29**, net cash
+₹12,064/cycle-day at OIL's confirmed FY25 price. The recommendation (**1,000 t / 10 d /
89 kgf/cm² / 64-in / start 4.5 spm, cutoff 0.60 backstop, VFD-hold**) gives **SOR 2.83 and
net cash +₹15,396/cycle-day** — a same-policy gain of **+₹3,332/cycle-day** (57% from a
shorter stroke, 30% from cutoff, 11% from steam). If the baseline instead pulls on the
first alarm, the gain looks like +₹12,917 — but 68% of that is the policy switch, not the
set-points. At the $65/bbl price floor the same-policy gain is +₹4,319; net of royalty and
cess, +₹5,382 (every absolute point on that deck is negative, baseline included) — show
all three where relevant. Three honest gaps remain, disclosed as strict xfail: no interior
soak optimum; the mid-diesel-price steam optimum sits below the BGW-8 slug range; and rod
damage from holding the float line (VFD-hold) is real but entirely unpriced in ₹.

---

## 4. The ML layer, honestly

### 4.1 Where the data comes from

Zero real cycles. **All 3,000 training rows are physics-generated.** Learn to say that
sentence without flinching — it is asked, and hesitating is worse than the fact.

The defence is genuine: this is not fabricated data, it is data produced by solving
four peer-reviewed models (Marx-Langenheim 1959, Andrade 1930, Vogel 1968, API RP 11L-style
rod mechanics) at 3,000 parameter combinations that a Latin-hypercube design chose to
cover the space evenly. Every row obeys energy conservation and the correct
viscosity-temperature law. The models therefore learn real physical structure. Standard
practice for digital-twin prototypes when field data is commercially sensitive.

**The line that separates a good answer from a great one:** "This makes the model
physically plausible. It does not make it field-validated. Those are two different
claims and we don't mix them."

**Update, 26–27 Sep:** the 3,000 rows were regenerated against the **rev-9 twin** (physics v3
+ economics v2, seed 42, same LHS design) and both regressors plus the classifier were
retrained on them — the dataset and models are current, not frozen v1 or rev-5 artefacts, as
of this pass. It remains **circular** by construction regardless of which physics generated
it: the surrogate learns *our* equations, so its scores measure imitation of our twin, not
agreement with the field. That's still the honest caveat to lead with.

### 4.2 What each model learns

`ml/train.py`, features = `[steam_t, soak_days, cutoff_m3d, spm]`, a **single 80/20
hold-out split** at seed 42 (2,400 train / 600 test). There was **no cross-validation, no
k-fold, and no RMSE** reported. If anyone (including an older doc) says otherwise, it's
wrong. This applies to the v1 run, the rev-5 retrain, and the current rev-9 retrain.

**Model 1 — `oil_model.joblib`: predict oil output (log target).** An `XGBRegressor` (300
trees, depth 4, lr 0.05, subsample 0.9) wrapped in `sklearn.compose.TransformedTargetRegressor`
with `func=np.log, inverse_func=np.exp`, predicting `log(oil_total_m3)`. This **replaces the
old v1 `sor_model.joblib`** (which fit SOR directly): since `steam_t` is a known decision
variable, only the denominator (oil) needs predicting — **SOR is derived**,
`SOR = steam_t / oil_model.predict(X)`, not separately fit. Rev-9 retrain: R² **0.998**
overall (0.996 inside the 1,000–2,000 t envelope).

**Model 2 — `margin_model.joblib` family: predict ₹ margin per cycle-day.** From rev 9
through rev 12, **the optimiser's actual objective was the incremental-margin model**
(`margin_incremental_inr_per_cycle_day` — over the cold, unstimulated well, see §4.4 and
`docs/model-improvement/TIER1_PROGRESS_LOG.md` §8). **As of rev 13 the objective is net
cash per cycle-day** (counterfactual-free) instead — the cold well's own status now
depends on the float policy, so an incremental figure would book that policy switch as
the recommendation's gain (§4.4 below); the canonical set-points are chosen by minimax
regret across the FY25 and $65 price decks. The incremental and gross-margin models are
kept too, for continuity/reporting only. Same XGBRegressor family, raw scale (no transform). Incremental:
R² **0.883** overall / **0.996** inside the envelope; gross: R² 0.862 overall / 0.997 in
envelope. The overall numbers are pulled down by a heavy negative tail in thin-steam,
high-cutoff corners nobody would run; inside the operating envelope both fit almost exactly.

**Model 3 — `float_model.joblib`: predict floating risk.** An `XGBClassifier` on the
binary label `(max_floating_index > 0.6) OR (alarm_days > 0)` (reduces to the `>0.6`
threshold in the dataset, since `alarm_days>0` is a strict subset). Rev-9 retrain:
positive class share 31.6% train / 29.2% test, **AUC 0.9994**, accuracy 0.985.

### 4.3 What the metrics mean — and don't (rev 9 retrain)

| Metric | Value | What it means | What it does NOT mean |
|---|---|---|---|
| Oil regressor R² (log target) | **0.998** overall, **0.996** in envelope | The surrogate explains ~99.8% of the variance in simulated oil output across the design space | Not real-world accuracy — it's agreement with our own twin |
| Oil regressor MAE | 4.43 m³ overall, ~3.5 m³ in envelope | Typical miss on oil output | Not a confidence interval |
| Incremental-margin regressor R² | **0.883** overall, **0.996** in envelope | Overall is pulled down by a heavy negative tail outside the operating envelope (thin-steam/high-cutoff corners nobody would run); inside 1,000–2,000 t steam it fits almost exactly | Don't quote the overall number alone without the envelope figure |
| Incremental-margin regressor MAE | ~₹619/day overall, **~₹235/day in envelope** | The hold-out MAE the optimiser page's error bar should quote | Not a field-validated error |
| Classifier AUC | **0.9994** | Near-perfect ranking of risky vs safe settings | Not proof it works on real rods |
| Classifier accuracy | **0.985** | At the 0.5 threshold | With ~30% positives, always quote AUC alongside |

All rows: rev-9 retrain, `ml/models/metrics.json`, single 80/20 hold-out, seed 42,
**no cross-validation**.

**Why is the overall margin R² only ~0.88 when the oil regressor is at 0.998?** Because
incremental margin/cycle-day can go sharply negative in corners the optimiser would never
pick (thin steam, high cutoff) — those large negative outliers dominate squared error over
the full design space. Inside the 1,000–2,000 t operating envelope (where the recommendation
and baseline both sit) it's 0.996. The optimiser mostly needs the surrogate to **rank**
settings correctly near the plausible region, and the winner is always re-verified by
re-running the physics twin, not just trusted from the surrogate.

**The surrogate-vs-physics spot-check:** the recommendation is re-verified by running the
true-physics grid directly (`ml/recommend_physics.py`), not just trusted from the surrogate
— see TIER1 §7.5/§8.6 for the gap analysis between the ML-optimiser's pick and the
true-physics grid optimum on both price decks.

### 4.4 Bayesian optimisation in one page

> **v1 engine (commit 351a89b): prototype outputs, historical, superseded.** The *method*
> (Bayesian optimisation, GP surrogate + acquisition function) is unchanged. The v1 result
> (1,585 t / 3 d / 7.76 / 10.2 spm → 0.88) is historical. The current result and objective
> (rev 9) are in the boxes below.

**The problem.** Four continuous knobs, a noisy non-convex objective, and a limited
evaluation budget. **Be careful with "expensive":** our physics twin is *not* expensive. One
full cycle is **0.55 ms**, which is faster than one surrogate call (**1.13 ms**). The method is
built for the case where the physics *will* be expensive, for example a CMG STARS run taking
minutes to hours.

**Why not grid search?** With 4 dimensions and only 10 levels each you already need
10,000 runs to get a resolution of one-tenth of each range — and 10 levels of steam
volume is a coarse 250 t step. Grid cost explodes as `levels^dimensions` (the curse of
dimensionality), and it spends the same effort on hopeless corners as on the promising
region. Random search is better but still blind. **Bayesian optimisation is the one that
learns while it searches.**

**How it works, in two ideas:**

1. **The surrogate.** Fit a Gaussian Process to the points evaluated so far. A GP gives
   you two things at every untested point: a *predicted value* and an *uncertainty*.
   Think of it as a contour map of the objective that also shades in how foggy each
   region is.
2. **The acquisition function.** Use both numbers to pick where to look next, balancing
   **exploitation** (go where the prediction is good) against **exploration** (go where
   the fog is thick, because something better might hide there). Evaluate there, add the
   point, refit the GP, repeat.

**Analogy for CS teammates:** it's epsilon-greedy bandits, except instead of a fixed
random-exploration rate, the uncertainty estimate tells you *precisely where* exploring
is worth it. Or: gradient descent for a function that has no gradient and costs money to
sample.

**Our settings** (`ml/optimize.py`): `skopt.gp_minimize`, `n_calls = 60` total
evaluations = **15 random initial points + 45 GP-guided calls** (these are not "restarts"),
`random_state = 42`. Search space read from `field_params.json`: `Real` steam_t and cutoff
ranges (cutoff now **[0.6, 2.0] m³/d**), `Integer` soak_days, and `spm` is restricted to
`srp.spm_practice_band` (**3–6**, heavy-oil practice), not the full sensor range [4, 12].
An optional `fixed={"soak_days": 10}` argument removes soak from the search entirely and
splices in the fixed value, since soak has no interior optimum to search for (see the
xfail note in the status banner). As of rev 13, `spm`, `stroke_in`, `p_wellhead_kgf_cm2`
and `float_policy` are all search dimensions too. **The exhaustive 6-lever × policy
true-physics grid in `ml/recommend_physics.py` (`best_settings_physics_5d`), not this
surrogate optimiser, is what the current rev-13 cascade recommendation (1,000 t / 10 d /
89 kgf/cm² / 64-in / start 4.5 spm / cutoff 0.60 backstop / VFD-hold) is actually taken
from** — the surrogate optimiser's own pick lands **~24% below** it at rev 13 (+₹11,635/d
vs +₹15,396/d FY25), so it is reported only as a cross-check. See `ml/README.md`
"Optimizer vs physics grid" for the comparison.

**The objective changed 26 Sep: maximise predicted ₹ margin/cycle-day, not minimise SOR —
changed again 27 Sep (rev 9): incremental margin, not gross — and changed a third time 27
Sep evening (rev 13): net cash per cycle-day, counterfactual-free.** Under the calibrated
physics SOR falls monotonically as steam volume drops — minimising it would just push
steam to the search floor. Gross margin credits CSS with oil the well makes anyway.
Incremental margin has its own rev-13 problem: the cold-well counterfactual itself now
depends on the float policy (shut in under `pull`/`vfd_hold`/`vfd_then_pull`, pumped
floating under `none`), so comparing incremental margin *across* policies would book that
counterfactual switch as if it were the recommendation's own gain — the exact structural
bug the technical re-score found. Net cash has no such term, which is why it is rev 13's
objective, subject to a **hard injectivity gate** replacing the old soft float-risk
penalty (below). `ml/optimize.py` is safe to run directly on the current branch — it uses
the rev-13 surrogates and rev-13 params (it will simply take longer than the twin itself,
since it's a 60-call Bayesian search).

**Note what the objective actually evaluates:** not the physics twin, but the *trained
surrogates* — with the winning candidate always re-verified against the real physics twin
before being reported (`physics_verified_optimum` in the return dict). **Why surrogates,
honestly** (since "physics is expensive" is false today):
1. **Contract-first design.** The optimiser talks to a predictor interface. When the
   physics becomes CMG-class expensive, the same optimiser still works.
2. **Batching.** A batched XGBoost call is ~262× faster per candidate than looping the
   twin. That matters for 10⁴-candidate schedule searches and multi-well steam allocation.
3. **Historically, a smooth constraint** (through rev 12 only — see below). The classifier's
   p(float) was a smooth probability, used as a soft optimisation penalty instead of the
   twin's hard 0/1 threshold crossing. **Rev 13 drops this**: p(float) is informational only
   now, not a search constraint (next paragraph).

**Constraint handling — replaced at rev 13.** Through rev 12, SPEC's floating-probability
< 0.3 constraint was a *soft* penalty method, maximising margin minus penalty:

```python
if float_prob >= FLOAT_PROB_LIMIT:            # 0.3
    penalty = PENALTY_SCALE * (float_prob - FLOAT_PROB_LIMIT)   # excess, in ₹/day units
return margin_pred - penalty
```

**Rev 13 drops this entirely.** Once the operator's float response is itself a policy
(`pull`/`vfd_hold`/`vfd_then_pull`), penalising "risk of floating" fights the physics
rather than pricing a real cost — under every policy, the pull *is* that policy's own float
response, so a float-risk penalty was penalising the operating rule itself (a re-score
finding). It is replaced by a **hard injectivity gate**: the candidate's sandface pressure
must clear `steam.min_injection_margin_kPa` (400 kPa) over the reservoir's pre-cycle
pressure — a real physical constraint (steam cannot enter the formation below it), computed
directly from the steam-state physics, not gated on a surrogate. This description is the
surrogate's own optimiser (`ml/optimize.py`); the physics-grid recommendation (the actual
decision engine) instead uses the **float-onset produce-end rule plus its policy** directly
— under VFD-hold every case (reference, baseline, recommendation) is held at the float
alarm line for 3 days at the 2-spm floor, which is exactly what ends the cycle.

**Never say "guaranteed global optimum."** Bayesian optimisation is a sample-efficient
heuristic over a non-convex objective. The correct phrasing is "a very good,
often near-optimal solution within a limited evaluation budget."

### 4.5 The recalibration story for real OIL data

Two levels, and know both:

**Level 1 — parameter recalibration, and as of rev 9 this is now an actual built loop, not
just a plan.** `twin/calibrate.py` fits the twin's biggest uncertain constants
(`water_cut`, `thickness_m`, `AOF_REF_M3D` — `bl_delta_factor` is sourced now, not fitted)
to observed CSS cycles (`scipy.optimize.least_squares`, bounded, deterministic), and
`ml/recommend_physics.py` re-recommends set-points directly against the recalibrated
**physics** (grid search, no surrogate — the trained ML surrogate was fit on the old
physics and would silently mismatch a recalibrated params tree). `POST /calibrate` and
`GET /calibrate/demo` expose it over the API. On a synthetic pseudo-real demo (hidden truth,
not real OIL data): `water_cut` recovers within 0.2%, `aof_ref_m3d` within 1.6%,
`thickness_m` within 0.9% — `bl_delta_factor` and `water_cut` are jointly identifiable only
through their ratio (Jacobian correlation ≈ −1), and `thickness_m`/`aof_ref_m3d` similarly
correlate at ≈0.97–0.99, both disclosed, not hidden (TIER1 §6.2, §8.7). Feed it a CSV of a
few dozen real cycles and the loop runs in well under a second. Beyond that, updating any
other field value in `field_params.json` still flows into a full re-run:
`twin/generate_data.py` → `ml/train.py` → `ml/optimize.py`. **How long the full retrain
takes is unverified**; the old claim "under an hour" was never timed end to end, so don't
promise it. The first ask of OIL is **cycle records and dyno cards**. The highest-value
single measurements beyond calibration-loop inputs are a **high-temperature viscosity
point** to replace the 150 °C / 50 cP anchor in `viscosity.py`, **real pump geometry**
(the rod string is still `[TYPICAL]`, not Baghewala-specific), and **net-pay thickness**
from a well log.

**Level 2 — model recalibration (sim-to-real).** Add OIL's real historical cycles to
the training set — either mixed in directly, or with the synthetic rows down-weighted
against a smaller real dataset. XGBoost handles small, mixed tabular datasets far better
than a deep model would, which is part of why it was chosen. The Bayesian optimiser's
surrogate then gets updated with real observed SOR and floating outcomes as they arrive.

**And the validation that comes with it:** compare twin-predicted SOR and floating risk
against known-outcome historical cycles; check directional agreement between what the
twin recommends and what actually worked; then advisory-mode pilot with a human in the
loop before anything resembling closed-loop control.

---

## 5. Code map — "if a judge asks X, the answer is in file Y"

> **Current code, rev 9.** File and function names below are the **rev-9** code
> on `main` unless a row says v1/historical. The v1 code is at commit 351a89b; a
> worktree of 6bb604d reproduces it only if someone specifically wants the old numbers.

| If a judge asks… | Look in | Specifically |
|---|---|---|
| "How do you model reservoir heating?" | `twin/thermal.py` | `steam_zone_temperature()`, `_heat_loss_efficiency()`, `wellbore_delivery()` — now credits sensible **and** latent heat |
| "How does the zone cool after injection?" | `twin/thermal.py` | `boberg_lantz_theta()` (exact-cylinder form), `cylinder_theta()` (replaced v1's τ = 20 d exponential) |
| "Where does the heat go / how much is lost?" | `twin/thermal.py` | Sensible + latent heat balance, wellbore loss (sandface quality 0.55 × wellhead), no longer double-counted |
| "Why 8 metres drainage radius?" (v1, historical) | `params/CHANGELOG.md` (v1 retune note) | It was a fudge that manufactured the SOR optimum, and it's deleted. Now `reservoir.drainage_radius_m = 100` |
| "How does viscosity change with temperature?" | `twin/viscosity.py` | `mu_cP()`, `_fit_walther()` (Walther/ASTM D341, 1 cP floor); v1 used `_fit_andrade()` |
| "Where did the viscosity constants come from?" | `twin/viscosity.py` `ANCHOR_T_C/ANCHOR_MU_CP` | One CONFIRMED anchor (11,500 cP @ 50 °C) + one ASSUMPTION anchor (50 cP @ 150 °C) |
| "What's your inflow model?" | `twin/ipr.py` | `oil_rate_m3d()`: Vogel + `composite_uplift()` (v1: mobility factor μ_ref/μ) |
| "Why is the cold well uneconomic?" | `twin/ipr.py` `AOF_REF_M3D = 0.46` | Cold ≈ 0.447 m³/d, below the [0.6, 2.0] cutoff range |
| "How does reservoir pressure behave?" | `twin/cycle.py` | `_p_res_at()` charge/bleed; `_pump_intake_pressure_kPa()` gives absolute P_wf ≈ 1,144 kPa. P_res xfail **closed** (rev 9) — re-specified as a derived Darcy/Vogel band, which the twin now sits inside |
| "How do you compute rod load?" | `twin/srp.py` | `pump_state()`; W_b + F_f + F_v; oil capacity now compared against **liquid** rate, not oil-only (the 6.7× bug fix) |
| "What is the floating index exactly?" | `twin/srp.py` | `FI = min(F_v / W_b, 1)`, threshold 0.6 (our design choice) |
| "How is pump capacity limited?" | `twin/srp.py` | `FILLAGE_MAX = 0.85`; oil capacity = displacement × fillage × (1 − water_cut) |
| "Why does SPM decline during production?" | `twin/srp.py`, `twin/cycle.py` | `max_spm_for_viscosity()`, `SPM_MARGIN = 1.0` (enforces the physical fall-velocity limit; 0.6 is now only the risk-alarm threshold), floor 2 spm |
| "Is the dynamometer card real?" | `twin/dyno.py` | Computed Gibbs (1963) rod wave-equation FD solve, not RP 11L chart-based; rod-float carrier-bar separation onset independently reproduces the ≈0.6 FI alarm line |
| "How do the phases fit together?" | `twin/cycle.py` | `simulate_css_cycle()` — inject / soak / produce loop |
| "When does the cycle stop?" | `twin/cycle.py` | `if prod_rate < cutoff_m3d: break` |
| "Where do the headline metrics come from?" | `twin/cycle.py` | `summary(df, params)`: oil, gross SOR, days, max FI, plus ₹ (gross and incremental), CO₂, margin/cycle-day, graded float damage |
| "How do you calibrate from real field data?" | `twin/calibrate.py`, `ml/recommend_physics.py` | `fit()`/`apply()` — fits water_cut/thickness/AOF from an observed-cycles CSV, then re-recommends against the recalibrated physics; `POST /calibrate`, `GET /calibrate/demo` |
| "How did you sample the design space?" | `twin/generate_data.py` | `qmc.LatinHypercube(d=4, seed=42)`, `_sample_inputs()`; 3,000 rows regenerated against rev-9 physics |
| "What ML models, what hyperparameters?" | `ml/train.py` | `train()`; XGBRegressor ×2 (gross + incremental margin) + XGBClassifier, 300/4/0.05 |
| "Why log-transform the oil target?" | `ml/train.py` | `TransformedTargetRegressor` on oil (not SOR directly); SOR is now derived, `steam_t / oil_pred` |
| "What are your metrics?" | `ml/models/metrics.json` (rev 9) | Oil R² 0.998 (0.996 envelope); incremental-margin R² 0.883 (0.996 envelope); classifier AUC 0.9994, acc 0.985; single 80/20 hold-out, no CV |
| "How does the optimiser work?" | `ml/optimize.py` | `best_settings()`, `gp_minimize`, 60 calls = 15 random initial + 45 GP-guided; **maximises net cash/cycle-day** (rev 13; was incremental margin), spm/stroke/pressure/float_policy all searched, soak can be fixed via `fixed={"soak_days": 10}` |
| "How is the safety constraint enforced?" | `ml/optimize.py` | Rev 13: a hard **injectivity gate** (≥400 kPa sandface margin) — the old soft P(float) penalty (`PENALTY_SCALE`, `FLOAT_PROB_LIMIT = 0.3`) was dropped, since penalising float risk once it's a policy choice fights the physics |
| "What's the baseline you compare against?" | `ml/optimize.py` | **Published-practice** (1,300 t / 10 d / 1.3 m³/d / 5 spm), derived from OIL's own BGW-8 first CSS job — one documented data point, **not** OIL's current practice; as of rev 13 always name which float policy it's run under |
| "Show me the API" | `api/main.py` | `/params`, `/simulate`, `/optimize`, `/calibrate` — agrees with the dashboard directly from `main`, no worktree needed |
| "Is the dashboard faked?" | `dashboard/README.md`, `dashboard/src/core.js:9` | `MOCK = true`; the two baked scenarios (assumed baseline, recommendation) are physics-verified output, **including the computed dyno card**; other set-points + the 12-spm stress test's oil/margin numbers are the JS heuristic `mockSimulate` |
| "What did you test?" | `tests/` | **263 passed, 2 xfailed** (soak; mid-diesel-price steam optimum below the BGW-8 slug range — documented, known gaps, not failures) |
| "What changed after the audit and the calibration?" | `docs/model-improvement/TIER1_PROGRESS_LOG.md` §4–§12, `MODEL_IMPROVEMENT_PLAN_{PHYSICS,ML,ECON_VALIDATION}.md` | What was wrong in v1, what Tier-1 replaced, the three bugs found and fixed in the 26 Sep calibration, sourcing the BL constant, moving to incremental then net-cash economics, and rev 13's operating-policy fix |
| "Where do your field numbers come from?" | `docs/research/baghewala_facts.md` | CONFIRMED / TYPICAL / DERIVED labels + URLs |
| "What did you change and why?" | `params/CHANGELOG.md` (rev 13) | Field-by-field diff and rationale for every constant touched, rev 1 through rev 13 |
| "Define [any term]" | `docs/guides/GLOSSARY.md` | ~83+ terms including the calibration vocabulary (margin/cycle-day, assumed baseline, xfail, sensible vs latent heat, CWE, VFD-hold, float policy, injectivity margin) |
| "Tough Q&A / trap questions" | `docs/study/viva_prep.md` | Safe-to-say block, K1–K40, traps, cheat table — rev 13 |

### How to run everything

**Always use the venv.** Bare `python` on this machine is a broken MSYS2 build.

```bat
cd <repo>

.venv\Scripts\python.exe -m pytest tests -q        :: 263 passed, 2 xfailed
```

**Now SAFE to run** on `main` (they were not, before calibration):

```bat
.venv\Scripts\python.exe twin\generate_data.py      :: ~24 s for 3,000 rows — OVERWRITES data/synthetic_cycles.csv
.venv\Scripts\python.exe ml\train.py                :: retrains all 3 models — OVERWRITES ml/models/*
.venv\Scripts\python.exe ml\optimize.py             :: 60-call Bayesian search, reproduces the recommendation
```

Run them if you want to demonstrate the pipeline end to end — just know they take time and
overwrite the current artefacts, so don't kick them off casually right before a demo.

**Why 2 tests are xfailed, and why that's fine (not a failure):** soak has no interior
optimum (Boberg–Lantz gives no soak benefit beyond conduction, so the recommendation holds
soak fixed at practice instead); and a cold, unstimulated well cannot be rod-pumped at the
2-spm keep-moving floor under any published emulsion law (field produced these wells cold,
so a model assumption is off somewhere) — both disclosed, understood, not silent bugs.

**API — the physics grid, not the surrogate, is the recommendation source:**

```bat
.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000
curl "http://localhost:8000/params"
curl "http://localhost:8000/simulate?steam_t=1300&soak_days=10&cutoff=1.3&spm=5"   :: baseline, default policy `pull`: gross SOR ~4.35; under VFD-hold: ~3.29
curl "http://localhost:8000/api/recommend/physics"                                :: physics-grid recommendation (rev 13, VFD-hold), gross SOR ~2.83
curl "http://localhost:8000/api/schedule/demo"                                    :: field scheduler demo
curl "http://localhost:8000/api/dyno/classify/demo"                               :: measured-card classifier demo
curl "http://localhost:8000/calibrate/demo"                                       :: calibration-loop demo
```

(If a judge specifically wants the old v1 or rev-9 numbers for comparison, those require an
old worktree or commit — out of scope for the current demo.)

**Dashboard (v4, four pages).** `dashboard/index.html` (Overview, read-only),
`console.html` (Twin console: Simulate cycle, Replay, Stress test (12 spm), Reset, alarm
with ACK), `optimizer.html` (Run optimiser → Stage set-points → Confirm; the console then
offers **Load into console**), `methodology.html` (Model basis: equations, validation
status, what is NOT validated). Plotly is now bundled locally (`dashboard/vendor/`), so the
charts need no internet. The built pages are **generated**: edit `dashboard/src/`, then run
`node dashboard/build.js`. The data source is `const MOCK = true;` at
**`dashboard/src/core.js:9`**:

- `MOCK = true` → serves `BAKED` (in `src/data.js`), **verbatim rev-9
  `twin.cycle.simulate_css_cycle` output** at exactly two set-points: the published-practice
  baseline (1,300/10/1.3/5) and the rev-9 recommendation (1,600/10/0.70/4) — **including the
  computed dynamometer card** (`twin/dyno.py`, baked via `dashboard/src/dyno-data.js`).
  **This bake is pending its rev-13 update** (the cascade's next job) — say the rev-13
  numbers from the status banner on stage regardless of what the bake currently shows, and
  flag the gap honestly if asked. Any other set-point, including the 12-spm stress test's
  oil/margin numbers, is the in-browser heuristic `mockSimulate`, and the panel meta says
  "in-browser approximation" vs "baked twin output".
- `MOCK = false` → live calls to `http://localhost:8000`, now the current rev-13 physics
  directly (the API is not baked; it runs the live engine). **There is no automatic
  fallback**: if the API fails, the status chip shows "Data source error · …".
- The rebuilt dashboard prints a stale test-count tag pending its own re-bake; **say "263
  physics & benchmark tests, 2 known gaps marked xfail" from this guide regardless of what
  the dashboard chip currently shows**, and flag the gap honestly if asked. Neither 24/24,
  21/24, 57/57, 60, nor 236 is current any more.

Useful URL params for QC and the demo: `?autoreplay`, `?lang=hi`, `?theme=dark`,
`?qc=replay`, `?qc=alarm`, `?qc=optimized`, `?qc=staged` (optimiser: run, stage, confirm),
`?qc=loadstaged` (console: load the staged set-points and re-simulate). Demo flow:
`docs/guides/DEMO_SCRIPT.md`.

**If you change the physics**, the dashboard's baked numbers go stale. Re-bake per
`dashboard/README.md`'s re-baking section: update `BAKED` in `src/data.js` and the derived
constants in `src/core.js`, then run `node dashboard/build.js`.

---

## 6. Number discipline table

**The rule: if it's on this table, know its label. If it's not on this table, don't say
it on stage.** Three labels:
**CONFIRMED** (a cited source states it) · **LITERATURE-TYPICAL** (industry-general, not
Baghewala) · **OUR-SIMULATION** (our twin computed it; real only if our assumptions hold).

> **v1 engine (commit 351a89b): prototype outputs, historical, superseded.** Rows 30–51 are
> the v1 simulation and constants block, kept so you can recognise what the old dashboard and
> deck showed, but **don't state any of them as a current result**. Field facts (rows 1–29)
> are unaffected. Rows 53–66 record the 13 Sep Tier-1 (then still uncalibrated) engine —
> also historical now. Rows 67–82, marked ~~struck~~ below, were the rev-12 (physics wave 4)
> numbers — superseded 27 Sep evening, because their headline gain turned out to be the
> baseline's own pull-on-float rule, not the set-points (the technical re-score's top
> finding). **Rows 83+ are the current, rev-13 numbers — safe to quote.**
> Row numbers are unchanged throughout so older references still work.

| # | Number | Source | Label |
|---|---|---|---|
| 1 | API gravity 17–19° | PS SIH26120 text | CONFIRMED (as PS text) |
| 2 | API gravity 14–17° (current producing crude) | SPE-23APOG-535203 + OIL internal PPT | CONFIRMED |
| 3 | Reservoir temperature 46–48 °C | PS SIH26120 text | CONFIRMED (as PS text) |
| 4 | Bottom-hole temperature ~50 °C | OIL internal PPT (12.07.2025) | CONFIRMED |
| 5 | Viscosity 8,000–15,000 cP @ 50 °C | SPE-23APOG-535203 | CONFIRMED |
| 6 | Viscosity 10,000–13,000 cP @ 50 °C | OIL internal PPT | CONFIRMED |
| 7 | μ_ref = **11,500 cP** used in our model | midpoint of #6 | CONFIRMED (derived midpoint) |
| 8 | Depth ~1,100–1,150 m | oil-india.com; SPE-23APOG; OIL PPT | CONFIRMED |
| 9 | Reservoir pressure ~116 kgf/cm² = 11,400 kPa | OIL internal PPT | CONFIRMED |
| 10 | Porosity <10% (we use 0.09) | Basha et al., GEOHORIZONS Jan 2015 | CONFIRMED |
| 11 | Steam temperature 280–305 °C (we use 290) | OIL internal PPT (BGW-8) | CONFIRMED |
| 12 | Steam quality 60–70% (we use 0.65) | OIL internal PPT (BGW-8) | CONFIRMED |
| 13 | Steam rate ~3,100 kg/hr ≈ **74 t/d** | OIL internal PPT (BGW-8) | CONFIRMED |
| 14 | Injection 14–21 d; soak 50–60% of injection (~7–13 d) | OIL internal PPT (BGW-8) | CONFIRMED |
| 15 | India's first CSS: BGW-8, Dec 2018, Belgrave partner | Oil & Gas Journal; oil-india.com | CONFIRMED |
| 16 | 5–6× production uplift after first CSS cycle | OGJ; OIL internal PPT | CONFIRMED |
| 17 | 39 CSS cycles by Jun 2025; 19 CSS jobs in FY26 (+72%) | OIL PPT; PSU Watch; BusinessToday | CONFIRMED |
| 18 | 52–56 drilled / 33–34 operational wells | oil-india.com; 2026 news | CONFIRMED (snapshot-dependent) |
| 19 | Production 218 t (FY17) → 32,787 t (FY25) → 43,773 t (FY26), ~200× since commercial **production** began (FY17 predates the first CSS, Dec 2018) | OIL PPT; PSU Watch | CONFIRMED |
| 20 | Artificial lift is SRP; vacuum-insulated tubing used | oil-india.com | CONFIRMED |
| 21 | CSS SOR 3–8, average ~6, efficient below 3 | ScienceDirect; Wikipedia | LITERATURE-TYPICAL |
| 22 | **Baghewala's own actual SOR — NOT PUBLISHED** | — | **NEVER STATE A NUMBER** |
| 23 | Rod-pump workover $15k–$50k per event | iFactory industry article | LITERATURE-TYPICAL |
| 24 | Steam generation ~2.6–4 GJ/t (~720–1,200 kWh/t) | Thundersaid Energy | LITERATURE-TYPICAL |
| 25 | ~71 kg diesel/t steam ≈ 3.0 GJ/t at Baghewala | DERIVED from #13 + 220 kg/hr HSD (OIL PPT) | CONFIRMED-derived |
| 26 | CSS depth-efficiency limit ~1,000–1,500 m | industry rule of thumb | LITERATURE-TYPICAL (verify) |
| 27 | Reservoir thickness 12 m | not found for Baghewala; SPEC default | ASSUMPTION |
| 28 | k = 2.5 W/m·K, ρcp = 2.3×10⁶ J/m³K | generic sandstone literature | LITERATURE-TYPICAL |
| 29 | Stroke 3.0 m, plunger 0.057 m, rod 3.8 kg/m, spm 4–12 | generic heavy-oil SRP practice | LITERATURE-TYPICAL |
| 30 | Andrade A = 1.164×10⁻⁶, B = 7,436.6 K | v1 fit to #7 + the 150 °C/50 cP anchor | v1 only (retired; gave 0.63 cP at 290 °C) |
| 31 | 150 °C / 50 cP high-T anchor | `twin/viscosity.py` (still used, now through Walther) | **ASSUMPTION** (current) |
| 32 | `DRAINAGE_RADIUS_M = 8.0` | v1 tuning to create an SOR optimum | **v1 FUDGE, deleted**; now `drainage_radius_m = 100` (realistic 50–150 m) |
| 33 | `AOF_REF_M3D = 0.7` (v1) → 0.60 (Tier-1, uncalibrated) → **0.46** (rev 5, calibrated) | tuning; no measured PI | v1/Tier-1 historical; **0.46 is current default**, cold rate 0.447 m³/d (calibration loop can refit this per-well) |
| 34 | `K_VISC = 10.0`; `COOLDOWN_TAU_DAYS = 20` | tuned | K_VISC current ASSUMPTION; τ **deleted** (Boberg–Lantz) |
| 35 | Floating threshold 0.6; constraint <0.3 probability | docs/SPEC.md definition | our design choice (current) |
| 36 | Reference cycle SOR **1.2943 t/m³** | v1 `twin` at 1500/7/3.0/8.0 | **v1 OUR-SIMULATION, superseded** |
| 37 | Reference oil 1,158.96 m³ over 61.27 d | same v1 run | v1, superseded |
| 38 | Peak rod load 85.6 kN, peak FI 0.539, 0 failures | same v1 run | v1, superseded |
| 39 | Peak T 244 °C, min μ **2.04 cP** (at 244.2 °C; 2.18 cP was the day-20 row at 241.8 °C), heated radius 7.20 m | same v1 run | v1, superseded (current Walther: 7.2 cP at 244 °C) |
| 40 | Pump ceiling 74.96 m³/d at 8 spm = **471 bbl/d** | v1 `srp.pump_state` | v1, superseded; field ~19 bbl/d per well |
| 41 | Optimiser rec: 1,585 t / 3 d / 7.76 / 10.2 spm | v1 `ml/optimize.py` | v1, superseded (10 SPM and 3 d soak are artefacts) |
| 42 | Predicted SOR **0.8816 ± 0.31**, float prob 0.0011 | v1 surrogate | v1, superseded |
| 43 | Physics twin re-check at that rec: SOR 0.8922 | v1 `twin` | v1, superseded |
| 44 | As-applied optimum (1,600/3/8/10): SOR 0.9062, 1,765.6 m³, 53.6 d, FI 0.255 | v1 `twin` | v1, superseded (current engine: 9.95, worse than reference) |
| 45 | Optimiser baseline (midpoint 1750/9/4.5/8): SOR 1.5022 | v1 surrogate | v1; midpoint scenario, **not** field practice |
| 46 | Headline **−30.0%** (1.29 → 0.91) | #36 vs #44 | **NEVER STATE AS A RESULT**; only as "v1 prototype, since audited" |
| 47 | Secondary **−41.3%** (1.50 → 0.88); deck slide 5 | `improvement_pct` | **NEVER STATE AS A RESULT**; same framing |
| 48 | 3,000 cycles, LHS, seed 42; dataset mean SOR ≈ 2.96 | v1 `twin/generate_data.py` | v1, frozen artefact |
| 49 | R² 0.7246, MAE 0.3068, AUC 0.9989, accuracy 0.98 | `ml/models/metrics.json` | v1, frozen; **single 80/20 hold-out, no CV** |
| 50 | ~~24/24~~ → ~~21/24~~ → ~~57~~ → ~~116/127~~ → ~~236~~ → **263 passed, 2 xfailed** (current, rev 13) | `pytest tests -q` on branch `wave5` | OUR-VERIFICATION — see row 71 |
| 51 | ~~₹0.61 crore/yr~~: **withdrawn** (₹1,300/t was a gas price on a diesel field, and 6.8 cycles/well/yr is impossible) | — | **NEVER STATE.** Use row 60 (per-cycle fuel) instead |
| 52 | Real CSS cycles in our training data: **ZERO** | — | CONFIRMED about ourselves |
| 53 | Field output ~**655 bbl/d** (10 Jul 2025) | OIL internal PPT | CONFIRMED |
| 54 | Record **1,202 bbl/d** (FY26, up ~70% from 705) | BusinessToday, Apr 2026 | CONFIRMED |
| 55 | ≈19 bbl/d per well (655 ÷ ~34 operational wells) | DERIVED from #53 + #18 | DERIVED (why 471 bbl/d/well is impossible) |
| 56 | Heavy-oil SPM practice 3–6 | heavy-oil SRP literature | LITERATURE-TYPICAL |
| 57 | CSS cycles on a well 6–18 months apart | CSS literature (`css_thermal_eor_deep_dive.md`) | LITERATURE-TYPICAL (why we never annualise) |
| 58 | ONGC's thermal heavy-oil work is at **Mehsana, Gujarat** (Balol/Santhal, in-situ combustion) | SPE-89451 | CONFIRMED (not Assam or Rajasthan) |
| 59 | 71 kg HSD per t steam → **₹5,900–8,400/t**, **~224 kg CO₂/t** | DERIVED from #25 + diesel price (upper = Rajasthan pump price) | CONFIRMED-derived |
| 60 | A 1,500 t cycle ≈ **₹0.9–1.25 crore of diesel**, **≈336 t CO₂** | #59 × 1,500 t | DERIVED, **per cycle only** |
| 61 | Tier-1 engine, uncalibrated (13 Sep), 1,500/7/**1.5**/8: SOR 9.83, 152.6 m³, 93 d, peak 17.8 bbl/d, uplift ~4× | Tier-1 `twin`, run 13 Sep | **HISTORICAL — superseded by rev-5 calibration, row 67** |
| 62 | Tier-1 engine at the v1 set-points (cutoff 3.0): SOR ≈ 530 (dies produce-day 1; peak 2.83 m³/d) | same | HISTORICAL |
| 63 | Tier-1 engine, v1 "optimum" at cutoff 1.5: SOR 9.95 (1.2% worse) | same | HISTORICAL |
| 64 | Current viscosity (Walther): 7.2 cP @ 244 °C, **4.13 cP @ 290 °C**, floor 1 cP | `twin/viscosity.py` | OUR-MODEL (anchors per #31); unchanged in rev 9 |
| 65 | ~~Recalibration target: SOR ≈ 4.4 at 1,500 t~~ **met and exceeded — see row 67** | `TIER1_PROGRESS_LOG.md` §4 | superseded, target achieved |
| 66 | Twin cycle ~8 ms/cycle vs surrogate call — still far cheaper than a CMG-class run | `TIER1_PROGRESS_LOG.md` §5.1 | MEASURED (why "physics is expensive" is false) |
| ~~67~~ | ~~Rev-9 (physics v3), reference set-point: gross SOR 4.027, incremental SOR 5.403~~ | ~~superseded~~ | ~~HISTORICAL — water cut was a constant 85%, cycle ended on rate cutoff only~~ |
| ~~68–69~~ | ~~Rev-9 baseline 1,300/10/1.3/5 → SOR 4.061; rev-9 recommendation 1,600/10/0.70/4 → SOR 3.590, +₹4,423/cycle-day~~ | ~~superseded~~ | ~~HISTORICAL — 83–96% of that gain was the assumed baseline cutoff moving (external review finding)~~ |
| ~~67~~ | ~~Rev-12, reference set-point: gross SOR 4.50, incremental SOR 5.91, ends by float onset day 151~~ | ~~superseded~~ | ~~HISTORICAL — reference is unchanged in rev 13 (still `pull`), but "incremental SOR" is no longer the ₹ basis~~ |
| ~~68~~ | ~~Published-practice baseline, pull: gross SOR 4.35, incremental ₹/cycle-day −1,601 (FY25) / −11,295 ($65)~~ | ~~superseded~~ | ~~HISTORICAL — see row 84 for the same baseline under VFD-hold~~ |
| ~~69~~ | ~~Recommendation: 1,000/10/85/64-in/3 spm → gross SOR 3.19, incremental ₹/cycle-day +7,973 (FY25)/+40 ($65). Gain: SPM 62%, stroke 32%, cutoff 0%~~ | ~~superseded~~ | ~~HISTORICAL — the re-score found this whole gain was the baseline's pull rule, not the set-points; see row 85~~ |
| ~~70~~ | ~~"Recommended cycle burns less steam" framing~~ | ~~superseded~~ | ~~still true under VFD-hold, restated at row 86~~ |
| **71** | Tests: **263 passed, 2 xfailed** (soak; the mid-diesel-price steam optimum sits below the BGW-8 slug range — the rev-12 cold-well xfail is now un-xfailed) | `pytest -q` on branch `wave5` | OUR-VERIFICATION, disclosed gaps not hidden |
| **72** | ML's honest role: the 6-lever × policy physics grid (40,194 feasible points/policy) is the decision engine; the Bayesian surrogate lands **~24% below** it (+₹11,635/d vs +₹15,396/d FY25) and is a cross-check only. Float classifier now informational, not a search constraint | `ml/README.md` "Optimizer vs physics grid" | OUR-VERIFICATION; single 80/20 hold-out, **no CV** |
| **73** | Steam cost bulk (base case, 0.15 discount) ₹7,111/t / retail ₹8,366/t — discount base moved 0.30→0.15 this rev | `params/CHANGELOG.md` rev 13 | CALIBRATED (discount unsourced) / DERIVED |
| **74** | `BL_DELTA_FACTOR = 0.5` **sourced** — exactly the ½ inside Boberg & Lantz's own δ (PEH Eqs. 15.70–15.74), computed per produce-day, not fitted | `docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md`; CHANGELOG rev 7 | OUR-MODEL, sourced — **never call this "unverified"** |
| **75** | Price decks: OIL's **CONFIRMED FY25 realisation** ₹5,992/bbl (base); $65/bbl planning floor ₹4,840/bbl (comparison preset); **new, rev 13: net of royalty+cess ~₹3,600/bbl** (~35% levies, OIL's own FY25 Annual Report exchequer table) — every feasible point is net-cash-negative on this deck | `params/CHANGELOG.md` rev 13 | CONFIRMED (price) + ASSUMPTION (discount, levy rates) |
| ~~76~~ | ~~UQ (rev 12): P(rec beats baseline) 94.3%/98.0%; P(incremental margin>0) 34%/12%~~ | ~~superseded~~ | ~~HISTORICAL — see row 88 for the rev-13, same-policy UQ~~ |
| **77** | Real-data benchmark: CalGEM 2021 field SOR band **3.47–8.24** (9,692 real CSS cycles, 5,771 CA wells) — our gross SOR sits inside it, unchanged by rev 13 | `docs/research/CALGEM_CSS_BENCHMARK_2026-09-26.md` | CONFIRMED (real, external data) |
| **78** | Calibration demo: formation_water_cut/aof/thickness recovered within **−5.2/−0.9/−10.9%** of a hidden truth (re-run under rev 13, story and recovery unchanged) | `ml/models/calibration_demo_report.json` | OUR-VERIFICATION, synthetic demo, not real OIL data |
| **79** | Dyno card: computed (Gibbs wave equation); measured-card classifier, 94.8% hold-out accuracy, 5 fault classes — never seen a real card, never call it field-validated | `docs/model-improvement/DYNO_CARD_MODEL.md`; `ml/README.md` | OUR-MODEL — **no longer "illustrative"** |
| **80** | Cold well: now **shut in** under every float policy except `none` (FI 1.0, 189 kN at the 2-spm floor) — every absolute incremental ₹ figure is therefore an upper bound; the `pumpable` counterfactual (~₹11.4k/d lower) is field-consistent and reported alongside it | TIER1 §12.4 | OUR-FINDING, un-xfailed this rev |
| ~~81~~ | ~~Field scheduler (rev 12, pull everywhere): naive loses ₹13.3k/d field-wide; exact earns +₹46.6k/d~~ | ~~superseded~~ | ~~HISTORICAL — see row 89, every well now VFD-hold~~ |
| **82** | External reviews, 27 Sep: judge-shaped review scored **61/100**; technical review scored **52/100**, then **re-scored 58/100** after the rev-10–12 hardening cascade — its top finding (the rev-12 gain was the pull rule, not the set-point) is what rev 13 answers | `TIER1_PROGRESS_LOG.md` §9, §12; `PROJECT_LOG.md` §16 | CONFIRMED (our own review process) |
| **83** | **Rev-13 (physics wave 5): the operator's response to rod float is now a control.** `css.float_policy` ∈ `pull`/**`vfd_hold`**/`vfd_then_pull`/`none`, applied alike to the baseline, the recommendation, and the cold counterfactual (shut in, not pumpable, once it floats under a policy) | `params/CHANGELOG.md` rev 13; TIER1 §12 | OUR-MODEL, current |
| **84** | Baseline (b), VFD-hold: 1,300 t/10 d/91 kgf/cm²/86-in/5 spm → **SOR 3.29**, 395 m³ oil, net cash +₹12,064/−₹582/−₹14,193 (FY25/$65/net-of-levies) | TIER1 §12.3 | OUR-SIMULATION + CONFIRMED inputs |
| **85** | **Recommendation, VFD-hold: 1,000 t / 10 d / 89 kgf/cm² / 64-in / start 4.5 spm / cutoff 0.60 backstop → SOR 2.83**, 353 m³ oil, net cash **+₹15,396/+₹3,738/−₹8,811** (FY25/$65/net-of-levies) | TIER1 §12.5 | OUR-SIMULATION, physics-verified |
| **86** | **The gain, naming the baseline's own policy** (net cash ₹/cycle-day, FY25/$65/net-of-levies): same policy (VFD-hold) **+3,332/+4,319/+5,382** (decomposes stroke 57%/cutoff 30%/steam 11%); if baseline pulls **+12,917/+14,694/+16,606** (68% is the policy switch alone); if baseline does nothing about float, the canonical recommendation still **gains +2,622/+3,484/+4,413** (TIER1 §12.6 "mixed" row — the older −3,865/−2,513/−1,057 figure was a different, non-canonical plan and is retired). Rod damage unpriced either way | TIER1 §12.6 | OUR-SIMULATION — **never quote one number without naming the policy** |
| **87** | Rod damage: VFD-hold holds FI at 0.6 for ~55–60 days/cycle, graded damage index (Σ FI³) ~5× the `pull` policy's — entirely unpriced in ₹ | TIER1 §12.3 | OUR-FINDING, disclosed, not fixed |
| **88** | UQ (1,500 draws, 3 decks): P(injectable)=1.000 everywhere; same-policy P(rec>baseline), VFD-hold: **96%** against a baseline whose 1.3 m³/d cutoff we chose (raw draws 0.965/0.992/0.999, FY25/$65/net-of-levies); **84%** (median ₹2.5k/day) with the same 0.6 backstop; **≈ 0%** if the VFD can run below 2 spm as our own cold well does; if baseline pulls 0.991–1.000; if baseline does nothing, only 0.16–0.25; same-policy gain p10/p50/p90 (FY25) +2,175/+12,101/+161,014 | `ml/models/uq_summary.json` | OUR-VERIFICATION, true physics, not the surrogate |
| **89** | Field scheduler, every well VFD-hold: naive is now **+₹72,320/d** field-wide (was a rev-12 pull-everywhere **loss** of −₹13.3k/d); exact scheduling +₹109,799/d, serving 10 of 12 wells | `ml/models/field_schedule_demo.json`; `ml/README.md` | OUR-SIMULATION, synthetic wells |
| **90** | Injectivity gate: ≥400 kPa sandface margin rejects the old 85 kgf/cm² floor (53 kPa margin); 89 kgf/cm² (498 kPa) is the new floor, cost ≈₹112/d FY25 | TIER1 §12.9 | OUR-MODEL, `[ASSUMPTION 300–500 kPa]` |

**Five sentences that keep you out of trouble:**
- "Baghewala's own SOR isn't published, so we benchmark against the literature 3–8 range."
- "That's from our simulation, not a field measurement."
- "That's industry-typical, not Baghewala-specific."
- "That's from our v1 prototype; we audited it ourselves and it's been superseded."
- "The recommended cycle uses more steam and more diesel in absolute terms — it's the
  per-barrel numbers (SOR, CO₂/m³) that improve, and that's the honest way to say it."

---

## A. Killer judge questions — one-line pointers

These are the questions most likely to sink us. The full prepared answers are in
`docs/study/viva_prep.md` Part 1B (K1–K31, extended through 27 Sep). The one-liners below
are the spine.

| Judge asks | One-line answer | Where |
|---|---|---|
| "SOR 0.9–1.3 when literature says 3–8?" | v1 prototype, ~25x optimistic on rate, and we audited it ourselves; the current (rev-12) engine gives gross SOR 4.50 at the reference set-point, inside the 3.0-4.6 re-specified band and a real CalGEM 3.47-8.24 band | viva K1; §1 |
| "471 bbl/d from one well? The field made 655." | v1 pump ceiling; the field averages ~19 bbl/d/well; the calibrated engine peaks at ~15.1 bbl/d at the reference set-point (AOF retuned to sit inside the 15-40 bbl/d field band) | viva K2; §3 |
| "10 SPM? Practice is 3–6." | The whole v1 gain came from 10 SPM; SPM is now restricted to the 3–6 practice band everywhere, including the optimiser search space | viva K3; §2.4 |
| "3-day soak? OIL does 7–13." | v1 modelled only the heat soak costs, never its benefit; under the float-onset rule the calibrated engine's soak sensitivity is small and monotone (margin actually falls slightly beyond ~5 d), so soak is held fixed at the 10-day published-practice value, not optimiser-searched | viva K4; §3 |
| "61-day cycle vs 6–18 months?" | That was the simulated inject-to-cutoff time, not the job interval, so all economics are per cycle (the calibrated reference cycle runs ~178 total days, ending on the float-onset rule) | viva K5 |
| "Oil thinner than water?" | v1 Andrade gave 0.63 cP at 290 °C; Walther now gives 4.13 cP, unchanged by the calibration pass | viva K6; §2.2 |
| "Where does 0.6 come from?" | Our design threshold (drag = 60% of buoyant rod weight), now independently cross-checked by the computed dyno card's separation onset; the rev-12 recommendation deliberately runs right up to it — it produces until FI 0.6 has persisted 3 days, then pulls | viva K7 |
| "Why ML if physics is fast?" | Not speed: contract-first design, batching, and the dashboard's live what-if sliders. As of rev 13, p(float) is dropped as a search constraint entirely — replaced by a hard injectivity gate + the FI ≤ 0.6 policy rule | viva K8; §4.4 |
| "Isn't training on your own physics circular?" | Yes, partly — the ML surrogate is a copy of our current twin (still rev-9-trained, pending retrain), which narrows but doesn't remove the circularity; the physics grid, not the surrogate, is the actual decision engine, and field data is still the real fix | viva K9; §4.1 |
| "Why SOR, not money?" | Agreed, and done: the optimiser's objective is net cash ₹ per cycle-day, counterfactual-free (not gross, not SOR, and, as of rev 13, not incremental margin either); canonical set-points are chosen by minimax regret across the FY25 and $65 decks, so the recommendation is robust to price, not tuned to one deck | viva K10 |
| "Twin or simulator?" | A twin-ready simulator, and the calibration loop itself is now built (`twin/calibrate.py`) — demonstrated on synthetic data, not yet fed real OIL cycles | viva K11 |
| "What did the ChemE member do?" | Owns the physics, the energy/fuel basis, the self-audit, the calibration passes that found and fixed bugs, and sourcing the Boberg-Lantz constant; say it in your own words | viva K12 |
| "Why not XSPOC / Lufkin SAM / SLB / CMG STARS?" | Those are pump-only, facility-only or full-simulator tools; we couple steam and rod risk on one well, alongside them | viva K13 |
| "What if OIL gives you data?" | History-match → retrain → blind test on held-back cycles → advisory pilot | viva K14 |
| "Another well?" | One parameter file per well, calibrated to that well's history | viva K15 |
| "Why CSS, not SAGD / downhole heaters?" | CSS is what OIL runs; OIL has trialled heaters and named SAGD as next | viva K16 |
| "Multi-well steam allocation?" | We built a first version: `ml/schedule.py` optimises each well then schedules a shared generator — 12-well synthetic demo, naive +₹72,320/d, exact scheduling +₹109,799/d serving 10/12 wells; "we're single-well" is no longer accurate | viva K17 |
| "Is the dyno card computed?" | Yes, as of rev 6/9 — a Gibbs (1963) rod wave-equation finite-difference solve (surface + pump card), not an illustrative shape and not an RP-11L chart look-up | viva K18 |
| "BGW-07? The first CSS well was BGW-8." | BGW-07 is a representative label, not well-7 data | viva K19 |
| "Slide 4: what parameter-sweep tests?" (older deck: "Monte-Carlo") | Now literally true: `ml/uq.py` runs a proper 1,500-draw paired Monte Carlo through the true physics on both price decks | viva K20 |
| "Do set-points go to the steam/VFD controllers?" (older slide 3 said so) | No. Advisory to the operator, SCADA hook planned, as the current slide 3 says | viva K21 |
| "Slide 5's −41.3%? You commit to 20–30%?" | −41.3% is labelled prototype v1, self-audited, historical; the current, quotable number is the same-policy net-cash gain — +₹3,332/cycle-day at OIL's confirmed FY25 price, against a baseline that also slows down first | viva K22 |
| "Run the optimiser now." | Go ahead — it's safe on the current branch and reproduces the recommendation (takes time for the 60-call search) | viva K23; §4.4 |
| "Is the v1 optimum still better on the new engine?" | Not the question any more — v1, rev-9 and rev-12 numbers are all historical; the current engine's own recommendation beats a same-policy (VFD-hold) baseline by SOR 3.29→2.83 and +₹3,332/cycle-day, 57% of it from a shorter stroke, at OIL's confirmed FY25 price | viva K24; §3 |
| "Your recommended cycle uses more steam — how is that green?" | Under the same operating policy it uses LESS steam than the baseline (1,000 t vs 1,300 t); SOR and CO₂ per m³ oil both fall as a result — but that's a same-policy comparison, not a law of the physics | viva K25 |
| "Why is soak fixed at 10 days instead of optimised?" | Soak sensitivity is <2%, near-flat — letting the optimiser search it just drifts to a search-box edge with no physical meaning, so it's held at the BGW-8 practice value and disclosed as a model limitation | viva K26 |
| "What did the 3 bugs teach you?" | We found and fixed them ourselves before trusting a single number — missing sensible heat, double-counted wellbore loss, pump vs. oil instead of liquid — that's a debugging strength, not a weakness | viva K27 |
| "Why is your baseline losing money?" | Depends which policy you compare it under — VFD-hold, it's actually cash-positive (+₹12,064/d FY25); it only loses money under the `pull` policy, because pulling the well the instant the rods float throws away real late-cycle oil | viva K28 |
| "Gross vs incremental SOR — which do you quote?" | Gross (4.50 reference, 2.83 recommendation under VFD-hold), because that's the literature/CalGEM convention; ₹ decisions now run on net cash per cycle-day, counterfactual-free, not incremental margin, with canonical set-points chosen by minimax regret over the FY25 and $65 decks | viva K29 |
| "Is the dyno card real?" | Computed from a Gibbs wave equation over a typical rod string, not measured — give us one real card and we calibrate the string properties against it | viva K30 |
| "What if we give you 10 cycles of data?" | We run the calibration loop we've already built and demonstrated: it fits our most uncertain constants and re-recommends against the recalibrated physics | viva K31 |
| "Your gain depends on what the baseline operator does — so what is it?" | Honestly, we don't know OIL's actual float practice, so we report all three: same policy +₹3,332/cycle-day; if the baseline pulls, +₹12,917 (68% of that is just the policy switch); if it does nothing about float, the canonical recommendation still GAINS +₹2,622 (TIER1 §12.6 "mixed" row — an earlier version of this line said "LOSE −₹3,865", but that was a different, non-canonical plan, now retired) — either way, rod damage stays unpriced; never one number without naming the baseline's policy | TIER1 §12.6; PROJECT_LOG §16 |
| "Why VFD-hold and not just pull?" | More oil (SOR 2.83 vs 3.60) and zero days at the floating-index safety limit of 1.0 — but the rods sit AT the 0.6 alarm line for ~55–60 days a cycle, a damage index ~5× the pull policy's, and we price none of that rod wear yet | TIER1 §12.3, §12.6 |
| "Is CSS even profitable net of royalty and cess?" | No, on our numbers — at OIL's own ~35%-levy structure (its FY25 Annual Report basis), every feasible set-point is net-cash-negative even against a shut-in cold well; that's exactly why we're asking OIL for its own net-of-levies price basis | TIER1 §12.10; `docs/research/OIL_DATA_REQUEST.md` |
| "Why does your slug size drop below what BGW-8 used?" | At our assumed mid-range (0.15) diesel discount, the model's own optimal slug is ~750 t vs BGW-8's actual 1,040–1,560 t — a disclosed test failure (xfail), read as revealed preference that OIL's real steam cost is probably cheaper than we assumed | TIER1 §12.2 |
| "Why is 11% less oil a good thing?" | It isn't on its own — it's a trade: same policy, 23% less steam for 11% less oil (353 vs 395 m³), so SOR falls 3.29→2.83. "More oil" is only true against a baseline that pulls instead of slowing — a comparison we don't make | viva K42 |
| "Is the pump actually safer?" | Only vs. a baseline that lets rods float unmanaged (72→3 alarm days). Against a same-policy (VFD-hold) baseline, our own FI and damage index are essentially unchanged (0.62 vs 0.62); damage while held at the 0.6 limit for ~55–60 d/cycle is still unpriced either way | viva K43 |

---

## 7. Each teammate's 10-minute mastery track

Everyone reads the status banner, §1 (the story), §3 (the walkthrough), §6 (number
discipline), §A (killer questions) and the safe-to-say block in `viva_prep.md`. Those
are non-negotiable, because a judge can point at anyone. Then:

### ChemE lead (Gaurav): you own the physics and the honesty
1. `twin/thermal.py`, `twin/ipr.py` and `twin/srp.py`, a full read including every `# ASSUMPTION`. **6 min.**
2. `docs/model-improvement/TIER1_PROGRESS_LOG.md` §1–§3. Be able to explain, without notes, why v1's 10→8 m and 1.0→0.7 retunes were fudges and what replaced them. **2 min.**
3. `docs/research/baghewala_facts.md` §2 and §6, the CONFIRMED vs TYPICAL boundary. **2 min.**

You must be able to: derive the 65.3 kN base rod load on a whiteboard; explain why an
optimum steam volume *can* exist physically (Marx-Langenheim diminishing returns vs a
linear fuel cost) and why v1's optimum was an artefact of the 8 m drainage radius; explain
why 471 bbl/d and 0.63 cP were wrong; and answer "is your model validated?" with the honest
answer, fast and without defensiveness.

**Before the viva, write your own answer to K12 in `viva_prep.md` — don't leave it
templated.** Three lines: (1) your own role in the physics audit — which v1 bug did you
personally catch, and which published model did you pick to replace it, and why; (2) the
emulsion/water-cut modelling — what you decided about Pal–Rhodes, the inversion point, or
water-cut-as-a-state, in your own words; (3) the data request — what's the one thing you'd
personally ask OIL for first, from the chemical-engineering side.

### Backend / API teammate: you own "does it actually run"
1. `api/main.py`: all three endpoints, the `_to_native` numpy coercion, why params reload on every call. **3 min.**
2. `twin/cycle.py`: the loop structure and the break condition. **4 min.**
3. §5 run commands, memorised, including the venv path gotcha and what's now safe to run on the current branch. **3 min.**

You must be able to: start the live API on `physics-v2` directly (no worktree needed any
more — it agrees with the dashboard); explain why `/optimize` returns 503 with a friendly
error instead of a stack trace; explain why 2 tests are xfailed and why that's a disclosed
gap, not a failure; and say what happens if someone passes `cutoff=0` (the well produces to
`MAX_PRODUCE_DAYS = 730`).

### ML teammate — you own §4
1. `ml/train.py` — features, split, the `TransformedTargetRegressor` reasoning, and the log-oil / margin / classifier three-model split. **4 min.**
2. `ml/optimize.py` — `gp_minimize`, the search space, the margin objective and penalty, the `fixed={"soak_days": 10}` mechanism. **4 min.**
3. `ml/models/metrics.json` and this guide's §4.3 table. **2 min.**

You must be able to: explain Bayesian optimisation in 60 seconds using the fog-map
analogy; say why the margin regressor's overall R² (0.833) is lower than its in-envelope R²
(0.998), and that it was a single hold-out with no cross-validation; refuse the "guaranteed
global optimum" bait; explain why the objective changed from SOR to ₹ margin/cycle-day; and
admit the circularity (the surrogate learns our own calibrated twin, not the field) before a
judge raises it.

### Frontend teammate: you own what's on the screen
1. `dashboard/README.md`: the four pages, `MOCK`, `BAKED`, the reconciliation table, the hand-off loop. **5 min.**
2. `docs/guides/DEMO_SCRIPT.md`: the v4 four-page flow, about 2:45 spoken. **3 min.**
3. `MOCK` at `dashboard/src/core.js:9`, `node dashboard/build.js`, the URL params (`?qc=staged`, `?qc=loadstaged`, `?qc=alarm`). **2 min.**

You must be able to: explain that `BAKED` is verbatim **rev-9, physics-verified** twin
output at exactly two set-points (assumed baseline, recommendation) **including
the computed dyno card**, and that everything else (including the stress test's oil/margin
numbers) is the `mockSimulate` heuristic; explain that the assumed baseline's 1,300 t is
BGW-8's own first CSS job, one documented data point, but its 86-in stroke, 5 spm and 1.3
cutoff are our own pump-setting assumptions, not OIL's current practice; drive the
stress test and the stage → confirm → load flow; state where every on-screen number comes
from (`BAKED`, nothing hand-typed); and check before the demo that the status bar reads
116/1 (1 known gap marked xfail).

### Pitch person: you own the framing
1. The safe-to-say block in `viva_prep.md`, word for word, plus §1 here. **3 min.**
2. §6, especially rows 22, 46, 47, 51, 52, 53–55, 60, and the current rows **67–79**. **4 min.**
3. `docs/study/viva_prep.md` Parts 1B and 2, the killer questions (now K1–K31) and the traps. **3 min.**

You must be able to: deliver the 90-second story cold, with the v1 → audit → Tier-1 →
calibration arc as a strength ("we caught our own errors, twice"); **never** state −30% or
−41.3% as a result, and never claim an absolute CO₂ reduction or a soak-day recommendation;
say "zero real cycles, all physics-generated" without flinching; and hand off to the right
teammate the instant a question goes technical. **The handoff is a strength, not a weakness.
It shows the team has depth.**

---

## 8. Self-test — 20 questions

Answers in §9. Don't peek. If you get 16+, you're ready. Several questions are about the
**v1 engine** because that's the history that explains today's design choices, and because
you may be asked to contrast old and new. The dashboard itself now shows the **current
rev-9** engine, not v1 or rev-5 — the answers say where the current engine differs.

**Physics**
1. In one sentence each, what does Marx-Langenheim tell you, and what does it *not* cover in our implementation?
2. Why is reservoir thickness `h` squared in the dimensionless time t_D, and what does a thinner reservoir do to heat loss?
3. In v1, why did `DRAINAGE_RADIUS_M` exist, why did shrinking it from 10 m to 8 m create an interior SOR optimum, and why was that a fudge?
4. Our viscosity fit uses two anchors. Which is real field data and which is an assumption, and what went wrong when v1 put them through Andrade?
5. In v1's Vogel term, Pwf/Pr was fixed at 0.4 all cycle. So what was the *only* thing that made oil rate change during produce, and what does the current engine add?
6. Compute the base (zero-viscosity) rod load from first principles. What are the two components and roughly what are they?
7. Define the floating index in one formula and explain why higher spm makes floating *more* likely at the same viscosity.
8. Why is the well's cold production rate deliberately set below every value in the cutoff range?

**The cycle**
9. Why does injection take 20.27 days when the input said 1,500 tonnes?
10. In the v1 replay, oil rate is flat at 74.96 m³/d for about eleven days. What is limiting it, how would you compute that number, and why is it physically impossible for Baghewala?
11. Why does rod load *rise* over the produce phase while oil rate *falls*? Name the shared cause.
12. At what point exactly does the cycle stop, and is the last row above or below the cutoff?

**ML**
13. Why Latin-hypercube sampling instead of 3,000 uniform random draws?
14. Why is the SOR target log-transformed, and what did it buy?
15. R² = 0.72. State what that does mean and what it does not mean.
16. How is the floating-risk constraint enforced inside `gp_minimize`, and why does a penalty of 1,000 work?
17. Why is grid search the wrong tool here — give the scaling argument with a number.

**Code & field**
18. A judge asks "where in your code does steam actually turn into money?" — name the file, function and line of logic.
19. What is Baghewala's actual measured SOR, and what do you say when asked?
20. How many real CSS cycles are in your training data, and what's the strongest honest defence?

---

## 9. Answers

**1.** Marx-Langenheim (1959) gives how a hot steam zone grows during injection into a
reservoir that leaks heat to the rock above and below, via the thermal-efficiency
function E_h(t_D) = F(t_D)/t_D — early heat is nearly all retained, later heat is
increasingly lost. It gives a heated *area* (a heat balance), not a temperature field. It
does **not** cover what happens after injection stops. In v1 the cooldown was an arbitrary
exponential with τ = 20 days. The current engine uses **Boberg–Lantz**, which cools the zone
by conduction and by heat carried out with produced fluids.

**2.** t_D = 4αt/h². Heat escapes through the top and bottom faces of the pay zone, so
the loss rate scales with surface area per unit volume, which goes as 1/h. Working
through the conduction solution puts h squared in the denominator: **halving the
thickness quadruples t_D at the same real time**, which pushes you much further down the
efficiency curve. A thin reservoir is a leaky pan.

**3.** v1 compared the heated area against an assumed drainage disc, and that ratio
"saturated". Once the heated disc covered the whole drainage disc, extra steam raised
nothing (T pinned at 290 °C) while SOR's numerator kept growing, so SOR curved back up. At
10 m saturation came past the top of the design range, so there was no interior optimum and
a test failed. At 8 m it landed at ~1,750–1,900 t, which "restored" the optimum. **It was a
fudge:** the radius was tuned to make a test pass, not taken from data. Real drainage radii
are ~50–150 m, and the edge SOR at 3,000 t (2.03) was actually *below* the 3–8 literature
band. The constant is deleted. The current engine uses 100 m, and SOR rises monotonically
with steam.

**4.** **11,500 cP at 50 °C is real** (CONFIRMED, OIL internal PPT, midpoint of
10,000–13,000). **50 cP at 150 °C is an assumption** (`ANCHOR_MU_CP`/`ANCHOR_T_C` in
`twin/viscosity.py`), because no high-temperature viscosity measurement for Baghewala
crude was found anywhere. It's the first thing we'd replace with an OIL lab point. v1's
Andrade through these two points extrapolated to **0.63 cP at 290 °C**, thinner than water
at room temperature. The current engine fits the same anchors with Walther (ASTM D341) and
gives **4.13 cP**.

**5.** In v1, **viscosity, through the mobility factor μ_ref/μ.** Reservoir pressure was held
constant and the drawdown fraction fixed, so `vogel_shape` was a constant 0.792 for the
entire cycle, and every bit of movement in oil rate came from the thermal → viscosity chain.
The current engine adds a **live P_res** (charge during injection, bleed during production)
and an **absolute P_wf ≈ 1,144 kPa**, so pressure now moves the rate too. The mobility factor
is replaced by a capped composite-radial uplift.

**6.** Buoyant rod weight + fluid load. Rod: 3.8 kg/m × 1,150 m = 4,370 kg → 42.9 kN in
air; API 15.5 → SG 0.9626 → ρ 963 kg/m³; buoyancy factor 1 − 963/7850 = 0.877 →
**37.6 kN**. Fluid: ρgLA = 963 × 9.81 × 1150 × 2.552×10⁻³ = **27.7 kN**. Total
**≈ 65.3 kN**, constant all cycle; everything above that is viscous drag.

**7.** FI = min(F_v/W_b, 1) where F_v = K_VISC·μ·v_avg·L and v_avg = 2·stroke·spm/60.
Drag is **linear in rod velocity**, and velocity is linear in spm — so doubling spm
doubles the drag at unchanged viscosity, while the buoyant weight in the denominator
doesn't change at all. Concretely, at 8 spm you cross 0.6 at ~2,450 cP; at 12 spm you
cross it at ~1,635 cP.

**8.** Because that *is* CSS's premise, expressed numerically. In v1, 0.7 × 0.792 =
0.55 m³/d cold, against a cutoff range of 1–8 m³/d. In the current engine, 0.60 × 0.792 ≈
0.475 m³/d (≈3 bbl/d) against [0.5, 2.5]. Either way an unstimulated Baghewala well is below
any economic cutoff on day one. If the cold well were economic, there'd be no reason to burn
diesel making steam. (`test_ipr.py::test_cold_rate_is_uneconomically_low` enforces this, so AOF
and the cutoff range must be moved together.)

**9.** Steam volume is an amount, not a duration. Injection time = steam_t /
`injection_rate_tpd` = 1,500 / **74** = 20.27 days. The 74 t/d comes from OIL's own
reported BGW-8 first-cycle rate of ~3,100 kg/hr — CONFIRMED, not a guess. (And note it
lands neatly inside the reported 14–21 day injection window.)

**10.** The **pump's mechanical displacement capacity**, not the reservoir.
`A_plunger × stroke × (spm × 1440) × VOLUMETRIC_EFFICIENCY` (now `FILLAGE_MAX`) =
2.552×10⁻³ × 3.0 × 11,520 × 0.85 = **74.96 m³/d**. `srp.pump_state` takes `min(IPR rate, pump
capacity)`, and while v1's zone was hot its IPR rate was far higher, so the pump was the
bottleneck. **Why it's impossible:** 74.96 m³/d = **471 bbl/d from one well**, while the whole
field made 655 bbl/d (Jul 2025), about 19 bbl/d per well. In the current engine the well is
reservoir-limited and peaks at 17.8 bbl/d, so no plateau exists.

**11.** **Cooling, therefore rising viscosity.** Thicker oil means the inflow term (v1:
mobility μ_ref/μ; now: composite uplift) falls (rate down) *and* the rod drag term K_VISC·μ·v·L rises (load up) — same μ
in both. That single shared driver is the physical coupling the whole project is about,
and it's why you cannot optimise the steam schedule and the pump independently.

**12.** The produce loop appends a row, then breaks the first time
`prod_rate_m3d < cutoff_m3d`. So the final row is always recorded and is always **below**
cutoff. In the v1 run that's day 61.27 at 2.89 m³/d against a 3.0 cutoff. That's exactly what
`tests/test_cycle.py::test_cycle_ends_at_or_below_cutoff` asserts.

**13.** Uniform random draws in 4-D clump and leave gaps; you can spend 3,000 samples and
still have whole regions of steam_t × soak space unexplored. LHS stratifies **every
dimension independently** — each of the 3,000 slices of each input range gets exactly one
sample. Same compute, far better coverage, and a much more trustworthy surrogate at the
edges of the design space.

**14.** SOR is a strictly-positive ratio with a heavy right tail — a few
low-steam/high-cutoff corners produce almost no oil, giving huge SOR values that dominate
squared-error training. Fitting log(SOR) is the standard remedy. It raised held-out **R²
from 0.69 to 0.7246**, and because `TransformedTargetRegressor.predict()` inverts the
transform automatically, `ml/optimize.py` required **zero** changes.

**15.** It means the surrogate explains about 72% of the variance in **simulated** SOR
across the design space, on a single held-out 600-row split of physics-generated data (no
cross-validation). Inside the 1,200–2,400 t envelope it's 0.992. It does
**not** mean 72% accuracy, and it does **not** say anything about real-world accuracy — it
measures how well XGBoost learned our own physics engine, not how well our physics engine
matches Baghewala. Those are two different claims.

**16.** As an additive penalty inside the objective:
`if float_prob >= 0.3: penalty = 1000 × (float_prob − 0.3)`, returned as
`sor_pred + penalty`. Good SOR values are around 1, so even a tiny violation adds tens or
hundreds — the candidate becomes hopeless and the GP learns to avoid that region. It's a
soft constraint that keeps the objective continuous (which Gaussian Processes prefer)
while behaving like a hard one. Result: floating probability 0.0011, far below the limit.

**17.** Grid cost scales as levels^dimensions. Four knobs at just 10 levels each is
**10,000 full evaluations** — and 10 levels of steam volume is a crude 250 t resolution.
Bayesian optimisation reached its answer in **60** evaluations (15 random initial + 45
GP-guided) because the GP lets it *learn where to look*, and unlike a grid it doesn't waste
identical effort on regions it has already proven hopeless. (Honest footnote: our twin is
0.55 ms per cycle, so today even a 10,000-point grid on the twin would take seconds. The
method is chosen for when the physics gets expensive.)

**18.** `twin/ipr.py`, function `oil_rate_m3d`. In **v1** it was the line
`mobility_factor = mu_ref_cP / mu_cP`, the single division where "the reservoir got hot"
became "more barrels": 1.0 at 50 °C, ~5,600 at 244 °C (μ 2.04 cP). That factor was far too
large (effective uplift ~135× vs the field's 5–6×), and it's the root of v1's rate error. In
the **current** engine the same job is done by `composite_uplift()` (hot inner zone, cold
outer zone, capped at 10; ~4× in practice). Everything upstream exists to move that number,
and everything downstream (SOR, the optimiser, ₹ and CO₂) is a consequence of it.

**19.** **It is not published anywhere we could find** — and that is the answer you give.
"Baghewala's own SOR isn't in any public source, so we deliberately don't quote one. We
benchmark against the industry literature range of 3–8 t/m³, average ~6, with under 3
considered thermally efficient." Never state a specific number as Baghewala's current
SOR; it's the easiest way to lose the room, and it's on the cheat table as a red flag.

**20.** **Zero.** All 3,000 are physics-generated (by the v1 engine). The defence: they're
not fabricated. Each row is the output of published models (Marx-Langenheim, a viscosity
law, Vogel, API RP 11L-style rod mechanics) solved at Latin-hypercube-sampled operating
points. Then close it yourself, before the judge does: *"That makes the model physically
plausible, not field-validated, which are two different claims. Our own audit already found
the first engine optimistic, which is why we rebuilt the physics. Oil India's historical
cycles and dyno cards are exactly what we'd calibrate against next, and `field_params.json`
is built so that's recalibration, not a rewrite."* (Don't promise "an hour"; it hasn't been
timed.)

---

## Footnotes — build-session notes

History that explains odd-looking choices in the code. Useful if a judge reads the source;
not needed on stage.

1. **Why `andrade_A/B` (and now `walther_A/B`) are `null` in `field_params.json`.** The v1
   research pass computed A = 1.164e-6 and B = 7436.6 and offered to hard-code them.
   Integration kept them null on purpose: `viscosity.py` re-derives the constants at runtime
   from the two anchors at full float precision. Writing the *rounded* values into the JSON
   made μ(50 °C) come back as 11,489.6 instead of exactly 11,500 and broke
   `test_reference_point_recovered`. Tier-1 keeps the same rule for Walther.
2. **The v1 retunes (`params/CHANGELOG.md`).** When the real field parameters landed
   (μ_ref 11,500 cP instead of 2,000; steam at 290 °C instead of 250), two constants were
   retuned to keep tests green: `DRAINAGE_RADIUS_M` 10 → 8 (to restore an SOR optimum) and
   `AOF_REF_M3D` 1.0 → 0.7 (so cycles weren't pump-limited everywhere). Both were tuning to
   tests, not to data. The audit caught this, and Tier-1 removed the first and reset the second
   to 0.60 pending recalibration.
3. **The CHANGELOG was written after the fact.** The Tier-1 parameter changes (new
   `wellbore`, `economics` blocks; `latent_heat_Jkg` 1.3e6 → 1.40e6; `drainage_radius_m`;
   `mu_floor_cP`; cutoff range [0.5, 2.5]) were committed in **8c6643b**, seven minutes before
   the code that reads them (a82cfa7). `params/CHANGELOG.md` gained a "rev 4" entry for them on
   26 Sep. The same fact is why a worktree of 8c6643b does **not** reproduce v1 numbers; use
   6bb604d.
4. **`K_VISC = 10`** was checked, not retuned, when rod length went 500 → 1,150 m. Across
   μ 1–11,500 cP × spm 4–12 the floating index still spans 0.0001 → 1.0 with a smooth
   transition around 300–3,000 cP.

---

*Sources: `docs/SPEC.md`, `twin/*.py`, `ml/train.py`, `ml/optimize.py`,
`params/field_params.json`, `params/CHANGELOG.md`, `docs/reviews/integration_report.md`,
`docs/research/baghewala_facts.md`, `docs/model-improvement/*.md`, `docs/guides/GLOSSARY.md`,
`docs/guides/DEMO_SCRIPT.md`, `dashboard/README.md`, `docs/study/viva_prep.md`. v1 simulation
figures were verified against the v1 twin on 2026-09-13 (commit 351a89b era). Tier-1 figures
(commit a82cfa7, then uncalibrated) were re-run on 2026-09-26 morning, then calibrated as
rev 5 that evening (57 passed, 2 xfailed — since superseded). **Current figures are physics
rev 9 (physics v3 + economics v2)** (`params/CHANGELOG.md` rev 6–9;
`docs/model-improvement/TIER1_PROGRESS_LOG.md` §6–§9) — 116 tests passed, 1 xfailed. Revised
2026-09-27 after physics v3, the calibration loop, computed dynamometer cards, and
incremental economics landed.*
