# Glossary

One sentence per term. It's enough to talk about this project without a ChemE degree.
Terms are grouped; the first 20 are the original core list (rod floating, #6, is fixed:
the old wording described the physics backwards). Where a term behaves differently in
our **v1 engine** (commit 351a89b, historical, the source of the old dashboard and deck
numbers) and the **current engine** (physics rev 13, 27 Sep 2026 — see
`params/CHANGELOG.md` rev 10–13 and `docs/model-improvement/TIER1_PROGRESS_LOG.md`
§9–§12), the entry says which is which. Two sections cover this project's current
headline findings: § "Water cut and rod float (rev 11–12)" and, new this pass,
§ "Operating policy and injectivity (rev 13, physics wave 5)".

---

## Core terms (original 20)

1. **CSS (Cyclic Steam Stimulation)**: a heavy-oil production method that repeats three phases on the same well (inject steam, soak, then produce) so the oil gets hot enough to flow.
2. **Soak time**: the period after steam injection stops, when the well stays shut in so the heat spreads into the reservoir before production starts. OIL's BGW-8 practice is roughly 7–13 days.
3. **SOR (Steam-Oil Ratio)**: tonnes of steam injected per cubic metre of oil produced. Lower is better, and it is the main number this project tries to reduce (literature CSS range 3–8, average ~6).
4. **API gravity**: a scale for how light or heavy a crude is (higher means lighter). Baghewala's crude is 17–19° per the official problem statement and 14–17° per published field literature (SPE-23APOG), against 30°+ for light crude.
5. **Dynamometer card**: a plot of polished-rod load against rod position over one stroke. Engineers use it like an X-ray to read pump health from the surface. (Our dashboard's card is a **computed** surface + pump card from a Gibbs 1963 rod wave-equation solve, not an illustrative sketch; a separate measured-card classifier reads a real, uploaded card.)
6. **Rod floating**: a downstroke problem. Viscous drag from thick oil stops the rod string from falling as fast as the pumping unit drives it down, so the rods go slack, fall behind, buckle or get hit, and repeated cycles wear and part them.
7. **IPR (Inflow Performance Relationship)**: a curve of how much oil flows from the reservoir into the wellbore as the bottomhole pressure changes.
8. **VFD (Variable Frequency Drive)**: the motor controller that lets an operator change the pump's speed (SPM) electronically instead of by changing pulleys. As of rev 13, using it to slow down instead of pulling the well on a float alarm is one of our four modelled **float policies** — see the "Operating policy" section below.
9. **Asphaltene**: heavy, polar, sticky molecules in crude oil that can come out of solution and clog pores, tubing or pump valves when pressure or temperature changes.
10. **Workover**: a maintenance job that pulls equipment out of a well to repair or replace it. It is expensive (industry-typical $15k–$50k for a rod-pump job) and stops production while it happens.
11. **Marx-Langenheim model**: the 1959 heat-balance model we use to estimate how large the heated zone grows during steam injection. It accounts for heat conducted into the cap rock and base rock, and it gives a heated *area*, not a detailed temperature field.
12. **Andrade equation**: the viscosity law μ = A·exp(B/T), from Andrade (1930). Our v1 engine used it; with our two anchor points it predicted an implausible 0.63 cP at 290 °C.
13. **Viscosity**: a fluid's resistance to flow. Baghewala crude is 8,000–15,000 cP at 50 °C, roughly as thick as honey, until steam heats it.
14. **Cutoff rate**: the oil rate below which a CSS production phase is ended and the well is lined up for its next steam cycle.
15. **SPM (strokes per minute)**: how fast the sucker-rod pump cycles up and down. Heavy-oil practice is about 3–6 SPM, and running faster raises rod-floating risk.
16. **Plunger**: the piston-like part inside the downhole pump barrel that lifts oil upward one stroke at a time (ours is 57 mm).
17. **Bubble point**: the pressure at which dissolved gas starts coming out of the oil as free bubbles, which changes how the fluid flows.
18. **Mobility factor**: in our v1 engine, the ratio μ_ref/μ that scaled oil rate up as viscosity fell. It reached thousands, far beyond the 5–6× uplift the field actually saw, and was replaced by a capped composite-radial uplift.
19. **Bayesian optimisation**: a search method that picks each new parameter combination based on what it has learned so far. We use it to search steam/soak/cutoff/SPM settings without trying every combination.
20. **Digital twin**: a model of a specific real asset that is kept in step with that asset's data and used to predict and recommend actions for it. Ours is not yet connected to any live well data.

---

## Reservoir and flow

21. **Reservoir**: porous, permeable rock deep underground whose pore spaces hold oil, water or gas. It is not an underground lake.
22. **Porosity**: the fraction of the rock volume that is pore space. Baghewala's is under 10% (we use 0.09).
23. **Permeability**: how easily fluid can move through the connected pores, measured in darcies or millidarcies. It is separate from porosity, because a rock can have pores that are poorly connected.
24. **Jodhpur Sandstone**: the sandstone formation at about 1,100–1,150 m in the Bikaner–Nagaur basin that holds Baghewala's heavy oil.
25. **Huff-and-puff**: the informal name for CSS. "Huff" is injecting steam, "puff" is producing it back out of the same well.
26. **cP and Pa·s**: units of viscosity. 1 Pa·s = 1,000 cP, and water at room temperature is about 1 cP.
27. **t/m³ vs bbl**: SOR is quoted in tonnes of steam per m³ of oil. 1 m³ = 6.29 barrels (bbl), so a rate of 1 m³/d ≈ 6.3 bbl/d.
28. **EOR (Enhanced Oil Recovery)**: any method beyond natural reservoir pressure and plain pumping (steam, gas, chemicals) used to get more oil out. CSS is thermal EOR.
29. **Drawdown**: the pressure difference between the reservoir (Pr) and the flowing bottom of the well (Pwf). This difference drives oil into the well.
30. **Pwf / Pr**: flowing bottomhole pressure divided by average reservoir pressure. It is the x-axis of Vogel's curve; lower means more drawdown.
31. **Vogel correlation (1968)**: the standard empirical IPR shape, q/q_max = 1 − 0.2(Pwf/Pr) − 0.8(Pwf/Pr)².
32. **AOF (Absolute Open Flow)**: the theoretical rate a well would give if bottomhole pressure were zero. Our current engine uses `AOF_REF_M3D` 0.56 m³/d (retuned from 0.46 at rev 12 to put the reference peak inside the field's 15–40 bbl/d band), which gives a cold rate of about 0.44–0.54 m³/d (≈2.8–3.4 bbl/d) depending on reservoir pressure.
33. **PI (Productivity Index)**: oil rate per unit of drawdown, J = q/(Pr − Pwf). We have no measured PI for Baghewala, which is why AOF is calibrated.
34. **Drainage radius**: the radius of the reservoir disc that one well effectively drains. Field-realistic values are about 50–150 m; the current engine uses 100 m, while v1 used a tuned 8 m that was a fudge.
35. **Depletion**: the fall in reservoir pressure as fluid is withdrawn. Our v1 engine ignored it (Pr constant), and the current engine lets Pr rise with injected steam and bleed off during production.

## Heat

36. **Steam quality**: the mass fraction of the steam that is vapour rather than liquid. It is 60–70% at the Baghewala wellhead and lower at the sandface after wellbore losses (our current engine uses 0.55 × wellhead).
37. **Latent heat**: the heat released when steam condenses back to water at the same temperature. It carries most of steam's useful energy (current engine: 1.40 MJ/kg).
38. **Sensible heat**: heat that changes a material's temperature without changing its phase. Our models credit only the latent part of the steam's heat, which is conservative.
39. **Thermal diffusivity (α)**: how fast heat spreads through a material, α = k/(ρ·cp). For our cap/base rock it is ≈1.09×10⁻⁶ m²/s.
40. **Dimensionless time (t_D)**: t_D = 4αt/h², the clock Marx-Langenheim runs on. A thinner pay zone (smaller h) moves through it faster and loses heat sooner.
41. **erfc (complementary error function)**: the standard mathematical shape for heat conducting into a large solid. It appears inside the Marx-Langenheim function.
42. **E_h (thermal efficiency)**: the fraction of injected heat still held in the pay zone rather than lost to cap and base rock. It falls as injection goes on.
43. **Heated radius**: the radius of a cylinder with the same area as the Marx-Langenheim heated zone. It is a bookkeeping radius, not a measured steam front.
44. **Overburden / cap rock**: the rock above the pay zone (base rock is below). Conduction into it is the main heat loss during and after injection.
45. **Boberg–Lantz (1966)**: the classic model for how a CSS heated zone cools after injection, from conduction to the surrounding rock and heat carried out with produced fluids. It replaced v1's arbitrary 20-day exponential decay.
46. **Walther equation / ASTM D341**: the standard petroleum viscosity–temperature law, log log(ν + 0.7) vs log T. Our current engine uses it (μ at 290 °C = 4.13 cP, floored at 1 cP) instead of Andrade.
47. **Wellbore heat loss**: heat the steam loses on its ~1,150 m trip down the tubing. VIT (vacuum-insulated tubing) reduces it, and our current engine models it (v1 did not).

## Pump

48. **Pumpjack (beam pumping unit)**: the see-saw surface machine that drives a sucker-rod pump up and down.
49. **Polished rod**: the smooth top rod that passes through the wellhead seal. The surface load cell sits on it, so it is where the dynamometer card is measured.
50. **Rod string**: the ~1,150 m chain of steel sucker rods connecting the polished rod to the downhole plunger (ours: 3.8 kg/m).
51. **Buoyancy**: the upward push of the well fluid on the submerged rods. It reduces their effective weight by about 12% here (buoyant rod weight ≈37.6 kN).
52. **Floating index (FI)**: our own index, viscous drag force divided by buoyant rod weight, capped at 1. We flag above 0.6 as floating risk; that threshold is our design choice and still has to be calibrated against real dyno cards.
53. **Fillage**: the fraction of the pump barrel that actually fills with liquid on each stroke. The current engine caps it at 0.85 (FILLAGE_MAX, formerly VOLUMETRIC_EFFICIENCY) and lowers it when the oil is too thick.
54. **API RP 11L**: the American Petroleum Institute's recommended practice for sucker-rod system design calculations. Our srp.py is a simplified single-point approximation of it, not a full implementation.
55. **Pump-off controller (POC)**: a surface controller that detects when the pump barrel is not filling and slows or stops the unit. It is a standard feature of commercial rod-pump systems.
56. **Water cut**: the fraction of produced liquid that is water. Since rev 11 our engine models it as a **state**, not a constant — see the "Water cut and rod float" section below.

## ML and optimisation

57. **LHS (Latin Hypercube Sampling)**: a space-filling way to choose simulation inputs so that each input's range is evenly covered. We used it to pick 3,000 design points (seed 42).
58. **Surrogate model**: a fast statistical model trained to imitate a slower or more complex model. Our XGBoost models imitate the physics twin.
59. **XGBoost**: a gradient-boosted decision-tree library that works well on tabular numeric data. We use one regressor (SOR) and one classifier (floating risk).
60. **Gaussian Process (GP)**: a model that gives both a predicted value and an uncertainty at every untested point. Bayesian optimisation uses it to decide where to look next.
61. **Acquisition function**: the rule in Bayesian optimisation that trades exploiting good predictions against exploring uncertain regions to choose the next point.
62. **R² (coefficient of determination)**: the fraction of variance a model explains. Our v1 SOR surrogate scored 0.7246 on held-out synthetic data (0.992 inside the 1,200–2,400 t operating envelope).
63. **MAE (mean absolute error)**: the average size of a model's miss, in the target's own units. Ours is 0.3068 t/m³ on the synthetic hold-out.
64. **AUC (area under the ROC curve)**: how well a classifier ranks positives above negatives, where 1.0 is perfect. Our floating classifier scored 0.9989 on synthetic data.
65. **Hold-out set**: data kept aside and never used in training, used only to score the model. We used a single 80/20 split, with no cross-validation.
66. **Log-target**: training on log(SOR) instead of SOR so a few huge values do not dominate the fit. It raised our R² from 0.69 to 0.7246.
67. **Penalty method**: handling a constraint by adding a large cost to any candidate that breaks it. We add 1,000 × the excess when predicted floating probability ≥ 0.3.
68. **Sim-to-real gap**: the difference between how a model performs on simulated data and how it performs on the real system. Ours is unmeasured because we have no field data yet.
69. **Calibration / history matching**: tuning a model's uncertain parameters until its outputs reproduce measured field history (cycle rates, temperatures, dyno cards). It is our first task once OIL shares data.

## Operations and industry

70. **VIT (vacuum-insulated tubing)**: double-walled tubing with a vacuum gap that cuts wellbore heat loss. Baghewala uses it.
71. **HSD (high-speed diesel)**: the fuel for Baghewala's steam generators. It takes about 71 kg HSD per tonne of steam, ≈ ₹5,900–8,400 and ≈224 kg CO₂ per tonne.
72. **SCADA**: the supervisory control and data-acquisition system that collects field sensor data and sends operator commands.
73. **OPC-UA**: a standard industrial protocol for reading tags from SCADA and control systems. A deployment would use it to feed a twin.
74. **Advisory vs closed-loop**: advisory mode means the system recommends and a human decides and acts. Closed-loop means the system writes set-points to the controller itself. Ours is advisory only, with no controller link.
75. **SAGD (Steam-Assisted Gravity Drainage)**: continuous steam injection through an upper horizontal well with production from a lower one, using gravity. OIL has named it as a next step at Baghewala.
76. **CMG STARS / Eclipse**: commercial full-field reservoir simulators (thermal and black-oil). They model 3-D, multi-phase flow and are far more complete, and far slower, than our twin.
77. **XSPOC / Lufkin SAM**: commercial rod-pump optimisation and pump-off control products (ChampionX, Lufkin). They optimise the pump well but treat the reservoir's thermal cycle as a fixed input.
78. **Digital twin vs simulator**: a simulator answers "what if" for a generic model. A twin is a simulator tied to one specific asset and updated from that asset's data. Until it is fed and recalibrated from real well data, ours is honestly a twin-ready simulator.

## Calibration (physics rev 5, 26 Sep 2026)

79. **Margin per cycle-day**: the ₹ economic result (steam cost subtracted from oil revenue) divided by the *total* cycle length — inject + soak + produce, not just the producing days. This, not SOR, is the optimiser's actual objective from rev 5 onward: minimising SOR alone pushes steam toward the minimum, which is honest physics but not what the field wants.
80. **Published-practice baseline**: the comparison scenario derived from Oil India's own documented **BGW-8 first CSS job** (Dec 2018): ~1,300 t steam, 10-day soak, 5 SPM (cutoff and exact SPM weren't published for that job, so a mid-range value fills the gap). It is **one real, cited data point, not OIL's current operating practice** — say so whenever it's shown.
81. **xfail**: a test that is *expected* to fail and is marked as such in the test suite, so the run still reports as passing overall (`263 passed, 2 xfailed`, not "261/263"). Current xfails (rev 13): no interior soak optimum, and a steam-slug optimum at the mid-range (0.15) diesel-discount price that comes out below the BGW-8-documented slug range — both found, understood and left open on purpose, not hidden bugs. (The rev-12 cold-well-unpumpable xfail is now **un-xfailed**: the cold counterfactual obeys the same float policy as everything else and is correctly shut in, not "pumpable, but the test says it can't be" — see #94 below.)
82. **Sensible heat vs latent heat**: sensible heat raises a fluid's temperature without changing its phase (energy = mass × specific heat × ΔT); latent heat drives the phase change itself — steam condensing to water — at constant temperature (energy = mass × latent heat of vaporisation). The rev-4→rev-5 fix was crediting only the latent term in the heat balance and missing the sensible term entirely, which undercounted the heat actually delivered by about 3.6×.
83. **Cold-water-equivalent (CWE)**: a convention for reporting injected steam as the volume or mass of liquid water it's equivalent to at reference conditions, rather than as steam volume at wellhead temperature and pressure (used e.g. by California's CalGEM steam-injection records: 1 bbl CWE ≈ 0.159 m³ ≈ 0.159 t). It lets steam volumes from different pressures/qualities be compared on one consistent basis; this project reports steam mass in tonnes directly rather than CWE, but the concept is the same idea applied to public benchmark datasets we compare against.

## Water cut and rod float (rev 11–12, 27 Sep 2026)

This project's current headline finding — "rod float is a late-cycle event, so pull the
well when it fires, rather than chasing a fixed rate" — rests on these six terms.

84. **Condensate flowback**: the portion of injected steam, now condensed to hot water, that
    the well produces back before it reaches the native reservoir fluid. It is why water cut
    starts *high* early in a CSS produce phase (our model: ~0.87) rather than at the
    reservoir's own native water cut — a well-mixed cell decays it exponentially as it drains,
    with `condensate_recovery_frac` (0.7 `[ASSUMPTION]`) of the injected mass ultimately
    recovered.
85. **Emulsion inversion**: the water cut at which a water-oil mixture flips from
    **water-continuous** (water is the connected phase; viscosity stays close to hot water's,
    a few cP) to **oil-continuous**, i.e. water-in-oil (oil is the connected phase; viscosity
    can be many times the oil's own). Our model places this inversion at **water cut ≈ 0.70**
    `[ASSUMPTION]` — above it the produced stream is easy to lift; below it, the rods see a
    much thicker fluid.
86. **Pal–Rhodes (1989)**: a published water-in-oil emulsion viscosity law,
    μ_r = [1 + (φ/φ*)/(1.187 − φ/φ*)]^2.49, where φ is water cut and φ* is a fitted solvation
    parameter. Algebraically it is Brinkman's older law with an extra solvated-fraction term;
    at our fitted φ* = 0.84 it equals Brinkman below 60% water. We use it, capped at 10× the
    oil's own viscosity `[ASSUMPTION]`, for rod drag once the stream turns oil-continuous.
87. **Float-onset rule** (`css.produce_end_rule = "either"`): the operating policy that ends a
    produce phase on the rate cutoff **or** on 3 consecutive days of a floating-index alarm
    (`css.fi_alarm_days`), whichever comes first — modelling an operator who pulls the well on
    persistent float, rather than running floating rods for months or chasing a fragile fixed
    low cutoff. As of rev 13 this is just one leg of a fuller **float policy** (#90 below):
    under `pull` it fires as described here; under `vfd_hold`/`vfd_then_pull` the alarm can
    only fire once the VFD has already slowed the well to its floor.
88. **Produce-end rule**: the general term for *which* condition stops a produce phase —
    `rate_cutoff` (the original, rate-only rule), `float_onset` (float-alarm only), or
    `either` (both, matching whichever float policy is active). Changing this rule alone can
    move a cycle's SOR by ~40% at the same set-points, since it decides whether a well is
    allowed to keep producing cheap, late, cooling oil.
89. **Shut-in counterfactual**: reading a ₹ figure as "stimulated cycle minus a shut-in
    (non-producing) well" instead of "minus an idealised, pumpable cold well." As of rev 13
    this is the **default**, not an alternate reading: the cold well is shut in under every
    float policy except `none` (FI 1.0, 189 kN at the assumed unit's 2-spm floor), because a
    real operator following any of the three float policies would shut it in too. The old
    "idealised pumpable cold well" figure (~₹11.4k/d more favourable) is kept and reported
    alongside it as the more field-consistent reading, since the field did produce these
    wells cold.

## Operating policy and injectivity (rev 13, physics wave 5, 27 Sep 2026)

A technical re-score found this project's rev-12 headline gain was really the **pull
rule** ending the baseline early, not the recommendation's own set-points. These five
terms are the fix: the operator's response to rod float is now a modelled, priced
**policy** choice, applied the same way to the baseline and the recommendation alike.

90. **Float policy** (`css.float_policy`): the operator's chosen response once the rods
    start floating — `pull` (end the cycle the moment the alarm has held 3 days),
    **`vfd_hold`** (slow the pump with a VFD to hold the floating index at a safe 0.6
    instead, down to a 2-spm floor, and only pull after 3 days *at that floor* — our
    **recommended** policy), `vfd_then_pull` (a milder VFD turndown, otherwise the same),
    or `none` (no float response at all — the cycle runs to the rate cutoff only). Which
    policy the *baseline* is assumed to run changes the recommendation's ₹ gain more than
    any steam, pressure or stroke set-point does: +₹3,332/d if it VFD-holds too,
    +₹12,917/d if it pulls, −₹3,865/d if it does nothing — always name which one a gain
    number is against.
91. **VFD-hold**: the recommended float policy (#90) — instead of pulling the well the
    instant rods start floating, a Variable Frequency Drive slows the pumping unit down
    just enough to hold the floating index at the 0.6 alarm line, buying extra produce
    days at the cost of running the rods at that limit for weeks at a time (an unpriced
    rod-damage cost — see #93 in the numbers bible / README "Honest limits").
92. **Injectivity margin** (`steam.min_injection_margin_kPa`): how much higher the
    wellhead-driven sandface steam pressure is than the reservoir's own current pressure,
    in kPa. Below about 300–400 kPa of margin, steam cannot physically be injected at a
    useful rate — this is a **hard feasibility gate**, not an economic preference, and it
    is why rev 13 rejects the old 85 kgf/cm² wellhead-pressure floor (only 53 kPa margin)
    in favour of 89 kgf/cm² (498 kPa).
93. **Net-of-levies deck**: one of three price scenarios this project reports ₹ under —
    the realised oil price after subtracting India's royalty and Oil Industry Development
    (OID) cess (~35% combined, cross-checked against OIL's own FY25 Annual Report
    exchequer table), i.e. roughly what the company nets per barrel after government
    levies, alongside the gross FY25-realisation and $65/bbl-floor decks. On this deck,
    every feasible recommendation in this project is currently **negative**, even against
    a shut-in cold well.
94. **Inversion band** (`fluid.emulsion_inversion_band_wc`, 0.075): a small range of water
    cut, centred on the emulsion-inversion point (#85), over which drag viscosity is now
    blended smoothly between the water-continuous and oil-continuous branches instead of
    switching abruptly. Without it, viscosity (and rod drag) could jump **3,365×** from one
    simulated day to the next at the inversion crossing — numerically ugly, though it
    barely changes the ₹ economics (<₹0.1k/d) since the float onset that actually ends
    most cycles happens below the band, not at it.
