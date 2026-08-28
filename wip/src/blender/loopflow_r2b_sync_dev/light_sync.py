# -*- coding: utf-8 -*-
"""Blender Light consumer：parse＋apply；空／無效不清燈（ED-07）。"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

import bpy
import mathutils

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.light_payload import parse_light_payload
from foundation.paths import resolve_light_json_from_work_folder

COL_FIXTURES = "Lighting Fixtures"
COL_LIGHTING = "Lighting"
COL_LIGHT_POINTS = "R2B Lighting Points"
EMPTY_DISPLAY_SIZE = 0.3
LIGHT_POLL_INTERVAL = 0.25

_WM_ACTIVE = "r2b3_light_auto_active"
_WM_SEEN_MTIME = "r2b3_light_seen_mtime"
_WM_APPLIED_MTIME = "r2b3_light_applied_mtime"


def _light_json_path(scene) -> str:
    folder = bpy.path.abspath(scene.r2b_sync_folder)
    return str(resolve_light_json_from_work_folder(folder))


def get_template_objects(type_name: str):
    templates = []
    clean_type = type_name.strip()
    for col_name in (COL_FIXTURES, COL_LIGHTING):
        col = bpy.data.collections.get(col_name)
        if not col:
            continue
        for obj in col.objects:
            base_name = re.sub(r"\.\d{3}$", "", obj.name).strip()
            if base_name == clean_type:
                templates.append(obj)
                break
    return templates


def read_and_parse_light(path: str):
    if not os.path.isfile(path):
        return None, "找不到 Light 檔：{}".format(path)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception as exc:
        return None, "讀取／JSON 失敗：{}".format(exc)
    result = parse_light_payload(raw)
    if not result.ok:
        return None, result.message
    return result.data, None


def apply_light_points(context, parsed, *, scale: float) -> str:
    """套用非空 points；成功回傳 ""。"""
    points = parsed.get("points") or []
    if not points:
        return "points 為空：不清燈（ED-07）"

    light_col = bpy.data.collections.get(COL_LIGHT_POINTS)
    if not light_col:
        light_col = bpy.data.collections.new(COL_LIGHT_POINTS)
        context.scene.collection.children.link(light_col)

    active_guids = set()
    try:
        for pt_data in points:
            guid = pt_data["guid"]
            active_guids.add(guid)
            pt_type = pt_data["type"]
            loc_raw = pt_data["loc"]
            pt_loc = mathutils.Vector(
                (loc_raw[0] * scale, loc_raw[1] * scale, loc_raw[2] * scale)
            )

            target_empty = None
            for obj in light_col.objects:
                try:
                    if obj.get("rhino_guid") == guid:
                        target_empty = obj
                        break
                except ReferenceError:
                    pass

            if target_empty:
                target_empty.location = pt_loc
                target_empty["rhino_type"] = pt_type
            else:
                new_empty = bpy.data.objects.new("RH_{}_{}".format(pt_type, guid[:5]), None)
                new_empty.empty_display_type = "PLAIN_AXES"
                new_empty.empty_display_size = EMPTY_DISPLAY_SIZE
                new_empty["rhino_guid"] = guid
                new_empty["rhino_type"] = pt_type
                light_col.objects.link(new_empty)
                new_empty.location = pt_loc
                target_empty = new_empty

                for potential_child in bpy.data.objects:
                    try:
                        if potential_child.get("recovered_rhino_guid") == guid:
                            world_mat = potential_child.matrix_world.copy()
                            potential_child.parent = target_empty
                            potential_child.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                            parent_future_world = mathutils.Matrix.Translation(pt_loc)
                            potential_child.matrix_local = parent_future_world.inverted() @ world_mat
                            del potential_child["recovered_rhino_guid"]
                    except ReferenceError:
                        pass

            templates = get_template_objects(pt_type)
            processed_insts = []
            for template in templates:
                safe_name = re.sub(r"\.\d{3}$", "", template.name)
                prefix = "INST_{}_{}".format(safe_name, guid[:5])
                existing_inst = None
                for child in target_empty.children:
                    try:
                        if child.name.startswith(prefix) and child not in processed_insts:
                            existing_inst = child
                            break
                    except ReferenceError:
                        pass
                if existing_inst:
                    existing_inst.location = template.location
                    existing_inst.rotation_euler = template.rotation_euler
                    existing_inst.scale = template.scale
                    processed_insts.append(existing_inst)
                else:
                    new_inst = template.copy()
                    if template.data:
                        new_inst.data = template.data
                    new_inst.name = prefix
                    light_col.objects.link(new_inst)
                    new_inst.parent = target_empty
                    new_inst.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                    new_inst.location = template.location
                    new_inst.rotation_euler = template.rotation_euler
                    new_inst.scale = template.scale
                    processed_insts.append(new_inst)

            for child in list(target_empty.children):
                try:
                    if child.name.startswith("INST_") and child not in processed_insts:
                        bpy.data.objects.remove(child, do_unlink=True)
                except ReferenceError:
                    pass

        empties_to_remove = []
        for obj in light_col.objects:
            try:
                if "rhino_guid" in obj and obj["rhino_guid"] not in active_guids:
                    empties_to_remove.append(obj)
            except ReferenceError:
                pass

        for empty in empties_to_remove:
            try:
                removed_guid = empty["rhino_guid"]
                for child in list(empty.children):
                    try:
                        if child.name.startswith("INST_"):
                            bpy.data.objects.remove(child, do_unlink=True)
                        else:
                            child["recovered_rhino_guid"] = removed_guid
                            world_mat = child.matrix_world.copy()
                            child.parent = None
                            child.matrix_world = world_mat
                    except ReferenceError:
                        pass
                bpy.data.objects.remove(empty, do_unlink=True)
            except ReferenceError:
                pass
    except Exception as exc:
        return "套用失敗：{}".format(exc)
    return ""


def push_light_once(context) -> str:
    scene = context.scene
    path = _light_json_path(scene)
    parsed, err = read_and_parse_light(path)
    if err:
        return err
    err = apply_light_points(context, parsed, scale=float(scene.r2b_cam_scale))
    if err:
        return err
    wm = context.window_manager
    try:
        mtime = os.path.getmtime(path)
        wm[_WM_SEEN_MTIME] = mtime
        wm[_WM_APPLIED_MTIME] = mtime
    except OSError:
        pass
    return ""


def light_timer_poll():
    wm = bpy.context.window_manager
    if int(wm.get(_WM_ACTIVE, 0)) != 1:
        return None

    scene = bpy.context.scene
    path = _light_json_path(scene)
    if not os.path.isfile(path):
        return LIGHT_POLL_INTERVAL

    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return LIGHT_POLL_INTERVAL

    last_seen = float(wm.get(_WM_SEEN_MTIME, -1.0))
    if math.isclose(mtime, last_seen, rel_tol=0.0, abs_tol=1e-9):
        return LIGHT_POLL_INTERVAL

    wm[_WM_SEEN_MTIME] = mtime
    parsed, err = read_and_parse_light(path)
    if err or not parsed:
        return LIGHT_POLL_INTERVAL

    err = apply_light_points(
        bpy.context, parsed, scale=float(scene.r2b_cam_scale)
    )
    if err:
        return LIGHT_POLL_INTERVAL

    wm[_WM_APPLIED_MTIME] = mtime
    return LIGHT_POLL_INTERVAL


def set_light_auto(context, enabled: bool) -> None:
    wm = context.window_manager
    if enabled:
        wm[_WM_ACTIVE] = 1
        wm[_WM_SEEN_MTIME] = -1.0
        if not bpy.app.timers.is_registered(light_timer_poll):
            bpy.app.timers.register(light_timer_poll, first_interval=LIGHT_POLL_INTERVAL)
    else:
        wm[_WM_ACTIVE] = 0
        if bpy.app.timers.is_registered(light_timer_poll):
            bpy.app.timers.unregister(light_timer_poll)
