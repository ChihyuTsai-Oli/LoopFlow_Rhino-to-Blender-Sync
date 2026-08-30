# -*- coding: utf-8 -*-
"""LoopFlow ToolBox — 獨立 add-on（Export／Rename／Selection）。不進 yak、不參與同步。"""

bl_info = {
    "name": "LoopFlow ToolBox",
    "author": "Chihyu Tsai",
    "version": (1, 0, 0),
    "blender": (5, 2, 1),
    "location": "N-Panel > LoopFlow > ToolBox",
    "description": "Export, Rename, and Selection tools",
    "category": "Object",
}

import bpy

from .constants import PARENT_PANEL_ID
from . import features


class LOOPFLOW_TOOLBOX_PT_root(bpy.types.Panel):
    """N 面板父 bar：ToolBox。各功能畫在子面板。"""

    bl_label = "ToolBox"
    bl_idname = PARENT_PANEL_ID
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LoopFlow"

    def draw(self, _context):
        return


def register():
    bpy.utils.register_class(LOOPFLOW_TOOLBOX_PT_root)
    features.register()


def unregister():
    features.unregister()
    bpy.utils.unregister_class(LOOPFLOW_TOOLBOX_PT_root)
