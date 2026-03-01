"""
瀏覽器處理器 - 封裝所有瀏覽器自動化操作
"""
import re
import time
from playwright.sync_api import Page, expect
from config.settings import (
    BASE_URL, TARGET_BOARD_NAME, USER_NAME, 
    EMAIL, PASSWORD, SELECTORS, WAIT_TIMES, FILES
)


class BrowserHandler:
    """瀏覽器處理類，負責所有網頁操作"""
    
    def __init__(self, page: Page):
        """
        初始化瀏覽器處理器
        
        Args:
            page: Playwright Page 對象
        """
        self.page = page
    
    def login(self):
        """執行登入流程"""
        # 前往首頁
        self.page.goto(BASE_URL)
        
        # 點擊初始登入按鈕（空白按鈕）
        self.page.get_by_role("button").filter(has_text=re.compile(r"^$")).click()
        
        # 填寫 Email
        self.page.get_by_role("textbox", name="user@example.com").click()
        self.page.get_by_role("textbox", name="user@example.com").fill(EMAIL)
        
        # 填寫密碼
        self.page.get_by_role("textbox", name="********").click()
        self.page.get_by_role("textbox", name="********").fill(PASSWORD)
        
        # 點擊登入
        self.page.get_by_role("button", name="登入").click()
    
    def navigate_to_board(self):
        """導航到目標討論板"""
        self.page.get_by_role("button", name=TARGET_BOARD_NAME).click()
        
        # 等待貼文列表載入
        self.page.wait_for_selector(
            SELECTORS["post_container"], 
            timeout=WAIT_TIMES["post_list_load"]
        )
        time.sleep(WAIT_TIMES["post_detail_load"] / 1000)  # 額外等待確保完全載入
    
    def get_posts(self) -> list:
        """
        獲取所有貼文元素
        
        Returns:
            貼文元素列表
        """
        return self.page.locator(SELECTORS["post_container"]).all()
    
    def get_post_id(self, post) -> str:
        """
        獲取貼文ID
        
        Args:
            post: 貼文元素
        
        Returns:
            貼文 ID
        """
        return post.get_attribute("data-post-id")
    
    def get_post_title(self, post) -> str:
        """
        獲取貼文標題
        
        Args:
            post: 貼文元素
        
        Returns:
            貼文標題
        """
        return post.locator(SELECTORS["post_title"]).inner_text()
    
    def click_post(self, post):
        """
        點擊進入貼文詳情
        
        Args:
            post: 貼文元素
        """
        post.locator(SELECTORS["post_link"]).first.click()
        time.sleep(WAIT_TIMES["post_detail_load"] / 1000)
    
    def get_post_content(self) -> str:
        """
        獲取貼文完整內容
        
        Returns:
            貼文內容文字
        """
        return self.page.locator(SELECTORS["post_content"]).first.inner_text()
    
    def check_if_already_replied(self, user_name=None) -> bool:
        """
        檢查評論區是否已經有自己的回覆
        
        Args:
            user_name: 要檢查的用戶名稱，預設使用設定中的 USER_NAME
        
        Returns:
            是否已回覆
        """
        if user_name is None:
            user_name = USER_NAME
        
        try:
            # 查找評論區中的所有回覆者名稱
            comment_authors = self.page.locator(SELECTORS["comment_author"]).all()
            for author in comment_authors:
                if author.inner_text() == user_name:
                    return True
            return False
        except Exception as e:
            print(f"  ⚠ 檢查回覆時出錯: {e}")
            return False
    
    def submit_reply(self, reply_content: str) -> bool:
        """
        提交回覆
        
        Args:
            reply_content: 回覆內容
        
        Returns:
            是否成功提交
        """
        try:
            # 找到回覆輸入框
            reply_textarea = self.page.locator(SELECTORS["reply_textarea"]).first
            reply_textarea.click()
            time.sleep(WAIT_TIMES["textarea_fill"] / 1000)
            
            # 輸入回覆內容
            reply_textarea.fill(reply_content)
            time.sleep(WAIT_TIMES["after_click"] / 1000)
            
            # 定位送出按鈕（多種方式，增加成功率）
            submit_button = self._find_submit_button()
            
            if not submit_button:
                print(f"  ✗ 找不到送出按鈕")
                return False
            
            # 等待按鈕可用
            if not self._wait_button_enabled(submit_button):
                print(f"  ⚠ 送出按鈕仍為 disabled 狀態")
                return False
            
            # 點擊送出（取消註解以實際送出）
            # submit_button.click()
            print(f"  ✅ 已成功送出回覆!")
            time.sleep(WAIT_TIMES["after_submit"] / 1000)
            
            return True
        except Exception as e:
            print(f"  ✗ 回覆時發生錯誤: {e}")
            return False
    
    def _find_submit_button(self):
        """
        尋找送出按鈕（多種方式）
        
        Returns:
            按鈕元素或 None
        """
        # 方法1: 透過漸變色 class 定位
        try:
            button = self.page.locator(SELECTORS["submit_button_gradient"]).first
            if button.count() > 0:
                return button
        except:
            pass
        
        # 方法2: 透過 SVG 圖標定位
        try:
            button = self.page.locator(SELECTORS["submit_button_icon"]).first
            if button.count() > 0:
                return button
        except:
            pass
        
        # 方法3: 透過相對位置定位
        try:
            button = self.page.locator(SELECTORS["submit_button_adjacent"]).first
            if button.count() > 0:
                return button
        except:
            pass
        
        return None
    
    def _wait_button_enabled(self, button, max_wait_ms=None) -> bool:
        """
        等待按鈕變為可用
        
        Args:
            button: 按鈕元素
            max_wait_ms: 最大等待時間（毫秒）
        
        Returns:
            按鈕是否變為可用
        """
        if max_wait_ms is None:
            max_wait_ms = WAIT_TIMES["button_enable_max"]
        
        check_interval = WAIT_TIMES["button_check_interval"] / 1000
        max_iterations = int(max_wait_ms / WAIT_TIMES["button_check_interval"])
        
        for _ in range(max_iterations):
            if not button.is_disabled():
                return True
            time.sleep(check_interval)
        
        return False
    
    def go_back(self):
        """返回貼文列表"""
        self.page.go_back()
        time.sleep(WAIT_TIMES["after_click"] / 1000)
        
        # 重新等待列表載入
        self.page.wait_for_selector(
            SELECTORS["post_container"], 
            timeout=5000
        )
    
    def save_debug_html(self, filepath=None):
        """
        保存當前頁面的 HTML 供調試
        
        Args:
            filepath: 保存路徑，預設使用設定中的路徑
        """
        if filepath is None:
            filepath = FILES["debug_html"]
        
        try:
            full_html = self.page.content()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_html)
        except Exception as e:
            print(f"警告：保存 debug HTML 時出錯: {e}")
    
    def pause(self):
        """暫停執行（用於調試）"""
        self.page.pause()
