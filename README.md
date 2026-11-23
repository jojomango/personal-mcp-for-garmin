# connect-personal-mcp

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

### Option A: Claude Desktop extension (one click)

Install the `connect-personal-mcp` extension, then paste your key into the extension's settings. The
key is kept in your operating system's secure storage. *(Directory listing pending; until then,
download the `.mcpb` file from the Releases page and open it with Claude Desktop.)*

### Option B: from source (Claude Code, Claude Desktop or any MCP client)

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/jojomango/connect-personal-mcp.git
cd connect-personal-mcp
uv run connect-personal-mcp-setup     # paste your key; it is verified, then saved outside the repo
```

**Claude Code:**

```bash
claude mcp add garmin --scope user -- uv run --directory "$PWD" connect-personal-mcp
```

Use `--scope user` so the configuration lives in your home directory, not in the repository.

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/connect-personal-mcp", "connect-personal-mcp"]
    }
  }
}
```

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
| `GARMIN_MCP_CONFIG_DIR` | `~/.config/connect-personal-mcp` | Where the setup command stores the key |

## Security and privacy

- Your key never enters this repository. If you ever expose it, delete it on Garmin Connect at once:
  every token issued from it stops working immediately.
- Data flows only between Garmin and your computer, then to the MCP client you choose. See
  [PRIVACY.md](PRIVACY.md).

## Development

```bash
uv run python -m unittest discover -s tests   # offline tests against a mock Garmin API
npx @anthropic-ai/mcpb pack                    # build the desktop extension (.mcpb)
```

## License

[MIT](LICENSE). Garmin, Garmin Connect and Body Battery are trademarks of Garmin Ltd. or its
subsidiaries. This project is not affiliated with or endorsed by Garmin.
