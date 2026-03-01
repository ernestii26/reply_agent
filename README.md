# 自動回覆 Agent - 架構說明

## 📁 專案結構

```
web_agent/
├── config/                 # 配置模組
│   ├── __init__.py
│   └── settings.py        # 集中所有配置參數
│
├── core/                   # 核心功能模組
│   ├── __init__.py
│   ├── ai_handler.py      # AI 處理器（判斷與生成回覆）
│   └── browser_handler.py # 瀏覽器操作處理器
│
├── utils/                  # 工具模組
│   ├── __init__.py
│   ├── logger.py          # 日誌系統
│   └── storage.py         # 儲存管理（已回覆記錄）
│
├── main.py                 # 主程式入口（簡潔的流程編排）
├── test_ai.py             # AI 功能測試
├── test_reply.py          # 回覆機制測試
├── .env                   # 環境變數（EMAIL, PASSWORD, GEMINI_API_KEY）
├── replied.txt            # 已回覆貼文 ID 記錄
└── README.md              # 本文件
```

## 🎯 架構設計原則

### 1. **模組化 (Modularity)**
- 每個模組職責單一明確
- 易於測試和維護
- 可獨立替換或升級

### 2. **配置集中 (Centralized Configuration)**
- 所有配置參數統一在 `config/settings.py`
- 環境變數透過 `.env` 管理
- 方便調整參數而無需修改代碼

### 3. **關注點分離 (Separation of Concerns)**
- **config**: 配置管理
- **core**: 業務邏輯（AI、瀏覽器操作）
- **utils**: 基礎設施（日誌、儲存）
- **main**: 流程編排

## 📦 模組說明

### `config/settings.py` - 配置管理
集中管理所有配置參數：
- 用戶設定（USER_NAME）
- API 配置（GEMINI_API_KEY, GEMINI_MODEL）
- 網站配置（BASE_URL, 選擇器）
- 時間配置（等待時間、超時設定）
- AI 配置（prompt 模板、回覆長度）

### `core/ai_handler.py` - AI 處理器
封裝所有 AI 相關邏輯：
- `should_reply()`: 判斷是否需要回覆
- `generate_reply()`: 生成回覆內容
- `_remove_markdown()`: 移除 Markdown 格式
- `_basic_should_reply()`: 降級方案（AI 不可用時）

使用方法：
```python
from core.ai_handler import get_ai_handler

ai = get_ai_handler()
if ai.should_reply(title, content):
    reply = ai.generate_reply(title, content)
```

### `core/browser_handler.py` - 瀏覽器操作處理器
封裝所有網頁自動化操作：
- `login()`: 登入系統
- `navigate_to_board()`: 導航到目標討論板
- `get_posts()`: 獲取貼文列表
- `get_post_id/title/content()`: 提取貼文資訊
- `check_if_already_replied()`: 檢查是否已回覆
- `submit_reply()`: 提交回覆
- `go_back()`: 返回列表頁

使用方法：
```python
from core.browser_handler import BrowserHandler

handler = BrowserHandler(page)
handler.login()
handler.navigate_to_board()
posts = handler.get_posts()
```

### `utils/logger.py` - 日誌系統
提供統一的日誌輸出：
- 彩色控制台輸出（INFO/WARNING/ERROR）
- 文件日誌記錄（完整日誌保存到 agent.log）
- 專用方法（`success()`, `skip()`, `ai()`, `reply()`）

使用方法：
```python
from utils.logger import get_logger

logger = get_logger()
logger.info("一般訊息")
logger.success("操作成功")
logger.ai("AI 分析中...")
logger.error("發生錯誤")
```

### `utils/storage.py` - 儲存管理
管理已回覆貼文的記錄：
- `load()`: 讀取已記錄的貼文 ID
- `save(post_id)`: 儲存新的貼文 ID
- `contains(post_id)`: 檢查是否已記錄
- `count()`: 獲取已記錄數量
- `get_recent(n)`: 獲取最近 N 筆記錄

使用方法：
```python
from utils.storage import get_storage

storage = get_storage()
if not storage.contains(post_id):
    # 處理貼文
    storage.save(post_id)
```

