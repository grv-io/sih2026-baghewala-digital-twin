# Model Improvement Plan — Economics & Validation Layer

**Scope:** (a) a rupee/CO₂ economics layer (`twin/economics.py`) and (b) a benchmark-validation
suite (`tests/test_benchmarks.py`) for the Baghewala CSS+SRP digital twin (PS SIH26120).

**Status:** design document. No code was written or changed by this pass. Every number below
was either read out of the research pack (cited) or computed by running the *current* twin
(`.venv\Scripts\python.exe`, `params/field_params.json` as merged by the integration pass).

**Honesty labels used throughout** (same convention as `docs/research/baghewala_facts.md`):
`[CONFIRMED]` operator/peer-reviewed source · `[DERIVED]` our arithmetic from cited numbers
· `[TYPICAL]` industry value, not Baghewala-specific · `[UNSOURCED]` placeholder we must
replace or bracket · `[MEASURED-TWIN]` produced by running our own code today.

---

## 0. Executive answer — read this if you read nothing else

### 0.1 The recommended defensible headline

> **≈ 685 tonnes of steam — about 59,000 litres of diesel — not burned per optimised CSS
> cycle. That is ₹0.40–0.57 crore and 152 tonnes of CO₂ per cycle, on one well.
> Across the 19 CSS jobs Oil India ran in FY2025-26, ₹7.6–10.9 crore and 2,913 tCO₂ a year.**

**Do not say "₹0.61 crore/yr" and do not say "₹4 crore/yr."** Both are wrong, for two
*different* reasons, and the second is the dangerous one:

| Claim | What's wrong with it |
|---|---|
| ₹0.61 cr/yr (current dashboard) | Uses ₹1,300/t steam. Baghewala burns **HSD diesel**, not gas. Understates fuel cost ~6.5×. |
| ~₹4 cr/yr (naive fix) | Fixes the fuel price but keeps a **6.8 cycles/well/year** denominator that is physically impossible. Published CSS cycles are 6–18 months (Cold Lake); Baghewala banked **39 cycles in ~6.5 years across a 34-well field**. The fuel-price fix *multiplies* the denominator error by 6.5. |
| **₹0.40–0.57 cr per cycle** (recommended) | Denominator is one cycle — a unit the twin actually simulates and a judge can check. Scale-up to the field is a **separately labelled** multiplication by OIL's own published 19 CSS jobs. |

**Why per-cycle beats per-year:** the twin's `days_total` (53–61 d) is the *simulated* cycle
length, not a field cycle. Dividing 365 by it manufactures 6.8 cycles/year — a number no CSS
operation on earth achieves. Quoting per-cycle removes the fabricated denominator entirely and
lets the audience do the multiplication with a number *they* believe.

### 0.2 The fuel-price conflict is resolved, not bracketed

**₹8,400/t is right. ₹1,300/t is wrong for Baghewala.** The research pack settles it:

- `docs/research/baghewala_facts.md` §4 `[CONFIRMED]`: BGW-08 first-cycle parameters include
  **"HSD (high-speed diesel) fuel consumption: ~220 kg/hr"** against **~3,100 kg/hr of steam**
  (OIL internal operations deck, 12 Jul 2025). Baghewala's steam generators are **diesel-fired**.
  There is no gas supply to a remote Thar Desert location with no pipeline out
  (`baghewala_india_heavyoil_dossier.md` §2.3: crude leaves by *road tanker*).
- `[DERIVED]` 220/3,100 = **71 kg HSD per tonne of steam** = 85.5 L/t = **₹8,366/t** at the
  ₹97.8/L Rajasthan retail rate (`css_thermal_eor_deep_dive.md` §5.2; rounds to ₹8,400).
- `dashboard/index.html:1243` — `const STEAM_INR_PER_T = 1300;` — has **no source comment and
  no provenance anywhere in the repo.** It is roughly what *gas*-fired steam costs: the same
  research derives **US$11/t ≈ ₹970/t for natural gas at $4/MMBtu**, so ₹1,300/t is a
  gas-fired-plus-water-and-O&M number. Baghewala does not burn gas.

**The honest band to print is ₹5,900–8,400/t**, not because the fuel type is in doubt but
because ₹97.8/L is *pump price* and the research itself flags it as "an upper bound, since a
bulk industrial buyer pays less than pump price." Bulk HSD discount is `[UNSOURCED]` — so
present ₹8,400/t as the sourced figure and carry a −30% sensitivity (₹5,880/t) on the same
slide. Leading with the physical unit (tonnes of steam, litres of diesel) makes the headline
unfalsifiable and pushes the price uncertainty into a clearly-labelled conversion.

**One-line stage answer if challenged:** *"₹8,400 a tonne, because OIL's own deck says 220
kilos of high-speed diesel an hour for 3.1 tonnes of steam an hour. That's pump price and
they almost certainly buy in bulk, so we show minus-thirty-percent alongside. The dashboard
used to say ₹1,300 — that's a gas-fired number and there is no gas at Baghewala."*

### 0.3 Tier-1 items (do before the internal round)

| # | Item | Size | Sentence it buys |
|---|---|---|---|
| T1-1 | `twin/economics.py` — per-cycle ₹ + tCO₂ with sourced constants | **M** | *"Every result comes out in three units at once: barrels, rupees and kilos of CO₂."* |
| T1-2 | Kill `STEAM_INR_PER_T = 1300`; re-cut the dashboard headline to per-cycle | **S** | *"Our steam price is Oil India's own diesel burn, not a textbook number."* |
| T1-3 | `tests/test_benchmarks.py` Groups A + B + E (10 of the 16 tests) | **M** | *"Twenty-four unit tests prove the code is right; sixteen benchmark tests prove the *physics* is right against published field data."* |
| T1-4 | Write up the three benchmark tests that **currently fail** (§3.7) as a known-limitations slide | **S** | *"Here are the three places our twin does not yet match the literature, and what we'd fix first."* |
| T1-5 | CO₂ slide: intensity vs the 171–185 kgCO₂/bbl published band | **S** | *"Cutting SOR from 5 to 3 cuts cost and carbon by the same 40%. The economics slide and the sustainability slide are the same slide."* |
| T1-6 | Pull OIL's actual crude realization $/bbl from the May-2025 investor deck | **S** | *"We price the oil at Oil India's own reported realization, not at Brent."* |

### 0.4 Benchmark test count proposed

**16 benchmark tests** in `tests/test_benchmarks.py`, in five groups
(A viscosity ×4, B SOR ×4, C thermal ×3, D field behaviour ×3, E economics/CO₂ ×2).
**13 pass today; 3 fail** — and the three failures are the most valuable output of this
whole exercise (§3.7). Total suite after the pass: **24 unit + 16 benchmark = 40 tests.**

---

## 1. Economics module spec — `twin/economics.py`

### 1.1 Design principles

1. **Pure function of a `summary()` dict + a price scenario.** No I/O, no globals, no
   dependence on `cycle.py` internals. `economics(summary, prices) -> dict`. This keeps it
   testable in isolation and lets `tests/test_benchmarks.py` Group E drive it with synthetic
   SOR values (2/3/5/8) to reproduce the published cost table.
