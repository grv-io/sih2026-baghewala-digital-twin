"""Benchmark suite: the v2 twin against published field / literature numbers.

Unlike the unit tests, every test here encodes an EXTERNAL band (rev 5
calibration, 26 Sep 2026). Design rule from
docs/model-improvement/MODEL_IMPROVEMENT_PLAN_ECON_VALIDATION.md section 3.1:
a benchmark that fails is a physics or data finding, not a tolerance to widen.
Such findings are kept here as strict xfails (they flip to a hard failure
if a future change makes them pass unexpectedly, so the write-up is updated):
  * the soak-day optimum is not a meaningful interior optimum in 5-15 d
    (physics v3: margin/day peaks near 18-20 d on a plateau < 3 % deep;
    Boberg-Lantz gives soak only conduction-timing effects);
  * (rev 11 -> resolved in rev 12) the reference peak was 12.4 bbl/d, below
    the 15-40 bbl/d field envelope. rev 12 re-tuned ONLY AOF_REF_M3D
    (0.46 -> 0.56; peak 15.1 bbl/d, uplift unchanged at 5.41x) and
    re-specified the reference-SOR band to 3.0-4.6 (the old 3.8-4.6 was our
    own plan target; literature 3-8, Kern River 3.47) -- TIER1 section 11.
rev 12 (physics wave 4) ALSO changed what ends a cycle: css.produce_end_rule
"either" = rate cutoff OR 3 consecutive float-alarm days. Benchmarks whose
statement is about the reservoir / heat physics of a rate-driven cycle (soak
plateau, Darcy depletion) are evaluated so the operating rule cannot mask it,
and the rule's own effect is reported next to them.
rev 11 (physics wave 3) also moved three rev-5/10 mechanism benchmarks to the
rev-10 switches (conftest.legacy_rev10: constant water cut, legacy steam,
virgin pressure) where the statement is about THAT stream, and added the
water-cut-state findings next to them.
Physics v3 (26-27 Sep 2026) RE-SPECIFIED the P_res benchmark instead of keeping
the Liaohe xfail: Liaohe's +24 % is a 20-year field life-cycle drift in a
shallow, gravity-drainage / solution-gas field; Baghewala's only drive at
7.4-11.4 MPa is pressure depletion, whose single-cycle response is the Darcy /
Vogel drawdown ratio (see test_depletion_response_is_darcy_proportional and
docs/model-improvement/TIER1_PROGRESS_LOG.md section 7).

Reference cycle: 1,500 t (BGW-8 first cycle: 1,040-1,560 t), 7 d soak
(BGW-8: 7-13 d), cutoff 1.2 m3/d, 5 spm (published heavy-oil band 3-6 spm).
Sources for every band: docs/research/baghewala_facts.md and the two
MODEL_IMPROVEMENT_PLAN_*.md files.
"""
import copy
import json
from pathlib import Path

import pytest

from twin import cycle, ipr, viscosity

pytestmark = pytest.mark.benchmark

REF = dict(steam_t=1500, soak_days=7, cutoff_m3d=1.2, spm=5)

# Rounded rev-5 recommendation (docs/model-improvement/TIER1_PROGRESS_LOG.md
# section 5b): soak held at the published-practice value, steam/cutoff/spm
# optimised for margin/cycle-day, re-verified with the physics twin.
REC = dict(steam_t=1700, soak_days=10, cutoff_m3d=0.85, spm=5)

CALGEM_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "external" / "calgem_css" / "summary.json"
)


def _summary(params, **kw):
    args = dict(REF, **kw)
    df = cycle.simulate_css_cycle(params=params, **args)
    return df, cycle.summary(df, params)


