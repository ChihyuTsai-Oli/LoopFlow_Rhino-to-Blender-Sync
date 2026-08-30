# -*- coding: utf-8 -*-
"""Rename Tools：Collection／物件批次命名（含 _Ins）。"""
from __future__ import annotations

import bpy

from ...constants import PARENT_PANEL_ID


class LOOPFLOW_TOOLBOX_OT_rename_collections(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.rename_collections"
    bl_label = "Rename Collections"
    bl_description = (
        "Batch sequential renaming of Collections selected in the Outliner "
        "(cross-window); also enables Render"
    )
    bl_options = {"REGISTER", "UNDO"}

    new_base_name: bpy.props.StringProperty(name="Base Name", default="LHT_Group")
    cached_target_names: bpy.props.StringProperty(options={"HIDDEN"})

    def invoke(self, context, _event):
        target_cols = []
        for area in context.screen.areas:
            if area.type == "OUTLINER":
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                if region:
                    with context.temp_override(area=area, region=region):
                        try:
                            sel_ids = getattr(context, "selected_ids", [])
                            cols = [item for item in sel_ids if isinstance(item, bpy.types.Collection)]
                            if len(cols) > len(target_cols):
                                target_cols = cols
                        except AttributeError:
                            pass

        if len(target_cols) <= 1 and context.selected_objects:
            obj_cols = set()
            for obj in context.selected_objects:
                for col in obj.users_collection:
                    obj_cols.add(col)
            for col in obj_cols:
                if col not in target_cols:
                    target_cols.append(col)

        if not target_cols:
            active_lc = context.view_layer.active_layer_collection
            if active_lc and active_lc.collection:
                target_cols = [active_lc.collection]

        if not target_cols:
            self.report({"WARNING"}, "Please select at least one Collection!")
            return {"CANCELLED"}

        self.cached_target_names = "|||".join([col.name for col in target_cols])
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.cached_target_names:
            return {"CANCELLED"}
        names = self.cached_target_names.split("|||")
        target_cols = [bpy.data.collections.get(n) for n in names if bpy.data.collections.get(n)]

        active_col = context.view_layer.active_layer_collection.collection
        if active_col in target_cols:
            target_cols.remove(active_col)
            target_cols.insert(0, active_col)

        for i, col in enumerate(target_cols):
            col.name = self.new_base_name if i == 0 else "{0}_{1:03d}".format(self.new_base_name, i)
            col.hide_render = False

        for area in context.screen.areas:
            area.tag_redraw()
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_rename_objects_by_collections(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.rename_objects_by_collections"
    bl_label = "Rename Objects by Collections"
    bl_description = (
        "Auto-number objects using their Collection name as base. "
        "Supports instance dual-counter and syncs Mesh data names"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        target_cols = []
        for area in context.screen.areas:
            if area.type == "OUTLINER":
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                if region:
                    with context.temp_override(area=area, region=region):
                        try:
                            sel_ids = getattr(context, "selected_ids", [])
                            cols = [item for item in sel_ids if isinstance(item, bpy.types.Collection)]
                            if len(cols) > len(target_cols):
                                target_cols = cols
                        except AttributeError:
                            pass

        if not target_cols and context.selected_objects:
            obj_cols = set()
            for obj in context.selected_objects:
                for col in obj.users_collection:
                    obj_cols.add(col)
            target_cols = list(obj_cols)

        if not target_cols:
            active_lc = context.view_layer.active_layer_collection
            if active_lc and active_lc.collection:
                target_cols = [active_lc.collection]

        target_cols = list(set(target_cols))
        if not target_cols:
            self.report({"WARNING"}, "Please select a Collection or objects inside one!")
            return {"CANCELLED"}

        for col in target_cols:
            objs_in_col = list(col.objects)
            if not objs_in_col:
                continue

            lead_obj = None
            parents_in_col = [o for o in objs_in_col if any(c in objs_in_col for c in o.children)]

            if parents_in_col:
                top_parents = [p for p in parents_in_col if p.parent not in parents_in_col]
                lead_obj = top_parents[0] if top_parents else parents_in_col[0]
                if context.active_object in top_parents:
                    lead_obj = context.active_object
            else:
                if context.active_object in objs_in_col:
                    lead_obj = context.active_object
                else:
                    lead_obj = objs_in_col[0]

            sorted_objs = [lead_obj] + [o for o in objs_in_col if o != lead_obj]

            processed_data = set()
            for i, obj in enumerate(sorted_objs):
                obj.name = "TMP_R_{0}_{1}".format(col.name, i)
                if obj.data and obj.data not in processed_data:
                    obj.data.name = "TMP_D_{0}_{1}".format(col.name, i)
                    processed_data.add(obj.data)

            processed_data.clear()
            idx_unique = 0
            idx_instance = 0

            for obj in sorted_objs:
                is_instance = getattr(obj.data, "users", 1) > 1 if obj.data else False
                if is_instance:
                    new_exact_name = (
                        "{0}_Ins".format(col.name)
                        if idx_instance == 0
                        else "{0}_Ins.{1:03d}".format(col.name, idx_instance)
                    )
                    idx_instance += 1
                else:
                    new_exact_name = (
                        col.name if idx_unique == 0 else "{0}.{1:03d}".format(col.name, idx_unique)
                    )
                    idx_unique += 1

                obj.name = new_exact_name
                if obj.data and obj.data not in processed_data:
                    obj.data.name = new_exact_name
                    processed_data.add(obj.data)

        for area in context.screen.areas:
            area.tag_redraw()
        self.report(
            {"INFO"},
            "Rename by Collections complete! Processed {0} collection(s).".format(len(target_cols)),
        )
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_OT_rename_objects(bpy.types.Operator):
    bl_idname = "loopflow_toolbox.rename_objects"
    bl_label = "Rename Objects"
    bl_description = (
        "Pure sequential numbering ignoring hierarchy. XY spatial sort from "
        "bottom-left; Active object gets the base name with no suffix"
    )
    bl_options = {"REGISTER", "UNDO"}

    new_base_name: bpy.props.StringProperty(name="Object Base Name", default="Object")

    def invoke(self, context, _event):
        if not context.selected_objects:
            self.report({"WARNING"}, "Please select objects to rename first!")
            return {"CANCELLED"}

        if context.active_object and context.active_object in context.selected_objects:
            self.new_base_name = context.active_object.name
        else:
            self.new_base_name = context.selected_objects[0].name

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_objs = context.selected_objects
        if not selected_objs:
            return {"CANCELLED"}

        lead_obj = context.active_object if context.active_object in selected_objs else selected_objs[0]
        rest_objs = [o for o in selected_objs if o != lead_obj]

        rest_objs.sort(key=lambda o: (round(o.location.x, 3), o.location.y))
        sorted_objs = [lead_obj] + rest_objs

        processed_data = set()
        for i, obj in enumerate(sorted_objs):
            obj.name = "TMP_RO_{0}".format(i)
            if obj.data and obj.data not in processed_data:
                obj.data.name = "TMP_DO_{0}".format(i)
                processed_data.add(obj.data)

        processed_data.clear()
        idx_unique = 0
        idx_instance = 0

        for obj in sorted_objs:
            is_instance = getattr(obj.data, "users", 1) > 1 if obj.data else False
            if is_instance:
                new_exact_name = (
                    "{0}_Ins".format(self.new_base_name)
                    if idx_instance == 0
                    else "{0}_Ins.{1:03d}".format(self.new_base_name, idx_instance)
                )
                idx_instance += 1
            else:
                new_exact_name = (
                    self.new_base_name
                    if idx_unique == 0
                    else "{0}.{1:03d}".format(self.new_base_name, idx_unique)
                )
                idx_unique += 1

            obj.name = new_exact_name
            if obj.data and obj.data not in processed_data:
                obj.data.name = new_exact_name
                processed_data.add(obj.data)

        for area in context.screen.areas:
            area.tag_redraw()
        self.report(
            {"INFO"},
            "XY spatial array numbering complete! Processed {0} object(s).".format(len(sorted_objs)),
        )
        return {"FINISHED"}


class LOOPFLOW_TOOLBOX_PT_rename(bpy.types.Panel):
    bl_label = "Rename Tools"
    bl_idname = "LOOPFLOW_TOOLBOX_PT_rename"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow"
    bl_parent_id = PARENT_PANEL_ID

    def draw(self, _context):
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("loopflow_toolbox.rename_collections", text="Rename Collections", icon="OUTLINER_COLLECTION")
        col.operator(
            "loopflow_toolbox.rename_objects_by_collections",
            text="Rename Objects by Collections",
            icon="GROUP",
        )
        col.operator("loopflow_toolbox.rename_objects", text="Rename Objects", icon="MESH_DATA")


_CLASSES = (
    LOOPFLOW_TOOLBOX_OT_rename_collections,
    LOOPFLOW_TOOLBOX_OT_rename_objects_by_collections,
    LOOPFLOW_TOOLBOX_OT_rename_objects,
    LOOPFLOW_TOOLBOX_PT_rename,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
