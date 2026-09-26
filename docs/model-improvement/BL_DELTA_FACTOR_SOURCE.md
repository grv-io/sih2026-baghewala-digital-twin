# `BL_DELTA_FACTOR` — source and verdict (physics v3, 26 Sep 2026)

**Verdict: the constant is justified at exactly 0.5. δ itself is now computed from the
simulated oil and water every produce day (PEH Eq. 15.74), which replaces the unsourced
`CP_LIQUID_JM3K = 4.0e6` blend.** The ½ is part of Boberg & Lantz's own definition of δ, and
energy conservation fixes it, so it is not a fudge factor. The UQ range U[0.35, 1.00] in
`ml/uq.py` should be dropped. The uncertainty in δ comes from the produced **water rate**.

## 1. The published equations
Boberg, T.C. & Lantz, R.B. (1966), *JPT* 18(12) 1613–1623, SPE-1578-PA. The original paper
is paywalled and was not retrieved. The equations below are its reproduction in the SPE
*Petroleum Engineering Handbook* Vol. V ch. 15, "The Boberg and Lantz Method", on PetroWiki:
<https://web.archive.org/web/20220123095900/https://petrowiki.spe.org/PEH:Thermal_Recovery_by_Steam_Injection>
(equation images `Vol5_page_1334_eq_001…004`, `Vol5_page_1335_eq_001`):
```
(15.70)  T̄ = T_R + ΔT · [ f_Vr · f_Vz · (1 − f_pD) − f_pD ]
(15.73)  f_pD = (1 / 2Q) · ∫₀ᵗ Q̇_p dt
(15.74)  Q̇_p = [ 5.615 (q_o M_o + q_wh M_w + q_s M_w + q_s ρ_w h_fv / ΔT) + 10³ q_gh M_g ] · ΔT
nomenclature:  Q = "amount of injected heat remaining in reservoir";
               f_pD = "heat loss factor caused by hot fluid production"
```
The handbook adds: *"The model does not predict steam, gas, or water producing rates, which
must be estimated from some other source."* UPC Global (2021, *Artificial Lift Performance
Coupled with Boberg & Lantz Model*) says the same in words: f_pD is "the ratio between
cumulative heat produced and the total heat injected".

## 2. What our constant is
| Ours | Boberg–Lantz |
|---|---|
| `delta = BL_DELTA_FACTOR · Q_removed_J / Q_retained_J` | `f_pD = (1/2Q) ∫ Q̇_p dt` |
| `BL_DELTA_FACTOR = 0.5` | the **½** in Eq. 15.73 |
| `Q_retained_J` (Marx–Langenheim heat left at end of injection) | `Q`, injected heat remaining |
| `Q_removed_J`, accumulated daily in `cycle.py` | `∫ Q̇_p dt` |
| `f_VD` exact slab, `f_HD` exact cylinder | `f_Vz`, `f_Vr` (Fig. 15.19, fits 15.71–72) |

It is not δ and not an adjustment to (1 − δ). It is the ½ inside δ.

**Why ½ is forced.** With no conduction (f = 1, as at t = 0), Eq. 15.70 gives θ = 1 − 2δ.
The zone keeps a fixed volume and holds heat Q − Q_p, so θ must equal 1 − Q_p/Q, which
requires δ = Q_p/2Q. A factor of 1.0 would remove twice the heat the produced fluid actually
carries. The rev-5/UQ "1.0 → SOR ≈ 5.1" case is an energy-balance violation, not an
alternative (`test_thermal.py::test_bl_half_is_exact_energy_conservation_without_conduction`).
With conduction, removal enters as δ(1 + F) ≤ 2δ: a zone cooled by production then loses
less by conduction. That is B–L's stated approximation, inside the published 42 % band
(*Petroleum* 2018, S2405656118301755).

Cross-check: our exact kernels agree with the PEH fits
`f_Vz = 0.96·e^{−(ln t_D+4.4)²/27}` and `f_Vr = 0.92·e^{−(ln t_D+4.6)²/13.5}` within ±0.05 at
h = 12 m, r_h = 9.8 m over 10–300 d. The fits are poor only below t_D ≈ 0.01.

## 3. Computing δ from our own production: done, now per Eq. 15.74
rev 5 already accumulated δ daily, but used one blend (`CP_LIQUID_JM3K = 4.0e6`,
ASSUMPTION) on `oil/(1 − wc)`. v3 (`thermal.produced_heat_J_per_day`) computes each stream:
- **Oil:** `q_o·M_o·(T̄ − T_R)`, with M_o = ρ_o(API)·c_o. c_o is Gambill's (1957)
  (0.388 + 0.00045 T_F)/√SG Btu/lb·°F at the mean temperature, giving ≈ 2.15 MJ/m³K at 150 °C
  (about half of water's, as PEH ch. 15 notes).
- **Hot water:** `q_wh·ρ_w·[h_f(T̄) − h_f(T_R)]` from the saturated-liquid steam table
  (h_f(290 °C) = 1,291 vs IAPWS 1,290 kJ/kg).
- **q_s and q_gh:** 0, labelled [ASSUMPTION]. The model does not predict them. Near-well
  pressure ≥ 11.4 MPa is above p_sat(290 °C) = 7.4 MPa, so the params do not support free
  steam in the zone. Water that flashes in the tubing has already left the zone and is
  counted at T̄.

Reference cycle (1,500 t / 7 d / 1.2 / 5): produced heat 0.78 TJ, which is 33 % of the heat
delivered to the sand face and 39 % of Q. δ at the end of the cycle is 0.19. The effective
blend is ≈ 3.9 vs 4.0 MJ/m³K, so SOR moves 4.089 → 4.027 (−1.5 %).

## 4. Where the uncertainty lives
δ ∝ (water produced) × Δh_f. The open inputs are `fluid.water_cut = 0.85` (2,111 m³ back
for 1,500 t injected, 141 %, high for cycle 1) and the zero-steam-production assumption.
**For `ml/uq.py` (not edited here):** fix `bl_delta_factor` at 0.5 (the override is kept only
for backward compatibility) and widen `water_cut` instead. The earlier finding that "BL is
the largest margin driver" came from sampling an excluded range.
