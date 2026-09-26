# UI/UX Overhaul Brief — Baghewala Digital Twin Dashboard

Quick research pass (Grafana docs, Palantir Foundry design writeups, ISA-101 /
high-performance-HMI guidance) plus the existing dashboard's own visual
language. Ten decisions applied in `dashboard/index.html`, each chosen to read
as "control room," not "demo site," in a single screenshot.

1. **Calm-by-default, color-means-something.** ISA-101 and the High
   Performance HMI Handbook both push a mostly neutral screen with color
   reserved for abnormal states — red/amber never appear as decoration, only
   as alarm. We already had a dark/amber base; the overhaul keeps every new
   accent (tricolor line, ticker, sparkline) desaturated/thin so the one red
   alert banner + panel glow stays the single loud thing on screen.
   [Industrial Monitor Direct — HMI grayscale & alarm philosophy](https://industrialmonitordirect.com/blogs/knowledgebase/high-performance-hmi-design-principles-for-industrial-control)

2. **One alarm, done properly.** Per ISA-101's "red = critical, nothing else
   is ever red" rule, the floating-risk alarm (`floating_index > 0.6`) now
   also throws a soft red siren-glow border on the two panels actually
   implicated (dynamometer card + gauge/KPI panel) instead of tinting the
   whole page — a single, trustworthy signal rather than screen-wide panic.
   [ISA-101 alarm colour hierarchy](https://www.instrumentationblog.in/scada-hmi-screen-design-isa-101-best-practices/)

3. **Grafana-style restraint on the base theme.** Grafana's dark dashboards
   keep the background near-black, type grey, and put all saturated colour
   on the data itself. We kept the existing `#0d1117`/`#161b22` palette
   untouched and only ever introduced new colour on interactive/telemetry
   elements (ticker text, sparkline, droplet), never on chrome.
   [Grafana dashboard best practices](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/)

4. **Palantir-Foundry-grade "mission" framing in the header.** Foundry/
   Workshop dashboards read as authoritative because of restrained motion +
   dense-but-clean typographic hierarchy, not flashy graphics. The header
   gets a very slow (6s) diagonal shimmer sweep — barely visible, reads as
   "live system," not a banner ad.
   [Palantir Foundry app-building overview](https://www.palantir.com/docs/foundry/app-building/overview)

5. **Restrained national identity, not a flag.** A 3px animated tricolor
   (saffron/white/green) hairline sits under the header with a slow
   specular sweep, plus a small classy "Digital India · Make in India" badge
   with an inline tricolor dot — present, tasteful, never plastered across
   the UI (explicit brief constraint).

6. **Animated nodding-donkey pumpjack in the header, speed tied to SPM.**
   Judges (Oil India engineers) will recognize a sucker-rod pumpjack
   instantly — it's the single fastest way to signal "this is a real oilfield
   twin, not a generic dashboard template." Built as one inline SVG with a
   CSS-transform beam rotation; its animation-duration is bound to the SPM
   slider live (`--pump-duration` custom property), at zero extra JS-per-frame
   cost.

7. **Well-schematic micro-diagram with phase-aware steam/oil flow.** A small
   inline SVG (casing + dashed flow line) sits in the time-series panel
   header. `stroke-dashoffset` animates continuously; JS only flips a class
   (`phase-inject` / `phase-soak` / `phase-produce`) after each simulate —
   amber flowing down during injection, green flowing up during production,
   dim/static during soak — so the picture matches the physics state without
   any per-frame script.

8. **Telemetry ticker = the "it's alive" cue control rooms actually use.**
   A slim scrolling strip of timestamped log lines (`T_res 132.4°C · μ 310 cP
   · SPM 8.0 — OK`) under the header mimics a real SCADA event/trend log.
   Pure CSS marquee (duplicated content, `translateX` loop) — no timers.

9. **KPI tiles get count-up, glow-on-change, and one sparkline + droplet.**
   Numbers animate from old→new via `requestAnimationFrame` (~600 ms) with a
   soft amber glow pulse so a re-simulate visibly registers; the "Total Oil
   Recovered" tile gets a tiny inline sparkline of the cycle's oil-rate curve
   and a small looping droplet glyph — genuinely cheap (all data already
   computed) and it's the tile judges' eyes land on first.

10. **Motion has an off switch and a screenshot-safe rest state.** Every
    infinite animation is wrapped in `@media (prefers-reduced-motion:
    reduce)` to pause/disable it, and every element's *first frame* (load
    state) is already a finished, legible composition — because a judge's
    screenshot is a random freeze-frame, not the end of a timeline. The one
    deliberate multi-frame moment — a 400–600 ms fake "computing" shimmer on
    Simulate/Optimize — exists specifically so a *live demo* shows a
    computation happening, without ever depending on it for the screenshot.

## Deliberately not done (restraint)

- No screen-wide red tint, no flashing/strobing anything — HMI guidance is
  explicit that flooding operators with color trains them to ignore alarms.
- No flag graphic, no saffron/white/green fill on panels or charts — only the
  one hairline + one small badge.
- No particle/steam background system beyond a near-invisible (~4% opacity)
  static-feeling diagonal drift — it needed to cost nothing and never compete
  with data.
- No new external assets: no Google Fonts, no icon font/CDN — every icon is
  inline SVG, system font stack unchanged, Plotly stays the only external
  script (cdnjs, pinned version, unchanged).
- Did not touch `MOCK`, `API_BASE`, `RANGES`, `P`, `mockSimulate`,
  `mockOptimize`, `apiSimulate`, `apiOptimize`, or the JSON shapes the real
  API is expected to return — only rendering/animation code changed.
