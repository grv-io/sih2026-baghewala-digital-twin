# CSS & Thermal EOR — Deep Dive for SIH26120 (Baghewala Digital Twin)

**Who this is for:** the whole team. A 3rd-year Chemical Engineering student and CS teammates should be able to read this end-to-end and then hold a conversation with a petroleum engineer.

**How to read the citations:** every claim taken from outside is followed by `(Source: URL)`. Anything marked **[DERIVED]** is our own arithmetic from cited numbers — the assumptions are written out so a judge can check them.

---

## 1. CSS Fundamentals — what "huff and puff" actually is

### 1.1 The three-stage cycle

Cyclic Steam Stimulation (CSS) uses **one well** to do three jobs in sequence. It is also called "huff-and-puff" or "steam soak".

1. **Huff / Injection.** Steam is pumped down the well at high temperature — typically 300–340 °C — for a period of weeks. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
2. **Soak / Shut-in.** The well is closed. Heat spreads from the wellbore into the rock and oil by conduction. Classic soak periods are 2–7 days, though field practice varies widely. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
3. **Puff / Production.** The well is opened. Steam has condensed, the near-well oil is hot and thin, and it flows back with the condensed water. Production runs for up to about 6 months, then the cycle repeats. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)

At Imperial Oil's Cold Lake, the reference CSS operation in the world, typical first-cycle timings are: injection 4–6 weeks, soak 4–8 weeks, production 3–6 months — a total cycle of 6 to 18 months. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)

### 1.2 Why CSS beats primary recovery for heavy crude

For oil below roughly 20° API, primary (cold) production is weak. Published recovery factors for cold production of heavy oil sit around **8–12 % of original oil in place**, and other sources put primary heavy-oil recovery at 10–15 %. (Source: https://www.netl.doe.gov/sites/default/files/2018-05/BC15311_Final.pdf)

CSS works because of four stacked effects, but one dominates:

- **Viscosity collapse.** Heat is the lever. Viscosity reduction alone is credited with about **40 % of the oil recovered** in steam flooding. (Source: https://www.sciencedirect.com/topics/engineering/oil-viscosity)
- **Pressure re-charge.** Injecting steam raises near-well pressure, giving drive energy for the first weeks of the puff phase. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
- **Thermal expansion and gravity drainage** of the heated oil.
- **Wellbore clean-up** — heat dissolves wax and asphaltene deposits near the perforations.

Theoretically, huff-and-puff produces around **20–25 % of the initial oil-in-place**, and published recovery factors for CSS are quoted as **20–35 %**. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation) One operator-side source claims CSS in Alberta recovers about 50 % of oil in place over a well's full life. (Source: https://www.oilsandsmagazine.com/news/2024/10/24/sagd-vs-css-thermal-in-situ-recovery-differences)

So CSS roughly **doubles to triples** what cold production would have given. That is the whole business case.

### 1.3 When CSS stops paying — declining cycle efficiency

This is the single most important idea for our digital twin.

Each cycle heats a bigger but colder region. The near-well oil that was easy to mobilise is already gone. Published field behaviour:

- **Peak oil rates typically occur in cycles 2 and 3, then fall sharply through cycles 4 to 6.** (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
- The number of cycles that stays economic is generally **not more than about 10** per well by one guideline (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation); operator data from Alberta reports **10 to 20 cycles over a well's lifetime**. (Source: https://www.oilsandsmagazine.com/news/2024/10/24/sagd-vs-css-thermal-in-situ-recovery-differences)
- Late-life CSS symptoms are textbook: **high water cut, low oil-gas ratio, "invalid" thermal cycles, low oil rate, high cost**. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)

The key performance index is the **Oil-Steam Ratio (OSR)** — barrels (or m³) of oil produced per unit of water injected as steam, measured at standard conditions. SOR is its inverse. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation) A cycle stops paying when the value of the incremental oil no longer covers the fuel, water and workover cost of the steam. **Our twin's job is to predict that crossing point before the operator spends the steam.**

### 1.4 CSS vs Steamflood vs SAGD — the decision logic

| | **CSS (huff & puff)** | **Steamflood (steam drive)** | **SAGD** |
|---|---|---|---|
| Wells | One well does both jobs | Separate injectors + producers | Horizontal well *pair* |
| Typical depth | ~400–500 m in Alberta practice | Shallow (<300 m at Duri) | ~100–500 m |
| Permeability needed | Works in **low**-perm, poor vertical flow | High perm | Good perm, unconsolidated |
| Steam pressure | High — often slightly above fracture pressure | Moderate | Low |
| Life-cycle SOR | ~**6.0** average | ~4–6 (Kern River) | ~**3.5** in permeable pay |
| Recovery factor | 20–35 % (up to ~50 % claimed) | Up to **51–55 %** at Duri | **>80 %** in good cases |

