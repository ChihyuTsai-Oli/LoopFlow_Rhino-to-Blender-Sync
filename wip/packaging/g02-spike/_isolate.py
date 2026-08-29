# -*- coding: utf-8 -*-
"""Yak 指令載入前：把 wip/src 放到最前，並清掉 R2O 同名套件快取。"""
from __future__ import annotations

import os
import sys


def isolate_src(src):
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


def isolate_for_yak_command(command_file):
    here = os.path.dirname(os.path.abspath(command_file))
    src = os.path.abspath(os.path.join(here, "..", "..", "..", "src"))
    if os.path.isdir(os.path.join(src, "foundation")):
        return isolate_src(src)
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
    return ""
