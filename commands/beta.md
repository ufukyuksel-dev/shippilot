---
description: Upload a beta build (TestFlight / Play internal) after explicit confirmation
argument-hint: "[ios|android|both]"
---

Prepare a beta upload for: ${ARGUMENTS:-both}

Use the `mobile-store-release` skill. Steps:
1. Discover the actual Fastlane lanes, variants/schemes, version and build-number source. Do not assume lane names.
2. Show a plan: platform, lane, version, build number, commit SHA, destination (TestFlight or Play internal track). Upload the beta build only; do not upload store metadata or submit for review.
3. Wait for the user's explicit confirmation of that plan before running any upload.
4. After the upload, verify the exact build in TestFlight / Play internal and report build ID, status and anything still processing. A finished command is not proof the build is available.
