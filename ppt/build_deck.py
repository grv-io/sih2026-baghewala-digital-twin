"""
Builds ppt/archive/SIH26120_Idea_Presentation.pptx from the OFFICIAL SIH 2026 Idea
Presentation template (ppt/template/template_official.pptx), filling in the content
from ppt/notes/deck_content.md (trimmed to fit the template's text boxes).

Run with the Python 3.13 interpreter that has python-pptx / matplotlib:
  "C:\\Users\\Gaurav Agrawal\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" build_deck.py
"""
import os
from copy import deepcopy

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE, "template", "template_official.pptx")
OUT_PATH = os.path.join(BASE, "archive", "SIH26120_Idea_Presentation.pptx")
CHART_PNG = os.path.join(BASE, "assets", "sor_chart.png")

A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

TEAM_NAME = "TEAM ________"


# --------------------------------------------------------------------------
# Paragraph-filling helper: reuses the template's own paragraph/run XML
# (so font, size, bold, bullet formatting are preserved) and clones it as
# many times as needed to fit the number of bullets we want to insert.
# --------------------------------------------------------------------------
def normalize_single_run(paragraph):
    runs = paragraph.runs
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def set_paragraph_texts(text_frame, texts, start_index=0, template_index=None):
    paragraphs = text_frame.paragraphs
    if template_index is None:
        template_index = start_index
    template_p_elm = deepcopy(paragraphs[template_index]._p)
    txBody = text_frame._txBody

    existing = paragraphs[start_index:]
    for p in existing:
        normalize_single_run(p)

    n_existing = len(existing)
    n_needed = len(texts)

    for i in range(min(n_existing, n_needed)):
        p = existing[i]
        if len(p.runs) == 0:
            template_run_r = deepcopy(template_p_elm.findall(f".//{A_NS}r")[0])
            p._p.append(template_run_r)
        p.runs[0].text = texts[i]

    last_p_elm = existing[-1]._p if existing else template_p_elm
    for i in range(n_existing, n_needed):
        new_p_elm = deepcopy(template_p_elm)
        runs = new_p_elm.findall(f".//{A_NS}r")
        if runs:
            for extra in runs[1:]:
                extra.getparent().remove(extra)
            t_elm = runs[0].find(f"{A_NS}t")
            if t_elm is None:
                t_elm = runs[0].makeelement(f"{A_NS}t", {})
                runs[0].append(t_elm)
            t_elm.text = texts[i]
        last_p_elm.addnext(new_p_elm)
        last_p_elm = new_p_elm

    if n_existing > n_needed:
        for p in existing[n_needed:]:
            p._p.getparent().remove(p._p)


def set_team_name_oval(slide):
    for sh in slide.shapes:
        if sh.name.startswith("Oval") and sh.has_text_frame:
            if sh.text_frame.text.strip().lower().startswith("your team name"):
                # keep formatting of first run, replace text
                tf = sh.text_frame
                normalize_single_run(tf.paragraphs[0])
                if tf.paragraphs[0].runs:
                    tf.paragraphs[0].runs[0].text = TEAM_NAME
                else:
                    tf.text = TEAM_NAME


def set_title_text(text_frame, text):
    """Set the visible text of a title placeholder to a single line, removing
    any existing <a:br/> line breaks and extra runs (the official template's
    'IDEA TITLE' placeholder is an empty run + <a:br/> + a second run)."""
    p_elm = text_frame.paragraphs[0]._p
    runs = p_elm.findall(f"{A_NS}r")
    for br in p_elm.findall(f"{A_NS}br"):
        p_elm.remove(br)
    if not runs:
        return
    first_run = runs[0]
    for r in runs[1:]:
        r.getparent().remove(r)
    t_elm = first_run.find(f"{A_NS}t")
    if t_elm is None:
        t_elm = first_run.makeelement(f"{A_NS}t", {})
        first_run.append(t_elm)
    t_elm.text = text


def shrink_font(text_frame, size):
    for para in text_frame.paragraphs:
        for run in para.runs:
            run.font.size = size


