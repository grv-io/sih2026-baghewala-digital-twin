# Computed dynamometer cards — `twin/dyno.py`

Replaces the dashboard's illustrative lens (`buildDynoLoop`) with a surface card and a pump
card **computed** from rod-pump mechanics, at any day of a simulated CSS cycle.
Tests: `tests/test_dyno.py` (24). Export: `python -m twin.dyno --bake ml/models/dyno_cards.json`.

## 1. Method: predictive Gibbs wave equation by finite differences (not RP 11L)
RP 11L needs its chart look-ups (F1/Skr, F2/Skr vs N/No, Fo/Skr), is limited to its
electric-analog damping, and has **no carrier-bar separation**, which is the rod-float
signature we need. The Gibbs FD model gives the full card shape, validates cleanly against
the static and energy limits below, and runs in 13 ms median / 48 ms worst per card (2–12 SPM). RP 11L-style numbers
(W_rf, Fo, rod stretch, Mills factor) are kept as cross-checks.

Rod string (effective force, buoyant weight distributed, Gibbs 1963, SPE-588-PA):

    ρA ∂²u/∂t² = ∂/∂x(EA ∂u/∂x) − w_b − (ρA·c_G + K_VISC·μ) ∂u/∂t,   c_G = π·a·ν / (2L)

Lumped-mass chain, 14 segments split over the tapers, central differences, damping at the
mid-step velocity (stable for any μ), Courant a·dt/dx = 0.95. Strokes are repeated until
peak/min/mean PRL and plunger stroke repeat within 0.5 % (usually 3–5 strokes).
- **Surface BC:** polished-rod position U(θ) = S/2·[1 − cos θ + (λ/2) sin²θ] (SHM + second
  harmonic, slider-crank / Mills 1939), λ = 0.25. The carrier bar can **pull but never push**:
  if the load needed to drive the rods down goes negative, the clamp separates (PRL = 0) and
  the string falls on its own weight against drag, until the rising carrier re-catches it
  (impact). Card position = horsehead position, as a beam-inclinometer dynamometer records.
- **Pump BC:** valve state machine. Upstroke: plunger held while rod stretch picks up
  Fo = (P_d − P_i)·A_p, then load Fo + F_fr. Downstroke: full barrel → held until load
  releases, then −F_fr. Fillage f < 1 → plunger falls through the vapour void still carrying
  Fo, then **releases in one step** when it strikes liquid (fluid pound). Gas option: void is
  isothermal gas at P_i, compressed to P_d before the TV opens (gradual release) and dead-space
  gas re-expands on the upstroke (rounded pickup).
- P_d = THP + ρ_mix·g·L (ρ_mix = 994 kg/m³ at 85 % cut); P_i = `cycle._pump_intake_pressure_kPa`.
- **Heavy oil:** the only viscous term beyond ν is `srp.py`'s own Couette law K_VISC·μ·v per
  metre (K_VISC = 10) — one drag law for the day-by-day twin and the card.
- **Along a cycle:** `card_for_row` sets fillage = produced liquid ÷ plunger displacement
  (plunger stroke corrected once from the FD result), so the pump is part-empty whenever the
  reservoir, not the pump, sets the rate. `cards_along_cycle(df, params)` tabulates it.

| Parameter (`params.srp`) | Value | Tag |
|---|---|---|
| Rod string | 1″ 558 m over 7/8″ 592 m, 4.322/3.310 kg/m with couplings | [TYPICAL – not Baghewala] |
| E, wave speed | 2.07e11 Pa → a = 4,926 m/s | [TYPICAL] |
| Gibbs ν | 0.10 (c_G = 0.67 s⁻¹) | [TYPICAL, 0.05–0.15] |
| crank/pitman λ, THP, plunger friction | 0.25, 300 kPa, 0.9 kN | [TYPICAL] |
| W_r / W_rf / Fo / static stretch | 42.9 / 37.4 / 16.1 kN / 0.205 m | derived |

