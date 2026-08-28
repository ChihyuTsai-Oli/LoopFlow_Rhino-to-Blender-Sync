# -*- coding: utf-8 -*-
"""Models 匯出：圖層階層／同名同色材質／視圖寫入 File3dm（不開作業檔清理）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from foundation.result import Result
from rhino.platform.collect import layer_path_is_excluded


def _copy_layer_fields(dst, src) -> None:
    """把來源圖層的名稱／顏色／階層等寫到目標（不含舊材質）。"""
    try:
        dst.Name = src.Name
    except Exception:
        pass
    for attr in (
        "Color",
        "PlotColor",
        "PlotWeight",
        "LinetypeIndex",
        "IsVisible",
        "IsLocked",
        "IsExpanded",
    ):
        try:
            setattr(dst, attr, getattr(src, attr))
        except Exception:
            pass
    try:
        dst.ParentLayerId = src.ParentLayerId
    except Exception:
        pass
    try:
        dst.Id = src.Id
    except Exception:
        pass
    try:
        dst.RenderMaterialIndex = -1
    except Exception:
        pass


def export_ids_to_3dm(ids: Sequence[str], path: Path) -> Result:
    """
    將指定物件寫入 3dm：
    - 圖層名稱／顏色／階層比照作業檔（FullPath 含 // 者不寫入）
    - 清掉舊材質指派；每用到的圖層新建同名同色材質；物件 MaterialFromLayer
    - 複製具名視圖，並加入目前作用中視角
    """
    import Rhino  # type: ignore
    import rhinoscriptsyntax as rs  # type: ignore
    import scriptcontext as sc  # type: ignore
    from System import Guid  # type: ignore

    src = sc.doc
    if src is None:
        return Result.fail("無作用中文件", stage="export")

    out = Rhino.FileIO.File3dm()
    try:
        out.Settings.ModelUnitSystem = src.ModelUnitSystem
        out.Settings.ModelAbsoluteTolerance = src.ModelAbsoluteTolerance
        out.Settings.ModelAngleToleranceRadians = src.ModelAngleToleranceRadians
        out.Settings.ModelAngleToleranceDegrees = src.ModelAngleToleranceDegrees
    except Exception:
        pass

    kept: List[object] = []
    src_layers_by_index: Dict[int, object] = {}
    for layer in src.Layers:
        if layer is None or getattr(layer, "IsDeleted", False):
            continue
        full = str(getattr(layer, "FullPath", "") or "")
        if layer_path_is_excluded(full):
            continue
        kept.append(layer)
        src_layers_by_index[int(layer.Index)] = layer

    if not kept:
        return Result.fail("沒有可匯出的圖層", stage="export_layers")

    def _layer_table_get(idx: int):
        try:
            return out.AllLayers[idx]
        except Exception:
            return out.Layers[idx]

    def _layer_table_add(layer_obj) -> int:
        try:
            return int(out.AllLayers.Add(layer_obj))
        except Exception:
            return int(out.Layers.Add(layer_obj))

    old_index_to_new: Dict[int, int] = {}
    kept_old_ids: Set[object] = set()

    # File3dm 天生有 Default＠0：覆寫成第一個保留圖層，其餘再 Add
    first_dst = _layer_table_get(0)
    _copy_layer_fields(first_dst, kept[0])
    old_index_to_new[int(kept[0].Index)] = 0
    kept_old_ids.add(kept[0].Id)

    for layer in kept[1:]:
        try:
            dup = layer.Duplicate()
        except Exception:
            continue
        try:
            dup.RenderMaterialIndex = -1
        except Exception:
            pass
        new_idx = _layer_table_add(dup)
        if new_idx < 0:
            continue
        # Duplicate 通常已帶 Id／Parent；再保險覆寫一次
        try:
            _layer_table_get(new_idx).Id = layer.Id
        except Exception:
            pass
        old_index_to_new[int(layer.Index)] = int(new_idx)
        kept_old_ids.add(layer.Id)

    # Parent 被排除時改掛 Empty
    try:
        empty = Guid.Empty
        for new_idx in list(old_index_to_new.values()):
            layer_out = _layer_table_get(new_idx)
            parent_id = getattr(layer_out, "ParentLayerId", None)
            if parent_id is None:
                continue
            if parent_id != empty and parent_id not in kept_old_ids:
                layer_out.ParentLayerId = empty
    except Exception:
        pass

    used_new_layers: Set[int] = set()
    added = 0
    for oid in ids:
        try:
            guid = rs.coerceguid(oid)
            robj = src.Objects.FindId(guid) if guid else None
            if robj is None:
                continue
            old_li = int(robj.Attributes.LayerIndex)
            if old_li not in old_index_to_new:
                continue
            geom = robj.Geometry
            if geom is None:
                continue
            attr = robj.Attributes.Duplicate()
            new_li = old_index_to_new[old_li]
            attr.LayerIndex = new_li
            attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
            try:
                attr.MaterialIndex = -1
            except Exception:
                pass
            out.Objects.Add(geom.Duplicate(), attr)
            used_new_layers.add(new_li)
            added += 1
        except Exception:
            continue

    if added == 0:
        return Result.fail("沒有可寫入的幾何（可能都在 // 圖層）", stage="export")

    new_to_old = {v: k for k, v in old_index_to_new.items()}
    for new_li in sorted(used_new_layers):
        old_li = new_to_old.get(new_li)
        src_layer = src_layers_by_index.get(old_li) if old_li is not None else None
        layer_out = _layer_table_get(new_li)
        name = str(getattr(src_layer, "Name", None) or getattr(layer_out, "Name", "Layer"))
        color = getattr(src_layer, "Color", None) or getattr(layer_out, "Color", None)

        mat = Rhino.DocObjects.Material()
        mat.Name = name
        if color is not None:
            try:
                mat.DiffuseColor = color
            except Exception:
                pass
        try:
            mat_index = int(out.AllMaterials.Add(mat))
        except Exception:
            try:
                mat_index = int(out.Materials.Add(mat))
            except Exception as exc:
                return Result.fail("建立圖層材質失敗：{}".format(exc), stage="export_materials")
        if mat_index < 0:
            continue
        try:
            layer_out.RenderMaterialIndex = mat_index
        except Exception:
            try:
                layer_out.MaterialIndex = mat_index
            except Exception:
                pass

    try:
        for named in src.NamedViews:
            try:
                out.NamedViews.Add(named)
            except Exception:
                try:
                    out.AllNamedViews.Add(named)
                except Exception:
                    pass
    except Exception:
        pass

    try:
        active = src.Views.ActiveView
        if active is not None:
            view_info = Rhino.DocObjects.ViewInfo(active.MainViewport)
            view_info.Name = "R2B_Active"
            try:
                out.NamedViews.Add(view_info)
            except Exception:
                out.AllNamedViews.Add(view_info)
    except Exception:
        pass

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
        "已寫入 {} 個物件、{} 個圖層材質".format(added, len(used_new_layers)),
        stage="export",
        data=str(path),
    )
