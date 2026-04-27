# -*- coding: utf-8 -*-
"""
====================================
Import Rhinoceros 3D (R2B Pro)
====================================
版本 (Version) : v5.0
日期 (Date)    : 2026-04-27
開發者 (Author) : Cursor + Claude Sonnet 4.6
開發環境 (Env)  : Blender 4.5.0 / Python 3.11
位置 (Location) : 3D Viewport 側邊欄 (N-Panel > LoopFlow 3dm > Rhino Live Link)

【系統概述 / System Overview】
本外掛為「Rhino into Blender 工作流」的 Blender 端接收器。
旨在打破雙軟體間的壁壘，提供包含幾何體無縫更新、雙 JSON 效能分離連動、
全自動燈光組裝，以及 BIM 自動材質指派等自動化Render解決方案。

【核心功能與操作指南 / Core Features & Operations】

1. 幾何體無縫更新 (Model Sync & State Memory)
   ▶ 功能描述：支援首次載入與後續更新。更新時會自動防呆去重，並完美保留
      使用者在 Blender 中手動設定的「排除、隱藏、算圖關閉」與效能顯示模式(Bounds)。
   ▶ 操作方式：Rhino 端執行 LiveLink_R2B_Models.py（選擇圖層後產生 R2B.3dm）；
      Blender 端點擊 [Import Models] 或 [Update Models]。

2. 雙 JSON 引擎：攝影機與燈光同步 (Dual Engine Real-time Sync)
   ▶ 功能描述：
      - 攝影機 (Camera)：背景每 CAMERA_POLL_INTERVAL 秒掃描 R2B_Camera_Sync.json，極度輕量保證 60FPS。
      - 燈光 (Lights)：獨立為「手動更新」，讀取 R2B_Light_Sync.json。
      - 精確對位與防殘留：採用精確對位更新法，強制復位被亂移的燈具。具備同生共死引擎，
        Rhino 刪除點位，Blender 端乾淨回收，徹底杜絕 StructRNA 幽靈報錯。
   ▶ 操作方式：
      - 建立 COL_FIXTURES (放模型) 與 COL_LIGHTING (放燈光) 集合，並對齊母體。
      - 在面板的 [Sync Folder] 指定 JSON 所在目錄。
      - 攝影機：點擊 [Start Camera Sync] 啟動背景連動。
      - 燈光：Rhino 端匯出點位後，點擊 [Sync Rhino Lights] 進行一鍵更新。

3. 全自動基礎材質指派 (Auto Basic Material Assigner)
   ▶ 功能描述：
      - 通用與特化綁定：切除前綴後智慧全場指派；並強制 LAYER_SUFFIX_LT 巢狀圖層內所有物件
        (含無材質空槽) 無痛綁定為指定發光材質。
      - 終極防護印章與本尊機制：內建「本尊尋找機制」。更新模型時若產生無印章的 .001，
        腳本會自動將其靈魂轉移回「已手動調整並蓋過印章的本尊材質」，徹底根除材質增生與覆蓋。
   ▶ 操作方式：
      - 在 `Materials` 放入物件並賦予母體材質（如 DW_Glass, D_Frame；LAYER_SUFFIX_LT 指定為 MAT_PRESET_LT_K）。
      - 點擊 [Assign Basic Mat.] 按鈕，瞬間完成全場精確替換。

【變數連動與注意事項 / Notes】
- 同步目錄由 RHINO_OT_ResetPath 自動填入 R2B_Path.txt 的 DataPath 目錄。
- 燈光同步依賴於 COL_FIXTURES 與 COL_LIGHTING 集合中的母體物件名稱。
- 攝影機同步為背景 Timer 運作，關閉外掛或 Blender 前建議先點擊 [Stop Camera Sync]。

"""

bl_info = {
    "name": "Import Rhinoceros 3D (R2B Pro)",
    "author": "Nathan 'jesterKing' Letwory, Joel Putnam, Tom Svilans, Lukas Fertig, Bernd Moeller, Workflow Partner",
    "version": (0, 0, 50),
    "blender": (4, 5, 0),
    "location": "N-Panel > LoopFlow 3dm",
    "description": "R2B 雙 JSON 效能版 (V50 常數集中化 + LoopFlow 3dm Panel)",
    "category": "Import-Export",
}

import bpy
import os
import re
import json
import mathutils
from .read3dm import read_3dm
from bpy_extras.io_utils import ImportHelper

