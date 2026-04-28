# -*- coding: utf-8 -*-
"""
==============================================================================
工具名稱: Export Tools (R2B Workflow)
版本資訊: v3.4
開發日期: 2026-04-12
開發者: Cursor (Claude Sonnet 4.6)
開發環境: Blender 4.5.0+ (Python 3.11 / CPython 核心)
同步檔案: 無
==============================================================================
[ 功能與操作說明 ]

1. Export All to USD (全場景批次)
   - 自動跑完場景中所有頂層 Collection 的匯出流程。

2. Selective Export (精準複選匯出)
   - 功能：提供打勾清單，支援「複選」特定的 Collection 進行匯出。
   - 輔助：附帶 All / None 一鍵全選與清除按鈕。
   - UI 更新：套用最簡潔直觀的按鈕命名方案 (v3.4)。

[ 對位邏輯 ]
- 匯出前自動將「根物件」原點歸零 (0,0,0)，子物件隨行。
- 匯出完成後自動還原物件至原始位置。

[ 變數連動注意事項 ]
- `bpy.types.Collection.r2b_export_selected`：於 register() 動態擴充至 Blender 原生 Collection，
  卸載時須在 unregister() 手動 del，否則會殘留於資料結構。
- `pos_history`：以根物件名稱為 key 儲存原始世界座標，若中途發生例外則位置可能未被還原，需手動 Ctrl+Z。
==============================================================================
"""

bl_info = {
    "name": "Export Tools",
    "author": "Python Partner",
    "version": (3, 4, 0),
    "blender": (4, 5, 0),
    "location": "View3D > N Panel > Item",
    "description": "支援全場景批次與精準複選匯出 USDZ (原點歸零對位)",
    "category": "Object",
}

import bpy
import os
from mathutils import Vector

# ==========================================
# 1. 核心處理函式
# ==========================================

def set_collection_visible(col, visible):
    col.hide_viewport = not visible
    col.hide_render   = not visible
    for child in col.children:
        set_collection_visible(child, visible)

def save_visibility(col, states):
    states[col.name] = (col.hide_viewport, col.hide_render)
    for child in col.children:
        save_visibility(child, states)

def restore_visibility(col, states):
    if col.name in states:
        col.hide_viewport, col.hide_render = states[col.name]
    for child in col.children:
        restore_visibility(child, states)

def get_all_objects_in_collection(col):
    objs = list(col.objects)
    for child in col.children:
        objs.extend(get_all_objects_in_collection(child))
    return objs

def move_roots_to_origin_and_record(objs):
    history = {}
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    for root in roots:
        history[root.name] = root.matrix_world.translation.copy()
        root.matrix_world.translation = Vector((0.0, 0.0, 0.0))
    return history

def restore_roots_from_history(objs, history):
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    for root in roots:
        if root.name in history:
            root.matrix_world.translation = history[root.name]

# ==========================================
# 2. 共用匯出邏輯引擎
# ==========================================

def run_collection_export(context, target_col, output_dir, states):
    master = context.scene.collection
    top_collections = list(master.children)

    # 1. 隔離顯示
    for col in top_collections:
        set_collection_visible(col, False)
    set_collection_visible(target_col, True)

    all_objs = get_all_objects_in_collection(target_col)
    geo_objs = [o for o in all_objs if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}]

    if not geo_objs:
        return False, "Empty"

    # 2. 對位
    context.view_layer.update()
    pos_history = move_roots_to_origin_and_record(all_objs)
    context.view_layer.update()

    # 3. 匯出
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in target_col.name)
    filepath = os.path.join(output_dir, f"{safe_name}.usdz")

    bpy.ops.wm.usd_export(
        filepath=filepath,
        export_animation=False,
        export_uvmaps=True,
        export_normals=True,
        export_materials=True,
        use_instancing=True,
        visible_objects_only=True,
    )

    # 4. 還原位置
    restore_roots_from_history(all_objs, pos_history)
    context.view_layer.update()
    
    return True, filepath


# ==========================================
# 3. 算子 (Operators)
# ==========================================

