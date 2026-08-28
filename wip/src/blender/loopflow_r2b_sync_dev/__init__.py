# -*- coding: utf-8 -*-
"""LoopFlow R2B Sync — 開發用 add-on（Camera 通道已接；其餘仍為空殼）。

隔離 package：勿與 2.x `Import Rhinoceros 3D (R2B Pro)`／Toolkit 同 profile 混用正式專案。
"""

bl_info = {
    "name": "LoopFlow R2B Sync (Dev Stub)",
    "author": "Chihyu Tsai",
    "version": (0, 0, 2),
    "blender": (5, 2, 1),
    "location": "N-Panel > LoopFlow R2B Dev",
    "description": "3.0 開發 Sync：Camera 開／關／手動；其餘按鈕仍為空殼",
    "category": "Import-Export",
}

import bpy

from . import camera_sync

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


class LOOPFLOW_R2B_DEV_PT_panel(bpy.types.Panel):
    bl_label = "R2B Sync (Dev)"
    bl_idname = "LOOPFLOW_R2B_DEV_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow R2B Dev"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "r2b_sync_folder", text="Sync Folder")
        row = layout.row(align=True)
        row.prop(scene, "r2b_cam_scale", text="Scale")
        row.prop(scene, "r2b_cam_lens_mult", text="Lens")

        layout.separator()
        col = layout.column(align=True)
        op = col.operator("loopflow_r2b_dev.stub", text="Update Models")
        op.action = "Update Models"
        op = col.operator("loopflow_r2b_dev.stub", text="Import Models")
        op.action = "Import Models"

        layout.separator()
        col = layout.column(align=True)
        col.operator("loopflow_r2b_dev.camera_auto_on", text="Camera Auto On")
        col.operator("loopflow_r2b_dev.camera_auto_off", text="Camera Auto Off")
        col.operator("loopflow_r2b_dev.camera_push", text="Camera Push Once")

        layout.separator()
        col = layout.column(align=True)
        op = col.operator("loopflow_r2b_dev.stub", text="Sync Lights")
        op.action = "Sync Lights"

        layout.separator()
        col = layout.column(align=True)
        op = col.operator("loopflow_r2b_dev.stub", text="Open / Health")
        op.action = "Open / Health"
        op = col.operator("loopflow_r2b_dev.stub", text="Reset Paths")
        op.action = "Reset Paths"


_CLASSES = (
    LOOPFLOW_R2B_DEV_OT_stub,
    LOOPFLOW_R2B_DEV_OT_camera_auto_on,
    LOOPFLOW_R2B_DEV_OT_camera_auto_off,
    LOOPFLOW_R2B_DEV_OT_camera_push,
    LOOPFLOW_R2B_DEV_PT_panel,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.r2b_sync_folder = bpy.props.StringProperty(
        name="Sync Folder",
        description="專案 _LoopFlow_Config/loopflow_R2B（內含 live/camera.json）",
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
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.r2b_sync_folder
    del bpy.types.Scene.r2b_cam_scale
    del bpy.types.Scene.r2b_cam_lens_mult


if __name__ == "__main__":
    register()
