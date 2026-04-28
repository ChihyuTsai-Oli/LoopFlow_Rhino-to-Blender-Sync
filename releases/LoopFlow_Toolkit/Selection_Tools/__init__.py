# -*- coding: utf-8 -*-
"""
==============================================================================
工具名稱: Selection Tools
版本資訊: v1.3.0 (UI Draw Fix Version)
開發日期: 2026-03-30
開發者: Cursor (Claude Sonnet 4.6)
開發環境: Blender 4.5.4 (Python 3.11 / CPython 核心)
同步檔案: 無
==============================================================================
[ 功能與操作說明 ]

1. Group (直向錨定器)
   - 操作：選取多個子 Mesh，最後加選一個 Mesh 作為 Active，點擊執行。

2. Un-Group (批次解構器)
   - 操作：選取要解散的群組內任一成員，點擊執行。

3. Re-Group (極限壓平器)
   - 操作：選取複雜階層，最後加選目標 Mesh 作為 Active，點擊執行。

4. Select All in Group (層級連選器)
   - 操作：選取群組內任一子物件，點擊執行。

5. Delete Objects From Group (智慧解構器)
   - 操作：選取要被刪除的父級物件，點擊執行。

6. Material Isolator (材質孤立器)
   - 操作：選取需要獨立材質的物件，點擊執行。
   * 手動對照：至右下角屬性面板 -> 材質分頁 -> 將材質連結下拉選單從「Data」切換為「Object」。

[ 變數連動注意事項 ]
- context.active_object 與 context.selected_objects 為主要輸入來源，需在 OBJECT 模式下執行。
- Group 操作會同步建立同名 Collection，若已存在同名 Collection 則直接掛載，不重複建立。
- Material Isolator 對材質執行 copy()，複製後名稱自動加上 `_Unique` 後綴，需避免與既有材質名稱衝突。
==============================================================================
"""

bl_info = {
    "name": "Selection Tools",
    "author": "Python Partner",
    "version": (1, 3, 0),
    "blender": (4, 5, 0),
    "location": "View3D > N Panel > Item",
    "description": "提供群組化、解散、壓平與選取等進階管理工具",
    "category": "Object",
}

import bpy

# ==========================================
# 1. 核心算子 (Operators)
# ==========================================

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


# ==========================================
# 2. 介面面板 (UI Panel)
# ==========================================

class LIGHTHOUSE_PT_selection_tools(bpy.types.Panel):
    """在 3D 視圖 Item 標籤中建立控制面板"""
    bl_label = "Selection Tools"
    bl_idname = "LIGHTHOUSE_PT_selection_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'

    def draw(self, context):
        # 關鍵修復：必須先宣告 layout = self.layout
        layout = self.layout
        
        # 使用 column 進行垂直排列
        col = layout.column(align=True)
        col.scale_y = 1.2 # 稍微增加按鈕高度，提升點擊體驗
        
        col.operator("lighthouse.group", icon='OUTLINER_COLLECTION')
        col.operator("lighthouse.un_group", icon='FILE_PARENT')
        col.operator("lighthouse.re_group", icon='OUTLINER_OB_GROUP_INSTANCE')
        col.operator("lighthouse.select_all_in_group", icon='RESTRICT_SELECT_OFF')
        col.operator("lighthouse.delete_objects_from_group", icon='TRASH')
        col.operator("lighthouse.material_isolator", icon='MATERIAL')


# ==========================================
# 3. 註冊與註銷 (Registration)
# ==========================================

classes = (
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

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()