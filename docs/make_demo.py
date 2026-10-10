#!/usr/bin/env python3
"""Render the ShipPilot motion demo and the README flow graphic.

  docs/video/motion.html  ->  docs/assets/demo-<MEDIA_VERSION>.mp4 (30 fps), demo-<MEDIA_VERSION>.gif (800 px), poster.png
  flow_page() below       ->  docs/assets/flow-<MEDIA_VERSION>.png
Bump MEDIA_VERSION and the README image paths together when the media changes.

The motion demo is one HTML page whose CSS animations share a single timeline. Each frame is captured by pausing
every animation at time t (Web Animations API), so the output is deterministic and never drops frames.
It is an illustrative demo with sample numbers; store and platform screens are simplified re-drawings.

Requires: Python Playwright (`pip install playwright`) using the installed Google Chrome, ffmpeg.
Usage: python3 docs/make_demo.py [--fps 30] [--real-run-repo PATH_TO_APP_REPO [--only-real-run]]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
MOTION = ROOT / "docs" / "video" / "motion.html"
# MP4s are release assets, not repository files (directory rules hold non-image binaries); they are written here.
BUILD = ROOT / "build"
# Bump when the media changes: GitHub caches images by URL, so a new file name is what makes READMEs show it.
MEDIA_VERSION = "v3"
DEMO_MP4, DEMO_GIF, FLOW_PNG = (BUILD / f"demo-{MEDIA_VERSION}.mp4", ASSETS / f"demo-{MEDIA_VERSION}.gif",
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


SOCIAL_PNG = ASSETS / "social-v1.png"
ICON_PNG = ASSETS / "icon.png"


def icon_page() -> str:
    """512x512 plugin icon (directory listing)."""
    return """<!doctype html><html><head><style>* { margin: 0; } html, body { width: 512px; height: 512px; background: transparent; }
    .i { width: 512px; height: 512px; border-radius: 116px; background: linear-gradient(140deg, #0ea5e9, #2563eb 55%, #7c3aed);
      display: grid; grid-template-columns: 1fr 1fr; gap: 34px; padding: 84px; box-sizing: border-box; }
    .i span { background: #fff; border-radius: 30px; display: grid; place-items: center; font: 900 104px -apple-system, "Helvetica Neue", Arial, sans-serif; color: #4c1d95; }
    </style></head><body><div class="i"><span>S</span><span>H</span><span>I</span><span>P</span></div></body></html>"""


def social_page() -> str:
    """1280x640 repository social preview card."""
    return """<!doctype html><html><head><meta charset="utf-8"><style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { width: 1280px; height: 640px; overflow: hidden; font-family: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
      background: linear-gradient(150deg, #f7f9ff, #eef3ff 50%, #f3ecff); color: #0b1220; position: relative; }
    .blob { position: absolute; border-radius: 50%; filter: blur(70px); opacity: .6; }
    .logo { position: absolute; left: 80px; top: 78px; display: flex; align-items: center; gap: 22px; }
    .icon { width: 96px; height: 96px; border-radius: 24px; background: linear-gradient(140deg, #0ea5e9, #2563eb 55%, #7c3aed);
      display: grid; grid-template-columns: 1fr 1fr; gap: 7px; padding: 17px; box-shadow: 0 18px 40px rgba(37,99,235,.35); }
    .icon span { background: #fff; border-radius: 7px; display: grid; place-items: center; font-weight: 900; font-size: 22px; color: #4c1d95; }
    .name { font-size: 84px; font-weight: 900; letter-spacing: -2.5px; }
    .tag { position: absolute; left: 80px; top: 230px; font-size: 46px; font-weight: 800; letter-spacing: -1px; line-height: 1.12; width: 760px; }
    .tag em { font-style: normal; color: #2563eb; }
    .steps { position: absolute; left: 80px; top: 410px; display: flex; flex-wrap: wrap; gap: 12px; width: 760px; }
    .steps span { background: #fff; border-radius: 999px; padding: 10px 18px; font-size: 22px; font-weight: 700; box-shadow: 0 8px 20px rgba(30,41,80,.12); }
    .foot { position: absolute; left: 80px; bottom: 54px; font-size: 24px; font-weight: 700; color: #475569; }
    .phone { position: absolute; right: 120px; top: 70px; width: 250px; height: 500px; border-radius: 46px; background: #0b0b0f; padding: 11px;
      box-shadow: 0 30px 70px rgba(15,23,42,.35); transform: rotate(4deg); }
    .screen { width: 100%; height: 100%; border-radius: 36px; background: #fff; padding: 56px 18px; }
    .row { display: flex; gap: 12px; align-items: center; } .t { font-size: 20px; font-weight: 800; } .s { font-size: 13px; color: #64748b; font-weight: 600; }
    .get { display: inline-block; margin-top: 8px; background: #2563eb; color: #fff; font-weight: 800; border-radius: 999px; padding: 5px 18px; font-size: 14px; }
    .live { margin-top: 26px; display: flex; flex-direction: column; gap: 10px; }
    .live div { background: #dcfce7; color: #166534; font-weight: 800; border-radius: 12px; padding: 10px 12px; font-size: 15px; }
    </style></head><body>
    <div class="blob" style="width:520px;height:520px;left:-160px;top:-200px;background:#a5b4fc"></div>
    <div class="blob" style="width:520px;height:520px;right:-140px;bottom:-240px;background:#99f6e4"></div>
    <div class="logo"><div class="icon"><span>S</span><span>H</span><span>I</span><span>P</span></div><div class="name">ShipPilot</div></div>
    <div class="tag">Ship your mobile app, run the ads, <em>measure</em> and improve &mdash; inside Claude Code.</div>
    <div class="steps"><span>&#128221; Build</span><span>&#128640; CI &amp; release</span><span>&#128241; App Store + Google Play</span><span>&#128227; Campaigns</span><span>&#128202; Measure</span><span>&#8635; Improve</span></div>
    <div class="foot">Claude Code plugin &middot; MIT &middot; github.com/ufukyuksel-dev/shippilot</div>
    <div class="phone"><div class="screen">
      <div class="row"><div class="icon" style="width:58px;height:58px;border-radius:14px;padding:9px;gap:4px"><span style="font-size:12px;border-radius:4px">P</span><span style="font-size:12px;border-radius:4px">W</span><span style="font-size:12px;border-radius:4px">O</span><span style="font-size:12px;border-radius:4px">R</span></div>
        <div><div class="t">Your app</div><div class="s">Live on both stores</div><span class="get">GET</span></div></div>
      <div class="live"><div>&#10003; App Store &middot; v1.1</div><div>&#10003; Google Play &middot; v1.1</div><div style="background:#dbeafe;color:#1e40af">&#9201; re-measured</div></div>
    </div></div>
    </body></html>"""


def seek(page, ms: float) -> None:
    page.evaluate("t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", ms)


def capture(browser, load, fps: int, mp4: Path, gif: Path, poster: "tuple[float, Path] | None" = None) -> float:
    """Render an animated page frame by frame into an MP4 and an 800 px GIF; return the duration in seconds."""
    page = browser.new_page(viewport={"width": W, "height": H})
    load(page)
    page.wait_for_load_state("networkidle")
    duration = float(page.evaluate("document.documentElement.dataset.duration"))
    count = int(duration * fps)
    with tempfile.TemporaryDirectory() as tmp:
        frames = Path(tmp)
        for i in range(count):
            seek(page, i * 1000 / fps)
            page.screenshot(path=str(frames / f"f{i:05d}.png"))
        if poster:
            seek(page, poster[0] * 1000)
            page.screenshot(path=str(poster[1]))
        pattern = str(frames / "f%05d.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern, "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", str(mp4)],
                       check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern, "-vf",
                        "fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];"
                        "[b][p]paletteuse=dither=none:diff_mode=rectangle", str(gif)], check=True)
    page.close()
    return round(count / fps, 1)


# ---------------------------------------------------------------- real run (terminal, real commands, real output)
REAL_MP4, REAL_GIF = BUILD / "real-run-v1.mp4", ASSETS / "real-run-v1.gif"


def run(cmd: "list[str]", cwd: Path) -> "tuple[str, int]":
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    return (proc.stdout + proc.stderr).rstrip("\n"), proc.returncode


def real_run_steps(repo: Path, store_url: str) -> list:
    """Run the commands for real in the given app repository; return (shown command, output lines, exit code)."""
    scripts = ROOT / "scripts"
    steps = []
    for platform, meta in (("ios", "fastlane/metadata/ios"), ("android", "fastlane/metadata/android")):
        if not (repo / meta).is_dir():
            meta = "fastlane/metadata" if platform == "ios" else meta
        out, code = run([sys.executable, str(scripts / "check_metadata.py"), "--platform", platform, "--metadata", meta], repo)
        steps.append((f"python3 check_metadata.py --platform {platform} --metadata {meta}", out.splitlines(), code))
    out, code = run([sys.executable, str(scripts / "fetch_listing.py"), store_url], repo)
    # The seller field is a person's name for individual developers; keep it out of a public clip.
    lines = [re.sub(r'("seller": )".*?"', r'\1"(redacted in this clip)"', ln) for ln in out.splitlines()]
    shown = [ln if len(ln) <= 74 else ln[:73] + "…" for ln in lines[:14]]
    if len(lines) > 14:
        shown.append(f"… ({len(lines) - 14} more lines of JSON)")
    steps.append((f"python3 fetch_listing.py {store_url}", shown, code))
    return steps


def real_run_page(steps: list, label: str) -> str:
    import html as _html
    css = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { width: 1280px; height: 720px; overflow: hidden; background: linear-gradient(160deg,#f7f9ff,#eef3ff 45%,#f6f0ff);
      font-family: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif; }
    .top { position: absolute; top: 26px; left: 40px; right: 40px; display: flex; align-items: center; justify-content: space-between; }
    .h { font-size: 34px; font-weight: 800; color: #0b1220; letter-spacing: -.5px; }
    .badge { padding: 8px 16px; border-radius: 999px; background: #dcfce7; color: #166534; font-weight: 800; font-size: 19px; white-space: nowrap; }
    .term { position: absolute; top: 96px; left: 40px; right: 40px; bottom: 30px; background: #0d1117; border-radius: 18px;
      box-shadow: 0 30px 60px rgba(15,23,42,.3); padding: 22px 26px; overflow: hidden; font-family: Menlo, monospace; font-size: 17px; }
    .bar { display: flex; gap: 8px; margin-bottom: 14px; } .bar i { width: 13px; height: 13px; border-radius: 50%; }
    .ln { white-space: pre; line-height: 1.45; color: #c9d1d9; opacity: 0; }
    .cmd { color: #f0f6fc; font-weight: 700; } .cmd b { color: #7ee787; }
    .ok { color: #7ee787; } .bad { color: #ff7b72; } .dim { color: #8b949e; }
    .view { position: absolute; left: 26px; right: 26px; top: 56px; bottom: 20px; overflow: hidden; }
    .scroll { position: relative; }
    @keyframes show { from { opacity: 0; } to { opacity: 1; } }
    @keyframes type { from { clip-path: inset(0 100% 0 0); opacity: 1; } to { clip-path: inset(0 0 0 0); opacity: 1; } }
    @keyframes up { from { transform: translateY(0); } to { transform: translateY(var(--dy)); } }
    """
    t, rows, total_lines = 0.6, [], 0
    for cmd, out, code in steps:
        n = len(cmd) + 2
        dur = min(2.2, 0.035 * n)
        rows.append(f'<div class="ln cmd" style="animation:type {dur:.2f}s steps({n}) {t:.2f}s both"><b>$</b> {_html.escape(cmd)}</div>')
        t += dur + 0.35
        for line in out + [f"exit code {code}"]:
            cls = "ok" if line.startswith(("OK", "exit code 0")) else "bad" if line.startswith(("FAIL", "ERROR")) else "dim"
            rows.append(f'<div class="ln {cls}" style="animation:show .15s linear {t:.2f}s both">{_html.escape(line)}</div>')
            t += 0.12
        t += 1.4
        total_lines += len(out) + 2
    # scroll up once the output is taller than the terminal (26 px per line, ~21 lines visible)
    overflow = int(max(0, total_lines - 20) * 24.65)
    scroll_start = max(0.0, t - 4.0 - overflow / 120)
    duration = t + 2.5
    body = (f'<div class="top"><div class="h">Real run · {_html.escape(label)}</div><div class="badge">REAL OUTPUT · not a mock-up</div></div>'
            '<div class="term"><div class="bar"><i style="background:#ff5f56"></i><i style="background:#ffbd2e"></i><i style="background:#27c93f"></i></div>'
            f'<div class="view"><div class="scroll" style="--dy:-{overflow}px;animation:up {max(0.1, overflow / 120):.2f}s ease-in-out {scroll_start:.2f}s both">'
            + "".join(rows) + "</div></div></div>")
    return f'<!doctype html><html data-duration="{duration:.1f}"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the ShipPilot motion demo, flow graphic and real-run clip")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--real-run-repo", type=Path, help="app repository with fastlane/metadata (enables the real-run clip)")
    parser.add_argument("--real-run-store-url", default="https://apps.apple.com/us/app/id6761381016",
                        help="public store URL for fetch_listing.py in the real-run clip")
    parser.add_argument("--real-run-label", default="Wordfall (live app)")
    parser.add_argument("--only-real-run", action="store_true", help="skip the motion demo and the flow graphic")
    parser.add_argument("--only-stills", action="store_true", help="render only flow and social preview images")
    args = parser.parse_args()
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg not found", file=sys.stderr)
        return 2
    ASSETS.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    info = json.loads((ASSETS / "demo.json").read_text()) if (ASSETS / "demo.json").exists() else {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True, args=CHROME_ARGS)
        if args.only_stills:
            flow = browser.new_page(viewport={"width": 1200, "height": 620})
            flow.set_content(flow_page())
            flow.screenshot(path=str(FLOW_PNG))
            card = browser.new_page(viewport={"width": 1280, "height": 640})
            card.set_content(social_page())
            card.screenshot(path=str(SOCIAL_PNG))
            icon = browser.new_page(viewport={"width": 512, "height": 512})
            icon.set_content(icon_page())
            icon.screenshot(path=str(ICON_PNG), omit_background=True)
            print(f"OK: {FLOW_PNG.name}, {SOCIAL_PNG.name}, {ICON_PNG.name}")
        elif not args.only_real_run:
            info["seconds"] = capture(browser, lambda pg: pg.goto(MOTION.as_uri()), args.fps, DEMO_MP4, DEMO_GIF,
                                      (23.6, ASSETS / "poster.png"))  # both store pages on screen
            info["fps"] = args.fps
            flow = browser.new_page(viewport={"width": 1200, "height": 620})
            flow.set_content(flow_page())
            flow.screenshot(path=str(FLOW_PNG))
            card = browser.new_page(viewport={"width": 1280, "height": 640})
            card.set_content(social_page())
            card.screenshot(path=str(SOCIAL_PNG))
            print(f"OK: motion demo {info['seconds']}s -> {DEMO_MP4.name}, {DEMO_GIF.name}; {FLOW_PNG.name}")
        if args.real_run_repo:
            steps = real_run_steps(args.real_run_repo.expanduser().resolve(), args.real_run_store_url)
            page_html = real_run_page(steps, args.real_run_label)
            info["real_run_seconds"] = capture(browser, lambda pg: pg.set_content(page_html), args.fps, REAL_MP4, REAL_GIF)
            print(f"OK: real run {info['real_run_seconds']}s -> {REAL_MP4.name}, {REAL_GIF.name}")
        browser.close()
    (ASSETS / "demo.json").write_text(json.dumps(info) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
