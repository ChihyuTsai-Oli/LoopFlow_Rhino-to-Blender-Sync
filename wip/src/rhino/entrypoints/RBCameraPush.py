# -*- coding: utf-8 -*-
"""RBCameraPush：手動推送相機 JSON 一次。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "RBCameraPush"


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

    from rhino.commands.camera import publish_camera_once

    result = publish_camera_once()
    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if not result.ok and result.status == "blocked":
        rs.MessageBox(result.message)


if __name__ == "__main__":
    main()