(Sources: https://www.oilsandsmagazine.com/news/2024/10/24/sagd-vs-css-thermal-in-situ-recovery-differences ; https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation ; https://ccreservoirs.com/duri-field-an-ideal-analogue-for-steamflooding/ ; http://theoildrum.com/node/5023)

**Plain-English decision rule.** If the rock has poor vertical flow and you cannot rely on steam travelling well-to-well, you cannot run a flood — you must heat around each well individually, so you pick CSS. If the sand is thick, shallow and permeable, a steamflood or SAGD sweeps far more oil. Duri needs **>50 ft (≈15 m) net pay minimum** to be economic as a steamflood, and >100 ft for inverted 9-spot patterns. (Source: https://ccreservoirs.com/duri-field-an-ideal-analogue-for-steamflooding/) Baghewala's thin, sub-10 %-porosity Jodhpur sandstone at ~1,100 m is squarely CSS territory, and CSS is in fact what OIL chose.

A common industrial path is CSS first (to heat and de-pressure the near-well region), then convert to steamflood once neighbouring heated zones start to overlap. (Source: https://www.researchgate.net/publication/346334099_Combination_of_Cyclic_Steam_Stimulation_and_Steam_Flooding_to_Improve_Oil_Recovery_in_Unconsolidated_Sand_Heavy_Oil_Reservoir)

---

## 2. The Physics That Drives Optimization

### 2.1 Marx–Langenheim (1959) — the heated-area workhorse

Marx and Langenheim built a front-propagation model relating the **growth of the steam zone** to the **rate of heat loss into the cap rock and base rock** above and below the pay. (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)

**What it predicts.** Given a constant steam injection rate and temperature, it gives you the cumulative heated area (and hence heated volume) as a function of time, plus a *thermal efficiency* — the fraction of injected heat still inside the pay zone. The solution is built around a complementary error function `erfc` evaluated at a dimensionless time `tD` that depends on pay thickness, reservoir heat capacity, and the thermal diffusivity of the surrounding rock. (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)

Its great strength: it places **no restriction on the geometry or direction of growth** of the heated area, so it works for linear drive, five-spot, seven-spot — or a radial CSS bubble around one well. (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)

**Its assumptions (and therefore its limits):**

- The steam zone is a **sharp step** in temperature — hot inside, cold outside, nothing in between. Real reservoirs have a smeared front. (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)
- **Constant steam-zone thickness**, which experiments show is not realistic. (Source: https://doi.org/10.3390/en15134816)
- **Equal heat-loss rates to overburden and underburden.** (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)
- **Constant injection rate**, and no heat flux across the front — realistic only while latent heat from condensing steam is enough to cover all losses. (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)
- **No gravity override.** In reality steam rises to the top of the pay, which is why later models add an override term. (Source: https://ogst.ifpenergiesnouvelles.fr/articles/ogst/full_html/2017/01/ogst160087/ogst160087.html)
- **Time validity.** The front advance matches Marx–Langenheim well *early*, at sufficiently high injection rates, and deviates at long times — a formal criterion exists for how long it is valid. (Source: https://www.osti.gov/biblio/6523884-marx-langenheim-sup-model-steam-injection)

### 2.2 Boberg–Lantz (1966) — the CSS-specific model we should actually build

Marx–Langenheim gives the heated *volume*. Boberg and Lantz turned that into a **producing-well forecast**, and it is the first analytical model of cyclic steam injection for a vertical well; its steam-zone radius comes straight out of Marx–Langenheim. (Source: https://www.sciencedirect.com/science/article/pii/S2405656118301755)

It computes an **average temperature of the heated zone** that decays through the production phase, using dimensionless functions for horizontal conduction loss to the cold reservoir (`fHD`) and vertical loss to the surroundings (`fVD`). That average temperature gives a new viscosity → a new productivity index → a new oil rate. (Source: https://www.upcoglobal.com/resources/technical-papers/artificial-lift-performance-coupled-with-boberg-lantz-model-for-a-better-prediction-of-cyclic-steam-injection-wells)

Two documented weaknesses matter for us: it assumes the **heated radius is constant**, and the gap between its temperature prediction and a full numerical simulator can reach **42 % over 300 days of steam injection**. (Source: https://www.sciencedirect.com/science/article/pii/S2405656118301755) That gap is exactly the space where an ML correction layer earns its place.

### 2.3 Heat losses — where the steam energy actually goes

**Wellbore losses (surface to sand face).** Ramey's classic treatment assumes steady-state heat transfer inside the wellbore and unsteady radial conduction into the formation. (Source: https://onepetro.org/JPT/article/17/07/845/162458/Heat-Losses-During-Flow-of-Steam-Down-a-Wellbore) Numbers that matter:

- Ramey's method predicted **45 % heat loss at 4,000 ft**; a newer model including cement-sheath effects and steam quality change predicts **31 %**. (Source: https://www.academia.edu/73339013/Wellbore_Heat_Losses_and_Pressure_Drop_In_Steam_Injection)
- Losses through **uninsulated casing can exceed 25 % of the energy input.** (Source: https://www.academia.edu/73339013/Wellbore_Heat_Losses_and_Pressure_Drop_In_Steam_Injection)
- Tubing insulation can reduce heat loss up to **100 % more effectively than aluminium paint**, which itself gives 40–50 %. (Source: https://www.academia.edu/73339013/Wellbore_Heat_Losses_and_Pressure_Drop_In_Steam_Injection)

This is not academic for Baghewala: at ~1,100 m depth, wellbore loss is a first-order term, and OIL already runs **vacuum-insulated tubing (VIT)** for exactly this reason. (Source: https://www.oil-india.com/rajasthan-fields)

**Cap-rock losses (in the reservoir).** These are what Marx–Langenheim models. They scale with the *area* of the heated zone and with the *time* it is hot — which is precisely why an infinitely long soak is a bad idea.

### 2.4 Steam quality — the hidden variable

Steam quality `x` is the mass fraction that is actually vapour. It matters because **latent heat is the payload**: at 300 °C, latent heat is roughly 1,400 kJ/kg while sensible heat above reservoir temperature is much smaller. Cut quality in half and you cut delivered energy roughly in half at the same tonnage.

- High injection pressures give **lower latent heat**, which makes heating less effective — a real trade-off, because high pressure is what gets steam into a low-permeability sand. (Source: https://link.springer.com/article/10.1007/s13202-025-02052-1)
- Quality degrades badly down the hole. One study reports VIT giving the best results, delivering downhole quality of **20–40 % from an 80 % wellhead quality** at 200 m³ CWE/day. (Source: https://www.sciencedirect.com/science/article/pii/S0920410513002477)

Baghewala's reported wellhead quality is **60–70 %** — so downhole quality is a genuinely uncertain, high-leverage number, and a good candidate for the twin to *infer* rather than assume.

### 2.5 Why there is an optimal steam slug size and soak time

This is the marginal-heat-versus-marginal-oil argument. Say it exactly like this to a judge:

- **Marginal oil per extra tonne of steam falls.** Heated volume in a radial geometry grows roughly with the heated *area*, so radius grows like √(volume). Each extra tonne pushes the front a smaller distance, and the oil it mobilises is a shrinking annulus of oil that is farther from the well and harder to lift.
- **Marginal heat loss per extra tonne rises.** Cap-rock loss is proportional to heated area × time hot (Marx–Langenheim). A bigger, longer-lived hot zone loses a bigger absolute amount of heat upward and downward.
- Cross the two curves and you get a finite optimum. Injecting past it *raises* SOR while adding almost no oil.

The same logic applies to soak time:

- **Too short:** steam has not condensed and the heat is still in a narrow ring near the wellbore; you produce back hot water and steam rather than oil, and you waste latent heat.
- **Too long:** the heat you paid for keeps bleeding into cap rock while the well makes zero revenue, and near-well pressure — a real part of the drive — decays.

Published field practice brackets it: steam injected at the highest practical rate for **10 to 60 days**, then shut in to soak for **two days to a week**, depending on reservoir conditions. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation) Baghewala runs 14–21 day injection with a soak equal to 50–60 % of the injection length — i.e. roughly 7–13 days, notably longer than the generic 2–7 day guideline. That is a legitimate question our twin can put a number on.

The full list of levers an optimizer can pull is, from the literature: **steam volume, injection rate, injection intensity, soak time, production time, bottomhole flowing pressure, minimum oil rate to end a cycle, percent change in slug size for the next cycle, steam quality, steam temperature, injection pressure and cycle length.** (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)

### 2.6 Viscosity vs temperature — the ASTM D341 / Walther law

The industry standard relationship is the **Walther equation**, which underlies the ASTM D341 viscosity–temperature charts:

`log₁₀(log₁₀(ν + 0.6)) = A − B · log₁₀(T)`

where ν is kinematic viscosity in cSt and T is absolute temperature. Two measured points fix A and B, and you interpolate everything else. (Source: https://industrialmonitordirect.com/blogs/knowledgebase/oil-viscosity-temperature-equation-fitting-for-industrial-applications ; standard: https://www.astm.org/Standards/D341.htm) The double-log form is what makes a viscosity chart plot as a straight line — that is the whole trick.

The simpler **Andrade** form, `μ = A·exp(B/T)`, is a one-exponential approximation that is fine over a narrow window but under-predicts the collapse over the 50 → 300 °C span CSS actually covers.

**Scale of the effect.** A CSI field study reports temperature swinging from **580 °F to 130 °F (≈304 °C to 54 °C) across a cycle, with viscosity moving from 5 cP to 600 cP** — a 120× change from the same rock, same oil, just cooling down. (Source: https://www.upcoglobal.com/resources/technical-papers/artificial-lift-performance-coupled-with-boberg-lantz-model-for-a-better-prediction-of-cyclic-steam-injection-wells)

**Baghewala caution.** Baghewala crude is anomalously viscous for its API: 8,000–15,000 cP at 50 °C at 14–17° API, where a *generic* 18° API crude is only ~120 cP at 50 °C. Do **not** use an API-gravity correlation for this oil; fit Walther through the field's own measured points. (Prior team research file: `docs/research/baghewala_facts.md`, sourced to SPE-23APOG-535203 and https://www.engineeringtoolbox.com/crude-oil-petroleum-viscosity-gravity-density-d_1959.html)

---

## 3. World CSS Benchmarks — numbers you can quote

### Cold Lake, Alberta (Imperial Oil) — the CSS reference case
- CSS was **developed by Imperial at Cold Lake in the late 1950s and commercialised by 1985**. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
- **2024 full-year production: 148,000 bbl/d**, with Q4 2024 at 157,000 boe/d. (Source: https://news.imperialoil.ca/news-releases/news-releases/2025/Imperial-announces-fourth-quarter-2024-financial-and-operating-results/default.aspx)
- **SOR ≈ 4** on the first four Cold Lake properties; the Nabiye phase averaged **just over 6** in 2018. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
- Cycle structure: injection 4–6 weeks, soak 4–8 weeks, production 3–6 months; **6–18 months per cycle**, 10–20 cycles per well. (Sources: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation ; https://www.oilsandsmagazine.com/news/2024/10/24/sagd-vs-css-thermal-in-situ-recovery-differences)
- Imperial's newer Grand Rapids project reached **15,000 bbl/d of "GHG-advantaged" volumes, cutting emissions intensity up to 40 %** versus existing technology. (Source: https://news.imperialoil.ca/news-releases/news-releases/2024/Imperial-achieves-first-oil-production-from-Grand-Rapids-project-using-lower-emission-technology/default.aspx)

### Duri, Indonesia (Chevron/Pertamina) — the steamflood benchmark
- **World's largest thermal EOR project.** Primary recovery was forecast at only **9 % of STOIIP**; steamflood added an **incremental 51 %**, taking ultimate recovery to about **55 %** and adding roughly **2.5 billion barrels**. (Sources: https://ccreservoirs.com/duri-field-an-ideal-analogue-for-steamflooding/ ; https://www.ipa.or.id/en/publications/a-review-of-steamflooding-in-duri-field-sumatra)
- Production went from **44,000 BOPD in 1967 to about 300,000 BOPD within ten years** of steamflooding; still nearly 200,000 BOPD. (Source: https://ccreservoirs.com/duri-field-an-ideal-analogue-for-steamflooding/)
- Reservoir: **<770 ft depth, 34 % porosity, 1,335 mD, viscosity only 150 cP**, cut up to 95 % by heating. **Cumulative fuel/oil ratio 0.21.** (Sources: https://ccreservoirs.com/duri-field-an-ideal-analogue-for-steamflooding/ ; https://www.ipa.or.id/en/publications/a-review-of-steamflooding-in-duri-field-sumatra)
- Note how *easy* Duri is compared to Baghewala: 30× shallower-viscosity oil, 3.4× the porosity. Duri is the ceiling, not the comparison.

### Liaohe, China — the mature-CSS cautionary tale
- Block D was developed by CSS from 1997. After nearly 20 years, **reservoir pressure fell from 7.4 MPa to 2.9 MPa and SOR rose from 2.86 to 3.56.** (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/18HOCE/18HOCE/D021S009R002/214695)
- CO₂-assisted CSS pushed injection pressure from 5.7 to 6.9 MPa and **brought SOR back down from 3.45 to 2.86.** (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/18HOCE/18HOCE/D021S009R002/214695)
- This is the clearest published example of SOR *drifting upward* with depletion — the exact degradation our twin should track.

### Venezuela — Bolívar Coast (Tía Juana, Bachaquero, Lagunillas) and Boscán
- CSS was the most-applied method, with **oil-steam ratio ranging 1.5 to 6.8** across projects — i.e. SOR from about 0.15 to 0.67 in OSR terms, or roughly 1.5 to 6.8 barrels of oil per barrel of steam depending on the reporting convention used. (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/11HOCE/All-11HOCE/SPE-150283-MS/150828)
- Bolívar Coast fields: **11–15° API, 100–10,000 cP, 1,000–3,000 ft depth, 50–300 ft sand thickness.** (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/11HOCE/All-11HOCE/SPE-150283-MS/150828)
- **Boscán: 10.5° API, ~8,000 ft deep, OOIP >20 billion STB**, depleted-area pressure ~800 psi. (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/11HOCE/All-11HOCE/SPE-150283-MS/150828)
- Orinoco Belt: **8–9° API, ~8,500 cP, ~2,900 ft, 217–287 ft thick.** (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/11HOCE/All-11HOCE/SPE-150283-MS/150828)

### Where Baghewala sits

| Metric | Baghewala (OIL) | Cold Lake | Duri | Liaohe D | Bolívar Coast |
|---|---|---|---|---|---|
| API | 14–17° | ~10° bitumen | ~21° | heavy | 11–15° |
| Viscosity @50 °C | **8,000–15,000 cP** | ~100,000+ cP | 150 cP | heavy | 100–10,000 cP |
| Depth | **~1,100 m** | ~400–500 m | <235 m | — | 300–900 m |
| Porosity | **<10 %** | 30 %+ | 34 % | — | — |
| Steam T | **280–305 °C** | 300–340 °C typical | — | — | — |
| Steam quality | **60–70 %** | ~80 % typical | — | — | — |
| Reported SOR | **not published** | ~4 (up to 6) | fuel/oil 0.21 | 2.86 → 3.56 | OSR 1.5–6.8 |
| Field rate | **~655 bbl/d (Jul-2025); 1,202 bbl/d (2026)** | 148,000 bbl/d | ~200,000 bbl/d | — | — |

(Baghewala row from prior team research file `docs/research/baghewala_facts.md`; field rate from https://psuwatch.com/newsupdates/oil-india-ramps-up-crude-production-from-rajasthans-thar-desert and https://www.slideshare.net/slideshow/baghewala-ppt-oil-india-limited-12-07-2025-pptx/282258575. Other columns cited above.)

**Read of the table.** Baghewala is a *hard* CSS case: deeper than Cold Lake, far tighter than Duri, with lower steam quality than typical practice. On the other hand, the reported **5–6× first-cycle uplift** (Source: https://www.scribd.com/document/444099090/CSS-Implementation-Baghewala-Rajasthan-Project) is a strong early-cycle result, consistent with world experience that cycles 1–3 are the good ones. **74 tpd of steam is a small, precious resource** — Cold Lake runs orders of magnitude more — which makes allocation optimisation (which well gets the next slug) more valuable here than almost anywhere.

**[DERIVED] What 74 tpd of steam is worth.** At SOR = 5 t steam/t oil, 74 t/d of steam supports ~14.8 t/d of oil ≈ **96 bbl/d**. At SOR = 3 it supports ~160 bbl/d. Against a field making ~655 bbl/d, that says: *a one-unit improvement in SOR on the steamed wells is worth roughly 10 % of field production.* (Assumes 15° API → SG 0.966 → 6.5 bbl per tonne.)

---

## 4. CSS Optimization Literature — six papers worth citing

**1. Boberg, T.C. & Lantz, R.B. (1966), "Calculation of the Production Rate of a Thermally Stimulated Well", JPT.**
The first analytical CSS model for a vertical well; steam-zone radius from Marx–Langenheim, then an average heated-zone temperature that decays via `fHD`/`fVD` conduction functions to give viscosity → PI → rate. Still the industry-accepted analytical baseline. (Source: https://www.sciencedirect.com/science/article/pii/S2405656118301755)
*Takeaway for us:* this is the cheapest defensible physics core for a real-time twin — milliseconds, not hours.

**2. "Temperature profile estimation: a study on the Boberg and Lantz steam stimulation model", *Petroleum* (Elsevier), 2018.**
Benchmarks Boberg–Lantz against numerical solutions and finds the temperature-prediction gap can reach **42 % over 300 days**. (Source: https://www.sciencedirect.com/science/article/pii/S2405656118301755)
*Takeaway:* quantifies exactly how much error an ML residual model has to absorb — a ready-made justification for hybrid physics+ML.

**3. UPC Global, "Artificial Lift Performance Coupled with Boberg & Lantz Model for Better Prediction of Cyclic Steam Injection Wells" (2021).**
Couples Boberg–Lantz with **nodal analysis** — instead of assuming constant bottomhole flowing pressure, it builds outflow curves across the viscosity range and intersects them with IPR curves. Four case studies; for **deep horizontal wells, sucker-rod pumping dominated**, and reservoir inflow potential exceeded what the lift could take. (Source: https://www.upcoglobal.com/resources/technical-papers/artificial-lift-performance-coupled-with-boberg-lantz-model-for-a-better-prediction-of-cyclic-steam-injection-wells)
*Takeaway:* this is our exact problem statement — CSS **plus** sucker-rod pumps — and it proves the lift system, not the reservoir, is often the binding constraint. Strongest single paper for SIH26120.

**4. SPE-185716-MS (SPE Western Regional 2017), "Cyclic Steam Injection Modeling and Optimization for Candidate Selection, Steam Volume Optimization, and SOR Minimization".**
Fast modelling + data-assimilation algorithms applied to mature heavy-oil fields; reports **steam savings, production increases and SOR reduction in excess of 20 %.** (Source: https://onepetro.org/SPEWRM/proceedings-abstract/17WRM/17WRM/D031S003R001/196053)
*Takeaway:* gives us a defensible, published target number for what optimisation is worth — >20 % SOR reduction.

**5. SPE-195307-PA (SPE Reservoir Evaluation & Engineering, 2020), "Artificial Neural Network Modeling of Cyclic Steam Injection Process in Naturally Fractured Reservoirs".**
Trains three ANN surrogate models for fast CSI performance evaluation, explicitly as an answer to commercial simulators being slow, costly and hard to learn; uses a network-topology optimisation workflow during training. (Source: https://onepetro.org/journal-paper/SPE-195307-PA)
*Takeaway:* peer-reviewed precedent that ANN surrogates are an accepted substitute for full simulation in CSS.

**6. "A Simulation Augmented Machine Learning Approach for Cyclic Steam Stimulation Development Targeting Lower Carbon / Higher Return", SPE Western Regional 2022 (SPE-209284 series).**
Uses simulation to generate training data, then ML to steer CSS development for both **carbon** and **return** objectives simultaneously. (Source: https://onepetro.org/SPEWRM/proceedings-abstract/22WRM/22WRM/D031S014R004/484171)
*Takeaway:* validates our dual objective — SOR/₹ **and** CO₂ — as a live research direction, not a bolt-on.

**Also worth knowing:**
- **Proxy/response-surface approach:** quadratic multivariate regression proxies for steam huff-and-puff, with parametric screening to pick the impactful inputs. (Source: https://www.mdpi.com/2076-3417/12/6/3169)
- **Metaheuristics:** particle-swarm optimisation applied to CSS in an offshore heavy-oil reservoir (Source: https://arxiv.org/pdf/1306.4092), and a **PSO-optimised neural network** for horizontal CSS well production prediction (Source: https://doi.org/10.3390/app13042540).
- **Deployed AI in the field:** an ANN-based candidate-review tool replaced a manual engineer-by-engineer review and, combined with Power BI visualisation, **delivered 5,800 BOPD from a CSS campaign in the Krakatau field** while shortening review cycle time and improving job success ratio. (Source: https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/23APOG/D031S027R002/535350)
- **Geomechanics coupling:** SPE-176716-MS optimises CSS under geomechanics-dependent permeability — relevant because CSS injects **above fracture pressure**. (Source: https://www.academia.edu/30725101/SPE_176716_MS_Optimization_of_Cyclic_Steam_Stimulation_CSS_Under_Geomechanics_Dependent_Permeability)

**The gap we fill:** almost all of the above are offline studies or candidate-screening tools. Very few close the loop as a **live twin** that ingests daily field data, re-estimates state, and recommends the next cycle's slug and soak — and none published for an Indian field with diesel-fired steam and rod-pump lift.

---

## 5. Economics — why SOR is the only number that matters

### 5.1 Steam generation cost drivers

Cost of steam = **fuel + water treatment + capital/maintenance**, and fuel dominates. The standard formula depends on fuel type, unit fuel cost, boiler efficiency, feedwater temperature and steam pressure, plus accessories: feedwater pumps, fans, fuel heaters, atomising steam, soot blowing, treatment chemicals and maintenance. (Source: https://www.campbell-sevey.com/steam-tip-15-benchmark-the-fuel-cost-of-steam-generation/)

Physical anchor: producing steam takes roughly **2.6–4.0 GJ per tonne** depending on pressure and boiler efficiency. (Source: https://thundersaidenergy.com/downloads/energy-needed-to-produce-steam-enthalpy-and-entropy-data/)

**Baghewala's own fuel intensity [DERIVED]:** 220 kg HSD per hour to make 3,100 kg/h of steam = **71 kg diesel per tonne of steam**. At a diesel LHV of 42.6 MJ/kg that is **~3.0 GJ/tonne** — squarely inside the published band, which is a good sanity check on the source deck. (Base numbers from `docs/research/baghewala_facts.md`, sourced to the OIL operations deck: https://www.slideshare.net/slideshow/baghewala-ppt-oil-india-limited-12-07-2025-pptx/282258575)

**Water treatment.** Feedwater must be essentially free of hardness (Ca, Mg) or the generator tubes and the formation scale up; silica is a second scaling risk. Once-through steam generators (OTSGs) are used in EOR precisely because they tolerate poorer feedwater than packaged boilers — at the cost of never reaching 100 % quality and always needing a high-pressure blowdown stream. (Source: https://www.eurowater.com/en/industrial-steam-boilers) Typical treatment train: de-oiling → softener → filtration → organic trap.

### 5.2 SOR → opex per barrel

**Fuel cost of a tonne of steam [DERIVED].** 71 kg diesel/t ÷ 0.83 kg/L ≈ **86 litres of diesel per tonne of steam**. At the Rajasthan retail rate of about ₹97.8/L (Aug 2026) that is **≈ ₹8,400 (~US$95) per tonne of steam** — an upper bound, since a bulk industrial buyer pays less than pump price. (Diesel price source: https://www.goodreturns.in/diesel-price-in-rajasthan-s28.html)

**Cost per barrel of oil at different SOR [DERIVED]** (15° API → 6.5 bbl/t oil):

| SOR (t steam / t oil) | Steam fuel cost per barrel of oil |
|---|---|
| 2 | ~₹2,580 (~US$29/bbl) |
| 3 | ~₹3,880 (~US$44/bbl) |
| 5 | ~₹6,460 (~US$73/bbl) |
| 8 | ~₹10,340 (~US$117/bbl) |

This is the whole argument in one table: **at diesel prices, CSS goes from profitable to loss-making somewhere between SOR 3 and SOR 5.** Getting SOR down by one unit is worth roughly US$15/bbl.

**Cross-check against published figures.** Steam cost is quoted as rising to **US$20–30 per barrel of incremental oil recovered when natural gas is the fuel** (Source: http://theoildrum.com/node/5023) — and gas is far cheaper per GJ than diesel, so our diesel-based numbers sitting well above that band is exactly what you'd expect. Kern River needs **4.2 barrels of steam per barrel of oil at 350 psi**, with steamflood generally at 4–6. (Source: http://theoildrum.com/node/5023) Santa Fe Energy's Kern River redevelopment cut operating cost **from over US$8/bbl to about US$4/bbl** — proof that operating-practice optimisation, not new hardware, moved the number. (Source: https://www.ogj.com/home/article/17217319/kern-river-steam-flood-doubles-oil-production)

**[DERIVED] the fuel-switch finding.** At 3.0 GJ/tonne of steam and natural gas at US$4/MMBtu (≈US$3.79/GJ), fuel cost would be **~US$11 per tonne of steam** versus ~US$95 for diesel — roughly **8× cheaper**. Low-cost gas, often under $4/mcf, is what made gas the default EOR steam fuel elsewhere. (Source: https://personal.ems.psu.edu/~radovic/Chaar_OilGasFacil_2015.pdf) Any Baghewala economics slide should flag fuel switching as the single biggest cost lever, with SOR optimisation as the second.

### 5.3 CO₂ intensity — why SOR reduction *is* the emissions story

- Steam generation is **the largest source of carbon emissions in in-situ thermal recovery**. (Source: https://www.cer-rec.gc.ca/en/data-analysis/energy-markets/market-snapshots/2023/market-snapshot-trends-in-situ-bitumen-production.html)
- **Steam-oil ratio explains about 60 % of the variance in SAGD assets' emissions.** (Source: https://thundersaidenergy.com/downloads/oil-sands-co2-intensity/) That one sentence is the entire justification for treating SOR as a carbon KPI.
- Oil sands Scope 1&2 intensity is around **185 kg CO₂/bbl**, against an industry average near **60 kg CO₂/bbl**. (Source: https://thundersaidenergy.com/downloads/oil-sands-co2-intensity/)
- About **1.7 GJ of natural gas makes 1 m³ of steam and about 150 kg of CO₂.** (Source: https://thundersaidenergy.com/downloads/oil-sands-co2-intensity/)

**[DERIVED] Baghewala's carbon number.** Diesel's IPCC default emission factor is **74.1 kg CO₂/GJ** versus **56.1 kg CO₂/GJ** for natural gas. (Source: https://greencalculus.com/data/ipcc-fuel-combustion-factors/) At 3.0 GJ/tonne of steam:
- Diesel-fired: **~222 kg CO₂ per tonne of steam.** At SOR 5 that is ~1,110 kg CO₂ per tonne of oil = **~171 kg CO₂/bbl** — right on top of the published oil-sands figure of 185 kg/bbl, which is a strong independent validation of our arithmetic.
- At SOR 3 it falls to **~102 kg CO₂/bbl**; switching to gas as well takes it to **~78 kg CO₂/bbl**.

So: **cutting SOR from 5 to 3 cuts both cost and CO₂ per barrel by ~40 %.** The economics slide and the sustainability slide are the same slide.

---

## 6. Ammunition Box

### 15 quotable facts

1. Cold Lake's first four properties run at **SOR ≈ 4**; Nabiye averaged **just over 6** in 2018. (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
2. CSS life-cycle SOR averages about **6.0**; SAGD about **3.5** in permeable pay. (Source: https://www.oilsandsmagazine.com/news/2024/10/24/sagd-vs-css-thermal-in-situ-recovery-differences)
3. CSS recovery factors are **20–35 %** of OOIP versus **8–12 %** for cold production. (Sources: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation ; https://www.netl.doe.gov/sites/default/files/2018-05/BC15311_Final.pdf)
4. **Peak CSS oil rates come in cycles 2–3 and fall sharply through cycles 4–6.** (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation)
5. Wells run **10–20 CSS cycles** over a lifetime in Alberta practice. (Source: https://www.oilsandsmagazine.com/news/2024/10/24/sagd-vs-css-thermal-in-situ-recovery-differences)
6. Uninsulated casing can lose **>25 % of injected heat** in the wellbore; Ramey's model gives **45 % at 4,000 ft**, refined models **31 %**. (Source: https://www.academia.edu/73339013/Wellbore_Heat_Losses_and_Pressure_Drop_In_Steam_Injection)
7. Even with VIT, downhole steam quality can be **20–40 % from an 80 % wellhead quality**. (Source: https://www.sciencedirect.com/science/article/pii/S0920410513002477)
8. Duri: primary recovery **9 %** of STOIIP; steamflood added **51 %** incremental, ~2.5 billion barrels. (Source: https://ccreservoirs.com/duri-field-an-ideal-analogue-for-steamflooding/)
9. Liaohe Block D: after ~20 years of CSS, pressure fell 7.4 → 2.9 MPa and **SOR rose 2.86 → 3.56**; CO₂-assisted CSS pulled it back to 2.86. (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/18HOCE/18HOCE/D021S009R002/214695)
10. Venezuelan CSS projects reported **oil-steam ratios spanning 1.5 to 6.8**. (Source: https://onepetro.org/SPEHOCE/proceedings-abstract/11HOCE/All-11HOCE/SPE-150283-MS/150828)
11. Published CSS optimisation with fast modelling + data assimilation delivered **>20 % SOR reduction** in mature fields. (Source: https://onepetro.org/SPEWRM/proceedings-abstract/17WRM/17WRM/D031S003R001/196053)
12. An AI candidate-selection tool delivered **5,800 BOPD from a CSS campaign in the Krakatau field**. (Source: https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/23APOG/D031S027R002/535350)
13. **SOR explains ~60 % of the variance in SAGD emissions**; oil sands Scope 1&2 intensity is ~185 kg CO₂/bbl vs a ~60 kg/bbl industry average. (Source: https://thundersaidenergy.com/downloads/oil-sands-co2-intensity/)
14. Boberg–Lantz temperature predictions can differ from numerical simulation by up to **42 % over 300 days**. (Source: https://www.sciencedirect.com/science/article/pii/S2405656118301755)
15. Kern River redevelopment cut opex **from >$8/bbl to ~$4/bbl** through operating practice. (Source: https://www.ogj.com/home/article/17217319/kern-river-steam-flood-doubles-oil-production)

### 5 hard questions a petroleum engineer will ask

**Q1. "Marx–Langenheim assumes a sharp temperature front, constant steam-zone thickness and constant injection rate. None of that holds at Baghewala. Why is your twin not garbage?"**
Correct on all three, and we don't claim otherwise. We use Marx–Langenheim only for the **heated-volume envelope** and Boberg–Lantz for the **average heated-zone temperature**, because those give us a fast, physically-consistent state that is right in *structure* even when it is wrong in *magnitude*. The published Boberg–Lantz error against numerical solutions reaches 42 % over 300 days (Source: https://www.sciencedirect.com/science/article/pii/S2405656118301755) — so we treat that residual as a learnable quantity and fit it against actual cycle history. Physics gives the shape; data corrects the scale. We also report an uncertainty band, never a single number.

**Q2. "You have 74 tpd of steam and 33 producing wells. Why is a longer soak better than more steam?"**
Because they cost different things. Extra steam costs fuel (~₹8,400/tonne at diesel prices, **[DERIVED]** above); extra soak costs only deferred production. Marx–Langenheim says cap-rock heat loss scales with heated area × time hot, so beyond an optimum the extra soak burns heat for no oil — but before that optimum, soak is nearly free conductive spreading of heat you have already bought. The practical evidence that this is a real tuning knob: generic guidance is a 2–7 day soak (Source: https://www.sciencedirect.com/topics/engineering/cyclic-steam-stimulation) while Baghewala runs 7–13 days. One of those is wrong for this reservoir, and it is a question a twin can answer with numbers.

**Q3. "CSS injects above fracture pressure. Do you model geomechanics at all?"**
Not from first principles — that needs a coupled geomechanical simulator, and SPE-176716-MS shows permeability in CSS is genuinely geomechanics-dependent. (Source: https://www.academia.edu/30725101/SPE_176716_MS_Optimization_of_Cyclic_Steam_Stimulation_CSS_Under_Geomechanics_Dependent_Permeability) What we do instead is treat effective near-well permeability as a **state variable re-estimated each cycle from observed injectivity and productivity**. If a cycle fractures the rock and injectivity jumps, the twin sees it in the data and updates. That is honest about the limit, and it is how the change actually shows up in operations.

**Q4. "Your oil is 14–17° API but 10,000+ cP at 50 °C. Any correlation you pull off the shelf will be wrong by two orders of magnitude."**
Agreed, and that is exactly why we don't use one. A generic 18° API crude is around 120 cP at 50 °C, roughly 100× thinner than Baghewala's oil — a wax/asphaltene effect, not a density effect. We fit the **ASTM D341 / Walther double-log law** (`log log(ν+0.6) = A − B log T`) through the field's own measured viscosity points and extrapolate only within the range CSS actually spans. (Standard: https://www.astm.org/Standards/D341.htm)

**Q5. "SOR is a lagging indicator — by the time you know it, the steam is spent. What does your twin give an operator on Monday morning?"**
Three things. (a) A **forward** SOR forecast for the *proposed* next slug, not the last one, so the decision is made before the money is spent. (b) A **ranked allocation** of the day's 74 tpd across candidate wells — this matters more here than at Cold Lake precisely because the steam is scarce. (c) A **stop signal**: the cycle at which forecast incremental revenue crosses forecast steam cost, which is the practical definition of when CSS stops paying and the well should be converted, rested, or handed to a different technique. Published work reports >20 % SOR reduction from exactly this class of intervention. (Source: https://onepetro.org/SPEWRM/proceedings-abstract/17WRM/17WRM/D031S003R001/196053)

---

## 7. What this means for our build (one paragraph)

Build a **Boberg–Lantz core** (heated radius from Marx–Langenheim, average temperature decay from the `fHD`/`fVD` functions), feed it a **Walther/ASTM D341 viscosity law fitted to Baghewala's own data**, couple it to a **nodal-analysis lift model for the sucker-rod pump** as UPC Global did (Source: https://www.upcoglobal.com/resources/technical-papers/artificial-lift-performance-coupled-with-boberg-lantz-model-for-a-better-prediction-of-cyclic-steam-injection-wells), subtract **wellbore heat loss** explicitly since 1,100 m and VIT make it a live term, and wrap an **ML residual + optimiser** around slug size, soak time and steam allocation. Report every result in three units at once: **bbl, ₹, and kg CO₂** — because at diesel-fired steam prices those three numbers move together, and that is the story that wins.

---

*Compiled September 2026. Cross-reference with `docs/research/baghewala_facts.md` for field-specific confirmed/typical/derived flags, and `docs/research/references.md` for the full source list.*
