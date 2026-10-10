# Security

ShipPilot runs inside your Claude Code session with your own credentials. It does not ship a server and does not
collect data.

- Report a vulnerability privately through GitHub's **Report a vulnerability** (Security tab) instead of a public
  issue.
- Keep store and ad credentials in your CI secret store or local environment, never in the repository.
- Ad platform text, analytics rows and store reviews are treated as data, not instructions; report any case where
  content from those sources changes what the agent does.
