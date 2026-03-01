"""
AI 處理器 - 封裝 AI 判斷和回覆生成邏輯
"""
import re
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, AI_CONFIG


class AIHandler:
    """AI 處理類，負責判斷是否回覆以及生成回覆內容"""
    
    def __init__(self):
        """初始化 AI 處理器"""
        self.model = None
        self.enabled = False
        
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL)
                self.enabled = True
            except Exception as e:
                print(f"警告：初始化 Gemini API 失敗: {e}")
                self.enabled = False
        else:
            print("警告：未設定 GEMINI_API_KEY，AI功能將無法使用")
    
    def should_reply(self, title: str, content: str) -> bool:
        """
        判斷是否需要回覆這篇貼文
        
        Args:
            title: 貼文標題
            content: 貼文內容
        
        Returns:
            是否需要回覆
        """
        if not self.enabled:
            # 基本判斷：是否包含問號或提問關鍵字
            return self._basic_should_reply(title, content)
        
        try:
            prompt = AI_CONFIG["decision_prompt_template"].format(
                title=title,
                content=content
            )
            
            response = self.model.generate_content(prompt)
            result = response.text.strip().upper()
            return "YES" in result
        except Exception as e:
            print(f"  ⚠ AI判斷時出錯: {e}")
            # 降級到基本判斷
            return self._basic_should_reply(title, content)
    
    def _basic_should_reply(self, title: str, content: str) -> bool:
        """
        基本判斷規則（不使用 AI 時的降級方案）
        
        Args:
            title: 貼文標題
            content: 貼文內容
        
        Returns:
            是否需要回覆
        """
        question_keywords = AI_CONFIG["question_keywords"]
        text = title + content
        return any(keyword in text for keyword in question_keywords)
    
    def generate_reply(self, title: str, content: str) -> str:
        """
        生成回覆內容
        
        Args:
            title: 貼文標題
            content: 貼文內容
        
        Returns:
            生成的回覆內容
        """
        if not self.enabled:
            return self._default_reply()
        
        try:
            prompt = AI_CONFIG["reply_prompt_template"].format(
                title=title,
                content=content,
                min_length=AI_CONFIG["reply_min_length"],
                max_length=AI_CONFIG["reply_max_length"]
            )
            
            response = self.model.generate_content(prompt)
            reply = response.text.strip()
            
            # 額外保險：移除可能殘留的 Markdown 語法
            reply = self._remove_markdown(reply)
            
            return reply
        except Exception as e:
            print(f"  ⚠ AI生成回覆時出錯: {e}")
            return self._default_reply()
    
    def _remove_markdown(self, text: str) -> str:
        """
        移除文字中的 Markdown 格式語法
        
        Args:
            text: 原始文字
        
        Returns:
            移除 Markdown 後的文字
        """
        # 移除粗體 **text** 和 __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # 移除斜體 *text* 和 _text_
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # 移除標題符號 ## text
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # 移除列表符號 - text 或 * text
        text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
        
        # 移除連結 [text](url)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # 移除行內程式碼 `code`
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        return text.strip()
    
    def _default_reply(self) -> str:
        """
        預設回覆（當 AI 不可用時）
        
        Returns:
            預設回覆文字
        """
        return "同學你好！看到你的問題了，建議可以多參考學長姐的經驗，或者到相關科系的版上詢問看看。加油！"


# 全局 AI 處理器實例
_ai_handler_instance = None

def get_ai_handler(reinit=False):
    """
    獲取全局 AI 處理器實例
    
    Args:
        reinit: 是否強制重新初始化
    
    Returns:
        AIHandler 實例
    """
    global _ai_handler_instance
    
    if _ai_handler_instance is None or reinit:
        _ai_handler_instance = AIHandler()
    
    return _ai_handler_instance
