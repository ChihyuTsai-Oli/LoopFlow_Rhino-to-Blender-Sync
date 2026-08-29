#! python 3
# -*- coding: utf-8 -*-
"""Yak 指令 RBOpen。開發入口仍是 entrypoints/RBOpen.py。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "RBOpen"


def _prepare_src():
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "_loopflow_r2b_yak_isolate",
        os.path.join(here, "..", "_isolate.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.isolate_for_yak_command(__file__)


def RunCommand(is_interactive):
    _prepare_src()
    from rhino.commands.open import run_open

    result = run_open()
    print("{} [{}]".format(_CMD, result.status))
    if result.message:
        print(result.message)