## 2. Validation (μ = 5 cP unless stated; stroke 2.18 m; numbers from the test cases)
| # | Check | Result |
|---|---|---|
| a | 2 SPM, full pump: PPRL vs W_rf+Fo = 53.6 kN; MPRL vs W_rf = 37.4 kN | 57.7 (+7.7 %), 33.9 (−9.5 %) — inside RP 11L's ±10 %. Load **lines** 55.1 / 35.9 kN = W_rf+Fo+F_fr / W_rf−F_fr within 3 %. Plunger stroke 1.954 m vs S − stretch 1.975 m. At 3 SPM the extremes are +10.9 / −13.3 %: the pickup/release stress wave (≈ Z·v, Z = EA/a = 21 kN·s/m) that RP 11L's charts smooth out. |
| b | PPRL / MPRL at 3, 6, 9, 12 SPM | 59.4/32.5, 65.2/27.9, 71.1/22.4, 78.6/16.4 kN — monotone. Mills (rigid rod) 54.2, 55.9, 58.9, 63.0: FD/Mills = 1.10→1.25, the elastic-wave excess growing with N/No (0.05→0.19). |
| c | f = 0.6, 5 SPM | Pump card holds Fo to 60 % then drops in < 1 % of stroke (card fillage 0.599); surface downstroke carries the same step. Gas variant: release spread over 25 % of stroke → *gas interference, 66 %*. |
| d | 10,000 cP, 12 SPM (srp FI = 1.0) | Carrier separates 55 % of the cycle, MPRL = 0, plunger stroke 0.82 m of 2.18 (62 % lost), PPRL 144.6 kN (srp static 154.8). **Onset of separation** vs srp's v_stroke/v_fall: 0.625 / 0.591 / 0.589 / 0.551 at 3 / 5 / 8 / 12 SPM — the SPEC's 0.6 alarm line (≈ 2/π, where the *peak* harmonic rod speed reaches v_fall) is reproduced independently. MPRL/W_rf at 5 SPM: 0.78, 0.72, 0.57, 0.39, 0.21, 0.03 for μ = 0.1–5k cP. |
| e | Card area = pump work + damping dissipation | Error ≤ 0.2 % in all cases. 5 SPM full: 41.3 = 35.3 + 6.0 kJ; pump card = (Fo + 2F_fr)·S_p within 2 %. Hydraulic ÷ polished-rod power 0.84 (2 SPM), 0.77 (5), 0.63 (12 SPM), 0.37 at 2,000 cP. |
| f | Stability / grid | Courant ≤ 0.95 asserted; finite and bounded at μ = 1–50,000 cP, 2–12 SPM, 600–2,000 m. PPRL 63.08 / 63.22 / 63.36 / 63.39 kN at 8 / 14 / 40 / 80 segments. |

**Against `srp.py`'s static peak (W_b + Fo + F_v at v_avg).** The old "85.6 kN" was the v1
twin (3 m stroke, 2,203 cP); at today's params srp gives 54.5 kN hot → 63.7 kN at the
baseline's cold end. The card gives 62.8 → 71.2 kN: **+12 to +16 %**, which is the dynamic load
srp omits (pickup wave + acceleration; dynamic factor 1.18 at 5 SPM, 1.47 at 12 SPM hot). Both
rise together with μ. srp's `energy_kWh_d` is 3.6× (hot) / 2.0× (cold) the card-area energy
because it never credits the rod weight back on the downstroke — flagged in CHANGELOG rev 6. **Fixed in rev 8 (27 Sep, Economics v2):** `srp.energy_kWh_d` is now the closed-loop polished-rod work and matches this card's area within −1 to +9 % (tests/test_srp.py).

## 3. Classifier (`classify_card`, rule-based on card features)
Priority rod_float > heavy_oil_viscous > gas_interference > fluid_pound > full_pump; all hits
are in `signatures`. Rod float: carrier separation or MPRL ≤ 5 % W_rf, *and* heavy-oil drag ≥
10 % W_rf. Viscous: (surface − pump) up/down gap averaged over 25–75 % of stroke ≥ 0.30 W_rf
(inertia peaks at the stroke ends, drag at mid-stroke), same drag guard. Pound vs gas: card
fillage < 0.90, release over < / > 10 % of stroke. Severity: mild ≥ 75 %, moderate ≥ 50 %.

