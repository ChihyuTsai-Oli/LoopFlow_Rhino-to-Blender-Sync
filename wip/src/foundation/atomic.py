# -*- coding: utf-8 -*-
"""pending →（可選 validate）→ atomic replace；失敗不碰既有 last-good。"""
from __future__ import annotations

import json
import os
import shutil
import time
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


def _is_sharing_violation(exc: BaseException) -> bool:
    if isinstance(exc, OSError):
        # WinError 32 = sharing violation；Errno 11/16 等同鎖定語意
        if getattr(exc, "winerror", None) == 32:
            return True
        if getattr(exc, "errno", None) in (11, 16, 13):
            return True
    text = str(exc).lower()
    return "being used by another process" in text or "winerror 32" in text


def replace_pending_with_retry(
    pending: Path,
    final: Path,
    *,
    retries: int = 10,
    delay_sec: float = 0.2,
) -> Optional[BaseException]:
    """
    pending → final。先 os.replace，遇檔案鎖定則重試；再退回 copy2。

    成功回傳 None；失敗回傳最後例外（**不刪** pending，方便診斷／重試）。
    """
    last_exc: Optional[BaseException] = None
    for attempt in range(max(1, retries)):
        try:
            os.replace(str(pending), str(final))
            return None
        except OSError as exc:
            last_exc = exc
            if not _is_sharing_violation(exc) and attempt == 0:
                # 非鎖定類錯誤仍多試一次，然後走 copy 備援
                pass
            time.sleep(delay_sec * (attempt + 1))

    try:
        shutil.copy2(str(pending), str(final))
        try:
            pending.unlink()
        except OSError:
            # final 已更新；pending 殘留可下次覆寫
            pass
        return None
    except Exception as exc:
        return last_exc or exc


def atomic_publish_bytes(
    final_path: PathLike,
    data: bytes,
    *,
    validate: Optional[ValidateFn] = None,
    fsync: bool = True,
    retries: int = 10,
    delay_sec: float = 0.2,
) -> Result:
    """
    寫入 pending，可選驗證，再以 os.replace 換成 final。

    - 不先刪除既有 final（失敗時 last-good 仍在）。
    - pending 與 final 須同磁碟區，否則 replace 可能非原子。
    - 自動相機熱路徑可關 fsync、縮短鎖定重試；手動 Push／Models 維持預設。
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
            if fsync:
                os.fsync(handle.fileno())

        if validate is not None:
            err = validate(pending)
            if err:
                try:
                    pending.unlink()
                except OSError:
                    pass
                return Result.fail(err, stage="validate")

        replace_err = replace_pending_with_retry(
            pending, final, retries=retries, delay_sec=delay_sec
        )
        if replace_err is not None:
            return Result.fail(
                "發布失敗：{}（pending 仍保留：{}）".format(replace_err, pending),
                stage=stage,
            )
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
    fsync: bool = True,
    retries: int = 10,
    delay_sec: float = 0.2,
) -> Result:
    return atomic_publish_bytes(
        final_path,
        text.encode(encoding),
        validate=validate,
        fsync=fsync,
        retries=retries,
        delay_sec=delay_sec,
    )


def atomic_publish_json(
    final_path: PathLike,
    payload: Any,
    *,
    encoding: str = "utf-8",
    indent: Optional[int] = 2,
    validate: Optional[ValidateFn] = None,
    fsync: bool = True,
    retries: int = 10,
    delay_sec: float = 0.2,
) -> Result:
    if indent is None:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=indent)
    if not text.endswith("\n"):
        text += "\n"
    return atomic_publish_text(
        final_path,
        text,
        encoding=encoding,
        validate=validate,
        fsync=fsync,
        retries=retries,
        delay_sec=delay_sec,
    )


def atomic_publish_from_pending(
    final_path: PathLike,
    *,
    pending_path: Optional[PathLike] = None,
    validate: Optional[ValidateFn] = None,
) -> Result:
    """
    已寫好的 pending 檔 → 可選驗證 → replace 成 final。

    給大型二進位（如 3dm）：由呼叫端直接匯出到 pending，避免整檔讀入記憶體。
    驗證失敗刪 pending；**replace 鎖定失敗則保留 pending**。
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

        replace_err = replace_pending_with_retry(pending, final)
        if replace_err is not None:
            hint = ""
            if _is_sharing_violation(replace_err):
                hint = "；請關閉已開啟的 R2B.3dm，並稍候 Dropbox 同步後重試"
            return Result.fail(
                "發布失敗：{}（pending 仍保留：{}{}）".format(
                    replace_err, pending, hint
                ),
                stage=stage,
            )
        return Result.success("已發布：{}".format(final), stage=stage, data=str(final))
    except Exception as exc:
        return Result.fail("發布失敗：{}".format(exc), stage=stage)
