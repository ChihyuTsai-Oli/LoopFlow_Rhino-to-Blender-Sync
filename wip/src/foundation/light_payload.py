# -*- coding: utf-8 -*-
"""Light JSON 契約（開發暫定 schema_version=1；兩端共用）。

本輪只同步 Point 位置＋guid／type（ED-06）。
空 points 視為無效發布（ED-07：不覆寫 last-good、consumer 不清燈）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from foundation.result import Result

SCHEMA_VERSION = 1
PRODUCER_RHINO = "r2b_rhino"

# 開發暫定：與 2.x LightLayer 預設同名（設定檔 JSON 落地前寫死）
DEFAULT_LIGHT_LAYER = "R2B_LT_Points"

Loc3 = Tuple[float, float, float]


def layer_matches_prefix(layer_full: str, prefix: str) -> bool:
    """圖層前綴比對：精確或子層（prefix::…），避免 R2B_LT_Points_舊 誤中。"""
    if not layer_full or not prefix:
        return False
    if layer_full == prefix:
        return True
    return layer_full.startswith(prefix + "::")


def build_light_payload(
    points: Sequence[Mapping[str, Any]],
    *,
    producer: str = PRODUCER_RHINO,
    document_name: str = "",
    light_layer: str = DEFAULT_LIGHT_LAYER,
) -> Dict[str, Any]:
    """組出可發布的 Light payload（呼叫端應先確保 points 非空）。"""
    normalized: List[Dict[str, Any]] = []
    for item in points:
        loc = item["loc"]
        normalized.append(
            {
                "guid": str(item["guid"]),
                "type": str(item["type"]),
                "loc": [float(loc[0]), float(loc[1]), float(loc[2])],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "producer": producer,
        "document": document_name or "",
        "light_layer": light_layer,
        "points": normalized,
    }


def validate_light_payload(data: Any) -> Optional[str]:
    """回傳錯誤字串；通過則 None。空 points 一律失敗（ED-07）。"""
    if not isinstance(data, Mapping):
        return "Light JSON 根節點必須是物件"
    try:
        ver = int(data.get("schema_version"))
    except (TypeError, ValueError):
        return "缺少或無效的 schema_version"
    if ver != SCHEMA_VERSION:
        return "不支援的 schema_version：{}（需要 {}）".format(ver, SCHEMA_VERSION)
    points = data.get("points")
    if not isinstance(points, list):
        return "欄位 points 必須是陣列"
    if len(points) == 0:
        return "points 為空：不發布、不清燈（ED-07）"
    for idx, item in enumerate(points):
        if not isinstance(item, Mapping):
            return "points[{}] 必須是物件".format(idx)
        if not str(item.get("guid") or "").strip():
            return "points[{}] 缺少 guid".format(idx)
        if not str(item.get("type") or "").strip():
            return "points[{}] 缺少 type".format(idx)
        loc = item.get("loc")
        if not isinstance(loc, (list, tuple)) or len(loc) != 3:
            return "points[{}] loc 必須是長度 3 的陣列".format(idx)
        try:
            float(loc[0])
            float(loc[1])
            float(loc[2])
        except (TypeError, ValueError):
            return "points[{}] loc 必須是數值".format(idx)
    return None


def parse_light_payload(data: Any) -> Result:
    """Parse 成功回傳正規化 dict；空／無效失敗。"""
    err = validate_light_payload(data)
    if err:
        return Result.fail(err, stage="parse_light")
    assert isinstance(data, Mapping)
    points_out = []
    for item in data["points"]:
        loc = item["loc"]
        points_out.append(
            {
                "guid": str(item["guid"]),
                "type": str(item["type"]),
                "loc": (float(loc[0]), float(loc[1]), float(loc[2])),
            }
        )
    return Result.success(
        stage="parse_light",
        data={
            "schema_version": SCHEMA_VERSION,
            "producer": str(data.get("producer") or ""),
            "document": str(data.get("document") or ""),
            "light_layer": str(data.get("light_layer") or DEFAULT_LIGHT_LAYER),
            "points": points_out,
        },
    )


def validate_light_file(path) -> Optional[str]:
    """atomic publish 用：讀 pending 並驗證。"""
    import json
    from pathlib import Path

    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception as exc:
        return "Light pending 無法解析：{}".format(exc)
    return validate_light_payload(data)
