import re 
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()

# 設定 Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    print("警告：未設定 GEMINI_API_KEY，AI功能將無法使用")
    model = None

USER_NAME = "冠冠｜台大資工學長"  # 你的顯示名稱

def load_replied_posts():
    """讀取已處理過的貼文ID列表"""
    try:
        with open("replied.txt", "r", encoding="utf-8") as f:
            # 讀取所有非空行，去除空白
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        # 檔案不存在則返回空集合
        return set()

def save_replied_post(post_id):
    """將已處理的貼文ID保存到replied.txt"""
    with open("replied.txt", "a", encoding="utf-8") as f:
        f.write(f"{post_id}\n")
    print(f"  ✓ 已記錄貼文ID: {post_id}")

def check_if_replied(page, user_name):
    """檢查評論區是否已經有自己的回覆"""
    try:
        # 查找評論區中的所有回覆者名稱
        comment_authors = page.locator("div.bg-gray-50\\/50 span.font-medium.text-gray-700").all()
        for author in comment_authors:
            if author.inner_text() == user_name:
                return True
        return False
    except Exception as e:
        print(f"  ⚠ 檢查回覆時出錯: {e}")
        return False

def ai_should_reply(title, content):
    """使用AI判斷是否需要回覆這篇貼文"""
    if not model:
        print("  ⚠ AI未設定，使用基本規則判斷")
        # 基本判斷：是否包含問號或提問關鍵字
        question_keywords = ["？", "?", "請問", "想問", "有人知道", "嗎", "呢"]
        return any(keyword in title + content for keyword in question_keywords)
    
    try:
        prompt = f"""你是一位台大資工學長，專門回答學測和升學相關問題。

請判斷以下貼文是否需要你回答（回答YES或NO）：

標題：{title}
內容：{content}

判斷標準：
1. 是否為提問性質（而非單純分享或閒聊）
2. 是否與學測、升學、選系、大學生活相關
3. 是否是你能夠回答的問題（資工、理工科系相關更佳）

只回答 YES 或 NO，不需要解釋。"""
        
        response = model.generate_content(prompt)
        result = response.text.strip().upper()
        return "YES" in result
    except Exception as e:
        print(f"  ⚠ AI判斷時出錯: {e}")
        return False

def remove_markdown_syntax(text):
    """移除文字中的 Markdown 格式語法"""
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

