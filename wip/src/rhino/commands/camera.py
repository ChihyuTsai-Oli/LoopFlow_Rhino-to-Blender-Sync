# -*- coding: utf-8 -*-
"""Rhino Camera 通道：手動推一次／自動同步開／關。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from foundation.atomic import atomic_publish_json, direct_overwrite_json
from foundation.camera_hotpath import CameraAutoPublishGate
from foundation.camera_payload import (
    build_camera_payload,
    payload_pose,
    validate_camera_file,
    validate_camera_payload,
)
from foundation.log import append_log
from foundation.paths import (
    camera_path,
    config_root_for_document,
    ensure_config_layout,
    require_saved_document_path,
)
from foundation.result import Result

_STICKY_EVENT = "R2B3_Camera_Sync_Event"
_STICKY_PATH = "R2B3_CAMERA_JSON_PATH"
_STICKY_DOC = "R2B3_CAMERA_DOC_NAME"
_STICKY_GATE = "R2B3_CAMERA_GATE"


def _sticky():
    import scriptcontext as sc  # type: ignore

    return sc.sticky


def capture_active_camera() -> Result:
    """從 ActiveView 擷取相機；無視角則 fail。"""
    import Rhino  # type: ignore

    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return Result.fail("No active document", stage="capture_camera")
    view = doc.Views.ActiveView
    if not view:
        return Result.fail("No active view", stage="capture_camera")
    vp = view.ActiveViewport
    loc = vp.CameraLocation
    direction = vp.CameraDirection
    up = vp.CameraUp
    payload = build_camera_payload(
        location=(loc.X, loc.Y, loc.Z),
        direction=(direction.X, direction.Y, direction.Z),
        up=(up.X, up.Y, up.Z),
        lens=float(vp.Camera35mmLensLength),
        document_name=os.path.basename(doc.Path or "") if doc.Path else "",
    )
    return Result.success(stage="capture_camera", data=payload)


def _resolve_publish_target() -> Result:
    import scriptcontext as sc  # type: ignore

    doc = sc.doc
    path = getattr(doc, "Path", None) if doc else None
    saved = require_saved_document_path(path)
    if not saved.ok:
        return saved
    root = ensure_config_layout(config_root_for_document(saved.data))
    return Result.success(data={"root": root, "camera": camera_path(root)}, stage="resolve_path")


def publish_camera_once(payload: Optional[dict] = None) -> Result:
    """擷取（或使用既有 payload）並 atomic 發布 camera.json。"""
    if payload is None:
        cap = capture_active_camera()
        if not cap.ok:
            return cap
        payload = cap.data
    target = _resolve_publish_target()
    if not target.ok:
        return target
    final = Path(target.data["camera"])
    root = Path(target.data["root"])
    result = atomic_publish_json(final, payload, validate=validate_camera_file)
    append_log(root, "Camera publish: {} ({})".format(result.status, result.message))
    return result


def _publish_camera_hot(json_path: str, payload: dict) -> bool:
    """自動同步熱路徑：直接覆蓋 final（對齊 2.x json.dump）。"""
    err = validate_camera_payload(payload)
    if err:
        return False
    return bool(direct_overwrite_json(json_path, payload, indent=None).ok)


def _on_view_modified(sender: Any, e: Any) -> None:
    """視角一變就擷取寫盤；姿態未變則略過。"""
    try:
        sticky = _sticky()
        json_path = sticky.get(_STICKY_PATH)
        gate = sticky.get(_STICKY_GATE)
        if not json_path or gate is None:
            return
        cap = capture_active_camera()
        if not cap.ok:
            return
        pose = payload_pose(cap.data)
        if not gate.should_publish(pose):
            return
        if _publish_camera_hot(str(json_path), cap.data):
            gate.mark_published(pose)
    except Exception:
        pass


def camera_auto_on() -> Result:
    import Rhino  # type: ignore

    target = _resolve_publish_target()
    if not target.ok:
        return target
    sticky = _sticky()
    if _STICKY_EVENT in sticky:
        return Result.success("Camera auto sync already running", stage="camera_auto_on")

    path = str(target.data["camera"])
    sticky[_STICKY_PATH] = path
    sticky[_STICKY_GATE] = CameraAutoPublishGate()
    sticky[_STICKY_EVENT] = _on_view_modified
    Rhino.Display.RhinoView.Modified += _on_view_modified
    # 開自動同步時先推一次，方便 Blender 立刻對齊（完整 atomic）
    push = publish_camera_once()
    cap = capture_active_camera()
    if cap.ok:
        sticky[_STICKY_GATE].mark_published(payload_pose(cap.data))
    append_log(target.data["root"], "Camera Auto On → {}".format(path))
    if push.ok:
        return Result.success("Camera auto sync on: {}".format(path), stage="camera_auto_on")
    return Result.success(
        "Camera auto sync on (first push: {})".format(push.message),
        stage="camera_auto_on",
    )


def camera_auto_off() -> Result:
    import Rhino  # type: ignore

    sticky = _sticky()
    if _STICKY_EVENT not in sticky:
        return Result.success("Camera auto sync was already off", stage="camera_auto_off")
    func = sticky.get(_STICKY_EVENT)
    try:
        if func is not None:
            Rhino.Display.RhinoView.Modified -= func
    except Exception:
        pass
    sticky.pop(_STICKY_EVENT, None)
    sticky.pop(_STICKY_PATH, None)
    sticky.pop(_STICKY_DOC, None)
    sticky.pop(_STICKY_GATE, None)
    idle = sticky.pop("R2B3_Camera_Sync_Idle", None)
    try:
        if idle is not None:
            Rhino.RhinoApp.Idle -= idle
    except Exception:
        pass
    return Result.success("Camera auto sync off", stage="camera_auto_off")


def camera_is_auto_on() -> bool:
    try:
        return _STICKY_EVENT in _sticky()
    except Exception:
        return False


def camera_toggle_auto() -> Result:
    """開／關自動同步（按一下切換）。"""
    if camera_is_auto_on():
        return camera_auto_off()
    return camera_auto_on()
