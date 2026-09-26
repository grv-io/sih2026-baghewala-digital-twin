"""srp.py -- sucker-rod pump load, energy, rod-float velocity ratio and fillage.

Source model: a lumped, single-point simplification of the classical API
RP 11L sucker-rod-pumping load calculation (peak polished-rod load = buoyant
rod-string weight + fluid load, e.g. Gault/Neely-style hand calculations used
for pumpjack sizing), extended with a lumped viscous-drag term to capture the
heavy-oil operating problem of **rod floating**.

**T1-E -- what `floating_index` actually is.** Algebraically it has always been

    floating_index = viscous_drag / buoyant_rod_weight
                   = v_stroke / v_fall

i.e. **the rod string's average stroke velocity over its drag-limited terminal
fall velocity**, where

    v_fall = W_buoyant / (K_VISC * mu_Pa_s * L_rod)      [m/s]

The value is unchanged by this rename (regression-tested); the name is now
honest, and it is the physics-side twin of the *scaled load ratio* that
SPE Journal 233386 uses to predict rod failures ~14 days ahead
(SOURCE: srp_dynamometer_ml_deep_dive.md section 6.3-1).

**T1-E -- rod float now costs barrels.** When `v_stroke > v_fall` the rods
cannot complete the downstroke, so plunger travel is lost. The previous flat
`VOLUMETRIC_EFFICIENCY = 0.85` -- a NORMAL-oil number applied to an 11,500 cP
well -- is replaced by a **fillage** that degrades with lost stroke:

    stroke_eff_frac = min(1, v_fall / v_stroke)
    fillage         = FILLAGE_MAX * stroke_eff_frac

**rev 5 -- the pump lifts LIQUID.** Displacement x fillage is a liquid rate;
the oil it can deliver is that times (1 - fluid.water_cut), the same produced
stream cycle.py uses for the Boberg-Lantz energy-removed term. Pump geometry is
[TYPICAL - not Baghewala]: 1.75 in plunger, 86 in (2.18 m) stroke, i.e. a
C-228-class unit sized for a ~20 bbl/d oil / ~130 bbl/d liquid well at
1,150 m. The rev-4 2.25 in x 118 in pump compared on an oil basis gave
~75 m3/d at 8 spm, ~25x the well's rate, so SPM could never matter.

SOURCE: srp_dynamometer_ml_deep_dive.md sections 1.3(c) / 5.1(3):
**"75 % consistent fillage counts as a win"** in severe heavy oil
(SPE-175369-MS, SPE Kuwait 2015), against 85-95 % for normal fillage-based VSD
control.

**T1-D -- the SPM ceiling the rods can physically keep up with.** Inverting the
same velocity ratio gives, for a target margin phi = v_stroke/v_fall,

    SPM_max(mu) = 60 * phi * W_buoyant / (2 * S * K_VISC * mu_Pa_s * L_rod)

which at the real params (W_b = 37.6 kN, L = 1,150 m, S = 2.18 m, K_VISC = 10,
phi = 1) gives SPM_max = 22.5 / 9.0 / 3.9 at mu = 2,000 / 5,000 / 11,500 cP --
i.e. the schedule falls into the published heavy-oil **3-6 SPM** band by itself
as the well cools (rev 5: stroke 3.0 -> 2.18 m, schedule margin 0.6 -> 1.0) (SOURCE: srp deep dive section 5.1;
sciencedirect.com/topics/engineering/pumping-unit; US Patent 4,406,597).

**rev 10 -- the rods are dragged by the PRODUCED STREAM, not by reservoir
oil.** Until rev 9 the drag law used the heated-zone reservoir-oil viscosity
(6,493 cP on the recommendation's last day) for a tubing stream that is 85 %
water. `rod_drag_viscosity_cP` now returns an effective produced-fluid
viscosity with a phase-inversion point (`fluid.emulsion_inversion_wc`,
[ASSUMPTION] 0.70, heavy-oil literature band 0.6-0.75):

    water cut <  inversion (oil-continuous W/O):  mu_e = mu_o * (1 - wc)^-2.5
    water cut >= inversion (water-continuous O/W): mu_e = mu_w(T) * wc^-2.5

i.e. Brinkman's (1952) concentrated-suspension law, mu_e = mu_c (1 - phi)^-2.5,
applied to whichever phase is continuous (phi = dispersed fraction; its dilute
limit is Einstein's 1 + 2.5 phi). `fluid.tubing_viscosity_model = "oil"`
restores the rev-9 behaviour (tubing fluid = reservoir oil) for comparison and
for tests of the drag mechanics themselves. Every rod-drag quantity -- v_fall,
floating_index, fillage, the SPM schedule ceiling, the drag part of the
polished-rod energy and dyno.py's card -- uses this one effective viscosity.
Consequence (TIER1_PROGRESS_LOG.md section 9): at the shipped 85 % cut the
stream is water-continuous and the float index is ~0 everywhere.

**rev 12 -- the W/O branch is Pal & Rhodes (1989) with a cap.**
`wo_relative_viscosity`: mu_r = [1 + (phi/phi*)/(1.187 - phi/phi*)]^2.49,
phi* = `fluid.emulsion_phi_star` (0.84, [ASSUMPTION], UQ 0.65-1.0), capped at
`fluid.emulsion_mu_r_max` (10x, [ASSUMPTION]). The law is Brinkman on a
solvated fraction phi/(1.187 phi*): at phi* = 0.84 it IS Brinkman to <1 %
below 60 % water, so the wave-4 change that moves the physics is the cap
(Brinkman gave 10-19x at 60-69 % water, where the late-cycle stream sits).
`fluid.emulsion_law = "brinkman"` (or a tree without the key) is rev 10/11.
The O/W branch is unchanged. TIER1_PROGRESS_LOG.md section 11.

**rev 13 -- the inversion is a band, not a cliff.** The rev 10-12 switch at
`emulsion_inversion_wc` made the drag viscosity jump ~3,400x in one day (3,000
cP W/O -> 0.69 cP O/W at 300 cP oil). Phase inversion of crude emulsions is
hysteretic and gradual: over a range of water cuts the two phases coexist as
multiple (W/O/W, O/W/O) emulsions and the inversion point depends on the
direction of change and the shear history (Salager et al., "Emulsion
inversion", in *Encyclopedic Handbook of Emulsion Technology*, 2001; Pal 1993,
Chem. Eng. Sci. 48: catastrophic inversion hysteresis in crude emulsions --
recalled, not re-retrieved). `fluid.emulsion_inversion_band_wc` [ASSUMPTION
0.05-0.10, base 0.075] sets a transition band centred on the inversion cut in
which ln(mu) is blended linearly between the W/O and O/W branches. Absent/0 =
the rev 12 sharp switch. TIER1_PROGRESS_LOG.md section 12.

None of this is a full API RP 11L dynamometer-card calculation (that needs rod
elasticity, wave propagation and dynamic loading); it is a static,
single-number-per-day approximation appropriate for a day-by-day CSS cycle
simulator, not a mechanical design tool.
"""
from __future__ import annotations

