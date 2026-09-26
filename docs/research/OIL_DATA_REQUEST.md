# Data Request to Oil India Limited — Baghewala CSS/SRP Digital Twin (SIH26120)

*Draft letter + prioritised data-request table, for the team to route through the SIH SPOC / OIL
mentor. Placeholders (`[ ]`) must be filled in before sending — no OIL contact names/emails are
assumed here.*

---

## Letter

**To:** [SPOC name], Smart India Hackathon 2026 — Problem Statement SIH26120
**Organisation:** Oil India Limited
**From:** SIH 2026 Team, MNIT Jaipur, PS SIH26120 — Team Lead: [team lead name], [date]
**Subject:** Request for Baghewala field data to calibrate our CSS/SRP digital-twin prototype

Respected Sir/Madam,

We are a Chemical Engineering + Software team from MNIT Jaipur working on PS SIH26120, a
physics-based digital twin that simulates Cyclic Steam Stimulation (CSS) and Sucker-Rod Pump
(SRP) operations for a heavy-oil well and recommends steam/soak/SPM set-points to raise oil
recovery per tonne of steam. Our twin currently runs on public literature values and typical
industry placeholders where Baghewala-specific data is not publicly available, and a handful of
its constants — noted below — visibly dominate its output uncertainty. Even a small, anonymised
sample of real Baghewala cycle records would let us replace these assumptions with a fitted,
field-calibrated model rather than a literature-only simulator, which is the single biggest
improvement we can make before the final round. We have kept this request to the minimum data
needed and are glad to sign any NDA or data-handling undertaking OIL requires.

We would be grateful for whichever items below OIL's team is able to share, in whatever
approximate or aggregated form is convenient — even 8-10 representative cycles from one or two
wells (e.g. BGW-8, BGW-9) would materially improve our model.

Thank you for your consideration and for hosting this problem statement.

Yours sincerely,
[team lead name]
On behalf of the SIH 2026 Team, MNIT Jaipur (PS SIH26120)
[team lead phone/email]

---

## Prioritised data request

*Reordered 27 Sep (rev 12, physics wave 4) around the model's live open questions:
whether the rod-float thesis is real, whether the cold well is really unpumpable, and
whether the steam is really steam at the sandface. Items 1–4 below are the direct,
one-measurement answers to those three questions; items 5+ are the same structural
gaps carried forward from earlier revisions. Items 12–15 are new asks from rev 13
(physics wave 5, operating policy as a control): the float-response practice
question now decides more money than any set-point, and rod damage, net-of-levies
pricing and the injectivity gate are all currently unpriced or unconfirmed.*

