# web_agent — 自動回覆 Agent

台大升學論壇（pei.com.tw）的自動巡邏 & 回覆機器人。使用 Playwright 操作瀏覽器，Google Gemini 生成回覆，Serper.dev 擴充外部知識（RAG），SQLite 儲存已回覆記錄。

---

## 📁 專案結構

```
web_agent/
├── config/
│   ├── settings.py              # 所有設定集中管理
│   └── prompts/                 # AI 提示詞檔案
│       ├── decision_prompt.txt
│       ├── reply_prompt.txt
│       ├── keyword_extract_prompt.txt
│       └── external_search_strategy_prompt.txt
├── core/
│   ├── ai_handler.py            # Gemini AI 判斷 & 回覆生成（多 Key 輪替）
│   ├── browser_handler.py       # Playwright 瀏覽器自動化
│   └── search_handler.py        # Serper RAG 外部知識增強
├── utils/
│   ├── logger.py                # 彩色 console + 檔案日誌
│   └── sqlite_storage.py        # SQLite 儲存後端
├── logs/
│   ├── agent.log                # 執行日誌
│   ├── debug.html               # 最後一次頁面 HTML（偵錯用）
│   ├── storage.db               # SQLite 資料庫（回覆記錄）
│   └── screenshots/             # 每次送出回覆後的截圖
├── md/
│   └── ARCHITECTURE.md          # 架構設計說明
├── main.py                      # 主程式（流程編排）
├── run_main.sh                  # 手動執行腳本
├── .env                         # 環境變數（不提交到版控）
├── .env.example                 # 環境變數範本
└── README.md
```

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install playwright python-dotenv google-generativeai requests
playwright install chromium
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 填入實際資訊
```

### 3. 執行

```bash
python main.py
# 或使用腳本
bash run_main.sh
```

---

## ⚙️ 環境變數說明

| 變數 | 必填 | 說明 |
|------|------|------|
| `EMAIL` | ✅ | 論壇登入 Email |
| `PASSWORD` | ✅ | 論壇登入密碼 |
| `GEMINI_API_KEY` | ✅（若未設定 `GEMINI_API_KEYS`）| 單一 Gemini API Key |
| `GEMINI_API_KEYS` | 可選 | 多 Key 輪替，JSON 陣列或逗號分隔（見下方說明） |
| `SERPER_API_KEY` | 可選 | Serper.dev 搜尋 Key，缺少時停用外部知識增強 |

### 多 Key 輪替格式

```env
# JSON 陣列格式
GEMINI_API_KEYS=["AIzaSy...", "AIzaSy...", "AIzaSy..."]

# 逗號分隔格式
GEMINI_API_KEYS=AIzaSy...,AIzaSy...,AIzaSy...
```

當某個 Key 失敗時，程式**立即**切換至下一個 Key 並重試，不等待。所有 Key 皆失敗時程式退出（`sys.exit(1)`）。

---

## 🔧 常用設定（`config/settings.py`）

### 模擬模式 / 實際發文

```python
BROWSER_CONFIG = {
    "dry_run": True,   # True = 模擬（不真正送出），False = 實際發文
    "max_replies_per_run": 8,  # 每次執行最多回覆篇數，0 = 不限
    "headless": True,
}
```

### 回覆長度

```python
AI_CONFIG = {
    "reply_min_length": 100,
    "reply_max_length": 200,
}
```

### 巡邏模式

```python
AGENT_PATROL_CONFIG = {
    "mode": "keyword",  # "keyword"（關鍵字搜尋）或 "board"（直接瀏覽最新貼文）
    "target_keywords": ["資工", "電機", "物理", "學測"],
}
```

---

## 🤖 API 輪替機制

`AIHandler` 與 `SearchHandler` 均使用 `GEMINI_API_KEYS_LIST`：

1. 啟動時依序測試每個 Key，使用第一個成功的
2. 任何一次 API 呼叫失敗，**立即切換**到下一個 Key 重試
3. 所有 Key 用盡才終止程式

---

## 📊 資料儲存

所有記錄儲存於 `logs/storage.db`（SQLite）：

- `replied_posts` — 已回覆的貼文 ID（防止重複）
- `replies_log` — 完整回覆記錄（post_id、標題、回覆內容、時間）

---

## 🪵 日誌

```bash
tail -f logs/agent.log   # 即時查看執行日誌
```

截圖保存於 `logs/screenshots/`，每次送出回覆後自動截圖。

---

## 🐛 常見問題

**Q: 所有 Gemini Key 都失敗，程式退出**  
A: 確認 `.env` 内的 Key 有效，且 Gemini API 配額未超過

**Q: 找不到貼文 / 選擇器失效**  
A: 網站改版時更新 `config/settings.py` 中的 `SELECTORS`

**Q: SERPER_API_KEY 未設定**  
A: 程式會跳過外部知識增強，仍可正常回覆（品質略降）

**Q: 重複回覆同一篇貼文**  
A: 確認 `logs/storage.db` 存在且可寫入；資料庫損壞時可刪除後重建

