r"""Screen-record the 3-minute website walkthrough (no audio) for the demo video.

Drives the dashboard served by a LOCAL API (`uvicorn api.main:app --port 8000`,
optimiser pre-run once so "Run optimiser" returns from cache) with Playwright
Chromium at 1920x1080 and records it. Actions are paced to the voice-over
script's timestamps (docs/VIDEO_SCRIPT.md):

    0:00 Overview      0:55 Simulator     1:40 Recommendation
    2:15 Model basis   2:45 Overview (close)   3:00 end

A fake cursor (a dot that follows the mouse) is injected so viewers can see
where the clicks happen -- headless recordings have no system cursor.

Run:
    .venv\Scripts\python.exe ppt\record_walkthrough.py
Output:
    ppt/final/SIH26120_walkthrough_screen.webm  (+ .mp4 when ffmpeg can encode H.264)
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8000"
OUT_DIR = ROOT / "ppt" / "final"
OUT_WEBM = OUT_DIR / "SIH26120_walkthrough_screen.webm"
OUT_MP4 = OUT_DIR / "SIH26120_walkthrough_screen.mp4"
TEMPLATE = ROOT / "data" / "templates" / "dyno_card_template.csv"

CURSOR_JS = """
(() => {
  const mk = () => {
    if (document.getElementById('__cur')) return;
    const d = document.createElement('div');
    d.id = '__cur';
    d.style.cssText = 'position:fixed;z-index:2147483647;width:22px;height:22px;border-radius:50%;' +
      'background:rgba(214,69,26,.55);border:2.5px solid #fff;box-shadow:0 0 0 2px rgba(0,0,0,.35);' +
      'pointer-events:none;transform:translate(-50%,-50%);left:-100px;top:-100px;transition:transform .08s';
    document.documentElement.appendChild(d);
    window.addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
    window.addEventListener('mousedown', () => { d.style.transform = 'translate(-50%,-50%) scale(.7)'; }, true);
    window.addEventListener('mouseup', () => { d.style.transform = 'translate(-50%,-50%) scale(1)'; }, true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mk); else mk();
})();
"""


class Clock:
    def __init__(self):
        self.t0 = time.time()

    def at(self, sec: float, page):
        """Wait until `sec` seconds after the recording started."""
        remaining = self.t0 + sec - time.time()
        if remaining > 0:
            page.wait_for_timeout(remaining * 1000)
        else:
            print(f"   (behind schedule by {-remaining:.1f}s at {sec}s)")


def smooth_to(page, selector: str, block: str = "start", offset: int = 0):
    page.evaluate(
        """([sel, block, off]) => { const el = document.querySelector(sel); if (!el) return;
             const y = el.getBoundingClientRect().top + window.scrollY - off;
             window.scrollTo({top: Math.max(0, y), behavior: 'smooth'}); }""",
        [selector, block, offset],
    )


def scroll_by(page, dy: int):
    page.evaluate("dy => window.scrollBy({top: dy, behavior: 'smooth'})", dy)


def hover(page, selector: str, steps: int = 25):
    el = page.locator(selector).first
    el.scroll_into_view_if_needed()
    box = el.bounding_box()
    if box:
        page.mouse.move(box["x"] + min(box["width"] / 2, 220), box["y"] + box["height"] / 2, steps=steps)


def click(page, selector: str):
    hover(page, selector)
    page.wait_for_timeout(250)
    page.locator(selector).first.click()


def set_range(page, selector: str, value):
    page.evaluate(
        """([sel, v]) => { const el = document.querySelector(sel); if (!el) return;
             el.value = v; el.dispatchEvent(new Event('input', {bubbles: true}));
             el.dispatchEvent(new Event('change', {bubbles: true})); }""",
        [selector, value],
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    template_rows = TEMPLATE.read_text(encoding="utf-8").strip()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=str(OUT_DIR / "_rec"),
            record_video_size={"width": 1920, "height": 1080},
            locale="en-IN",
        )
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        clk = Clock()

        # ---------------- 0:00 Overview ----------------
        page.goto(f"{BASE}/index.html?theme=light&lang=en", wait_until="networkidle")
        page.mouse.move(960, 540, steps=10)
        clk.at(3, page); page.mouse.move(700, 420, steps=30)
        clk.at(8, page); scroll_by(page, 420)          # KPI tiles -> comparison table
        clk.at(14, page); scroll_by(page, 420)         # table / fuel-cost-carbon
        clk.at(20, page); scroll_by(page, 380)
        clk.at(25, page); smooth_to(page, "#yourPrices", offset=120)
        clk.at(28, page); click(page, "#yourPrices > summary")
        clk.at(31, page); click(page, "#pxPresetFy26Floor")
        clk.at(36, page); click(page, "#pxReset")
        clk.at(39, page); smooth_to(page, "details:not(#yourPrices) > summary", offset=200)
        clk.at(41, page); click(page, "details:not(#yourPrices) > summary")
        clk.at(43, page); scroll_by(page, 300)
        clk.at(47, page); page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        clk.at(49, page); click(page, "#langHI")
        clk.at(53, page); click(page, "#langEN")

        # ---------------- 0:55 Simulator ----------------
        clk.at(55, page); page.goto(f"{BASE}/console.html", wait_until="networkidle")
        clk.at(57, page); hover(page, "#in_steam_t")
        clk.at(59, page); hover(page, "#in_spm")
        clk.at(61, page); set_range(page, "#in_spm", 4.5)
        clk.at(63, page); hover(page, "#in_floatPolicy")
        clk.at(64, page); page.select_option("#in_floatPolicy", "vfd_hold")
        clk.at(67, page); click(page, "#btnSimulate")
        clk.at(70, page); smooth_to(page, "#btnReplay2, #btnReplay", offset=160)
        clk.at(75, page)
        if page.locator("#btnReplay2").count():
            click(page, "#btnReplay2")
        else:
            click(page, "#btnReplay")
        clk.at(82, page); smooth_to(page, "#btnStress", offset=160)
        clk.at(84, page); click(page, "#btnStress")
        clk.at(89, page); smooth_to(page, "#dynoDetails", offset=520)   # computed dyno card above its details
        clk.at(93, page); smooth_to(page, "#dynoClfDetails", offset=140)
        clk.at(94, page); click(page, "#dynoClfDetails > summary")
        clk.at(95, page); page.fill("#dynoClfPaste", template_rows)
        clk.at(96.5, page); click(page, "#btnDynoClassify")
        clk.at(98, page); scroll_by(page, 200)

        # ---------------- 1:40 Recommendation ----------------
        clk.at(100, page); page.goto(f"{BASE}/optimizer.html", wait_until="networkidle")
        clk.at(102, page); click(page, "#btnOptimize")
        clk.at(108, page); scroll_by(page, 360)          # recommendation table
        clk.at(114, page); scroll_by(page, 420)          # constraint report
        clk.at(119, page); scroll_by(page, 420)          # uncertainty and model quality
        clk.at(124, page); smooth_to(page, "#baselinePolicyToggle", offset=140)
        clk.at(126, page)
        if page.locator("#baselinePolicyToggle input").count() > 1:
            click(page, "#baselinePolicyToggle input >> nth=1")
            clk.at(128, page); click(page, "#baselinePolicyToggle input >> nth=0")
        clk.at(129.5, page); smooth_to(page, "#btnStage", offset=300)
        clk.at(130.5, page); click(page, "#btnStage")
        clk.at(133, page); click(page, "#btnCancel")
        clk.at(134, page); page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")

        # ---------------- 2:15 Model basis ----------------
        clk.at(135, page); page.goto(f"{BASE}/methodology.html", wait_until="networkidle")
        clk.at(137, page); smooth_to(page, "#scope", offset=100)
        clk.at(142, page); smooth_to(page, "#validation", offset=100)
        clk.at(146, page); scroll_by(page, 380)
        clk.at(150, page); smooth_to(page, "#calib", offset=100)
        clk.at(154, page); scroll_by(page, 500)
        clk.at(158, page); smooth_to(page, "#field", offset=100)
        clk.at(162, page); scroll_by(page, 380)

        # ---------------- 2:45 Close on Overview ----------------
        clk.at(165, page); page.goto(f"{BASE}/index.html", wait_until="networkidle")
        clk.at(167, page); page.mouse.move(960, 500, steps=30)
        clk.at(180, page)

        video = page.video
        page.close()
        ctx.close()
        browser.close()
        src = Path(video.path())
        shutil.move(str(src), OUT_WEBM)
        shutil.rmtree(OUT_DIR / "_rec", ignore_errors=True)
        print(f"wrote {OUT_WEBM.relative_to(ROOT)} ({OUT_WEBM.stat().st_size / 1e6:.1f} MB), "
              f"{time.time() - clk.t0:.0f}s of recording")

    # Optional H.264 MP4 for editors that reject WebM (Playwright ships an ffmpeg).
    ff = next((Path.home() / "AppData/Local/ms-playwright").glob("ffmpeg-*/ffmpeg-win64.exe"), None)
    if ff:
        r = subprocess.run([str(ff), "-y", "-i", str(OUT_WEBM), "-c:v", "libx264", "-preset", "medium",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT_MP4)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(f"wrote {OUT_MP4.relative_to(ROOT)} ({OUT_MP4.stat().st_size / 1e6:.1f} MB)")
        else:
            print("mp4 conversion not available with the bundled ffmpeg (WebM is fine for CapCut/Premiere/Clipchamp):",
                  r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "")


if __name__ == "__main__":
    main()
