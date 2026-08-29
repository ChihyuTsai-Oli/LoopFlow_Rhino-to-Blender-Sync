# -*- coding: utf-8 -*-
"""R2B_Objects：發布選取物件 → models/R2B_Objects_時戳.3dm。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "R2B_Objects"


def _prepare_src() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "_loopflow_isolate",
        os.path.join(here, "_isolate.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.isolate_from_entrypoint(__file__)


def main() -> None:
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


if __name__ == "__main__":
    main()
