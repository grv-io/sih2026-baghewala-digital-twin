# Viva Prep: Baghewala Digital Twin (SIH 2026, PS SIH26120)

Q&A material for the internal PPT round and finale judging, in simple English so any
team member (ChemE or software) can answer. Where a number is industry-typical rather
than Baghewala-specific it is marked **(verify)** or **TYPICAL**. Say the range honestly;
never present it as a confirmed fact.

---

## STATUS: 27 Sep 2026 — physics wave 5, operating policy as a control (rev 13)

- **Five engines of history, one current.** The **v1 engine** (commit 351a89b) was
  **~25× optimistic on oil rate**. Rev 5 (13–26 Sep) fixed three internal bugs but its ₹
  margin was **gross** (crediting CSS with oil the well would make anyway). Rev 9 (26–27
  Sep, physics v3 + economics v2) sourced the Boberg–Lantz δ and moved ₹ to an incremental
  basis — **but modelled water cut as a constant 85% and ended every cycle on a fixed rate
  cutoff**, so 83–96% of its headline gain turned out to be the assumed baseline cutoff
  moving, not real physics. **All of v1, rev 5 and rev 9's numbers are now historical.**
- **27 Sep: two rounds of independent adversarial review** (AI-assisted, persona-based:
  production engineer + data scientist; judge panel) — not a named human expert —
  scored rev 9 **61/100 and 52/100** and
  found real, reproducible gaps: a `dt`-summation bug, hardcoded constants invisible to
  uncertainty quantification, a steam state that wasn't physically self-consistent, and the
  cutoff-artefact finding above. We responded in three physics waves, all on branch
  `harden`, now merged to `main`:
  - **Rev 10 (hardening):** fixed the `dt` bug; moved skin, pressure-boost and viscosity
    constants into params + UQ; made the cold rate viscosity-dependent; added an emulsion
    viscosity for rod drag and a documented steam-state consistency check.
  - **Rev 11 (water cut as a state):** the produced stream starts water-continuous (~0.87,
    condensate flowback) and falls toward a formation floor (~0.45) late in the cycle. Once
    it crosses a ~0.70 inversion point it turns oil-continuous, and the rods float at
    practice speed — **a late-cycle phenomenon**, restoring a rod-float thesis rev 10 had
    found didn't bind at a constant water cut. Also added injection-pressure (IAPWS-IF97
    steam state) and stroke-length levers.
  - **Rev 12 (physics wave 4):** replaced the emulsion law with published Pal–Rhodes
    (capped at 10×), and — the pivotal change — introduced `produce_end_rule = "either"`:
    the cycle ends on the rate cutoff **or** 3 consecutive days of a floating-index alarm,
    whichever comes first — what an operator actually does, rather than running floating
    rods for months or writing a fragile high fixed cutoff. `AOF_REF_M3D` was retuned
    0.46→0.56 to meet the field's 15–40 bbl/d peak band.
  See `docs/model-improvement/TIER1_PROGRESS_LOG.md` §9–§11.
