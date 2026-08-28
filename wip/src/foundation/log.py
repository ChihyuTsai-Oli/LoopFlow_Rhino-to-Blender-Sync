# -*- coding: utf-8 -*-
"""簡易附加 log（寫在設定根 r2b.log）。"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Union
import os

from foundation.paths import ensure_config_layout, log_path
from foundation.result import Result

PathLike = Union[str, os.PathLike]


def append_log(root: PathLike, message: str, *, level: str = "INFO") -> Result:
    """附加一行 UTF-8 log；自動建立設定根版面。"""
    try:
        root_path = ensure_config_layout(root)
        path = log_path(root_path)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = "{} [{}] {}\n".format(stamp, level, message.rstrip())
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
        return Result.success(data=str(path), stage="append_log")
    except Exception as exc:
        return Result.fail("Failed to write log: {}".format(exc), stage="append_log")
