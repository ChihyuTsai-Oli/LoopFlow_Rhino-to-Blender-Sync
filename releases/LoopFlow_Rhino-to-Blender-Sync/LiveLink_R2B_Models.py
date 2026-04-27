# -*- coding: utf-8 -*-
"""
=================================================
LiveLink Rhino to Blender (Model Exporter)
=================================================
程式名稱 : LiveLink_R2B_Models
版本     : v3.0
日期     : 2026-04-27
開發者   : Cursor + Claude Sonnet 4.6
開發環境 : Rhino 8 / CPython 3.9
同步檔案 : 由 R2B_Path.txt 的 ModelFile 欄位決定（預設 R2B.3dm）

【系統概述 / System Overview】
本程式旨在最佳化 Rhino 與 Blender 之間的 Render 協作流程。透過自動化處理，
確保匯出至 Blender 的模型達到「即插即用」的純淨度。

【功能與操作指南 / Features & Operations】
▶ 功能描述：
   1. 圖層選擇：每次執行時彈出圖層選擇視窗，僅匯出指定母圖層及其子圖層的物件；
      上次選擇記憶為預設值，存入 R2B_Path.txt 的 LastModelLayer 欄位。
   2. 輸出路徑：ModelDir 不為空時輸出至 ModelDir；空白時 fallback 至 Rhino 作業檔同目錄。
   3. 深度環境清理：自動刪除 Layout、點、線、文字點、標註及剖面線等非渲染物件。
   4. 圖層邏輯最佳化：自動顯示/解鎖所有圖層；刪除包含 "//" 的輔助圖層及其物件。
   5. 材質標準化：材質定義與圖層顏色同步，並轉換為可被 Blender 識別的材質結構。
   6. UV 映射標準化：強制清除既有貼圖通道，統一套用 BoxMapSize × BoxMapSize × BoxMapSize 的 Box Mapping。
▶ 操作方式：
   - 在 Rhino 中儲存工作檔後執行本腳本，於彈出視窗中選擇要匯出的模型圖層。
   - 腳本完成後會自動切換回原始工作檔，中轉檔留存於指定目錄供 Blender 匯入使用。

【變數連動注意事項】
- orig_full_path：使用 sc.doc.Path 取得完整路徑，需確保 Rhino 檔案已儲存。
- export_full_path：由 ModelDir（空白時 fallback 至 Rhino 作業檔同目錄）+ ModelFile 組合。
- BoxMapSize：從 R2B_Path.txt 的 BoxMapSize 欄位讀取，預設 500。
- LastModelLayer：記憶上次選擇的圖層，作為下次彈出視窗的預設值。
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B_Config import load_r2b_config, save_r2b_config

def RhinoLiveLinkSync():
    # --- 1. 環境設定與路徑檢查 ---
    orig_full_path = sc.doc.Path
    if not orig_full_path:
        rs.MessageBox("請先儲存目前的 Rhino 檔案！")
        return

    cfg = load_r2b_config()

    # --- 2. 圖層選擇視窗（記憶上次選擇） ---
    last_layer = cfg.get("LastModelLayer") or None
    target_layer = rs.GetLayer("選擇要匯出的模型圖層", default_layer=last_layer)
    if not target_layer:
        return
    cfg["LastModelLayer"] = target_layer
    save_r2b_config(cfg)

    # --- 3. 決定輸出路徑 ---
    model_dir = cfg.get("ModelDir", "").strip() or os.path.dirname(orig_full_path)
    export_full_path = os.path.join(model_dir, cfg["ModelFile"])

    # BoxMapSize 設定
    box_size = cfg.get("BoxMapSize", "500").strip() or "500"

    # 關閉螢幕重繪提升效能
    rs.EnableRedraw(False)

    try:
        # --- 4. 建立保險方塊（防止 Export 遇到空場景報錯）---
        pts = [[0,0,0], [1,0,0], [1,1,0], [0,1,0], [0,0,1], [1,0,1], [1,1,1], [0,1,1]]
        rs.AddBox(pts)

        # --- 5. 依選取圖層篩選要匯出的物件 ---
        rs.UnselectAllObjects()

        # 先對所有圖層解鎖/顯示
        for layer in sc.doc.Layers:
            if not layer.IsDeleted:
                layer.IsLocked = False
                layer.IsVisible = True
                layer.CommitChanges()

        rs.Command("_Show _Unlock", False)

        # 選取目標圖層（及其子圖層）內的物件
        target_fullpaths = set()
        for layer in sc.doc.Layers:
            if layer is None or layer.IsDeleted:
                continue
            fp = layer.FullPath
            if fp == target_layer or fp.startswith(target_layer + "::"):
                target_fullpaths.add(fp)

        if not target_fullpaths:
            print("R2B Models: 找不到目標圖層 {}，匯出取消。".format(target_layer))
            return

        for layer_fp in target_fullpaths:
            layer_objs = rs.ObjectsByLayer(layer_fp)
            if layer_objs:
                rs.SelectObjects(layer_objs)

        # 加入保險方塊（確保至少有一個物件可匯出）
        rs.Command("_SelAll", False)

        if os.path.exists(export_full_path):
            try:
                os.remove(export_full_path)
            except Exception:
                pass

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        # --- 6. 執行匯出 ---
        quote = chr(34)
        export_cmd = '_-ExportWithOrigin _0,0,0 ' + quote + export_full_path + quote + ' _Enter _Enter'
        rs.Command(export_cmd, False)

        # --- 7. 開啟中轉檔進行清理 ---
        rs.DocumentModified(False)
        rs.Command('_-Open ' + quote + export_full_path + quote + ' _Enter', False)

        # =========================================================
        # 【純 API 靜默清理區】
        # =========================================================
        pages = sc.doc.Views.GetPageViews()
        if pages:
            for page in pages:
                try:
                    page.Close()
                except Exception:
                    pass

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
        for mat in mats:
            sc.doc.Materials.Remove(mat)
        rms = [rm for rm in sc.doc.RenderMaterials]
        for rm in rms:
            sc.doc.RenderMaterials.Remove(rm)

        for layer in sc.doc.Layers:
            if layer.IsDeleted:
                continue
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
        mapping_macro = "-ApplyBoxMapping _Center 0,0,0 {0} {0} {0} _Yes _Single _Enter _Enter _Enter".format(box_size)
        rs.Command(mapping_macro, False)
        rs.Command("_SelNone", False)

        purge_cmd = "_-Purge _BlockDefinitions=Yes _AnnotationStyles=Yes _Groups=Yes _HatchPatterns=Yes _Layers=Yes _Linetypes=Yes _Materials=Yes _Textures=Yes _Environments=Yes _Bitmaps=Yes _Enter"
        rs.Command(purge_cmd, False)

        # =========================================================
        # 存檔與無縫切換邏輯
        # =========================================================
        save_cmd = '_-SaveAs _Version=8 "{}" _Enter'.format(export_full_path)
        rs.Command(save_cmd, False)

        rs.DocumentModified(False)
        return_cmd = '_-Open "{}" _Enter'.format(orig_full_path)
        rs.Command(return_cmd, False)

    finally:
        rs.EnableRedraw(True)
        print("R2B Models: 模型同步輸出完成，已回到工作檔。（輸出：{}）".format(export_full_path))

if __name__ == "__main__":
    RhinoLiveLinkSync()
