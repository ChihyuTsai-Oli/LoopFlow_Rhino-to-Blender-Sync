# -*- coding: utf-8 -*-
"""Rhino Models 通道：選圖層 → 精準 ID → pending 匯出 → atomic；來源一律還原。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from foundation.atomic import atomic_publish_from_pending, atomic_publish_json
from foundation.block_payload import empty_blocks_payload, validate_blocks_file
from foundation.log import append_log
from foundation.model_payload import validate_model_3dm
from foundation.paths import (
    blocks_path,
    config_root_for_document,
    ensure_config_layout,
    model_path,
    pending_path_for,
    require_saved_document_path,
)
from foundation.result import Result
from rhino.commands.model_export import export_ids_to_3dm
from rhino.platform.collect import (
    DEFAULT_LAYER_EXCLUDE_TOKEN,
    collect_ids_under_layer,
    layer_path_is_excluded,
    layer_subtree_paths,
)
from rhino.platform.guard import run_guarded
from rhino.platform.live import LiveSession, open_session

_STICKY_LAST_LAYER = "R2B3_LAST_MODEL_LAYER"
_STICKY_EXCLUDE_TOKEN = "R2B3_LAYER_EXCLUDE_TOKEN"
_STICKY_LAST_TYPES = "R2B3_LAST_MODEL_TYPES"

# (顯示名, 預設勾選, 對應 kind 集合)
_TYPE_ROWS: Tuple[Tuple[str, bool, Set[str]], ...] = (
    ("Point", False, {"point"}),
    ("Curve", False, {"curve"}),
    ("Brep / Polysurface / Surface", True, {"brep", "polysurface", "surface"}),
    ("Mesh", True, {"mesh"}),
    ("SubD", True, {"subd"}),
    ("Extrusion", True, {"extrusion"}),
    ("Block / Instance", True, {"block", "instance"}),
    ("Other", True, {"other"}),
)


def _sticky():
    import scriptcontext as sc  # type: ignore

    return sc.sticky


def _prompt_exclude_token(default_token: str) -> Optional[str]:
    """自訂排除標記：圖層 FullPath 含此文字則不匯出；空白＝不排除。"""
    import rhinoscriptsyntax as rs  # type: ignore

    seed = default_token if default_token is not None else DEFAULT_LAYER_EXCLUDE_TOKEN
    value = rs.StringBox(
        message="圖層路徑含此文字者不匯出（空白＝不排除）",
        default_value=seed,
        title="R2B Models — 排除標記",
    )
    if value is None:
        return None
    return str(value)


def _prompt_layer(
    session: LiveSession,
    default_layer: Optional[str],
    exclude_token: str,
) -> Optional[str]:
    """階層圖層樹＋捲軸選取（Eto TreeGridView）；依排除標記過濾。"""
    from rhino.ui.layer_picker import pick_layer_path

    paths = [
        p
        for p in session.layer_paths()
        if not layer_path_is_excluded(str(p), exclude_token)
    ]
    return pick_layer_path(
        paths,
        default_path=default_layer,
        title="R2B Models",
        message="選擇要匯出的模型圖層，含子層",
    )


def _count_kinds_under_layer(
    session: LiveSession, root: str, exclude_token: str
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for path in layer_subtree_paths(
        session.layer_paths(), root, exclude_token=exclude_token
    ):
        for oid in session.objects_on_layer(path):
            kind = str(session.object_kind(oid) or "other").lower()
            counts[kind] = counts.get(kind, 0) + 1
    return counts


def checklist_defaults(last_labels: Optional[Sequence[str]] = None) -> List[Tuple[str, bool]]:
    """回傳 (列標籤, 是否勾選)。無紀錄時用 _TYPE_ROWS 預設。"""
    last_set = None if last_labels is None else set(last_labels)
    rows: List[Tuple[str, bool]] = []
    for label, default, _kinds in _TYPE_ROWS:
        checked = default if last_set is None else (label in last_set)
        rows.append((label, checked))
    return rows


def _prompt_type_flags(
    session: LiveSession,
    layer: str,
    exclude_token: str,
    last_labels: Optional[Sequence[str]] = None,
) -> Result:
    """CheckListBox：勾選框 [數量] 類別名。"""
    import rhinoscriptsyntax as rs  # type: ignore

    counts = _count_kinds_under_layer(session, layer, exclude_token)
    checklist: List[Tuple[str, bool]] = []
    row_kinds: List[Set[str]] = []
    labels: List[str] = []
    for label, checked in checklist_defaults(last_labels):
        kinds = next(k for lab, _d, k in _TYPE_ROWS if lab == label)
        n = sum(counts.get(k, 0) for k in kinds)
        checklist.append(("[{}] {}".format(n, label), checked))
        row_kinds.append(kinds)
        labels.append(label)

    chosen = rs.CheckListBox(
        checklist,
        message="勾選要匯出的幾何類別",
        title="R2B Models",
    )
    if chosen is None:
        return Result.blocked("已取消幾何類別選擇", stage="models_types")

    include: Set[str] = set()
    selected_labels: List[str] = []
    for (label, (_shown, checked), kinds) in zip(labels, chosen, row_kinds):
        if checked:
            include.update(kinds)
            selected_labels.append(label)
    if not include:
        return Result.blocked("未勾選任何幾何類別", stage="models_types")

    all_kinds: Set[str] = set()
    for kinds in row_kinds:
        all_kinds.update(kinds)
    exclude = all_kinds - include
    return Result.success(
        stage="models_types",
        data={"include": include, "exclude": exclude, "labels": selected_labels},
    )


def _ensure_visible_for_export(session: LiveSession, ids: Sequence[str]) -> None:
    """匯出前暫時顯示／解鎖目標物件。"""
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


def publish_models_once(
    *,
    layer: Optional[str] = None,
    include_kinds: Optional[Set[str]] = None,
    exclude_kinds: Optional[Set[str]] = None,
    exclude_token: Optional[str] = None,
    interactive: bool = True,
) -> Result:
    """
    發布 models/R2B.3dm。

    interactive=True：排除標記 → 階層圖層樹 → CheckListBox 選類別。
    FullPath 含排除標記的圖層不匯出（預設 `//`）。
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
        token = exclude_token
        if interactive and token is None:
            token = _prompt_exclude_token(
                sticky.get(_STICKY_EXCLUDE_TOKEN, DEFAULT_LAYER_EXCLUDE_TOKEN)
            )
            if token is None:
                return Result.blocked("已取消排除標記設定", stage="models_exclude")
        if token is None:
            token = DEFAULT_LAYER_EXCLUDE_TOKEN

        target_layer = layer
        if interactive and not target_layer:
            target_layer = _prompt_layer(
                session, sticky.get(_STICKY_LAST_LAYER), token
            )
            if not target_layer:
                return Result.blocked("已取消圖層選擇", stage="models_layer")

        if not target_layer:
            return Result.blocked("未指定模型圖層", stage="models_layer")

        kinds_include = include_kinds
        kinds_exclude = exclude_kinds
        kinds_labels: Optional[List[str]] = None
        if interactive and include_kinds is None and exclude_kinds is None:
            last_labels = sticky.get(_STICKY_LAST_TYPES)
            flags = _prompt_type_flags(
                session, target_layer, token, last_labels=last_labels
            )
            if not flags.ok:
                return flags
            kinds_include = flags.data["include"]
            kinds_exclude = flags.data["exclude"]
            kinds_labels = list(flags.data.get("labels") or [])

        ids = collect_ids_under_layer(
            session,
            target_layer,
            include_kinds=kinds_include,
            exclude_kinds=kinds_exclude,
            exclude_token=token,
        )
        if not ids:
            return Result.blocked(
                "圖層「{}」無符合物件可匯出".format(target_layer),
                stage="models_collect",
            )

        _ensure_visible_for_export(session, ids)
        # File3dm 路徑不依賴選取；仍選取方便使用者看到範圍
        session.select_objects(ids)

        exported = export_ids_to_3dm(ids, pending, exclude_token=token)
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
        blocks_payload = empty_blocks_payload()
        if isinstance(exported.data, dict) and exported.data.get("blocks"):
            blocks_payload = exported.data["blocks"]
        sidecar = atomic_publish_json(
            blocks_path(root), blocks_payload, validate=validate_blocks_file
        )
        append_log(
            root,
            "Models publish: {} ({}); layer={}; exclude={!r}; count={}; blocks={}".format(
                published.status,
                published.message,
                target_layer,
                token,
                len(ids),
                sidecar.status,
            ),
        )
        if published.ok:
            sticky[_STICKY_LAST_LAYER] = target_layer
            sticky[_STICKY_EXCLUDE_TOKEN] = token
            if kinds_labels is not None:
                sticky[_STICKY_LAST_TYPES] = kinds_labels
            return Result.success(
                "已發布 {} 個物件 → {}".format(len(ids), final),
                stage="publish_models",
                data=str(final),
            )
        return published

    return run_guarded(session, _action)