2. **Every constant carries `SOURCE:` and a label** in a comment on the line above it — the
   same discipline `twin/thermal.py` and `twin/ipr.py` already use for `# ASSUMPTION`.
3. **Physical units first, money second.** The module returns tonnes of steam, litres of
   diesel and tonnes of CO₂ *before* it returns rupees, so a price challenge never invalidates
   the physical claim.
4. **No annualisation inside the module.** `economics()` returns per-cycle values only. A
   separate, explicitly-named `scale_to_programme(per_cycle, n_cycles)` does the multiplication
   and *requires* the caller to pass `n_cycles` — so nobody can accidentally divide 365 by
   `days_total` again.

### 1.2 Constants block (copy this into the module verbatim)

```python
# ---------------------------------------------------------------- FLUID
# SOURCE: params/field_params.json fluid.api_gravity = 15.5 (merged from
#   SPE-23APOG-535203 "API 14-17", GEOHORIZONS 2015 "14-18"). [CONFIRMED]
# Standard API->SG:  SG = 141.5 / (131.5 + API)
OIL_SG                = 0.96259          # t/m3   [DERIVED from api_gravity 15.5]
BBL_PER_M3            = 6.28981          # exact  [DEFINITION] 1 bbl = 0.158987 m3
BBL_PER_TONNE_OIL     = 6.5343           # [DERIVED] BBL_PER_M3 / OIL_SG

# ---------------------------------------------------------------- STEAM FUEL
# SOURCE: OIL internal operations deck 12-Jul-2025, BGW-08 first cycle:
#   220 kg/hr HSD  ->  3,100 kg/hr steam.  [CONFIRMED-but-secondary]
#   (docs/research/baghewala_facts.md section 4)
HSD_KG_PER_T_STEAM    = 71.0             # [DERIVED] 220/3.1
HSD_DENSITY_KG_L      = 0.83             # [TYPICAL] high-speed diesel
HSD_L_PER_T_STEAM     = 85.54            # [DERIVED]
HSD_LHV_MJ_KG         = 42.6             # [TYPICAL] diesel lower heating value
GJ_PER_T_STEAM        = 3.02             # [DERIVED] 71 * 42.6 / 1000
#   cross-check: published band 2.6-4.0 GJ/t  ->  in band. GOOD.
#   SOURCE: https://thundersaidenergy.com/downloads/energy-needed-to-produce-steam-...

# ---------------------------------------------------------------- PRICES
# SOURCE: https://www.goodreturns.in/diesel-price-in-rajasthan-s28.html (Aug 2026)
#   This is RETAIL PUMP PRICE. A bulk industrial buyer pays less; the bulk
#   discount is [UNSOURCED], which is why sensitivity() runs -30%.
HSD_INR_PER_L         = 97.80            # [CONFIRMED - retail, upper bound]
INR_PER_USD           = 88.0             # [UNSOURCED - set from the demo-day rate]
# Crude realization: OIL publishes this quarterly. GO GET IT before the deck ships.
#   SOURCE TO FETCH: oil-india.com Investor Presentation / Analysts Meet transcript
#   Until then this is a PLACEHOLDER and must be printed as such on any slide.
CRUDE_REALIZATION_USD_BBL = 65.0         # [UNSOURCED - PLACEHOLDER]
HEAVY_OIL_DISCOUNT_USD_BBL = 10.0        # [UNSOURCED - PLACEHOLDER] 14-18 API sour,
#   trucked 600 km to ONGC North Santhal CTF then piped to IOCL Koyali; no pipeline
#   netback. SOURCE for the logistics chain: https://www.oil-india.com/rajasthan-fields

# ---------------------------------------------------------------- CO2
# SOURCE: IPCC default combustion factors via
#   https://greencalculus.com/data/ipcc-fuel-combustion-factors/
CO2_KG_PER_GJ_DIESEL  = 74.1             # [CONFIRMED]
CO2_KG_PER_GJ_GAS     = 56.1             # [CONFIRMED] - for the fuel-switch scenario
CO2_KG_PER_T_STEAM    = 223.8            # [DERIVED] 3.02 GJ/t * 74.1
#   cross-check A: 71 kg diesel * 3.17 kgCO2/kg diesel = 225 kg. AGREES.
#   cross-check B: research derives ~222 kg/t. AGREES to 1%.

# ---------------------------------------------------------------- WORKOVER
# SOURCE: https://ifactoryapp.com/... (SRP failure prediction) [TYPICAL]
#   Two published bands exist and they disagree by ~5x:
#     15,000-50,000 USD/event  (iFactory, general SRP)
#     90,000-270,000 USD/event (petropt.com, cited in digital_twin deep dive s.2)
#   We use the LOWER band. Using the higher one would inflate our benefit and
#   is not defensible for a 1,150 m onshore well with rig-less fishing precedent
#   at Baghewala itself (ResearchGate 398187378).
WORKOVER_USD_LOW      = 15_000           # [TYPICAL]
WORKOVER_USD_HIGH     = 50_000           # [TYPICAL]

# ---------------------------------------------------------------- LIFT POWER
# Grid/diesel-genset tariff for the SRP prime mover. [UNSOURCED] - Baghewala is
# off-grid desert; if genset-powered this should be a diesel number, not a tariff.
ELECTRICITY_INR_PER_KWH = 8.0            # [UNSOURCED - PLACEHOLDER]
```

### 1.3 Function signatures

```python
def cycle_economics(summary: dict, steam_t: float, prices: dict | None = None) -> dict:
    """Per-cycle rupee and CO2 accounting for one simulate_css_cycle() summary.

    Args:
        summary: output of twin.cycle.summary().
        steam_t: tonnes of steam injected this cycle (summary carries SOR and
            oil_total_m3 but the caller knows steam_t exactly; do not back it out
            of SOR, which is inf for a degenerate zero-oil cycle).
        prices: optional overrides for the PRICES block above.

    Returns (all per cycle, all floats):
        # --- physical (unfalsifiable; print these first) ---
        oil_m3, oil_t, oil_bbl
        steam_t, diesel_l, fuel_energy_GJ
        co2_t
        # --- intensity ---
        SOR_t_per_m3, sor_t_per_t          # t steam per tonne of oil, for world comparison
        co2_kg_per_bbl
        fuel_cost_inr_per_bbl, fuel_cost_usd_per_bbl
        # --- money ---
        fuel_cost_inr
        lift_energy_cost_inr               # energy_per_m3_kWh * oil_m3 * tariff
        workover_cost_inr_low/high         # failures_expected * WORKOVER_USD_*
        revenue_inr                        # oil_bbl * (realization - heavy discount) * fx
        net_value_inr                      # revenue - fuel - lift - workover(low)
```