import math

G = 9.81  # m/s^2

# ASSUMPTION: steel sucker-rod density, used only for the buoyancy factor.
RHO_STEEL_KGM3 = 7850.0

# ASSUMPTION: maximum achievable pump fillage in clean, hot, gas-free
# conditions -- the value the old flat VOLUMETRIC_EFFICIENCY used. Fillage now
# degrades below this with lost stroke (T1-E). SOURCE for the heavy-oil target:
# SPE-175369-MS (75 % consistent fillage = success in severe heavy oil).
FILLAGE_MAX = 0.85

# ASSUMPTION: lumped viscous-drag coefficient for the rod string moving through
# fluid in the tubing annulus, modelled as a Couette-like drag
# F_visc [N] = K_VISC * mu [Pa.s] * v_avg [m/s] * rod_length [m].
# Not derived from an annular-gap geometry (none is in field_params.json);
# tuned so cold heavy oil at mid-to-high SPM pushes the velocity ratio into the
# >0.6 floating-risk band while hot oil gives negligible drag.
# rev 10: now params["srp"]["k_visc"] [ASSUMPTION, UQ +/-50 % = U[5, 15]];
# this constant is the FALLBACK. Sanity bound: Couette flow in a concentric
# annulus gives 2*pi/ln(D_t/D_r) ~ 6-7 for 2-7/8 in tubing x 7/8-1 in rods, so
# 10 with couplings is in the right range -- but it is not derived.
K_VISC = 10.0

# rev 10: produced-stream (tubing) viscosity model. See the module docstring.
# [ASSUMPTION] water cut at which the produced W/O emulsion inverts to O/W.
# Heavy-oil emulsions typically invert at 60-75 % water (asphaltene-stabilised
# W/O emulsions push it to the high end); overridable via
# fluid.emulsion_inversion_wc, sampled U[0.60, 0.75] in ml/uq.py.
DEFAULT_EMULSION_INVERSION_WC = 0.70
# Brinkman (1952) exponent, mu_e = mu_c * (1 - phi)^-BRINKMAN_EXP. [SOURCED]
BRINKMAN_EXP = 2.5
TUBING_VISCOSITY_MODELS = ("emulsion", "oil")

