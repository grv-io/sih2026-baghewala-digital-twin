r"""Slides 2, 4, 5 and 6 of the STRICT deck, redrawn in the FINAL slide-3 aesthetic.

Same family as build_tech_slide_final.py: rounded cards with a coloured header band, a
tinted icon disc, one plain sentence, and small "detail chips" -- so a non-technical
screener gets the story from the icons and sentences, and a technical judge gets the
substance from the chips. Every word is native text (copyable in the PDF); only the
icons are pictures rasterised from ppt/assets/svg/icons/.

Template rules (SIH 2026 idea-presentation format) are respected:
  * slide order, titles, the "Your Team Name" oval, the SIH banner, the footer bar,
    footer text and slide numbers are not touched (they are gate-checked furniture);
  * the template's own pointer texts ("Detailed explanation of the proposed solution",
    "Potential challenges and risks", ...) are kept VERBATIM as the card header bands;
  * slide 1 (title page) and slide 3 (technical approach) are left exactly as they are.

Slides 2 and 6 carry three link placeholders (live dashboard, demo video, GitHub) for
the team to fill in -- native text boxes, so they are editable in PowerPoint.

Outputs (in place, after a backup):
    ppt/final/SIH26120_Idea_Presentation_STRICT.pptx / .pdf
    ppt/diagram/slide{2,4,5,6}_final.png
    ppt/archive/SIH26120_Idea_Presentation_STRICT_pre-final-deck.pptx  (backup, once)

Run:
    .venv\Scripts\python.exe ppt\build_deck_final.py               # build, gates, export
    .venv\Scripts\python.exe ppt\build_deck_final.py --no-export   # build + gates only
"""

from __future__ import annotations

import argparse
import copy
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.util import Inches

ROOT = Path(__file__).resolve().parent.parent
PPT_DIR = ROOT / "ppt"
sys.path.insert(0, str(PPT_DIR))
import build_tech_slide_native as N  # noqa: E402
import build_tech_slide_simple as S  # noqa: E402
from build_tech_slide_native import (  # noqa: E402
    A, Box, E, EMU, Para, Wire, C_IN, C_ML, C_PHY, C_SVC, C_TEXT, PANEL_FILL, TINT,
)
from build_strict_deck import HEADING_COLOR, fill_textbox  # noqa: E402

DECK = PPT_DIR / "final" / "SIH26120_Idea_Presentation_STRICT.pptx"
PDF = DECK.with_suffix(".pdf")
BACKUP = PPT_DIR / "archive" / "SIH26120_Idea_Presentation_STRICT_pre-final-deck.pptx"
PNG_DIR = PPT_DIR / "diagram"
PREFIX = "FD_"
C_GREY = "595959"
C_ARROW = "595959"

# --------------------------------------------------------------------------- #
# extra icons from the library (added to the simple builder's registry)        #
# --------------------------------------------------------------------------- #
for _k, _n in {
    "rupee": "rupee-saving", "co2": "co2-cloud", "team": "team", "graph": "graph-up",
    "wellhead": "well", "chip": "ai-chip", "optim": "optimization", "wrench":
    "wrench-maintenance", "sensor": "sensor", "gauge": "pressure-gauge", "barrel":
    "oil-barrel", "flag": "india-flag-chakra", "bolt": "energy-bolt", "temp":
    "temperature", "visc": "viscosity", "valve": "valve", "pipe": "pipeline",
}.items():
    S.ICONS[_k] = (S._lib(_n, 2.2), f"ic_{_n}.svg")

# --------------------------------------------------------------------------- #
# geometry shared by the four slides                                           #
# --------------------------------------------------------------------------- #
X0, X1 = 0.32, 13.11
FOOT = 6.93                      # template footer bar starts at 6.95
TOP_BOX = (0.55, 1.28, 12.30)    # the template pointer text box: left, top, width
HDR_H = 0.58                     # two-line header bands (the pointers are long)
DISC_D = 0.80
ICON_D = 0.64
CARD_H = 3.32
TITLE_PT, SENT_PT, CHIP_PT, STRIP_PT = 13.0, 11.5, 9.5, 11.0


