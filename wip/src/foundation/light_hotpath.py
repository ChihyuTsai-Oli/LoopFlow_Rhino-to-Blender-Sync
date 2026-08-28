# -*- coding: utf-8 -*-
"""燈光自動同步：事件過濾與指紋（純邏輯，不依賴 Rhino）。"""
from __future__ import annotations

from typing import Any, Mapping, Sequence, Tuple

from foundation.light_payload import layer_matches_prefix

LIGHT_AUTO_DEBOUNCE_SEC = 0.2

LightFingerprint = Tuple[Any, ...]


def object_is_light_point(object_kind: str, layer_full: str, light_layer: str) -> bool:
    """只有 LightLayer 子層上的 Point 才觸發自動發布。"""
    return str(object_kind or "").lower() == "point" and layer_matches_prefix(
        layer_full, light_layer
    )


def light_payload_fingerprint(
    points: Sequence[Mapping[str, Any]], *, clear: bool = False
) -> LightFingerprint:
    """guid＋type＋loc；clear 另成獨立指紋，避免空清單與 clear 混淆。"""
    if clear:
        return ("clear",)
    rows = []
    for item in points:
        loc = item["loc"]
        rows.append(
            (
                str(item["guid"]),
                str(item["type"]),
                round(float(loc[0]), 6),
                round(float(loc[1]), 6),
                round(float(loc[2]), 6),
            )
        )
    return tuple(sorted(rows))
