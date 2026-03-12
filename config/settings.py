"""
配置文件 - 集中管理所有配置參數
"""
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
 

def _load_prompt(filename: str, default: str) -> str:
    """
    從 `config/prompts/` 讀取提示詞檔案；若不存在或讀取失敗，回傳 `default`。
    """
    base_dir = os.path.dirname(__file__)
    prompts_dir = os.path.join(base_dir, "prompts")
    path = os.path.join(prompts_dir, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default
# ==================== 瀏覽器配置 ====================
BROWSER_CONFIG = {
    "headless": True,  # 是否使用無頭模式
    "slow_mo": 0,  # 減慢操作速度（毫秒），用於調試
    "dry_run": False,  # True = 模擬模式（不實際發文）；改為 False 才會真正送出回覆
    "min_replies_per_run": 5,  # 每次執行至少回覆幾篇（會自動捲動載入更多貼文）；設為 0 表示不限制
}

# ==================== 用戶配置 ====================
USER_NAME = "冠冠｜台大資工學長"  # 你的顯示名稱

# ==================== API 配置 ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GEMINI_MODEL = "gemma-3-4b-it"
GEMINI_MODEL = "gemini-2.5-flash"
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
# 支持多個 GEMINI API KEY（用逗號分隔），若未設定則回退到單一 GEMINI_API_KEY
GEMINI_API_KEYS_RAW = os.getenv("GEMINI_API_KEYS")
GEMINI_API_KEYS_LIST = []
if GEMINI_API_KEYS_RAW:
    s = GEMINI_API_KEYS_RAW.strip()
    parsed = None
    # 嘗試解析為 Python/JSON 陣列，例如：["key1","key2"]（支援換行與空白）
    try:
        import ast
        parsed = ast.literal_eval(s)
    except Exception:
        try:
            import json
            parsed = json.loads(s)
        except Exception:
            parsed = None

    if isinstance(parsed, (list, tuple)):
        GEMINI_API_KEYS_LIST = [str(k).strip() for k in parsed if k]
    else:
        # 回退到逗號分隔的格式
        GEMINI_API_KEYS_LIST = [k.strip() for k in s.split(",") if k.strip()]
elif GEMINI_API_KEY:
    GEMINI_API_KEYS_LIST = [GEMINI_API_KEY]

# 登入憑證
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# ==================== 網站配置 ====================
BASE_URL = "https://pei.com.tw/internal"
TARGET_BOARD_NAME = "🔥 討論學測、落點分析"

# ==================== 選擇器配置 ====================
SELECTORS = {
    # 貼文相關
    "post_container": "div[data-post-id]",
    "post_title": "h3",
    "post_content": "p.whitespace-pre-wrap",
    "post_link": "a[href*='/feed/']",
    
    # 回覆相關
    "reply_textarea": "textarea[placeholder*='寫下你的留言']",
    "submit_button_gradient": "button.from-teal-500.to-cyan-500",
    "submit_button_icon": "button:has(svg.lucide-send)",
    "submit_button_adjacent": "textarea[placeholder*='寫下你的留言'] + button",
    
    # 評論區相關
    "comment_section": "div.bg-gray-50\\/50",
    "comment_author": "div.bg-gray-50\\/50 span.font-medium.text-gray-700",
    
    # 登入相關
    "login_button_initial": "button",  # 初始登入按鈕（透過 filter has_text 使用）
    "email_input": "textbox[name='user@example.com']",
    "password_input": "textbox[name='********']",
    "login_submit": "button[name='登入']",
    
    # 搜尋相關
    "search_textbox": "textbox[name='搜尋文章或作者暱稱']",
    "search_result_container": "div[data-post-id]",  # 搜尋結果與一般貼文使用相同容器
}

# ==================== 時間配置 ====================
WAIT_TIMES = {
    "post_list_load": 10000,  # 等待貼文列表載入（毫秒）
    "post_detail_load": 2000,  # 等待貼文詳情載入（毫秒）
    "after_click": 1000,  # 點擊後等待（毫秒）
    "textarea_fill": 500,  # 填寫文字框後等待（毫秒）
    "button_enable_max": 5000,      # 等待按鈕啟用最大時間（毫秒）
    "button_check_interval": 500,   # 檢查按鈕狀態間隔（毫秒）
    "after_submit": 2000,           # 提交後等待（毫秒）
    "after_submit_screenshot": 10000,  # 送出後截圖前的等待時間（毫秒）
    "scroll_load_wait": 2500,       # 捲動後等待新貼文載入（毫秒）
}

# ==================== AI 配置 ====================
decision_default = """
        你是一位學長，專門回答學測和升學相關問題。

        請判斷以下貼文是否需要你回答（回答YES或NO）：

        標題：{title}
        內容：{content}

        判斷標準：
        1. 是否為提問性質（而非單純分享或閒聊）
        2. 是否與學測、升學、選系、大學生活相關
        3. 是否是你能夠回答的問題（資工、理工科系相關更佳）

        只回答 YES 或 NO，不需要解釋。
    """

reply_default = """
        你現在是扮演一個溫暖的學長，正在回答學弟妹的升學問題。

        貼文標題：{title}
        貼文內容：{content}

        請生成一個友善、專業且有幫助的回覆。要求：
        1. 以學長的口吻，親切但專業，
        2. 提供具體建議或資訊
        3. 如果是選系問題，可以分享資工相關經驗
        4. 如果是學測問題，給予鼓勵和實用建議
        5. 長度控制在{min_length}-{max_length}字
        6. 不要提到你是AI，而是以真實學長身份回答
        7. 重要：請用純文字回覆，不要使用任何 Markdown 格式（如 **粗體**、##標題、-列表 等）
        8. 不要使用特殊符號如星號、井號、底線等格式符號
        9. 開頭一定不用打招呼，像是嗨學弟妹之類的，或是自我介紹，請務必直接切入主題回答問題
        回覆內容：
    """

AI_CONFIG = {
    "reply_min_length": 30,  # 回覆最小字數
    "reply_max_length": 200,  # 回覆最大字數
    "decision_prompt_template": _load_prompt("decision_prompt.txt", decision_default),
    "reply_prompt_template": _load_prompt("reply_prompt.txt", reply_default),
    "question_keywords": ["？", "?", "請問", "想問", "有人知道", "嗎", "呢"],
}

# ==================== 代理巡邏配置 ====================
AGENT_PATROL_CONFIG = {
    "mode": "keyword",  # 模式選擇："keyword" (關鍵字搜尋) 或 "board" (直接瀏覽最新貼文)
    "target_keywords": ["資工", "電機", "物理","數學", "理科", "化學", "理工", "數學", "學測"],
}

# ==================== 回覆貼文時用來外部搜尋配置 ====================
SEARCH_CONFIG = {
    # 功能開關
    "enable_external_search": True,  # 啟用外部網路搜尋（Serper API）

    # 搜尋結果數量
    "max_external_results": 7,  # 外部搜尋最多返回結果數
    
    # 關鍵字提取提示詞
    "keyword_extract_prompt": _load_prompt(
        "keyword_extract_prompt.txt",
        """
        從以下貼文中提取關鍵字，用於搜尋相關討論：

        標題：{title}
        內容：{content}

        請提取最重要的1-3個關鍵字（如：科系名稱、大學名稱、分數範圍等），用空格分隔。
        只回傳關鍵字，不要解釋。
        """,
    ),
            
    # 外部搜尋策略提示詞
    "external_search_strategy_prompt": _load_prompt(
        "external_search_strategy_prompt.txt",
        """
        我們需要根據以下貼文進行網際網路搜尋，提供學測落點、錄取分數或大學升學最新資訊（當前為 2026 年）。

        標題：{title}
        內容：{content}

        任務：根據貼文內容，提供最適合用來 Google 搜尋的關鍵字。

        請只回傳合法的 JSON 格式（不要有 Markdown code block），只包含一個欄位：
        "query": (字串) 最佳的搜尋字詞（繁體中文，不要加年份）
        """,
    ),
    
    # 外部搜尋端點
    "serper_api_endpoint": "https://google.serper.dev/search",
    
    # 搜尋等待時間
    "search_load_wait": 2000,  # 搜尋結果載入等待時間（毫秒）
    "search_input_delay": 500,  # 輸入搜尋字後等待（毫秒）
}

# ==================== 檔案配置 ====================
FILES = {
    "debug_html": "logs/debug.html",            # 除錯用 HTML 文件
    "log_file": "logs/agent.log",               # 日誌文件
    "screenshots_dir": "logs/screenshots",      # 送出回覆後的截圖資料夾
    "db_path": "logs/storage.db",               # SQLite DB 檔案
}

# 儲存後端：固定使用 SQLite
STORAGE = {
    "backend": "sqlite"
}

