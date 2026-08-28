# -*- coding: utf-8 -*-
"""Models 3dm 發布驗證（開發暫定；不依賴 Rhino／rhino3dm）。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


def validate_model_3dm(path: PathLike) -> Optional[str]:
    """pending／final 基本檢查：存在、非空、副檔名。通過回傳 None。"""
    p = Path(path)
    if not p.is_file():
        return "Model file not found: {}".format(p)
    if p.suffix.lower() != ".3dm":
        return "Extension must be .3dm: {}".format(p.name)
    try:
        size = p.stat().st_size
    except OSError as exc:
        return "Could not read model file size: {}".format(exc)
    if size <= 0:
        return "Model file is empty"
    # 3dm 檔頭常見為 "3D Geometry File Format" 或 Rhino 二進位；至少擋明顯非 3dm
    try:
        head = p.read_bytes()[:32]
    except OSError as exc:
        return "Could not read model file header: {}".format(exc)
    if not head:
        return "Model file header is empty"
    return None