def _bulk(params):
    """rev 13: a copy at the rev 5-12 bulk diesel discount (0.30, the
    economics.diesel_discount_presets "bulk_0.30" preset). The steam-slug and
    soak MARGIN statements below were calibrated there (rev 5 revealed
    preference: 19 CSS jobs/yr must pay); at the rev-13 mid-range base (0.15)
    the reference's gross margin per cycle-day falls ~Rs 12.8k -> ~2.2k, so the
    relative (%) plateau / "meaningful optimum" criteria lose their meaning and
    the slug optimum moves below BGW-8's range -- recorded as a finding
    (test_steam_optimum_at_the_mid_range_diesel_price_is_within_bgw8, strict xfail)."""
    q = copy.deepcopy(params)
    q["economics"]["diesel_bulk_discount_frac"] = params["economics"].get(
        "diesel_discount_presets", {}).get("bulk_0.30", 0.30)
    return q


def _cold_rate(params):
    # rev 11: at the pressure the IPR actually sees (reservoir.P_current_kPa,
    # else virgin) -- the same cold rate cycle.cold_baseline uses.
    return ipr.oil_rate_m3d(
        cycle.reservoir_pressure_kPa(params),
        cycle._pump_intake_pressure_kPa(params),
        params["fluid"]["mu_ref_cP"],
        params,
    )


# --------------------------------------------------------------- fluid ------
def test_mu_at_50C_is_the_field_anchor_exactly(params):
    """mu(50 C) = 11,500 cP (OIL PPT 10,000-13,000; SPE-23APOG 8,000-15,000)."""
    assert viscosity.mu_cP(50.0, params) == pytest.approx(11500.0, rel=1e-9)


def test_mu_at_steam_temperature_is_a_few_cP(params):
    """mu(290 C) in 3-6 cP (CSI field case: ~5 cP at 304 C, css deep dive 2.6);
    never thinner than water."""
    assert 3.0 <= viscosity.mu_cP(290.0, params) <= 6.0


# --------------------------------------------------------------- cold well --
def test_cold_rate_is_at_most_half_a_cubic_metre(params):
    """Unstimulated 11,500 cP well: <= ~0.5 m3/d (~3 bbl/d), i.e. uneconomic
    without steam, and below the whole cutoff search range."""
    q = _cold_rate(params)
    assert 0.2 <= q <= 0.5
    assert q < params["css"]["cutoff_rate_m3d_range"][0]


# --------------------------------------------------------------- reference --
def test_reference_SOR_in_calibration_band(params):
    """SOR at the reference cycle inside the reference band 3.0-4.6 t/m3.

    rev 12 re-specification (coordinator decision, TIER1 section 11): the
    3.8-4.6 band of rev 11 was OUR calibration target (plan ~4.4), not data;
    the external evidence is the literature CSS band 3-8 (Cold Lake ~4,
    life-cycle ~6) and Kern River's 2021 field SOR 3.47 (CalGEM), so the
    floor is 3.0. The peak-rate band (15-40 bbl/d, a FIELD observable) now
    sets AOF_REF_M3D = 0.56. Reference under the "either" produce-end rule:
    4.50, ending on float onset at produce day 151 (rate-cutoff rule: 3.18)."""
    _, s = _summary(params)
    assert 3.0 <= s["SOR_t_per_m3"] <= 4.6


def test_SOR_stays_in_literature_band_over_steam_range(params):
    for steam_t in (500, 1000, 1500, 2000, 3000):
        _, s = _summary(params, steam_t=steam_t)
        assert 3.0 <= s["SOR_t_per_m3"] <= 8.0, steam_t


def test_first_cycle_uplift_matches_BGW8(params):
    """Peak produce rate / cold rate: OIL published 5-6x first-cycle uplift
    for BGW-8 (Scribd/OIL; baghewala_facts.md section 4). Band 5.0-6.5 allows
    for peak-vs-average reporting."""
    _, s = _summary(params)
    uplift = s["peak_oil_m3d"] / _cold_rate(params)
    assert 5.0 <= uplift <= 6.5


@pytest.mark.parametrize("steam_t", [1040, 1560])
def test_uplift_at_BGW8_reported_slugs(params, steam_t):
    """At BGW-8's reported first-cycle slug range (14-21 d x 74 t/d) the
    uplift brackets the published 5-6x (PHYSICS plan T1-A validation test)."""
    _, s = _summary(params, steam_t=steam_t)
    assert 4.5 <= s["peak_oil_m3d"] / _cold_rate(params) <= 6.5


