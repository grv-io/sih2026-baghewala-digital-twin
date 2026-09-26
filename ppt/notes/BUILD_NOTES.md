# PPT Build Notes — SIH26120 Idea Presentation

> **SUBMIT THIS ONE:** `SIH26120_Idea_Presentation_STRICT.pptx` /
> `SIH26120_Idea_Presentation_STRICT.pdf`. **Slide 3 is now the FINAL icon version**
> (`build_tech_slide_final.py`, 26 Sep). The detailed native diagram is kept in
> `archive/…_pre-final-slide3.pptx`. See "Slide 3, FINAL" below.
> The earlier `SIH26120_Idea_Presentation.pptx` and the `..._VISUAL*.pptx` decks are
> superseded — the VISUAL deck restyled the template (custom dark/amber theme, own
> title bars, own layout grid) and SIH internal screeners eliminate decks that deviate
> from the mandated format. See the "STRICT rebuild" section at the bottom.

## Template source
- **Official SIH 2026 Idea Presentation Format**, downloaded directly from:
  `https://www.sih.gov.in/letters/2026/SIH2026-IDEA-Presentation-Format.pptx`
  (found via web search for `site:sih.gov.in SIH2026 IDEA Presentation Format`; the
  same URL pattern as the SIH2025 template that's also hosted at sih.gov.in/letters).
- Saved locally as `ppt/template/template_official.pptx` (902 KB, verified as a valid
  PowerPoint 2007+ .pptx, HTTP 200 direct download — no GitHub mirror was needed).
- The official file has 7 slides: Title Page, Idea Title/Proposed Solution, Technical
  Approach, Feasibility and Viability, Impact and Benefits, Research and References,
  and a final "IMPORTANT INSTRUCTIONS" slide. That instructions slide explicitly says
  *"You can delete this slide (Important Pointers) when you upload the details of your
  idea on SIH portal"* — `build_deck.py` deletes it automatically, leaving exactly 6
  slides (title + 5 content), matching the template's own "max 6 slides" rule.

## How the deck was built
- `ppt/build_deck.py` opens `template_official.pptx` (NOT built from scratch) and fills
  the existing placeholders/text boxes with content from `ppt/notes/deck_content.md`, trimmed
  to fit (the official template's boxes are sized for short bullets, not full sentences).
- Original template formatting (fonts, sizes, bold/underline, bullet styling, the
  official red/white theme, logos) is preserved — text is injected into the template's
  own XML runs rather than rebuilt, so it stays visually consistent with the official
  format.
- On the Technical Approach and Impact & Benefits slides, the bullet text box was
  narrowed to the left ~7 in of the slide and the font dropped from 28pt to 22pt (still
  well above the 18pt readability floor) so a right-hand visual column has guaranteed
  clear space — verified programmatically (see "Layout verification" below), not by eye.
- Run it with the Python 3.13 interpreter that has `python-pptx`/`matplotlib` installed:
  ```
  "C:\Users\Gaurav Agrawal\AppData\Local\Programs\Python\Python313\python.exe" ppt\build_deck.py
  ```
- `ppt/make_chart.py` regenerates `ppt/assets/sor_chart.png` (the Impact slide's
  baseline-vs-optimized SOR bar chart) if it needs to be re-rendered.

## Visuals added
- **Technical Approach slide**: `docs/architecture.svg` did not exist yet at build time
  (another agent was producing it), so a simple 4-layer flow diagram (Physics Engine →
  Synthetic Data → ML Models → Bayesian Optimizer, with a feedback-loop caption) was
  drawn directly with native PowerPoint shapes instead. **If `docs/architecture.svg`
  exists by the time you read this, swap it in**: convert it to PNG (`cairosvg` is not
  installed in this environment — pip install it, or use a headless-Edge screenshot) and
  replace the `add_architecture_diagram()` shapes in `build_deck.py` with a
  `slide.shapes.add_picture(...)` call in the same right-column position
  (left ≈ 8.3in, top ≈ 2.77in, width ≈ 4.3in on slide index 2).
- **Impact & Benefits slide**: bar chart comparing baseline SOR (4.5 t/m³) to the
  optimized target (3.2 t/m³), explicitly labelled *"Illustrative target — physics-model
  projection, not measured field data"* on the chart itself, per instructions — these are
  NOT real experimental results yet.

## Layout verification performed
- Re-opened the built .pptx with python-pptx: confirmed 6 slides, correct titles per
  slide, file size ~694 KB (comfortably > 30 KB and under SIH's 25 MB upload limit).
  No LibreOffice/PowerPoint was available in this environment to render a visual
  screenshot, so verification was done by checking every shape's (left, top, width,
  height) in inches against the 13.33in × 7.5in slide canvas and against each other —
  confirmed no shape exceeds the slide bounds and the bullet text columns don't
  horizontally overlap the diagram/chart columns. Text-wrapping line counts were
  estimated (chars-per-line heuristic for Arial at the given point sizes) to confirm
  bullets stay above the footer — **do a final visual proof in PowerPoint/Google Slides
  before submission**, since this could not be rendered here.

## PLACEHOLDERS — must be updated by the team before submission
- **Team Name**: set to literal `TEAM ________` on the title slide and on every content
  slide's team-name oval. Replace with your actual registered team name everywhere.
- **Team ID**: title slide currently says `TBD (fill after SIH portal team registration)`.
- Title slide's "PS Category" is set to `Software` and "Theme" to `Smart Automation`,
  per the task brief — double check these still match your final PS registration.

## What to update once ML / field results are real
- The Impact slide's SOR bar chart (4.5 → 3.2 t/m³) and every "target"/"illustrative"
  number in the bullets (20–30% SOR reduction, ~$500k/yr, ~80% failure reduction, ~30%
  energy cut) come from `deck_content.md` and are physics-model projections, explicitly
  marked "verify source" there. Once the XGBoost model + Bayesian optimizer have run on
  real synthetic/field data, replace these with actual measured/validated numbers and
  regenerate the chart via `ppt/make_chart.py`.
- If `docs/architecture.svg` becomes available, swap it in per the note above for a more
  accurate/branded architecture diagram than the placeholder shapes.

## Files in this folder
- `template_official.pptx` — the untouched official SIH 2026 template (kept for reference).
- `build_strict_deck.py` — **current** build script for the submission deck.
- `WINNING_DECK_ANALYSIS.md` — slide-by-slide teardown of a *selected* SIH 2025 deck.
- `SIH26120_Idea_Presentation_STRICT.pptx` / `.pdf` — **the deck to submit**.
- `_strict_build/` — generated PNGs (SVG→PNG at 2x) + their wrapper HTML. Regenerated
  by the build script; safe to delete.
- `diagram/` — source + renderer for the Technical Approach architecture picture
  (`tech_architecture.html`, `render.py`, the 3960x1560 PNG and its QC downscales,
  `slide3_rendered.png` = the COM-exported slide for visual proof).
- `build_tech_slide_native.py` — **current** slide-3 builder: native-shape diagram
  (copyable text), layout/text-fit gates, COM export of PDF + `diagram/slide3_native.png`,
  pypdf label check. Run it after `build_strict_deck.py`.
- `patch_tech_slide.py` — *superseded for slide 3*: it swapped the PNG diagram into an
  already-built deck. It is kept because `build_tech_slide_native.py` imports its
  `FURNITURE` set.
- `build_deck.py`, `make_chart.py`, `assets/sor_chart.png`,
  `SIH26120_Idea_Presentation.pptx`, `SIH26120_Idea_Presentation_VISUAL*.pptx`,
  `visual/` — superseded earlier attempts, kept only for reference.

---

# STRICT rebuild (current deck)

## Why it was rebuilt
The VISUAL deck was rejected: it looked good but it was *not* the official template —
it replaced the SIH master, colours, title bars and layout grid. SIH internal screeners
are known to drop decks that deviate from the mandated format. The rebuild goes the
other way: open the official file, change nothing structural, fill it in.

## Model: a deck that actually got selected
`WINNING_DECK_ANALYSIS.md` is a full teardown of the friend's *selected* SIH 2025 idea
deck (PS 25049, `~/Downloads/SIH2025-IDEA-Presentation-Format.pptx.pdf`), extracted
page by page with `pypdf` (text, text positions, font sizes, every embedded image).
The five rules taken from it:

1. Exactly 6 slides; template untouched (master, banner, footer bar, team-name oval,
   slide numbers, 48pt title casing all left alone); only the instructions slide deleted.
2. The template's instruction pointers are **kept verbatim and reused as the section
   headings**, with content underneath — never deleted, never reworded.
3. **Technical Approach is a picture, not a list** — a real architecture flowchart
   filling the content area, plus a smaller tech-stack diagram beside it. Near-zero text.
4. Bullets are 3-9 words. Three-column layouts wherever the content has parallel parts.
5. Impact = short benefit blocks + **one real chart**; empty space beats padding.

## How the STRICT deck is built
```
.venv\Scripts\python.exe ppt\build_strict_deck.py
```
- Opens `template_official.pptx`, fills the existing title placeholders and body text
  boxes in place, and deep-copies the template's *own* `TextBox 8` whenever a second or
  third column is needed — so every added box inherits the template's body formatting
  (Arial, template bullet glyph, theme colours) rather than a new style.
- Headings use the theme's dk2 navy `#1F497D`, bold + underlined, exactly as the
  template's own pointer text is styled.
- Runs carry an explicit `<a:sym typeface="Arial"/>` so `°`, `μ`, `→`, `³` render
  instead of being font-substituted (this was a real bug — `50°C` first exported as
  `50˚  C`).
- Deletes slide 7 ("IMPORTANT INSTRUCTIONS") as the template instructs → 6 slides.

## Diagrams
SVG → PNG at 2x through headless Edge (no cairosvg in this env):
```
msedge.exe --headless --disable-gpu --force-device-scale-factor=2 --hide-scrollbars
           --screenshot=<out>.png --window-size=<w>,<h> file:///<wrapper.html>
```
then whitespace-trimmed with PIL. Sources (from `ppt/assets/svg/diagrams/`, light variants):
- `sor_waterfall_light.svg` → cropped 2376x1151 — Impact, SOR waterfall.

### Slide 3 is NATIVE SHAPES now — `ppt/build_tech_slide_native.py` (26 Sep)
**Requirement (team lead): all text on the Technical Approach slide must be
selectable / copyable in the exported PDF.** A PNG cannot satisfy that, so slide 3's
diagram is no longer a picture. It is built entirely from python-pptx shapes:
rounded rectangles with real text frames, orthogonal wires with arrowheads (straight
connectors, or open freeform polylines when a wire bends), and junction dots. **Do
not put a picture back on slide 3.** `patch_tech_slide.py` is superseded for this
slide. If you run it anyway, its overlap check fails against the native shapes.

```
.venv\Scripts\python.exe ppt\build_strict_deck.py           # template fill (slide 3 still gets the old PNG)
.venv\Scripts\python.exe ppt\build_tech_slide_native.py     # slide 3 -> native diagram, gates, PDF + PNG, pypdf check
.venv\Scripts\python.exe ppt\build_tech_slide_native.py --no-export   # gates + save only
```
- **What it touches:** only slide 3's diagram. It deletes the `TechArchitecture`
  picture, drops that picture's orphaned image relationship (the .pptx shrank from
  1,160 KB to 736 KB), deletes its own `TA_*` shapes from any previous run
  (so the script can be re-run), then draws the new diagram. The title placeholder,
  banner, team-name oval, footer bar, footer text, slide number and the two
  instruction pointers (`TextBox 8`) are byte-identical to before. So are slides 1, 2,
  4, 5 and 6 (checked: `ppt/slides/slide3.xml` is the only changed part). On the first
  run it backs the deck up to
  `ppt/archive/SIH26120_Idea_Presentation_STRICT_pre-native-slide3.pptx`, and never
  overwrites that backup.
- **Content:** 5 colour-coded layer panels plus a validation ring. There are 40 nodes
  (inputs 4 · physics twin 7 · data & ML 9 · service 9 · dashboard 4 · operator/well 2
  · validation 5) and 40 wires, plus 4 legend samples and 7 junction dots. Colours:
  navy = inputs, orange = physics, green = ML, purple = service/dashboard, grey =
  wires and validation. The key wires are the thick orange `viscosity.py → ipr.py` and
  `viscosity.py → srp.py` pair ("one μ(T), two failures"). Other wiring shown: a params
  bus into every twin module; `cycle.py → generate_data.py / uq.py`; `train →
  optimize ↔ recommend_physics`; every ML module → its real `/api/*` endpoint → the
  dashboard page that calls it (endpoint→page mapping taken from
  `dashboard/src/*.js`); observed CSV → `calibrate.py` → params as a dashed feedback
  loop; and Recommendation → Operator → BGW well, advisory only ("no controller is
  contacted"). Fonts: Arial (Consolas for endpoint chips), 7 pt sub-labels, 7.5–8.5 pt
  node titles, 9.5 pt panel headers.
- **Gates** (the build exits non-zero and saves nothing if any gate fails):
  canvas band (below the pointers at 2.08 in, above the footer bar at 6.95 in); no
  overlap with the same `FURNITURE` set that `patch_tech_slide.py` uses (imported from
  it); no node overlaps; every node inside its panel; every wire orthogonal and never
  passing through a node, label or panel header that is not its own endpoint; and
  **text fit**. The text-fit gate word-wraps each paragraph with real Arial/Consolas
  advance widths (PIL). It includes PowerPoint's roundRect text inset
  (0.29289 × corner radius per side; without it the gate passed a line PowerPoint
  wrapped), wraps at 97.5 % of the width, and uses a 1.2× line height. It enforces a
  7 pt minimum. Calibration: PowerPoint kept a line at 98.5 % of the inner width and
  wrapped one at 100.7 %.
- **Export + copyable-text check:** PowerPoint COM through PowerShell (no pywin32 in the
  venv). It runs `SaveAs(..., 32)` → `final/…_STRICT.pdf` (6 pages) and
  `Slides(3).Export(..., 1920, 1080)` → `diagram/slide3_native.png`. Then `pypdf`
  extracts page 3 and requires at least 25 node titles as text. Current result:
  **40/40**.
- Gotcha found on the way: a panel with no text produced an `a:txBody` with zero
  `a:p`. python-pptx saved it, but PowerPoint refused to open the file ("could not
  open the file"). Every text body now gets at least one paragraph.

### Slide 3, SIMPLE variant — `ppt/build_tech_slide_simple.py` (26 Sep, preview only)
The team lead asked for a second version of slide 3 that someone with no technical
background can follow at a glance. The detailed native slide above **stays in the
submission deck**. The simple one is a separate one-slide preview:
```
.venv\Scripts\python.exe ppt\build_tech_slide_simple.py              # preview .pptx + .pdf + PNG
.venv\Scripts\python.exe ppt\build_tech_slide_simple.py --no-export  # gates + .pptx only
```
→ `final/SIH26120_Slide3_SIMPLE_preview.pptx` / `.pdf` (1 page) and
`diagram/slide3_simple.png` (1920×1080). Because it is its own one-slide deck, the
template's slide-number field shows "1" there.

- **How it is built:** it opens the STRICT deck, drops every slide except slide 3,
  removes the detailed diagram's `TA_*` shapes and draws its own `TS_*` shapes. The
  template furniture (title placeholder, SIH banner, team oval, footer bar and text,
  slide number, and the two pointer lines in `TextBox 8`) is left as it is. It imports
  the gates, text-fit maths and drawing helpers from `build_tech_slide_native.py`, so
  the two slides share one box style: rounded panels with coloured header bands, the
  navy / orange / green / purple palette, Arial and triangle arrowheads.
- **Content:** five stations from left to right, each with a large icon (0.94 in on a
  white disc), a 15 pt title and one 12 pt sentence: 1 The well, 2 Digital twin,
  3 Smart search, 4 Dashboard, 5 Operator. Fat grey arrows join them. A dashed return
  arrow runs from the operator back to the twin, labelled "Real cycle records come back
  → the twin learns". Below that, "What the operator gets" (steam & pressure, pump speed
  & stroke, when to stop before the rods jam) → "What it leads to" (less diesel per
  barrel, safer pump, more oil per cycle). A small trust line sits in the corner.
- **Icons:** pictures rasterised from `assets/svg/icons/`. Headless Edge renders them
  black on white, then the grey level becomes the alpha channel and the icon is
  recoloured to its station colour. Library icons used as they are: `ic_pumpjack`,
  `ic_dashboard`, `ic_calendar-cycle`, `ic_steam`, `ic_alert-triangle`, `ic_flame`,
  `ic_shield-check` and `ic_oil-drop`. Three are composed from library parts. The
  operator is `ic_team`'s centre figure with a hard hat. The twin is `ic_dashboard`'s
  screen with `ic_pumpjack` inside it. Smart search is a magnifier with `ic_neural-net`
  in the lens. Every word on the slide is native text.
- **Gates:** it runs all five of the native builder's gates (canvas band, furniture,
  overlap, wiring, text fit). It adds these on top: every text ≥ 11 pt; station titles
  14–16 pt; station icons ≥ 0.9 in; body text (5 sentences + the loop caption) ≤ 60
  words, currently **57**; each sentence ≤ 12 words; no acronyms or code names (no
  all-caps token, `_`, `/` or `.py`). There is also an orphan check. The sentences are
  set by hand as balanced lines, one paragraph each. Every line must stay one rendered
  line, and no line may be a lone word unless it is a whole sentence ("Decides.").
  Icons and discs may not overlap text, furniture or each other, and no wire may cross
  a panel it does not start or end at. After the COM export, pypdf must find all
  **20/20** titles, sentences and chip labels as text.
- **Swapping it into the submission deck:** `--into-strict` redraws slide 3 of
  `final/SIH26120_Idea_Presentation_STRICT.pptx` with the simple version. It backs the
  deck up to `archive/…_STRICT_pre-simple-slide3.pptx` first and re-exports the 6-page
  PDF. **This has not been run on the real deck.** It was tested on a scratch copy
  (6 pages, 20/20 text). To go back, restore the backup:
  `build_tech_slide_native.py` refuses to run on a slide 3 that carries `TS_*` shapes.
- The template's own "Technologies to be used" pointer still names the stack (XGBoost,
  FastAPI …) on this slide too. It is mandated template text, so it was left alone.
  The no-acronym rule covers the diagram only.