class EXPORTTOOLS_OT_export_multi_usd(bpy.types.Operator):
    bl_idname  = "exporttools.export_multi_usd"
    bl_label   = "Export All to USD"
    bl_description = "匯出場景中所有頂層 Collection"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        output_dir = bpy.path.abspath(self.directory)
        os.makedirs(output_dir, exist_ok=True)
        master = context.scene.collection
        top_collections = list(master.children)

        states = {}
        save_visibility(master, states)

        count = 0
        for col in top_collections:
            success, info = run_collection_export(context, col, output_dir, states)
            if success: count += 1

        restore_visibility(master, states)
        self.report({"INFO"}, f"全場景批次匯出完成：共 {count} 個檔案")
        return {"FINISHED"}


class EXPORTTOOLS_OT_export_selected_usd(bpy.types.Operator):
    bl_idname  = "exporttools.export_selected_usd"
    bl_label   = "Export Selected to USD"
    bl_description = "僅匯出上方勾選的 Collection"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        master = context.scene.collection
        # 檢查是否有勾選任何項目
        selected_cols = [c for c in master.children if c.r2b_export_selected]
        if not selected_cols:
            self.report({"ERROR"}, "請至少勾選一個 Collection！")
            return {"CANCELLED"}
            
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        output_dir = bpy.path.abspath(self.directory)
        os.makedirs(output_dir, exist_ok=True)
        master = context.scene.collection
        
        # 抓出所有打勾的 Collection
        selected_cols = [c for c in master.children if c.r2b_export_selected]

        states = {}
        save_visibility(master, states)
        
        count = 0
        for target_col in selected_cols:
            success, info = run_collection_export(context, target_col, output_dir, states)
            if success: count += 1
        
        restore_visibility(master, states)
        
        self.report({"INFO"}, f"局部複選匯出成功：共 {count} 個檔案")
        return {"FINISHED"}


class EXPORTTOOLS_OT_select_all_cols(bpy.types.Operator):
    bl_idname  = "exporttools.select_all_cols"
    bl_label   = "Select / Deselect All"
    bl_description = "全選或清除所有勾選狀態"
    bl_options = {'REGISTER', 'UNDO'}

    action: bpy.props.EnumProperty(
        items=[('SELECT', "Select All", ""), ('DESELECT', "Deselect All", "")]
    )

    def execute(self, context):
        master = context.scene.collection
        state = (self.action == 'SELECT')
        for col in master.children:
            col.r2b_export_selected = state
        return {"FINISHED"}


# ==========================================
# 4. 介面面板 (UI Panel)
# ==========================================

class EXPORTTOOLS_PT_panel(bpy.types.Panel):
    bl_label       = "Export Tools"
    bl_idname      = "EXPORTTOOLS_PT_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Item'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        master = scene.collection
        
        # --- 全場景批次區 ---
        layout.label(text="Batch Process:", icon='FILE_PARENT')
        box_all = layout.box()
        box_all.operator("exporttools.export_multi_usd", text="Export All to USD", icon='EXPORT')

        layout.separator()

        # --- 複選匯出區 ---
        layout.label(text="Selective Export:", icon='RESTRICT_SELECT_OFF')
        box_single = layout.box()
        
        # 畫出所有頂層 Collection 的打勾清單
        for col in master.children:
            box_single.prop(col, "r2b_export_selected", text=col.name)
            
        # 畫出全選/清除按鈕
        if master.children:
            row = box_single.row(align=True)
            row.operator("exporttools.select_all_cols", text="All").action = 'SELECT'
            row.operator("exporttools.select_all_cols", text="None").action = 'DESELECT'
        
        # 畫出匯出按鈕
        col_btn = box_single.column()
        col_btn.scale_y = 1.3
        col_btn.operator("exporttools.export_selected_usd", text="Export Selected to USD", icon='EXPORT')


# ==========================================
# 5. 註冊與屬性設定
# ==========================================

classes = (
    EXPORTTOOLS_OT_export_multi_usd,
    EXPORTTOOLS_OT_export_selected_usd,
    EXPORTTOOLS_OT_select_all_cols,
    EXPORTTOOLS_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 幫 Blender 原生的 Collection 擴充一個「打勾」屬性
    bpy.types.Collection.r2b_export_selected = bpy.props.BoolProperty(
        name="Export",
        description="勾選以進行局部批次匯出",
        default=False
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Collection.r2b_export_selected

if __name__ == "__main__":
    register()