def test_peak_rate_inside_field_envelope(params):
    """15-40 bbl/d per well at peak (field average ~19 bbl/d/well, 655 bbl/d
    over 34 producers, Jul-2025; the old engine gave 471 bbl/d).
    rev 11 strict xfail (12.4 bbl/d) RESOLVED in rev 12 by AOF_REF_M3D
    0.46 -> 0.56 (15.1 bbl/d); the uplift is AOF-invariant (TIER1 s. 11)."""
    _, s = _summary(params)
    assert 15.0 <= s["peak_oil_bbl_d"] <= 40.0


def test_produce_phase_is_months_not_weeks(params):
    """Produce phase 3-8 months (Cold Lake 3-6 months; Baghewala cycles 6-18
    months apart including inject + soak)."""
    df, _ = _summary(params)
    n = int((df["phase"] == "produce").sum())
    assert 90 <= n <= 240


def test_cycle_oil_in_plan_envelope(params):
    """PHYSICS plan field-plausibility envelope: 500-4,000 bbl per cycle."""
    _, s = _summary(params)
    assert 500.0 <= s["oil_bbl"] <= 4000.0


# --------------------------------------------------------------- levers -----
def test_steam_volume_has_interior_margin_optimum(params):
    """SOR rises monotonically with slug size (composite-radial physics), so
    the optimum is in Rs margin per cycle-day; it must be interior and land
    near BGW-8's own 1,040-1,560 t first-cycle choice."""
    params = _bulk(params)   # rev 13: at the bulk-discount preset it was calibrated at
    grid = (500, 750, 1000, 1500, 2000, 2500, 3000)
    m = {s: _summary(params, steam_t=s)[1]["margin_inr_per_cycle_day"] for s in grid}
    best = max(m, key=m.get)
    assert best not in (grid[0], grid[-1])
    assert 1000 <= best <= 2000


@pytest.mark.xfail(strict=True, reason=(
    "rev 13 FINDING: at the mid-range diesel discount (0.15, Rs 7,111/t steam) the gross-margin "
    "optimum slug is ~750 t, BELOW BGW-8's own 1,040-1,560 t first-cycle choice (at 0.30 it is "
    "1,000 t). Read as revealed preference, OIL's slug size is evidence that its steam is cheaper "
    "than the mid-range (closer to the bulk 0.30 case) -- or that its oil is worth more. "
    "TIER1_PROGRESS_LOG.md section 12."))
def test_steam_optimum_at_the_mid_range_diesel_price_is_within_bgw8(params):
    assert params["economics"]["diesel_bulk_discount_frac"] == pytest.approx(0.15)
    grid = (500, 750, 1000, 1500, 2000, 2500, 3000)
    m = {s: _summary(params, steam_t=s)[1]["margin_inr_per_cycle_day"] for s in grid}
    assert 1000 <= max(m, key=m.get) <= 2000


def test_spm_is_a_real_lever(legacy_params):
    """The pump must be able to limit production early in the cycle at the
    low end of the practice band: at 3 spm the rate is pump-limited for at
    least a month, the cycle runs longer and SOR is worse than at 5 spm.
    rev 11: holds for the rev-10 constant 85 % stream (conftest.legacy_rev10).
    With the water-cut state the reference is reservoir-limited from ~4 spm
    (liquid ~15 m3/d vs 20.7 m3/d displacement at 5 spm) and SPM acts through
    float and power instead -- test_physics_wave3.py records that finding."""
    params = legacy_params
    _, s3 = _summary(params, spm=3)
    _, s5 = _summary(params, spm=5)
    assert s3["pump_limited_days"] >= 30
    assert s3["days_total"] > s5["days_total"] + 10
    assert s3["SOR_t_per_m3"] > 1.02 * s5["SOR_t_per_m3"]
    assert s3["margin_inr_per_cycle_day"] < s5["margin_inr_per_cycle_day"]


