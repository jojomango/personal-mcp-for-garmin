# connect-personal-mcp

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

### 方式 A：Claude Desktop 擴充套件（一鍵安裝）

安裝 `connect-personal-mcp` 擴充套件，在擴充套件設定裡貼上 key；key 會存在作業系統的安全儲存區。
*（上架審核中；在那之前可以到 Releases 頁面下載 `.mcpb` 檔，用 Claude Desktop 開啟。）*

### 方式 B：從原始碼安裝（Claude Code、Claude Desktop 或任何 MCP 用戶端）

需要先安裝 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/jojomango/connect-personal-mcp.git
cd connect-personal-mcp
uv run connect-personal-mcp-setup     # 貼上 key：先向 Garmin 驗證，成功才存到 repo 之外
```

**Claude Code：**

```bash
claude mcp add garmin --scope user -- uv run --directory "$PWD" connect-personal-mcp
```

請用 `--scope user`，設定才會存在你的家目錄，不會進到 repo 裡。

**Claude Desktop**（`claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uv",
      "args": ["run", "--directory", "/絕對路徑/connect-personal-mcp", "connect-personal-mcp"]
    }
  }
}
```

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
| `GARMIN_MCP_CONFIG_DIR` | `~/.config/connect-personal-mcp` | 設定指令存放 key 的位置 |

## 安全與隱私

- key 永遠不會進到這個 repo。如果不小心外流，請立刻到 Garmin Connect 刪除，所有由它發出的 token 會立即失效。
- 資料只在 Garmin 和你的電腦之間傳輸，再交給你選擇的 MCP 用戶端。詳見 [PRIVACY.md](PRIVACY.md)。

## 開發

```bash
uv run python -m unittest discover -s tests   # 用模擬的 Garmin API 跑離線測試
npx @anthropic-ai/mcpb pack                    # 打包桌面擴充套件（.mcpb）
```

## 授權

[MIT](LICENSE)。Garmin、Garmin Connect 與 Body Battery 為 Garmin Ltd. 或其子公司之商標。本專案與 Garmin 無關，亦未獲其背書。
