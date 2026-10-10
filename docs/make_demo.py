#!/usr/bin/env python3
"""Render the ShipPilot motion demo and the README flow graphic.

  docs/video/motion.html  ->  docs/assets/demo-<MEDIA_VERSION>.mp4 (30 fps), demo-<MEDIA_VERSION>.gif (800 px), poster.png
  flow_page() below       ->  docs/assets/flow-<MEDIA_VERSION>.png
Bump MEDIA_VERSION and the README image paths together when the media changes.

The motion demo is one HTML page whose CSS animations share a single timeline. Each frame is captured by pausing
every animation at time t (Web Animations API), so the output is deterministic and never drops frames.
It is an illustrative demo with sample numbers; store and platform screens are simplified re-drawings.

Requires: Python Playwright (`pip install playwright`) using the installed Google Chrome, ffmpeg.
Usage: python3 docs/make_demo.py [--fps 30]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
MOTION = ROOT / "docs" / "video" / "motion.html"
# Bump when the media changes: GitHub caches images by URL, so a new file name is what makes READMEs show it.
MEDIA_VERSION = "v3"
DEMO_MP4, DEMO_GIF, FLOW_PNG = (ASSETS / f"demo-{MEDIA_VERSION}.mp4", ASSETS / f"demo-{MEDIA_VERSION}.gif",
                                ASSETS / f"flow-{MEDIA_VERSION}.png")
W, H = 1280, 720
# Chrome's own sandbox cannot start inside some sandboxed runners; only local files from this repo are rendered.
CHROME_ARGS = ["--no-sandbox"]

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: 1200px; height: 620px; overflow: hidden; color: #e8edf6; background: radial-gradient(1200px 700px at 80% -10%, #16213a, #0a0e18);
  font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif; }
.mono { font-family: Menlo, "DejaVu Sans Mono", monospace; }
"""


def page(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


FLOW = [
    ("Build", "A reviewed code change", "Claude Code · /shippilot:launch-check", False),
    ("Test &amp; release", "CI tests + store checks, beta to TestFlight / Play internal", "/shippilot:check-metadata · /shippilot:beta", True),
    ("Store &amp; creatives", "Store text per language within limits, 3 ad angles", "/shippilot:localize · /shippilot:ad-creatives", False),
    ("Campaigns", "Spend, installs and CPI per campaign; changes previewed first", "/shippilot:ads-report", True),
    ("Measure", "Campaign &rarr; onboarding &rarr; day-1 return, same cohort", "/shippilot:grow", False),
    ("Improve", "One hypothesis, one change, a decision rule", "/shippilot:grow", True),
]


def flow_page() -> str:
    """Static README graphic: the six stages, what each produces, and where you approve."""
    xs, ys, cw, ch = (40, 430, 820), (44, 344), 340, 250
    cards = []
    for i, (name, output, cmd, gate) in enumerate(FLOW):
        x, y = xs[i % 3], ys[i // 3]
        lock = '<div class="lock">&#128274; you approve</div>' if gate else ""
        cards.append(f'<div class="fc" style="left:{x}px;top:{y}px;width:{cw}px;height:{ch}px">'
                     f'<div class="fn"><span>{i + 1}</span>{name}</div><div class="fo">{output}</div>'
                     f'<div class="ff">{lock}<div class="fx mono">{cmd}</div></div></div>')
    arrows = (
        '<svg width="1200" height="620" style="position:absolute;inset:0"><defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#38bdf8"/></marker>'
        '<marker id="g" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#22c55e"/></marker></defs>'
        '<g stroke="#38bdf8" stroke-width="4" fill="none" marker-end="url(#a)">'
        '<line x1="382" y1="169" x2="426" y2="169"/><line x1="772" y1="169" x2="816" y2="169"/>'
        '<path d="M990,296 L990,320 L210,320 L210,340"/>'
        '<line x1="382" y1="469" x2="426" y2="469"/><line x1="772" y1="469" x2="816" y2="469"/></g>'
        '<path d="M1162,469 L1185,469 L1185,22 L210,22 L210,40" stroke="#22c55e" stroke-width="4" stroke-dasharray="10 8" '
        'fill="none" marker-end="url(#g)"/><text x="1176" y="16" text-anchor="end" fill="#4ade80" font-size="17" font-weight="700" '
        'font-family="Avenir Next, Helvetica Neue, sans-serif">re-measure &#8594; next loop</text></svg>')
    css = (".fc { position:absolute; background:#111a2c; border:2px solid #24314d; border-radius:20px; padding:18px 22px; display:flex; flex-direction:column; }"
           ".fn { font-size:27px; font-weight:800; display:flex; align-items:center; gap:12px; white-space:nowrap; }"
           ".fn span { width:38px; height:38px; border-radius:50%; background:#38bdf8; color:#06121f; display:grid; place-items:center; font-size:22px; }"
           ".fo { font-size:22px; color:#dbe4f3; margin-top:12px; line-height:1.3; }"
           ".ff { margin-top:auto; } .fx { font-size:15px; color:#7dd3fc; line-height:1.35; }"
           ".lock { display:inline-block; font-size:16px; font-weight:800; color:#fcd34d; border:1px solid #f59e0b; border-radius:8px; padding:2px 8px; margin-bottom:8px; }"
           )
    return page(f"<style>{css}</style>{arrows}{''.join(cards)}")


def seek(page, ms: float) -> None:
    page.evaluate("t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", ms)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the ShipPilot motion demo and flow graphic")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg not found", file=sys.stderr)
        return 2
    ASSETS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        frames = Path(tmp)
        browser = pw.chromium.launch(channel="chrome", headless=True, args=CHROME_ARGS)
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(MOTION.as_uri())
        page.wait_for_load_state("networkidle")
        duration = float(page.evaluate("document.documentElement.dataset.duration"))
        count = int(duration * args.fps)
        for i in range(count):
            seek(page, i * 1000 / args.fps)
            page.screenshot(path=str(frames / f"f{i:05d}.png"))
        seek(page, 23_600)  # both store pages on screen
        page.screenshot(path=str(ASSETS / "poster.png"))

        flow = browser.new_page(viewport={"width": 1200, "height": 620})
        flow.set_content(flow_page())
        flow.screenshot(path=str(FLOW_PNG))
        browser.close()

        pattern = str(frames / "f%05d.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(args.fps), "-i", pattern, "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-movflags", "+faststart",
                        str(DEMO_MP4)], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(args.fps), "-i", pattern, "-vf",
                        "fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];"
                        "[b][p]paletteuse=dither=none:diff_mode=rectangle", str(DEMO_GIF)], check=True)
    seconds = round(count / args.fps, 1)
    (ASSETS / "demo.json").write_text(json.dumps({"seconds": seconds, "frames": count, "fps": args.fps}) + "\n")
    print(f"OK: {count} frames, {seconds}s -> {DEMO_MP4.name}, {DEMO_GIF.name}, poster.png, {FLOW_PNG.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
