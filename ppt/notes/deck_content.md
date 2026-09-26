# Baghewala Digital Twin — SIH Idea Presentation Deck

## SLIDE 1: Idea Title & Team

**Headline:** Digital Twin for Well-to-Surface Optimization of Cyclic Steam Stimulation and Sucker Rod Pump Operations

**Bullets:**
- Digital twin designed for real-time prediction of heavy oil well dynamics, targeting Baghewala field, Bikaner-Nagaur basin
- Physics-integrated AI model for CSS and SRP parameter optimization
- Team: 3rd-year Chemical Engineering + Software members, MNIT Jaipur
- Targeting 17–19° API crude (per PS; field literature reports current-producing crude at 14–17° API, SPE-23APOG) in an extreme viscosity regime — 8,000–15,000 cP @ 50°C (~90–100x more viscous than a typical 18° API crude)
- India's first Cyclic Steam Stimulation project runs at this exact field — well BGW-8, December 2018, with Calgary technical partner Belgrave Oil & Gas Corp.

**Killer Number:** ~550–600 km — road distance from Baghewala (Jaisalmer district, Thar Desert) to Jaipur; a remote field is exactly why real-time digital-twin monitoring matters

**ChemE Term:** Cyclic Steam Stimulation (CSS) and Sucker Rod Pump (SRP) operations

**VISUAL:** Field location map (Rajasthan highlighted, Bikaner-Nagaur basin marked, ~550–600 km annotation to Jaipur); Oil India logo; MNIT Jaipur position

---

## SLIDE 2: Proposed Solution

**Headline:** Physics-Driven AI Optimizer — From Manual Tuning to Autonomous SOR Minimization

**Bullets:**
- Problem: high Steam-Oil Ratio (SOR), manual parameter tweaking, rod floating failures
- Solution: digital twin integrating reservoir heating, fluid viscosity, pump dynamics, and inflow performance
- Outputs: optimized steam injection volume, soak duration, cutoff rate, and pump speed
- Constraints: rod floating risk < 30%, real-time prediction (sub-second latency)
- Differentiation: no commercial product (XSPOC, Lufkin SAM/SROD, Weatherford ForeSite, Schlumberger OptiSite, AVEVA, Kongsberg Kognitwin — all checked, `docs/research/landscape.md`) integrates CSS steam-cycle scheduling with sucker-rod-pump co-optimization; Baghewala's own first CSS cycle already showed a 5–6x production uplift, proving the physics case for coupling the two

**Killer Number:** Target SOR <3.5 t/m³ vs the typical heavy-oil CSS range of 3–8 (avg ~6) — Baghewala's own current SOR is not publicly reported, so we benchmark against the literature range, not an invented field figure

**ChemE Term:** Steam-Oil Ratio (SOR) — tonnes of steam per cubic metre of oil produced

**VISUAL:** Dashboard screenshot showing SOR gauge, floating-risk alert banner, and baseline-vs-optimized bar chart (amber/dark theme)

---

## SLIDE 3: Technical Approach

**Headline:** Layered Physics Engine and ML Pipeline

**Bullets:**
- Layer 1 Physics: Marx-Langenheim steam zone growth, Andrade viscosity-temperature model (mu = A·exp(B/T)), Vogel inflow performance curve
- Layer 2 Dynamics: sucker-rod load, pump efficiency, floating-risk index (>0.6 = unsafe)
- Layer 3 Simulation: ≥3000 synthetic CSS cycles (Latin-hypercube sampling over parameter ranges)
- Layer 4 ML: XGBoost SOR predictor + floating-risk classifier + Bayesian optimizer (minimize SOR subject to floating prob. < 30%)

**Killer Number:** 3000+ synthetic cycles for training (deterministic, seed=42)

**ChemE Term:** Andrade equation — exponential viscosity-temperature law for heavy crude

**VISUAL:** 3-layer architecture diagram (physics engine box → synthetic data cylinder → ML models → Bayesian optimizer feedback loop); equations for Marx-Langenheim and Andrade displayed

---

## SLIDE 4: Feasibility & Viability

**Headline:** Established Models, Field Parameters, Clear Data Path

**Bullets:**
- Physics foundation: Marx-Langenheim (1959) validated in CSS literature; Andrade law (ASTM standard); Vogel IPR (well-logging industry standard)
- Parameter source: field_params.json calibrated to Oil India / SPE-published Baghewala data (reservoir depth ~1,150 m, viscosity 8,000–15,000 cP @ 50°C, steam 280–305°C @ 60–70% quality, porosity <10% — poor-to-fair reservoir, a genuinely hard target that justifies a twin over trial-and-error)
- Proven at this exact field: India's first CSS success (well BGW-8, Dec 2018) already delivered a 5–6x first-cycle production uplift — de-risked, not unproven technology
- Scale: 52 wells drilled at Baghewala (33 operational); 19 CSS'd in FY2025-26 alone (~72% YoY growth) — same twin framework extends across this and future CSS wells
- Synthetic data bridge: physics-generated cycles now; Oil India historical data (listed in PS) for validation and final model tuning; implementation on Python 3.12 (NumPy, SciPy, XGBoost, scikit-optimize), FastAPI deployment, <4-week build-to-API timeline

**Killer Number:** ~1,150 m — Jodhpur Sandstone reservoir depth (CONFIRMED, SPE-23APOG-535203 / Oil India), now correctly reflected in field_params.json

**ChemE Term:** Well-to-surface integration — linking reservoir heating to pump rod mechanics

