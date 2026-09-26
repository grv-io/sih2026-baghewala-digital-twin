# Brutal Content Review — Baghewala Digital Twin (SIH26120)

Reviewer stance: SIH national-round judge, 20 years oil & gas, elimination-round mindset. This document is read-only research — it does not touch docs/SPEC.md, ppt/, docs/, or docs/research/. Every fix below still needs to be applied by the team.

**Files cross-checked:** docs/SPEC.md, params/field_params.json, ppt/notes/deck_content.md, docs/study/viva_prep.md, docs/research/landscape.md, docs/research/baghewala_facts.md, docs/research/ppt_ammo.md, docs/research/field_params_recommended.json.

---

## 0. THE ROOT CAUSE (read this first)

The research agent did excellent work and produced `docs/research/field_params_recommended.json` with real, sourced Baghewala numbers (depth ~1,150 m, API 14–17°, viscosity 8,000–15,000 cP @ 50°C, pressure ~11,400 kPa, steam 280–305°C, injection ~74 tpd, porosity <10%). **None of it was ever merged into the live `params/field_params.json`** — I checked the actual file on disk and it is byte-for-byte the original docs/SPEC.md placeholder block (depth 500 m, API 18.0, mu_ref 2000 cP, T_injection 250°C, andrade_A/B still `null`). This is not a cosmetic slide problem: **the twin's physics engine, the ML training data, and every downstream SOR/floating-index number are currently computed from wrong inputs.** Every contradiction below traces back to this one unmerged file.

---

## 1. FACTUAL CONTRADICTIONS ACROSS FILES

**Finding 1 — SEVERITY: KILLER**
File:section: `ppt/notes/deck_content.md` Slide 1 killer number vs `docs/research/ppt_ammo.md` #13
Problem: Slide 1's headline killer number is "**250 km** — distance from MNIT Jaipur to Baghewala field." Research (`ppt_ammo.md` #13, sourced) gives Jaisalmer district (where Baghewala/Thar operations are described) to Jaipur as **~550–600 km** (range 485–650 km across sources). Even under the alternate "Bikaner-Nagaur sub-basin" description (`baghewala_facts.md` §1), Jaipur–Bikaner is ~330–350 km by road. **250 km matches neither reading.** This is the very first number a judge hears, and it's checkable on a phone in 10 seconds.
Fix: Before printing anything, resolve which admin location you're using (the field is described inconsistently across your own research as "Bikaner-Nagaur sub-basin" AND "Jaisalmer field operations" — pick one and cite it), then verify the actual road distance from MNIT Jaipur's campus (not just "Jaipur") to that location. Until then, use the sourced range: **"~550–600 km — road distance from Baghewala (Jaisalmer district, Thar Desert) to Jaipur (ppt_ammo.md #13)."** A remote, hard-to-reach field is a *better* story for "why real-time digital twin monitoring matters" than a nearby one — don't undersell the remoteness with a wrong small number.

**Finding 2 — SEVERITY: KILLER**
File:section: `ppt/notes/deck_content.md` Slide 2 & Slide 5 ("~4.5 t/m³ typical current SOR") vs `docs/research/baghewala_facts.md` §4
Problem: The deck states 4.5 t/m³ as "typical current SOR in field" with no verify-tag, and `viva_prep.md`'s cheat table row 7 repeats it as "**deck's stated figure**" — also unflagged. But `baghewala_facts.md` §4 says explicitly: **"Steam-oil ratio (SOR) actually achieved at Baghewala — NOT FOUND as an explicit reported number in any source searched."** You are presenting an invented number as Baghewala's real current SOR, on two slides and in the memorization table, with zero hedge. This is the single easiest "gotcha" in the whole deck — any judge who asks "what's your source for 4.5?" gets an answer of silence.
Fix: Either (a) relabel it honestly — **"~4.5 t/m³ — illustrative current-SOR baseline (Baghewala's own actual SOR is not publicly reported; this baseline is drawn from the literature range of 3–8, avg ~6, for CSS operations generally — ppt_ammo.md #10)"** — or (b) drop the specific "4.5" entirely and instead present the literature range 3–8 (avg ~6, efficient <3) as the industry SOR benchmark you're targeting against. Do the same fix to the before/after bar chart on Slide 5 (currently "4.5 → 3.2") — it inherits the same unsourced baseline.

