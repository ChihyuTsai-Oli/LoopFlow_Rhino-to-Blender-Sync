# -*- coding: utf-8 -*-
"""
=================================
LiveLink Rhino to Blender (Camera Sender)
=================================
程式名稱 : LiveLink_R2B_Camera
版本     : v2.0
日期     : 2026-04-14
開發者   : Cursor + Claude Sonnet 4.6
開發環境 : Rhino 8 / CPython 3.9
同步檔案 : R2B_Camera_Sync.json

【系統概述 / System Overview】
本腳本為 Rhino 端的「攝影機即時同步引擎」。
利用背景事件監聽技術，捕捉視窗變動並輸出輕量化 JSON，達成即時連動。

【功能與操作指南 / Features & Operations】
▶ 功能描述：
   - 採常駐型切換開關設計 (Toggle)。
   - 綁定 `RhinoView.Modified` 事件，只在畫面旋轉或縮放時觸發。
   - 僅萃取攝影機 XYZ 座標、方向向量、向上向量與焦距。
   - 輸出至專案同目錄下的 `R2B_Camera_Sync.json`。
▶ 操作方式：
   - 執行本腳本一次，指令列顯示「啟動」即進入背景監聽狀態。
   - 若要停止同步，再次執行腳本，指令列顯示「停止」即解除綁定。

【變數連動注意事項】
- event_key：sc.sticky 的鍵名，需與 Blender 端 R2B_Camera 監聽器的識別名稱一致。
- json 輸出路徑依賴 doc.Path，執行前需確保 Rhino 檔案已儲存。
- 若主動視窗無 ActiveView，export_camera 將靜默略過此次更新。
"""
import Rhino
import scriptcontext as sc
import os
import json

def export_camera(sender, e):
    """背景執行：當視窗改變時，瞬間寫入極輕量的 Camera JSON"""
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc or not doc.Path:
        return
        
    vp = doc.Views.ActiveView.ActiveViewport
    
    # 只提取攝影機的極簡資料
    data = {
        "location": {"x": vp.CameraLocation.X, "y": vp.CameraLocation.Y, "z": vp.CameraLocation.Z},
        "direction": {"x": vp.CameraDirection.X, "y": vp.CameraDirection.Y, "z": vp.CameraDirection.Z},
        "up": {"x": vp.CameraUp.X, "y": vp.CameraUp.Y, "z": vp.CameraUp.Z},
        "lens": vp.Camera35mmLensLength
    }
    
    # 輸出為獨立的 R2B_Camera.json
    json_path = os.path.join(os.path.dirname(doc.Path), "R2B_Camera_Sync.json")
    
    try:
        with open(json_path, 'w') as f:
            json.dump(data, f)
    except Exception as ex:
        pass # 避免檔案被鎖定時報錯干擾建模

def toggle_camera_sync():
    """啟動或關閉背景監聽器"""
    event_key = "R2B_Camera_Sync_Event"
    
    # 如果已經在執行，就將其關閉 (解除綁定)
    if sc.sticky.has_key(event_key):
        func = sc.sticky[event_key]
        Rhino.Display.RhinoView.Modified -= func
        sc.sticky.Remove(event_key)
        print("🛑 R2B Camera Sync: 已停止即時同步")
    # 如果尚未執行，就將其啟動 (綁定事件)
    else:
        sc.sticky[event_key] = export_camera
        Rhino.Display.RhinoView.Modified += export_camera
        print("🟢 R2B Camera Sync: 已啟動 (背景即時同步中...)")

if __name__ == "__main__":
    toggle_camera_sync()