# -*- coding: utf-8 -*-
"""Blender Models consumer：Update／Import 自作業資料夾讀 models/R2B.3dm。

使用 Sync 內嵌的 import_3dm fork（含 rhino3dm wheel bootstrap）。
Update＝update_materials=False（ED-08）；Import＝True。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import bpy

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.paths import resolve_model_3dm_from_work_folder

from .import_3dm import default_import_options
from .import_3dm.read3dm import read_3dm

_WM_APPLIED_MTIME = "r2b3_model_applied_mtime"


def _model_3dm_path(scene) -> str:
    folder = bpy.path.abspath(scene.r2b_sync_folder)
    return str(resolve_model_3dm_from_work_folder(folder))


def merge_duplicate_materials() -> int:
    count = 0
    for mat in list(bpy.data.materials):
        match = re.match(r"(.*)\.\d{3}$", mat.name)
        if not match:
            continue
        base_name = match.group(1)
        base_mat = bpy.data.materials.get(base_name)
        if base_mat and base_mat != mat:
            mat.user_remap(base_mat)
            bpy.data.materials.remove(mat)
            count += 1
    return count


def _capture_visibility(context):
    col_states = {}

    def capture_col(lc):
        col_states[lc.collection.name] = {
            "exclude": lc.exclude,
            "hide_viewport_eye": lc.hide_viewport,
            "hide_viewport_screen": lc.collection.hide_viewport,
            "hide_render": lc.collection.hide_render,
        }
        for child in lc.children:
            capture_col(child)

    capture_col(context.view_layer.layer_collection)

    obj_states = {}
    for obj in bpy.data.objects:
        obj_states[obj.name] = {
            "hide_get": obj.hide_get(),
            "hide_viewport": obj.hide_viewport,
            "hide_render": obj.hide_render,
            "display_type": obj.display_type,
            "display_bounds_type": getattr(obj, "display_bounds_type", "BOX"),
        }
    return col_states, obj_states


def _restore_visibility(context, col_states, obj_states):
    def restore_col(lc):
        if lc.collection.name in col_states:
            state = col_states[lc.collection.name]
            lc.exclude = state["exclude"]
            lc.hide_viewport = state["hide_viewport_eye"]
            lc.collection.hide_viewport = state["hide_viewport_screen"]
            lc.collection.hide_render = state["hide_render"]
        for child in lc.children:
            restore_col(child)

    restore_col(context.view_layer.layer_collection)

    for obj in bpy.data.objects:
        if obj.name not in obj_states:
            continue
        state = obj_states[obj.name]
        try:
            obj.hide_set(state["hide_get"])
            obj.hide_viewport = state["hide_viewport"]
            obj.hide_render = state["hide_render"]
            obj.display_type = state.get("display_type", "TEXTURED")
            if hasattr(obj, "display_bounds_type"):
                obj.display_bounds_type = state.get("display_bounds_type", "BOX")
        except ReferenceError:
            pass


def _call_import_3dm(context, filepath: str, *, update_materials: bool) -> str:
    """呼叫內嵌 import_3dm.read_3dm；失敗回傳錯誤字串。"""
    options = default_import_options(update_materials=update_materials)
    try:
        result = read_3dm(context, filepath, options)
    except ImportError as exc:
        return "載入 rhino3dm 失敗：{}".format(exc)
    except Exception as exc:
        return "匯入失敗：{}".format(exc)
    if not result:
        return "匯入未完成（空結果）"
    if "FINISHED" not in result and "CANCELLED" in result:
        return "匯入取消或讀檔失敗：{}".format(filepath)
    if "FINISHED" not in result:
        return "匯入未完成：{}".format(result)
    return ""


def sync_models(context, *, update_materials: bool) -> str:
    """Update／Import 共用；成功回傳 ""。"""
    scene = context.scene
    path = _model_3dm_path(scene)
    if not os.path.isfile(path):
        return "找不到模型檔：{}".format(path)

    col_states, obj_states = _capture_visibility(context)
    err = _call_import_3dm(context, path, update_materials=update_materials)
    if err:
        return err
    merge_duplicate_materials()
    _restore_visibility(context, col_states, obj_states)
    try:
        context.window_manager[_WM_APPLIED_MTIME] = os.path.getmtime(path)
    except OSError:
        pass
    return ""
