# -*- coding: utf-8 -*-
"""
============================================================
程式名稱 (Program) : LiveLink R2B 快速開啟工具
版本 (Version)     : v1.0
日期 (Date)        : 2026-04-28
開發者 (Author)    : Cursor + Claude Sonnet 4.6
開發環境 (Env)     : Rhino 8 (CPython 3.9) / Python 3
============================================================
【功能說明】
在 Rhino 指令列提供三個快速開啟選項：
  Config     → 開啟 R2B_Path.txt 設定檔
  DataFolder → 開啟 Data\ 資料夾
  DebugLog   → 開啟 cursor_R2B_debug_log.txt 除錯日誌

【Rhino 工具列按鈕 Macro】
  ! _-RunPythonScript "%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Python\LiveLink_R2B_Open.py"
============================================================
"""
import rhinoscriptsyntax as rs
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B_Config import CONFIG_FILE, DATA_DIR, DEBUG_LOG_FILE, load_r2b_config

mode = rs.GetString("R2B 開啟", "Config", ["Config", "DataFolder", "DebugLog"])

if not mode:
    pass  # 使用者按 Esc，靜默結束

elif mode == "Config":
    load_r2b_config()  # 確保設定檔存在
    os.startfile(CONFIG_FILE)
    print("R2B: 已開啟 {}".format(CONFIG_FILE))

elif mode == "DataFolder":
    if not os.path.exists(DATA_DIR):
        load_r2b_config()  # 觸發自動建立 Data\ 目錄
    os.startfile(DATA_DIR)
    print("R2B: 已開啟 {}".format(DATA_DIR))

elif mode == "DebugLog":
    load_r2b_config()  # 確保 Data\ 目錄存在
    if not os.path.exists(DEBUG_LOG_FILE):
        open(DEBUG_LOG_FILE, 'a').close()  # 首次使用時建立空白日誌
    os.startfile(DEBUG_LOG_FILE)
    print("R2B: 已開啟 {}".format(DEBUG_LOG_FILE))