def card(pid, x, y, w, h, col, header, icon, sentence, chips, chip_h=0.235,
         chip_gap=0.07, hdr_pt=TITLE_PT, sent_h=None, icon_disc=True, sent_pt=SENT_PT):
    """A station card: header band (template pointer, verbatim) + icon disc + one
    plain sentence (hand-balanced lines) + detail chips."""
    N.add(Box(pid, x, y, w, h, "panel", col, fill=PANEL_FILL[col], line=col, line_w=1.5,
              radius=0.12))
    N.add(Box(pid + "_hdr", x, y, w, HDR_H, "header", col,
              [Para(header, hdr_pt, True, color="FFFFFF", align="ctr")],
              fill=col, line=None, radius=0.12, anchor="ctr", ins=(0.08, 0.0, 0.08, 0.0)))
    cy = y + HDR_H + 0.07
    if icon_disc:
        dx = x + (w - DISC_D) / 2
        S.DISCS.append((pid + "_disc", col, dx, cy, DISC_D))
        S.PICS.append((pid + "_icon", icon, col, dx + (DISC_D - ICON_D) / 2,
                       cy + (DISC_D - ICON_D) / 2, ICON_D, pid))
        cy += DISC_D + 0.05
    sh = sent_h if sent_h is not None else 0.20 * len(sentence) + 0.02
    N.add(Box(pid + "_txt", x + 0.10, cy, w - 0.20, sh, "label", col,
              [Para(t, sent_pt, color=C_TEXT, align="ctr") for t in sentence],
              fill=None, line=None, anchor="t", ins=(0.0, 0.0, 0.0, 0.0)))
    cy += sh + 0.06
    for k, text in enumerate(chips):
        N.add(Box(f"{pid}_d{k + 1}", x + 0.08, cy + k * (chip_h + chip_gap), w - 0.16,
                  chip_h, "chip", col, [Para(text, CHIP_PT, color=C_TEXT)],
                  fill=TINT[col], line=None, panel=pid, anchor="ctr", radius=0.05,
                  ins=(0.06, 0.0, 0.04, 0.0)))
    return cy + len(chips) * (chip_h + chip_gap)


def strip(gid, x, y, w, col, title, items, chip_h=0.46, icon=True, pt=STRIP_PT,
          hdr_h=0.27, bold=True, fill="FFFFFF"):
    """A bottom strip: header band + a row of chips (icon + 1-2 line label)."""
    h = hdr_h + 0.06 + chip_h + 0.06
    N.add(Box(gid, x, y, w, h, "panel", col, fill=PANEL_FILL[col], line=col, line_w=1.25,
              radius=0.10))
    N.add(Box(gid + "_hdr", x, y, w, hdr_h, "header", col,
              [Para(title, 12.0, True, color="FFFFFF")], fill=col, line=None, radius=0.10,
              anchor="ctr", ins=(0.12, 0.0, 0.06, 0.0)))
    pad, cg = 0.10, 0.10
    n = len(items)
    cw = (w - 2 * pad - (n - 1) * cg) / n
    cy = y + hdr_h + 0.06
    for ci, (ikey, text) in enumerate(items):
        cx = x + pad + ci * (cw + cg)
        cid = f"{gid}{ci + 1}"
        ins_l = 0.50 if (icon and ikey) else 0.08
        N.add(Box(cid, cx, cy, cw, chip_h, "chip", col,
                  [Para(t, pt, bold, color=C_TEXT) for t in text], fill=fill, line=col,
                  line_w=0.75, panel=gid, anchor="ctr", radius=0.06,
                  ins=(ins_l, 0.01, 0.05, 0.01)))
        if icon and ikey:
            S.PICS.append((cid + "_icon", ikey, col, cx + 0.08, cy + (chip_h - 0.36) / 2,
                           0.36, cid))
    return y + h


def note(lid, x, y, w, text, pt=10.5, align="r", color=C_GREY, italic=True, h=0.22):
    N.add(Box(lid, x, y, w, h, "label", color,
              [Para(text, pt, italic=italic, color=color, align=align)],
              fill=None, line=None, anchor="ctr", ins=(0.0, 0.0, 0.0, 0.0)))


def links(gid, y, col=C_SVC):
    """Three editable link placeholders for the team (website, video, GitHub)."""
    items = [("dash", ("Live dashboard:", "https://  ________________")),
             ("sensor", ("Demo video:", "https://  ________________")),
             ("chip", ("GitHub repository:", "https://  ________________"))]
    return strip(gid, X0, y, X1 - X0, col, "Links (fill in before submission)", items,
                 chip_h=0.44, bold=False, pt=10.5)


