"""
自動回覆 Agent - 主程式
使用模組化架構，負責整體流程編排
"""
from playwright.sync_api import Playwright, sync_playwright

# 導入自定義模組
from config.settings import BROWSER_CONFIG
from utils.logger import get_logger
from utils.storage import get_storage
from core.ai_handler import get_ai_handler
from core.browser_handler import BrowserHandler


def run(playwright: Playwright) -> None:
    """主執行流程"""
    # 初始化模組
    logger = get_logger()
    storage = get_storage()
    ai = get_ai_handler()
    
    # 啟動瀏覽器
    browser = playwright.chromium.launch(headless=BROWSER_CONFIG["headless"])
    context = browser.new_context()
    page = context.new_page()
    browser_handler = BrowserHandler(page)
    
    try:
        # 1. 登入
        logger.info("\n🚀 開始執行自動回覆 Agent\n")
        logger.info("步驟 1: 登入系統")
        browser_handler.login()
        logger.success("登入成功")
        
        # 2. 導航到目標討論板
        logger.info("\n步驟 2: 前往目標討論板")
        browser_handler.navigate_to_board()
        logger.success("成功進入討論板")
        
        # 3. 讀取已處理記錄
        replied_ids = storage.load()
        logger.info(f"\n已記錄的貼文數量: {len(replied_ids)}")
        if replied_ids:
            recent = storage.get_recent(5)
            logger.info(f"最近記錄的ID: {', '.join(recent)}...")
        
        # 4. 獲取所有貼文
        posts = browser_handler.get_posts()
        logger.section(f"找到 {len(posts)} 個貼文，開始處理")
        
        # 統計數據
        processed_count = 0
        skipped_count = 0
        
        # 5. 逐一處理貼文
        for i, post in enumerate(posts, 1):
            try:
                # 獲取貼文基本資訊
                post_id = browser_handler.get_post_id(post)
                title = browser_handler.get_post_title(post)
                
                logger.post_header(i, len(posts), post_id)
                logger.post_title(title)
                
                # 檢查是否已處理
                if storage.contains(post_id):
                    logger.skip("此貼文已處理過，跳過")
                    skipped_count += 1
                    continue
                
                # 點擊進入貼文
                logger.action("點擊進入貼文...")
                browser_handler.click_post(post)
                
                # 檢查是否已在評論區回覆過
                if browser_handler.check_if_already_replied():
                    logger.success("已回覆過此貼文，記錄並跳過")
                    storage.save(post_id)
                    processed_count += 1
                    browser_handler.go_back()
                    continue
                
                # 獲取貼文內容
                content = browser_handler.get_post_content()
                logger.post_content_preview(content)
                
                # AI 判斷是否需要回覆
                logger.ai("AI分析中...")
                should_reply = ai.should_reply(title, content)
                
                if should_reply:
                    logger.success("AI判斷：需要回覆")
                    
                    # AI 生成回覆
                    reply_content = ai.generate_reply(title, content)
                    logger.reply(reply_content)
                    
                    # 提交回覆
                    success = browser_handler.submit_reply(reply_content)
                    if success:
                        storage.save(post_id)
                        processed_count += 1
                    else:
                        # 即使失敗也記錄，避免重複嘗試
                        storage.save(post_id)
                else:
                    logger.reject("AI判斷：不需回覆（可能不是提問或不相關）")
                    storage.save(post_id)
                    processed_count += 1
                
                # 返回列表
                logger.back("返回貼文列表")
                browser_handler.go_back()
                
            except Exception as e:
                logger.error(f"處理貼文時出錯: {e}")
                continue
        
        # 6. 輸出統計結果
        total_recorded = len(replied_ids) + processed_count
        logger.summary(processed_count, skipped_count, total_recorded)
        
        # 7. 保存調試 HTML
        browser_handler.save_debug_html()
        
    finally:
        # 清理資源
        # browser_handler.pause()  # 取消註解以啟用調試暫停
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
