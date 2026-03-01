"""
自動回覆 Agent - 主程式
使用模組化架構，負責整體流程編排
"""
from playwright.sync_api import Playwright, sync_playwright
import time

# 導入自定義模組
from config.settings import BROWSER_CONFIG, WAIT_TIMES, AI_CONFIG, AGENT_PATROL_CONFIG
from utils.logger import get_logger
from utils.storage import get_storage
from core.ai_handler import get_ai_handler
from core.browser_handler import BrowserHandler
from core.search_handler import create_search_handler


def run(playwright: Playwright) -> None:
    """主執行流程"""
    # 初始化模組
    logger = get_logger()
    storage = get_storage()
    ai = get_ai_handler()
    
    # 啟動瀏覽器
    browser = playwright.chromium.launch(
        headless=BROWSER_CONFIG["headless"],
        slow_mo=BROWSER_CONFIG["slow_mo"]
    )
    context = browser.new_context()
    page = context.new_page()
    browser_handler = BrowserHandler(page)
    
    # 初始化搜尋處理器（外部 RAG，透過 Serper API 取得外部知識）
    search_handler = create_search_handler()
    
    try:
        # 1. 登入
        logger.info("\n🚀 開始執行自動回覆 Agent\n")
        logger.info("步驟 1: 登入系統")
        browser_handler.login()
        logger.success("登入成功")
        
        # 2. 讀取已處理記錄
        replied_ids = storage.load()
        logger.info(f"\n已記錄的貼文數量: {len(replied_ids)}")
        if replied_ids:
            recent = storage.get_recent(5)
            logger.info(f"最近記錄的ID: {', '.join(recent)}...")
        
        # 3. 準備巡邏設定
        patrol_mode = AGENT_PATROL_CONFIG.get("mode", "board")
        target_keywords = AGENT_PATROL_CONFIG.get("target_keywords", ["二類"])
        processed_count, skipped_count, replied_count = 0, 0, 0
        max_replies = BROWSER_CONFIG["max_replies_per_run"]

        if max_replies > 0:
            logger.info(f"  本次最多回覆 {max_replies} 篇")

        # 定義內部函式：負責處理傳入的貼文列表（避免程式碼重複）
        def process_posts_list(posts_list):
            nonlocal processed_count, skipped_count, replied_count
            for i, post in enumerate(posts_list, 1):
                if max_replies > 0 and replied_count >= max_replies:
                    return True # 回傳 True 代表已達上限，通知外層停止
                try:
                    post_id = browser_handler.get_post_id(post)
                    title = browser_handler.get_post_title(post)
                    
                    logger.post_header(i, len(posts_list), post_id)
                    logger.post_title(title)
                    
                    if storage.contains(post_id):
                        logger.skip("此貼文已處理過，跳過")
                        skipped_count += 1
                        continue
                    
                    logger.action("點擊進入貼文...")
                    browser_handler.click_post(post)
                    
                    if browser_handler.check_if_already_replied():
                        logger.success("已回覆過此貼文，記錄並跳過")
                        storage.save(post_id)
                        processed_count += 1
                        browser_handler.go_back()
                        continue
                    
                    content = browser_handler.get_post_content()
                    logger.post_content_preview(content)
                    
                    logger.ai("AI分析中...")
                    should_reply = ai.should_reply(title, content)
                    
                    if should_reply:
                        logger.success("AI判斷：需要回覆")
                        enriched_ctx = search_handler.get_enriched_context(title, content)
                        
                        if enriched_ctx["has_additional_context"]:
                            formatted_context = search_handler.format_context_for_ai(enriched_ctx)
                            logger.info("  ✓ 已整合額外上下文資訊")
                        else:
                            formatted_context = content
                        
                        reply_content = ai.generate_reply(title, content, formatted_context)
                        logger.reply(reply_content)
                        
                        success = browser_handler.submit_reply(reply_content)
                        if success:
                            storage.save_reply(post_id, title, reply_content)
                            storage.save(post_id)
                            processed_count += 1
                            replied_count += 1
                            logger.action(f"等待 {WAIT_TIMES['after_submit_screenshot'] // 1000} 秒後截圖...")
                            time.sleep(WAIT_TIMES["after_submit_screenshot"] / 1000)
                            browser_handler.take_screenshot(post_id)
                            
                            if max_replies > 0 and replied_count >= max_replies:
                                logger.info(f"  ✓ 已達本次回覆上限（{max_replies} 篇），結束處理")
                                browser_handler.go_back()
                                return True
                        else:
                            storage.save(post_id)
                    else:
                        logger.reject("AI判斷：不需回覆")
                        storage.save(post_id)
                        processed_count += 1
                    
                    logger.back("返回貼文列表")
                    browser_handler.go_back()
                    
                except Exception as e:
                    logger.error(f"處理貼文時出錯: {e}")
                    continue
            return False

        # 4. 根據模式執行對應邏輯
        if patrol_mode == "keyword":
            logger.info("\n步驟 2: [關鍵字模式] 啟動")
            for query in target_keywords:
                logger.info(f"\n🔍 開始搜尋關鍵字: {query}")
                browser_handler.navigate_to_board() 
                
                if not browser_handler.search_feed(query):
                    continue
                    
                posts = browser_handler.get_posts()
                logger.section(f"「{query}」找到 {len(posts)} 個貼文，開始處理")
                
                # 執行貼文處理，若達到上限則中斷迴圈
                if process_posts_list(posts):
                    break
        else:
            logger.info("\n步驟 2: [一般模式] 直接瀏覽討論板最新貼文")
            browser_handler.navigate_to_board()
            posts = browser_handler.get_posts()
            logger.section(f"找到 {len(posts)} 個貼文，開始處理")
            process_posts_list(posts)
            
        # 5. 輸出統計結果
        total_recorded = len(storage.load())
        logger.summary(processed_count, skipped_count, total_recorded)
        
        # 6. 保存調試 HTML
        browser_handler.save_debug_html()
        
    finally:
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)