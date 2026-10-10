# Privacy

ShipPilot is a Claude Code plugin made of instructions (skills and commands) and small local scripts. It has no
server, no account, no telemetry and no analytics. MB Worldwide Apps receives no data from your use of it.

What it touches is listed in the README section "What ShipPilot runs and connects to". In short:

- `scripts/check_metadata.py` reads local files only.
- `scripts/fetch_listing.py` requests public pages: Apple's iTunes Lookup API (`itunes.apple.com`) and the public
  Google Play app page (`play.google.com`). It sends the app id and region in the request, nothing else.
- Store, ad and analytics actions go through tools and credentials **you** configure (Fastlane, MCP servers, CI
  secrets). Their data handling is governed by those providers and by your Claude Code setup.

Contact: business@mbworldwideapps.com