# -------------------------------------------------------------------
# 模組層級常數（集中管理，方便日後調整）
# -------------------------------------------------------------------

# 同步檔名
CAMERA_SYNC_FILE   = "R2B_Camera_Sync.json"
LIGHT_SYNC_FILE    = "R2B_Light_Sync.json"

# Collection 名稱
COL_FIXTURES       = "Lighting Fixtures"
COL_LIGHTING       = "Lighting"
COL_LIGHT_POINTS   = "R2B Lighting Points"
COL_MATERIALS      = "Materials"       # Assign Basic Mat. 母體庫 Collection（功能暫停用）

# 材質相關常數
MAT_PRESET_LT_K    = "Preset_Lighting_K"
LAYER_SUFFIX_LT    = "5_LT"
MAT_AUTO_5LT       = "Auto_5LT_Light"

# 技術參數
CAMERA_POLL_INTERVAL = 0.03     # 攝影機輪詢間隔（秒）
DEFAULT_LENS         = 50.0     # 焦距預設值（mm）
EMPTY_DISPLAY_SIZE   = 0.3      # 燈光點位 Empty 顯示大小

# -------------------------------------------------------------------
# 1. 核心輔助函數
# -------------------------------------------------------------------
def merge_duplicate_materials():
    count = 0
    for mat in bpy.data.materials:
        match = re.match(r"(.*)\.\d{3}$", mat.name)
        if match:
            base_name = match.group(1)
            base_mat = bpy.data.materials.get(base_name)
            if base_mat and base_mat != mat:
                mat.user_remap(base_mat)
                bpy.data.materials.remove(mat)
                count += 1
    return count

def get_template_objects(type_name):
    templates = []
    clean_type = type_name.strip()
    for col_name in [COL_FIXTURES, COL_LIGHTING]:
        col = bpy.data.collections.get(col_name)
        if col:
            for obj in col.objects:
                base_name = re.sub(r'\.\d{3}$', '', obj.name).strip()
                if base_name == clean_type:
                    templates.append(obj)
                    break
    return templates

def get_all_objects_in_collection(collection):
    objs = set(collection.objects)
    for child in collection.children:
        objs.update(get_all_objects_in_collection(child))
    return objs

# -------------------------------------------------------------------
# 2. 視窗同步引擎 (純攝影機 - 極度輕量化)
# -------------------------------------------------------------------
def update_viewport_from_json():
    wm = bpy.context.window_manager
    scene = bpy.context.scene
    if wm.get("livelink_viewport_active", 0) == 0:
        return None

    json_dir = bpy.path.abspath(scene.rhino_json_dir)
    json_path = os.path.join(json_dir, CAMERA_SYNC_FILE)

    scale_factor = scene.rhino_cam_scale
    lens_mult = scene.rhino_cam_lens_mult

    if not os.path.exists(json_path):
        return CAMERA_POLL_INTERVAL

    try:
        current_mtime = os.path.getmtime(json_path)
        last_mtime = wm.get("livelink_last_mtime", 0.0)

        if current_mtime == last_mtime:
            return CAMERA_POLL_INTERVAL
        wm["livelink_last_mtime"] = current_mtime

        with open(json_path, 'r') as f:
            data = json.load(f)

        raw_x = data["location"]["x"] * scale_factor
        raw_y = data["location"]["y"] * scale_factor
        raw_z = data["location"]["z"] * scale_factor
        loc = mathutils.Vector((raw_x, raw_y, raw_z))

        dir_vec = mathutils.Vector((data["direction"]["x"], data["direction"]["y"], data["direction"]["z"])).normalized()
        up_vec  = mathutils.Vector((data["up"]["x"], data["up"]["y"], data["up"]["z"])).normalized()

        base_lens = data.get("lens", DEFAULT_LENS)
        final_lens = base_lens * lens_mult

        z_axis = -dir_vec
        x_axis = up_vec.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()

        mat = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed()
        rot_quat = mat.to_quaternion()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                rv3d = space.region_3d
                if rv3d.view_perspective != 'PERSP':
                    rv3d.view_perspective = 'PERSP'
                space.lens = final_lens
                rv3d.view_rotation = rot_quat
                rv3d.view_location = loc + dir_vec * rv3d.view_distance
                area.tag_redraw()

    except Exception:
        pass

    return CAMERA_POLL_INTERVAL

