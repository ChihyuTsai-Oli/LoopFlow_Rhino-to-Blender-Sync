# -*- coding: utf-8 -*-
"""Rhino Light 通道：手動推一次／自動同步開／關（只位置；空點不發布）。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional

from foundation.atomic import atomic_publish_json
from foundation.light_payload import (
    DEFAULT_LIGHT_LAYER,
    build_light_payload,
    layer_matches_prefix,
    validate_light_file,
)
from foundation.log import append_log
from foundation.paths import (
    config_root_for_document,
    ensure_config_layout,
    light_path,
    require_saved_document_path,
)
from foundation.result import Result

_STICKY_HANDLERS = "R2B3_Light_Sync_Handlers"
_STICKY_PATH = "R2B3_LIGHT_JSON_PATH"
_STICKY_LAYER = "R2B3_LIGHT_LAYER"


def _sticky():
    import scriptcontext as sc  # type: ignore

    return sc.sticky


def _resolve_publish_target() -> Result:
    import scriptcontext as sc  # type: ignore

    doc = sc.doc
    path = getattr(doc, "Path", None) if doc else None
    saved = require_saved_document_path(path)
    if not saved.ok:
        return saved
    root = ensure_config_layout(config_root_for_document(saved.data))
    return Result.success(data={"root": root, "light": light_path(root)}, stage="resolve_path")


def collect_light_points(light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    """掃描全場景 Point，過濾 LightLayer 前綴（含子層）。"""
    import rhinoscriptsyntax as rs  # type: ignore

    points = rs.ObjectsByType(1) or []
    collected: List[dict] = []
    for pt in points:
        layer_full = rs.ObjectLayer(pt) or ""
        if not layer_matches_prefix(layer_full, light_layer):
            continue
        layer_short = layer_full.split("::")[-1]
        coord = rs.PointCoordinates(pt)
        collected.append(
            {
                "guid": str(pt),
                "type": layer_short,
                "loc": (coord.X, coord.Y, coord.Z),
            }
        )
    if not collected:
        return Result.blocked(
            "無符合 LightLayer「{}」的 Point：不發布、不清 Blender 燈".format(light_layer),
            stage="collect_lights",
        )
    return Result.success(stage="collect_lights", data=collected)


def publish_light_once(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    """收集並 atomic 發布 light.json；空點＝blocked，不動 last-good。"""
    import scriptcontext as sc  # type: ignore

    collected = collect_light_points(light_layer)
    if not collected.ok:
        return collected

    target = _resolve_publish_target()
    if not target.ok:
        return target

    doc = sc.doc
    doc_name = os.path.basename(doc.Path or "") if doc and doc.Path else ""
    payload = build_light_payload(
        collected.data,
        document_name=doc_name,
        light_layer=light_layer,
    )
    final = Path(target.data["light"])
    root = Path(target.data["root"])
    result = atomic_publish_json(final, payload, validate=validate_light_file)
    append_log(
        root,
        "Light publish: {} ({}); count={}".format(
            result.status, result.message, len(collected.data)
        ),
    )
    if result.ok:
        return Result.success(
            "已發布 {} 個燈點：{}".format(len(collected.data), final),
            stage="publish_light",
            data=str(final),
        )
    return result


def _try_auto_publish() -> None:
    """自動同步：失敗略過；空點不寫檔。"""
    try:
        sticky = _sticky()
        json_path = sticky.get(_STICKY_PATH)
        if not json_path:
            return
        layer = sticky.get(_STICKY_LAYER) or DEFAULT_LIGHT_LAYER
        collected = collect_light_points(layer)
        if not collected.ok:
            return
        import scriptcontext as sc  # type: ignore

        doc = sc.doc
        doc_name = os.path.basename(doc.Path or "") if doc and doc.Path else ""
        payload = build_light_payload(
            collected.data,
            document_name=doc_name,
            light_layer=layer,
        )
        atomic_publish_json(json_path, payload, validate=validate_light_file)
    except Exception:
        pass


def _on_doc_changed(sender: Any, e: Any) -> None:
    _try_auto_publish()


def light_auto_on(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    import Rhino  # type: ignore

    target = _resolve_publish_target()
    if not target.ok:
        return target
    sticky = _sticky()
    if _STICKY_HANDLERS in sticky:
        return Result.success("Light 自動同步已在執行", stage="light_auto_on")

    path = str(target.data["light"])
    sticky[_STICKY_PATH] = path
    sticky[_STICKY_LAYER] = light_layer

    handlers = {
        "add": _on_doc_changed,
        "delete": _on_doc_changed,
        "replace": _on_doc_changed,
        "undelete": _on_doc_changed,
    }
    Rhino.RhinoDoc.AddRhinoObject += handlers["add"]
    Rhino.RhinoDoc.DeleteRhinoObject += handlers["delete"]
    Rhino.RhinoDoc.ReplaceRhinoObject += handlers["replace"]
    Rhino.RhinoDoc.UndeleteRhinoObject += handlers["undelete"]
    sticky[_STICKY_HANDLERS] = handlers

    push = publish_light_once(light_layer=light_layer)
    append_log(target.data["root"], "Light Auto On → {}".format(path))
    if push.ok:
        return Result.success("Light 自動同步已開啟：{}".format(path), stage="light_auto_on")
    return Result.success(
        "Light 自動同步已開啟（首次推送：{}）".format(push.message),
        stage="light_auto_on",
    )


def light_auto_off() -> Result:
    import Rhino  # type: ignore

    sticky = _sticky()
    if _STICKY_HANDLERS not in sticky:
        return Result.success("Light 自動同步本來就關閉", stage="light_auto_off")
    handlers = sticky.get(_STICKY_HANDLERS) or {}
    try:
        if "add" in handlers:
            Rhino.RhinoDoc.AddRhinoObject -= handlers["add"]
        if "delete" in handlers:
            Rhino.RhinoDoc.DeleteRhinoObject -= handlers["delete"]
        if "replace" in handlers:
            Rhino.RhinoDoc.ReplaceRhinoObject -= handlers["replace"]
        if "undelete" in handlers:
            Rhino.RhinoDoc.UndeleteRhinoObject -= handlers["undelete"]
    except Exception:
        pass
    sticky.pop(_STICKY_HANDLERS, None)
    sticky.pop(_STICKY_PATH, None)
    sticky.pop(_STICKY_LAYER, None)
    return Result.success("Light 自動同步已關閉", stage="light_auto_off")


def light_is_auto_on() -> bool:
    try:
        return _STICKY_HANDLERS in _sticky()
    except Exception:
        return False


def light_toggle_auto(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    if light_is_auto_on():
        return light_auto_off()
    return light_auto_on(light_layer=light_layer)
