# -*- coding: utf-8 -*-
"""開發期用 repo 的 wip/src；Install from Disk 後用 zip 內附的 foundation。"""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_src() -> str:
    here = Path(__file__).resolve().parent
    if (here / "foundation").is_dir():
        root = here
    else:
        root = here.parents[2]
    path = str(root)
    if path not in sys.path:
        sys.path.insert(0, path)
    return path