# -------------------------------------------------------------------
# 3. 燈光同步引擎 (手動按鈕觸發)
# -------------------------------------------------------------------
class RHINO_OT_SyncLights(bpy.types.Operator):
    bl_idname = "import_3dm.sync_lights"
    bl_label = "Sync Rhino Lights"
    bl_description = "讀取 R2B_Light_Sync.json，手動執行燈光母體對位、生成與孤兒回收"

    def execute(self, context):
        scene = context.scene
        json_dir = bpy.path.abspath(scene.rhino_json_dir)
        json_path = os.path.join(json_dir, LIGHT_SYNC_FILE)
        scale_factor = scene.rhino_cam_scale

        if not os.path.exists(json_path):
            self.report({'WARNING'}, f"找不到檔案: {json_path}！請確認目錄正確。")
            return {'CANCELLED'}

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            if "points" not in data:
                self.report({'INFO'}, "JSON 中沒有燈光點位資料。")
                return {'FINISHED'}

            light_col = bpy.data.collections.get(COL_LIGHT_POINTS)
            if not light_col:
                light_col = bpy.data.collections.new(COL_LIGHT_POINTS)
                bpy.context.scene.collection.children.link(light_col)

            active_guids = set()

            for pt_data in data["points"]:
                guid = pt_data["guid"]
                active_guids.add(guid)
                pt_type = pt_data["type"]
                pt_loc = mathutils.Vector((
                    pt_data["loc"][0] * scale_factor,
                    pt_data["loc"][1] * scale_factor,
                    pt_data["loc"][2] * scale_factor
                ))

                target_empty = None
                for obj in light_col.objects:
                    try:
                        if obj.get("rhino_guid") == guid:
                            target_empty = obj
                            break
                    except ReferenceError:
                        pass

                if target_empty:
                    target_empty.location = pt_loc
                else:
                    new_empty = bpy.data.objects.new(f"RH_{pt_type}_{guid[:5]}", None)
                    new_empty.empty_display_type = 'PLAIN_AXES'
                    new_empty.empty_display_size = EMPTY_DISPLAY_SIZE
                    new_empty["rhino_guid"] = guid
                    new_empty["rhino_type"] = pt_type
                    light_col.objects.link(new_empty)
                    new_empty.location = pt_loc
                    target_empty = new_empty

                    for potential_child in bpy.data.objects:
                        try:
                            if potential_child.get("recovered_rhino_guid") == guid:
                                world_mat = potential_child.matrix_world.copy()
                                potential_child.parent = target_empty
                                potential_child.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                                parent_future_world = mathutils.Matrix.Translation(pt_loc)
                                potential_child.matrix_local = parent_future_world.inverted() @ world_mat
                                del potential_child["recovered_rhino_guid"]
                        except ReferenceError:
                            pass

                templates = get_template_objects(pt_type)
                processed_insts = []

                for template in templates:
                    safe_name = re.sub(r'\.\d{3}$', '', template.name)
                    prefix = f"INST_{safe_name}_{guid[:5]}"

                    existing_inst = None
                    for c in target_empty.children:
                        try:
                            if c.name.startswith(prefix) and c not in processed_insts:
                                existing_inst = c
                                break
                        except ReferenceError:
                            pass

                    if existing_inst:
                        existing_inst.location = template.location
                        existing_inst.rotation_euler = template.rotation_euler
                        existing_inst.scale = template.scale
                        processed_insts.append(existing_inst)
                    else:
                        new_inst = template.copy()
                        if template.data:
                            new_inst.data = template.data
                        new_inst.name = prefix
                        light_col.objects.link(new_inst)

                        new_inst.parent = target_empty
                        new_inst.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                        new_inst.location = template.location
                        new_inst.rotation_euler = template.rotation_euler
                        new_inst.scale = template.scale
                        processed_insts.append(new_inst)

                for c in list(target_empty.children):
                    try:
                        if c.name.startswith("INST_") and c not in processed_insts:
                            bpy.data.objects.remove(c, do_unlink=True)
                    except ReferenceError:
                        pass

            # 【V49 修復】點位刪除連坐機制
            empties_to_remove = []
            for obj in light_col.objects:
                try:
                    if "rhino_guid" in obj and obj["rhino_guid"] not in active_guids:
                        empties_to_remove.append(obj)
                except ReferenceError:
                    pass

            for empty in empties_to_remove:
                try:
                    removed_guid = empty["rhino_guid"]
                    for child in list(empty.children):
                        try:
                            if child.name.startswith("INST_"):
                                bpy.data.objects.remove(child, do_unlink=True)
                            else:
                                child["recovered_rhino_guid"] = removed_guid
                                world_mat = child.matrix_world.copy()
                                child.parent = None
                                child.matrix_world = world_mat
                        except ReferenceError:
                            pass
                    bpy.data.objects.remove(empty, do_unlink=True)
                except ReferenceError:
                    pass

            self.report({'INFO'}, f"✨ 燈光同步完成！共處理了 {len(data['points'])} 個點位。")
        except Exception as e:
            self.report({'ERROR'}, f"同步失敗: {e}")

        return {'FINISHED'}

