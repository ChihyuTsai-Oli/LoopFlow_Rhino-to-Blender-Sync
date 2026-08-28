# -*- coding: utf-8 -*-
"""Rhino Models 通道：選圖層 → 精準 ID → pending 匯出 → atomic；來源一律還原。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence, Set

from foundation.atomic import atomic_publish_from_pending
from foundation.log import append_log
from foundation.model_payload import validate_model_3dm
from foundation.paths import (
    config_root_for_document,
    ensure_config_layout,
    model_path,
    pending_path_for,
    require_saved_document_path,
)
from foundation.result import Result
from rhino.platform.collect import (
    DEFAULT_EXCLUDED_KINDS,
    DEFAULT_INCLUDED_KINDS,
    collect_ids_under_layer,
)
from rhino.platform.guard import run_guarded
from rhino.platform.live import LiveSession, open_session

_STICKY_LAST_LAYER = "R2B3_LAST_MODEL_LAYER"


def _sticky():
    import scriptcontext as sc  # type: ignore

    return sc.sticky


def _prompt_layer(default_layer: Optional[str]) -> Optional[str]:
    import rhinoscriptsyntax as rs  # type: ignore

    kwargs = {}
    if default_layer:
        kwargs["layer"] = default_layer
    chosen = rs.GetLayer("選擇要匯出的模型圖層（含子層）", **kwargs)
    if not chosen:
        return None
    return str(chosen)


def _prompt_type_flags() -> Result:
    """Point／Curve 預設不勾（ED-01）；其餘類別預設勾。用 CheckListBox 彈窗（非指令列）。"""
    import rhinoscriptsyntax as rs  # type: ignore

    # (顯示名, 預設勾選, 對應 kind 集合)
    rows = (
        ("Point", False, {"point"}),
        ("Curve", False, {"curve"}),
        ("Brep / Polysurface / Surface", True, {"brep", "polysurface", "surface"}),
        ("Mesh", True, {"mesh"}),
        ("SubD", True, {"subd"}),
        ("Extrusion", True, {"extrusion"}),
        ("Block / Instance", True, {"block", "instance"}),
        ("Other", True, {"other"}),
    )
    checklist = [(label, default) for label, default, _kinds in rows]
    chosen = rs.CheckListBox(
        checklist,
        message="勾選要匯出的幾何類別（Point／Curve 預設不勾）",
        title="R2B Models — 幾何類別",
    )
    if chosen is None:
        return Result.blocked("已取消幾何類別選擇", stage="models_types")

    include = set()
    for (label, checked), (_label, _default, kinds) in zip(chosen, rows):
        if checked:
            include.update(kinds)
    if not include:
        return Result.blocked("未勾選任何幾何類別", stage="models_types")

    # exclude = 全部可能 kind 減去 include（collect 以 include 為準）
    all_kinds = set()
    for _label, _default, kinds in rows:
        all_kinds.update(kinds)
    exclude = all_kinds - include
    return Result.success(
        stage="models_types",
        data={"include": include, "exclude": exclude},
    )


def _ensure_visible_for_export(session: LiveSession, ids: Sequence[str]) -> None:
    """匯出前暫時顯示／解鎖目標物件（契約：隱藏鎖定仍當可見匯出）。"""
    import rhinoscriptsyntax as rs  # type: ignore

    for oid in ids:
        try:
            rs.ShowObject(oid)
        except Exception:
            pass
        try:
            rs.UnlockObject(oid)
        except Exception:
            pass


def _export_selected_to(path: Path) -> Result:
    import rhinoscriptsyntax as rs  # type: ignore

    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            return Result.fail("無法清除舊 pending：{}".format(exc), stage="export")
    path.parent.mkdir(parents=True, exist_ok=True)
    quote = chr(34)
    # 僅匯出目前選取；禁止 _SelAll
    cmd = "_-ExportWithOrigin _0,0,0 {}{}{} _Enter _Enter".format(quote, path, quote)
    ok = rs.Command(cmd, False)
    if not ok:
        return Result.fail("ExportWithOrigin 指令失敗", stage="export")
    if not path.is_file() or path.stat().st_size <= 0:
        return Result.fail("匯出後找不到有效 pending 檔", stage="export")
    return Result.success(stage="export", data=str(path))


def publish_models_once(
    *,
    layer: Optional[str] = None,
    include_kinds: Optional[Set[str]] = None,
    exclude_kinds: Optional[Set[str]] = None,
    interactive: bool = True,
) -> Result:
    """
    發布 models/model.3dm。

    interactive=True：彈圖層與 Point／Curve 勾選。
    測試可傳 layer／kinds 並 interactive=False。
    """
    session = open_session()
    saved = require_saved_document_path(session.document_path())
    if not saved.ok:
        return saved

    root = ensure_config_layout(config_root_for_document(saved.data))
    final = model_path(root)
    pending = pending_path_for(final)

    def _action() -> Result:
        sticky = _sticky()
        target_layer = layer
        if interactive and not target_layer:
            target_layer = _prompt_layer(sticky.get(_STICKY_LAST_LAYER))
            if not target_layer:
                return Result.blocked("已取消圖層選擇", stage="models_layer")

        if not target_layer:
            return Result.blocked("未指定模型圖層", stage="models_layer")

        kinds_include = include_kinds
        kinds_exclude = exclude_kinds
        if interactive and include_kinds is None and exclude_kinds is None:
            flags = _prompt_type_flags()
            if not flags.ok:
                return flags
            kinds_include = flags.data["include"]
            kinds_exclude = flags.data["exclude"]

        ids = collect_ids_under_layer(
            session,
            target_layer,
            include_kinds=kinds_include,
            exclude_kinds=kinds_exclude,
        )
        if not ids:
            return Result.blocked(
                "圖層「{}」無符合物件可匯出".format(target_layer),
                stage="models_collect",
            )

        _ensure_visible_for_export(session, ids)
        session.select_objects(ids)

        exported = _export_selected_to(pending)
        if not exported.ok:
            try:
                if pending.exists():
                    pending.unlink()
            except OSError:
                pass
            return exported

        published = atomic_publish_from_pending(final, pending_path=pending, validate=validate_model_3dm)
        append_log(
            root,
            "Models publish: {} ({}); layer={}; count={}".format(
                published.status, published.message, target_layer, len(ids)
            ),
        )
        if published.ok:
            sticky[_STICKY_LAST_LAYER] = target_layer
            return Result.success(
                "已發布 {} 個物件 → {}".format(len(ids), final),
                stage="publish_models",
                data=str(final),
            )
        return published

    return run_guarded(session, _action)
