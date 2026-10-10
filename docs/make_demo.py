#!/usr/bin/env python3
"""Render docs/assets/demo.mp4 and docs/assets/demo.gif (requires Pillow and ffmpeg).

Terminal scenes show the real output of scripts/check_metadata.py, captured when this script runs, so the video
cannot drift from what the tool prints. Usage: python3 docs/make_demo.py
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
W, H, FPS = 1280, 720, 24
BG, PANEL, FG, DIM = (11, 15, 25), (20, 26, 40), (226, 232, 240), (120, 134, 160)
ACCENT, OK, BAD = (34, 211, 238), (74, 222, 128), (248, 113, 113)
STAGES = ["Build", "Ship", "Grow", "Measure", "Improve"]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = ["/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size, index=1 if bold and path.endswith(".ttc") else 0)
    return ImageFont.load_default()


MONO, MONO_B, TITLE, SUB = font(24), font(24, True), font(64, True), font(28)


def run_checker(*args: str) -> list:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_metadata.py"), *args],
                          capture_output=True, text=True, cwd=ROOT)
    return (proc.stdout + proc.stderr).splitlines() + [f"exit code {proc.returncode}"]


def loop_frame(t: float, caption: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 92), "ShipPilot", font=TITLE, fill=FG, anchor="mm")
    d.text((W // 2, 150), caption, font=SUB, fill=DIM, anchor="mm")
    cx, cy, r = W // 2, 430, 190
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(40, 52, 78), width=4)
    active = int(t) % len(STAGES)
    a = -math.pi / 2 + 2 * math.pi * (t / len(STAGES))
    d.ellipse((cx + r * math.cos(a) - 9, cy + r * math.sin(a) - 9, cx + r * math.cos(a) + 9,
               cy + r * math.sin(a) + 9), fill=OK)
    for i, name in enumerate(STAGES):
        a = -math.pi / 2 + 2 * math.pi * i / len(STAGES)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        on = i == active
        rad = 62 if on else 54
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=ACCENT if on else PANEL,
                  outline=ACCENT, width=3)
        d.text((x, y), name, font=font(18, on), fill=BG if on else FG, anchor="mm")
    d.text((cx, cy), "approval\ngates", font=font(22), fill=DIM, anchor="mm", align="center")
    return img


WRAP = 74


def wrap(lines: list) -> list:
    out = []
    for kind, text in lines:
        while kind == "cmd" and len(text) > WRAP:
            cut = text.rfind(" ", 0, WRAP)
            out.append((kind, text[:cut] + " \\"))
            text = "  " + text[cut + 1:]
        out.append((kind, text))
    return out


def terminal_frame(title: str, lines: list, typed: int, cursor: bool) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((60, 50, W - 60, H - 50), radius=18, fill=PANEL)
    for i, c in enumerate([(248, 113, 113), (251, 191, 36), (74, 222, 128)]):
        d.ellipse((90 + i * 30, 72, 106 + i * 30, 88), fill=c)
    d.text((W // 2, 80), title, font=font(20), fill=DIM, anchor="mm")
    budget, y = typed, 130
    for kind, text in lines:
        if budget <= 0:
            break
        shown = text[:budget] if kind == "cmd" else text
        budget -= len(text) if kind == "cmd" else 1
        if kind == "cmd":
            if not text.startswith("  "):  # continuation lines of a wrapped command have no prompt
                d.text((95, y), "$", font=MONO_B, fill=ACCENT)
            d.text((125, y), shown, font=MONO_B, fill=FG)
        else:
            color = BAD if text.startswith(("FAIL", "FAILED")) else OK if text.startswith("OK") else DIM
            d.text((95, y), text, font=MONO, fill=color)
        y += 38
    if cursor:
        d.rectangle((95, y + 4, 109, y + 30), fill=ACCENT)
    return img


def terminal_scene(title: str, lines: list, hold: float = 2.5) -> list:
    lines = wrap(lines)
    total = sum(len(t) if k == "cmd" else 1 for k, t in lines)
    frames, typed = [], 0
    while typed < total:
        kind = None
        budget = typed
        for k, t in lines:  # find what is being revealed now
            size = len(t) if k == "cmd" else 1
            if budget < size:
                kind = k
                break
            budget -= size
        typed += 2 if kind == "cmd" else 1
        frames.append(terminal_frame(title, lines, typed, True))
        if kind != "cmd":
            frames.extend([frames[-1]] * 3)
    frames.extend([terminal_frame(title, lines, total, (i // 12) % 2 == 0) for i in range(int(hold * FPS))])
    return frames


def card(title: str, rows: list, seconds: float = 4.0) -> list:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 110), title, font=font(46, True), fill=FG, anchor="mm")
    y = 200
    for left, right in rows:
        d.text((180, y), left, font=MONO_B, fill=ACCENT)
        d.text((560, y), right, font=MONO, fill=FG)
        y += 54
    return [img] * int(seconds * FPS)


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg not found", file=sys.stderr)
        return 2
    example = "examples/fastlane/metadata"
    frames = []
    for i in range(int(5 * FPS)):
        frames.append(loop_frame(i / FPS * 1.0, "Build, ship and grow mobile apps with Claude Code"))
    frames += terminal_scene("Install in Claude Code", [
        ("cmd", "/plugin marketplace add ufukyuksel-dev/shippilot"),
        ("cmd", "/plugin install shippilot@shippilot"),
    ])
    frames += card("What you get", [
        ("/shippilot:launch-check", "read-only readiness report"),
        ("/shippilot:localize", "store text, local + validated"),
        ("/shippilot:check-metadata", "App Store / Play limits"),
        ("/shippilot:beta", "TestFlight / Play internal"),
        ("/shippilot:ads-report", "Google, Meta, TikTok (read-only)"),
        ("/shippilot:grow", "measure -> change -> re-measure"),
    ], 5)
    cmd = f"python3 scripts/check_metadata.py --platform ios --metadata {example}"
    frames += terminal_scene("Real output: valid listing", [("cmd", cmd)] + [("out", l) for l in run_checker(
        "--platform", "ios", "--metadata", example)])
    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp) / "metadata"
        shutil.copytree(ROOT / example, broken)
        (broken / "en-US" / "subtitle.txt").write_text("Pocket Words: Daily brain puzzles\n", encoding="utf-8")
        (broken / "tr" / "keywords.txt").write_text("kelime,,bulmaca\n", encoding="utf-8")
        out = run_checker("--platform", "ios", "--metadata", str(broken))
    frames += terminal_scene("Real output: too-long subtitle, empty keyword", [
        ("cmd", "python3 scripts/check_metadata.py --platform ios --metadata metadata")] +
        [("out", l) for l in out], hold=3)
    for i in range(int(4 * FPS)):
        frames.append(loop_frame(i / FPS * 1.0, "github.com/ufukyuksel-dev/shippilot  -  MIT"))

    ASSETS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for i, frame in enumerate(frames):
            frame.save(Path(tmp) / f"f{i:05d}.png")
        pattern = str(Path(tmp) / "f%05d.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-movflags", "+faststart",
                        str(ASSETS / "demo.mp4")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern, "-vf",
                        "fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];"
                        "[b][p]paletteuse=dither=none", str(ASSETS / "demo.gif")], check=True)
        frames[int(2 * FPS)].save(ASSETS / "poster.png")
    print(f"OK: {len(frames)} frames -> docs/assets/demo.mp4, demo.gif, poster.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
