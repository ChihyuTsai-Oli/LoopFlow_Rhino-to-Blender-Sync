# -*- coding: utf-8 -*-
"""R2B_Open：Health 摘要與開啟設定資料夾。"""
from __future__ import annotations

import os
import sys

_CMD = "R2B_Open"


def _repo_src_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    src = _repo_src_root()
    if src not in sys.path:
        sys.path.insert(0, src)

    from rhino.commands.open import run_open

    result = run_open()
    print("{} [{}]".format(_CMD, result.status))
    if result.message:
        print(result.message)


if __name__ == "__main__":
    main()
