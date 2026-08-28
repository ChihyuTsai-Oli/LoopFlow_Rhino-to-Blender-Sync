# -*- coding: utf-8 -*-
"""R2B.3dm 經典材質 → 線性 RGB（不依賴 bpy）。"""
from __future__ import annotations

from typing import Any, Tuple


def _srgb_channel_to_linear(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _to_srgb_unit(value: float) -> float:
    x = float(value)
    if x > 1.0:
        x = x / 255.0
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def classic_diffuse_linear_rgb(color: Any) -> Tuple[float, float, float]:
    """Rhino DiffuseColor（0–255 或 0–1）→ Principled base_color 線性 RGB。"""
    r = g = b = 0.8
    try:
        if color is None:
            pass
        elif hasattr(color, "R"):
            r, g, b = float(color.R), float(color.G), float(color.B)
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            r, g, b = float(color[0]), float(color[1]), float(color[2])
    except (TypeError, ValueError):
        return (0.8, 0.8, 0.8)
    r, g, b = _to_srgb_unit(r), _to_srgb_unit(g), _to_srgb_unit(b)
    return (_srgb_channel_to_linear(r), _srgb_channel_to_linear(g), _srgb_channel_to_linear(b))
