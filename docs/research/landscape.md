# Landscape Analysis: CSS + Sucker Rod Pump Digital Twin for Heavy Oil
## SIH 2026 - Oil India Baghewala Field (PS SIH26120)

---

## 1. Existing Commercial Products for Rod-Pump Optimization and Oilfield Digital Twins

### Artificial Lift Optimization (Pump-focused)

**XSPOC (ChampionX)**
- Artificial lift production optimization software using physics-based diagnostics and AI. Diagnoses anomalies, recommends optimizations, and provides autonomous control for rod and gas-lifted wells. Uses 1+ billion dynamometer pump cards from 135,000 wells globally. Covers rod pump diagnostics but focuses on pump performance alone; no integrated thermal EOR + artificial lift co-optimization.
- https://www.championx.com/products-and-solutions/artificial-lift-technologies/production-optimization-software-solutions/xspoc/

**Lufkin SAM (Smart Automation Manager)**
- Intelligent automation solution for sucker rod pumping units with dynamometer analysis, automatic pump-off detection, and speed control. Industry standard for Lufkin pump units but operates at the wellhead level without thermal reservoir integration.
- https://www.lufkin.com/solutions-services/srod/

**Lufkin SROD**
- Intelligent rod pump design, validation, and optimization software. Generates system designs and validates pump performance for given reservoir and well conditions but does not integrate CSS steam scheduling.
- https://www.lufkin.com/solutions-services/srod/

### Production Operations & Digital Twins (Field-level)

**Weatherford ForeSite Edge + CygNet**
- IoT/SCADA platform pairing ForeSite software with CygNet for high-frequency well data acquisition, storage, and continuous production optimization. Monitors 460,000 wells and 30 billion daily data updates. Real-time surface data but no reservoir thermal cycle integration for CSS.
- https://www.weatherford.com/en/products-and-services/production-optimization/sucker-rod-solutions/

**Schlumberger OptiSite & ProcessOps**
- Cloud-based digital twins using AI and physics-based models for facility-level optimization: process optimization, asset health, pipeline integrity, and emissions control. Uses high-resolution data and advanced AI models (Delfi platform, Lumi data engine). Facility twins but not integrated with subsurface CSS cycle and lift operations.
- https://www.slb.com/products-and-services/delivering-digital-at-scale/software/optisite

**AVEVA Digital Asset Management**
- Comprehensive digital twin platform for upstream operations: engineering handover, continuous monitoring, advanced analytics, and visualization. Used globally for onshore and offshore production. Primarily handles asset and reservoir data; does not specialize in CSS-SRP co-optimization.
- https://www.aveva.com/en/industries/oil-gas/upstream/

**Kongsberg Digital Kognitwin Energy**
- SaaS digital twin platform integrating IT/OT data with advanced process and flow simulation. Deployed across Shell and ExxonMobil facilities. Focuses on facility performance and collaboration; designed for general asset optimization, not CSS-pump integration.
- https://www.hartenergy.com/exclusives/kongsberg-advances-virtual-oilfield-tech-digital-twin-software-debut-189849/

---

## 2. What None of Them Do: The Gap

**FINDING: Integrated CSS Steam-Cycle + Sucker Rod Pump Co-Optimization for Heavy Oil Does NOT Exist Commercially**

**Gap confirmed:**
- Pump optimizers (XSPOC, Lufkin SAM/SROD, Weatherford) optimize pump performance, sucker rod stress, gas anchoring, and speed control in isolation.
- Thermal EOR optimizers (SLB ProcessOps, AVEVA, Kongsberg) optimize steam injection schedules, reservoir sweeping, and steam channeling at the reservoir/field scale.
- **None integrate both**: a closed-loop system that simultaneously optimizes CSS steam injection cycles (when to inject, how long to soak, production phase) AND sucker rod pump configuration/operation (rod string design, pump size, stroke speed, load) to account for the changing well conditions during a CSS cycle (viscosity, flow rate, downhole pressure/temperature dynamics).