- **Iterations** (read from the PNG each time): (1) first render. The balance and colours
  worked, but the gate caught five orphan words ("out.", "pump.", "Hindi."…). Sentences
  were then set as hand-balanced lines, and the "gets" panel was widened. (2) The network
  in the smart-search lens was too heavy to read at a distance, so its stroke was thinned
  and the network enlarged to fill the lens. (3) "When to stop before the rods jam" ran
  to three lines. The gets/leads split was rebalanced (7.24 in / 5.15 in, tighter chip
  insets) so every chip is two lines, and the strip got 0.08 in shorter.

### Slide 3, FINAL — `ppt/build_tech_slide_final.py` (26 Sep) — IN THE DECK
The team lead chose MEDIUM as the base. This script imports the medium builder and
changes only the chip texts, the loop caption and the output names (shapes `TF_*`).
Everything else is the same as MEDIUM: layout, icons, sentences, strips, trust line and
gates.
```
.venv\Scripts\python.exe ppt\build_tech_slide_final.py                 # 1-slide preview + PDF + PNG
.venv\Scripts\python.exe ppt\build_tech_slide_final.py --into-strict   # redraw slide 3 of the STRICT deck (done 26 Sep)
```
- **Edits vs MEDIUM:**
  - honesty: "Checked vs 9,692 real cycles" → "Checked vs field data (CalGEM)";
  - thesis: "Thick oil vs heat (Walther)" → "Thick oil: less flow + stuck rods";
  - "Rod loads + rod-float index" → "Pump loads, rod-float risk";
  - search → "Physics grid: 53,000 runs" · "Fast what-if model (XGBoost)" ·
    "Best / worst case (1,500 runs)";
  - operator → "5 settings + when to stop";
  - caption → "Real cycle records come back → the twin re-learns".
