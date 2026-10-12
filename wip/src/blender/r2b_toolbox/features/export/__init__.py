# -*- coding: utf-8 -*-
"""Export Tools：頂層 Collection 批次／勾選匯出 USDZ。"""
from __future__ import annotations

import os

import bpy
from mathutils import Vector

from ...constants import PARENT_PANEL_ID

PROP_EXPORT_SELECTED = "loopflow_toolbox_export_selected"


def set_collection_visible(col, visible):
    col.hide_viewport = not visible
    col.hide_render = not visible
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


def run_collection_export(context, target_col, output_dir):
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
    filepath = os.path.join(output_dir, "{0}.usdz".format(safe_name))

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


class LOOPFLOW_TOOLBOX_OT_export_all_usd(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.export_all_usd"
    bl_label = "Export All to USD"
    bl_description = "Export all top-level Collections in the scene"
    bl_options = {"REGISTER"}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, _event):
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
            success, _info = run_collection_export(context, col, output_dir)
            if success:
                count += 1

        restore_visibility(master, states)
        self.report({"INFO"}, "Full-scene batch export complete: {0} file(s)".format(count))
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_export_selected_usd(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.export_selected_usd"
    bl_label = "Export Selected to USD"
    bl_description = "Export only the checked Collections above"
    bl_options = {"REGISTER"}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, _event):
        master = context.scene.collection
        selected_cols = [c for c in master.children if getattr(c, PROP_EXPORT_SELECTED)]
        if not selected_cols:
            self.report({"ERROR"}, "Please check at least one Collection!")
            return {"CANCELLED"}
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        output_dir = bpy.path.abspath(self.directory)
        os.makedirs(output_dir, exist_ok=True)
        master = context.scene.collection
        selected_cols = [c for c in master.children if getattr(c, PROP_EXPORT_SELECTED)]

        states = {}
        save_visibility(master, states)

        count = 0
        for target_col in selected_cols:
            success, _info = run_collection_export(context, target_col, output_dir)
            if success:
                count += 1

        restore_visibility(master, states)
        self.report({"INFO"}, "Selective export complete: {0} file(s)".format(count))
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_select_all_cols(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.select_all_cols"
    bl_label = "Select / Deselect All"
    bl_description = "Select or deselect all Collections"
    bl_options = {"REGISTER", "UNDO"}

    action: bpy.props.EnumProperty(
        items=[("SELECT", "Select All", ""), ("DESELECT", "Deselect All", "")]
    )

    def execute(self, context):
        master = context.scene.collection
        state = self.action == "SELECT"
        for col in master.children:
            setattr(col, PROP_EXPORT_SELECTED, state)
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_PT_export(bpy.types.Panel):
    bl_label = "Export Tools"
    bl_idname = "LOOPFLOW_TOOLBOX_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow"
    bl_parent_id = PARENT_PANEL_ID

    def draw(self, context):
        layout = self.layout
        master = context.scene.collection

        layout.label(text="Batch Process:", icon="FILE_PARENT")
        box_all = layout.box()
        box_all.operator("loopflow_toolbox.export_all_usd", text="Export All to USD", icon="EXPORT")

        layout.separator()

        layout.label(text="Selective Export:", icon="RESTRICT_SELECT_OFF")
        box_single = layout.box()

        for col in master.children:
            box_single.prop(col, PROP_EXPORT_SELECTED, text=col.name)

        if master.children:
            row = box_single.row(align=True)
            row.operator("loopflow_toolbox.select_all_cols", text="All").action = "SELECT"
            row.operator("loopflow_toolbox.select_all_cols", text="None").action = "DESELECT"

        col_btn = box_single.column()
        col_btn.scale_y = 1.3
        col_btn.operator(
            "loopflow_toolbox.export_selected_usd",
            text="Export Selected to USD",
            icon="EXPORT",
        )


_CLASSES = (
    LOOPFLOW_TOOLBOX_OT_export_all_usd,
    LOOPFLOW_TOOLBOX_OT_export_selected_usd,
    LOOPFLOW_TOOLBOX_OT_select_all_cols,
    LOOPFLOW_TOOLBOX_PT_export,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    setattr(
        bpy.types.Collection,
        PROP_EXPORT_SELECTED,
        bpy.props.BoolProperty(
            name="Export",
            description="Check to include in selective batch export",
            default=False,
        ),
    )


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Collection, PROP_EXPORT_SELECTED):
        delattr(bpy.types.Collection, PROP_EXPORT_SELECTED)