**Finding 3 — SEVERITY: KILLER**
File:section: `ppt/notes/deck_content.md` Slide 4 bullet: "Parameter source: field_params.json populated from Oil India Baghewala data (reservoir depth 500 m, thickness 12 m, steam injection 100 tpd)"
Problem: This sentence explicitly *claims* field_params.json is populated from real Oil India data. It is not. 500 m and 100 tpd are unmodified docs/SPEC.md placeholders that predate any research (confirmed: `params/field_params.json` on disk still has these exact values). The real, sourced numbers exist in `docs/research/field_params_recommended.json` (depth 1,150 m, injection ~74 tpd) but were never merged. If a judge asks "where did 500 m come from in the Oil India data," the honest answer is "it didn't — it's a spec default we forgot to update," which contradicts the slide's own claim in real time.
Fix: Merge `docs/research/field_params_recommended.json` into `params/field_params.json` before the deck is finalized (this is a 10-minute engineering fix, not a rewrite). Then change the bullet to: **"Parameter source: field_params.json calibrated to Oil India / SPE-published Baghewala data (reservoir depth ~1,150 m, viscosity 8,000–15,000 cP @ 50°C, steam 280–305°C @ 60–70% quality)."** Also update the Slide 4 killer number from "500 m" to "~1,150 m."

**Finding 4 — SEVERITY: KILLER**
File:section: `ppt/notes/deck_content.md` Slide 1 ("2000 cP baseline") vs `docs/research/baghewala_facts.md` §2 and `field_params_recommended.json`
Problem: Slide 1's own subtitle bullet states "high viscosity regime (2000 cP baseline)." Confirmed field data (two independent sources: SPE-23APOG paper and OIL internal PPT) puts Baghewala viscosity at **8,000–15,000 cP at 50°C** — the research agent's own note calls the 2000 cP default "off by roughly 5x from confirmed field data; this is the single most important correction in this file." You are stating the *wrong number by 5–6x* on your title slide, for the exact statistic that justifies why the project exists (high viscosity → need thermal recovery).
Fix: Change to **"high viscosity regime (8,000–15,000 cP @ 50°C — ~90–100x more viscous than a typical 18° API crude, ppt_ammo.md #4)."** This is strictly a better number for you: it makes the problem sound harder and more interesting, not easier.

**Finding 5 — SEVERITY: MAJOR**
File:section: `ppt/notes/deck_content.md` Slide 5 ("Oil India's 40+ CSS wells across Rajasthan") vs `docs/research/baghewala_facts.md` §5
Problem: No source in your own research supports "40+ CSS wells." What you actually have: 52 wells *drilled* at Baghewala (33 operational per 2026 reporting), and CSS specifically performed on 19 wells in FY2025-26 (with 39 cumulative CSS cycles as of June 2025). "40+ CSS wells across Rajasthan" conflates "wells drilled" with "wells CSS'd" and implies a Rajasthan-wide (multi-field) count you never sourced. `viva_prep.md`'s own cheat table (row 15) hedges this as "deck's figure — verify exact count with Oil India," i.e., the team already knows this number is shaky and put it on a slide anyway.
Fix: Replace with the real, better numbers: **"52 wells drilled at Baghewala (33 operational); 19 wells CSS'd in FY2025-26 alone (~72% YoY growth) — the same twin framework extends across this and future CSS wells as they come online."** This is more specific and more credible than a vague "40+."

**Finding 6 — SEVERITY: MAJOR**
File:section: `docs/research/field_params_recommended.json` (`steam.T_injection_C`, `steam.latent_heat_Jkg`) vs `docs/study/viva_prep.md` cheat table row 10 vs `docs/research/ppt_ammo.md` #14
Problem: The cheat table tells the team to memorize "Steam temperature ~250°C **(verify)**" as an "order-of-magnitude" number needing verification. But you already have a **CONFIRMED, non-hedged** number sitting in your own research: BGW-8's actual first-cycle steam was **280–305°C at 85–97 kgf/cm²** (`ppt_ammo.md` #14, `field_params_recommended.json` sets 290°C). The cheat table is telling the team to hedge on a number that doesn't need hedging, and to recite the *wrong, lower, generic textbook value* instead of the real one you already sourced.
Fix: Cheat-table row 10 should read: **"Steam temperature 280–305°C (CONFIRMED, BGW-8 first cycle, OIL internal data) — hotter than generic CSS textbook assumption of ~250°C, showing our twin is calibrated to real Baghewala operating conditions, not a generic default."** Delete the "(verify)" tag — you have a source.

