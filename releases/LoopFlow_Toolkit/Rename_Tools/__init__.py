# -*- coding: utf-8 -*-
"""
==============================================================================
工具名稱: Rename Tools
版本資訊: v7.5.0 (Clean UI Edition)
開發日期: 2026-03-30
開發者: Cursor (Claude Sonnet 4.6)
開發環境: Blender 4.5.4 (Python 3.11 / CPython 核心)
同步檔案: 無
==============================================================================
[ 功能與操作說明 ]

1. Rename Collections (資料夾批次編碼)
   - 功能：跨視窗對大綱視圖 (Outliner) 選取的 Collection 進行批次連號命名，同步開啟 Render。
   - 操作：在大綱視圖選取一個或多個 Collection，點擊執行並輸入基礎名稱。

2. Rename Objects by Collections (依資料夾智慧編碼物件)
   - 功能：以物件所屬的 Collection 名稱為基準，對內部的物件進行自動連號命名。
           內建「雙軌計數器」，自動辨識 Alt+D 共用網格並賦予 `_Ins` 後綴防撞，同時精準同步底層 Mesh 名稱。
   - 操作：選取 Collection 或其內部的物件，點擊執行。

3. Rename Objects (XY 空間陣列編碼)
   - 功能：無視層級的純物件序列編碼。強制以「左下角為起點，先沿 +Y 軸行進，再沿 +X 軸換行」的絕對空間座標排序。
           X 軸具備 1mm 容錯機制，確保微小位移不會導致錯亂；Active 物件享有免後綴與首位特權。
   - 操作：在 3D 視圖全選要排號的物件，確保 Active (最後點選) 為主物件，點擊執行。

[ 變數連動注意事項 ]
- `cached_target_names` 屬性以 `"|||"` 作為 Collection 名稱分隔符，需確保 Collection 名稱不含此字串。
- 雙軌計數器以 `obj.data.users > 1` 判定 Instance，命名時會同步異動底層 Mesh Data 名稱。
- Rename Objects 排序以 `round(location.x, 3)` 進行 X 軸容錯，如需調整精度請同步修改此值。
==============================================================================
"""

bl_info = {
    "name": "Rename Tools",
    "author": "Python Partner",
    "version": (7, 5, 0),
    "blender": (4, 5, 0),
    "location": "View3D > N Panel > Item",
    "description": "提供 Collection 與 Object 的絕對精準批次命名，支援 XY 空間陣列排序與 Instance 標註",
    "category": "Object",
}

import bpy

# ==========================================
# 1. 算子：Rename Collections (資料夾編碼)
# ==========================================
class LIGHTHOUSE_OT_rename_collections(bpy.types.Operator):
    bl_idname = "lighthouse.rename_collections"
    bl_label = "Rename Collections"
    bl_description = "跨視窗批次連號命名大綱視圖中選取的 Collection，並同步開啟 Render"
    bl_options = {'REGISTER', 'UNDO'}

    new_base_name: bpy.props.StringProperty(name="基礎名稱", default="LHT_Group")
    cached_target_names: bpy.props.StringProperty(options={'HIDDEN'})

    def invoke(self, context, event):
        target_cols = []
        for area in context.screen.areas:
            if area.type == 'OUTLINER':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region:
                    with context.temp_override(area=area, region=region):
                        try:
                            sel_ids = getattr(context, "selected_ids", [])
                            cols = [item for item in sel_ids if isinstance(item, bpy.types.Collection)]
                            if len(cols) > len(target_cols): target_cols = cols
                        except AttributeError: pass

        if len(target_cols) <= 1 and context.selected_objects:
            obj_cols = set()
            for obj in context.selected_objects:
                for col in obj.users_collection: obj_cols.add(col)
            for col in obj_cols:
                if col not in target_cols: target_cols.append(col)

        if not target_cols:
            active_lc = context.view_layer.active_layer_collection
            if active_lc and active_lc.collection: target_cols = [active_lc.collection]

        if not target_cols: 
            self.report({'WARNING'}, "請選取至少一個 Collection！")
            return {'CANCELLED'}
            
        self.cached_target_names = "|||".join([col.name for col in target_cols])
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.cached_target_names: return {'CANCELLED'}
        names = self.cached_target_names.split("|||")
        target_cols = [bpy.data.collections.get(n) for n in names if bpy.data.collections.get(n)]

        active_col = context.view_layer.active_layer_collection.collection
        if active_col in target_cols:
            target_cols.remove(active_col)
            target_cols.insert(0, active_col)

        for i, col in enumerate(target_cols):
            col.name = self.new_base_name if i == 0 else f"{self.new_base_name}_{i:03d}"
            col.hide_render = False

        for area in context.screen.areas: area.tag_redraw()
        return {'FINISHED'}


