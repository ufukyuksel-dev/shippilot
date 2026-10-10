#!/usr/bin/env python3
"""Fetch the public store listing of an app as JSON (stdlib only, Python 3.9+). No account or API key needed.

Usage:
  python3 fetch_listing.py https://apps.apple.com/us/app/some-app/id123456789
  python3 fetch_listing.py "https://play.google.com/store/apps/details?id=com.example.app&hl=en&gl=US"

Sources:
  App Store    Apple's public iTunes Lookup API (https://itunes.apple.com/lookup?id=...&country=...).
  Google Play  The public app page, read once without signing in; only standard <meta> tags and <title> are used.

Only fields the source actually returns are filled. Everything else is null and listed in "missing" -- for example the
App Store subtitle, keywords and in-app purchase details are not in the Lookup API, and the Play meta description is a
short excerpt, not the full store description. Exit codes: 0 fetched, 2 unsupported URL, not found or network error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_metadata import LIMITS  # noqa: E402  (one source of truth for store limits)

USER_AGENT = "Mozilla/5.0 (compatible; ShipPilot-audit/0.3; +https://github.com/ufukyuksel-dev/shippilot)"
Fetch = Callable[[str], bytes]


class ListingError(Exception):
    pass


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (fixed https hosts only)
        return resp.read()


def parse_url(url: str) -> Tuple[str, str, str]:
    """Return (platform, app_id, region) where region is the App Store country or the Play hl/gl pair."""
    parsed = urllib.parse.urlparse(url.strip())
    host = parsed.netloc.lower()
    query = urllib.parse.parse_qs(parsed.query)
    if host in ("apps.apple.com", "itunes.apple.com"):
        match = re.search(r"/id(\d+)", parsed.path) or re.fullmatch(r"(\d+)", (query.get("id") or [""])[0])
        if not match:
            raise ListingError("App Store URL without an app id (expected .../id123456789)")
        country = parsed.path.strip("/").split("/")[0]
        return "ios", match.group(1), country if re.fullmatch(r"[a-z]{2}", country) else "us"
    if host == "play.google.com" and parsed.path.rstrip("/") == "/store/apps/details":
        package = (query.get("id") or [""])[0]
        if not re.fullmatch(r"[A-Za-z][\w]*(\.[A-Za-z0-9_]+)+", package):
            raise ListingError("Google Play URL without a valid package id (?id=com.example.app)")
        hl = (query.get("hl") or ["en"])[0]
        gl = (query.get("gl") or ["US"])[0]
        return "android", package, f"{hl}_{gl}"
    raise ListingError("unsupported URL: use an apps.apple.com or play.google.com/store/apps/details link")


def _length(field_platform: str, field: str, value: Optional[str]) -> Optional[dict]:
    limit = LIMITS[field_platform].get(field)
    if value is None or limit is None:
        return None
    in_bytes = (field_platform, field) == ("ios", "keywords")
    size = len(value.encode("utf-8")) if in_bytes else len(value)
    return {"length": size, "limit": limit, "unit": "bytes" if in_bytes else "characters", "over": size > limit}


def fetch_ios(app_id: str, country: str, get: Fetch) -> dict:
    url = f"https://itunes.apple.com/lookup?id={app_id}&country={country}"
    data = json.loads(get(url).decode("utf-8"))
    if not data.get("resultCount"):
        raise ListingError(f"App Store id {app_id} not found in country '{country}'")
    r = data["results"][0]
    fields = {
        "name": r.get("trackName"),
        "subtitle": None,
        "keywords": None,
        "promotional_text": None,
        "description": r.get("description"),
        "release_notes": r.get("releaseNotes"),
        "version": r.get("version"),
        "current_version_release_date": r.get("currentVersionReleaseDate"),
        "primary_genre": r.get("primaryGenreName"),
        "seller": r.get("sellerName"),
        "price": r.get("formattedPrice"),
        "in_app_purchases": None,
        "average_rating": r.get("averageUserRating"),
        "rating_count": r.get("userRatingCount"),
        "content_rating": r.get("contentAdvisoryRating"),
        "languages": r.get("languageCodesISO2A"),
        "iphone_screenshots": len(r.get("screenshotUrls") or []),
        "ipad_screenshots": len(r.get("ipadScreenshotUrls") or []),
        "store_url": r.get("trackViewUrl"),
    }
    lengths = {f: _length("ios", f, fields[f]) for f in ("name", "subtitle", "promotional_text", "description",
                                                          "release_notes", "keywords")}
    return {"source": url, "fields": fields, "lengths": {k: v for k, v in lengths.items() if v}}


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: Dict[str, str] = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = a.get("property") or a.get("name") or a.get("itemprop")
            if key and a.get("content") is not None and key not in self.meta:
                self.meta[key] = a["content"]
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def fetch_android(package: str, region: str, get: Fetch) -> dict:
    hl, gl = region.split("_", 1)
    url = f"https://play.google.com/store/apps/details?id={package}&hl={hl}&gl={gl}"
    try:
        page = get(url).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ListingError(f"Google Play package {package} not found") from exc
        raise
    parser = _MetaParser()
    parser.feed(page)
    raw_title = parser.meta.get("og:title") or parser.title
    title = re.sub(r"\s+-\s+Apps on Google Play\s*$", "", raw_title or "").strip() or None
    fields = {
        "title": title,
        "short_description": None,
        "full_description": None,
        "meta_description": parser.meta.get("og:description") or parser.meta.get("description"),
        "developer": None,
        "average_rating": None,
        "screenshots": None,
        "store_url": f"https://play.google.com/store/apps/details?id={package}",
    }
    lengths = {"title": _length("android", "title", title)}
    return {"source": url, "fields": fields, "lengths": {k: v for k, v in lengths.items() if v},
            "notes": ["meta_description is the page's <meta> summary, not the full store description"]}


def fetch(url: str, get: Fetch = http_get) -> dict:
    platform, app_id, region = parse_url(url)
    result = fetch_ios(app_id, region, get) if platform == "ios" else fetch_android(app_id, region, get)
    result.update({
        "platform": platform,
        "app_id": app_id,
        "region": region,
        "input_url": url,
        "fetched_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "missing": sorted(k for k, v in result["fields"].items() if v is None),
    })
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="App Store or Google Play app URL")
    args = parser.parse_args(argv)
    try:
        result = fetch(args.url)
    except ListingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:  # network errors, HTTP errors, invalid JSON
        print(f"ERROR: could not fetch the listing: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