# --------------------------------------------------------------------------- #
# content -- slide 2: PROPOSED SOLUTION                                        #
# --------------------------------------------------------------------------- #
def layout_s2():
    """WHAT and WHY. Slide 3 is HOW -- so no pipeline numbers (53,000 runs, 1,500 runs,
    236 tests) and no repeated sentences here."""
    top = 2.26
    w = (X1 - X0 - 2 * 0.36) / 3
    hh = 3.68
    xs = [X0 + i * (w + 0.36) for i in range(3)]
    card("A", xs[0], top, w, hh, C_PHY, "Detailed explanation of the proposed solution",
         "twin", ("Every steam cycle, the twin re-plans", "the well from first principles —",
                  "heat, thick oil, the rod pump."),
         ["One well, simulated day by day: inject → soak → produce",
          "Tracks heat, viscosity, water cut and rod loads",
          "Inputs: field parameters + Oil India's cycle records",
          "Output: 5 settings + an operating rule, with a range",
          "Field view: which of the 33 wells gets steam next"])
    card("B", xs[1], top, w, hh, C_ML, "How it addresses the problem", "operator",
         ("Today's cycles are tuned by experience;", "the twin adds the physics", "and keeps the engineer in charge."),
         ["Manual steam and pump choices → one checked plan",
          "Rods that float late in the cycle → slowed, then pulled",
          "Steam wasted on cold oil → less steam per m³ of oil",
          "No field data yet → every assumption tagged and ranged",
          "Engineer reviews, confirms, then loads — advisory only"])
    card("C", xs[2], top, w, hh, C_IN, "Innovation and uniqueness of the solution",
         "search", ("Steam and pump treated as one system —", "because one thick oil", "causes both failures."),
         ["Couples the steam cycle to the rod pump — rare in tools",
          "Rod float predicted from falling water cut, late in the cycle",
          "Computed dynamometer card + a measured-card checker",
          "Self-audited: 3 physics bugs found and fixed before judging",
          "Offline, English + Hindi, no licence cost — built for the field"])
    links("K", top + hh + 0.12)


# --------------------------------------------------------------------------- #
# content -- slide 4: FEASIBILITY AND VIABILITY                                #
# --------------------------------------------------------------------------- #
def layout_s4():
    top = 1.92
    w = (X1 - X0 - 2 * 0.36) / 3
    hh = CARD_H + 0.34
    xs = [X0 + i * (w + 0.36) for i in range(3)]
    card("A", xs[0], top, w, hh, C_ML, "Analysis of the feasibility of the idea", "shield",
         ("Built and running today —", "published physics,", "real field numbers."),
         ["Real Baghewala inputs: 1,150 m, 11,500 cP",
          "Steam 85–97 kgf/cm², 60–70 % quality (published)",
          "Inside real field bands (uplift 5–6×, CalGEM)",
          "Runs on a laptop · deployable API + Docker"])
    card("B", xs[1], top, w, hh, C_PHY, "Potential challenges and risks", "alert",
         ("Some numbers stay assumptions", "until Oil India", "shares its data."),
         ["No public per-cycle Baghewala records",
          "Skin, water cut, condensate return unknown",
          "Rod float depends on emulsion behaviour",
          "Marginal at $65/bbl; negative net of royalty + cess"])
    card("C", xs[2], top, w, hh, C_IN, "Strategies for overcoming these challenges",
         "loop", ("Every assumption is tagged,", "given a range,", "and re-fitted from data."),
         ["Data request to Oil India ready (10 items)",
          "Calibration loop: 10 cycles → re-fit in minutes",
          "Uncertainty shown as a range, not one number",
          "Advisory mode first · control hook later"])
    # timeline strip
    y = top + hh + 0.12
    items = [("graph", ("Now: prototype,", "263 tests, live demo")),
             ("loop", ("Oct: Oil India data,", "calibrate the twin")),
             ("shield", ("Finale: field-checked", "recommendations")),
             ("wellhead", ("Pilot: one well,", "advisory mode"))]
    y2 = strip("T", X0, y, X1 - X0, C_SVC, "Roadmap", items, chip_h=0.46, pt=10.5)
    note("n", X0, y2 + 0.04, X1 - X0,
         "Team: Chemical Engineering + Software, MNIT Jaipur · open-source stack, "
         "no licence cost to Oil India", pt=10.5, align="l")


