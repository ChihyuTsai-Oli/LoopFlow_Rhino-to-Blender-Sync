# -*- coding: utf-8 -*-
"""Box 投影常數（不依賴 bpy）。"""
from __future__ import annotations

NODE_LABEL = "LoopFlow Box Projection"
OSL_TEXT_NAME = "LoopFlow_Box_Projection.osl"
OSL_FILE_NAME = "box_projection.osl"
OSL_NODE_FLAG = "loopflow_box_osl"
COLOR_SOCKET = "Color"
FILENAME_SOCKET = "Filename"
DEFAULT_SIZE_M = 1.0
DEFAULT_SCALE_XYZ = (1.0, 1.0, 1.0)


def scale_from_size_meters(size_m: float) -> float:
    """貼圖實際尺寸（公尺）→ 座標除數的倒數。S＝公尺／張時 P'＝P／S。"""
    size = float(size_m)
    if size <= 0:
        raise ValueError("size_m must be > 0")
    return 1.0 / size
