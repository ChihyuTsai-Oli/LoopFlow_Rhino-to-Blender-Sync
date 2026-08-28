# -*- coding: utf-8 -*-
"""Block 關聯複製 sidecar（純邏輯；不依賴 Rhino／Blender）。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence

SCHEMA_VERSION = 1
USERSTRING_DEF_ID = "r2b_block_def"


def empty_blocks_payload() -> dict:
    return {"schema_version": SCHEMA_VERSION, "definitions": []}


def build_blocks_payload(definitions: Sequence[Mapping[str, Any]]) -> dict:
    return {"schema_version": SCHEMA_VERSION, "definitions": list(definitions)}


def _as_mat4(node: Any) -> Optional[List[float]]:
    if not isinstance(node, (list, tuple)) or len(node) != 16:
        return None
    out: List[float] = []
    try:
        for item in node:
            out.append(float(item))
    except (TypeError, ValueError):
        return None
    return out


def validate_blocks_payload(data: Any) -> Optional[str]:
    if not isinstance(data, Mapping):
        return "Block JSON root must be an object"
    try:
        ver = int(data.get("schema_version"))
    except (TypeError, ValueError):
        return "Missing or invalid schema_version"
    if ver != SCHEMA_VERSION:
        return "Unsupported schema_version: {} (need {})".format(ver, SCHEMA_VERSION)
    defs = data.get("definitions")
    if not isinstance(defs, list):
        return "Field definitions must be an array"
    for idx, item in enumerate(defs):
        if not isinstance(item, Mapping):
            return "definitions[{}] must be an object".format(idx)
        if not str(item.get("id") or "").strip():
            return "definitions[{}] is missing id".format(idx)
        if _as_mat4(item.get("prototype_xform")) is None:
            return "definitions[{}] prototype_xform must be 16 numbers".format(idx)
        copies = item.get("copies")
        if not isinstance(copies, list):
            return "definitions[{}] copies must be an array".format(idx)
        for cidx, copy in enumerate(copies):
            if not isinstance(copy, Mapping):
                return "definitions[{}].copies[{}] must be an object".format(idx, cidx)
            if _as_mat4(copy.get("xform")) is None:
                return "definitions[{}].copies[{}] xform must be 16 numbers".format(
                    idx, cidx
                )
    return None


def parse_blocks_payload(data: Any):
    from foundation.result import Result

    err = validate_blocks_payload(data)
    if err:
        return Result.fail(err, stage="parse_blocks")
    assert isinstance(data, Mapping)
    defs_out = []
    for item in data["definitions"]:
        copies = []
        for copy in item.get("copies") or []:
            copies.append(
                {
                    "xform": _as_mat4(copy.get("xform")),
                    "layer": str(copy.get("layer") or ""),
                }
            )
        defs_out.append(
            {
                "id": str(item["id"]),
                "name": str(item.get("name") or ""),
                "prototype_xform": _as_mat4(item.get("prototype_xform")),
                "copies": copies,
            }
        )
    return Result.success(
        stage="parse_blocks",
        data={"schema_version": SCHEMA_VERSION, "definitions": defs_out},
    )


def validate_blocks_file(path) -> Optional[str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception as exc:
        return "Block sidecar could not be parsed: {}".format(exc)
    return validate_blocks_payload(data)


def mat4_mul(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """列主序 4x4：C = A × B（先 B 後 A）。"""
    out = [0.0] * 16
    for row in range(4):
        for col in range(4):
            total = 0.0
            for k in range(4):
                total += float(a[row * 4 + k]) * float(b[k * 4 + col])
            out[row * 4 + col] = total
    return out


def mat4_identity() -> List[float]:
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def mat4_invert(m: Sequence[float]) -> Optional[List[float]]:
    """4x4 反矩陣；奇異則 None。"""
    a = [float(x) for x in m]
    inv = mat4_identity()
    for col in range(4):
        pivot = col
        best = abs(a[pivot * 4 + col])
        for row in range(col + 1, 4):
            val = abs(a[row * 4 + col])
            if val > best:
                best = val
                pivot = row
        if best < 1e-12:
            return None
        if pivot != col:
            for k in range(4):
                a[col * 4 + k], a[pivot * 4 + k] = a[pivot * 4 + k], a[col * 4 + k]
                inv[col * 4 + k], inv[pivot * 4 + k] = (
                    inv[pivot * 4 + k],
                    inv[col * 4 + k],
                )
        diag = a[col * 4 + col]
        for k in range(4):
            a[col * 4 + k] /= diag
            inv[col * 4 + k] /= diag
        for row in range(4):
            if row == col:
                continue
            factor = a[row * 4 + col]
            if abs(factor) < 1e-18:
                continue
            for k in range(4):
                a[row * 4 + k] -= factor * a[col * 4 + k]
                inv[row * 4 + k] -= factor * inv[col * 4 + k]
    return inv


def relative_xform(prototype: Sequence[float], other: Sequence[float]) -> Optional[List[float]]:
    """other × inverse(prototype)，讓已在 prototype 世界座標的幾何對到 other。"""
    inv = mat4_invert(prototype)
    if inv is None:
        return None
    return mat4_mul(other, inv)


def rhino_mat4_translation_scaled(m: Sequence[float], scale: float) -> List[float]:
    """旋轉不變，平移乘 scale（對齊 import_3dm 頂點縮放）。"""
    out = [float(x) for x in m]
    out[3] *= float(scale)
    out[7] *= float(scale)
    out[11] *= float(scale)
    return out
