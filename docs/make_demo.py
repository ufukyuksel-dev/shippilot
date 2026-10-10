#!/usr/bin/env python3
"""Render the ShipPilot walkthrough video (docs/assets/demo.mp4, demo.gif, poster.png) and the README flow graphic (flow.png).

One fictional app ("Pocket Words") goes through the six stages. Scenes are HTML/CSS pages rendered with headless
Chrome, joined with crossfades (Pillow) and encoded with ffmpeg. Every scene carries a badge:
  REAL OUTPUT        produced while this script runs (scripts/check_metadata.py on examples/)
  ILLUSTRATIVE       a representative screen; numbers are sample data
Requires: Google Chrome (or Chromium), ffmpeg, Pillow. Usage: python3 docs/make_demo.py
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
EXAMPLE = ROOT / "examples" / "fastlane" / "metadata"
W, H, FPS, FADE = 1280, 720, 24, 0.45
STAGES = ["Build", "Test & release", "Store & creatives", "Campaigns", "Measure", "Improve"]
CHROME_CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "chromium",
                     "chromium-browser"]

sys.path.insert(0, str(ROOT / "scripts"))
import check_metadata  # noqa: E402  (the real checker, not a copy)

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: 1280px; height: 720px; overflow: hidden; background: radial-gradient(1200px 700px at 80% -10%, #16213a, #0a0e18);
  color: #e8edf6; font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif; }
.mono { font-family: Menlo, "DejaVu Sans Mono", monospace; }
.rail { position: absolute; top: 26px; left: 48px; right: 48px; display: flex; align-items: center; }
.pill { display: flex; align-items: center; gap: 10px; padding: 9px 16px; border-radius: 999px; font-size: 21px;
  font-weight: 700; color: #7d8aa6; border: 2px solid #26324c; background: #0f1626; white-space: nowrap; }
.pill .n { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-size: 15px;
  background: #1c2740; color: #9fb0cf; }
.pill.done { color: #c9f5d9; border-color: #1f6b45; } .pill.done .n { background: #22c55e; color: #06210f; }
.pill.on { color: #06121f; background: #38bdf8; border-color: #38bdf8; } .pill.on .n { background: #06121f; color: #38bdf8; }
.link { flex: 1; height: 3px; margin: 0 6px; background: #26324c; border-radius: 3px; }
.link.done { background: linear-gradient(90deg, #22c55e, #38bdf8); }
.head { position: absolute; top: 118px; left: 64px; right: 64px; display: flex; justify-content: space-between; align-items: flex-start; }
h1 { font-size: 50px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.05; }
h1 .k { color: #38bdf8; }
.sub { margin-top: 10px; font-size: 25px; color: #a9b6cf; max-width: 760px; line-height: 1.3; }
.badge { padding: 8px 14px; border-radius: 10px; font-size: 16px; font-weight: 800; letter-spacing: .6px; white-space: nowrap; }
.real { background: #0f3b26; color: #7ef0a8; border: 1px solid #22c55e; }
.illu { background: #3b2a0a; color: #fcd34d; border: 1px solid #f59e0b; }
.stage { position: absolute; top: 262px; left: 64px; right: 64px; bottom: 40px; display: flex; gap: 28px; align-items: flex-start; }
.stage > .card { min-width: 0; }
.card { background: #111a2c; border: 1px solid #24314d; border-radius: 18px; padding: 22px 24px;
  box-shadow: 0 18px 40px rgba(0,0,0,.35); position: relative; }
.card h3 { font-size: 22px; color: #9fb0cf; font-weight: 700; margin-bottom: 14px; display: flex; justify-content: space-between; gap: 12px; }
.row { display: flex; align-items: center; gap: 12px; font-size: 23px; padding: 7px 0; }
.ok { color: #4ade80; } .bad { color: #f87171; } .warn { color: #fbbf24; } .dim { color: #7d8aa6; }
.diff div { font-size: 20px; padding: 3px 10px; border-radius: 6px; white-space: pre; }
.add { background: rgba(34,197,94,.14); color: #a7f3c4; } .del { background: rgba(248,113,113,.13); color: #fecaca; }
.term div { font-size: 19px; white-space: pre; padding: 2px 0; }
.chip { display: inline-block; margin-top: 16px; padding: 10px 16px; border-radius: 12px; font-size: 21px; font-weight: 700;
  background: #0f2a3d; color: #7dd3fc; border: 1px solid #38bdf8; }
table { width: 100%; border-collapse: collapse; font-size: 23px; }
th { text-align: left; color: #7d8aa6; font-size: 18px; font-weight: 700; padding: 6px 8px; border-bottom: 1px solid #24314d; }
td { padding: 12px 8px; border-bottom: 1px solid #1a2540; }
.modal { position: absolute; right: 30px; bottom: 26px; width: 470px; background: #0d1424; border: 2px solid #38bdf8;
  border-radius: 18px; padding: 20px 22px; box-shadow: 0 30px 60px rgba(0,0,0,.55); }
.btn { display: inline-block; padding: 9px 18px; border-radius: 10px; font-weight: 800; font-size: 20px; margin-right: 10px; }
.btn.go { background: #22c55e; color: #052012; } .btn.no { border: 1px solid #3a4a6d; color: #9fb0cf; }
.bar { height: 30px; border-radius: 8px; display: flex; align-items: center; padding-left: 10px; font-size: 18px; font-weight: 800; color: #06121f; }
.phone { width: 210px; height: 360px; border-radius: 28px; border: 3px solid #2c3b5c; background: linear-gradient(160deg, #1d4ed8, #7c3aed);
  padding: 22px 16px; display: flex; flex-direction: column; justify-content: space-between; }
.square { width: 250px; height: 250px; border-radius: 18px; border: 3px solid #2c3b5c; background: linear-gradient(140deg, #0e7490, #22c55e);
  padding: 18px; display: flex; flex-direction: column; justify-content: space-between; }
.ad-title { font-size: 25px; font-weight: 800; line-height: 1.15; } .ad-cta { background: #fff; color: #111; border-radius: 10px;
  text-align: center; font-weight: 800; padding: 8px; font-size: 18px; }
.center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.big { font-size: 74px; font-weight: 800; letter-spacing: -1px; line-height: 1.05; }
.lede { font-size: 30px; color: #a9b6cf; margin-top: 18px; }
.cmd { font-size: 26px; background: #0f1626; border: 1px solid #26324c; border-radius: 12px; padding: 12px 20px; margin-top: 12px; }
.loop { position: absolute; top: 92px; left: 120px; right: 120px; height: 24px; border: 3px dashed #22c55e; border-top: none;
  border-radius: 0 0 24px 24px; }
"""