# --------------------------------------------------------------------------- #
# content -- slide 5: IMPACT AND BENEFITS                                      #
# --------------------------------------------------------------------------- #
def layout_s5():
    top = 1.92
    gap = 0.36
    wl = 4.05
    wr = X1 - X0 - gap - wl
    hh = CARD_H + 0.34
    card("A", X0, top, wl, hh, C_IN, "Potential impact on the target audience", "team",
         ("The plan: 1,000 t steam · 89 kgf/cm²", "64-in stroke · start 4.5 spm ·", "slow at the float limit, then pull."),
         ["Steam per m³ of oil: 3.3 → 2.8 t (−14 %), same policy",
          "Beats our assumed baseline in 84–96 % of runs",
          "₹ gain ₹0–5k/day — set by the VFD's minimum speed",
          "Drive slows the pump at the float limit, then pull",
          "Field view: which well gets steam next"])
    # right: benefits panel with three mini cards
    bx = X0 + wl + gap
    N.add(Box("B", bx, top, wr, hh, "panel", C_ML, fill=PANEL_FILL[C_ML], line=C_ML,
              line_w=1.5, radius=0.12))
    N.add(Box("B_hdr", bx, top, wr, HDR_H, "header", C_ML,
              [Para("Benefits of the solution (social, economic, environmental, etc.)",
                    TITLE_PT, True, color="FFFFFF", align="ctr")],
              fill=C_ML, line=None, radius=0.12, anchor="ctr", ins=(0.08, 0.0, 0.08, 0.0)))
    minis = [
        ("rupee", C_ML, "Economic",
         ("Less steam per barrel:", "3.3 → 2.8 t/m³ (−14 %)"),
         ["23 % less steam · 11 % less oil",
          "₹ gain hinges on OIL's VFD floor speed",
          "A range is shown, never one number"]),
        ("co2", C_PHY, "Environmental",
         ("Every tonne of steam burns", "71 kg of diesel"),
         ["Fewer tonnes of steam per m³ oil",
          "Less diesel and CO₂ per barrel",
          "No wasted pumping after float"]),
        ("team", C_SVC, "Social & operational",
         ("Operators keep control;", "the twin explains itself"),
         ["Plain words, English and Hindi",
          "Rod failures not priced yet ($15–50k)",
          "Open source — skills stay with OIL"]),
    ]
    mw = (wr - 0.10 * 2 - 0.12 * 2) / 3
    my = top + HDR_H + 0.10
    mh = hh - HDR_H - 0.20
    for i, (ikey, col, title, sent, chips) in enumerate(minis):
        mx = bx + 0.10 + i * (mw + 0.12)
        N.add(Box(f"M{i}", mx, my, mw, mh, "panel", col, fill="FFFFFF", line=col,
                  line_w=1.0, radius=0.10))
        dx = mx + (mw - 0.80) / 2
        S.DISCS.append((f"M{i}_disc", col, dx, my + 0.14, 0.80))
        S.PICS.append((f"M{i}_icon", ikey, col, dx + 0.09, my + 0.23, 0.62, f"M{i}"))
        N.add(Box(f"M{i}_t", mx + 0.06, my + 1.02, mw - 0.12, 0.24, "label", col,
                  [Para(title, 12.5, True, color=col, align="ctr")], fill=None, line=None,
                  anchor="ctr", ins=(0, 0, 0, 0)))
        N.add(Box(f"M{i}_s", mx + 0.06, my + 1.30, mw - 0.12, 0.40, "label", col,
                  [Para(t, 10.5, color=C_TEXT, align="ctr") for t in sent], fill=None,
                  line=None, anchor="t", ins=(0, 0, 0, 0)))
        cy = my + 1.80
        for k, text in enumerate(chips):
            N.add(Box(f"M{i}_d{k + 1}", mx + 0.06, cy + k * 0.31, mw - 0.12, 0.235,
                      "chip", col, [Para(text, 9.5, color=C_TEXT)], fill=TINT[col],
                      line=None, panel=f"M{i}", anchor="ctr", radius=0.05,
                      ins=(0.06, 0.0, 0.04, 0.0)))
    # honesty strip
    y = top + hh + 0.12
    items = [(None, ("Synthetic data today — the first real", "cycle records re-fit the twin in minutes")),
             (None, ("Cash-positive in about half of scenarios", "at OIL's FY25 price (vs a shut-in well)")),
             (None, ("Break-even at $65/bbl; negative net of", "royalty + cess — OIL's price deck decides")),
             (None, ("VFD minimum speed and pull criterion set", "the ₹ gain — both on our data request"))]
    y2 = strip("H", X0, y, X1 - X0, C_GREY, "Assumptions to confirm with Oil India", items, chip_h=0.42,
               icon=False, bold=False, pt=10.5)
    note("n", X0, y2 + 0.04, X1 - X0,
         "Scales with the field: 218 t (FY17) → 43,773 t (FY26) of heavy oil · 19 steam "
         "jobs in FY26 · one twin per well", pt=10.5, align="l")


