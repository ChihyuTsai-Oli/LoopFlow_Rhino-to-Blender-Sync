# -*- coding: utf-8 -*-
"""Camera JSON 契約（開發暫定 schema_version=1；兩端共用）。"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from foundation.result import Result

SCHEMA_VERSION = 1
PRODUCER_RHINO = "r2b_rhino"

Vec3 = Tuple[float, float, float]


def _as_xyz(node: Any, field: str) -> Optional[Vec3]:
    if not isinstance(node, Mapping):
        return None
    try:
        return (float(node["x"]), float(node["y"]), float(node["z"]))
    except (KeyError, TypeError, ValueError):
        return None


def build_camera_payload(
    *,
    location: Vec3,
    direction: Vec3,
    up: Vec3,
    lens: float,
    producer: str = PRODUCER_RHINO,
    document_name: str = "",
) -> Dict[str, Any]:
    """組出可發布的 Camera payload。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "producer": producer,
        "document": document_name or "",
        "location": {"x": float(location[0]), "y": float(location[1]), "z": float(location[2])},
        "direction": {
            "x": float(direction[0]),
            "y": float(direction[1]),
            "z": float(direction[2]),
        },
        "up": {"x": float(up[0]), "y": float(up[1]), "z": float(up[2])},
        "lens": float(lens),
    }


def validate_camera_payload(data: Any) -> Optional[str]:
    """回傳錯誤字串；通過則 None。"""
    if not isinstance(data, Mapping):
        return "Camera JSON 根節點必須是物件"
    try:
        ver = int(data.get("schema_version"))
    except (TypeError, ValueError):
        return "缺少或無效的 schema_version"
    if ver != SCHEMA_VERSION:
        return "不支援的 schema_version：{}（需要 {}）".format(ver, SCHEMA_VERSION)
    for key in ("location", "direction", "up"):
        if _as_xyz(data.get(key), key) is None:
            return "欄位 {} 必須含 x/y/z 數值".format(key)
    try:
        float(data.get("lens"))
    except (TypeError, ValueError):
        return "欄位 lens 必須是數值"
    return None


def parse_camera_payload(data: Any) -> Result:
    """Parse 成功回傳 data=正規化 dict；失敗不猜測。"""
    err = validate_camera_payload(data)
    if err:
        return Result.fail(err, stage="parse_camera")
    assert isinstance(data, Mapping)
    loc = _as_xyz(data["location"], "location")
    direction = _as_xyz(data["direction"], "direction")
    up = _as_xyz(data["up"], "up")
    assert loc and direction and up
    return Result.success(
        stage="parse_camera",
        data={
            "schema_version": SCHEMA_VERSION,
            "producer": str(data.get("producer") or ""),
            "document": str(data.get("document") or ""),
            "location": loc,
            "direction": direction,
            "up": up,
            "lens": float(data["lens"]),
        },
    )


def payload_pose(payload: Mapping[str, Any]) -> Optional[Tuple[float, ...]]:
    """抽出比對用姿態（location＋direction＋up＋lens）；無效則 None。"""
    loc = _as_xyz(payload.get("location"), "location")
    direction = _as_xyz(payload.get("direction"), "direction")
    up = _as_xyz(payload.get("up"), "up")
    if loc is None or direction is None or up is None:
        return None
    try:
        lens = float(payload.get("lens"))
    except (TypeError, ValueError):
        return None
    return loc + direction + up + (lens,)


def poses_equivalent(
    a: Optional[Tuple[float, ...]],
    b: Optional[Tuple[float, ...]],
    *,
    pos_eps: float = 1e-6,
    lens_eps: float = 1e-3,
) -> bool:
    """epsilon 內視為同一姿態；缺欄或長度不對則否。"""
    if a is None or b is None or len(a) != 10 or len(b) != 10:
        return False
    for i in range(9):
        if abs(a[i] - b[i]) > pos_eps:
            return False
    return abs(a[9] - b[9]) <= lens_eps


def validate_camera_file(path) -> Optional[str]:
    """atomic publish 用：讀 pending 檔並驗證 JSON。"""
    import json
    from pathlib import Path

    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception as exc:
        return "Camera pending 無法解析：{}".format(exc)
    return validate_camera_payload(data)