def rail(active: int, loop: bool = False) -> str:
    parts = []
    for i, name in enumerate(STAGES):
        cls = "on" if i == active else "done" if i < active else ""
        mark = "&#10003;" if i < active else str(i + 1)
        parts.append(f'<div class="pill {cls}"><span class="n">{mark}</span>{html.escape(name)}</div>')
        if i < len(STAGES) - 1:
            parts.append(f'<div class="link {"done" if i < active else ""}"></div>')
    return f'<div class="rail">{"".join(parts)}</div>' + ('<div class="loop"></div>' if loop else "")


def page(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def header(n: int, title: str, sub: str, badges: str) -> str:
    return (f'<div class="head"><div><h1><span class="k">{n} ·</span> {title}</h1><div class="sub">{sub}</div></div>'
            f'<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end">{badges}</div></div>')


REAL = '<span class="badge real">REAL OUTPUT</span>'
ILLU = '<span class="badge illu">ILLUSTRATIVE · SAMPLE DATA</span>'


def real_runs() -> dict:
    """Run the real checker on the example listing, once broken and once fixed."""
    with tempfile.TemporaryDirectory() as tmp:
        meta = Path(tmp) / "metadata"
        shutil.copytree(EXAMPLE, meta)
        (meta / "en-US" / "subtitle.txt").write_text("Daily word puzzles for your commute\n", encoding="utf-8")
        broken = check_metadata.check("ios", meta)
        (meta / "en-US" / "subtitle.txt").write_text("Daily word puzzles\n", encoding="utf-8")
        fixed = check_metadata.check("ios", meta)
        subs = {loc: (meta / loc / "subtitle.txt").read_text(encoding="utf-8").strip() for loc in ("en-US", "tr")}
    return {"broken": broken, "fixed": fixed, "subtitles": subs}


def term(result) -> str:
    code, lines = result
    rows = []
    for line in lines + [f"exit code {code}"]:
        cls = "bad" if line.startswith("FAIL") else "ok" if line.startswith("OK") else "dim"
        rows.append(f'<div class="{cls}">{html.escape(line)}</div>')
    return "".join(rows)


def scenes(real: dict) -> list:
    """Return [(seconds, html)] in order. Steps of one scene share a layout so crossfades read as progress."""
    out = []
    # 0 intro
    for step, secs in ((0, 1.6), (1, 2.4)):
        lede = '<div class="lede">One app, six stages, and every release and ad dollar approved by you.</div>' if step else ""
        out.append((secs, page(rail(-1) + f'<div class="center"><div class="big">From commit<br>to growth</div>{lede}'
                                          '<div class="lede" style="font-size:24px;margin-top:26px">ShipPilot · a Claude Code plugin</div></div>')))
    # 1 build
    diff = ("<div class='del'>-   startTutorial()</div><div class='add'>+   if (prefs.firstOpen) openTodaysPuzzle()</div>"
            "<div class='add'>+   else startTutorial()</div><div class='dim'>    analytics.log(\"onboarding_start\")</div>"
            "<div class='add'>+   analytics.log(\"first_puzzle_open\")</div>")
    for step, secs in ((0, 2.2), (1, 2.6)):
        chip = '<div class="chip">Claude Code · change ready for review · 2 tests added</div>' if step else ""
        out.append((secs, page(rail(0) + header(1, "Build", "Claude Code writes the change in your repo; you review the diff.", ILLU)
                    + f'<div class="stage"><div class="card" style="flex:1"><h3><span class="mono">onboarding/OnboardingFlow.kt</span>'
                      f'<span>diff</span></h3><div class="diff mono">{diff}</div>{chip}</div></div>')))
    # 2 test & release
    steps = [
        (2.6, [("ok", "Unit tests · 38 passed"), ("bad", "Store metadata limits")], term(real["broken"]), ""),
        (2.6, [("ok", "Unit tests · 38 passed"), ("ok", "Store metadata limits")], term(real["fixed"]), ""),
        (2.4, [("ok", "Unit tests · 38 passed"), ("ok", "Store metadata limits"), ("warn", "Beta upload · waiting for your approval")],
         term(real["fixed"]), ""),
        (2.6, [("ok", "Unit tests · 38 passed"), ("ok", "Store metadata limits"), ("ok", "Beta upload · approved")],
         term(real["fixed"]), '<div class="chip">TestFlight · Pocket Words 1.4 (13) · Processing</div>'),
    ]
    for secs, checks, terminal, chip in steps:
        rows = "".join(f'<div class="row"><span class="{c}">{"&#10003;" if c == "ok" else "&#10007;" if c == "bad" else "&#9208;"}'
                       f'</span>{html.escape(t)}</div>' for c, t in checks)
        out.append((secs, page(rail(1) + header(2, "Test &amp; release", "CI runs your tests and the store checks; the beta upload waits for you.",
                                                 REAL + ILLU)
                    + f'<div class="stage"><div class="card" style="width:500px"><h3><span>CI · tag v1.4.0</span>'
                      f'<span class="badge illu" style="font-size:12px">ILLUSTRATIVE</span></h3>{rows}{chip}</div>'
                      f'<div class="card" style="flex:1"><h3><span class="mono">check_metadata.py --platform ios</span>'
                      f'<span class="badge real" style="font-size:12px">REAL</span></h3><div class="term mono">{terminal}</div></div></div>')))
    # 3 store & creatives
    subs = real["subtitles"]
    listing = "".join(f'<div class="row"><span class="dim mono" style="width:70px">{loc}</span>{html.escape(text)}'
                      f'<span class="ok mono" style="margin-left:auto">{len(text)}/30</span></div>' for loc, text in subs.items())
    for step, secs in ((0, 2.4), (1, 3.0)):
        creatives = ""
        if step:
            creatives = ('<div class="phone"><div class="ad-title">One fresh word puzzle every morning</div><div class="ad-cta">Play today\'s puzzle</div></div>'
                         '<div class="square"><div class="ad-title">5 minutes.<br>New words.</div><div class="ad-cta">Install free</div></div>')
        out.append((secs, page(rail(2) + header(3, "Store &amp; creatives", "Localized store text within limits, then ad angles that match the first screen.",
                                                 REAL + ILLU)
                    + f'<div class="stage"><div class="card" style="width:500px"><h3><span>App Store subtitle</span>'
                      f'<span class="badge real" style="font-size:12px">REAL · LIMITS CHECKED</span></h3>{listing}'
                      f'<div class="row dim" style="font-size:19px;margin-top:8px">/shippilot:localize · /shippilot:ad-creatives</div></div>'
                      f'<div style="display:flex;gap:26px;align-items:flex-start">{creatives}</div></div>')))
    # 4 campaigns
    table = ("<table><tr><th>Campaign</th><th>Spend</th><th>Installs</th><th>CPI</th></tr>"
             "<tr><td>A · Google App · daily puzzle</td><td>$140</td><td>212</td><td class='ok'>$0.66</td></tr>"
             "<tr><td>B · Meta · brain training</td><td>$140</td><td>171</td><td class='warn'>$0.82</td></tr></table>")
    modals = [
        "",
        '<div class="modal"><div style="font-size:18px;color:#7dd3fc;font-weight:800">PREVIEW · campaign A budget</div>'
        '<div style="font-size:30px;font-weight:800;margin:8px 0">$20.00 &rarr; $24.00 / day</div>'
        '<div class="dim" style="font-size:18px;margin-bottom:14px">Currency USD · account timezone UTC</div>'
        '<span class="btn go">Approve</span><span class="btn no">Cancel</span></div>',
        '<div class="modal" style="border-color:#22c55e"><div style="font-size:18px;color:#4ade80;font-weight:800">APPLIED · READ-BACK</div>'
        '<div style="font-size:30px;font-weight:800;margin:8px 0">budget = $24.00 / day &#10003;</div>'
        '<div class="dim" style="font-size:18px">verified with a separate read after apply</div></div>',
    ]
    for step, secs in ((0, 2.2), (1, 2.4), (2, 2.2)):
        out.append((secs, page(rail(3) + header(4, "Campaigns", "Read every account first. Every change: preview &rarr; your approval &rarr; read-back.", ILLU)
                    + f'<div class="stage"><div class="card" style="flex:1"><h3><span>/shippilot:ads-report · last 7 days</span></h3>{table}</div></div>'
                    + modals[step])))
    # 5 measure
    def funnel(label, n, vals, color):
        bars = "".join(f'<div style="display:flex;align-items:center;gap:12px;margin:8px 0"><span class="dim" style="width:190px;font-size:20px">{k}</span>'
                       f'<div class="bar" style="width:{int(v * 2.9)}px;background:{color}">{v}%</div></div>' for k, v in vals)
        return f'<div class="card" style="flex:1"><h3><span>{label}</span><span class="dim">n = {n}</span></h3>{bars}</div>'
    for step, secs in ((0, 2.4), (1, 3.0)):
        callout = ('<div class="chip" style="position:absolute;left:64px;bottom:-6px;background:#3b2a0a;color:#fde68a;border-color:#f59e0b">'
                   'Campaign B users finish onboarding far less often (41% vs 68%)</div>') if step else ""
        out.append((secs, page(rail(4) + header(5, "Measure", "Same cohort, same window: campaigns joined with in-app behaviour.", ILLU)
                    + '<div class="stage" style="bottom:70px">'
                    + funnel("Campaign A", "1,240", [("Install", 100), ("Onboarding done", 68), ("Day-1 return", 32)], "#38bdf8")
                    + funnel("Campaign B", "980", [("Install", 100), ("Onboarding done", 41), ("Day-1 return", 18)], "#f59e0b")
                    + f'{callout}</div>')))
    # 6 improve
    cards = [
        ("Hypothesis", "Ad B promises brain training; the app opens with a tutorial, not a puzzle."),
        ("One change", "First open goes straight to today's puzzle (the Build diff)."),
        ("Decision rule", "Keep it if B onboarding &ge; 55% after 7 days with n &ge; 800."),
    ]
    for step, secs in ((0, 2.0), (1, 2.0), (2, 3.0)):
        shown = "".join(f'<div class="card" style="flex:1;visibility:{"visible" if i <= step else "hidden"}"><h3><span>{t}</span></h3>'
                        f'<div style="font-size:25px;line-height:1.35">{b}</div></div>' for i, (t, b) in enumerate(cards))
        out.append((secs, page(rail(5, loop=step == 2) + header(6, "Improve", "One hypothesis, one change, a rule decided before you look again.", ILLU)
                    + f'<div class="stage">{shown}</div>'
                    + ('<div class="chip" style="position:absolute;left:64px;bottom:40px">&#8634; next loop starts at Build: ship the change, then measure again</div>' if step == 2 else ""))))
    # 7 outro
    out.append((4.0, page(rail(6) + '<div class="center"><div class="big" style="font-size:60px">Install ShipPilot</div>'
                          '<div class="cmd mono">/plugin marketplace add ufukyuksel-dev/shippilot</div>'
                          '<div class="cmd mono">/plugin install shippilot@shippilot</div>'
                          '<div class="lede">github.com/ufukyuksel-dev/shippilot · MIT · runs in your Claude Code</div></div>')))
    return out


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
           "body { width:1200px; height:620px; }")
    return page(f"<style>{css}</style>{arrows}{''.join(cards)}").replace("width: 1280px; height: 720px;", "")


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    raise SystemExit("ERROR: Google Chrome / Chromium not found")


