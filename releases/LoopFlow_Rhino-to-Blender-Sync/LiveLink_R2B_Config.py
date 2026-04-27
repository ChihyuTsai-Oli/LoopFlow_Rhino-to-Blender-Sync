# -*- coding: utf-8 -*-
"""
============================================================
模組名稱 (Module)  : LiveLink_R2B_Config
版本 (Version)     : v1.0
日期 (Date)        : 2026-04-27
開發者 (Author)    : Cursor + Claude Sonnet 4.6
開發環境 (Env)     : Rhino 8 (CPython 3.9) / Python 3
============================================================
【功能說明】
LiveLink R2B 系列腳本的共用設定模組。
統一管理 R2B_Path.txt 的讀取、寫入與預設值，
確保所有腳本使用一致的設定邏輯。

【放置位置】
%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Python\LiveLink_R2B_Config.py

【使用方式】
各腳本開頭加入：
    import os, sys
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _HERE)
    from LiveLink_R2B_Config import load_r2b_config, save_r2b_config, DATA_DIR

【變數連動注意事項】
- 設定檔：%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\R2B_Path.txt
- 除錯日誌：%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\cursor_R2B_debug_log.txt
============================================================
"""
import os

# ── 全域路徑推算（依安裝位置自動推算，不依賴硬編碼） ──────────────────
_PYTHON_DIR    = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR    = os.path.dirname(_PYTHON_DIR)
DATA_DIR       = os.path.join(INSTALL_DIR, "Data")
CONFIG_FILE    = os.path.join(DATA_DIR, "R2B_Path.txt")
DEBUG_LOG_FILE = os.path.join(DATA_DIR, "cursor_R2B_debug_log.txt")

# 所有腳本共用的完整預設值（單一真理來源）
DEFAULT_CONFIG = {
    "DataPath":       DATA_DIR,
    "ModelDir":       "",           # 空白 = fallback 至 Rhino 作業檔同目錄
    "LightLayer":     "R2B_LT_Points",
    "CameraFile":     "R2B_Camera_Sync.json",
    "LightFile":      "R2B_Light_Sync.json",
    "ModelFile":      "R2B.3dm",
    "BoxMapSize":     "500",
    "LastModelLayer": "",
}

# 寫入設定檔時的欄位順序
_FIELD_ORDER = [
    "DataPath",
    "ModelDir",
    "LightLayer",
    "CameraFile",
    "LightFile",
    "ModelFile",
    "BoxMapSize",
    "LastModelLayer",
]


def load_r2b_config():
    """
    讀取全域設定檔 R2B_Path.txt。
    - 若檔案不存在：自動建立並寫入所有預設欄位。
    - 若檔案存在但缺少欄位：自動補齊缺少的欄位並回寫。
    - 確保 DataPath 資料夾存在。
    """
    config = DEFAULT_CONFIG.copy()

    if not os.path.exists(CONFIG_FILE):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        save_r2b_config(config)
    else:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip()
                        val = parts[1].strip()
                        if key in config:
                            config[key] = val
        except Exception:
            pass

        # 補齊缺少的欄位
        needs_update = False
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            for key in _FIELD_ORDER:
                if (key + ":") not in content:
                    needs_update = True
                    break
        except Exception:
            needs_update = True

        if needs_update:
            save_r2b_config(config)

    if not os.path.exists(config["DataPath"]):
        try:
            os.makedirs(config["DataPath"])
        except Exception:
            pass

    return config


def save_r2b_config(config):
    """依固定順序寫入設定檔，保留使用者已修改的值。"""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
        except Exception:
            pass
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            for key in _FIELD_ORDER:
                f.write("{}: {}\n".format(key, config.get(key, DEFAULT_CONFIG.get(key, ""))))
    except Exception:
        pass
