# -*- coding: utf-8 -*-
"""R2B_Camera：開／關自動同步 toggle（再按一次停止）。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "R2B_Camera"


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

    from rhino.commands.camera import camera_toggle_auto

    result = camera_toggle_auto()

    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if not result.ok and result.status == "blocked":
        rs.MessageBox(result.message)


if __name__ == "__main__":
    main()
