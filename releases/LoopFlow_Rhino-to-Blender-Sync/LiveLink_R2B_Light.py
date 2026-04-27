# -*- coding: utf-8 -*-
"""
=================================
LiveLink Rhino to Blender (Light Sender)
=================================
程式名稱 : LiveLink_R2B_Light
版本     : v3.0
日期     : 2026-04-27
開發者   : Cursor + Claude Sonnet 4.6
開發環境 : Rhino 8 / CPython 3.9
同步檔案 : 由 R2B_Path.txt 的 LightFile 欄位決定（預設 R2B_Light_Sync.json）

【系統概述 / System Overview】
本腳本為 Rhino 端的「燈光點位手動匯出引擎」。
負責將 Rhino 場景中的點物件 (Points) 轉化為 BIM 燈光組裝資料。

【功能與操作指南 / Features & Operations】
▶ 功能描述：
   - 自動讀取 R2B_Path.txt，僅針對 LightLayer 指定的圖層（及其子圖層）進行燈光點位掃描。
   - 自動生成設定：若 R2B_Path.txt 不存在，執行時會自動建立並寫入所有預設欄位。
   - 自動提取點位所在的「末端子圖層名稱」作為母體對位類型 (Type)。
   - 提取點位的 XYZ 空間座標。
   - 將所有符合條件的點位打包並輸出至 DataPath 目錄下。
▶ 操作方式：
   - 確認 R2B_Path.txt 中的 LightLayer 設定正確。
   - 在指定的圖層（如 R2B_LT_Points::嵌燈）中放置點物件代表燈光位置。
   - 執行本腳本，指令列會提示成功打包的點位數量，隨後即可至 Blender 端進行同步。

【變數連動注意事項】
- R2B_Path.txt：由 LiveLink_R2B_Config.py 統一管理，不依賴 doc.Path。
- LightLayer：target_layer 前綴，子圖層以 startswith 方式比對。
- layer_short：取 :: 分割後的最末段名稱，對應 Blender 端的燈具母體 (Type) 識別符。
- json 輸出路徑由 DataPath + LightFile 決定，不依賴 doc.Path。
"""
import rhinoscriptsyntax as rs
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B_Config import load_r2b_config, DATA_DIR

def export_lights():
    """手動執行：依據 R2B_Path.txt 設定掃描點位並寫入 Lights JSON"""
    cfg = load_r2b_config()
    target_layer = cfg["LightLayer"]
    target_prefix = target_layer  # startswith 比對

    # 2. 抓取場景中所有的「點 (Point)」物件（代碼 1）
    points = rs.ObjectsByType(1)
    data = {"points": []}

    if points:
        for pt in points:
            layer_full = rs.ObjectLayer(pt)

            if not layer_full.startswith(target_prefix):
                continue

            # 切除父圖層，只保留最後的子圖層名稱當作母體 Type
            layer_short = layer_full.split("::")[-1]
            coord = rs.PointCoordinates(pt)

            data["points"].append({
                "guid": str(pt),
                "type": layer_short,
                "loc": [coord.X, coord.Y, coord.Z]
            })

    # 3. 輸出至 DataPath + LightFile
    json_path = os.path.join(cfg["DataPath"], cfg["LightFile"])

    try:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        print("R2B Light: 燈光點位已匯出！共成功打包了 {} 個點位（輸出至 {}）".format(
            len(data["points"]), json_path
        ))
    except Exception as e:
        print("R2B Light: 匯出失敗: {}".format(e))

if __name__ == "__main__":
    export_lights()
