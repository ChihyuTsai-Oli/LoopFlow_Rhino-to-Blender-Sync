#! python 3
# -*- coding: utf-8 -*-
"""Yak 指令 RBObjects。開發入口仍是 entrypoints/RBObjects.py。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "RBObjects"


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
    import rhinoscriptsyntax as rs  # type: ignore

    from rhino.commands.objects import publish_objects_once

    result = publish_objects_once()
    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if result.ok:
        rs.MessageBox("Objects export succeeded\n\n{}".format(result.message), title=_CMD)
    elif result.status in ("blocked", "fail"):
        rs.MessageBox(result.message, title=_CMD)