# -------------------------------------------------------------------
# 4. 其他功能運算子 (Operators)
# -------------------------------------------------------------------

# ===========================================================================
# [DISABLED] RHINO_OT_AssignBasicMat — Assign Basic Mat. 全場材質自動指派
# 取消下方所有 # 前綴可重新啟用；同時需取消 classes tuple 與 Panel draw 中的對應註解
# ===========================================================================
# class RHINO_OT_AssignBasicMat(bpy.types.Operator):
#     bl_idname = "import_3dm.assign_basic_mat"
#     bl_label = "Assign Basic Mat."
#     bl_description = "自動掃描 Materials 母體庫，以關鍵字替換全場材質"
#
#     def execute(self, context):
#         mat_col = bpy.data.collections.get(COL_MATERIALS)
#         if not mat_col:
#             self.report({'WARNING'}, "找不到 'Materials' Collection，請先建立並放入母體物件！")
#             return {'CANCELLED'}
#
#         assigned_phase1 = 0
#         assigned_phase2 = 0
#
#         # 第一階段：特化規則 LAYER_SUFFIX_LT（本尊尋找防呆版）
#         preset_k_mat = None
#         for obj in mat_col.objects:
#             if MAT_PRESET_LT_K in obj.name and obj.material_slots and obj.material_slots[0].material:
#                 preset_k_mat = obj.material_slots[0].material
#                 break
#             for slot in obj.material_slots:
#                 if slot.material and MAT_PRESET_LT_K in slot.material.name:
#                     preset_k_mat = slot.material
#                     break
#             if preset_k_mat:
#                 break
#
#         if not preset_k_mat:
#             self.report({'WARNING'}, f"在 {COL_MATERIALS} 集合中找不到包含 '{MAT_PRESET_LT_K}' 的材質，跳過 {LAYER_SUFFIX_LT} 綁定！")
#         else:
#             target_objs = set()
#             for col in bpy.data.collections:
#                 col_base = col.name.split('.')[0].strip()
#                 if col_base.endswith(LAYER_SUFFIX_LT):
#                     target_objs.update(get_all_objects_in_collection(col))
#
#             shared_empty_mat = bpy.data.materials.get(MAT_AUTO_5LT)
#             if not shared_empty_mat or not shared_empty_mat.get("r2b_auto_assigned"):
#                 shared_empty_mat = preset_k_mat.copy()
#                 shared_empty_mat.name = MAT_AUTO_5LT
#                 shared_empty_mat["r2b_auto_assigned"] = True
#
#             for obj in target_objs:
#                 if obj.type in {'MESH', 'CURVE', 'SURFACE'}:
#                     if len(obj.material_slots) == 0:
#                         obj.data.materials.append(shared_empty_mat)
#                         assigned_phase1 += 1
#                     else:
#                         for slot in obj.material_slots:
#                             mat = slot.material
#                             if not mat:
#                                 slot.material = shared_empty_mat
#                                 assigned_phase1 += 1
#                             elif not mat.get("r2b_auto_assigned"):
#                                 base_name = mat.name.split('.')[0].strip()
#                                 existing_tagged = bpy.data.materials.get(base_name)
#
#                                 if existing_tagged and existing_tagged.get("r2b_auto_assigned") and existing_tagged != mat:
#                                     mat.user_remap(existing_tagged)
#                                     bpy.data.materials.remove(mat)
#                                     assigned_phase1 += 1
#                                 else:
#                                     new_mat = preset_k_mat.copy()
#                                     mat.user_remap(new_mat)
#                                     bpy.data.materials.remove(mat)
#                                     new_mat.name = base_name
#                                     new_mat["r2b_auto_assigned"] = True
#                                     assigned_phase1 += 1
#
#         # 第二階段：通用規則（本尊尋找防呆版）
#         source_mats = {}
#         for obj in mat_col.objects:
#             for slot in obj.material_slots:
#                 if slot.material:
#                     mat = slot.material
#                     clean_name = mat.name.split('.')[0].strip()
#                     if MAT_PRESET_LT_K in clean_name:
#                         continue
#                     keyword = re.sub(r'^(DW_|D_|W_)', '', clean_name, flags=re.IGNORECASE).strip()
#                     if keyword:
#                         source_mats[keyword.lower()] = mat
#
#         if source_mats:
#             sorted_keywords = sorted(source_mats.keys(), key=len, reverse=True)
#             for mat in list(bpy.data.materials):
#                 if mat.get("r2b_auto_assigned"):
#                     continue
#
#                 mat_name_lower = mat.name.lower()
#                 best_keyword = None
#
#                 for kw in sorted_keywords:
#                     if kw in mat_name_lower:
#                         if mat != source_mats[kw]:
#                             best_keyword = kw
#                             break
#
#                 if best_keyword:
#                     base_name = mat.name.split('.')[0].strip()
#                     existing_tagged = bpy.data.materials.get(base_name)
#
#                     if existing_tagged and existing_tagged.get("r2b_auto_assigned") and existing_tagged != mat:
#                         mat.user_remap(existing_tagged)
#                         bpy.data.materials.remove(mat)
#                         assigned_phase2 += 1
#                     else:
#                         source_mat = source_mats[best_keyword]
#                         new_mat = source_mat.copy()
#                         mat.user_remap(new_mat)
#                         bpy.data.materials.remove(mat)
#                         new_mat.name = base_name
#                         new_mat["r2b_auto_assigned"] = True
#                         assigned_phase2 += 1
#
#         self.report({'INFO'}, f"✨ 魔法完成！{LAYER_SUFFIX_LT} 強制替換 {assigned_phase1} 個，基礎材質替換 {assigned_phase2} 個。")
#         return {'FINISHED'}
# ===========================================================================

