# -*- coding: utf-8 -*-
"""
=================================
LiveLink Rhino to Blender (Light Sender)
=================================
程式名稱 : LiveLink_R2B_Light
版本     : v2.0
日期     : 2026-04-14
開發者   : Cursor + Claude Sonnet 4.6
開發環境 : Rhino 8 / CPython 3.9
同步檔案 : R2B_Light_Sync.json、R2B_Path.txt

【系統概述 / System Overview】
本腳本為 Rhino 端的「燈光點位手動匯出引擎」。
負責將 Rhino 場景中的點物件 (Points) 轉化為 BIM 燈光組裝資料。

【功能與操作指南 / Features & Operations】
▶ 功能描述：
   - 自動讀取 Rhino 專案同目錄下的 `R2B_Path.txt`，
     僅針對設定檔內指定的圖層 (及其子圖層) 進行燈光點位掃描。
   - 自動生成設定：若 `R2B_Path.txt` 不存在，執行時會自動建立並寫入預設圖層 `R2B_LT_Points`。
   - 自動提取點位所在的「末端子圖層名稱」作為母體對位類型 (Type)。
   - 提取點位的 XYZ 空間座標。
   - 將所有符合條件的點位打包並輸出至專案同目錄下的 `R2B_Light_Sync.json`。
▶ 操作方式：
   - 確認 `R2B_Path.txt` 中的圖層路徑設定正確 (可包含多個路徑，一行一個)。
   - 在指定的圖層 (如 R2B_LT_Points::嵌燈) 中放置點物件代表燈光位置。
   - 執行本腳本，指令列會提示成功打包的點位數量，隨後即可至 Blender 端進行同步。

【變數連動注意事項】
- R2B_Path.txt：每行一個 Rhino 圖層路徑，開頭為 `#` 的行視為註解略過。
- target_layers：由設定檔動態載入，子圖層以 `startswith` 方式比對，確保子圖層均納入掃描。
- layer_short：取 `::` 分割後的最末段名稱，對應 Blender 端的燈具母體 (Type) 識別符。
- json 輸出路徑依賴 rs.DocumentPath()，執行前需確保 Rhino 檔案已儲存。
"""
import rhinoscriptsyntax as rs
import os
import json

def export_lights():
    """手動執行：依據 R2B_Path.txt 設定掃描點位並寫入 Lights JSON"""
    doc_path = rs.DocumentPath()
    if not doc_path:
        print("⚠️ 請先將 Rhino 檔案儲存，才能產生 JSON 與設定檔案！")
        return
        
    nDir = os.path.dirname(doc_path)
    txt_path = os.path.join(nDir, "R2B_Path.txt")
    target_layers = []
    
    # 1. 檢查並讀取/生成 R2B_Path.txt
    if not os.path.exists(txt_path):
        try:
            with open(txt_path, 'w') as f:
                f.write("R2B_LT_Points\n")
            target_layers.append("R2B_LT_Points")
            print(">> 已自動生成預設圖層路徑設定檔：R2B_Path.txt (預設: R2B_LT_Points)")
        except Exception as e:
            print("❌ 無法建立設定檔: {}".format(e))
            return
    else:
        try:
            with open(txt_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    cleaned_line = line.strip()
                    # 略過空行與註解符號開頭的行
                    if cleaned_line and not cleaned_line.startswith("#"):
                        target_layers.append(cleaned_line)
        except Exception as e:
            print("❌ 讀取設定檔失敗: {}".format(e))
            return
            
    if not target_layers:
        print("⚠️ R2B_Path.txt 內容為空，請填入要抓取的燈光圖層路徑！")
        return

    # 2. 抓取場景中所有的「點 (Point)」物件 (代碼 1)
    points = rs.ObjectsByType(1)
    data = {"points": []}
    
    if points:
        for pt in points:
            # 取得該點位的完整圖層路徑 (例如: R2B_LT_Points::嵌燈)
            layer_full = rs.ObjectLayer(pt)
            
            # 檢查這個點是否在我們指定的母圖層 (或其子圖層) 底下
            is_valid_layer = False
            for target in target_layers:
                if layer_full.startswith(target):
                    is_valid_layer = True
                    break
            
            # 如果圖層符合，才進行紀錄
            if is_valid_layer:
                # 切除父圖層，只保留最後的子圖層名稱當作母體 Type (例如: 嵌燈)
                layer_short = layer_full.split("::")[-1]
                
                # 取得座標
                coord = rs.PointCoordinates(pt)
                
                # 打包點位資料
                data["points"].append({
                    "guid": str(pt),
                    "type": layer_short,
                    "loc": [coord.X, coord.Y, coord.Z]
                })
            
    # 3. 輸出為獨立的 R2B_Light_Sync.json
    json_path = os.path.join(nDir, "R2B_Light_Sync.json")
    
    try:
        with open(json_path, 'w') as f:
            # 加入 indent 讓 JSON 格式化，方便除錯
            json.dump(data, f, indent=4)
        print(">> 燈光點位已依據設定檔匯出！共成功打包了 {} 個點位。".format(len(data["points"])))
    except Exception as e:
        print("❌ 匯出失敗: {}".format(e))

if __name__ == "__main__":
    export_lights()