def test_float_alarm_does_not_bind_in_a_water_continuous_stream(legacy_params):
    """rev 10 RE-SPECIFICATION of the rev-5 "float binds in the high-SPM /
    cold-tail corner" benchmark (external review, finding 8). The rods are
    dragged by the PRODUCED stream (srp.rod_drag_viscosity_cP), not by the
    reservoir oil. At the shipped 85 % water cut, above the [ASSUMPTION] 0.70
    W/O -> O/W inversion, that stream is water-continuous (~1 cP), so the
    float index stays ~0 everywhere -- even at 12 spm with the lowest cutoff.
    This is a FINDING, not a tolerance: the rod-float thesis does not hold at
    the base water cut. Recorded here so a future change that brings the
    alarm back at 85 % cut is noticed (TIER1_PROGRESS_LOG.md section 9).
    rev 11: this is the CONSTANT-cut stream (conftest.legacy_rev10). With the
    water-cut state the late-cycle stream falls below the inversion and the
    alarm binds (test_physics_wave3.py)."""
    params = legacy_params
    spm_hi = params["srp"]["spm_range"][1]
    cut_lo = params["css"]["cutoff_rate_m3d_range"][0]
    for kw in ({}, dict(spm=spm_hi, cutoff_m3d=cut_lo)):
        _, s = _summary(params, **kw)
        assert s["max_floating_index"] < 0.05, kw
        assert s["failures_expected"] == 0, kw


def test_float_alarm_binds_when_the_stream_is_oil_continuous(params):
    """Where the float constraint still exists: an oil-continuous (W/O)
    produced stream, i.e. water cut below the inversion point -- there the
    W/O emulsion viscosity is 10x the oil's at 65 % water (rev 12: Pal-Rhodes,
    capped at 10x; Brinkman gave ~14x) and the alarm trips in the cold tail
    even at the practice-band 4-5 spm. The rev-9 drag rule (tubing fluid = reservoir oil, model "oil")
    still reproduces the rev-5/9 behaviour: silent at the reference, tripping
    in the 12-spm / low-cutoff corner."""
    spm_hi = params["srp"]["spm_range"][1]
    cut_lo = params["css"]["cutoff_rate_m3d_range"][0]
    wo = copy.deepcopy(params)
    wo["fluid"]["water_cut_model"] = "constant"   # rev 11: a constant W/O stream
    wo["fluid"]["water_cut"] = 0.65
    assert wo["fluid"]["water_cut"] < wo["fluid"]["emulsion_inversion_wc"]
    _, s = _summary(wo, spm=4, cutoff_m3d=cut_lo)
    assert s["max_floating_index"] > 0.6 and s["failures_expected"] > 0

    legacy = copy.deepcopy(params)
    legacy["fluid"]["water_cut_model"] = "constant"
    legacy["fluid"]["tubing_viscosity_model"] = "oil"
    _, ref = _summary(legacy)
    assert ref["max_floating_index"] <= 0.6 and ref["failures_expected"] == 0
    _, corner = _summary(legacy, spm=spm_hi, cutoff_m3d=cut_lo)
    assert corner["max_floating_index"] > 0.6 and corner["failures_expected"] > 0


def test_soak_has_a_small_benefit(params):
    """Longer soak lowers SOR slightly (heat leaves by conduction rather than
    in hot produced fluid). The effect is SMALL in Boberg-Lantz physics
    (< 2 %) -- recorded, not hidden."""
    _, s3 = _summary(params, soak_days=3)
    _, s15 = _summary(params, soak_days=15)
    assert s15["SOR_t_per_m3"] < s3["SOR_t_per_m3"]
    assert s15["SOR_t_per_m3"] > 0.98 * s3["SOR_t_per_m3"]


def test_soak_is_a_weak_lever_margin_plateau(params):
    """rev 12: evaluated under the rate-cutoff produce-end rule, i.e. the
    Boberg-Lantz heat physics of soak itself. Under the "either" rule the
    cycle length is set by float onset and soak becomes a mild shorter-is-
    better lever (test_soak_under_the_float_onset_rule_is_mildly_shorter_better)."""
    params = _bulk(params)
    params["css"]["produce_end_rule"] = "rate_cutoff"
    _soak_plateau(params)


