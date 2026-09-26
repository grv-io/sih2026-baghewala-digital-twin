r"""Slide 3 (TECHNICAL APPROACH) as a NATIVE-SHAPE wiring diagram.

Replaces the full-width PNG (`TechArchitecture`, from ppt/diagram/render.py) with a
diagram built entirely from python-pptx shapes -- rounded rectangles, orthogonal
wires with real arrowheads, text frames -- so that PowerPoint -> PDF keeps every
label as SELECTABLE / COPYABLE text (the team lead's hard requirement).

What it touches: only slide 3's diagram. The title placeholder, SIH banner,
team-name oval, footer bar, footer text, slide number and the template's two
instruction pointers ("Technologies to be used" / "Methodology ...", TextBox 8)
are left exactly as they are. Slides 1, 2, 4, 5, 6 are not touched.

Gates (the build fails loudly, nothing is saved, if any of these trips):
  1. canvas   -- every new shape inside the 13.333 x 7.5 in slide and inside the
                 diagram band (below the pointer text, above the footer bar);
  2. overlap  -- no new shape overlaps any template furniture rectangle (the same
                 FURNITURE set as ppt/patch_tech_slide.py);
  3. nodes    -- no two nodes overlap; every node sits inside its layer panel;
  4. wiring   -- every wire is orthogonal and no wire segment passes through a
                 node that is not its own source/target, a panel header, or a
                 wire label (i.e. no wire runs through text);
  5. text fit -- every text frame is word-wrapped with real Arial / Consolas
                 advance widths (PIL) and its wrapped height must fit the box;
                 minimum font 7 pt.

Run (re-runnable / idempotent -- it deletes its own `TA_*` shapes first):
    .venv\Scripts\python.exe ppt\build_tech_slide_native.py            # build + export + QC
    .venv\Scripts\python.exe ppt\build_tech_slide_native.py --no-export # build + gates only

Export (PowerPoint COM through PowerShell -- no pywin32 in the venv):
    ppt/final/SIH26120_Idea_Presentation_STRICT.pdf   (6 pages, SaveAs ..., 32)
    ppt/diagram/slide3_native.png                     (1920 x 1080, Slides(3).Export)
then pypdf extracts page 3 and asserts >= 25 node labels are present as text.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from PIL import ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.util import Emu

ROOT = Path(__file__).resolve().parent.parent
PPT_DIR = ROOT / "ppt"
DECK = PPT_DIR / "final" / "SIH26120_Idea_Presentation_STRICT.pptx"
PDF = PPT_DIR / "final" / "SIH26120_Idea_Presentation_STRICT.pdf"
BACKUP = PPT_DIR / "archive" / "SIH26120_Idea_Presentation_STRICT_pre-native-slide3.pptx"
PNG = PPT_DIR / "diagram" / "slide3_native.png"

sys.path.insert(0, str(PPT_DIR))
from patch_tech_slide import FURNITURE, SLIDE_IDX  # noqa: E402  (same furniture set)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = f"{{{A_NS}}}"
PREFIX = "TA_"                      # every shape this script owns
OLD_PICTURE = "TechArchitecture"    # the PNG this script replaces

SLIDE_W, SLIDE_H = 13.3333, 7.5
BAND = (0.15, 2.12, 13.30, 6.93)    # diagram band: below pointers (2.08), above footer (6.95)
EMU = 914400

# --------------------------------------------------------------------------- #
# palette: 4 layer colours + neutral greys                                    #
# --------------------------------------------------------------------------- #
C_IN, C_PHY, C_ML, C_SVC = "1F497D", "C55A11", "2E7D32", "5B3FA0"   # navy/orange/green/purple
TINT = {C_IN: "EAF0F8", C_PHY: "FCEEE4", C_ML: "E8F3E9", C_SVC: "EEEAF7", "595959": "F2F2F2"}
PANEL_FILL = {C_IN: "F6F8FC", C_PHY: "FEF8F3", C_ML: "F6FBF6", C_SVC: "F9F7FD", "595959": "FAFAFA"}
C_VAL = "595959"
C_WIRE = "7F7F7F"
C_TEXT = "1A1A1A"
C_LABEL = "404040"

FONT, MONO, DEVA = "Arial", "Consolas", "Nirmala UI"
_FONT_FILES = {
    (FONT, False): r"C:\Windows\Fonts\arial.ttf",
    (FONT, True): r"C:\Windows\Fonts\arialbd.ttf",
    (MONO, False): r"C:\Windows\Fonts\consola.ttf",
    (MONO, True): r"C:\Windows\Fonts\consolab.ttf",
}
_fonts: dict = {}
MIN_PT = 7.0
LINE = 1.2          # PowerPoint single-spacing line height, x font size
FIT_SLACK = 0.975   # wrap at 97.5 % of the inner width (calibrated: PowerPoint kept a 98.5 % line, wrapped a 100.7 % one)


def _font(face, bold):
    key = (face, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(_FONT_FILES[key], 200)
    return _fonts[key]


def text_w_pt(text, face, bold, size):
    return _font(face, bold).getlength(text) / 200.0 * size


# --------------------------------------------------------------------------- #
# model                                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Para:
    text: str
    size: float = 7.0
    bold: bool = False
    italic: bool = False
    color: str = C_TEXT
    face: str = FONT
    align: str = "l"


@dataclass
class Box:
    id: str
    x: float
    y: float
    w: float
    h: float
    kind: str                      # panel | header | node | chip | note | label | legend
    layer: str = C_WIRE
    paras: list = field(default_factory=list)
    fill: str | None = None
    line: str | None = None
    line_w: float = 1.0
    dash: str | None = None
    radius: float = 0.07           # corner radius, inches (rounded kinds)
    anchor: str = "t"
    ins: tuple = (0.05, 0.02, 0.04, 0.01)   # l, t, r, b insets (in)
    panel: str | None = None       # the panel a node must sit inside

    @property
    def r(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)


@dataclass
class Wire:
    pts: list
    src: str | None
    dst: str | None
    kind: str = "flow"             # flow | thesis | feedback | validate | field
    heads: str = "end"             # end | both | none
    extra_ok: tuple = ()           # other boxes the wire may legitimately touch


BOXES: dict[str, Box] = {}
WIRES: list[Wire] = []
DOTS: list[tuple] = []


def add(box: Box) -> Box:
    assert box.id not in BOXES, box.id
    BOXES[box.id] = box
    return box


def panel(pid, x, y, w, h, layer, title, sub=""):
    add(Box(pid, x, y, w, h, "panel", layer, fill=PANEL_FILL[layer], line=layer,
            line_w=1.0, radius=0.09))
    add(Box(pid + "_hdr", x, y, w, 0.24, "header", layer,
            [Para(title + (f"   {sub}" if sub else ""), 9.5, True, color="FFFFFF")],
            fill=layer, line=None, radius=0.09, anchor="ctr", ins=(0.08, 0.0, 0.05, 0.0)))


def node(nid, x, y, w, h, layer, title, subs=(), pnl=None, title_sz=8.5, sub_sz=7.0,
         kind="node", fill="FFFFFF", title_face=FONT, line_w=1.0, dash=None, line=None,
         anchor="t"):
    paras = [Para(title, title_sz, True, color=layer if kind != "chip" else C_TEXT,
                  face=title_face)]
    paras += [Para(s, sub_sz, color=C_TEXT) for s in subs]
    return add(Box(nid, x, y, w, h, kind, layer, paras, fill=fill, line=line or layer,
                   line_w=line_w, dash=dash, panel=pnl, anchor=anchor))


def chip(cid, x, y, w, h, layer, text, pnl, face=MONO, size=7.5, subs=()):
    paras = [Para(text, size, True, color=C_TEXT, face=face)]
    paras += [Para(s, 7.0, color=C_TEXT) for s in subs]
    return add(Box(cid, x, y, w, h, "chip", layer, paras, fill=TINT[layer], line=layer,
                   line_w=0.75, panel=pnl, anchor="ctr", radius=0.05,
                   ins=(0.05, 0.01, 0.03, 0.01)))


def label(lid, x, y, w, h, text, size=7.0, color=C_LABEL, italic=True, bold=False,
          align="l"):
    return add(Box(lid, x, y, w, h, "label", C_LABEL,
                   [Para(text, size, bold, italic, color=color, align=align)],
                   fill=None, line=None, anchor="ctr", ins=(0.0, 0.0, 0.0, 0.0)))


def wire(pts, src=None, dst=None, kind="flow", heads="end", extra_ok=()):
    WIRES.append(Wire([tuple(p) for p in pts], src, dst, kind, heads, tuple(extra_ok)))


def dot(x, y):
    DOTS.append((x, y))


# edges of a box
def L(b): return BOXES[b].x
def R(b): return BOXES[b].x + BOXES[b].w
def T(b): return BOXES[b].y
def B(b): return BOXES[b].y + BOXES[b].h
def CX(b): return BOXES[b].x + BOXES[b].w / 2
def CY(b): return BOXES[b].y + BOXES[b].h / 2


# --------------------------------------------------------------------------- #
# the diagram                                                                  #
# --------------------------------------------------------------------------- #
PT, PB = 2.16, 5.56                           # layer panels: top / bottom
LANE = {1: 5.64, 2: 5.71, 3: 5.78, 4: 5.85}   # bottom routing channel under the panels
VAL_TOP = 5.93                                # validation ring / legend / field row


def layout():
    # ---------------- 1 · INPUTS --------------------------------------------
    panel("P_in", 0.32, PT, 1.48, PB - PT, C_IN, "1 · INPUTS")
    ix, iw = 0.38, 1.36
    node("params", ix, 2.46, iw, 0.94, C_IN, "field_params.json",
         ["rev 12 · real Baghewala", "1,150 m · 11,500 cP",
          "@ 50 °C", "sat. steam 85–97 kgf/cm²",
          "(307–317 °C at sandface)", "19 CSS jobs FY26"], pnl="P_in")
    node("price", ix, 3.40, iw, 0.46, C_IN, "Price decks",
         ["OIL FY25 $78.09/bbl", "FY26 floor $65/bbl"], pnl="P_in")
    node("csv", ix, 3.94, iw, 0.62, C_IN, "OIL cycle records",
         ["CSV: steam_t · soak_days", "cutoff · spm · oil_m3",
          "produce_days · peak"], pnl="P_in")
    node("calgem", ix, 4.70, iw, 0.46, C_IN, "CalGEM benchmark",
         ["9,692 real CSS cycles (CA)"], pnl="P_in")

    # ---------------- 2 · PHYSICS TWIN --------------------------------------
    panel("P_twin", 2.06, PT, 3.80, PB - PT, C_PHY, "2 · PHYSICS TWIN", "twin/")
    c1, c2, cw = 2.18, 4.07, 1.55
    node("cycle", c1, 2.46, c2 + cw - c1, 0.72, C_PHY, "cycle.py  —  CSS cycle orchestrator",
         ["day by day: inject → soak → produce",
          "water cut as a state (condensate flowback 0.87 → 0.56)",
          "produce ends at rate cutoff OR 3 days of rod float",
          "economics gross + incremental · opex"],
         pnl="P_twin")
    node("thermal", c1, 3.20, cw, 0.80, C_PHY, "thermal.py",
         ["Marx–Langenheim +", "sensible heat",
          "Boberg–Lantz cooldown,", "δ computed (PEH 15.70–74)",
          "wellbore loss"], pnl="P_twin")
    node("ipr", c2, 3.20, cw, 0.69, C_PHY, "ipr.py",
         ["composite-radial inflow", "μ-scaled cold rate · skin",
          "P_res(t) charge/bleed,", "P_current 9.4 MPa"], pnl="P_twin")
    node("visc", c1, 4.01, cw, 0.69, C_PHY, "viscosity.py",
         ["Walther / ASTM D341 μ(T)", "Pal–Rhodes emulsion",
          "(O/W ↔ W/O inversion 0.70,", "cap 10×)"], pnl="P_twin", line_w=2.25)
    node("srp", c2, 3.89, cw, 0.92, C_PHY, "srp.py",
         ["rod load · buoyancy · drag", "on produced stream ·",
          "floating index · liquid-basis", "pump capacity ·",
          "stroke 64–144 in · declining", "SPM (VFD)"], pnl="P_twin")
    node("callout", c1, 4.71, cw, 0.80, C_PHY, "ONE μ(T), TWO FAILURES",
         ["cold oil → low inflow (ipr)", "AND late-cycle rod float once the",
          "stream turns oil-continuous (srp)"],
         pnl="P_twin", title_sz=7.5, fill=TINT[C_PHY], dash="dash", kind="note")
    node("dyno", c2, 4.82, cw, 0.70, C_PHY, "dyno.py",
         ["Gibbs 1-D wave equation →", "surface card; valve-mechanics",
          "pump card; fault classifier",
          "measured-card classifier (96 %)"], pnl="P_twin")

    # ---------------- 3 · DATA & ML -----------------------------------------
    panel("P_ml", 6.10, PT, 3.20, PB - PT, C_ML, "3 · DATA & ML", "ml/")
    m1, m2, mw = 6.16, 7.78, 1.46
    node("gen", m1, 2.54, mw, 0.58, C_ML, "generate_data.py",
         ["twin/ · 3,000 LHS cycles", "6 controls incl. pressure", "& stroke · seed 42"],
         pnl="P_ml")
    node("train", m1, 3.14, mw, 1.62, C_ML, "train.py  —  XGBoost", [], pnl="P_ml")
    tx, tw = m1 + 0.07, mw - 0.14
    chip("m_oil", tx, 3.40, tw, 0.34, C_ML, "log-oil regressor", "P_ml", face=FONT,
         size=7.5, subs=["R² 0.996"])
    chip("m_margin", tx, 3.81, tw, 0.34, C_ML, "incr. margin / day", "P_ml", face=FONT,
         size=7.5, subs=["R² 0.98 in-envelope"])
    chip("m_float", tx, 4.22, tw, 0.42, C_ML, "float classifier", "P_ml", face=FONT,
         size=7.5, subs=["AUC 0.9998 (emulator role)"])
    node("uq", m2, 2.54, mw, 0.92, C_ML, "uq.py",
         ["1,500 paired Monte-Carlo", "16 inputs: skin, water cut,",
          "condensate recovery, prices…", "→ p10/p50/p90 · P(better)",
          "both decks"], pnl="P_ml")
    node("opt", m2, 3.48, mw, 0.46, C_ML, "optimize.py",
         ["surrogate what-if / UQ", "emulator · gp_minimize"], pnl="P_ml")
    node("rphys", m2, 3.96, mw, 1.02, C_ML, "recommend_physics.py  —  decision engine",
         ["true-physics 5-D grid: steam,", "pressure, cutoff, stroke, SPM",
          "(soak fixed 10 d)", "53,592 points · 36 s",
          "FI ≤ 0.6 · aggressive /", "conservative"], pnl="P_ml", title_sz=7.0)
    node("calib", m1, 4.98, m2 + mw - m1, 0.56, C_ML,
         "calibrate.py  —  closed loop (twin/)",
         ["bounded least-squares fit of formation water_cut / AOF / thickness",
          "from observed cycles → re-recommend"], pnl="P_ml")

    # ---------------- 4 · SERVICE --------------------------------------------
    panel("P_api", 9.52, PT, 1.46, PB - PT, C_SVC, "4 · SERVICE", "api/")
    ax, aw = 9.58, 1.34
    node("a_app", ax, 2.46, aw, 0.30, C_SVC, "FastAPI · typed /api/*", [], pnl="P_api",
         title_sz=7.5, anchor="ctr")
    chip("a_uq", ax, CY("uq") - 0.1, aw, 0.2, C_SVC, "/api/uq", "P_api")
    node("a_infra", ax, 3.13, aw, 0.44, C_SVC, "runtime",
         ["SQLite run history · jobs", "Docker / Render · CI"], pnl="P_api", title_sz=7.5)
    chip("a_opt", ax, CY("opt") - 0.1, aw, 0.2, C_SVC, "/api/optimize", "P_api", size=7.0)
    chip("a_jobs", ax, 3.97, aw, 0.17, C_SVC, "/api/jobs/{id}", "P_api", size=7.0)
    chip("a_rphys", ax, CY("rphys") - 0.1, aw, 0.2, C_SVC, "/api/recommend/physics",
         "P_api", size=7.0)
    chip("a_sched", ax, 4.59, aw, 0.17, C_SVC, "/api/schedule", "P_api", size=7.0)
    chip("a_cal", ax, 4.78, aw, 0.17, C_SVC, "/api/calibrate", "P_api", size=7.0)
    chip("a_sim", ax, 4.97, aw, 0.17, C_SVC, "/simulate → /runs", "P_api", size=7.0)
    chip("a_dyno", ax, 5.16, aw, 0.30, C_SVC, "/api/dyno/{cards,", "P_api",
         size=7.0, subs=["classify}"])

    # ---------------- 5 · OPERATOR DASHBOARD ---------------------------------
    panel("P_dash", 11.16, PT, 1.95, PB - PT, C_SVC, "5 · DASHBOARD")
    dx, dw = 11.23, 1.81
    add(Box("d_tags", dx, 2.42, dw, 0.25, "label", C_SVC,
            [Para("dashboard/ · EN / हिं · offline", 7.0, color=C_SVC),
             Para("live / MOCK auto-detect", 7.0, color=C_SVC)],
            fill=None, line=None, anchor="ctr", ins=(0.0, 0.0, 0.0, 0.0)))
    node("d_over", dx, 2.70, dw, 0.565, C_SVC, "Overview",
         ["recommendation: 5 set-points +", "operating rule · incremental",
          "₹/day · UQ range · P(better)"],
         pnl="P_dash")
    node("d_rec", dx, 3.265, dw, 1.24, C_SVC, "Recommendation",
         ["Bayesian optimiser job and the", "physics-verified point, side by side",
          "P(float) gate < 0.3 · run history",
          "stage → confirm → load", "no controller is contacted"], pnl="P_dash")
    node("d_model", dx, 4.505, dw, 0.45, C_SVC, "Model basis",
         ["equations · coverage matrix ·", "validation · calibrate · field view"],
         pnl="P_dash")
    node("d_sim", dx, 4.955, dw, 0.565, C_SVC, "Simulator",
         ["cycle replay: water cut & float index ·",
          "computed & measured dyno cards ·", "ISA-101 alarm"], pnl="P_dash")

    # ---------------- 6 · VALIDATION RING + field loop + legend --------------
    add(Box("P_val", 0.32, VAL_TOP, 8.98, 6.90 - VAL_TOP, "panel", C_VAL,
            fill=PANEL_FILL[C_VAL], line=C_VAL, line_w=1.0, dash="dash", radius=0.09))
    label("val_title", 3.06, VAL_TOP + 0.03, 1.66, 0.16, "6 · VALIDATION RING",
          size=8.5, italic=False, bold=True, color=C_VAL)
    vy, vh = 6.14, 0.70
    node("v_calgem", 0.38, vy, 1.36, vh, C_VAL, "CalGEM 2021",
         ["field SORs 3.47–8.24;", "model sits inside"], pnl="P_val", title_sz=8.0)
    node("v_bgw", 2.18, vy, 1.62, vh, C_VAL, "BGW-8 published",
         ["first-cycle uplift 5–6×", "SOR 3–8 (literature band)"], pnl="P_val",
         title_sz=8.0)
    node("v_tests", 3.98, vy, 1.62, vh, C_VAL, "236 tests pass",
         ["+ 2 declared gaps: soak;", "cold-well pumpability"],
         pnl="P_val", title_sz=8.0)
    node("v_audit", 6.16, vy, 1.46, vh, C_VAL, "Self-audit",
         ["external tech. review 27 Sep", "10 findings, 8 fixed"], pnl="P_val",
         title_sz=8.0)
    node("v_oil", 7.78, vy, 1.46, vh, C_VAL, "OIL data request",
         ["per-cycle field records", "→ calibrate.py loop"], pnl="P_val", title_sz=8.0)

    # field end of the loop (advisory only: the operator confirms, no auto-control)
    node("operator", 11.16, 6.08, 0.90, 0.78, C_SVC, "Operator",
         ["reviews and", "confirms", "(advisory)"], title_sz=8.0)
    node("well", 12.22, 6.08, 0.89, 0.78, C_SVC, "BGW well",
         ["CSS job +", "sucker-rod", "pump"], title_sz=8.0)

    # legend
    add(Box("P_leg", 9.52, VAL_TOP, 1.46, 6.90 - VAL_TOP, "panel", C_VAL, fill="FFFFFF",
            line="BFBFBF", line_w=0.75, radius=0.06))
    label("leg_title", 9.60, VAL_TOP + 0.03, 1.3, 0.15, "LEGEND", size=7.0, italic=False,
          bold=True, color=C_VAL)
    for i, (kind, text) in enumerate([("flow", "data flow"),
                                      ("thesis", "μ(T) coupling"),
                                      ("feedback", "feedback loop"),
                                      ("validate", "validated by")]):
        y = VAL_TOP + 0.29 + i * 0.18
        wire([(9.60, y), (9.98, y)], kind=kind)
        label(f"leg_{kind}", 10.04, y - 0.075, 0.92, 0.15, text, italic=False)

    # ----------------------------------------------------------------------- #
    # WIRES                                                                   #
    # ----------------------------------------------------------------------- #
    # params bus: params -> gap lane -> twin bottom -> central bus -> every module
    BUS_X, FORK_X, GAP_X, BUS_Y = 3.86, 3.97, 1.93, 5.545
    wire([(R("params"), 2.94), (GAP_X, 2.94), (GAP_X, BUS_Y), (BUS_X, BUS_Y),
          (BUS_X, B("cycle"))], "params", "cycle")
    dot(GAP_X, CY("price"))
    wire([(R("price"), CY("price")), (GAP_X, CY("price"))], "price", None, heads="none")
    for nid, y, side in [("thermal", 3.40, "l"), ("ipr", 3.34, "r"), ("visc", 4.42, "l"),
                         ("srp", 4.38, "r"), ("dyno", 5.08, "r")]:
        x_end = R(nid) if side == "l" else L(nid)
        wire([(BUS_X, y), (x_end, y)], None, nid)
        dot(BUS_X, y)

    # twin internals
    wire([(2.95, B("thermal")), (2.95, T("visc"))], "thermal", "visc")
    wire([(2.95, T("thermal")), (2.95, B("cycle"))], "thermal", "cycle")
    wire([(4.85, T("ipr")), (4.85, B("cycle"))], "ipr", "cycle")
    # the thesis wires: ONE viscosity feeds BOTH the inflow and the rod string
    wire([(R("visc"), 4.10), (FORK_X, 4.10), (FORK_X, 3.58), (L("ipr"), 3.58)], "visc",
         "ipr", kind="thesis")
    wire([(R("visc"), 4.24), (L("srp"), 4.24)], "visc", "srp", kind="thesis")
    wire([(4.85, B("srp")), (4.85, T("dyno"))], "srp", "dyno")
    wire([(R("srp"), 3.98), (5.74, 3.98), (5.74, 2.94), (R("cycle"), 2.94)], "srp", "cycle")

    # twin -> ML
    CYC_Y, J_X = 2.76, 6.02
    wire([(R("cycle"), CYC_Y), (L("gen"), CYC_Y)], "cycle", "gen")
    dot(J_X, CYC_Y)
    wire([(J_X, CYC_Y), (J_X, 2.47), (7.70, 2.47), (7.70, CY("uq")), (L("uq"), CY("uq"))],
         None, "uq")
    # ML internals
    wire([(6.88, B("gen")), (6.88, T("train"))], "gen", "train")
    wire([(R("train"), CY("opt")), (L("opt"), CY("opt"))], "train", "opt")
    wire([(8.50, B("opt")), (8.50, T("rphys"))], "opt", "rphys", heads="both")
    # ML -> API
    for s, d in [("uq", "a_uq"), ("opt", "a_opt"), ("rphys", "a_rphys"),
                 ("rphys", "a_sched"), ("calib", "a_cal")]:
        wire([(R(s), CY(d)), (L(d), CY(d))], s, d)
    # twin -> API through the bottom channel
    wire([(J_X, CYC_Y), (J_X, LANE[1]), (9.37, LANE[1]), (9.37, CY("a_sim")),
          (L("a_sim"), CY("a_sim"))], None, "a_sim")
    wire([(R("dyno"), 4.80), (5.94, 4.80), (5.94, LANE[2]), (9.45, LANE[2]),
          (9.45, CY("a_dyno")), (L("a_dyno"), CY("a_dyno"))], "dyno", "a_dyno")
    # observed CSV -> calibrate -> params (the closed loop)
    wire([(R("csv"), CY("csv")), (1.86, CY("csv")), (1.86, LANE[3]), (6.50, LANE[3]),
          (6.50, B("calib"))], "csv", "calib")
    wire([(6.80, B("calib")), (6.80, LANE[4]), (0.22, LANE[4]), (0.22, 2.70),
          (L("params"), 2.70)], "calib", "params", kind="feedback")
    wire([(10.25, B("a_opt")), (10.25, T("a_jobs"))], "a_opt", "a_jobs")
    # API -> dashboard
    for s, d in [("a_uq", "d_over"), ("a_opt", "d_rec"), ("a_rphys", "d_rec"),
                 ("a_sched", "d_model"), ("a_cal", "d_model"),
                 ("a_sim", "d_sim"), ("a_dyno", "d_sim")]:
        wire([(R(s), CY(s)), (L(d), CY(s))], s, d)
    # dashboard -> operator -> well (advisory; no closed-loop control claim)
    wire([(R("d_rec"), 4.10), (13.20, 4.10), (13.20, 5.98), (CX("operator"), 5.98),
          (CX("operator"), T("operator"))], "d_rec", "operator", kind="feedback")
    wire([(R("operator"), CY("operator")), (L("well"), CY("operator"))], "operator", "well",
         kind="feedback")
    # validation (dotted)
    wire([(1.60, B("calgem")), (1.60, T("v_calgem"))], "calgem", "v_calgem",
         kind="validate")
    add(Box("lbl_loop", 0.40, 5.24, 1.14, 0.26, "label", C_LABEL,
            [Para("closed loop: calibrate.py", 7.0, italic=True, color=C_LABEL),
             Para("re-fits these params", 7.0, italic=True, color=C_LABEL)],
            fill=None, line=None, anchor="ctr", ins=(0.0, 0.0, 0.0, 0.0)))
    wire([(2.95, T("v_bgw")), (2.95, B("P_twin"))], "v_bgw", "P_twin", kind="validate")
    wire([(4.79, T("v_tests")), (4.79, B("P_twin"))], "v_tests", "P_twin", kind="validate")
    wire([(7.95, T("v_oil")), (7.95, B("calib"))], "v_oil", "calib", kind="validate")


# --------------------------------------------------------------------------- #
# gates                                                                        #
# --------------------------------------------------------------------------- #
def overlaps(a, b, eps=1e-6):
    return not (a[2] <= b[0] + eps or b[2] <= a[0] + eps or a[3] <= b[1] + eps
                or b[3] <= a[1] + eps)


def inside(a, b, eps=1e-6):
    return a[0] >= b[0] - eps and a[1] >= b[1] - eps and a[2] <= b[2] + eps and \
        a[3] <= b[3] + eps


def wrap(para: Para, width_pt: float):
    words = para.text.split(" ")
    lines, cur = [], ""
    for w in words:
        cand = w if not cur else cur + " " + w
        if text_w_pt(cand, para.face if para.face in (FONT, MONO) else FONT, para.bold,
                     para.size) <= width_pt:
            cur = cand
        else:
            if not cur:
                return None          # a single word wider than the box
            lines.append(cur)
            cur = w
            if text_w_pt(cur, para.face, para.bold, para.size) > width_pt:
                return None
    lines.append(cur)
    return lines


def geom_inset(box: Box) -> float:
    """PowerPoint's roundRect preset puts its text rectangle 0.29289 x corner-radius
    inside the shape on every side (presetShapeDefinitions.xml: il = ss*a*0.29289).
    Measured the hard way: without this the gate passed a line PowerPoint wrapped."""
    if box.kind in ("label",):
        return 0.0
    if box.kind == "header":
        return 0.0          # round2Same: text rect only loses the top corners
    return box.radius * 0.29289


def text_height(box: Box):
    li, ti, ri, bi = box.ins
    g = geom_inset(box)
    width_pt = (box.w - li - ri - 2 * g) * 72 * FIT_SLACK
    ti, bi = ti + g, bi + g
    total_pt, detail = 0.0, []
    for p in box.paras:
        lines = wrap(p, width_pt) if p.text else [""]
        if lines is None:
            return None, [f"word too wide in {p.text!r}"]
        total_pt += len(lines) * p.size * LINE
        detail.append(len(lines))
    return total_pt / 72 + ti + bi, detail


def seg_hits_rect(p, q, r, shrink=0.012):
    (x1, y1), (x2, y2) = p, q
    rx0, ry0, rx1, ry1 = r[0] + shrink, r[1] + shrink, r[2] - shrink, r[3] - shrink
    if abs(y1 - y2) < 1e-9:                    # horizontal
        if not (ry0 < y1 < ry1):
            return False
        lo, hi = sorted((x1, x2))
        return hi > rx0 and lo < rx1
    lo, hi = sorted((y1, y2))                  # vertical
    if not (rx0 < x1 < rx1):
        return False
    return hi > ry0 and lo < ry1


def run_gates(furniture):
    problems = []
    node_kinds = ("node", "chip", "note")
    # 1 + 2: canvas band and furniture
    shapes = [(b.id, b.r) for b in BOXES.values()]
    for w in WIRES:
        xs = [p[0] for p in w.pts]
        ys = [p[1] for p in w.pts]
        shapes.append((f"wire{w.src}->{w.dst}", (min(xs), min(ys), max(xs), max(ys))))
    for sid, r in shapes:
        if r[0] < BAND[0] or r[1] < BAND[1] or r[2] > BAND[2] or r[3] > BAND[3]:
            problems.append(f"[canvas] {sid} {tuple(round(v, 2) for v in r)} outside band {BAND}")
        for fname, fr in furniture.items():
            if overlaps(r, fr):
                problems.append(f"[furniture] {sid} overlaps {fname} {fr}")
    # 3: nodes vs nodes, nodes inside their panel
    nodes = [b for b in BOXES.values() if b.kind in node_kinds]
    for i, a in enumerate(nodes):
        if a.panel and not inside(a.r, BOXES[a.panel].r):
            problems.append(f"[nodes] {a.id} not inside {a.panel}")
        if a.panel and overlaps(a.r, BOXES[a.panel + "_hdr"].r if a.panel + "_hdr" in BOXES
                                else (0, 0, 0, 0)):
            problems.append(f"[nodes] {a.id} overlaps header of {a.panel}")
        for b in nodes[i + 1:]:
            nested = inside(b.r, a.r) or inside(a.r, b.r)
            if overlaps(a.r, b.r) and not nested:
                problems.append(f"[nodes] {a.id} overlaps {b.id}")
    labels = [b for b in BOXES.values() if b.kind == "label"]
    for lb in labels:
        for n in nodes + [b for b in BOXES.values() if b.kind == "header"]:
            if overlaps(lb.r, n.r):
                problems.append(f"[labels] {lb.id} overlaps {n.id}")
    # 4: wiring
    blockers = nodes + labels + [b for b in BOXES.values() if b.kind == "header"]
    for w in WIRES:
        for p, q in zip(w.pts, w.pts[1:]):
            if abs(p[0] - q[0]) > 1e-9 and abs(p[1] - q[1]) > 1e-9:
                problems.append(f"[wiring] {w.src}->{w.dst} has a diagonal segment {p}->{q}")
                continue
            for bx in blockers:
                if bx.id in (w.src, w.dst) or bx.id in w.extra_ok:
                    continue
                # a wire may run inside the box that contains its own endpoint box
                if w.dst and bx.kind in node_kinds and inside(BOXES[w.dst].r, bx.r):
                    continue
                if w.src and bx.kind in node_kinds and inside(BOXES[w.src].r, bx.r):
                    continue
                if seg_hits_rect(p, q, bx.r):
                    problems.append(f"[wiring] {w.src}->{w.dst} segment {p}->{q} "
                                    f"runs through {bx.id}")
    # 5: text fit
    fit_rows = []
    for b in BOXES.values():
        if not b.paras:
            continue
        for p in b.paras:
            if p.size < MIN_PT:
                problems.append(f"[text] {b.id}: {p.size} pt < {MIN_PT} pt")
        need, detail = text_height(b)
        if need is None:
            problems.append(f"[text] {b.id}: {detail[0]}")
            continue
        fill = need / b.h
        fit_rows.append((fill, b.id, detail))
        if need > b.h + 1e-6:
            problems.append(f"[text] {b.id}: needs {need:.3f} in, box is {b.h:.3f} in "
                            f"(lines per para {detail})")
    fit_rows.sort(reverse=True)
    return problems, fit_rows


# --------------------------------------------------------------------------- #
# drawing                                                                      #
# --------------------------------------------------------------------------- #
def E(v):
    return Emu(int(round(v * EMU)))


def _strip_style(shape):
    st = shape._element.find(f"{{{P_NS}}}style")
    if st is not None:
        shape._element.remove(st)


def _ln_xml(color, width_pt, dash=None, heads="none", cap_round=False):
    ln = etree.SubElement(etree.Element("x"), f"{A}ln", w=str(int(width_pt * 12700)))
    if cap_round:
        ln.set("cap", "rnd")
    fill = etree.SubElement(ln, f"{A}solidFill")
    etree.SubElement(fill, f"{A}srgbClr", val=color)
    if dash:
        etree.SubElement(ln, f"{A}prstDash", val=dash)
    etree.SubElement(ln, f"{A}round")
    if heads in ("both",):
        etree.SubElement(ln, f"{A}headEnd", type="triangle", w="med", len="med")
    if heads in ("end", "both"):
        etree.SubElement(ln, f"{A}tailEnd", type="triangle", w="med", len="med")
    return ln


def _set_ln(shape, ln_new):
    spPr = shape._element.spPr
    old = spPr.find(f"{A}ln")
    if old is not None:
        spPr.remove(old)
    # a:ln must come after fill / geometry and before effect lists
    after = None
    for tag in ("prstGeom", "custGeom", "noFill", "solidFill", "gradFill", "blipFill",
                "pattFill", "grpFill"):
        el = spPr.find(f"{A}{tag}")
        if el is not None:
            after = el
    if after is None:
        spPr.insert(0, ln_new)
    else:
        after.addnext(ln_new)


def _set_fill(shape, color):
    spPr = shape._element.spPr
    for tag in ("noFill", "solidFill"):
        el = spPr.find(f"{A}{tag}")
        if el is not None:
            spPr.remove(el)
    geom = spPr.find(f"{A}prstGeom")
    if geom is None:
        geom = spPr.find(f"{A}custGeom")
    if color is None:
        el = etree.Element(f"{A}noFill")
    else:
        el = etree.Element(f"{A}solidFill")
        etree.SubElement(el, f"{A}srgbClr", val=color)
    geom.addnext(el)


def _rpr(p: Para, text: str):
    r = etree.Element(f"{A}rPr", lang="en-IN", sz=str(int(round(p.size * 100))), dirty="0")
    if p.bold:
        r.set("b", "1")
    if p.italic:
        r.set("i", "1")
    fill = etree.SubElement(r, f"{A}solidFill")
    etree.SubElement(fill, f"{A}srgbClr", val=p.color)
    deva = any("\u0900" <= ch <= "\u097f" for ch in text)
    face = p.face
    etree.SubElement(r, f"{A}latin", typeface=face)
    etree.SubElement(r, f"{A}ea", typeface=face)
    etree.SubElement(r, f"{A}cs", typeface=DEVA if deva else face)
    etree.SubElement(r, f"{A}sym", typeface=face)
    return r


def _fill_text(shape, box: Box):
    tf = shape.text_frame
    txBody = tf._txBody
    for p in txBody.findall(f"{A}p"):
        txBody.remove(p)
    bodyPr = txBody.find(f"{A}bodyPr")
    for child in list(bodyPr):
        bodyPr.remove(child)
    li, ti, ri, bi = box.ins
    bodyPr.set("wrap", "square")
    bodyPr.set("lIns", str(int(li * EMU)))
    bodyPr.set("tIns", str(int(ti * EMU)))
    bodyPr.set("rIns", str(int(ri * EMU)))
    bodyPr.set("bIns", str(int(bi * EMU)))
    bodyPr.set("anchor", box.anchor)
    bodyPr.set("rtlCol", "0")
    etree.SubElement(bodyPr, f"{A}noAutofit")
    if not box.paras:                      # a:txBody needs at least one a:p
        etree.SubElement(txBody, f"{A}p")
    for para in box.paras:
        p = etree.SubElement(txBody, f"{A}p")
        pPr = etree.SubElement(p, f"{A}pPr", marL="0", indent="0", algn=para.align)
        lnSpc = etree.SubElement(pPr, f"{A}lnSpc")
        etree.SubElement(lnSpc, f"{A}spcPct", val="100000")
        sb = etree.SubElement(pPr, f"{A}spcBef")
        etree.SubElement(sb, f"{A}spcPts", val="0")
        sa = etree.SubElement(pPr, f"{A}spcAft")
        etree.SubElement(sa, f"{A}spcPts", val="0")
        etree.SubElement(pPr, f"{A}buNone")
        if para.text:
            # split Devanagari into its own run so it gets the complex-script font
            chunks, cur, cur_deva = [], "", None
            for ch in para.text:
                d = "\u0900" <= ch <= "\u097f"
                if cur and d != cur_deva and ch != " ":
                    chunks.append(cur)
                    cur = ""
                cur += ch
                if ch != " ":
                    cur_deva = d
            chunks.append(cur)
            for c in chunks:
                r = etree.SubElement(p, f"{A}r")
                r.append(_rpr(para, c))
                t = etree.SubElement(r, f"{A}t")
                t.text = c
        end = etree.SubElement(p, f"{A}endParaRPr", lang="en-IN",
                               sz=str(int(round(para.size * 100))), dirty="0")


def draw_box(slide, b: Box):
    if b.kind == "label":
        shp = slide.shapes.add_textbox(E(b.x), E(b.y), E(b.w), E(b.h))
    elif b.kind == "header":
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, E(b.x), E(b.y),
                                     E(b.w), E(b.h))
        shp.adjustments[0] = min(0.5, b.radius / min(b.w, b.h))
        shp.adjustments[1] = 0.0
    else:
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, E(b.x), E(b.y), E(b.w),
                                     E(b.h))
        shp.adjustments[0] = min(0.5, b.radius / min(b.w, b.h))
    shp.name = PREFIX + b.id
    _strip_style(shp)
    if b.kind != "label":
        _set_fill(shp, b.fill)
        if b.line:
            _set_ln(shp, _ln_xml(b.line, b.line_w, b.dash))
        else:
            ln = etree.Element(f"{A}ln")
            etree.SubElement(ln, f"{A}noFill")
            _set_ln(shp, ln)
    if b.paras:
        _fill_text(shp, b)
    elif shp.has_text_frame:
        _fill_text(shp, b)
    return shp


WIRE_STYLE = {
    "flow": (C_WIRE, 1.0, None),
    "thesis": (C_PHY, 2.25, None),
    "feedback": ("404040", 1.25, "dash"),
    "field": ("404040", 1.25, "dash"),
    "validate": ("8C8C8C", 1.0, "sysDot"),
}


def draw_wire(slide, w: Wire, idx: int):
    color, width, dash = WIRE_STYLE[w.kind]
    pts = w.pts
    if len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        shp = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
    else:
        fb = slide.shapes.build_freeform(E(pts[0][0]), E(pts[0][1]), scale=1.0)
        fb.add_line_segments([(E(x), E(y)) for x, y in pts[1:]], close=False)
        shp = fb.convert_to_shape()
        _set_fill(shp, None)
    shp.name = f"{PREFIX}wire{idx:02d}_{w.src or 'bus'}_{w.dst or 'bus'}"
    _strip_style(shp)
    _set_ln(shp, _ln_xml(color, width, dash, w.heads))
    return shp


def draw_dot(slide, x, y, idx, d=0.06):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, E(x - d / 2), E(y - d / 2), E(d), E(d))
    shp.name = f"{PREFIX}dot{idx:02d}"
    _strip_style(shp)
    _set_fill(shp, "595959")
    ln = etree.Element(f"{A}ln")
    etree.SubElement(ln, f"{A}noFill")
    _set_ln(shp, ln)
    return shp


# --------------------------------------------------------------------------- #
# export + QC                                                                  #
# --------------------------------------------------------------------------- #
def export_com():
    ps = f"""
