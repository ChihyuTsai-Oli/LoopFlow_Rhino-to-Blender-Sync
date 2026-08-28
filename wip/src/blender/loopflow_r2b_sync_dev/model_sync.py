# -*- coding: utf-8 -*-
"""Blender Models consumer：Sync／Update 讀 R2B.3dm；Import Objects 讀 R2B_Objects.3dm。"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path

import bpy
from mathutils import Matrix

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.block_payload import (
    USERSTRING_DEF_ID,
    parse_blocks_payload,
    relative_xform,
    rhino_mat4_translation_scaled,
)
from foundation.paths import (
    resolve_blocks_json_from_work_folder,
    resolve_model_3dm_from_work_folder,
    resolve_objects_3dm_from_work_folder,
)

from .import_3dm import default_import_options
from .import_3dm.read3dm import read_3dm

_WM_APPLIED_MTIME = "r2b3_model_applied_mtime"
OBJECTS_EMPTY_NAME = "R2B_Objects"


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
            "hide_select": getattr(lc.collection, "hide_select", False),
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
            "hide_select": getattr(obj, "hide_select", False),
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
            if hasattr(lc.collection, "hide_select"):
                lc.collection.hide_select = state.get("hide_select", False)
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
            if hasattr(obj, "hide_select"):
                obj.hide_select = state.get("hide_select", False)
            obj.display_type = state.get("display_type", "TEXTURED")
            if hasattr(obj, "display_bounds_type"):
                obj.display_bounds_type = state.get("display_bounds_type", "BOX")
        except ReferenceError:
            pass


def _call_import_3dm(context, filepath: str, *, update_materials: bool, options=None) -> str:
    """呼叫內嵌 import_3dm.read_3dm；失敗回傳錯誤字串。"""
    opts = options if options is not None else default_import_options(
        update_materials=update_materials
    )
    try:
        result = read_3dm(context, filepath, opts)
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


def _mat4_to_blender(m16, scale: float) -> Matrix:
    scaled = rhino_mat4_translation_scaled(m16, scale)
    return Matrix(
        (
            (scaled[0], scaled[1], scaled[2], scaled[3]),
            (scaled[4], scaled[5], scaled[6], scaled[7]),
            (scaled[8], scaled[9], scaled[10], scaled[11]),
            (scaled[12], scaled[13], scaled[14], scaled[15]),
        )
    )


def _import_unit_scale(context, filepath: str) -> float:
    from .import_3dm._bootstrap_rhino3dm import ensure_rhino3dm

    ensure_rhino3dm()
    import rhino3dm as r3d

    model = r3d.File3dm.Read(filepath)
    if model is None:
        return 1.0
    return r3d.UnitSystem.UnitScale(
        model.Settings.ModelUnitSystem, r3d.UnitSystem.Meters
    ) / context.scene.unit_settings.scale_length


def _collection_for_layer(layer_full: str):
    leaf = (layer_full or "").split("::")[-1].strip()
    if not leaf:
        return None
    return bpy.data.collections.get(leaf)


def apply_block_instances(context, work_folder: str, model_path: str) -> str:
    """依 R2B_blocks.json 對原型做關聯複製。"""
    path = str(resolve_blocks_json_from_work_folder(work_folder))
    if not os.path.isfile(path):
        return ""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        return "讀取 Block sidecar 失敗：{}".format(exc)
    parsed = parse_blocks_payload(raw)
    if not parsed.ok:
        return parsed.message
    defs = parsed.data.get("definitions") or []
    if not defs:
        return ""
    try:
        scale = _import_unit_scale(context, model_path)
    except Exception:
        scale = 1.0

    for defn in defs:
        def_id = defn["id"]
        proto_objs = [
            obj
            for obj in bpy.data.objects
            if obj.get(USERSTRING_DEF_ID) == def_id and not obj.get("r2b_block_copy")
        ]
        if not proto_objs:
            continue
        copies = defn.get("copies") or []
        if not copies:
            continue
        rel_base = defn.get("prototype_xform")
        for copy in copies:
            rel = relative_xform(rel_base, copy["xform"])
            if rel is None:
                continue
            mat = _mat4_to_blender(rel, scale)
            dest = _collection_for_layer(copy.get("layer") or "")
            for proto in proto_objs:
                dup = proto.copy()
                dup.data = proto.data
                dup["r2b_block_copy"] = def_id
                if dest is None:
                    dests = list(proto.users_collection) or [context.scene.collection]
                    dest_col = dests[0]
                else:
                    dest_col = dest
                try:
                    dest_col.objects.link(dup)
                except RuntimeError:
                    context.scene.collection.objects.link(dup)
                dup.matrix_world = mat @ proto.matrix_world
    return ""


def _remove_collection_tree(col) -> None:
    if col is None:
        return
    for child in list(col.children):
        _remove_collection_tree(child)
    try:
        bpy.data.collections.remove(col)
    except Exception:
        pass


def import_objects(context) -> str:
    """累加匯入 R2B_Objects.3dm 到 Scene 最上層，parent＝R2B_Objects Empty。"""
    scene = context.scene
    folder = bpy.path.abspath(scene.r2b_sync_folder)
    path = str(resolve_objects_3dm_from_work_folder(folder))
    if not os.path.isfile(path):
        return "找不到物件檔：{}".format(path)

    before_collections = set(bpy.data.collections.keys())
    tmp_name = "_r2b_tmp_objects_{}".format(uuid.uuid4().hex[:8])
    layers_name = "_r2b_tmp_layers_{}".format(uuid.uuid4().hex[:8])
    options = default_import_options(update_materials=True)
    options["container_name"] = tmp_name
    options["wipe_container"] = False
    options["link_container"] = False
    options["layers_container_name"] = layers_name
    err = _call_import_3dm(
        context, path, update_materials=True, options=options
    )
    if err:
        for name in set(bpy.data.collections.keys()) - before_collections:
            _remove_collection_tree(bpy.data.collections.get(name))
        return err

    tmp = bpy.data.collections.get(tmp_name)
    imported = list(tmp.all_objects) if tmp else []
    parent = bpy.data.objects.new(OBJECTS_EMPTY_NAME, None)
    parent.empty_display_type = "PLAIN_AXES"
    scene.collection.objects.link(parent)

    for obj in imported:
        try:
            world = obj.matrix_world.copy()
        except ReferenceError:
            continue
        for col in list(obj.users_collection):
            try:
                col.objects.unlink(obj)
            except Exception:
                pass
        try:
            scene.collection.objects.link(obj)
        except RuntimeError:
            pass
        obj.parent = parent
        obj.matrix_world = world

    for name in set(bpy.data.collections.keys()) - before_collections:
        col = bpy.data.collections.get(name)
        if col is None:
            continue
        for obj in list(col.all_objects):
            if obj == parent or obj.parent == parent:
                try:
                    col.objects.unlink(obj)
                except Exception:
                    pass
        _remove_collection_tree(col)
    merge_duplicate_materials()
    return ""


def sync_models(context, *, update_materials: bool) -> str:
    """Update／Sync Models 共用；成功回傳 ""。"""
    scene = context.scene
    path = _model_3dm_path(scene)
    if not os.path.isfile(path):
        return "找不到模型檔：{}".format(path)

    col_states, obj_states = _capture_visibility(context)
    err = _call_import_3dm(context, path, update_materials=update_materials)
    if err:
        return err
    merge_duplicate_materials()
    folder = bpy.path.abspath(scene.r2b_sync_folder)
    err = apply_block_instances(context, folder, path)
    if err:
        return err
    _restore_visibility(context, col_states, obj_states)
    try:
        context.window_manager[_WM_APPLIED_MTIME] = os.path.getmtime(path)
    except OSError:
        pass
    return ""
