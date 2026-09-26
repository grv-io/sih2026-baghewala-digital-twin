# References

## A. Model citations used by the twin (task 3)

1. **Marx & Langenheim steam-zone model (thermal.py)**
   Marx, J.W. and Langenheim, R.H. (1959). "Reservoir Heating by Hot Fluid Injection." *Transactions of AIME*, 216, 312–314.
   Analytical energy-balance model for a growing hot-water/steam zone during continuous fluid injection into a reservoir, accounting for heat injected vs. heat lost vertically to over/underlying rock; it is the foundational model behind virtually all later steam-zone-growth and steamflood analytical models. OIL's own CSS operations at Baghewala target the same underlying physics (a growing heated zone around the wellbore during the injection phase).
   Background: [PetroWiki — Thermal Recovery by Steam Injection](https://petrowiki.org/PEH:Thermal_Recovery_by_Steam_Injection); [OSTI record of the original model](https://www.osti.gov/biblio/6523884)

2. **Andrade viscosity-temperature form / ASTM D341 (viscosity.py)**
   Andrade, E.N. da C. (1930). "The Viscosity of Liquids." *Nature*, 125, 309–310. (Origin of the exponential form μ = A·exp(B/T).)
   ASTM D341-20e1, "Standard Practice for Viscosity-Temperature Equations and Charts for Liquid Petroleum or Hydrocarbon Products," ASTM International.
   The classical Andrade equation gives a simple exponential decay of viscosity with absolute temperature and is the basis of the twin's `mu_cP` fit. Note: ASTM D341 itself formally standardizes the (related but distinct) double-log Walther/Ubbelohde-Walther equation `log(log(v+0.7)) = A − B·log(T)` for petroleum products — cite both, but document in code that the twin uses the simpler single-exponential Andrade form as an engineering approximation, not the full ASTM D341 procedure.
   Source: [ASTM D341 standard page](https://www.astm.org/Standards/D341.htm)

3. **Vogel IPR (ipr.py)**
   Vogel, J.V. (1968). "Inflow Performance Relationships for Solution-Gas Drive Wells." *Journal of Petroleum Technology*, 20(1), 83–92. SPE-1476-PA.
   Empirical dimensionless curve relating producing bottomhole pressure to oil rate for solution-gas-drive reservoirs below the bubble point; widely used (with mobility/viscosity corrections) as a general-purpose IPR curve even outside its original solution-gas-drive assumptions.
   Source: [OnePetro — Vogel 1968](https://onepetro.org/JPT/article/20/01/83/163252/Inflow-Performance-Relationships-for-Solution-Gas)

4. **Gibbs wave equation for rod pumping (srp.py)**
   Gibbs, S.G. (1963). "Predicting the Behavior of Sucker-Rod Pumping Systems." *Journal of Petroleum Technology*, 15(7), 769–778. SPE-588-PA. https://doi.org/10.2118/588-PA
   Models the sucker-rod string as a damped wave equation, propagating surface polished-rod motion down the rod string to predict downhole pump displacement/load (or vice versa for diagnosis); this became the standard basis for rod-pumping design and dynamometer-card diagnostic software still used industry-wide.
   Source: [Semantic Scholar record](https://www.semanticscholar.org/paper/Predicting-the-Behavior-of-Sucker-Rod-Pumping-Gibbs/093c7119ac27d80b776051047550bffe69af8b5e)

## B. Best links for the PPT References slide

1. [Oil India Limited — Rajasthan Fields (official company page)](https://www.oil-india.com/rajasthan-fields) — richest single public overview of Baghewala history, technology, and current status.
2. Basha, S.K., Kumar, A., Borgohain, J.K., Shaw, R., Gupta, M., Singh, S. "Rock physics modeling and simultaneous inversion to map heavy-oil bearing sands in Baghewala area, Bikaner-Nagaur basin, India." *GEOHORIZONS* (SPG India), January 2015. [PDF](https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf) — peer-reviewed, gives porosity, discovery API, and reservoir geology.
3. "Case Study for Enhancement of Production of Heavy and Highly Viscous Crude Oil Using Electrical Downhole Heater." SPE/IATMI Asia Pacific Oil & Gas Conference and Exhibition, Jakarta, Oct 2023. [OnePetro abstract](https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/2-23APOG/535203) — SPE-vetted source for API gravity (14–17°) and viscosity (8,000–15,000 cP @ 50°C) of the producing crude.
4. "Using Downhole Electric Heaters to Complement or Replace Cyclic Steam Stimulation Operations." SPE EOR Conference at Oil and Gas West Asia, 2024. [OnePetro abstract](https://onepetro.org/SPEOGWA/proceedings-abstract/24OPES/24OPES/D031S035R002/544525)
5. "Successful Rig-Less Fishing Operation to Recover a Downhole Sucker Rod Pump at Baghewala Heavy Oil Field, Rajasthan – India: A Case Study." [ResearchGate](https://www.researchgate.net/publication/398187378_Successful_Rig-Less_Fishing_Operation_to_Recover_a_Downhole_Sucker_Rod_Pump_at_Baghewala_Heavy_Oil_Field_Rajasthan_-_India_A_Case_Study) — directly ties SRP failure/workover topic to Baghewala specifically.
6. "OIL starts CSS of well in Rajasthan." *Oil & Gas Journal*. [Link](https://www.ogj.com/drilling-production/production-operations/unconventional-resources/article/17296851/oil-starts-css-of-well-in-rajasthan) — trade-press record of India's first CSS at well BGW-8, Dec 2018.
7. "Hormuz blocked, India turns to Thar desert: Oil India ramps up crude output from Rajasthan field." *Business Today*, Apr 2026. [Link](https://www.businesstoday.in/india/story/hormuz-blocked-india-turns-to-thar-desert-oil-india-ramps-up-crude-output-from-rajasthan-field-524088-2026-04-05) — current-events framing (Hormuz crisis, national energy security angle) useful for the "why this matters now" slide.
8. "OIL ramps up crude production from Rajasthan's Thar amid energy crisis." *Business Standard*. [Link](https://www.business-standard.com/companies/news/oil-ramps-up-crude-production-from-rajasthan-s-thar-amid-energy-crisis-126040500173_1.html)
9. Marx, J.W. and Langenheim, R.H. (1959). "Reservoir Heating by Hot Fluid Injection." *Trans. AIME*, 216, 312–314. (see model citations above)
10. Vogel, J.V. (1968); Gibbs, S.G. (1963) — see model citations above.

## C. Note on source reliability

Item 1 above (oil-india.com) and an internal-looking OIL slide deck ("Baghewala PPT, Oil India Limited, 12.07.2025," hosted on SlideShare, used extensively in `baghewala_facts.md`) are the two richest sources on operational numbers but are not independently peer-reviewed. Where possible, numbers from these were cross-checked against the independently-published SPE paper (item 3) and found consistent (API gravity, viscosity, and depth all agree within the stated ranges). Cite item 3 (the SPE paper) preferentially on slides that need a defensible, citable technical source; use the OIL company page and PPT for narrative/history context.
