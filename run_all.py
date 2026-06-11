"""
多用戶循序執行入口
依序執行每個 user 的巡邏流程，各自獨立 browser context 與 storage。
"""
import sys
from playwright.sync_api import sync_playwright
from config.settings import USERS
from main import run


if __name__ == "__main__":
    failed = []
    for i, user_config in enumerate(USERS):
        print(f"\n[run_all] 開始執行 user{i+1}：{user_config['user_name']}")
        try:
            with sync_playwright() as playwright:
                run(playwright, user_config)
        except SystemExit as e:
            if e.code != 0:
                print(f"[run_all] user{i+1} 異常結束（exit code {e.code}）")
                failed.append(f"user{i+1}")
        except Exception as e:
            print(f"[run_all] user{i+1} 發生例外：{e}")
            failed.append(f"user{i+1}")

    if failed:
        print(f"[run_all] 以下 user 異常結束：{', '.join(failed)}")
        sys.exit(1)