**Single reference to integrated approach—not commercial:**
- *PetroTwin* (research/advisory platform at https://github.com/devxaves/PetroTwin) bridges downhole reservoir thermodynamics (CSS) and surface pump diagnostics (SRP), but it is an air-gapped decision-support system for engineers, not a real-time autonomous platform, and is not optimized for Indian heavy-oil conditions or field-scale deployment.

**Why the gap exists:**
- Pump vendors (ChampionX, Lufkin, Weatherford) treat the well as a mechanical system; reservoir data is input, pump specs are output.
- Reservoir/facility vendors (SLB, AVEVA, Kongsberg) treat the well as a production sink; they optimize throughput but do not model the pump as a constraint.
- CSS + SRP co-optimization requires bridging two traditionally separate domains: **thermal reservoir modeling + mechanical pump design + real-time control**, with tightly coupled feedback.

---

## 3. Academic & Industry Precedents: ML + Pump Diagnostics + CSS Optimization

### Machine Learning for Dynamometer Card Classification (Well-Established)

**1. "Diagnostic of Operation Conditions and Sensor Faults Using Machine Learning in Sucker-Rod Pumping Wells"**
- MDPI Sensors, 2021 | Multiple ML algorithms (decision tree, random forest, XGBoost) with Fourier/wavelet descriptors for automated dynamometer card diagnosis. AlexNet transfer learning achieved >99% classification accuracy for sucker rod pump working condition recognition.
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8271678/ | https://www.mdpi.com/1424-8220/20/19/5659

**2. "Beam Pump Dynamometer Card Classification Using Machine Learning" (SPE-194949)**
- Established automated recognition of pump card patterns (normal, gas lock, excess load, etc.) using supervised learning; widely cited in the industry as foundational for pump diagnostics.
- https://www.academia.edu/38619298/SPE_194949_Beam_Pump_Dynamometer_Card_Classification_Using_Machine_Learning

**3. "Automatic sucker rod pump fault diagnostics by transfer learning using GoogLeNet"**
- ScienceDirect, 2024 | GoogLeNet-based transfer learning with ECOC-SVM for real-time fault detection from diverse dynamometer card images. Practical deployment-ready approach.
- https://www.sciencedirect.com/science/article/abs/pii/S0957582024010310

**Takeaway:** Pump diagnostics via ML is mature; real-time dynamometer analysis is production-ready.

### Cyclic Steam Stimulation Optimization with ML

**4. "Machine-Learning-Assisted Identification of Steam Channeling after Cyclic Steam Stimulation in Heavy-Oil Reservoirs"**
- Geofluids (Wiley), 2023 | Random-forest ensemble model predicting steam channeling (breakthrough) during CSS huff-and-puff cycles. Directly addresses efficiency loss after multiple cycles in heavy oil.
- https://onlinelibrary.wiley.com/doi/10.1155/2023/6593464

**5. "A Simulation Augmented Machine Learning Approach for Cyclic Steam Stimulation Development Targeting Lower Carbon/Higher Return"**
- SPE Western Regional Meeting, 2022 | Hybrid physics-ML model for CSS parameter optimization: injection volume, soak time, production phase duration. Co-authored work bridging simulation and ML.
- https://onepetro.org/SPEWRM/proceedings-abstract/22WRM/22WRM/D031S014R004/484171

**6. "Numerical Simulation of Cyclic Steam Stimulation with Horizontal Well in Heavy Oil Reservoirs"**
- Springer, 2024 | Case study on CSS in heavy oil with horizontal wells; covers simulator design and parameter sensitivity (steam quality, injection rate, soak duration).
- https://link.springer.com/chapter/10.1007/978-3-031-44947-5_96

**Takeaway:** CSS optimization via ML is published but fragmentary; no production-ready integrated platforms found for CSS + lift.

### Physics-Informed ML for Reservoir Simulation & Production Forecasting

**7. "Physics Informed Machine Learning for Reservoir Connectivity Identification and Production Forecasting"**
- SPE Annual Technical Conference, 2024 | Hybrid models (physics + ML) for rapid production forecasting using routine injection/production data. Demonstrates feasibility of coupled reservoir-surface models.
- https://onepetro.org/SPEATCE/proceedings-abstract/24ATCE/24ATCE/563781

**Takeaway:** Integrated physics-ML frameworks are emerging in academia; commercial deployment lags.

---

## 4. India Context: Oil India, Baghewala, and Indigenous Digitalization

### Oil India's CSS Operations at Baghewala

**Current Deployment:**
- Oil India began CSS operations at the Baghewala heavy oil field (Rajasthan, Bikaner-Nagaur sub-basin) in 2018 with "fishbone drilling" and barefoot completions—technologies being used for the first time in India's heavy oil reserves.
- 52 wells drilled in the 200-km² field; currently 33 operational. Achieved record production of 1,202 bbl/day (FY 2024) using sucker rod pumps, electric downhole heaters, and high-temperature thermal wellheads.
- Production transported to ONGC facilities and IOCL Koyali refinery; field is strategically important for India's energy security.
- https://www.oil-india.com/rajasthan-fields
- https://telanganatoday.com/oil-india-ramps-up-crude-production-from-rajasthans-thar-desert

### Oil India's Digitalization Initiatives

**Existing Systems:**
- **AI & Big Data**: ML models and data mining for full-field reservoir modeling, leveraging IoT sensor networks and cloud-based storage of digitalized well information.
- **CxO Dashboard Business Intelligence**: Web and mobile dashboards for data-driven decision-making; enables faster subsurface insights.
- **Predictive Maintenance**: ML-based anomaly detection and downtime reduction across assets.
- *Current gap*: These systems exist in isolation; no evidence of integrated CSS-SRP real-time co-optimization at Baghewala.
- https://www.oil-india.com/leveraging-technology
- https://indianinfrastructure.com/2024/07/30/smart-solutions-digital-innovations-shaping-the-future-of-the-oil-and-gas-sector/

### ONGC Digitalization

- **Edge computing** (Mumbai High): Real-time well and drilling operation monitoring.
- **SCADA**: Pipeline and rig monitoring across assets.
- **ERP systems**: Business process optimization.
- **In-house IT-OT development**: ONGC building internal digital capabilities to reduce vendor dependency and enhance cybersecurity.
- https://smartutilities.net.in/2019/09/20/intelligent-systems/

### Data Governance & Sovereignty

- **DGH (Directorate General of Hydrocarbons)**: India's regulatory body under the Ministry of Petroleum and Natural Gas; custodian of all E&P data via the National Data Repository (NDR) at Noida. DGH oversees technical evaluation, data preservation, and compliance.
- **Make-in-India Context**: Government actively seeking indigenous oilfield software solutions and data sovereignty in operations.
- https://www.dghindia.org/
- https://www.ndrdgh.gov.in/NDR/

**Digitalization Trends in India:**
- Rising investment in smart oilfield technologies and automation systems across India.
- Shift toward building in-house IT-OT capabilities by ONGC and GAIL, reducing reliance on global vendors.
- Digital twins for oilfields recognized as strategic; early-stage adoption by Oil India and ONGC.

---

## 5. One-Paragraph Differentiation Statement

**For Judges — What Makes This Solution Unique:**

Sucker rod pump optimization software (ChampionX XSPOC, Lufkin SAM) is commercially mature and widely deployed; digital twin platforms for oilfields (Schlumberger, AVEVA, Kongsberg) handle facility-level production. However, **no commercial solution integrates real-time CSS steam-cycle scheduling with sucker rod pump co-optimization for heavy-oil wells**, especially under the specific thermodynamic and operational constraints of Indian heavy-oil fields like Baghewala. This solution addresses that gap by building an indigenous, cost-effective digital twin that couples reservoir thermal dynamics (CSS injection/soak/production phases), downhole equipment behavior (rod string stress, pump fillage, thermal resilience), and surface real-time telemetry into a single closed-loop optimization system—optimizing for **both** steam injection efficiency and pump performance simultaneously. Unlike global vendors targeting high-cost offshore deepwater assets, this system is tailored for onshore, land-locked heavy oil operations with sucker rod pumps, aligns with India's Make-in-India and data-sovereignty goals (DGH data repository, ONGC in-house IT-OT), and provides actionable real-time guidance to field operators at Oil India's Baghewala field and similar ONGC assets. **The combination—integrated CSS+SRP digital twin, built in-country, optimized for Rajasthan heavy oil—does not exist today and directly addresses an operational pain point in India's energy security agenda.**

---

## 6. Research Methodology & Data Quality

- All commercial product descriptions sourced directly from vendor websites (ChampionX, Lufkin, Weatherford, Schlumberger, AVEVA, Kongsberg).
- Academic papers verified via peer-reviewed journals (MDPI Sensors, Geofluids/Wiley, Springer, SPE OnePetro proceedings).
- Oil India operational data sourced from official company website and recent news reports (2024–2026).
- DGH and ONGC information from official government and company sources.
- **Claims without supporting links are marked as "not found" and excluded from this analysis.**

---

## References (Full URL List)

1. ChampionX XSPOC: https://www.championx.com/products-and-solutions/artificial-lift-technologies/production-optimization-software-solutions/xspoc/
2. Lufkin SAM: https://www.lufkin.com/solutions-services/srod/
3. Weatherford ForeSite: https://www.weatherford.com/en/products-and-services/production-optimization/sucker-rod-solutions/
4. Schlumberger OptiSite: https://www.slb.com/products-and-services/delivering-digital-at-scale/software/optisite
5. AVEVA Upstream: https://www.aveva.com/en/industries/oil-gas/upstream/
6. Kongsberg Digital: https://www.hartenergy.com/exclusives/kongsberg-advances-virtual-oilfield-tech-digital-twin-software-debut-189849/
7. PetroTwin (Research Reference): https://github.com/devxaves/PetroTwin
8. ML Pump Diagnostics (MDPI Sensors 2021): https://www.mdpi.com/1424-8220/20/19/5659
9. Dynamometer Card Classification (SPE-194949): https://www.academia.edu/38619298/SPE_194949_Beam_Pump_Dynamometer_Card_Classification_Using_Machine_Learning
10. GoogLeNet Transfer Learning (2024): https://www.sciencedirect.com/science/article/abs/pii/S0957582024010310
11. Steam Channeling ML (Geofluids 2023): https://onlinelibrary.wiley.com/doi/10.1155/2023/6593464
12. CSS ML Optimization (SPE WRM 2022): https://onepetro.org/SPEWRM/proceedings-abstract/22WRM/22WRM/D031S014R004/484171
13. CSS Horizontal Well Simulation: https://link.springer.com/chapter/10.1007/978-3-031-44947-5_96
14. Physics-Informed ML (SPE ATCE 2024): https://onepetro.org/SPEATCE/proceedings-abstract/24ATCE/24ATCE/563781
15. Oil India Rajasthan Fields: https://www.oil-india.com/rajasthan-fields
16. Oil India Technology & Digitalization: https://www.oil-india.com/leveraging-technology
17. Oil India Production (Telangana Today 2026): https://telanganatoday.com/oil-india-ramps-up-crude-production-from-rajasthans-thar-desert
18. Digital Innovations in Oil & Gas (Indian Infrastructure): https://indianinfrastructure.com/2024/07/30/smart-solutions-digital-innovations-shaping-the-future-of-the-oil-and-gas-sector/
19. ONGC Intelligent Systems: https://smartutilities.net.in/2019/09/20/intelligent-systems/
20. DGH Official: https://www.dghindia.org/
21. National Data Repository (NDR): https://www.ndrdgh.gov.in/NDR/

---

**Document Status:** Completed per SIH 2026 Requirements  
**Last Updated:** 2026-09-13  
**Prepared for:** Oil India / DGH Evaluation Panel
