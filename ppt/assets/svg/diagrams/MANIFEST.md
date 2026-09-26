# Diagram Manifest — Baghewala Digital Twin

Stock SVG diagrams for reuse in PPTs, posters, and the README. Each diagram
ships in a dark (`*_dark.svg`, `#0d1117` background, amber `#f59e0b` accent)
and light (`*_light.svg`, white background, navy `#0f2540` + amber accent)
variant. All are standalone, self-contained XML with a `viewBox` — no
external references, no scripts.

Open `_preview.html` in a browser to see every diagram rendered on its
correct background side by side (used for QC).

| File | Size (px) | Intended slide / section |
|---|---|---|
| `system_flow_dark.svg` / `_light.svg` | 1600×700 | **Architecture / solution overview slide.** The four-stage pipeline — Field/Synthetic Data → Physics Engine (Marx–Langenheim, Andrade μ(T), Vogel IPR, SRP dynamics) → ML Layer (SOR predictor, floating classifier, Bayesian optimizer) → Digital Twin Dashboard (replay, alerts, recommendations) — with the feedback arrow back to steam/VFD control. Use as the main "how it works" slide and in the README's architecture section. |
| `closed_loop_dark.svg` / `_light.svg` | 1000×1000 | **Concept / methodology slide.** The continuous monitor → predict → optimize → act loop around the well. Good as an early "our approach" slide, a poster centerpiece, or a small inline figure in the README's methodology section. |
| `sor_waterfall_dark.svg` / `_light.svg` | 1200×600 | **Results slide.** Waterfall from baseline 1.50 t/m³ to optimized 0.88 t/m³ via steam scheduling (−0.38) and pump pacing (−0.24), with the −41.3% callout and the synthetic-data caveat footnote. Use on the "results / impact" slide and in the README's results section — this is the single most important chart in the deck. |
| `data_journey_dark.svg` / `_light.svg` | 1600×500 | **Roadmap / timeline slide.** Seven-milestone journey from PS release through physics prototype, synthetic training (3,000 cycles), internal round, OIL historical data (flagged FINALE), recalibrated twin, to pilot well. Use on the "roadmap / next steps" slide and README timeline section. |
| `stack_layers_dark.svg` / `_light.svg` | 900×900 | **Tech stack slide.** Layered stack — Web Dashboard (Plotly) → FastAPI → XGBoost/scikit-optimize → Python/NumPy/SciPy — with open-source / indigenous / no-license-cost side annotations. Use on the "technology / feasibility" slide and README tech-stack section. |

## Usage notes

- Pick the dark variant for dark-themed slide decks / dark README sections,
  light variant for light-themed decks, print, or posters on white stock.
- All diagrams share the same visual language (rounded cards, amber accent,
  Segoe UI/Arial text ≥16px, consistent stroke widths) so they read as one
  family when mixed on a single deck.
- SVGs scale losslessly — resize freely in PowerPoint/Figma/Illustrator
  without quality loss.