- **27 Sep, again: a technical re-score (58/100)** found rev 12's own headline gain
  (+₹9,574/cycle-day) was itself an artefact — it came from the **pull rule** ending
  the baseline on the float alarm while it still made real oil, not from the
  recommendation's own set-points. Response: **wave 5 (rev 13)**, on branch `wave5`
  — the operator's **response to rod float is now itself a control**,
  `css.float_policy` ∈ `pull` (rev-12 style: physical keep-up SPM limit, pulled
  after 3 alarm days) / **`vfd_hold`** (recommended — a VFD slows the pump to hold
  the floating index at 0.6, floor 2 spm, pull only after 3 alarm days AT the
  floor) / `vfd_then_pull` / `none` (ride to the rate cutoff, no float action). The
  SAME policy now applies to the baseline, the recommendation, **and the cold,
  unstimulated counterfactual well** — which is **shut in** under every float
  policy except `none` (not "idealised pumpable" as rev 12 had it). Wave 5 also
  smooths the sharp water-cut-inversion cliff, adds a hard injectivity gate (steam
  must clear ≥400 kPa over reservoir pressure — this rejects the old 85 kgf/cm²
  floor, selects 89), and adds a net-of-royalty-and-cess price deck. **No
  calibration knob moved** — only the diesel discount base (0.30→0.15, an
  economics input). See `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12.
- **There is no single "verified improvement" number — the gain depends on what the
  baseline operator does, and we say all three.** Canonical recommendation: **1,000 t
  / 10 d soak / 89 kgf/cm² / 64-in stroke / start 4.5 spm / cutoff 0.60 m³/d backstop
  / VFD-hold**. Against the baseline (1,300 t / 10 d / 91 kgf/cm² / 86-in / 5 spm),
  **under the same policy (VFD-hold, fair comparison)**: SOR 3.29 → 2.83, net cash
  **+₹3,332/cycle-day (FY25) / +₹4,319 ($65) / +₹5,382 (net of levies)** — decomposes
  stroke 57% / cutoff 30% / steam 11%. **If the baseline instead pulls at the first
  alarm** (rev-12-style operation): SOR 4.35 → 2.83, **+₹12,917 / +14,694 / +16,606**
  — but **68% of that is the policy switch alone**, not the set-point (this is what
  the retired "+₹9,574" number actually was). **If the baseline does nothing about
  float** (rods run floating to the rate cutoff): our canonical (VFD-hold)
  recommendation still *gains* **+₹2,622 / +3,484 / +4,413** against it (TIER1
  §12.6, "mixed" row) — **correcting an earlier misattribution**: a different,
  non-canonical plan optimised *for* a do-nothing world (1,000 t / 89 kgf/cm² /
  cutoff **1.45** / 64-in / **3** spm, policy `none`), compared against a
  same-policy do-nothing baseline, is what actually loses **−₹3,865 / −2,513 /
  −1,057** — that number is not our recommendation's own result and should never be
  quoted as such. What the corrected comparison does **not** change: rod-string
  damage remains **entirely unpriced** — VFD-hold still buys its oil by holding the
  floating index at the 0.6 limit for ~55–60 days a cycle (graded damage index
  ~5× the `pull` policy's, **in-model, with the controller given perfect knowledge
  of the true drag law**), and in the uncertainty runs, where drag error is
  sampled, the recommendation is actually **more** float-exposed than the baseline
  (median alarm days 6 vs 0). **Never state a single gain number without naming
  which of these three the baseline is doing.**
- **Tests: 263 passed, 2 xfailed.** Soak (no interior optimum, unchanged) and a new
  one: the steam optimum at the mid-range (0.15) diesel discount sits below the
  BGW-8 slug range (~750 t vs 1,040–1,560 t) — read as revealed preference that
  OIL's real steam is probably cheaper than assumed. The rev-12 cold-well xfail is
  now **un-xfailed**: the counterfactual obeys the policy (shut in), so it's no
  longer an open physics question, just an economic reading choice. Not 236, not
  197, not 24/24.
- **ML's honest role, sharpened.** The exhaustive 6-lever × policy physics grid
  (`ml/recommend_physics.py`'s `best_settings_physics_5d`, 40,194 feasible
  points/policy, ~172 s, every point true-physics-verified) is the **decision
  engine**; the XGBoost surrogate (`ml/optimize.py`) lands **~24% below** it
  (+₹11,635/d vs +₹15,396/d FY25) and is a cross-check only. The float classifier
  (`float_premature_pull`, 41% positive, AUC 0.999) is now informational only — it
  is **not** a search constraint (the injectivity gate, a real physical limit,
  replaced the old soft float-risk penalty).
- **Field scheduler, rev 13:** every well run VFD-hold — naive fixed-job policy is
  now **+₹72,320/d** field-wide (rev 12, still pulling on float, was a field-wide
  **loss** of −₹13.3k/d — the policy switch alone is the difference); exact
  per-well-optimised scheduling reaches +₹109,799/d, serving 10 of 12 wells.
- **Net of royalty + OID cess (~₹3,600/bbl, OIL's own ~35%-levy FY25 basis), every
  feasible grid point is negative** — the recommendation's edge over the baseline
  still grows on this deck (it saves steam), but "is CSS even profitable" is
  answered by OIL's own price/levy deck, not by our assumptions.
- Never quote a single gain number without the "against a baseline that does X
  about float" caveat — OIL's real float-response practice (slow or pull?) is now
  the single biggest lever in the whole model, bigger than any set-point.

### The safe-to-say block (learn this verbatim)

> "Our operating rule: slow the pump with a VFD as it nears the float limit, and
> only pull if it stays there — the same rule on both sides of every comparison.
> Under that rule, steam per cubic metre of oil falls from 3.29 to 2.83, a 14%
> cut, and we beat our own assumed baseline in 84–96% of simulated runs. The
> rupee gain is real but modest and uncertain: roughly ₹0 to ₹5,000 a cycle-day,
> because it's set by two numbers we don't have — OIL's actual VFD minimum speed
> and their real pull/produce cutoff — both now on our data request. Everything
> here is physics-simulated, not field-validated; 263 of 265 tests pass."

**Full version** (five rounds of audit, all three baseline-policy numbers, and
everything else — use this for follow-ups, not as the opening line):

> "We've been through five rounds of self- and external audit. Our first engine was about 25 times optimistic on rate; a later pass put our rupee objective on an incremental basis; two rounds of independent adversarial review on 27 September (AI-assisted, persona-based — not a named human expert) scored us 61 and 52 out of 100 and drove three physics waves; and a follow-up technical re-score found that even THAT headline gain — plus 9,574 rupees a cycle-day — was mostly an artefact: it came from the baseline operator pulling the well the moment its rods floated, while our recommendation didn't. So in this latest wave we made the operator's own response to rod float — pull the well, or slow it down with a VFD and hold it there — into a control, and we apply the SAME choice to the baseline, to our recommendation, and to the cold, unstimulated counterfactual well, which is now shut in under every float policy rather than treated as if it could still be pumped. That's the honest way to ask 'how much do we actually gain': it depends entirely on what the baseline operator does, so we report all three answers. If the baseline slows down the same way we recommend — the fair comparison — our recommendation gains about 3,300 rupees a cycle-day at OIL's own confirmed FY25 price, 4,300 at the older 65-dollar floor, and 5,400 net of royalty and cess. If the baseline instead pulls the well at the first alarm, the gain looks much bigger — about 12,900 rupees — but two-thirds of that number is just the policy switch, not our set-points; that's exactly what the old headline number actually was. And even if the baseline does nothing about float at all, our recommendation still gains a little — about 2,600 rupees a cycle-day — though a different, non-canonical plan built specifically for a do-nothing world actually loses against a do-nothing baseline, which is a separate comparison we don't want confused with our own recommendation's result. What none of this changes: we still put no rupee cost on rod damage, and running rods at the float limit for 55 to 60 days a cycle is not free in the field even though it's free in the model. We also smoothed a numerically sharp water-cut-inversion cliff, added a hard feasibility gate on steam injectivity — which throws out our own earlier recommended injection pressure — and added a fourth price deck, net of royalty and cess, on which every feasible set-point we tested is still negative even against a shut-in cold well. Two hundred sixty-three of two hundred sixty-five tests pass, with two gaps disclosed as strict test failures, not hidden: no interior soak optimum, and our best steam-slug size now sits below what OIL's own first CSS well actually used, at our assumed mid-range diesel price. All training data is still physics-generated — plausible, not field-validated. Our two biggest asks of Oil India are now: what do your operators actually do when rods float — do they slow down or pull? — and what does a rod-failure workover actually cost, because that's the one real cost our model doesn't have a number for."

### Never say these as results

| Never say | Why |
|---|---|
| **−30%** or **−41.3%** as our result | v1 prototype numbers, audited and superseded. Only say them labelled "v1 prototype, since audited". |
| **Rev-5's "+188% margin"**, or **rev-9's "+4,423/cycle-day"** / "cutoff drives 83–96% of the gain" | Both superseded. Rev 9's headline gain turned out to be mostly the assumed baseline cutoff moving; rev 12's gain is 62% SPM + 32% stroke, 0% cutoff. |
| **₹0.61 crore/yr** | Wrong twice: a ₹1,300/t *gas* price on a diesel field, and an impossible 6.8 cycles/well/yr. |
| **6.8 cycles a year**, anything "per year" from 365/cycle-days | CSS cycles are 6–18 months apart. Economics are **per cycle** only. |
| **₹1,300/t** steam | Real basis: 71 kg HSD/t → ₹7,111/t at the mid-range (0.15) discount (base case) / ₹5,856/t at 0.30 bulk / ₹8,366/t retail, 224 kg CO₂/t. |
| **24/24**, **116/127**, **57/57**, **60**, or **236 passed** tests | 263 passed, 2 xfailed today. |
| **471 bbl/d** (74.96 m³/d) as a well rate | v1 pump ceiling. Field average is ~19 bbl/d per well; the *whole field* made 655–1,202 bbl/d. |
| **μ = 0.63 cP** at steam temperature | v1 Andrade artefact, thinner than room-temperature water. The current engine gives 4.13 cP. |
| **"Our engine was 25% optimistic"** | It's **25×**, not 25% — the first engine's peak rate was about 25 times the field-implied average. |
| **"Optimal soak is N days"**, any soak-day recommendation | Soak sensitivity is <2% (near-flat). It's held fixed at 10 d field practice, never twin-derived. |
| **Any Baghewala SOR** | Not published anywhere. Benchmark against literature 3–8 (and the real CalGEM 3.47–8.24 band). |
| **"We commit to 20–30%"** | We don't. >20% is a literature benchmark for this class of method, not our promise. |
| **Cross-validation / k-fold / RMSE / "random restarts"** | We did none of these. Single hold-out; 15 random initial points + 45 GP-guided calls. |
| **Andrade 1934** (an older deck said this; the current deck is fixed) | Andrade's paper is **1930** (Nature 125, 309–310). |
| **Any absolute CO₂ *reduction* per cycle** | Say it via SOR and CO₂ **per m³ oil**, not the absolute totals. |
| **"Baghewala's own SOR is [some number]"** or presenting the recommendation as OIL's practice | The baseline is BGW-8's own first CSS job — one documented data point, not current OIL practice, and the gain now rides on OIL's real SPM/stroke, both unknown. |
| **Gross margin quoted as profit** | ₹ decisions are incremental, now against an idealised pumpable cold well; gross margin is kept only for continuity/reporting. |
| **"The BL delta factor is unverified"** | It's sourced: exactly the ½ inside Boberg and Lantz's own 1966 δ, forced by energy conservation. |
| **A single gain number without the baseline SPM/stroke caveat** | Say: "against our assumed 5-spm/86-in baseline" every time — OIL's real SPM/stroke are unknown, and the gain moves with them. |
| **The measured-card classifier as "field-validated"** | It has never seen a real Baghewala card — 94.8% hold-out on synthetic cards, a first read, not a validated diagnosis. |
| **"reproduces Baghewala's benchmarks"** | Say: "calibrated to the published band; not field-validated". We match literature and CalGEM bands, not Baghewala's own cycle records, which don't exist publicly. |
| **"verified improvement"** | Say: "physics-consistent improvement on synthetic data". Real validation waits for OIL's cycles. |
| **"OIL's own practice baseline"** | Say: "baseline derived from the one published BGW-8 job; OIL's actual cutoff/SPM/stroke/pull criteria unknown". It's a reference case, not their current operating target. |
| **"recovers thickness within 0.9%"** | Say: "thickness recovered within about 11% on the current committed seed — weakly identified, trades off against AOF". |
| **"+₹9,574/cycle-day"** as our gain | Superseded (rev 13): that number was the **pull-rule policy switch**, not our recommendation's own gain. Say "+₹12,917, but 68% of that is the baseline pulling on the alarm, not our set-points" — and always give the fair, same-policy number (+₹3,332) alongside it. |
| **"62% SPM, 32% stroke"** decomposition | Superseded. Under the fair, same-policy (VFD-hold) comparison it's **stroke 57%, cutoff 30%, steam 11%** (FY25 deck) — a different decomposition of a different, smaller, honestly-labelled gain. |
| **"verified improvement"** | Nothing here is field-verified. Say "physics-simulated improvement, same-policy comparison" — and name the baseline's policy. |
| **Any single gain number without naming the baseline's float policy** (pull / VFD-hold / does nothing) | The policy alone swings the gain from +₹2,622 to +₹12,917/cycle-day — bigger than any set-point in the model. Always say which one you mean. |

---

## PART 1: 25 TOUGH QUESTIONS

### A. Domain / Chemical Engineering (10)

**1. Why does viscosity rise so steeply as temperature falls? Explain the Andrade/activation-energy intuition.**
Heavy crude is a tangle of long hydrocarbon chains and asphaltenes that resist sliding past each other. Flow is thermally activated, like a reaction that has to hop an energy barrier. At low T few molecules have the energy to make that jump, so resistance climbs roughly exponentially, and a given temperature rise buys a much bigger drop at the cold end than the hot end. Baghewala's Jodhpur Sandstone crude is **8,000–15,000 cP at 50 °C** [CONFIRMED, SPE-23APOG-535203 / OIL internal data], roughly **90–100× more viscous than a "typical" 18° API crude**.
**How we fit it (be precise):** it is a **two-point fit**. One anchor is real: **11,500 cP at 50 °C** (midpoint of OIL's 10,000–13,000). The other is an **assumed** high-temperature anchor, **50 cP at 150 °C**, because no Baghewala lab point exists. In v1 we put those two points through Andrade (μ = A·exp(B/T), Andrade **1930**; A = 1.164×10⁻⁶ cP, B = 7,436.6 K). Extrapolated to steam temperature it gave **0.63 cP at 290 °C**, thinner than room-temperature water and implausible for a 15° API crude. The current engine fits the same two anchors with **Walther / ASTM D341**, the petroleum-standard form, which gives **7.2 cP at 244 °C and 4.13 cP at 290 °C**, with a 1 cP floor. The first thing we'd replace is the assumed anchor, with an OIL lab measurement.

**2. What physically happens during the "soak" phase of CSS, and what soak does your model recommend?**
The well is shut in so the steam condenses and gives up its latent heat to the rock and oil near the wellbore, and that heat conducts outward instead of flowing straight back up the well. Too short a soak wastes heat on hot backflow; too long a soak lets heat leak to the cap and base rock. So there is a trade-off, and OIL's BGW-8 practice is soak ≈ 50–60% of injection, **about 7–13 days**.
**Honest part:** our **v1** engine modelled only the *cost* of soak (a 20-day exponential cooldown), not its benefit. So the shortest soak always won and the v1 optimiser sat on the 3-day lower bound (the optimiser page flags it "at lower bound"). That is a model artefact, not a recommendation. In the current engine (Boberg–Lantz cooldown) SOR is **almost flat in soak**. Soak optimisation needs field data to resolve, so we recommend nothing on it yet.

**3. Why is there an optimum steam volume rather than "more is always better"?**
Physically: every extra tonne heats a bigger zone, but conduction losses to cap and base rock grow with the zone's area (Marx-Langenheim's efficiency falls), so each tonne buys less new hot rock while its fuel cost stays roughly constant. Diminishing returns meet a linear cost.
**Honest part:** in our **v1** engine the SOR optimum existed *only* because we shrank an assumed **8 m drainage radius** until the heated zone "saturated" inside the design range. That was a fudge; the constant has since been deleted, and real drainage radii are about 50–150 m (we now use 100 m). On the current engine **SOR simply rises with steam volume**, which is actually what the literature expects. SOR alone is the wrong objective for finding an optimum. The honest objective is **incremental ₹ margin per cycle-day** (oil revenue over the cold, unstimulated well, minus diesel, opex and pumping power, divided by cycle length) — and that's the actual optimiser objective as of rev 8/9: it has an interior optimum near 1,000–2,000 t (flat across that range), unlike SOR.

**4. What is a dynamometer card, and how does rod floating change its shape?**
A dyno card is polished-rod load plotted against rod position over one stroke, the diagnostic fingerprint of a rod pump. A healthy card is a roughly parallelogram loop. With heavy, cold crude, viscous drag on the downstroke means **the rod string cannot fall as fast as the pumping unit drives it**. The rods go slack, can go into compression and buckle, and the carrier bar can separate from the polished-rod clamp. On the card the downstroke load collapses toward or below zero, often followed by a sharp spike, and repeated floating is a leading cause of rod and tubing wear and parted rods. (The rods are **not** "falling faster than the fluid".) **As of rev 6/9, our dashboard's card is computed** — `twin/dyno.py` solves a Gibbs (1963) rod wave-equation finite-difference model (surface + pump card), not an illustrative sketch and not an RP-11L chart look-up, and its computed carrier-bar-separation onset independently matches our ≈0.6 floating-index alarm line.

**5. Why does heavy crude have high asphaltene-related issues?**
Heavy crude (Baghewala: 17–19° API per the PS, 14–17° per field literature) carries a larger fraction of big, polar, aromatic asphaltene and resin molecules. They cause much of the viscosity, and they can precipitate when pressure, temperature or composition changes (for example across the near-wellbore pressure drop), plugging pores, tubing and pump valves, and stabilising water-in-oil emulsions. Heating helps with viscosity and often keeps asphaltenes in solution, but CSS is not a guaranteed fix. We don't model asphaltenes.

**6. What limits CSS to shallow-to-moderate depths?**
Steam loses heat on the way down the wellbore, so deeper wells deliver lower-quality steam at the sandface. The industry rule of thumb is that CSS gets markedly less efficient beyond about 1,000–1,500 m **(verify: rule of thumb, not a Baghewala study)**. Baghewala sits at **~1,100–1,150 m** [CONFIRMED], right at that edge, which is why OIL uses **vacuum-insulated tubing (VIT)** and has trialled **electric downhole heaters**. **Wellbore heat loss is now modelled** in the current engine (VIT loss ≈10% per 1,000 m; sandface quality taken as 0.55 × wellhead quality). v1 did not model it, which is one reason v1 was optimistic.

**7. What is Steam-Oil Ratio (SOR), and why is it the key metric for CSS?**
SOR = tonnes of steam injected per m³ of oil produced over a cycle. Steam is the largest recurring cost of a thermal project (diesel here), so SOR ties heating efficiency, viscosity reduction and pump performance into one economic yardstick. Literature puts CSS at **3–8 over a well's life, average ~6, with below 3 considered efficient** [TYPICAL]; a real 2021 California CSS field-SOR band from 9,692 real cycles is **3.47–8.24**, which we also sit inside (our own reference-SOR band is re-specified 3.0-4.6). **Baghewala's own SOR is not published**, so we never state one. Caveat to volunteer: minimising SOR alone ignores oil price, time and fixed costs — and credits CSS with oil an idealised pumpable cold well would make anyway — which is why the ₹ objective is **incremental margin per cycle-day** (Q3), while SOR stays the gross, literature-comparable headline.

**8. Why does Baghewala need thermal recovery at all? Why not pump it cold?**
The PS describes 17–19° API crude at 46–48 °C; SPE-23APOG and OIL data put the producing crude at **14–17° API, ~50 °C, 8,000–15,000 cP**. At that viscosity cold inflow is uneconomic. Our current engine's cold well makes ≈0.475 m³/d, about 3 bbl/d. Heat cuts viscosity by orders of magnitude, and the field proved it: the first CSS at **BGW-8 (Dec 2018)** gave a **5–6× uplift**.

**9. What does "steam quality" mean, and why does it matter here?**
Quality is the mass fraction of the steam that is vapour. 65% quality means 65% vapour, 35% hot water. The vapour carries the latent heat, so quality measures delivered heat. BGW-8's **wellhead** quality was **60–70%** [OIL internal PPT]; we use 0.65. At the **sandface** it is lower after wellbore loss, and the current engine uses 0.55 × wellhead ≈ 0.36.

**10. Walk through the energy balance of one CSS cycle.**
Physically, energy in = latent + sensible heat of the injected steam. Our engine originally credited **only the latent part**, which we found in our own 26 Sep calibration pass was **wrong, not conservative** — it undercounted the heat actually delivered by about 3.6×. The fix adds the sensible-heat term (`C_w·ΔT`) alongside latent heat (L = 1.40 MJ/kg), both at sandface quality after wellbore loss (which is also no longer double-counted — a second bug we found and fixed the same pass). That heat goes to (a) heating reservoir rock and fluids near the well (useful), (b) conduction into cap and base rock (Marx-Langenheim during injection, Boberg–Lantz afterwards), and (c) wellbore loss on the way down. During production, produced fluids carry heat out and the zone cools, tracked through the Boberg–Lantz energy-removed term. SOR is the economic shadow of this balance: the more of (a), the lower the SOR.

---

### B. ML / Software (8)

**11. Why is physics-based synthetic data legitimate for a prototype, not just "fake data"?**
Each row is the output of published models (Marx-Langenheim, a viscosity law, Vogel IPR, rod mechanics) solved at 3,000 Latin-hypercube design points, so it obeys energy conservation and the right trends. That is standard for a prototype when field data is confidential. **But it is only as good as the engine that made it**, and our v1 engine was audited as ~25× optimistic on rate, so the current v1 dataset is a pipeline artefact, not a model of Baghewala. The line to say: *"physically plausible is not field-validated. Those are two different claims."*

**12. How does the model recalibrate when real field data becomes available?**
Two levels, and level (a) is now an actual built loop, not just a plan. (a) **Calibrate the physics** (history matching): `twin/calibrate.py` fits the uncertain constants (`water_cut`, `thickness_m`, `AOF_REF_M3D` — `BL_DELTA_FACTOR` is sourced now, not fitted) so the twin reproduces observed cycle rates and days, then `ml/recommend_physics.py` re-recommends directly against the recalibrated physics. On a synthetic demo it recovers those constants within 0.2–1.6%. Parameters live in `params/field_params.json`. (b) **Regenerate and retrain**: re-run the design of experiments on the recalibrated twin, retrain the surrogates, and optionally add real cycles to the training set. The **first ask of OIL is cycle records and dyno cards**. How long the full retrain takes is unverified, so don't promise "an hour" — but the calibration loop itself runs on a CSV in well under a second.

**13. Why XGBoost instead of a deep learning model?**
The data is small (3,000 rows), tabular and numeric, which is where gradient-boosted trees usually beat neural nets. XGBoost trains in seconds, needs little tuning, gives feature importances, and handles a future mix of synthetic and a few real cycles better than a data-hungry deep model.

**14. Explain Bayesian optimisation in one paragraph.**
Fit a Gaussian Process to the points evaluated so far. It gives a predicted value **and** an uncertainty everywhere. An acquisition function picks the next point by balancing exploitation (good predictions) against exploration (high uncertainty). Evaluate there, refit, repeat. Ours: `skopt.gp_minimize`, **60 calls = 15 random initial points + 45 GP-guided**, `random_state=42`. The objective it evaluates is the **XGBoost surrogates** (predicted SOR plus a penalty when predicted floating probability ≥ 0.3), not the physics twin directly.

**15. How do you validate the model without real field data?**
Honestly, only internal consistency, plus one real-data comparison. (1) **Physics property + benchmark tests**: 265 pytest tests for monotonicity, bounds, limiting cases and published benchmarks; **263 pass, 2 are xfailed** — documented, known gaps (no interior soak optimum; the steam optimum at the mid-range diesel price sits below the BGW-8 slug range), not hidden failures. (2) **ML hold-out**: a **single 80/20 split** of synthetic data on rev-13 physics (7 features incl. the new float-policy dimension) — oil regressor R² 0.995, float classifier AUC 0.999, no cross-validation. (3) **The physics grid, not the surrogate, is the decision engine**: an exhaustive 40,194-feasible-point-per-policy grid, every point true-physics-verified. (4) **Real-data band check**: our gross SOR sits inside a real 2021 California CSS field-SOR band (3.47-8.24). (5) **UQ**: 1,500 paired Monte-Carlo draws through the true physics, three price decks, show the recommendation beats a same-policy baseline in 96% of draws at FY25 prices (raw draws 96.5-99.9% across the three decks) — but that baseline's 1.3 m³/d cutoff is our own choice; with the same 0.6 backstop on both sides it's 84% (median ₹2.5k/day), and if the VFD can run below 2 spm, as our own cold well does, the set-point gain is ≈ ₹0. It also drops to only 16-25% if the baseline is assumed to do nothing about float. None of this is field validation against Baghewala itself, and we say so.

**16. What's the overfitting risk on synthetic data, and how do you handle it?**
The deeper risk isn't classic overfitting. It's **circularity**: the surrogate learns *our* equations, so a high score measures how well XGBoost imitates our twin, not how well the twin matches Baghewala. What we did: a held-out split (single, not k-fold), shallow trees (depth 4, 300 trees, subsample 0.9), and a log-transformed target so extreme SOR corners don't dominate. What we don't claim: that any synthetic metric transfers to the field. The fix for circularity is calibrating the twin to OIL's data first, then retraining.

**17. Why is a "digital twin" different from a SCADA system?**
SCADA collects sensor data and carries operator commands; it doesn't model *why* the well behaves as it does. A twin is a physics/ML model of a specific asset that computes states you can't measure (heated radius, downhole viscosity, floating risk) and predicts the effect of a change before you make it. A twin would *consume* SCADA data. Any path back to the field would start as advisory mode (human approves), and **today nothing is connected in either direction**.

**18. What's the realistic deployment path: SCADA/OPC-UA, edge vs cloud?**
(1) Read tags from OIL's SCADA via OPC-UA (casing pressure, injection rate, rod load, temperatures) into the FastAPI backend. (2) Inference is light (milliseconds), so an edge box at the field office works and survives patchy connectivity, with the cloud for retraining and fleet analytics. (3) **Advisory mode first**: the twin recommends and an engineer approves, and only much later, if ever, closed-loop. None of this is built. The prototype has no SCADA link, and the dashboard says so on every page.

---

### C. Business / Impact (7)

**19. Who pays for this, and why would they?**
Oil India, which pays for the diesel that makes steam and for rod-pump workovers. The value case rests on two cost lines, each stated **per cycle**, on a **net-cash** basis (counterfactual-free, as of rev 13). **Fuel**: the recommended 1,000 t cycle burns *less* diesel than the baseline's 1,300 t — against a baseline run the SAME way (VFD-hold), the net-cash gain is **+₹3,332/cycle-day** at OIL's confirmed FY25 price (+₹4,319 at the $65 floor, +₹5,382 net of royalty and cess) — always name the baseline's own float policy, since it moves this number more than any set-point does. **Workovers**: $15k–$50k per rod-pump workover, industry-typical, but our own model doesn't yet price the specific cost of the VFD-hold policy holding rods at the float-alarm line for ~55–60 days a cycle — a direct data ask, not a solved problem.

**20. What does a rod failure workover typically cost?**
No Baghewala number is published. Industry literature gives roughly **$15,000–$50,000 per event** [TYPICAL], covering rig time, rod/tubing replacement and lost production. Rod/tubing wear is among the most common SRP failure causes, which is what the floating index is meant to flag.

**21. What's the intuition behind steam generation cost?**
Fuel dominates. OIL's own BGW-8 numbers (~3,100 kg/hr of steam from ~220 kg/hr of HSD) give **~71 kg diesel per tonne of steam**, inside the generic 2.6–4 GJ/t band. As of rev 13, base case is a **mid-of-range 15% discount off retail** (moved down from the earlier 30% "bulk" assumption on the coordinator's instruction — still unsourced either way), giving **₹7,111 per tonne of steam**; 30% and 0% (retail) are kept as named presets. CO₂ is **~224 kg/t**. **Per cycle only.** Never multiply by 365/cycle-days — CSS jobs are 6–18 months apart in the field. The oil-price side matters just as much: our base case is OIL's own **confirmed FY25 realisation ($78.09/bbl)**; the $65/bbl planning floor is a comparison preset; and a third, new deck nets out royalty and OID cess (~₹3,600/bbl) — on which every feasible set-point is negative even against a shut-in cold well.

**22. Can this scale to other Indian or global CSS fields?**
Architecturally, yes. The physics is general and field-specific numbers live in a parameter file. India's other thermal heavy-oil experience is **ONGC's Mehsana asset in Gujarat (Balol/Santhal, in-situ combustion)**, which is not in Assam or Rajasthan. Internationally, California and Canadian CSS. Caveat: each field needs its own calibration against its own data. It is reusable engineering, not copy-paste.

**23. Why can't Oil India just buy an off-the-shelf optimiser?**
They can buy excellent **pump** tools: **XSPOC (ChampionX)**, **Lufkin SAM / SROD**, **Weatherford ForeSite**. These do dyno-card diagnostics, pump-off control and speed optimisation, but they treat reservoir inflow as a fixed input. They can buy **reservoir/facility** tools: **CMG STARS / Eclipse** for thermal simulation, and **SLB, AVEVA and Kongsberg** facility twins. These treat the pump as a sink. What we found no product doing is coupling the CSS steam decision with rod-pump risk on one well, where steam changes viscosity and viscosity changes rod loading. We'd sit alongside these tools, not replace them. The in-house and data-sovereignty angle is a bonus, not the core claim.

**24. What are the model's realistic limitations right now?**
Say them plainly. (1) **No history match against real field data** — calibrated against published literature bands and a real CalGEM field-SOR band, not Baghewala's own cycle records, which don't exist publicly (though the calibration loop is now built and demonstrated on synthetic data). (2) **Two disclosed physics/economics gaps**: no interior soak optimum (soak held fixed at practice); and the gross-margin-optimal steam slug at our mid-range diesel discount sits below the BGW-8 slug range (~750 t vs 1,040-1,560 t) — read as revealed preference on OIL's real steam cost. (3) **Single well.** No interference or field-wide pressure communication (though a field-level scheduler demo exists on synthetic wells). (4) **Thermal model form.** Marx-Langenheim is a **heat-balance / heated-area model with vertical conduction loss to cap and base rock**, not a 1-D radial temperature solution, with no gravity override, no steam fingering and no layering. (5) **Rod-string failure/workover cost is entirely unpriced** — our recommended VFD-hold policy holds the rods at the floating-index alarm line for ~55-60 days a cycle (a damage index ~5x the pull policy's), and we have no ₹ figure for what that actually costs. Same-policy, the recommendation is 11% less oil for 23% less steam (353 vs 395 m³), not more oil; even so, against a baseline that does nothing about float, the canonical recommendation still nets +₹2,622/cycle-day — the damage cost this item flags simply isn't in that number either way, positive or negative. (6) **Several unsourced economic assumptions remain**: daily opex (₹5,000/d), the $10/bbl heavy-oil discount, the diesel discount base (moved to 0.15 this rev, still unsourced), and the royalty/cess rates in our new levies deck (20%/20%, cross-checked only against an implied ≤35% cap). Pump geometry and net pay are still open data asks. (7) **No geomechanics** (compaction, thermal fracturing). (8) **Net of royalty and cess, every feasible set-point we tested is negative** — even against a shut-in cold well; "is CSS profitable" ultimately needs OIL's own P&L basis, not ours. (9) **ML** is trained only on our own physics (circular), and the model's cold, unstimulated well counterfactual is shut in (not pumped) under every float policy but "do nothing" — an upper-bound reading, disclosed as such.

**25. What does success look like at the pilot stage?**
(1) The twin, calibrated on some of OIL's historical cycles, predicts **held-back** cycles within an agreed error. (2) Its floating flags line up with the well's own dyno cards and rod-failure history. (3) On a few pilot wells in advisory mode, engineers find the recommendations sensible and at least directionally better. (4) Only then is a savings figure quoted. Success is "an engineer would act on it", not "deployed everywhere".

---

## PART 1B: KILLER QUESTIONS (prepared, short, honest)

These are the questions that sink teams. Each answer is two to four sentences, so say it
and stop.

**K1. "Your SOR is 0.9–1.3. The literature says 3–8. How?"**
That was our v1 prototype, and it's exactly why we audited it: v1 over-predicted the oil rate about 25 times, and SOR is steam divided by oil. We replaced the physics with published models, fixed more bugs ourselves, then two rounds of independent adversarial review (AI-assisted, persona-based, not a named human expert) on 27 September found the next revision's headline gain was mostly a baseline artefact, which drove three more physics waves. The current engine gives **gross SOR 4.50** at the reference set-point, inside the re-specified 3.0-4.6 band and a real CalGEM 3.47-8.24 band. We still don't quote any Baghewala-specific SOR — this is our simulated benchmark, not a measurement.

**K2. "One well at 471 bbl/d? The whole field made 655 bbl/d in July 2025."**
Correct, and we caught it. 74.96 m³/d (471 bbl/d) was the v1 pump ceiling, while the field averages about 19 bbl/d per well (655 bbl/d over ~34 wells; the 2026 record was 1,202 bbl/d field-wide). The current engine peaks at **15.1 bbl/d** at the reference set-point — inside the field-plausible range (AOF was retuned specifically to sit inside this 15-40 bbl/d band).

**K3. "Your optimiser says 10 SPM. Heavy-oil practice is 3–6."**
In v1, higher SPM raised pump capacity during a pump-limited plateau that shouldn't exist, and that is where the entire −30% came from. In the current engine, SPM is restricted to the **3–6 practice band**, and our recommendation starts at **4.5 SPM against the baseline's 5** — but as of rev 13, SPM is a weak lever once a VFD is doing the work: our recommended **`vfd_hold`** policy holds the pump at the floating-index alarm line (0.6) automatically, down to a 2-spm floor, so the start speed barely matters (4–5 spm are all within ~₹0.2k/cycle-day of each other). The lever that actually matters now is **stroke length** (64-in vs the baseline's 86-in, 57% of the same-policy gain).

**K4. "A 3-day soak? OIL soaks 7–13 days."**
v1 modelled only the heat soak costs, not its benefit, so the shortest soak always won. The current engine (Boberg–Lantz) has soak sensitivity that is small and monotone, not an interior optimum (under the float-onset rule, margin per cycle-day actually falls slightly beyond 5 days of soak). So we don't let the optimiser search it: soak is **held fixed at 10 days**, the same published-practice value the baseline already uses, and we disclose that as a model limitation rather than presenting a twin-derived soak recommendation.

**K5. "A 61-day cycle? Real CSS cycles are 6–18 months apart."**
That 61-day figure was v1's inject + soak + produce time until the rate hit cutoff — not the interval between steam jobs, which is why every economic figure we give is per cycle, never per year. The current reference cycle runs about **178 total days** (about 202 days for the recommended cycle, ending on the float-alarm rule), still well short of the 6–18-month field interval, and we still never annualise.

**K6. "Your oil is thinner than water at steam temperature?"**
Yes, in v1: Andrade through our two anchors gave 0.63 cP at 290 °C, which is impossible for a 15° API crude. We switched to Walther (ASTM D341), the petroleum standard, with the same anchors: 7.2 cP at 244 °C, 4.13 cP at 290 °C, and a 1 cP floor. Unchanged since — heat balance, wellbore loss, pump-capacity and BL-sourcing fixes never touched viscosity.

**K7. "Where does the 0.6 floating threshold come from?"**
It's our design threshold, defined in our spec, not an API standard. FI is viscous drag divided by buoyant rod weight, so at 0.6 the drag is 60% of the weight pulling the rods down. It's independently cross-checked: our separately computed dynamometer card shows carrier-bar separation starting right around that same line. It must still be calibrated against this well's real dyno cards and rod-failure history. Our current recommendation runs right up to it deliberately: it produces until FI 0.6 has persisted 3 consecutive days, then the cycle ends. The alarm is what stops the cycle, not a margin kept clear of it.

**K8. "Why ML at all, if the physics is fast?"**
Fair question, and speed was never really the reason. The real ones: (1) **contract-first design**, meaning the optimiser talks to a predictor interface, so it survives swapping in CMG-class physics that takes minutes to hours per run; (2) **batching**, since a batched surrogate call is much faster per candidate than looping the twin, which matters for multi-well sweeps and the dashboard's live what-if sliders. What ML is **not** any more: as of rev 13 the classifier's p(float) is dropped as an optimisation constraint entirely — it's informational only. The search is instead constrained by two real physical limits: the injectivity gate (≥400 kPa sandface margin) and the FI ≤ 0.6 float-policy rule itself.

**K9. "You train on your own physics. Isn't that circular?"**
Yes, partly, and we say so. The surrogate can only be as right as the twin it copies, so its R² measures imitation, not Baghewala accuracy — and at rev 13 the surrogate's own optimum lands ~24% below the true physics grid's (a 60-call Bayesian search under-resolving a 7-D space, including the new policy dimension, against the grid's 40,194-point exhaustive search), which is why the physics grid, not the surrogate, is the actual decision engine now. Each revision narrows the gap by fixing bugs and sourcing constants, but none of it removes the circularity — field data is still the real fix.

**K10. "Why minimise SOR instead of money?"**
Agreed, and done: the optimiser's objective is **net cash ₹ per cycle-day** (counterfactual-free) — not gross, not SOR, and, as of rev 13, no longer incremental margin against an idealised pumpable cold well either, since that counterfactual's own status now depends on the float policy. SOR falls monotonically as steam is cut under the calibrated physics, which isn't the field's actual goal, so it stays the efficiency/carbon headline, not the decision objective. The canonical set-points themselves are chosen by **minimax regret across price decks** (FY25 realisation and the $65 planning floor — the levies deck is reported alongside but isn't part of the minimax), so the recommendation is picked to be robust to which price turns out to be real, not just to maximise the FY25 number in isolation.

**K11. "Is this a digital twin or just a simulator?"**
Today, honestly, a twin-ready simulator, and the calibration loop itself is now built: feed it a CSV of observed cycles and it refits our most uncertain constants, then re-recommends against the recalibrated physics — demonstrated on synthetic data, not yet real OIL cycles. It becomes a full twin once a live data feed exists.

**K12. "What did the chemical engineer on the team actually do?"**
Say it in your own words and be specific. The ChemE lead owns the physics: choosing the models, sourcing parameters from OIL and SPE documents, the energy balance and fuel/CO₂ basis, the self-audit that caught v1's errors (rate 25× high, μ below water, the drainage fudge) and specified the replacements (Boberg–Lantz, Walther, wellbore loss, live P_res), and later sourcing the Boberg-Lantz delta constant. Judges test this with follow-ups, so only claim what you did.

> **ChemE lead: write your own 3 lines here before the viva — don't leave this templated.**
> 1. Your own role in the physics audit: which of the v1 bugs did *you* personally
>    catch or diagnose, and which published model did you pick to replace it (and why
>    that one, not an alternative)?
> 2. The emulsion / water-cut modelling: what did you decide about the Pal–Rhodes law,
>    the inversion point, or the water-cut-as-a-state change — in your own words, not
>    the doc's?
> 3. The data request: if a judge asks "what one thing would you personally ask OIL
>    for first", what's your answer and why, from the chemical-engineering side?

**K13. "Why not XSPOC, Lufkin SAM, SLB or CMG STARS?"**
XSPOC (ChampionX) and Lufkin SAM are excellent pump optimisers that treat the reservoir as fixed. SLB, AVEVA and Kongsberg do facility and field twins. CMG STARS and Eclipse are the gold-standard thermal simulators but take hours per run and need a geomodel. We're a light single-well layer that couples the steam decision with rod risk, sitting alongside those tools, and we could use STARS as our physics later.

**K14. "What changes if OIL gives you real data?"**
The PS says production history and cycle records exist. With them we (1) history-match the uncertain constants, (2) regenerate data and retrain, (3) test blind on held-back cycles, and (4) run an advisory pilot. Only then do we quote a gain.

**K15. "Does it work for a different well?"**
The design is one parameter file per well (`params/field_params.json`: depth, thickness, rod string, pump, fluid), calibrated to that well's own history. Today there is exactly one file, for one representative well.

**K16. "Why CSS, not SAGD or downhole heaters?"**
CSS is what OIL runs at Baghewala, and we optimise the operation as it exists. OIL has trialled electric downhole heaters and has named SAGD as a next step. SAGD needs horizontal well pairs and thick, permeable pay, so it is a different design problem, but our thermal and viscosity modules would carry over.

**K17. "What about allocating steam across many wells?"**
We built a first version: `ml/schedule.py` physics-optimises each well's own job, then chooses which wells get steam next off one shared generator (bitmask-exact search over well subsets, ERD order within a subset). On a 12-synthetic-well demo, with every well run VFD-hold, a naive fixed-job policy already earns +₹72,320/d field-wide, and exact scheduling reaches +₹109,799/d, serving 10 of 12 wells. It's still a synthetic-wells demo, not deployed against real field interference or generator physical limits, but "we are single-well" is no longer accurate — that's where batched surrogates earn their keep.

**K18. "Is the dynamometer card computed?"**
Yes, as of rev 6/9 — `twin/dyno.py` solves a Gibbs (1963) rod wave-equation finite-difference model over a typical rod string, giving a full surface and pump card, not a scaled sketch. It's not a *measured* card — no sensor has been on a real Baghewala rod — so OIL's recorded cards are still the calibration target for the string properties.

**K19. "Your dashboard says BGW-07. The first CSS well was BGW-8."**
BGW-07 is a label for one representative well. We have no single well's data, and nothing on screen is well 7's data. BGW-8 (Dec 2018) is where the 5–6× uplift and our steam-rate/quality figures come from.

**K20. "Slide 4 says parameter-sweep tests. What exactly?" (An older deck said "Monte-Carlo sensitivity in tests".)**
The property tests still run small deterministic grids: viscosity × SPM for the floating index, several steam volumes for the SOR shape, and so on — those assert monotonicity, bounds and limiting cases, not uncertainty. But as of this pass **there now is a real Monte Carlo**: `ml/uq.py` runs 1,500 paired draws over our uncertain economic and reservoir inputs through the true physics, on both price decks, and reports P10–P90 bands and driver rankings. The old "Monte-Carlo sensitivity" wording overstated what we had at the time; it's accurate now.

**K21. "Does the recommendation actually go to the steam and VFD controllers?" (An older slide 3 said "set-points back to steam / VFD control".)**
No. The current slide 3 says "advisory set-points to the operator (SCADA hook planned)", and that's accurate: the optimiser recommends, an engineer stages and confirms, and nothing is sent to any controller. There is no SCADA link. As of rev 13 the VFD is modelled as a real **operating-policy control** in its own right — whether the operator pulls the well on a float alarm or has the VFD slow it down and hold the floating index at 0.6 — not just the SPM set-point schedule; intra-stroke speed shaping is still out of scope.

**K22. "Slide 5 says −41.3%. Do you commit to a 20–30% SOR cut?" (An older slide 5 said "we commit to a 20–30% SOR cut".)**
No, we don't commit to a number, and −41.3% is v1 history now, superseded several times over. The current, quotable numbers name the baseline's own float policy: under the fair, same-policy (VFD-hold) comparison, SOR moves **3.29 → 2.83** and net cash **+₹12,064 → +₹15,396/cycle-day** at OIL's confirmed FY25 price (a gain of +₹3,332) — both physics-verified. Against a *pulling* baseline, SOR moves 4.35 → 2.83, but that comparison books the policy switch, not just our set-points. The deck was rebuilt on these rev-13 numbers (`6da5b6b`).

**K23. "Run your optimiser now. What does it say?"**
Go ahead. `ml/recommend_physics.py`'s `best_settings_physics_5d` — an exhaustive 6-lever × policy grid, every point true-physics-verified — is what the canonical recommendation (1,000 t / 10 d / 89 kgf/cm² / 64-in / start 4.5 spm / cutoff 0.60 backstop / **VFD-hold**) actually comes from. `ml/optimize.py`'s Bayesian surrogate search is kept as a cross-check, but it lands ~24% below this optimum at rev 13, so we report it as a cross-check, not an alternative.

**K24. "On your current engine, is the old v1 'optimum' still relevant?"**
No, and that's not really the comparison any more — v1, rev-9 and rev-12 numbers are all historical. What matters now is that the current engine's own recommendation beats a baseline run the SAME way it is: a SOR cut from 3.29 to 2.83 and a **+₹3,332/cycle-day** net-cash gain at OIL's confirmed FY25 price, under a fair same-policy (VFD-hold) comparison, physics-verified. The bigger-sounding "+₹12,917" number only appears if the baseline is assumed to pull instead — and 68% of that bigger number is the policy switch, not our set-points.

**K25. "Your recommended cycle uses more steam — how is that green?"**
Actually, this time it uses less: 1,000 t against the baseline's 1,300 t, because almost all of the gain now comes from slowing the rods, not from more steam. Gross SOR and CO₂ per m³ oil both fall as a result. We still never claim a headline CO₂ number without saying it's per m³ of oil, not an absolute figure.

**K26. "Why is soak fixed at 10 days instead of optimised?"**
Because the twin's own soak sensitivity is small and monotone, not an interior optimum — under the float-onset rule, margin per cycle-day actually falls slightly with more soak beyond about 5 days. Boberg–Lantz gives no soak benefit beyond simple conduction, so letting the optimizer search it just drifts to whichever search-box edge is marginally better, with no physical meaning. We hold soak at the 10-day published-practice value instead and disclose this as a model limitation, not a twin-derived recommendation.

**K27. "What did the three bugs teach you?"**
That's a strength question, and we treat it that way: we found and fixed missing sensible heat, double-counted wellbore loss, and pump capacity sized against oil instead of liquid — all through our own internal calibration process, before trusting a single number, not because a judge or reviewer caught it. That's the same debugging discipline that later sourced our heat-loss constant and caught v1's ~25× rate error in the first place.

**K28. "Why is your baseline losing money?"**
Depends on the price deck and which float policy it runs. Under the recommended (VFD-hold) comparison the baseline doesn't lose money at all — it nets +₹12,064/cycle-day, just less than our recommendation's +₹15,396. It only shows a loss if it's assumed to **pull** the well the moment its rods float, which forfeits cheap late oil a VFD-hold policy would have kept producing. Either way, ₹ is now on a **net-cash** basis (counterfactual-free) rather than gross, and the real root cause is that OIL's actual SPM, stroke and — now the biggest one — float-response practice are unknown; that's exactly why we're asking for their real operating practice.

**K29. "Gross vs incremental SOR — which do you quote?"**
Gross, always, as the headline — that's the literature and CalGEM convention, so it's the number that's actually comparable (4.50 at reference; 2.83 at the recommendation, VFD-hold). As of rev 13, the ₹ decision itself no longer runs on incremental margin against an idealised pumpable cold well — it runs on **net cash per cycle-day** (counterfactual-free), because the cold well's own status now depends on the float policy (shut in under every policy except "do nothing"), so an incremental figure would book that policy switch as if it were the recommendation's gain. The canonical set-points are chosen by **minimax regret over the FY25 and $65 price decks**, so the recommendation itself is robust to price, not tuned to one deck. SOR stays gross either way.

**K30. "Is the dyno card real?"**
It's computed, not measured — a Gibbs 1963 rod wave-equation solve over a typical heavy-oil rod string, not an illustrative shape. Separately, we've built a classifier that would read a real, measured card and flag a fault type — 94.8% accuracy on synthetic cards — but it too has never seen a real card, so we call it a first read, not a validated diagnosis. Give us one measured card from OIL and we can calibrate both against it.

**K31. "What if we give you 10 cycles of data?"**
That's exactly the loop we've already built and demonstrated: feed us a CSV of observed cycles, our calibration step fits the model's most uncertain constants — recovering them within about 1 to 10% on a synthetic test — and then re-recommends set-points directly against that recalibrated physics. But the single most valuable thing OIL could give us now is a water-cut-versus-time log and one late-cycle dynamometer card — those directly test the mechanism our whole recommendation rests on.

**K32. "Where does most of the gain actually come from?"**
At rev 13 the honest answer is two layers. First, and biggest: **the operator's own response to rod float** — whether they pull the well or slow it with a VFD — is worth more money than any set-point: our same canonical recommendation gains +₹2,622/cycle-day against a baseline that does nothing about float, +₹3,332 against a baseline that also VFD-holds, and +₹12,917 against a baseline that pulls at the first alarm — almost the whole range is the baseline's own policy, not our set-points. Once you hold that policy fixed and compare fairly (both sides VFD-hold), the remaining, smaller gain (+₹3,332) decomposes stroke 57%, cutoff 30%, steam 11% — SPM itself is barely a lever any more, since the VFD is doing the slowing automatically.

**K33. "Why a 64-inch stroke and VFD-hold — isn't that just pumping less?"**
It looks that way, but the mechanism is different: a shorter stroke means lower rod velocity at the VFD's 2-spm floor, so the VFD can hold the floating index at its 0.6 limit for longer before the well has to be pulled. That means a longer producing phase, and more oil per tonne of steam; SOR itself improves too. It's about letting the VFD hold the float line longer, not pumping less for its own sake — which is why stroke is 57% of the (same-policy) gain and SPM itself is barely a lever once a VFD is doing the slowing.

**K34. "Why does your baseline lose money?"**
Depends which baseline you mean, and we now say so explicitly. If the baseline is run the SAME way as our recommendation (VFD-hold), it doesn't "lose money" at all — it nets +₹12,064/cycle-day, just less than our +₹15,396. If the baseline instead **pulls** the well the moment its rods float (the rev-12 assumption), it does lose value relative to VFD-holding — it loses the cheap late oil the VFD-hold policy would have let it keep. Either way, the real root cause is that we don't know OIL's actual SPM, stroke, **or float-response practice** — and that last one is now the single biggest open question in the whole model.

**K35. "Is stimulation even worth it, given the cold-well counterfactual?"**
As of rev 13, the model's cold, unstimulated well is **shut in** under every float policy except "do nothing" (FI 1.0, 189 kN at the assumed unit's 2-spm floor) — so every incremental ₹ figure we quote is against a shut-in well, and is an upper bound; the field DID produce these wells cold, so a "pumpable" reading (~₹11.4k/d lower) is reported alongside it as the more field-consistent one. On our net-cash numbers, P(recommendation beats a same-policy baseline) is 96% against a baseline whose 1.3 m³/d cutoff we chose — 84% (median ₹2.5k/day) with the same 0.6 backstop, and ≈ ₹0 if the VFD can run below 2 spm as our own cold well does; OIL's VFD minimum speed is the one datum that decides this. Net of royalty and cess, every feasible set-point we tested is negative even against the shut-in well — so "is stimulation worth it" still depends on OIL's own price/levy basis, which is why that's now a direct data ask.

**K36. "What is real-time here — is this actually live?"**
Two things, kept separate. The twin itself is fast — about 8 milliseconds a cycle — so a 1,500-draw uncertainty sweep runs in seconds, and the exhaustive 6-lever × policy physics grid (40,194 feasible points per policy) runs in about 172 seconds (~3 minutes), not instantly, but still fast enough that we optimise interactively rather than waiting overnight. Separately, we have a live FastAPI service the dashboard talks to. What we don't have yet is a SCADA hook pulling live field telemetry — that's planned, not built, and we say so rather than imply this is already streaming real field data.

**K37. "Your gain depends on what the baseline operator does — so what is it?"**
Honestly, we don't know, and it's the single biggest lever in the whole model — bigger than any set-point. We report all three answers: if the baseline operator VFD-holds the same way we recommend, our gain is **+₹3,332/cycle-day (FY25) / +₹4,319 ($65) / +₹5,382 (net of levies)**. If the baseline instead pulls the well at the first alarm, the gain looks much bigger — **+₹12,917 / +14,694 / +16,606** — but 68% of that is just the policy switch, not our set-points. And if the baseline does nothing about float at all, our canonical recommendation still **gains** **+₹2,622 / +3,484 / +4,413** against it (TIER1 §12.6, "mixed" row) — an earlier version of this answer quoted **−₹3,865 / −2,513 / −1,057** here, but that number belongs to a different, non-canonical plan built specifically for a do-nothing world, not to our actual recommendation, and has been retired. What doesn't change: our model still prices no cost for running floating rods, so none of these three numbers reflect rod-string damage. Which of the three baseline behaviours is real depends on what OIL's operators actually do — a direct data ask.

**K38. "Why VFD-hold and not just pull?"**
Because SOR is better: 2.83 under VFD-hold vs 3.60 if the same recommended set-points are run with a pull policy, and — in-model, with a perfectly known drag law — the well spends **zero** days at the floating index's hard limit (FI=1.0), against 72–124 days if float is ignored entirely. But it isn't free: VFD-hold holds the rods right at the 0.6 alarm line for roughly 55–60 days a cycle, our graded rod-damage index there runs about 5× what the pull policy sees, and once drag uncertainty is sampled in the UQ, VFD-hold is actually the **more** float-exposed policy of the two (median 6 alarm days vs 0 for the baseline). We don't have a ₹ figure for that extra wear — it's disclosed as unpriced, not hidden.

**K39. "Is CSS even profitable net of royalty and cess?"**
No, not on our numbers. At OIL's own approximate levy structure (~35% of realisation, cross-checked against their FY25 Annual Report's own royalty-plus-cess exchequer table), every feasible set-point we tested is net-cash-negative — even against a shut-in cold well that costs nothing to not-produce. That's not a model failure so much as an open question: OIL's own P&L treats these levies differently than a flat national-value basis might, so this is exactly why we're asking for their real net-of-levies price deck rather than assuming one.

**K40. "Why does your slug size drop below what BGW-8 used?"**
At our assumed mid-range diesel discount (0.15, the midpoint of a 0–0.30 range with no cited source), the model's own gross-margin-optimal steam slug is about 750 tonnes — below the 1,040–1,560 tonnes BGW-8's actual first CSS job used. We've recorded this as a disclosed test failure (xfail), not hidden it, and we read it as revealed preference: if OIL is actually running bigger slugs than our optimum suggests, their real diesel cost is probably cheaper than the mid-range we assumed, which is itself an open data ask.

**K41. "Your gain disappears if the VFD floor is the same for both wells — so what is your gain?"**
Honestly, the set-point ₹ number does go to about zero: the stimulated well's 2-spm VFD floor and the cold well's credited 0.53 spm are inconsistent, and the baseline's 1.3 m³/d cutoff is our own assumption, not OIL's. Give both wells one floor and the same 0.6 backstop, and the fair gain runs **₹0–5,000/cycle-day** depending on where that floor sits. What's robust isn't a rupee figure — it's the **operating rule** (slow the pump before you pull it) and the SOR drop (3.29 → 2.83), both of which hold regardless. The ₹ gain is decided by two numbers we don't have: **OIL's actual VFD minimum speed and their real pull/produce cutoff** — both are now items 16–17 on our data request.

**K42. "You keep saying 'less steam, less oil' — why is 11% less oil a good thing?"**
It isn't, on its own — it's a trade, and we say the trade out loud. Under the same VFD-hold policy on both sides, the recommended cycle burns 23% less steam (1,000 vs 1,300 t) and makes 11% less oil (353 vs 395 m³), so SOR falls 3.29 → 2.83: we're buying a bigger cut in fuel and CO₂ per barrel than the oil we give up. "More oil" is only true against a baseline that *pulls* instead of slowing down (≈299 m³) — a different, unfair comparison we no longer make. Whether that trade is worth it commercially is exactly what the net-cash numbers (Q19/K37) are for, not SOR alone.

**K43. "Is the pump actually safer under your recommendation, or does it just look that way?"**
Only relative to a specific baseline, and we say which one. Against a baseline run the SAME way (VFD-hold), the recommendation's own floating index and graded damage index are essentially unchanged (FI 0.62 vs 0.62; damage index 15.99 vs 15.91 — very slightly worse) — it is **not** demonstrably safer than a same-policy baseline. It only looks safer against a baseline that *lets rods float unmanaged* (72 alarm days vs 3, 42 days at FI = 1.0 vs 0) — a real, meaningful difference, but one that compares our whole policy choice (VFD-hold vs none) to a baseline's lack of one, not our set-points to theirs. And in either comparison, the damage done while the rods are **held** at the 0.6 alarm line for ~55–60 days a cycle is not priced in ₹ — "safer" here means "safer than doing nothing," not "cheap to run."

---

## PART 2: 10 TRAP QUESTIONS

**Trap 1: "Have you validated this against real field data?"**
*The trap:* any "yes" collapses at the first follow-up.
*Safe answer:* "Not against Baghewala itself. We've checked internal physics consistency with 265 property and benchmark tests (2 are disclosed xfails, not failures), a real 2021 California CSS field-SOR band check against 9,692 real cycles, and scored the ML on a single held-out split of synthetic data generated by our own twin. Real Oil India cycle records — especially a water-cut-vs-time log, a late-cycle dyno card, and their actual float-response practice (do operators slow the pump or pull the well?) — are the next step, and we've already built the calibration loop to ingest them. Synthetic performance and field accuracy are two different things."

**Trap 2: "What's your model's accuracy?"**
*The trap:* quoting R² without "on synthetic data" implies field accuracy.
*Safe answer:* "On a single 80/20 hold-out of our own synthetic data, the oil regressor has R² 0.998, and the incremental-margin-per-cycle-day regressor 0.883 overall / 0.996 inside the operating envelope. That measures how well XGBoost learned our own twin. Field accuracy is unknown until we test on Oil India's cycles."

**Trap 3: "Is this ready to deploy on a real well tomorrow?"**
*Safe answer:* "No. It's a prototype pipeline whose physics is being recalibrated. Deployment needs calibration on OIL data, an advisory pilot with engineers approving every change, and a SCADA integration we haven't built."

**Trap 4: "Does your Bayesian optimiser guarantee the global optimum?"**
*Safe answer:* "No. Nothing guarantees a global optimum on a non-convex function with a limited budget. We use 60 evaluations: 15 random initial points for coverage, then 45 GP-guided calls that balance exploration and exploitation. That gives a good, often near-optimal answer, not a guarantee."

**Trap 5: "How is this different from what ChampionX (XSPOC), Lufkin or Weatherford sell?"**
*Safe answer:* "Those are mature pump-optimisation products and we're not replacing them. They treat the reservoir as fixed. Our layer couples the CSS steam decision with rod-floating risk on the same well, and would sit alongside them."

**Trap 6: "What if your physics assumptions are wrong for Baghewala?"**
*Safe answer:* "Some already were, twice. Our own audit found the first version ~25× optimistic on rate, and we replaced those parts with published models; our own later calibration pass then found three more internal bugs (sensible heat, wellbore-loss double-counting, pump vs. liquid) and fixed those too. What's left is calibrated against literature benchmarks, not Baghewala's own cycle records, which don't exist publicly — every uncertain constant lives in one parameter file, and history-matching against OIL's data is the next step."

**Trap 7: "Can a student team's model compete with professional reservoir engineering tools?"**
*Safe answer:* "No, and it isn't meant to. CMG STARS and Eclipse model 3-D multiphase thermal flow; we don't. Ours is a light, fast single-well tool for coupling steam and pump decisions, complementary to them."

**Trap 8: "How many real CSS cycles has your model seen?"**
*Safe answer:* "Zero. All 3,000 training rows are physics-generated. Oil India's historical cycles are what we'd calibrate and validate against."

**Trap 9: "What's the uncertainty on your SOR reduction and your economics?"**
*The trap:* treating a prototype simulation as a field outcome, quoting a per-year rupee figure, or quoting a gain without naming the baseline's own float policy.
*Safe answer:* "Our v1 prototype showed about 30%, and we audited it and withdrew it as a result. Our current engine gives a physics-verified gross-SOR improvement from 3.29 to 2.83 and a net-cash swing from plus 12,064 to plus 15,396 rupees per cycle-day at OIL's confirmed FY25 price — that's a same-policy comparison, both sides slowing the pump the same way, which is the fair one; if instead the baseline pulls the well on the alarm, the same recommendation looks like a much bigger 12,917-rupee gain, but two-thirds of that is just the policy difference, not our set-points, so we always name which comparison we mean. Our 1,500-draw uncertainty sweep shows the recommendation beats a same-policy baseline in 96% of draws at FY25 prices — but that baseline's 1.3 m³/d cutoff is our own choice; give both sides the same 0.6 backstop and it's 84%, median gain ₹2,500/day; if the VFD can run below 2 spm, as our own cold well does, the set-point gain goes to about zero. That also drops to 16 to 25% if the baseline is assumed to do nothing about float at all — which we show rather than hide. That's still synthetic — physically plausible, not field-validated. On fuel, we state per-cycle numbers, and the recommended cycle burns less: 1,000 tonnes of steam versus the baseline's 1,300. No per-year figure, ever."

**Trap 10: "Have you considered geomechanical risks from repeated thermal cycling?"**
*Safe answer:* "Not in the model. Our thermal model is a heat-balance (heated-area) model with conduction losses to cap and base rock, and there's no geomechanics. It's a stated limitation, and any repeated-cycling decision would need geomechanical assessment from OIL's specialists."

---

## PART 3: CHEAT TABLE (numbers to memorise)

| # | Number | Context |
|---|--------|---------|
| 1 | API gravity 17–19° (PS) / 14–17° (literature) | Quote the PS when quoting the PS; field literature (SPE-23APOG + OIL data) says 14–17° for the producing crude; we model 15.5° |
| 2 | Reservoir temperature 46–48 °C (PS) / ~50 °C (OIL) | Same PS-vs-literature pattern; both mean heavy-oil regime |
| 3 | Depth ~1,100–1,150 m | CONFIRMED; at the edge of the ~1,000–1,500 m CSS rule of thumb (verify), hence VIT |
| 4 | Pay thickness ~12 m | **ASSUMPTION**: net pay not found publicly |
| 5 | Steam rate ~74 t/d | CONFIRMED-derived from BGW-8 (~3,100 kg/hr) |
| 6 | Viscosity 8,000–15,000 cP @ 50 °C | CONFIRMED; we use 11,500 cP (midpoint of OIL's 10,000–13,000) |
| 7 | Baghewala's own SOR: **NOT PUBLISHED** | Never state a number; benchmark against row 8 |
| 8 | Literature CSS SOR 3–8, avg ~6, efficient < 3; real CalGEM 2021 field band **3.47–8.24** | TYPICAL + CONFIRMED (real). Our v1 gave 1.29 (too low, audited); the current engine gives **gross SOR 4.03** at the reference set-point, inside both bands |
| 9 | Steam 280–305 °C (we use 290), wellhead quality 60–70% (we use 0.65) | CONFIRMED, BGW-8 |
| 10 | BGW-8 cycle: 14–21 d injection, soak ~50–60% of that (~7–13 d) | CONFIRMED, OIL internal PPT |
| 11 | Floating threshold 0.6 (VFD-hold: held here down to a 2-spm floor); rev 13 constraint: injectivity margin ≥ 400 kPa (replaces the old p(float) < 0.3 penalty) | **Our design choices**, to be calibrated on dyno cards / a real BHP survey |
| 12 | Heavy-oil SPM practice 3–6 | TYPICAL; v1's "10 SPM" is a model artefact |
| 13 | CSS cycles 6–18 months apart | TYPICAL; why we never annualise |
| 14 | 52–56 wells drilled / 33–34 operational; 19 CSS jobs FY26 (+72%) | CONFIRMED (snapshot-dependent) |
| 15 | First CSS: BGW-8, Dec 2018 (partner Belgrave) → 5–6× uplift | CONFIRMED (OGJ, OIL) |
| 16 | 39 CSS cycles by Jun 2025 | CONFIRMED |
| 17 | Production 218 t (FY17) → 32,787 t (FY25) → 43,773 t (FY26) | CONFIRMED. ~200× since commercial **production** began; FY17 predates CSS (Dec 2018) |
| 18 | Field output ~655 bbl/d (Jul 2025); record 1,202 bbl/d (2026) | CONFIRMED; ≈19 bbl/d per well, so a single well at 471 bbl/d is impossible |
| 19 | 71 kg HSD per t steam ≈ 3.0 GJ/t → ₹5,900–8,400/t, ~224 kg CO₂/t | DERIVED from OIL's BGW-8 numbers |
| 20 | Recommended cycle burns **less** steam this time (1,000 t vs baseline's 1,300 t) | DERIVED, **per cycle only** — direction reversed from rev 9 |
| 21 | Rod-pump workover $15k–$50k (generic); **rod-string damage from running floating rods specifically is unpriced in our model** | TYPICAL, not Baghewala-specific; the unpriced part is a rev-13 finding |
| 22 | 3,000 synthetic cycles, LHS, seed 42, rev-13 physics (7th column: float policy) | Single 80/20 hold-out: oil R² 0.995, float classifier AUC 0.999 (41% positive) — **physics grid, not this surrogate, is the decision engine** |
| 23 | Current engine, reference set-point (1,500/7/1.2/5/86 in/91 kgf, shipped default `pull`): gross **SOR 4.50** | OUR-SIMULATION, **CALIBRATED — safe to quote** |
| 24 | Tests **263 passed, 2 xfailed** (no interior soak optimum; steam optimum at the mid-range diesel price below the BGW-8 slug range — documented gaps, not failures) | Current engine. Neither 236, 197, nor 24/24 appears anywhere current |
| 25 | Recommendation vs baseline, **BOTH under VFD-hold** (fair comparison): 1,000/10/89 kgf/64-in/start 4.5 spm/cutoff 0.60 backstop → gross SOR **2.83**, net cash **+₹15,396**/cycle-day (FY25) vs baseline 1,300/10/91 kgf/86-in/5 spm → gross SOR **3.29**, net cash **+₹12,064** — **gain +₹3,332**. If baseline instead pulls: baseline SOR 4.35, gain **+₹12,917** (68% is the policy switch). If baseline does nothing about float: gain **+₹2,622** (TIER1 §12.6 "mixed" row — the canonical plan still gains here; **−₹3,865** is a different, non-canonical plan and is retired from this comparison) | OUR-SIMULATION, physics-verified. Always name the baseline's own float policy |
| 26 | Gain decomposition (same-policy, VFD-hold): **stroke 57%, cutoff 30%, steam 11%** (FY25 deck) | Supersedes the rev-12 finding (SPM 62%/stroke 32%), now that a VFD does the SPM work automatically |
| 27 | `BL_DELTA_FACTOR = 0.5` **sourced** — exactly the ½ inside Boberg & Lantz's own δ (PEH Eqs. 15.70–15.74) | OUR-MODEL, sourced — never call this unverified |
| 28 | Price decks: OIL's **CONFIRMED FY25 realisation** $78.09/bbl; $65/bbl FY26 planning-floor preset; **new, net of royalty+OID cess ~₹3,600/bbl** (~35% levies, OIL's own FY25 AR basis) — every feasible point is negative on this third deck | CONFIRMED (base price) + ASSUMPTION (discounts, levy rates) |
| 29 | UQ (1,500 draws, 3 decks): same-policy P(rec > baseline), VFD-hold **96%** FY25 (raw draws 96.5/99.2/99.9%) — but **84%** (median ₹2.5k/day) with the same 0.6 backstop on the baseline, and **≈ 0%** gain if the VFD can run below 2 spm as our own cold well does; if baseline pulls 99.1%+; if baseline does nothing only **16–25%**. P(injectable)=100% everywhere | OUR-VERIFICATION, true physics |
| 30 | Real-data benchmark: CalGEM 2021 field SOR band **3.47–8.24** (9,692 real cycles, 5,771 CA wells, a shallow steamflood field with a cyclic-steam subset) | CONFIRMED (real, external data) |
| 31 | Calibration demo: formation_water_cut/aof/thickness recovered within **−5.2/−0.9/−10.9%** (BL fixed, sourced; re-run under rev 13, story unchanged) | OUR-VERIFICATION, synthetic demo |
| 32 | Dyno card: computed (Gibbs wave equation); rod float independently matches the ≈0.6 FI alarm line. Measured-card classifier, 94.8% hold-out, never field-validated | OUR-MODEL — no longer illustrative |
| 33 | Cold well: **shut in** under every float policy except "do nothing" (FI 1.0, 189 kN at the 2-spm floor) — the field produced these wells cold, so every incremental ₹ figure here is an upper bound; a "pumpable" reading (~₹11.4k/d lower) is reported alongside it | OUR-FINDING, rev-13 reframe of the rev-12 cold-well xfail |
| 34 | Independent adversarial reviews (AI-assisted, persona-based; not a named human expert), 27 Sep: judge-shaped **61/100**, technical **52/100 → re-score 58/100 → re-score #2 64/100 → judge re-score #2 66/100** — the top finding each round (rev-12's gain was the pull rule, not the set-point; then the VFD-floor/cutoff finding) drove wave 5 / rev 13 | CONFIRMED (our own review process) |
| 35 | Field scheduler demo (12 synthetic wells, one generator, all VFD-hold): naive **+₹72,320/d** field-wide (rev 12, pulling, was a **loss** of −₹13.3k/d); exact scheduling reaches **+₹109,799/d**, serving 10/12 wells | OUR-SIMULATION, synthetic wells |
| 36 | Best gross-margin slug at the 0.15 diesel discount: **~750 t**, below BGW-8's 1,040–1,560 t (disclosed xfail) | OUR-FINDING, read as revealed preference on OIL's real steam cost |

---

*Prepared for internal PPT round and finale judging. Every "(verify)" tag is intentional.
Revised 27 Sep 2026 after a technical re-score (58/100) of the rev-12 cascade found its
headline gain was a policy artefact, driving **physics wave 5 → rev 13**
(`docs/model-improvement/TIER1_PROGRESS_LOG.md` §12, `params/CHANGELOG.md` rev 13, branch
`wave5`) — operating policy as a control, fair same-policy baselines, a smoothed inversion
band, an injectivity gate and a net-of-levies price deck. This followed the earlier
external-review hardening cascade → physics waves 3–4 (rev 12) (TIER1 §9–§11, CHANGELOG
rev 10–12), rev 9 (physics v3 + economics v2), the rev-5 calibration pass, the self-audit
(`docs/model-improvement/MODEL_IMPROVEMENT_PLAN_{PHYSICS,ML,ECON_VALIDATION}.md`) and the
Tier-1 physics rewrite. Current-engine figures are physics rev 13, calibrated and
physics-verified, re-run on 27 Sep; v1, rev-5, rev-9 and rev-12 figures are all historical
now — from the 13 Sep build (commit 351a89b), 26 Sep evening, 26–27 Sep morning, and 27 Sep
afternoon/evening respectively.*
