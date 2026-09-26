r"""Slide 3 (TECHNICAL APPROACH) -- the FINAL version, the one in the submission deck.

Base: the MEDIUM variant (build_tech_slide_medium.py). The layout, icons, stations,
sentences, strips, trust line and every gate are reused unchanged. The team lead's edits
on top are listed below.
  * honesty -- the well's benchmark chip names the source instead of a cycle count;
  * thesis  -- the twin says what thick oil does (less flow AND stuck rods), which is
               the project's core insight, next to the heat-flow and pump-load chips;
  * search  -- physics grid / fast what-if model / best-worst case (1,500 runs);
  * operator -- "5 settings + when to stop";
  * loop caption -- "... the twin re-learns".
Two chips had to be trimmed to stay ONE line at 9.5 pt in a 2.2 in card (see
BUILD_NOTES): "Band check vs California data" (not "... real field data ...", 154 pt
of text in 136 pt) and "Physics grid: 53,000 runs" (not "... 5 controls, 53,000 runs",
153 pt). The "5 settings" chip under the operator still carries the five controls.

Outputs:
    ppt/final/SIH26120_Slide3_FINAL_preview.pptx / .pdf    (1-slide preview)
    ppt/diagram/slide3_final.png                           (1920 x 1080)
    --into-strict: slide 3 of ppt/final/SIH26120_Idea_Presentation_STRICT.pptx is
    redrawn with this version (shapes TF_*), the 6-page PDF is re-exported, and the
    PNG is re-rendered from the deck. The deck is first backed up to
    ppt/archive/SIH26120_Idea_Presentation_STRICT_pre-final-slide3.pptx.

Revert to the detailed slide: copy that backup over the STRICT .pptx and rerun
build_tech_slide_native.py for the PDF. Or just re-export the PDF through PowerPoint.

Run:
    .venv\Scripts\python.exe ppt\build_tech_slide_final.py                # preview
    .venv\Scripts\python.exe ppt\build_tech_slide_final.py --into-strict  # in the deck
"""

from __future__ import annotations

import sys
from pathlib import Path

PPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PPT_DIR))
import build_tech_slide_medium as M  # noqa: E402
import build_tech_slide_simple as S  # noqa: E402

M.DETAILS = [
    ("Baghewala: 1,150 m, 11,500 cP",
     "Oil India cycle records (CSV)",
     "Band check vs California data"),
    ("Heat flow (Marx–Langenheim)",
     "Thick oil: less flow + stuck rods",
     "Pump loads, rod-float risk"),
    ("Physics grid: 12,936 plans",
     "Fast what-if model (XGBoost)",
     "Best / worst case (1,500 runs)"),
    ("4 pages, works offline",
     "Computed pump card (dyno)",
     "Upload records → twin re-fits"),
    ("5 settings + an operating rule",
     "Review, confirm, then load",
     "Field view: which well next"),
]
M.CHIP_MAX_WORDS = 6      # the thesis chip "Thick oil: less flow + stuck rods" has 6
S.LOOP_TEXT = "Real cycle records come back → the twin re-learns"
_k, _c, _t, _ = S.STATIONS[2]
S.STATIONS[2] = (_k, _c, _t, ("Tries 13,000 plans", "in about 3 minutes,", "keeps the safe ones."))
S.TRUST = ("Built on published physics · benchmarked against a California steam-ratio band · "
           "263 automated tests")
S.GETS[2] = ("alert", ("Slow, then stop,", "before the rods jam"))
S.LEADS[2] = ("oil", ("Every plan", "with a range"))
S.LEADS[1] = ("shield", ("A stop rule", "for the rods"))
M.LOOP_W = 4.20

M.OUT = PPT_DIR / "final" / "SIH26120_Slide3_FINAL_preview.pptx"
M.OUT_PDF = M.OUT.with_suffix(".pdf")
M.PNG = PPT_DIR / "diagram" / "slide3_final.png"
M.SWAP_BACKUP = PPT_DIR / "archive" / "SIH26120_Idea_Presentation_STRICT_pre-final-slide3.pptx"
M.PREFIX = "TF_"

if __name__ == "__main__":
    M.main()