- **Two chips trimmed to stay one line at 9.5 pt:**
  - "Checked vs **real** field data (CalGEM)" is 154 pt of text. The chip has room for
    136 pt, and even 9 pt needs 146 pt. "real" was dropped; the CalGEM source name and
    the trust line ("checked against real field data") carry it.
  - "Physics grid: **5 controls,** 53,000 runs" is 153 pt, so "5 controls" was dropped.
    The five controls are the operator's "5 settings + when to stop".
  - Widening the cards enough for either chip would have cut the arrow gaps to about
    0.3 in and pushed every chip down to 9 pt. That was rejected.
- **Gate change:** the chip word limit is 6 words outside brackets instead of 5, because
  the thesis chip has 6. All other gates are unchanged. Results: 49 sentence words,
  15 chips (67 words), and pypdf finds 35/35 strings on the page.
- **Optional connector** from the "When to stop before the rods jam" chip up to the
  Operator card: **skipped.** It would cross the dashed return loop and its caption, and
  it would be the only long, bent run on the slide. The strip is already titled "What
  the operator gets".
- **Swap into STRICT (done):**
  - The deck was backed up to
    `archive/SIH26120_Idea_Presentation_STRICT_pre-final-slide3.pptx`, slide 3 was
    redrawn, and the 6-page PDF was re-exported.
  - pypdf finds 35/35 on page 3.
  - Slides 1, 2, 4, 5 and 6 are **byte-identical** to the backup: slide XML, rels and
    media, compared zip part by zip part. Only `slide3.xml` and its rels changed, plus
    12 new icon PNGs in `ppt/media/`. The PDF text of pages 1, 2, 4, 5 and 6 is also
    identical.
  - `diagram/slide3_final.png` is the in-deck render (slide number 3).
