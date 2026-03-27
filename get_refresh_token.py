"""
一次性授權腳本：取得 Google Drive refresh token
跑完後把印出來的三個值存到 GitHub Secrets
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file("cloud.json", SCOPES)
creds = flow.run_local_server(port=0)

# 讀取 client_id / client_secret
with open("cloud.json") as f:
    client_info = json.load(f)
    installed = client_info.get("installed") or client_info.get("web", {})

print("\n===== 複製以下三個值到 GitHub Secrets =====")
print(f"GDRIVE_CLIENT_ID     = {installed['client_id']}")
print(f"GDRIVE_CLIENT_SECRET = {installed['client_secret']}")
print(f"GDRIVE_REFRESH_TOKEN = {creds.refresh_token}")
print("==========================================\n")