# ==========================================
# 2. 算子：Rename Objects by Collections (依資料夾編碼)
# ==========================================
class LIGHTHOUSE_OT_rename_objects_by_collections(bpy.types.Operator):
    bl_idname = "lighthouse.rename_objects_by_collections"
    bl_label = "Rename Objects by Collections"
    bl_description = "以所屬 Collection 為基準自動連號命名。支援 Instance 雙軌計數，並同步底層 Mesh 名稱"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_cols = []
        for area in context.screen.areas:
            if area.type == 'OUTLINER':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region:
                    with context.temp_override(area=area, region=region):
                        try:
                            sel_ids = getattr(context, "selected_ids", [])
                            cols = [item for item in sel_ids if isinstance(item, bpy.types.Collection)]
                            if len(cols) > len(target_cols): target_cols = cols
                        except AttributeError: pass

        if not target_cols and context.selected_objects:
            obj_cols = set()
            for obj in context.selected_objects:
                for col in obj.users_collection: obj_cols.add(col)
            target_cols = list(obj_cols)

        if not target_cols:
            active_lc = context.view_layer.active_layer_collection
            if active_lc and active_lc.collection: target_cols = [active_lc.collection]

        target_cols = list(set(target_cols))
        if not target_cols: 
            self.report({'WARNING'}, "請選取 Collection 或裡面的物件！")
            return {'CANCELLED'}

        for col in target_cols:
            objs_in_col = list(col.objects)
            if not objs_in_col: continue

            lead_obj = None
            parents_in_col = [o for o in objs_in_col if any(c in objs_in_col for c in o.children)]
            
            if parents_in_col:
                top_parents = [p for p in parents_in_col if p.parent not in parents_in_col]
                lead_obj = top_parents[0] if top_parents else parents_in_col[0]
                if context.active_object in top_parents: lead_obj = context.active_object
            else:
                if context.active_object in objs_in_col: lead_obj = context.active_object
                else: lead_obj = objs_in_col[0]

            sorted_objs = [lead_obj] + [o for o in objs_in_col if o != lead_obj]

            processed_data = set()
            for i, obj in enumerate(sorted_objs):
                obj.name = f"TMP_R_{col.name}_{i}"
                if obj.data and obj.data not in processed_data:
                    obj.data.name = f"TMP_D_{col.name}_{i}"
                    processed_data.add(obj.data)

            processed_data.clear() 
            idx_unique = 0
            idx_instance = 0
            
            for obj in sorted_objs:
                is_instance = getattr(obj.data, "users", 1) > 1 if obj.data else False
                if is_instance:
                    new_exact_name = f"{col.name}_Ins" if idx_instance == 0 else f"{col.name}_Ins.{idx_instance:03d}"
                    idx_instance += 1
                else:
                    new_exact_name = col.name if idx_unique == 0 else f"{col.name}.{idx_unique:03d}"
                    idx_unique += 1
                
                obj.name = new_exact_name
                if obj.data and obj.data not in processed_data:
                    obj.data.name = new_exact_name
                    processed_data.add(obj.data)

        for area in context.screen.areas: area.tag_redraw()
        self.report({'INFO'}, f"依 Collection 命名完成！處理了 {len(target_cols)} 個資料夾。")
        return {'FINISHED'}


# ==========================================
# 3. 算子：Rename Objects (XY 空間座標陣列編碼)
# ==========================================
class LIGHTHOUSE_OT_rename_objects(bpy.types.Operator):
    bl_idname = "lighthouse.rename_objects"
    bl_label = "Rename Objects"
    bl_description = "無視層級的純序列編碼。以左下角為起點(XY陣列)精確排序，Active 物件享首位免後綴特權"
    bl_options = {'REGISTER', 'UNDO'}

    new_base_name: bpy.props.StringProperty(name="物件基礎名稱", default="Object")

    def invoke(self, context, event):
        if not context.selected_objects:
            self.report({'WARNING'}, "請先選取要更名的物件！")
            return {'CANCELLED'}
        
        if context.active_object and context.active_object in context.selected_objects:
            self.new_base_name = context.active_object.name
        else:
            self.new_base_name = context.selected_objects[0].name
            
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_objs = context.selected_objects
        if not selected_objs: return {'CANCELLED'}

        lead_obj = context.active_object if context.active_object in selected_objs else selected_objs[0]
        rest_objs = [o for o in selected_objs if o != lead_obj]

        rest_objs.sort(key=lambda o: (round(o.location.x, 3), o.location.y))
        sorted_objs = [lead_obj] + rest_objs

        processed_data = set()
        for i, obj in enumerate(sorted_objs):
            obj.name = f"TMP_RO_{i}"
            if obj.data and obj.data not in processed_data:
                obj.data.name = f"TMP_DO_{i}"
                processed_data.add(obj.data)

        processed_data.clear()
        idx_unique = 0
        idx_instance = 0

        for obj in sorted_objs:
            is_instance = getattr(obj.data, "users", 1) > 1 if obj.data else False
            if is_instance:
                new_exact_name = f"{self.new_base_name}_Ins" if idx_instance == 0 else f"{self.new_base_name}_Ins.{idx_instance:03d}"
                idx_instance += 1
            else:
                new_exact_name = self.new_base_name if idx_unique == 0 else f"{self.new_base_name}.{idx_unique:03d}"
                idx_unique += 1

            obj.name = new_exact_name
            if obj.data and obj.data not in processed_data:
                obj.data.name = new_exact_name
                processed_data.add(obj.data)

        for area in context.screen.areas: area.tag_redraw()
        self.report({'INFO'}, f"XY 空間陣列編碼完成！共處理 {len(sorted_objs)} 個物件。")
        return {'FINISHED'}


# ==========================================
# 4. 介面面板 (UI Panel)
# ==========================================
class LIGHTHOUSE_PT_rename_tools_panel(bpy.types.Panel):
    bl_label = "Rename Tools"
    bl_idname = "LIGHTHOUSE_PT_rename_tools_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item' 

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("lighthouse.rename_collections", text="Rename Collections", icon='OUTLINER_COLLECTION')
        col.operator("lighthouse.rename_objects_by_collections", text="Rename Objects by Collections", icon='GROUP')
        col.operator("lighthouse.rename_objects", text="Rename Objects", icon='MESH_DATA')


# ==========================================
# 5. 註冊與註銷 (Registration)
# ==========================================
classes = (
    LIGHTHOUSE_OT_rename_collections,
    LIGHTHOUSE_OT_rename_objects_by_collections,
    LIGHTHOUSE_OT_rename_objects,
    LIGHTHOUSE_PT_rename_tools_panel,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    try: unregister()
    except: pass
    register()