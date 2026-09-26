# Visual deck — design system & rebuild guide

**PS SIH26120 · Oil India Limited · Baghewala CSS + SRP Digital Twin · MNIT Jaipur**

This folder is the source of truth for the *visual* deck
(`ppt/SIH26120_Idea_Presentation_VISUAL.pptx` / `.pdf`). It is separate from, and
does not touch, the programmatic deck built by `ppt/build_deck.py`.

---

## Two outputs

| File | What it is |
|---|---|
| `ppt/SIH26120_Idea_Presentation_VISUAL.pptx` / `.pdf` | The presentation deck. Each slide is one full-bleed 2560×1440 render; all copy also lives in the slide notes. **Use this to present.** |
| `ppt/SIH26120_Idea_Presentation_VISUAL_EDITABLE.pptx` | Same design, but the copy is native PowerPoint text you can click and retype (see *Editable variant* below). **Use this for quick wording tweaks.** |

**For design-level changes — layout, colours, illustrations, anything structural —
edit the HTML and re-render.** The editable PPTX is only for text.

## Rebuild in one command

```
.venv\Scripts\python.exe ppt\visual\render.py          # the presentation deck
.venv\Scripts\python.exe ppt\visual\make_editable.py   # the editable variant
```

Run `render.py` first — `make_editable.py` reads the same `slideN.html` files.

That single command re-shoots all seven HTML pages to PNG, verifies each one, and
rebuilds both the PPTX and the PDF. To re-shoot only some slides (faster while
iterating), pass their numbers:

```
.venv\Scripts\python.exe ppt\visual\render.py 3 5
```

Slides not listed keep their existing PNG; the PPTX and PDF are still rebuilt from
the full set of seven.

**Requirements:** Microsoft Edge at
`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, plus `pillow` and
`python-pptx` in `.venv`. Note that `--headless=new` **and** an explicit
`--user-data-dir` are both required — plain `--headless` fails with
"Access is denied" when writing the screenshot on this machine.

## How to edit the text

Each slide is a single self-contained file, `slide1.html` … `slide7.html`:
inline CSS, inline SVG, system fonts, **no external resources of any kind**. Edit
the HTML directly, then re-run the command above.

Each file also carries a `<script type="text/x-notes">` block at the bottom. That
text is not rendered on the slide — `render.py` extracts it and writes it into the
PowerPoint **slide notes**, so the full talking points stay searchable and editable
inside the PPTX. Keep it updated when you change slide copy.

---

## Design system

### Palette — three colours, no more

| Role | Hex | Used for |
|---|---|---|
| Ink (deep navy) | `#0f2540` | Headlines, rail, dark cards |
| Ink secondary | `#1e3a5f` / `#3b5471` | Sub-headings, secondary bars |
| Body text | `#4c6076` | Paragraph copy |
| Muted | `#8493a6` | Captions, footer, axis labels |
| Amber (primary accent) | `#f59e0b` | Rules, pins, highlight bars, rail text |
| Ember (secondary accent) | `#ea580c` | Kickers, arrows, emphasis |
| Ember deep | `#c2410c` / `#a1560c` | `<em>` in headlines, amber-on-light text |
| Base | `#fbfcfd` | Slide background |
| Surface | `#ffffff` | Cards |
| Rule | `#e4e8ee` | Borders, hairlines |
| Amber tint | `#fff7e8` / border `#f6d69a` | Chips, icon tiles, callouts |

Light base throughout — SIH rooms project onto bright screens, and a dark deck
washes out.

### Type — Segoe UI stack, two sizes per block

```
"Segoe UI", "Segoe UI Variable Text", -apple-system, Roboto, Helvetica, Arial, sans-serif
```

| Element | Size | Weight |
|---|---|---|
| Title-slide H1 | 47px | 700, `-1.1px` tracking |
| Content H1 | 40px | 700, `-0.85px` tracking |
| Kicker (section eyebrow) | 13.5px | 700, `3.2px` tracking, uppercase, ember |
| Card heading | 20px | 700 |
| Body copy | 20px on light slides, 16px in dense card grids | 400 |
| Big stat number | 42px | 700, `-2px` tracking |
| Caption / axis / footer | 11–13.5px | 400–600 |
| Code & equations | Consolas mono, 14.5–15px | — |

Never more than two text sizes inside one text block.

### Grid — the repeated frame

