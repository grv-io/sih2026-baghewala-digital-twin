r"""
Build SIH26120_Idea_Presentation_STRICT.pptx.

STRICT = the official SIH 2026 template (ppt/template/template_official.pptx) is opened and
FILLED IN PLACE. Its master, layouts, theme, banner images, footer bar, slide-number
and "Your Team Name" ovals, title placeholders, title casing and title font sizes are
left exactly as downloaded from sih.gov.in. The only structural edit is deleting the
"IMPORTANT INSTRUCTIONS" slide, which the template itself tells you to delete.

Content model copied from the friend's *selected* SIH 2025 deck (see
ppt/notes/WINNING_DECK_ANALYSIS.md):
  * 6 slides total, instructions slide removed
  * the template's own instruction pointers are KEPT VERBATIM and reused as the
    section headings of each block/column
  * 3-9 word bullets, three-column layouts for anything with parallel parts
  * TECHNICAL APPROACH = one full-width architecture picture (ppt/diagram/), ~no text
  * IMPACT = benefit blocks + one real chart

Run:  .venv\Scripts\python.exe ppt\build_strict_deck.py
"""

from __future__ import annotations

import copy
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
PPT_DIR = ROOT / "ppt"
TEMPLATE = PPT_DIR / "template" / "template_official.pptx"
OUT_PPTX = PPT_DIR / "final" / "SIH26120_Idea_Presentation_STRICT.pptx"
BUILD_DIR = PPT_DIR / "_strict_build"
SVG_DIR = PPT_DIR / "assets" / "svg" / "diagrams"

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

# Template's own body typeface / heading colour (theme dk2 = 1F497D).
FONT = "Arial"
HEADING_COLOR = "1F497D"


# --------------------------------------------------------------------------- #
# SVG -> PNG (2x, headless Edge)                                              #
# --------------------------------------------------------------------------- #
def svg_to_png(name: str, w: int, h: int, crop: bool = False) -> Path:
    BUILD_DIR.mkdir(exist_ok=True)
    png = BUILD_DIR / f"{name}.png"
    wrapper = BUILD_DIR / f"wrap_{name}.html"
    svg = SVG_DIR / f"{name}.svg"
    wrapper.write_text(
        "<style>html,body{margin:0;padding:0;background:#fff;overflow:hidden}"
        f"img{{display:block;width:{w}px;height:{h}px}}</style>"
        f'<img src="file:///{svg.as_posix()}">',
        encoding="utf-8",
    )
    if png.exists():
        png.unlink()
    subprocess.run(
        [
            EDGE,
            "--headless",
            "--disable-gpu",
            "--force-device-scale-factor=2",
            "--hide-scrollbars",
            f"--screenshot={png}",
            f"--window-size={w},{h}",
            f"file:///{wrapper.as_posix()}",
        ],
        check=False,
        capture_output=True,
    )
    if not png.exists():
        raise RuntimeError(f"Edge failed to render {name}")
    if crop:
        im = Image.open(png).convert("RGB")
        # trim uniform white margin, keep a small pad
        bbox = Image.eval(im, lambda p: 255 - p).getbbox()
        if bbox:
            pad = 24
            im = im.crop(
                (
                    max(0, bbox[0] - pad),
                    max(0, bbox[1] - pad),
                    min(im.width, bbox[2] + pad),
                    min(im.height, bbox[3] + pad),
                )
            )
            im.save(png)
    return png


# --------------------------------------------------------------------------- #
# text helpers                                                                 #
# --------------------------------------------------------------------------- #
def _rpr(sz, bold=False, italic=False, underline=False, color=None) -> str:
    bits = [f'lang="en-IN" sz="{int(sz * 100)}"']
    if bold:
        bits.append('b="1"')
    if italic:
        bits.append('i="1"')
    if underline:
        bits.append('u="sng"')
    fill = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if color else ""
    return (
        f'<a:rPr {" ".join(bits)} dirty="0">{fill}'
        f'<a:latin typeface="{FONT}" pitchFamily="34" charset="0"/>'
        f'<a:ea typeface="{FONT}" pitchFamily="34" charset="0"/>'
        f'<a:cs typeface="{FONT}" pitchFamily="34" charset="0"/>'
        f'<a:sym typeface="{FONT}" pitchFamily="34" charset="0"/></a:rPr>'
    )


