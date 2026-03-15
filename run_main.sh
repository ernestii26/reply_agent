#!/bin/bash

# 1. 載入 Conda 環境定義 (根據你的 miniconda3 路徑)
source /home/ernestii26/miniconda3/etc/profile.d/conda.sh

# 2. 進入你的專案目錄 (請將下面的路徑換成你 main.py 所在的資料夾)
cd /home/ernestii26/Desktop/web_agent

# 3. 激活環境並執行程式
conda activate web_agent
echo "--- Run started at $(date) ---" > /home/ernestii26/Desktop/web_agent/auto_run.log
python3 main.py >> /home/ernestii26/Desktop/web_agent/auto_run.log 2>&1