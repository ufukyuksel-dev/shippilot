"""Tests for scripts/check_metadata.py."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_metadata.py"
EXAMPLE = ROOT / "examples" / "fastlane" / "metadata"

spec = importlib.util.spec_from_file_location("check_metadata", SCRIPT)
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)


class CheckMetadataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.meta = self.tmp / "metadata"
        shutil.copytree(EXAMPLE, self.meta)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_examples_pass(self):
        code, lines = cm.check("ios", self.meta)
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[-1], "OK: 7 file(s) in 2 locale(s) checked (ios)")
        code, lines = cm.check("android", self.meta / "android")
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[-1], "OK: 4 file(s) in 1 locale(s) checked (android)")

    def test_over_limit_fails(self):
        (self.meta / "en-US" / "subtitle.txt").write_text("x" * 31 + "\n", encoding="utf-8")
        code, lines = cm.check("ios", self.meta)
        self.assertEqual(code, 1)
        self.assertIn("FAIL en-US/subtitle.txt: 31/30 characters (+1)", lines)

    def test_ios_keywords_are_counted_in_bytes(self):
        (self.meta / "tr" / "keywords.txt").write_text("ç" * 51, encoding="utf-8")  # 51 chars, 102 bytes
        code, lines = cm.check("ios", self.meta)
        self.assertEqual(code, 1)
        self.assertIn("FAIL tr/keywords.txt: 102/100 bytes (+2)", lines)

    def test_empty_keyword_fails(self):
        (self.meta / "en-US" / "keywords.txt").write_text("word,,puzzle", encoding="utf-8")
        self.assertEqual(cm.check("ios", self.meta)[0], 1)

    def test_android_changelog_limit(self):
        (self.meta / "android" / "en-US" / "changelogs" / "13.txt").write_text("y" * 501, encoding="utf-8")
        code, lines = cm.check("android", self.meta / "android")
        self.assertEqual(code, 1)
        self.assertIn("FAIL en-US/changelogs/13.txt: 501/500 characters (+1)", lines)

    def test_android_dir_is_not_an_ios_locale(self):
        code, lines = cm.check("ios", self.meta)
        self.assertNotIn("android", " ".join(lines[:-1]))

    def test_nothing_to_check_is_not_success(self):
        self.assertEqual(cm.check("ios", self.tmp / "missing")[0], 2)
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(cm.check("android", empty)[0], 2)
        (empty / "en-US").mkdir()
        (empty / "en-US" / "notes.txt").write_text("x", encoding="utf-8")
        code, lines = cm.check("android", empty)
        self.assertEqual(code, 2)
        self.assertIn("no recognised android metadata files", lines[0])

    def test_wrong_platform_root_is_not_success(self):
        # iOS files under an Android root: nothing recognised.
        self.assertEqual(cm.check("android", self.meta)[0], 2)

    def test_cli_exit_codes(self):
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), *a], capture_output=True, text=True)
        self.assertEqual(run("--platform", "ios", "--metadata", str(self.meta)).returncode, 0)
        self.assertEqual(run("--platform", "android", "--metadata", str(self.tmp / "nope")).returncode, 2)
        self.assertEqual(run("--metadata", str(self.meta)).returncode, 2)  # --platform is required


if __name__ == "__main__":
    unittest.main()
