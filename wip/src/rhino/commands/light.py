# -*- coding: utf-8 -*-
"""Rhino Light 通道：手動推一次／自動同步開／關（只位置；空點手動不發、自動可 clear）。"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, List

from foundation.atomic import atomic_publish_json, direct_overwrite_json
from foundation.light_hotpath import (
    LIGHT_AUTO_DEBOUNCE_SEC,
    light_payload_fingerprint,
    object_is_light_point,
)
from foundation.light_payload import (
    DEFAULT_LIGHT_LAYER,
    build_light_payload,
    layer_matches_prefix,
    validate_light_file,
    validate_light_payload,
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
_STICKY_DIRTY = "R2B3_LIGHT_DIRTY"
_STICKY_LAST_EVENT = "R2B3_LIGHT_LAST_EVENT"
_STICKY_FINGERPRINT = "R2B3_LIGHT_FINGERPRINT"


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
            "No Point on LightLayer '{}::…' sublayers: manual push skipped; auto sync may send clear if points existed".format(
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
            sticky = _sticky()
            sticky[_STICKY_HAD_POINTS] = True
            sticky[_STICKY_FINGERPRINT] = light_payload_fingerprint(collected.data)
        except Exception:
            pass
        return Result.success(
            "Published {} light points: {}".format(len(collected.data), final),
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
            sticky = _sticky()
            sticky[_STICKY_HAD_POINTS] = False
            sticky[_STICKY_FINGERPRINT] = light_payload_fingerprint([], clear=True)
        except Exception:
            pass
    return result


def _layer_full_from_object(obj: Any, attrs: Any = None) -> str:
    try:
        import Rhino  # type: ignore

        doc = getattr(obj, "Document", None) or Rhino.RhinoDoc.ActiveDoc
        if doc is None:
            return ""
        index = None
        if attrs is not None:
            index = getattr(attrs, "LayerIndex", None)
        if index is None:
            index = obj.Attributes.LayerIndex
        return str(doc.Layers[int(index)].FullPath)
    except Exception:
        return ""


def _rhino_object_is_point(obj: Any) -> bool:
    try:
        import Rhino  # type: ignore

        return obj.ObjectType == Rhino.DocObjects.ObjectType.Point
    except Exception:
        return False


def _event_object(e: Any) -> Any:
    return getattr(e, "TheObject", None) or getattr(e, "Object", None)


def _is_watched_light_point(obj: Any, light_layer: str, attrs: Any = None) -> bool:
    if obj is None or not _rhino_object_is_point(obj):
        return False
    return object_is_light_point("point", _layer_full_from_object(obj, attrs), light_layer)


def _note_light_dirty() -> None:
    try:
        sticky = _sticky()
        sticky[_STICKY_DIRTY] = True
        sticky[_STICKY_LAST_EVENT] = time.monotonic()
    except Exception:
        pass


def _try_auto_publish() -> None:
    """自動同步：有點就發；先前有點而今為零則發 clear；指紋未變不寫檔。"""
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
            fingerprint = light_payload_fingerprint(collected.data)
            if fingerprint == sticky.get(_STICKY_FINGERPRINT):
                return
            payload = build_light_payload(
                collected.data,
                document_name=doc_name,
                light_layer=layer,
            )
            if validate_light_payload(payload):
                return
            result = direct_overwrite_json(final, payload, indent=None)
            if result.ok:
                sticky[_STICKY_HAD_POINTS] = True
                sticky[_STICKY_FINGERPRINT] = fingerprint
            return

        if sticky.get(_STICKY_HAD_POINTS):
            fingerprint = light_payload_fingerprint([], clear=True)
            if fingerprint == sticky.get(_STICKY_FINGERPRINT):
                return
            payload = build_light_payload(
                [],
                document_name=doc_name,
                light_layer=layer,
                clear=True,
            )
            if validate_light_payload(payload):
                return
            result = direct_overwrite_json(final, payload, indent=None)
            if result.ok:
                sticky[_STICKY_HAD_POINTS] = False
                sticky[_STICKY_FINGERPRINT] = fingerprint
    except Exception:
        pass


def _on_idle(sender: Any, e: Any) -> None:
    try:
        sticky = _sticky()
        if not sticky.get(_STICKY_DIRTY):
            return
        last_event = float(sticky.get(_STICKY_LAST_EVENT) or 0.0)
        if (time.monotonic() - last_event) < LIGHT_AUTO_DEBOUNCE_SEC:
            return
        sticky[_STICKY_DIRTY] = False
        _try_auto_publish()
    except Exception:
        pass


def _on_add_or_delete(sender: Any, e: Any) -> None:
    try:
        layer = _sticky().get(_STICKY_LAYER) or DEFAULT_LIGHT_LAYER
        if _is_watched_light_point(_event_object(e), layer):
            _note_light_dirty()
    except Exception:
        pass


def _on_replace(sender: Any, e: Any) -> None:
    try:
        layer = _sticky().get(_STICKY_LAYER) or DEFAULT_LIGHT_LAYER
        old_obj = getattr(e, "OldRhinoObject", None)
        new_obj = getattr(e, "NewRhinoObject", None)
        if _is_watched_light_point(old_obj, layer) or _is_watched_light_point(new_obj, layer):
            _note_light_dirty()
    except Exception:
        pass


def _on_attributes_modified(sender: Any, e: Any) -> None:
    """換圖層：僅 Point 且舊或新圖層落在 LightLayer 子層才重發。"""
    try:
        old_attrs = getattr(e, "OldAttributes", None)
        new_attrs = getattr(e, "NewAttributes", None)
        if old_attrs is None or new_attrs is None:
            return
        if int(old_attrs.LayerIndex) == int(new_attrs.LayerIndex):
            return
        obj = getattr(e, "RhinoObject", None) or _event_object(e)
        if obj is None or not _rhino_object_is_point(obj):
            return
        layer = _sticky().get(_STICKY_LAYER) or DEFAULT_LIGHT_LAYER
        old_full = _layer_full_from_object(obj, old_attrs)
        new_full = _layer_full_from_object(obj, new_attrs)
        if object_is_light_point("point", old_full, layer) or object_is_light_point(
            "point", new_full, layer
        ):
            _note_light_dirty()
    except Exception:
        pass


def light_auto_on(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    import Rhino  # type: ignore

    target = _resolve_publish_target()
    if not target.ok:
        return target
    sticky = _sticky()
    if _STICKY_HANDLERS in sticky:
        return Result.success("Light auto sync already running", stage="light_auto_on")

    path = str(target.data["light"])
    sticky[_STICKY_PATH] = path
    sticky[_STICKY_LAYER] = light_layer
    sticky[_STICKY_DIRTY] = False

    handlers = {
        "add": _on_add_or_delete,
        "delete": _on_add_or_delete,
        "replace": _on_replace,
        "undelete": _on_add_or_delete,
        "attrs": _on_attributes_modified,
        "idle": _on_idle,
    }
    Rhino.RhinoDoc.AddRhinoObject += handlers["add"]
    Rhino.RhinoDoc.DeleteRhinoObject += handlers["delete"]
    Rhino.RhinoDoc.ReplaceRhinoObject += handlers["replace"]
    Rhino.RhinoDoc.UndeleteRhinoObject += handlers["undelete"]
    Rhino.RhinoDoc.ModifyObjectAttributes += handlers["attrs"]
    try:
        Rhino.RhinoApp.Idle += handlers["idle"]
    except Exception:
        handlers.pop("idle", None)
    sticky[_STICKY_HANDLERS] = handlers

    push = publish_light_once(light_layer=light_layer)
    append_log(target.data["root"], "Light Auto On → {}".format(path))
    if push.ok:
        sticky[_STICKY_HAD_POINTS] = True
        return Result.success("Light auto sync on: {}".format(path), stage="light_auto_on")
    sticky[_STICKY_HAD_POINTS] = False
    return Result.success(
        "Light auto sync on (first push: {})".format(push.message),
        stage="light_auto_on",
    )


def light_auto_off() -> Result:
    import Rhino  # type: ignore

    sticky = _sticky()
    if _STICKY_HANDLERS not in sticky:
        return Result.success("Light auto sync was already off", stage="light_auto_off")
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
        if "idle" in handlers:
            Rhino.RhinoApp.Idle -= handlers["idle"]
    except Exception:
        pass
    sticky.pop(_STICKY_HANDLERS, None)
    sticky.pop(_STICKY_PATH, None)
    sticky.pop(_STICKY_LAYER, None)
    sticky.pop(_STICKY_DIRTY, None)
    sticky.pop(_STICKY_LAST_EVENT, None)
    return Result.success("Light auto sync off", stage="light_auto_off")


def light_is_auto_on() -> bool:
    try:
        return _STICKY_HANDLERS in _sticky()
    except Exception:
        return False


def light_toggle_auto(*, light_layer: str = DEFAULT_LIGHT_LAYER) -> Result:
    if light_is_auto_on():
        return light_auto_off()
    return light_auto_on(light_layer=light_layer)
