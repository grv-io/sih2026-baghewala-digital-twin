r"""Slide 3 (TECHNICAL APPROACH) -- the MEDIUM variant.

The SIMPLE slide's layout, icons, five stations and plain sentences (reused from
build_tech_slide_simple.py), plus 3 small "detail chips" under every sentence so a
technical judge also sees what is inside each station. The method name goes in
brackets where it helps. The chip facts come from the detailed slide
(build_tech_slide_native.py).

Three variants of slide 3 now exist:
    detailed  build_tech_slide_native.py  -> in the STRICT submission deck
    medium    build_tech_slide_medium.py  -> this file, separate preview
    simple    build_tech_slide_simple.py  -> separate preview

Output (a PREVIEW -- neither the STRICT deck nor the SIMPLE preview is touched):
    ppt/final/SIH26120_Slide3_MEDIUM_preview.pptx / .pdf   (1 slide)
    ppt/diagram/slide3_medium.png                          (1920 x 1080)

Gates: the native builder's five gates (band, furniture, overlap, wiring, text fit),
then the simple builder's rules, adjusted for this slide:
  * sentences, titles, captions and strip labels >= 11 pt; detail chips 9-10 pt;
  * <= 60 words in the five sentences, <= 15 detail chips (2-3 per station);
  * every detail chip is ONE rendered line with <= 5 words outside the brackets;
  * no acronym or code name in sentences; in chips, all-caps only inside brackets;
  * no orphan word; icons >= 0.7 in and clear of text; no wire across a foreign panel.
pypdf must then find every title, sentence, detail chip and strip label as text.

Run:
    .venv\Scripts\python.exe ppt\build_tech_slide_medium.py              # preview + PDF + PNG
    .venv\Scripts\python.exe ppt\build_tech_slide_medium.py --no-export  # gates + .pptx only
    .venv\Scripts\python.exe ppt\build_tech_slide_medium.py --into-strict
        # SWAP (not run by default): redraws slide 3 of the STRICT deck with this
        # variant, after backing the deck up to ppt/archive/.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PPT_DIR = ROOT / "ppt"
sys.path.insert(0, str(PPT_DIR))
import build_tech_slide_simple as S  # noqa: E402  (icons, stations, drawing, deck plumbing)
from build_tech_slide_simple import N, joined, words  # noqa: E402
from build_tech_slide_native import (  # noqa: E402
    Box, Para, Wire, C_IN, C_ML, C_TEXT, PANEL_FILL, TINT, SLIDE_IDX, inside, overlaps,
)

OUT = PPT_DIR / "final" / "SIH26120_Slide3_MEDIUM_preview.pptx"
OUT_PDF = OUT.with_suffix(".pdf")
PNG = PPT_DIR / "diagram" / "slide3_medium.png"
SWAP_BACKUP = PPT_DIR / "archive" / "SIH26120_Idea_Presentation_STRICT_pre-medium-slide3.pptx"
PREFIX = "TM_"

# --------------------------------------------------------------------------- #
# detail chips (one line each; the plain words first, the method in brackets) #
# --------------------------------------------------------------------------- #
DETAILS = [
    ("Baghewala: 1,150 m, 11,500 cP",
     "Oil India cycle records (CSV)",
     "Checked vs 9,692 real cycles"),
    ("Heat flow (Marx–Langenheim)",
     "Thick oil vs heat (Walther)",
     "Rod loads + rod-float index"),
    ("True-physics grid, 5 controls",
     "Fast what-if model (XGBoost)",
     "Best/worst case (Monte-Carlo)"),
    ("4 pages, works offline",
     "Computed pump card (dyno)",
     "Upload records → twin learns"),
    ("5 settings, incl. stop rule",
     "Review, confirm, then load",
     "Field view: which well next"),
]
DETAIL_PT = 9.5
CHIP_MAX_WORDS = 5          # words outside the brackets, per detail chip

# --------------------------------------------------------------------------- #
# layout                                                                       #
# --------------------------------------------------------------------------- #
X0, X1 = S.X0, S.X1
GAP = 0.44
CARD_W = (X1 - X0 - 4 * GAP) / 5
CARD_T = 2.20
HDR_H = 0.38
DISC_D = 0.94
ICON_D = 0.78
SENT_PT = 12.0
SENT_H = 0.62
CHIP_H, CHIP_GAP = 0.235, 0.05
DETAIL_H = 3 * CHIP_H + 2 * CHIP_GAP
CARD_H = HDR_H + 0.06 + DISC_D + 0.05 + SENT_H + 0.05 + DETAIL_H + 0.07

LOOP_Y = CARD_T + CARD_H + 0.20
CAP_PT = 11.0
STRIP_T = LOOP_Y + 0.33
STRIP_HDR = 0.27
STRIP_CHIP_H = 0.50
STRIP_H = STRIP_HDR + 0.05 + STRIP_CHIP_H + 0.06
STRIP_GAP = 0.40
STRIP_PT = 11.0
GETS_W = 7.24
LOOP_W = 3.95


def card_x(i):
    return X0 + i * (CARD_W + GAP)


def layout():
    N.BOXES.clear()
    N.WIRES.clear()
    N.DOTS.clear()
    S.PICS.clear()
    S.DISCS.clear()
    S.BIG.clear()
    for i, (key, col, title, sentence) in enumerate(S.STATIONS):
        x = card_x(i)
        pid = f"S{i + 1}"
        N.add(Box(pid, x, CARD_T, CARD_W, CARD_H, "panel", col, fill=PANEL_FILL[col],
                  line=col, line_w=1.5, radius=0.12))
        N.add(Box(pid + "_hdr", x, CARD_T, CARD_W, HDR_H, "header", col,
                  [Para(f"{i + 1} · {title}", 15.0, True, color="FFFFFF", align="ctr")],
                  fill=col, line=None, radius=0.12, anchor="ctr",
                  ins=(0.06, 0.0, 0.06, 0.0)))
        dy = CARD_T + HDR_H + 0.06
        dx = x + (CARD_W - DISC_D) / 2
        S.DISCS.append((pid + "_disc", col, dx, dy, DISC_D))
        S.PICS.append((pid + "_icon", key, col, dx + (DISC_D - ICON_D) / 2,
                       dy + (DISC_D - ICON_D) / 2, ICON_D, pid))
        sy = dy + DISC_D + 0.05
        N.add(Box(pid + "_txt", x + 0.08, sy, CARD_W - 0.16, SENT_H, "label", col,
                  [Para(t, SENT_PT, color=C_TEXT, align="ctr") for t in sentence],
                  fill=None, line=None, anchor="t", ins=(0.0, 0.0, 0.0, 0.0)))
        cy = sy + SENT_H + 0.05
        for k, text in enumerate(DETAILS[i]):
            N.add(Box(f"{pid}_d{k + 1}", x + 0.07, cy + k * (CHIP_H + CHIP_GAP),
                      CARD_W - 0.14, CHIP_H, "chip", col,
                      [Para(text, DETAIL_PT, color=C_TEXT)], fill=TINT[col], line=None,
                      panel=pid, anchor="ctr", radius=0.05,
                      ins=(0.06, 0.0, 0.04, 0.0)))
    # big arrows between the stations (level with the icon discs)
    ay = CARD_T + HDR_H + 0.06 + DISC_D / 2
    for i in range(4):
        w = Wire([(card_x(i) + CARD_W + 0.05, ay), (card_x(i + 1) - 0.05, ay)],
                 f"S{i + 1}", f"S{i + 2}")
        N.WIRES.append(w)
        S.BIG.append(w)
    # the return loop
    ox, tx = card_x(4) + CARD_W / 2, card_x(1) + CARD_W / 2
    bottom = CARD_T + CARD_H
    N.WIRES.append(Wire([(ox, bottom), (ox, LOOP_Y), (tx, LOOP_Y), (tx, bottom)], "S5", "S2",
                        kind="feedback"))
    lw = LOOP_W
    lx = (ox + tx) / 2 - lw / 2 + 0.2
    N.add(Box("loop_txt", lx, LOOP_Y + 0.05, lw, 0.22, "label", S.C_LOOP,
              [Para(S.LOOP_TEXT, CAP_PT, True, color=S.C_LOOP)],
              fill=None, line=None, anchor="ctr", ins=(0.0, 0.0, 0.0, 0.0)))
    S.PICS.append(("loop_icon", "loop", S.C_LOOP, lx - 0.34, LOOP_Y + 0.03, 0.28, None))
    # bottom strips
    widths = (GETS_W, X1 - X0 - STRIP_GAP - GETS_W)
    for gi, (gid, col, title, items) in enumerate(
            [("G", C_IN, S.GETS_TITLE, S.GETS), ("L", C_ML, S.LEADS_TITLE, S.LEADS)]):
        sw = widths[gi]
        gx = X0 if gi == 0 else X1 - sw
        N.add(Box(gid, gx, STRIP_T, sw, STRIP_H, "panel", col, fill=PANEL_FILL[col],
                  line=col, line_w=1.25, radius=0.10))
        N.add(Box(gid + "_hdr", gx, STRIP_T, sw, STRIP_HDR, "header", col,
                  [Para(title, 12.0, True, color="FFFFFF")],
                  fill=col, line=None, radius=0.10, anchor="ctr",
                  ins=(0.12, 0.0, 0.06, 0.0)))
        pad, cg = 0.10, 0.10
        cw = (sw - 2 * pad - 2 * cg) / 3
        cy = STRIP_T + STRIP_HDR + 0.05
        for ci, (ikey, text) in enumerate(items):
            cx = gx + pad + ci * (cw + cg)
            cid = f"{gid}{ci + 1}"
            N.add(Box(cid, cx, cy, cw, STRIP_CHIP_H, "chip", col,
                      [Para(t, STRIP_PT, True, color=C_TEXT) for t in text],
                      fill="FFFFFF", line=col, line_w=0.75, panel=gid, anchor="ctr",
                      radius=0.06, ins=(0.50, 0.01, 0.05, 0.01)))
            S.PICS.append((cid + "_icon", ikey, col, cx + 0.08,
                           cy + (STRIP_CHIP_H - 0.36) / 2, 0.36, cid))
    ly = STRIP_T + STRIP_HDR + 0.05 + STRIP_CHIP_H / 2
    w = Wire([(X0 + GETS_W + 0.05, ly), (X0 + GETS_W + STRIP_GAP - 0.05, ly)], "G", "L")
    N.WIRES.append(w)
    S.BIG.append(w)
    ty = STRIP_T + STRIP_H + 0.06
    N.add(Box("trust", X1 - 7.2, ty, 7.2, 0.22, "label", S.C_NOTE,
              [Para(S.TRUST, 11.0, italic=True, color=S.C_NOTE, align="r")],
              fill=None, line=None, anchor="ctr", ins=(0.0, 0.0, 0.0, 0.0)))


# --------------------------------------------------------------------------- #
# gates                                                                        #
# --------------------------------------------------------------------------- #
def is_detail(b):
    return re.fullmatch(r"S\d_d\d", b.id) is not None


def outside_brackets(t):
    return re.sub(r"\([^)]*\)", "", t)


def medium_gates(furniture):
    problems = []
    texts = [b for b in N.BOXES.values() if b.paras]
    details = [b for b in texts if is_detail(b)]
    # fonts
    for b in texts:
        for p in b.paras:
            lo, hi = (9.0, 10.0) if is_detail(b) else (11.0, 99.0)
            if not lo <= p.size <= hi:
                problems.append(f"[font] {b.id}: {p.size} pt outside {lo}-{hi}")
    for i in range(5):
        sz = N.BOXES[f"S{i + 1}_hdr"].paras[0].size
        if not 14.0 <= sz <= 16.0:
            problems.append(f"[font] station title S{i + 1} is {sz} pt (want 14-16)")
    # words / counts
    sentences = [joined(s) for *_, s in S.STATIONS]
    n_sent = sum(words(s) for s in sentences)
    if n_sent > 60:
        problems.append(f"[words] sentences are {n_sent} words (> 60)")
    for s in sentences:
        if words(s) > 12:
            problems.append(f"[words] sentence > 12 words: {s!r}")
    if len(details) > 15:
        problems.append(f"[chips] {len(details)} detail chips (> 15)")
    for i in range(5):
        n = sum(1 for b in details if b.id.startswith(f"S{i + 1}_"))
        if not 2 <= n <= 3:
            problems.append(f"[chips] station {i + 1} has {n} detail chips (want 2-3)")
    for b in details:
        t = b.paras[0].text
        if words(outside_brackets(t)) > CHIP_MAX_WORDS:
            problems.append(f"[chips] {b.id} has > {CHIP_MAX_WORDS} words outside "
                            f"brackets: {t!r}")
    # jargon: none in sentences / titles / captions; in chips only inside brackets
    for b in texts:
        for p in b.paras:
            t = outside_brackets(p.text) if is_detail(b) else p.text
            caps = re.findall(r"\b[A-Z]{2,}\b", t)
            code = "_" in t or ".py" in t or ("/" in t and not is_detail(b))
            if caps or code:
                problems.append(f"[jargon] {b.id}: {p.text!r}")
    # one line per hand-set line / chip; no lone words
    for b in texts:
        g = N.geom_inset(b)
        width_pt = (b.w - b.ins[0] - b.ins[2] - 2 * g) * 72 * N.FIT_SLACK
        for k, p in enumerate(b.paras):
            lines = N.wrap(p, width_pt) or []
            if (len(b.paras) > 1 or is_detail(b)) and len(lines) != 1:
                problems.append(f"[lines] {b.id}: {p.text!r} renders as {lines}")
            for j, ln in enumerate(lines):
                if len(b.paras) + len(lines) > 2 and len(ln.split()) < 2 and not (
                        k == 0 and j == 0 and ln.endswith(".")):
                    problems.append(f"[orphan] {b.id}: lone word {ln!r}")
    # icons, discs
    for pid, _key, _c, x, y, d, cont in S.PICS:
        if cont and cont.startswith("S") and d < 0.7:
            problems.append(f"[icon] {pid} is {d:.2f} in (< 0.7 in)")
    rects = [(p[0], (p[3], p[4], p[3] + p[5], p[4] + p[5]), p[6]) for p in S.PICS]
    rects += [(d[0], (d[2], d[3], d[2] + d[4], d[3] + d[4]), None) for d in S.DISCS]
    for rid, r, cont in rects:
        if r[0] < N.BAND[0] or r[1] < N.BAND[1] or r[2] > N.BAND[2] or r[3] > N.BAND[3]:
            problems.append(f"[canvas] {rid} outside band")
        for fname, fr in furniture.items():
            if overlaps(r, fr):
                problems.append(f"[furniture] {rid} overlaps {fname}")
        for b in texts:
            if cont and b.id == cont:
                if r[2] > b.x + b.ins[0] - 0.02 or not inside(r, b.r):
                    problems.append(f"[icon] {rid} intrudes on {b.id}'s text")
                continue
            if overlaps(r, b.r):
                problems.append(f"[icon] {rid} overlaps text box {b.id}")
    for i, (ia, ra, _) in enumerate(rects):
        for ib, rb, _ in rects[i + 1:]:
            if overlaps(ra, rb) and not (inside(ra, rb) or inside(rb, ra)):
                problems.append(f"[icon] {ia} overlaps {ib}")
    panels = [b for b in N.BOXES.values() if b.kind == "panel"]
    for w in N.WIRES:
        for p, q in zip(w.pts, w.pts[1:]):
            for pb in panels:
                if pb.id not in (w.src, w.dst) and N.seg_hits_rect(p, q, pb.r):
                    problems.append(f"[wiring] {w.src}->{w.dst} crosses panel {pb.id}")
    return problems, n_sent, len(details)


def pdf_check(pdf: Path, page: int):
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    raw = reader.pages[page].extract_text() or ""
    flat, tight = " ".join(raw.split()), "".join(raw.split())
    wanted = [f"{i + 1} · {t}" for i, (_k, _c, t, _s) in enumerate(S.STATIONS)]
    wanted += [joined(s) for *_, s in S.STATIONS]
    wanted += [t for chips in DETAILS for t in chips]
    wanted += [S.LOOP_TEXT, S.TRUST, S.GETS_TITLE, S.LEADS_TITLE]
    wanted += [joined(t) for _k, t in S.GETS + S.LEADS]
    found = [w for w in wanted if " ".join(w.split()) in flat or "".join(w.split()) in tight]
    return len(reader.pages), wanted, found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--into-strict", action="store_true",
                    help="replace slide 3 of the STRICT submission deck (not the default)")
    args = ap.parse_args()
    into = args.into_strict

    S.PREFIX = PREFIX            # draw() names every shape TM_*
    S.PNG = PNG                  # export_com() writes the slide PNG here
    prs, slide, furniture = S.open_slide3(keep_only=not into)
    layout()
    problems, fit_rows = N.run_gates(furniture)
    extra, n_sent, n_chips = medium_gates(furniture)
    problems += extra
    print("-- text fit (fullest 6) --")
    for fill, bid, detail in fit_rows[:6]:
        print(f"  {bid:<10} {fill * 100:5.1f}%  lines/para {detail}")
    if problems:
        print("\n!! GATES FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("GATES PASS: native gates (band, furniture, overlap, wiring, text fit) + medium "
          "gates (fonts, words, chip count/length, jargon, one-line chips, orphans, icons)")
    print(f"sentences {n_sent} words · detail chips {n_chips} "
          f"({sum(words(t) for c in DETAILS for t in c)} words) · loop caption "
          f"{words(S.LOOP_TEXT)} · trust line {words(S.TRUST)}")

    work = Path(tempfile.mkdtemp(prefix="tm_icons_"))
    try:
        S.draw(slide, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if into:
        if not SWAP_BACKUP.exists():
            shutil.copy2(S.STRICT, SWAP_BACKUP)
            print(f"backed up STRICT deck -> {SWAP_BACKUP.relative_to(ROOT)}")
        deck, pdf, slide_no, pages = S.STRICT, S.STRICT_PDF, SLIDE_IDX + 1, 6
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