# --- rev 12 (physics wave 4): the W/O (oil-continuous) branch ---------------
# Pal & Rhodes (1989), "Viscosity/concentration relationships for emulsions",
# J. Rheol. 33(7):1021-1045, their Eq. for Newtonian emulsions written with
# phi* = the dispersed fraction at which the relative viscosity reaches 100:
#     mu_r = [1 + (phi/phi*) / (PR_A - phi/phi*)]^PR_EXP,  PR_A = 1.187, PR_EXP = 2.49
# Algebraically mu_r = (1 - phi / (PR_A * phi*))^-PR_EXP: Brinkman's law on an
# EFFECTIVE (solvated) volume fraction phi/(1.187 phi*). Brinkman is therefore
# the special case phi* = 1/1.187 = 0.842 (no solvation); Pal & Rhodes' fitted
# emulsions (phi* below that) are MORE viscous than Brinkman, not less.
# `fluid.emulsion_phi_star` [ASSUMPTION] base 0.84 = the value that puts
# mu_r(45 % water) at 4.5x, the geometric centre of the published heavy-oil W/O
# band of ~2-10x at 40-50 % water (coordinator brief, wave 4); UQ U[0.65, 1.0]
# (mu_r(0.45) ~ 9x -> 3.3x). Pal & Rhodes' own fitted phi* sit roughly
# 0.6-0.85 [recalled, not re-retrieved in full]; 1.0 is beyond them on the
# loose side and is kept as the "deformable / weakly stabilised" edge.
# Consequence (TIER1 section 11): at 30-50 % water the law is Brinkman to
# within a few %; what changes the physics is the CAP below, which binds
# only near inversion (Brinkman gives 10-19x at 60-69 % water).
PAL_RHODES_A = 1.187
PAL_RHODES_EXP = 2.49
DEFAULT_EMULSION_PHI_STAR = 0.84
# [ASSUMPTION] cap on the W/O relative viscosity: the top of the published
# heavy-oil 2-10x band. Above ~60 % water both Brinkman and Pal-Rhodes are
# extrapolating their zero-shear crowding divergence toward the inversion
# point; measured crude W/O emulsions are strongly shear-thinning there, and
# the rod annulus runs at ~10^2-10^3 1/s. Overridable via
# fluid.emulsion_mu_r_max (null = no cap). Not sampled in UQ (fixed rule).
DEFAULT_EMULSION_MU_R_MAX = 10.0
EMULSION_LAWS = ("pal_rhodes", "brinkman")


def wo_relative_viscosity(phi: float, params: dict | None = None) -> float:
    """Relative viscosity of the W/O (oil-continuous) emulsion at water fraction phi.

    rev 12: `fluid.emulsion_law` "pal_rhodes" (default when the key is absent
    is "brinkman", i.e. rev 10/11, so old params trees reproduce) with
    `fluid.emulsion_phi_star`, capped at `fluid.emulsion_mu_r_max`."""
    fluid = (params or {}).get("fluid", {}) if isinstance(params, dict) else {}
    law = str(fluid.get("emulsion_law") or "brinkman").lower()
    if law not in EMULSION_LAWS:
        raise ValueError(f"fluid.emulsion_law must be one of {EMULSION_LAWS}, got {law!r}")
    phi = min(max(float(phi), 0.0), 0.99)
    if law == "brinkman":
        mu_r = (1.0 - phi) ** (-BRINKMAN_EXP)
    else:
        ps = fluid.get("emulsion_phi_star")
        ps = DEFAULT_EMULSION_PHI_STAR if ps is None else float(ps)
        x = phi / max(ps, 1e-6)
        if x >= PAL_RHODES_A - 1e-9:
            mu_r = float("inf")
        else:
            mu_r = (1.0 + x / (PAL_RHODES_A - x)) ** PAL_RHODES_EXP
    cap = fluid.get("emulsion_mu_r_max")   # absent/null = no cap (rev 10/11 trees)
    if cap is not None:
        mu_r = min(mu_r, float(cap))
    return float(mu_r)

# Heavy-oil rod-descent speed limit: <= 2 inches per second for the slow
# descent phase. SOURCE: srp_dynamometer_ml_deep_dive.md section 5.1(1).
# [CITED] 2 in/s = 0.0508 m/s.
#
# DEVIATION FROM THE PLAN SKETCH (documented on purpose): the plan wrote
# `descent_violation = v_avg_ms > DESCENT_LIMIT_MS`. Taken literally that is
# True for every pumping unit ever built (a 3 m stroke at 4 SPM already gives
# v_avg = 0.4 m/s), so the flag would carry no information -- the same
# "decorative alarm" failure mode T1-E exists to remove. The 2 in/s figure is
# guidance for the SLOW DESCENT PHASE, i.e. it bounds how fast rods may be
# allowed to fall when they are float-limited. So a violation is raised when
# the commanded stroke velocity exceeds BOTH what the rods can physically do
# (v_fall) AND the published slow-descent limit.
DESCENT_LIMIT_MS = 0.0508

# --- Economics v2 (27 Sep 2026): polished-rod energy -----------------------
# [TYPICAL] surface (prime-mover-to-polished-rod) efficiency of a beam unit:
# motor x V-belts x gear reducer x linkage. Takacs, *Sucker-Rod Pumping
# Handbook* (Elsevier 2015) ch. 4 gives typical component efficiencies of
# roughly 0.85-0.92 (NEMA D motor at its cyclic load), 0.95-0.97 (belts),
# 0.95-0.97 (gearbox) and ~0.95 (structure), i.e. a surface efficiency of
# ~0.55-0.75; 0.60 is used (a small, cyclically loaded motor). Overridable via
# params["srp"]["surface_efficiency"]. Converts the polished-rod energy below
# into the ELECTRICAL energy the tariff is charged on.
DEFAULT_SURFACE_EFFICIENCY = 0.60