Every slide, including the title, carries the identical frame:

- **Left rail**, 62px, navy vertical gradient. Contains: hex logo mark (top),
  `SIH26120 · OIL INDIA LTD` set vertically in amber (middle), and the slide
  number `NN /07` (bottom).
- **Top bar**, 4px, amber→ember for the first 46% then navy.
- **Content column** starts at x=110 and ends at x=1222 (1112px wide).
- **Header block**: kicker at y=31, H1 at y=52, hairline rule at y=122 with a 64px
  amber cap on its left end.
- **Content region**: y=140 to y≈620.
- **Footer**, 38px, hairline top border: slide subject on the left,
  `MNIT JAIPUR · SIH 2026` in ember on the right.

Corner radius is 14px for cards, 13px for dark panels, 999px for chips.
Icon strokes are 2px everywhere, 24×24 viewBox, `round` caps and joins.

### Official SIH template branding

Extracted from `ppt/template_official.pptx` and mirrored on all seven slides.
What the official template actually carries (positions below are the template's
own EMU values scaled to our 1280×720 canvas):

| Template element | Where it sits | What we did |
|---|---|---|
| SIH 2026 logo (`ppt/media/image2.png`, 12222×5771 px) | Picture, top-right, `x=1026.8 y=0.2 w=236.2 h=111.5` — on **every** slide | Same corner. Downscaled to 504px wide, embedded as an inline `data:` URI, rendered at **168×79.3** at `right:58px top:10px`. Smaller than the template's so it never crowds our headline |
| Footer band | `Rectangle`, full width, `x=0 y=667.2 w=1280 h=52.8`, solid fill **`#0070C0`** | Full-width band, `y=672 h=48`, in our navy `#0f2540` with a **3px `#0070C0` SIH-blue top rule** — keeps the official structure without adding a fourth colour to the palette |
| Footer text | `"@SIH Idea submission- Template"` at `x=488 y=667.3` | Replaced with the real submission line: **`PS SIH26120 · TEAM ________ · Smart India Hackathon 2026`** |
| Slide-number placeholder | `x=917.3 y=667.3`, right side of the band | Right side of our band: `SECTION · NN/07` in amber |
| "Your Team Name" oval (alt-text *"Your startup LOGO"*) | `x=34.6 y=26.5 w=131.4 h=84.8`, top-left | **Not reproduced** — that spot is our navy rail, and the team placeholder already appears in the footer line. Fill the `TEAM ________` blank instead |
| `image1.png` (SIH **2022** logo) | Only a decorative picture on the template's title page | Not used — it is last year's mark |

Consequences for our grid: the logo occupies `x 1054–1222, y 10–89`, so the
content-slide `h1` was reduced to **37px with `width:930px`**, and the title
slide's header block shifted down 22px (`.kick{margin-top:66px}`). The left rail
now stops at `y=672` where the footer band begins.

To re-extract: `unzip ppt/template_official.pptx -d somewhere` — the logo is
`ppt/media/image2.png`, and every slide's top-right `<p:pic>` references it.

### Headline length rule

The 40px H1 fits **~57 characters on one line** in the 1112px column. Longer
headlines wrap into the hairline rule. If you edit a headline, keep it under that
and re-render to confirm.

---

## Slide inventory

| # | Section | Custom illustration |
|---|---|---|
| 1 | Title & PS details | Wide horizon scene — pumpjack silhouette, steam plume, layered Thar dunes, amber sunset |
| 2 | Proposed Solution | Well cross-section cutaway — beam pump, rod string in insulated tubing, downhole pump at ~1,150 m, steam-heated halo in the Jodhpur Sandstone with inflow arrows |
| 3 | Technical Approach — architecture | Four-layer flow with chevrons, closed-loop feedback bar, three governing equations as dark cards (light-theme redraw of `docs/architecture.svg`) |
| 4 | Technical Approach — methodology | CSS cycle chart: inject / soak / produce phase bands, reservoir-temperature and oil-rate curves, four decision-variable pins |
| 5 | Feasibility & Viability | Three pillars, five-node build timeline with progress track, risk/mitigation strip |
| 6 | Impact & Benefits | Four big-number callouts (one with a growth sparkline), SOR baseline-vs-target bar comparison with published-range whisker and efficiency threshold |
| 7 | Research & References | Two-column citations with favicon-style source dots, MNIT strip |