class RHINO_OT_ResetProp(bpy.types.Operator):
    bl_idname = "import_3dm.reset_prop"
    bl_label = "Reset Property"
    bl_description = "恢復為預設值"
    target: bpy.props.StringProperty()

    def execute(self, context):
        if self.target == "scale":
            context.scene.rhino_cam_scale = 0.01
            self.report({'INFO'}, "Scale Factor 已恢復預設值 (0.01)")
        elif self.target == "lens":
            context.scene.rhino_cam_lens_mult = 1.80
            self.report({'INFO'}, "Lens Multiplier 已恢復預設值 (1.80)")
        return {'FINISHED'}

class RHINO_OT_ToggleCamSync(bpy.types.Operator):
    bl_idname = "import_3dm.toggle_cam_sync"
    bl_label = "Toggle Camera Sync"
    bl_description = "啟動或關閉與 Rhino 的視窗鏡頭同步"

    def execute(self, context):
        wm = context.window_manager
        current_state = wm.get("livelink_viewport_active", 0)

        if current_state == 1:
            wm["livelink_viewport_active"] = 0
            self.report({'INFO'}, "鏡頭同步：已關閉")
        else:
            wm["livelink_viewport_active"] = 1
            wm["livelink_last_mtime"] = 0.0
            bpy.app.timers.register(update_viewport_from_json)
            self.report({'INFO'}, "鏡頭同步：已啟動")

        return {'FINISHED'}

class RHINO_OT_ShowHelp(bpy.types.Operator):
    bl_idname = "import_3dm.show_help"
    bl_label = "Rhino Live Link 快速指南"
    bl_description = "顯示 R2B 工作流的操作步驟與注意事項"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="【模型同步】", icon='MESH_DATA')
        box.label(text="1. Rhino: 執行 LiveLink_R2B_Models.py（選擇圖層後產生 R2B.3dm）")
        box.label(text="2. Blender: 點擊 'Import Models' 或 'Update Models'")
        layout.separator()
        box2 = layout.box()
        box2.label(text="【自動材質與燈光】", icon='LIGHT')
        box2.label(text="1. 將母體物件放入 Materials 以使用 Assign Basic Mat")
        box2.label(text=f"2. 建立 {COL_FIXTURES} / {COL_LIGHTING} 以連動 Rhino 點位")
        box2.label(text="3. 設定 Sync Folder（點 Auto-Detect 自動填入），即可一鍵更新燈光與鏡頭")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