def test_soak_under_the_float_onset_rule_is_mildly_shorter_better(params):
    """rev 12 FINDING: with the float-onset rule setting the cycle length, the
    idle soak days are not bought back by a longer produce phase, so Rs
    margin/cycle-day falls ~0.6-0.7 %/day of soak beyond ~5 d: 5-10 d stays
    within 5 % of the best, 20 d is ~11 % below it. Still no MEANINGFUL
    interior optimum (the strict xfail below stands); soak stays fixed at the
    10-d practice value in the optimiser (TIER1 section 11)."""
    params = _bulk(params)   # rev 13: relative criterion, calibrated at 0.30 (see _bulk)
    days = (3, 5, 7, 10, 13, 15, 20, 30)
    m = {d: _summary(params, soak_days=d)[1]["margin_inr_per_cycle_day"] for d in days}
    top = max(m.values())
    assert all(m[d] >= 0.95 * top for d in (5, 7, 10))
    assert m[20] < 0.95 * top and m[30] < m[20]


def _soak_plateau(params):
    """Physics v3: Rs margin/cycle-day over soak is a PLATEAU, not a lever.
    Across 5-20 d it stays within 5 % of its best value at both the reference
    and the rev-5 recommendation, and the 30-d end is below the plateau top
    (soak is not "more is always better" once the search box is opened). This
    is the Boberg-Lantz answer and matches the literature's "little impact"
    (PEH ch. 15: soak "should be as short as possible"; CSS simulation studies,
    css deep dive 2.5) -- it is why the dashboard holds soak at practice."""
    for kw in ({}, dict(steam_t=REC["steam_t"], cutoff_m3d=REC["cutoff_m3d"])):
        m = {d: _summary(params, soak_days=d, **kw)[1]["margin_inr_per_cycle_day"]
             for d in (5, 7, 10, 13, 15, 20, 30)}
        top = max(m.values())
        assert all(m[d] >= 0.95 * top for d in (5, 7, 10, 13, 15, 20)), m
        assert m[30] < top, m


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN FINDING (rev 5, re-checked physics v3): no MEANINGFUL interior soak "
    "optimum in 5-15 d. With the search opened to 30 d, margin/cycle-day peaks "
    "at ~18 d (same at dt 1 and 0.25 d) on a plateau <3 % deep, from the Boberg-Lantz delta*f timing "
    "term only. Mechanisms tried and bounded in v3: soak-only conductive "
    "spreading (rejected -- books horizontal conduction as loss in production "
    "but not in soak, so soak becomes a free lunch, monotone); uncondensed-steam "
    "flashback (<1 % of zone heat at 9 % porosity); gravity segregation "
    "(rho*g*h = 0.11 MPa vs ~10 MPa drawdown). TIER1_PROGRESS_LOG.md section 7."))
def test_soak_optimum_is_interior_in_5_to_15_days(params):
    params = _bulk(params)   # rev 13: the relative 2 % criterion needs the 0.30 margin level (see _bulk)
    days = (3, 5, 7, 9, 11, 13, 15, 16, 17, 18, 19, 20, 25, 30)
    m = {d: _summary(params, soak_days=d)[1]["margin_inr_per_cycle_day"] for d in days}
    best = max(m, key=m.get)
    assert 5 <= best <= 15
    # "meaningful": the optimum beats both ends of the box by >= 2 %.
    assert m[best] >= 1.02 * max(m[3], m[30])


# --------------------------------------------------------------- pressure ---
def _dsor_for_pressure(params, P_kPa, **kw):
    # rev 11: the pressure the IPR sees is reservoir.P_current_kPa (9.4 MPa
    # default, [ASSUMPTION]); P_initial_kPa is only its null fallback.
    base = _summary(params, **kw)[1]["SOR_t_per_m3"]
    q = copy.deepcopy(params)
    q["reservoir"]["P_current_kPa"] = P_kPa
    return _summary(q, **kw)[1]["SOR_t_per_m3"] / base - 1.0