def shoot(chrome: str, html_text: str, png: Path, size=(W, H)) -> Image.Image:
    src = png.with_suffix(".html")
    src.write_text(html_text, encoding="utf-8")
    # --no-sandbox: only local HTML generated by this script is rendered; Chrome's own sandbox cannot start inside
    # some sandboxed runners. A throwaway profile keeps the user's Chrome profile untouched.
    profile = png.parent / "chrome-profile"
    proc = subprocess.Popen([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                             "--disable-extensions", "--use-mock-keychain", "--password-store=basic",
                             f"--user-data-dir={profile}", "--force-device-scale-factor=1", f"--window-size={size[0]},{size[1]}",
                             f"--screenshot={png}", src.as_uri()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Some Chrome builds keep running after writing the screenshot; wait for the file, then stop the process.
    deadline, last = time.time() + 60, -1
    while time.time() < deadline:
        nbytes = png.stat().st_size if png.exists() else -1
        if nbytes > 0 and nbytes == last:
            break
        if proc.poll() is not None and nbytes > 0:
            break
        last = nbytes
        time.sleep(0.3)
    if proc.poll() is None:
        proc.kill()
        proc.wait()
    if not png.exists():
        raise SystemExit(f"ERROR: Chrome produced no screenshot for {src.name}")
    return Image.open(png).convert("RGB").resize(size)


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg not found", file=sys.stderr)
        return 2
    chrome = find_chrome()
    real = real_runs()
    plan = scenes(real)
    ASSETS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        shots = [shoot(chrome, h, tmpdir / f"s{i:02d}.png") for i, (_, h) in enumerate(plan)]
        frames_dir = tmpdir / "frames"
        frames_dir.mkdir()
        n = 0
        fade = int(FADE * FPS)
        for i, ((secs, _), img) in enumerate(zip(plan, shots)):
            hold = max(1, int(secs * FPS) - (fade if i + 1 < len(shots) else 0))
            for _ in range(hold):
                img.save(frames_dir / f"f{n:05d}.png"); n += 1
            if i + 1 < len(shots):
                for k in range(1, fade + 1):
                    Image.blend(img, shots[i + 1], k / (fade + 1)).save(frames_dir / f"f{n:05d}.png"); n += 1
        pattern = str(frames_dir / "f%05d.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern, "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "22", "-movflags", "+faststart", str(ASSETS / "demo.mp4")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern, "-vf",
                        "fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];"
                        "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", str(ASSETS / "demo.gif")], check=True)
        shots[13].save(ASSETS / "poster.png")
        shoot(chrome, flow_page(), tmpdir / "flow.png", (1200, 620)).save(ASSETS / "flow.png")
    duration = n / FPS
    (ASSETS / "demo.json").write_text(json.dumps({"seconds": round(duration, 1), "frames": n, "scenes": len(plan)}) + "\n")
    print(f"OK: {n} frames, {duration:.1f}s -> docs/assets/demo.mp4, demo.gif, poster.png, flow.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
