"""
搜尋處理器 - 外部知識增強（RAG）

負責透過 Serper API 從外部可靠網站取得最新資訊，以增強 AI 回覆品質。
"""
import json
import re
import requests
import google.generativeai as genai
from config.settings import GEMINI_API_KEYS_LIST, GEMINI_MODEL, SEARCH_CONFIG, SERPER_API_KEY


class SearchHandler:
    """搜尋處理類，負責透過 Serper API 取得外部知識（RAG）。"""

    def __init__(self):
        """初始化搜尋處理器，支援多 API Key 輪替"""
        self.model = None
        self.enabled = False
        self.api_keys = GEMINI_API_KEYS_LIST or []
        self.current_key_index = 0

        if self.api_keys:
            for i, key in enumerate(self.api_keys):
                if self._configure_with_key(key):
                    self.current_key_index = i
                    break
            if not self.enabled:
                print("警告：所有 GEMINI API Key 均初始化失敗，搜尋功能將無法使用")

            if SEARCH_CONFIG["enable_external_search"] and not SERPER_API_KEY:
                print("警告：啟用了外部網路搜尋，但未設定 SERPER_API_KEY")
        else:
            print("警告：未設定 GEMINI_API_KEY，搜尋功能將無法使用")

    def _configure_with_key(self, key: str) -> bool:
        """嘗試用指定 key 初始化 Gemini model，成功返回 True，失敗返回 False"""
        try:
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            self.enabled = True
            return True
        except Exception as e:
            print(f"警告：SearchHandler 使用指定 GEMINI API Key 初始化失敗: {e}")
            self.enabled = False
            return False

    def _switch_api_key(self) -> bool:
        """切換到下一個可用的 API Key，成功返回 True"""
        if not self.api_keys or len(self.api_keys) <= 1:
            return False
        start = self.current_key_index
        for offset in range(1, len(self.api_keys)):
            idx = (start + offset) % len(self.api_keys)
            if self._configure_with_key(self.api_keys[idx]):
                self.current_key_index = idx
                return True
        return False
    
    def extract_keywords(self, title: str, content: str) -> str:
        """
        從貼文中提取搜尋關鍵字
        
        Args:
            title: 貼文標題
            content: 貼文內容
        
        Returns:
            提取的關鍵字字串
        """
        if not self.enabled or not self.model:
            # 降級方案：直接使用標題的前幾個字
            return title[:10] if title else content[:10]
        
        try:
            prompt = SEARCH_CONFIG["keyword_extract_prompt"].format(
                title=title,
                content=content
            )
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"  ⚠ 提取關鍵字時出錯: {e}")
            if self._switch_api_key():
                try:
                    prompt = SEARCH_CONFIG["keyword_extract_prompt"].format(title=title, content=content)
                    response = self.model.generate_content(prompt)
                    return response.text.strip()
                except Exception as e2:
                    print(f"  ⚠ 切換 Key 後仍失敗: {e2}")
            return title[:10] if title else content[:10]
    
    def search_external_knowledge(self, title: str, content: str) -> str:
        """
        使用 Serper API 獲取外部知識
        
        Args:
            title: 貼文標題
            content: 貼文內容
        
        Returns:
            外部知識摘要
        """
        if not SEARCH_CONFIG["enable_external_search"] or not SERPER_API_KEY or not self.model:
            return ""
        
        try:
            print(f"  🔍 分析最佳外部搜尋策略...")
            # 1. 讓 AI 解析出最佳的搜尋關鍵字與網站篩選
            prompt = SEARCH_CONFIG["external_search_strategy_prompt"].format(
                title=title,
                content=content
            )
            try:
                strategy_response = self.model.generate_content(prompt)
            except Exception as e_gen:
                print(f"  ⚠ 搜尋策略生成失敗: {e_gen}")
                if self._switch_api_key():
                    print(f"  ↺ 已切換至 Key #{self.current_key_index}，重試")
                    strategy_response = self.model.generate_content(prompt)
                else:
                    return ""
            strategy_text = strategy_response.text.strip()

            # 用 regex 抷出 JSON 主體，避免 Gemini 輸出格式不固定導致 json.loads 失敗
            json_match = re.search(r'\{.*?\}', strategy_text, re.DOTALL)
            if not json_match:
                raise ValueError(f"無法從回應中找到 JSON：{strategy_text[:100]}")
            strategy = json.loads(json_match.group())
            
            search_query = strategy.get("query", "")

            if not search_query:
                # 降級方案
                search_query = self.extract_keywords(title, content)

            print(f"  🔍 執行 Serper API 搜尋: [{search_query}]")
            organics = self._serper_search(search_query)
            if not organics:
                print("  ⚠ 找不到相關的外部知識")
                return ""

            knowledge_parts = []
            for item in organics[:SEARCH_CONFIG["max_external_results"]]:
                item_title = item.get("title", "")
                item_snippet = item.get("snippet", "")
                item_link = item.get("link", "")
                
                part = f"- {item_title}: {item_snippet} (來源: {item_link})"
                knowledge_parts.append(part)
            
            knowledge = "\n".join(knowledge_parts)
            
            # (可選) 可再把搜尋結果丟給 AI 濃縮，但為了保持資訊精確度，這裏直接回傳 Serper 結果給後續回覆處理
            print(f"  ✓ 獲取外部知識: {len(knowledge)} 字")
            return knowledge
        except Exception as e:
            print(f"  ⚠ 外部搜尋時出錯: {e}")
            return ""
    
    def _serper_search(self, query: str) -> list:
        """
        呼叫 Serper API 並回傳 organic 結果列表

        Args:
            query: 完整搜尋字串（含 site filter 若有）

        Returns:
            organic 結果列表，失敗時回傳空列表
        """
        try:
            payload = json.dumps({
                "q": query,
                "gl": "tw",
                "hl": "zh-tw",
                "num": SEARCH_CONFIG["max_external_results"]
            })
            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            }
            response = requests.post(
                SEARCH_CONFIG["serper_api_endpoint"],
                headers=headers,
                data=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("organic", [])
        except Exception as e:
            print(f"  ⚠ Serper API 呼叫失敗: {e}")
            return []

    def get_enriched_context(self, title: str, content: str) -> dict:
        """
        獲取增強的上下文資訊（外部知識）
        
        Args:
            title: 貼文標題
            content: 貼文內容
        
        Returns:
            結構化的上下文資料 {
                "original_title": str,
                "original_content": str,
                "external_knowledge": str,
                "has_additional_context": bool
            }
        """
        context = {
            "original_title": title,
            "original_content": content,
            "external_knowledge": "",
            "has_additional_context": False
        }
        
        if not self.enabled:
            return context
        
        print("  🔎 開始搜尋外部相關資訊...")
        
        # 搜尋外部知識(Serper)
        external_info = self.search_external_knowledge(title, content)
        if external_info:
            context["external_knowledge"] = external_info
            context["has_additional_context"] = True
        
        return context
    
    def format_context_for_ai(self, context: dict) -> str:
        """
        將上下文格式化為 AI 可讀的文字
        
        Args:
            context: get_enriched_context 返回的結構化上下文
        
        Returns:
            格式化的上下文字串
        """
        if not context["has_additional_context"]:
            return context["original_content"]
        
        formatted = f"【原始貼文】\n{context['original_content']}\n\n"
        
        # 加入外部知識
        if context["external_knowledge"]:
            formatted += "【最新外部相關資訊】\n"
            formatted += f"{context['external_knowledge']}\n"
        
        return formatted


# 工廠函數
def create_search_handler():
    """
    建立 SearchHandler 實例的工廠函數

    Returns:
        SearchHandler 實例
    """
    return SearchHandler()
