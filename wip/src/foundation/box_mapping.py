# -*- coding: utf-8 -*-
"""Box 投影節點組的純資料（不依賴 bpy）。"""
from __future__ import annotations

GROUP_NAME = "LoopFlow Box Projection"
SIZE_SOCKET = "Size"
LOCATION_SOCKET = "Location"
ROTATION_SOCKET = "Rotation"
VECTOR_SOCKET = "Vector"
DEFAULT_SIZE_M = 1.0
MIN_SIZE_M = 0.001


def scale_from_size_meters(size_m: float) -> float:
    """貼圖實際尺寸（公尺）→ Mapping Scale。Blender 預設一張貼圖跨 1 個場景單位。"""
    size = float(size_m)
    if size <= 0:
        raise ValueError("size_m must be > 0")
    return 1.0 / size
