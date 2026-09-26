# Fixes Applied — Content & Docs Review (2026-09-13)

Scope of this pass: `ppt/notes/deck_content.md`, `docs/study/viva_prep.md`, `ppt/build_deck.py`
(+ rebuilt `SIH26120_Idea_Presentation.pptx`), `README.md`, `docs/guides/DEMO_SCRIPT.md`,
`docs/guides/GLOSSARY.md`, `docs/architecture.svg` (font-size only, per docs_review Finding 5).
`dashboard/`, `params/`, `twin/`, `ml/`, `data/`, `api/`, `docs/guides/ui_brief.md`, and
`docs/reviews/integration_report.md` were left untouched, per instructions — the
integration agent's merge of `docs/research/field_params_recommended.json` into
`params/field_params.json` was found to be **already complete** on disk (depth
1150 m, API 15.5, mu_ref 11500 cP, T_injection 290°C, injection_rate 74 tpd,
porosity 0.09, Andrade constants fitted) when this pass started, so all content
fixes below use those real numbers directly rather than assuming placeholders.

## content_review.md — findings

| # | Severity | Finding | Status | Notes |
|---|---|---|---|---|
| 1 | KILLER | Slide 1 "250 km" MNIT-Baghewala distance wrong | **Applied** | Replaced with "~550–600 km" (ppt_ammo.md #13), reframed as a remoteness argument for real-time monitoring |
| 2 | KILLER | Unsourced "4.5 t/m³ current SOR" stated as fact (Slides 2 & 5) | **Applied** | Dropped the invented figure everywhere; now benchmarks against the literature range 3–8 (avg ~6, efficient <3), explicitly noting Baghewala's own SOR is not publicly reported. Chart (`make_chart.py`) relabeled "industry-typical baseline (~6)" vs "optimizer target" |
| 3 | KILLER | Slide 4 falsely claimed field_params.json "populated from Oil India data" while file had placeholder 500 m / 100 tpd | **Applied** | `params/field_params.json` was already merged with real data by the integration agent by the time this pass ran; Slide 4 bullet rewritten to state the real calibrated values (depth ~1,150 m, viscosity 8,000–15,000 cP, steam 280–305°C @ 60–70% quality) which are now actually true |
| 4 | KILLER | Slide 1 "2000 cP baseline" off by 5–6x from confirmed 8,000–15,000 cP | **Applied** | Slide 1 bullet corrected to "8,000–15,000 cP @ 50°C (~90–100x more viscous than a typical 18° API crude)" |
| 5 | MAJOR | "40+ CSS wells across Rajasthan" unsourced/conflated | **Applied** | Replaced everywhere (deck Slide 4 & 5, viva cheat table row 15) with "52 wells drilled (33 operational); 19 CSS'd in FY2025-26 (~72% YoY growth)" |
| 6 | MAJOR | Viva cheat table hedged confirmed 280–305°C steam temp as "~250°C (verify)" | **Applied** | Cheat table row 10 now states 280–305°C as CONFIRMED (BGW-8, OIL internal data), verify tag removed |
| 7 | MAJOR / diplomatic | PS (17–19° API, 46–48°C) vs literature (14–17°, ~50°C) conflict | **Applied** | Slides use PS numbers with a literature footnote (per review's exact diplomatic phrasing pattern); viva Q8 and cheat table rows 1–2 present both explicitly and explain which is used where |
| 8 | MINOR | Live params porosity 0.28 vs confirmed <10% (0.09) | **Applied** (already fixed on disk) | `field_params.json` already has porosity 0.09; surfaced "<10% porosity, poor-to-fair reservoir" on deck Slide 4 as an added feasibility justification, per the review's suggestion |
| 9 | MINOR | andrade_A/B null, wrong viscosity anchor — engineering bug | **Not applicable / already fixed** | `field_params.json` already has `andrade_A=1.164e-6`, `andrade_B_K=7436.6`, `mu_ref_cP=11500`; this is params/twin territory owned by the integration agent, out of this pass's edit scope, and already resolved on disk |
| 10 | MAJOR | "$500k/yr" and "80% failure reduction" stated as fact, then hedged, then flat fact again in elevator pitch (self-contradictory) | **Applied** | Slide 5 and elevator pitch reframed to the sourced $15k–$50k per-workover figure (ppt_ammo.md #12), framed explicitly as illustrative; safety bullet reframed around the mechanism (metal-on-metal rod wear) instead of an invented 80% number |
| 11 | MAJOR | "physics-validated" loaded phrase, contradicts viva Trap 9's own honesty stance | **Applied** | Changed to "physics-simulated (internal consistency-checked; field validation is the next phase)" on Slide 5, elevator pitch, and `build_deck.py` |
| 12 | MINOR | Slide 1 "real-time prediction... at Baghewala field" overclaims as accomplished | **Applied** | Changed to "Digital twin designed for real-time prediction... targeting Baghewala field" |
| 13 | MINOR | Pennwell reference cites "verify source and access" on the references slide | **Applied** | Removed; replaced with SPE-23APOG-535203 and Oil India internal data + `docs/research/landscape.md` citation (both real, checkable) |

## content_review.md — viva_prep.md rewrites (5 weakest answers)

| Q | Was | Status |
|---|---|---|
| Q1 (Andrade intuition) | Score 3 | **Applied verbatim** from review's rewrite — now cites the fitted Andrade constants and the 90–100x viscosity comparison |
| Q6 (CSS depth limits) | Score 1 — actively dangerous, cited wrong ~500 m depth | **Applied verbatim** — now uses confirmed ~1,100–1,150 m and frames it honestly as sitting at the edge of the efficiency window, citing vacuum-insulated tubing and the EDH trial |
| Q9 (steam quality) | Score 3 | **Applied verbatim** — now cites Baghewala's own confirmed 60–70% wellhead quality |
| Q20 (workover cost) | Score 2 | **Applied verbatim** — now uses the sourced $15,000–$50,000/event figure |
| Q21 (steam generation cost) | Score 2 | **Applied verbatim** — now derives and states the real ~71 kg diesel/tonne, ~3.0 GJ/tonne Baghewala-specific figure |

Additional viva_prep.md updates beyond the mandatory 5 (in scope per the task's
instruction to apply the API/temperature diplomatic framing "in viva answers" and
to work unused GOLD facts in): Q7 now cites the literature SOR range 3–8; Q8
rewritten with the full PS-vs-literature diplomatic framing (Finding 7); Q19 and
Trap 9 updated so the economics numbers referenced match the deck's new $15k–$50k
framing instead of the retired $500k/yr figure. Cheat table expanded from 15 to 18
rows and every corrected number cross-referenced to which finding fixed it.

## content_review.md — Section 4 (unused GOLD material)

| Fact | Status | Where added |
|---|---|---|
| India's first CSS — BGW-8, Dec 2018, Belgrave Oil & Gas Corp. | **Applied** | Slide 1 bullet, Slide 4 feasibility bullet, elevator pitch, viva cheat table row 16 |
| 5–6x first-cycle production uplift | **Applied** | Slide 2 differentiation bullet, Slide 4 feasibility bullet, viva Q8, cheat table row 17 |
| 218 t (FY17) → 43,773 t (FY26), ~200x growth | **Applied** | Slide 5 "Growth context" bullet, viva cheat table row 18 |
| 52 wells drilled / 33 operational, 19 CSS'd FY25-26 | **Applied** | Slide 4 and Slide 5 scalability bullets (replacing "40+ CSS wells"), viva cheat table row 15 |
| Competitive gap — no commercial product integrates CSS+SRP co-optimization (landscape.md) | **Applied** | Integrated onto Slide 2 as a named-competitor differentiation bullet (XSPOC, Lufkin, Weatherford, Schlumberger, AVEVA, Kongsberg) rather than a 7th slide, since the official template caps at 6 slides; also added to Slide 6 references and the elevator pitch |

## docs_review.md — findings

| # | Severity | Finding | Status | Notes |
|---|---|---|---|---|
| 1 | MAJOR | README Windows `start` cmd.exe command in a bash block | **Applied** | Replaced with cross-platform `python -m webbrowser dashboard/index.html` |
| 2 | MAJOR | DEMO_SCRIPT step order implies opening dashboard before confirming API health | **Applied** | Setup checklist reworded to confirm API health first, explicitly, with a curl test |
| 3 | MAJOR | DEMO_SCRIPT timing: 1:35–2:10 segment overshoots (~70 words/47s in a 35s slot); 2:10–2:45 undershoots | **Applied** | Trimmed the 1:35–2:10 script to ~52 words (fits ~35s at 1.5 wps); extended the Optimize segment to 2:10–2:50 using the review's own suggested expanded wording, shifted the closing beat to 2:50–3:00 |
| 4 | MINOR | Fallback instruction doesn't name the exact mock-mode variable/line | **Applied** | Opened `dashboard/index.html` read-only, confirmed the real names: `const MOCK = true;` (line 648) and `const API_BASE = "http://localhost:8000";` (line 649). Fallback section now names them exactly, and notes MOCK is already `true` by default |
| 5 | MINOR | architecture.svg 13px font marginal for projection | **Applied** | Bumped the four `font-size="13"` detail lines to `font-size="14"` |
| 6 | MINOR | Setup checklist doesn't mention where to find the mock-mode toggle | **Applied** | Added a pre-flight checklist item naming the exact line/variable, folded into the same fix as Finding 4 |
| 7 | MINOR (no issue) | GLOSSARY.md — clean | **No change needed**; added one clarifying phrase to the API-gravity entry for PS-vs-literature consistency with content_review Finding 7 (not a docs_review finding, but keeps the doc set internally consistent) |
| 8 | MINOR | README doesn't state the field/API/dashboard dependency order explicitly | **Applied** | Added an explicit "Dependency order (critical)" note in the Quickstart, combined with the Finding 1 fix |

## Additional consistency fixes (not a numbered finding, done to avoid reintroducing the same class of bug)

- `docs/guides/DEMO_SCRIPT.md` opening line used stale "18° API" and the invented "4.5 SOR" figures; corrected to the literature viscosity framing and the 3–8 industry SOR range, consistent with content_review Findings 2 and 4.
- `README.md` field-description table row and license note updated to reflect that `params/field_params.json` is now calibrated to real sourced data, not "illustrative placeholders."
- `ppt/build_deck.py`: while verifying no text-frame overflow, found the **original, pre-existing** template mapping for the Feasibility and References slides already ran past the footer boundary at the template's default font size (measured independently of this review's content changes, using actual Arial glyph metrics against each box's width and the footer's vertical position). Fixed by shrinking those two boxes to 24pt and 22pt respectively (matching the readability floor already used elsewhere in the deck) and trimming bullet wording slightly. Also added a 26pt shrink on the Slide 2/Proposed-Solution box, which was fitting with only ~0.02in of margin under the old estimate — now has ~0.8in of margin.

## Skipped

Nothing marked KILLER was skipped. Nothing marked MAJOR was skipped. The only
"not applicable" item is Finding 9 (viscosity anchor / andrade constants), which
is a `params/field_params.json` + `twin/` engineering fix outside this pass's
edit scope (owned by the integration agent) — and it was already resolved on
disk before this pass started, so no action was needed from here.

Not touched, per explicit scope boundary: `dashboard/index.html` (read-only
lookup only, per instructions), `params/`, `twin/`, `ml/`, `data/`, `api/`,
`docs/guides/ui_brief.md`, `docs/reviews/integration_report.md`.

## PPTX rebuild verification

- Rebuilt with `.venv\Scripts\python.exe ppt\build_deck.py` (chart PNG regenerated
  with the system Python 3.13 + matplotlib install, since the project venv does
  not have matplotlib — `build_deck.py` itself only needs `python-pptx`, which the
  venv has).
- Re-opened the output with python-pptx: **6 slides**, correct titles per slide,
  **709 KB** file size.
- Checked every content text box's rendered font size and wrapped line count
  (using real Arial glyph metrics, not a character-count guess) against its
  actual vertical space to the footer boundary on all 5 content slides — all fit
  with positive margin (0.15in–0.8in), including the two pre-existing overflow
  bugs found and fixed in this pass (see above).
