# Garmin Personal API terms: summary · Garmin Personal API 條款摘要

> **Paraphrased from Garmin. Not Garmin's official text and not legal advice.**
> The binding terms are the *Personal API Supplemental Terms* that Garmin shows when you create a
> key at [Garmin Connect → Personal API Key](https://connect.garmin.com/app/settings/personalApiToken),
> together with the [Garmin Terms of Use](https://www.garmin.com/en-US/legal/terms-of-use/) they refer to.
> Garmin can change them at any time; read the current version yourself. Summary written in November 2026.
>
> **以下內容轉述自 Garmin，並非 Garmin 官方原文，也不構成法律意見。**
> 具約束力的是你在 [Garmin Connect 產生 Personal API key](https://connect.garmin.com/app/settings/personalApiToken)
> 時 Garmin 顯示的《Personal API 補充條款》，以及其引用的 [Garmin 使用條款](https://www.garmin.com/en-US/legal/terms-of-use/)。
> Garmin 可隨時修改條款，請自行閱讀最新版本。本摘要撰寫於 2026 年 11 月。

---

## English

### Key points (paraphrased from Garmin's Personal API Supplemental Terms)

1. **The key is for your own use only.** Your Personal API key may only be used with applications,
   services or tools that you develop or operate yourself. It may not be sold, transferred, licensed,
   distributed, disclosed or shared with any third party.
2. **Rate limits.** Garmin may set and enforce limits on the number, frequency or volume of your API
   requests, and may throttle, delay, deny, suspend or restrict requests without prior notice.
3. **Consequences of a violation.** Breaking the terms can lead to suspension or termination of your
   API access and revocation of your API key.

Garmin's [Personal API FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq/)
also states that the Personal API is intended for individual Garmin users who want programmatic access
to their own data, and *"is not intended for commercial applications serving multiple end users."*

### What this means for this project

- **Bring your own key.** This project ships no key and runs no shared server. Each user creates their
  own key and runs the server on their own computer, so it is a tool *you* operate.
- **Never share your key.** Don't paste it into issues or chats, and don't commit it. The setup command
  stores it outside the repository (`~/.config/personal-mcp-for-garmin/`, permissions 600); the desktop
  extension stores it in your operating system's secure storage.
- **Don't turn this into a hosted service.** Running it as a server that holds other people's keys
  would conflict with the terms above. Multi-user services need Garmin's business developer program.
- **Be gentle with the API.** Identical requests within 5 minutes reuse the cached result
  (`GARMIN_CACHE_TTL`), and the server never polls on its own.
- **Your data goes where you send it.** Results go to the MCP client you connect (for example
  Claude), and from there to that client's AI provider under its own terms.
- **Attribution.** Following Garmin's
  [API Brand Guidelines](https://developer.garmin.com/brand-guidelines/overview/), every result is
  labelled `data_source: "Garmin"`, and the server asks the AI to name Garmin as the source when it
  presents or analyses the data.

---

## 繁體中文

### 重點（轉述自 Garmin《Personal API 補充條款》）

1. **key 只能自己用：** Personal API key 只能用於你自己開發或操作的應用程式、服務或工具；
   不可出售、轉讓、授權、散布、揭露或分享給任何第三方。
2. **流量限制：** Garmin 可以設定並執行 API 請求的次數、頻率或數量上限，
   而且可以不事先通知就限流、延遲、拒絕、暫停或限制你的請求。
3. **違規後果：** 違反條款可能導致 API 存取權被停權或終止，並撤銷你的 API key。

Garmin 的 [Personal API FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq/)
也說明：Personal API 是給想用程式存取**自己**資料的個人 Garmin 使用者，
「不適用於服務多位終端使用者的商業應用程式」。

### 對本專案的意義

- **自備 key：** 本專案不附任何 key，也不架設共用伺服器。每位使用者自己產生 key、
  在自己的電腦上執行，所以這是「你自己操作的工具」。
- **絕不分享 key：** 不要貼到 issue 或聊天裡，也不要 commit。設定指令會把 key 存在 repo 之外
  （`~/.config/personal-mcp-for-garmin/`，權限 600）；桌面擴充套件則存在作業系統的安全儲存區。
- **不要改成雲端服務：** 若架成保管別人 key 的伺服器，會違反上述條款。
  多使用者服務需要申請 Garmin 的企業開發者方案。
- **溫和使用 API：** 5 分鐘內的相同請求會直接用快取結果（`GARMIN_CACHE_TTL`），
  server 也不會自行輪詢。
- **資料去向由你決定：** 查詢結果會傳給你連接的 MCP 用戶端（例如 Claude），
  再依該用戶端的條款傳給其 AI 服務商。
- **來源標示：** 依 Garmin 的 [API 品牌規範](https://developer.garmin.com/brand-guidelines/overview/)，
  每筆結果都標示 `data_source: "Garmin"`，server 也會要求 AI 在呈現或分析資料時註明來源為 Garmin。

---

Garmin, Garmin Connect and Body Battery are trademarks of Garmin Ltd. or its subsidiaries.
This project is not affiliated with or endorsed by Garmin.
Garmin、Garmin Connect 與 Body Battery 為 Garmin Ltd. 或其子公司之商標。本專案與 Garmin 無關，亦未獲其背書。
