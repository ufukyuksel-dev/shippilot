---
description: Read-only ad performance report across connected Google Ads, Meta and TikTok accounts
argument-hint: "[period, e.g. last 7 days]"
---

Build a read-only ad report for ${ARGUMENTS:-the last 7 days}.

Use the `google-ads-management`, `meta-ads-management` and `tiktok-ads-management` skills for whichever platforms have tools connected in this session; list unconnected platforms instead of guessing. Never call a mutation, preview or apply tool in this command.

Per platform and campaign: spend, impressions, installs (or the configured conversion), cost per install, with currency and account timezone stated. Do not mix different conversion events, and mark totals from truncated reads as incomplete. End with observations labelled as observations (not causes) and suggest `/shippilot:grow` for any question worth testing.
