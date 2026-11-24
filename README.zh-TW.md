# personal-mcp-for-garmin

**非官方、唯讀的 MCP server，讓 Claude 讀取你自己的 Garmin Connect™ 資料。**
使用 Garmin 官方 [Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/)，
可以問 Claude 你的睡眠、HRV、Body Battery、跑步紀錄等。

[English](README.md)

> [!IMPORTANT]
> **本專案與 Garmin 無關，亦未獲其背書。** 你需要自己的 Garmin Personal API key，使用方式受 Garmin 條款約束：
> key 只能自己用、絕不可分享，Garmin 也可能限流或撤銷 key。
> 開始前請先閱讀 [Garmin 條款摘要（轉述自 Garmin）](GARMIN_TERMS.md)。

- **自備 key：** 在你的電腦上執行，只連線到 Garmin；沒有共用伺服器，也不收集任何使用數據。
- **唯讀：** 23 個工具，都不會改動你 Garmin 帳號裡的任何東西。
- **標示來源：** 依 Garmin API 品牌規範，每筆結果都標示 `data_source: "Garmin"`。
- **依賴極少：** Garmin 連線只用 Python 標準函式庫，唯一的套件是 MCP Python SDK。

## 1. 產生 Personal API key

1. 登入 Garmin Connect 網頁版，打開 [Personal API Key](https://connect.garmin.com/app/settings/personalApiToken)。
2. 按 **Create Key**，同意條款，選效期（30／90／180 天或 1 年），再按 **Create**。
3. 複製 key。key 只會顯示一次；到期前約一週 Garmin 會寄信提醒。

## 2. 安裝

每種方式都需要先安裝 [uv](https://docs.astral.sh/uv/)（`curl -LsSf https://astral.sh/uv/install.sh | sh`）。

> [!CAUTION]
> 不要把 key 貼到跟 Claude 或任何 AI 的對話裡，只在下面指定的地方輸入。

### 方式 A：Claude Code plugin（建議）

在 Claude Code 裡輸入：

```
/plugin marketplace add jojomango/personal-mcp-for-garmin
/plugin install personal-mcp-for-garmin@jojomango
```

Claude Code 會用遮罩欄位詢問 key，並存在它的安全憑證儲存區，不會寫進任何設定檔。
之後要更換 key：打開 `/plugin`，選這個 plugin，再選 **Configure**。

### 方式 B：Codex、Claude Desktop 或其他 MCP 用戶端

先在你自己的 Terminal 存一次 key（輸入時不顯示；先向 Garmin 驗證，成功後才存到
`~/.config/personal-mcp-for-garmin/`，權限 600）：

```bash
uvx --from personal-mcp-for-garmin personal-mcp-for-garmin-setup
```

**Codex CLI：**

```bash
codex mcp add garmin -- uvx personal-mcp-for-garmin
```

**Claude Desktop**（`claude_desktop_config.json`）：

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

以上設定都不含你的 key。

### 方式 C：Claude Desktop 擴充套件檔

到 [Releases](https://github.com/jojomango/personal-mcp-for-garmin/releases) 頁面下載 `.mcpb` 檔，
用 Claude Desktop 開啟。它會詢問 key，並存在作業系統的安全儲存區。

接著試試：「我這週睡得怎麼樣？」或「比較我最近三次跑步的心率」。

## 工具

| 工具 | 內容 |
|---|---|
| `daily_summary` | 步數、卡路里、靜止心率、壓力、Body Battery、強度分鐘（單日或區間） |
| `sleep` | 睡眠分期與分數（單晚或區間） |
| `heart_rate` | 單日全天心率 |
| `hrv` | HRV 狀態與基準（單日或區間） |
| `body_battery`、`stress`、`steps`、`hydration` | 區間每日統計 |
| `spo2_acclimation` | 血氧與高海拔適應 |
| `weight`、`weight_goal` | 體重、體組成與目標 |
| `vo2max`、`fitness_age`、`heart_rate_zones` | 體能指標 |
| `nutrition` | 飲食紀錄 |
| `menstrual_cycle` | 月經週期摘要或當日詳情 |
| `user_settings` | 單位、個人資料、睡眠時間 |
| `activities` | 搜尋運動紀錄；精簡模式含配速、心率區間、步頻、步幅 |
| `activity_detail`、`activity_workouts` | 單筆運動詳情 |
| `activity_summary_range` | 健康活動（如呼吸練習，不是運動統計） |
| `activity_types` | 可用的運動類型代碼 |
| `download_activity_file` | 下載原始 FIT 檔到 `~/Downloads/garmin` |

日期參數接受 `YYYY-MM-DD`、`today` 或 `yesterday`。訓練準備度、訓練狀態、呼吸頻率不在 Personal API 範圍內，所以沒有提供。

## 設定

| 環境變數 | 預設值 | 用途 |
|---|---|---|
| `GARMIN_API_KEY` | — | 改用這把 key，不讀存檔 |
| `GARMIN_REGION` | `global` | 中國大陸區（garmin.cn）帳號設為 `cn` |
| `GARMIN_CACHE_TTL` | `300` | 相同查詢重複使用結果的秒數（0 為關閉） |
| `GARMIN_DOWNLOAD_DIR` | `~/Downloads/garmin` | FIT 檔下載位置 |
| `GARMIN_MCP_CONFIG_DIR` | `~/.config/personal-mcp-for-garmin` | 設定指令存放 key 的位置 |

## 安全與隱私

- key 永遠不會進到這個 repo。如果不小心外流，請立刻到 Garmin Connect 刪除，所有由它發出的 token 會立即失效。
- 資料只在 Garmin 和你的電腦之間傳輸，再交給你選擇的 MCP 用戶端。詳見 [PRIVACY.md](PRIVACY.md)。

## 開發

```bash
uv run python -m unittest discover -s tests   # 用模擬的 Garmin API 跑離線測試
npx @anthropic-ai/mcpb pack                    # 打包桌面擴充套件（.mcpb）
claude plugin validate --strict .              # 檢查 Claude Code plugin 設定
```

要執行本機程式碼而不是已發布的套件：先用 `uv run personal-mcp-for-garmin-setup` 存 key，再執行
`claude mcp add garmin --scope user -- uv run --directory "$PWD" personal-mcp-for-garmin`。

發布新版：更新 `pyproject.toml`、`src/personal_mcp_for_garmin/__init__.py`、`manifest.json`
和 `.claude-plugin/plugin.json` 的版本號（包含 `uvx` 固定的版本，測試會檢查是否一致），
再推送 `vX.Y.Z` tag，GitHub Actions 就會用 Trusted Publishing 發布到 PyPI。

## 授權

[MIT](LICENSE)。Garmin、Garmin Connect 與 Body Battery 為 Garmin Ltd. 或其子公司之商標。本專案與 Garmin 無關，亦未獲其背書。
