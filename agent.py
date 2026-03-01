from playwright.sync_api import sync_playwright
import time

def test_browser():
    with sync_playwright() as p:
        # headless=False 才能親眼看到瀏覽器跳出來
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("正在導航至 Google...")
        page.goto("https://www.google.com")
        
        # 停 5 秒讓你看一下畫面
        time.sleep(5)
        print("成功打開網頁！")
        browser.close()

if __name__ == "__main__":
    test_browser()