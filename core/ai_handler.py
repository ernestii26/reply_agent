"""
AI 處理器 - 封裝 AI 判斷和回覆生成邏輯
"""
import re
import sys
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, AI_CONFIG, GEMINI_API_KEYS_LIST


class AIHandler:
    """AI 處理類，負責判斷是否回覆以及生成回覆內容"""
    
    def __init__(self):
        """初始化 AI 處理器"""
        self.model = None
        self.enabled = False
        self.api_keys = GEMINI_API_KEYS_LIST or []
        self.current_key_index = 0
        
        # 嘗試使用可用的 API key 初始化，支援多 key
        if self.api_keys:
            for i, key in enumerate(self.api_keys):
                if self._configure_with_key(key):
                    self.current_key_index = i
                    break
            if not self.enabled:
                print("警告：所有提供的 GEMINI_API_KEY 均初始化失敗，AI功能將無法使用")
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
            # 嘗試切換 API key 再次詢問一次
            if self.switch_api_key():
                try:
                    response = self.model.generate_content(prompt)
                    result = response.text.strip().upper()
                    return "YES" in result
                except Exception as e2:
                    print(f"  ⚠ 切換 API Key 後仍然失敗: {e2}")
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
    
    def generate_reply(self, title: str, content: str, enriched_context: str = None) -> str:
        """
        生成回覆內容
        
        Args:
            title: 貼文標題
            content: 貼文內容
            enriched_context: 增強的上下文資訊（包含論壇討論和外部知識）
        
        Returns:
            生成的回覆內容
        """
        if not self.enabled:
            return self._default_reply()
        
        # 每個 key 嘗試一次，失敗後立即切換，所有 key 耗盡才終止
        max_attempts = max(1, len(self.api_keys))
        attempt = 0
        while attempt < max_attempts:
            try:
                # 如果有增強上下文，使用增強上下文；否則使用原始內容
                context_to_use = enriched_context if enriched_context else content

                # 根據是否有增強上下文調整提示詞
                if enriched_context and enriched_context != content:
                    prompt = AI_CONFIG["reply_prompt_template"].format(
                        title=title,
                        content=context_to_use,
                        min_length=AI_CONFIG["reply_min_length"],
                        max_length=AI_CONFIG["reply_max_length"]
                    )
                    # 加入引用來源的指示
                    prompt += "\n\n注意：如果你參考了「論壇相關討論」或「最新相關資訊」中的具體數據（如分數、日期），請在回覆中自然地提及（例如：「根據最新資訊...」、「參考過往討論...」）。"
                else:
                    prompt = AI_CONFIG["reply_prompt_template"].format(
                        title=title,
                        content=context_to_use,
                        min_length=AI_CONFIG["reply_min_length"],
                        max_length=AI_CONFIG["reply_max_length"]
                    )

                response = self.model.generate_content(prompt)
                reply = response.text.strip()

                # 額外保險：移除可能殘留的 Markdown 語法
                reply = self._remove_markdown(reply)

                return reply
            except Exception as e:
                attempt += 1
                print(f"  ⚠ AI 生成回覆失敗 (第 {attempt} 次，Key #{self.current_key_index}): {e}")

                # 立即嘗試切換到下一個 API key
                if self.switch_api_key():
                    print(f"  ↺ 已切換至 GEMINI API Key #{self.current_key_index}，重試生成回覆")
                    continue
                else:
                    print(f"  ✖ 所有 GEMINI API Key 均已嘗試失敗，程序終止")
                    sys.exit(1)
    
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

    def _configure_with_key(self, key: str) -> bool:
        """
        嘗試用指定 key 設定 genai 並初始化 model，成功返回 True，失敗返回 False
        """
        try:
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            self.enabled = True
            return True
        except Exception as e:
            print(f"警告：使用指定 GEMINI API Key 初始化失敗: {e}")
            self.enabled = False
            return False

    def switch_api_key(self) -> bool:
        """
        在 `self.api_keys` 中切換到下一個可用的 API key，成功返回 True。
        若沒有其他可用 key 或切換失敗返回 False。
        """
        if not self.api_keys or len(self.api_keys) <= 1:
            return False

        start = self.current_key_index
        for offset in range(1, len(self.api_keys)):
            idx = (start + offset) % len(self.api_keys)
            key = self.api_keys[idx]
            if self._configure_with_key(key):
                self.current_key_index = idx
                return True

        return False
    
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
