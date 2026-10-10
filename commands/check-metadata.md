---
description: Validate Fastlane store metadata against App Store / Google Play length limits
argument-hint: "[ios|android] [metadata dir]"
---

Run the ShipPilot metadata checker for this project and explain the result.

- iOS: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_metadata.py" --platform ios --metadata fastlane/metadata`
- Android: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_metadata.py" --platform android --metadata fastlane/metadata/android`

Arguments given: $ARGUMENTS (default: every platform whose metadata directory exists). Exit code 0 = all within limits, 1 = violations (list them with the overflow), 2 = nothing was checked (say why; this is not a pass). Offer shorter wording for each violation but do not edit files unless the user asks.
