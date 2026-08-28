# -*- coding: utf-8 -*-
"""R2B Import 預設 Principled 底色（不依賴 bpy）。"""
from __future__ import annotations

from typing import Any, Tuple

# 使用者指定的 Import 預設色（sRGB HEX，含 alpha）
DEFAULT_BASE_COLOR_HEX = "F2F2F2FF"


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


def hex_srgb_to_linear_rgb(hex_color: str) -> Tuple[float, float, float]:
    """#RRGGBB 或 RRGGBBAA → Principled 線性 RGB。"""
    h = (hex_color or "").strip().lstrip("#")
    if len(h) < 6:
        h = DEFAULT_BASE_COLOR_HEX
    try:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
    except ValueError:
        r = g = b = 0xF2 / 255.0
    return (
        _srgb_channel_to_linear(r),
        _srgb_channel_to_linear(g),
        _srgb_channel_to_linear(b),
    )


DEFAULT_BASE_COLOR_LINEAR = hex_srgb_to_linear_rgb(DEFAULT_BASE_COLOR_HEX)


def classic_diffuse_linear_rgb(color: Any) -> Tuple[float, float, float]:
    """舊路徑：Rhino DiffuseColor → 線性 RGB（R2B Import 預設改走 HEX）。"""
    r = g = b = 0.8
    try:
        if color is None:
            pass
        elif hasattr(color, "R"):
            r, g, b = float(color.R), float(color.G), float(color.B)
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            r, g, b = float(color[0]), float(color[1]), float(color[2])
    except (TypeError, ValueError):
        return DEFAULT_BASE_COLOR_LINEAR
    r, g, b = _to_srgb_unit(r), _to_srgb_unit(g), _to_srgb_unit(b)
    return (_srgb_channel_to_linear(r), _srgb_channel_to_linear(g), _srgb_channel_to_linear(b))
