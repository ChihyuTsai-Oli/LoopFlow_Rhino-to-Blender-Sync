# -*- coding: utf-8 -*-
"""
=================================
LiveLink Rhino to Blender (Camera Sender)
=================================
程式名稱 : LiveLink_R2B_Camera
版本     : v3.0
日期     : 2026-04-27
開發者   : Cursor + Claude Sonnet 4.6
開發環境 : Rhino 8 / CPython 3.9
同步檔案 : 由 R2B_Path.txt 的 CameraFile 欄位決定（預設 R2B_Camera_Sync.json）

【系統概述 / System Overview】
本腳本為 Rhino 端的「攝影機即時同步引擎」。
利用背景事件監聽技術，捕捉視窗變動並輸出輕量化 JSON，達成即時連動。

【功能與操作指南 / Features & Operations】
▶ 功能描述：
   - 採常駐型切換開關設計 (Toggle)。
   - 綁定 `RhinoView.Modified` 事件，只在畫面旋轉或縮放時觸發。
   - 僅萃取攝影機 XYZ 座標、方向向量、向上向量與焦距。
   - 輸出至 R2B_Path.txt 指定的 DataPath 目錄下。
▶ 操作方式：
   - 執行本腳本一次，指令列顯示「啟動」即進入背景監聽狀態。
   - 若要停止同步，再次執行腳本，指令列顯示「停止」即解除綁定。

【變數連動注意事項】
- event_key：sc.sticky 的鍵名，需與 Blender 端 R2B_Camera 監聽器的識別名稱一致。
- 輸出路徑由 R2B_Path.txt 的 DataPath + CameraFile 決定（不依賴 doc.Path）。
- 若主動視窗無 ActiveView，export_camera 將靜默略過此次更新。
"""
import Rhino
import scriptcontext as sc
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B_Config import load_r2b_config, DATA_DIR

def export_camera(sender, e):
    """背景執行：當視窗改變時，瞬間寫入極輕量的 Camera JSON"""
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return

    if not doc.Views.ActiveView:
        return

    vp = doc.Views.ActiveView.ActiveViewport

    # 只提取攝影機的極簡資料
    data = {
        "location":  {"x": vp.CameraLocation.X,  "y": vp.CameraLocation.Y,  "z": vp.CameraLocation.Z},
        "direction": {"x": vp.CameraDirection.X,  "y": vp.CameraDirection.Y, "z": vp.CameraDirection.Z},
        "up":        {"x": vp.CameraUp.X,          "y": vp.CameraUp.Y,        "z": vp.CameraUp.Z},
        "lens": vp.Camera35mmLensLength
    }

    # 輸出至 DataPath + CameraFile（在 toggle 時已存入 sticky，避免每幀讀取設定檔）
    json_path = sc.sticky.get("R2B_CAMERA_JSON_PATH",
                              os.path.join(DATA_DIR, "R2B_Camera_Sync.json"))

    try:
        with open(json_path, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass  # 避免檔案被鎖定時報錯干擾建模

def toggle_camera_sync():
    """啟動或關閉背景監聽器"""
    event_key = "R2B_Camera_Sync_Event"

    if sc.sticky.has_key(event_key):
        # 已在執行，關閉並解除綁定
        func = sc.sticky[event_key]
        Rhino.Display.RhinoView.Modified -= func
        sc.sticky.Remove(event_key)
        sc.sticky.Remove("R2B_CAMERA_JSON_PATH")
        print("R2B Camera Sync: 已停止即時同步")
    else:
        # 讀取設定，預先計算輸出路徑
        cfg = load_r2b_config()
        json_path = os.path.join(cfg["DataPath"], cfg["CameraFile"])
        sc.sticky["R2B_CAMERA_JSON_PATH"] = json_path

        sc.sticky[event_key] = export_camera
        Rhino.Display.RhinoView.Modified += export_camera
        print("R2B Camera Sync: 已啟動 (輸出至 {})".format(json_path))

if __name__ == "__main__":
    toggle_camera_sync()
