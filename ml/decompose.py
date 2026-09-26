"""ml/decompose.py -- where does the recommendation's gain come from? (rev 10/11)

Hardening after the external technical review (27 Sep 2026, finding 1: "91 %
of the headline gain comes from a baseline cutoff you invented"). Everything
here runs the TRUE physics (`twin.cycle.simulate_css_cycle` + `summary`), no
surrogate.

rev 11 (physics wave 3): FIVE levers -- cutoff, spm, steam, stroke length
(API sizes, in) and injection (wellhead) pressure (kgf/cm2) -- and the
canonical recommendation comes from `ml.recommend_physics.best_settings_physics_5d`
(exhaustive 5-D grid, FI <= 0.6 + unit PRL cap, minimax regret across the two
price decks) instead of the rev-10 3-D grid.

1. **Gain decomposition.** From baseline (b) -- 1,300 t / 10 d / cutoff 1.3
   m3/d / 5 spm / 86 in / 91 kgf/cm2 (BGW-8-derived steam, soak and the
   mid-range CONFIRMED pressure; the cutoff is the params-range MIDPOINT and
   5 spm / 86 in are practice-band picks, i.e. OUR assumptions, not OIL's
   practice) -- to a recommendation, the incremental Rs/cycle-day gain is
   attributed to the five levers two ways:
     * one-at-a-time (OAT): change only that lever from baseline to rec;
       OAT terms do not sum to the total when the levers interact;
     * Shapley: the average of each lever's marginal contribution over all
       5! = 120 orders of switching the levers on (32 distinct cycles); the
       terms sum EXACTLY to the total (efficiency property).
   Done for the rev-9 (1,600 / 0.70 / 4), rev-10 (1,700 / 0.60 / 4) and rev-11
   canonical recommendations, on both price decks (FY25 realisation Rs
   5,992/bbl, the base; FY26 floor Rs 4,840/bbl). NOTE: rev-9/10 points are
   FI-infeasible under the rev-11 physics (the late-cycle stream is
   oil-continuous); their decompositions are reported for continuity.

rev 12 (physics wave 4): every cycle -- baseline, recommendation and every
Shapley coalition -- ends on the params' produce-end rule (default "either":
rate cutoff OR 3 consecutive float-alarm days, twin/cycle.py). The rev-11
canonical point (1,000 / 1.25 / 3 spm / 64 in / 93) is kept as a checked
previous recommendation; feasibility of previous points uses the optimiser's
rule-aware test (recommend_physics._level_feasible).

rev 13 (wave 5): the operator's float response is a lever too
(`float_policy`: pull / vfd_hold / vfd_then_pull / none, twin/cycle.py). The
Shapley/OAT attribution is computed on the counterfactual-free GAIN metric --
net cash per cycle-day, `margin_with_opex_inr_per_cycle_day` -- which equals
the incremental-margin difference whenever the two cycles share one cold
counterfactual, and stays correct when switching the float policy switches the
counterfactual (css.cold_counterfactual "policy": an operator who ignores float
runs the cold well floating, the three float policies shut it in). The canonical
recommendation is decomposed against baseline (b) operated under the SAME
policy (5 levers; the fair comparison) and under the other policies (6 levers,
the policy switch included).

2. **Baseline-cutoff sensitivity.** OIL's real cutoff is unknown, so the
   improvement is recomputed against baselines with cutoff 1.0 / 1.3 / 1.6
   m3/d (other levers as baseline (b)).

Usage:  python ml/decompose.py [--params params/field_params.json]
                               [--out ml/models/gain_decomposition.json]
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
import sys
import warnings
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from twin import cycle  # noqa: E402

PARAMS_PATH = _ROOT / "params" / "field_params.json"
OUT_JSON = Path(__file__).resolve().parent / "models" / "gain_decomposition.json"

OBJECTIVE = "margin_incremental_inr_per_cycle_day"
# rev 13: attribution metric (net cash per cycle-day; the counterfactual cancels)
GAIN = "margin_with_opex_inr_per_cycle_day"
_MID = {"stroke_in": 86.0, "p_wellhead_kgf_cm2": 91.0}
BASELINE_B = {"steam_t": 1300.0, "soak_days": 10.0, "cutoff_m3d": 1.3, "spm": 5.0, **_MID}
REC_REV9 = {"steam_t": 1600.0, "soak_days": 10.0, "cutoff_m3d": 0.70, "spm": 4.0, **_MID}
REC_REV10 = {"steam_t": 1700.0, "soak_days": 10.0, "cutoff_m3d": 0.60, "spm": 4.0, **_MID}
REC_REV11 = {"steam_t": 1000.0, "soak_days": 10.0, "cutoff_m3d": 1.25, "spm": 3.0,
             "stroke_in": 64.0, "p_wellhead_kgf_cm2": 93.0}
# rev 12 canonical point as operated in rev 12 (pull on the float alarm)
REC_REV12 = {"steam_t": 1000.0, "soak_days": 10.0, "cutoff_m3d": 0.60, "spm": 3.0,
             "stroke_in": 64.0, "p_wellhead_kgf_cm2": 85.0, "float_policy": "pull"}
LEVERS = ("cutoff_m3d", "spm", "steam_t", "stroke_in", "p_wellhead_kgf_cm2", "float_policy")
BASELINE_POLICIES = ("vfd_hold", "pull", "vfd_then_pull", "none")
BASELINE_CUTOFFS = (1.0, 1.3, 1.6)
# rev 12 (cascade): baseline (b)'s spm (5) and stroke (86 in) are ALSO our
# assumptions, not published OIL practice (same status as its 1.3 m3/d
# cutoff -- see meta.baseline_note below), so the same "how does the gain
# move if OIL's real practice differs" sensitivity is worth reporting for
# these two levers. Ranges: spm brackets the srp.spm_practice_band (3-6)
# around the baseline's 5; stroke brackets the baseline's 86 in with the
# neighbouring API sizes either side (74/86/100, from srp.stroke_in_options).
BASELINE_SPMS = (4.0, 5.0, 6.0)
BASELINE_STROKES = (74.0, 86.0, 100.0)
KEYS = (OBJECTIVE, "SOR_t_per_m3", "SOR_incremental", "oil_total_m3", "oil_incremental_m3",
        "days_total", "peak_oil_bbl_d", "max_floating_index", "failures_expected",
        "max_floating_index_produce_day", "water_cut_start", "water_cut_end", "max_peak_prl_kN",
        "T_sandface_C", "recharge_kPa",
        # rev 12
        "produce_end_reason", "produce_days", "produce_end_days_after_peak", "peak_oil_produce_day",
        # rev 13
        GAIN, "float_policy", "cold_status", "injection_margin_kPa", "injection_ok", "min_spm",
        "days_vfd_slowed")


def decks(params: dict) -> dict[str, dict]:
    """{deck name: params copy} -- FY25 realisation (shipped), FY26 floor and
    (rev 13, when the preset exists) FY25 net of royalty + OID cess."""
    fy25 = copy.deepcopy(params)
    fy26 = copy.deepcopy(params)
    presets = params.get("economics", {}).get("oil_price_presets", {})
    fy26["economics"]["oil_price_inr_per_bbl"] = float(
        presets.get("fy26_floor_65", {}).get("inr_per_bbl", 4840.0))
    out = {"fy25_realisation": fy25, "fy26_floor": fy26}
    if "fy25_net_of_levies" in presets:
        lev = copy.deepcopy(params)
        lev["economics"]["oil_price_inr_per_bbl"] = float(presets["fy25_net_of_levies"]["inr_per_bbl"])
        out["fy25_net_of_levies"] = lev
    return out


def evaluate(settings: dict, deck_params: dict[str, dict]) -> dict[str, Any]:
    """Simulate once (physics does not depend on price) and price on every deck.

    `settings` may omit the rev-11 controls (stroke_in, p_wellhead_kgf_cm2)
    and the rev-13 `float_policy`: then the params values are used."""
    base = next(iter(deck_params.values()))
    stroke_in = settings.get("stroke_in")
    df = cycle.simulate_css_cycle(
        settings["steam_t"], settings["soak_days"], settings["cutoff_m3d"], settings["spm"], base,
        stroke_m=(float(stroke_in) * 0.0254 if stroke_in is not None else None),
        p_wellhead_kgf_cm2=settings.get("p_wellhead_kgf_cm2"),
        float_policy=settings.get("float_policy"))
    out: dict[str, Any] = {"settings": dict(settings)}
    for name, p in deck_params.items():
        s = cycle.summary(df, p)
        out[name] = {k: s.get(k) for k in KEYS}
    return out


def decompose(baseline: dict, rec: dict, deck_params: dict[str, dict],
              levers: tuple[str, ...] = LEVERS) -> dict[str, Any]:
    """OAT and Shapley attribution of the gain (rev 13: net cash per cycle-day,
    GAIN), per deck. A lever enters only if both settings carry it and (for the
    float policy) the two differ."""
    levers = tuple(lv for lv in levers if lv in rec and lv in baseline
                   and not (lv == "float_policy" and rec[lv] == baseline[lv]))
    cache: dict[tuple, dict] = {}

    def value(on: frozenset) -> dict:
        key = tuple(sorted(on))
        if key not in cache:
            st = dict(baseline)
            for lever in on:
                st[lever] = rec[lever]
            cache[key] = evaluate(st, deck_params)
        return cache[key]

    out: dict[str, Any] = {"baseline": dict(baseline), "recommendation": dict(rec), "levers": list(levers)}
    orders = list(itertools.permutations(levers))
    for deck in deck_params:
        v0 = value(frozenset())[deck][GAIN]
        v1 = value(frozenset(levers))[deck][GAIN]
        oat = {lv: value(frozenset([lv]))[deck][GAIN] - v0 for lv in levers}
        shap = {lv: 0.0 for lv in levers}
        for order in orders:
            on: set = set()
            for lv in order:
                before = value(frozenset(on))[deck][GAIN]
                on.add(lv)
                shap[lv] += (value(frozenset(on))[deck][GAIN] - before) / len(orders)
        total = v1 - v0
        out[deck] = {
            "metric": GAIN,
            "baseline_value": v0, "recommendation_value": v1, "total_gain": total,
            "baseline_incremental": value(frozenset())[deck][OBJECTIVE],
            "recommendation_incremental": value(frozenset(levers))[deck][OBJECTIVE],
            "one_at_a_time": oat,
            "one_at_a_time_sum": sum(oat.values()),
            "shapley": shap,
            "shapley_share": {lv: (shap[lv] / total if total else float("nan")) for lv in levers},
        }
    out["points"] = {"+".join(sorted(k)) or "baseline": v for k, v in cache.items()}
    return out


def baseline_lever_sensitivity(rec: dict, deck_params: dict[str, dict],
                               lever: str, values: tuple[float, ...]) -> dict[str, Any]:
    """How the reported improvement over baseline (b) moves if OIL's real
    practice on ONE lever (cutoff_m3d / spm / stroke_in) differs from our
    assumed baseline (b) value, other baseline levers held fixed."""
    r = evaluate(rec, deck_params)
    rows = []
    for v in values:
        # rev 13: the baseline is operated under the recommendation's float policy
        b_set = dict(BASELINE_B, **{lever: v})
        if "float_policy" in rec:
            b_set.setdefault("float_policy", rec["float_policy"])
        b = evaluate(b_set, deck_params)
        row = {f"baseline_{lever}": v}
        for deck in deck_params:
            row[deck] = {
                "baseline_value": b[deck][OBJECTIVE],
                "recommendation_value": r[deck][OBJECTIVE],
                "improvement": r[deck][GAIN] - b[deck][GAIN],
                "baseline_SOR": b[deck]["SOR_t_per_m3"],
                "baseline_max_floating_index": b[deck]["max_floating_index"],
                "baseline_float_alarm_days": b[deck]["failures_expected"],
                "baseline_produce_end_reason": b[deck]["produce_end_reason"],
            }
        rows.append(row)
    return {"lever": lever, "recommendation": dict(rec), "rows": rows}


def baseline_cutoff_sensitivity(rec: dict, deck_params: dict[str, dict]) -> dict[str, Any]:
    return baseline_lever_sensitivity(rec, deck_params, "cutoff_m3d", BASELINE_CUTOFFS)


def baseline_spm_sensitivity(rec: dict, deck_params: dict[str, dict]) -> dict[str, Any]:
    return baseline_lever_sensitivity(rec, deck_params, "spm", BASELINE_SPMS)


def baseline_stroke_sensitivity(rec: dict, deck_params: dict[str, dict]) -> dict[str, Any]:
    return baseline_lever_sensitivity(rec, deck_params, "stroke_in", BASELINE_STROKES)


def run(params: dict, opt: dict | None = None) -> dict[str, Any]:
    from ml import recommend_physics as rp
    dp = decks(params)
    if opt is None:
        opt = rp.best_settings_physics_5d(params, policies=rp.ALL_POLICIES)
    c = opt["canonical_recommendation"]["settings"]
    canonical = {"steam_t": c["steam_t"], "soak_days": c["soak_days"], "cutoff_m3d": c["cutoff_m3d"],
                 "spm": c["spm"], "stroke_in": c["stroke_in"], "p_wellhead_kgf_cm2": c["p_wellhead_kgf_cm2"],
                 "float_policy": c.get("float_policy", cycle.float_policy_of(params))}
    best = opt["levels"]["aggressive"]["best_value_by_deck"]
    checks = {}
    for name, pt in (("rev9", REC_REV9), ("rev10", REC_REV10), ("rev11", REC_REV11), ("rev12", REC_REV12)):
        e = evaluate(pt, dp)
        f25 = e["fy25_realisation"]
        checks[name] = {"settings": pt, "evaluation": e,
                        "fi_feasible": bool(rp._level_feasible(
                            f25["max_floating_index"], f25["failures_expected"], rp.AGGRESSIVE_FI_MAX,
                            params)),
                        "value_minus_rev11_feasible_optimum": {d: e[d][OBJECTIVE] - best[d] for d in dp}}
        # rev 12: the key name is historical; the optimum is the CURRENT params' one
    return {
        "meta": {
            "objective": OBJECTIVE,
            "baseline_b": BASELINE_B,
            "baseline_note": ("steam 1,300 t and soak 10 d are BGW-8-derived, 91 kgf/cm2 the middle of the "
                              "CONFIRMED 85-97; the 1.3 m3/d cutoff is the params-range midpoint and 5 spm / "
                              "86 in practice-band picks -- the team's assumptions, not OIL's practice."),
            "decks": {d: dp[d]["economics"]["oil_price_inr_per_bbl"] for d in dp},
            "levers": list(LEVERS),
            "physics": ("rev 12 (rev 11 -- water cut as a state, IF97 steam state from the wellhead "
                        "pressure, recharge capped at the sandface pressure, P_current 9.4 MPa, "
                        "stroke lever with unit PRL cap -- plus Pal-Rhodes W/O emulsion capped at "
                        "10x, the 'either' produce-end rule (rate cutoff OR 3 consecutive float-"
                        "alarm days) and AOF_REF_M3D 0.56)"),
            "produce_end_rule": cycle.produce_end_rule_of(params),
        },
        "optimiser": {k: v for k, v in opt.items() if k not in ("table", "table_columns")},
        "canonical_recommendation": {
            "settings": canonical,
            "rule": opt["canonical_recommendation"]["rule"],
            "pinned_at_grid_edge": opt["canonical_recommendation"]["pinned_at_grid_edge"],
        },
        "previous_recommendations_check": checks,
        "decomposition_to_rev9_rec": decompose(BASELINE_B, REC_REV9, dp),
        "decomposition_to_rev10_rec": decompose(BASELINE_B, REC_REV10, dp),
        "decomposition_to_rev11_rec": decompose(BASELINE_B, REC_REV11, dp),
        "decomposition_to_canonical_rec": decompose(dict(BASELINE_B, float_policy=canonical["float_policy"]),
                                                    canonical, dp),
        # rev 13: the canonical rec against baseline (b) under EVERY float policy
        # (the policy switch is a sixth lever when the two differ)
        "decomposition_to_canonical_rec_by_baseline_policy": {
            pol: decompose(dict(BASELINE_B, float_policy=pol), canonical, dp) for pol in BASELINE_POLICIES},
        "decomposition_rev12_rec_vs_baseline_pull": decompose(dict(BASELINE_B, float_policy="pull"),
                                                              REC_REV12, dp),
        "baseline_cutoff_sensitivity_canonical_rec": baseline_cutoff_sensitivity(canonical, dp),
        # rev 12 (cascade): baseline (b)'s spm/stroke are equally our
        # assumptions (see meta.baseline_note) -- same sensitivity treatment.
        "baseline_spm_sensitivity_canonical_rec": baseline_spm_sensitivity(canonical, dp),
        "baseline_stroke_sensitivity_canonical_rec": baseline_stroke_sensitivity(canonical, dp),
    }


def _print(res: dict) -> None:
    decks_ = list(res["meta"]["decks"])
    items = [(k, res[k]) for k in ("decomposition_to_rev9_rec", "decomposition_to_rev10_rec",
                                   "decomposition_to_rev11_rec", "decomposition_to_canonical_rec",
                                   "decomposition_rev12_rec_vs_baseline_pull") if k in res]
    items += [(f"canonical vs baseline(b) [{pol}]", d)
              for pol, d in res.get("decomposition_to_canonical_rec_by_baseline_policy", {}).items()]
    for key, d in items:
        print(f"\n== {key}: {d['baseline']} -> {d['recommendation']}")
        for deck in decks_:
            e = d[deck]
            print(f"  [{deck}] total {e['total_gain']:+,.0f} Rs/d")
            for lv in d["levers"]:
                print(f"      {lv:20s} OAT {e['one_at_a_time'][lv]:+9,.0f}   Shapley {e['shapley'][lv]:+9,.0f}"
                      f" ({100 * e['shapley_share'][lv]:.0f} %)")
    for key, label in (("baseline_cutoff_sensitivity_canonical_rec", "cutoff_m3d"),
                       ("baseline_spm_sensitivity_canonical_rec", "spm"),
                       ("baseline_stroke_sensitivity_canonical_rec", "stroke_in")):
        print(f"\n== {key}")
        for row in res[key]["rows"]:
            print(f"  baseline {label} {row[f'baseline_{label}']}: "
                  + "  ".join(f"[{d}] base {row[d]['baseline_value']:+,.0f} (FI {row[d]['baseline_max_floating_index']:.2f})"
                              f" -> rec {row[d]['recommendation_value']:+,.0f} = {row[d]['improvement']:+,.0f}"
                              for d in decks_))
    print("\n canonical:", res["canonical_recommendation"])
    for k, v in res["previous_recommendations_check"].items():
        print(f" {k}: FI-feasible {v['fi_feasible']}, value - current feasible optimum "
              f"{ {d: round(x) for d, x in v['value_minus_rev11_feasible_optimum'].items()} }")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--params", type=Path, default=PARAMS_PATH)
    ap.add_argument("--out", type=Path, default=OUT_JSON)
    args = ap.parse_args()
    with open(args.params, encoding="utf-8") as f:
        params = json.load(f)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # steam-state warning, reported in the log
        res = run(params)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=float)
    _print(res)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
