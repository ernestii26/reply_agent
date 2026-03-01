"""
Serper API 連線測試腳本
用法：python3 test_serper.py
"""
import json
import requests
from dotenv import load_dotenv
from config.settings import SERPER_API_KEY, SEARCH_CONFIG

load_dotenv()


def test_serper():
    if not SERPER_API_KEY:
        print("❌ 未設定 SERPER_API_KEY，請在 .env 檔案中加入：SERPER_API_KEY=你的金鑰")
        return

    print(f"✓ 找到 SERPER_API_KEY（前8碼：{SERPER_API_KEY[:8]}...）")
    print("🔍 發送測試查詢：「台大資工 學測 錄取分數 2025 site:exam-match.1111.com.tw\n")

    payload = json.dumps({
        "q": "台大資工 學測 錄取分數 2025",
        "gl": "tw",
        "hl": "zh-tw",
        "num": 3
    })
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            SEARCH_CONFIG["serper_api_endpoint"],
            headers=headers,
            data=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        organics = data.get("organic", [])
        if not organics:
            print("⚠ API 回應成功，但找不到搜尋結果（organic 為空）")
            print("完整回應：\n", json.dumps(data, ensure_ascii=False, indent=2))
            return

        print(f"✅ Serper API 正常！找到 {len(organics)} 筆結果：\n")
        for i, item in enumerate(organics, 1):
            print(f"[{i}] {item.get('title', '（無標題）')}")
            print(f"    {item.get('snippet', '（無摘要）')}")
            print(f"    來源：{item.get('link', '')}\n")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 錯誤：{e.response.status_code}")
        print(f"   回應內容：{e.response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ 網路連線失敗，請檢查網路")
    except requests.exceptions.Timeout:
        print("❌ 請求逾時（超過 10 秒）")
    except Exception as e:
        print(f"❌ 未知錯誤：{e}")


if __name__ == "__main__":
    test_serper()
