# -*- coding: utf-8 -*-
"""LoopFlow R2B Sync — 開發用測試 add-on 空殼（無業務邏輯）。

隔離 package：勿與 2.x `Import Rhinoceros 3D (R2B Pro)`／Toolkit 同 profile 混用正式專案。
在隔離 Blender 5.2.1 profile 以「從磁碟安裝」指向本資料夾即可。
"""

bl_info = {
    "name": "LoopFlow R2B Sync (Dev Stub)",
    "author": "Chihyu Tsai",
    "version": (0, 0, 1),
    "blender": (5, 2, 1),
    "location": "N-Panel > LoopFlow R2B Dev",
    "description": "3.0 開發空殼：N-Panel 按鈕對齊 Rhino entrypoints；尚未接同步邏輯",
    "category": "Import-Export",
}

import bpy


_STUB = "尚未實作（3.0 測試 Sync 空殼）"


class LOOPFLOW_R2B_DEV_OT_stub(bpy.types.Operator):
    """通用空殼 operator：只回報尚未實作。"""

    bl_idname = "loopflow_r2b_dev.stub"
    bl_label = "Stub"
    bl_options = {"REGISTER"}

    action: bpy.props.StringProperty(default="")

    def execute(self, context):
        label = self.action or self.bl_label
        self.report({"INFO"}, f"{label}：{_STUB}")
        return {"FINISHED"}


class LOOPFLOW_R2B_DEV_PT_panel(bpy.types.Panel):
    bl_label = "R2B Sync (Dev)"
    bl_idname = "LOOPFLOW_R2B_DEV_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow R2B Dev"

    def draw(self, context):
        layout = self.layout
        layout.label(text="空殼按鈕（無業務邏輯）")

        col = layout.column(align=True)
        op = col.operator("loopflow_r2b_dev.stub", text="Update Models")
        op.action = "Update Models"
        op = col.operator("loopflow_r2b_dev.stub", text="Import Models")
        op.action = "Import Models"

        layout.separator()
        col = layout.column(align=True)
        op = col.operator("loopflow_r2b_dev.stub", text="Camera Auto On")
        op.action = "Camera Auto On"
        op = col.operator("loopflow_r2b_dev.stub", text="Camera Auto Off")
        op.action = "Camera Auto Off"
        op = col.operator("loopflow_r2b_dev.stub", text="Camera Push Once")
        op.action = "Camera Push Once"

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
    LOOPFLOW_R2B_DEV_PT_panel,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
