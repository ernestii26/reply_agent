"""
配置文件 - 集中管理所有配置參數
"""
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# ==================== 用戶配置 ====================
USER_NAME = "冠冠｜台大資工學長"  # 你的顯示名稱

# ==================== API 配置 ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

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
}

# ==================== 時間配置 ====================
WAIT_TIMES = {
    "post_list_load": 10000,  # 等待貼文列表載入（毫秒）
    "post_detail_load": 2000,  # 等待貼文詳情載入（毫秒）
    "after_click": 1000,  # 點擊後等待（毫秒）
    "textarea_fill": 500,  # 填寫文字框後等待（毫秒）
    "button_enable_max": 5000,  # 等待按鈕啟用最大時間（毫秒）
    "button_check_interval": 500,  # 檢查按鈕狀態間隔（毫秒）
    "after_submit": 2000,  # 提交後等待（毫秒）
}

# ==================== AI 配置 ====================
AI_CONFIG = {
    "reply_min_length": 100,  # 回覆最小字數
    "reply_max_length": 200,  # 回覆最大字數
    "decision_prompt_template": """你是一位台大資工學長，專門回答學測和升學相關問題。

請判斷以下貼文是否需要你回答（回答YES或NO）：

標題：{title}
內容：{content}

判斷標準：
1. 是否為提問性質（而非單純分享或閒聊）
2. 是否與學測、升學、選系、大學生活相關
3. 是否是你能夠回答的問題（資工、理工科系相關更佳）

只回答 YES 或 NO，不需要解釋。""",
    
    "reply_prompt_template": """你是「冠冠｜台大資工學長」，正在回答學弟妹的升學問題。

貼文標題：{title}
貼文內容：{content}

請生成一個友善、專業且有幫助的回覆。要求：
1. 以學長的口吻，親切但專業
2. 提供具體建議或資訊
3. 如果是選系問題，可以分享資工相關經驗
4. 如果是學測問題，給予鼓勵和實用建議
5. 長度控制在{min_length}-{max_length}字
6. 不要提到你是AI，而是以真實學長身份回答
7. 重要：請用純文字回覆，不要使用任何 Markdown 格式（如 **粗體**、##標題、-列表 等）
8. 不要使用特殊符號如星號、井號、底線等格式符號

回覆內容：""",
    
    "question_keywords": ["？", "?", "請問", "想問", "有人知道", "嗎", "呢"],
}

# ==================== 檔案配置 ====================
FILES = {
    "replied_posts": "replied.txt",  # 已回覆貼文記錄文件
    "debug_html": "debug.html",  # 除錯用 HTML 文件
    "log_file": "agent.log",  # 日誌文件
}

# ==================== 瀏覽器配置 ====================
BROWSER_CONFIG = {
    "headless": False,  # 是否使用無頭模式
    "slow_mo": 0,  # 減慢操作速度（毫秒），用於調試
}
