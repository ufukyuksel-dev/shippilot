<div align="center">

# ShipPilot

**Build, ship and grow mobile apps with Claude Code.**

A Claude Code plugin that turns the release and growth work around a mobile app — Fastlane releases, store listings,
Android device QA, Google / Meta / TikTok ads and a measured growth loop — into skills and commands you can run from
your own repository, with every risky step behind an explicit approval.

[![CI](https://github.com/ufukyuksel-dev/shippilot/actions/workflows/ci.yml/badge.svg)](https://github.com/ufukyuksel-dev/shippilot/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-22d3ee)

[English](README.md) · [Türkçe](README.tr.md)

<img src="docs/assets/demo.gif" alt="ShipPilot demo: install, commands and real metadata checker output" width="800">

<sub>28-second demo · [MP4 version](docs/assets/demo.mp4) · terminal scenes show real output, rendered by
[`docs/make_demo.py`](docs/make_demo.py)</sub>

</div>

## Why

Writing the app is no longer the hard part. Getting it through signing, TestFlight and Play tracks, writing a store
listing in ten languages that fits every character limit, testing on a real device, spending ad money carefully and
then finding out *why* users leave — that is where solo developers and small studios lose weeks.

We are a small studio. We shipped our word game **Wordfall** to the App Store and Google Play with Claude Code and
these workflows. ShipPilot is those workflows, cleaned of our private setup and published so anyone can use them.

## The loop

<img src="docs/assets/loop.svg" alt="Build, Ship, Grow, Measure, Improve" width="800">

ShipPilot is not an autopilot that spends your money. Claude does the reading, checking, drafting and preparing;
**you** approve every upload, every store-text publish and every ad change.

## Install

In Claude Code:

```text
/plugin marketplace add ufukyuksel-dev/shippilot
/plugin install shippilot@shippilot
```

Then, inside your app repository:

```text
/shippilot:launch-check
```

## Commands

| Command | What it does | Changes anything? |
|---|---|---|
| `/shippilot:launch-check` | Readiness report: Fastlane lanes, metadata, device QA, ads and analytics connections | No |
| `/shippilot:localize <locales>` | Writes localized store text to `fastlane/metadata`, validates limits, shows the diff | Local files only |
| `/shippilot:check-metadata` | Checks App Store / Google Play length limits | No |
| `/shippilot:beta [ios\|android\|both]` | Plans a beta upload (TestFlight / Play internal), uploads after you confirm | After approval |
| `/shippilot:ads-report [period]` | Spend, installs and cost per install across connected ad accounts | No |
| `/shippilot:grow <question>` | Baseline → one hypothesis → one change → stops at the approval gate | After approval |

## Skills and what they need

Skills load automatically when a task matches. A skill is knowledge and procedure; it does not grant access. When a
requirement is missing, the skill says exactly what is missing and stops at that step instead of guessing.

| Skill | Needs | If missing |
|---|---|---|
| `mobile-store-release` | Fastlane + Bundler; Xcode on macOS for iOS; App Store Connect API key and/or Play service account | Reports the missing lane, tool or credential; never prints key contents |
| `store-listing-assets` | Your existing ASO/screenshot design source; an image model for raster artwork (optional) | Works on text and inventory only |
| `mobile-ui-review` | [`adb` MCP server](https://github.com/ufukyuksel-dev/SUPER_COMPUTER_AI/tree/main/mcp/servers/adb) + an Android device or emulator | Asks you to connect the server; does not fall back to raw `adb` |
| `google-ads-management` | [`google-ads` MCP server](https://github.com/ufukyuksel-dev/SUPER_COMPUTER_AI/tree/main/mcp/servers/google-ads) with your own credentials | Read-only planning; no mutations |
| `meta-ads-management` | [Official Meta Ads MCP](https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-overview) | Lists the setup steps |
| `tiktok-ads-management` | [TikTok API for Business](https://business-api.tiktok.com/portal) app, scopes and an MCP/adapter | Reports which prerequisite is missing |
| `growth-loop` | An analytics source with real events (Firebase/GA4 export, your own events table, store consoles) + optional ad data | Does the parts the data allows; never reports guesses as findings |

## Safety rules built in

- **Approval gates:** uploads, publishing store text, review submission and every ad mutation (budget, status,
  targeting, creation) require your explicit decision. Ad changes use preview → apply → read-back.
- **Beta is not metadata:** `/shippilot:beta` uploads binaries only. Store text changes the *live* store page and
  is a separate step.
- **No secrets in output:** credentials are checked for presence, never printed, committed or logged.
- **Measured, not claimed:** the growth loop reports sample sizes and "not yet measurable" instead of declaring wins;
  correlation is labelled as correlation.

## Metadata checker

Also usable without Claude, in CI or a pre-commit hook (Python 3.9+, no dependencies):

```sh
python3 scripts/check_metadata.py --platform ios     --metadata fastlane/metadata
python3 scripts/check_metadata.py --platform android --metadata fastlane/metadata/android
```

| Platform | Field (file) | Limit |
|---|---|---|
| iOS | `name`, `subtitle` | 30 characters |
| iOS | `keywords` | 100 **bytes** (UTF-8) |
| iOS | `promotional_text` | 170 characters |
| iOS | `description`, `release_notes` | 4000 characters |
| Android | `title` | 30 characters |
| Android | `short_description` | 80 characters |
| Android | `full_description` | 4000 characters |
| Android | `changelogs/*.txt` | 500 characters |

Exit code `0` = within limits, `1` = violations, `2` = nothing was checked (missing directory, no locale, no
recognised file) — an empty run never passes silently. Limits are from Apple's
[App Store Connect reference](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information)
and Google's [Play Console help](https://support.google.com/googleplay/android-developer/answer/9859152).

A starting point for the beta lanes is in [`templates/Fastfile.example`](templates/Fastfile.example).

## Status

**v0.1 — early.** What exists today: the skills, the commands, the metadata checker and its tests. What does not
exist yet: a hosted service, automatic attribution between ad platforms and in-app analytics, or any autonomous
spending. Feedback from people shipping real apps decides what comes next.

Roadmap: App Review rejection analysis · screenshot localization pipeline · analytics adapters (Firebase/GA4) for the
growth loop · iOS device QA.

## How this repository is built

The skills in [`skills/`](skills) are generated, not hand-edited here. Their single source is
[SUPER_COMPUTER_AI](https://github.com/ufukyuksel-dev/SUPER_COMPUTER_AI), where project-specific content is marked
private and removed by `scripts/export_plugin.py`, which also refuses to export home paths, secret-like strings or
denied project names. Commands, the checker, templates and docs live here. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © MB Worldwide Apps · [mbworldwideapps.com](https://mbworldwideapps.com)
