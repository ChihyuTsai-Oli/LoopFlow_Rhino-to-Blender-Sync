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
        return "模型檔不存在：{}".format(p)
    if p.suffix.lower() != ".3dm":
        return "副檔名必須是 .3dm：{}".format(p.name)
    try:
        size = p.stat().st_size
    except OSError as exc:
        return "無法讀取模型檔大小：{}".format(exc)
    if size <= 0:
        return "模型檔為空"
    # 3dm 檔頭常見為 "3D Geometry File Format" 或 Rhino 二進位；至少擋明顯非 3dm
    try:
        head = p.read_bytes()[:32]
    except OSError as exc:
        return "無法讀取模型檔頭：{}".format(exc)
    if not head:
        return "模型檔頭為空"
    return None
