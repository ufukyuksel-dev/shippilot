---
description: Localize store listing text into new locales locally, validate limits, show the diff (no upload)
argument-hint: "<locales, e.g. de-DE fr-FR tr>"
---

Localize this app's store listing into: $ARGUMENTS

Rules:
- Read the existing source-locale metadata in `fastlane/metadata/<locale>/` (iOS) and `fastlane/metadata/android/<locale>/` (Android) and the app itself (README, strings, screens) so the copy describes what the app really does. Do not invent features, awards or prices.
- Write only to local files under `fastlane/metadata`. Never run `deliver`, `supply` or any upload in this command; publishing store text changes the live store page and is a separate, explicitly approved step (see the `mobile-store-release` skill).
- Adapt keywords per market instead of translating them word for word; iOS keywords are comma-separated, no spaces after commas, max 100 bytes.
- Preserve every existing locale and field you were not asked to change.

Then run:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_metadata.py" --platform ios` and `--platform android` (for the platforms present) and fix every FAIL.

Finish with `git diff --stat -- fastlane/metadata`, the checker output, and a short list of wording choices the user should review.
