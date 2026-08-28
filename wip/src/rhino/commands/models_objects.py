# -*- coding: utf-8 -*-
"""Rhino 選取物件通道：只匯出目前選取 → models/R2B_Objects.3dm。"""
from __future__ import annotations

from pathlib import Path
from typing import List

from foundation.atomic import atomic_publish_from_pending
from foundation.log import append_log
from foundation.model_payload import validate_model_3dm
from foundation.paths import (
    config_root_for_document,
    ensure_config_layout,
    objects_path,
    pending_path_for,
    require_saved_document_path,
)
from foundation.result import Result
from rhino.commands.model_export import BLOCK_MODE_EXPLODE_ALL, export_ids_to_3dm
from rhino.commands.models import _ensure_visible_for_export
from rhino.platform.guard import run_guarded
from rhino.platform.live import open_session


def _selected_ids() -> List[str]:
    import rhinoscriptsyntax as rs  # type: ignore

    try:
        ids = rs.SelectedObjects(include_lights=False, include_grips=False) or []
    except TypeError:
        ids = rs.SelectedObjects() or []
    except Exception:
        return []
    return [str(oid) for oid in ids]


def publish_objects_once() -> Result:
    """發布選取物件；Block 各自展開成獨立幾何。沒選取＝擋住。"""
    session = open_session()
    saved = require_saved_document_path(session.document_path())
    if not saved.ok:
        return saved

    root = ensure_config_layout(config_root_for_document(saved.data))
    final = objects_path(root)
    pending = pending_path_for(final)

    def _action() -> Result:
        ids = _selected_ids()
        if not ids:
            return Result.blocked("請先選取要匯出的物件", stage="objects_select")

        _ensure_visible_for_export(session, ids)
        exported = export_ids_to_3dm(
            ids,
            pending,
            exclude_token="",
            block_mode=BLOCK_MODE_EXPLODE_ALL,
        )
        if not exported.ok:
            try:
                if pending.exists():
                    pending.unlink()
            except OSError:
                pass
            return exported

        published = atomic_publish_from_pending(
            final, pending_path=pending, validate=validate_model_3dm
        )
        append_log(
            root,
            "Objects publish: {} ({}); count={}".format(
                published.status, published.message, len(ids)
            ),
        )
        if published.ok:
            return Result.success(
                "已發布 {} 個選取物件 → {}".format(len(ids), final),
                stage="publish_objects",
                data=str(final),
            )
        return published

    return run_guarded(session, _action)