# --------------------------------------------------------------------------- #
# content -- slide 6: RESEARCH AND REFERENCES                                   #
# --------------------------------------------------------------------------- #
C_LINK = "0563C1"
REFS_L = [  # (one-line citation, URL) -- the URL is a second, clickable line in the chip
    ("Marx & Langenheim (1959). Reservoir heating by hot fluid injection. Trans. AIME 216.",
     "https://doi.org/10.2118/1266-G"),
    ("Boberg & Lantz (1966). Thermally stimulated well rate — via SPE PEH ch. 15 (Prats).",
     "https://petrowiki.org/PEH:Thermal_Recovery_by_Steam_Injection"),
    ("Vogel (1968). Inflow performance relationships for solution-gas drive wells. JPT.",
     "https://onepetro.org/JPT/article/20/01/83/163252"),
    ("Gibbs (1963). Predicting the behavior of sucker-rod pumping systems. JPT 15.",
     "https://doi.org/10.2118/588-PA"),
    ("ASTM D341 viscosity–temperature charts (Walther); Pal & Rhodes (1989) emulsions.",
     "https://www.astm.org/Standards/D341.htm"),
    ("API Spec 11E / RP 11L — pumping-unit ratings and rod-string design.",
     "https://www.api.org/products-and-services/standards"),
]
REFS_R = [
    ("SPE-23APOG-535203 (2023). Baghewala heavy oil: depth, API, viscosity, heater case.",
     "https://onepetro.org/SPEAPOG/proceedings-abstract/23APOG/2-23APOG/535203"),
    ("Yasin et al. (2022). Scientific Reports 12:11086 — Baghewala-1 reservoir properties.",
     "https://doi.org/10.1038/s41598-022-14831-5"),
    ("Oil India Ltd — Rajasthan fields (BGW-8 CSS); investor presentation (realised price).",
     "https://www.oil-india.com/rajasthan-fields"),
    ("CalGEM (2021). Annual Report of the State Oil & Gas Supervisor — field steam-oil ratios.",
     "https://www.conservation.ca.gov/calgem/Documents/2021%20CalGEM%20Supervisor%20Annual%20Report.pdf"),
    ("Inside Climate News (2022) mirror of CalGEM injection data — 9,692 cyclic-steam records.",
     "https://github.com/InsideClimateNews/2022-09-ca-kern-oil-water"),
    ("Landscape: XSPOC, Lufkin SAM/SROD, ForeSite, AVEVA — none couples CSS with the pump.",
     "https://www.lufkin.com/solutions-services/srod/"),
]
REF_URLS: dict[str, str] = {}


def layout_s6():
    top = 1.92
    hh = 3.50
    w = X1 - X0
    N.add(Box("R", X0, top, w, hh, "panel", C_IN, fill=PANEL_FILL[C_IN], line=C_IN,
              line_w=1.5, radius=0.12))
    N.add(Box("R_hdr", X0, top, w, HDR_H, "header", C_IN,
              [Para("Details / Links of the reference and research work", TITLE_PT, True,
                    color="FFFFFF", align="ctr")],
              fill=C_IN, line=None, radius=0.12, anchor="ctr", ins=(0.08, 0.0, 0.08, 0.0)))
    cw = (w - 0.30) / 2
    REF_URLS.clear()
    for ci, refs in enumerate((REFS_L, REFS_R)):
        cx = X0 + 0.10 + ci * (cw + 0.10)
        cy = top + HDR_H + 0.10
        for k, (t, url) in enumerate(refs):
            bid = f"R{ci}{k}"
            N.add(Box(bid, cx, cy + k * 0.46, cw, 0.40, "chip", C_IN,
                      [Para(t, 9.5, color=C_TEXT), Para(url, 8.0, color=C_LINK)],
                      fill="FFFFFF", line=C_IN, line_w=0.5, panel="R", anchor="ctr",
                      radius=0.05, ins=(0.08, 0.01, 0.06, 0.01)))
            REF_URLS[PREFIX + bid] = url
    y = links("K", top + hh + 0.12)
    note("n", X0, y + 0.04, X1 - X0,
         "Every link is clickable in this PDF · full list with notes in the repository "
         "(docs/research/references.md)", pt=10.5, align="l")


