# -*- coding: utf-8 -*-
"""Selection Tools：編組、打平、材質隔離。"""
from __future__ import annotations

import bpy

from ...constants import PARENT_PANEL_ID


class LOOPFLOW_TOOLBOX_OT_group(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.group"
    bl_label = "Group"
    bl_description = (
        "Parent selected objects under the Active object and sync to a "
        "same-named Collection. Preserves world coordinates"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = context.active_object
        selected_objs = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if not active_obj or active_obj.type != "MESH":
            self.report({"WARNING"}, "Please select a Mesh as the Active object (main anchor) first")
            return {"CANCELLED"}
        if len(selected_objs) < 1:
            self.report({"WARNING"}, "Please select at least one child object to group")
            return {"CANCELLED"}

        old_parents = set()
        old_collections = set()

        for obj in selected_objs:
            if obj.parent and obj.parent.type == "EMPTY":
                old_parents.add(obj.parent)
            for col in obj.users_collection:
                old_collections.add(col)

        target_col_name = active_obj.name
        target_col = bpy.data.collections.get(target_col_name)

        if not target_col:
            target_col = bpy.data.collections.new(target_col_name)
            context.scene.collection.children.link(target_col)
        elif target_col_name not in context.scene.collection.children.keys():
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

        context.view_layer.update()
        if active_obj.name in context.view_layer.objects:
            context.view_layer.objects.active = active_obj
        self.report({"INFO"}, "Group complete: synced to '{0}'".format(target_col_name))
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_un_group(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.un_group"
    bl_label = "Un-Group"
    bl_description = (
        "Trace to root parent and unparent all children while preserving "
        "world coordinates. Supports multiple groups at once"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected_initial = context.selected_objects
        if not selected_initial:
            self.report({"WARNING"}, "Please select a member of the group to dissolve")
            return {"CANCELLED"}

        unique_roots = set()
        for obj in selected_initial:
            curr = obj
            while curr.parent is not None:
                curr = curr.parent
            unique_roots.add(curr)

        for root in unique_roots:
            all_descendants = root.children_recursive
            if not all_descendants and root.type != "EMPTY":
                continue

            for child in all_descendants:
                original_matrix = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = original_matrix

            if root.type == "EMPTY":
                bpy.data.objects.remove(root, do_unlink=True)

        context.view_layer.update()
        self.report({"INFO"}, "Un-Group complete: processed {0} group(s)".format(len(unique_roots)))
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_re_group(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.re_group"
    bl_label = "Re-Group"
    bl_description = (
        "Flatten complex hierarchies and apply Armature modifiers, "
        "parenting all Meshes under the Active object"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != "MESH":
            self.report({"WARNING"}, "Please select a Mesh as the final main anchor")
            return {"CANCELLED"}

        selected_objs = list(context.selected_objects)
        all_meshes = [obj for obj in selected_objs if obj.type == "MESH"]
        junk_objs = [obj for obj in selected_objs if obj.type in {"EMPTY", "ARMATURE"}]

        old_collections = set()
        for obj in selected_objs:
            for col in obj.users_collection:
                old_collections.add(col)

        for mesh_obj in all_meshes:
            context.view_layer.objects.active = mesh_obj
            for mod in mesh_obj.modifiers:
                if mod.type == "ARMATURE":
                    bpy.ops.object.modifier_apply(modifier=mod.name)

        target_col_name = "COL_FINAL_{0}".format(active_obj.name)
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

        bpy.ops.object.select_all(action="DESELECT")
        active_obj.select_set(True)
        context.view_layer.objects.active = active_obj

        self.report({"INFO"}, "Re-Group complete: flattened under '{0}'".format(active_obj.name))
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_select_all_in_group(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.select_all_in_group"
    bl_label = "Select All in Group"
    bl_description = "Trace up to the root parent and select all objects in the hierarchy"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected_initial = context.selected_objects
        if not selected_initial:
            self.report({"WARNING"}, "Please select at least one object first")
            return {"CANCELLED"}

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
        self.report({"INFO"}, "Selection complete: selected {0} group(s)".format(len(target_roots)))
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_delete_objects_from_group(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.delete_objects_from_group"
    bl_label = "Delete Objects From Group"
    bl_description = (
        "Unparent children while preserving world coordinates, then delete "
        "the parent object for render optimisation"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({"WARNING"}, "Please select the parent object to delete")
            return {"CANCELLED"}

        children = list(active_obj.children)

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

        self.report(
            {"INFO"},
            "Deleted '{0}', kept {1} child object(s)".format(target_name, len(children)),
        )
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_material_isolator(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.material_isolator"
    bl_label = "Material Isolator"
    bl_description = "Switch material link to Object mode so Alt+D instances can have independent materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not selected_objs:
            self.report({"WARNING"}, "Please select Mesh objects that need isolated materials")
            return {"CANCELLED"}

        for obj in selected_objs:
            for i, slot in enumerate(obj.material_slots):
                obj.active_material_index = i
                slot.link = "OBJECT"

                if slot.material:
                    new_mat = slot.material.copy()
                    new_mat.name = "{0}_Unique".format(slot.material.name)
                    slot.material = new_mat

        self.report(
            {"INFO"},
            "Material isolation complete: switched {0} object(s)".format(len(selected_objs)),
        )
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_PT_selection(bpy.types.Panel):
    bl_label = "Selection Tools"
    bl_idname = "LOOPFLOW_TOOLBOX_PT_selection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow"
    bl_parent_id = PARENT_PANEL_ID

    def draw(self, _context):
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("loopflow_toolbox.group", icon="OUTLINER_COLLECTION")
        col.operator("loopflow_toolbox.un_group", icon="FILE_PARENT")
        col.operator("loopflow_toolbox.re_group", icon="OUTLINER_OB_GROUP_INSTANCE")
        col.operator("loopflow_toolbox.select_all_in_group", icon="RESTRICT_SELECT_OFF")
        col.operator("loopflow_toolbox.delete_objects_from_group", icon="TRASH")
        col.operator("loopflow_toolbox.material_isolator", icon="MATERIAL")


_CLASSES = (
    LOOPFLOW_TOOLBOX_OT_group,
    LOOPFLOW_TOOLBOX_OT_un_group,
    LOOPFLOW_TOOLBOX_OT_re_group,
    LOOPFLOW_TOOLBOX_OT_select_all_in_group,
    LOOPFLOW_TOOLBOX_OT_delete_objects_from_group,
    LOOPFLOW_TOOLBOX_OT_material_isolator,
    LOOPFLOW_TOOLBOX_PT_selection,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
