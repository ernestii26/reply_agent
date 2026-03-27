"""
Google Drive 同步工具

使用方式：
  python -m utils.drive_sync download   # 執行前：從 Drive 下載 storage.db
  python -m utils.drive_sync upload     # 執行後：上傳 storage.db + 截圖

環境變數：
  GDRIVE_CLIENT_ID             OAuth 用戶端 ID
  GDRIVE_CLIENT_SECRET         OAuth 用戶端密鑰
  GDRIVE_REFRESH_TOKEN         OAuth refresh token（由 get_refresh_token.py 取得）
  GDRIVE_DB_FOLDER_ID          storage.db 存放的資料夾 ID
  GDRIVE_SCREENSHOTS_FOLDER_ID 截圖存放的資料夾 ID（依日期建子資料夾）
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ==================== 本地路徑 ====================
DB_PATH = Path("logs/storage.db")
SCREENSHOTS_DIR = Path("logs/screenshots")

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _tw_date_label() -> str:
    """回傳台灣時間的日期標籤，格式為 M/D（例如 3/27）"""
    tw_now = datetime.now(timezone.utc) + timedelta(hours=8)
    return f"{tw_now.month}/{tw_now.day}"


def _get_service():
    client_id = os.environ.get("GDRIVE_CLIENT_ID")
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET")
    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN")

    missing = [k for k, v in {
        "GDRIVE_CLIENT_ID": client_id,
        "GDRIVE_CLIENT_SECRET": client_secret,
        "GDRIVE_REFRESH_TOKEN": refresh_token,
        "GDRIVE_DB_FOLDER_ID": os.environ.get("GDRIVE_DB_FOLDER_ID"),
        "GDRIVE_SCREENSHOTS_FOLDER_ID": os.environ.get("GDRIVE_SCREENSHOTS_FOLDER_ID"),
    }.items() if not v]
    if missing:
        print(f"[drive_sync] 缺少環境變數：{', '.join(missing)}，跳過")
        sys.exit(0)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def _find_file(service, name: str, folder_id: str) -> str | None:
    q = f"name='{name}' and '{folder_id}' in parents and trashed=false"
    resp = service.files().list(q=q, fields="files(id)").execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None


def _get_or_create_subfolder(service, name: str, parent_id: str) -> str:
    q = (
        f"name='{name}' and '{parent_id}' in parents"
        f" and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    resp = service.files().list(q=q, fields="files(id)").execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id").execute()
    print(f"[drive_sync] 建立資料夾：{name}")
    return folder["id"]


def _upload_file(service, local_path: Path, folder_id: str, mime_type: str = "application/octet-stream"):
    name = local_path.name
    existing_id = _find_file(service, name, folder_id)
    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=False)
    if existing_id:
        service.files().update(fileId=existing_id, media_body=media).execute()
        print(f"[drive_sync] 更新：{name}")
    else:
        meta = {"name": name, "parents": [folder_id]}
        service.files().create(body=meta, media_body=media).execute()
        print(f"[drive_sync] 新增：{name}")


def download():
    service = _get_service()
    db_folder_id = os.environ["GDRIVE_DB_FOLDER_ID"]

    file_id = _find_file(service, "storage.db", db_folder_id)
    if not file_id:
        print("[drive_sync] Drive 上尚無 storage.db，略過下載（首次執行）")
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with open(DB_PATH, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    print(f"[drive_sync] 下載完成：storage.db ({DB_PATH.stat().st_size} bytes)")


def upload():
    service = _get_service()
    db_folder_id = os.environ["GDRIVE_DB_FOLDER_ID"]
    screenshots_folder_id = os.environ["GDRIVE_SCREENSHOTS_FOLDER_ID"]

    if DB_PATH.exists():
        _upload_file(service, DB_PATH, db_folder_id)
    else:
        print("[drive_sync] storage.db 不存在，略過")

    if SCREENSHOTS_DIR.exists():
        screenshots = sorted(SCREENSHOTS_DIR.glob("*.png"))
        if screenshots:
            date_label = _tw_date_label()
            date_folder_id = _get_or_create_subfolder(service, date_label, screenshots_folder_id)
            for f in screenshots:
                _upload_file(service, f, date_folder_id, mime_type="image/png")
        else:
            print("[drive_sync] 無截圖可上傳")
    else:
        print("[drive_sync] screenshots/ 資料夾不存在，略過")

    print("[drive_sync] 上傳完成")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "download":
        download()
    elif cmd == "upload":
        upload()
    else:
        print("Usage: python -m utils.drive_sync [download|upload]")
        sys.exit(1)