# Defaults for the Gibbs-damping / plunger-friction / discharge-pressure terms:
# the same keys and values twin/dyno.py reads from params["srp"], so the
# day-by-day energy and the computed card dissipate through the same laws.
_DYNO_DEFAULTS = {
    "rod_taper_d_in": [1.0, 0.875],
    "rod_taper_frac": [0.485, 0.515],
    "rod_taper_mass_kgm": [4.322, 3.310],
    "rod_E_Pa": 2.07e11,
    "gibbs_damping_nu": 0.10,
    "crank_pitman_ratio": 0.25,
    "tubing_head_pressure_kPa": 300.0,
    "plunger_friction_kN": 0.9,
}


def _fluid_density_kgm3(api_gravity: float) -> float:
    """Standard API-gravity to specific-gravity conversion, then to kg/m3."""
    sg = 141.5 / (131.5 + api_gravity)
    return sg * 1000.0


def k_visc(params: dict) -> float:
    """Lumped rod-drag coefficient, params["srp"]["k_visc"] or K_VISC (rev 10)."""
    v = params.get("srp", {}).get("k_visc") if isinstance(params, dict) else None
    return float(v) if v is not None else K_VISC


def rod_drag_viscosity_cP(mu_oil_cP: float, params: dict, water_cut: float | None = None,
                          T_C: float | None = None) -> float:
    """Effective viscosity of the produced stream that drags the rods (cP).

    rev 10 (external review, finding 8). Args:
        mu_oil_cP: oil viscosity at the stream temperature (the twin passes the
            heated-zone value -- there is still no tubing temperature profile,
            which is a stated limit).
        params: reads fluid.water_cut, fluid.emulsion_inversion_wc,
            fluid.tubing_viscosity_model, reservoir.T_initial_C.
        water_cut: overrides fluid.water_cut (dyno.py passes its own).
        T_C: stream temperature for the water viscosity; default reservoir T
            (a conservative, i.e. more viscous, choice for the water phase).

    Model "emulsion" (default): the continuous phase's viscosity times a
    relative viscosity, inverting at `emulsion_inversion_wc` -- W/O: rev 12
    Pal-Rhodes capped at 10x (`wo_relative_viscosity`; Brinkman in rev 10/11
    trees); O/W: Brinkman mu_w(T) * wc^-2.5. rev 13: with
    `fluid.emulsion_inversion_band_wc` > 0 the switch is a band centred on the
    inversion cut in which ln(mu) is blended linearly between the two branches
    (no day-to-day cliff). Model "oil": the rev-9 behaviour, the reservoir oil
    viscosity itself.
    """
    fluid = params.get("fluid", {})
    model = str(fluid.get("tubing_viscosity_model") or "emulsion").lower()
    if model not in TUBING_VISCOSITY_MODELS:
        raise ValueError(f"fluid.tubing_viscosity_model must be one of {TUBING_VISCOSITY_MODELS}, got {model!r}")
    if model == "oil":
        return float(mu_oil_cP)
    wc = water_cut if water_cut is not None else fluid.get("water_cut", 0.0)
    wc = min(max(float(wc or 0.0), 0.0), 0.99)
    inv = fluid.get("emulsion_inversion_wc")
    inv = DEFAULT_EMULSION_INVERSION_WC if inv is None else float(inv)
    band = inversion_band_wc(params)
    lo, hi = inv - 0.5 * band, inv + 0.5 * band
    oil_continuous = (wc < inv) if band <= 0.0 else (wc <= lo)
    if oil_continuous:
        # oil-continuous: water droplets dispersed in oil (phi = wc).
        # rev 12: Pal-Rhodes with a capped relative viscosity (wo_relative_viscosity).
        return _wo_branch_cP(mu_oil_cP, wc, params)
    if band <= 0.0 or wc >= hi:
        # water-continuous: oil droplets dispersed in water (phi = 1 - wc)
        return _ow_branch_cP(wc, params, T_C)
    # rev 13: inside the transition band both phases are partly continuous
    # (dual / multiple emulsions, hysteretic inversion): log-linear blend of the
    # two branch viscosities, each evaluated at the day's own water cut.
    s = (wc - lo) / band
    ln_mu = ((1.0 - s) * math.log(max(_wo_branch_cP(mu_oil_cP, wc, params), 1e-12))
             + s * math.log(max(_ow_branch_cP(wc, params, T_C), 1e-12)))
    return math.exp(ln_mu)


def _wo_branch_cP(mu_oil_cP: float, wc: float, params: dict) -> float:
    """Oil-continuous (W/O) branch: mu_oil * mu_r(wc) (rev 12 law + cap)."""
    return float(mu_oil_cP) * wo_relative_viscosity(wc, params)


def _ow_branch_cP(wc: float, params: dict, T_C: float | None) -> float:
    """Water-continuous (O/W) branch: Brinkman on water, mu_w(T) * wc^-2.5."""
    from twin import viscosity  # local import: keeps srp importable on its own
    T = params["reservoir"]["T_initial_C"] if T_C is None else T_C
    return viscosity.water_mu_cP(T) * max(wc, 1e-6) ** (-BRINKMAN_EXP)