**Finding 7 — SEVERITY: MAJOR / DIPLOMATIC HANDLING REQUIRED**
File:section: `docs/SPEC.md` field_params defaults + `docs/study/viva_prep.md` cheat table rows 1–2 ("17-19° API," "46-48°C — per problem statement") vs `docs/research/baghewala_facts.md` §2 ("API 14–17°... CONFIRMED"; "Bottom-hole temperature ~50°C")
Problem: **This is the trickiest one — the official PS text itself says 17–19° API and 46–48°C, while your own literature research (SPE-23APOG, an independently published paper, corroborated by an internal OIL deck) says the *current producing* crude is 14–17° API at ~50°C.** These are not wildly far apart, but they are different, and if the PS author or an Oil India judge is in the room, flatly contradicting the PS text ("actually you're wrong, it's 14-17°") on stage is a bad look — even though your number is better-sourced.
Fix (diplomatic framing — use this exact phrasing pattern): **"Per the official problem statement, Baghewala crude is characterized as 17–19° API at 46–48°C reservoir temperature. Our team additionally cross-referenced published field literature (SPE-23APOG, 2023) and Oil India's own operational data, which report the currently producing Jodhpur Sandstone crude at a slightly heavier 14–17° API and ~50°C — consistent with the PS's heavy-oil classification, and if anything reinforcing that thermal recovery is necessary."** This frames the discrepancy as "we did extra homework and found it's even harder than the PS states," not "the PS is wrong" — never say the latter out loud in the room. Use PS numbers when directly quoting the PS; use the tighter, sourced numbers for your own model calibration and say so explicitly if asked.

