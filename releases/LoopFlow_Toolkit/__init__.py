# -*- coding: utf-8 -*-
"""
==============================================================================
工具名稱: LoopFlow Toolkit (合併 Export / Rename / Selection 三工具)
版本資訊: v1.0.0 (Unified Addon)
開發日期: 2026-04-27
開發者: Cursor (Claude Sonnet 4.6)
開發環境: Blender 4.5.0+ (Python 3.11 / CPython 核心)
==============================================================================

此 addon 整合三支獨立工具為單一統一套件，N Panel 統一分類為 'LoopFlow Toolkit'。

子工具包含：
1. Export Tools：全場景批次匯出 + 精準複選匯出 USDZ
2. Rename Tools：Collection 與 Object 的智慧批次命名
3. Selection Tools：群組化、解散、壓平與材質隔離

==============================================================================
"""

bl_info = {
    "name": "LoopFlow Toolkit",
    "author": "Python Partner",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "View3D > N Panel > LoopFlow Toolkit",
    "description": "Export、Rename、Selection 整合工具包",
    "category": "Object",
}

import bpy
import os
from mathutils import Vector

# ===============================================
# EXPORT TOOLS
# ===============================================

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

def run_collection_export(context, target_col, output_dir, states):
    master = context.scene.collection
    top_collections = list(master.children)

    for col in top_collections:
        set_collection_visible(col, False)
    set_collection_visible(target_col, True)

    all_objs = get_all_objects_in_collection(target_col)
    geo_objs = [o for o in all_objs if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}]

    if not geo_objs:
        return False, "Empty"

    context.view_layer.update()
    pos_history = move_roots_to_origin_and_record(all_objs)
    context.view_layer.update()

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

    restore_roots_from_history(all_objs, pos_history)
    context.view_layer.update()
    
    return True, filepath


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


class EXPORTTOOLS_PT_panel(bpy.types.Panel):
    bl_label       = "Export Tools"
    bl_idname      = "EXPORTTOOLS_PT_panel"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'LoopFlow Toolkit'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        master = scene.collection
        
        layout.label(text="Batch Process:", icon='FILE_PARENT')
        box_all = layout.box()
        box_all.operator("exporttools.export_multi_usd", text="Export All to USD", icon='EXPORT')

        layout.separator()

        layout.label(text="Selective Export:", icon='RESTRICT_SELECT_OFF')
        box_single = layout.box()
        
        for col in master.children:
            box_single.prop(col, "r2b_export_selected", text=col.name)
            
        if master.children:
            row = box_single.row(align=True)
            row.operator("exporttools.select_all_cols", text="All").action = 'SELECT'
            row.operator("exporttools.select_all_cols", text="None").action = 'DESELECT'
        
        col_btn = box_single.column()
        col_btn.scale_y = 1.3
        col_btn.operator("exporttools.export_selected_usd", text="Export Selected to USD", icon='EXPORT')


# ===============================================
# RENAME TOOLS
# ===============================================

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


class LIGHTHOUSE_PT_rename_tools_panel(bpy.types.Panel):
    bl_label = "Rename Tools"
    bl_idname = "LIGHTHOUSE_PT_rename_tools_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LoopFlow Toolkit' 

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("lighthouse.rename_collections", text="Rename Collections", icon='OUTLINER_COLLECTION')
        col.operator("lighthouse.rename_objects_by_collections", text="Rename Objects by Collections", icon='GROUP')
        col.operator("lighthouse.rename_objects", text="Rename Objects", icon='MESH_DATA')


# ===============================================
# SELECTION TOOLS
# ===============================================