def inversion_band_wc(params: dict) -> float:
    """Width (water-cut units) of the W/O <-> O/W transition band (rev 13).

    `fluid.emulsion_inversion_band_wc` [ASSUMPTION 0.05-0.10]; absent / null /
    0 = the rev 10-12 sharp switch at `emulsion_inversion_wc`. The band is
    centred on the inversion water cut."""
    v = (params.get("fluid", {}) if isinstance(params, dict) else {}).get("emulsion_inversion_band_wc")
    return max(float(v), 0.0) if v is not None else 0.0


def _buoyant_rod_weight_N(params: dict) -> float:
    srp = params["srp"]
    rho_fluid = _fluid_density_kgm3(params["fluid"]["api_gravity"])
    rod_mass_kg = srp["rod_mass_kgm"] * srp["rod_length_m"]
    return rod_mass_kg * G * (1.0 - rho_fluid / RHO_STEEL_KGM3)


def _fall_velocity_ms(weight_buoyant_N: float, mu_Pa_s: float, rod_length_m: float,
                      k: float = K_VISC) -> float:
    """Drag-limited terminal fall velocity of the rod string (m/s).

    `mu_Pa_s` is the DRAG viscosity (rod_drag_viscosity_cP, in Pa.s)."""
    return weight_buoyant_N / max(k * mu_Pa_s * rod_length_m, 1e-9)


def fall_velocity_ms(mu_cP: float, params: dict, T_C: float | None = None,
                     water_cut: float | None = None) -> float:
    """Public wrapper: rod-string terminal fall velocity (m/s).

    `mu_cP` is the OIL viscosity; rev 10 converts it to the produced-stream
    drag viscosity (rod_drag_viscosity_cP) at the params water cut (rev 11:
    or at `water_cut`, the day's produced-stream cut from cycle.py)."""
    mu_drag = rod_drag_viscosity_cP(mu_cP, params, water_cut=water_cut, T_C=T_C)
    return _fall_velocity_ms(
        _buoyant_rod_weight_N(params), mu_drag * 1.0e-3, params["srp"]["rod_length_m"],
        k_visc(params),
    )


def max_spm_for_viscosity(mu_cP: float, stroke_m: float, params: dict, margin: float = 1.0,
                          T_C: float | None = None, water_cut: float | None = None) -> float:
    """Highest SPM that keeps the rods ahead of the horsehead at ratio `margin` (T1-D).

        SPM_max = 60 * margin * v_fall / (2 * stroke_m)

    `margin` is the target `v_stroke / v_fall`: 1.0 is the physical limit
    (rods exactly keep up), <1 leaves headroom. Monotone decreasing in mu.
    """
    v_fall = fall_velocity_ms(mu_cP, params, T_C=T_C, water_cut=water_cut)
    if stroke_m <= 0.0:
        return 0.0
    return 60.0 * margin * v_fall / (2.0 * stroke_m)


def _srp_key(params: dict, key: str):
    return params["srp"].get(key, _DYNO_DEFAULTS[key])


def surface_efficiency(params: dict) -> float:
    """Prime-mover-to-polished-rod efficiency (see DEFAULT_SURFACE_EFFICIENCY)."""
    eta = params.get("srp", {}).get("surface_efficiency", DEFAULT_SURFACE_EFFICIENCY)
    eta = float(eta if eta is not None else DEFAULT_SURFACE_EFFICIENCY)
    return min(max(eta, 0.05), 1.0)


def params_water_cut(params: dict) -> float:
    """fluid.water_cut clipped to [0, 0.99] (the rev <= 10 constant cut)."""
    return min(max(float(params["fluid"].get("water_cut", 0.0) or 0.0), 0.0), 0.99)


def _mixture_density_kgm3(water_cut: float, params: dict) -> float:
    """Tubing-liquid density at `water_cut` (same law as dyno.mixture_density_kgm3)."""
    wc = min(max(float(water_cut), 0.0), 0.99)
    return wc * 1000.0 + (1.0 - wc) * _fluid_density_kgm3(params["fluid"]["api_gravity"])


def _gibbs_damping_Ns_m(params: dict) -> float:
    """Lumped Gibbs damping coefficient of the whole rod string (N.s/m).

    Gibbs (1963): damping force per unit mass = c_G * v, c_G = pi*a*nu/(2L),
    `a` = travel-time (harmonic) mean wave speed over the tapers -- exactly
    dyno.py's `a_mean` -- times the string mass (srp.rod_mass_kgm * L, which
    dyno's taper split reproduces by construction).
    """
    srp_p = params["srp"]
    L = srp_p["rod_length_m"]
    E = float(_srp_key(params, "rod_E_Pa"))
    frac = [float(f) for f in _srp_key(params, "rod_taper_frac")]
    tot = sum(frac) or 1.0
    travel = 0.0
    for d_in, f, m in zip(_srp_key(params, "rod_taper_d_in"), frac,
                          _srp_key(params, "rod_taper_mass_kgm")):
        area = math.pi / 4.0 * (float(d_in) * 0.0254) ** 2
        travel += (L * f / tot) / math.sqrt(E / (float(m) / area))
    a_mean = L / travel if travel > 0 else 4926.0
    c_g = math.pi * a_mean * float(_srp_key(params, "gibbs_damping_nu")) / (2.0 * L)
    return c_g * srp_p["rod_mass_kgm"] * L


