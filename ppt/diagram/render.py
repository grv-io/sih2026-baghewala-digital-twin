r"""Render ppt/diagram/tech_architecture.html -> tech_architecture.png at 2x
(3960x1560) via headless Edge, plus a 1980x780 downscale legibility check
(tech_architecture_check.png) and a 50%-zoom check (990x390).

Run:  .venv\Scripts\python.exe ppt\diagram\render.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
HTML = HERE / "tech_architecture.html"
PNG = HERE / "tech_architecture.png"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

W, H = 1980, 780


def main() -> None:
    if PNG.exists():
        PNG.unlink()
    subprocess.run(
        [
            EDGE,
            "--headless=new",
            "--disable-gpu",
            "--force-device-scale-factor=2",
            "--hide-scrollbars",
            "--default-background-color=FFFFFFFF",
            f"--screenshot={PNG}",
            f"--window-size={W},{H}",
            f"file:///{HTML.as_posix()}",
        ],
        check=False,
        capture_output=True,
    )
    if not PNG.exists():
        sys.exit("Edge failed to render")
    im = Image.open(PNG).convert("RGB")
    print("rendered", PNG.name, im.size)

    im.resize((W, H), Image.LANCZOS).save(HERE / "tech_architecture_check.png")
    im.resize((W // 2, H // 2), Image.LANCZOS).save(HERE / "tech_architecture_zoom50.png")
    print(f"wrote {W}x{H} and {W//2}x{H//2} legibility checks")

    # programmatic overflow assertion (the page stamps body[data-overflow])
    dom = subprocess.run(
        [
            EDGE,
            "--headless=new",
            "--disable-gpu",
            "--dump-dom",
            "--virtual-time-budget=3000",
            f"--window-size={W},{H}",
            f"file:///{HTML.as_posix()}",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout
    marker = 'data-overflow="'
    if marker in dom:
        val = dom.split(marker, 1)[1].split('"', 1)[0]
        print("OVERFLOW CHECK:", val)
        if val != "NONE":
            sys.exit("!! text overflows a box — fix before shipping")
    else:
        print("OVERFLOW CHECK: (marker not found)")


if __name__ == "__main__":
    main()
