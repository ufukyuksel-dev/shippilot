#!/usr/bin/env python3
"""Check Fastlane store metadata against App Store / Google Play length limits (stdlib only, Python 3.9+).

Usage:
  python3 check_metadata.py --platform ios     [--metadata fastlane/metadata]
  python3 check_metadata.py --platform android [--metadata fastlane/metadata/android]

Layouts (as written by `fastlane deliver` / `fastlane supply`):
  ios:     <metadata>/<locale>/{name,subtitle,keywords,promotional_text,description,release_notes}.txt
  android: <metadata>/<locale>/{title,short_description,full_description}.txt and <locale>/changelogs/*.txt

Lengths are counted in Unicode characters (iOS keywords: UTF-8 bytes) after stripping the trailing newline. Exit codes:
  0  every recognised file is within its limit
  1  at least one limit or format violation
  2  nothing to check (missing directory, no locale, no recognised file) or usage error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Sources (checked 2026-10): developer.apple.com/help/app-store-connect/reference/app-information/ (app-information,
# platform-version-information) and support.google.com/googleplay/android-developer/answer/9859152.
# iOS keywords are limited in UTF-8 bytes, everything else in characters.
LIMITS: Dict[str, Dict[str, int]] = {
    "ios": {
        "name": 30,
        "subtitle": 30,
        "keywords": 100,
        "promotional_text": 170,
        "description": 4000,
        "release_notes": 4000,
    },
    "android": {
        "title": 30,
        "short_description": 80,
        "full_description": 4000,
    },
}
BYTE_LIMITED = {("ios", "keywords")}
ANDROID_CHANGELOG_LIMIT = 500
DEFAULT_DIR = {"ios": Path("fastlane/metadata"), "android": Path("fastlane/metadata/android")}
# Directories under an iOS metadata root that are not locales.
IOS_NON_LOCALE = {"android", "review_information", "trade_representative_contact_information"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip("\r\n")


def check_file(path: Path, limit: int, label: str, in_bytes: bool = False) -> List[str]:
    try:
        text = read_text(path)
    except UnicodeDecodeError:
        return [f"FAIL {label}: not valid UTF-8"]
    problems = []
    size, unit = (len(text.encode("utf-8")), "bytes") if in_bytes else (len(text), "characters")
    if size > limit:
        problems.append(f"FAIL {label}: {size}/{limit} {unit} (+{size - limit})")
    if label.endswith("/keywords.txt") and text and any(not k.strip() for k in text.split(",")):
        problems.append(f"FAIL {label}: empty keyword between commas")
    return problems


def check(platform: str, root: Path) -> Tuple[int, List[str]]:
    if not root.is_dir():
        return 2, [f"ERROR: metadata directory not found: {root}"]
    locales = sorted(p for p in root.iterdir()
                     if p.is_dir() and not (platform == "ios" and p.name in IOS_NON_LOCALE))
    if not locales:
        return 2, [f"ERROR: no locale directories in {root}"]
    lines, checked, failed = [], 0, False
    for locale in locales:
        for field, limit in LIMITS[platform].items():
            path = locale / f"{field}.txt"
            if path.is_file():
                problems = check_file(path, limit, f"{locale.name}/{field}.txt", (platform, field) in BYTE_LIMITED)
                checked += 1
                failed |= bool(problems)
                lines.extend(problems)
        if platform == "android":
            for path in sorted((locale / "changelogs").glob("*.txt")):
                problems = check_file(path, ANDROID_CHANGELOG_LIMIT, f"{locale.name}/changelogs/{path.name}")
                checked += 1
                failed |= bool(problems)
                lines.extend(problems)
    if checked == 0:
        return 2, [f"ERROR: no recognised {platform} metadata files in {root}"]
    summary = f"{'FAILED' if failed else 'OK'}: {checked} file(s) in {len(locales)} locale(s) checked ({platform})"
    return (1 if failed else 0), lines + [summary]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--platform", required=True, choices=sorted(LIMITS))
    parser.add_argument("--metadata", type=Path, help="metadata root (default depends on --platform)")
    args = parser.parse_args(argv)
    code, lines = check(args.platform, args.metadata or DEFAULT_DIR[args.platform])
    for line in lines:
        print(line, file=sys.stderr if code == 2 else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
