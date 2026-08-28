# -*- coding: utf-8 -*-
"""文件 snapshot／restore 與 guarded 執行（R2B：任何結束皆還原 Modified）。"""
from __future__ import annotations

from typing import Callable

from foundation.result import Result
from rhino.platform.state import DocumentSnapshot


def capture_snapshot(session) -> DocumentSnapshot:
    states = []
    for oid in session.iter_object_ids(include_hidden=True, include_locked=True):
        states.append(session.get_view_state(oid))
    return DocumentSnapshot(
        objects=tuple(states),
        document_modified=bool(session.document_modified()),
    )


def restore_snapshot(
    session,
    snap: DocumentSnapshot,
    *,
    restore_document_modified: bool = True,
) -> None:
    """還原物件視圖狀態；預設同時還原 document_modified。"""
    try:
        session.set_redraw_enabled(False)
    except Exception:
        pass
    try:
        for item in snap.objects:
            try:
                session.set_view_state(item)
            except Exception:
                pass
        if restore_document_modified:
            session.set_document_modified(snap.document_modified)
    finally:
        try:
            session.set_redraw_enabled(True)
        except Exception:
            pass


def run_guarded(session, action: Callable[[], Result]) -> Result:
    """
    執行 action 前後做 snapshot／restore。

    R2B 契約：成功／取消／失敗／例外 **皆**還原來源視圖與 Modified
    （與 LoopFlow 出圖「成功可留 dirty」不同）。
    """
    snap = capture_snapshot(session)
    try:
        result = action()
        if result is None:
            result = Result.fail("action 未回傳 Result", stage="run_guarded")
        elif not isinstance(result, Result):
            result = Result.fail("action 回傳型別錯誤", stage="run_guarded")
    except Exception as exc:
        restore_snapshot(session, snap, restore_document_modified=True)
        return Result.fail("執行例外：{}".format(exc), stage="run_guarded")

    restore_snapshot(session, snap, restore_document_modified=True)
    return result
