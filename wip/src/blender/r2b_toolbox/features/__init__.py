# -*- coding: utf-8 -*-
"""功能清單。加／刪模組只改 FEATURES，並對齊 wip/docs/toolbox/功能/<id>.md。"""
from __future__ import annotations

import importlib

FEATURES = ("export", "rename", "selection")


def register():
    for name in FEATURES:
        importlib.import_module(".{0}".format(name), __name__).register()


def unregister():
    for name in reversed(FEATURES):
        importlib.import_module(".{0}".format(name), __name__).unregister()