- **Revert:** copy the backup over the STRICT `.pptx`, then rerun
  `build_tech_slide_native.py`. It re-applies the detailed slide and re-exports the PDF.

### Slide 3, MEDIUM variant — `ppt/build_tech_slide_medium.py` (26 Sep, preview only)
The team lead liked the simple slide and asked for a middle version. It keeps the same
layout, icons, five stations and plain sentences, and adds enough detail that a technical
judge also sees substance.
```
.venv\Scripts\python.exe ppt\build_tech_slide_medium.py              # preview .pptx + .pdf + PNG
.venv\Scripts\python.exe ppt\build_tech_slide_medium.py --no-export  # gates + .pptx only
.venv\Scripts\python.exe ppt\build_tech_slide_medium.py --into-strict # swap into STRICT (not run)
```
→ `final/SIH26120_Slide3_MEDIUM_preview.pptx` / `.pdf` (1 page) and
`diagram/slide3_medium.png`. It imports the simple builder (icons, stations, strips,
`draw()`, deck plumbing, COM export) and names its shapes `TM_*`. The simple builder's
slide opener now strips `TA_*`, `TS_*` and `TM_*`, so any variant can be redrawn over any
other.

- **What changed from simple:** cards are 2.21 in wide (the arrow gaps shrink from
  0.51 to 0.44 in). Icons are 0.78 in on 0.94 in discs. Each station gets **3 detail
  chips**, 15 in all: 9.5 pt, one line each, tinted fill, no border. The caption, strip
  labels and strip headers drop to 11–12 pt, and the strip icons to 0.36 in.
