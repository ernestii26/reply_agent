"""
多用戶平行執行入口
使用 multiprocessing 同時啟動兩個 user 的巡邏流程，各自獨立 browser context 與 storage。
"""
import multiprocessing
from playwright.sync_api import sync_playwright
from config.settings import USERS
from main import run


def _run_user(user_index: int):
    user_config = USERS[user_index]
    with sync_playwright() as playwright:
        run(playwright, user_config)


if __name__ == "__main__":
    processes = []
    for i in range(len(USERS)):
        p = multiprocessing.Process(target=_run_user, args=(i,), name=f"user{i+1}")
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
