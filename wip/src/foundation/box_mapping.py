# -*- coding: utf-8 -*-
"""Box 投影節點組的純資料（不依賴 bpy）。"""
from __future__ import annotations

GROUP_NAME = "LoopFlow Box Projection"
GROUP_VERSION = 3
VERSION_KEY = "loopflow_box_proj_version"
GROUP_FLAG = "loopflow_box_group"
NODE_LABEL = GROUP_NAME
SCALE_SOCKET = "Scale"
LOCATION_SOCKET = "Location"
ROTATION_SOCKET = "Rotation"
BLEND_SOCKET = "Blend"
COLOR_SOCKET = "Color"
IMAGE_NODE_NAMES = (
    "LoopFlow Box Image X",
    "LoopFlow Box Image Y",
    "LoopFlow Box Image Z",
)
DEFAULT_SIZE_M = 1.0
DEFAULT_SCALE_XYZ = (1.0, 1.0, 1.0)
MIN_SIZE_M = 0.001


def scale_from_size_meters(size_m: float) -> float:
    """貼圖實際尺寸（公尺）→ 座標除數的倒數。S＝公尺／張時 P'＝P／S。"""
    size = float(size_m)
    if size <= 0:
        raise ValueError("size_m must be > 0")
    return 1.0 / size
