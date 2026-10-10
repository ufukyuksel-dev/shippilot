---
description: Draft ad headlines, descriptions and a creative brief from what the app really does (local file only)
argument-hint: "[platforms, e.g. google meta tiktok] [locales]"
---

Draft ad copy and a creative brief for this app. Arguments: ${ARGUMENTS:-google meta tiktok, source locale}

Rules:
- Base every claim on the app itself: README, store metadata in `fastlane/metadata`, strings, screens and recent changes. Do not invent features, ratings, awards, prices or user numbers. If the store listing and the code disagree, say so.
- Respect each platform's current text limits; check the official ad specs for the platforms requested (for example Google Ads App campaign headlines and descriptions, Meta primary text and headline, TikTok ad text) and state the limit you used next to each field. Mark any limit you could not verify.
- Write 3 distinct angles (for example: the core loop, a concrete feature, a use moment), each with headlines, descriptions and one line on which in-app screen should open after install, so the ad promise matches the first session.
- For visuals write a creative brief per angle (format 9:16 / 1:1 / 16:9, what is on screen, which real app screen to capture, text overlay). Do not generate or upload media here; the `store-listing-assets` skill covers visual production.

Write the result to `ads/creatives/<YYYY-MM-DD>.md` (create the folder if needed) and show a short summary. Never upload, create ads or change campaigns in this command; publishing creatives is an ad mutation and goes through the ad skills' preview -> approval -> read-back flow.
