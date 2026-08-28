# -*- coding: utf-8 -*-
"""Light JSON 契約（開發暫定 schema_version=1；兩端共用）。

本輪只同步 Point 位置＋guid／type（ED-06）。
空 points：手動 Push 不發布；自動同步在「先前有點→現在為零」可發 clear=true 清 consumer（ED-07 修正）。
合法燈點必須在 LightLayer **子層**（例 R2B_LT_Points::Downlight），不可只在父層。
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
    """只認 LightLayer 子層（prefix::…）；父層本身與前綴撞名層皆非法。"""
    if not layer_full or not prefix:
        return False
    return layer_full.startswith(prefix + "::")


def build_light_payload(
    points: Sequence[Mapping[str, Any]],
    *,
    producer: str = PRODUCER_RHINO,
    document_name: str = "",
    light_layer: str = DEFAULT_LIGHT_LAYER,
    clear: bool = False,
) -> Dict[str, Any]:
    """組出可發布的 Light payload。clear=True 時允許 points 為空。"""
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
    payload = {
        "schema_version": SCHEMA_VERSION,
        "producer": producer,
        "document": document_name or "",
        "light_layer": light_layer,
        "points": normalized,
    }
    if clear:
        payload["clear"] = True
    return payload


def validate_light_payload(data: Any) -> Optional[str]:
    """回傳錯誤字串；通過則 None。空 points 僅在 clear=true 時合法。"""
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
    clear = bool(data.get("clear"))
    if len(points) == 0 and not clear:
        return "points 為空：不發布、不清燈（ED-07）；需 clear=true 才可清空"
    if clear and len(points) != 0:
        return "clear=true 時 points 必須為空陣列"
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
            "clear": bool(data.get("clear")),
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
