#!/usr/bin/env python3
"""
快速測試 Google Gemini API 設定
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini_api():
    print("=" * 50)
    print("測試 Google Gemini API 設定")
    print("=" * 50)
    
    # 檢查 API Key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ 錯誤：未找到 GEMINI_API_KEY")
        print("\n請檢查：")
        print("1. 是否已創建 .env 檔案")
        print("2. .env 中是否包含 GEMINI_API_KEY=你的API金鑰")
        print("3. API Key 申請網址：https://makersuite.google.com/app/apikey")
        return False
    
    print(f"✓ 找到 API Key: {api_key[:10]}...")
    
    # 測試 API 連接
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("\n測試 AI 判斷功能...")
        test_title = "請問台大資工好考嗎？"
        test_content = "我是高三學生，想請問學長姐台大資工的申請難度如何？"
        
        prompt = f"""判斷這是否需要回覆（YES/NO）：
標題：{test_title}
內容：{test_content}"""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        print(f"✓ AI 回應: {result}")
        
        print("\n測試 AI 生成回覆功能...")
        prompt2 = f"""你是台大資工學長，請用50字內回覆：
標題：{test_title}
內容：{test_content}"""
        
        response2 = model.generate_content(prompt2)
        reply = response2.text.strip()
        print(f"✓ AI 生成的回覆: {reply}")
        
        print("\n" + "=" * 50)
        print("✅ 所有測試通過！AI 功能正常運作")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤：{e}")
        print("\n可能的原因：")
        print("1. API Key 無效或過期")
        print("2. 網路連接問題")
        print("3. 超出免費額度（每天1500次）")
        return False

if __name__ == "__main__":
    test_gemini_api()
