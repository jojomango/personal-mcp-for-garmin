# Privacy Policy

_Last updated: 2026-11-23_

connect-personal-mcp is software that runs **on your own computer**. The author does not operate
any server for it and does not receive, store or see your data or your API key.

## What the software accesses

- **Your Garmin Personal API key**, which you provide. It is stored locally: in
  `~/.config/connect-personal-mcp/personal_api_key` (file permissions 600) when you use the setup
  command, or in your operating system's secure storage when you use the desktop extension.
- **Your own Garmin Connect data** (health, sleep, activity and related data), read-only, only when
  your MCP client calls one of the tools.

## Where data goes

- **Garmin:** the software connects only to Garmin's Personal API hosts
  (`personal.connectapi.garmin.com`, or `personal.connectapi.garmin.cn` for China-region accounts) to
  exchange your key for an access token and to read your data.
- **Your MCP client:** tool results are returned to the MCP client you connected (for example Claude).
  That client, and the AI provider behind it, handle the data under their own privacy policies.
- **Local files:** `download_activity_file` saves activity files to `~/Downloads/garmin` (or
  `GARMIN_DOWNLOAD_DIR`). Results are cached in memory for up to 5 minutes and discarded when the
  server stops.
- **Nothing else.** No analytics, telemetry or third-party services.

## Your control

- Delete your key at any time on Garmin Connect; every token issued from it stops working immediately.
- Remove the local key file, or uninstall the extension, to remove the stored key.

## Contact

Open an issue in this project's GitHub repository. Never include your API key or personal health
data in an issue.