- **Chips** (from the detailed slide):
  - The well: Baghewala: 1,150 m, 11,500 cP · Oil India cycle records (CSV) · Checked vs 9,692 real cycles
  - Digital twin: Heat flow (Marx–Langenheim) · Thick oil vs heat (Walther) · Rod loads + rod-float index
  - Smart search: True-physics grid, 5 controls · Fast what-if model (XGBoost) · Best/worst case (Monte-Carlo)
  - Dashboard: 4 pages, works offline · Computed pump card (dyno) · Upload records → twin learns
  - Operator: 5 settings, incl. stop rule · Review, confirm, then load · Field view: which well next
- **Where the chips differ from the brief:** it proposed 17 chips (3/4/4/3/3). That is
  over its own ≤ 15 cap, and most of them were longer than 5 words or one line at
  9–10 pt in a 2.2 in card. These were trimmed:
  - Twin: the water-cut chip was dropped.
  - Search: the rod-float safety rule was dropped, because the sentence already says
    "keeps the safe ones" and the operator's stop rule covers it. The 53,000 / 36 s
    figure is already in the sentence, so that chip became "True-physics grid,
    5 controls".
  - Operator: "advisory only" was already the sentence, so that chip became the
    stage → confirm → load flow.
  - The CalGEM name was dropped from "Checked vs 9,692 real cycles" to keep it on one
    line.
  - "OIL", "CSS" and "ML" were written out or dropped. Upper-case abbreviations are
    only allowed inside brackets, e.g. "(CSV)".
