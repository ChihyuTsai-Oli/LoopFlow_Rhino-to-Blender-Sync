# -*- coding: utf-8 -*-
"""記憶體 RhinoSession：單元測試用，不依賴 Rhino。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from rhino.platform.state import ObjectViewState

Color = Tuple[int, int, int]


@dataclass
class _MemObject:
    object_id: str
    layer: str
    kind: str = "other"
    selected: bool = False
    locked: bool = False
    hidden: bool = False
    color: Color = (200, 200, 200)
    color_by_layer: bool = True


@dataclass
class MemorySession:
    """可注入圖層與物件的假 session。"""

    path: Optional[str] = None
    modified: bool = False
    layers: List[str] = field(default_factory=list)
    objects: Dict[str, _MemObject] = field(default_factory=dict)
    redraw_enabled: bool = True
    select_calls: List[Tuple[str, ...]] = field(default_factory=list)

    def add_object(
        self,
        object_id: str,
        layer: str,
        *,
        kind: str = "other",
        locked: bool = False,
        hidden: bool = False,
        selected: bool = False,
    ) -> None:
        if layer not in self.layers:
            self.layers.append(layer)
        self.objects[object_id] = _MemObject(
            object_id=object_id,
            layer=layer,
            kind=kind,
            locked=locked,
            hidden=hidden,
            selected=selected,
        )

    def document_path(self) -> Optional[str]:
        return self.path

    def document_modified(self) -> bool:
        return self.modified

    def set_document_modified(self, value: bool) -> None:
        self.modified = bool(value)

    def layer_paths(self) -> Sequence[str]:
        return tuple(self.layers)

    def has_layer(self, path: str) -> bool:
        return path in self.layers

    def objects_on_layer(self, path: str) -> Sequence[str]:
        return tuple(
            oid for oid, obj in self.objects.items() if obj.layer == path
        )

    def object_kind(self, object_id: str) -> str:
        obj = self.objects.get(object_id)
        return obj.kind if obj else "other"

    def iter_object_ids(
        self, *, include_hidden: bool = True, include_locked: bool = True
    ) -> Sequence[str]:
        out = []
        for oid, obj in self.objects.items():
            if obj.hidden and not include_hidden:
                continue
            if obj.locked and not include_locked:
                continue
            out.append(oid)
        return tuple(out)

    def get_view_state(self, object_id: str) -> ObjectViewState:
        obj = self.objects[object_id]
        return ObjectViewState(
            object_id=obj.object_id,
            selected=obj.selected,
            locked=obj.locked,
            hidden=obj.hidden,
            color=obj.color,
            color_by_layer=obj.color_by_layer,
        )

    def set_view_state(self, state: ObjectViewState) -> None:
        obj = self.objects.get(state.object_id)
        if obj is None:
            return
        obj.selected = state.selected
        obj.locked = state.locked
        obj.hidden = state.hidden
        obj.color = state.color
        obj.color_by_layer = state.color_by_layer

    def select_objects(self, ids: Sequence[str]) -> None:
        id_set: Set[str] = set(ids)
        self.select_calls.append(tuple(ids))
        for oid, obj in self.objects.items():
            obj.selected = oid in id_set

    def set_redraw_enabled(self, enabled: bool) -> None:
        self.redraw_enabled = bool(enabled)