def test_depletion_worsens_SOR_and_no_longer_over_responds(params):
    """ECON plan D3 / FAIL 3: P_res must be live (SOR rises as pressure falls)
    and the rev-4 over-response (+92 % for 11.4 -> 7.4 MPa) must be gone."""
    d84 = _dsor_for_pressure(params, 8400)   # rev 11: base is now 9.4 MPa
    d74 = _dsor_for_pressure(params, 7400)
    assert 0.0 < d84 < d74
    assert d74 < 0.70


def test_depletion_response_is_darcy_proportional(params):
    """See _darcy_doc below (kept verbatim) and the rev-12 note: the band is
    now evaluated on a FIXED produce window -- literally the derivation's
    'fixed-duration cycle' -- because under the "either" rule the depleted
    cycle floats later (its slower liquid rate drains the condensate tank more
    slowly), so the rule itself shortens the depletion response (+15.5 % at
    9.4 -> 7.4 MPa, reported) and, with AOF 0.56, the 0.8 m3/d cutoff run also
    sits 1.4 pp under the band's lower edge (+22.5 %; Boberg-Lantz: the slower
    depleted well carries less heat out). The fixed-window response is +25.4 %
    against the +28.9 % Darcy limit."""
    pwf = cycle._pump_intake_pressure_kPa(params)
    mu = params["fluid"]["mu_ref_cP"]
    base_p = cycle.reservoir_pressure_kPa(params)
    r = ipr.oil_rate_m3d(7400, pwf, mu, params) / ipr.oil_rate_m3d(base_p, pwf, mu, params)
    darcy = 1.0 / r - 1.0
    assert 0.25 <= darcy <= 0.35  # the derived limit itself (~0.29 for 9.4 -> 7.4 MPa)
    oil = {}
    for P_kPa in (base_p, 7400.0):
        q = copy.deepcopy(params)
        q["reservoir"]["P_current_kPa"] = P_kPa
        df, _ = _summary(q, cutoff_m3d=0.6)
        oil[P_kPa] = df.loc[df["phase"] == "produce", "oil_m3d"].to_numpy()
    n = min(120, len(oil[base_p]), len(oil[7400.0]))
    assert n >= 100
    d74 = oil[base_p][:n].sum() / oil[7400.0][:n].sum() - 1.0   # same steam, fixed window
    assert darcy - 0.05 <= d74 <= darcy + 0.15


def _darcy_doc(params):
    """Physics v3 re-specification of the rev-5 Liaohe xfail (+20-40 %).

    Band derivation: for a pure pressure-depletion drive the rate scales with
    the Vogel drawdown term (Vogel 1968, q_max = J*P_res/1.8, at the absolute
    pump-intake P_wf), so a FIXED-DURATION cycle at 7.4 MPa makes r = q(7.4)/
    q(11.4) of the oil and SOR rises by 1/r - 1 (~+58 %). A rate cutoff ends
    the low-pressure cycle a little sooner (more), the injection recharge adds
    the same kPa to both (less). Band: [1/r - 1 - 5 pp, 1/r - 1 + 15 pp].

    Why Liaohe's +24 % (7.4 -> 2.9 MPa over ~20 years; SPE 18HOCE
    D021S009R002) is not the band: it is a field life-cycle drift with
    operator re-design and CO2 assist, in a shallow field where gravity
    drainage (Towson & Boberg, PEH ch. 15: Boberg-Lantz "assumes significant
    reservoir energy") and solution gas near the bubble point carry part of
    the drive. At Baghewala neither applies: rho*g*h over 12 m is 0.11 MPa
    (~1 % of the ~10 MPa drawdown) and 7.4-11.4 MPa is far above the 3 MPa
    bubble point. Also verified in v3: an economic cutoff cannot change this --
    with electricity-only opex (~250 kWh/d, ~Rs 2,000/d) the economic-limit
    rate is ~0.07 m3/d, below the cold rate, so it never binds. Economics v2
    (rev 8) re-checked it with the full daily opex (Rs 5,000/d fixed + ~Rs
    1,100-1,400/d of corrected pumping power): q_EL ~0.2 m3/d, still below the
    0.447 m3/d cold rate.

    rev 11 re-specification (base pressure, not band): the IPR's base is now
    P_current = 9.4 MPa, so the derived limit for 9.4 -> 7.4 MPa is ~+29 %
    (was +58 % for 11.4 -> 7.4). The derivation is for a FIXED-DURATION cycle;
    a rate cutoff adds a truncation term that is second-order only while the
    cutoff is well below both peaks. At the reference 1.2 m3/d the depleted
    peak (1.68 m3/d) is only 40 % above the cutoff and the truncation adds
    +17 pp (dSOR +46 %, reported in TIER1 section 10); the band is therefore
    evaluated with the cutoff at half the depleted peak (0.8 m3/d, dSOR +26 %).
    Recharge is capped at the sandface pressure in both runs.
    (Documentation only since rev 12 -- the test body is above.)
    """


