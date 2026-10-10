---
description: Audit any app's public App Store / Google Play listing - no store account, API key or Fastlane needed
argument-hint: "<App Store or Google Play URL> [more URLs]"
---

Audit the public store listing(s): $ARGUMENTS

## 1. Fetch the data (do not guess it)

For each URL run:

`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_listing.py" "<url>"`

Exit code 2 means the URL is unsupported, the app was not found or the network failed: report that and stop for
that URL. Use only the JSON that comes back. Every field in `missing` is **unknown**: say so, do not infer it.
In particular:
- App Store: `subtitle`, `keywords`, `promotional_text` and in-app purchases are not in Apple's Lookup API.
- Google Play: `meta_description` is the page's short meta summary, **not** the full store description or the
  short description field. Do not judge the full description from it.
- Screenshots: only counts are known (App Store) or nothing (Google Play). Do not critique the images; propose a
  screenshot story instead.

## 2. Write the report

Write `shippilot-audit-<app-name>-<YYYY-MM-DD>.md` in the current directory with these sections:

1. **Source** — input URL(s), API/page URL(s) from `source`, `fetched_at_utc`, region, and the list of missing fields.
2. **What the listing promises** — what the name and the first lines of the available text promise a new user, in
   two or three sentences. Quote the text you are judging.
3. **Length check** — the `lengths` entries as a table (field, length, limit, unit, over?). Limits come from the
   fetcher, which uses the same table as `check-metadata`.
4. **Quick wins** — at most five concrete, specific changes, each tied to text you actually saw.
5. **Drafts per platform**, each within its own platform's fields and limits:
   - iOS: `name` (30 chars), `subtitle` (30 chars), `keywords` (100 bytes, comma-separated, no spaces after commas,
     no words already in the name), `promotional_text` (170 chars).
   - Android: `title` (30 chars), `short_description` (80 chars).
   Provide them in English plus up to four more languages that fit the app's market (state why). Show the length
   of every draft next to it. Do not translate keywords literally; adapt them per market.
6. **Screenshot story** — 5 frames: the message of each frame and which real screen it should show.
7. **Three ad angles** — headline + one line + which first screen the ad should open, so the ad promise matches the
   first session.
8. **Next step with ShipPilot** — how this app would continue in the loop (`/shippilot:localize`,
   `/shippilot:ad-creatives`, `/shippilot:beta`, `/shippilot:grow`).

Rules: never invent features, ratings, awards, download numbers or prices that are not in the fetched data. Be
neutral and factual about apps that are not the user's own. Do not upload, publish or change anything.

Finish with a three-line summary in the chat and the path of the report.
