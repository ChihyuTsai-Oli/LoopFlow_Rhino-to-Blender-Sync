# -*- coding: utf-8 -*-
"""Rhino 執行期 session（延遲 import；模組載入不需 Rhino）。"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from rhino.platform.state import ObjectViewState

Color = Tuple[int, int, int]


def _rs():
    import rhinoscriptsyntax as rs  # type: ignore

    return rs


def _sc():
    import scriptcontext as sc  # type: ignore

    return sc


class LiveSession:
    """對現行 ActiveDoc 的薄包裝；禁止內部使用 _SelAll。"""

    def document_path(self) -> Optional[str]:
        doc = _sc().doc
        if doc is None:
            return None
        path = getattr(doc, "Path", None) or ""
        return path or None

    def document_modified(self) -> bool:
        doc = _sc().doc
        return bool(getattr(doc, "Modified", False)) if doc else False

    def set_document_modified(self, value: bool) -> None:
        try:
            _rs().DocumentModified(bool(value))
        except Exception:
            doc = _sc().doc
            if doc is not None:
                doc.Modified = bool(value)

    def layer_paths(self) -> Sequence[str]:
        out = []
        doc = _sc().doc
        if doc is None:
            return ()
        for layer in doc.Layers:
            if layer is None or getattr(layer, "IsDeleted", False):
                continue
            fp = getattr(layer, "FullPath", None)
            if fp:
                out.append(str(fp))
        return tuple(out)

    def has_layer(self, path: str) -> bool:
        return path in set(self.layer_paths())

    def objects_on_layer(self, path: str) -> Sequence[str]:
        try:
            ids = _rs().ObjectsByLayer(path) or []
            return tuple(str(i) for i in ids)
        except Exception:
            return ()

    def object_kind(self, object_id: str) -> str:
        rs = _rs()
        try:
            if rs.IsPoint(object_id):
                return "point"
            if rs.IsCurve(object_id):
                return "curve"
            if rs.IsMesh(object_id):
                return "mesh"
            if rs.IsBlockInstance(object_id):
                return "block"
            if rs.IsPolysurface(object_id):
                return "polysurface"
            if rs.IsSurface(object_id):
                return "surface"
            if rs.IsBrep(object_id):
                return "brep"
        except Exception:
            pass
        # SubD／Extrusion：rs 未必有對應 Is*，改看 ObjectType
        try:
            import Rhino  # type: ignore

            guid = rs.coerceguid(object_id)
            robj = _sc().doc.Objects.FindId(guid) if guid else None
            if robj is not None:
                ot = robj.ObjectType
                if ot == Rhino.DocObjects.ObjectType.SubD:
                    return "subd"
                if ot == Rhino.DocObjects.ObjectType.Extrusion:
                    return "extrusion"
                if ot == Rhino.DocObjects.ObjectType.InstanceReference:
                    return "instance"
        except Exception:
            pass
        return "other"

    def iter_object_ids(
        self, *, include_hidden: bool = True, include_locked: bool = True
    ) -> Sequence[str]:
        rs = _rs()
        try:
            ids = rs.AllObjects(include_lights=False, include_grips=False) or []
        except Exception:
            return ()
        out = []
        for oid in ids:
            try:
                if (not include_hidden) and rs.IsObjectHidden(oid):
                    continue
                if (not include_locked) and rs.IsObjectLocked(oid):
                    continue
            except Exception:
                pass
            out.append(str(oid))
        return tuple(out)

    def get_view_state(self, object_id: str) -> ObjectViewState:
        rs = _rs()
        color = (200, 200, 200)
        by_layer = True
        try:
            c = rs.ObjectColor(object_id)
            if c is not None:
                color = (int(c[0]), int(c[1]), int(c[2]))
        except Exception:
            pass
        try:
            by_layer = bool(rs.ObjectColorSource(object_id) == 0)
        except Exception:
            pass
        return ObjectViewState(
            object_id=str(object_id),
            selected=bool(rs.IsObjectSelected(object_id)),
            locked=bool(rs.IsObjectLocked(object_id)),
            hidden=bool(rs.IsObjectHidden(object_id)),
            color=color,
            color_by_layer=by_layer,
        )

    def set_view_state(self, state: ObjectViewState) -> None:
        rs = _rs()
        oid = state.object_id
        try:
            if state.selected:
                rs.SelectObject(oid, quiet=True)
            else:
                rs.UnselectObject(oid)
        except Exception:
            pass
        try:
            if state.locked:
                rs.LockObject(oid)
            else:
                rs.UnlockObject(oid)
        except Exception:
            pass
        try:
            if state.hidden:
                rs.HideObject(oid)
            else:
                rs.ShowObject(oid)
        except Exception:
            pass

    def select_objects(self, ids: Sequence[str]) -> None:
        """精準選取；明確不呼叫 _SelAll。"""
        rs = _rs()
        try:
            rs.UnselectAllObjects()
        except Exception:
            pass
        if not ids:
            return
        try:
            rs.SelectObjects(list(ids))
        except Exception:
            for oid in ids:
                try:
                    rs.SelectObject(oid, quiet=True)
                except Exception:
                    pass

    def set_redraw_enabled(self, enabled: bool) -> None:
        try:
            _rs().EnableRedraw(bool(enabled))
        except Exception:
            pass


def open_session() -> LiveSession:
    """取得現行文件 session（需在 Rhino 內呼叫）。"""
    return LiveSession()
