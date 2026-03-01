import os
from dotenv import load_dotenv

import google.generativeai as genai
load_dotenv()
# 請填入你的 API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print(f"{'模型名稱':<40} | {'顯示名稱'}")
print("-" * 60)

# 列出所有支援生成內容的模型
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"{m.name:<40} | {m.display_name}")