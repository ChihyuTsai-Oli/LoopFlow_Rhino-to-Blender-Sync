# -*- coding: utf-8 -*-
"""R2B_Open：Health 摘要與開啟設定資料夾。"""
from __future__ import annotations

import importlib.util
import os

_CMD = "R2B_Open"


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

    from rhino.commands.open import run_open

    result = run_open()
    print("{} [{}]".format(_CMD, result.status))
    if result.message:
        print(result.message)


if __name__ == "__main__":
    main()
