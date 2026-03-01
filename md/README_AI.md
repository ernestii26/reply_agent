# AI自動回覆系統安裝說明

## 功能特色
✅ AI智能判斷是否需要回覆（學測、升學相關問題）
✅ 自動生成專業且友善的回覆內容
✅ 避免重複回覆（檢查評論區+記錄已回覆ID）
✅ 完全免費（使用Google Gemini免費額度）

## 安裝步驟

### 1. 安裝Python套件
```bash
pip install google-generativeai
```

### 2. 設定API Key
1. 複製 `.env.example` 為 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 申請Google Gemini API Key：
   - 訪問: https://makersuite.google.com/app/apikey
   - 點擊"Create API Key"
   - 複製生成的API Key

3. 編輯 `.env` 檔案，填入你的資訊：
   ```
   EMAIL=你的郵箱
   PASSWORD=你的密碼
   GEMINI_API_KEY=你申請的API_Key
   ```

### 3. 運行程式
```bash
python3 a2.py
```

## 工作流程

```
1. 登入網站
2. 遍歷貼文列表
3. 檢查replied.txt (已處理過？→ 跳過)
4. 點擊進入貼文
5. 檢查評論區 (已回覆過？→ 記錄並跳過)
6. AI分析貼文 (需要回覆？)
   ├─ 是 → AI生成回覆 → 自動回覆 → 記錄
   └─ 否 → 記錄並跳過
7. 返回列表，繼續下一篇
```

## AI判斷標準

AI會根據以下標準決定是否回覆：
1. ✅ 是否為提問性質（而非單純分享或閒聊）
2. ✅ 是否與學測、升學、選系、大學生活相關
3. ✅ 是否是可以回答的問題（資工、理工科系相關更佳）

## 檔案說明

- `a2.py` - 主程式
- `replied.txt` - 記錄已處理的貼文ID
- `.env` - 存放敏感資訊（需自行創建）
- `debug.html` - 調試用的完整頁面HTML

## 免費額度

Google Gemini API:
- 每天 1,500 次請求
- 每分鐘 60 次請求
- 完全免費

## 故障排除

### 問題：找不到回覆按鈕
檢查 `page1.locator("button").filter(has_text=re.compile(r"發布|送出|回覆"))` 選擇器是否正確

### 問題：AI未回覆
檢查 `.env` 中的 `GEMINI_API_KEY` 是否正確設定

### 問題：重複回覆
確保 `replied.txt` 檔案正常讀寫，並且回覆成功後有正確記錄