class RHINO_OT_ResetPath(bpy.types.Operator):
    bl_idname = "import_3dm.reset_path"
    bl_label = "Auto-Detect Paths"
    bl_description = "自動將模型路徑設為 //R2B.3dm，並將 JSON 同步目錄設為 R2B_Path.txt 的 DataPath"

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, "請先儲存 Blender 檔案以取得目錄")
            return {'CANCELLED'}

        # 模型路徑：相對於 Blender 檔案的 R2B.3dm
        context.scene.rhino_update_path = "//R2B.3dm"

        # Sync Folder：指向 R2B_Path.txt 的 DataPath（AppData 絕對路徑）
        data_dir = os.path.join(
            os.getenv("APPDATA", ""),
            "McNeel", "Rhinoceros", "8.0", "scripts", "LoopFlow_R2B", "Data"
        )
        context.scene.rhino_json_dir = data_dir

        self.report({'INFO'}, "路徑已自動設定（模型: //R2B.3dm, JSON: {})".format(data_dir))
        return {'FINISHED'}

class RHINO_OT_QuickSync(bpy.types.Operator):
    bl_idname = "import_3dm.quick_sync"
    bl_label = "Rhino Quick Sync"

    @classmethod
    def description(cls, context, properties):
        if getattr(properties, 'update_mats', False):
            return "匯入模型並更新材質 (適合首次載入，會覆蓋現有未保護之材質)"
        return "僅更新模型幾何體，完美保留 Blender 內已調整過的材質與圖層狀態"

    update_mats: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        path = bpy.path.abspath(context.scene.rhino_update_path)
        if not os.path.exists(path):
            self.report({'ERROR'}, f"找不到檔案: {path}")
            return {'CANCELLED'}

        col_states = {}

        def capture_col_states(lc):
            col_states[lc.collection.name] = {
                'exclude': lc.exclude,
                'hide_viewport_eye': lc.hide_viewport,
                'hide_viewport_screen': lc.collection.hide_viewport,
                'hide_render': lc.collection.hide_render
            }
            for child in lc.children:
                capture_col_states(child)

        capture_col_states(context.view_layer.layer_collection)

        obj_states = {}
        for obj in bpy.data.objects:
            obj_states[obj.name] = {
                'hide_get': obj.hide_get(),
                'hide_viewport': obj.hide_viewport,
                'hide_render': obj.hide_render,
                'display_type': obj.display_type,
                'display_bounds_type': obj.display_bounds_type
            }

        bpy.ops.import_3dm.some_data(
            filepath=path,
            import_curves=True,
            import_meshes=True,
            update_materials=self.update_mats
        )

        merged = merge_duplicate_materials()

        def restore_col_states(lc):
            if lc.collection.name in col_states:
                state = col_states[lc.collection.name]
                lc.exclude = state['exclude']
                lc.hide_viewport = state['hide_viewport_eye']
                lc.collection.hide_viewport = state['hide_viewport_screen']
                lc.collection.hide_render = state['hide_render']
            for child in lc.children:
                restore_col_states(child)

        restore_col_states(context.view_layer.layer_collection)

        for obj in bpy.data.objects:
            if obj.name in obj_states:
                state = obj_states[obj.name]
                obj.hide_set(state['hide_get'])
                obj.hide_viewport = state['hide_viewport']
                obj.hide_render = state['hide_render']
                obj.display_type = state.get('display_type', 'TEXTURED')
                obj.display_bounds_type = state.get('display_bounds_type', 'BOX')

        if merged > 0:
            self.report({'INFO'}, f"模型已更新 (保留狀態，合併 {merged} 材質)")
        else:
            self.report({'INFO'}, "模型已更新 (保留狀態)")

        return {'FINISHED'}

# -------------------------------------------------------------------
# 5. 介面板與匯入定義
# -------------------------------------------------------------------
class Import3dm(bpy.types.Operator, ImportHelper):
    bl_idname = "import_3dm.some_data"
    bl_label = "Import Rhinoceros 3D"
    filename_ext = ".3dm"
    filter_glob: bpy.props.StringProperty(default="*.3dm", options={'HIDDEN'})
    import_curves: bpy.props.BoolProperty(name="Curves", default=True)
    import_meshes: bpy.props.BoolProperty(name="Meshes", default=True)
    update_materials: bpy.props.BoolProperty(name="Update Materials", default=False)

    def execute(self, context):
        options = self.as_keywords(ignore=("filter_glob",))
        return read_3dm(context, options)

