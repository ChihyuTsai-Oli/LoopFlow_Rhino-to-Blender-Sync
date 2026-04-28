# -*- coding: utf-8 -*-
"""
=================================================
LiveLink Rhino to Blender (Model Exporter)
=================================================
程式名稱 : LiveLink_R2B_Models
版本     : v2.0
日期     : 2026-04-14
開發者   : Cursor + Claude Sonnet 4.6
開發環境 : Rhino 8 / CPython 3.9
同步檔案 : _R2B_Model.3dm

【系統概述 / System Overview】
本程式旨在最佳化 Rhino 與 Blender 之間的 Render 協作流程。透過自動化處理，
確保匯出至 Blender 的模型達到「即插即用」的純淨度。

【功能與操作指南 / Features & Operations】
▶ 功能描述：
   1. 影子存檔機制：自動建立中轉檔案 (_R2B_Model.3dm)，確保原始工作檔不受影響。
   2. 深度環境清理：自動刪除 Layout 圖紙、點 (Point)、線 (Curve)、文字點 (Dot)、
      標註 (Dimension) 及剖面線 (Hatch) 等 Render 不需要之物件。
   3. 圖層邏輯最佳化：
      - 自動將所有圖層設為顯示並解鎖。
      - 精準過濾：自動刪除所有包含 "//" 的輔助圖層 (如 Grasshopper 生成物) 及其物件。
   4. 材質標準化：將材質定義與圖層顏色同步，並轉換為可被 Blender 識別的材質結構。
   5. UV 映射標準化：強制清除物件既有貼圖通道，並統一套用 500x500x500 的 Box Mapping。
▶ 操作方式：
   - 在 Rhino 中儲存工作檔後執行本腳本。
   - 腳本完成後會自動切換回原始工作檔，中轉檔留存於同目錄供 Blender 匯入使用。

【變數連動注意事項】
- orig_full_path：使用 sc.doc.Path 取得完整路徑，需確保 Rhino 檔案已儲存。
- export_full_path：中轉檔固定命名為 _R2B_Model.3dm，存於原始檔同目錄。
- Box Mapping 尺寸 (500x500x500)：若需調整貼圖比例，修改 mapping_macro 中的三個數值。
- 清除材質的迴圈需在 ExplodeBlock 之後執行，避免殘留 Block 內部材質。
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import os

def RhinoLiveLinkSync():
    # --- 1. 環境設定與路徑檢查 (改用 sc.doc.Path 確保抓到完整路徑) ---
    orig_full_path = sc.doc.Path
    if not orig_full_path:
        rs.MessageBox("請先儲存目前的 Rhino 檔案！")
        return

    nDir = os.path.dirname(orig_full_path)
    export_full_path = os.path.join(nDir, "_R2B_Model.3dm")

    # 關閉螢幕重繪提升效能
    rs.EnableRedraw(False) 
    original_selection = rs.SelectedObjects()
    
    try:
        # --- 2. 建立保險方塊 (改用 API 建立，防卡死) ---
        pts = [[0,0,0], [1,0,0], [1,1,0], [0,1,0], [0,0,1], [1,0,1], [1,1,1], [0,1,1]]
        rs.AddBox(pts)
        
        # --- 3. 準備匯出內容 ---
        rs.UnselectAllObjects()
        
        # 在原檔案先做初步的顯示與解鎖
        for layer in sc.doc.Layers:
            if not layer.IsDeleted:
                layer.IsLocked = False
                layer.IsVisible = True
                layer.CommitChanges()
                
        rs.Command("_Show _Unlock _SelAll", False)
        
        if os.path.exists(export_full_path):
            try: os.remove(export_full_path)
            except: pass

        # --- 4. 執行匯出 ---
        quote = chr(34)
        export_cmd = '_-ExportWithOrigin _0,0,0 ' + quote + export_full_path + quote + ' _Enter _Enter'
        rs.Command(export_cmd, False)
        
        # --- 5. 開啟中轉檔進行清理 ---
        # 欺騙 Rhino 當前沒有修改，強制開啟轉存檔
        rs.DocumentModified(False)
        rs.Command('_-Open ' + quote + export_full_path + quote + ' _Enter', False)
        
        # =========================================================
        # 【純 API 靜默清理區】
        # =========================================================
        
        pages = sc.doc.Views.GetPageViews()
        if pages:
            for page in pages:
                try: page.Close()
                except: pass
                
        for layer in sc.doc.Layers:
            if not layer.IsDeleted:
                layer.IsLocked = False
                layer.IsVisible = True
                layer.CommitChanges()

        for layer in sc.doc.Layers:
            if not layer.IsDeleted and "//" in layer.FullPath:
                layer_objs = rs.ObjectsByLayer(layer.FullPath)
                if layer_objs:
                    rs.DeleteObjects(layer_objs)
                    
        for obj_type in [1, 4, 512, 8192, 65536]:
            useless_objs = rs.ObjectsByType(obj_type)
            if useless_objs:
                rs.DeleteObjects(useless_objs)
                
        # =========================================================
        # 指令區
        # =========================================================
        rs.Command("_ExplodeBlock _AllBlocks", False) 
        rs.Command("_SelAll _UngroupAll _SelNone", False) 
        
        mats = [mat for mat in sc.doc.Materials] 
        for mat in mats: sc.doc.Materials.Remove(mat) 
        rms = [rm for rm in sc.doc.RenderMaterials] 
        for rm in rms: sc.doc.RenderMaterials.Remove(rm) 

        for layer in sc.doc.Layers:
            if layer.IsDeleted: continue
            path_parts = layer.FullPath.split("::")
            short_name = "::".join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
            temp_mat = Rhino.DocObjects.Material()
            temp_mat.Name = short_name
            temp_mat.DiffuseColor = layer.Color
            render_mat = Rhino.Render.RenderMaterial.CreateBasicMaterial(temp_mat, sc.doc)
            sc.doc.RenderMaterials.Add(render_mat)
            layer.RenderMaterial = render_mat

        for obj in sc.doc.Objects:
            attr = obj.Attributes
            attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer 
            obj.CommitChanges()

        rs.Command("_SelAll", False)
        rs.Command("_-RemoveMappingChannel 1 _Enter", False)
        mapping_macro = "-ApplyBoxMapping _Center 0,0,0 500 500 500 _Yes _Single _Enter _Enter _Enter"
        rs.Command(mapping_macro, False)
        rs.Command("_SelNone", False)
        
        purge_cmd = "_-Purge _BlockDefinitions=Yes _AnnotationStyles=Yes _Groups=Yes _HatchPatterns=Yes _Layers=Yes _Linetypes=Yes _Materials=Yes _Textures=Yes _Environments=Yes _Bitmaps=Yes _Enter"
        rs.Command(purge_cmd, False) 
        
        # =========================================================
        # 存檔與無縫切換邏輯 (已修正)
        # =========================================================
        # 1. 儲存目前已經清理完畢的中轉檔
        save_cmd = '_-SaveAs _Version=8 "{}" _Enter'.format(export_full_path)
        rs.Command(save_cmd, False) 
        
        # 2. 強制解除修改標記，直接用絕對路徑開啟原工作檔
        rs.DocumentModified(False)
        return_cmd = '_-Open "{}" _Enter'.format(orig_full_path)
        rs.Command(return_cmd, False)
        
    finally:
        rs.EnableRedraw(True)
        print(">> LiveLink Rhino to Blender: 模型同步輸出完成，已回到工作檔。")

if __name__ == "__main__":
    RhinoLiveLinkSync()