def ai_generate_reply(title, content):
    """使用AI生成回覆內容"""
    if not model:
        return "同學你好！看到你的問題了，建議可以多參考學長姐的經驗，或者到相關科系的版上詢問看看。加油！"
    
    try:
        prompt = f"""你是「冠冠｜台大資工學長」，正在回答學弟妹的升學問題。

貼文標題：{title}
貼文內容：{content}

請生成一個友善、專業且有幫助的回覆。要求：
1. 以學長的口吻，親切但專業
2. 提供具體建議或資訊
3. 如果是選系問題，可以分享資工相關經驗
4. 如果是學測問題，給予鼓勵和實用建議
5. 長度控制在100-200字
6. 不要提到你是AI，而是以真實學長身份回答
7. 重要：請用純文字回覆，不要使用任何 Markdown 格式（如 **粗體**、##標題、-列表 等）
8. 不要使用特殊符號如星號、井號、底線等格式符號

回覆內容："""
        
        response = model.generate_content(prompt)
        reply = response.text.strip()
        
        # 額外保險：移除可能殘留的 Markdown 語法
        reply = remove_markdown_syntax(reply)
        
        return reply
    except Exception as e:
        print(f"  ⚠ AI生成回覆時出錯: {e}")
        return "同學你好！看到你的問題了，建議可以多參考學長姐的經驗。加油！"

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page1 = context.new_page()
    page1.goto("https://pei.com.tw/internal")
    page1.get_by_role("button").filter(has_text=re.compile(r"^$")).click()
    page1.get_by_role("textbox", name="user@example.com").click()
    page1.get_by_role("textbox", name="user@example.com").fill(os.getenv("EMAIL"))
    page1.get_by_role("textbox", name="********").click()
    page1.get_by_role("textbox", name="********").fill(os.getenv("PASSWORD"))
    page1.get_by_role("button", name="登入").click()
    page1.get_by_role("button", name="🔥 討論學測、落點分析").click()
    
    # 等待貼文列表載入
    page1.wait_for_selector("div[data-post-id]", timeout=10000)
    time.sleep(2)  # 額外等待確保所有貼文載入
    
    # 讀取已處理過的貼文ID
    replied_ids = load_replied_posts()
    print(f"\n已記錄的貼文數量: {len(replied_ids)}")
    if replied_ids:
        print(f"已記錄的ID: {', '.join(list(replied_ids)[:5])}{'...' if len(replied_ids) > 5 else ''}")
    
    # 抓取所有貼文容器
    posts = page1.locator("div[data-post-id]").all()
    print(f"\n找到 {len(posts)} 個貼文")
    
    processed_count = 0
    skipped_count = 0
    
    for i, post in enumerate(posts, 1):
        try:
            # 獲取貼文的唯一ID
            post_id = post.get_attribute("data-post-id")
            
            # 獲取標題用於顯示
            title = post.locator("h3").inner_text()
            
            print(f"\n[{i}/{len(posts)}] 貼文ID: {post_id}")
            print(f"  標題: {title}")
            
            # 檢查是否已處理過
            if post_id in replied_ids:
                print(f"  ⊗ 此貼文已處理過，跳過")
                skipped_count += 1
                continue
            
            # 未處理過的貼文：點擊進入
            print(f"  → 點擊進入貼文...")
            post.locator("a[href*='/feed/']").first.click()
            
            # 等待貼文內容載入
            time.sleep(2)
            
            # 抓取貼文詳細內容
            try:
                # 檢查是否已經回覆過此貼文
                if check_if_replied(page1, USER_NAME):
                    print(f"  ✓ 已回覆過此貼文，記錄並跳過")
                    save_replied_post(post_id)
                    processed_count += 1
                    continue
                
                # 獲取完整的貼文內容
                full_content = page1.locator("p.whitespace-pre-wrap").first.inner_text()
                print(f"  內容預覽: {full_content[:100]}...")
                
                # 使用AI判斷是否需要回覆
                print(f"  🤖 AI分析中...")
                should_reply = ai_should_reply(title, full_content)
                
                if should_reply:
                    print(f"  ✓ AI判斷：需要回覆")
                    
                    # 使用AI生成回覆內容
                    reply_content = ai_generate_reply(title, full_content)
                    print(f"  💬 生成的回覆: {reply_content[:80]}...")
                    
                    # 🔥 執行回覆操作
                    try:
                        # 找到回覆輸入框（使用 placeholder 定位）
                        reply_textarea = page1.locator("textarea[placeholder*='寫下你的留言']").first
                        reply_textarea.click()
                        time.sleep(0.5)
                        
                        # 輸入回覆內容
                        reply_textarea.fill(reply_content)
                        time.sleep(1)  # 等待按鈕解除 disabled 狀態
                        
                        # 定位送出按鈕（多種方式定位，增加成功率）
                        submit_button = None
                        
                        # 方法1: 透過漸變色 class 定位
                        try:
                            submit_button = page1.locator("button.from-teal-500.to-cyan-500").first
                            if submit_button.count() == 0:
                                submit_button = None
                        except:
                            pass
                        
                        # 方法2: 透過 SVG 圖標定位（send 圖標）
                        if not submit_button:
                            try:
                                submit_button = page1.locator("button:has(svg.lucide-send)").first
                            except:
                                pass
                        
                        # 方法3: 透過相對位置定位（textarea 旁的按鈕）
                        if not submit_button:
                            try:
                                submit_button = page1.locator("textarea[placeholder*='寫下你的留言'] + button").first
                            except:
                                pass
                        
                        if submit_button:
                            # 等待按鈕可用（最多等待5秒）
                            max_wait = 10
                            for i in range(max_wait):
                                if not submit_button.is_disabled():
                                    break
                                time.sleep(0.5)
                            
                            if not submit_button.is_disabled():
                                #submit_button.click()
                                print(f"  ✅ 已成功送出回覆!")
                                time.sleep(2)  # 等待回覆送出
                                
                                save_replied_post(post_id)
                                processed_count += 1
                            else:
                                print(f"  ⚠ 送出按鈕仍為 disabled 狀態（等待{max_wait*0.5}秒後）")
                                save_replied_post(post_id)
                        else:
                            print(f"  ✗ 找不到送出按鈕")
                            save_replied_post(post_id)
                        
                    except Exception as e:
                        print(f"  ✗ 回覆時發生錯誤: {e}")
                        print(f"  詳細錯誤: {str(e)}")
                        # 即使回覆失敗，也記錄下來避免一直重試
                        save_replied_post(post_id)
                else:
                    print(f"  ⊘ AI判斷：不需回覆（可能不是提問或不相關）")
                    save_replied_post(post_id)
                    processed_count += 1
                
            except Exception as e:
                print(f"  ✗ 讀取貼文內容時出錯: {e}")
            page1.pause()
            # 返回列表頁
            print(f"  ← 返回貼文列表")
            page1.go_back()
            time.sleep(1)
            
            # 重新等待列表載入
            page1.wait_for_selector("div[data-post-id]", timeout=5000)
            
        except Exception as e:
            print(f"  ✗ 處理貼文時出錯: {e}")
            continue
    
    print(f"\n" + "="*50)
    print(f"處理完成！")
    print(f"  新處理: {processed_count} 個貼文")
    print(f"  跳過: {skipped_count} 個貼文")
    print(f"  總計已記錄: {len(replied_ids) + processed_count} 個貼文")
    print("="*50)
    
    # 保存完整頁面供調試
    full_html = page1.content()
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    page1.pause()
    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
