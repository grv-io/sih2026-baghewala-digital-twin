# Baghewala Field & Indian Heavy Oil — Deep Dossier

**For:** SIH 2026, PS **SIH26120** — *"Digital Twin for Well-to-Surface Optimization of Cyclic Steam Stimulation (CSS) and Sucker Rod Pump (SRP) Operations for Heavy Oil Wells of Baghewala Field"*, Oil India Limited, Smart Automation theme, Software category.
(Source: https://github.com/dasher06/Baghewala_Digital_Twin_SIH26120 ; https://zaidsayyed.in/tools/sih-problem-statements/theme/smart-automation)

**Companion doc:** `docs/research/baghewala_facts.md` (first pass — operating parameters, CSS cycle numbers, TYPICAL/DERIVED gap-fills). This dossier does **not** repeat those; it goes underneath them into basin geology, dated operational history, OIL as an organisation, national policy context, source conflicts, and stage-ready material.

**Evidence convention:** every claim carries `(Source: URL)`. Where nothing was found, it says **NOT FOUND** — no substitutions, no estimates dressed as facts.

---

## 1. Field and basin geology

### 1.1 The basin

Baghewala sits in the **Bikaner–Nagaur basin**, a Neoproterozoic–Early Palaeozoic (Infracambrian) basin on the north-western flank of the Peninsular Indian Shield, itself a sub-basin of the larger onland Rajasthan basin. Reported area is ~**70,000 sq km** for Bikaner–Nagaur within a ~**126,000 sq km** Rajasthan basin (Source: https://www.dghindia.gov.in/assets/downloads/56ceb6e098299Rajasthan_Basin_18.pdf ; https://rajras.in/ras/pre/rajasthan/geography/minerals/hydrocarbon/). It is described as **the only evaporite basin of its kind in India** and splits into two sub-basins: **Jodhpur–Nagaur** (south, SW–NE trending, *heavy* oil — Baghewala's home) and **Nagaur–Ganganagar** (north, NNE–SSW, where the N1 well found *light* crude) (Source: https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india).

Basin boundaries: Delhi–Sargodha ridge to the NE, the Aravallis to the E, the Jodhpur–Pokhran–Chottan–Malani ridge to the S, and the Devikot–Nachna high separating it from the Jaisalmer basin (Source: https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india). Across the international border the same play continues into the **Punjab Platform of Pakistan's Middle Indus basin** (Source: https://link.springer.com/article/10.1007/s13202-021-01432-7).

### 1.2 Stratigraphy at Baghewala (bottom-up)

- **Basement:** Malani rhyolite and granite gneiss, overlain by a *thin* Lower Palaeozoic sedimentary cover of only **~1,500 m** total (Source: https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf — Basha, Kumar, Borgohain (Oil India) + Shaw, Gupta, Singh (Schlumberger), *GEOHORIZONS* Jan 2015, pp. 47–50). **This is the single most important geological fact for the digital twin: the entire petroleum system is squeezed into 1.5 km, which is why the reservoir is shallow, cold (~50 °C BHT) and immature.**
- **Marwar Supergroup — Jodhpur Group:** sandstone with shale/limestone bands, split into Sonia shale and sandstone members. This is the **primary reservoir** (Source: https://www.nature.com/articles/s41598-022-14831-5).
- **Bilara Group (carbonates/dolomites) + Hanseran Evaporite Group (HEG):** limestone–dolomite–evaporites. HEG contains **seven halite cycles** separated by clay-shale and dolomite zones; HEG thickness **100–1,000 m**, reaching **1,000–1,100 m** westward (Source: https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india).
- **Nagaur Group** (argillaceous/arenaceous) above, then Permo-Triassic Bap–Badhura boulder bed, Mesozoic and Tertiary/Quaternary cover (Source: same OGJ article).

### 1.3 The petroleum system — source, migration, trap, seal

- **Source rock:** the **Bilara–Hanseran** carbonate-evaporite sequence, **TOC 5–6 %**, ~200 m estimated thickness (Source: https://www.nature.com/articles/s41598-022-14831-5 — Yasin, Baklouti, Sohail, Asif & Xufei, *Scientific Reports* 12:11102, 2022).
- **Biomarker evidence:** the Baghewala-1 oil came from **algal and bacterial organic matter with no higher-plant input**, in an Infracambrian **carbonate-rich source deposited under anoxic marine conditions** — most likely **organic-rich laminated dolomites of the Bilara Formation** (Source: https://pubs.geoscienceworld.org/aapg/aapgbull/article-abstract/79/10/1481/39084/Recognition-of-an-Infracambrian-Source-Rock-Based — *AAPG Bulletin* v.79 no.10, p.1481, "Recognition of an Infracambrian Source Rock Based on Biomarkers in the Baghewala-1 Oil, India"). The Jodhpur Formation is dated **540–640 Ma** in the same work.
- **Migration/trap:** "The Baghewala anticline provides conditions favorable for oil migrating from Bilara shales to be entrapped in shaly Jodhpur sand." Top seal is provided by **Bilara carbonates or shale** (Source: https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf). So the trap is a **four-way anticlinal closure with a carbonate/evaporite top seal** — an unusually clean trap geometry for such an old section.

### 1.4 Why the crude is so heavy — the counter-intuitive answer

Most heavy oil worldwide is heavy because it was **biodegraded** by bacteria at shallow depth. **Baghewala's is not.** The AAPG biomarker study states the Baghewala-1 oil is **non-biodegraded**, and maturity-sensitive biomarker ratios put it in the **early oil window** (Source: https://pubs.geoscienceworld.org/aapg/aapgbull/article-abstract/79/10/1481/39084/Recognition-of-an-Infracambrian-Source-Rock-Based ; corroborated at https://www.nature.com/articles/s41598-022-14831-5). OGJ puts it plainly: the oil "originated from sulfur-rich organic matter in low maturity marine carbonate" (Source: https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india).

**Mechanism to state on stage:** an anoxic, clay-starved, carbonate–evaporite source with abundant sulphur produced a **Type II-S (sulphur-rich) kerogen**. Sulphur-rich kerogens expel oil *early*, at low thermal maturity, and the expelled oil is loaded with high-molecular-weight sulphur-bridged resins and asphaltenes. Combine that with a shallow (~1.1 km), thin (~1.5 km total section) basin that never buried the source deep enough to crack those molecules, and you get an oil that is **only moderately heavy by API (14–19°) but extraordinarily viscous (8,000–15,000 cP at 50 °C)**. That decoupling of API from viscosity is the field's signature anomaly — and, as the first-pass doc already showed, it is why a generic API→viscosity correlation is ~90–100× wrong here.

### 1.5 Reservoir properties

| Property | Value | Source |
|---|---|---|
| Reservoir | Infracambrian Jodhpur sandstone (shaly sand) | GEOHORIZONS 2015 |
| Depth | ~1,100–1,150 m | https://www.oil-india.com/rajasthan-fields |
| Porosity — Jodhpur (Baghewala area, from logs) | **< 10 %**, "poor porosity" | https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf |
| Porosity — Jodhpur sandstone (basin-wide) | **16–25 %** | https://www.nature.com/articles/s41598-022-14831-5 |
| Porosity — Bilara dolostone | 7–15 % | https://www.nature.com/articles/s41598-022-14831-5 |
| Porosity — Hanseran siltstones | 3–12 % | https://www.nature.com/articles/s41598-022-14831-5 |
| Oil saturation (Jodhpur, basin-wide) | 65–80 % | https://www.nature.com/articles/s41598-022-14831-5 |
| Heterogeneity | "significant vertical and lateral reservoir heterogeneity" | GEOHORIZONS 2015 |
| **Permeability** | **NOT FOUND** in any public source | — |
| **Net pay / net sand thickness** | **NOT FOUND** | — |

**Reservoir characterisation work done:** OIL and Schlumberger ran **simultaneous pre-stack inversion of multiple angle stacks** over the Baghewala structure to derive acoustic impedance (AI) and shear impedance (SI), then classified litho-facies in a **Bayesian framework** to map good vs poor reservoir facies and their probabilities. Because **no measured shear-sonic (Vs) logs existed in any well penetrating the Jodhpur**, they used the **Greenberg–Castagna (1992) rock-physics model**, calibrated on offset well O1, validated on O2, then applied to well A1 and the rest. Key finding: **AI alone cannot separate brine sands from heavy-oil sands** (the impedance values overlap) — SI or Vp/Vs is essential (Source: https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf).

### 1.6 Cross-border and global analogues

- **Pakistan (Punjab Platform):** heavy oil from **Karampur-1, Fort Abbas-1 and Bijnot-1** "geochemically resembled the heavy nonbiodegradable oil from the Jodhpur sandstone, the Bilara dolostone, and the Hanseran evaporite of the Baghewala-1 well" (Source: https://www.nature.com/articles/s41598-022-14831-5). The same study concludes the Infracambrian section on Pakistan's eastern flank is **thicker, thermally more mature and has deep-seated structural closures**, giving it a *higher* chance of both heavy and light oil than the Indian side. **Karampur-1 is the direct across-the-border twin of Baghewala-1** and OGJ made the same correlation back in 2002 (Source: https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india).
- **Oman:** "Similar geochemistry of heavy oil has been reported for the carbonate-evaporite facies of the **Huqf Group** (Infracambrian) … more than 2000 km to the SW, along the eastern flank of southern Oman." The Punjab Platform, Bikaner–Nagaur and the Ghaba/Fahud/South Oman salt basins formed in the same latest-Neoproterozoic–earliest-Cambrian rift/transtension event (Source: https://www.nature.com/articles/s41598-022-14831-5). **This makes Baghewala a member of the same global Infracambrian salt-basin family as the giant South Oman fields — a strong, defensible line for a judge who knows petroleum geology.**

---

## 2. Operations timeline — every dated fact found

| Date | Event | Source |
|---|---|---|
| 1960s | ONGC drills **Pugal-1**; encounters evaporites; exploration ceased | https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india |
| **1991** | **OIL drills Baghewala-1 (A1)** — the discovery well on the western periphery of the basin. Confirms heavy oil (**17.6° API**) in Jodhpur sandstone and **bitumen in Upper and Lower Bilara carbonates** | https://link.springer.com/article/10.1007/s13202-021-01432-7 |
| 1994 | Dasgupta & Bulgauda publish the first overview of geology/hydrocarbon occurrences in the western Bikaner–Nagaur basin (*Indian J. Petroleum Geology* 3, 218–220) | cited in https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf |
| 1995 | AAPG Bulletin publishes the Baghewala-1 biomarker study establishing the Infracambrian source | https://pubs.geoscienceworld.org/aapg/aapgbull/article-abstract/79/10/1481/39084/Recognition-of-an-Infracambrian-Source-Rock-Based |
| 1996 | **Essar Oil Ltd** signs PSCs for blocks **RJ-ON-90/4 and RJ-ON-90/5**; **Polish Oil & Gas Co (POGC)** takes 25 % participating interest | https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india |
| Sep 1997 – Apr 1998 | First seismic campaign, **1,062 line km** | same |
| Aug – Nov 1998 | Second seismic campaign, **348 line km** | same |
| ~2000 | **N1** — first exploratory well in the Nagaur–Ganganagar sub-basin; **light** crude, five HC-bearing zones, drilled to basement through eight HEG formations / 7 halite cycles | same |
| ~2006 | OIL trials chemical floods and steam from portable/mobile generators at Baghewala | https://www.ogj.com/drilling-production/production-operations/unconventional-resources/article/17296851/oil-starts-css-of-well-in-rajasthan |
| Jan 2015 | OIL + Schlumberger publish the rock-physics / simultaneous-inversion study of the Baghewala anticline | https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf |
| **FY2016-17** | Annual production **218 tonnes** (see first-pass doc) | OIL internal PPT |
| **2017** | **Commercial production begins** at Baghewala | https://www.business-standard.com/companies/news/oil-ramps-up-crude-production-from-rajasthan-s-thar-amid-energy-crisis-126040500173_1.html |
| **4 Dec 2018** | **India's first Cyclic Steam Stimulation** begins at well **BGW-8**, with assistance from **Belgrave Oil & Gas Corp., Calgary** | https://www.ogj.com/drilling-production/production-operations/unconventional-resources/article/17296851/oil-starts-css-of-well-in-rajasthan |
| ~2019–21 | Government of India acquires **2,525 line km of regional 2D seismic** across the basin under the **National Seismic Programme (NSP)** — first ever coverage of the central/eastern Bikaner–Nagaur basin | https://link.springer.com/article/10.1007/s13202-021-01432-7 |
| Oct 2023 | SPE-535203 presented at SPE Asia Pacific Oil & Gas Conf — **Electrical Downhole Heater (EDH) trial in a horizontal Baghewala well** | https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/2-23APOG/535203 |
| 2024 | SPE (24OPES) follow-up: "Using Downhole Electric Heaters to Complement or Replace CSS Operations" — abstract behind paywall (403), **details NOT RETRIEVED** | https://onepetro.org/SPEOGWA/proceedings-abstract/24OPES/24OPES/D031S035R002/544525 |
| **FY2024-25** | **32,787 t** annual; **705 bbl/d**; 9 new wells drilled; 11 CSS jobs (derived from "19 wells, ~72 % higher") | https://psuwatch.com/newsupdates/oil-india-ramps-up-crude-production-from-rajasthans-thar-desert |
| Apr 2025 | Well-status snapshot: 25 flowing, 9 non-flowing, 3 shut-in, 4 under drilling/testing/CSS, 3 temporarily abandoned | OIL internal PPT (first-pass doc §5) |
| Jun 2025 | **39 CSS cycles** completed to date | OIL internal PPT |
| 10 Jul 2025 | ~655 bbl/d | OIL internal PPT |
| **FY2025-26** | **43,773 t** annual (+33.5 %); **1,202 bbl/d** record (+70 %); **19 CSS wells** (+72 %); **13 new wells** drilled | https://www.businesstoday.in/india/story/from-dunes-to-diesel-how-thar-desert-is-powering-india-524228-2026-04-06 |
| Current (OIL website) | **56 wells drilled, 34 producing, >1,100 bbl/d**; **SAGD planned** as the next production-enhancement step | https://www.oil-india.com/rajasthan-fields |

### 2.1 The EDH trial — what SPE-535203 actually says

Verbatim-substance abstract: the paper "addresses the challenging task of producing highly viscous and extra heavy crude oil from the Jodhpur Sandstone reservoir of Baghewala field of Western Rajasthan in India by conventional methods. The crude has API in the range of **14-17** and viscosity ranging from **8000 to 15000 cP @ 50°C**. The study proposes carrying out a trial test with the **Electrical Downhole Heater (EDH) in one of the horizontal wells** and checks the performance in production rates in comparison with other wells without EDH." (Source: https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/2-23APOG/535203). **Note the design: it is a controlled comparison — one horizontal well with EDH vs offset wells without.** Quantified uplift results were **NOT FOUND** (full text paywalled).

### 2.2 Technology stack in the field

Confirmed deployed: **CSS** (primary thermal EOR); **conventional and hydraulic sucker-rod pumps**; **high-temperature thermal wellheads**; **vacuum-insulated tubing (VIT)**; **thermal completions**; **electric downhole heaters**; **barefoot completion**; **fishbone drilling at well BGW#40** — "First-Ever Fishbones Drilling Deployment in India's Heavy Oil Reservoir"; **mobile/skid-mounted HP steam generators**; **diluent injection** for viscosity management; **SAGD planned** (Source: https://www.oil-india.com/rajasthan-fields ; https://www.businesstoday.in/india/story/from-dunes-to-diesel-how-thar-desert-is-powering-india-524228-2026-04-06).

### 2.3 Surface handling and evacuation

There is **no pipeline out of Baghewala**. Crude is stored in tanks, **heated with steam and hot water from the mobile steam generator to restore flowability**, pumped into **bowsers (road tankers)**, trucked to **ONGC's North Santhal CTF at Mehsana, Gujarat**, and only then piped to **IOCL's Koyali refinery** (Source: https://www.oil-india.com/rajasthan-fields). **There is no Rajasthan-state refinery linkage for Baghewala crude** — the HPCL–Rajasthan Refinery at Pachpadra is *not* cited by any source as the Baghewala offtaker. Treat any claim otherwise as unsupported.

**Operational constraints named in reporting:** water availability for steam generation, equipment maintenance under extreme desert temperatures, logistics in a remote desert location, continuous energy supply for steam, and environmental management in a sensitive desert ecosystem (Source: https://discoveryalert.com.au/thermal-enhanced-oil-recovery-methods-2026/).

---

## 3. Oil India Limited as an organisation

### 3.1 Where Rajasthan sits in the portfolio

Baghewala is **small in volume, large in symbolism**. OIL's FY25 upstream production was **6.7 MMTOE** (up from 5.6 MMTOE five years earlier); domestic **2P oil reserve 69 MMT**, gas **121 MMTOE**; **reserve replacement ratio 0.94** in FY25; **2P reserves-to-production life ~31 years** (Source: https://www.oil-india.com/files/investor_services_documents/Transcript_of_the_Analysts_and_Investors_Meet_on_28th_May_2025.pdf). Against that, Baghewala's 43,773 t/yr is **~0.65 % of OIL's total upstream output** (derived). Its value to OIL is as the **only thermal-EOR school in India** and as a proof point in the investor narrative.

In OIL's May 2025 investor deck, the EOR/IOR pillar lists, in order: *Hydraulic Sucker Rod Pumping Unit in Rajasthan fields; Plunger Lift System in North-eastern banks; Radial Drilling; **India's first Cyclic steam simulation (CSS) in Baghewala Field**; Polymer flooding in Naharkatiya; microbial EOR in Assam; CO2-based EOR in Naharkatiya* (Source: https://www.oil-india.com/files/investor_services_documents/Investor_Presentation_May_2025.pdf). **Two of the seven EOR bullets are Rajasthan/Baghewala.**

### 3.2 OIL's digital programme — this is the frame SIH26120 sits inside

- **Project DRIVE** — *Digital Readiness for Innovation & Value in E&P* — launched **2019**. Phase 1 delivered **11 digital initiatives**, including **AI-enabled drone surveillance, real-time monitoring of drilling and production operations, and advanced analytics for decision support** (Source: https://www.oil-india.com/files/financial_results_documents/OIL_India_Annual_Report_2024_25.pdf ; https://www.oil-india.com/index.php/digitalfootprint).
- **DRIVE 2.0** — establishes a **state-of-the-art Command-and-Control Centre**, an **IT–OT integration framework**, cyber risk management, and wider adoption of **AI, robotics, drones** and Industry 4.0 (Source: same annual report).
- Midstream digital: **AI-driven SCADA**, **corrosion-rate prediction engine**, pipeline intrusion detection, and **5× faster leak detection via acoustic sensing and gradient-boosting predictive models** (Source: https://www.oil-india.com/files/investor_services_documents/Investor_Presentation_May_2025.pdf).
- Management framing: "tech-led efficiency … we continue to embed technology across the value chain, from integrated seismic and drilling, to **digital reservoir modelling** and advanced development planning" (Source: https://www.oil-india.com/files/investor_services_documents/Transcript_of_the_Analysts_and_Investors_Meet_on_28th_May_2025.pdf).

**Pitch implication:** frame the digital twin as **"the Baghewala node of DRIVE 2.0's Command-and-Control Centre"**, and reuse OIL's own vocabulary — *IT-OT integration, condition-based monitoring, digital reservoir modelling*. Gradient boosting already has an OIL precedent (leak detection), so an ML component in the twin is a continuation, not a novelty.

### 3.3 OIL's SIH participation history

- **SIH 2026:** OIL has posted **four** problem statements, all under **Smart Automation** — **SIH26120** (Baghewala CSS+SRP digital twin), **SIH26121** (*eRTMAC-NWIS: AI-powered offset-well knowledge and decision-support platform for drilling operations*), **SIH26122** (*Intelligent data capture & schedule-linking layer for infrastructure project management*), plus a fourth in the same theme (Source: https://zaidsayyed.in/tools/sih-problem-statements/theme/smart-automation ; https://www.blinknbuild.in/sih).
- **Prior years (SIH 2023/2024/2025):** **NOT FOUND.** No OIL-sponsored problem statement, winning team, or post-hackathon adoption could be confirmed for any earlier edition. PS 1653 of SIH 2024, which surfaced in searching, is *"Web Based Selector Applicant Simulation Software"* and is **not** an Oil India statement (Source: https://www.kaggle.com/datasets/adharshinikumar/sih-2024-ps-with-winning-teams-and-solutions). **Do not claim OIL has a SIH track record.** If asked, the honest and safer line is: *"OIL has put four problem statements into SIH 2026, three of them clearly operational rather than cosmetic — that reads like a first serious ask, not a PR exercise."*

---

## 4. India heavy-oil and policy context

### 4.1 Import dependence — the number that justifies the whole exercise

India's crude import dependence hit a **record ~88.6–88.7 %** on PPAC data, with self-sufficiency at just **11.8 %**; domestic crude output has slid from a **peak of 35.9 MMT in FY12** to roughly **26–28 MMT in FY26**, mainly on ageing fields; dependency is projected to reach **~92 % by 2035** (Source: https://theprint.in/economy/indias-crude-import-dependence-rises-to-record-88-7-as-domestic-output-continues-to-decline/2998114/ ; https://www.ey.com/en_in/insights/tax/economy-watch/india-s-petroleum-economy-import-dependence-and-unanticipated-shocks). **Every barrel of heavy oil left in the ground at Baghewala is a barrel imported.**

The April 2026 news cycle explicitly tied Baghewala's record output to **Strait of Hormuz disruption** and the search for domestic supply (Source: https://www.businesstoday.in/india/story/hormuz-blocked-india-turns-to-thar-desert-oil-india-ramps-up-crude-output-from-rajasthan-field-524088-2026-04-05).

### 4.2 Resource base

- Bikaner–Nagaur basin heavy-oil discovered volume is reported as **935 million barrels** across the Jodhpur sandstone, Bilara dolostone and Hanseran siltstones (Source: https://www.nature.com/articles/s41598-022-14831-5 — the figure appears in indexed copy of this paper alongside the porosity ranges; **flagged as single-source, not independently re-verified in the fetched text**). At ~7.3 bbl/t that is roughly **128 million tonnes in place** (derived). Against FY26 production of 43,773 t, the field is producing **~0.03 % of the basin's discovered heavy oil per year** — the upside case in one number.
- Rajasthan holds ~**34–35 MMT** of India's ~**671 MMT** proven crude reserves (~6 %), and produced >**5 MMT** in 2023-24, overwhelmingly from Cairn's Barmer basin fields (Source: https://www.statesinsights.com/crude-oil-producing-states-in-india/).
- **A consolidated national "heavy oil in-place" figure for India was NOT FOUND** from DGH/ONGC. Do not quote one.

### 4.3 EOR policy

The Union Cabinet approved the **Policy Framework to Promote and Incentivize Enhanced Recovery (ER) / Improved Recovery (IR) / Unconventional Hydrocarbon (UHC) Methods on 2 January 2018** — eleven months before CSS started at BGW-8 (Source: https://pib.gov.in/newsite/PrintRelease.aspx?relid=183408 ; https://www.dghindia.gov.in/assets/downloads/5a61c49869d82Policy_Framework_to_Promote_and_Incentivize_Enhanced_Recovery_Methods_02012018.pdf). Provisions:

- **50 % waiver of cess on crude oil** and **75 % waiver of royalty on natural gas** from ER/UHC production;
- **up to 150 % business-income-tax deduction** on ER pilot-project expenditure (applicable to 31 March 2025);
- **mandatory screening** of every field by designated institutions, and **mandatory pilots** before commercial ER implementation;
- fiscal incentives run **120 months from commencement of ER production**; the policy itself has a **10-year sunset** from notification;
- an **Enhanced Recovery Committee** (MoPNG + DGH + upstream experts + academia) monitors implementation.

**The "mandatory screening and pilot before commercial rollout" clause is the policy hook for a digital twin:** a validated twin is exactly the screening-and-pilot-design instrument the policy demands, and it is how an SIH prototype becomes a compliance asset rather than a demo.

### 4.4 Neighbour context — Cairn/Vedanta in Barmer

Different basin (Barmer rift, Cretaceous–Tertiary), same state, and the obvious comparison a judge will reach for. Cairn Oil & Gas began **ASP (alkaline–surfactant–polymer) injection at Mangala** — described as **India's largest commercial ASP injection** and among very few worldwide — targeting a recovery lift from ~33 % toward ~60 %, now expanding across **Mangala, Bhagyam and Aishwariya** (Source: https://www.business-standard.com/markets/capital-market-news/cairn-oil-gas-commences-injection-of-asp-in-mangala-rajasthan-124061100585_1.html ; https://www.spglobal.com/energy/en/news-research/latest-news/crude-oil/020426-iew-2026-indias-cairn-looks-to-boost-output-from-rajasthan-fields-boost-offshore-exploration). The business was **carved out of Vedanta Ltd as Vedanta Oil & Gas Ltd and listed on NSE/BSE on 15 June 2026** (Source: https://91capital.substack.com/p/vedanta-oil-and-gas-paid-to-wait).

**The distinction to make cleanly:** Mangala is a **chemical** EOR problem in a good-quality, high-permeability reservoir with a waxy but pumpable crude. Baghewala is a **thermal** EOR problem in a poor-quality, sub-10 %-porosity, heterogeneous Infracambrian sand with a crude 100× more viscous. **They are not the same problem and the same optimisation logic does not transfer.**

---

## 5. Contradictions and gaps — with a recommendation for each

| # | Item | Source A | Source B | What to say on stage |
|---|---|---|---|---|
| 1 | **API gravity** | **17.6°** at Baghewala-1 (Mandal et al. 2021, https://link.springer.com/article/10.1007/s13202-021-01432-7 ; OGJ 2002) | **14–17°** current producing crude (SPE-535203, 2023); **14–18°** (GEOHORIZONS 2015); "~20°" DST at A1 (GEOHORIZONS); **17–19°** (SIH PS repos) | Say **"14–18° API, with the 1991 discovery test at 17.6°"**. It reconciles every source and shows you know the discovery number is not the production number. |
| 2 | **Viscosity** | **8,000–15,000 cP @ 50 °C** (SPE-535203) | **10,000–13,000 cP @ 50 °C** (https://www.oil-india.com/rajasthan-fields) | Quote **OIL's own 10,000–13,000 cP** — it is the operator's number and sits inside the SPE range. Mention the wider range as the published envelope. |
| 3 | **Porosity** | **< 10 %**, "poor porosity" at Baghewala (GEOHORIZONS 2015, OIL+SLB) | **16–25 %** Jodhpur sandstone basin-wide (Sci Rep 2022) | **Not a real conflict — explain it and win the point.** The 16–25 % is a *basin-wide formation-quality* range; the <10 % is *log-measured at the Baghewala anticline*. Baghewala's Jodhpur is a **shaly** sand facies. Say: *"the Jodhpur is a 16–25 % porosity sandstone regionally, but at Baghewala it is a shaly facies logging under 10 % — which is precisely why simple analytical inflow models fail here."* |
| 4 | **Depth** | ~**1,100 m** (SPE-535203) | ~**1,150 m** (https://www.oil-india.com/rajasthan-fields) | Say **"~1,100–1,150 m"**. Never a single decimal-precise figure. |
| 5 | **Well count** | **56 drilled / 34 producing** (https://www.oil-india.com/rajasthan-fields) | **52 drilled / 33 operational** (Apr 2026 news, https://www.businesstoday.in/india/story/from-dunes-to-diesel-how-thar-desert-is-powering-india-524228-2026-04-06) | Use **"52–56 wells drilled, ~33–34 producing, depending on snapshot date"**. Acknowledging the snapshot dependence reads as rigour, not vagueness. |
| 6 | **Current rate** | **>1,100 bbl/d** (OIL site) | **1,202 bbl/d** record (Apr 2026 news); **655 bbl/d** on 10 Jul 2025 (OIL PPT) | Quote **"a record 1,202 bbl/d in FY26, up ~70 % from 705 bbl/d"** — it is the most recent, most specific, and most flattering to OIL. |
| 7 | **Field district** | **Jaisalmer** district (PSU Watch, BusinessToday) | Bikaner–Nagaur basin naming and OIL's own page give no district | **Say "western Rajasthan, Bikaner–Nagaur sub-basin"** and skip the district. The district attribution is inconsistent across news sources and is not worth a correction from a judge. |
| 8 | **India domestic crude FY26** | **28 MMT** (Rau's IAS compilation) | **26.0 MMT** (EY, from PPAC) | Say **"~26–28 MMT, down from a 35.9 MMT peak in FY12"**. |
| 9 | **Import dependence** | **88.6 %** (10 months FY26, PPAC) | **">90 % in FY26"** (secondary) ; 88.7 % record (ThePrint) | Say **"~88–89 %, a record"**. Do not say 90 %+. |
| 10 | **Basin area** | **70,000 sq km** Bikaner–Nagaur | 126,000 sq km "Rajasthan basin" | Say **"~70,000 sq km Bikaner–Nagaur sub-basin"** and be ready to note the 126,000 figure is the whole Rajasthan onland basinal area. |
| 11 | **CSS credit** | "with technical assistance from **Belgrave Oil & Gas Corp., Calgary**" (OGJ 2018) | OIL/news framing: OIL's own achievement | Say **"India's first CSS, executed by OIL with technical assistance from Belgrave Oil & Gas of Calgary"**. Giving the credit is more credible than omitting it, and it is in OGJ. |
| 12 | **935 MMbbl basin heavy oil** | Sci Rep 2022 indexed text | Not repeated in any second independent source | **Use with a hedge** — "one published estimate puts basin heavy-oil discovered volume near 935 million barrels." Do not present as DGH-official. |

### Hard gaps — say "not found", never guess

- **Permeability** of the Jodhpur sand at Baghewala — NOT FOUND.
- **Net pay / net sand thickness** — NOT FOUND.
- **Achieved steam-oil ratio (SOR)** at Baghewala — NOT FOUND as a published number.
- **Quantified EDH production uplift** (SPE-535203 / 24OPES full text) — paywalled, NOT RETRIEVED.
- **Baghewala capex, SAGD timeline, or 2030 production target** — NOT FOUND in OIL's FY25 investor materials.
- **A consolidated Indian national heavy-oil in-place figure** — NOT FOUND.
- **Any OIL SIH problem statement or winner before 2026** — NOT FOUND.

---

## 6. Judge-room pack

### 6.1 Twelve Baghewala-specific quotables

1. "Baghewala is India's **only** field where cyclic steam stimulation is a production method rather than an experiment — India's first CSS started at well **BGW-8 in December 2018**, with technical assistance from Belgrave Oil & Gas of Calgary." (Source: https://www.ogj.com/drilling-production/production-operations/unconventional-resources/article/17296851/oil-starts-css-of-well-in-rajasthan)
2. "The oil is **not** heavy because bacteria degraded it. Biomarkers show it is **non-biodegraded**, generated in the **early oil window** from a sulphur-rich Infracambrian carbonate source — it was born heavy." (Source: https://pubs.geoscienceworld.org/aapg/aapgbull/article-abstract/79/10/1481/39084/Recognition-of-an-Infracambrian-Source-Rock-Based)
3. "The whole petroleum system fits in about **1,500 metres** of Lower Palaeozoic cover over Malani rhyolite basement. That is why the reservoir is shallow, cold at ~50 °C, and the oil never cracked." (Source: https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf)
4. "Source rock is the **Bilara–Hanseran** carbonate-evaporite sequence at **5–6 % TOC**; the oil migrated from Bilara shales into the shaly Jodhpur sand of the **Baghewala anticline**, sealed by Bilara carbonate." (Sources: https://www.nature.com/articles/s41598-022-14831-5 ; https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf)
5. "**14–18° API, 10,000–13,000 cP at 50 °C.** That decoupling is the whole engineering problem — a generic API-to-viscosity correlation is wrong here by roughly two orders of magnitude." (Sources: https://www.oil-india.com/rajasthan-fields ; https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/2-23APOG/535203)
6. "FY26 was a record: **43,773 tonnes**, up 33.5 %, and **1,202 barrels/day**, up ~70 % from 705 — on **19 CSS wells**, 72 % more than the year before, and **13 new wells** against 9." (Source: https://www.businesstoday.in/india/story/from-dunes-to-diesel-how-thar-desert-is-powering-india-524228-2026-04-06)
7. "From **218 tonnes in FY2016-17 to 43,773 tonnes in FY2025-26** — a 200-fold increase in nine years, almost entirely attributable to thermal EOR." (Sources: OIL internal PPT; https://psuwatch.com/newsupdates/oil-india-ramps-up-crude-production-from-rajasthans-thar-desert)
8. "Well **BGW#40** carried the **first-ever fishbones drilling deployment in an Indian heavy-oil reservoir**, alongside barefoot completion, vacuum-insulated tubing, thermal wellheads and electric downhole heaters." (Source: https://www.oil-india.com/rajasthan-fields)
9. "There is no pipeline. Crude is **heated in tanks with steam to restore flowability**, trucked in bowsers to ONGC's North Santhal CTF at Mehsana, and only then piped to IOCL Koyali. Flow assurance is a **surface** problem here, not just a downhole one." (Source: https://www.oil-india.com/rajasthan-fields)
10. "OIL's **SAGD** is the stated next step at Baghewala — so a twin that only models CSS has a shelf life. Ours is built so the thermal module generalises." (Source: https://www.oil-india.com/rajasthan-fields)
11. "India's EOR policy of **2 January 2018** — 50 % cess waiver, 75 % gas royalty waiver, 150 % tax deduction on pilots — **mandates screening and a pilot before commercial ER rollout**. A validated digital twin is the cheapest way to satisfy that mandate." (Source: https://pib.gov.in/newsite/PrintRelease.aspx?relid=183408)
12. "Baghewala's cross-border twin is **Karampur-1** on Pakistan's Punjab Platform, and its global family is the **Huqf Group of South Oman** — same latest-Neoproterozoic rift, same carbonate-evaporite source, same heavy sulphurous oil." (Source: https://www.nature.com/articles/s41598-022-14831-5)

### 6.2 Five questions only someone who really studied the field can answer

**Q1. Why is Baghewala's oil 10,000+ cP when 17° API crude is normally around 100 cP?**
Because it is **not biodegraded**. It came out of a **sulphur-rich, clay-starved Infracambrian carbonate-evaporite source (Bilara–Hanseran)** in the **early oil window** — a Type II-S kerogen expels early, and what it expels is loaded with sulphur-bridged resins and asphaltenes. The basin's total sedimentary cover is only ~1,500 m, so those molecules were never thermally cracked. The result is an oil that is only moderately heavy by density but extraordinarily viscous. **Practical consequence: API-based viscosity correlations must be discarded; the model must be anchored on the field's own measured μ–T curve.** (Sources: https://pubs.geoscienceworld.org/aapg/aapgbull/article-abstract/79/10/1481/39084/Recognition-of-an-Infracambrian-Source-Rock-Based ; https://www.ogj.com/home/article/17234026/early-work-indicates-prospectivity-in-bikaner-nagaur-basin-india ; https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf)

**Q2. Published porosity for the Jodhpur sandstone is 16–25 %, but OIL's own paper says under 10 % at Baghewala. Which is right?**
Both. **16–25 % is the basin-wide Jodhpur sandstone range** (Sci Rep 2022); **<10 % is what the logs actually read at the Baghewala anticline**, where the Jodhpur is a **shaly** sand facies (OIL + Schlumberger, GEOHORIZONS 2015). The same OIL/SLB paper notes heavy oil at Baghewala is found where the sand has *relatively* higher porosity — the local sweet spots inside a poor-quality envelope. **This is exactly why they had to run pre-stack simultaneous inversion at all: acoustic impedance alone could not separate brine sand from oil sand, so they derived shear impedance too.** (Sources: https://www.nature.com/articles/s41598-022-14831-5 ; https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf)

**Q3. What was the single biggest data problem OIL faced in characterising this reservoir, and how did they solve it?**
**No measured shear-sonic (Vs) log existed in any well penetrating the Jodhpur formation.** Without Vs there is no wavelet estimation for the angle stacks and no low-frequency shear-impedance background model, so simultaneous inversion is impossible. OIL and Schlumberger applied the **Greenberg–Castagna (1992) rock-physics model** to predict Vs from measured Vp and lithology volume fractions, calibrated the coefficients on offset well **O1**, validated the prediction against measured Vs in offset well **O2** across both Bilara and Jodhpur, then propagated it to well **A1** and the rest of the field. **The lesson for a digital twin: at Baghewala, the missing-measurement problem is chronic and the accepted local practice is physics-constrained inference, not interpolation.** (Source: https://spgindia.org/geohorizons_vol_20_january_2015/technical_articles7_january_2015_30_12_14.pdf)

**Q4. Baghewala produces under 1,300 bbl/d. Why does OIL care so much about it?**
Three reasons, none of them volume. **(a) It is India's only thermal-EOR school** — the only field where OIL, or anyone in India, has run CSS at scale, banked **39+ cycles** by mid-2025, and now plans SAGD. **(b) It is the resource-unlock case:** one published estimate puts Bikaner–Nagaur discovered heavy oil near **935 million barrels**, of which Baghewala is producing roughly **0.03 % a year**. **(c) It is national-security optics:** with import dependence at a record ~88.7 % and domestic output down from a 35.9 MMT peak in FY12 to ~26–28 MMT, a field that grew 200× in nine years is the story MoPNG wants told — which is exactly why the April 2026 Hormuz coverage led with Baghewala. (Sources: https://www.nature.com/articles/s41598-022-14831-5 ; https://theprint.in/economy/indias-crude-import-dependence-rises-to-record-88-7-as-domestic-output-continues-to-decline/2998114/ ; https://www.businesstoday.in/india/story/hormuz-blocked-india-turns-to-thar-desert-oil-india-ramps-up-crude-output-from-rajasthan-field-524088-2026-04-05 ; https://www.oil-india.com/rajasthan-fields)

**Q5. Has OIL already tried alternatives to CSS at Baghewala, and what does that tell you about the optimisation problem?**
Yes, and the sequence matters. **~2006:** chemical floods and steam from portable/mobile generators. **Dec 2018:** first formal CSS at BGW-8. **2023:** an **Electrical Downhole Heater trial in a horizontal well**, designed as a controlled comparison against non-EDH offsets (SPE-535203), followed by a 2024 SPE paper explicitly on "using downhole electric heaters to **complement or replace** CSS operations." **Also in the field:** diluent injection, hydraulic SRPs, VIT and thermal wellheads, fishbone drilling at BGW#40, barefoot completions — and SAGD on the roadmap. **What that tells you:** OIL is not looking for one winning technology; it is running a **portfolio of heat-delivery and lift options and needs a way to choose among them per well, per cycle.** That is precisely the gap a well-to-surface digital twin fills — the decision is not "should we steam?", it is "for *this* well, this month, is it a steam cycle, an EDH, a diluent change, or a pump reconfiguration?" (Sources: https://www.ogj.com/drilling-production/production-operations/unconventional-resources/article/17296851/oil-starts-css-of-well-in-rajasthan ; https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/2-23APOG/535203 ; https://onepetro.org/SPEOGWA/proceedings-abstract/24OPES/24OPES/D031S035R002/544525 ; https://www.oil-india.com/rajasthan-fields)

---

## 7. Source-quality ledger

**Tier 1 — peer-reviewed / operator-published, quote freely:**
*AAPG Bulletin* v.79 no.10 p.1481 (Baghewala-1 biomarkers); *Scientific Reports* 12:11102 (Yasin et al. 2022); *J. Petrol. Explor. Prod. Technol.* doi:10.1007/s13202-021-01432-7 (Mandal, Saha & Kumar 2021); *GEOHORIZONS* Jan 2015 pp.47–50 (Basha et al., OIL + Schlumberger); SPE-535203 (2023); oil-india.com/rajasthan-fields; OIL Annual Report 2024-25; OIL Investor Presentation May 2025 and Analysts Meet transcript 28 May 2025; PIB/DGH EOR policy 2018; Oil & Gas Journal (2002, 2018).

**Tier 2 — mainstream news, reliable for FY26 production numbers:** BusinessToday, Business Standard, PSU Watch, Telangana Today, India Narrative (all April 2026, all tracing to the same OIL release — treat as **one** source, not five).

**Tier 3 — use with a hedge, never alone:** the SlideShare copy of an OIL internal Baghewala deck (12 Jul 2025) — richest technical source found, internally consistent, but an uploaded internal document; DiscoveryAlert and similar aggregator write-ups; the 935 MMbbl figure.

**Not obtained:** DGH Rajasthan Basin PDF (server returned a shell page), NDR India well data, SPE 24OPES full abstract (403), AAPG Datapages full text (403), ResearchGate PDFs (403). If the team can get institutional access to OnePetro, **SPE-535203 and SPE-24OPES full texts are the highest-value remaining targets** — they are the only places a quantified Baghewala EDH-vs-CSS comparison is likely to exist.
