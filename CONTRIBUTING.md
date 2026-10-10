# Contributing

Issues and pull requests are welcome — especially reports from real releases ("this step failed on my project
because…").

- **Commands, checker, templates, docs:** edit them here. Run `python3 -m unittest discover -s tests` and, if you
  touched the demo, `python3 docs/make_demo.py` (needs Pillow and ffmpeg).
- **Skills (`skills/`):** generated from [SUPER_COMPUTER_AI](https://github.com/ufukyuksel-dev/SUPER_COMPUTER_AI).
  Open the change there (or open an issue here describing it); a re-export updates this repository:

  ```sh
  # from a SUPER_COMPUTER_AI checkout
  python3 scripts/export_plugin.py --out <path-to-shippilot> --deny <private-project-name> \
    --skill mobile-store-release --skill store-listing-assets --skill mobile-ui-review \
    --skill google-ads-management --skill meta-ads-management --skill tiktok-ads-management --skill growth-loop
  ```

- Never commit credentials, account IDs or machine-specific paths. Examples use made-up apps.
- Keep the approval gates: a change that lets the plugin upload, publish or spend without an explicit user decision
  will not be merged.

## README media

`python3 docs/make_demo.py` renders the motion demo, the flow graphic, the social preview and the icon
(`--real-run-repo <app repo>` adds the real-run clip). GIFs and PNGs go to `docs/assets/`; MP4s go to `build/` and
are attached to the GitHub release (`gh release upload <tag> build/*.mp4`), not committed. When media change, bump
`MEDIA_VERSION` and the README image paths together, because GitHub caches images by URL.
