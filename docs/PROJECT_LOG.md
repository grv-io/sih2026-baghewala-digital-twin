# PROJECT LOG — SIH 2026 · PS SIH26120 · Baghewala CSS + SRP Digital Twin

> §1–§3 and §6–§15 are dated history (13–27 Sep) and contain superseded numbers (24/24 tests, −30 %, 'no GitHub repo', rev-9 "1,600/0.70/4" recommendation, and §15's own rev-12 "+₹9,574/d" headline — superseded in turn, see §16). Current state = §2 status table, §5 numbers bible, and §16 (27 Sep: technical re-score → wave 5 → rev 13, operating policy as a control, fair baseline).

**Single source of truth for project state.** Written 2026-09-13 ~18:15 IST, at the end of
the first (and so far only) build day. Everything below was verified against the repo on
disk, `git log`, and a live `pytest` run — where the verbal handoff and the repo disagreed,
the repo wins and the discrepancy is called out in **§11 Corrections**.

Repo: `<repo>` · branch `main` · **13 commits**, all dated
2026-09-13, 16:18 → 18:14 IST (HEAD `1a4101f` as of that day) · pushed to
`github.com/grv-io/sih-baghewala` since 25 Sep 2026 — **remote exists**, commit count now
**~20** (see §12).

> **Late update, 18:16 IST** — two in-flight streams finished while this log was being
> written. Dashboard **v4 is now built** (four pages on disk) and the Hinglish
> **study-pack is complete (00–07)**. Sections below are updated; §11 records what
> changed relative to the handoff.

---

## 1. TL;DR (10 lines)

1. We are building **PS SIH26120** (Oil India Ltd): a digital twin that co-optimises Cyclic Steam Stimulation *and* the sucker-rod pump at the Baghewala heavy-oil field, Bikaner-Nagaur basin, Rajasthan.
2. Chosen out of **233** scraped SIH 2026 problem statements because it is the one where a Chemical Engineer is the differentiator, not a liability. Backup: SIH26165 (also OIL). Rejected: SIH26119 (solver trap), SIH26121 (kept as the *hedge* second PS, not rejected outright).
3. A working prototype exists end-to-end: `twin/` physics (**24/24 pytest, re-verified today**) → `ml/` XGBoost surrogate + Bayesian optimiser → `api/` FastAPI (3 endpoints, smoke-tested) → `dashboard/` (v3 live; v4 mid-build).
4. All reservoir/fluid/steam parameters are **real, sourced Baghewala values** (1,150 m, 11,500 cP @ 50 °C, steam 290 °C @ 0.65 quality), merged from SPE-23APOG-535203 + an OIL presentation (publicly posted on SlideShare; secondary source). Citations in `docs/research/baghewala_facts.md`, diff in `params/CHANGELOG.md`.
5. **The deck to submit is `ppt/final/SIH26120_Idea_Presentation_STRICT.pptx` / `.pdf`.** Everything else in `ppt/` is superseded and kept only for reference.
6. Headline claim framing is deliberately split: dashboard leads **−30 %** (SOR 1.29 → 0.91, both numbers on screen); the STRICT deck's chart leads **−41.3 %** (1.50 → 0.88, the optimiser's own midpoint baseline). **These two are not yet reconciled across artefacts.**
7. Three deep-research analysts have just landed **model-improvement plans** (`docs/model-improvement/MODEL_IMPROVEMENT_PLAN_{PHYSICS,ML,ECON_VALIDATION}.md`) that say, bluntly, that several current numbers are wrong: oil rate ~25× too high, first-cycle uplift 135× vs published 5–6×, and **₹0.61 cr/yr is wrong twice over** (wrong steam price *and* an impossible 6.8 cycles/well/year).
8. Both in-flight streams closed at 18:14–18:16: dashboard **v4 is built** (4 pages, light-theme default) and `docs/study/hinglish-pack/` **00–07 is complete**. Neither is committed yet.
9. Hard blockers that are *not* code: team of 6 (≥1 female) not formed, Team Name/ID are literal placeholders in the deck, SPOC deadline conflict (**15 Sep** per the official guidelines PDF vs **30 Sep** everywhere else, including the scraped portal CSV) unresolved, and the college authorisation letter (Principal's signature, takes days) not started.
10. Nothing has been submitted. Nothing is public. There is no GitHub repo yet.

---

## 2. Current state

| Component | Status | Where |
|---|---|---|
| Build contract | Frozen, still accurate | `docs/SPEC.md` |
| Field parameters | Real, sourced, merged | `params/field_params.json` + `params/CHANGELOG.md` |
| Physics engine | **Rev 13** (physics wave 5, 27 Sep) — the operator's **response to rod float is now a control** (`css.float_policy` ∈ `pull`/`vfd_hold`/`vfd_then_pull`/`none`, recommended: `vfd_hold`), applied alike to the baseline, the recommendation and the cold counterfactual (shut in, not pumpable, once it floats under a policy); smooth inversion band, injectivity gate (≥400 kPa), net-of-levies price deck. **No calibration knob moved** (only the diesel discount base, 0.30→0.15). **263 passed + 2 xfailed** (soak; the steam optimum at the mid-range diesel price sits below the BGW-8 slug range — the rev-12 cold-well xfail is now un-xfailed). ~~Rev 12 (physics wave 4) — water cut as a state, Pal–Rhodes W/O emulsion capped at 10×, injection-pressure + stroke-length levers, the float-onset produce-end rule, AOF retuned 0.46→0.56; 197 passed + 2 xfailed.~~ Branch `wave5`. See §16 (and §15 for rev-9→12 history). | `twin/` (`thermal, viscosity, ipr, srp, cycle, dyno, calibrate, generate_data`); `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12 |
| Dynamometer cards — computed | **rev 6/9** — computed surface + pump cards (Gibbs 1963 wave equation, FD solve), rod-float separation onset independently matches the SPEC's ≈0.6 FI alarm line; classifies float/viscous/pound/gas signatures | `twin/dyno.py`; `docs/model-improvement/DYNO_CARD_MODEL.md` |
| Dynamometer cards — measured | **New, rev 12 cascade** — `RandomForestClassifier` on 3,200 synthetic cards, 5 fault classes, 94.8% hold-out accuracy; classifies a **measured** surface card the field uploads; every call repeats a domain-shift caveat (never seen a real Baghewala card — a first read, not a field-validated diagnosis) | `ml/dyno_classifier.py`; `ml/models/dyno_clf.joblib`, `dyno_clf_metrics.json` |
| Calibration loop | **rev 12 cascade update, re-run under rev 13** (story unchanged — this demo's 3-D grid doesn't search policy/stroke/pressure, so it runs at the params' own default `pull`; only the numbers were regenerated against rev-13 physics, moving under 1 point) — `twin/calibrate.py` fits `formation_water_cut`/`thickness_m`/`AOF_REF_M3D` (bl_delta_factor still fixed, sourced) to observed CSS cycles under the shipped water-cut-as-state model; `ml/recommend_physics.py` re-recommends against the recalibrated physics; pseudo-real demo recovers formation_water_cut/aof/thickness within −5.2/−0.9/−10.9% | `twin/calibrate.py`, `ml/recommend_physics.py`; `ml/models/calibration_demo_report.json`; TIER1 §11–§12, `ml/README.md` |
| Field-level scheduler | **Rev 13 cascade** — `ml/schedule.py`, every well on **VFD-hold**: naive fixed-job policy is **+₹72,320/d** field-wide (~~rev 12, pulling on float, was a field-wide **loss** of −₹13.3k/d~~ — the policy switch alone is the difference), greedy per-well tuning adds +₹32,083/d (+₹104,403/d total), exact bitmask×ERD scheduling (serving 10/12 synthetic wells) adds a further +₹5,396/d (+₹109,799/d total) | `ml/schedule.py`; `ml/models/field_schedule_demo.json`; `ml/README.md` |
| CalGEM real-data benchmark | 9,692 real CSS cycles, 5,771 CA wells (2018–21), a shallow predominantly-steamflood field with a cyclic-steam subset — field-level SOR band only; official 2021 field SOR band 3.47–8.24, model (gross SOR 4.50 at reference) sits inside it; no per-well oil obtainable → per-cycle SOR/uplift check blocked on a human browser session | `docs/research/CALGEM_CSS_BENCHMARK_2026-09-26.md`, `docs/research/OIL_DATA_REQUEST.md` |
| Synthetic dataset | 3,000 LHS cycles, seed 42, no NaN — still on the rev-9 4-D sampling; the rev-12 cascade's LHS is 6-D (adds wellhead pressure, stroke) and **not yet regenerated** on `main` | `data/synthetic_cycles.csv` |
| ML surrogate | **Honest role, rev 13 cascade**: the exhaustive 6-lever × policy physics grid (`best_settings_physics_5d`, 40,194 feasible points/policy, 4 policies) is the decision engine, not the surrogate. 7-feature XGBoost models retrained on the rev-13 LHS (oil R²=0.995 overall; float classifier `float_premature_pull` now **41%** positive, AUC 0.999 — supersedes the ~~rev-12 label's ~95% positive share, which was uninformative~~). The float classifier is informational only as of rev 13 (not a search constraint) | `ml/train.py`, `ml/models/*.joblib`, `ml/models/metrics.json`, `ml/README.md` |
| Optimiser | Bayesian search over the surrogate lands **~24% below** the physics-grid optimum at rev 13 (+₹11,635/d vs +₹15,396/d FY25 — steam/pressure under-resolved in a 60-call budget); ~~rev 12: 51% below~~; reported as a cross-check only, never the recommendation, which is the physics grid's own canonical point (**maximises net cash/cycle-day**, not incremental margin, as of rev 13, subject to a hard injectivity gate) | `ml/optimize.py`, `ml/recommend_physics.py` |
| UQ | **Rev 13 bake** — 1,500 draws × 9 points × 3 price decks, true physics; same-policy P(rec > baseline), VFD-hold: **96% against a baseline whose 1.3 m³/d cutoff we chose; 84% (median ₹2.5k/day) with the same 0.6 backstop; ≈ ₹0 if the VFD can run below 2 spm, as our own cold well does** (raw draws 0.965/0.992/0.999, FY25/$65/net-of-levies); if baseline pulls 0.991–1.000; if baseline does nothing about float, only 0.16–0.25; same-policy gain p10/p50/p90 (FY25) **+2,175/+12,101/+161,014** (right-skewed); P(injectable)=1.000 everywhere; top drivers μ_ref, cold-well skin, oil price, formation water cut. ~~Rev 12: P(rec beats baseline) 0.943 (FY25)/0.98 ($65); P(incremental margin>0 vs pumpable cold well) 0.34/0.12, gross-basis 0.77/0.45.~~ | `ml/uq.py`; `ml/models/uq_summary.json` |
| API | 3 endpoints verified 200 + SPEC-shaped JSON | `api/main.py` (`/params`, `/simulate`, `/optimize`) |
| Dashboard **v3** | Superseded — was a 150 KB single file (bilingual EN\|हिं, ISA-101, honest claim framing). Recover from commit `a32230e` if ever needed | `git show a32230e:dashboard/index.html` |
| Dashboard **v4** | **Re-baked 27 Sep on rev 9** — incremental-margin headline, FY25/FY26-floor price presets, dyno panel, calibration section, 116/1-test tag — 4 pages, light theme default: `index.html` (overview), `console.html`, `optimizer.html`, `methodology.html` | generated in `dashboard/`; **edit `dashboard/src/` only**, rebuild with `node dashboard/build.js` |
| SVG asset library | Done — 28 icons + sprite, 5 illustrations, 5 diagrams, each dark+light | `ppt/assets/svg/{icons,illustrations,diagrams}` + `MANIFEST.md` per folder |
| Deck — official plain | Superseded | `ppt/archive/SIH26120_Idea_Presentation.pptx` |
| Deck — VISUAL | **Rejected** (restyled the SIH master; screeners drop off-template decks) | `ppt/..._VISUAL.pptx/.pdf`, `..._VISUAL_EDITABLE.pptx` |
| Deck — **STRICT** | **STALE on TWO fronts now** (rebuilt 26 Sep morning, advisory wording, Andrade 1930, Python 3.13, reframed slide 5 — for the v1 numbers). Deliberately **not touched** through physics-v2, v3, or economics v2; still shows the v1 "prototype, since audited" caption/framing, inconsistent with the dashboard's rev-9 numbers AND now with the gross-vs-incremental story — deck rebuild decision still pending from the team lead (see §14) | `ppt/final/SIH26120_Idea_Presentation_STRICT.pptx` / `.pdf` |
| Slide-3 architecture diagram | Done, overflow-gated (build fails loudly on clipped text) | `ppt/diagram/` |
| Reviews | 6 done: content, docs, UI-visual, UI-UX, integration, fixes-applied | `docs/reviews/` |
| Research (basic) | Done, source-labelled CONFIRMED / TYPICAL / DERIVED | `docs/research/` |
| Research (deep) | 6 docs + English master study guide + **3 improvement plans** (committed 18:14) | `docs/research/deep-dives/` |
| Hinglish study pack | **Complete 00–07**, **committed**, and revised 26 Sep (v1/v2 banners, safe-to-say block, killer questions, demo commands) | `docs/study/hinglish-pack/` |
| Team / registration | **Not started** | — |
| Mirror copy | **STALE** (16:42; predates docs/research/deep-dives, study-pack, dashboard v3, STRICT deck) | `Downloads\SIH-2026\sih-baghewala-code` |

---

## 3. Decision log — every major fork, and why

**D1 · PS choice: SIH26120.** Scraped all SIH 2026 problem statements from a community GitHub mirror into `Downloads\SIH-2026\sih2026_ps.csv` (233 unique PS IDs). Filter was "where does a ChemE beat a pure-CS team?". SIH26120 is thermal EOR + artificial lift — domain-heavy, and the landscape scan (`docs/research/landscape.md`) found **no commercial product that co-optimises CSS steam scheduling and rod-pump operation together** (XSPOC, Lufkin SAM/SROD, Weatherford ForeSite, SLB OptiSite, AVEVA, Kongsberg all do one side only). That gap is the pitch.

**D2 · Rejected SIH26119 (MRPL, indigenous GPU optimisation solver).** A solver-engineering PS: our ChemE edge evaporates and we'd compete on our weakest ground (CUDA/numerics) against CS specialists.

**D3 · SIH26165 as backup, SIH26121 as hedge.** SIH26165 (OIL, NLP for serious-injury/fatality precursors) is the fallback if 26120 hits a wall. `docs/research/deep-dives/sih_winning_playbook.md` separately recommends **SIH26121 (eRTMAC-NWIS, offset-well decision support)** as the *second* PS, since a team may submit against a maximum of two and it shares the same sponsor.

**D4 · Contract-first build.** `docs/SPEC.md` was written before any code — exact function signatures, exact DataFrame columns, `params/field_params.json` as the single source of truth ("consumers must read this file, never hardcode"). This is what let ~30 subagents build in parallel without integration hell. It held: the integration pass changed values, never the schema.

**D5 · Physics model selection.** Marx & Langenheim 1959 (steam zone), Andrade / ASTM D341 (μ(T)), Vogel 1968 (IPR), Gibbs 1963 (rod dynamics) — all public, peer-reviewed, citable on the references slide. Every simplification carries an inline `# ASSUMPTION:` comment.

**D6 · Real params merged, two constants retuned.** Merging the real field data (μ 2,000 → 11,500 cP, depth 500 → 1,150 m) broke the SOR-interior-optimum test. Fixed by retuning two already-flagged assumption constants: `ipr.AOF_REF_M3D` 1.0 → **0.7**, `thermal.DRAINAGE_RADIUS_M` 10.0 → **8.0**. Documented, not hidden. (The physics improvement plan now calls this optimum "a fudge" — see §7.)

**D7 · Andrade constants kept `null`.** The research agent computed A=1.164e-6, B=7436.6, but `viscosity.py` refits those exact constants at runtime from `mu_ref_cP`/`T_ref_C` plus a hardcoded 150 °C / 50 cP anchor. Hardcoding the rounded values introduced float drift (11,489.6 instead of 11,500) and failed `test_reference_point_recovered`. Null = full precision.

**D8 · Log-target regressor.** Raw XGBRegressor scored R²=0.69 on a heavy-right-tailed ratio target; wrapping in `TransformedTargetRegressor(log/exp)` lifted it to 0.72 with no change to the public `.predict()` contract.

**D9 · Dashboard evolved v1 → v4.** v1/v2 were "AI slop" — animated tricolour, shimmer, parallax, rotated stamps. Two senior reviews (`docs/reviews/ui_review_visual.md`, `ui_review_ux.md`) forced v3: motion budget cut to three animations, ISA-101 colour discipline, bilingual EN|हिं with a three-tier translation policy (numerals and units never translated), a provenance chip replacing "MOCK DATA", and stated uncertainty. v4 (in flight) splits it into 4 pages with a light default theme.

**D10 · Claim reconciliation (the most important honesty decision).** v2 asserted two different baselines on one page (a 1.29 KPI tile and a 1.50 chart bar) and led with the one the judge couldn't see. v3 states **three labelled bars and two deltas**: primary **1.29 → 0.91 = −30 %** (both on screen), secondary **−41.3 % vs field-practice baseline 1.50** (labelled as the optimiser's own midpoint). Never a bare −41.3 %.

**D11 · VISUAL deck killed, STRICT deck built.** The VISUAL deck looked premium but replaced the SIH master, colours, title bars and layout grid — and SIH internal screeners drop off-template decks. Rebuilt from `template_official.pptx` (downloaded from `sih.gov.in/letters/2026/`), modelled on a friend's **selected** SIH 2025 deck, torn down page-by-page in `ppt/notes/WINNING_DECK_ANALYSIS.md`. Five rules copied: exactly 6 slides; template pointers kept verbatim as section headings; Technical Approach is a **picture, not a list**; bullets 3–9 words; Impact = short blocks + one real chart.

**D12 · No product screenshots in the deck.** The winning deck has none; its Technical Approach is diagrams only. We matched that.

**D13 · Never state Baghewala's own SOR.** It is not published anywhere. We benchmark against the literature range 3–8 (avg ~6, "efficient" < 3) and say so out loud. An earlier invented "4.5 t/m³ current SOR" was a KILLER review finding and was deleted everywhere.

**D14 · PS-vs-literature conflict handled diplomatically.** The PS text says 17–19° API / 46–48 °C; the literature says 14–17° API / ~50 °C. Slides use the PS numbers with a literature footnote; viva answers present both and explain which is used where. Never contradict the sponsor on their own slide.

---

## 4. File map

```
sih-baghewala/
├── README.md               public-facing overview + quickstart + repo map
├── requirements.txt        numpy scipy pandas scikit-learn xgboost scikit-optimize fastapi uvicorn pytest
├── params/
│   ├── field_params.json   SINGLE SOURCE OF TRUTH for all physical parameters
│   └── CHANGELOG.md        field-by-field diff placeholder → real, with citations
├── twin/                   physics engine (thermal, viscosity, ipr, srp, cycle, generate_data)
├── tests/                  24 pytest monotonicity/sanity tests
├── data/synthetic_cycles.csv   3,000 LHS cycles, seed 42
├── ml/                     train.py, optimize.py, models/{sor,float}_model.joblib, metrics.json
├── api/main.py             FastAPI: /params /simulate /optimize
├── dashboard/
│   ├── index.html console.html optimizer.html methodology.html   GENERATED v4 pages — do not edit
│   ├── README.md           data provenance, claim reconciliation, QC commands  ← read before touching
│   ├── build.js            v4 builder (node) → the four pages above
│   └── src/                v4 sources — EDIT HERE, never the generated html
├── ppt/
│   ├── final/SIH26120_Idea_Presentation_STRICT.pptx/.pdf   ★ SUBMIT THIS
│   ├── build_strict_deck.py     builds it from template/template_official.pptx
│   ├── patch_tech_slide.py      swaps the slide-3 diagram in and re-verifies layout
│   ├── diagram/                 tech_architecture.html + render.py (overflow-gated)
│   ├── notes/BUILD_NOTES.md     ★ how the deck is built, QC done, placeholders left
│   ├── notes/WINNING_DECK_ANALYSIS.md   teardown of a selected SIH 2025 deck
│   ├── notes/deck_content.md    written for the SUPERSEDED deck; still useful for Q&A
│   ├── assets/svg/              28 icons + sprite · 5 illustrations · 5 diagrams (dark+light) + MANIFESTs
│   └── archive/, visual/        superseded decks (plain, VISUAL, VISUAL_EDITABLE) + their sources
└── docs/
    ├── PROJECT_LOG.md      ← you are here
    ├── SPEC.md             build contract (module signatures, JSON schema, conventions)
    ├── architecture.svg
    ├── guides/             DEMO_SCRIPT.md (3-min judge walkthrough), GLOSSARY.md, ui_brief.md
    ├── research/           baghewala_facts.md (sourced, labelled), references.md, ppt_ammo.md, landscape.md
    │   └── deep-dives/     5 deep dives (CSS/EOR, SRP+dyno ML, digital twins, Baghewala dossier, SIH playbook)
    ├── model-improvement/  3 improvement plans (physics / ML / econ-validation) + TIER1_PROGRESS_LOG.md
    ├── reviews/            content, docs, ui_visual, ui_ux, integration_report, FIXES_APPLIED
    └── study/              TEAM_STUDY_GUIDE.md (English master), viva_prep.md,
                            hinglish-pack/ (Gaurav-facing, 00–07, ~3 h; minimum path 01 → 03 → 06)
```

> Layout reorganised on 2026-09-25 (was 17 top-level folders). Old → new:
> `research/` → `docs/research/` · `research-deep/` → `docs/research/deep-dives/`, `docs/model-improvement/`, `docs/study/` ·
> `review/` → `docs/reviews/` · `study-pack/` → `docs/study/hinglish-pack/` · `assets/svg/` → `ppt/assets/svg/` ·
> `SPEC.md`, `PROJECT_LOG.md` → `docs/` · decks → `ppt/final/` (submit) and `ppt/archive/` (superseded).
> Path mentions throughout this log have been updated to the new locations.

Outside the repo: `Downloads\SIH-2026\` holds `sih2026_ps.csv` (the 233-PS scrape),
`SIH26120-Strategy.pdf`, copies of every deck (`SIH26120_Deck_FINAL_BRANDED.pptx` = the VISUAL
version), and a **stale** code mirror at `sih-baghewala-code`.

---

## 5. The numbers bible

Legend: **[CONFIRMED]** sourced · **[TYPICAL]** industry gap-filler · **[DERIVED]** computed
from confirmed values · **[OURS]** our own simulation, not measured · **[DISPUTED]** an
improvement plan says this is wrong.

### Field (all [CONFIRMED] unless noted — see `docs/research/baghewala_facts.md`)
| Value | Number | Source |
|---|---|---|
| Depth (Jodhpur Sandstone) | ~1,100–1,150 m | oil-india.com; SPE-23APOG-535203; OIL deck 12.07.2025 |
| Viscosity @ 50 °C | 8,000–15,000 cP (SPE) / 10,000–13,000 cP (OIL) — we model **11,500** | both above |
| API gravity | 14–17° literature vs **17–19° in the PS text**; params use 15.5 | SPE + OIL deck |
| Reservoir T / P | 50 °C / ~11,400 kPa (116 kgf/cm², hydrostatic-consistent) | OIL deck |
| Porosity | <10 % (we use 0.09) | Basha et al., GEOHORIZONS Jan 2015 |
| Steam (BGW-8 cycle 1) | 280–305 °C, 60–70 % quality, ~3,100 kg/h, 85–97 kgf/cm², inject 14–21 d, soak 50–60 % of inject | OIL deck |
| India's first CSS | well **BGW-8, Dec 2018**, with Belgrave Oil & Gas (Calgary) | OGJ; oil-india.com |
| First-cycle uplift | **5–6×** | Scribd CSS case study; OIL deck |
| Production growth | 218 t (FY17) → 32,787 t (FY25) → **43,773 t (FY26)** | OIL deck; PSU Watch |
| Wells | 52–56 drilled, 33–34 operational; **19 CSS'd in FY25-26** (+72 % YoY); 39 CSS cycles to Jun 2025 | oil-india.com; news roundups |
| Distance to Jaipur | ~550–600 km **[TYPICAL/range]** (an earlier "250 km" was a KILLER error) | distance tools |
| Net pay thickness, rock k, Cp | **[TYPICAL]** — no Baghewala source exists | — |
| Baghewala's own SOR | **NOT PUBLISHED. NEVER STATE A NUMBER.** | — |
| Literature CSS SOR | 3–8 t/m³, avg ~6, "efficient" < 3 **[TYPICAL]** | ScienceDirect; Wikipedia |
| Workover cost | $15k–50k/event (all-in band $90k–270k in the deep dive) **[TYPICAL]** | iFactory; SRP deep dive |

### Model results — **CURRENT (physics rev 13, 27 Sep, physics wave 5)**, all **[OURS]** — physics-simulated, *not* field-validated

Three price decks now matter: OIL's own **CONFIRMED FY25 realisation** (US$78.09/bbl,
Annual Report 2024-25, minus a $10/bbl heavy-oil discount `[ASSUMPTION]` = ₹5,992/bbl)
is the base case; the old US$65/bbl **FY26 planning floor** (₹4,840/bbl — a CMD
budgeting number, never a realisation) is a named downside preset; new this rev, a
**net-of-royalty-and-cess deck** (~₹3,600/bbl, ~35% levies, OIL's own FY25 Annual
Report exchequer table). ₹ decisions run on **net cash per cycle-day**
(counterfactual-free, rev 13's optimiser objective — see below); the headline SOR
stays **gross** (steam ÷ all oil), matching every literature/CalGEM benchmark this
repo cites.

**Rev 13's story: the operator's response to rod float is itself a control, and it
moves more money than any set-point.** The technical re-score (58/100) found that
rev 12's headline (+₹9,574/d) came entirely from the **pull rule** ending the
baseline on the float alarm while it still made real oil — the twin's own VFD-slowing
mode erased it. Rev 13 makes `css.float_policy` ∈ `pull`/**`vfd_hold`**/
`vfd_then_pull`/`none` a parameter and an optimiser dimension, applies the SAME
policy to the baseline, the recommendation and the cold counterfactual (shut in, not
pumpable, once it floats under a policy), smooths the inversion cliff, gates
injectivity (≥400 kPa sandface margin), and adds the levies deck. **No calibration
knob moved** — only the diesel discount base (0.30 → 0.15, an economics input).

| | Baseline (b), VFD-hold — 1,300 t/10 d/91 kgf/cm²/86-in/5 spm/cutoff 1.3 | **Recommended, VFD-hold — 1,000 t/10 d/89 kgf/cm²/64-in/start 4.5 spm/cutoff 0.60 backstop** |
|---|---|---|
| SOR | 3.29 | **2.83** |
| oil m³ · produce days (window) | 395 · 199 (227) | 353 · 196 (220) |
| ended by | float pull at the 2-spm floor | float pull at the 2-spm floor |
| net cash ₹/cycle-day — FY25 / $65 / net-of-levies | +12,064 / −582 / −14,193 | **+15,396 / +3,738 / −8,811** |

**The gain depends on the baseline's own float policy** (net cash ₹/cycle-day,
FY25 / $65 / net-of-levies):
- **Baseline VFD-holds too (fair comparison): +₹3,332 / +4,319 / +5,382** —
  decomposes stroke 57% / cutoff 30% / steam 11%; positive in every one-at-a-time
  sensitivity and 95%+ of UQ draws.
- **Baseline pulls at the first alarm (rev-12 operation): +₹12,917 / +14,694 /
  +16,606** — **68% of this is the policy switch alone**; this is the same
  structure as the retired "+₹9,574/d" headline.
- **Baseline does nothing about float: −₹3,865 / −2,513 / −1,057** — a float-safe
  recommendation *loses* money here; the model prices no rod-failure/workover cost,
  so what float avoidance buys (72→3 alarm days, 42→0 days at FI=1.0) isn't in the ₹. [corrected 27 Sep: this was a non-canonical plan; the recommendation gains +₹2,622 / +3,484 / +4,413 vs a do-nothing baseline]
- SOR moves 3.29 → 2.83 (−14%) same policy; 4.35 → 2.83 vs. a pulling baseline.

- Reference cycle (1,500 t / 7 d / 1.2 m³/d / 5 spm / 86 in / 91 kgf/cm², shipped
  default `pull`, unchanged by rev 13): SOR **4.50** gross.
- UQ (1,500 draws, seed 42, all 3 decks): **P(injectable) = 1.000** everywhere.
  Same-policy P(rec > baseline), VFD-hold: **96% against a baseline whose 1.3
  m³/d cutoff we chose; 84% (median ₹2.5k/day) with the same 0.6 backstop;
  ≈ ₹0 if the VFD can run below 2 spm, as our own cold well does — OIL's VFD
  minimum speed is the one datum that decides the gain** (raw draws 0.965 /
  0.992 / 0.999, FY25/$65/net-of-levies); if baseline pulls, 0.991–1.000; if
  baseline does nothing, only 0.16–0.25. Same-policy gain (VFD-hold) p10/p50/p90, FY25: **+2,175 / +12,101 /
  +161,014** (right-skewed — the point estimate sits toward the low side; the p90
  tail is the baseline's own fragility). Recommendation's own net cash/day, median:
  +₹1,132 (FY25) / −₹6,940 ($65) / −₹15,621 (net-of-levies) — **positive in about
  half of scenarios at FY25, a minority at $65, none net of levies** *(to confirm
  from `ml/models/uq_summary.json`)*. Top drivers: μ_ref, cold-well skin, oil price,
  formation water cut.
- Gain decomposition (canonical vs. baseline (b), same policy VFD-hold, Shapley):
  stroke **57%**, cutoff **30%**, steam **11%**, spm 1%, pressure 1% (FY25 deck).
- Tests: **263 passed, 2 xfailed** (soak; the steam optimum at the mid-range diesel
  price sits below the BGW-8 slug range — the rev-12 cold-well xfail is now
  un-xfailed, since the counterfactual obeys the policy).
- ML honest role: the exhaustive 6-lever × policy physics grid (~172 s, 40,194
  feasible points/policy, every point true-physics-verified) is the decision engine;
  the XGBoost surrogate lands **~24% below** it (+₹11,635/d vs +₹15,396/d FY25) and
  is reported only as a cross-check. Float classifier `float_premature_pull`: 41%
  positive, AUC 0.999, informational only (not a search constraint).
- Calibration demo (re-run under rev 13, story unchanged): recovers
  `formation_water_cut` −5.2%, `aof_ref_m3d` −0.9%, `thickness_m` −10.9% against a
  hidden truth.
- Scheduler demo (12 synthetic wells, one shared generator, every well VFD-hold):
  naive fixed-job policy is **+₹72,320/d** field-wide (rev 12, still pulling, was a
  field-wide **loss** of −₹13.3k/d — the policy switch alone is the difference);
  greedy adds +₹32,083/d (+₹104,403/d); exact scheduling adds a further +₹5,396/d
  (+₹109,799/d total), serving 10 of 12 wells.
- **The physics story since rev 9, in order:** (1) Boberg–Lantz δ computed and
  sourced; (2) incremental economics (over the cold well, not gross); (3) hardening
  after an external review; (4) water cut modelled as a state, restoring the
  rod-float thesis; (5) an injection-pressure lever plus a stroke-length lever; (6)
  the float-onset produce-end rule; (7) `AOF_REF_M3D` retuned to the field peak
  band; (8) **rev 13 (wave 5): the float response itself becomes a policy control**,
  applied fairly to the baseline and the cold counterfactual, with a smoothed
  inversion band, an injectivity gate and a net-of-levies deck.
- **Controls coverage:** steam ✓ optimised, injection pressure ✓ optimised, cutoff ✓
  optimised (as an economic backstop), stroke length ✓ optimised, SPM ✓ optimised,
  soak modelled and held fixed (no interior optimum), **VFD ✓ a real operating-policy
  control** (`pull`/`vfd_hold`/`vfd_then_pull`/`none`, recommended `vfd_hold`) as of
  rev 13 — previously only the SPM set-point schedule.
- **Data ingest:** per-well cycle records ✓ (the calibration loop), measured dyno
  cards ✓ (the classifier, 94.8% hold-out), production history ✗ (not shared, ask).
- **Multi-well:** demo scheduler only, 12 synthetic wells (`data/external/SOURCE.md`)
  — no real Baghewala per-well data.
- **External technical/judge reviews (27 Sep)** scored 61 (judge) / 52→58 (technical
  re-score); the re-score's top finding (the rev-12 gain was the pull rule, not the
  set-point) is what rev 13's whole cascade answers — see §16.
- Physics tests: **263 passed, 2 xfailed** — soak (no defensible interior-optimum
  mechanism); the steam optimum at the mid-range (0.15) diesel price sits below the
  BGW-8 slug range (new strict xfail — read as revealed preference, OIL's steam is
  probably cheaper than the mid-range assumed here). Full log:
  `docs/model-improvement/TIER1_PROGRESS_LOG.md` §12; sourcing:
  `docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md`.
- Real-data benchmark: CalGEM (California) 9,692 real CSS cycles, 5,771 wells,
  2018–21 — a shallow, predominantly steamflood field (Kern River) with a
  cyclic-steam subset, field-level SOR band only: official 2021 field SOR band
  3.47–8.24; the model's gross SOR (4.50 at reference) sits inside it. Per-cycle real
  oil (for a true per-cycle SOR/uplift check) is not obtainable from any public
  mirror — needs a human browser session at
  `wellstar-public.conservation.ca.gov`. `docs/research/CALGEM_CSS_BENCHMARK_2026-09-26.md`.

<details>
<summary><strong>Historical — rev-12 model results (physics wave 4, 27 Sep; superseded 27 Sep evening by wave 5 → rev 13, do not quote)</strong></summary>

| ~~Value~~ | ~~Number~~ |
|---|---|
| ~~Baseline (b) "published-practice", pull~~ | ~~1,300/10/91/86-in/5 spm/cutoff 1.3 → SOR gross 4.35 / incr 5.80, 299 m³ oil, 140 d, incr −₹1,601/cycle-day (FY25), ends float onset day 139~~ |
| ~~Recommended, pull~~ | ~~1,000/10/85/64-in/3 spm, produce until float 3 days (0.6 backstop) → SOR gross 3.19 / incr 4.49, 313 m³ oil, 180 d, incr **+₹7,973**/cycle-day (FY25), ends float onset day 179~~ |
| ~~PRIMARY claim~~ | ~~incremental margin/cycle-day −1,601 → +7,973 (Δ **+9,574**), gain decomposition SPM 62% / stroke 32% / cutoff 0%~~ |
| ~~Physics tests~~ | ~~197 passed, 2 xfailed (soak; cold well unpumpable at 2 spm under any published emulsion law)~~ |
| ~~Scheduler demo~~ | ~~naive fixed-job policy loses ₹13.3k/d field-wide (pull rule floats rods late in most wells); exact scheduling earns +₹46.6k/d, serving 9/12 wells~~ |

Superseded because: the technical re-score (58/100) found the rev-12 +₹9,574/d
headline was structurally the **pull rule** ending the baseline early while it still
made oil, not the recommendation's own set-points — confirmed by re-running the
same comparison under the twin's own VFD-hold mode, which erased the gain to +₹3.3k/d
(the fair, same-policy number). Do not quote the rev-12 numbers above as current;
the field-scheduler "loses ₹13.3k/d" line is the same artefact field-wide.

</details>

<details>
<summary><strong>Historical — rev-9 model results (27 Sep morning; superseded 27 Sep afternoon/evening by the hardening → wave 3/4 cascade, do not quote)</strong></summary>

| ~~Value~~ | ~~Number~~ |
|---|---|
| ~~Baseline (b) published-practice~~ | ~~1,300/10/1.3/5 → SOR gross 4.061 / incr 5.502, 320.1 m³ oil, 186.6 d, incr −₹724/cycle-day (FY25), max FI 0.24~~ |
| ~~Recommended (rounded)~~ | ~~1,600/10 (fixed)/0.70/4 → SOR gross 3.590 / incr 5.004, 445.6 m³ oil, 280.6 d, incr **+₹4,423**/cycle-day (FY25), max FI 0.58~~ |
| ~~PRIMARY claim~~ | ~~SOR −11.6%, incremental margin/cycle-day −724 → +4,423 (Δ +5,147), at 85% CONSTANT water cut and the rate-cutoff rule only~~ |
| ~~Physics tests~~ | ~~116 passed, 1 xfailed (soak only; P_res xfail closed via a derived Darcy band)~~ |
| ~~Gain decomposition~~ | ~~cutoff 83–92% of the gain (review finding: "the headline is mostly an assumed-baseline artefact")~~ |
| ~~Rod-float thesis~~ | ~~does NOT bind at a constant 85% water cut — float never sets the cutoff or SPM~~ |

Superseded because: (1) a `dt`-summation bug in `summary()` was fixed (totals now
correctly weighted by day-length); (2) water cut became a **state**, not a constant
85% — this is what restores the rod-float thesis in the late cycle and is why the
recommendation changed from "produce to a low fixed cutoff" to "produce until the
rods float, then pull"; (3) the produce-end rule changed from rate-cutoff-only to
`either` (rate cutoff or float-alarm), which is why the cutoff's share of the gain
fell from ~90% to 0%; (4) `AOF_REF_M3D` moved 0.46→0.56 to meet the field peak band.
Do not quote the rev-9 numbers above as current.

</details>

### Economics — **CURRENT (rev 13)**
| Claim | Status |
|---|---|
| Basis | **Net cash per cycle-day** (`margin_with_opex_inr_per_cycle_day`, counterfactual-free — rev 13's optimiser objective; the incremental-margin keys are kept for continuity but are no longer what the recommendation maximises). Daily opex ₹5,000/d `[ASSUMPTION]` + corrected pumping-unit power still deducted. The cold-well counterfactual now **obeys the operator's own float policy**: it is **shut in** under `pull`/`vfd_hold`/`vfd_then_pull` (FI 1.0, 189 kN at the 2-spm floor), and only pumped floating under `none` — the old "idealised pumpable" reading (~₹11.4k/d lower) is reported alongside it as the more field-consistent one, since the field did produce these wells cold. |
| Price deck — base case | OIL's own **CONFIRMED FY25 realisation**, US$78.09/bbl (Annual Report 2024-25) − $10/bbl heavy-oil discount `[ASSUMPTION]` = **₹5,992/bbl** |
| Price deck — comparison preset | US$65/bbl FY26 **planning floor** (CMD budgeting number, not a realisation) − $10/bbl = ₹4,840/bbl |
| Price deck — new, rev 13 | **Net of royalty + OID cess**, ~₹3,600/bbl (₹5,992 × (1−20%−20%) `[ASSUMPTION on the rates]`; cross-checked against OIL's own FY25 Annual Report exchequer table, which caps total levies at ~35% → ₹3,890) — **every feasible grid point is negative on this deck**, even against a shut-in cold well |
| Headline economic claim (rev 13) | **The gain depends on the baseline's own float policy** — same-policy (VFD-hold, fair): net cash **+₹3,332/+4,319/+5,382** (FY25/$65/net-of-levies) per cycle-day; if the baseline pulls: +₹12,917/+14,694/+16,606 (68% is the policy switch, not the set-point — the retired "+₹9,574" headline was this structure); if the baseline does nothing about float: **+₹2,622/+3,484/+4,413** (we do not price rod failures: VFD-hold holds FI at 0.6 for ~60 days, damage index ~5× the pull policy's). Always name which baseline policy a gain number is against. |
| Steam cost, bulk (base case) | ₹7,111/t **[CALIBRATED, discount unsourced]** — 71 kg HSD/t at a **0.15** (mid-of-range) bulk-diesel discount off retail, moved from 0.30 this rev on the coordinator's instruction (an economics input, not a physics fit); presets 0.30 (bulk) and 0 (retail) both kept. |
| CO₂ | diesel-fired steam **[DERIVED]** — falls per m³ oil under a same-policy comparison (the recommendation burns 23% less steam for 11% less oil, 353 vs 395 m³, under VFD-hold; steam per m³ falls 3.29 → 2.83) |
| Not modelled | Rod-string failure/workover cost from running floating rods (VFD-hold holds FI at 0.6 for ~55–60 days/cycle, damage index ~5× the pull policy's — entirely unpriced); royalty/cess are now modelled as a deck (above), but the ER-policy 50% cess waiver is not netted |
| Unsourced placeholders still open | opex ₹5,000/d · heavy-oil discount $10/bbl · bulk-diesel discount base 0.15 · electricity ₹8/kWh · INR/USD 88.0 · `fi_alarm_days`=3 · `css.vfd_turndown_frac`=0.5 (an assumed NEMA-D VFD turndown) · royalty/cess rates 20%/20% (cross-checked, not confirmed) |

<details>
<summary><strong>Historical — v1 economics dispute (13–25 Sep) and rev-5 gross-margin framing (26 Sep; superseded 27 Sep)</strong></summary>

| ~~Claim~~ | ~~Status~~ |
|---|---|
| ~~₹1,300/t steam (hardcoded in `dashboard/index.html`)~~ | ~~[DISPUTED — WRONG]. Unsourced; roughly a gas-fired price, and Baghewala has no gas supply.~~ |
| ~~₹8,400/t steam (≈US$95/t)~~ | ~~[DERIVED, CORRECT] from OIL's own 220 kg HSD/h ÷ 3,100 kg/h steam = 71 kg diesel/t at ₹97.8/L. Honest band ₹5,900–8,400/t.~~ |
| ~~₹0.61 crore/yr~~ | ~~[DISPUTED — WRONG TWICE]: wrong steam price *and* an impossible 6.8 cycles/well/year denominator.~~ |
| ~~rev-5 headline: ₹2,739 → ₹7,893/cycle-day, +188%~~ | ~~GROSS margin (no opex, no cold-well baseline) — credits CSS with oil the well makes anyway; superseded by the incremental basis, which is negative for this exact pair at the $65 deck.~~ |

Superseded: rev 8's economics v2 found the margin had no daily opex and no
cold-production counterfactual, and that the "revealed preference" 30% bulk-diesel
discount calibration (OIL ran 19 CSS jobs, so a sensible cycle must pay) had been done
on the gross basis. Putting ₹ on the incremental basis is why the base-case price deck
became a live decision (rev 9) rather than a settled placeholder.

</details>

### Honesty lines to memorise (verbatim)
- "Baghewala's own SOR is not published — we do not quote one; we benchmark against literature 3–8."
- "Our training data contains **zero real cycles**. All 3,000 are physics-generated."
- "This model is physically **plausible**, not field-**validated**. Two different claims."
- "Bayesian optimisation does not guarantee a global optimum."
- "That's an assumption, and here's why we made it."

---

## 6. Timeline (2026-09-13, one marathon day, IST)

| Time | Event |
|---|---|
| ~15:30 | 233 SIH 2026 PS scraped → `Downloads\SIH-2026\sih2026_ps.csv` |
| 15:46 | `SIH26120-Strategy.pdf` written (PS choice + backup + rejects) |
| 15:54 | `docs/SPEC.md` frozen — the contract every subagent built against |
| 15:59–16:15 | `template_official.pptx` fetched from sih.gov.in; `deck_content.md`, `viva_prep.md`, tests |
| **16:18** | **commit 1 `f70bbbb`** — physics engine (24/24), ML pipeline, dashboard v2, API, official-template PPTX, research + reviews |
| **16:25** | `351a89b` brutal-review fixes: real Baghewala numbers, gold facts, competitive differentiation; PPTX rebuilt; dashboard regressions fixed · `b60fc9e` gitignore Edge profile junk |
| **16:42** | `3477f71` visual premium deck (7 slides, custom SVG, QC'd) + PDF · code mirrored to Downloads (last sync) |
| **16:48** | `d6c1997` SVG asset library — 28 icons, 5 illustrations, 5 diagrams, dark+light |
| **16:55** | `39bc6e5` premium dashboard: baked real physics data, well cross-section, replay, apply-optimized flow |
| **16:59** | `8b233ae` SIH branding on visual deck + `_VISUAL_EDITABLE` (180 native text boxes) |
| 17:20 | `WINNING_DECK_ANALYSIS.md` — teardown of the friend's selected SIH 2025 deck |
| **17:30** | `24dfd07` **STRICT deck** built on the untouched official template, QC-passed |
| **17:47** | `a32230e` **dashboard v3** — de-AI rework per dual Opus reviews: honest claims, EN\|हिं, ISA-101, provenance, projector fold |
| **17:53** | `62ddd9d` TEAM_STUDY_GUIDE.md (English master, verified against live twin runs) |
| **17:54** | `f27e3a4` deep-research pack: CSS EOR, SRP/dyno ML, digital-twin industry, Baghewala dossier, SIH playbook |
| **17:59** | `5b81b68` (HEAD) winner-style tech architecture diagram pinned into slide 3, overflow-gated, 5 iterations |
| **18:14** | `1a4101f` (HEAD) model-improvement plans (physics / ML / econ-validation) + study-pack 00–02 |
| 18:16 | *Uncommitted:* dashboard **v4 built** (4 pages) · study-pack 03–07 completed |

---

## 7. Work that landed at the end of the session (uncommitted, unverified)

**A · Dashboard v4 — multi-page + light theme. BUILT at 18:16.** `dashboard/build.js` (node
v24.15.0) assembles four self-contained pages from `dashboard/src/`: `index.html` (overview),
`console.html` (the twin console, the only page carrying the baked `data.js`), `optimizer.html`,
`methodology.html`. Light theme is the pre-paint default; `?theme=dark` and the `bgw.v4`
localStorage key override. Plotly is loaded only on the overview and console pages.
**Not yet QC'd** — nobody has rendered these four pages headless, checked the 1366×768 fold,
or re-run the `?qc=applied` / `?lang=hi` / `?qc=alarm` captures documented in
`dashboard/README.md`. Do that before demoing. Also note the demo-fallback flag moved: `MOCK`
is now `dashboard/src/core.js:9` (inlined into all four pages), **not** "line 648 of
index.html" as `docs/guides/DEMO_SCRIPT.md` and `docs/study/hinglish-pack/00_START_HERE.md` still claim.
**Do not hand-edit generated HTML — edit `src/` and rebuild.**

**B · Model-improvement plans — all three landed** (`docs/research/deep-dives/`, 18:10–18:12). They are
the most important new input in the repo and they are *critical of the current build*:

- **PHYSICS** (975 lines): peak oil rate ~25× too high (75 m³/d vs ~19 bbl/d/well implied by field data); SOR 2–4× too optimistic; produce phase 3–4× too short; μ at peak T computes to 0.63 cP, **below liquid water — non-physical**; `failures_expected = 0` at the demo point makes the rod-float alarm decorative; and the SOR interior optimum "exists only because of a fudge" (the `DRAINAGE_RADIUS_M` retune) and "will not survive contact with better physics." Tier 1 = 8 items: composite-radial Boberg–Lantz IPR (retire `DRAINAGE_RADIUS_M`), Boberg–Lantz cooldown (retire the invented `COOLDOWN_TAU_DAYS=20`), pressure recharge so `P_res(t)` varies, declining-SPM schedule, floating index with a real fillage consequence, Walther/ASTM D341 viscosity with a ~1 cP floor, an economic + carbon objective, and wellbore heat loss over 1,150 m.
- **ML** (Tier 1 = 5 items, all small): optimise in **₹ not SOR** (R² 0.72 → 0.998, because oil is linear and SOR is a ratio); physics-verification loop + two-stage search (optimiser 22.3 s → ~6 s, verified SOR 0.892 → ~0.85); a viability gate / hurdle model (R² 0.7246 → 0.987 on 95.9 % of the space, the other 4.1 % classified at AUC 0.9992); local conformal uncertainty (band ±0.31 → ±0.02); constraint/bound realism (three of four decision variables are currently **pinned at their bounds** — "the single most dangerous viva question"). If only three: **T1-3, T1-2, T1-1**.
- **ECON_VALIDATION**: builds `twin/economics.py` + a 16-test benchmark suite of which **13 pass and 3 fail** — and the plan argues the failures are the most valuable output. FAIL-1: twin's first-cycle uplift is **135×** vs published 5–6× (unbounded mobility factor). FAIL-2: peak single-well rate 471 bbl/d vs the whole field's record 1,202 bbl/d. FAIL-3: the twin **cannot reproduce SOR drift under depletion at all** — `P_res` algebraically cancels because `P_wf` is a fixed 0.4×`P_res`, so dropping reservoir pressure from 11,400 → 2,900 kPa yields an *identical* SOR of 1.294. That last one is "the finding a petroleum-engineer judge is most likely to find on their own."

**C · Hinglish study pack — complete.** `docs/study/hinglish-pack/00`–`07` all exist as of 18:16
(~3 hours of reading). 00 names **01 → 03 → 06** as Gaurav's non-negotiable minimum, since
he is team lead and the ChemE: every physics and "where did that number come from" question
lands on him. 03–07 are uncommitted.

---

## 8. TODO — ranked

**Blockers (not code; start today, they have external latency)**
1. **Resolve the deadline.** Official SIH 2026 Guidelines PDF (created 29 Jul 2026) says last date **15 Sep 2026**; September circulars, colleges running internal rounds 9–15 Sep, and every row of our own scraped portal CSV say **30 Sep 2026**. Get it in writing from the MNIT SPOC, and treat the SPOC's own (earlier) cut-off as the real one.
2. **Form the team: exactly 6 members, at least 1 female.** Team details, once entered by the SPOC, **cannot be altered** — verify every name spelling, gender, email and mobile first.
3. **College authorisation letter** — letterhead, team name, all 6 members, up to 2 mentors, Principal/Dean/Director signature, college seal. Signatures take days. Start now.
4. **Find out the internal-round date and mode.** It is mandatory; only internally-selected students can be registered.
5. **Fill the deck placeholders**: title slide still reads `TEAM ________` and `Team ID- TBD`, and the team-name oval on every content slide is a placeholder.

**High value, low effort (do before the internal round)**
6. **QC dashboard v4 and commit it.** The four pages were generated at 18:16 and nobody has looked at them: render each headless at 1600×2400, check the 1366×768 fold, and re-run the `?qc=applied`, `?qc=alarm`, `?lang=hi` captures from `dashboard/README.md`. Then commit v4 + `docs/study/hinglish-pack/03`–`07` (19 paths untracked or modified).
7. Apply ML Tier-1 **T1-3** (viability gate, ~40 lines, R² 0.72 → 0.987) — biggest metric move per line of code in the whole repo.
8. **Delete `STEAM_INR_PER_T = 1300`** and recut the money claim to per-cycle (₹0.40–0.57 cr/cycle + 152 t CO₂), citing OIL's own diesel burn. The ₹0.61 cr/yr figure must not reach a judge.
9. Add a **viscosity floor (~1 cP)** — one-line fix that kills the 0.63 cP absurdity and the 135× uplift benchmark failure.
10. Reconcile the deck and the dashboard: the STRICT deck's Impact chart leads **−41.3 %**, the dashboard leads **−30 %**. Pick one primary framing and make both artefacts and the viva answers agree.
11. ~~Update the two places that still point at the old `MOCK` location ("line 648 of `index.html`"): `docs/guides/DEMO_SCRIPT.md` and `docs/study/hinglish-pack/00_START_HERE.md`. It is now `dashboard/src/core.js:9`.~~ **DONE (26 Sep)** — both fixed as part of the 26 Sep audit fixes (see §12).
12. Add the SIH rubric items that are currently under-served — **sustainability** (the CO₂ numbers now exist), **user experience**, and **potential for future work** (the Tier-2/Tier-3 roadmaps are ready-made).
13. Create the GitHub repo, push, and put a QR to it on the references slide.
14. Re-sync the Downloads mirror (`robocopy`, excluding `.venv` and `.git`) — it is ~1.5 h stale.

**Medium**
15. ML T1-2 (physics-verification loop) and T1-1 (optimise in ₹).
16. ~~Physics Tier-1 T1-A / T1-G — but note these will change **every downstream number** and force a full ML retrain, the dashboard re-bake, and a deck-chart rebuild. Do not start this the night before submission.~~ **SUPERSEDED** — Tier-1 (T1-A..H) landed 13 Sep 18:26 (`a82cfa7`), uncalibrated; it did exactly what this warned about (every downstream number moved) and calibration is now the open item — see §12 TODO.
17. Fix the three failing benchmark tests, or write them up as a "known limitations" slide — the plan argues the write-up is worth more than a silent fix.
18. Ask OIL, via the SPOC/mentor route, for *anything* real: a data dictionary, a sample SCADA export, a dynamometer card set, a well-test sheet. Sponsor engagement before the finale is a repeated winner behaviour.
19. Decide the second PS (a team may submit against max 2). SIH26121 is the natural hedge.

**Known internal inconsistencies to clean up**
20. `docs/reviews/FIXES_APPLIED.md` Finding 9 asserts `field_params.json` "already has `andrade_A=1.164e-6`, `andrade_B_K=7436.6`". **It does not** — both are `null`, deliberately (D7). That review note is wrong; the file and `params/CHANGELOG.md` are right.
21. `README.md`'s quickstart says `pip install`, `python -m twin.generate_data`, `python api/main.py` with bare `python` — which is the broken MSYS2 build on this machine. It must say `.venv\Scripts\python.exe`.
22. `docs/SPEC.md` says Python 3.12; the venv is **3.13.3**.
23. `ppt/notes/BUILD_NOTES.md`'s upper half still documents the superseded `build_deck.py` deck (including a retired "4.5 → 3.2 t/m³" chart and "$500k/yr"). The authoritative part is the "STRICT rebuild" section at the bottom.
24. A stray PowerPoint lock file `~$SIH26120_Idea_Presentation_STRICT.pptx` sits in `Downloads\SIH-2026` — the deck may still be open in PowerPoint; close it before any rebuild.

---

## 9. Environment / how to run

**The one rule: never use bare `python`.** It resolves to a broken MSYS2 build (3.12.12) on this
machine. Always `.venv\Scripts\python.exe` (Python 3.13.3).

```powershell
# from <repo>
.venv\Scripts\python.exe -m pytest tests -q                      # → 24 passed
.venv\Scripts\python.exe twin\generate_data.py                   # → data/synthetic_cycles.csv (3000 rows, seed 42)
.venv\Scripts\python.exe ml\train.py --data data\synthetic_cycles.csv
.venv\Scripts\python.exe ml\optimize.py
.venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# then, in another shell:
curl "http://localhost:8000/params"
curl "http://localhost:8000/simulate?steam_t=1500&soak_days=7&cutoff=3&spm=8"
curl "http://localhost:8000/optimize"
```

Dependency order is strict: generate_data → train → api → dashboard.

**Dashboard.** All four v4 pages open straight off the filesystem; Plotly (cdnjs) is the only
external dependency. `MOCK = true` at **`dashboard/src/core.js:9`** serves baked real-physics
data, so the demo survives a dead API — know that line. Flip to `false` (and rebuild) with the
API running for live mode. Rebuild: `node dashboard/build.js`. **Edit `dashboard/src/*` only.**
Re-baking `BAKED` after physics changes is documented in `dashboard/README.md` §"Re-baking".

**Deck.**
```powershell
.venv\Scripts\python.exe ppt\build_strict_deck.py      # rebuild the submission deck
.venv\Scripts\python.exe ppt\diagram\render.py         # slide-3 diagram (fails loudly on overflow)
.venv\Scripts\python.exe ppt\patch_tech_slide.py       # swap the diagram into an existing deck
```
`build_deck.py`/`make_chart.py` additionally need `matplotlib`, which is **not** in the venv —
use the system Python 3.13 install for those two only.

**Gotchas.**
- **PDF export**: PowerPoint COM works on this machine (`New-Object -ComObject PowerPoint.Application`, `SaveAs ..., 32`), and it is the only way to render a .pptx here. Headless Edge cannot open .pptx.
- **SVG → PNG**: no `cairosvg`. Use headless Edge: `msedge.exe --headless --disable-gpu --force-device-scale-factor=2 --hide-scrollbars --screenshot=out.png --window-size=W,H file:///wrapper.html`. Some invocations need `--headless=new` and/or an explicit `--user-data-dir`.
- **Mirror sync**: `robocopy` to `Downloads\SIH-2026\sih-baghewala-code`, excluding `.venv` and `.git`.
- **Subagents**: Gaurav's Fable token budget is low — prefer Opus for subagents.

---

## 10. If you are resuming this project after a break, start here

1. Read §2 (status), §5 (numbers bible) and the latest §16.x of this log first. The team lead is **Gaurav**.
2. Read **this file** top to bottom. It is the only document that describes the whole project.
3. Then, depending on what you're asked:
   - **Code / physics / ML** → `docs/SPEC.md`, then `docs/reviews/integration_report.md`, then the relevant `docs/model-improvement/MODEL_IMPROVEMENT_PLAN_*.md`.
   - **Dashboard** → `dashboard/README.md` before touching anything; edit `dashboard/src/`, never generated HTML.
   - **Deck** → `ppt/notes/BUILD_NOTES.md` (the "STRICT rebuild" section) + `ppt/notes/WINNING_DECK_ANALYSIS.md`. Submit only the STRICT files.
   - **Any number** → `docs/research/baghewala_facts.md` for provenance, §5 above for the current values, `docs/study/TEAM_STUDY_GUIDE.md` for how to defend them.
   - **Competition mechanics / deadlines** → `docs/research/deep-dives/sih_winning_playbook.md`.
   - **Explaining it to Gaurav** → `docs/study/hinglish-pack/` (Hinglish); the English master is `docs/study/TEAM_STUDY_GUIDE.md`.
4. Before you change a number anywhere, check whether it appears in *all four* places it usually does: `params/field_params.json`, the dashboard's `BAKED`/constants, the STRICT deck, and `viva_prep.md` / the study pack. Number drift across artefacts is this project's most likely failure mode.
5. Run `git log --oneline` and `git status` first — as of this writing ~19 paths are untracked or modified (dashboard v4 and `docs/study/hinglish-pack/03`–`07`) and represent real, valuable, uncommitted work.

---

## 11. Corrections to the verbal handoff

Verified against `git log`, the file tree, and a live test run:

- **"229 problem statements" → 233.** `sih2026_ps.csv` contains 233 rows with 233 unique PS IDs.
- **"SIH26121 = generic RAG, rejected."** It is *eRTMAC-NWIS*, an offset-well knowledge/decision-support PS from the same sponsor, and `sih_winning_playbook.md` recommends it as the **hedge second submission**, not a reject. OIL posted 3–4 PS this year, all under Smart Automation.
- **"~12 commits" → 13**, `f70bbbb` (16:18) through `1a4101f` (18:14), all today. Commit 13 landed while this log was being written.
- **"dashboard v4 IN PROGRESS"** — it finished at 18:16. Four pages are on disk, **uncommitted and un-QC'd**. v3's single-file `index.html` was overwritten; recover it from `a32230e` if needed. The `MOCK` fallback flag moved from `index.html:648` to `dashboard/src/core.js:9`, which `docs/guides/DEMO_SCRIPT.md` and `docs/study/hinglish-pack/00_START_HERE.md` have not caught up with.
- **"3 model-improvement analysts"** — all three plans landed (ML last, 18:12) and are committed in `1a4101f`.
- **"3 Hinglish study-pack agents, 00-07"** — now complete, 00 through 07; 03–07 uncommitted.
- **"₹0.61 cr/yr conservative; ECON analyst may revise"** — it did, and rejected the figure outright as wrong on *both* the price (₹1,300/t is a gas-fired number for a field with no gas) and the denominator (6.8 cycles/well/year is physically impossible). Treat ₹0.61 cr/yr as retired.
- **"PRIMARY −30 %, SECONDARY −41.3 %"** is true of the **dashboard**, but the **STRICT deck's** Impact chart leads with "SOR 1.50 → 0.88 t/m³ (−41.3 %)" with a 20–30 % field commitment in the bullets. The two artefacts do not currently lead with the same number.
- **Steam quality/temperature**: params use 0.65 quality and 290 °C (midpoints of the confirmed 60–70 % and 280–305 °C) — the handoff's "q 0.6–0.7" is the source range, not the modelled value.
- **`docs/reviews/FIXES_APPLIED.md` contradicts `params/field_params.json`** on the Andrade constants (see TODO 20). The file is right; the review note is wrong.
- **Mirror is stale**, not current: last synced 16:42, before the STRICT deck, dashboard v3, `docs/research/deep-dives/` and `docs/study/hinglish-pack/` existed.

---

## 12. Work log — 25–26 Sep 2026

**25 Sep:** Repo restructured — 17 top-level entries collapsed to 9, docs consolidated under
`docs/`, decks split into `ppt/final/` (submit) and `ppt/archive/` (superseded). Already
recorded in §4. Pushed to `github.com/grv-io/sih-baghewala` — the header's "no git remote
configured yet" was stale; the remote exists and the commit count is now ~20.

**26 Sep — audit (3 agents, read-only, engine re-run).** Findings, tersely:

- Tier-1 engine (`a82cfa7`) is implemented but **uncalibrated**. The current engine
  reproduces **none** of the v1 numbers: reference set-points give **SOR ≈530** (the cycle
  dies day 1 — cutoff 3.0 m³/d is above the new peak of 2.83 m³/d).
- At cutoff 1.5: SOR **9.83**, 152.6 m³ oil, 93 d, 17.8 bbl/d peak, uplift **4×**,
  μ(290 °C) = **4.13 cP**.
- The "optimised" set-points from the frozen v1 model give **9.95** — 1.2% *worse* than
  cutoff 1.5, not better.
- Grid search best: **7.27** at 1,500 t / 15 d / 1.0 m³/d / 4 spm, with a **negative margin**.
- SPM has **no effect on oil** in the new engine (well is reservoir-limited); soak is flat.
- Physics runs **0.55 ms/cycle** vs the surrogate's **1.13 ms** — the "surrogate for speed"
  rationale in the original design was **false**.
- ML models and the synthetic CSV are still the frozen **v1** artefacts (13 Sep 16:21).
  Running `ml/optimize.py` today gives **1500 / 4 / 2.45 / 5.86 → SOR 1.34 (−7.5%)** —
  contradicting the engine numbers above, because it optimises against v1 physics that no
  longer matches the code.
- Tests: **21/24** (3 fail by design under v2 physics; two others pass vacuously; a third,
  `test_ipr::test_cold_rate_is_uneconomically_low`, exercises a retired `P_wf = 0.4·P_res`
  relationship that no longer exists in the code).
- v1 reproduction requires a worktree of commit **`6bb604d`**, not `8c6643b` — `8c6643b`
  already carries the Tier-1 params (it lands after `a82cfa7` in the log), so v1 code there
  still gives SOR 1.18, not the documented 1.2943/0.9062. `6bb604d` reproduces 1.2943/0.9062
  exactly.
- Study material scored **3/10 on factual currency**: every model number was stale, ₹0.61
  cr/yr was still present, `viva_prep.md` made false cross-validation claims, `DEMO_SCRIPT.md`
  described the old single-page dashboard, `GLOSSARY.md` had rod floating reversed, and deck
  slide 5's "commit to 20–30%" contradicted the study pack's own guidance.

**26 Sep — decision.** Present the v1 numbers as "prototype v1 simulation, self-audited,
physics v2 recalibration in progress" rather than attempt a same-day calibration before the
30 Sep deadline. **No physics or ML code was changed.**

**26 Sep — fixes landed** (one line per artefact):

- **Deck** (`ppt/`) — slide 3 reframed to advisory wording ("advisory set-points to the
  operator, SCADA hook planned") + Python 3.13 tech-stack chip; slide 4 reframed to
  "Parameter-sweep sanity tests"; slide 5 reframed off the 20–30% commitment; Andrade
  1934 → **1930**; PDF re-exported via PowerPoint COM; slide-3 diagram chip re-rendered
  for "3.13".
- **Dashboard** (`dashboard/`) — 21/24 shown everywhere (footer, methodology page); "Field
  practice" relabelled **"Optimiser midpoint baseline"**; bilingual provenance line
  ("Prototype v1 physics — self-audited; physics v2 recalibration in progress") added to
  the overview and methodology pages; a v2-physics bullet added to methodology; the test tag
  recoloured amber; per-module test counts added.
- **`params/CHANGELOG.md`** — bumped to rev 4 (Tier-1 params).
- **Hinglish study pack** (`docs/study/hinglish-pack/00`–`07`) — v1/v2 banners on every
  file; a "safe-to-say" block added to 06; killer questions N1–N16 added; §2b rewritten for
  v2 physics; §5b rewritten for economics; demo commands fixed (no stray `::` comments,
  explicit warning never to run `generate_data.py` / `train.py`); the `MOCK` flag location
  corrected to `core.js:9`; `console.html` confirmed as the demo page; every `8c6643b`
  worktree reference corrected to `6bb604d`.
- **`docs/study/TEAM_STUDY_GUIDE.md`** — v1 labels added throughout + "Now (Tier-1)" notes;
  a primer box added; §A killer-question table added; rows 53–66 added.
- **`docs/study/viva_prep.md`** — banner added; a never-say table added; K1–K24 added; false
  cross-validation / k-fold / RMSE claims removed; the Mehsana reference fixed.
- **`docs/guides/DEMO_SCRIPT.md`** — rewritten for the v4 four-page flow (~2:45 runtime).
- **`docs/guides/GLOSSARY.md`** — expanded 20 → 78 terms; entry #6 (rod floating) fixed.

**Still open (TODO, prioritised):**

- Tier-1 recalibration — target SOR ≈4.4 at 1,500 t; `AOF_REF` 1.3–1.5; reset the cutoff
  search range to ≈[1.2, 4.0].
- Rewrite the 3 red tests; fix the two vacuous passes and the one retired-relationship test
  (`test_ipr::test_cold_rate_is_uneconomically_low`).
- Retrain ML on v2 physics once calibrated.
- Re-bake the dashboard's `BAKED` series.
- Rebuild the deck with v2 numbers.
- Team name / Team ID placeholders still literal on the deck.
- Team formation still not started.
- Slide-3 diagram **image** (not text) still says "pytest (24 tests)" and "CLOSED LOOP →
  VFD" — `ppt/diagram/slide3_rendered.png` is stale and needs re-rendering.
- Archived `ppt/build_deck.py` (superseded, kept for reference only) still says Python
  3.12 / Andrade 1934 — out of scope to fix since it is not the build path.
- K12 in `viva_prep.md` (the ChemE-contribution question) is a template — Gaurav needs to
  personalise it.
- Demo timing and the stress-test alarm have not been verified end-to-end in a browser.

---

## 13. Work log — 26 Sep 2026 (evening): physics v2 calibration → ML retrain → dashboard re-bake → docs

Commits on `physics-v2` this pass, most recent first (`git log --oneline -8`):

```
a825cbd Dashboard re-baked on physics rev 5: published-practice baseline, margin/day objective, soak held at practice, rev-5 provenance
01d4065 Merge branch 'main' into physics-v2
8769d9f Add data hunt + OIL-engineer UX review docs
37d229d ML retrain on physics rev 5: log-oil + margin/day regressors, float classifier, margin/day optimiser with practice-band SPM
5c76ef5 Dashboard UX for OIL engineers: recommendation card, plain labels, jargon folded, real Hindi, approx-run isolation, Plotly bundled, auto-run
9d0bffe Physics v2 calibration: reference SOR 4.09, uplift 5.7x, 182-d cycle, margin +Rs 8.8 L; 57 pass + 2 strict xfail
bfa5963 PROJECT_LOG: 25-26 Sep work log, status table + TODO refresh
40a31ce English study guide, viva prep, demo script, glossary: 26 Sep audit fixes
```

**What was done, per artefact:**

- **Physics** (`9d0bffe`, `twin/`) — calibrated to rev 5. Three internal bugs found and
  fixed by the team's own debugging, not a reviewer: (1) the Marx–Langenheim heat
  balance credited only latent heat of the injected steam, missing the sensible-heat
  term (3.6× more delivered heat once fixed); (2) wellbore heat loss was subtracted
  twice — once via the sandface-quality ratio, once via an extra loss multiplier on
  top of it; (3) the sucker-rod pump's oil capacity was compared against the oil rate
  alone, when the produced stream (and the pump) handles liquid — at 85% water cut
  this overstated pump capacity 6.7×. Fixing these three, plus retuning `AOF_REF_M3D`,
  `PRESSURE_BOOST_PER_T_KPA` and `SPM_MARGIN` against the BGW-8 benchmark table, gives
  **57 passed, 2 xfailed**. Full iteration log: `docs/model-improvement/TIER1_PROGRESS_LOG.md`
  §4; constant-by-constant diff: `params/CHANGELOG.md` rev 5.
- **ML** (`37d229d`, `ml/`) — regenerated `data/synthetic_cycles.csv` (3,000 LHS rows,
  seed 42) against the calibrated twin, retrained: an oil regressor (log-oil target,
  SOR now derived from it, not fit directly), a margin/cycle-day regressor, and the
  floating-risk classifier (all XGBoost, single 80/20 hold-out, seed 42, **no
  cross-validation**). Retired `sor_model.joblib`. Changed the optimiser's objective
  from minimising predicted SOR to **maximising predicted ₹ margin/cycle-day**, with
  `spm` restricted to the 3–6 practice band (was the full 4–12 range).
- **Dashboard** (`5c76ef5`, `a825cbd`, `dashboard/`) — UX pass for OIL engineers
  (recommendation card, plain labels, jargon folded, Hindi copy, approx-run isolation)
  then re-baked with the rev-5 published-practice baseline and rounded recommendation,
  57/57-test tag, margin/cycle-day led as the primary claim.
- **Docs** (this pass) — study pack, TEAM_STUDY_GUIDE, viva_prep, DEMO_SCRIPT,
  GLOSSARY, README, this file: banners and numbers moved from "v2 implemented but
  uncalibrated, quote neither" to "v2 calibrated, quote these numbers."

**Canonical numbers (physics-verified, use exactly these):**

| | steam t | soak d | cutoff m³/d | spm | SOR t/m³ | oil m³ | cycle d | ₹/cycle-day | max FI | alarm d | steam ₹/cycle | tCO₂ | diesel L |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline (b) published-practice (BGW-8-derived, not OIL's current practice) | 1,300 | 10 | 1.3 | 5 | 4.11 | 316 | 185 | 2,739 | 0.24 | 0 | 76.1 L | 291 | 111,205 |
| Recommended (rounded) | 1,700 | 10 (fixed) | 0.85 | 5 | 3.81 | 446 | 268 | 7,893 | 0.55 | 0 | 99.6 L | 380 | 145,422 |

Deltas: SOR −7.3%, margin/cycle-day +188%. Reference calibration point
(1,500 t / 7 d / 1.2 m³/d / 5 spm): SOR 4.09, uplift 5.66×, peak 15.9 bbl/d, 182
produce days, μ(290 °C) 4.13 cP, margin +₹8.8 L/cycle. Steam: 71 kg HSD/t → ₹5,856/t
bulk (base case) / ₹8,366/t retail; 224 kg CO₂/t. **The recommended cycle burns more
steam and emits more CO₂ in absolute terms per cycle** (1,700 t vs 1,300 t) but
produces 41% more oil, so SOR and CO₂ per m³ oil fall — never claim an absolute
per-cycle CO₂ reduction.

**Known gaps, disclosed as strict xfail, not hidden:**

1. **P_res sensitivity**: dropping reservoir pressure 11.4 → 7.4 MPa moves SOR **+61%**
   vs a published Liaohe-field band of +20–40%. Rate scales with drawdown and the
   cutoff is absolute, so a lower-pressure cycle hits it sooner; Liaohe's weaker
   response likely comes from drive mechanisms (gravity drainage, compaction, solution
   gas) this twin does not model.
2. **No interior soak optimum**: soak sensitivity is <2% (SOR 4.11→4.09→4.06 over
   3→7→15 d) — Boberg–Lantz has no soak benefit beyond conduction; heat
   redistribution into the pay and in-situ flashing on early production are not
   modelled. The recommendation therefore **holds soak fixed at the 10-day published-
   practice value** rather than presenting a twin-derived soak recommendation.

**Judgement calls the team should know before presenting:**

- Base-case fuel is **bulk diesel at a 30% discount off retail — the discount itself
  is unsourced**, justified by revealed preference (OIL ran 19 CSS jobs in FY26, so a
  sensible cycle must pay). At retail pricing the baseline cycle **loses ₹28.8 L**.
- `BL_DELTA_FACTOR = 0.5` (Boberg–Lantz) is unverified against the original 1966 JPT
  paper, which could not be retrieved this session — the single most sensitive
  constant in the model (1.0 → reference SOR ≈5).
- `fluid.water_cut = 0.85` implies ~139% of injected water produced back in cycle 1 —
  high for a first cycle; open item.
- Pump geometry (1.75 in plunger × 86 in / 2.18 m stroke) is **typical heavy-oil
  sizing, not Baghewala-specific** — top data request to OIL.
- Net pay kept at **12 m** (placeholder) against the 2022 Yasin et al. *Scientific
  Reports* paper's **50 m gross** Jodhpur Fm thickness at Baghewala-1. The paper's
  porosity figure (16–25% vs our 9%) is irrelevant to the twin — `porosity` is not
  read anywhere in `twin/` — but net-pay **thickness** is first-order (h=12/20/30/50 m
  → SOR 4.09/4.05/4.38/5.27) and the BGW-8 5–6× uplift only reproduces for roughly
  8–20 m net pay, so 50 m gross must not be substituted for net-pay thickness. Open
  item: get a net-pay datum from OIL.

**Data hunt** (`docs/research/DATA_HUNT_2026-09-26.md`): no public Baghewala-specific
CSS cycle or production dataset was found this session. The best lead for an open,
per-well, cycle-capable calibration/benchmark dataset is **Kern River, CA (CalGEM Well
Finder / annual SQL-backup downloads)** — extraction is in progress as a separate,
concurrent workstream (see `data/external/calgem_css/` and `docs/research/CALGEM_*.md`
for its output once landed; not detailed here as it was still running while this log
was written).

**Decisions taken by the orchestrator on the team lead's behalf** (flag for
confirmation): the optimiser's objective is **₹ margin/cycle-day**, not SOR, because
under the calibrated physics SOR falls monotonically as steam is cut, which is not the
field's actual goal; **soak is fixed at the 10-day published-practice value** rather
than optimiser-searched, since the twin has no interior soak optimum; the baseline for
comparison is the **published-practice** BGW-8-derived set-points, not the old
param-midpoint baseline. **The deck (`ppt/`) was deliberately not touched** — it still
carries the v1 "prototype, since audited" caption and framing and is now inconsistent
with the dashboard's rev-5 numbers. **Decision needed tomorrow** from the team lead:
whether/how to rebuild it before the internal round.

**Open TODOs (carried forward + new):**

- Deck rebuild decision (numbers, captions, and the slide-3 diagram image, which still
  says "24 tests").
- Team name / Team ID registration; team formation; SPOC deadline still unresolved.
- K12 personalisation in `viva_prep.md` (if still a template — see §8/§12 above).
- Turn the Kern River/CalGEM benchmark into an actual test once extraction lands.
- Source `BL_DELTA_FACTOR` against the original 1966 Boberg–Lantz paper.
- Get real pump geometry and net-pay thickness from OIL.
- Resolve retail-vs-bulk diesel pricing with a real OIL number (current 30% bulk
  discount is unsourced).
- P_res model gap: no drive-mechanism physics (gravity drainage, compaction, solution
  gas) to explain the Liaohe-band mismatch.

### §13.1 · Late addendum, 26 Sep night — Kern River data, UQ, CI landed (commits 1b12291 → a77509b)

- **Real-field benchmark now exists.** `data/external/calgem_css/` — 9,692 real cyclic-steam
  injection cycles (5,771 wells, Kern River / Midway-Sunset / Coalinga, 2018–21) from CalGEM
  SQL backups via the Inside Climate News GitHub mirror (CalGEM's own site is unreachable
  from here). Official 2021 field SORs: **3.47 / 7.60 / 8.24**. Our reference 4.09 and
  recommendation 3.81 sit inside the band → encoded as 3 tests in `tests/test_benchmarks.py`
  (skip if data missing). Limitation: no per-well monthly *oil* → no per-cycle SOR/uplift;
  band check only. Doc: `docs/research/CALGEM_CSS_BENCHMARK_2026-09-26.md`.
- **UQ (`ml/uq.py`, 1,500 paired MC draws, true physics).** Recommendation beats baseline
  in **100 %** of draws (margin and SOR). **But absolute economics are marginal:**
  P(margin/day > 0) = 47 % at the recommendation, 31 % at baseline; p50 margin is
  **−₹1,201/day** (rec) vs the nominal +₹7,893. Nominal sits near p90 because the base
  constants are at the favourable end of their ranges. Drivers: 1) `BL_DELTA_FACTOR`
  (unverified), 2) `water_cut`, 3) diesel bulk-vs-retail. OIL runs 19 jobs/yr, so either
  their costs/prices differ or our BL factor is pessimistic → **top data ask**.
- Dashboard shows the UQ range under the ₹/day line and a new "Uncertainty" section on
  Model basis. **Decision needed (lead):** headline nominal ₹7,893 (current) vs p50, and how
  to phrase "marginal under uncertainty" to OIL.
- CI: `.github/workflows/tests.yml` (py 3.12/3.13) + README badge. **60 passed, 2 xfail.**
- Deck still untouched (v1 caption). Worktrees left on disk: `sih-baghewala-ux` (main),
  `sih-baghewala-uq` (uq-ci, merged) — safe to `git worktree remove` both.

---

## 14. Work log — 26 Sep night → 27 Sep: v3 physics, computed dyno cards, calibration loop, economics v2, rev-9 cascade

Commits this pass, oldest first (`git log --oneline 5d91a57..44a1009`):

```
b5ccee8 Dashboard: robust delta headline, 'Your prices' economics inputs (re-priced, not re-optimised), Hindi
e606bfb Calibration loop: fit BL/water-cut/thickness/AOF from observed cycles, physics re-recommendation, /calibrate API, pseudo-real demo + tests
de143fa Merge branch 'econ-ui'
93b59e3 Add OIL data-request letter; CalGEM benchmark: second attempt notes (production portal needs a real browser)
43677fe Computed dynamometer cards: pump card + Gibbs wave-equation surface card, fault-signature classifier, validation tests
d09dee8 Merge branch 'dyno'
bb7f72a Physics v3: sourced Boberg-Lantz delta (computed per PEH Eq. 15.74), P_res benchmark re-specified, soak bounded
183a75a Merge main into physics-v3 (calibration loop, dyno cards, econ UI)
b55e252 Dashboard: Calibrate-from-field-data section - baked pseudo-real demo, CSV upload (MOCK preview / live /calibrate), calibrated recommendation staging
b3e1572 Merge branch 'calib-ui'
ef88bed Console: computed dynamometer cards (surface + pump) follow the cycle; rod-float separation on the 12-SPM stress test
bd65113 Merge dyno-ui: keep both STR blocks, rebuild pages
9060609 Economics v2: incremental-oil basis, daily opex, corrected srp energy; UQ fixes BL delta at 0.5; calibration frees water_cut
d8d8e71 Merge main into physics-v3 (dyno-UI + calib-UI dashboard merges)
02194d2 Price deck rev 9: OIL FY25 realisation; cascade rec re-bake
6361cde Dashboard rev 9: incremental margin headline, FY25/FY26-floor prices
44a1009 dashboard/README.md: rev 9 (incremental margin, FY25/FY26-floor decks)
```

**Per artefact - what and why:**

- **Physics v3** (`bb7f72a`) - sourced `BL_DELTA_FACTOR = 0.5`: it is exactly the half
  inside Boberg and Lantz's own definition of delta (`f_pD = (1/2Q) times integral of Q_p dt`,
  SPE *PEH* Vol. V ch. 15, Eqs. 15.70/15.73, reproducing the 1966 JPT paper), forced by
  energy conservation with no conduction - not a free constant. Delta is now computed per
  produce-day from the simulated oil/water streams via Eq. 15.74 (oil: API-derived heat
  capacity plus Gambill's c_o; water: steam-table enthalpy), replacing the unsourced
  `CP_LIQUID_JM3K = 4.0e6` blend. Full citation and derivation:
  `docs/model-improvement/BL_DELTA_FACTOR_SOURCE.md`. The rev-5 P_res xfail was
  re-specified, not widened: the Liaohe +20-40% benchmark was the wrong comparison (a
  multi-decade field-life drift with re-design and CO2 assist, not a same-design
  single-cycle sensitivity); replaced with a derived Darcy/Vogel-drawdown band
  (`test_depletion_response_is_darcy_proportional`), which the twin passes. The soak
  xfail was kept and tightened after three rejected mechanisms (soak-only conductive
  spreading makes soak a monotone free lunch; uncondensed-steam flashback holds under 1%
  of the cycle's heat; gravity segregation is irrelevant against the drawdown) -
  Boberg-Lantz has no soak benefit beyond conduction timing, matching PEH's own "soak
  should be as short as possible." `pytest -q` gave 67 passed, 1 xfailed at this commit.
- **Computed dynamometer cards** (`43677fe`, `ef88bed`) - `twin/dyno.py`: a Gibbs (1963)
  rod wave-equation finite-difference solve (surface plus pump cards), chosen over RP 11L
  because RP 11L needs chart look-ups and has no carrier-bar separation, which is exactly
  the rod-float signature needed. Validated against RP 11L static limits (within 10%),
  card-area vs pump-plus-damping work (0.2% error or better), and Mills' rigid-rod
  approximation (FD/Mills ratio grows with N/N0 as expected). Rod-float separation onset
  independently reproduces the SPEC's approximately 0.6 floating-index alarm line at
  every tested SPM. Replaced the dashboard's illustrative `buildDynoLoop` lens with real
  computed cards on the console page. Full method and validation:
  `docs/model-improvement/DYNO_CARD_MODEL.md`.
- **Calibration loop** (`e606bfb`, `b55e252`) - `twin/calibrate.py` fits the twin's
  biggest uncertain constants to observed CSS cycles (`scipy.optimize.least_squares`,
  bounded, deterministic); `ml/recommend_physics.py` re-recommends directly against the
  recalibrated physics (grid search, no surrogate - the trained ML surrogates were fit on
  the old physics and would silently mismatch a recalibrated params tree). `POST
  /calibrate` and `GET /calibrate/demo` expose it over the API. Honest identifiability
  finding: `bl_delta_factor` and `water_cut` correlate at essentially -1 (they enter only
  through their ratio) and `aof_ref_m3d`/`thickness_m` at +0.97 to +0.99 - both disclosed,
  not hidden; a downhole temperature or pressure log, not more cycle totals, would split
  them. Dashboard "Calibrate from field data" section added (CSV upload, MOCK preview /
  live `/calibrate`, calibrated-recommendation staging).
- **Economics v2** (`9060609`) - closed physics v3's own section 7.6 finding (the margin
  had no daily opex and no cold-production counterfactual, so "lower cutoff is always
  better" never triggered a re-steam point). Added a cold-well baseline (same well,
  unstimulated, same calendar window including inject plus soak), daily opex (Rs 5,000/d
  `[ASSUMPTION]`) plus corrected pumping power, and fixed `srp.energy_kWh_d`
  (closed-loop polished-rod work, crediting rod weight back on the downstroke - the old
  estimate was 1.4 to 3.6 times the true dyno-card energy). `ml/uq.py` stopped varying
  `bl_delta_factor` (sourced, fixed at 0.5) and started varying `water_cut` in its place;
  `twin/calibrate.py`'s default free parameters became `water_cut, aof_ref_m3d,
  thickness_m`. `pytest -q` gave 116 passed, 1 xfailed.
- **Price deck rev 9** (`02194d2`, `6361cde`, `44a1009`) - re-priced the base case to
  OIL's own CONFIRMED FY25 realisation (US$78.09/bbl, Annual Report 2024-25) minus the
  existing $10/bbl heavy-oil discount `[ASSUMPTION]`, kept the old $65/bbl FY26 planning
  floor as a named comparison preset (`params/CHANGELOG.md` rev 9), re-baked the ML/UQ
  cascade on both decks, and updated the dashboard (`dashboard/README.md`, incremental
  margin headline, FY25/FY26-floor one-click presets).

**The canonical numbers (rev 9) are in section 5 above** - do not re-derive them here;
this section is the decision/provenance record, not a second copy of the numbers bible.

**Three big findings:**

1. **`BL_DELTA_FACTOR = 0.5` is sourced exactly, not a fitted or unverified constant** -
   it is the half inside Boberg and Lantz's own delta. The earlier UQ finding "BL is the
   largest margin driver" (rev 5, `ml/uq.py` sampling U[0.35, 1.0]) was therefore an
   artefact of sampling a physically excluded range - 1.0 double-counts the produced heat
   and violates energy conservation. With BL fixed, the real number-one UQ driver is
   `water_cut`.
2. **Switching the money objective from gross to incremental margin flips profitability
   at the old price floor.** Every SOR/oil/margin number in this repo through rev 5 was
   computed as gross margin (revenue from all oil produced, no opex, no cold-well
   counterfactual) - which credits CSS with oil the well would have made anyway. Once the
   money is computed incrementally (rev 8), the model loses money against the cold well at
   every feasible set-point at the old $65/bbl price floor. That is what forced the
   price-deck decision (rev 9): OIL's own confirmed FY25 realisation is the deck at which
   CSS actually pays, and the $65 floor was never a realisation to begin with (it is the
   CMD's forward planning number). Both decks are now shown side by side, never one alone.
3. **The rev-5 recommendation (1,700 t / 0.85 m3/d / 5 spm) was about 12-13% off the
   true-physics grid optimum**, on both the base and FY25 decks (TIER1 section 7.5, 8.6) -
   a gap that belonged to the ML optimiser's surrogate plus float-probability penalty, not
   to the physics. The lever the grid found was spm 5 to 4 with cutoff 0.85 to 0.70 m3/d:
   lower SPM keeps the rods ahead of the horsehead further into the cold tail, letting the
   cycle run longer before the float-index limit binds. The cascade recommendation is now
   **1,600 t / 10 d (fixed) / 0.70 m3/d / 4 spm** - a minimax-regret point within
   Rs 214/cycle-day of either deck's own true optimum.

**Decisions taken on the lead's behalf (flag for confirmation):**
- Optimiser/dashboard money objective is incremental margin per cycle-day, not gross,
  and not SOR (which falls monotonically with steam under the calibrated physics).
- Dashboard base case is the FY25 realisation deck; the $65 floor is a named comparison
  preset, not deleted.
- Soak stays fixed at the 10-day published-practice value - the twin has no defensible
  interior soak optimum (xfail, kept deliberately, not silently dropped).
- **`ppt/` was deliberately not touched** in this entire pass (physics v3, dyno cards,
  calibration loop, economics v2, price deck) - it still carries the v1 "prototype, since
  audited" caption and rev-5-or-earlier numbers, and is now inconsistent with the
  dashboard on TWO fronts: the numbers, and the gross-vs-incremental story itself.

**Human TODOs (cannot be done from this session):**
- **CalGEM per-well monthly oil production** - confirmed to live at
  `wellstar-public.conservation.ca.gov/General/PublicDownloads/Index`, geo-blocked from
  India (confirmed in a normal browser 27 Sep) — needs US VPN or a US-based collaborator.
  Deferred past the idea-round deadline (30 Sep); keep for the final round. A human with
  access will download and re-run `extract_calgem.py` joined against `inj_all_filtered.csv`
  to get a real per-cycle SOR/uplift/peak-rate comparison, not just the field-annual band
  check that exists today. See `docs/research/CALGEM_CSS_BENCHMARK_2026-09-26.md` §"Third check".
- Team formation (6 members, at least 1 female) and Team Name/ID - still literal
  placeholders.
- SPOC deadline conflict (15 Sep guidelines PDF vs 30 Sep everywhere else) - still
  unresolved; get it in writing.
- K12 in `viva_prep.md` (ChemE-contribution question) - still a template; Gaurav needs to
  personalise it.
- **Deck rebuild decision.** The deck is now stale on two independent fronts (numbers,
  and the entire gross-vs-incremental economics story) - a team-lead call on whether or
  how to rebuild before the internal round, not something to auto-decide from this
  session.

**Open model TODOs (carried forward):**
- Soak mechanism remains open at Tier-3 (a numerical radial-conduction model that treats
  spread heat consistently in both soak and production, not just soak) - not attempted
  here; the xfail is honest, not a placeholder for laziness.
- Royalty (Rs 2,987 cr FY25) and OID cess (Rs 2,567 cr FY25) are not modelled; the money
  figures here are pre-levy / national-value, not OIL's own P&L view.
- No Indian per-well onshore lifting-cost figure was found for `opex_inr_per_day`
  (Rs 5,000/d is an assumption cross-checked only against implied $/bbl ranges).
- Real rod string and pump specs are still `[TYPICAL]`, not Baghewala-specific - top data
  request to OIL alongside net-pay thickness.
- `ml/optimize.py`'s `optHistory` logging still reports gross margin in places even
  though the objective itself is incremental (rev 9) - cosmetic, not a correctness bug,
  but should be cleaned up before it confuses a viva question.
- Archived `ppt/build_deck.py` (superseded, kept for reference only) still says Python
  3.12 / Andrade 1934 - out of scope, not the active build path.

### §14.1 · 27 Sep morning — deployable service landed (commits f780344 → 2db2d62, merged to main)

- `api/` is now a package: settings (env), SQLModel/SQLite (Run / Recommendation /
  Calibration / Job), background jobs with `/api/jobs/{id}` polling and request-hash cache,
  typed routers under `/api/*` (params, simulate, optimize, recommend/physics, calibrate,
  uq, dyno/cards, runs, health/version). Old flat paths kept as hidden aliases.
- FastAPI mounts `dashboard/` at `/`; the dashboard auto-detects live mode (`file:` →
  baked; served → live API, chip "Live API · rev 9"), optimiser polls a job with a progress
  state, dyno panel computes cards live for the current set-points.
- Deploy kit: `Dockerfile`, `.dockerignore`, `docker-compose.yml` (postgres profile),
  `render.yaml`, `fly.toml`, `railway.json`/Procfile, `.env.example`, `docs/DEPLOY.md`;
  CI gained a Docker build + `/api/health` job. **127 passed, 1 xfail.**
- Gaurav deploys himself (his call, 27 Sep). Frontend stays framework-free by design —
  see README "Run as one service" for the judge-facing line.
- CalGEM production portal confirmed geo-blocked from India → dropped for the idea round.

---

## 15. 27 Sep: external reviews → hardening → waves 3–4 → rev 12 cascade

Rev 9 (§14) went out for two independent external reviews the same day: a petroleum
engineer + data scientist reading as a **technical** reviewer, and a separate **judge**
pass reading as a competition screener would. Scores: **61/100 (judge)**, **52/100
(technical)**. What follows is four physics passes on branch `harden` responding to
both, in order: **hardening** (rev 10, commit `54f6bc7`) → **physics wave 3** (rev 11,
`1c95694`) → **physics wave 4** (rev 12, `cd7eebe`) → **the rev-12 cascade** (ML/data/
UQ/dyno/scheduler re-bakes, `5282f6c`). Full derivations:
`docs/model-improvement/TIER1_PROGRESS_LOG.md` §9–§11; constant-by-constant diffs:
`params/CHANGELOG.md` rev 10–12.

### 15.1 Findings addressed / mitigated / open

The technical review shipped four reproducible probes (`probe1-4.py`) plus a written
list; only the findings this session can source directly from `TIER1_PROGRESS_LOG.md`
are mapped below — the review document itself lived in an implementer's session
scratchpad, not the repo, so this is not a claim to have every one of the "top 10" in
hand, only the ones with a traceable fix.

| # | Finding | Status | Where fixed / why open |
|---|---|---|---|
| 1 | `summary()` was not dt-invariant: SOR 4.03 / 2.02 / 1.01 at dt = 1 / 0.5 / 0.25 | **Fixed** | rev 10, `54f6bc7`: totals now Σ(rate)·dt; re-checked to ≤0.15% agreement across dt (TIER1 §9.1.1) |
| 2 | `S_COLD` (skin) was a hardcoded module constant, not in params or UQ; sweeping it 0→8 moved uplift 3.28×→6.96× | **Fixed** | rev 10: moved to `params/ipr.s_cold`, sampled in UQ, opt-in free parameter in `twin/calibrate.py` (TIER1 §9.1.2) |
| 3 | Pressure-boost constant likewise hardcoded; 0→2 moved uplift 5.13×→6.19× | **Fixed** | rev 10: `reservoir.pressure_boost_kPa_per_t` moved to params + UQ (TIER1 §9.1.2) |
| 4 | The cold (unstimulated) rate was identical at every `μ_ref` — physically the cold rate must fall as oil gets heavier | **Fixed** | rev 10: `AOF_REF_M3D` now scales by Darcy mobility 11,500/μ_ref (TIER1 §9.1.3) |
| 5 | 83–96% of the headline gain was the assumed baseline cutoff (1.3 m³/d) moving, not real physics ("headline is a baseline artefact") | **Fixed, differently than expected** | rev 10/11 confirmed it still held; rev 12's float-onset rule makes the cutoff contribute **0%** of the gain instead — the finding stopped applying because the mechanism it targeted (a fixed rate cutoff) is no longer what ends the cycle (TIER1 §11.7) |
| 6 | Steam P–T inconsistency: 290 °C at the assumed pressures is not a saturated state; the pressure-boost / latent-heat mechanism had no physical carrier | **Fixed** | rev 11: injection pressure is now a lever, steam state set by IAPWS-IF97 from the wellhead pressure, `P_current` made an explicit `[ASSUMPTION]` (TIER1 §10.1–§10.2) |
| 7 | Rod drag used the reservoir oil's viscosity, ignoring that the produced stream is an emulsion | **Fixed, then corrected twice** | rev 10 added Brinkman emulsion drag; rev 12 replaced it with Pal–Rhodes (algebraically Brinkman below 60% water) plus a 10× cap (TIER1 §9.1.4, §11.1) |
| 8 | Wording overclaimed Kern River as a huff-and-puff analogue / "9,692 cycles validate the SOR" | **Fixed** | rev 10 wording: "a shallow, predominantly steamflood field with a cyclic-steam subset; field-level SOR band only" (TIER1 §9.1.8, `tests/test_benchmarks.py`) |
| 9 | Rod-pump peak-load model uses oil density for `srp.peak_rod_load` but the mixture density for the dyno card — an internal inconsistency (review §7) | **Open** | not changed through rev 12 (TIER1 §9.10 item 4) |
| 10 | Royalty and OID cess are not modelled; ₹ figures are pre-levy/national-value, not OIL's own P&L | **Open** | unchanged since rev 9; at ~20%+20% levies the rev-10 recommendation's incremental margin goes negative (TIER1 §9.10 item 5) |

Items explicitly still open at rev 12, matching the coordinator's own framing: **the
cold well is not pumpable** (a real cold, unstimulated Baghewala well cannot be
rod-pumped at the 2-spm floor on the assumed unit under any published W/O emulsion
law — new strict xfail, not fixed; it inflates every incremental ₹ figure by ~₹2.7k/d
until a cold-well dyno card resolves it); **royalty/cess** (above); **no real
production data** (all 3,000+ training cycles remain physics-simulated); **soak**
(still a strict xfail — no defensible interior optimum in Boberg–Lantz).

The **judge** review's own numbered findings are not separately reconstructable from
repo files (no equivalent probe/finding list was committed) — its score is recorded
here for provenance, and this session's presentation-level responses to a judge-shaped
critique are folded into the "never say" tables throughout `docs/study/` (rewritten
this pass) and the honesty-lines discipline that already runs through this log.

### 15.2 The physics story, in order (rev 9 → rev 12)

1. **Boberg–Lantz δ computed and sourced** (physics v3, §14) — 0.5 is exactly the ½
   inside Boberg & Lantz's own definition, not a fitted constant; the earlier UQ
   finding "δ is the biggest margin driver" was an artefact of sampling a physically
   excluded range.
2. **Incremental economics** (Economics v2, §14) — ₹ decisions run over the same well
   produced cold across the same calendar window, not gross oil.
3. **Hardening after the external review** (rev 10) — skin and `K_VISC` moved to
   params + UQ, a `dt`-summation bug fixed, the cold rate made viscosity-dependent.
4. **Water cut modelled as a state** (rev 11) — the produced stream is
   water-continuous early (~0.87, condensate flowback) and turns oil-continuous late
   (<0.70 inversion), so **rod float is a late-cycle phenomenon** — restoring the
   rod-float thesis honestly after rev 10 had found it didn't bind at all at a
   constant 85% cut.
5. **Injection pressure as a lever** (rev 11) — steam state set by the wellhead
   pressure via IAPWS-IF97, `P_current` 9.4 MPa `[ASSUMPTION]`, plus a stroke-length
   lever.
6. **The float-onset produce-end rule** (rev 12) — the cycle ends on a rate cutoff
   (economic backstop) **or** 3 consecutive floating-index-alarm days, matching what
   an operator actually does instead of running floating rods for months or writing a
   fragile high fixed cutoff.
7. **AOF retuned to the field peak band** (rev 12) — `AOF_REF_M3D` 0.46→0.56 to put
   the reference peak inside the field's 15–40 bbl/d band; the reference-SOR band was
   correspondingly re-specified 3.8–4.6 → 3.0–4.6.

### 15.3 Canonical rev-12 numbers

See §5 above for the full table (do not re-derive it here). Three-line story: **slow
rods, short stroke, pull when they float** — 3 spm / 64-in stroke, produce until the
float alarm has persisted 3 days (0.6 m³/d backstop), because almost all of the gain
(SPM 62%, stroke 32%) is delaying the float onset, not producing to a lower rate.

### 15.4 Decisions taken on the lead's behalf (flag for confirmation)

- **Float-onset produce-end rule adopted as the default operating policy**, not just
  a feasibility check — it changes which recommendation is canonical (TIER1 §11.3).
- **AOF retuned to the field's 15–40 bbl/d peak band, overriding this project's own
  earlier 3.8–4.6 reference-SOR band** (re-specified to 3.0–4.6 to accommodate it) —
  the peak-rate field datum was judged more load-bearing than our own internally
  chosen SOR target (TIER1 §11.4).
- **Pal–Rhodes emulsion law capped at 10×** — the brief's premise that Brinkman
  over-predicts at 30–50% water was tested and not supported; the cap itself (not the
  law) is what changes the physics near the water-cut inversion, and it is an
  `[ASSUMPTION]` at the top of the published band (TIER1 §11.1).
- **Cold-well vs. shut-in framing** — the incremental ₹ figures are reported against
  an *idealised pumpable* cold well (P(incremental > 0) = 0.34 FY25 / 0.12 $65 in UQ);
  a gross-basis reading, closer to "vs. shut-in", gives P = 0.77 FY25 / 0.45 $65. Both
  decks and both readings are shown, since the real cold well is not pumpable in the
  model (a strict xfail) and neither counterfactual is the field's literal alternative.
  *Correction (27 Sep 2026, later pass): P = 0.12 / 0.45 were previously quoted
  unlabelled here even though this section's own headline is the FY25 deck (see
  §15.4 below) — 0.12/0.45 are the $65-deck values; 0.34/0.77 are FY25.*
- **FY25 realisation stays the base price deck** (carried from rev 9, §14) — the $65
  floor stays a named comparison preset where the rev-12 recommendation is only
  ≈ break-even (+₹40/d).

### 15.5 Human TODOs (cannot be done from this session)

- Team formation (6 members, ≥1 female), Team Name/ID, and the SPOC deadline conflict
  — still unresolved, carried from §8/§12/§14.
- K12 in `viva_prep.md` (ChemE-contribution question) — still a template.
- **Deck slide 5 and slide-3 labels need updating to rev 12.** The deck was already
  stale on the gross-vs-incremental story at rev 9 (§14); it is now stale on the
  headline numbers, the recommendation's set-points (slide 5: 1,000/10/85/64/3, not
  1,600/10/0.70/4), and the float-onset framing. Not touched this pass — a team-lead
  rebuild decision, same as every prior physics cascade.
- **Repository visibility** — still team-controlled; the README already carries the
  "ask the team lead for access" line.
- **AI-mention lines decision.** This project's build process has made heavy use of
  AI-assisted development throughout (this log documents it openly, commit by
  commit). Whether and how to disclose that on the deck or in the viva is a
  team-lead call this session does not make — flagging it as an open decision, not
  deciding it either way.
- **CalGEM geo-block** — the production portal is confirmed geo-blocked from India
  (§14.1); still needs a US VPN or collaborator, deferred past the idea round.

### 15.6 Open model items

- **Downstream regeneration.** `data/synthetic_cycles.csv` (still 4-D LHS, not the
  rev-12 6-D design), `ml/models/*.joblib` (still rev-9-trained), the dashboard and
  the deck are **not yet regenerated on rev-12 physics** — that is the cascade's
  remaining job once `harden` merges to `main`.
- **Cold-well pumpability.** Unresolved: a strict xfail plus a data ask (one
  cold-well dyno card) — see TIER1 §11.2, §11.9.
- **Fractional-flow (mobility-weighted) flowback**, not the current volume-weighted
  mixing cell — decides how much of the slow-rod benefit is real (TIER1 §11.9 item 4,
  §11.11 item 3).
- **VFD policy at the 0.6 alarm line** — not adopted; untested against the rev-12 cap
  (TIER1 §11.11 item 4).
- **Tubing temperature profile** — still missing; the rods see `T_avg`, not a cooler
  tubing temperature, which would worsen W/O drag (TIER1 §9.10 item 3, §10.12 item 3,
  §11.11 item 5).
- **Data asks, in priority order** (TIER1 §11.11 item 6, superseding the rev-9/10/11
  lists in §14): (1) a water-cut-vs-time log for one CSS cycle; (2) one late-cycle
  dyno card and one cold-well card; (3) OIL's current SPM/stroke/pull criteria (the
  gain now rides on these, not on the cutoff); (4) a static BHP survey; (5) a lab W/O
  viscosity at 30/45/60% water (fixes the emulsion φ* and its cap).

---

## 16. 27 Sep: technical re-score 58 → wave 5 (operating policy, fair baseline) → rev 13 cascade; deck rebuilt in the slide-3 aesthetic

§15 closed with a technical re-score of **58/100**. Its single top finding: the rev-12
headline (+₹9,574/d) was structural, not physical — it came from the **pull rule**
ending the baseline (b) on produce day 139 while it still made 1.87 m³/d. This section
is the response: **wave 5** on branch `wave5` (physics), landing as **rev 13**
(`params/CHANGELOG.md`), plus the deck rebuild that followed on `main`
(`git log --oneline`: `98ea3f6` slide 2 WHAT/WHY, `5bc8d33` slide 6 clickable
references, `6da5b6b` deck rev-13 numbers).

### 16.1 Findings → fixes

| # | Finding (re-score) | Fix (wave 5 / rev 13) |
|---|---|---|
| N1 (top) | The rev-12 gain was the pull rule ending the baseline early, not the recommendation's own set-points | `css.float_policy` ∈ `pull`/`vfd_hold`/`vfd_then_pull`/`none` — a parameter and an optimiser dimension, applied alike to the baseline, the recommendation and the cold counterfactual (TIER1 §12.1) |
| N4 | The 10× emulsion-viscosity cap swung the pull-policy gain ₹6.1k→₹19.0k | Still true under `pull`; **no longer true under VFD-hold** (₹3.28–3.33k over cap 5→∞) — one more reason the default stays `pull` for calibration but the *recommendation* is `vfd_hold` (TIER1 §12.7) |
| N7 | Penalising a float-risk classifier fights the physics rather than pricing a real cost, once float response is a control | Dropped the soft float-risk penalty; replaced with a **hard injectivity gate** (≥400 kPa sandface margin), a real physical constraint (TIER1 §12.9, `ml/README.md` "Objective") |
| (inversion cliff) | Sharp W/O↔O/W emulsion switch, 3,365× drag jump day-to-day | Smoothed to a 0.075 water-cut band, 1.22× max ratio (TIER1 §12.8) — cosmetic for the ₹ (< ₹0.1k/d, ₹30/d OAT swing), real for numerical honesty |
| (levies) | Royalty/cess never modelled — "is CSS profitable" unanswerable on OIL's own basis | Added a net-of-levies deck (~₹3,600/bbl); every feasible grid point is negative on it (TIER1 §12.10) |
| (diesel discount) | 0.30 bulk discount was the top of its own U[0,0.30] range, unsourced | Moved to 0.15 (the mid), **coordinator's instruction, not a physics fit**; knock-on: the gross-margin-optimum slug drops to ~750 t, below BGW-8's 1,040–1,560 t (new strict xfail, TIER1 §12.2) |

### 16.2 Canonical table (rev 13)

| | Baseline (b), VFD-hold | **Recommendation, VFD-hold (canonical)** |
|---|---|---|
| Set-points | 1,300 t / 10 d / 91 kgf/cm² / 86-in / 5 spm / cutoff 1.3 | **1,000 t / 10 d / 89 kgf/cm² / 64-in / start 4.5 spm / cutoff 0.60 backstop** |
| SOR | 3.29 | **2.83** |
| oil m³ · produce d (window) | 395 · 199 (227) | 353 · 196 (220) |
| net cash — FY25 / $65 / net-of-levies | +12,064 / −582 / −14,193 | **+15,396 / +3,738 / −8,811** |

**Gain vs. baseline (b), naming the baseline's own policy** (net cash ₹/cycle-day):
same policy (VFD-hold) **+3,332 / +4,319 / +5,382**; if baseline pulls **+12,917 /
+14,694 / +16,606** (68% policy switch); if baseline does nothing **+2,622 / +3,484 /
+4,413** (we do not price rod failures). Full derivation and sensitivity: TIER1 §12.6–§12.7.
Tests: **263 passed, 2 xfailed**.

### 16.3 Decisions taken on the lead's behalf (flag for confirmation)

- **`vfd_hold` is recommended, but the shipped params default stays `pull`.** Under
  VFD-hold two benchmark bands fail (reference SOR 3.4645, 0.0005 below the CalGEM
  floor; the 500-t slug at 2.65, below the 3–8 literature band) — re-specifying the
  bands to fit would be "calibration by re-specification," the exact re-score
  criticism this wave answers elsewhere. The default stays where the calibration
  anchor was made; the *recommendation* the deck and dashboard lead with is
  `vfd_hold` regardless (TIER1 §12.2).
- **The injectivity gate (≥400 kPa) is now a real feasibility constraint**, not a
  soft penalty — it rejects the old 85 kgf/cm² floor outright (53 kPa margin) and
  selects 89 kgf/cm² (498 kPa) as the new floor.
- **Diesel discount base moved to 0.15** (mid of U[0, 0.30]) on the coordinator's
  instruction — an economics input, not a physics fit; 0.30 and 0 kept as presets.
- **The deck was rebuilt on robust numbers only** — every figure on the rebuilt
  slides is the same-policy or explicitly-labelled-baseline-policy gain, never a bare
  single number (the discipline this whole wave exists to enforce). Slide 2 is
  **WHAT/WHY only** (no overlap with slide 3); slide 3 is **HOW** (the architecture
  diagram); slide 6's references now all carry a **clickable URL/DOI line**.
- **Deck commits this pass:** `98ea3f6` (slide 2 WHAT/WHY, 5 detail chips per card;
  slide 5 mini-card spacing), `5bc8d33` (slide 6 clickable references), `6da5b6b`
  (rev-13 numbers: fair same-policy gain, SOR 3.3→2.8, 263 tests, slow-then-stop
  rule, levies deck, honest strip).

### 16.4 Human TODOs (cannot be done from this session)

- Team formation (6 members, ≥1 female), Team Name/ID, and the SPOC deadline conflict
  — still unresolved, carried from §8/§12/§14/§15.
- K12 in `viva_prep.md` (ChemE-contribution question) — still a template.
- **Links on slides 2 and 6** — the WHAT/WHY slide and the references slide both
  need the team to drop in the actual repo/demo/reference URLs before submission;
  this session wrote the slide structure and the reference *text*, not live links
  where a URL depends on something only the team has (e.g. the repo's final visibility
  state).
- **Repository visibility** — still team-controlled; the README already carries the
  "ask the team lead for access" line.
- **AI-mention lines decision** — still an open team-lead call, carried from §15.5.
- **Confirm two unverified DOIs on slide 6**: Marx–Langenheim `10.2118/1266-G`, and
  the ASTM/Pal–Rhodes citation pair — both were entered from memory/secondary
  citation during the reference-rebuild pass (`5bc8d33`) and should be checked
  against the primary source before the deck is final.
- **CalGEM geo-block** — still needs a US VPN or collaborator, carried from §14.1/§15.5.

### 16.5 Open model items

- **Rod-string failure / workover cost is unpriced.** VFD-hold holds the floating
  index at the 0.6 alarm line for ~55–60 days a cycle (graded damage index Σ FI³
  ~5× the `pull` policy's) — we report the canonical gain vs. a do-nothing baseline
  as +₹2,622/d (FY25) because rod failure is unpriced. A real ₹/event or rod-life figure
  would let this be priced instead of merely disclosed.
- **Tubing temperature profile** — still missing, carried from §15.6: the rods see
  `T_avg`, not a cooler tubing temperature, which would worsen W/O drag.
- **Cold well unpumpable under every float policy** — the model's cold, unstimulated
  well is shut in (not the rev-12 "pumpable" reading) at base; every absolute
  incremental ₹ figure is therefore an upper bound against the `pumpable`
  counterfactual (~₹11.4k/d lower), which is closer to the field fact that these
  wells were produced cold (TIER1 §12.4).
- **Fractional-flow (mobility-weighted) flowback** — carried from §15.6; the sampled
  flowback mobility ratio M ∈ {1, 3, 10} moves the VFD-hold gain from +₹3.3k (M=1,
  base) to +₹6.6k (M=10) — the biggest mover in the sensitivity table (TIER1 §12.7).
- **Royalty/cess base is an assumption**, not a confirmed rate: 20% + 20% is
  cross-checked only against OIL's own FY25 exchequer table's implied ≤35% cap, and
  the ER-policy 50% cess waiver (if CSS output qualifies) is not netted in (TIER1
  §12.10).

---

### 16.6 Technical re-score #2: 64/100 — what still carries the gain

An independent second technical re-score (64/100, +6 on §16's 58) found the fair
same-policy gain still rests on two of our own assumptions, not new physics: the
VFD speed floor applied to the stimulated well (2 spm) versus the floor the model
credits the "pumpable" cold well (0.53 spm), and the baseline's 1.3 m³/d rate
cutoff (ours, not OIL's). Apply one floor to both wells and the same 0.6 backstop
to both, and the same-policy gain goes to **≈ ₹0/cycle-day** (P(rec > baseline)
falls to 0.66, p50 ₹439); with only the matched backstop it is 0.84 (p50 ₹2.5k).
Three claims are downgraded as a result: "P(rec > baseline) 0.965/0.992/0.999" now
carries the cutoff caveat above; "burns less steam and makes more oil" is corrected
to "burns 23% less steam for 11% less oil (353 vs 395 m³)"; and "published-practice
baseline" is relabelled "our assumed baseline" (86 in / 5 spm / cutoff 1.3 are our
choices, not OIL's practice). The recommendation is also **more float-exposed** in
the UQ than the baseline (median alarm days 6 vs 0), where "0 days at FI 1.0" holds
only in-model. The one datum that would settle the gain — **OIL's actual VFD
minimum speed and their real pull/produce cutoff** — is not yet in hand; both are
now items 16–17 in `docs/research/OIL_DATA_REQUEST.md`. Full detail:
`rescore_tech2/RESCORE2.md` (not checked into this repo).
  cross-checked only against OIL's own FY25 exchequer table's implied ≤35% cap, and
  the ER-policy 50% cess waiver (if CSS output qualifies) is not netted in (TIER1
  §12.10).

---

### 16.7 Judge re-score #2: 66/100 — screen vs slides

A second, independent judge-panel re-score (66/100, +5 on §16's 61) found the deck and
docs materially improved but the **dashboard screen and demo path still tell a rosier
story than the repo's own tables**: the Overview/Optimiser still label the physics-grid
recommendation "ML optimum"/"ML-optimised"; the 12-spm stress test's `bakedFor()` match
doesn't key on SPM, so it silently replays the 5-spm bake and leaks a mislabelled "12 spm"
run into the Overview; the console's "Rod-float response" selector changes only
explanation text, not the physics; and one honesty-strip number (−₹3,865 for the
recommendation vs. a do-nothing baseline) was a different, non-canonical plan, not our
own — the canonical plan actually gains **+₹2,622 / +3,484 / +4,413** (FY25/$65/net-of-levies) there. **The dashboard agent is
fixing** the `bakedFor()` SPM match, the "ML" labelling, the VIOLATED/THRESHOLD badges'
policy-awareness, and hiding the cosmetic selector. **This pass already fixed** in
`docs/study/` and `docs/guides/DEMO_SCRIPT.md`: the safe-to-say block cut to ≤120 words
(result-first: the operating rule, SOR −14%, 84–96% win-rate, ₹0–5k/day gated on OIL's
VFD floor and cutoff); K8/K10-vs-K29/K17/K36/K37 contradictions; the new K42/K43
(why less oil, is the pump actually safer); the "petroleum engineer + data scientist /
two independent external reviews" line reworded to "two rounds of independent
adversarial review (AI-assisted, persona-based) — not a named human expert"; and the
demo script's "ignore the screen" hedges removed. **Human gate before submission:**
team fields (name/ID on slide 1, the five "Your Team Name" ovals), the deck's link
band and repo URL, repository visibility (public vs. request-access), and the AI-use
disclosure line — none of these can be decided from this session.

### 16.8 · 27 Sep late — closing state after both second-round reviews

- **Scores:** technical 52 → 58 → **64**; judge 61 → **66**. Internal cut: **yes** once the human
  fields are filled (team ID/name, five "Your Team Name" ovals, link boxes on slides 2 & 6).
- **Landed after the reviews:** dashboard 13.1 (`cbb4186`: 12-SPM stress test runs the
  approximate model and is never published to the Overview; console rod-float selector now
  drives the approximate model; VFD-hold constraints "held at limit (by design)"; physics-grid
  labels; baseline-policy toggle wording, "does nothing" = **+₹2,622**; card/tile/table agree;
  footer rev/date from constants); deck truth pass (`c40ff1b`, `773257f`: plan on slide 5,
  no "more oil" / "safer pump" / "first twin" / "real field data", "Assumptions to confirm
  with Oil India" strip, rods *float* not jam, 3-minute search, "twin re-fits"); docs
  (`40950d3`, `51c9904`, `ba2feb0`: 114-word safe-to-say, K41–K43 / N30–N32, review claim
  reworded as AI-assisted adversarial review, −₹3,865 retired everywhere).
- **The honest pitch now:** the robust results are the operating rule (slow at the float
  limit, then pull) and steam per m³ 3.29 → 2.83; the ₹ gain is ₹0–5k per cycle-day and is
  set by two numbers only OIL has — the VFD minimum speed and the real pull criterion.
- **Human gate (nothing else blocks):** team registration; fill slide 1 + ovals + links;
  repo visibility (private today; slide 5 says "open source"); AI-use disclosure line; confirm
  the two unverified DOIs on slide 6; record the 2-minute demo video; K12 in the ChemE
  lead's words.
