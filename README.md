# personal-mcp-for-garmin

**An unofficial, read-only MCP server for your own Garmin Connect™ data**, built on Garmin's
official [Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/).
Ask Claude (or any MCP client) about your sleep, HRV, Body Battery, runs and more.

[繁體中文說明](README.zh-TW.md)

> [!IMPORTANT]
> **Not affiliated with or endorsed by Garmin.** You need your own Garmin Personal API key, and its
> use is governed by Garmin's terms: the key is for your own use only, must never be shared, and
> Garmin may rate-limit or revoke it. Read the [Garmin terms summary (paraphrased from Garmin)](GARMIN_TERMS.md)
> before you start.

- **Bring your own key.** Runs on your computer and talks only to Garmin. No shared server, no telemetry.
- **Read-only.** 23 tools, none of which change anything in your Garmin account.
- **Attributed.** Every result is labelled `data_source: "Garmin"`, per Garmin's API Brand Guidelines.
- **Standard library only** for the Garmin client; the single dependency is the MCP Python SDK.

## 1. Create your Personal API key

1. Sign in to Garmin Connect on the web and open
   [Personal API Key](https://connect.garmin.com/app/settings/personalApiToken).
2. Select **Create Key**, accept the terms, choose an expiry (30, 90 or 180 days, or 1 year) and **Create**.
3. Copy the key. Garmin shows it only once. Garmin emails you about a week before it expires.

## 2. Install

All options need [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

> [!CAUTION]
> Never paste your key into a chat with Claude or any other AI. Enter it only in the places below.

### Option A: Claude Code plugin (recommended)

In Claude Code:

```
/plugin marketplace add jojomango/personal-mcp-for-garmin
/plugin install personal-mcp-for-garmin@jojomango
```

Claude Code asks for your key in a masked field and keeps it in its secure credential store, not in
any settings file. To change it later, open `/plugin`, select the plugin and choose **Configure**.

### Option B: Codex, Claude Desktop or any other MCP client

Save your key once, in your own terminal (input is hidden; the key is verified with Garmin, then
saved to `~/.config/personal-mcp-for-garmin/` with permissions 600):

```bash
uvx --from personal-mcp-for-garmin personal-mcp-for-garmin-setup
```

**Codex CLI:**

```bash
codex mcp add garmin -- uvx personal-mcp-for-garmin
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uvx",
      "args": ["personal-mcp-for-garmin"]
    }
  }
}
```

None of these configurations contain your key.

### Option C: Claude Desktop extension file

Download the `.mcpb` file from the [Releases](https://github.com/jojomango/personal-mcp-for-garmin/releases)
page and open it with Claude Desktop. It asks for your key and keeps it in your operating system's
secure storage.

Then try: *"How did I sleep this week?"* or *"Compare the heart rate of my last three runs."*

## Tools

| Tool | Data |
|---|---|
| `daily_summary` | Steps, calories, resting HR, stress, Body Battery, intensity minutes (one day or a range) |
| `sleep` | Sleep stages and score (one night or a range) |
| `heart_rate` | All-day heart rate for one day |
| `hrv` | HRV status and baseline (one day or a range) |
| `body_battery`, `stress`, `steps`, `hydration` | Daily statistics for a range |
| `spo2_acclimation` | Pulse Ox and altitude acclimation |
| `weight`, `weight_goal` | Weight, body composition and goals |
| `vo2max`, `fitness_age`, `heart_rate_zones` | Fitness metrics |
| `nutrition` | Food log |
| `menstrual_cycle` | Cycle summary or day view |
| `user_settings` | Units, profile and sleep schedule |
| `activities` | Search workouts, with pace, HR zones, cadence and stride in compact mode |
| `activity_detail`, `activity_workouts` | One workout in detail |
| `activity_summary_range` | Wellness activities such as breathwork (not workouts) |
| `activity_types` | Valid activity type keys |
| `download_activity_file` | Save the original FIT file to `~/Downloads/garmin` |

Dates accept `YYYY-MM-DD`, `today` or `yesterday`. Training readiness, training status and
respiration are not available in the Personal API, so they are not included.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GARMIN_API_KEY` | — | Use this key instead of the saved file |
| `GARMIN_REGION` | `global` | Set to `cn` for China-region (garmin.cn) accounts |
| `GARMIN_CACHE_TTL` | `300` | Seconds to reuse identical results (0 disables) |
| `GARMIN_DOWNLOAD_DIR` | `~/Downloads/garmin` | Where `download_activity_file` saves files |
| `GARMIN_MCP_CONFIG_DIR` | `~/.config/personal-mcp-for-garmin` | Where the setup command stores the key |

## What the plugin runs and connects to

- **Starts:** `uvx personal-mcp-for-garmin==<version>`, pinned to the exact version in
  `.claude-plugin/plugin.json`. The first time, uv downloads that package and its dependencies
  (the MCP Python SDK) from **PyPI** and caches them; this source code is what gets published there.
- **Connects to:** only Garmin's Personal API (`personal.connectapi.garmin.com`, or
  `personal.connectapi.garmin.cn` for China-region accounts), and only when a tool is called. It
  exchanges your key for an access token, then reads your data. Nothing runs in the background.
- **Writes:** nothing, except that `download_activity_file` saves FIT files to `~/Downloads/garmin`
  (or `GARMIN_DOWNLOAD_DIR`). Results are cached in memory for 5 minutes.
- **Never:** sends data anywhere else, collects analytics or telemetry, changes your Garmin account,
  or changes Claude's settings or permissions.

## Security and privacy

- Your key never enters this repository. If you ever expose it, delete it on Garmin Connect at once:
  every token issued from it stops working immediately.
- Data flows only between Garmin and your computer, then to the MCP client you choose. See
  [PRIVACY.md](PRIVACY.md).

## Development

```bash
uv run python -m unittest discover -s tests   # offline tests against a mock Garmin API
npx @anthropic-ai/mcpb pack                    # build the desktop extension (.mcpb)
claude plugin validate --strict .              # check the Claude Code plugin manifest
```

To run your local checkout instead of the released package, save a key with
`uv run personal-mcp-for-garmin-setup`, then
`claude mcp add garmin --scope user -- uv run --directory "$PWD" personal-mcp-for-garmin`.

Releases: bump the version in `pyproject.toml`, `src/personal_mcp_for_garmin/__init__.py`,
`manifest.json` and `.claude-plugin/plugin.json` (including the pinned `uvx` version; a test checks
they match), then push a `vX.Y.Z` tag. GitHub Actions publishes to PyPI with Trusted Publishing.

## License

[MIT](LICENSE). Garmin, Garmin Connect and Body Battery are trademarks of Garmin Ltd. or its
subsidiaries. This project is not affiliated with or endorsed by Garmin.