class RHINO_PT_QuickUpdate(bpy.types.Panel):
    bl_label = "Rhino Live Link"
    bl_idname = "RHINO_PT_QuickUpdate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LoopFlow 3dm'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager

        layout.label(text="Model Sync", icon='MESH_DATA')
        box_model = layout.box()

        col = box_model.column()
        col.scale_y = 1.2
        col.operator("import_3dm.quick_sync", text="Import Models", icon='IMPORT').update_mats = True

        col_upd = box_model.column()
        col_upd.scale_y = 1.3
        col_upd.operator("import_3dm.quick_sync", text="Update Models", icon='FILE_REFRESH').update_mats = False

        row_model_path = box_model.row(align=True)
        row_model_path.prop(scene, "rhino_update_path", text="")
        row_model_path.operator("import_3dm.reset_path", text="", icon='VIEWZOOM')

        layout.separator()

        layout.label(text="Camera & Light Sync", icon='OUTLINER_OB_CAMERA')
        box_cam = layout.box()

        is_active = wm.get("livelink_viewport_active", 0) == 1

        row_cam = box_cam.row()
        row_cam.scale_y = 1.3
        if is_active:
            row_cam.operator("import_3dm.toggle_cam_sync", text="Stop Camera Sync", icon='PAUSE')
        else:
            row_cam.operator("import_3dm.toggle_cam_sync", text="Start Camera Sync", icon='PLAY')

        row_scale = box_cam.row(align=True)
        row_scale.prop(scene, "rhino_cam_scale", text="Scale")
        row_scale.operator("import_3dm.reset_prop", text="", icon='FILE_REFRESH').target = "scale"

        row_lens = box_cam.row(align=True)
        row_lens.prop(scene, "rhino_cam_lens_mult", text="Lens")
        row_lens.operator("import_3dm.reset_prop", text="", icon='FILE_REFRESH').target = "lens"

        box_cam.separator()

        row_light = box_cam.row()
        row_light.scale_y = 1.3
        row_light.operator("import_3dm.sync_lights", text="Sync Rhino Lights", icon='LIGHT')

        box_cam.prop(scene, "rhino_json_dir", text="Sync Folder")

        layout.separator()

        # layout.operator("import_3dm.assign_basic_mat", text="Assign Basic Mat.", icon='MATERIAL')  # [DISABLED]
        layout.operator("import_3dm.show_help", text="Help & Guide", icon='HELP')

# -------------------------------------------------------------------
# 6. 註冊邏輯
# -------------------------------------------------------------------
classes = (
    Import3dm,
    RHINO_OT_SyncLights,
    # RHINO_OT_AssignBasicMat,  # [DISABLED]
    RHINO_OT_ResetProp,
    RHINO_OT_ResetPath,
    RHINO_OT_QuickSync,
    RHINO_OT_ToggleCamSync,
    RHINO_OT_ShowHelp,
    RHINO_PT_QuickUpdate
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.rhino_update_path = bpy.props.StringProperty(
        name="Path", default="//R2B.3dm", subtype='FILE_PATH'
    )
    bpy.types.Scene.rhino_json_dir = bpy.props.StringProperty(
        name="Sync Folder", default="//", subtype='DIR_PATH'
    )
    bpy.types.Scene.rhino_cam_scale = bpy.props.FloatProperty(
        name="Scale Factor", description="單位轉換比例 (公分為 0.01)", default=0.01, min=0.0001, max=100.0
    )
    bpy.types.Scene.rhino_cam_lens_mult = bpy.props.FloatProperty(
        name="Lens Multiplier", description="畫面太廣時，調高此數值", default=1.80, min=0.1, max=5.0
    )

def unregister():
    if bpy.context.window_manager.get("livelink_viewport_active", 0) == 1:
        bpy.context.window_manager["livelink_viewport_active"] = 0

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.rhino_update_path
    del bpy.types.Scene.rhino_json_dir
    del bpy.types.Scene.rhino_cam_scale
    del bpy.types.Scene.rhino_cam_lens_mult

if __name__ == "__main__":
    register()