class LIGHTHOUSE_OT_group(bpy.types.Operator):
    bl_idname = "lighthouse.group"
    bl_label = "Group"
    bl_description = "以 Active 物件為父級進行群組化，並同步建立同名 Collection。維持世界座標"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object
        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not active_obj or active_obj.type != 'MESH':
            self.report({'WARNING'}, "請先選取一個 Mesh 作為 Active 物件（主錨點）")
            return {'CANCELLED'}
        if len(selected_objs) < 1:
            self.report({'WARNING'}, "請選取至少一個子物件進行群組化")
            return {'CANCELLED'}

        old_parents = set()
        old_collections = set()

        for obj in selected_objs:
            if obj.parent and obj.parent.type == 'EMPTY':
                old_parents.add(obj.parent)
            for col in obj.users_collection:
                old_collections.add(col)

        target_col_name = active_obj.name
        target_col = bpy.data.collections.get(target_col_name)
        
        if not target_col:
            target_col = bpy.data.collections.new(target_col_name)
            context.scene.collection.children.link(target_col)
        
        if active_obj.name not in target_col.objects:
            target_col.objects.link(active_obj)

        for obj in selected_objs:
            for col in list(obj.users_collection):
                if col != target_col:
                    col.objects.unlink(obj)
            
            if obj.name not in target_col.objects:
                target_col.objects.link(obj)

            if obj != active_obj:
                original_matrix = obj.matrix_world.copy()
                obj.parent = active_obj
                obj.matrix_world = original_matrix

        context.view_layer.update()

        for p in old_parents:
            if p != active_obj and len(p.children) == 0:
                bpy.data.objects.remove(p, do_unlink=True)

        for col in old_collections:
            if col != target_col and len(col.objects) == 0 and col != context.scene.collection:
                bpy.data.collections.remove(col)

        context.view_layer.objects.active = active_obj
        self.report({'INFO'}, f"Group 成功：已同步至 '{target_col_name}'")
        return {'FINISHED'}


class LIGHTHOUSE_OT_un_group(bpy.types.Operator):
    bl_idname = "lighthouse.un_group"
    bl_label = "Un-Group"
    bl_description = "自動追溯頂層父級，批次解除連結並鎖定世界座標。支援同時解散多個群組"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_initial = context.selected_objects
        if not selected_initial:
            self.report({'WARNING'}, "請選取要解散的群組成員")
            return {'CANCELLED'}

        unique_roots = set()
        for obj in selected_initial:
            curr = obj
            while curr.parent is not None:
                curr = curr.parent
            unique_roots.add(curr)

        for root in unique_roots:
            all_descendants = root.children_recursive
            if not all_descendants and root.type != 'EMPTY':
                continue

            for child in all_descendants:
                original_matrix = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = original_matrix

            if root.type == 'EMPTY':
                bpy.data.objects.remove(root, do_unlink=True)

        context.view_layer.update()
        self.report({'INFO'}, f"Un-Group 成功：已處理 {len(unique_roots)} 個群組")
        return {'FINISHED'}


class LIGHTHOUSE_OT_re_group(bpy.types.Operator):
    bl_idname = "lighthouse.re_group"
    bl_label = "Re-Group"
    bl_description = "極限壓平所有複雜階層，自動套用 Armature，將子 Mesh 掛載於 Active 下"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != 'MESH':
            self.report({'WARNING'}, "請選取一個 Mesh 作為最終的主錨點")
            return {'CANCELLED'}

        selected_objs = [obj for obj in context.selected_objects]
        all_meshes = [obj for obj in selected_objs if obj.type == 'MESH']
        junk_objs = [obj for obj in selected_objs if obj.type in {'EMPTY', 'ARMATURE'}]
        
        old_collections = set()
        for obj in selected_objs:
            for col in obj.users_collection:
                old_collections.add(col)

        for mesh_obj in all_meshes:
            context.view_layer.objects.active = mesh_obj
            for mod in mesh_obj.modifiers:
                if mod.type == 'ARMATURE':
                    bpy.ops.object.modifier_apply(modifier=mod.name)

        target_col_name = f"COL_FINAL_{active_obj.name}"
        target_col = bpy.data.collections.get(target_col_name) or bpy.data.collections.new(target_col_name)
        if target_col_name not in context.scene.collection.children.keys():
            context.scene.collection.children.link(target_col)

        context.view_layer.objects.active = active_obj
        
        for mesh_obj in all_meshes:
            for col in list(mesh_obj.users_collection):
                col.objects.unlink(mesh_obj)
            target_col.objects.link(mesh_obj)

            if mesh_obj == active_obj:
                continue
                
            original_matrix = mesh_obj.matrix_world.copy()
            mesh_obj.parent = active_obj
            mesh_obj.matrix_world = original_matrix

        context.view_layer.update()

        for junk in junk_objs:
            if junk != active_obj:
                bpy.data.objects.remove(junk, do_unlink=True)

        for col in old_collections:
            if col != target_col and len(col.objects) == 0 and col != context.scene.collection:
                bpy.data.collections.remove(col)

        bpy.ops.object.select_all(action='DESELECT')
        active_obj.select_set(True)
        context.view_layer.objects.active = active_obj

        self.report({'INFO'}, f"Re-Group 成功：已壓平至 '{active_obj.name}'")
        return {'FINISHED'}