# --------------------------------------------------------------------------- #
# the template pointer box on top of each slide                                #
# --------------------------------------------------------------------------- #
TOP_TEXT = {
    2: [dict(text="Proposed Solution (Describe your Idea/Solution/Prototype)", sz=18,
             bold=True, underline=True, color=HEADING_COLOR, space_after=3),
        dict(text="For Oil India's Baghewala field — India's first cyclic-steam wells: a "
                  "digital twin that recommends the steam, pump and stop settings for "
                  "each cycle, and tells the engineer why.", sz=13.5)],
    4: [dict(text="Feasibility and viability — a working prototype, its known gaps, and "
                  "how each gap closes with Oil India's data.", sz=13.5)],
    5: [dict(text="Impact and benefits — what changes for Oil India's operators, and "
                  "what we honestly do and do not claim yet.", sz=13.5)],
    6: [dict(text="Everything we used is public and cited — physics from the 1950s–80s, "
                  "field facts from Oil India and SPE, benchmarks from California's "
                  "regulator.", sz=13.5)],
}
TOP_H = {2: 0.92, 4: 0.48, 5: 0.48, 6: 0.48}
LAYOUT = {2: layout_s2, 4: layout_s4, 5: layout_s5, 6: layout_s6}
REMOVE = ("ColBox", "FeasCol", "SorCaption", "Picture 17410", PREFIX)


def prepare(slide, no):
    """Delete the old content shapes, reshape the pointer box, return the furniture."""
    for shp in list(slide.shapes):
        if shp.name.startswith(REMOVE):
            shp._element.getparent().remove(shp._element)
    xml = etree.tostring(slide._element).decode()
    for rId, rel in list(slide.part.rels.items()):
        if rel.reltype.endswith("/image") and f'"{rId}"' not in xml:
            slide.part.drop_rel(rId)
    tb = next(s for s in slide.shapes if s.name == "TextBox 8")
    tb.left, tb.top, tb.width, tb.height = (Inches(TOP_BOX[0]), Inches(TOP_BOX[1]),
                                            Inches(TOP_BOX[2]), Inches(TOP_H[no]))
    fill_textbox(tb, TOP_TEXT[no])
    furniture = {}
    for shp in slide.shapes:
        furniture[shp.name] = (shp.left / EMU, shp.top / EMU, (shp.left + shp.width) / EMU,
                               (shp.top + shp.height) / EMU)
    return furniture


def reset():
    N.BOXES.clear()
    N.WIRES.clear()
    N.DOTS.clear()
    S.PICS.clear()
    S.DISCS.clear()
    S.BIG.clear()


def extra_gates(furniture):
    problems = []
    texts = [b for b in N.BOXES.values() if b.paras]
    for b in texts:
        g = N.geom_inset(b)
        width_pt = (b.w - b.ins[0] - b.ins[2] - 2 * g) * 72 * N.FIT_SLACK
        for p in b.paras:
            lines = N.wrap(p, width_pt) or []
            if b.kind == "chip" and not b.id.startswith("R") and len(lines) != 1 \
                    and len(b.paras) == 1:
                problems.append(f"[lines] {b.id}: {p.text!r} renders as {lines}")
            if len(b.paras) > 1 and len(lines) != 1 and not b.id.startswith("R"):
                problems.append(f"[lines] {b.id}: hand-set line {p.text!r} wraps to {lines}")
            if b.id.startswith("R") and b.kind == "chip" and len(lines) != 1:
                problems.append(f"[lines] {b.id}: reference line wraps: {p.text!r}")
    rects = [(p[0], (p[3], p[4], p[3] + p[5], p[4] + p[5]), p[6]) for p in S.PICS]
    rects += [(d[0], (d[2], d[3], d[2] + d[4], d[3] + d[4]), None) for d in S.DISCS]
    for rid, r, cont in rects:
        if r[0] < N.BAND[0] or r[1] < N.BAND[1] or r[2] > N.BAND[2] or r[3] > N.BAND[3]:
            problems.append(f"[canvas] {rid} outside band")
        for fname, fr in furniture.items():
            if N.overlaps(r, fr):
                problems.append(f"[furniture] {rid} overlaps {fname}")
        for b in texts:
            if cont and b.id == cont:
                if b.kind == "chip" and (r[2] > b.x + b.ins[0] - 0.02 or not N.inside(r, b.r)):
                    problems.append(f"[icon] {rid} intrudes on {b.id}'s text")
                continue
            if N.overlaps(r, b.r):
                problems.append(f"[icon] {rid} overlaps text box {b.id}")
    return problems


