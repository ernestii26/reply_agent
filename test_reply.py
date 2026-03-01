#!/usr/bin/env python3
"""
測試回覆功能的調試腳本
僅測試單一貼文的回覆流程，不記錄到 replied.txt
"""

import re 
from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_reply_mechanism():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("=" * 60)
        print("測試回覆機制")
        print("=" * 60)
        
        # 登入
        print("\n1. 登入中...")
        page.goto("https://pei.com.tw/internal")
        page.get_by_role("button").filter(has_text=re.compile(r"^$")).click()
        page.get_by_role("textbox", name="user@example.com").fill(os.getenv("EMAIL"))
        page.get_by_role("textbox", name="********").fill(os.getenv("PASSWORD"))
        page.get_by_role("button", name="登入").click()
        time.sleep(2)
        
        # 進入討論區
        print("2. 進入學測討論區...")
        page.get_by_role("button", name="🔥 討論學測、落點分析").click()
        time.sleep(2)
        
        # 等待貼文載入
        page.wait_for_selector("div[data-post-id]", timeout=10000)
        print("3. 貼文列表已載入")
        
        # 找到第一個貼文（測試用）
        first_post = page.locator("div[data-post-id]").first
        post_id = first_post.get_attribute("data-post-id")
        title = first_post.locator("h3").inner_text()
        
        print(f"\n測試貼文:")
        print(f"  ID: {post_id}")
        print(f"  標題: {title}")
        
        # 點擊進入
        print("\n4. 點擊進入貼文...")
        first_post.locator("a[href*='/feed/']").first.click()
        time.sleep(2)
        
        # 檢查回覆輸入框
        print("\n5. 檢查回覆輸入框...")
        try:
            textarea = page.locator("textarea[placeholder*='寫下你的留言']")
            count = textarea.count()
            print(f"  找到 {count} 個輸入框")
            
            if count > 0:
                print("  ✓ 輸入框定位成功!")
                
                # 測試輸入
                print("\n6. 測試輸入文字...")
                test_text = "這是測試回覆，請忽略（測試中）"
                textarea.first.click()
                time.sleep(0.5)
                textarea.first.fill(test_text)
                print(f"  ✓ 已輸入測試文字: {test_text}")
                time.sleep(1)
                
                # 檢查送出按鈕
                print("\n7. 檢查送出按鈕...")
                
                # 方法1: 漸變色按鈕
                btn1 = page.locator("button.from-teal-500.to-cyan-500")
                print(f"  方法1 (漸變色): 找到 {btn1.count()} 個")
                
                # 方法2: SVG 圖標
                btn2 = page.locator("button:has(svg.lucide-send)")
                print(f"  方法2 (send圖標): 找到 {btn2.count()} 個")
                
                # 方法3: 所有圓形按鈕
                btn3 = page.locator("button.rounded-full")
                print(f"  方法3 (圓形按鈕): 找到 {btn3.count()} 個")
                
                # 選擇最佳方法
                submit_button = None
                if btn1.count() > 0:
                    submit_button = btn1.first
                    print("  → 使用方法1")
                elif btn2.count() > 0:
                    submit_button = btn2.first
                    print("  → 使用方法2")
                
                if submit_button:
                    # 檢查按鈕狀態
                    print("\n8. 檢查按鈕狀態...")
                    is_disabled = submit_button.is_disabled()
                    print(f"  按鈕 disabled 狀態: {is_disabled}")
                    
                    if not is_disabled:
                        print("\n⚠ 注意：按鈕已啟用，可以送出")
                        print("  (這是測試，不會真的送出)")
                        
                        # 注意：這裡不實際點擊，避免真的送出測試留言
                        # submit_button.click()
                        
                        print("\n✅ 測試完成！回覆機制工作正常")
                    else:
                        print("\n⚠ 按鈕仍為 disabled（可能需要更多內容或稍等片刻）")
                        
                        # 等待一下看是否會解除
                        print("  等待5秒看是否解除...")
                        for i in range(10):
                            time.sleep(0.5)
                            if not submit_button.is_disabled():
                                print(f"  ✓ 在 {(i+1)*0.5} 秒後解除 disabled!")
                                break
                        else:
                            print("  ✗ 5秒後仍為 disabled")
                else:
                    print("  ✗ 無法定位送出按鈕")
                
                # 清除輸入
                print("\n9. 清除測試內容...")
                textarea.first.fill("")
                print("  ✓ 已清除")
                
            else:
                print("  ✗ 找不到輸入框")
                
        except Exception as e:
            print(f"  ✗ 錯誤: {e}")
        
        print("\n" + "=" * 60)
        print("測試結束，瀏覽器將保持開啟供檢查")
        print("按 Ctrl+C 結束程式")
        print("=" * 60)
        
        # 暫停以便檢查
        page.pause()
        
        browser.close()

if __name__ == "__main__":
    test_reply_mechanism()
