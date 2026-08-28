# -*- coding: utf-8 -*-
"""Models 匯出：圖層階層／同名同色材質／視圖寫入 File3dm（不開作業檔清理）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from foundation.result import Result
from rhino.platform.collect import layer_path_is_excluded


def _new_layer_from(src, LayerCls):
    """新建 Layer 並複製顯示／階層欄位（不複製 Id，避免 File3dm 衝突）。"""
    dst = LayerCls()
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
        # 暫存來源 Parent Id；稍後以 old_id→new_id 重寫
        dst.ParentLayerId = src.ParentLayerId
    except Exception:
        pass
    try:
        dst.RenderMaterialIndex = -1
    except Exception:
        pass
    return dst


def _fresh_attributes(Rhino, src_attr, layer_index: int):
    """精簡 ObjectAttributes，避免來源檔材質／群組索引拖垮 File3dm.Add。"""
    attr = Rhino.DocObjects.ObjectAttributes()
    attr.LayerIndex = int(layer_index)
    attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
    try:
        attr.MaterialIndex = -1
    except Exception:
        pass
    for name in ("Name", "ObjectColor", "ColorSource", "PlotColor", "PlotColorSource", "PlotWeight", "PlotWeightSource"):
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

    LayerCls = Rhino.DocObjects.Layer
    kept: List[object] = []
    src_layers_by_index: Dict[int, object] = {}
    for layer in src.Layers:
        if layer is None or getattr(layer, "IsDeleted", False):
            continue
        full = str(getattr(layer, "FullPath", "") or "")
        if layer_path_is_excluded(full, exclude_token):
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
    old_id_to_new_id: Dict[object, object] = {}
    kept_old_ids: Set[object] = set()

    # File3dm 天生有 Default＠0：覆寫成第一個保留圖層（不強行改 Id）
    first_dst = _layer_table_get(0)
    first_src = kept[0]
    try:
        first_dst.Name = first_src.Name
    except Exception:
        pass
    for attr in ("Color", "PlotColor", "PlotWeight", "LinetypeIndex", "IsVisible", "IsLocked", "IsExpanded"):
        try:
            setattr(first_dst, attr, getattr(first_src, attr))
        except Exception:
            pass
    try:
        first_dst.ParentLayerId = first_src.ParentLayerId
    except Exception:
        pass
    try:
        first_dst.RenderMaterialIndex = -1
    except Exception:
        pass
    old_index_to_new[int(first_src.Index)] = 0
    old_id_to_new_id[first_src.Id] = first_dst.Id
    kept_old_ids.add(first_src.Id)

    add_fail = 0
    for layer in kept[1:]:
        try:
            new_layer = _new_layer_from(layer, LayerCls)
            new_idx = _layer_table_add(new_layer)
            if new_idx < 0:
                add_fail += 1
                continue
            written = _layer_table_get(new_idx)
            old_index_to_new[int(layer.Index)] = int(new_idx)
            old_id_to_new_id[layer.Id] = written.Id
            kept_old_ids.add(layer.Id)
        except Exception:
            add_fail += 1
            continue

    # Parent 對應：排除層改掛 Empty；其餘改寫成新 Id
    try:
        empty = Guid.Empty
        for new_idx in list(old_index_to_new.values()):
            layer_out = _layer_table_get(new_idx)
            parent_id = getattr(layer_out, "ParentLayerId", None)
            if parent_id is None or parent_id == empty:
                continue
            if parent_id in old_id_to_new_id:
                layer_out.ParentLayerId = old_id_to_new_id[parent_id]
            elif parent_id not in kept_old_ids:
                layer_out.ParentLayerId = empty
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