def get_shape(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    return None


def main():
    prs = Presentation(TEMPLATE_PATH)
    slides = prs.slides

    # ---------------- Slide 0: Title page ----------------
    s0 = slides[0]
    title_info_box = get_shape(s0, "TextBox 9")
    set_paragraph_texts(
        title_info_box.text_frame,
        [
            "Problem Statement ID - SIH26120",
            "Problem Statement Title - Digital Twin for Well-to-Surface Optimization "
            "of Cyclic Steam Stimulation and Sucker Rod Pump Operations",
            "Theme - Smart Automation",
            "PS Category - Software",
            "Team ID - TBD (fill after SIH portal team registration)",
            f"Team Name (Registered on portal) - {TEAM_NAME}",
        ],
        start_index=1,
        template_index=1,
    )

    # ---------------- Slide 1: Idea Title / Proposed Solution ----------------
    s1 = slides[1]
    set_title_text(
        get_shape(s1, "Title 1").text_frame,
        "Physics-Driven AI Optimizer for CSS & Sucker-Rod Pump Operations",
    )
    box1 = get_shape(s1, "TextBox 8")
    set_paragraph_texts(
        box1.text_frame,
        [
            "Problem: high Steam-Oil Ratio (industry CSS range 3-8, avg ~6), manual tuning, rod-floating",
            "Digital twin fuses reservoir heating, viscosity, pump dynamics & inflow performance",
            "Outputs real-time optimal steam volume, soak time, cutoff rate & pump speed",
            "No commercial product (XSPOC, Lufkin, Weatherford, SLB) couples CSS + SRP like this",
            "Killer number: targets SOR <3.5 t/m3 (20-30% cut vs literature CSS benchmark)",
        ],
        start_index=1,       # keep the bold/underlined "Proposed Solution (...)" header at index 0
        template_index=3,    # a plain-formatted bullet paragraph to clone from
    )
    # Five bullets at the template's default 28pt leave almost no margin above
    # the footer on this full-width box (measured against the footer boundary)
    # -- drop to 26pt for a safe margin (header paragraph included, harmless).
    shrink_font(box1.text_frame, Pt(26))
    set_team_name_oval(s1)

    # ---------------- Slide 2: Technical Approach ----------------
    s2 = slides[2]
    box2 = get_shape(s2, "TextBox 8")
    set_paragraph_texts(
        box2.text_frame,
        [
            "Physics: Marx-Langenheim heating, Andrade viscosity law, Vogel inflow curve",
            "Dynamics: sucker-rod load, pump efficiency, floating-risk index (unsafe > 0.6)",
            "Simulation: 3000+ synthetic CSS cycles via Latin-hypercube sampling (seed=42)",
            "ML: XGBoost SOR predictor + floating-risk classifier + Bayesian optimizer",
            "Stack: Python 3.12, NumPy/SciPy/XGBoost/scikit-optimize, FastAPI backend",
        ],
        start_index=0,
        template_index=0,
    )
    # Narrow the text column (left half of the slide) so the architecture
    # diagram can sit in a clear right-hand column with no overlap risk,
    # and drop the font a touch so 5 bullets comfortably fit above the footer.
    box2.width = Emu(6400800)  # ~7.0in
    shrink_font(box2.text_frame, Pt(22))
    set_team_name_oval(s2)
    add_architecture_diagram(s2)

    # ---------------- Slide 3: Feasibility & Viability ----------------
    s3 = slides[3]
    box3 = get_shape(s3, "TextBox 8")
    set_paragraph_texts(
        box3.text_frame,
        [
            "Physics validated: Marx-Langenheim, Andrade (ASTM D341), Vogel IPR models",
            "Params from Oil India/SPE data (depth ~1150 m, 8-15k cP, <10% porosity)",
            "Proven at Baghewala: India's first CSS (BGW-8, 2018) - 5-6x uplift",
            "Scale: 52 wells drilled, 33 operational, 19 CSS'd in FY25-26 (+72% YoY)",
            "Killer number: ~1,150 m confirmed depth (SPE-23APOG / Oil India)",
        ],
        start_index=0,
        template_index=0,
    )
    # Five longer, fact-dense bullets no longer fit at the template's default
    # 28pt on this box (measured against the footer boundary) -- shrink to 24pt,
    # matching the readability floor used on the other narrowed content slides.
    shrink_font(box3.text_frame, Pt(24))
    set_team_name_oval(s3)

    # ---------------- Slide 4: Impact & Benefits ----------------
    s4 = slides[4]
    box4 = get_shape(s4, "TextBox 8")
    set_paragraph_texts(
        box4.text_frame,
        [
            "Economics: $15k-$50k saved per avoided rod-workover (industry-typical)",
            "Safety: alerts target the #1 SRP failure mode (rod/tubing wear)",
            "Growth: Baghewala output up ~200x since CSS began (218t -> 43,773t)",
            "Scale: 52 wells drilled, 33 operational, 19 CSS'd in FY25-26 (+72% YoY)",
            "Killer number: 20-30% SOR cut (physics-simulated; field validation next)",
        ],
        start_index=0,
        template_index=0,
    )
    box4.width = Emu(6400800)  # ~7.0in — leaves a clear right column for the chart
    shrink_font(box4.text_frame, Pt(22))
    set_team_name_oval(s4)
    add_impact_chart(s4)

    # ---------------- Slide 5: Research & References ----------------
    s5 = slides[5]
    box5 = get_shape(s5, "TextBox 8")
    set_paragraph_texts(
        box5.text_frame,
        [
            "Marx & Langenheim (1959), Reservoir Heating by Hot Fluid Injection, Trans. AIME",
            "Andrade (1934), Viscosity of Liquids, Nature; ASTM D341 viscosity-temp standard",
            "Vogel, J.V. (1968), Inflow Performance Relationships, J. Petrol. Tech., 20",
            "SPE-23APOG-535203 (2023) - Baghewala reservoir/fluid data (depth, API, viscosity)",
            "Oil India internal data (BGW-8 CSS cycle) + landscape.md competitive-gap check",
        ],
        start_index=0,
        template_index=0,
    )
    # Five full citation lines overflow the template's default 28pt on this box
    # (measured against the footer boundary) -- shrink to 22pt to fit cleanly.
    shrink_font(box5.text_frame, Pt(22))
    set_team_name_oval(s5)

    # ---------------- Remove the template's own "IMPORTANT INSTRUCTIONS" slide ----------------
    # The template explicitly says: "You can delete this slide (Important Pointers)
    # when you upload the details of your idea on SIH portal." This keeps us at the
    # required max of 6 slides (title + 5 content slides).
    delete_slide(prs, len(prs.slides) - 1)

    prs.save(OUT_PATH)
    print("Saved:", OUT_PATH)


def add_architecture_diagram(slide):
    """Simple 4-layer flow diagram (physics engine -> synthetic data -> ML
    models -> Bayesian optimizer, feedback loop) drawn with native pptx
    shapes since docs/architecture.svg was not available at build time.
    Laid out as a vertical stack in the right-hand column (the bullet text
    box was narrowed to the left ~7in) so it cannot overlap the bullets
    regardless of how many lines the text wraps to."""
    labels = ["Physics Engine\n(Marx-Langenheim, Andrade, Vogel)",
              "Synthetic Data\n(3000+ CSS cycles)",
              "ML Models\n(XGBoost SOR + risk classifier)",
              "Bayesian Optimizer"]
    fills = [RGBColor(0x2E, 0x4A, 0x62), RGBColor(0x3B, 0x66, 0x4D),
             RGBColor(0x6B, 0x4A, 0x2E), RGBColor(0x5A, 0x3B, 0x66)]

    col_left = Emu(7590790)   # ~8.3in — right column, clear of the narrowed text box
    box_w, box_h = Emu(3931920), Emu(548640)  # ~4.3in x 0.6in
    gap = Emu(109728)  # ~0.12in
    top0 = Emu(2533653)  # matches the bullet box's top

    shapes = slide.shapes
    for i, (label, fill) in enumerate(zip(labels, fills)):
        top = Emu(int(top0 + i * (box_h + gap)))
        box = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, col_left, top, box_w, box_h)
        box.fill.solid()
        box.fill.fore_color.rgb = fill
        box.line.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        box.line.width = Pt(1)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_top = Emu(18288)
        tf.margin_bottom = Emu(18288)
        tf.text = label
        for para in tf.paragraphs:
            para.alignment = PP_ALIGN.CENTER
            for run in para.runs:
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.bold = True
        if i < 3:
            ay = Emu(int(top + box_h))
            arrow = shapes.add_shape(MSO_SHAPE.DOWN_ARROW,
                                      Emu(int(col_left + box_w / 2 - Emu(91440))), ay,
                                      Emu(182880), gap)
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RGBColor(0x99, 0x99, 0x99)
            arrow.line.fill.background()

    bottom = Emu(int(top0 + 4 * box_h + 3 * gap))
    fb = shapes.add_textbox(col_left, Emu(int(bottom + Emu(45720))), box_w, Emu(365760))
    fb.text_frame.word_wrap = True
    fb.text_frame.text = "Feedback loop: optimizer output refines the next simulated CSS cycle"
    p = fb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(11)
    p.runs[0].font.italic = True
    p.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def add_impact_chart(slide):
    if not os.path.exists(CHART_PNG):
        return
    # Right-hand column, clear of the narrowed (~7in) bullet text box.
    left = Emu(7590790)   # ~8.3in
    top = Emu(2533653)    # matches the bullet box's top
    width = Emu(3931920)  # ~4.3in
    slide.shapes.add_picture(CHART_PNG, left, top, width=width)


def delete_slide(prs, index):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    rId = slides[index].rId
    prs.part.drop_rel(rId)
    xml_slides.remove(slides[index])


if __name__ == "__main__":
    main()
