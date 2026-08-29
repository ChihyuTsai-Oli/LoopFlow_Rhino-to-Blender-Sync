# -*- coding: utf-8 -*-
"""Objects 時戳檔名：每次新檔、不覆蓋。"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, Union

PathLike = Union[str, Path]
ExistsFn = Callable[[Path], bool]
NowFn = Callable[[], datetime]

_STAMP = "%y%m%d_%H%M%S"


def stamped_objects_name(prefix: str, suffix: str, when: datetime) -> str:
    """例：R2B_Objects_260829_200105.3dm"""
    return "{}_{}{}".format(prefix, when.strftime(_STAMP), suffix)


def _pending_for(path: Path) -> Path:
    return path.with_name("{}_pending{}".format(path.stem, path.suffix))


def unique_stamped_path(
    models_dir: PathLike,
    prefix: str,
    suffix: str,
    *,
    now_fn: Optional[NowFn] = None,
    exists_fn: Optional[ExistsFn] = None,
) -> Path:
    """在 models/ 配一個尚未存在的時戳路徑（含 pending）。同秒則加一秒。"""
    folder = Path(models_dir)
    folder.mkdir(parents=True, exist_ok=True)
    now = now_fn() if now_fn is not None else datetime.now()
    exists = exists_fn or (lambda p: Path(p).exists())
    for i in range(120):
        candidate = folder / stamped_objects_name(
            prefix, suffix, now + timedelta(seconds=i)
        )
        if not exists(candidate) and not exists(_pending_for(candidate)):
            return candidate
    raise RuntimeError("Could not allocate a unique Objects filename")


def latest_stamped_path(
    models_dir: PathLike,
    prefix: str,
    suffix: str,
) -> Optional[Path]:
    """最新時戳檔；沒有時回退舊的固定名 `prefix+suffix`。"""
    folder = Path(models_dir)
    if not folder.is_dir():
        return None
    found = []
    needle = prefix + "_"
    for path in folder.iterdir():
        if not path.is_file():
            continue
        if "_pending" in path.stem:
            continue
        if path.name.startswith(needle) and path.name.endswith(suffix):
            found.append(path)
    if found:
        return max(found, key=lambda p: p.name)
    legacy = folder / (prefix + suffix)
    if legacy.is_file():
        return legacy
    return None