| # | Item requested | Why we need it (model constant it fixes) | Minimum acceptable form | Sensitivity |
|---|---|---|---|---|
| 1 | **Water-cut-vs-time log for one full CSS cycle** | Our rev-12 model treats water cut as a *state* (condensate flowback decaying to a formation-water floor, not a constant 85%) — this is the single measurement that would confirm or refute the whole late-cycle rod-float thesis and pin `formation_water_cut` and `condensate_recovery_frac` directly, instead of `[ASSUMPTION]` | Even a handful of spot water-cut readings across one produce phase (date/day-of-cycle + %) | **H** |
| 2 | **One late-cycle dynamometer card, and one cold-well (pre-CSS or shut-in-then-restarted) dynamometer card** | Directly tests whether the rods actually float late in a real cycle (our recommendation is built entirely around a modelled float onset) and whether a cold Baghewala well is pumpable at all at low SPM (our model currently says it is **not**, at 45% water cut on the assumed 86-in unit — a strict test failure, not a fix) | Position-vs-load pairs (even ~20-30 points) from one late-cycle card and one cold-well card; our `ml/dyno_classifier.py` reads either format directly | **H** |
| 3 | **A static bottom-hole pressure (BHP) survey on one BGW well** | Fixes `reservoir.P_current_kPa` — currently a 9.4 MPa `[ASSUMPTION]` derived from "the near-well region must be depleted enough for 290°C steam to be physically steam," not a measurement; this single number resets the whole injectivity/steam-state calculation | One BHP reading (kPa or psi), any recent well | **H** |
| 4 | **Wellhead pressure and temperature logged together during one steam injection** | Directly resolves the steam-state (P–T) inconsistency our own review flagged: at the assumed pressures, 290°C injected fluid is not physically saturated steam at the sandface unless the reservoir is depleted below ~7.4 MPa | A few paired (P, T) readings during one injection job | **H** |
| 5 | **Per-cycle CSS records** (date, steam tonnes injected, soak days, SPM, stroke length, wellhead pressure, cumulative oil, days produced, and — if tracked — whether/when the rods floated) | Fits our calibration routine's free constants at once (`formation_water_cut`, `aof_ref_m3d`, `thickness_m`) and is the only way to check the recommendation's core premise: **OIL's actual current SPM and stroke, and their pull criteria**, all unknown and now the biggest lever in our model | Per cycle: `well_id, steam_t, soak_days, spm, oil_m3, produce_days` (+ `cutoff_m3d`, `peak_oil_m3d`, `sor`, `stroke_in`, `p_wellhead_kgf_cm2` if available). **10 cycles from 1-2 wells is enough to fit.** | **H** |
| 6 | **A lab W/O emulsion viscosity at 30%, 45% and 60% water cut**, for Baghewala or nearby crude | Fixes the Pal–Rhodes emulsion parameter `φ*` (currently 0.84, `[ASSUMPTION]`, calibrated only to the centre of a published heavy-oil band) and the 10× viscosity cap near the water-cut inversion, both load-bearing for the float-onset timing | 3+ (water cut %, viscosity cP) pairs from any lab/PVT report | **M/H** |
| 7 | **OIL's realised bulk diesel price and crude realisation price** (₹/L or ₹/tonne HSD; ₹/bbl crude) | Fixes our steam-cost assumption (we currently guess a 30% bulk discount off retail diesel, unsourced) and the oil-price assumption — a top-ranked uncertain input, and one that moves the margin sign | A single representative ₹/unit figure for each, even if only an approximate FY26 average | **H** |
| 8 | **Net pay thickness and porosity from well logs** (Baghewala-1 or any well) | Fixes net steam-contacted pay thickness — we currently use a 12 m placeholder against a 50 m *gross* formation thickness from open literature, an unresolved 4x gap | A single net-pay figure (metres) and porosity (%), even approximate, for one well | **M/H** |
| 9 | **Pump specs** (bore/plunger diameter, stroke length options, rod taper, pumping-unit size/PRL rating) | Replaces our "typical" pump geometry and PRL cap (assumed 86-in unit, 113.9 kN rating) — our recommendation now depends on whether a slower/shorter-stroke unit is actually deployed | A single spec sheet or nameplate data for one representative well | **M** |
| 10 | **Steam generator log** (steam rate t/h, steam quality %) and **HSD (diesel) consumption per job** | Cross-checks our steam-cost-per-tonne estimate and the one-generator field-scheduling constraint (`ml/schedule.py` assumes ~74 t/d, unfitted) | A few representative job logs, or average rate/quality per job | **M** |
| 11 | **Workover / servicing cost per CSS job** | Fixes our assumed fixed cost per cycle (currently a placeholder ₹15 lakh/cycle) | A single ₹ figure per job, average is fine | **M** |
| 12 | **Actual float-response practice**: when the rods start floating, does the operator slow the pumping unit (VFD) or pull the well? | Rev-13 finding: this single choice is worth **more money than any set-point** (+₹12.9k/d if the baseline pulls, +₹3.3k/d if it VFD-holds like the recommendation, −₹3.9k/d if nothing is done — all per cycle-day, same recommendation) — our whole "fair baseline" comparison depends on which one OIL's operators actually do | A single sentence describing current SOP, or a handful of dynamometer-card timestamps around a known float event | **H** |
| 13 | **Rod-string failure / workover cost specifically attributable to running rods floating** (not a generic workover cost — see item 11) | Our recommended VFD-hold policy holds the floating index at the 0.6 alarm line for ~55–60 days a cycle (a graded damage index ~5× the `pull` policy's) — **this cost is entirely unpriced in our model today**, so we cannot yet tell OIL whether the extra oil is worth the extra rod wear | A single ₹/event figure, or an observed rod-string life (cycles or months) under a "runs floating" vs. "pulls on float" practice | **H** |
| 14 | **Realised price net of royalty, OID cess and any other levies** (or the exact percentages/structure OIL nets against — we assumed 20% royalty + 20% cess, cross-checked only against OIL's own FY25 Annual Report exchequer table, which caps total levies at ~35%) | We can only guess at OIL's own P&L view of CSS economics; on our current net-of-levies deck (~₹3,600/bbl) every feasible recommendation is negative against a shut-in cold well, so this number directly answers "is CSS even profitable" on OIL's own basis | A single ₹/bbl net-of-levies realisation figure, or the levy percentages/structure applied to Baghewala crude | **H** |
| 15 | **Injection pressure log across multiple jobs** (wellhead pressure over time, plus any noted injectivity/step-rate behaviour) — not just the single paired reading in item 4 | Our rev-13 injectivity gate (≥300–400 kPa sandface margin over reservoir pressure) rejects the 85 kgf/cm² floor used in earlier revisions in favour of 89 kgf/cm²; a real log would confirm whether our new floor is itself conservative or already tight | A handful of (wellhead pressure, date) pairs across 2+ jobs, ideally flagging any injection-rate/pressure anomalies noticed at the time | **M/H** |
| 16 | **The VFD's actual minimum speed (turndown), on whichever unit OIL runs at Baghewala** | Our model slows the stimulated well's pump to a **2-spm floor** before it counts a float alarm, but credits the "pumpable" cold-well counterfactual at **0.53 spm** — an internal inconsistency a technical re-score flagged. This one number decides almost the whole fair, same-policy gain: at a 2-spm floor the gain is +₹3,332/cycle-day; at 0.5 spm (matched to the cold well) it is **≈ ₹0**. We cannot resolve this ourselves | A single number: the lowest SPM the beam-pump VFD (or motor) can sustain in continuous operation, and whether that differs between a stimulated and an unstimulated well | **H** |
| 17 | **OIL's actual pull/produce-end criterion** — at what rate, water cut, or floating-index reading (if measured at all) does an operator actually pull a floating well off production, versus our assumed 1.3 m³/d rate cutoff | Our whole "baseline" is built on a cutoff **we chose**, not one OIL uses; the same re-score found 87% of the fair gain traces to this cutoff plus the stroke-length assumption. Knowing OIL's real criterion would let us stop assuming one | A sentence describing the current rule of thumb (a rate, a time floor, an operator's judgement call, or "we don't track it that precisely") | **H** |

*(Sensitivity H/M/L reflects both our uncertainty-quantification sweep over the twin's
most uncertain inputs and, for items 1–4, how directly the item answers an open
physics question — not solely UQ variance ranking.)*

## What we give back

In return, OIL receives a **calibrated digital twin fitted to its own Baghewala data**: a
per-well recommendation for steam volume, soak duration and pump speed that maximises margin
per cycle-day (not just steam-oil ratio) within the well's rod-floating safety limit, plus a
transparent report of which constants were fitted and how confidently. No data leaves the team —
all fitting runs locally against our open-source codebase, results can be shared as aggregated
tables/plots only if preferred, and we are willing to sign an NDA or any data-confidentiality
undertaking OIL's legal/data team requires before any file changes hands.

---

## हिंदी में संक्षिप्त नोट (WhatsApp/फोन फॉलो-अप के लिए)

नमस्ते [SPOC name] जी,

हम SIH 2026 की MNIT Jaipur टीम हैं, PS SIH26120 (Baghewala CSS/SRP digital twin) पर काम कर रहे
हैं। हमने ऊपर एक formal data request भेजी है — अगर संभव हो तो कुछ wells के 8-10 CSS cycles का
डेटा (स्टीम टन, soak days, cumulative oil, SPM) मिल जाए तो हमारा मॉडल काफी बेहतर हो जाएगा। कोई भी
NDA sign करने को तैयार हैं। कृपया सुविधानुसार बताएं कि यह डेटा किससे/कैसे मिल सकता है।

धन्यवाद,
[team lead name], MNIT Jaipur