class LIGHTHOUSE_OT_select_all_in_group(bpy.types.Operator):
    bl_idname = "lighthouse.select_all_in_group"
    bl_label = "Select All in Group"
    bl_description = "自動向上追溯至最頂層，並全選該群組下的所有層級物件"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_initial = context.selected_objects
        if not selected_initial:
            self.report({'WARNING'}, "請先選取至少一個物件")
            return {'CANCELLED'}

        target_roots = set()
        for obj in selected_initial:
            root_obj = obj
            while root_obj.parent is not None:
                root_obj = root_obj.parent
            target_roots.add(root_obj)

        for root in target_roots:
            root.select_set(True)
            for child in root.children_recursive:
                child.select_set(True)

        context.view_layer.update()
        self.report({'INFO'}, f"選取完畢：已連選 {len(target_roots)} 個群組")
        return {'FINISHED'}


class LIGHTHOUSE_OT_delete_objects_from_group(bpy.types.Operator):
    bl_idname = "lighthouse.delete_objects_from_group"
    bl_label = "Delete Objects From Group"
    bl_description = "釋放子物件並鎖定世界座標，隨即刪除父級物件以利 Render 最佳化"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "請選取要刪除的父級物件")
            return {'CANCELLED'}

        children = [child for child in active_obj.children]

        for child in children:
            world_matrix = child.matrix_world.copy()
            child.parent = None
            child.matrix_world = world_matrix

        target_name = active_obj.name
        parent_collections = [col for col in active_obj.users_collection]

        bpy.data.objects.remove(active_obj, do_unlink=True)

        for col in parent_collections:
            if len(col.objects) == 0 and col != context.scene.collection:
                bpy.data.collections.remove(col)

        self.report({'INFO'}, f"已刪除 '{target_name}'，保留 {len(children)} 個子物件")
        return {'FINISHED'}


class LIGHTHOUSE_OT_material_isolator(bpy.types.Operator):
    bl_idname = "lighthouse.material_isolator"
    bl_label = "Material Isolator"
    bl_description = "將材質連結切換至 Object 模式，讓 Alt+D 的分身可擁有獨立材質"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objs:
            self.report({'WARNING'}, "請選取需要隔離材質的 Mesh 物件")
            return {'CANCELLED'}

        for obj in selected_objs:
            for i, slot in enumerate(obj.material_slots):
                obj.active_material_index = i
                slot.link = 'OBJECT'
                
                if slot.material:
                    new_mat = slot.material.copy()
                    new_mat.name = f"{slot.material.name}_Unique"
                    slot.material = new_mat

        self.report({'INFO'}, f"隔離成功：已切換 {len(selected_objs)} 個物件")
        return {'FINISHED'}


class LIGHTHOUSE_PT_selection_tools(bpy.types.Panel):
    bl_label = "Selection Tools"
    bl_idname = "LIGHTHOUSE_PT_selection_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LoopFlow Toolkit'

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.scale_y = 1.2
        
        col.operator("lighthouse.group", icon='OUTLINER_COLLECTION')
        col.operator("lighthouse.un_group", icon='FILE_PARENT')
        col.operator("lighthouse.re_group", icon='OUTLINER_OB_GROUP_INSTANCE')
        col.operator("lighthouse.select_all_in_group", icon='RESTRICT_SELECT_OFF')
        col.operator("lighthouse.delete_objects_from_group", icon='TRASH')
        col.operator("lighthouse.material_isolator", icon='MATERIAL')


# ===============================================
# 註冊與註銷
# ===============================================

classes = (
    # Export Tools
    EXPORTTOOLS_OT_export_multi_usd,
    EXPORTTOOLS_OT_export_selected_usd,
    EXPORTTOOLS_OT_select_all_cols,
    EXPORTTOOLS_PT_panel,
    # Rename Tools
    LIGHTHOUSE_OT_rename_collections,
    LIGHTHOUSE_OT_rename_objects_by_collections,
    LIGHTHOUSE_OT_rename_objects,
    LIGHTHOUSE_PT_rename_tools_panel,
    # Selection Tools
    LIGHTHOUSE_OT_group,
    LIGHTHOUSE_OT_un_group,
    LIGHTHOUSE_OT_re_group,
    LIGHTHOUSE_OT_select_all_in_group,
    LIGHTHOUSE_OT_delete_objects_from_group,
    LIGHTHOUSE_OT_material_isolator,
    LIGHTHOUSE_PT_selection_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
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
