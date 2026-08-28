# -*- coding: utf-8 -*-
"""pending →（可選 validate）→ atomic replace；失敗不碰既有 last-good。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Optional, Union

from foundation.paths import pending_path_for
from foundation.result import Result

PathLike = Union[str, os.PathLike]
ValidateFn = Callable[[Path], Optional[str]]


def _same_volume(final: Path, pending: Path) -> bool:
    """pending 應與 final 同目錄；此檢查防跨碟誤用。"""
    if os.name == "nt":
        return final.resolve().drive.lower() == pending.resolve().drive.lower()
    try:
        return os.stat(final.parent).st_dev == os.stat(pending.parent).st_dev
    except OSError:
        return True


def atomic_publish_bytes(
    final_path: PathLike,
    data: bytes,
    *,
    validate: Optional[ValidateFn] = None,
) -> Result:
    """
    寫入 pending，可選驗證，再以 os.replace 換成 final。

    - 不先刪除既有 final（失敗時 last-good 仍在）。
    - pending 與 final 須同磁碟區，否則 replace 可能非原子。
    """
    final = Path(final_path)
    pending = pending_path_for(final)
    stage = "atomic_publish"

    try:
        final.parent.mkdir(parents=True, exist_ok=True)
        if final.exists() and not _same_volume(final, pending):
            return Result.fail("pending 與目標不在同一磁碟區，拒絕發布", stage=stage)

        with open(pending, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        if validate is not None:
            err = validate(pending)
            if err:
                try:
                    pending.unlink()
                except OSError:
                    pass
                return Result.fail(err, stage="validate")

        os.replace(str(pending), str(final))
        return Result.success("已發布：{}".format(final), stage=stage, data=str(final))
    except Exception as exc:
        try:
            if pending.exists():
                pending.unlink()
        except OSError:
            pass
        return Result.fail("發布失敗：{}".format(exc), stage=stage)


def atomic_publish_text(
    final_path: PathLike,
    text: str,
    *,
    encoding: str = "utf-8",
    validate: Optional[ValidateFn] = None,
) -> Result:
    return atomic_publish_bytes(
        final_path,
        text.encode(encoding),
        validate=validate,
    )


def atomic_publish_json(
    final_path: PathLike,
    payload: Any,
    *,
    encoding: str = "utf-8",
    indent: int = 2,
    validate: Optional[ValidateFn] = None,
) -> Result:
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    if not text.endswith("\n"):
        text += "\n"
    return atomic_publish_text(final_path, text, encoding=encoding, validate=validate)


def atomic_publish_from_pending(
    final_path: PathLike,
    *,
    pending_path: Optional[PathLike] = None,
    validate: Optional[ValidateFn] = None,
) -> Result:
    """
    已寫好的 pending 檔 → 可選驗證 → os.replace 成 final。

    給大型二進位（如 3dm）：由呼叫端直接匯出到 pending，避免整檔讀入記憶體。
    失敗不碰既有 final；驗證失敗會刪 pending。
    """
    final = Path(final_path)
    pending = Path(pending_path) if pending_path is not None else pending_path_for(final)
    stage = "atomic_publish"

    try:
        final.parent.mkdir(parents=True, exist_ok=True)
        if not pending.is_file():
            return Result.fail("找不到 pending：{}".format(pending), stage=stage)
        if final.exists() and not _same_volume(final, pending):
            return Result.fail("pending 與目標不在同一磁碟區，拒絕發布", stage=stage)

        if validate is not None:
            err = validate(pending)
            if err:
                try:
                    pending.unlink()
                except OSError:
                    pass
                return Result.fail(err, stage="validate")

        os.replace(str(pending), str(final))
        return Result.success("已發布：{}".format(final), stage=stage, data=str(final))
    except Exception as exc:
        try:
            if pending.exists():
                pending.unlink()
        except OSError:
            pass
        return Result.fail("發布失敗：{}".format(exc), stage=stage)