## 4. Reference shapes for the UI (pump card red, surface card blue)
1. **Healthy / full pump** — pump card a rectangle 0 → Fo+F_fr (≈17 kN) over the plunger stroke
   (~1.95 m of 2.18). Surface card a parallelogram between ~W_rf (37 kN) and ~W_rf+Fo (54 kN);
   slanted left/right sides = rod stretch (0.2 m); small ringing on the top line.
2. **Fluid pound** — top line held into the downstroke, then a near-vertical drop at the fillage
   point (right-to-left); pump card an "L": full load on the right, step down at f·S_p. Upper-left
   corner stays square (vs. gas: both corners rounded, release is a slope).
3. **Heavy-oil viscous** — fat card: upstroke line lifted and downstroke line depressed by
   up to ±K_VISC·μ·L·v_peak (6.6 kN at 1,000 cP, 33 kN at 5,000 cP, 5 SPM), rounded ends, pump card unchanged.
   Baghewala's late cycle is this **plus** severe pound (fillage 25–40 %).
4. **Rod float** — egg/teardrop sitting on the zero line: load goes slack (0 kN) through the
   late downstroke and early upstroke while the clamp rides above the carrier, a steep
   re-catch rise, a very high peak (130–145 kN), and a shortened pump card (lost stroke).
The baked progression: early hot = mild/moderate pound (the pump out-displaces the heated
well even at 5 SPM), late cold = viscous + severe pound, 12 SPM on cold oil = rod float.

## 5. JSON the UI consumes (`ml/models/dyno_cards.json`, ~42 kB, 200 points per curve)
```
{schema:"dyno_cards/v1", method, units:{position:"m",load:"kN"}, stroke_m,
 scenarios:{baseline|recommendation:{settings:{steam_t,soak_days,cutoff_m3d,spm},
   cards:[{key:"early_hot"|"mid"|"late_cold"|"stress_12spm", day, mu_cP, spm,
     floating_index_srp, pump_fillage, card_type, card_label, signatures[],
     peak_prl_kN, min_prl_kN, plunger_stroke_m, carrier_separation, min_rod_force_kN,
     polished_rod_kW, reference:{W_rf_kN,Fo_kN,static_peak_kN},
     surface:{position_m[],load_kN[]}, downhole:{position_m[],load_kN[]}}]}}}
```
Plot `surface` and `downhole` as closed loops on one axis (0–2.2 m, 0–150 kN); draw
`reference.W_rf_kN` and `static_peak_kN` as dashed guides. Drop the "indicative" caveat;
keep "computed, typical rod string".

| Baked card | Baseline 1,300/10/1.3/5 | Recommendation 1,700/10/0.85/5 |
|---|---|---|
| early hot | d27.6, 7 cP: 62.8 / 27.6 kN, fluid pound 72 % | d33.0, 7 cP: 63.1 / 28.6, fluid pound 78 % (mild) |
| mid | d106.6, 214 cP: 63.7 / 25.3, fluid pound 63 % | d151.0, 436 cP: 64.5 / 23.4, fluid pound 62 % |
| late cold | d184.6, 2,200 cP: 71.2 / 18.3, viscous + pound 39 % | d268.0, 4,908 cP: 89.1 / 13.0, viscous + pound 25 % |
| 12 SPM stress | 98.5 / 11.7, viscous + pound 16 % | 133.7 / 0.0, **rod float** (separation) |

## 6. Known limits
- Rod string, pumping-unit geometry, THP, ν and plunger friction are [TYPICAL], not
  Baghewala's; with OIL's real string and one measured card, ν and an effective c(μ) are the
  first things to calibrate (srp deep dive Q5: linear damping at 10⁴ cP is a stretch).
- No tubing stretch (anchored tubing), vertical well (no rod–tubing Coulomb drag), no
  tubing-flow pressure drop on the upstroke (water-continuous 85 %-cut stream assumed), no
  plunger/valve viscous resistance beyond K_VISC rod drag; gas only as the lumped option.
- Single-phase-ish column density; fillage along the cycle is volumetric, not from an inflow
  model of barrel filling. Unit kinematics are symmetric (no Mark II / phase-angle asymmetry).
- Drag is taken relative to the tubing wall (fluid velocity ignored), as in `srp.py`.
