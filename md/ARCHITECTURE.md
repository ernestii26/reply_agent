# 架構說明

## 模組概覽

```
main.py
  └─ 流程編排：登入 → 巡邏 → 判斷 → 搜尋 → 生成回覆 → 送出 → 儲存

config/
  └─ settings.py        所有設定集中管理（API keys、選擇器、等待時間、prompt 模板）
  └─ prompts/           AI 提示詞文字檔（獨立維護，避免硬碼在程式中）

core/
  └─ ai_handler.py      Gemini 多 Key 輪替；should_reply() 判斷；generate_reply() 生成回覆
  └─ browser_handler.py Playwright 操作封裝（登入、導覽、取得貼文、送出回覆）
  └─ search_handler.py  Serper RAG 增強（多 Key 輪替；外部搜尋→格式化→傳給 AI）

utils/
  └─ logger.py          彩色 console + 滾動 file log（logs/agent.log）
  └─ sqlite_storage.py  SQLite 儲存後端（WAL 模式；唯一索引防重複回覆）

logs/
  └─ storage.db         已回覆記錄（replied_posts + replies_log 兩張表）
  └─ agent.log          執行日誌
  └─ debug.html         最後一次頁面 HTML（偵錯用）
  └─ screenshots/       每次送出後自動截圖
```

---

## API 輪替流程

```
初始化
  for each key in GEMINI_API_KEYS_LIST:
      if _configure_with_key(key): break   ← 使用第一個成功的 key

呼叫 API 失敗
  → switch_api_key()                       ← 立即切換，不等待
      → 從 current_key_index + 1 開始輪替
      → 若找到可用 key：return True → 重試
      → 若所有 key 均失敗：
          generate_reply()  → sys.exit(1)
          should_reply()    → fallback 到 _basic_should_reply()（關鍵字比對）
          SearchHandler     → return "" 空字串
```

---

## 資料流

```
main.py
  1. SQLitePostStorage.contains(post_id)    ← 已處理則跳過
  2. AIHandler.should_reply(title, content) ← 不需要回覆則跳過
  3. SearchHandler.get_enriched_context()   ← Serper API 取外部知識
  4. SearchHandler.format_context_for_ai()  ← 組合原始內容 + 外部知識
  5. AIHandler.generate_reply(enriched)     ← Gemini 生成回覆
  6. BrowserHandler.submit_reply(reply)     ← Playwright 送出（dry_run=True 則跳過）
  7. SQLitePostStorage.save(post_id)        ← 記錄已處理
  8. SQLitePostStorage.save_reply(...)      ← 儲存完整回覆內容
```

---

## SQLite 資料庫結構

```sql
-- 已回覆貼文（防重複）
CREATE TABLE replied_posts (
    post_id   TEXT PRIMARY KEY,
    timestamp TEXT,
    source    TEXT DEFAULT 'agent'
);

-- 完整回覆記錄
CREATE TABLE replies_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    TEXT,
    title      TEXT,
    reply      TEXT,
    timestamp  TEXT,
    reply_hash TEXT
);
CREATE UNIQUE INDEX idx_reply_dedup ON replies_log (post_id, reply_hash);
```

---

## 設定調整速查

| 目的 | 位置 |
|------|------|
| API key 輪替 | `.env` → `GEMINI_API_KEYS` |
| 模擬 / 實際發文 | `config/settings.py` → `BROWSER_CONFIG["dry_run"]` |
| 每次回覆上限 | `config/settings.py` → `BROWSER_CONFIG["max_replies_per_run"]` |
| 巡邏關鍵字 | `config/settings.py` → `AGENT_PATROL_CONFIG["target_keywords"]` |
| 回覆字數範圍 | `config/settings.py` → `AI_CONFIG["reply_min/max_length"]` |
| AI 提示詞 | `config/prompts/*.txt` |
| 頁面選擇器 | `config/settings.py` → `SELECTORS` |
| 等待時間 | `config/settings.py` → `WAIT_TIMES` |