def polished_rod_energy_J_per_stroke(
    spm: float, stroke_m: float, mu_cP: float, q_liquid_m3d: float, params: dict,
    intake_pressure_kPa: float | None = None, T_C: float | None = None,
    water_cut: float | None = None,
) -> dict:
    """Net polished-rod work per stroke: the closed-loop integral of load.dx.

    rev 10: `mu_cP` is the oil viscosity; the drag term uses the produced-
    stream viscosity rod_drag_viscosity_cP(mu_cP, params, T_C=T_C).

    Economics v2 (27 Sep 2026). Over one closed stroke the rod WEIGHT is lifted
    on the upstroke and handed back on the downstroke, and inertia is
    conservative, so both integrate to zero. What is left is what is actually
    delivered or dissipated:

      pump (hydraulic) work  dP_pump x liquid volume lifted per stroke, with
                             dP_pump = THP + rho_mix*g*L - P_intake (dyno's
                             Fo / A_plunger); a part-filled barrel (pound)
                             does proportionally less work, as on the card;
      plunger friction       2 * F_fr * S (opposes both half-strokes);
      viscous rod drag       (K_VISC*mu*L) * <v^2> * T, where for the dyno's
                             SHM + second-harmonic horsehead motion
                             <v^2> = (pi^2/8) * v_avg^2 * (1 + lambda^2/4);
      Gibbs damping          the same with the lumped Gibbs coefficient.

    Downstroke damping can consume at most the buoyant rod weight's work
    (W_rf * S): beyond that the carrier bar separates and the polished rod
    stops doing negative work (rod float).

    The pre-v2 estimate charged the PEAK upstroke load over the whole stroke
    and never credited the rod weight back: 2.0-3.6x the card area
    (docs/model-improvement/DYNO_CARD_MODEL.md). tests/test_srp.py pins this
    function to dyno.compute_cards()'s card area within 15 %.
    """
    srp_p = params["srp"]
    L = srp_p["rod_length_m"]
    wc = params_water_cut(params) if water_cut is None else min(max(float(water_cut), 0.0), 0.99)
    if intake_pressure_kPa is None:
        from twin import cycle  # lazy: cycle imports srp at module load
        intake_pressure_kPa = cycle._pump_intake_pressure_kPa(params)
    p_dis = (float(_srp_key(params, "tubing_head_pressure_kPa")) * 1e3
             + _mixture_density_kgm3(wc, params) * G * L)
    dp = max(p_dis - intake_pressure_kPa * 1e3, 0.0)

    spm = max(float(spm), 1e-9)
    strokes_per_day = spm * 1440.0
    w_pump = dp * max(q_liquid_m3d, 0.0) / strokes_per_day
    w_fric = 2.0 * float(_srp_key(params, "plunger_friction_kN")) * 1e3 * stroke_m

    period = 60.0 / spm
    v_avg = 2.0 * stroke_m / period
    lam = float(_srp_key(params, "crank_pitman_ratio"))
    v2_mean = (math.pi ** 2 / 8.0) * v_avg ** 2 * (1.0 + lam ** 2 / 4.0)
    mu_drag = rod_drag_viscosity_cP(mu_cP, params, water_cut=wc, T_C=T_C)
    c_tot = k_visc(params) * mu_drag * 1.0e-3 * L + _gibbs_damping_Ns_m(params)
    w_damp_half = 0.5 * c_tot * v2_mean * period
    w_damp = w_damp_half + min(w_damp_half, _buoyant_rod_weight_N(params) * stroke_m)
    return {"total_J": w_pump + w_fric + w_damp, "pump_J": w_pump,
            "friction_J": w_fric, "damping_J": w_damp, "dp_pump_Pa": dp}


