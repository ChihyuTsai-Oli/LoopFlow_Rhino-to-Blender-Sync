# -*- coding: utf-8 -*-
"""LoopFlow R2B Sync — 開發用 add-on（Camera／Light／Models 已接；Open 仍空殼）。

隔離 package：勿與 2.x `Import Rhinoceros 3D (R2B Pro)`／Toolkit 同 profile 混用正式專案。
Models Update／Import 會呼叫本機已啟用的 `import_3dm.some_data`。
"""

bl_info = {
    "name": "LoopFlow R2B Sync (Dev Stub)",
    "author": "Chihyu Tsai",
    "version": (0, 0, 6),
    "blender": (5, 2, 1),
    "location": "N-Panel > LoopFlow R2B Dev",
    "description": "3.0 開發 Sync：Models／Camera／Light；作業資料夾自動偵測",
    "category": "Import-Export",
}

import os

import bpy

from . import camera_sync
from . import light_sync
from . import model_sync

_STUB = "尚未實作（3.0 測試 Sync 空殼）"


class LOOPFLOW_R2B_DEV_OT_stub(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.stub"
    bl_label = "Stub"
    bl_options = {"REGISTER"}

    action: bpy.props.StringProperty(default="")

    def execute(self, context):
        label = self.action or self.bl_label
        self.report({"INFO"}, f"{label}：{_STUB}")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_reset_paths(bpy.types.Operator):
    """把作業資料夾設成目前 .blend 所在目錄（與 .3dm／_LoopFlow_Config 同層）。"""

    bl_idname = "loopflow_r2b_dev.reset_paths"
    bl_label = "Auto-Detect Work Folder"
    bl_options = {"REGISTER"}

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({"ERROR"}, "請先儲存 Blender 檔，才能自動偵測作業資料夾")
            return {"CANCELLED"}
        work_dir = os.path.dirname(bpy.path.abspath(blend_path))
        context.scene.r2b_sync_folder = work_dir
        self.report({"INFO"}, f"作業資料夾已設為：{work_dir}")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_update_models(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.update_models"
    bl_label = "Update Models"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = model_sync.sync_models(context, update_materials=False)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Update Models 完成（保留材質／顯隱）")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_import_models(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.import_models"
    bl_label = "Import Models"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = model_sync.sync_models(context, update_materials=True)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Import Models 完成（可更新材質）")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_camera_auto_on(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.camera_auto_on"
    bl_label = "Camera Auto On"
    bl_options = {"REGISTER"}

    def execute(self, context):
        camera_sync.set_camera_auto(context, True)
        err = camera_sync.push_camera_once(context)
        if err:
            self.report({"WARNING"}, f"自動同步已開；首次套用：{err}")
        else:
            self.report({"INFO"}, "Camera 自動同步已開啟")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_camera_auto_off(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.camera_auto_off"
    bl_label = "Camera Auto Off"
    bl_options = {"REGISTER"}

    def execute(self, context):
        camera_sync.set_camera_auto(context, False)
        self.report({"INFO"}, "Camera 自動同步已關閉")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_camera_push(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.camera_push"
    bl_label = "Camera Push Once"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = camera_sync.push_camera_once(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Camera 已套用一次")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_light_auto_on(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.light_auto_on"
    bl_label = "Light Auto On"
    bl_options = {"REGISTER"}

    def execute(self, context):
        light_sync.set_light_auto(context, True)
        err = light_sync.push_light_once(context)
        if err:
            self.report({"WARNING"}, f"自動同步已開；首次套用：{err}")
        else:
            self.report({"INFO"}, "Light 自動同步已開啟")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_light_auto_off(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.light_auto_off"
    bl_label = "Light Auto Off"
    bl_options = {"REGISTER"}

    def execute(self, context):
        light_sync.set_light_auto(context, False)
        self.report({"INFO"}, "Light 自動同步已關閉")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_OT_sync_lights(bpy.types.Operator):
    bl_idname = "loopflow_r2b_dev.sync_lights"
    bl_label = "Sync Lights"
    bl_options = {"REGISTER"}

    def execute(self, context):
        err = light_sync.push_light_once(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Light 已套用一次")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_PT_panel(bpy.types.Panel):
    bl_label = "R2B Sync (Dev)"
    bl_idname = "LOOPFLOW_R2B_DEV_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow R2B Dev"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row(align=True)
        row.prop(scene, "r2b_sync_folder", text="作業資料夾")
        row.operator("loopflow_r2b_dev.reset_paths", text="", icon="FILE_REFRESH")

        row = layout.row(align=True)
        row.prop(scene, "r2b_cam_scale", text="Scale")
        row.prop(scene, "r2b_cam_lens_mult", text="Lens")

        layout.separator()
        col = layout.column(align=True)
        col.operator("loopflow_r2b_dev.import_models", text="Import Models")
        col.operator("loopflow_r2b_dev.update_models", text="Update Models")

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
        op = col.operator("loopflow_r2b_dev.stub", text="Open / Health")
        op.action = "Open / Health"


_CLASSES = (
    LOOPFLOW_R2B_DEV_OT_stub,
    LOOPFLOW_R2B_DEV_OT_reset_paths,
    LOOPFLOW_R2B_DEV_OT_update_models,
    LOOPFLOW_R2B_DEV_OT_import_models,
    LOOPFLOW_R2B_DEV_OT_camera_auto_on,
    LOOPFLOW_R2B_DEV_OT_camera_auto_off,
    LOOPFLOW_R2B_DEV_OT_camera_push,
    LOOPFLOW_R2B_DEV_OT_light_auto_on,
    LOOPFLOW_R2B_DEV_OT_light_auto_off,
    LOOPFLOW_R2B_DEV_OT_sync_lights,
    LOOPFLOW_R2B_DEV_PT_panel,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.r2b_sync_folder = bpy.props.StringProperty(
        name="作業資料夾",
        description="與 .3dm／.blend／_LoopFlow_Config 同層；含 live／models",
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
