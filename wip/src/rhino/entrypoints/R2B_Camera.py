# -*- coding: utf-8 -*-
"""R2B_Camera 開發入口：Push／AutoOn／AutoOff。"""
from __future__ import annotations

import os
import sys

_CMD = "R2B_Camera"


def _repo_src_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    src = _repo_src_root()
    if src not in sys.path:
        sys.path.insert(0, src)

    import rhinoscriptsyntax as rs  # type: ignore

    from rhino.commands.camera import camera_auto_off, camera_auto_on, publish_camera_once

    mode = rs.GetString("R2B Camera", "Push", ["Push", "AutoOn", "AutoOff"])
    if not mode:
        print("{}：已取消".format(_CMD))
        return

    if mode == "Push":
        result = publish_camera_once()
    elif mode == "AutoOn":
        result = camera_auto_on()
    elif mode == "AutoOff":
        result = camera_auto_off()
    else:
        print("{}：未知選項 {}".format(_CMD, mode))
        return

    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if not result.ok and result.status == "blocked":
        rs.MessageBox(result.message)


if __name__ == "__main__":
    main()