# --------------------------------------------------------------- economics --
def test_margin_positive_at_reference(params):
    """OIL ran 19 CSS jobs in FY2025-26, so a sensible cycle must pay at the
    base-case (bulk-diesel) fuel price. NOTE (rev 10, external review): this is
    the GROSS margin (credits CSS with the oil the well makes cold anyway) --
    a calibration-band check, not the decision metric; the incremental margin
    at the reference is only ~+Rs 350/cycle-day on the FY25 deck and negative
    on the $65 floor (TIER1_PROGRESS_LOG.md sections 8-9)."""
    _, s = _summary(params)
    assert s["margin_inr"] > 0
    assert s["margin_inr_per_cycle_day"] > 0


def test_retail_diesel_flips_the_sign(params):
    """At the Rajasthan RETAIL pump price (Rs 97.8/L -> ~Rs 8,370/t steam):
    css deep dive 5.2 -- at diesel prices CSS goes loss-making between SOR 3
    and 5. rev 11 re-specification: the break-even GROSS SOR at retail diesel
    (oil value per m3 / steam cost per t, before the rig) must sit in that
    3-5 band, and retail must cost the reference cycle > Rs 3.5 M against the
    bulk base case. (Until rev 10 the reference itself, at SOR 4.03, flipped
    to a ~Rs 0.01 M loss; at the rev-11 SOR 3.90 it stays barely positive,
    so the sign of one cycle was never the finding -- the band is.)"""
    q = copy.deepcopy(params)
    q["economics"]["diesel_bulk_discount_frac"] = 0.0
    _, s = _summary(q)
    _, s_base = _summary(_bulk(params))   # rev 13: retail vs the BULK preset (base is now 0.15)
    cost_t = cycle.steam_cost_inr_per_t(q["economics"])
    assert 8200 <= cost_t <= 8500
    e = q["economics"]
    breakeven_sor = e["oil_price_inr_per_bbl"] * e["bbl_per_m3"] / cost_t
    assert 3.0 <= breakeven_sor <= 5.0
    assert s_base["margin_inr"] - s["margin_inr"] > 3.5e6


def test_steam_cost_in_documented_band(params):
    """Rs 5,900-8,400/t steam (71 kg HSD/t, ECON plan section 0.2), +/- 1 %."""
    assert 5800 <= cycle.steam_cost_inr_per_t(params["economics"]) <= 8500


def test_co2_per_bbl_at_SOR5_reproduces_published_intensity(params):
    """ECON plan E1: diesel steam at SOR 5 -> 165-180 kg CO2/bbl (research
    derives 171; oil-sands Scope 1+2 published 185)."""
    econ = params["economics"]
    kg_per_bbl = 5.0 * cycle.co2_kg_per_t_steam(econ) / econ["bbl_per_m3"]
    assert 165.0 <= kg_per_bbl <= 180.0


