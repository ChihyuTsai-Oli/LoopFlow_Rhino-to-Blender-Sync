# -*- coding: utf-8 -*-
"""Rhino Models 通道：選圖層 → 精準 ID → pending 匯出 → atomic；來源一律還原。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

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
from rhino.platform.collect import collect_ids_under_layer, layer_subtree_paths
from rhino.platform.guard import run_guarded
from rhino.platform.live import LiveSession, open_session

_STICKY_LAST_LAYER = "R2B3_LAST_MODEL_LAYER"

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


def _prompt_layer(session: LiveSession, default_layer: Optional[str]) -> Optional[str]:
    """階層圖層樹＋捲軸選取（Eto TreeGridView）。"""
    from rhino.ui.layer_picker import pick_layer_path

    return pick_layer_path(
        session.layer_paths(),
        default_path=default_layer,
        title="R2B Models",
        message="選擇要匯出的模型圖層，含子層",
    )


def _count_kinds_under_layer(session: LiveSession, root: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for path in layer_subtree_paths(session.layer_paths(), root):
        for oid in session.objects_on_layer(path):
            kind = str(session.object_kind(oid) or "other").lower()
            counts[kind] = counts.get(kind, 0) + 1
    return counts


def _prompt_type_flags(session: LiveSession, layer: str) -> Result:
    """CheckListBox：勾選框 [數量] 類別名。"""
    import rhinoscriptsyntax as rs  # type: ignore

    counts = _count_kinds_under_layer(session, layer)
    checklist: List[Tuple[str, bool]] = []
    row_kinds: List[Set[str]] = []
    for label, default, kinds in _TYPE_ROWS:
        n = sum(counts.get(k, 0) for k in kinds)
        checklist.append(("[{}] {}".format(n, label), default))
        row_kinds.append(kinds)

    chosen = rs.CheckListBox(
        checklist,
        message="勾選要匯出的幾何類別",
        title="R2B Models",
    )
    if chosen is None:
        return Result.blocked("已取消幾何類別選擇", stage="models_types")

    include: Set[str] = set()
    for (_label, checked), kinds in zip(chosen, row_kinds):
        if checked:
            include.update(kinds)
    if not include:
        return Result.blocked("未勾選任何幾何類別", stage="models_types")

    all_kinds: Set[str] = set()
    for kinds in row_kinds:
        all_kinds.update(kinds)
    exclude = all_kinds - include
    return Result.success(
        stage="models_types",
        data={"include": include, "exclude": exclude},
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


def _export_ids_to_3dm(ids: Sequence[str], path: Path) -> Result:
    """
    以 File3dm 寫入選取物件，不呼叫 Export／WriteFile。

    避免：ExportWithOrigin 腳本失敗、WriteFile 改寫作用中文件名。
    """
    import Rhino  # type: ignore
    import rhinoscriptsyntax as rs  # type: ignore
    import scriptcontext as sc  # type: ignore

    src = sc.doc
    if src is None:
        return Result.fail("無作用中文件", stage="export")

    out = Rhino.FileIO.File3dm()
    try:
        out.Settings.ModelUnitSystem = src.ModelUnitSystem
        out.Settings.ModelAbsoluteTolerance = src.ModelAbsoluteTolerance
        out.Settings.ModelAngleToleranceRadians = src.ModelAngleToleranceRadians
    except Exception:
        pass

    # 盡力複製圖層，讓 LayerIndex／材質名仍可對上
    try:
        for layer in src.Layers:
            if layer is None or getattr(layer, "IsDeleted", False):
                continue
            try:
                out.AllLayers.Add(layer.Duplicate())
            except Exception:
                try:
                    out.Layers.Add(layer.Duplicate())
                except Exception:
                    pass
    except Exception:
        pass

    added = 0
    for oid in ids:
        try:
            guid = rs.coerceguid(oid)
            robj = src.Objects.FindId(guid) if guid else None
            if robj is None:
                continue
            geom = robj.Geometry
            if geom is None:
                continue
            attr = robj.Attributes.Duplicate()
            out.Objects.Add(geom.Duplicate(), attr)
            added += 1
        except Exception:
            continue

    if added == 0:
        return Result.fail("沒有可寫入的幾何", stage="export")

    path = Path(path)
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            return Result.fail("無法清除舊 pending：{}".format(exc), stage="export")
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        write_opts = Rhino.FileIO.File3dmWriteOptions()
        ok = out.Write(str(path.resolve()), write_opts)
    except Exception as exc:
        return Result.fail("寫入 3dm 失敗：{}".format(exc), stage="export")
    if not ok:
        return Result.fail("File3dm.Write 回傳失敗", stage="export")
    if not path.is_file() or path.stat().st_size <= 0:
        return Result.fail("匯出後找不到有效 pending 檔", stage="export")
    return Result.success(
        "已寫入 {} 個物件".format(added),
        stage="export",
        data=str(path),
    )


def publish_models_once(
    *,
    layer: Optional[str] = None,
    include_kinds: Optional[Set[str]] = None,
    exclude_kinds: Optional[Set[str]] = None,
    interactive: bool = True,
) -> Result:
    """
    發布 models/model.3dm。

    interactive=True：ComboListBox 選圖層 + CheckListBox 選類別。
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
            target_layer = _prompt_layer(session, sticky.get(_STICKY_LAST_LAYER))
            if not target_layer:
                return Result.blocked("已取消圖層選擇", stage="models_layer")

        if not target_layer:
            return Result.blocked("未指定模型圖層", stage="models_layer")

        kinds_include = include_kinds
        kinds_exclude = exclude_kinds
        if interactive and include_kinds is None and exclude_kinds is None:
            flags = _prompt_type_flags(session, target_layer)
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
        # File3dm 路徑不依賴選取；仍選取方便使用者看到範圍
        session.select_objects(ids)

        exported = _export_ids_to_3dm(ids, pending)
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