```python
def versus_baseline(opt: dict, base: dict) -> dict:
    """Delta of two cycle_economics() results at EQUAL OIL (iso-oil counterfactual).

    This is the honest comparison and the one the headline must use. Comparing two
    cycles that produce different volumes of oil and calling the fuel-cost difference
    a 'saving' is wrong -- the optimised cycle burns MORE steam in absolute terms
    (1,600 t vs 1,500 t). The correct question is: how much steam would the BASELINE
    practice have burned to make the OPTIMISED cycle's oil?

        steam_counterfactual_t = opt.oil_m3 * base.SOR_t_per_m3
        steam_avoided_t        = steam_counterfactual_t - opt.steam_t

    Returns: steam_avoided_t, diesel_avoided_l, inr_avoided, co2_avoided_t,
             plus net_value_uplift_inr (the incremental-oil case, see honesty note).
    """
```

```python
def scale_to_programme(per_cycle: dict, n_cycles: int, label: str) -> dict:
    """Multiply a per-cycle result by an EXPLICIT cycle count.

    n_cycles is mandatory and unnamed defaults are forbidden. The only defensible
    values today are:
        19  -- CSS jobs OIL ran in FY2025-26 (BusinessToday, Apr 2026)  [CONFIRMED]
        11  -- CSS jobs in FY2024-25 (derived from '19 wells, ~72% higher') [DERIVED]
        39  -- cumulative CSS cycles to Jun-2025 (OIL deck) [CONFIRMED-secondary]
    NEVER 365 / summary['days_total'].
    """
```

```python
def sensitivity(summary, steam_t, base_prices) -> pandas.DataFrame:
    """3 x 3 grid: fuel price {-30%, base, +30%} x crude {-20%, base, +20%}."""
```

### 1.4 Worked numbers on the two baked demo cycles `[MEASURED-TWIN + DERIVED]`

Run at `params/field_params.json` as merged. Reference = 1,500 t / 7 d / 3.0 m³/d / 8.0 spm;
Optimised = 1,600 t / 3 d / 8.0 m³/d / 10.0 spm.

| Quantity | Reference | Optimised (as applied) |
|---|---:|---:|
| oil | 1,158.96 m³ · 7,289 bbl | 1,765.63 m³ · 11,106 bbl |
| SOR | 1.2943 t/m³ | 0.9062 t/m³ |
| steam | 1,500 t | 1,600 t |
| diesel | 128,300 L | 136,900 L |
| fuel energy | 4,530 GJ | 4,832 GJ |
| **fuel cost @ ₹97.8/L** | **₹1.255 cr** | **₹1.339 cr** |
| fuel cost per bbl | ₹1,722 (US$19.6) | ₹1,205 (US$13.7) |
| **CO₂** | **335.7 t** | **358.1 t** |
| **CO₂ intensity** | **46.1 kg/bbl** | **32.2 kg/bbl** |
| lift energy | 23,857 kWh → ₹1.9 L | 24,364 kWh → ₹1.9 L |
| `failures_expected` | 0 → ₹0 workover | 0 → ₹0 workover |

**Iso-oil counterfactual (the headline calculation):**

```
steam the baseline would have burned for 1,765.63 m3 =  1,765.63 x 1.2943 = 2,285.2 t
steam the optimised cycle actually burns                                  = 1,600.0 t
                                                                            ---------
steam avoided                                                             =   685.2 t
diesel avoided        685.2 x 85.54 L/t                                   = 58,613 L
INR avoided           58,613 x 97.80                                      = Rs 0.573 cr
CO2 avoided           685.2 x 0.2238 t/t                                  =   153.3 t
% steam per barrel    1 - 0.9062/1.2943                                   =   30.0 %
```

Cross-check against the published target: SPE-185716-MS reports optimisation delivering
**">20% SOR reduction"** in mature CSS fields. Our 30% is *above* that benchmark — say so, and
say it is above it, with the surrogate's ±0.31 t/m³ MAE band attached. Do not present 30% as
a hard number.

### 1.5 Sensitivity table design (put this on the slide, not in an appendix)

Rows = fuel price, columns = crude realization. Cell = **₹ crore of diesel avoided per cycle**
(the headline metric — it depends only on fuel price, so the crude columns are flat) *and*
**net-value uplift ₹ crore/cycle** (which moves with both). Two numbers per cell, stacked.

| ₹ avoided/cycle · net uplift/cycle | crude −20% ($44/bbl net) | crude base ($55/bbl net) | crude +20% ($66/bbl net) |
|---|---:|---:|---:|
| **fuel −30%** (₹68.5/L, ₹5,856/t) | ₹0.40 cr · ₹1.42 cr | ₹0.40 cr · ₹1.79 cr | ₹0.40 cr · ₹2.16 cr |
| **fuel base** (₹97.8/L, ₹8,366/t) | ₹0.57 cr · ₹1.39 cr | ₹0.57 cr · ₹1.76 cr | ₹0.57 cr · ₹2.13 cr |
| **fuel +30%** (₹127.1/L, ₹10,876/t) | ₹0.75 cr · ₹1.37 cr | ₹0.75 cr · ₹1.74 cr | ₹0.75 cr · ₹2.11 cr |

Base net realization = $65 − $10 heavy discount = **$55/bbl = ₹4,840/bbl** at ₹88/$; crude
±20% moves the *net* figure. Net uplift = 3,817 incremental bbl × net realization, minus the
₹0.084 cr of extra fuel the optimised cycle burns (1,600 t vs 1,500 t) and ~₹0.004 cr of extra
lift energy.

Two things a judge will notice, and you should point out before they do:

1. **The net-value uplift (₹1.4–2.2 cr/cycle) is 3–4× the steam saving (₹0.40–0.75 cr).**
   That is because most of the value is *incremental oil*, not avoided fuel. But incremental
   oil is the *less* defensible claim (it rides on the surrogate's R²=0.72), so **lead with
   the steam saving and show the net uplift as the labelled upside.** Inverting that order is
   how teams get caught.
2. **The steam saving is insensitive to crude price and the net uplift is insensitive to fuel
   price.** That is a feature: the recommendation is robust to both. Say it out loud.

### 1.6 The fuel-switch scenario (one extra row, big payoff)

`css_thermal_eor_deep_dive.md` §5.2 `[DERIVED]`: at 3.0 GJ/t, natural gas at $4/MMBtu gives
**~US$11/t of steam vs ~US$95/t for diesel — 8× cheaper**, and CO₂ falls from 74.1 to
56.1 kg/GJ (−24%). Add a single `fuel="gas"` scenario to `economics.py` and one slide line:

> *"The biggest single cost lever at Baghewala isn't SOR — it's the fuel. Switching the steam
> generators off diesel would cut steam cost roughly 8× and CO₂ per tonne of steam by 24%.
> We can't build a gas pipeline; we can cut the tonnes. So SOR optimisation is lever number
> two, and it's the one that's available this quarter."*

Admitting that the biggest lever is one you don't control reads as rigour, not weakness — and
`sih_winning_playbook.md` §3 explicitly notes that "admitting an unknown scores better than
guessing."

---

## 2. CO₂ / sustainability layer

### 2.1 Why this is a scored item, not a nice-to-have

`sih_winning_playbook.md` §1.2 `[CONFIRMED]` quotes the official rubric verbatim:

> *"Evaluation criteria will include novelty of the idea, complexity, clarity and details in
> the prescribed format, feasibility, practicability, **sustainability**, scale of impact,
> user experience and potential for future work progression."*

There are **no published weightages** — so every named criterion should be assumed equal. The
playbook's own warning: *"A physics+ML digital twin deck naturally over-indexes on
novelty/complexity and under-indexes on UX and post-hackathon continuation. Fix that
deliberately."* Sustainability is in the same bucket. A twin that emits a tCO₂ number per
recommendation converts an under-served rubric line into a scored one for ~30 lines of code.

### 2.2 The core physics claim (this is the whole slide)

> **Steam generation is the largest source of carbon emissions in in-situ thermal recovery,
> and steam-oil ratio explains about 60% of the variance in SAGD assets' emissions.**
> (Sources: cer-rec.gc.ca market snapshot; thundersaidenergy.com oil-sands CO₂ intensity)

Therefore **SOR is a carbon KPI, not just a cost KPI**, and the optimiser we already built is
a decarbonisation tool without changing a line of it. That is the cheapest sustainability
story available to any team on this problem statement, and it is fully sourced.

### 2.3 Intensity ladder — our SORs against the published band

`CO₂ kg/bbl = SOR (t steam / m³ oil) × 223.8 (kg CO₂ / t steam) ÷ 6.28981 (bbl / m³)`
= `SOR × 35.58`.

| Case | SOR (t/m³) | kg CO₂/bbl | Source / label |
|---|---:|---:|---|
| Oil sands Scope 1&2, published | — | **185** | thundersaidenergy `[CONFIRMED]` |
| Research pack, diesel steam @ SOR 5 | 5.0 | **171** | css deep dive §5.3 `[DERIVED]` |
| Cold Lake CSS, typical (SOR ≈ 4) | 4.0 | **142** | derived at our factor `[DERIVED]` |
| Liaohe Block D, late life (3.56) | 3.56 | **127** | derived at our factor `[DERIVED]` |
| Research pack @ SOR 3 | 3.0 | **102** | css deep dive §5.3 `[DERIVED]` |
| Global oil & gas industry average | — | **60** | thundersaidenergy `[CONFIRMED]` |
| **Our twin — reference cycle** | 1.294 | **46.1** | `[MEASURED-TWIN]` |
| **Our twin — optimised cycle** | 0.906 | **32.2** | `[MEASURED-TWIN]` |
| Fuel switch to gas @ our optimised SOR | 0.906 | **24.4** | `[DERIVED]` ×56.1/74.1 |

**⚠ Read the table honestly and say the caveat out loud.** Our modelled intensity (32–46
kg CO₂/bbl) is **below the global industry average of 60 kg/bbl** — i.e. we are claiming
Baghewala CSS is cleaner than the average conventional barrel worldwide. That is
not credible on its face and a judge from OIL will say so. Three things must be on the slide:

1. **Scope.** Our number is **Scope 1, steam generation only.** The published 185 kg/bbl is
   **Scope 1&2 for a full oil-sands operation.** Not like-for-like. We are missing: SRP prime-mover
   power, water treatment, the ~600 km road haul to ONGC North Santhal, tank heating for
   flow assurance, flaring and fugitives.
2. **Our SOR sits at the very bottom of the world band** (§3.3, test B1 passes by 0.007) — 0.9–1.3 at the demo set-points vs a published CSS
   life-cycle average near 6. Until that is reconciled, the intensity number inherits the
   same doubt. **Present 46 kg/bbl as a lower bound and 142 kg/bbl (at Cold Lake's SOR 4) as
   the upper bound**, and say which one you'd bet on.
3. **The delta is more robust than the level.** Whatever the absolute intensity is, a 30% SOR
   cut is a 30% CO₂ cut, because our CO₂ is strictly linear in steam tonnage. **Sell the
   delta, hedge the level.**

**One term nobody else will have thought of — add it, it's a differentiator.** Baghewala has
no pipeline: crude is steam-heated in tanks and trucked ~600 km in bowsers to Mehsana
(`dossier` §2.3 `[CONFIRMED]`). `[DERIVED, TYPICAL inputs]` a 25 t tanker at ~35 L/100 km
loaded burns ~210 L for 600 km = 8.4 L/t oil = **~3.4 kg CO₂/bbl of trucking emissions** on
top of the steam number, plus the tank-heating steam. It is small, but naming it is the
single most "we actually looked at this field" sentence in the sustainability section.

### 2.4 The "SOR cut = emissions cut" slide math (put these four lines on the slide)

```
1 tonne of steam at Baghewala  =  71 kg HSD  =  3.02 GJ  =  224 kg CO2      [DERIVED]
Cut SOR 1.29 -> 0.91 t/m3      =  -30% steam per barrel  =  -30% CO2/bbl    [LINEAR]
Per optimised cycle            =  685 t steam avoided    =  153 tCO2        [DERIVED]
Across FY26's 19 CSS jobs      =  13,019 t steam avoided =  2,913 tCO2/yr   [SCENARIO]
```

Context sentence for the last line: 2,913 tCO₂ is roughly the annual footprint of **630 Indian
passenger cars** `[DERIVED, TYPICAL]` at ~4.6 tCO₂/car/yr — use a comparison only if you can
source the per-car figure, otherwise drop it. The tonnage alone is fine.

### 2.5 Policy tie-in (free points on "scale of impact" and "future work")

`dossier` §4.3 `[CONFIRMED]`: the 2 Jan 2018 EOR/IR/UHC policy gives **50% cess waiver,
75% gas royalty waiver, 150% tax deduction on ER pilots** — and **mandates screening and a
pilot before commercial ER rollout**. A validated twin *is* the screening-and-pilot-design
instrument the policy demands. That converts our deliverable from "a demo" into "a compliance
asset", which is the answer to the rubric's *"potential for future work progression"* line.

---

## 3. Benchmark validation suite — `tests/test_benchmarks.py`

### 3.1 What this file is and is not

The existing 24 tests in `tests/` are **unit tests**: they check that the code does what the
code says (monotonicity, bounds, key presence, reference-point recovery). Not one of them
checks whether the *physics matches the real world*. `test_cold_viscosity_is_thousands_of_cP`
was even relaxed to a relative band during integration precisely because it had been asserting
against a placeholder.

`tests/test_benchmarks.py` is a **separate file with a separate purpose**: every test asserts
our twin reproduces a **published, cited number**, and every assertion carries the source URL
in its docstring. Mark them all `@pytest.mark.benchmark` so `pytest -m "not benchmark"`
still gives a fast unit run.

**Design rule: a benchmark test that fails is not a bug to be silenced by widening the
tolerance.** It is either a physics finding or a data finding, and it gets written up. Three
of the sixteen fail today (§3.7). That is the point.

### 3.2 Group A — Fluid physics vs ASTM D341 / Walther (4 tests)

`twin/viscosity.py` implements **Andrade** (`μ = A·exp(B/T_K)`), fitted through 11,500 cP @
50 °C and a hardcoded 50 cP @ 150 °C anchor. The research is explicit
(`css_thermal_eor_deep_dive.md` §2.6) that the industry standard is **Walther / ASTM D341**
(`log₁₀ log₁₀(ν + 0.6) = A − B·log₁₀ T`) and that "the simpler Andrade form … under-predicts
the collapse over the 50 → 300 °C span CSS actually covers." These tests quantify that gap.

| # | Test | Assertion | Tolerance | Source |
|---|---|---|---|---|
| A1 | `test_andrade_tracks_walther_over_css_span` | Fit a Walther/D341 line through the *same two anchors* (11,500 cP @50 °C, 50 cP @150 °C, converted cSt↔cP via `OIL_SG`); compare μ(T) at T = 60, 75, 100, 125 °C | agree within **factor 3** inside the anchor span (50–150 °C); **report, don't assert**, the extrapolated 150–290 °C gap | ASTM D341; css deep dive §2.6 |
| A2 | `test_viscosity_collapse_is_two_to_three_decades` | μ(50 °C)/μ(150 °C) | **100× ≤ ratio ≤ 1000×** | CSI field study 5→600 cP over 304→54 °C = 120× (upcoglobal); our own 230× |
| A3 | `test_mu_at_50C_matches_OIL_published_band` | μ(50 °C) | **8,000 ≤ μ ≤ 15,000 cP**, and warn if outside OIL's own **10,000–13,000** | SPE-23APOG-535203; oil-india.com/rajasthan-fields |
| A4 | `test_model_rejects_generic_API_correlation` | μ(50 °C) ÷ 123 cP (generic 18° API) | **ratio ≥ 50** | EngineeringToolBox contrast, `baghewala_facts.md` §6 |

A4 looks trivial but is the single best "we understood this field" test in the suite. It
encodes the field's signature anomaly — *born-heavy, non-biodegraded, Type II-S kerogen,
API decoupled from viscosity* — as an executable assertion. Quote it on stage.

**A5 (deliberately not written):** a test against a *measured* Baghewala μ–T curve. We have
exactly one measured point (11,500 cP @ 50 °C). The 150 °C anchor is
`ANCHOR_MU_CP = 50.0`, a SPEC placeholder. **Say this.** The most valuable single data request
to OIL is a two-point lab viscosity measurement at 100 °C and 200 °C.

### 3.3 Group B — SOR against world CSS benchmarks (4 tests)

| # | Test | Assertion | Tolerance | Source |
|---|---|---|---|---|
| B1 | `test_median_SOR_over_design_space_in_world_band` | median SOR over `data/synthetic_cycles.csv` (n=3,000 LHS) | **2.0 ≤ median ≤ 6.0** — **today: 2.007, passes by 0.007.** Treat as amber, not green | SPEC 2–6; CSS life-cycle avg ≈6, "efficient" <3 (`baghewala_facts.md` §6) |
| B2 | `test_SOR_never_beats_best_published_project` | min SOR over the design space | **≥ 0.147 t/m³** (Bolívar Coast best OSR 6.8 → SOR 0.147) and max ≤ 8.0 at sensible settings | SPE-150283-MS |
| B3 | `test_optimum_steam_slug_implies_field_injection_duration` | the `steam_t` minimising SOR, ÷ 74 tpd | implied injection **13–24 days**, bracketing Baghewala's published **14–21 d** | OIL deck, `baghewala_facts.md` §4 |
| B4 | `test_CSS_attributable_share_of_field_output_is_plausible` | (74 tpd × 365 ÷ SOR_opt) × `OIL_SG` ÷ 43,773 t | **5% ≤ share ≤ 40%** | OIL deck 3,100 kg/h; BusinessToday Apr-2026 FY26 output |

**B4 is the most powerful test in the suite** and deserves its own slide. The arithmetic:

```
Field steam capacity   3,100 kg/h  =  74.4 t/d  x 365  =  27,156 t steam/yr  (100% uptime)
At a world-normal CSS SOR of 4 t/m3, that supports    =   6,789 m3  = 6,535 t oil/yr
FY2025-26 actual field production                     =                43,773 t oil/yr
                                                                        ------------
=> CSS can account for AT MOST ~15% of Baghewala's output at a world-normal SOR.
```

This is a genuine, defensible, *new* insight the research pack does not state anywhere, and it
resolves the apparent tension between tests B1 and B4: **Baghewala's oil is overwhelmingly not
steam-driven.** One 74 tpd skid, 39 cycles in ~6.5 years, 19 CSS jobs in FY26 against 34
producing wells — most wells, most of the time, produce cold or with EDH/diluent assistance.
CSS is the *incremental* 10–20%, which is exactly why allocating the scarce 74 tpd correctly
is the highest-value decision on the field. **This strengthens the pitch, it does not weaken
it.** Stage line:

> *"Oil India has one 74-tonne-a-day steam skid for a 34-well field. At Cold Lake's steam-oil
> ratio that steam can only account for about 15% of Baghewala's barrels. Steam isn't the
> production system here — it's the scarcest, most expensive input in it. Which well gets
> Monday's slug is a ₹8,400-a-tonne decision, and right now it's made on experience. That's
> the decision our twin is built for."*

### 3.4 Group C — Marx–Langenheim thermal core (3 tests)

The research doc carries **no textbook worked example with numbers**, so C3 uses the closed
form itself as the oracle — which is legitimate and rigorous, because `_heat_loss_efficiency`
is a *numerical implementation* of an analytic expression and can be checked against
independently-computed `erfc` values.

| # | Test | Assertion | Tolerance | Source |
|---|---|---|---|---|
| C1 | `test_ML_efficiency_matches_closed_form` | `_heat_loss_efficiency(t_D)` at t_D ∈ {0.01, 0.1, 1, 10, 100} vs values computed independently from `F(t_D) = e^{t_D}erfc(√t_D) + 2√(t_D/π) − 1` | **rtol 1e-9** | Marx & Langenheim, *Pet. Trans. AIME* 216 (1959) 312–315 |
| C2 | `test_ML_efficiency_bounds_and_monotonicity` | 0 < E_h ≤ 1; strictly decreasing in t_D; E_h → 1 as t_D → 0 | exact | same |
| C3 | `test_heated_radius_is_a_near_wellbore_bubble` | heated radius after a full 1,500 t injection | **3 m ≤ r ≤ 30 m** | CSS heats "around each well individually"; `DRAINAGE_RADIUS_M = 8.0` |

Reference values for C1, computed today `[MEASURED-TWIN, verified against the closed form]`:

| t_D | E_h |
|---:|---:|
| 0.01 | 0.929489667868 |
| 0.10 | 0.804032617082 |
| 1.00 | 0.555962743251 |
| 10.0 | 0.273882595063 |
| 100. | 0.103399326637 |

C3 today: **r = 7.20 m** at 1,500 t `[MEASURED-TWIN]` — passes, and note it is just inside
`DRAINAGE_RADIUS_M = 8.0 m`, i.e. the heated zone is at 81% of the drainage area at the
reference slug. That saturation is exactly the mechanism that gives the SOR interior optimum,
so C3 is also a regression guard on the retuned constant.

### 3.5 Group D — cycle behaviour vs published field data (3 tests)

| # | Test | Assertion | Tolerance | Source |
|---|---|---|---|---|
| D1 | `test_first_cycle_uplift_matches_BGW8_pilot` | peak produce rate ÷ cold unstimulated rate | **5× ≤ uplift ≤ 20×** | BGW-8 pilot **5–6×** uplift (Scribd/OIL, `baghewala_facts.md` §4) |
| D2 | `test_single_well_rate_inside_field_envelope` | peak produce rate | hard: **< 191 m³/d** (whole field's 1,202 bbl/d record); soft: **≤ 28 m³/d** (5× the FY26 per-well average of 35 bbl/d) | oil-india.com; BusinessToday Apr-2026 |
| D3 | `test_SOR_drifts_up_under_depletion_Liaohe_pattern` | run the cycle at `P_initial_kPa` = 7,400 → 2,900 (Liaohe Block D's measured decline) and assert SOR **rises**, by roughly the Liaohe magnitude (2.86 → 3.56, **+24%**) | direction must be correct; magnitude within **±15 pp** | SPE 18HOCE D021S009R002 |

D3 note on method: `twin/cycle.py` has **no cycle-to-cycle state** — every call starts from
`P_initial_kPa` and there is no material balance. So the test cannot run "multi-cycle" in the
literal sense. Instead it drives the *published* Liaohe pressure trajectory in externally and
checks the twin's response has the right sign and rough magnitude. That is the honest,
runnable version of the test, and the write-up says so.

### 3.6 Group E — economics module self-consistency (2 tests)

These lock `twin/economics.py` to the research pack's own cited tables, so a later constant
edit cannot silently move the headline.

| # | Test | Assertion | Tolerance | Source |
|---|---|---|---|---|
| E1 | `test_CO2_per_bbl_reproduces_published_intensity_at_SOR5` | `cycle_economics` fed a synthetic SOR = 5 diesel case | **165 ≤ kg CO₂/bbl ≤ 180** (research derives 171; oil-sands published 185) | css deep dive §5.3; thundersaidenergy |
| E2 | `test_steam_fuel_cost_per_bbl_reproduces_research_table` | $/bbl at SOR = 2, 3, 5, 8 | within **±5%** of **29 / 44 / 73 / 117 US$/bbl** | css deep dive §5.2 `[DERIVED]` table |

E2 is worth its weight at the finale: it means the number on our slide and the number in the
literature are produced by *the same executable code path*, and we can say so.

### 3.7 The three tests that fail today — and why that is the best slide in the deck

I ran the current twin against every assertion above. **13 of 16 pass. Three fail.** Each
failure is a real, specific, fixable finding. Write them up; do not hide them.

---

**FAIL 1 — D1: first-cycle uplift is 135×, published is 5–6×.** `[MEASURED-TWIN]`

```
cold, unstimulated:  mu = 11,500 cP  ->  q =  0.554 m3/d
peak of produce phase (post-soak):        q = 74.96 m3/d   =  471 bbl/d
uplift = 135x    (published BGW-8 pilot: 5-6x)
```

Root cause chain, traced:
1. `viscosity.py` Andrade extrapolates to **0.63 cP at 290 °C** — thinner than liquid water
   at 25 °C (0.89 cP). Physically the oil viscosity should floor around 0.3–1 cP, and this
   is exactly the over-extrapolation the research warned about for Andrade vs Walther.
2. `ipr.py` `mobility_factor = mu_ref/mu` is **unbounded** → 11,500/0.63 = **18,200×** at peak.
   Real reservoirs do not deliver linear mobility gain across four orders of magnitude:
   relative permeability, skin and near-well pressure support all bind first.
3. `AOF_REF_M3D` was retuned 1.0 → 0.7 during integration to fight this, but even so
   0.7 × 0.792 × 18,200 = **10,090 m³/d** of "reservoir potential" before the pump caps it.

**Consequence — and this is the important part: at the demo set-points the twin is
effectively a pump-capacity model with a thermal on/off switch.** The reservoir term is
saturated for most of the produce phase, so the sucker-rod pump alone sets the rate.

**Fix (physics agent, M):** cap `mobility_factor` (e.g. at 200–500×, a defensible relative-
permeability/skin-limited ceiling), and/or floor `viscosity.mu_cP` at ~0.5 cP, and re-tune
`AOF_REF_M3D` upward so the cold rate stays realistic. Then re-bake the dashboard.

---

**FAIL 2 — D2 (soft bound): peak single-well rate is 471 bbl/d against a 34-well field
record of 1,202 bbl/d.** `[MEASURED-TWIN]`

One well would be 39% of the entire field's best-ever day. The hard bound (< 191 m³/d) passes;
the calibration bound (≤ 28 m³/d = 5× the FY26 per-well average) fails by 2.7×.

Second root cause, independent of FAIL 1 — **the SRP is spec'd far too large:**

```
plunger_d_m 0.057 (2.25")  x  stroke_m 3.0 (118")  x  8 spm  x  1440  x  0.85 eff
                                                             =  75 m3/d  =  471 bbl/d
```

`params/field_params.json` `srp` block is entirely `[TYPICAL]` fill —
`baghewala_facts.md` §5 states plainly: *"No Baghewala-specific SRP mechanical spec (stroke
length, SPM, plunger diameter, rod grade) was found in any public source."* A **3.0 m (118")
stroke** is a very large pumping unit; FY26's per-well average is ~35 bbl/d.

**Fix (S):** bring `stroke_m` and `plunger_d_m` down to a heavy-oil-appropriate spec
(e.g. 1.7–2.5 m stroke, 1.5–1.75" plunger) and label them `[TYPICAL - not Baghewala]` in the
UI. This is the **highest-value data request to OIL**, alongside the μ–T curve.

---

**FAIL 3 — D3: the twin cannot reproduce SOR drift under depletion, because reservoir
pressure has *no effect at all* on oil rate.** `[MEASURED-TWIN]`

```
P_initial_kPa    11,400   9,000   7,400   5,000   2,900
SOR (t/m3)        1.294   1.294   1.294   1.294   1.294     <- IDENTICAL
oil_total_m3      1,159   1,159   1,159   1,159   1,159
```

Root cause: `cycle.py` sets `P_wf = PWF_DRAWDOWN_FRACTION * P_res` with a **fixed fraction of
0.4**, so `ipr.py`'s `pr_ratio = P_wf/P_res` is *always exactly 0.4* and the Vogel shape factor
is constant. **Reservoir pressure algebraically cancels out of the rate equation.**
`P_initial_kPa = 11,400` — one of the headline "real field values" the integration pass merged
from the research — is currently an **inert parameter**. It appears on the dashboard and
changes nothing.

This is the finding a petroleum-engineer judge is most likely to find on their own, and it is
the one that would hurt most if they found it first.

**Fix (physics agent, M):** make `P_wf` an *absolute* pump-intake pressure derived from pump
submergence and fluid gradient (which the module already has: `rod_length_m`,
`_fluid_density_kgm3`), not a fraction of `P_res`. Then reservoir pressure becomes live, the
Liaohe drift test becomes runnable, and a per-cycle material-balance depletion term becomes
meaningful — which is the prerequisite for the multi-cycle "when does CSS stop paying" stop
signal that `css_thermal_eor_deep_dive.md` §6 Q5 says is the twin's core deliverable.

---

**How to present all three (this is the slide, and it is a strength):**

> *"We wrote sixteen benchmark tests against published field data. Thirteen pass. Three fail,
> and we can tell you exactly why each one fails and what we'd change. The one we care most
> about: reservoir pressure currently cancels out of our inflow equation, so we can't yet
> reproduce the Liaohe SOR drift. We found that because we wrote the test, not because
> somebody asked. That's the difference between a demo and a twin."*

`sih_winning_playbook.md` §3 `[REPORTED]`: *"Admitting an unknown scores better than
guessing"* and evaluators score **visible advancement between visits**, comparing against
their own last note. A named, diagnosed, scoped failure that is fixed between visit 2 and
visit 3 is worth more than a suite that was green from the start.

---

## 4. The "validation story" — slide and talk track

### 4.1 The maturity ladder, mapped to DNV-RP-A204

`digital_twin_oilfield_deep_dive.md` §1.3 `[CONFIRMED]` gives DNV's six capability levels.
Map our evidence onto them — this is the slide.

| DNV level | What DNV requires | Our evidence today | Status |
|---|---|---|---|
| **0** Standalone | Virtual model, no live data | Marx–Langenheim + Boberg-style thermal decay, Andrade viscosity, Vogel IPR, API RP 11L rod loads — **24/24 unit tests** | ✅ done |
| **1** Descriptive | Live data updates the model | Dashboard + `/simulate` API render full cycle state; **no live SCADA link** (stated on the provenance chip) | ⚠ architecture done, feed not connected |
| **2** Diagnostic | Detects faults, troubleshoots | `floating_index` + `failures_expected`; rod-floating classifier **AUC 0.9989** | ✅ done |
| **3** Predictive | Prognostics, early warning | SOR surrogate **R² 0.72, MAE 0.31** on n=3,000; forward SOR for the *proposed* slug | ✅ done |
| **4** Prescriptive | Recommends via what-if + risk | `ml/optimize.py` ranked set-points with an uncertainty band and a floating-risk constraint (p=0.0011 vs limit 0.3); two-stage audited Apply | ✅ **the SIH deliverable** |
| **5** Autonomous | Acts on its own prescriptions | Deliberately **not built** — read-from-OT-only, human-gated advisory channel | 🎯 roadmap, gated on acceptance rate |

Say the line the research recommends verbatim: **"We are targeting DNV Level 4 (prescriptive)
for the hackathon build, with a documented path to Level 5."**

### 4.2 The four rungs of evidence (the actual talk track — 60 seconds)

> **"Four things stand behind every number on this screen.**
>
> **One — twenty-four unit tests.** The code does what the code says: viscosity falls
> monotonically with temperature, the Marx–Langenheim heat-loss efficiency is bounded and
> decaying, rod load is positive and plausible, SOR has an interior optimum in steam volume.
> Those prove the implementation.
>
> **Two — sixteen benchmark tests.** These are different. Every one asserts against a
> *published* number with the citation in the docstring: our viscosity curve against ASTM
> D341, our steam-oil ratio against Cold Lake and Liaohe and the Bolívar Coast, our CO₂ per
> barrel against the 171–185 kilo band, our optimal slug size against Baghewala's own
> fourteen-to-twenty-one-day injection. Thirteen pass. Three fail, and here they are —
> [FAIL 1/2/3 slide]. Those prove the *physics*, and where it doesn't hold yet.
>
> **Three — the surrogate agrees with the physics to one-point-two percent** on the demo
> scenario, at sixty-times the speed. That is what makes optimisation possible at all: a full
> thermal simulation is hours; the decision has to be made this week.
>
> **Four — the assimilation loop we have not built yet.** Give us one CSS cycle of Oil India's
> actual injection and production history and every one of those constants stops being a
> literature value and becomes a fitted one. That's the graduation gate from Level 3 to
> Level 4, and it's the only thing standing between this and a field deployment.
>
> **Twenty-four plus sixteen plus one-point-two percent plus a named next data request.
> That's the validation story."**

### 4.3 The three numbers to have ready for cross-examination

| If they ask | Say |
|---|---|
| *"How do you know your SOR is right?"* | *"We don't — Baghewala's achieved SOR has never been published, and we say so. What we do know is the physical constraint: one 74-tonne-a-day skid, 43,773 tonnes of oil in FY26. At Cold Lake's SOR that steam accounts for at most 15% of the field. Our model sits below the world band and we've flagged that as an open calibration item, not buried it."* |
| *"Your CO₂ per barrel is lower than the industry average. Really?"* | *"Scope 1, steam only — the 185 figure is Scope 1 and 2 for a whole oil-sands operation. Not like-for-like, and we're missing lift power, water treatment and 600 km of road haul. Sell the delta, not the level: whatever the baseline is, a 30% SOR cut is a 30% cut, because our CO₂ is strictly linear in steam tonnage."* |
| *"Where did ₹8,400 a tonne come from?"* | *"Oil India's own operations deck: 220 kilos of high-speed diesel an hour for 3.1 tonnes of steam an hour. Seventy-one kilos of diesel per tonne of steam, 86 litres, at ₹97.8 a litre in Rajasthan. That's pump price and they buy in bulk, so we run minus-thirty percent alongside it."* |

---

## 5. Tier ranking

Sizes: **S** ≤ 2 h · **M** ½–1 day · **L** > 1 day. "Owner" is the natural agent, not a person.

### Tier 1 — before the internal round (the deck and the demo both need these)

| # | Item | Size | Owner | Pitch sentence gained |
|---|---|---|---|---|
| 1.1 | `twin/economics.py` — constants block + `cycle_economics()` + `versus_baseline()` + `scale_to_programme()` | **M** | econ | *"Every result comes out in barrels, rupees and kilos of CO₂ at the same time — because at diesel-fired steam prices those three numbers move together."* |
| 1.2 | Delete `STEAM_INR_PER_T = 1300`; wire the dashboard's value cell to per-cycle ₹ and tCO₂ with the fuel band printed | **S** | dashboard | *"Our steam price is Oil India's own diesel burn — 220 kilos an hour for 3.1 tonnes of steam — not a textbook number."* |
| 1.3 | `tests/test_benchmarks.py` Groups A, B, E (10 tests) | **M** | physics/test | *"Sixteen tests that assert against published field data, each with its citation in the docstring."* |
| 1.4 | Known-limitations slide from §3.7 (the three failing tests, diagnosed) | **S** | deck | *"Three of our benchmark tests fail. We found them because we wrote them. Here's the root cause of each."* |
| 1.5 | Sustainability slide: intensity ladder + the four-line SOR=CO₂ math + the scope caveat | **S** | deck | *"The economics slide and the sustainability slide are the same slide — SOR explains about 60% of thermal-EOR emissions variance."* |
| 1.6 | Fetch OIL's published crude realization $/bbl from the May-2025 investor deck; replace the placeholder | **S** | research | *"We price the barrel at Oil India's own reported realization, not at Brent."* |
| 1.7 | **FAIL 3 fix** — `P_wf` as absolute pump-intake pressure, not a fixed fraction of `P_res` | **M** | physics | *"Reservoir pressure is a live variable in our inflow model, which is what lets us reproduce the Liaohe depletion pattern."* |

### Tier 2 — before the finale

| # | Item | Size | Owner | Pitch sentence gained |
|---|---|---|---|---|
| 2.1 | `tests/test_benchmarks.py` Groups C, D (6 tests) incl. the Liaohe drift test, now runnable after 1.7 | **M** | physics/test | *"Our twin reproduces the published Liaohe pattern — steam-oil ratio drifting from 2.86 to 3.56 as pressure fell from 7.4 to 2.9 MPa."* |
| 2.2 | **FAIL 1 fix** — mobility-ratio ceiling + viscosity floor; re-tune `AOF_REF_M3D`; re-bake dashboard | **M** | physics | *"Our first-cycle uplift matches BGW-8's published five-to-six-times, because we cap mobility gain the way relative permeability actually does."* |
| 2.3 | **FAIL 2 fix** — right-size the SRP spec; label every `[TYPICAL]` param in the UI | **S** | physics/dashboard | *"Every parameter on this screen is colour-coded: measured at Baghewala, derived, or industry-typical. Eleven are typical, and here's the list we'd like from you."* |
| 2.4 | Sensitivity grid (§1.5) rendered live in the dashboard, not baked | **M** | dashboard | *"Move the diesel price and the crude price; the recommendation doesn't change. That robustness is the actual result."* |
| 2.5 | Walther/ASTM D341 viscosity as an alternative model behind a flag, with A1 comparing both | **M** | physics | *"We use the ASTM D341 double-log law that the industry uses, and we can show you the gap against the simpler Andrade form our first cut used."* |
| 2.6 | Fuel-switch scenario (gas vs diesel) as a one-click comparison | **S** | econ | *"The biggest cost lever isn't SOR — it's the fuel, eight times over. We can't build you a pipeline; we can cut the tonnes."* |
| 2.7 | Trucking + tank-heating CO₂ terms (600 km to Mehsana) added to the intensity total | **S** | econ | *"There's no pipeline out of Baghewala. We count the 600 kilometres of road haul in the carbon number, because it's real."* |

### Tier 3 — pilot / post-hackathon

| # | Item | Size | Owner | Pitch sentence gained |
|---|---|---|---|---|
| 3.1 | Multi-cycle state: per-cycle material-balance depletion + near-well permeability re-estimated from observed injectivity | **L** | physics | *"The twin carries state between cycles, so it can tell you the cycle at which forecast revenue crosses forecast steam cost — the stop signal."* |
| 3.2 | Steam-allocation optimiser across wells under the 74 tpd hard constraint | **L** | ml | *"The real decision isn't the slug size on one well. It's which of nineteen candidates gets Monday's 74 tonnes."* |
| 3.3 | OIL history-matching harness: ingest one full CSS cycle, refit constants, report before/after benchmark deltas | **L** | ml/physics | *"Give us one cycle of history and every literature constant in this model becomes a fitted one. That's our Level-3-to-Level-4 graduation gate."* |
| 3.4 | Workover-avoidance economics driven by the floating-risk classifier (AUC 0.999) against the $15–50k band | **M** | econ | *"Half of sucker-rod failures are metal-on-metal rod-tubing wear, and our floating index flags it before it happens — $15,000 to $50,000 an event."* |
| 3.5 | Scope 1&2 carbon accounting to a reportable standard; tie into the 2018 EOR policy's screening mandate | **M** | econ | *"India's 2018 EOR policy mandates screening and a pilot before commercial rollout. A validated twin is the cheapest way to satisfy that mandate — this stops being a demo and becomes a compliance asset."* |

---

## 6. Constants ledger — one table a judge can audit

| Constant | Value | Label | Source |
|---|---:|---|---|
| Oil SG (15.5° API) | 0.96259 t/m³ | `[DERIVED]` | `141.5/(131.5+API)`; API from SPE-23APOG-535203 |
| bbl per m³ | 6.28981 | `[DEFINITION]` | 1 bbl = 0.158987 m³ |
| HSD per t steam | 71.0 kg | `[DERIVED]` | OIL deck: 220 kg/h ÷ 3.1 t/h |
| HSD density | 0.83 kg/L | `[TYPICAL]` | standard diesel |
| Diesel per t steam | 85.54 L | `[DERIVED]` | 71 ÷ 0.83 |
| Diesel LHV | 42.6 MJ/kg | `[TYPICAL]` | standard |
| Fuel energy per t steam | 3.02 GJ | `[DERIVED]` | in the published 2.6–4.0 GJ/t band ✓ |
| Diesel price (Rajasthan) | ₹97.80/L | `[CONFIRMED — retail, upper bound]` | goodreturns.in, Aug 2026 |
| **Steam cost** | **₹8,366/t** | `[DERIVED]` | 85.54 × 97.80 (research rounds to ₹8,400) |
| ~~Steam cost (dashboard)~~ | ~~₹1,300/t~~ | **`[UNSOURCED — REJECT]`** | `dashboard/index.html:1243`, no provenance; ≈ a gas-fired number |
| CO₂ factor, diesel | 74.1 kg/GJ | `[CONFIRMED]` | IPCC defaults |
| CO₂ factor, gas | 56.1 kg/GJ | `[CONFIRMED]` | IPCC defaults |
| **CO₂ per t steam** | **223.8 kg** | `[DERIVED]` | 3.02 × 74.1; two independent cross-checks agree to 1% |
| CO₂ per bbl multiplier | SOR × 35.58 | `[DERIVED]` | 223.8 ÷ 6.28981 |
| Crude realization | $65/bbl | **`[UNSOURCED — PLACEHOLDER]`** | **fetch from OIL investor deck (Tier 1.6)** |
| Heavy-oil discount | $10/bbl | **`[UNSOURCED — PLACEHOLDER]`** | 14–18° API sour, no pipeline netback |
| INR/USD | 88.0 | `[UNSOURCED]` | set on demo day |
| Workover cost | $15k–50k/event | `[TYPICAL]` | iFactory; we reject the higher $90k–270k band as not defensible onshore |
| Electricity tariff | ₹8/kWh | **`[UNSOURCED — PLACEHOLDER]`** | Baghewala is off-grid; may need to be a genset-diesel number |
| Field steam capacity | 74.4 t/d | `[CONFIRMED-secondary]` | OIL deck, 3,100 kg/h |
| FY26 field output | 43,773 t | `[CONFIRMED]` | BusinessToday, Apr 2026 |
| FY26 CSS jobs | 19 | `[CONFIRMED]` | BusinessToday, Apr 2026 |

**Rule for the deck:** any number carrying `[UNSOURCED — PLACEHOLDER]` must either be replaced
before submission or printed on the slide *with* the word "assumed". There are four of them.
Three are Tier-1 S-sized to fix.

---

*Compiled September 2026 by the economics & validation pass. Read alongside
`docs/research/deep-dives/css_thermal_eor_deep_dive.md` §5 (economics), `§3` (world benchmarks),
`docs/research/deep-dives/digital_twin_oilfield_deep_dive.md` §1.3 (DNV levels),
`docs/research/deep-dives/sih_winning_playbook.md` §1.2 (the official rubric), and
`docs/reviews/integration_report.md` (the 24/24 unit-test baseline and the two retuned constants).*