# ----------------------------------------------------- CalGEM/Kern County ---
# These three tests are a PLAUSIBILITY BAND check against real CalGEM
# 2021 field-level annual data (Kern River / Midway-Sunset / Coalinga --
# data/external/calgem_css/summary.json, docs/research/CALGEM_CSS_BENCHMARK_
# 2026-09-26.md), NOT a calibration target. Per SOURCE.md limitation #4:
# these three fields are shallow (~300 m), ~100-year-old, hot-water-drive-
# assisted cyclic-steam fields; Baghewala is ~1,150 m deep with no legacy
# thermal drive. Also: no monthly OIL production by well was obtainable
# anywhere for these fields (SOURCE.md limitation #1), so the only real
# per-field SOR available is the 2021 ANNUAL aggregate (steam/oil, whole
# field, whole year) -- not a per-cycle series comparable one-for-one with
# the twin's single-cycle SOR. Skips cleanly if the data was never fetched
# into this checkout (it is real CalGEM/Wayback data, not synthetic, and is
# not regenerated by any script here).
def _calgem_summary():
    if not CALGEM_PATH.exists():
        pytest.skip(f"CalGEM benchmark data not present at {CALGEM_PATH}")
    with open(CALGEM_PATH) as f:
        return json.load(f)


def _field_sor_band(calgem):
    """(min, max) of the three fields' 2021 official field-level annual SOR
    (cyclic steam + steamflood, over oil -- the only real per-field SOR this
    dataset has). Read from summary.json, not hard-coded, so a re-fetch with
    updated Annual Report figures re-derives the band automatically."""
    sors = [
        f["field_level_annual_sor_2021_total_steam_over_oil"]
        for f in calgem["fields"].values()
    ]
    return min(sors), max(sors)


def test_reference_cycle_SOR_within_calgem_field_band(params):
    """PLAUSIBILITY BAND, not calibration (see module note above). The
    reference cycle's SOR (Baghewala twin, 1,500 t/7 d/1.2 m3/d/5 spm) must
    fall within the real 2021 official field-level annual SOR band spanned by
    Kern River (lowest, ~3.47 -- a shallow, predominantly steamflood field with
    a cyclic-steam subset; field-level SOR band only), Midway-Sunset and
    Coalinga (both also mix in continuous steamflood and run hotter, ~7.6-8.2).
    Three field-annual aggregates, 2.4x wide: a loose sanity band, not
    validation (rev 10 wording, external review finding 7)."""
    calgem = _calgem_summary()
    lo, hi = _field_sor_band(calgem)
    _, s = _summary(params)
    assert lo <= s["SOR_t_per_m3"] <= hi


def test_recommendation_SOR_within_calgem_field_band(params):
    """PLAUSIBILITY BAND, not calibration (see module note above). The rounded
    rev-5 recommendation (1,700 t / 10 d soak, fixed / 0.85 m3/d cutoff / 5
    spm -- TIER1_PROGRESS_LOG.md section 5b) must also fall within the real
    2021 CalGEM field-level annual SOR band, same as the reference cycle."""
    calgem = _calgem_summary()
    lo, hi = _field_sor_band(calgem)
    _, s = _summary(params, **REC)
    assert lo <= s["SOR_t_per_m3"] <= hi


def test_reference_steam_per_cycle_within_midway_sunset_p10_p90(params):
    """PLAUSIBILITY BAND, not calibration (see module note above). CalGEM's
    per-cycle steam mass comes only from real well-level monthly injection
    episodes on wells CalGEM itself codes cyclic-steam ("SC"); Midway-Sunset's
    are the best-reported (longer cycles, less split by the ~52% "Estimated"-
    record artifact that shrinks Kern River's median -- SOURCE.md limitation
    #2) and its median (p50 ~1,204 t) lands almost exactly inside our design
    range, so it is used as the cross-check band here. Two assertions:
    (1) our whole steam_volume_t_range (500-3,000 t, params/field_params.json
    css block) overlaps Midway-Sunset's p10-p90 steam-per-cycle band; (2) the
    reference cycle's own 1,500 t sits inside that same p10-p90 band."""
    calgem = _calgem_summary()
    ms = calgem["fields"]["Midway-Sunset"]["steam_tonnes_per_cycle"]
    p10, p90 = ms["p10"], ms["p90"]
    our_lo, our_hi = params["css"]["steam_volume_t_range"]

    overlap_lo, overlap_hi = max(our_lo, p10), min(our_hi, p90)
    assert overlap_lo < overlap_hi, "our steam range and Midway-Sunset p10-p90 do not overlap at all"

    assert p10 <= REF["steam_t"] <= p90
