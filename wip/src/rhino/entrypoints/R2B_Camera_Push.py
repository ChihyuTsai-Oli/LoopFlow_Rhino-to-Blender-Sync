# -*- coding: utf-8 -*-
"""R2B_Camera_Push：手動推送相機 JSON 一次。"""
from __future__ import annotations

import os
import sys

_CMD = "R2B_Camera_Push"


def _repo_src_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    src = _repo_src_root()
    if src not in sys.path:
        sys.path.insert(0, src)

    import rhinoscriptsyntax as rs  # type: ignore

    from rhino.commands.camera import publish_camera_once

    result = publish_camera_once()
    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if not result.ok and result.status == "blocked":
        rs.MessageBox(result.message)


if __name__ == "__main__":
    main()