- **Gates:** it runs all five native gates, plus:
  - text ≥ 11 pt everywhere except the detail chips, which must be 9–10 pt; station
    titles 14–16 pt;
  - ≤ 60 words in the five sentences (**49**) and ≤ 15 detail chips (**15**, 2–3 per
    station);
  - each chip has ≤ 5 words outside its brackets and must render as **one line**;
  - no acronyms or code names in the sentences; in chips, upper-case abbreviations only
    inside brackets;
  - the orphan check; station icons ≥ 0.7 in; icons clear of text; no wire across a
    panel it does not belong to.

  pypdf finds **35/35** strings as text: titles, sentences, chips, strip labels, caption
  and trust line.
- **Iterations:**
  1. The gate caught two chips that would wrap ("Heat in rock (Marx–Langenheim)",
     "Upload records → twin re-learns"), measured against the width left after the
     chip insets. They were shortened.
  2. First render. The layout read well, but about 0.25 in at the bottom of the band was
     unused. That space went to bigger icons (0.74 → 0.78 in), taller chips with more
     air, a wider gap before the loop and taller strip chips. The chip "vs 9,692 real
     cycles (CalGEM)" started lower-case and read oddly, so it became "Checked vs 9,692
     real cycles".
  3. Final render checked for clipping, orphans and icon legibility.
- **Swap:** `--into-strict` was tested on a scratch copy of the STRICT deck (6 pages,
  35/35 text). It has not been run on the real deck. It backs up to
  `archive/…_STRICT_pre-medium-slide3.pptx`.

### `ppt/diagram/` — the Technical Approach architecture picture (SUPERSEDED for slide 3, kept for reference)
Purpose-built to copy the *winning* deck's Technical Approach slide (see
`WINNING_DECK_ANALYSIS.md` lesson 3): colour-coded rounded blocks with sub-bullets
**inside** them, black elbow arrows with real arrowheads, left-to-right dataflow,
flat white ground, near-zero slide text. It replaced the old
`system_flow_light` + `stack_layers_light` pair — one picture instead of two.
```
.venv\Scripts\python.exe ppt\diagram\render.py        # HTML -> PNG (+ QC downscales)
.venv\Scripts\python.exe ppt\patch_tech_slide.py      # swap it into an existing deck
```
- `tech_architecture.html` — 1980x780 hand-laid-out canvas (absolute CSS positioning +
  one inline `<svg>` for every wire and the pumpjack glyph). Segoe UI / Arial.