def peak_prl_kN(spm: float, stroke_m: float, mu_drag_cP: float, water_cut: float, params: dict,
                intake_pressure_kPa: float | None = None) -> float:
    """Dynamic peak polished-rod load (kN) for the unit-rating cap (rev 11).

    Mills' (1939) acceleration factor on the rod weight, the form dyno.py
    already reports as `mills_peak_prl_kN` (API RP 11L hand method):
        PPRL = W_rf + F_o + W_r * alpha * (1 + lambda) + F_drag,peak + F_fr
        alpha = S[in] * N^2 / 70,500,   lambda = crank/pitman ratio,
    with W_rf / F_o on the tubing MIXTURE density at `water_cut` (dyno's
    static_loads) and the viscous drag at the peak polished-rod speed
    pi*S*N/60 (dyno's `viscous_drag_peak_kN`). tests/test_srp.py pins it to
    the wave-equation card peak (dyno.compute_cards) within 15 %.
    """
    srp_p = params["srp"]
    L = srp_p["rod_length_m"]
    if intake_pressure_kPa is None:
        from twin import cycle  # lazy: cycle imports srp at module load
        intake_pressure_kPa = cycle._pump_intake_pressure_kPa(params)
    rho = _mixture_density_kgm3(water_cut, params)
    w_air = srp_p["rod_mass_kgm"] * L * G
    w_rf = w_air * (1.0 - rho / RHO_STEEL_KGM3)
    a_p = math.pi / 4.0 * srp_p["plunger_d_m"] ** 2
    p_d = float(_srp_key(params, "tubing_head_pressure_kPa")) * 1e3 + rho * G * L
    f_o = max(p_d - intake_pressure_kPa * 1e3, 0.0) * a_p
    lam = float(_srp_key(params, "crank_pitman_ratio"))
    alpha = (stroke_m / INCH_M) * spm ** 2 / 70500.0
    v_peak = math.pi * stroke_m * spm / 60.0
    f_drag = k_visc(params) * mu_drag_cP * 1e-3 * L * v_peak
    f_fr = float(_srp_key(params, "plunger_friction_kN")) * 1e3
    return (w_rf + f_o + w_air * alpha * (1.0 + lam) + f_drag + f_fr) / 1000.0


# --- rev 11: stroke length as a control ---------------------------------------
# API Spec 11E standard polished-rod stroke lengths (in) spanning the C-114 to
# C-456 unit classes: 64, 74, 86, 100, 120, 144 in = 1.63-3.66 m. [SOURCED -
# API Spec 11E unit designations, e.g. C-228D-213-86, C-320D-256-120,
# C-456D-305-144: gear-reducer rating (1,000 in-lb) - structure (peak polished-
# rod load) rating (100 lb) - maximum stroke (in).]
API_STROKES_IN = (64, 74, 86, 100, 120, 144)
INCH_M = 0.0254


def stroke_options_m(params: dict) -> list[float]:
    """Discrete stroke-length control levels (m), from srp.stroke_in_options."""
    opts = params.get("srp", {}).get("stroke_in_options") or API_STROKES_IN
    return [float(i) * INCH_M for i in opts]


def max_prl_kN(params: dict) -> float | None:
    """Unit structure (peak polished-rod load) rating, srp.max_prl_kN; None = no cap."""
    v = params.get("srp", {}).get("max_prl_kN")
    return float(v) if v is not None else None


