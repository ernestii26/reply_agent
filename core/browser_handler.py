"""
瀏覽器處理器 - 封裝所有瀏覽器自動化操作
"""
import re
import time
from playwright.sync_api import Page, expect
from config.settings import (
    BASE_URL, TARGET_BOARD_NAME, USER_NAME,
    EMAIL, PASSWORD, SELECTORS, WAIT_TIMES, FILES, SEARCH_CONFIG, BROWSER_CONFIG
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
        # self.page.get_by_role("button").filter(has_text=re.compile(r"^$")).click()
        
        # 填寫 Email
        self.page.get_by_role("textbox", name="user@example.com").click()
        self.page.get_by_role("textbox", name="user@example.com").fill(EMAIL)
        
        # 填寫密碼
        self.page.get_by_role("textbox", name="********").click()
        self.page.get_by_role("textbox", name="********").fill(PASSWORD)
        
        # 點擊登入
        self.page.get_by_role("button", name="登入").click()
        time.sleep(WAIT_TIMES["after_click"] / 1000)
    def navigate_to_board(self):
        """導航到目標討論板"""
        # self.page.get_by_role("button", name=TARGET_BOARD_NAME).click()
        self.page.goto("https://pei.com.tw/feed")
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
        print(f"  🔍 check_if_already_replied: 檢查是否已以 [{user_name}] 回覆")

        # Step 1: 嘗試展開全部留言
        # try:
        #     # 直接鎖定包含「查看全部」字眼的按鈕，避開 Regex 解析問題
        #     # expand_btn = self.page.locator("button:has-text('查看全部')").first
            
        #     # 確保按鈕有成功載入 DOM 結構中
        #     expand_btn.wait_for(state="attached", timeout=3000)
        #     if expand_btn.is_visible():
        #         print(f"  🔍 找到「查看全部留言」按鈕，點擊展開...")
        #         expand_btn.first.click()
        #         time.sleep(1.5)
        #     else:
        #         print(f"  🔍 未找到「查看全部留言」按鈕（留言數少或不存在）")
        # except Exception as e:
        #     print(f"  🔍 展開留言時出錯（忽略）: {e}")

        # Step 2: 用 filter + regex 直接定位是否存在符合 user_name 的留言作者
        try:
            if self.page.locator(f"span:text-is('{user_name}')").count() > 0:
                print("  🔍 結果：已回覆過（找到匹配）")
                return True
            print("  🔍 結果：尚未回覆（未找到匹配）")
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
            
            # 根據 dry_run 決定是否真正送出
            if BROWSER_CONFIG["dry_run"]:
                print(f"  🔸 DRY_RUN 模式：略過實際送出（在 settings.py 將 dry_run 改為 False 以啟用）")
            else:
                submit_button.click()
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
    
    def search_feed(self, query: str) -> bool:
        try:
            search_box = self.page.get_by_role("textbox", name="搜尋文章或作者暱稱")
            search_box.click()
            time.sleep(SEARCH_CONFIG["search_input_delay"] / 1000)
            search_box.fill(query)
            search_box.press("Enter")  # 補上這行送出搜尋
            time.sleep(SEARCH_CONFIG["search_load_wait"] / 1000)
            return True
        except Exception as e:
            print(f"  ⚠ 論壇搜尋時出錯: {e}")
            return False
    
    def get_search_results(self, max_results: int = None) -> list:
        """
        獲取搜尋結果
        
        Args:
            max_results: 最多返回結果數量
        
        Returns:
            搜尋結果列表，每個結果包含 {id, title, content}
        """
        if max_results is None:
            max_results = 5  # 預設上限
        
        results = []
        try:
            # 獲取搜尋結果貼文元素
            posts = self.page.locator(SELECTORS["search_result_container"]).all()
            
            for post in posts[:max_results]:
                try:
                    post_id = self.get_post_id(post)
                    title = self.get_post_title(post)
                    content = self.get_post_content(post)
                    
                    results.append({
                        "id": post_id,
                        "title": title,
                        "content": content[:200]  # 只取前200字避免太長
                    })
                except Exception as e:
                    # 個別貼文解析失敗不影響其他結果
                    continue
        except Exception as e:
            print(f"  ⚠ 獲取搜尋結果時出錯: {e}")
        
        return results
    
    def clear_search(self):
        """清除搜尋框內容，返回正常瀏覽狀態"""
        try:
            search_box = self.page.get_by_role("textbox", name="搜尋文章或作者暱稱")
            search_box.click()
            search_box.fill("")  # 清空搜尋框
            time.sleep(SEARCH_CONFIG["search_input_delay"] / 1000)
        except Exception as e:
            print(f"  ⚠ 清除搜尋時出錯: {e}")
    
    def take_screenshot(self, post_id: str) -> str:
        """
        截圖當前頁面並儲存到 screenshots 資料夾

        Args:
            post_id: 貼文 ID，用於命名截圖檔案

        Returns:
            截圖檔案路徑，失敗時回傳空字串
        """
        import os
        from datetime import datetime
        try:
            screenshots_dir = FILES["screenshots_dir"]
            os.makedirs(screenshots_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(screenshots_dir, f"{timestamp}_{post_id}.png")
            self.page.screenshot(path=filename, full_page=False)
            print(f"  📷 截圖已儲存：{filename}")
            return filename
        except Exception as e:
            print(f"  ⚠ 截圖失敗: {e}")
            return ""

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