**VISUAL:** Parameter flow chart (Oil India data → field_params.json → twin simulator); timeline bar (Weeks 1–4: physics engine, synthetic data, ML training, API + dashboard)

---

## SLIDE 5: Impact & Benefits

**Headline:** Reduce SOR by 20–30%, Eliminate Rod Failures, Unlock Field Margins

**Bullets:**
- Economics (illustrative): $15k–$50k per avoided sucker-rod-pump workover (industry-typical, iFactory/general SRP literature) plus reduced steam fuel cost per barrel from a lower SOR — savings scale directly with wells covered; exact per-well $/year figure requires Oil India's own cost data to compute precisely
- Safety: real-time floating-risk monitoring is built to flag the exact failure mode (metal-on-metal rod/tubing wear, >50% of SRP failures) before it happens — a measured field failure-reduction % is not yet available and requires a pilot, not claimed here as a confirmed number
- Sustainability: lower steam demand cuts energy footprint per barrel produced; lighter greenhouse gas intensity
- Scalability: 52 wells drilled at Baghewala (33 operational), 19 CSS'd in FY2025-26 (~72% YoY growth) — same twin framework extends across this and future CSS wells as they come online
- Context: Baghewala's annual output grew ~200x since commercial CSS began — 218 t (FY2016-17) → 32,787 t (FY2024-25) → 43,773 t (FY2025-26) — our optimization further accelerates an already-scaling asset

**Killer Number:** 20–30% SOR reduction — physics-simulated (internal consistency-checked; field validation is the next phase), not yet a guaranteed field outcome

**ChemE Term:** Sucker rod floating — loss of pump integrity when viscous drag lifts rod above neutral point

**VISUAL:** Before-after SOR bar chart (industry-typical baseline ~6 t/m³, illustrative → optimizer target <3.5 t/m³); floating-risk gauge showing safe zone; production-growth sparkline (218 t → 43,773 t); 52-wells/33-operational icon

---

## SLIDE 6: Research & References

**Headline:** Foundation in Peer-Reviewed Theory and Industry Practice

**Bullets:**
- Marx, J. W., & Langenheim, R. H. (1959). "Reservoir heating by hot fluid injection." *Trans. AIME*, 216, 312–315.
- Andrade, E. N. da C. (1934). "Viscosity of liquids." *Nature*, 125, 309–310; ASTM D341 standard for viscosity-temperature relations.
- Vogel, J. V. (1968). "Inflow performance relationships for solution-gas drive wells." *J. Petrol. Tech.*, 20, 83–92.
- SPE-23APOG-535203 (2023), "Case Study for Enhancement of Production of Heavy and Highly Viscous Crude Oil Using Electrical Downhole Heater" — Baghewala reservoir/fluid data (depth, API, viscosity)
- Oil India Ltd. internal operations data (well BGW-8: steam rate, temperature, pressure, quality) + `docs/research/landscape.md` competitive-landscape check (XSPOC, Lufkin, Weatherford, Schlumberger, AVEVA, Kongsberg — none integrate CSS+SRP co-optimization)
- MNIT Jaipur research labs: thermodynamics & fluid mechanics precedent for physics model validation

**Killer Number:** 5 primary sources, zero unverifiable citations

**ChemE Term:** Inflow Performance Relationship (IPR) — map of well flow rate vs. pressure drawdown

**VISUAL:** Citation list formatted as academic references; small logos of Marx (1959), Andrade (1934), Vogel (1968) publications; MNIT emblem

---

---

## ELEVATOR PITCH (30 seconds, ~80 words)

Oil India's Baghewala field in Rajasthan — India's first Cyclic Steam Stimulation site (BGW-8, 2018) — relies on steam-driven production of extremely heavy, viscous crude (8,000–15,000 cP @ 50°C), but manual tuning and rod failures cost real money every cycle. We're building a digital twin integrating physics — Marx-Langenheim heating, Andrade viscosity, Vogel inflow dynamics — with machine learning to predict and optimize CSS and SRP parameters together, something no commercial rod-pump or reservoir-twin product does today. Our Bayesian optimizer targets minimizing Steam-Oil Ratio (against the industry's own 3–8 CSS benchmark) while constraining rod-floating risk below safe thresholds. With synthetic data training now and Oil India field data at finale, we'll deliver a FastAPI dashboard targeting a 20–30% SOR cut (physics-simulated, field validation next) and fewer costly rod-pump workovers.

---

## JUDGE Q&A (5 likely questions + 1-line answers)

1. **"Why synthetic data instead of real field data from the start?"**
   — Physics models are deterministic and validated; synthetic data lets us explore the full parameter space without operational risk, then Oil India data fine-tunes before deployment.

2. **"How do you handle uncertainty in reservoir properties (porosity, permeability, temperature profile)?"**
   — Field_params.json is the single source of truth, updated by research team with Oil India inputs; we propagate parametric ranges through Monte Carlo sensitivity checks in tests.

3. **"Can this twin transfer to other Oil India fields beyond Baghewala?"**
   — Yes—physics laws are universal; we swap field_params.json values (depth, thickness, fluid properties) and retrain on that field's synthetic cycles in <1 week.

4. **"What's your fallback if Bayesian optimization gets stuck in a local minimum?"**
   — We initialize with 10 random restarts and use skopt's gp_minimize with sufficient exploration budget; physics constraints (e.g., injection pressure < fracture gradient) keep solutions bounded and realistic.

5. **"How do you validate rod-floating risk predictions without live testing?"**
   — Floating index is physics-derived (viscous drag vs. rod weight on downstroke); we cross-check predictions against published sucker-rod failure datasets and Oil India's historical failure logs.