SIH allows a maximum of six content slides. Slide 1 is the mandated title/PS page;
slides 2–7 are the six content slides, with Technical Approach split across two
(architecture, then methodology).

---

## Editable variant

`SIH26120_Idea_Presentation_VISUAL_EDITABLE.pptx` exists because the presentation
deck is full-bleed images — nothing in it can be clicked. The editable build
(`make_editable.py`) splits each slide in two:

1. **A text-free background.** `editable/slideN.html` is the normal slide plus a
   measuring script. The script walks the DOM, records every text element's
   rectangle, font, weight, colour and inline runs, then paints that text
   `transparent` — so the render keeps every card, chip, rule, icon, chart axis
   and illustration, but loses the copy. Result: `editable/bgN.png`.
2. **Native text on top.** python-pptx places one real PowerPoint text box per
   measured element at the matching position and size. Conversion is exact:
   1280px canvas = 13.333in, so **1 css px = 0.75pt = 9525 EMU**. Bold/italic
   runs, per-run colours, letter-spacing and uppercase transforms are carried over.

**180 editable text boxes across 7 slides.** Click any headline, bullet, stat
number or the footer line and retype it.

Deliberately left in the background artwork, because they are geometry-locked to
a drawing and would break if reflowed:

- the navy left rail (`SIH26120 · OIL INDIA LTD`, slide number)
- anything inside an `<svg>` — chart axis ticks and values, the CSS-cycle phase
  bands, the well-cutaway leader labels, the SOR bar values and the chart's
  own heading and caption

To change any of those, edit the HTML and re-run both scripts.

Known limits of the editable build: subscripts in the equation blocks flatten to
normal characters, and PowerPoint's text metrics differ very slightly from the
browser's, so a long paragraph can wrap one word differently. Boxes carry ~5%
width slack to absorb that.

**Font sizes** come straight from the design, converted at 0.75pt/px: headlines
27.8–35.2pt, card headings 15pt, body copy 12–15pt, captions and axis notes
7.9–12pt. Only 16% of runs are ≥14pt — that is by design on a 13.333in canvas,
and it is exactly the type size the rendered deck already uses. Do not bulk-raise
them: the background artwork has holes sized for this type, and larger text will
overflow its card.

## Content version used

Built against **`ppt/deck_content.md` as of the post-review revision** — i.e. the
version produced *after* `review/FIXES_APPLIED.md` was written (2026-09-13). All
thirteen content-review findings are reflected. Specifically, this deck uses the
corrected numbers, not the originals:

- `~550–600 km` Baghewala→Jaipur (**not** the retired "250 km")
- Reservoir depth `~1,150 m` (**not** "500 m")
- Viscosity `8,000–15,000 cP @ 50 °C` (**not** "2000 cP")
- API stated diplomatically: `17–19° per PS · 14–17° in field literature`
- SOR benchmarked against the published `3–8` band, average `~6`, efficient `<3`,
  optimiser target `<3.5` — the invented "4.5 current SOR" appears nowhere
- Economics as `$15k–$50k per avoided workover` (**not** the retired "$500k/year")
- No field failure-reduction percentage is claimed (the retired "80%")
- SOR reduction labelled `physics-simulated`, never "physics-validated"
- `52 wells drilled / 33 operational`, 19 CSS'd FY2025-26 (**not** "40+ CSS wells")
- `218 t → 43,773 t`, FY2016-17 → FY2025-26
- References list SPE-23APOG-535203, Oil India / BGW-8 and `docs/landscape.md`;
  the unverifiable Pennwell citation is gone

The SOR comparison chart carries an explicit *"Illustrative — to be validated on
Oil India data. Baghewala's own SOR is unreported."* label, per the brief.

## Files here

```
slide1.html … slide7.html   source pages, 1280x720, fully self-contained
                            (SIH logo embedded as an inline data: URI)
slide1.png  … slide7.png    rendered at 2560x1440 (2x)
render.py                   HTML -> PNG -> PPTX + PDF, with verification
make_editable.py            HTML -> text-free PNG + native text -> EDITABLE PPTX
editable/                   generated: measuring pages + bg1..bg7.png
DESIGN_NOTES.md             this file
.edge-profile/              throwaway Edge user-data dir, recreated on demand
```

`template_extract/` (the unzipped official template) is scratch — it is deleted
after each branding pass and can be regenerated by unzipping
`ppt/template_official.pptx`.
