---
description: Read-only readiness report for building, shipping and growing this mobile app
---

Produce a read-only readiness report for this repository. Do not build, upload, change ads or edit files.

Check and report, each as ready / missing / unknown with the evidence you looked at:

1. **Build & release:** Fastlane setup (`fastlane/Fastfile`, `Appfile`, `Gemfile.lock`), actual lane names (`bundle exec fastlane lanes` if Bundler is available), Android variants and iOS schemes, where versions and build numbers come from, CI workflows. Note credential *presence* only; never print key contents. Use the `mobile-store-release` skill.
2. **Store listing:** `fastlane/metadata` (iOS) and `fastlane/metadata/android` (Android) locales. If they exist, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_metadata.py" --platform ios` and `--platform android` and include the result.
3. **Device QA:** whether the `adb` MCP tools are available in this session (`mobile-ui-review` skill).
4. **Ads:** which ad MCP servers/tools are available (Google Ads, Meta Ads, TikTok) and whether they are read-only or write-enabled. Do not call any mutation.
5. **Analytics:** which in-app analytics source the code actually sends events to, and which events exist for first open, onboarding, retention and purchase (`growth-loop` skill).

End with the three most valuable next steps and which ShipPilot command or skill handles each.