- `render.py` — headless Edge at `--force-device-scale-factor=2` → **3960x1560** PNG,
  plus `tech_architecture_check.png` (1:1) and `tech_architecture_zoom50.png` (50%) for
  legibility inspection, plus a **programmatic overflow assertion**: the page stamps
  `body[data-overflow]` after measuring `scrollHeight/scrollWidth` vs `clientHeight/Width`
  on every box, and `render.py` re-runs Edge with `--dump-dom` and exits non-zero if it
  is anything but `NONE`. No clipped text can ship silently.
- Content: well glyph (BGW-8) → ① DATA → ② PHYSICS ENGINE (4 model chips:
  Marx–Langenheim / Andrade μ(T) / Vogel IPR / SRP rod dynamics) → ③ ML + OPTIMIZATION
  (R²=0.72, AUC=0.99, `P(float) < 0.30` gate) → ④ DIGITAL TWIN CONSOLE, an orange
  closed-loop elbow arrow back to the well ("recommended set-points → VFD speed / steam
  schedule"), a dashed ROADMAP strip (OIL historical recalibration, SCADA/OPC-UA) and a
  mono-chip STACK strip along the bottom.
- Placed at **11.78 x 4.64 in at (0.78, 2.16)** — between the pointer text box
  (bottom 2.08 in) and the template footer bar (top 6.95 in), verified by
  `patch_tech_slide.py` against every template shape.
- The slide's "Technologies to be used" pointer is kept in sync with the STACK strip.

No dashboard screenshot: the winning deck uses **no product screenshots**, so per the
brief it was skipped (the winning Technical Approach slide is diagrams only).

## Final slide list
| # | Template heading (unchanged) | Content |
|---|---|---|
| 1 | SMART INDIA HACKATHON 2026 / TITLE PAGE | PS ID SIH26120, full PS title, Theme Smart Automation, PS Category Software, Team ID `TBD`, Team Name `TEAM ________`, organisation line, one tagline |
| 2 | *Idea title* → "Digital Twin for CSS and Sucker Rod Pump Optimization" | `Proposed Solution (Describe your Idea/Solution/Prototype)` lead-in + 3 columns using the template's own pointers: *Detailed explanation* / *How it addresses the problem* / *Innovation and uniqueness* |
| 3 | TECHNICAL APPROACH | 2 pointer lines (technologies; methodology) + a **native-shape** wiring diagram (`build_tech_slide_native.py`; all text selectable in the PDF): INPUTS → PHYSICS TWIN (`twin/`, 6 modules, μ(T) fork) → DATA & ML (`ml/`) → SERVICE (`api/` endpoints) → DASHBOARD pages → operator → well, with the calibrate feedback loop and a validation ring |
| 4 | FEASIBILITY AND VIABILITY | 3 columns: *Analysis of the feasibility* / *Potential challenges and risks* / *Strategies for overcoming these challenges* (risks pair 1:1 with mitigations) |
| 5 | IMPACT AND BENEFITS | *Potential impact on the target audience* + *Benefits (social, economic, environmental)* blocks, and the SOR waterfall chart captioned "synthetic-data result, to be validated on OIL field data" |
| 6 | RESEARCH  AND REFERENCES | Marx-Langenheim 1959, Vogel 1968, Gibbs 1963, Andrade 1930/ASTM D341, SPE-23APOG-535203, OIL Rajasthan Fields page, `docs/research/landscape.md` |

## QC performed on the STRICT deck
- **Rendered.** PowerPoint COM (`New-Object -ComObject PowerPoint.Application`) is
  available on this machine: exported `SIH26120_Idea_Presentation_STRICT.pdf`
  (`SaveAs ..., 32`) **and** exported every slide to PNG (`Slides.Export`, 1600x900) and
  inspected all six visually. Headless Edge cannot open .pptx — use COM.
- **Programmatic checks** (python-pptx + PIL Arial metrics): 6 slides; no empty
  non-footer placeholder; no shape outside the 13.333x7.5in canvas; per-text-box wrapped
  line-height measured against the box height (worst box 95% full, none overflowing);
  no content box overlapping the reserved template zones (team-name oval 0.36-1.73in,
  SIH banner from 10.70in, footer bar from 6.95in). **VERDICT: PASS.**
- The exported PDF is 6 pages at 960x540pt — identical page geometry to the winning
  2025 deck.
- One real fix found by rendering: slide 2's title initially ran under the team-name
  oval and the SIH banner, so the idea title was shortened (the full PS title stays on
  slide 1).

## Numbers on the STRICT deck (all traceable)
1,150 m depth · 8,000-15,000 cP at 50 °C · steam 280-305 °C at 60-70% quality ·
porosity <10% · 550-600 km to Jaipur · India's first CSS, BGW-8, Dec 2018 ·
52 wells drilled / 33 operational / 19 CSS'd FY2025-26 · 218 t (FY17) → 43,773 t (FY26) ·
$15k-$50k per avoided workover (industry-typical) · CSS literature SOR range 3-8 t/m³ ·
synthetic result SOR 1.50 → 0.88 t/m³ (−41.3%) with the "to be validated on OIL field
data" caveat printed on the chart *and* in the caption · field commitment stated as a
20-30% cut, not a guarantee.

> **26 Sep:** the field-commitment line above is stale. Following the same-day audit
> (see `docs/PROJECT_LOG.md` §12), slide 5's commitment now reads "self-audited,
> physics v2 recalibration in progress; literature benchmark >20%" instead of quoting
> a 20-30% cut. Other dated fixes landed the same day: slide 3 now reads "advisory
> set-points to the operator (SCADA hook planned)" (no closed-loop VFD claim), slide 4
> reads "Parameter-sweep sanity tests" (not Monte-Carlo), the tech-stack chip says
> Python 3.13, and `SIH26120_Idea_Presentation_STRICT.pdf` was re-exported via
> PowerPoint COM on 26 Sep to pick up all of the above.

> **26 Sep — slide 3 labels to physics rev 12:** `field_params.json` now reads rev 12
> (saturated steam 85–97 kgf/cm², 307–317 °C at sandface, replacing the old 290 °C/0.65
> quality figure). `cycle.py` gained water cut as a state (condensate flowback
> 0.87 → 0.56) and the produce-end rule (rate cutoff OR 3 days of rod float);
> `thermal.py` picked up wellbore loss; `viscosity.py` now names the Pal–Rhodes
> emulsion model (O/W ↔ W/O inversion at 0.70, capped 10×) alongside Walther/ASTM
> D341; `ipr.py` adds P_current 9.4 MPa; `srp.py` spells out drag on the produced
> stream, liquid-basis pump capacity and the 64–144 in stroke range; `dyno.py` gained
> the measured-card classifier (96%). The ONE μ(T)/TWO FAILURES callout now names the
> late-cycle, oil-continuous trigger for rod float. `train.py`'s three chips were
> corrected to the current metrics (log-oil R² 0.996, incr. margin/day R² 0.98
> in-envelope, float-classifier AUC 0.9998, "emulator role"). `optimize.py` is now
> labelled as the surrogate what-if / UQ emulator (gp_minimize); `recommend_physics.py`
> is relabelled **decision engine** — the true-physics 5-D grid (steam, pressure,
> cutoff, stroke, SPM; soak fixed 10 d), 53,592 points, 36 s, FI ≤ 0.6,
> aggressive/conservative — and grew from a 3-line, 0.58 in box to a 7-line, 1.02 in
> box to hold it (`optimize.py`'s own box shrank in exchange, since its new text is
> much shorter). A new `/api/schedule` chip (wired from `recommend_physics.py`) covers
> the field-level steam scheduler; `/api/dyno/cards` became `/api/dyno/{cards,
> classify}` (no room for a second chip). Dashboard Overview, Model basis (now also
> naming "field view") and Simulator (water cut & float index, computed vs. measured
> dyno cards, ISA-101 alarm) were reworded and their boxes re-heighted to fit. The
> validation ring now reads "236 tests pass + 2 declared gaps (soak; cold-well
> pumpability)" and "Self-audit: external technical review 27 Sep — 10 findings,
> 8 fixed"; CalGEM, BGW-8 and the OIL data request boxes are unchanged. The template's
> own "Methodology and process for implementation" pointer (`TextBox 8`, furniture) was
> also rewritten in place — same position, new text ending "...true-physics grid
> optimiser → dashboard → advisory set-points + operating rule to the operator (SCADA
> hook planned)". Four inline wire captions (`T(t)`, `q_oil(t)`, `3,000 rows`,
> `verify`) were dropped: rev 12's longer labels leave no gap at those seams to hold
> them without overlapping a node. Every panel is now packed within a few hundredths
> of an inch of its own bottom edge (text-fit gate margins as low as ~0.5%) — expect
> future label edits here to need the same careful re-budgeting of node heights this
> revision did. Gates pass; PDF page 3 carries 41/41 node titles as selectable text
> (up from 40 — the new `/api/schedule` chip).