$ErrorActionPreference = 'Stop'
$pp = New-Object -ComObject PowerPoint.Application
try {{
  $pres = $pp.Presentations.Open('{DECK}', -1, 0, 0)
  $pres.SaveAs('{PDF}', 32)
  $pres.Slides.Item({SLIDE_IDX + 1}).Export('{PNG}', 'PNG', 1920, 1080)
  $pres.Close()
}} finally {{
  $pp.Quit()
}}
"""
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   check=True)


def pdf_label_check():
    from pypdf import PdfReader
    reader = PdfReader(str(PDF))
    n_pages = len(reader.pages)
    text = reader.pages[SLIDE_IDX].extract_text() or ""
    flat = " ".join(text.split())
    titles = []
    for b in BOXES.values():
        if b.kind in ("node", "chip", "note") and b.paras:
            titles.append(b.paras[0].text)
    found = [t for t in titles if " ".join(t.split()) in flat]
    missing = [t for t in titles if t not in found]
    return n_pages, titles, found, missing


# --------------------------------------------------------------------------- #
# main                                                                         #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()

    if not BACKUP.exists():
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DECK, BACKUP)
        print(f"backed up original deck -> {BACKUP.relative_to(ROOT)}")

    prs = Presentation(str(DECK))
    slide = list(prs.slides)[SLIDE_IDX]
    title = slide.shapes.title.text_frame.text.strip()
    if title != "TECHNICAL APPROACH":
        sys.exit(f"slide {SLIDE_IDX + 1} is {title!r}, not TECHNICAL APPROACH")

    # idempotent: drop the old PNG and any shapes from a previous run
    removed = 0
    for shp in list(slide.shapes):
        if shp.name == OLD_PICTURE or shp.name.startswith(PREFIX):
            shp._element.getparent().remove(shp._element)
            removed += 1
    print(f"removed {removed} old diagram shape(s)")
    # drop the old PNG's now-orphaned image relationship so the picture stops
    # shipping inside the .pptx (python-pptx keeps rels when a shape is deleted)
    slide_xml = etree.tostring(slide._element).decode()
    for rId, rel in list(slide.part.rels.items()):
        if rel.reltype.endswith("/image") and f'"{rId}"' not in slide_xml:
            slide.part.drop_rel(rId)
            print(f"dropped orphaned image relationship {rId}")

    furniture = {}
    for shp in slide.shapes:
        if shp.name in FURNITURE:
            furniture[shp.name] = (shp.left / EMU, shp.top / EMU,
                                   (shp.left + shp.width) / EMU, (shp.top + shp.height) / EMU)
    missing_furn = FURNITURE - set(furniture)
    if missing_furn:
        sys.exit(f"template furniture missing from slide 3: {missing_furn}")
    leftovers = [s.name for s in slide.shapes if s.name not in FURNITURE]
    if leftovers:
        sys.exit(f"unexpected non-furniture shapes on slide 3: {leftovers}")

    # rev-12 methodology line: update the template's own "Methodology and process
    # for implementation" pointer (TextBox 8, furniture -- position untouched, text only)
    pointer = next(s for s in slide.shapes if s.name == "TextBox 8")
    for p in pointer.text_frame.paragraphs:
        if p.text.startswith("Methodology and process for implementation:"):
            runs = p.runs
            assert len(runs) == 1, f"expected 1 run in the methodology pointer, got {len(runs)}"
            runs[0].text = (
                "Methodology and process for implementation: physics engine → "
                "3,000 synthetic cycles → ML emulator → true-physics grid optimiser → "
                "dashboard → advisory set-points + operating rule to the operator "
                "(SCADA hook planned)"
            )
            break
    else:
        sys.exit("methodology pointer paragraph not found in TextBox 8")

    layout()
    problems, fit_rows = run_gates(furniture)
    print("\n-- text fit (fullest 8 boxes) --")
    for fill, bid, detail in fit_rows[:8]:
        print(f"  {bid:<12} {fill * 100:5.1f}% of box height   lines/para {detail}")
    if problems:
        print("\n!! GATES FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)

    n_nodes = sum(1 for b in BOXES.values() if b.kind in ("node", "chip", "note"))
    n_panels = sum(1 for b in BOXES.values() if b.kind == "panel")
    legend_w = sum(1 for w in WIRES if w.src is None and w.dst is None)
    n_wires = len(WIRES) - legend_w
    sizes = sorted({p.size for b in BOXES.values() for p in b.paras})
    print(f"\nGATES PASS: canvas band, furniture ({', '.join(sorted(furniture))}), "
          f"node overlap, wiring (no wire through a node/label/header), text fit")
    print(f"nodes {n_nodes} · panels {n_panels} · wires {n_wires} (+{legend_w} legend "
          f"samples) · junction dots {len(DOTS)} · font sizes {sizes}")

    # draw: panels first (bottom of z-order), then wires, then nodes/labels on top
    order = ["panel", "header"]
    for b in BOXES.values():
        if b.kind in order:
            draw_box(slide, b)
    for i, w in enumerate(WIRES):
        draw_wire(slide, w, i)
    for i, (x, y) in enumerate(DOTS):
        draw_dot(slide, x, y, i)
    for b in BOXES.values():
        if b.kind not in order:
            draw_box(slide, b)

    prs.save(str(DECK))
    print(f"saved {DECK.relative_to(ROOT)} ({DECK.stat().st_size / 1024:.0f} KB)")

    if args.no_export:
        return
    export_com()
    print(f"exported {PDF.relative_to(ROOT)} and {PNG.relative_to(ROOT)}")
    n_pages, titles, found, missing = pdf_label_check()
    print(f"PDF pages: {n_pages}; page-3 selectable node labels: {len(found)}/{len(titles)}")
    if missing:
        print("  not found verbatim:", missing)
    if n_pages != 6:
        sys.exit(f"PDF has {n_pages} pages, expected 6")
    if len(found) < 25:
        sys.exit("fewer than 25 node labels extractable from the PDF -- text not native?")


if __name__ == "__main__":
    main()
