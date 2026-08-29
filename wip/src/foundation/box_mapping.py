# -*- coding: utf-8 -*-
"""Box 投影節點組的純資料（不依賴 bpy）。"""
from __future__ import annotations

import re
from pathlib import Path

GROUP_NAME = "LoopFlow Box Projection"
GROUP_VERSION = 5
VERSION_KEY = "loopflow_box_proj_version"
GROUP_FLAG = "loopflow_box_group"
NODE_LABEL = GROUP_NAME
SCALE_SOCKET = "Scale"
LOCATION_SOCKET = "Location"
ROTATION_SOCKET = "Rotation"
BLEND_SOCKET = "Blend"
SPACE_SOCKET = "Object Space"
COLOR_SOCKET = "Color"
ROUGHNESS_SOCKET = "Roughness"
METALLIC_SOCKET = "Metallic"
NORMAL_SOCKET = "Normal"

MAP_SLOTS = ("color", "roughness", "metallic", "normal")
SLOT_OUTPUT = {
    "color": COLOR_SOCKET,
    "roughness": ROUGHNESS_SOCKET,
    "metallic": METALLIC_SOCKET,
    "normal": NORMAL_SOCKET,
}
SLOT_LABEL = {
    "color": "Base Color",
    "roughness": "Roughness",
    "metallic": "Metallic",
    "normal": "Normal",
}
# 較具體的 token 先比；每個檔只歸一槽
SLOT_TOKENS = (
    ("normal", ("normal", "nrm", "norm", "nor")),
    ("metallic", ("metallic", "metalness", "metal")),
    ("roughness", ("roughness", "rough")),
    ("color", ("basecolor", "albedo", "diffuse", "diff", "color", "col")),
)
IMAGE_NODE_NAMES = {
    "color": (
        "LoopFlow Box Color X",
        "LoopFlow Box Color Y",
        "LoopFlow Box Color Z",
    ),
    "roughness": (
        "LoopFlow Box Rough X",
        "LoopFlow Box Rough Y",
        "LoopFlow Box Rough Z",
    ),
    "metallic": (
        "LoopFlow Box Metal X",
        "LoopFlow Box Metal Y",
        "LoopFlow Box Metal Z",
    ),
    "normal": (
        "LoopFlow Box Normal X",
        "LoopFlow Box Normal Y",
        "LoopFlow Box Normal Z",
    ),
}
DEFAULT_SIZE_M = 1.0
DEFAULT_SCALE_XYZ = (1.0, 1.0, 1.0)
MIN_SIZE_M = 0.001
_SPLIT = re.compile(r"[^a-z0-9]+")


def scale_from_size_meters(size_m: float) -> float:
    """貼圖實際尺寸（公尺）→ 座標除數的倒數。S＝公尺／張時 P'＝P／S。"""
    size = float(size_m)
    if size <= 0:
        raise ValueError("size_m must be > 0")
    return 1.0 / size


def pbr_filename_tokens(name):
    """檔名（可含路徑）→ token 集合；含相鄰兩段黏合（base+color → basecolor）。"""
    stem = Path(str(name)).stem.lower()
    parts = [p for p in _SPLIT.split(stem) if p]
    glued = ["".join(parts[i : i + 2]) for i in range(max(0, len(parts) - 1))]
    return set(parts) | set(glued)


def classify_pbr_filename(name):
    """單一檔名對到 color／roughness／metallic／normal；對不到則 None。"""
    bag = pbr_filename_tokens(name)
    for slot, tokens in SLOT_TOKENS:
        for tok in tokens:
            if tok in bag:
                return slot
    return None


def classify_pbr_files(names):
    """多檔：每槽最多一張（先出現者）。回傳 {slot: original_name}。"""
    result = {}
    for name in names:
        slot = classify_pbr_filename(name)
        if slot and slot not in result:
            result[slot] = name
    return result
