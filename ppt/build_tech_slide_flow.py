r"""Slide 3 (TECHNICAL APPROACH) -- the DATA-FLOW version.

Reads left to right as "where does the data come from, where does it go, which model
touches it, what comes out": INPUTS -> PHYSICS TWIN (four models, day by day) ->
SEARCH & CHECKS -> SERVICE (FastAPI) -> DASHBOARD -> ENGINEER, with the field-records
feedback loop along the bottom. Every arrow is a data movement; labels in the gaps name
what travels. Built with the native framework (build_tech_slide_native: boxes, wires,
gates) so the same canvas/furniture/overlap/wiring/text-fit gates apply, and reuses the
simple builder's slide-3 open/export helpers.

Outputs:
    ppt/final/SIH26120_Slide3_FLOW_preview.pptx / .pdf   (1-slide preview)
    ppt/diagram/slide3_flow.png
    --into-strict: slide 3 of the STRICT deck is redrawn (shapes TX_*), the 6-page PDF
    re-exported, PNG re-rendered; deck backed up first to
    ppt/archive/SIH26120_Idea_Presentation_STRICT_pre-flow-slide3.pptx

Run:
    .venv\Scripts\python.exe ppt\build_tech_slide_flow.py                # preview
    .venv\Scripts\python.exe ppt\build_tech_slide_flow.py --into-strict  # in the deck
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PPT_DIR))
import build_tech_slide_native as N  # noqa: E402
import build_tech_slide_simple as S  # noqa: E402
from build_tech_slide_native import (  # noqa: E402
    Box, Para, C_IN, C_ML, C_PHY, C_SVC, C_TEXT, FONT, MONO, TINT, chip, label, node,
    panel, wire,
)

ROOT = PPT_DIR.parent
PREFIX = "TX_"
OUT = PPT_DIR / "final" / "SIH26120_Slide3_FLOW_preview.pptx"
OUT_PDF = OUT.with_suffix(".pdf")
PNG = PPT_DIR / "diagram" / "slide3_flow.png"
SWAP_BACKUP = PPT_DIR / "archive" / "SIH26120_Idea_Presentation_STRICT_pre-flow-slide3.pptx"
C_GREY = "595959"
LABELS = ("l_params", "l_card", "l_runs", "l_rerun", "l_plans", "l_json", "cap_lane", "cap_fb", "trust", "in_note")


def W(pts, src=None, dst=None, **kw):
    kw["extra_ok"] = tuple(kw.get("extra_ok", ())) + LABELS
    wire(pts, src, dst, **kw)

TITLE, SUB = 9.0, 7.5          # node title / sub-line sizes (pt)
PT, PB = 2.16, 6.05            # panel top / bottom
HDR = 0.24                     # N.panel header height


def stack(nid_prefix, specs, x, w, y0, gap, layer, pnl, **kw):
    """Stack nodes top-down; returns list of ids. specs = [(id, h, title, subs)]."""
    ids, y = [], y0
    for nid, h, title, subs in specs:
        node(nid, x, y, w, h, layer, title, subs, pnl=pnl, title_sz=TITLE, sub_sz=SUB, **kw)
        ids.append(nid)
        y += h + gap
    return ids


def vchain(ids):
    """Down-arrows between consecutive stacked nodes."""
    for a, b in zip(ids, ids[1:]):
        W([(N.CX(a), N.B(a)), (N.CX(b), N.T(b))], a, b)


def layout():
    N.BOXES.clear(); N.WIRES.clear(); N.DOTS.clear()

    # ---------------- 1 · INPUTS ----------------
    x1, w1 = 0.15, 2.30
    panel("P1", x1, PT, w1, PB - PT, C_IN, "1 · INPUTS", "what goes in")
    stack("in", [
        ("in1", 0.86, "Field parameters", ("field_params.json · 1,150 m · 11,500 cP",
                                           "every value tagged CONFIRMED /",
                                           "ASSUMPTION, with its source")),
        ("in2", 0.62, "Oil India cycle records (CSV)", ("steam t · soak d · spm · stroke",
                                                        "pressure · oil m³ · days")),
        ("in3", 0.48, "Measured pump card (CSV)", ("position, load from the well",)),
        ("in4", 0.48, "Prices", ("typed on the Overview page · diesel ₹/L · crude ₹/bbl",)),
    ], x1 + 0.22, w1 - 0.32, PT + HDR + 0.10, 0.11, C_IN, "P1")
    label("in_note", x1 + 0.22, 5.28, w1 - 0.32, 0.56,
          "No sensor data and no Oil India internal data are used today; "
          "records and cards arrive as uploads on the dashboard.", size=7.0, align="l")

    # ---------------- 2 · PHYSICS TWIN ----------------
    x2, w2 = 2.87, 3.20
    panel("P2", x2, PT, w2, PB - PT, C_PHY, "2 · PHYSICS TWIN", "day by day · twin/")
    chip("loop", x2 + 0.10, PT + HDR + 0.08, w2 - 0.20, 0.30, C_PHY,
         "inject → soak → produce  ·  operating rule  ·  injectivity gate", "P2",
         face=FONT, size=7.5)
    mids = stack("m", [
        ("m1", 0.56, "Heating", ("Marx–Langenheim heated zone",
                                 "Boberg–Lantz cooldown after injection")),
        ("m2", 0.56, "Viscosity", ("Walther / ASTM D341 μ(T)",
                                   "Pal–Rhodes emulsion: the fluid on the rods")),
        ("m3", 0.56, "Inflow", ("Vogel + composite-radial productivity",
                                "reservoir pressure and water cut as states")),
        ("m4", 0.56, "Rod pump", ("API RP 11L loads · floating index ≤ 0.6",
                                  "Gibbs wave-equation dynamometer card")),
    ], x2 + 0.10, w2 - 0.20, PT + HDR + 0.50, 0.12, C_PHY, "P2")
    vchain(mids)
    node("st", x2 + 0.10, 5.52, w2 - 0.20, 0.44, C_PHY, "State written every simulated day",
         ("temperature · viscosity · oil rate · rod load · water cut · float index",),
         pnl="P2", title_sz=8.0, sub_sz=7.0, kind="note", fill=TINT[C_PHY], line_w=0.75)
    W([(N.CX("m4"), N.B("m4")), (N.CX("st"), N.T("st"))], "m4", "st")

    # ---------------- 3 · SEARCH & CHECKS ----------------
    x3, w3 = 6.49, 2.85
    panel("P3", x3, PT, w3, PB - PT, C_ML, "3 · SEARCH & CHECKS", "ml/")
    sids = stack("s", [
        ("s1", 0.46, "3,000 simulated cycles", ("Latin-hypercube runs of the twin",)),
        ("s2", 0.46, "Fast what-if model + search", ("XGBoost surrogate · Bayesian proposals",)),
        ("s3", 0.46, "Physics grid: 12,936 plans", ("every winner re-run in the twin · ~3 min",)),
        ("s4", 0.46, "Safety checks", ("float index ≤ 0.6 · injectivity ≥ 400 kPa",)),
        ("s5", 0.46, "Uncertainty: 1,500 draws", ("p10 / p50 / p90 on every number",)),
        ("s6", 0.46, "Calibration from records", ("re-fits water cut, thickness, inflow",)),
    ], x3 + 0.10, w3 - 0.20, PT + HDR + 0.10, 0.12, C_ML, "P3")
    vchain(sids[:5])

    # ---------------- 4 · SERVICE ----------------
    x4, w4 = 9.76, 1.45
    panel("P4", x4, PT, w4, PB - PT, C_SVC, "4 · SERVICE", "api/")
    api = [("a1", "/api/simulate"), ("a2", "/api/dyno"), ("a3", "/api/optimize"),
           ("a4", "/api/jobs/{id}"), ("a5", "/api/uq"), ("a6", "/api/calibrate"),
           ("a7", "/api/schedule")]
    y = PT + HDR + 0.10
    for aid, txt in api:
        chip(aid, x4 + 0.10, y, w4 - 0.20, 0.30, C_SVC, txt, "P4", face=MONO, size=7.5)
        y += 0.40
    node("db", x4 + 0.10, y + 0.02, w4 - 0.20, 0.58, C_SVC, "FastAPI + SQLite",
         ("JSON in / out · jobs", "run history · Docker"), pnl="P4", title_sz=8.0, sub_sz=7.0)

    # ---------------- 5 · DASHBOARD → ENGINEER ----------------
    x5, w5 = 11.51, 1.79
    panel("P5", x5, PT, w5, PB - PT, C_SVC, "5 · DASHBOARD", "")
    dids = stack("d", [
        ("d1", 0.46, "Overview", ("managers · ₹, steam, CO₂",)),
        ("d2", 0.46, "Simulator", ("engineers · day by day",)),
        ("d3", 0.46, "Recommendation", ("plan · ranges · checks",)),
        ("d4", 0.46, "Model basis", ("reviewers · upload data",)),
    ], x5 + 0.10, w5 - 0.20, PT + HDR + 0.10, 0.10, C_SVC, "P5")
    node("eng", x5 + 0.10, 4.78, w5 - 0.20, 1.10, C_IN, "Engineer",
         ("reviews → stages → confirms", "applies at the well by hand",
          "nothing is sent to a controller"), pnl="P5", title_sz=TITLE, sub_sz=SUB, line_w=1.75)
    W([(N.CX("d4"), N.B("d4")), (N.CX("eng"), N.T("eng"))], "d4", "eng")

    # ---------------- data movements (all orthogonal) ----------------
    g12 = (x1 + w1 + x2) / 2                      # gap centre columns 1-2
    W([(N.R("in1"), N.CY("in1")), (g12 + 0.06, N.CY("in1")), (g12 + 0.06, N.CY("m1")),
          (N.L("m1"), N.CY("m1"))], "in1", "m1")
    W([(N.R("in3"), N.CY("in3")), (g12 + 0.06, N.CY("in3")), (g12 + 0.06, N.CY("m4")),
          (N.L("m4"), N.CY("m4"))], "in3", "m4")
    # records -> calibration along the bottom lane
    W([(N.R("in2"), N.CY("in2")), (g12 - 0.06, N.CY("in2")), (g12 - 0.06, 6.16),
          (N.CX("s6"), 6.16), (N.CX("s6"), N.B("s6"))], "in2", "s6")
    # prices -> overview along the bottom lane, up the far-right channel
    # twin -> search: cycles feed the surrogate; the grid re-runs the twin
    g23 = (x2 + w2 + x3) / 2
    W([(N.R("st"), N.CY("st")), (g23 - 0.08, N.CY("st")), (g23 - 0.08, N.CY("s1")),
          (N.L("s1"), N.CY("s1"))], "st", "s1")
    W([(N.L("s3"), N.CY("s3")), (g23 + 0.08, N.CY("s3")), (g23 + 0.08, N.CY("m3")),
          (N.R("m3"), N.CY("m3"))], "s3", "m3", heads="both")
    # search -> service bus
    g34 = (x3 + w3 + x4) / 2
    W([(N.CX("st"), N.B("st")), (N.CX("st"), 6.30), (g34, 6.30), (g34, N.CY("a1")),
          (N.L("a1"), N.CY("a1"))], "st", "a1", extra_ok=("in_note",))
    W([(g34, N.CY("a2")), (N.L("a2"), N.CY("a2"))], None, "a2")
    W([(N.R("s3"), N.CY("s3")), (g34, N.CY("s3")), (g34, N.CY("a3")), (N.L("a3"), N.CY("a3"))], "s3", "a3")
    W([(N.R("s5"), N.CY("s5")), (g34, N.CY("s5")), (g34, N.CY("a5")), (N.L("a5"), N.CY("a5"))], "s5", "a5")
    W([(N.R("s6"), N.CY("s6")), (g34, N.CY("s6")), (g34, N.CY("a6")), (N.L("a6"), N.CY("a6"))], "s6", "a6")
    # service -> dashboard bus
    g45 = (x4 + w4 + x5) / 2
    W([(N.R("a1"), N.CY("a1")), (g45, N.CY("a1")), (g45, N.CY("d2")), (N.L("d2"), N.CY("d2"))], "a1", "d2")
    W([(N.R("a3"), N.CY("a3")), (g45, N.CY("a3")), (g45, N.CY("d3")), (N.L("d3"), N.CY("d3"))], "a3", "d3")
    W([(N.R("a5"), N.CY("a5")), (g45, N.CY("a5")), (g45, N.CY("d1")), (N.L("d1"), N.CY("d1"))], "a5", "d1")
    W([(N.R("a6"), N.CY("a6")), (g45, N.CY("a6")), (g45, N.CY("d4")), (N.L("d4"), N.CY("d4"))], "a6", "d4")
    # prices reach the Overview page directly (typed on the page): lane -> right channel
    # feedback: after each cycle the real records come back -> calibration -> twin re-fits
    W([(N.CX("eng"), N.B("eng")), (N.CX("eng"), 6.42), (x1 + 0.10, 6.42),
          (x1 + 0.10, N.CY("in2")), (N.L("in2"), N.CY("in2"))], "eng", "in2", kind="feedback",
         extra_ok=("in_note",))

    # gap labels: what travels
    for lid, gx, txt, yy in (("l_params", g12, "params", N.CY("m1") - 0.22), ("l_card", g12, "card", N.CY("m4") - 0.22),
                             ("l_runs", g23, "3,000 runs", N.CY("s1") - 0.22), ("l_rerun", g23, "re-run", N.CY("s3") - 0.22),
                             ("l_plans", g34, "plans", N.CY("s3") - 0.22), ("l_json", g45, "JSON", N.CY("a3") - 0.22)):
        label(lid, gx - 0.24, yy, 0.48, 0.18, txt, size=7.0, align="ctr")
    label("cap_fb", 3.00, 6.48, 8.60, 0.20,
          "after each real cycle: records come back → calibration → the twin re-fits → next recommendation "
          "(dashed loop)", size=7.5, align="l", bold=True)
    label("trust", 0.15, 6.70, 13.15, 0.20,
          "Built on published physics · benchmarked against a California steam-ratio band · 263 automated tests", size=8.0, align="r", color=C_GREY)


def draw(slide):
    N.PREFIX = PREFIX
    for b in N.BOXES.values():
        N.draw_box(slide, b)
    for i, w in enumerate(N.WIRES):
        N.draw_wire(slide, w, i)


def pdf_check(pdf: Path, page: int):
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    raw = " ".join((reader.pages[page].extract_text() or "").split())
    wanted = ["1 · INPUTS", "2 · PHYSICS TWIN", "3 · SEARCH & CHECKS", "4 · SERVICE", "5 · DASHBOARD",
              "Heating", "Viscosity", "Inflow", "Rod pump", "Physics grid: 12,936 plans",
              "Uncertainty: 1,500 draws", "/api/optimize", "Recommendation", "Engineer",
              "nothing is sent to a controller", "263 automated tests"]
    found = [w for w in wanted if w in raw]
    return len(reader.pages), wanted, found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--into-strict", action="store_true")
    args = ap.parse_args()
    into = args.into_strict

    S.PNG = PNG
    prs, slide, furniture = S.open_slide3(keep_only=not into)
    for shp in list(slide.shapes):          # idempotent for our own prefix too
        if shp.name.startswith(PREFIX):
            shp._element.getparent().remove(shp._element)
    layout()
    problems, fit_rows = N.run_gates(furniture)
    print("-- text fit (fullest 8) --")
    for fill, bid, detail in fit_rows[:8]:
        print(f"  {bid:<10} {fill * 100:5.1f}%  lines/para {detail}")
    if problems:
        print("\n!! GATES FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print(f"GATES PASS ({len(N.BOXES)} boxes, {len(N.WIRES)} wires)")
    draw(slide)

    if into:
        if not SWAP_BACKUP.exists():
            shutil.copy2(S.STRICT, SWAP_BACKUP)
            print(f"backed up STRICT deck -> {SWAP_BACKUP.relative_to(ROOT)}")
        deck, pdf, slide_no, pages = S.STRICT, S.STRICT_PDF, S.SLIDE_IDX + 1, 6
    else:
        deck, pdf, slide_no, pages = OUT, OUT_PDF, 1, 1
    prs.save(str(deck))
    print(f"saved {deck.relative_to(ROOT)} ({deck.stat().st_size / 1024:.0f} KB)")
    if args.no_export:
        return
    S.export_com(deck, pdf, slide_no)
    print(f"exported {pdf.relative_to(ROOT)} and {PNG.relative_to(ROOT)}")
    n_pages, wanted, found = pdf_check(pdf, slide_no - 1)
    print(f"PDF pages: {n_pages}; selectable text found: {len(found)}/{len(wanted)}")
    missing = [w for w in wanted if w not in found]
    if missing:
        print("  missing:", missing)
    if n_pages != pages or missing:
        sys.exit("PDF check failed")


if __name__ == "__main__":
    main()
