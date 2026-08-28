# -*- coding: utf-8 -*-
"""R2B_Models 開發入口（空殼）。"""
from __future__ import annotations

import os
import sys

_CMD = "R2B_Models"


def _repo_src_root() -> str:
    # .../wip/src/rhino/entrypoints/this.py → wip/src
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    src = _repo_src_root()
    if src not in sys.path:
        sys.path.insert(0, src)
    from foundation.stub import stub_message

    msg = stub_message(_CMD)
    try:
        import rhinoscriptsyntax as rs

        rs.MessageBox(msg)
    except Exception:
        print(msg)


if __name__ == "__main__":
    main()
