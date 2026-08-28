# -*- coding: utf-8 -*-
"""R2B_Models_Objects：發布選取物件 → models/R2B_Objects.3dm。"""
from __future__ import annotations

import os
import sys

_CMD = "R2B_Models_Objects"


def _repo_src_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    src = _repo_src_root()
    if src not in sys.path:
        sys.path.insert(0, src)

    import rhinoscriptsyntax as rs  # type: ignore

    from rhino.commands.models_objects import publish_objects_once

    result = publish_objects_once()
    msg = "{} [{}] {}".format(_CMD, result.status, result.message)
    print(msg)
    if result.ok:
        rs.MessageBox("Objects export succeeded\n\n{}".format(result.message), title=_CMD)
    elif result.status in ("blocked", "fail"):
        rs.MessageBox(result.message, title=_CMD)


if __name__ == "__main__":
    main()