**Finding 8 — SEVERITY: MINOR (but compounds into others)**
File:section: `params/field_params.json` `reservoir.porosity` (0.28) vs `docs/research/baghewala_facts.md` §2 / `field_params_recommended.json` (0.09)
Problem: Live params file porosity is 3x too high (0.28 vs confirmed <10%, recommended 0.09). Not on any slide currently, but it silently understates how hard a reservoir this actually is — a "poor-to-fair, <10% porosity, extreme viscosity" reservoir (per `ppt_ammo.md` #15) is a *stronger* justification for needing a digital twin than a comfortable 28%-porosity one. You're sitting on a better story and using a worse number.
Fix: Merge the corrected value (0.09) into `params/field_params.json`; consider surfacing "<10% porosity, poor-to-fair reservoir quality" on Slide 4 as an added feasibility/difficulty justification.

**Finding 9 — SEVERITY: MINOR**
File:section: `params/field_params.json` `fluid.andrade_A` / `andrade_B_K` (both `null`) vs `field_params_recommended.json` (fitted: A=1.164e-6, B_K=7436.6)
Problem: Because the live params file still has `andrade_A`/`andrade_B_K` as `null` and `mu_ref_cP`/`T_ref_C` at the wrong (2000 cP / 47°C) anchor, per docs/SPEC.md's own module contract (`viscosity.mu_cP`), the viscosity fit routine will run against the *wrong* anchor point when it fits Andrade's constants — meaning the whole thermal-viscosity curve the simulator uses today is not just "using an old default," it is actively computing an internally-consistent-but-wrong physics model. This is an engineering bug, not just a slide typo, and it means every SOR/floating-index number currently coming out of the twin (dashboard, ML training data) is built on a 5x-wrong viscosity anchor.
Fix: Same as Finding 3 — merge `field_params_recommended.json` into `params/field_params.json`, then re-run `twin/generate_data.py` and `ml/train.py` so the synthetic dataset and trained models reflect real Baghewala physics before finale.

---

## 2. CLAIMS A JUDGE CAN KILL

**Finding 10 — SEVERITY: MAJOR**
File:section: `ppt/notes/deck_content.md` Slide 5, two bullets: "$500 k/year cost savings **(verify source)**" and "eliminates 80% of unplanned rod failures (industry benchmark, **verify source**)"
Problem: Literal "(verify source)" text sitting inside slide bullets that will be projected on screen. This does two bad things at once: (1) it signals to the judge, in real time, "we know this number is unconfirmed and printed it anyway," which is worse than just not having the number; (2) `deck_content.md`'s elevator pitch paragraph *drops the caveat entirely* — "unlocking $500k/year in margins per well" is stated as flat fact there, contradicting the hedged version two slides earlier. The deck is internally inconsistent about its own confidence in this number.
Fix: Never let "(verify)" reach a slide. Either replace with a number you can defend — you actually have one: `ppt_ammo.md` #12 gives a **sourced (TYPENARY) $15,000–$50,000 per sucker-rod workover** — or reframe the whole bullet as an illustrative economic model: **"Economics (illustrative): at $15k–$50k per avoided rod-pump workover (industry-typical, iFactory/general SRP literature) plus reduced steam cost per barrel from a lower SOR, savings scale directly with wells covered — exact per-well $/year figure requires Oil India's cost data to compute precisely."** Fix the elevator pitch to match this same hedge — do not state $500k/year as delivered fact there while hedging it on the slide.

**Finding 11 — SEVERITY: MAJOR**
File:section: `ppt/notes/deck_content.md` Slide 5 killer number: "20–30% SOR reduction (target, physics-validated)"
Problem: "Physics-validated" is a loaded phrase. Your own `viva_prep.md` Trap 9 explicitly pre-empts this exact issue ("these are simulation targets... treating them as guaranteed field outcomes is inconsistent with our own deck's honesty flags") — meaning the team already knows this wording is risky, but didn't fix the slide that causes it. "Validated" implies checked against an external ground truth; what you actually have is internal self-consistency within your own synthetic simulation.
Fix: Change "physics-validated" → **"physics-simulated (internal consistency-checked; field validation is the next phase)."** One-word-category swap, removes the trap entirely, and now matches Trap 9's own prepared answer instead of contradicting it.

**Finding 12 — SEVERITY: MINOR**
File:section: `ppt/notes/deck_content.md` Slide 1 bullet: "Real-time prediction of heavy oil well dynamics at Baghewala field"
Problem: Stated as an accomplished capability ("real-time prediction... at Baghewala field") rather than a design target. Nothing has been run against Baghewala's live SCADA or historical cycle data yet — docs/SPEC.md's own sub-second latency figure is a *constraint on the API*, not a demonstrated production capability at the named field.
Fix: **"Digital twin designed for real-time prediction of heavy oil well dynamics, targeting Baghewala field, Bikaner"** — small wording change, removes the implication that this is already running against the real field.

**Finding 13 — SEVERITY: MINOR**
File:section: `ppt/notes/deck_content.md` Slide 6, reference list: "Pennwell, 'CSS Field Data & Optimization' — industry case studies (**verify source and access with Oil India**)"
Problem: A citation that literally says "verify source and access" is sitting in the reference slide. A judge who reads slide references (some do) will notice a citation the team admits it hasn't confirmed exists.
Fix: Drop this reference entirely unless it's confirmed before the deck is finalized — you have plenty of real, checkable sources already (Marx & Langenheim 1959, Andrade 1934/ASTM D341, Vogel 1968, plus your own SPE-23APOG-535203 and the OIL internal PPT cited throughout `baghewala_facts.md`). A shorter, 100%-real reference list beats a longer one with a visible weak link.

---

## 3. VIVA_PREP.MD — SCORING (1–5, judge-survivability) & 5 REWRITES

| # | Question | Score | Why |
|---|---|---|---|
| 1 | Andrade/activation-energy intuition | 3 | Solid chemistry, but never cites the team's own fitted Andrade constants or the 11,500 cP anchor sitting in `field_params_recommended.json` — reads as a textbook answer, not a project answer. **Rewritten below.** |
| 2 | Soak phase physics | 4 | Correct, general, no Baghewala-specific gaps to expose. |
| 3 | Optimum steam volume | 4 | Good diminishing-returns argument, correctly ties to Bayesian optimization. |
| 4 | Dynamometer card / floating | 4 | Strong, vivid, technically correct. |
| 5 | Asphaltene issues | 4 | Good, appropriately hedges CSS as "not a guaranteed fix." |
| 6 | CSS depth limits | **1** | **Actively dangerous.** Cites Baghewala's depth as "~500 m (per field_params.json)" and uses that wrong number to argue CSS is favorable here. Real confirmed depth is ~1,100–1,150 m — which sits right at or inside the very 1,000–1,500 m threshold the same answer says is where CSS starts becoming inefficient. If a judge knows the real depth, this answer self-destructs live. **Rewritten below.** |
| 7 | Why SOR is the key metric | 3 | Correct concept, but doesn't cite the literature range (3–8, avg ~6, efficient <3) that's sitting in `ppt_ammo.md` #10 — a free, sourced number left unused. |
| 8 | Why Baghewala needs thermal recovery | 3 | Uses PS numbers (17-19°, 46-48°C) without the fallback framing from Finding 7 above — vulnerable if a judge quotes the tighter literature numbers back. |
| 9 | Steam quality meaning | 3 | Correct general explanation, but never states Baghewala's own confirmed 60–70% wellhead quality (BGW-8) — a real number sitting unused. **Rewritten below.** |
| 10 | CSS cycle energy balance | 4 | Solid, generic-but-correct, no factual exposure. |
| 11 | Why synthetic data is legitimate | 4 | Good, honest, appropriately distinguishes "plausible" from "validated." |
| 12 | Recalibration with real data | 4 | Concrete two-level (params + model) plan, credible. |
| 13 | Why XGBoost not deep learning | 4 | Standard, correct, well-argued for tabular data. |
| 14 | Bayesian optimization explained | 5 | Clean, technically precise, good exploration/exploitation framing. |
| 15 | Validation without ground truth | 5 | Best answer in the set — explicitly separates internal consistency from field validation. |
| 16 | Overfitting risk on synthetic data | 4 | Good mitigation list, honest about the real test being deferred. |
| 17 | Digital twin vs SCADA | 3 | Correct but generic — misses the chance to cite `landscape.md`'s finding that no commercial product does this integration (redundant with Q23 instead of reinforcing it here too). |
| 18 | Deployment path (OPC-UA/edge) | 4 | Concrete, realistic, appropriately scoped as "beyond prototype." |
| 19 | Who pays and why | 3 | Generic ROI narrative, no numbers — could cite the $15k-$50k workover figure or the fuel-cost derivation. |
| 20 | Rod-failure workover cost | **2** | The answer *actively avoids* using a number that exists and is sourced in your own research (`ppt_ammo.md` #12: $15,000–$50,000/event, TYPICAL, iFactory). Being cautious is good; not knowing your own research is not. **Rewritten below.** |
| 21 | Steam generation cost intuition | **2** | Purely generic textbook answer (fuel, water treatment, boiler capacity) when the team has actually *derived a real Baghewala-specific number* (~71 kg diesel/tonne steam, ~3.0 GJ/tonne, from BGW-8's own reported rates) sitting unused in `baghewala_facts.md` §4 and `ppt_ammo.md` #11. This is the single biggest missed opportunity in the whole viva doc — a judge-impressing, field-derived statistic, unused. **Rewritten below.** |
| 22 | Scale to other fields | 4 | Good, honest caveat about re-validation per field. |
| 23 | vs. commercial off-the-shelf (XSPOC/Lufkin) | 4 | Correctly names real competitors and gives an honest, non-overclaiming differentiation — matches `landscape.md`'s own research well. |
| 24 | Model limitations | 5 | Best "confident honesty" answer in the set — exactly what a judge wants to hear. |
| 25 | Pilot success criteria | 4 | Concrete, appropriately scoped, good closing answer. |

**Average score: 3.5/5.** No answer is flatly wrong except Q6, but roughly a third of the set (1, 7, 9, 19, 20, 21) reads as generic oil-and-gas-101 knowledge when the team has real, sourced, Baghewala-specific numbers sitting in `docs/research/` that would make the same answers dramatically stronger and harder to shake. That gap — not knowing your own research — is exactly what a domain-expert judge will probe for and find.

### Rewrites — 5 weakest answers

**Q6 rewrite (CSS depth limits) — was score 1, target 4+:**
> Steam loses heat as it travels down the wellbore, so deeper wells suffer higher bottomhole heat loss and lower effective steam quality — industry rule of thumb, CSS becomes markedly less efficient beyond roughly 1,000–1,500 m **(verify — order-of-magnitude industry threshold, not a Baghewala-specific study)**. Baghewala's Jodhpur Sandstone target actually sits at **~1,100–1,150 m** [CONFIRMED — Oil India, SPE-23APOG-535203], which puts it right at the edge of that efficiency window rather than comfortably inside it. That's not a weakness we're hiding — it's exactly why Oil India uses **vacuum-insulated tubing** at Baghewala (per Oil India's own field reports) to limit wellbore heat loss on the way down, and why OIL has separately trialed **downhole electric heaters** as a complement or alternative to CSS at this same depth. So depth is a real, actively-managed engineering challenge at this field, not a free advantage for us to claim — and it's precisely the kind of coupled wellbore-heat-loss effect our twin should eventually model explicitly (currently a stated limitation, not yet implemented).

**Q9 rewrite (steam quality) — was score 3, target 5:**
> Steam quality is the mass fraction of the injected steam that is actually vapor versus already-condensed liquid water — e.g., 65% quality means 65% vapor, 35% liquid by mass at that point. Vapor carries far more usable latent heat per unit mass, so quality is a direct measure of how much real heat is delivered. In Baghewala's own first CSS cycle at well BGW-8, **wellhead steam quality was confirmed at 60–70%** [OIL internal PPT], and bottomhole quality would be lower still after wellbore heat loss over ~1,150 m. That's exactly why our `field_params.json` sets `steam.quality = 0.65` — calibrated to Baghewala's own reported operating data, not a generic textbook default of 0.75–0.80.

**Q20 rewrite (workover cost) — was score 2, target 4:**
> There's no Baghewala-specific published number, but general industry literature on sucker-rod-pump failures gives a workover cost of roughly **$15,000–$50,000 per event** [TYPICAL — industry-general source, not Baghewala-specific], covering rig time, rod/tubing replacement, and lost production — and over half of SRP failures trace to metal-on-metal rod/tubing wear, which is exactly the failure mode our floating-index is built to flag before it happens. We're presenting this as an industry-typical range, clearly not a confirmed Baghewala figure, but it's a real, sourced order-of-magnitude anchor for the economic case rather than an unsupported guess.

**Q21 rewrite (steam generation cost intuition) — was score 2, target 5:**
> Generating steam requires fuel, treated feedwater, and boiler capacity — and fuel is normally the dominant, roughly-linear cost per tonne. We don't have to guess at this for Baghewala: OIL's own reported first-cycle numbers for well BGW-8 (~3,100 kg/hr steam from ~220 kg/hr of HSD diesel fuel) let us **derive real fuel intensity — about 71 kg diesel per tonne of steam, or roughly 3.0 GJ (~840 kWh) of fuel energy per tonne of steam generated**. That lines up well with generic industry figures for medium/high-pressure steam (2.5–3.6 GJ/tonne), which gives us confidence the field runs within a normal efficiency band — and it's exactly why every tonne of steam our optimizer saves is directly bankable fuel savings, not an abstract ratio improvement.

**Q1 rewrite (Andrade intuition) — was score 3, target 5:**
> Heavy crude is a tangle of long hydrocarbon chains and asphaltenes that resist sliding past each other. Andrade's law says viscosity follows mu = A·exp(B/T) — an exponential, because molecular flow is thermally activated, like a reaction needing to hop an energy barrier. At low T, few molecules have enough energy to make that jump, so resistance shoots up exponentially; the same temperature rise buys a much bigger viscosity drop near the cold end of the curve than near the hot end. Concretely, our research confirms Baghewala's Jodhpur Sandstone crude is **8,000–15,000 cP at 50°C** [CONFIRMED, SPE-23APOG-535203 / OIL internal data] — roughly **90–100x more viscous than a "typical" 18° API crude** at the same temperature, an outlier even among heavy oils, likely from high wax/asphaltene content. We fit our twin's Andrade constants (**A = 1.164×10⁻⁶, B = 7,436 K**) directly to this real 11,500-cP-at-50°C anchor point, not a generic textbook default — so the exponential curve our model actually runs on reflects Baghewala's real, unusually severe viscosity behavior.

---

## 4. MISSING KILLER MATERIAL — used vs. unused

Checked every sourced fact in `docs/research/landscape.md`, `docs/research/baghewala_facts.md`, and `docs/research/ppt_ammo.md` against every slide in `deck_content.md`. The deck currently uses almost none of the strongest available material. Five strongest unused facts, and exactly where each belongs:

1. **India's first CSS project — BGW-8, December 2018, with Calgary technical partner Belgrave Oil & Gas Corp.** (`ppt_ammo.md` #2, `baghewala_facts.md` §4). This is a genuine "first in India" hook and nowhere in the deck. → **Slide 1** (replace or supplement the weak 250 km killer number) or **Slide 4** (Feasibility — proves CSS is already proven technology at this exact field, de-risking the pitch).

2. **Competitive gap: no commercial product integrates CSS steam-cycle scheduling with sucker-rod-pump co-optimization** — the entire, well-researched finding of `docs/research/landscape.md` §2 and §5 (XSPOC, Lufkin SAM/SROD, Weatherford ForeSite, Schlumberger OptiSite, AVEVA, Kongsberg all checked and confirmed to not do this). This is the single strongest differentiation argument in the whole project and **is completely absent from the deck** — SIH judges score novelty heavily, and this is your best evidence of it. → Needs its own slide (insert after Slide 2, "Why This Doesn't Exist Yet / Competitive Landscape") or at minimum a headline bullet + named-competitor callout on **Slide 2**.

3. **218 t (FY2016-17) → 32,787 t (FY2024-25) → 43,773 t (FY2025-26)** — roughly 200x production growth since commercial CSS began (`baghewala_facts.md` §5, `ppt_ammo.md` #8). A dramatic, real, sourced growth curve that makes the field look like a live, scaling asset rather than a stagnant pilot. → **Slide 5** (Impact & Benefits) as an economic-context bar/line chart — "this is the trajectory our optimization accelerates further."

4. **5–6x production increase observed after Baghewala's own first CSS steam cycle** (`ppt_ammo.md` #6, `baghewala_facts.md` §4). Real, field-measured proof that thermal stimulation works dramatically at this specific field — stronger and more concrete than the generic "CSS is an established EOR technique" framing currently used. → **Slide 2** (Proposed Solution — justifies *why CSS specifically* pays off here) or **Slide 4** (Feasibility, as proof-of-concept evidence).

5. **52 wells drilled / 33 operational, 19 CSS'd in FY2025-26 alone (~72% YoY growth), record 1,202 bbl/d output (FY24)** (`baghewala_facts.md` §5). Concrete scale numbers that make Baghewala look like a real, growing, operationally significant program worth building a twin for — and directly replaces the unsourced "40+ CSS wells" line flagged in Finding 5. → **Slide 4** (Feasibility & Viability, replacing the current vague scale claim) and reinforces the **Slide 5** scalability bullet.

---

## 5. VERDICT

**MAYBE — leaning NO for any panel with a genuinely oil-and-gas-literate judge, as currently written.**

The technical architecture (physics layers → synthetic data → XGBoost → Bayesian optimizer) is sound and the viva prep's honesty discipline (verify-tags, trap-question answers, stated limitations) is genuinely above average for a student team — Q14, Q15, Q24 are judge-proof. But the deck currently: (a) states a headline number on slide 1 that is wrong by >2x and checkable in seconds, (b) presents an invented SOR baseline as fact on two slides, (c) explicitly claims the params file is "populated from Oil India data" when it verifiably is not, and (d) leaves the single best differentiation argument in all the research completely unused. Any one of these, surfaced by a sharp judge, undermines trust in every other number the team presents for the rest of the round — and there are four of them.

**Top 3 fixes, ranked by score impact:**

1. **Merge `docs/research/field_params_recommended.json` into `params/field_params.json` and re-run the pipeline.** This is the root cause (Section 0) behind nearly every contradiction in Sections 1 and 3 — one engineering fix (merge + regenerate synthetic data + retrain) cleans up the depth/API/viscosity/steam-temperature/injection-rate numbers everywhere at once, and makes Slide 4's "populated from Oil India data" claim actually true.
2. **Kill the two checkable-in-10-seconds wrong facts on the first two slides:** the 250 km distance (Finding 1) and the unsourced 4.5 t/m³ "current SOR" (Finding 2). These are the numbers most likely to be challenged first, because they're stated as simple facts with no hedge, and both are wrong or unsupported.
3. **Add the missing competitive-differentiation material** (Section 4, item 2) and swap in the "India's first CSS / 5–6x uplift / ~200x production growth" hooks (Section 4, items 1, 3, 4, 5) in place of the current weaker or wrong placeholder numbers — the deck is currently running on its second-best evidence while its best evidence sits unused in `docs/research/` and `docs/research/landscape.md`.
