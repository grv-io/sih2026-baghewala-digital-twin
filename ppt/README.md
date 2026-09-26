# ppt/ — SIH26120 pitch deck

**Submit this:** [`final/SIH26120_Idea_Presentation_STRICT.pptx`](final/) (and its `.pdf`).
It is the official SIH 2026 template with the master untouched — see
[`notes/BUILD_NOTES.md`](notes/BUILD_NOTES.md) for why the other versions were dropped.

| Folder / file | What it is |
|---|---|
| `final/` | ★ Submission deck (STRICT), `.pptx` + `.pdf` |
| `archive/` | Superseded decks: plain template fill, VISUAL (off-template, rejected), VISUAL_EDITABLE, and the STRICT-deck backups taken before each slide-3 swap (`…_pre-final-slide3.pptx` = the deck with the detailed slide 3) |
| `notes/` | `BUILD_NOTES.md` (how each deck is built + QC), `WINNING_DECK_ANALYSIS.md`, `deck_content.md` |
| `template/` | Official SIH 2026 idea-presentation template — never edit |
| `assets/` | `sor_chart.png` + `svg/` library (28 icons, 5 illustrations, 5 diagrams, dark + light) |
| `build_strict_deck.py` | Builds `final/…_STRICT.pptx` from the template |
| `build_tech_slide_native.py` | Slide 3 **detailed** version (no longer in the deck, see below) as **native shapes**, so all text is copyable in the PDF. Includes layout + text-fit gates, COM export and a pypdf label check |
| `build_tech_slide_final.py` | ★ Slide 3 **FINAL**, now in the STRICT deck: the medium layout plus the team lead's honesty/thesis chip edits. Also writes a 1-slide preview (`final/SIH26120_Slide3_FINAL_preview.*`) and `diagram/slide3_final.png` |
| `build_tech_slide_medium.py` | Slide 3, **medium version**: the simple layout plus 3 one-line detail chips per station (method names in brackets) so technical judges see substance too. Separate one-slide **preview** (`final/SIH26120_Slide3_MEDIUM_preview.pptx` + `.pdf`, `diagram/slide3_medium.png`). Reuses the simple builder. `--into-strict` swaps it in (documented, not run) |
| `build_tech_slide_simple.py` | Slide 3, **simple icon version** for non-technical readers (5 icon stations: well → digital twin → smart search → dashboard → operator). Separate one-slide **preview** (`final/SIH26120_Slide3_SIMPLE_preview.pptx` + `.pdf`, `diagram/slide3_simple.png`). `--into-strict` swaps it in (documented, not run) |
| `diagram/` | `slide3_native.png` = QC render of slide 3; `slide3_final.png` = slide 3 as it is in the deck now; `slide3_medium.png` / `slide3_simple.png` = previews; `slide3_native.png` = the detailed version. The old PNG pipeline (`tech_architecture.html` + `render.py`) is superseded |
| `patch_tech_slide.py` | Superseded for slide 3 (it placed the PNG). It is kept because the native builder imports its `FURNITURE` set |
| `_strict_build/` | Intermediate PNGs the STRICT build renders from `assets/svg/` |
| `build_deck.py`, `make_chart.py`, `visual/` | Build sources for the archived decks |

## Rebuild the submission deck

```bash
.venv\Scripts\python.exe ppt\build_strict_deck.py                     # -> ppt/final/SIH26120_Idea_Presentation_STRICT.pptx
.venv\Scripts\python.exe ppt\build_tech_slide_native.py               # slide 3 -> detailed diagram + methodology pointer text
.venv\Scripts\python.exe ppt\build_tech_slide_final.py --into-strict  # slide 3 -> FINAL version; 6-page PDF; pypdf check
```

The slide-3 builders export the PDF themselves. They drive PowerPoint through COM, so
PowerPoint must be installed and the deck must not be open. `--no-export` builds and
gates the slide only. **Slide 3's text must stay selectable in the PDF**, so never put a
picture of the diagram back. Edit the builders instead. See `notes/BUILD_NOTES.md` for
the gates and QC.

### Four versions of slide 3 — FINAL is the one in the deck

| Variant | Script | Who it is for | Where it lives |
|---|---|---|---|
| **Final** | `build_tech_slide_final.py` | everyone: the medium layout + honesty / thesis chips | ★ **slide 3 of the STRICT deck** (since 26 Sep); preview `final/SIH26120_Slide3_FINAL_preview.*`, `diagram/slide3_final.png` |
| **Detailed** | `build_tech_slide_native.py` | technical judges: every module, wire and metric | `archive/SIH26120_Idea_Presentation_STRICT_pre-final-slide3.pptx`, `diagram/slide3_native.png` |
| **Medium** | `build_tech_slide_medium.py` | simple story + 15 one-line detail chips | preview `final/SIH26120_Slide3_MEDIUM_preview.*`, `diagram/slide3_medium.png` |
| **Simple** | `build_tech_slide_simple.py` | no technical background: 5 icons, 5 plain sentences | preview `final/SIH26120_Slide3_SIMPLE_preview.*`, `diagram/slide3_simple.png` |

Every icon builder runs the native builder's gates plus its own: font floors, word and
chip budgets, no jargon in the plain sentences, one-line chips, no orphan words. Any of
them can be swapped into the deck with `--into-strict`. Each one backs the deck up to
`archive/` first, redraws only slide 3 and re-exports the 6-page PDF.

**Revert to the detailed slide 3:** copy
`archive/SIH26120_Idea_Presentation_STRICT_pre-final-slide3.pptx` over
`final/SIH26120_Idea_Presentation_STRICT.pptx`, then rerun `build_tech_slide_native.py`.
It rebuilds the detailed diagram, checks the gates and re-exports the PDF. Run on a
slide 3 that still carries `TF_*` / `TM_*` / `TS_*` shapes, it refuses on purpose, so
restore the backup first.

Study and viva material for the deck lives in [`../docs/study/`](../docs/study/).

## Whole deck in the slide-3 aesthetic (27 Sep)

`build_deck_final.py` redraws slides 2, 4, 5 and 6 in the same family as the FINAL
slide 3 (icon disc + one plain sentence + detail chips; template pointers kept verbatim
as the card header bands; slide 1 and 3 untouched). Slides 2 and 6 carry three editable
link placeholders (live dashboard, demo video, GitHub). Numbers are the rev-12 *robust*
ones (SOR 4.35 → 3.19, better than baseline in 94 % of runs, ₹ gain as a range).

```bash
.venv\Scripts\python.exe ppt\build_deck_final.py               # gates + PDF + slide PNGs
.venv\Scripts\python.exe ppt\build_deck_final.py --no-export   # gates + .pptx only
```

Backup of the pre-rebuild deck: `archive/SIH26120_Idea_Presentation_STRICT_pre-final-deck.pptx`.
