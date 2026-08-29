# -*- coding: utf-8 -*-
"""RBLightPush：手動推送燈光點位 JSON 一次。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "RBLightPush"


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

    from rhino.commands.light import publish_light_once

    result = publish_light_once()
    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if not result.ok and result.status in ("blocked", "fail"):
        rs.MessageBox(result.message)


if __name__ == "__main__":
    main()
