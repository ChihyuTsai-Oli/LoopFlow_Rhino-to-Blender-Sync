# -*- coding: utf-8 -*-
"""清掉同名套件快取，避免同一 Rhino 行程裡 R2B／R2O 互踩。"""
from __future__ import annotations

import os
import sys


def isolate_src(src: str) -> str:
    """刪除 `rhino`／`foundation` 快取，把此產品 src 放到 sys.path 最前。"""
    src = os.path.abspath(src)
    doomed = [
        name
        for name in list(sys.modules)
        if name == "rhino"
        or name.startswith("rhino.")
        or name == "foundation"
        or name.startswith("foundation.")
    ]
    for name in doomed:
        del sys.modules[name]
    while src in sys.path:
        sys.path.remove(src)
    sys.path.insert(0, src)
    return src


def isolate_from_entrypoint(entrypoint_file: str) -> str:
    here = os.path.dirname(os.path.abspath(entrypoint_file))
    src = os.path.abspath(os.path.join(here, "..", ".."))
    return isolate_src(src)
