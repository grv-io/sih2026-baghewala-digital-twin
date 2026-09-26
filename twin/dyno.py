"""dyno.py -- computed dynamometer cards: pump (downhole) card + surface card.

Replaces the dashboard's illustrative "lens" with a card computed from
published rod-pump mechanics. One call simulates one steady-state pumping
stroke of the whole rod string and returns the polished-rod (surface) card,
the plunger (downhole / pump) card, and a small rule-based shape diagnosis.

Method -- predictive Gibbs wave-equation model, explicit finite differences
--------------------------------------------------------------------------
The rod string is the 1-D damped wave equation of Gibbs (1963, JPT 15:769,
SPE-588-PA; srp_dynamometer_ml_deep_dive.md section 2.3), written for the
effective axial force with buoyant weight distributed along the string:

    rho*A * d2u/dt2 = d/dx( E*A * du/dx ) - w_b - (rho*A*c_G + K_VISC*mu) * du/dt

u = upward displacement, x = depth. It is discretised as a lumped-mass chain
(one node per segment end, masses/areas per taper, so the 1" x 7/8" taper
junction is exact) and advanced with central differences; the damping term is
taken at the mid-step velocity (u[n+1]-u[n-1])/2dt, which is unconditionally
stable in damping, so the scheme is stable for any viscosity as long as the
Courant number a*dt/dx <= 1 (asserted, reported as `cfl`).

* Damping. c_G = pi*a*nu/(2L) is the classical Gibbs damping with a
  dimensionless factor nu = 0.10 [TYPICAL, normal-crude range 0.05-0.15].
  The heavy-oil term is **the same Couette drag srp.py already uses**,
  F_v = K_VISC * mu * v per metre of rod (srp.k_visc(params), default 10), so
  the card and the day-by-day twin carry one viscous-drag law, not two.
  rev 10: `mu` in that law is the PRODUCED-STREAM viscosity
  srp.rod_drag_viscosity_cP(oil mu, params, water_cut) -- a Brinkman emulsion
  viscosity with a W/O -> O/W inversion point -- not the reservoir-oil
  viscosity. compute_cards() still takes the OIL viscosity (the API contract)
  and converts it internally with the same function srp.pump_state uses.
* Surface boundary = prescribed polished-rod motion of a conventional crank
  unit, "SHM + second harmonic" (slider-crank / Mills 1939 form):
      U(theta) = S/2 * [1 - cos(theta) + (lambda/2) sin^2(theta)],
  lambda = crank/pitman ratio 0.25 [TYPICAL]; peak acceleration
  (S/2)*w^2*(1+lambda) at the bottom of the stroke, as in Mills' factor.
  **Carrier-bar separation is modelled:** the polished rod can only be pulled,
  never pushed. If the load needed to make the rods follow the horsehead down
  would be negative, the clamp lifts off the carrier bar (PRL = 0) and the
  top of the string falls under its own buoyant weight against drag; it is
  re-caught when the rising carrier bar meets the clamp (impact load). This is
  the rod-float mechanism of srp_dynamometer_ml_deep_dive.md section 1.3(b)
  (US 7,547,196: "separate from a carrier bar of the pumping unit").
* Pump boundary = a travelling/standing-valve state machine on the plunger:
    UP_PICKUP   TV+SV closed, plunger held while rod stretch picks up load,
    UP          TV closed / SV open: load = Fo + friction,
    POUND       fillage < 1: plunger falls through the vapour void still
                carrying Fo, until it strikes the liquid (sharp release),
    DOWN_TRANSFER  full barrel: plunger held while the load releases,
    DOWN        TV open / SV closed: load = -friction,
    UP_GAS / DOWN_GAS  (gas_interference=True) isothermal gas in the void:
                load = (P_d - P_b(u))*A_p, released/picked up gradually.
  Fo = (P_discharge - P_intake) * A_plunger, P_discharge = THP + rho_mix*g*L,
  P_intake from cycle.py's submergence datum (same P_wf the IPR sees).

It is *predictive* (surface motion in, both cards out) -- the design mode of
Gibbs' method. Commercial controllers run the same equation in the diagnostic
direction (measured surface card in, pump card out).

Validation lives in tests/test_dyno.py and docs/model-improvement/
DYNO_CARD_MODEL.md: static limit vs W_rf + Fo, SPM/inertia trend vs Mills,
fluid-pound step, rod-float onset vs srp.floating_index, energy balance
(card area = pump work + damping dissipation), and the CFL bound.

Limits (see the doc): single-phase liquid column with a lumped gas option, no
tubing stretch (anchored tubing), vertical well (no rod-tubing Coulomb
friction), tubing-flow pressure drop ignored, linear (Gibbs) damping extended
by a linear heavy-oil drag, rod string and unit geometry [TYPICAL] not
Baghewala's.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from twin import cycle, srp

INCH = 0.0254

# Target Courant number a*dt/dx for the explicit scheme (<= 1 required).
CFL_TARGET = 0.95
# Rod-string discretisation: total segments over the two tapers. 14 segments
# (~82 m each) resolve the first ~7 longitudinal modes of a 1,150 m string
# (fundamental ~1 Hz vs a 0.03-0.2 Hz pumping frequency) and keep one card
# under ~50 ms. Grid study (DYNO_CARD_MODEL.md): peak PRL moves < 0.5 kN
# between 14 and 40 segments on full-pump cards.
N_SEGMENTS = 14
# Periodic steady state: strokes are repeated until peak/min/mean PRL and the
# plunger stroke of two successive strokes agree to this fraction of the peak
# load (stroke length for the plunger).
CONVERGENCE_TOL = 5e-3
MAX_CYCLES = 8
# Plunger-velocity dead band for valve-state reversals (m/s).
_EPS_V = 1e-3

# ASSUMPTION: gas-filled dead volume below the plunger at the bottom of the
# stroke, as a fraction of the swept volume, used only when
# gas_interference=True (upstroke re-expansion -> rounded pickup corner).
GAS_DEAD_FRAC = 0.02

# Rule-based classifier thresholds (see classify_card).
FULL_PUMP_FILLAGE = 0.90          # card fillage at/above which the pump is "full"
VISCOUS_EXCESS_RATIO = 0.30       # (surface gap - pump gap) over mid-stroke / W_rf
HEAVY_DRAG_RATIO = 0.10           # guard: heavy-oil drag at peak rod speed / W_rf
FLOAT_MIN_PRL_RATIO = 0.05        # min PRL <= 5 % of W_rf counts as slack rods
GAS_RELEASE_FRAC = 0.10           # >10 % of stroke to release load = cushioned (gas)

# Pump-state codes.
_UP_PICKUP, _UP, _POUND, _DOWN_TRANSFER, _DOWN, _UP_GAS, _DOWN_GAS = range(7)
_FROZEN = (_UP_PICKUP, _DOWN_TRANSFER)

# Defaults mirror params/field_params.json srp block (used if a key is absent).
_SRP_DEFAULTS = {
    "rod_taper_d_in": [1.0, 0.875],
    "rod_taper_frac": [0.485, 0.515],
    "rod_taper_mass_kgm": [4.322, 3.310],
    "rod_E_Pa": 2.07e11,
    "gibbs_damping_nu": 0.10,
    "crank_pitman_ratio": 0.25,
    "tubing_head_pressure_kPa": 300.0,
    "plunger_friction_kN": 0.9,
}


def _srp_get(params: dict, key: str):
    return params["srp"].get(key, _SRP_DEFAULTS[key])


def mixture_density_kgm3(water_cut: float, params: dict) -> float:
    """Produced-liquid density in the tubing (oil + water at `water_cut`)."""
    wc = min(max(float(water_cut), 0.0), 0.99)
    return wc * 1000.0 + (1.0 - wc) * srp._fluid_density_kgm3(params["fluid"]["api_gravity"])


def rod_string(params: dict, depth_m: float | None = None) -> dict:
    """Tapered rod string: per-taper length, area, mass, wave speed.

    Taper split [TYPICAL]: 1" over 7/8" (API "87"-class), fractions chosen so
    the mass-weighted mean equals srp.rod_mass_kgm, i.e. both models carry the
    identical buoyant rod weight. Rod masses include couplings (API RP 11B
    tabulated 2.904 / 2.224 lb/ft); effective density = mass / steel area, so
    a ~= 4,930 m/s, the usual ~16,000 ft/s for coupled steel rods.
    """
    L = float(depth_m if depth_m is not None else params["srp"]["rod_length_m"])
    d_in = list(_srp_get(params, "rod_taper_d_in"))
    frac = np.asarray(_srp_get(params, "rod_taper_frac"), dtype=float)
    frac = frac / frac.sum()
    mass = list(_srp_get(params, "rod_taper_mass_kgm"))
    E = float(_srp_get(params, "rod_E_Pa"))
    tapers = []
    for d, f, m in zip(d_in, frac, mass):
        area = math.pi / 4.0 * (d * INCH) ** 2
        tapers.append({
            "d_in": d, "length_m": L * f, "area_m2": area, "mass_kgm": m,
            "wave_speed_ms": math.sqrt(E / (m / area)),
        })
    return {"length_m": L, "E_Pa": E, "tapers": tapers}


def static_loads(water_cut: float, params: dict, depth_m: float | None = None) -> dict:
    """Static reference loads (N): air rod weight, buoyant weight, fluid load."""
    rs = rod_string(params, depth_m)
    L = rs["length_m"]
    rho_mix = mixture_density_kgm3(water_cut, params)
    w_air = sum(t["mass_kgm"] * t["length_m"] for t in rs["tapers"]) * srp.G
    w_rf = w_air * (1.0 - rho_mix / srp.RHO_STEEL_KGM3)
    a_p = math.pi / 4.0 * params["srp"]["plunger_d_m"] ** 2
    p_i = cycle._pump_intake_pressure_kPa(params) * 1e3
    p_d = float(_srp_get(params, "tubing_head_pressure_kPa")) * 1e3 + rho_mix * srp.G * L
    return {
        "W_r_N": w_air, "W_rf_N": w_rf, "Fo_N": (p_d - p_i) * a_p,
        "P_discharge_Pa": p_d, "P_intake_Pa": p_i, "A_plunger_m2": a_p,
        "rho_mix_kgm3": rho_mix,
        "rod_stretch_m": (p_d - p_i) * a_p * sum(t["length_m"] / (rs["E_Pa"] * t["area_m2"]) for t in rs["tapers"]),
    }


def carrier_position(theta: np.ndarray, stroke_m: float, lam: float) -> np.ndarray:
    """Polished-rod position (m above bottom of stroke) vs crank angle (rad)."""
    return 0.5 * stroke_m * (1.0 - np.cos(theta) + 0.5 * lam * np.sin(theta) ** 2)


def _simulate(spm, stroke_m, mu_cP, fillage, water_cut, params, depth_m, gas_interference):
    """Run the FD model to periodic steady state; return last-cycle series."""
    rs = rod_string(params, depth_m)
    st = static_loads(water_cut, params, depth_m)
    L = rs["length_m"]
    E = rs["E_Pa"]

    # --- grid: per-taper segments with a common dt (Courant <= 1 everywhere)
    seg_len, seg_EA, seg_m = [], [], []
    for tp in rs["tapers"]:
        n_i = max(2, int(round(N_SEGMENTS * tp["length_m"] / L)))
        dx = tp["length_m"] / n_i
        seg_len += [dx] * n_i
        seg_EA += [E * tp["area_m2"]] * n_i
        seg_m += [tp["mass_kgm"]] * n_i
    seg_len, seg_EA, seg_m = map(np.asarray, (seg_len, seg_EA, seg_m))
    a_seg = np.sqrt(seg_EA / (seg_m))  # E*A / (m) = E/rho_eff
    dt_cfl = float(np.min(seg_len / a_seg))
    period = 60.0 / spm
    steps = int(math.ceil(period / (CFL_TARGET * dt_cfl)))
    dt = period / steps
    cfl = float(np.max(a_seg * dt / seg_len))

    nn = len(seg_len) + 1
    k = seg_EA / seg_len
    M = np.zeros(nn)
    ell = np.zeros(nn)
    M[:-1] += 0.5 * seg_m * seg_len
    M[1:] += 0.5 * seg_m * seg_len
    ell[:-1] += 0.5 * seg_len
    ell[1:] += 0.5 * seg_len
    buoy = 1.0 - st["rho_mix_kgm3"] / srp.RHO_STEEL_KGM3
    W = M * srp.G * buoy
    a_mean = float(np.sum(seg_len) / np.sum(seg_len / a_seg))
    c_gibbs = math.pi * a_mean * float(_srp_get(params, "gibbs_damping_nu")) / (2.0 * L)
    # rev 10: mu_cP arriving here is already the produced-stream DRAG
    # viscosity (compute_cards converts); k from params (srp.k_visc).
    c_visc = srp.k_visc(params) * mu_cP * 1e-3  # N.s/m per metre of rod (srp.py F_v law)
    C = c_gibbs * M + c_visc * ell
    denom = M + 0.5 * C * dt
    A1 = 2.0 * M / denom
    A2 = (M - 0.5 * C * dt) / denom
    A3 = dt * dt / denom

    lam = float(_srp_get(params, "crank_pitman_ratio"))
    theta = 2.0 * math.pi * np.arange(steps + 1) / steps
    Uc = carrier_position(theta, stroke_m, lam)

    Fo = st["Fo_N"]
    F_fr = float(_srp_get(params, "plunger_friction_kN")) * 1e3
    F_up, F_dn = Fo + F_fr, -F_fr
    A_p, P_d, P_i = st["A_plunger_m2"], st["P_discharge_Pa"], st["P_intake_Pa"]
    fill = min(max(float(fillage), 0.0), 1.0)
    full = fill >= 0.995 and not gas_interference

    # --- initial state: static hang at bottom of stroke, TV open (load 0)
    T0 = np.cumsum(W[::-1])[::-1][1:]  # tension in segment j = weight of nodes below
    u = np.zeros(nn)
    u[1:] = -np.cumsum(T0 / k)
    u_prev = u.copy()
    state = _UP_GAS if gas_interference else _UP_PICKUP
    u_bot = u[-1]
    u_top = -1e9
    u_pound = -1e9
    V_dead = GAS_DEAD_FRAC * A_p * stroke_m
    gas_ref = (P_d, V_dead, u_bot)  # (P_ref, V_ref, u_ref) isothermal gas
    attached = True

    # Tridiagonal update matrix: u_new = B @ u - A2*u_prev + A3*(-W) (+ pump force)
    K = np.zeros((nn, nn))
    for j, kj in enumerate(k):
        K[j, j] -= kj
        K[j + 1, j + 1] -= kj
        K[j, j + 1] += kj
        K[j + 1, j] += kj
    B = np.diag(A1) + A3[:, None] * K
    # One matvec per step on the stacked state z = [u, u_prev, 1]:
    # z_new = G @ z = [B u - A2 u_prev - A3 W, u, 1]; BCs then patch z_new.
    G = np.zeros((2 * nn + 1, 2 * nn + 1))
    G[:nn, :nn] = B
    G[:nn, nn:2 * nn] = -np.diag(A2)
    G[:nn, -1] = -A3 * W
    G[nn:2 * nn, :nn] = np.eye(nn)
    G[-1, -1] = 1.0
    z = np.concatenate([u, u_prev, [1.0]])
    iN, iNm1, iP0 = nn - 1, nn - 2, nn
    k0, kN = float(k[0]), float(k[-1])
    W0, M0, C0 = float(W[0]), float(M[0]), float(C[0])
    WN, A3N = float(W[-1]), float(A3[-1])
    dt2 = dt * dt
    prev_prl = None
    converged = False
    for cyc in range(MAX_CYCLES):
        prl = np.empty(steps)
        fp_s = np.empty(steps)
        uN_s = np.empty(steps)
        det_s = np.zeros(steps, dtype=bool)
        hist = np.empty((steps + 2, nn))
        hist[0] = z[nn:2 * nn]
        for n in range(steps):
            hist[n + 1] = z[:nn]
            uN = z[iN]
            TN = kN * (z[iNm1] - uN)
            # ---- pump boundary force
            if state == _UP_PICKUP or state == _DOWN_TRANSFER:
                R = TN - WN
                if R >= F_up:
                    state = _UP
                elif R <= F_dn:
                    state = _DOWN
            if state == _UP:
                fp = F_up
            elif state == _DOWN:
                fp = F_dn
            elif state == _POUND:
                fp = Fo - F_fr
            elif state == _UP_GAS or state == _DOWN_GAS:
                P_ref, V_ref, u_ref = gas_ref
                V = max(V_ref + A_p * (uN - u_ref), 1e-12)
                Pb = min(max(P_ref * V_ref / V, P_i), P_d)
                fp = A_p * (P_d - Pb) + (F_fr if state == _UP_GAS else -F_fr)
            else:
                fp = TN - WN  # frozen: reaction at the held plunger
            u_new = G @ z
            if state == _UP_PICKUP or state == _DOWN_TRANSFER:
                u_new[iN] = uN
            else:
                u_new[iN] -= A3N * fp
            # ---- surface boundary: carrier bar can pull, never push
            Un1 = Uc[n + 1]
            u0, up0 = z[0], z[iP0]
            if attached or u_new[0] <= Un1:
                p = (M0 * (Un1 - 2.0 * u0 + up0) / dt2 + C0 * (Un1 - up0) / (2.0 * dt)
                     + W0 + k0 * (u0 - z[1]))
                if p < 0.0 and attached:
                    attached = False          # clamp lifts off the carrier bar
                    u_new[0] = max(u_new[0], Un1)
                    p = 0.0
                else:
                    attached = True           # (re)caught by the carrier bar
                    u_new[0] = Un1
                    p = max(p, 0.0)
            else:
                p = 0.0
            # ---- valve logic on the moving plunger
            uN1 = u_new[iN]
            v_p = (uN1 - uN) / dt
            if state == _UP:
                if v_p < -_EPS_V:
                    # Barrel contents are set by the highest plunger position of
                    # this stroke; a ringing-induced flicker (UP -> POUND -> UP)
                    # below that point must not move the liquid level.
                    u_top = max(u_top, uN)
                    s_p = max(u_top - u_bot, 1e-6)
                    if gas_interference:
                        gas_ref = (P_i, (1.0 - fill) * A_p * s_p + V_dead, u_top)
                        state = _DOWN_GAS
                    elif full:
                        state = _DOWN_TRANSFER
                        u_new[iN] = uN
                    else:
                        u_pound = u_top - (1.0 - fill) * s_p
                        state = _POUND
            elif state == _POUND:
                if uN1 <= u_pound:
                    state = _DOWN             # plunger strikes the liquid: TV opens
                elif v_p > _EPS_V:
                    state = _UP               # turned before striking liquid
            elif state == _DOWN:
                if v_p > _EPS_V:
                    u_bot = uN
                    u_top = -1e9
                    if gas_interference:
                        gas_ref = (P_d, V_dead, u_bot)
                        state = _UP_GAS
                    else:
                        state = _UP_PICKUP
                        u_new[iN] = uN
            elif state == _DOWN_GAS or state == _UP_GAS:
                P_ref, V_ref, u_ref = gas_ref
                V = max(V_ref + A_p * (uN1 - u_ref), 1e-12)
                Pb = P_ref * V_ref / V
                if state == _DOWN_GAS:
                    if Pb >= P_d:
                        state = _DOWN         # gas compressed to P_d: TV opens
                    elif v_p > _EPS_V:
                        gas_ref = (Pb, V, uN1)
                        state = _UP_GAS
                else:
                    if Pb <= P_i:
                        state = _UP           # gas expanded to P_i: SV opens
                    elif v_p < -_EPS_V:
                        gas_ref = (Pb, V, uN1)
                        state = _DOWN_GAS
            prl[n] = p
            fp_s[n] = fp
            uN_s[n] = uN
            det_s[n] = not attached
            z = u_new
        hist[steps + 1] = z[:nn]
        # Periodic steady state, judged on what a card reader sees: peak, min
        # and mean PRL and the plunger stroke. (A pointwise trace test never
        # settles on fluid-pound cards: the pound instant jitters by one dt.)
        metrics = np.array([prl.max(), prl.min(), prl.mean(), uN_s.max() - uN_s.min()])
        if prev_prl is not None:
            scale = np.array([prl.max(), prl.max(), prl.max(), stroke_m])
            if np.all(np.abs(metrics - prev_prl) <= CONVERGENCE_TOL * scale):
                converged = True
                break
        prev_prl = metrics
    body = hist[1:-1]
    vel = (hist[2:] - hist[:-2]) / (2.0 * dt)
    damp_E = float(np.sum((vel * vel) @ C) * dt)
    tension = k[None, :] * (body[:, :-1] - body[:, 1:])
    return {
        "theta": theta[:-1], "Uc": Uc[:-1], "prl": prl, "fp": fp_s, "uN": uN_s,
        "detached": det_s, "tmin": tension.min(axis=1), "damp_E": damp_E,
        "dt": dt, "steps": steps, "cfl": cfl, "cycles": cyc + 1, "converged": converged,
        "c_gibbs": c_gibbs, "c_visc": c_visc, "static": st, "rod_string": rs,
        "M_total": float(M.sum()), "L_rod": float(ell.sum()),
        "comp_len": float(((tension < 0.0) * seg_len[None, :]).sum(axis=1).max()),
    }


def _loop_work(x: np.ndarray, f: np.ndarray) -> float:
    """Closed-loop integral of f dx (J) over one periodic stroke."""
    x2 = np.append(x, x[0])
    f2 = np.append(f, f[0])
    return float(np.sum(0.5 * (f2[1:] + f2[:-1]) * np.diff(x2)))


def _branches(x: np.ndarray, f: np.ndarray):
    """Split a closed card into (upstroke, downstroke) arrays sorted by x."""
    n = len(x)
    i_top, i_bot = int(np.argmax(x)), int(np.argmin(x))
    up = (np.arange(i_bot, i_bot + ((i_top - i_bot) % n) + 1)) % n
    dn = (np.arange(i_top, i_top + ((i_bot - i_top) % n) + 1)) % n
    out = []
    for idx in (up, dn):
        xs, fs = x[idx], f[idx]
        o = np.argsort(xs, kind="stable")
        out.append((xs[o], fs[o]))
    return out


def _mean_gap(x: np.ndarray, f: np.ndarray, lo: float = 0.25, hi: float = 0.75) -> float:
    """Mean (upstroke - downstroke) load over the middle of the stroke.

    Averaging over 25-75 % of the travel suppresses the stress-wave ringing
    that a single mid-point sample picks up at higher N/No."""
    (xu, fu), (xd, fd) = _branches(x, f)
    x0, span = float(x.min()), float(x.max() - x.min())
    q = x0 + span * np.linspace(lo, hi, 21)
    return float(np.mean(np.interp(q, xu, fu) - np.interp(q, xd, fd)))


def classify_card(card: dict) -> tuple[str, str, list[str], dict]:
    """Rule-based card diagnosis from card-shape features.

    Features (all read off the computed cards, as an analyst would):
      * slack rods: carrier-bar separation or min PRL <= 5 % of W_rf, called
        rod float only when the heavy-oil drag guard below also holds,
      * viscous excess: (surface up-down load gap - pump gap), averaged over
        25-75 % of the stroke, over W_rf -- the rod-string friction band that
        a pump card strips out (srp deep dive 2.2 "fat and tilted" card).
        Inertia peaks at the stroke ENDS and drag at MID-stroke, which is why
        the mid-stroke band isolates drag. Guarded by the heavy-oil drag law
        itself (K_VISC*mu*L*v_peak >= 10 % of W_rf) so wave ringing at high
        N/No on a thin-oil well is never called "viscous".
      * card fillage: plunger travel on the downstroke before the pump load
        falls below Fo/2, over plunger stroke (pump-off / fluid pound),
      * release travel: plunger travel for the pump load to fall 90 %->10 %
        of Fo, over stroke -- sharp = liquid pound, gradual = gas cushion.

    Priority: rod_float > heavy_oil_viscous > gas_interference > fluid_pound >
    full_pump. Returns (card_type, human label, all signatures, features).
    """
    x_s, f_s = card["_x_s"], card["_f_s"]
    x_p, f_p = card["_x_p"], card["_f_p"]
    w_rf, fo = card["buoyant_rod_weight_kN"], card["fluid_load_kN"]
    s_p = max(float(x_p.max() - x_p.min()), 1e-6)

    gap_s = _mean_gap(x_s, f_s)
    gap_p = _mean_gap(x_p, f_p)
    viscous_excess = (gap_s - gap_p) / max(w_rf, 1e-6)
    drag_ratio = card["viscous_drag_peak_kN"] / max(w_rf, 1e-6)

    # downstroke of the pump card, top -> bottom
    i_top = int(np.argmax(x_p))
    xd = np.r_[x_p[i_top:], x_p[:i_top]]
    fd = np.r_[f_p[i_top:], f_p[:i_top]]
    i_bot = int(np.argmin(xd))
    xd, fd = xd[: i_bot + 1], fd[: i_bot + 1]
    top = xd[0]

    def travel_until(level):
        below = np.nonzero(fd < level)[0]
        return float(top - xd[below[0]]) if len(below) else s_p

    card_fill = min(1.0, max(0.0, 1.0 - travel_until(0.5 * fo) / s_p))
    release = max(0.0, travel_until(0.1 * fo) - travel_until(0.9 * fo)) / s_p

    # Slack rods are called ROD FLOAT only when the heavy-oil drag is material;
    # a thin-oil card that unloads from pound/inertia shock is not rod float.
    slack = (card["carrier_separation"] or card["min_prl_kN"] <= FLOAT_MIN_PRL_RATIO * w_rf)         and drag_ratio >= HEAVY_DRAG_RATIO
    sigs = []
    if slack:
        sigs.append("rod_float")
    if viscous_excess >= VISCOUS_EXCESS_RATIO and drag_ratio >= HEAVY_DRAG_RATIO:
        sigs.append("heavy_oil_viscous")
    if card_fill < FULL_PUMP_FILLAGE and release > GAS_RELEASE_FRAC:
        sigs.append("gas_interference")
    elif card_fill < FULL_PUMP_FILLAGE:
        sigs.append("fluid_pound")
    ctype = sigs[0] if sigs else "full_pump"

    if card_fill >= FULL_PUMP_FILLAGE:
        sev = ""
    elif card_fill >= 0.75:
        sev = "mild"
    elif card_fill >= 0.5:
        sev = "moderate"
    else:
        sev = "severe"
    fill_txt = f"{100 * card_fill:.0f} % fillage"
    names = {
        "full_pump": "Full pump",
        "fluid_pound": f"Fluid pound ({sev}, {fill_txt})",
        "gas_interference": f"Gas interference ({fill_txt})",
        "heavy_oil_viscous": "Heavy-oil viscous drag",
        "rod_float": "Rod float (carrier-bar separation)" if card["carrier_separation"] else "Rod float (rods unloading)",
    }
    label = names[ctype]
    extra = [names[s].split(" (")[0].lower() for s in sigs[1:]]
    if ctype == "heavy_oil_viscous" and "fluid_pound" in sigs:
        extra = [f"fluid pound {fill_txt}"]
    if extra:
        label += " + " + ", ".join(extra)
    feats = {"viscous_excess": viscous_excess, "card_fillage": card_fill,
             "release_travel_frac": release, "gap_surface_kN": gap_s, "gap_pump_kN": gap_p,
             "heavy_drag_ratio": drag_ratio}
    return ctype, label, sigs or ["full_pump"], feats


def compute_cards(spm: float, stroke_m: float, mu_cP: float, fillage: float,
                  water_cut: float, params: dict, depth_m: float | None = None,
                  *, gas_interference: bool = False, n_points: int = 200,
                  T_C: float | None = None) -> dict:
    """Surface + downhole dynamometer card for one steady-state stroke.

    Args:
        spm: strokes per minute (> 0).
        stroke_m: polished-rod stroke (m).
        mu_cP: oil viscosity (cP). rev 10: converted to the produced-stream
            drag viscosity srp.rod_drag_viscosity_cP(mu_cP, params,
            water_cut=water_cut, T_C=T_C) -- echoed as inputs.mu_drag_cP --
            which is what drives the rod-string viscous drag.
        fillage: liquid fill fraction of the plunger's swept volume (0-1].
            < 1 gives a fluid-pound void (or a gas void if gas_interference).
        water_cut: tubing-liquid water cut (sets column density and buoyancy).
        params: field_params.json tree.
        depth_m: pump depth; defaults to srp.rod_length_m.
        gas_interference: fill the void with free gas at intake pressure
            (cushioned release) instead of vapour (sharp pound).
        n_points: samples per card (uniform in crank angle).
        T_C: stream temperature (water phase of the emulsion model); default
            reservoir temperature.

    Returns dict (loads kN, positions m): position_m (polished rod),
    load_surface_kN, plunger_position_m, load_downhole_kN, peak_prl_kN,
    min_prl_kN, pump_fillage, plunger_stroke_m, card_type, card_label,
    signatures, fluid_load_kN, buoyant_rod_weight_kN, rod_weight_air_kN,
    dynamic_factor (peak PRL / (W_rf + Fo)), mills_peak_prl_kN,
    mills_min_prl_kN, carrier_separation, separation_frac, min_rod_force_kN
    (most compressive effective force anywhere in the string over the stroke),
    max_compression_length_m (longest string length in compression at once),
    card_area_kJ, pump_work_kJ, damping_loss_kJ, polished_rod_kW,
    hydraulic_kW, energy_balance_err, features, cfl, dt_s, cycles, converged,
    inputs (echo of the call).
    """
    if spm <= 0 or stroke_m <= 0:
        raise ValueError("compute_cards needs spm > 0 and stroke_m > 0")
    mu_drag = srp.rod_drag_viscosity_cP(float(mu_cP), params, water_cut=float(water_cut), T_C=T_C)
    sim = _simulate(float(spm), float(stroke_m), float(mu_drag), float(fillage),
                    float(water_cut), params, depth_m, bool(gas_interference))
    st = sim["static"]
    steps = sim["steps"]
    # Positions: the dynamometer's position channel follows the horsehead
    # (beam inclinometer); during separation the load cell reads zero.
    x_s = sim["Uc"]
    f_s = sim["prl"] / 1e3
    x_p = sim["uN"] - sim["uN"].min()
    f_p = sim["fp"] / 1e3

    idx = np.linspace(0.0, steps, n_points, endpoint=False)
    grid = np.arange(steps)

    def rs(a):
        return np.interp(idx, grid, a)

    w_surf = _loop_work(x_s, sim["prl"])
    w_pump = _loop_work(sim["uN"], sim["fp"])
    period = 60.0 / spm
    s_p = float(x_p.max())
    w_r = st["W_r_N"]
    lam = float(_srp_get(params, "crank_pitman_ratio"))
    alpha = (stroke_m / INCH) * spm ** 2 / 70500.0  # Mills acceleration factor
    peak = float(f_s.max())
    mn = float(f_s.min())
    out = {
        "position_m": rs(x_s).tolist(),
        "load_surface_kN": rs(f_s).tolist(),
        "plunger_position_m": rs(x_p).tolist(),
        "load_downhole_kN": rs(f_p).tolist(),
        "peak_prl_kN": peak,
        "min_prl_kN": mn,
        "pump_fillage": float(fillage),
        "plunger_stroke_m": s_p,
        "fluid_load_kN": st["Fo_N"] / 1e3,
        "buoyant_rod_weight_kN": st["W_rf_N"] / 1e3,
        "rod_weight_air_kN": w_r / 1e3,
        "static_peak_kN": (st["W_rf_N"] + st["Fo_N"]) / 1e3,
        "dynamic_factor": peak / ((st["W_rf_N"] + st["Fo_N"]) / 1e3),
        "mills_peak_prl_kN": (st["W_rf_N"] + st["Fo_N"] + w_r * alpha * (1 + lam)) / 1e3,
        "mills_min_prl_kN": (st["W_rf_N"] - w_r * alpha * (1 - lam)) / 1e3,
        "static_rod_stretch_m": st["rod_stretch_m"],
        "carrier_separation": bool(sim["detached"].any()),
        "separation_frac": float(sim["detached"].mean()),
        "min_rod_force_kN": float(sim["tmin"].min()) / 1e3,
        "max_compression_length_m": sim["comp_len"],
        "card_area_kJ": w_surf / 1e3,
        "pump_work_kJ": w_pump / 1e3,
        "damping_loss_kJ": sim["damp_E"] / 1e3,
        "polished_rod_kW": w_surf / period / 1e3,
        "hydraulic_kW": st["Fo_N"] * s_p * min(float(fillage), 1.0) / period / 1e3,
        "energy_balance_err": (w_surf - w_pump - sim["damp_E"]) / max(abs(w_surf), 1e-9),
        "viscous_drag_peak_kN": (sim["c_visc"] * sim["L_rod"]) * math.pi * stroke_m * spm / 60.0 / 1e3,
        "gibbs_c_per_s": sim["c_gibbs"],
        "cfl": sim["cfl"],
        "dt_s": sim["dt"],
        "cycles": sim["cycles"],
        "converged": sim["converged"],
        "inputs": {"spm": float(spm), "stroke_m": float(stroke_m), "mu_cP": float(mu_cP),
                   "mu_drag_cP": float(mu_drag),
                   "fillage": float(fillage), "water_cut": float(water_cut),
                   "gas_interference": bool(gas_interference),
                   "depth_m": float(sim["rod_string"]["length_m"])},
        "_x_s": x_s, "_f_s": f_s, "_x_p": x_p, "_f_p": f_p,
    }
    ctype, label, sigs, feats = classify_card(out)
    out.update({"card_type": ctype, "card_label": label, "signatures": sigs, "features": feats})
    for key in ("_x_s", "_f_s", "_x_p", "_f_p"):
        out.pop(key)
    return out


def fillage_for_rate(q_liquid_m3d: float, spm: float, plunger_stroke_m: float, params: dict) -> float:
    """Liquid fill fraction that makes the plunger displace `q_liquid_m3d`."""
    a_p = math.pi / 4.0 * params["srp"]["plunger_d_m"] ** 2
    disp = a_p * max(plunger_stroke_m, 1e-6) * spm * 1440.0
    return float(min(1.0, max(0.05, q_liquid_m3d / disp)))


def card_for_row(row, params: dict, *, spm: float | None = None, n_points: int = 200,
                 stroke_m: float | None = None) -> dict:
    """Card at one produce-day row of a cycle.simulate_css_cycle() frame.

    Pump fillage is set from the day's produced LIQUID rate over the plunger's
    displacement (the pump is part-empty whenever the reservoir, not the pump,
    sets the rate). The plunger stroke is first estimated as surface stroke
    minus static fluid-load stretch, then corrected once from the FD result.
    `spm` overrides the scheduled speed (e.g. the 12-SPM stress case).
    rev 11: the row's own produced-stream water cut (cycle.py water-cut state)
    when the frame carries it, and `stroke_m` (the cycle's stroke control,
    df.attrs["stroke_m"]) when given.
    """
    wc_row = row["water_cut"] if "water_cut" in row else None
    if wc_row is not None and float(wc_row) > 0.0:
        wc = float(wc_row)
    else:
        wc = float(params["fluid"].get("water_cut", cycle.DEFAULT_WATER_CUT))
    stroke = float(stroke_m) if stroke_m is not None else params["srp"]["stroke_m"]
    spm_run = float(spm if spm is not None else row["spm"])
    q_liq = float(row["oil_m3d"]) / max(1.0 - wc, 1e-6)
    s_est = max(stroke - static_loads(wc, params)["rod_stretch_m"], 0.1 * stroke)
    f = fillage_for_rate(q_liq, spm_run, s_est, params)
    T_row = row["T_res_C"] if "T_res_C" in row else None
    T_row = float(T_row) if T_row is not None else None
    card = compute_cards(spm_run, stroke, float(row["mu_cP"]), f, wc, params, n_points=n_points, T_C=T_row)
    f2 = fillage_for_rate(q_liq, spm_run, card["plunger_stroke_m"], params)
    if abs(f2 - f) > 0.02:
        card = compute_cards(spm_run, stroke, float(row["mu_cP"]), f2, wc, params, n_points=n_points,
                             T_C=T_row)
    return card


def cards_along_cycle(df: pd.DataFrame, params: dict, n_days: int = 8,
                      days: list[float] | None = None) -> pd.DataFrame:
    """Card metrics at `n_days` evenly spaced produce days (or given `days`)."""
    prod = df[df["phase"] == "produce"].reset_index(drop=True)
    if prod.empty:
        return pd.DataFrame()
    if days is not None:
        idx = sorted({int(np.argmin(np.abs(prod["day"].to_numpy() - d))) for d in days})
    else:
        idx = sorted(set(np.linspace(0, len(prod) - 1, min(n_days, len(prod))).round().astype(int)))
    rows = []
    for i in idx:
        r = prod.iloc[i]
        c = card_for_row(r, params, n_points=60, stroke_m=df.attrs.get("stroke_m"))
        rows.append({
            "day": float(r["day"]), "mu_cP": float(r["mu_cP"]), "spm": float(r["spm"]),
            "floating_index": float(r["floating_index"]), "srp_peak_kN": float(r["rod_load_kN"]),
            "pump_fillage": c["pump_fillage"], "peak_prl_kN": c["peak_prl_kN"],
            "min_prl_kN": c["min_prl_kN"], "plunger_stroke_m": c["plunger_stroke_m"],
            "carrier_separation": c["carrier_separation"], "card_type": c["card_type"],
            "card_label": c["card_label"],
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Dashboard export
# --------------------------------------------------------------------------
BAKE_SCENARIOS = {
    # rev 13 (physics wave 5, TIER1_PROGRESS_LOG.md section 12.3/12.5):
    # published-practice baseline (b), 86-in unit at the CONFIRMED wellhead
    # mid (91 kgf/cm2), operated VFD-hold (the recommended policy) --
    # unchanged steam/soak/cutoff/start-spm from rev 12, now under the
    # operating policy that actually erases the rev-12 pull-rule gain.
    "baseline": {"steam_t": 1300.0, "soak_days": 10.0, "cutoff_m3d": 1.3, "spm": 5.0,
                "stroke_in": 86.0, "p_wellhead_kgf_cm2": 91.0, "float_policy": "vfd_hold"},
    # rev-13 canonical (1,000 t / 10 d / cutoff 0.60 backstop / start 4.5 spm /
    # 64-in stroke / 89 kgf/cm2 / VFD-hold), TIER1 section 12.5 -- supersedes
    # the rev-12 1,000/0.60/3 spm/85 point.
    "recommendation": {"steam_t": 1000.0, "soak_days": 10.0, "cutoff_m3d": 0.60, "spm": 4.5,
                       "stroke_in": 64.0, "p_wellhead_kgf_cm2": 89.0, "float_policy": "vfd_hold"},
}
STRESS_SPM = 12.0


def _r(a, nd):
    return [round(float(v), nd) for v in a]


def _float_onset_index(prod: pd.DataFrame) -> int:
    """Index (into `prod`) of the day the float-onset rule FIRES: the first
    produce day with floating_index > cycle.FLOATING_RISK_THRESHOLD (rev 12:
    "the day the rule fires, oil-continuous, FI ~ 0.6" -- TIER1
    section 11.3's fi_alarm line, css.fi_alarm/FLOATING_RISK_THRESHOLD = 0.6).
    Falls back to the last produce day if the cycle never crosses it (e.g. a
    cycle that ends on the plain rate cutoff first)."""
    fi = prod["floating_index"].to_numpy()
    alarm = fi > cycle.FLOATING_RISK_THRESHOLD
    if alarm.any():
        return int(alarm.argmax())
    return len(prod) - 1


def _vfd_hold_day_index(prod: pd.DataFrame, spm_start: float) -> int:
    """Index (into `prod`) of a representative "VFD-hold" day (rev 13): the
    VFD has slowed the unit below its start SPM to hold the float index at
    css.vfd_hold_fi (0.6), well before the eventual pull at the floor
    (TIER1_PROGRESS_LOG.md section 12.3: "the VFD holds FI exactly on the 0.6
    alarm line for ~60 days"). Picked as the MIDPOINT of the days the
    schedule has already slowed below spm_start, so the card is neither the
    onset transient nor the terminal floor day. Falls back to the last
    produce day if the schedule never slows (e.g. the `pull`/`none`
    policies, where SPM stays at the physical keep-up limit throughout)."""
    spm = prod["spm"].to_numpy()
    reduced = spm < (float(spm_start) - 1e-6)
    if reduced.any():
        idx = np.flatnonzero(reduced)
        return int(idx[len(idx) // 2])
    return len(prod) - 1


def bake(params: dict, n_points: int = 200) -> dict:
    """Cards for the baseline and recommendation cycles at 4 days each:
    early_hot, mid, vfd_hold_day (rev 13: a representative day while the VFD
    is actively holding the float index at 0.6 with SPM reduced below the
    start speed -- TIER1_PROGRESS_LOG.md section 12.3/12.5; replaces the
    rev-12 "float_onset" pick, which was the pull-rule alarm day and no
    longer describes what happens under the recommended vfd_hold policy) and
    a 12-SPM stress test at the last produce day."""
    out = {
        "schema": "dyno_cards/v1",
        "method": "Predictive Gibbs (1963) damped wave equation, explicit FD, "
                  "crank-pitman surface motion, valve state-machine pump; see "
                  "docs/model-improvement/DYNO_CARD_MODEL.md",
        "units": {"position": "m", "load": "kN"},
        "stroke_m": params["srp"]["stroke_m"],
        "scenarios": {},
    }
    for name, s in BAKE_SCENARIOS.items():
        stroke_in = s.get("stroke_in")
        p_wh = s.get("p_wellhead_kgf_cm2")
        df = cycle.simulate_css_cycle(
            s["steam_t"], s["soak_days"], s["cutoff_m3d"], s["spm"], params,
            stroke_m=(float(stroke_in) * INCH if stroke_in is not None else None),
            p_wellhead_kgf_cm2=p_wh,
            float_policy=s.get("float_policy"),
        )
        prod = df[df["phase"] == "produce"].reset_index(drop=True)
        hold_idx = _vfd_hold_day_index(prod, s["spm"])
        picks = [("early_hot", 0, None), ("mid", len(prod) // 2, None),
                 ("vfd_hold_day", hold_idx, None), ("stress_12spm", len(prod) - 1, STRESS_SPM)]
        cards = []
        for key, i, spm_o in picks:
            r = prod.iloc[i]
            c = card_for_row(r, params, spm=spm_o, n_points=n_points, stroke_m=df.attrs.get("stroke_m"))
            cards.append({
                "key": key, "day": round(float(r["day"]), 1),
                "mu_cP": round(float(r["mu_cP"]), 1), "spm": c["inputs"]["spm"],
                "floating_index_srp": round(srp.pump_state(c["inputs"]["spm"],
                                                           df.attrs.get("stroke_m", params["srp"]["stroke_m"]),
                                                           float(r["mu_cP"]), 0.0, params,
                                                           T_C=float(r["T_res_C"]),
                                                           water_cut=c["inputs"]["water_cut"])["floating_index"], 3),
                "mu_drag_cP": round(c["inputs"]["mu_drag_cP"], 2),
                "pump_fillage": round(c["pump_fillage"], 3),
                "card_type": c["card_type"], "card_label": c["card_label"],
                "signatures": c["signatures"],
                "peak_prl_kN": round(c["peak_prl_kN"], 1), "min_prl_kN": round(c["min_prl_kN"], 1),
                "plunger_stroke_m": round(c["plunger_stroke_m"], 3),
                "carrier_separation": c["carrier_separation"],
                "min_rod_force_kN": round(c["min_rod_force_kN"], 1),
                "polished_rod_kW": round(c["polished_rod_kW"], 3),
                "reference": {"W_rf_kN": round(c["buoyant_rod_weight_kN"], 1),
                              "Fo_kN": round(c["fluid_load_kN"], 1),
                              "static_peak_kN": round(c["static_peak_kN"], 1)},
                "surface": {"position_m": _r(c["position_m"], 3), "load_kN": _r(c["load_surface_kN"], 2)},
                "downhole": {"position_m": _r(c["plunger_position_m"], 3), "load_kN": _r(c["load_downhole_kN"], 2)},
            })
        out["scenarios"][name] = {"settings": s, "cards": cards}
    return out


def _main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="Computed dynamometer cards")
    ap.add_argument("--bake", metavar="PATH", help="write baked cards JSON for the dashboard")
    ap.add_argument("--params", default=str(Path(__file__).resolve().parents[1] / "params" / "field_params.json"))
    args = ap.parse_args(argv)
    with open(args.params) as f:
        params = json.load(f)
    if args.bake:
        data = bake(params)
        Path(args.bake).parent.mkdir(parents=True, exist_ok=True)
        with open(args.bake, "w") as f:
            json.dump(data, f, separators=(",", ":"))
        for name, sc in data["scenarios"].items():
            for c in sc["cards"]:
                print(f"{name:15s} {c['key']:13s} day {c['day']:6.1f} mu {c['mu_cP']:8.1f} spm {c['spm']:4.1f} "
                      f"fill {c['pump_fillage']:.2f} PPRL {c['peak_prl_kN']:5.1f} MPRL {c['min_prl_kN']:5.1f}  {c['card_label']}")
        print(f"wrote {args.bake}")
    else:
        wc = params["fluid"]["water_cut"]
        for mu, spm, fill in [(5, 5, 1.0), (5, 5, 0.6), (2000, 5, 1.0), (10000, 12, 1.0)]:
            c = compute_cards(spm, params["srp"]["stroke_m"], mu, fill, wc, params)
            print(f"mu {mu:6} spm {spm:3} fill {fill:.2f}: PPRL {c['peak_prl_kN']:.1f} MPRL {c['min_prl_kN']:.1f} "
                  f"-> {c['card_label']}")


if __name__ == "__main__":
    _main()