### `main.py` - 主程式
簡潔的流程編排（約 130 行）：
1. 初始化模組（logger, storage, ai, browser_handler）
2. 登入系統
3. 導航到目標討論板
4. 讀取已處理記錄
5. 逐一處理貼文
   - 檢查是否已處理
   - 判斷是否需要回覆
   - 生成並提交回覆
   - 記錄已處理貼文
6. 輸出統計結果

## 🚀 使用方式

### 安裝依賴
```bash
pip install playwright python-dotenv google-generativeai
playwright install chromium
```

### 配置環境變數
編輯 `.env` 文件：
```env
EMAIL=your_email@example.com
PASSWORD=your_password
GEMINI_API_KEY=your_gemini_api_key
```

### 執行主程式
```bash
python main.py
```

### 測試 AI 功能
```bash
python test_ai.py
```

### 測試回覆機制
```bash
python test_reply.py
```

## ⚙️ 配置調整

### 修改用戶名稱
編輯 `config/settings.py`:
```python
USER_NAME = "你的顯示名稱"
```

### 調整等待時間
編輯 `config/settings.py` 的 `WAIT_TIMES`:
```python
WAIT_TIMES = {
    "post_list_load": 10000,  # 貼文列表載入等待時間
    "post_detail_load": 2000,  # 貼文詳情載入等待時間
    ...
}
```

### 修改 AI 回覆長度
編輯 `config/settings.py` 的 `AI_CONFIG`:
```python
AI_CONFIG = {
    "reply_min_length": 100,  # 最小字數
    "reply_max_length": 200,  # 最大字數
    ...
}
```

### 啟用無頭模式
編輯 `config/settings.py` 的 `BROWSER_CONFIG`:
```python
BROWSER_CONFIG = {
    "headless": True,  # 改為 True
}
```

## 🔍 除錯與測試

### 啟用調試暫停
在 `main.py` 的 `finally` 區塊取消註解：
```python
browser_handler.pause()  # 取消此行註解
```

### 查看日誌文件
```bash
tail -f agent.log
```

### 實際提交回覆
在 `core/browser_handler.py` 的 `submit_reply()` 方法中取消註解：
```python
submit_button.click()  # 取消此行註解
```

## 📊 架構優勢

### 優化前（單一文件 320 行）
❌ 所有邏輯混在一起  
❌ 難以測試單一功能  
❌ 配置散落各處  
❌ 難以擴展新功能  

### 優化後（模組化架構）
✅ 職責清晰分離  
✅ 易於單元測試  
✅ 配置集中管理  
✅ 易於擴展維護  
✅ 主程式僅 130 行（減少 60%）  

## 🎨 擴展建議

### 添加新功能
1. 在對應模組添加方法
2. 在 `main.py` 中調用
3. 在 `config/settings.py` 添加相關配置

### 添加新的 AI 模型
修改 `core/ai_handler.py`，實現不同的 AI 介面。

### 添加錯誤重試機制
在 `core/browser_handler.py` 的操作方法中添加重試邏輯。

### 添加通知系統
創建 `utils/notifier.py`，整合 Email/Webhook 通知。

## 📝 維護建議

1. **定期檢查選擇器**: 網站改版可能導致選擇器失效，需在 `config/settings.py` 更新
2. **監控 API 用量**: Gemini API 有免費額度限制（1500 請求/天）
3. **清理舊日誌**: 定期清理 `agent.log` 避免文件過大
4. **備份記錄**: 定期備份 `replied.txt` 防止誤刪

## 🐛 常見問題

### Q: 找不到模組錯誤
A: 確保在專案根目錄執行 `python main.py`，且各目錄下都有 `__init__.py`

### Q: AI 不回覆
A: 檢查 `.env` 中的 `GEMINI_API_KEY` 是否正確設定

### Q: 無法送出回覆
A: 檢查 `browser_handler.py` 中的 `submit_button.click()` 是否被註解

### Q: 重複回覆同一貼文
A: 檢查 `replied.txt` 是否正常寫入，權限是否正確

---

**優化完成時間**: 2026-03-01  
**架構版本**: 2.0  
**原始版本**: a2.py (320 lines, monolithic)  
**優化版本**: main.py (130 lines, modular) + 6 模組文件
