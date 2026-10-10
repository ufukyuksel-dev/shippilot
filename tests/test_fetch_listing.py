"""Tests for scripts/fetch_listing.py (no network: responses are injected)."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("fetch_listing", ROOT / "scripts" / "fetch_listing.py")
fl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fl)

LOOKUP = {"resultCount": 1, "results": [{
    "trackName": "Pocket Words: Daily Puzzles With Friends",  # 40 chars: over the 30-char name limit
    "description": "One new word puzzle every day.", "releaseNotes": "Bug fixes.", "version": "1.4",
    "primaryGenreName": "Games", "formattedPrice": "Free", "averageUserRating": 4.6, "userRatingCount": 120,
    "screenshotUrls": ["a", "b", "c"], "ipadScreenshotUrls": [], "trackViewUrl": "https://apps.apple.com/app/id1"}]}
PLAY_PAGE = """<html><head><title>Pocket Words - Apps on Google Play</title>
<meta property="og:title" content="Pocket Words - Apps on Google Play">
<meta name="description" content="One new word puzzle every day."></head><body></body></html>"""


def getter(responses):
    calls = []

    def get(url):
        calls.append(url)
        value = responses[url.split("?")[0]]
        if isinstance(value, Exception):
            raise value
        return value.encode("utf-8") if isinstance(value, str) else value
    get.calls = calls
    return get


class ParseUrlTest(unittest.TestCase):
    def test_app_store_forms(self):
        self.assertEqual(fl.parse_url("https://apps.apple.com/tr/app/pocket-words/id123456789"), ("ios", "123456789", "tr"))
        self.assertEqual(fl.parse_url("https://apps.apple.com/app/id42"), ("ios", "42", "us"))
        self.assertEqual(fl.parse_url("https://itunes.apple.com/lookup?id=77"), ("ios", "77", "us"))

    def test_play_forms(self):
        self.assertEqual(fl.parse_url("https://play.google.com/store/apps/details?id=com.example.app"),
                         ("android", "com.example.app", "en_US"))
        self.assertEqual(fl.parse_url("https://play.google.com/store/apps/details?id=a.b&hl=de&gl=DE"),
                         ("android", "a.b", "de_DE"))

    def test_rejects_other_urls(self):
        for url in ("https://example.com/app/id1", "https://apps.apple.com/us/app/no-id",
                    "https://play.google.com/store/apps/details?id=notapackage", "not a url"):
            with self.assertRaises(fl.ListingError, msg=url):
                fl.parse_url(url)


class FetchTest(unittest.TestCase):
    def test_ios_fields_lengths_and_missing(self):
        get = getter({"https://itunes.apple.com/lookup": json.dumps(LOOKUP)})
        r = fl.fetch("https://apps.apple.com/us/app/x/id1", get)
        self.assertEqual(get.calls, ["https://itunes.apple.com/lookup?id=1&country=us"])
        self.assertEqual(r["fields"]["iphone_screenshots"], 3)
        self.assertEqual(r["lengths"]["name"], {"length": 40, "limit": 30, "unit": "characters", "over": True})
        for unknown in ("subtitle", "keywords", "promotional_text", "in_app_purchases"):
            self.assertIn(unknown, r["missing"])
            self.assertIsNone(r["fields"][unknown])
        self.assertTrue(r["fetched_at_utc"].endswith("+00:00"))

    def test_ios_not_found(self):
        get = getter({"https://itunes.apple.com/lookup": '{"resultCount": 0, "results": []}'})
        with self.assertRaises(fl.ListingError):
            fl.fetch("https://apps.apple.com/us/app/x/id9", get)

    def test_android_meta_only(self):
        get = getter({"https://play.google.com/store/apps/details": PLAY_PAGE})
        r = fl.fetch("https://play.google.com/store/apps/details?id=com.example.words", get)
        self.assertEqual(r["fields"]["title"], "Pocket Words")
        self.assertEqual(r["fields"]["meta_description"], "One new word puzzle every day.")
        self.assertIsNone(r["fields"]["full_description"])
        self.assertIn("full_description", r["missing"])
        self.assertEqual(r["lengths"]["title"]["limit"], 30)

    def test_android_404(self):
        err = urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        get = getter({"https://play.google.com/store/apps/details": err})
        with self.assertRaises(fl.ListingError):
            fl.fetch("https://play.google.com/store/apps/details?id=com.example.gone", get)

    def test_limits_come_from_check_metadata(self):
        import check_metadata
        self.assertIs(fl.LIMITS, check_metadata.LIMITS)

    def test_cli_bad_url_exit_code(self):
        self.assertEqual(fl.main(["https://example.com"]), 2)


if __name__ == "__main__":
    unittest.main()