def draw(slide, work):
    S.PREFIX = PREFIX
    N.PREFIX = PREFIX
    S.draw(slide, work)
    # reference chips: the URL line becomes a real hyperlink (clickable in the PDF too)
    for shp in slide.shapes:
        url = REF_URLS.get(shp.name)
        if url and shp.has_text_frame and len(shp.text_frame.paragraphs) > 1:
            for run in shp.text_frame.paragraphs[1].runs:
                run.hyperlink.address = url


def export_com(pages):
    exports = "\n".join(
        f"  $pres.Slides.Item({n}).Export('{PNG_DIR / f'slide{n}_final.png'}', 'PNG', 1920, 1080)"
        for n in pages)
    ps = f"""
$ErrorActionPreference = 'Stop'
$pp = New-Object -ComObject PowerPoint.Application
try {{
  $pres = $pp.Presentations.Open('{DECK}', -1, 0, 0)
  $pres.SaveAs('{PDF}', 32)
{exports}
  $pres.Close()
}} finally {{
  $pp.Quit()
}}
"""
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], check=True)


def pdf_check(wanted_by_page):
    from pypdf import PdfReader
    reader = PdfReader(str(PDF))
    report = {}
    for page, wanted in wanted_by_page.items():
        raw = reader.pages[page - 1].extract_text() or ""
        flat, tight = " ".join(raw.split()), "".join(raw.split())
        found = [w for w in wanted if " ".join(w.split()) in flat or "".join(w.split()) in tight]
        report[page] = (len(found), len(wanted), [w for w in wanted if w not in found])
    return len(reader.pages), report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()
    if not BACKUP.exists():
        shutil.copy2(DECK, BACKUP)
        print(f"backed up deck -> {BACKUP.relative_to(ROOT)}")
    prs = Presentation(str(DECK))
    slides = list(prs.slides)
    wanted_by_page = {}
    work = Path(tempfile.mkdtemp(prefix="fd_icons_"))
    try:
        for no, fn in LAYOUT.items():
            slide = slides[no - 1]
            furniture = prepare(slide, no)
            N.BAND = (0.15, TOP_BOX[1] + TOP_H[no] + 0.02, 13.30, FOOT)
            reset()
            fn()
            problems, fit_rows = N.run_gates(furniture)
            problems += extra_gates(furniture)
            print(f"-- slide {no}: fullest text boxes --")
            for fill, bid, detail in fit_rows[:4]:
                print(f"   {bid:<10} {fill * 100:5.1f}%  lines/para {detail}")
            if problems:
                print(f"\n!! SLIDE {no} GATES FAILED")
                for p in problems:
                    print("   " + p)
                sys.exit(1)
            print(f"   gates pass ({len(N.BOXES)} boxes, {len(S.PICS)} icons)")
            draw(slide, work)
            wanted_by_page[no] = [p.text for b in N.BOXES.values() for p in b.paras
                                  if len(p.text) > 12 and "____" not in p.text
                                  and not p.text.startswith("http")]
    finally:
        shutil.rmtree(work, ignore_errors=True)
    prs.save(str(DECK))
    print(f"saved {DECK.relative_to(ROOT)} ({DECK.stat().st_size / 1024:.0f} KB)")
    if args.no_export:
        return
    export_com(list(LAYOUT))
    n_pages, report = pdf_check(wanted_by_page)
    print(f"PDF pages: {n_pages}")
    bad = False
    for page, (nf, nw, missing) in report.items():
        print(f"   page {page}: selectable text {nf}/{nw}" + (f"  missing: {missing[:3]}" if missing else ""))
        bad |= bool(missing)
    if n_pages != 6 or bad:
        sys.exit("PDF check failed")


if __name__ == "__main__":
    main()
