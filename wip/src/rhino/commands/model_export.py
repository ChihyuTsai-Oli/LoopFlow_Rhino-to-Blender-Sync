# -*- coding: utf-8 -*-
"""Models 匯出：圖層階層／同名同色材質／視圖寫入 File3dm（不開作業檔清理）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from foundation.result import Result
from rhino.platform.collect import layer_path_is_excluded


def _layer_name(layer) -> str:
    try:
        name = str(getattr(layer, "Name", "") or "")
    except Exception:
        name = ""
    return name or "Layer"


def _layer_color(layer, ColorCls):
    try:
        color = getattr(layer, "Color", None)
        if color is not None:
            return color
    except Exception:
        pass
    try:
        return ColorCls.Black
    except Exception:
        return None


def _fresh_attributes(Rhino, src_attr, layer_index: int):
    """精簡 ObjectAttributes，避免來源檔材質／群組索引拖垮 File3dm.Add。"""
    attr = Rhino.DocObjects.ObjectAttributes()
    attr.LayerIndex = int(layer_index)
    attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
    try:
        attr.MaterialIndex = -1
    except Exception:
        pass
    for name in (
        "Name",
        "ObjectColor",
        "ColorSource",
        "PlotColor",
        "PlotColorSource",
        "PlotWeight",
        "PlotWeightSource",
    ):
        try:
            setattr(attr, name, getattr(src_attr, name))
        except Exception:
            pass
    try:
        attr.Mode = src_attr.Mode
    except Exception:
        pass
    return attr


def export_ids_to_3dm(
    ids: Sequence[str],
    path: Path,
    *,
    exclude_token: str = "//",
) -> Result:
    """
    將指定物件寫入 3dm：
    - 圖層名稱／顏色／階層比照作業檔（FullPath 含 exclude_token 者不寫入）
    - 清掉舊材質指派；每用到的圖層新建同名同色材質；物件 MaterialFromLayer
    - 複製具名視圖，並加入目前作用中視角
    """
    import Rhino  # type: ignore
    import rhinoscriptsyntax as rs  # type: ignore
    import scriptcontext as sc  # type: ignore
    from System import Guid  # type: ignore
    from System.Drawing import Color  # type: ignore

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
        if layer_path_is_excluded(full, exclude_token):
            continue
        kept.append(layer)
        try:
            src_layers_by_index[int(layer.Index)] = layer
        except Exception:
            continue

    if not kept:
        return Result.fail("沒有可匯出的圖層", stage="export_layers")

    def _layers_count() -> int:
        for table in (getattr(out, "AllLayers", None), getattr(out, "Layers", None)):
            if table is None:
                continue
            try:
                return int(table.Count)
            except Exception:
                pass
        return 0

    def _layer_at(idx: int):
        for table in (getattr(out, "AllLayers", None), getattr(out, "Layers", None)):
            if table is None:
                continue
            try:
                layer = table[idx]
            except Exception:
                try:
                    layer = table.FindIndex(idx)
                except Exception:
                    layer = None
            if layer is not None:
                return layer
        return None

    def _add_layer(name: str, color) -> int:
        """回傳新圖層 index；失敗回傳 -1。"""
        tables = (
            getattr(out, "AllLayers", None),
            getattr(out, "Layers", None),
        )
        for table in tables:
            if table is None:
                continue
            try:
                if color is not None and hasattr(table, "AddLayer"):
                    idx = int(table.AddLayer(name, color))
                    if idx >= 0:
                        return idx
            except Exception:
                pass
            try:
                layer_obj = Rhino.DocObjects.Layer()
                layer_obj.Name = name
                if color is not None:
                    layer_obj.Color = color
                idx = int(table.Add(layer_obj))
                if idx >= 0:
                    return idx
            except Exception:
                pass
        return -1

    old_index_to_new: Dict[int, int] = {}
    old_id_to_new_id: Dict[object, object] = {}
    kept_old_ids: Set[object] = set()
    new_index_to_old_parent: Dict[int, object] = {}

    # 用 AddLayer 建表；若 File3dm 已有 Default＠0，第一層覆寫它，其餘再 Add
    add_fail = 0
    for i, layer in enumerate(kept):
        name = _layer_name(layer)
        color = _layer_color(layer, Color)
        new_idx = -1

        if i == 0 and _layers_count() >= 1:
            dst = _layer_at(0)
            if dst is not None:
                try:
                    dst.Name = name
                except Exception:
                    pass
                if color is not None:
                    try:
                        dst.Color = color
                    except Exception:
                        pass
                for attr in ("PlotColor", "PlotWeight", "IsVisible", "IsLocked"):
                    try:
                        setattr(dst, attr, getattr(layer, attr))
                    except Exception:
                        pass
                try:
                    dst.RenderMaterialIndex = -1
                except Exception:
                    pass
                new_idx = 0

        if new_idx < 0:
            new_idx = _add_layer(name, color)

        if new_idx < 0:
            add_fail += 1
            continue

        try:
            old_index_to_new[int(layer.Index)] = int(new_idx)
        except Exception:
            add_fail += 1
            continue

        try:
            old_id = layer.Id
        except Exception:
            old_id = None
        written = _layer_at(new_idx)
        if old_id is not None and written is not None:
            try:
                old_id_to_new_id[old_id] = written.Id
            except Exception:
                pass
            kept_old_ids.add(old_id)

        try:
            parent_id = layer.ParentLayerId
            if parent_id is not None and parent_id != Guid.Empty:
                new_index_to_old_parent[int(new_idx)] = parent_id
        except Exception:
            pass

    if not old_index_to_new:
        return Result.fail(
            "無法建立匯出圖層表（Add 失敗 {}）".format(add_fail),
            stage="export_layers",
        )

    # 重寫 ParentLayerId
    try:
        empty = Guid.Empty
        for new_idx, parent_id in list(new_index_to_old_parent.items()):
            layer_out = _layer_at(new_idx)
            if layer_out is None:
                continue
            if parent_id in old_id_to_new_id:
                try:
                    layer_out.ParentLayerId = old_id_to_new_id[parent_id]
                except Exception:
                    pass
            elif parent_id not in kept_old_ids:
                try:
                    layer_out.ParentLayerId = empty
                except Exception:
                    pass
    except Exception:
        pass

    used_new_layers: Set[int] = set()
    added = 0
    skip_no_obj = 0
    skip_layer = 0
    skip_geom = 0
    skip_add = 0
    last_add_err = ""

    for oid in ids:
        try:
            guid = rs.coerceguid(oid)
            robj = src.Objects.FindId(guid) if guid else None
            if robj is None:
                skip_no_obj += 1
                continue
            old_li = int(robj.Attributes.LayerIndex)
            if old_li not in old_index_to_new:
                skip_layer += 1
                continue
            geom = robj.Geometry
            if geom is None:
                skip_geom += 1
                continue
            new_li = old_index_to_new[old_li]
            attr = _fresh_attributes(Rhino, robj.Attributes, new_li)
            try:
                dup = geom.Duplicate()
            except Exception:
                dup = geom
            try:
                out.Objects.Add(dup, attr)
                used_new_layers.add(new_li)
                added += 1
            except Exception as exc:
                skip_add += 1
                last_add_err = str(exc)
                continue
        except Exception as exc:
            skip_add += 1
            last_add_err = str(exc)
            continue

    if added == 0:
        detail = (
            "收集 {}；略過找不到={} 圖層未對應={} 無幾何={} 寫入失敗={}；"
            "圖層表保留={} 對應={} Add層失敗={}"
        ).format(
            len(ids),
            skip_no_obj,
            skip_layer,
            skip_geom,
            skip_add,
            len(kept),
            len(old_index_to_new),
            add_fail,
        )
        if last_add_err:
            detail += "；末次錯誤={}".format(last_add_err)
        return Result.fail("沒有可寫入的幾何（{}）".format(detail), stage="export")

    new_to_old = {v: k for k, v in old_index_to_new.items()}
    for new_li in sorted(used_new_layers):
        old_li = new_to_old.get(new_li)
        src_layer = src_layers_by_index.get(old_li) if old_li is not None else None
        layer_out = _layer_at(new_li)
        name = _layer_name(src_layer) if src_layer is not None else (
            _layer_name(layer_out) if layer_out is not None else "Layer"
        )
        color = None
        if src_layer is not None:
            color = _layer_color(src_layer, Color)
        elif layer_out is not None:
            color = _layer_color(layer_out, Color)

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
        if mat_index < 0 or layer_out is None:
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
            if named is None:
                continue
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
        if active is not None and getattr(active, "MainViewport", None) is not None:
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
