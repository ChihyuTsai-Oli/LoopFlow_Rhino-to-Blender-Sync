# -*- coding: utf-8 -*-
"""Rhino Camera 通道：手動推一次／自動同步開／關。"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

from foundation.atomic import atomic_publish_json
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
_STICKY_IDLE = "R2B3_Camera_Sync_Idle"
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
        return Result.fail("無作用中文件", stage="capture_camera")
    view = doc.Views.ActiveView
    if not view:
        return Result.fail("無作用中視角", stage="capture_camera")
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
    """自動同步熱路徑：記憶體驗證、緊湊 JSON、略過 fsync 與 pending 重讀。"""
    err = validate_camera_payload(payload)
    if err:
        return False
    result = atomic_publish_json(
        json_path,
        payload,
        indent=None,
        validate=None,
        fsync=False,
        retries=1,
        delay_sec=0.0,
    )
    return bool(result.ok)


def _flush_auto_camera() -> None:
    try:
        sticky = _sticky()
        json_path = sticky.get(_STICKY_PATH)
        gate = sticky.get(_STICKY_GATE)
        if not json_path or gate is None:
            return
        if not gate.due_to_flush(time.monotonic()):
            return
        cap = capture_active_camera()
        if not cap.ok:
            return
        pose = payload_pose(cap.data)
        decision = gate.decide(time.monotonic(), pose)
        if decision != "publish":
            return
        if _publish_camera_hot(str(json_path), cap.data):
            gate.mark_published(time.monotonic(), pose)
    except Exception:
        pass


def _on_view_modified(sender: Any, e: Any) -> None:
    """標記 dirty；間隔到了才擷取寫盤，避免每幀 capture。"""
    try:
        gate = _sticky().get(_STICKY_GATE)
        if gate is None:
            return
        gate.note_view_modified()
        _flush_auto_camera()
    except Exception:
        pass


def _on_idle(sender: Any, e: Any) -> None:
    """補發旋轉結束後尚未寫出的最後姿態。"""
    _flush_auto_camera()


def camera_auto_on() -> Result:
    import Rhino  # type: ignore

    target = _resolve_publish_target()
    if not target.ok:
        return target
    sticky = _sticky()
    if _STICKY_EVENT in sticky:
        return Result.success("Camera 自動同步已在執行", stage="camera_auto_on")

    path = str(target.data["camera"])
    sticky[_STICKY_PATH] = path
    sticky[_STICKY_GATE] = CameraAutoPublishGate()
    sticky[_STICKY_EVENT] = _on_view_modified
    sticky[_STICKY_IDLE] = _on_idle
    Rhino.Display.RhinoView.Modified += _on_view_modified
    try:
        Rhino.RhinoApp.Idle += _on_idle
    except Exception:
        sticky.pop(_STICKY_IDLE, None)
    # 開自動同步時先推一次，方便 Blender 立刻對齊（完整 atomic）
    push = publish_camera_once()
    cap = capture_active_camera()
    if cap.ok:
        sticky[_STICKY_GATE].mark_published(time.monotonic(), payload_pose(cap.data))
    append_log(target.data["root"], "Camera Auto On → {}".format(path))
    if push.ok:
        return Result.success("Camera 自動同步已開啟：{}".format(path), stage="camera_auto_on")
    return Result.success(
        "Camera 自動同步已開啟（首次推送：{}）".format(push.message),
        stage="camera_auto_on",
    )


def camera_auto_off() -> Result:
    import Rhino  # type: ignore

    sticky = _sticky()
    if _STICKY_EVENT not in sticky:
        return Result.success("Camera 自動同步本來就關閉", stage="camera_auto_off")
    func = sticky.get(_STICKY_EVENT)
    idle = sticky.get(_STICKY_IDLE)
    try:
        if func is not None:
            Rhino.Display.RhinoView.Modified -= func
    except Exception:
        pass
    try:
        if idle is not None:
            Rhino.RhinoApp.Idle -= idle
    except Exception:
        pass
    sticky.pop(_STICKY_EVENT, None)
    sticky.pop(_STICKY_IDLE, None)
    sticky.pop(_STICKY_PATH, None)
    sticky.pop(_STICKY_DOC, None)
    sticky.pop(_STICKY_GATE, None)
    return Result.success("Camera 自動同步已關閉", stage="camera_auto_off")


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
