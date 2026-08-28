# -*- coding: utf-8 -*-
"""Blender Models consumer：Update／Import 自作業資料夾讀 models/R2B.3dm。

優先呼叫已啟用的 `import_3dm.some_data`；若未啟用會嘗試自動啟用。
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


def _import_3dm_repo_dir() -> Path:
    """repo/import_3dm/import_3dm-0.0.18-windows_x64（唯讀參考）。"""
    # model_sync.py → …/wip/src/blender/loopflow_r2b_sync_dev → parents[4]=repo
    return Path(__file__).resolve().parents[4] / "import_3dm" / "import_3dm-0.0.18-windows_x64"


def _operator_ready() -> bool:
    op = getattr(bpy.ops, "import_3dm", None)
    return op is not None and hasattr(op, "some_data")


def _ensure_import_3dm_operator() -> str:
    """確保 bpy.ops.import_3dm.some_data 可用；失敗回傳錯誤字串。"""
    if _operator_ready():
        return ""

    # 嘗試啟用已安裝的模組（junction 名稱固定 import_3dm）
    try:
        import addon_utils  # type: ignore

        addon_utils.enable("import_3dm", default_set=True, persistent=True)
    except Exception:
        try:
            bpy.ops.preferences.addon_enable(module="import_3dm")
        except Exception:
            pass

    if _operator_ready():
        return ""

    repo_dir = _import_3dm_repo_dir()
    hint = (
        "找不到 import_3dm.some_data。\n"
        "請在 Portable Blender 執行 wip/tools/link_dev_addon.ps1（會掛上 Sync＋import_3dm），\n"
        "再於偏好設定啟用「Import Rhinoceros 3D」。\n"
        "參考目錄：{}".format(repo_dir)
    )
    if not repo_dir.is_dir():
        return hint + "\n（參考目錄不存在，請確認 repo 完整。）"
    return hint


def _call_import_3dm(filepath: str, *, update_materials: bool) -> str:
    """呼叫既有 import_3dm operator；失敗回傳錯誤字串。"""
    err = _ensure_import_3dm_operator()
    if err:
        return err
    try:
        result = bpy.ops.import_3dm.some_data(
            filepath=filepath,
            import_curves=True,
            import_meshes=True,
            update_materials=update_materials,
        )
    except Exception as exc:
        return "匯入失敗：{}".format(exc)
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
    err = _call_import_3dm(path, update_materials=update_materials)
    if err:
        return err
    merge_duplicate_materials()
    _restore_visibility(context, col_states, obj_states)
    try:
        context.window_manager[_WM_APPLIED_MTIME] = os.path.getmtime(path)
    except OSError:
        pass
    return ""