def _esc(t: str) -> str:
    return (
        t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def _para_xml(text, sz, bold=False, italic=False, underline=False, color=None,
              bullet=False, space_before=0, space_after=0, indent=0.0) -> str:
    if bullet:
        marl = int((0.22 + indent) * 914400)
        ppr_inner = (
            f'<a:buFont typeface="{FONT}" panose="020B0604020202020204" '
            'pitchFamily="34" charset="0"/><a:buChar char="&#8226;"/>'
        )
        ppr_attrs = f'marL="{marl}" indent="-{int(0.22 * 914400)}"'
    else:
        marl = int(indent * 914400)
        ppr_inner = "<a:buNone/>"
        ppr_attrs = f'marL="{marl}" indent="0"'
    spc = ""
    if space_before:
        spc += f'<a:spcBef><a:spcPts val="{int(space_before * 100)}"/></a:spcBef>'
    if space_after:
        spc += f'<a:spcAft><a:spcPts val="{int(space_after * 100)}"/></a:spcAft>'
    return (
        f"<a:p><a:pPr {ppr_attrs}>{spc}{ppr_inner}</a:pPr>"
        f"<a:r>{_rpr(sz, bold, italic, underline, color)}"
        f"<a:t>{_esc(text)}</a:t></a:r></a:p>"
    )


def fill_textbox(shape, paras, fixed=True):
    """Replace a shape's paragraphs with `paras` (list of dicts for _para_xml)."""
    tx = shape._element.find(f"{{http://schemas.openxmlformats.org/presentationml/2006/main}}txBody")
    if tx is None:
        tx = shape.text_frame._txBody
    for p in tx.findall(f"{A}p"):
        tx.remove(p)
    body_pr = tx.find(f"{A}bodyPr")
    if body_pr is not None and fixed:
        for child in list(body_pr):
            body_pr.remove(child)
        etree.SubElement(body_pr, f"{A}noAutofit")
        body_pr.set("wrap", "square")
    xml = "".join(_para_xml(**p) for p in paras)
    frag = etree.fromstring(f'<root xmlns:a="{NS_A}">{xml}</root>')
    for p in frag:
        tx.append(p)


def clone_textbox(slide, src_shape, left, top, width, height, name):
    """Deep-copy the template's own TextBox so all inherited formatting is identical."""
    new = copy.deepcopy(src_shape._element)
    spTree = slide.shapes._spTree
    spTree.append(new)
    # unique id/name
    cNvPr = new.find(
        ".//{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr"
    )
    max_id = max(
        int(e.get("id"))
        for e in spTree.iter()
        if e.tag.endswith("}cNvPr") and e.get("id") and e.get("id").isdigit()
    )
    cNvPr.set("id", str(max_id + 1))
    cNvPr.set("name", name)
    for shp in slide.shapes:
        if shp._element is new:
            shp.left, shp.top, shp.width, shp.height = (
                Inches(left),
                Inches(top),
                Inches(width),
                Inches(height),
            )
            return shp
    raise RuntimeError("clone failed")


def set_title(slide, text, size=None):
    ph = slide.shapes.title
    p = ph.text_frame.paragraphs[0]
    runs = p.runs
    if not runs:
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    if size:
        runs[0].font.size = Pt(size)


def body_box(slide):
    for shp in slide.shapes:
        if shp.name.startswith("TextBox"):
            return shp
    raise RuntimeError("no body textbox")


def add_pic(slide, png, left, top, max_w, max_h):
    im = Image.open(png)
    ar = im.width / im.height
    w, h = max_w, max_w / ar
    if h > max_h:
        h, w = max_h, max_h * ar
    left = left + (max_w - w) / 2
    top = top + (max_h - h) / 2
    return slide.shapes.add_picture(
        str(png), Inches(left), Inches(top), Inches(w), Inches(h)
    )


# --------------------------------------------------------------------------- #
# build                                                                        #
# --------------------------------------------------------------------------- #
def main():
    # TECHNICAL APPROACH diagram — purpose-built winner-style architecture picture.
    # Source: ppt/diagram/tech_architecture.html, rendered 2x by ppt/diagram/render.py.
    tech_png = PPT_DIR / "diagram" / "tech_architecture.png"
    if not tech_png.exists():
        subprocess.run(
            [sys.executable, str(PPT_DIR / "diagram" / "render.py")], check=True
        )
    sor_png = svg_to_png("sor_waterfall_light", 1200, 600, crop=True)

    prs = Presentation(str(TEMPLATE))
    slides = list(prs.slides)

    # ---------------- Slide 1 — title page (template layout untouched) ------ #
    s1 = slides[0]
    tb = body_box(s1)
    fill_textbox(
        tb,
        [
            dict(text="Problem Statement ID – SIH26120", sz=16, bold=True, bullet=True,
                 space_after=6),
            dict(text="Problem Statement Title- Digital Twin for Well-to-Surface "
                      "Optimization of Cyclic Steam Stimulation and Sucker Rod Pump "
                      "Operations", sz=16, bold=True, bullet=True, space_after=6),
            dict(text="Theme- Smart Automation", sz=16, bold=True, bullet=True,
                 space_after=6),
            dict(text="PS Category- Software", sz=16, bold=True, bullet=True,
                 space_after=6),
            dict(text="Team ID- TBD", sz=16, bold=True, bullet=True, space_after=6),
            dict(text="Team Name (Registered on portal)- TEAM ________", sz=16,
                 bold=True, bullet=True, space_after=6),
            dict(text="Organisation- Oil India Limited  |  Baghewala field, Rajasthan",
                 sz=16, bold=True, bullet=True, space_after=14),
            dict(text="“Physics + AI for India’s first cyclic-steam oilfield”",
                 sz=15, bold=True, italic=True, color=HEADING_COLOR),
        ],
    )

    # ---------------- Slide 2 — IDEA TITLE / Proposed Solution -------------- #
    s2 = slides[1]
    # kept short so the centred title clears the template's team-name oval
    # (ends x=1.73") on the left and the SIH banner (starts x=10.70") on the right
    set_title(
        s2,
        "Digital Twin for CSS and Sucker Rod Pump Optimization",
        size=22,
    )
    tb2 = body_box(s2)
    tb2.left, tb2.top, tb2.width, tb2.height = (
        Inches(0.55), Inches(1.30), Inches(12.30), Inches(1.10),
    )
    fill_textbox(
        tb2,
        [
            dict(text="Proposed Solution (Describe your Idea/Solution/Prototype)",
                 sz=20, bold=True, underline=True, color=HEADING_COLOR,
                 space_after=4),
            dict(text="A physics-driven AI twin of a Baghewala CSS well that tunes "
                      "steam cycle and sucker-rod pump together to drive Steam-Oil "
                      "Ratio down while keeping rod-floating risk safe.",
                 sz=15, indent=0.0),
        ],
    )

    cols2 = [
        ("Detailed explanation of the proposed solution", [
            "Digital twin of one CSS well, end to end",
            "Physics: Marx–Langenheim heating, Andrade μ(T), Vogel IPR",
            "Dynamics: rod load, pump efficiency, floating-risk index",
            "ML: XGBoost SOR predictor + risk classifier",
            "Bayesian optimizer returns steam volume, soak, cutoff, pump speed",
        ]),
        ("How it addresses the problem", [
            "Replaces manual cycle-by-cycle tuning",
            "Minimises SOR (heavy-oil CSS range 3–8 t/m³)",
            "Warns of rod floating before the pump fails",
            "Sub-second answers for a field 550–600 km from Jaipur",
            "One dashboard: predict, optimize, replay, alert",
        ]),
        ("Innovation and uniqueness of the solution", [
            "First twin to co-optimize CSS scheduling with SRP",
            "XSPOC, Lufkin, Weatherford, AVEVA, Kongsberg do one, not both",
            "Tuned to real Baghewala data: 1,150 m deep, 8,000–15,000 cP crude",
            "India’s first CSS well (BGW-8, Dec 2018) as the proving ground",
            "Fully open-source stack — no licence cost to Oil India",
        ]),
    ]
    for i, (head, bullets) in enumerate(cols2):
        box = clone_textbox(s2, tb2, 0.55 + i * 4.18, 2.60, 3.93, 4.20,
                            f"ColBox{i}")
        fill_textbox(
            box,
            [dict(text=head, sz=15.5, bold=True, underline=True,
                  color=HEADING_COLOR, space_after=8)]
            + [dict(text=b, sz=14, bullet=True, space_after=9) for b in bullets],
        )

    # ---------------- Slide 3 — TECHNICAL APPROACH (graphics) --------------- #
    s3 = slides[2]
    tb3 = body_box(s3)
    tb3.left, tb3.top, tb3.width, tb3.height = (
        Inches(0.55), Inches(1.24), Inches(12.30), Inches(0.84),
    )
    fill_textbox(
        tb3,
        [
            dict(text="Technologies to be used: Python 3.13 · NumPy / SciPy · "
                      "pandas · scikit-learn · XGBoost · scikit-optimize · "
                      "FastAPI · Plotly · pytest",
                 sz=14, bullet=True, space_after=4),
            dict(text="Methodology and process for implementation: physics engine → "
                      "3,000 synthetic CSS cycles (Latin-hypercube, seed 42) → ML "
                      "layer → Bayesian optimizer → dashboard → advisory set-points "
                      "to the operator (SCADA hook planned)",
                 sz=14, bullet=True),
        ],
    )
    # one full-bleed architecture picture (winner's lesson 3), height-fitted between
    # the pointer text (bottom 2.08") and the template's footer bar (top 6.95")
    _p = add_pic(s3, tech_png, 0.32, 2.16, 12.70, 4.64)
    _p.name = "TechArchitecture"

    # ---------------- Slide 4 — FEASIBILITY AND VIABILITY ------------------- #
    s4 = slides[3]
    tb4 = body_box(s4)
    tb4.left, tb4.top, tb4.width, tb4.height = (
        Inches(0.55), Inches(1.32), Inches(3.93), Inches(5.45),
    )
    cols4 = [
        ("Analysis of the feasibility of the idea", [
            "Physics is settled: Marx–Langenheim (1959), Andrade, Vogel (1968)",
            "Field parameters published: 1,150 m depth, 8,000–15,000 cP at 50 °C",
            "Steam at 280–305 °C and 60–70% quality — normal CSS practice",
            "De-risked at this very field: India’s first CSS, BGW-8, Dec 2018",
            "Open-source stack, laptop-scale compute, ~4 weeks to a live API",
        ]),
        ("Potential challenges and risks", [
            "No public Baghewala SOR history to train on",
            "Poor-to-fair reservoir: porosity below 10%",
            "Physics model can drift from real well behaviour",
            "Extreme viscosity makes pump behaviour non-linear",
            "Operator trust in an automated set-point",
        ]),
        ("Strategies for overcoming these challenges", [
            "Train on 3,000 physics-generated cycles, deterministic seed",
            "Recalibrate on Oil India historical data at the finale",
            "Parameter-sweep sanity tests on the physics modules",
            "field_params.json as the single source of truth per well",
            "Advisory mode first — the engineer approves every set-point",
        ]),
    ]
    for i, (head, bullets) in enumerate(cols4):
        box = tb4 if i == 0 else clone_textbox(
            s4, tb4, 0.55 + i * 4.18, 1.32, 3.93, 5.45, f"FeasCol{i}")
        if i > 0:
            box.left = Inches(0.55 + i * 4.18)
        fill_textbox(
            box,
            [dict(text=head, sz=18, bold=True, underline=True,
                  color=HEADING_COLOR, space_after=14)]
            + [dict(text=b, sz=16.5, bullet=True, space_after=14) for b in bullets],
        )

    # ---------------- Slide 5 — IMPACT AND BENEFITS ------------------------- #
    s5 = slides[4]
    tb5 = body_box(s5)
    tb5.left, tb5.top, tb5.width, tb5.height = (
        Inches(0.55), Inches(1.32), Inches(5.90), Inches(5.45),
    )
    fill_textbox(
        tb5,
        [
            dict(text="Potential impact on the target audience", sz=16.5, bold=True,
                 underline=True, color=HEADING_COLOR, space_after=10),
            dict(text="Oil India CSS operators at Baghewala — 52 wells drilled, "
                      "33 operational, 19 CSS’d in FY2025-26", sz=14.5, bullet=True,
                 space_after=10),
            dict(text="Every avoided rod-pump workover saves $15k–$50k "
                      "(industry-typical)", sz=14.5, bullet=True, space_after=10),
            dict(text="Output already scaling: 218 t (FY17) → 43,773 t (FY26) — "
                      "the twin scales with it", sz=14.5, bullet=True, space_after=20),
            dict(text="Benefits of the solution (social, economic, environmental, "
                      "etc.)", sz=16.5, bold=True, underline=True,
                 color=HEADING_COLOR, space_after=10),
            dict(text="Economic: less steam fuel burned per barrel produced",
                 sz=14.5, bullet=True, space_after=10),
            dict(text="Environmental: lower energy and GHG intensity per barrel",
                 sz=14.5, bullet=True, space_after=10),
            dict(text="Social / safety: rod-floating alerts catch the failure mode "
                      "behind most SRP workovers", sz=14.5, bullet=True,
                 space_after=10),
            dict(text="Strategic: an indigenous twin for India’s first cyclic-steam "
                      "asset, portable to future CSS wells", sz=14.5, bullet=True),
        ],
    )
    add_pic(s5, sor_png, 6.65, 1.65, 6.20, 3.60)
    cap = clone_textbox(s5, tb5, 6.65, 5.35, 6.20, 1.30, "SorCaption")
    fill_textbox(
        cap,
        [
            dict(text="Prototype v1 simulation — to be validated on OIL field data.",
                 sz=13, bold=True, italic=True, color=HEADING_COLOR, space_after=6),
            dict(text="SOR 1.50 → 0.88 t/m³ (−41.3%) across 3,000 synthetic cycles — "
                      "self-audited, physics v2 recalibration in progress; literature "
                      "benchmark for optimisation-driven SOR cuts is >20%.",
                 sz=13),
        ],
    )

    # ---------------- Slide 6 — RESEARCH AND REFERENCES --------------------- #
    s6 = slides[5]
    tb6 = body_box(s6)
    tb6.left, tb6.top, tb6.width, tb6.height = (
        Inches(0.55), Inches(1.35), Inches(12.30), Inches(5.45),
    )
    fill_textbox(
        tb6,
        [
            dict(text="Details / Links of the reference and research work", sz=18,
                 bold=True, underline=True, color=HEADING_COLOR, space_after=16),
            dict(text="Marx, J. W., & Langenheim, R. H. (1959). Reservoir heating by "
                      "hot fluid injection. Trans. AIME, 216, 312–315.",
                 sz=16.5, bullet=True, space_after=15),
            dict(text="Vogel, J. V. (1968). Inflow performance relationships for "
                      "solution-gas drive wells. J. Petrol. Tech., 20, 83–92.",
                 sz=16.5, bullet=True, space_after=15),
            dict(text="Gibbs, S. G. (1963). Predicting the behavior of sucker-rod "
                      "pumping systems. J. Petrol. Tech., 15, 769–778.",
                 sz=16.5, bullet=True, space_after=15),
            dict(text="Andrade, E. N. da C. (1930). The viscosity of liquids. Nature, "
                      "125, 309–310; ASTM D341 viscosity–temperature standard.",
                 sz=16.5, bullet=True, space_after=15),
            dict(text="SPE-23APOG-535203 (2023). Case study for enhancement of "
                      "production of heavy and highly viscous crude oil using an "
                      "electrical downhole heater — Baghewala depth, API and "
                      "viscosity data.",
                 sz=16.5, bullet=True, space_after=15),
            dict(text="Oil India Limited — Rajasthan Fields (Baghewala / BGW-8 CSS) "
                      "https://www.oil-india.com/rajasthan-fields ; production and "
                      "well-count figures from OIL annual reports.",
                 sz=16.5, bullet=True, space_after=15),
            dict(text="Competitive landscape (docs/research/landscape.md): XSPOC, Lufkin "
                      "SAM/SROD, Weatherford ForeSite, Schlumberger, AVEVA, Kongsberg "
                      "Kognitwin — none couples CSS scheduling with SRP optimization.",
                 sz=16.5, bullet=True),
        ],
    )

    # ---------------- delete the instructions slide (template says to) ------ #
    xml_slides = prs.slides._sldIdLst
    ids = list(xml_slides)
    rId = ids[6].get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    )
    prs.part.drop_rel(rId)
    xml_slides.remove(ids[6])

    prs.save(str(OUT_PPTX))
    print(f"saved {OUT_PPTX}  ({OUT_PPTX.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