def pump_state(spm: float, stroke_m: float, mu_cP: float, rate_m3d: float, params: dict,
               intake_pressure_kPa: float | None = None, T_C: float | None = None,
               water_cut: float | None = None) -> dict:
    """Sucker-rod-pump load, energy, float and fillage at one operating point.

    Args:
        spm: strokes per minute.
        stroke_m: polished-rod stroke length (m).
        mu_cP: current in-situ oil viscosity (centipoise). rev 10: every
            rod-drag term uses rod_drag_viscosity_cP(mu_cP, params, T_C=T_C),
            the produced-stream (emulsion) viscosity, reported as mu_drag_cP.
        rate_m3d: IPR-available oil rate (m3/d) the reservoir can deliver
            at this timestep (e.g. from ipr.oil_rate_m3d).
        params: field_params.json tree (reads params["srp"], params["fluid"]).
        intake_pressure_kPa: pump-intake pressure for the hydraulic work;
            defaults to cycle._pump_intake_pressure_kPa(params).

    Returns:
        dict with keys (the first four are unchanged from before T1-E; the
        rest are additive):
            prod_rate_m3d:     min(rate_m3d, OIL capacity at this fillage and
                                water cut).
            peak_rod_load_kN:  upstroke peak polished-rod load.
            energy_kWh_d:      daily POLISHED-ROD energy. Economics v2: the
                                closed-loop card work, rod weight credited on
                                the downstroke (was peak load x stroke x spm,
                                2.0-3.6x too high).
            electric_kWh_d:    energy_kWh_d / surface_efficiency (grid kWh).
            hydraulic_kWh_d:   pump dP x liquid lifted (the useful part).
            floating_index:    v_stroke / v_fall, clipped to [0, 1]; >0.6 flags
                                floating risk (docs/SPEC.md). Value unchanged.
            fillage:           FILLAGE_MAX * lost-stroke fraction (T1-E).
            v_fall_ms:         drag-limited rod terminal fall velocity.
            v_stroke_ms:       average rod-string stroke velocity.
            descent_violation: v_stroke exceeds the 2 in/s heavy-oil limit.
            pump_capacity_m3d: displacement * fillage (LIQUID, m3/d).
            oil_capacity_m3d:  pump_capacity_m3d * (1 - fluid.water_cut).
            pump_limited:      True when the reservoir could deliver more oil
                                than the pump can lift (rev 5).
            mu_drag_cP:        produced-stream viscosity the rods see (rev 10).
        T_C: stream temperature for the water phase of the emulsion model.
    """
    srp = params["srp"]
    fluid = params["fluid"]

    rod_length_m = srp["rod_length_m"]
    plunger_d_m = srp["plunger_d_m"]

    rho_fluid = _fluid_density_kgm3(fluid["api_gravity"])
    weight_buoyant_N = _buoyant_rod_weight_N(params)

    # Fluid load: weight of the produced-fluid column lifted by the plunger.
    # ASSUMPTION: pump setting depth approximated by rod_length_m.
    plunger_area_m2 = math.pi / 4.0 * plunger_d_m ** 2
    fluid_load_N = rho_fluid * G * rod_length_m * plunger_area_m2

    # Average rod-string velocity: one stroke cycle covers 2*stroke_m of
    # travel per revolution; spm revolutions per minute.
    v_avg_ms = 2.0 * stroke_m * spm / 60.0
    # rev 11: `water_cut` is the day's produced-stream cut (cycle.py's water-cut
    # state); None = the rev <= 10 constant fluid.water_cut.
    water_cut = params_water_cut(params) if water_cut is None else min(max(float(water_cut), 0.0), 0.99)
    mu_drag_cP = rod_drag_viscosity_cP(mu_cP, params, water_cut=water_cut, T_C=T_C)
    mu_Pa_s = mu_drag_cP * 1.0e-3
    k = k_visc(params)
    viscous_drag_N = k * mu_Pa_s * v_avg_ms * rod_length_m

    # ASSUMPTION: peak (upstroke) polished-rod load = buoyant rod weight +
    # fluid load + viscous drag (drag opposes upward motion, adding to load).
    peak_rod_load_N = weight_buoyant_N + fluid_load_N + viscous_drag_N
    peak_rod_load_kN = peak_rod_load_N / 1000.0

    strokes_per_day = spm * 1440.0

    # Rod float as a VELOCITY RATIO (T1-E). Algebraically identical to the
    # previous viscous_drag / buoyant_weight, so every existing monotonicity
    # and bounds test holds exactly.
    v_fall_ms = _fall_velocity_ms(weight_buoyant_N, mu_Pa_s, rod_length_m, k)
    if weight_buoyant_N > 0:
        ratio = v_avg_ms / v_fall_ms if v_fall_ms > 0 else float("inf")
        floating_index = min(ratio, 1.0)
    else:
        ratio = float("inf")
        floating_index = 1.0  # ASSUMPTION: degenerate case, flag max risk.

    # T1-E: lost stroke -> fillage -> capacity. When the rods cannot fall as
    # fast as the horsehead descends, the plunger does not complete its travel
    # and that fraction of the displacement is simply never made.
    stroke_eff_frac = min(1.0, 1.0 / ratio) if ratio > 0 else 1.0
    fillage = FILLAGE_MAX * stroke_eff_frac

    # rev 5: the plunger displaces LIQUID (oil + water), not oil. cycle.py
    # already treats the produced stream as oil / (1 - water_cut) for the
    # Boberg-Lantz energy-removed term, so the pump must lift the same stream;
    # comparing displacement against the oil rate alone (the T1-E version)
    # overstated oil capacity by 1/(1 - water_cut) = 6.7x at 85 % cut.
    pump_capacity_m3d = plunger_area_m2 * stroke_m * strokes_per_day * fillage
    oil_capacity_m3d = pump_capacity_m3d * (1.0 - water_cut)
    prod_rate_m3d = min(max(rate_m3d, 0.0), oil_capacity_m3d)

    # Economics v2: polished-rod energy = closed-loop card work (rod weight
    # credited back on the downstroke) for the LIQUID actually lifted.
    q_liquid_m3d = prod_rate_m3d / max(1.0 - water_cut, 1e-6)
    work = polished_rod_energy_J_per_stroke(spm, stroke_m, mu_cP, q_liquid_m3d, params,
                                            intake_pressure_kPa=intake_pressure_kPa, T_C=T_C,
                                            water_cut=water_cut)
    energy_kWh_d = work["total_J"] * strokes_per_day / 3.6e6
    electric_kWh_d = energy_kWh_d / surface_efficiency(params)

    return {
        "prod_rate_m3d": prod_rate_m3d,
        "peak_rod_load_kN": peak_rod_load_kN,
        "energy_kWh_d": energy_kWh_d,
        "electric_kWh_d": electric_kWh_d,
        "hydraulic_kWh_d": work["pump_J"] * strokes_per_day / 3.6e6,
        "floating_index": floating_index,
        "fillage": fillage,
        "v_fall_ms": v_fall_ms,
        "v_stroke_ms": v_avg_ms,
        "descent_violation": bool(v_avg_ms > max(v_fall_ms, DESCENT_LIMIT_MS)),
        "pump_capacity_m3d": pump_capacity_m3d,
        "oil_capacity_m3d": oil_capacity_m3d,
        "pump_limited": bool(rate_m3d > oil_capacity_m3d),
        "mu_drag_cP": mu_drag_cP,
        # rev 11
        "water_cut": water_cut,
        "liquid_m3d": q_liquid_m3d,
        "peak_prl_kN": peak_prl_kN(spm, stroke_m, mu_drag_cP, water_cut, params,
                                   intake_pressure_kPa=intake_pressure_kPa),
    }
