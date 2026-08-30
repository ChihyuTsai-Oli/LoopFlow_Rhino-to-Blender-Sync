# -*- coding: utf-8 -*-
"""讓 `from foundation...` 找得到模組。

啟用 add-on 時必須在匯入 box_proj／camera_sync 之前呼叫：
那些檔一載入就會 `from foundation...`。zip 內附的 foundation 在本資料夾；
開發期則用 repo 的 wip/src。
"""
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
