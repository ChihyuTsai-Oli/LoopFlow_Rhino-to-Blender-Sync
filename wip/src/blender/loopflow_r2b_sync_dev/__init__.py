# -*- coding: utf-8 -*-
"""LoopFlow R2B Sync — 開發用 add-on（Models／Camera／Light／Open 已接）。

隔離 package：勿與 2.x `Import Rhinoceros 3D (R2B Pro)`／Toolkit 同 profile 混用正式專案。
Models Update／Import 使用內嵌 `import_3dm` fork（含 rhino3dm wheels）。
"""

bl_info = {
    "name": "LoopFlow R2B Sync (Dev Stub)",
    "author": "Chihyu Tsai",
    "version": (0, 0, 8),
    "blender": (5, 2, 1),
    "location": "N-Panel > LoopFlow",
    "description": "R2B 3.0 Sync: Models, Camera, Light, Open; embedded import_3dm",
    "category": "Import-Export",
}

import os

import bpy

from . import camera_sync
from . import health_sync
from . import light_sync
from . import model_sync

_STUB = "Not implemented (3.0 Sync stub)"


class LOOPFLOW_R2B_DEV_OT_stub(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.stub"
    bl_label = "Stub"
    bl_options = {"REGISTER"}

    action: bpy.props.StringProperty(default="")

    def execute(self, context):
        label = self.action or self.bl_label
        self.report({"INFO"}, f"{label}: {_STUB}")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_reset_paths(bpy.types.Operator):
    """Set the work folder to the current .blend directory."""

    bl_idname = "loopflow_r2b_dev.reset_paths"
    bl_label = "Auto-Detect Work Folder"
    bl_options = {"REGISTER"}

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({"ERROR"}, "Save the Blender file first to auto-detect the work folder")
            return {"CANCELLED"}
        work_dir = os.path.dirname(bpy.path.abspath(blend_path))
        context.scene.r2b_sync_folder = work_dir
        self.report({"INFO"}, f"Work folder: {work_dir}")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_update_models(bpy.types.Operator):
    """Rebuild R2B geometry from models/R2B.3dm. Keeps existing materials."""

    bl_idname = "loopflow_r2b_dev.update_models"
    bl_label = "Update Models"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = model_sync.sync_models(context, update_materials=False)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Update Models done (kept materials / visibility)")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_import_models(bpy.types.Operator):
    """Rebuild R2B geometry from models/R2B.3dm and assign default materials."""

    bl_idname = "loopflow_r2b_dev.import_models"
    bl_label = "Sync Models"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = model_sync.sync_models(context, update_materials=True)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Sync Models done")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_import_objects(bpy.types.Operator):
    """Add objects from models/R2B_Objects.3dm (no materials)."""

    bl_idname = "loopflow_r2b_dev.import_objects"
    bl_label = "Import Objects"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = model_sync.import_objects(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Import Objects done")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_camera_auto_on(bpy.types.Operator):
    """Start following the Rhino camera from live/camera.json."""

    bl_idname = "loopflow_r2b_dev.camera_auto_on"
    bl_label = "Camera Auto On"
    bl_options = {"REGISTER"}

    def execute(self, context):
        camera_sync.set_camera_auto(context, True)
        err = camera_sync.push_camera_once(context)
        if err:
            self.report({"WARNING"}, f"Auto sync on; first apply: {err}")
        else:
            self.report({"INFO"}, "Camera auto sync on")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_camera_auto_off(bpy.types.Operator):
    """Stop following the Rhino camera."""

    bl_idname = "loopflow_r2b_dev.camera_auto_off"
    bl_label = "Camera Auto Off"
    bl_options = {"REGISTER"}

    def execute(self, context):
        camera_sync.set_camera_auto(context, False)
        self.report({"INFO"}, "Camera auto sync off")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_camera_push(bpy.types.Operator):
    """Apply live/camera.json once."""

    bl_idname = "loopflow_r2b_dev.camera_push"
    bl_label = "Camera Push Once"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = camera_sync.push_camera_once(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Camera applied once")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_light_auto_on(bpy.types.Operator):
    """Start aligning lights from live/light.json."""

    bl_idname = "loopflow_r2b_dev.light_auto_on"
    bl_label = "Light Auto On"
    bl_options = {"REGISTER"}

    def execute(self, context):
        light_sync.set_light_auto(context, True)
        err = light_sync.push_light_once(context)
        if err:
            self.report({"WARNING"}, f"Auto sync on; first apply: {err}")
        else:
            self.report({"INFO"}, "Light auto sync on")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_light_auto_off(bpy.types.Operator):
    """Stop aligning lights."""

    bl_idname = "loopflow_r2b_dev.light_auto_off"
    bl_label = "Light Auto Off"
    bl_options = {"REGISTER"}

    def execute(self, context):
        light_sync.set_light_auto(context, False)
        self.report({"INFO"}, "Light auto sync off")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_sync_lights(bpy.types.Operator):
    """Apply live/light.json once."""

    bl_idname = "loopflow_r2b_dev.sync_lights"
    bl_label = "Sync Lights"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = light_sync.push_light_once(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Lights applied once")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_open_health(bpy.types.Operator):
    """Open the config folder. Hover for last-good file times."""

    bl_idname = "loopflow_r2b_dev.open_health"
    bl_label = "Open / Health"
    bl_options = {"REGISTER"}

    @classmethod
    def description(cls, context, _properties):
        folder = health_sync.work_folder_from_scene(context.scene)
        if not folder:
            return "Set the Work Folder or save the Blender file first"
        return health_sync.health_report_for_work_folder(folder)

    def execute(self, context):
        folder = health_sync.work_folder_from_scene(context.scene)
        if not folder:
            self.report({"ERROR"}, "Set the Work Folder or save the Blender file first")
            return {"CANCELLED"}
        err = health_sync.open_config_root(folder)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Opened config folder")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_PT_panel(bpy.types.Panel):
    bl_label = "Rhino to Blender Sync"
    bl_idname = "LOOPFLOW_R2B_DEV_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row(align=True)
        row.prop(scene, "r2b_sync_folder", text="Work Folder")
        row.operator("loopflow_r2b_dev.reset_paths", text="", icon="FILE_REFRESH")

        row = layout.row(align=True)
        row.prop(scene, "r2b_cam_scale", text="Scale")
        row.prop(scene, "r2b_cam_lens_mult", text="Lens")

        layout.separator()
        col = layout.column(align=True)
        col.operator("loopflow_r2b_dev.import_models", text="Sync Models")
        col.operator("loopflow_r2b_dev.update_models", text="Update Models")
        col.operator("loopflow_r2b_dev.import_objects", text="Import Objects")

        layout.separator()
        col = layout.column(align=True)
        col.operator("loopflow_r2b_dev.camera_auto_on", text="Camera Auto On")
        col.operator("loopflow_r2b_dev.camera_auto_off", text="Camera Auto Off")
        col.operator("loopflow_r2b_dev.camera_push", text="Camera Push Once")

        layout.separator()
        col = layout.column(align=True)
        col.operator("loopflow_r2b_dev.light_auto_on", text="Light Auto On")
        col.operator("loopflow_r2b_dev.light_auto_off", text="Light Auto Off")
        col.operator("loopflow_r2b_dev.sync_lights", text="Sync Lights")

        layout.separator()
        col = layout.column(align=True)
        col.operator("loopflow_r2b_dev.open_health", text="Open / Health")


_CLASSES = (
    LOOPFLOW_R2B_DEV_OT_stub,
    LOOPFLOW_R2B_DEV_OT_reset_paths,
    LOOPFLOW_R2B_DEV_OT_update_models,
    LOOPFLOW_R2B_DEV_OT_import_models,
    LOOPFLOW_R2B_DEV_OT_import_objects,
    LOOPFLOW_R2B_DEV_OT_camera_auto_on,
    LOOPFLOW_R2B_DEV_OT_camera_auto_off,
    LOOPFLOW_R2B_DEV_OT_camera_push,
    LOOPFLOW_R2B_DEV_OT_light_auto_on,
    LOOPFLOW_R2B_DEV_OT_light_auto_off,
    LOOPFLOW_R2B_DEV_OT_sync_lights,
    LOOPFLOW_R2B_DEV_OT_open_health,
    LOOPFLOW_R2B_DEV_PT_panel,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.r2b_sync_folder = bpy.props.StringProperty(
        name="Work Folder",
        description="Same folder as the .3dm / .blend / _LoopFlow_Config",
        default="",
        subtype="DIR_PATH",
    )
    bpy.types.Scene.r2b_cam_scale = bpy.props.FloatProperty(
        name="Camera Scale",
        default=0.01,
        min=0.000001,
    )
    bpy.types.Scene.r2b_cam_lens_mult = bpy.props.FloatProperty(
        name="Lens Mult",
        default=1.80,
        min=0.000001,
    )


def unregister():
    camera_sync.set_camera_auto(bpy.context, False)
    light_sync.set_light_auto(bpy.context, False)
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.r2b_sync_folder
    del bpy.types.Scene.r2b_cam_scale
    del bpy.types.Scene.r2b_cam_lens_mult


if __name__ == "__main__":
    register()
