# SVG Illustration Assets — Baghewala Digital Twin (SIH 2026)

Stock illustration assets for PPTs, dashboards, and posters. Each asset ships as a
`_dark` variant (tuned for `#0d1117` backgrounds, amber `#f59e0b` accents) and a
`_light` variant (tuned for white / near-white backgrounds, navy `#0f2540` + amber).
The hero scene (`pumpjack_scene_*`) paints its own full-canvas sky/ground and can be
dropped on any slide as-is. The four diagram assets (`well_cutaway_*`,
`css_cycle_phases_*`, `dyno_cards_*`, `india_field_map_*`) have transparent
backgrounds by design, so they compose cleanly onto a slide or dashboard panel
already carrying the matching dark/light theme color.

| File | Size (viewBox) | Intended use |
|---|---|---|
| `pumpjack_scene_dark.svg` | 1600×600 | Hero banner — dark-theme slide/deck cover or dashboard header showing a nodding-donkey pumpjack on Rajasthan dunes at night with warm rig lights and a steam plume. |
| `pumpjack_scene_light.svg` | 1600×600 | Same hero banner, dusk sky with sun, for light/white slide backgrounds and printed posters. |
| `well_cutaway_dark.svg` | 800×1200 | Tall cross-section for a side panel or poster: casing/tubing/sucker rod/downhole pump down to 1150 m with a depth ruler, geology strata bands, and the steam-heated Jodhpur Sandstone reservoir halo. Dark-theme dashboards. |
| `well_cutaway_light.svg` | 800×1200 | Same well cross-section, for light-theme reports, printed handouts, and slide decks. |
| `css_cycle_phases_dark.svg` | 1400×500 | Wide triptych explaining one CSS cycle (INJECT → SOAK → PRODUCE) with steam temperature and viscosity-drop callouts. Dark-theme process slides / dashboard explainer strip. |
| `css_cycle_phases_light.svg` | 1400×500 | Same CSS cycle triptych, for light-theme decks and printed one-pagers. |
| `dyno_cards_dark.svg` | 1200×500 | Side-by-side dynamometer card comparison (healthy loop vs. rod-floating / fluid-pound spike) with labeled axes, for a dark-theme diagnostics dashboard panel or training slide. |
| `dyno_cards_light.svg` | 1200×500 | Same dynamometer card comparison, for light-theme reports and printed material. |
| `india_field_map_dark.svg` | 900×1000 | Stylized/schematic India outline locating the Baghewala field (Bikaner) and MNIT Jaipur with an approximate distance connector and legend — dark-theme "where is this" context slide. Explicitly not survey-accurate (captioned "Schematic — not to scale"). |
| `india_field_map_light.svg` | 900×1000 | Same schematic locator map, for light-theme decks and posters. |
| `_preview.html` | — | QC harness only (not a deliverable asset): renders every SVG on both dark and light background strips, plus a wrong-background sanity pass, for visual review. Open directly in a browser. |

## Style notes
- Consistent 2–2.5 px stroke weight across all pieces.
- Palette capped at 4 colors + 1 gradient per asset: dark theme = `#0d1117` / `#f59e0b` / `#e6edf3` / `#334155` (+ 1 gradient); light theme = `#ffffff` / `#f59e0b` / `#0f2540` / `#94a3b8` (+ 1 gradient).
- All text ≥ 18 px, `font-family="Segoe UI, Arial, sans-serif"`.
- Only soft `feGaussianBlur` used (steam plumes, glow halos) — no heavier filters.
- Every file is standalone, valid XML with a `viewBox`, no external references; each opens directly in a browser.

## QC verdict
Reviewed via headless Edge screenshots of `_preview.html` (dark-on-dark, light-on-light,
and a wrong-background sanity pass for all 10 files). One real issue was found and
fixed: the Rajasthan highlight ellipse in `india_field_map_*` initially poked outside
the India outline — it was resized/recentered to sit fully inside the landmass, and the
overly needle-thin southern tip of the outline was rounded off. All other assets
(pumpjack scene, well cutaway, CSS cycle triptych, dynamometer cards) rendered cleanly
with no clipping, overlap, or contrast problems on their intended background. Final
pass confirmed clean — see report for details.
