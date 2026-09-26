# SIH Baghewala — Icon Set Manifest

28 stroke-based icons for the Oil India heavy-oil digital twin project.
48x48 viewBox, `stroke-width="2"`, round caps/joins, `stroke="currentColor"` (no fills except tiny accent dots/pivots). Safe to drop into PPTs, dashboards, or web UI — theme by setting the `color` CSS property or SVG `fill`/`color` attribute on a wrapping element.

Also included:
- `sprite.svg` — all 28 icons as `<symbol id="ic_...">` for `<use href="sprite.svg#ic_name">` (embed inline in an HTML page, not opened directly via `file://`, since `<use>` on an external file needs to be served or inlined — see note below).
- `_preview.html` — visual grid at 48px / 24px / 20px, dark (amber-on-#0d1117) and light (navy-on-white) rows. Open directly in a browser.

> Note on `sprite.svg`: browsers resolve external `<use href="sprite.svg#id">` references via a same-origin fetch, which most browsers block under `file://`. It works fine once the page is served over `http(s)://` (e.g. via a dev server, or bundled into the PPT/dashboard's build). For static file-preview purposes, `_preview.html` inlines the icon markup directly instead of referencing the sprite.

## Icon list and suggested use

| Icon | File | Suggested use |
|---|---|---|
| Pumpjack | `ic_pumpjack.svg` | Wellsite / production asset marker, field map pins |
| Oil drop | `ic_oil-drop.svg` | Crude oil volume, production rate, generic "oil" label |
| Oil barrel | `ic_oil-barrel.svg` | Barrels produced/stored, inventory, BPD (barrels per day) stat tiles |
| Steam | `ic_steam.svg` | Steam injection (SAGD/CSS), thermal recovery process indicator |
| Flame | `ic_flame.svg` | Heat/combustion, flare stack, thermal energy input |
| Temperature | `ic_temperature.svg` | Reservoir/wellbore temperature sensor readout, thermal setpoint |
| Viscosity | `ic_viscosity.svg` | Oil viscosity readout, flow-assurance status, heavy-oil property card |
| Pressure gauge | `ic_pressure-gauge.svg` | Wellhead/reservoir pressure readout, gauge widget in dashboards |
| Well | `ic_well.svg` | Well/derrick marker, drilling site, asset hierarchy icon |
| Drill bit | `ic_drill-bit.svg` | Drilling operations, well completion, drilling KPI section |
| Pipeline | `ic_pipeline.svg` | Flowline/pipeline network, transport infrastructure |
| Valve | `ic_valve.svg` | Choke/control valve status, flow control component |
| Sensor | `ic_sensor.svg` | IoT sensor node, telemetry source, data acquisition point |
| Dashboard | `ic_dashboard.svg` | Link to monitoring dashboard, "view analytics" CTA |
| AI chip | `ic_ai-chip.svg` | ML/AI model badge, edge-compute or inference engine label |
| Neural net | `ic_neural-net.svg` | Model architecture reference, "AI-powered" feature callout |
| Optimization | `ic_optimization.svg` | Optimization engine output, recommendation/target achieved |
| Graph up | `ic_graph-up.svg` | Positive trend — production increase, efficiency gain |
| Graph down | `ic_graph-down.svg` | Negative trend — decline curve, cost/emission reduction |
| Alert triangle | `ic_alert-triangle.svg` | Warning, anomaly detection flag, threshold breach |
| Shield check | `ic_shield-check.svg` | Safety compliance, validated/verified status, HSE badge |
| Rupee saving | `ic_rupee-saving.svg` | Cost savings, ROI callout, financial impact stat |
| Energy bolt | `ic_energy-bolt.svg` | Power consumption, energy efficiency, electrical load |
| CO2 cloud | `ic_co2-cloud.svg` | Emissions tracking, carbon footprint, sustainability metric |
| Calendar cycle | `ic_calendar-cycle.svg` | Maintenance schedule, recurring cycle/interval, planning view |
| Wrench maintenance | `ic_wrench-maintenance.svg` | Maintenance task, service ticket, equipment upkeep |
| Team | `ic_team.svg` | Team/crew assignment, collaboration, stakeholder section |
| India flag chakra | `ic_india-flag-chakra.svg` | National/SIH branding accent, "Made in India" marker |

## QC notes

All 28 icons were rendered at true 20px (the smallest intended UI size), screenshotted with headless Edge, and visually reviewed. Eight icons were ambiguous or muddy at 20px in the first pass and were redesigned:

- `oil-barrel` — was a flat grid (read as a spreadsheet); redesigned as a rimmed cylindrical drum with two bands.
- `viscosity` — was a blob-thread-drop (read as a lollipop/spoon); redesigned as a single droplet silhouette with an internal wave/swirl.
- `pressure-gauge` — was a full circle with cardinal ticks (read as a wall clock); redesigned as an open-bottom dial arc with fanned ticks, a needle, and mounting feet.
- `drill-bit` — was vertical with a flat top (read as a pencil); redesigned as a horizontal fluted bit with a conical tip.
- `pipeline` — was a double-line grid with an elbow (read as a hashtag/fence); redesigned as a single clean pipe with one right-angle bend.
- `valve` — was a bowtie plate with a spoked wheel (read as a bird/propeller); redesigned as a simple pipe-circle-pipe body with a T-handle.
- `rupee-saving` — was three stacked ellipses (read as a database icon); redesigned as a coin (circle) with a rupee-glyph mark inside.
- `wrench-maintenance` — was a custom hook shape (read as a balloon/lock); redesigned using a standard wrench-silhouette path.

All 28 were re-screenshotted after fixes and confirmed legible at 20px in both dark and light themes.
