# -*- coding: utf-8 -*-
"""Rhino Light 通道：手動推一次／自動同步開／關（只位置；空點手動不發、自動可 clear）。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List

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
_STICKY_HAD_POINTS = "R2B3_LIGHT_HAD_POINTS"


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
    """掃描全場景 Point；只收 LightLayer **子層**上的點。"""
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
            "無符合 LightLayer「{}::…」子層的 Point：手動不發布；若先前有點，自動同步會發 clear".format(
                light_layer
            ),
            stage="collect_lights",
        )
    return Result.success(stage="collect_lights", data=collected)


def _write_payload(final: Path, root: Path, payload: dict, count_label: str) -> Result:
    result = atomic_publish_json(final, payload, validate=validate_light_file)
    append_log(
        root,
        "Light publish: {} ({}); {}".format(result.status, result.message, count_label),
    )
    return result


def publish_light_once(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    """手動推：空點＝blocked，不動 last-good（ED-07）。"""
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
    result = _write_payload(final, root, payload, "count={}".format(len(collected.data)))
    if result.ok:
        try:
            _sticky()[_STICKY_HAD_POINTS] = True
        except Exception:
            pass
        return Result.success(
            "已發布 {} 個燈點：{}".format(len(collected.data), final),
            stage="publish_light",
            data=str(final),
        )
    return result


def publish_light_clear(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    """發布 clear=true 空清單，供 Blender 移除全部 rhino_guid empty。"""
    import scriptcontext as sc  # type: ignore

    target = _resolve_publish_target()
    if not target.ok:
        return target
    doc = sc.doc
    doc_name = os.path.basename(doc.Path or "") if doc and doc.Path else ""
    payload = build_light_payload(
        [],
        document_name=doc_name,
        light_layer=light_layer,
        clear=True,
    )
    final = Path(target.data["light"])
    root = Path(target.data["root"])
    result = _write_payload(final, root, payload, "clear=true")
    if result.ok:
        try:
            _sticky()[_STICKY_HAD_POINTS] = False
        except Exception:
            pass
    return result


def _try_auto_publish() -> None:
    """自動同步：有點就發；先前有點而今為零則發 clear。"""
    try:
        sticky = _sticky()
        json_path = sticky.get(_STICKY_PATH)
        if not json_path:
            return
        layer = sticky.get(_STICKY_LAYER) or DEFAULT_LIGHT_LAYER
        collected = collect_light_points(layer)
        import scriptcontext as sc  # type: ignore

        doc = sc.doc
        doc_name = os.path.basename(doc.Path or "") if doc and doc.Path else ""
        final = Path(json_path)

        if collected.ok:
            payload = build_light_payload(
                collected.data,
                document_name=doc_name,
                light_layer=layer,
            )
            result = atomic_publish_json(final, payload, validate=validate_light_file)
            if result.ok:
                sticky[_STICKY_HAD_POINTS] = True
            return

        # 無合法點：僅在本 session 曾成功發過點時發 clear，避免誤設 LightLayer 一次清空
        if sticky.get(_STICKY_HAD_POINTS):
            payload = build_light_payload(
                [],
                document_name=doc_name,
                light_layer=layer,
                clear=True,
            )
            result = atomic_publish_json(final, payload, validate=validate_light_file)
            if result.ok:
                sticky[_STICKY_HAD_POINTS] = False
    except Exception:
        pass


def _on_doc_changed(sender: Any, e: Any) -> None:
    _try_auto_publish()


def _on_attributes_modified(sender: Any, e: Any) -> None:
    """換圖層等屬性變更：僅 LayerIndex 變動才重發（避免選取雜訊）。"""
    try:
        old_attrs = getattr(e, "OldAttributes", None)
        new_attrs = getattr(e, "NewAttributes", None)
        if old_attrs is None or new_attrs is None:
            return
        if int(old_attrs.LayerIndex) == int(new_attrs.LayerIndex):
            return
        _try_auto_publish()
    except Exception:
        pass


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
        "attrs": _on_attributes_modified,
    }
    Rhino.RhinoDoc.AddRhinoObject += handlers["add"]
    Rhino.RhinoDoc.DeleteRhinoObject += handlers["delete"]
    Rhino.RhinoDoc.ReplaceRhinoObject += handlers["replace"]
    Rhino.RhinoDoc.UndeleteRhinoObject += handlers["undelete"]
    Rhino.RhinoDoc.ModifyObjectAttributes += handlers["attrs"]
    sticky[_STICKY_HANDLERS] = handlers

    push = publish_light_once(light_layer=light_layer)
    append_log(target.data["root"], "Light Auto On → {}".format(path))
    if push.ok:
        sticky[_STICKY_HAD_POINTS] = True
        return Result.success("Light 自動同步已開啟：{}".format(path), stage="light_auto_on")
    sticky[_STICKY_HAD_POINTS] = False
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
        if "attrs" in handlers:
            Rhino.RhinoDoc.ModifyObjectAttributes -= handlers["attrs"]
    except Exception:
        pass
    sticky.pop(_STICKY_HANDLERS, None)
    sticky.pop(_STICKY_PATH, None)
    sticky.pop(_STICKY_LAYER, None)
    # 保留 HAD_POINTS，避免關再開後誤清；下次成功推送會再設
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
