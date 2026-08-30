# -*- coding: utf-8 -*-
"""Blender Camera consumer：parse＋apply 成功才更新已套用狀態。"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy
import mathutils

from . import _srcpath

_srcpath.ensure_src()

from foundation.camera_payload import parse_camera_payload
from foundation.paths import resolve_camera_json_from_work_folder

CAMERA_POLL_INTERVAL = 0.016
DEFAULT_LENS = 50.0

_WM_ACTIVE = "r2b3_cam_auto_active"
_WM_SEEN_MTIME = "r2b3_cam_seen_mtime"
_WM_APPLIED_MTIME = "r2b3_cam_applied_mtime"


def _camera_json_path(scene) -> str:
    """Sync Folder＝作業資料夾（與 .3dm／.blend／_LoopFlow_Config 同層）。"""
    folder = bpy.path.abspath(scene.r2b_sync_folder)
    return str(resolve_camera_json_from_work_folder(folder))


def read_and_parse_camera(path: str):
    """回傳 (parsed_data_dict | None, error_message | None)。"""
    if not os.path.isfile(path):
        return None, "Camera file not found: {}".format(path)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception as exc:
        return None, "Read/JSON failed: {}".format(exc)
    result = parse_camera_payload(raw)
    if not result.ok:
        return None, result.message
    return result.data, None


def apply_camera_to_viewport(context, parsed, *, scale: float, lens_mult: float) -> str:
    """將已 parse 的相機套到 3D View；成功回傳空字串。"""
    try:
        loc_raw = parsed["location"]
        dir_raw = parsed["direction"]
        up_raw = parsed["up"]
        loc = mathutils.Vector(
            (loc_raw[0] * scale, loc_raw[1] * scale, loc_raw[2] * scale)
        )
        dir_vec = mathutils.Vector(dir_raw).normalized()
        up_vec = mathutils.Vector(up_raw).normalized()
        if dir_vec.length < 1e-8 or up_vec.length < 1e-8:
            return "Invalid direction/up vector"
        final_lens = float(parsed.get("lens", DEFAULT_LENS)) * lens_mult

        z_axis = -dir_vec
        x_axis = up_vec.cross(z_axis)
        if x_axis.length < 1e-8:
            return "Could not build view basis"
        x_axis.normalize()
        y_axis = z_axis.cross(x_axis).normalized()
        mat = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed()
        rot_quat = mat.to_quaternion()

        screen = getattr(context, "screen", None)
        if screen is None and context.window:
            screen = context.window.screen
        if screen is None:
            return "No available screen"
        applied = False
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            rv3d = space.region_3d
            if rv3d is None:
                continue
            if rv3d.view_perspective != "PERSP":
                rv3d.view_perspective = "PERSP"
            space.lens = final_lens
            rv3d.view_rotation = rot_quat
            rv3d.view_location = loc + dir_vec * rv3d.view_distance
            area.tag_redraw()
            applied = True
        if not applied:
            return "VIEW_3D not found"
        return ""
    except Exception as exc:
        return "Apply failed: {}".format(exc)


def push_camera_once(context) -> str:
    """手動套用一次；成功回傳 ""。"""
    scene = context.scene
    path = _camera_json_path(scene)
    parsed, err = read_and_parse_camera(path)
    if err:
        return err
    err = apply_camera_to_viewport(
        context,
        parsed,
        scale=float(scene.r2b_cam_scale),
        lens_mult=float(scene.r2b_cam_lens_mult),
    )
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


def camera_timer_poll():
    """Timer callback：僅 parse＋apply 成功才更新 applied mtime。"""
    wm = bpy.context.window_manager
    if int(wm.get(_WM_ACTIVE, 0)) != 1:
        return None

    scene = bpy.context.scene
    path = _camera_json_path(scene)
    if not os.path.isfile(path):
        return CAMERA_POLL_INTERVAL

    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return CAMERA_POLL_INTERVAL

    last_seen = float(wm.get(_WM_SEEN_MTIME, -1.0))
    if math.isclose(mtime, last_seen, rel_tol=0.0, abs_tol=1e-9):
        return CAMERA_POLL_INTERVAL

    # 標記已看過此版本；壞檔不 apply、不更新 applied
    wm[_WM_SEEN_MTIME] = mtime
    parsed, err = read_and_parse_camera(path)
    if err or not parsed:
        return CAMERA_POLL_INTERVAL

    err = apply_camera_to_viewport(
        bpy.context,
        parsed,
        scale=float(scene.r2b_cam_scale),
        lens_mult=float(scene.r2b_cam_lens_mult),
    )
    if err:
        return CAMERA_POLL_INTERVAL

    wm[_WM_APPLIED_MTIME] = mtime
    return CAMERA_POLL_INTERVAL


def set_camera_auto(context, enabled: bool) -> None:
    wm = context.window_manager
    if enabled:
        wm[_WM_ACTIVE] = 1
        wm[_WM_SEEN_MTIME] = -1.0
        if not bpy.app.timers.is_registered(camera_timer_poll):
            bpy.app.timers.register(camera_timer_poll, first_interval=CAMERA_POLL_INTERVAL)
    else:
        wm[_WM_ACTIVE] = 0
        if bpy.app.timers.is_registered(camera_timer_poll):
            bpy.app.timers.unregister(camera_timer_poll)
