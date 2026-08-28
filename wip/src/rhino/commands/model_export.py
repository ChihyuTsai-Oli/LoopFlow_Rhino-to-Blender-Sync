# -*- coding: utf-8 -*-
"""Models 匯出：圖層階層／同名同色材質／視圖寫入 File3dm（不開作業檔清理）。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from foundation.result import Result
from foundation.block_payload import USERSTRING_DEF_ID, build_blocks_payload
from rhino.platform.collect import layer_path_is_excluded

BLOCK_MODE_EXPLODE_ALL = "explode_all"
BLOCK_MODE_PROTOTYPE = "prototype"


def material_name_from_full_path(full_path: str) -> str:
    """
    材質名＝父圖層::最末端圖層；頂層則僅末端名。

    例：`A::B::C` → `B::C`；`Solo` → `Solo`。
    """
    parts = [p for p in str(full_path or "").split("::") if p]
    if len(parts) >= 2:
        return "{}::{}".format(parts[-2], parts[-1])
    if parts:
        return parts[-1]
    return "Layer"


def _layer_name(layer) -> str:
    try:
        name = str(getattr(layer, "Name", "") or "")
    except Exception:
        name = ""
    return name or "Layer"


def _layer_full_path(layer) -> str:
    try:
        full = str(getattr(layer, "FullPath", "") or "")
    except Exception:
        full = ""
    return full or _layer_name(layer)


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


def _is_instance_ref(robj, ObjectType) -> bool:
    try:
        return robj.ObjectType == ObjectType.InstanceReference
    except Exception:
        return False


def _instance_def_id(robj) -> str:
    try:
        idef = robj.InstanceDefinition
        if idef is not None:
            return str(idef.Id)
    except Exception:
        pass
    try:
        return str(robj.Geometry.ParentIdefId)
    except Exception:
        return ""


def _instance_xform(robj):
    try:
        return robj.InstanceXform
    except Exception:
        return robj.Geometry.Xform


def _xform_to_list(xf) -> List[float]:
    return [
        float(xf.M00),
        float(xf.M01),
        float(xf.M02),
        float(xf.M03),
        float(xf.M10),
        float(xf.M11),
        float(xf.M12),
        float(xf.M13),
        float(xf.M20),
        float(xf.M21),
        float(xf.M22),
        float(xf.M23),
        float(xf.M30),
        float(xf.M31),
        float(xf.M32),
        float(xf.M33),
    ]


def _layer_full_of(src, layer_index: int) -> str:
    try:
        return str(src.Layers[int(layer_index)].FullPath)
    except Exception:
        return ""


def _iter_definition_objects(idef):
    try:
        objs = idef.GetObjects()
        if objs:
            for obj in objs:
                if obj is not None:
                    yield obj
            return
    except Exception:
        pass
    try:
        count = int(idef.ObjectCount)
    except Exception:
        return
    for idx in range(count):
        try:
            obj = idef.Object(idx)
        except Exception:
            obj = None
        if obj is not None:
            yield obj


def _combine_xform(prefix, local, Transform):
    if prefix is None:
        return local
    try:
        return Transform.Multiply(prefix, local)
    except Exception:
        return prefix * local


def _explode_instance_geoms(robj, xform_prefix, ObjectType, Transform):
    """遞迴展開 Instance；產出已在世界座標的幾何複製。不改作業檔。"""
    if not _is_instance_ref(robj, ObjectType):
        geom = getattr(robj, "Geometry", None)
        if geom is None:
            return
        try:
            dup = geom.Duplicate()
        except Exception:
            return
        if xform_prefix is not None:
            try:
                dup.Transform(xform_prefix)
            except Exception:
                pass
        yield dup
        return

    local = _instance_xform(robj)
    xform = _combine_xform(xform_prefix, local, Transform)
    idef = None
    try:
        idef = robj.InstanceDefinition
    except Exception:
        idef = None
    if idef is None:
        return
    for child in _iter_definition_objects(idef):
        yield from _explode_instance_geoms(child, xform, ObjectType, Transform)


def _add_geoms(out, geoms, attr_template) -> int:
    added = 0
    for geom in geoms:
        try:
            out.Objects.Add(geom, attr_template)
            added += 1
        except Exception:
            continue
    return added


def export_ids_to_3dm(
    ids: Sequence[str],
    path: Path,
    *,
    exclude_token: str = "//",
    block_mode: str = BLOCK_MODE_PROTOTYPE,
) -> Result:
    """
    將指定物件寫入 3dm：
    - 只帶「有物件的圖層＋其祖先」；略過排除標記圖層
    - 材質名＝父::末端；顏色＝圖層色；物件 MaterialFromLayer
    - Block：prototype＝炸第一顆＋sidecar；explode_all＝每顆獨立展開
    - 複製具名視圖與目前作用視角；寫入後釋放 File3dm 把手
    """
    import gc

    import Rhino  # type: ignore
    import rhinoscriptsyntax as rs  # type: ignore
    import scriptcontext as sc  # type: ignore
    from System import Guid  # type: ignore
    from System.Drawing import Color  # type: ignore

    src = sc.doc
    if src is None:
        return Result.fail("無作用中文件", stage="export")

    # --- 先解析物件，決定真正需要的圖層（含子樹祖先）---
    resolved = []  # (robj, old_li)
    used_old_indices: Set[int] = set()
    for oid in ids:
        try:
            guid = rs.coerceguid(oid)
            robj = src.Objects.FindId(guid) if guid else None
            if robj is None or robj.Geometry is None:
                continue
            old_li = int(robj.Attributes.LayerIndex)
            resolved.append((robj, old_li))
            used_old_indices.add(old_li)
        except Exception:
            continue

    if not resolved:
        return Result.fail("沒有可寫入的幾何", stage="export")

    by_index: Dict[int, object] = {}
    by_id: Dict[object, object] = {}
    for layer in src.Layers:
        if layer is None or getattr(layer, "IsDeleted", False):
            continue
        full = _layer_full_path(layer)
        if layer_path_is_excluded(full, exclude_token):
            continue
        try:
            idx = int(layer.Index)
        except Exception:
            continue
        by_index[idx] = layer
        try:
            by_id[layer.Id] = layer
        except Exception:
            pass

    # 祖先一併納入（維持階層）
    needed_indices: Set[int] = set()
    stack = list(used_old_indices)
    while stack:
        idx = stack.pop()
        if idx in needed_indices:
            continue
        layer = by_index.get(idx)
        if layer is None:
            continue
        needed_indices.add(idx)
        try:
            parent_id = layer.ParentLayerId
            if parent_id is None or parent_id == Guid.Empty:
                continue
            parent = by_id.get(parent_id)
            if parent is None:
                continue
            stack.append(int(parent.Index))
        except Exception:
            continue

    if not needed_indices:
        return Result.fail("物件圖層皆不可匯出（可能在排除標記下）", stage="export_layers")

    kept = sorted(
        (by_index[i] for i in needed_indices if i in by_index),
        key=lambda ly: (_layer_full_path(ly).count("::"), _layer_full_path(ly)),
    )
    src_layers_by_index = {int(ly.Index): ly for ly in kept}

    out = Rhino.FileIO.File3dm()
    try:
        try:
            out.Settings.ModelUnitSystem = src.ModelUnitSystem
            out.Settings.ModelAbsoluteTolerance = src.ModelAbsoluteTolerance
            out.Settings.ModelAngleToleranceRadians = src.ModelAngleToleranceRadians
            out.Settings.ModelAngleToleranceDegrees = src.ModelAngleToleranceDegrees
        except Exception:
            pass

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
        skip_layer = 0
        skip_add = 0
        last_add_err = ""
        ObjectType = Rhino.DocObjects.ObjectType
        Transform = Rhino.Geometry.Transform
        block_defs: List[dict] = []
        instance_groups: Dict[str, List] = {}
        instance_order: List[str] = []

        def _append_plain(robj, old_li, user_strings=None) -> None:
            nonlocal added, skip_layer, skip_add, last_add_err
            if old_li not in old_index_to_new:
                skip_layer += 1
                return
            try:
                new_li = old_index_to_new[old_li]
                attr = _fresh_attributes(Rhino, robj.Attributes, new_li)
                if user_strings:
                    for key, value in user_strings:
                        try:
                            attr.SetUserString(str(key), str(value))
                        except Exception:
                            pass
                geom = robj.Geometry
                try:
                    dup = geom.Duplicate()
                except Exception:
                    dup = geom
                out.Objects.Add(dup, attr)
                used_new_layers.add(new_li)
                added += 1
            except Exception as exc:
                skip_add += 1
                last_add_err = str(exc)

        def _append_exploded(robj, old_li, user_strings=None) -> int:
            nonlocal added, skip_layer, skip_add, last_add_err
            if old_li not in old_index_to_new:
                skip_layer += 1
                return 0
            count = 0
            try:
                for geom in _explode_instance_geoms(
                    robj, None, ObjectType, Transform
                ):
                    piece_attr = _fresh_attributes(Rhino, robj.Attributes, new_li)
                    if user_strings:
                        for key, value in user_strings:
                            try:
                                piece_attr.SetUserString(str(key), str(value))
                            except Exception:
                                pass
                    out.Objects.Add(geom, piece_attr)
                    count += 1
            except Exception as exc:
                skip_add += 1
                last_add_err = str(exc)
                return count
            if count:
                used_new_layers.add(new_li)
                added += count
            return count

        for robj, old_li in resolved:
            if not _is_instance_ref(robj, ObjectType):
                _append_plain(robj, old_li)
                continue
            if block_mode == BLOCK_MODE_EXPLODE_ALL:
                if not _append_exploded(robj, old_li):
                    skip_add += 1
                continue
            def_id = _instance_def_id(robj) or str(id(robj))
            if def_id not in instance_groups:
                instance_groups[def_id] = []
                instance_order.append(def_id)
            instance_groups[def_id].append((robj, old_li))

        for def_id in instance_order:
            items = instance_groups[def_id]
            proto_robj, proto_li = items[0]
            tagged = [(USERSTRING_DEF_ID, def_id)]
            if not _append_exploded(proto_robj, proto_li, tagged):
                skip_add += 1
                continue
            copies = []
            for robj, old_li in items[1:]:
                try:
                    copies.append(
                        {
                            "xform": _xform_to_list(_instance_xform(robj)),
                            "layer": _layer_full_of(src, old_li),
                        }
                    )
                except Exception:
                    continue
            try:
                def_name = str(proto_robj.InstanceDefinition.Name)
            except Exception:
                def_name = ""
            block_defs.append(
                {
                    "id": def_id,
                    "name": def_name,
                    "prototype_xform": _xform_to_list(_instance_xform(proto_robj)),
                    "copies": copies,
                }
            )

        if added == 0:
            detail = "圖層未對應={} 寫入失敗={}；對應={}".format(
                skip_layer, skip_add, len(old_index_to_new)
            )
            if last_add_err:
                detail += "；末次錯誤={}".format(last_add_err)
            return Result.fail("沒有可寫入的幾何（{}）".format(detail), stage="export")

        new_to_old = {v: k for k, v in old_index_to_new.items()}

        def _add_material_index(mat_obj) -> Optional[int]:
            tables = (
                getattr(out, "AllMaterials", None),
                getattr(out, "Materials", None),
            )
            for table in tables:
                if table is None:
                    continue
                before = None
                try:
                    before = int(table.Count)
                except Exception:
                    before = None
                result = None
                try:
                    result = table.Add(mat_obj)
                except Exception:
                    continue
                if result is not None:
                    try:
                        return int(result)
                    except (TypeError, ValueError):
                        try:
                            return int(getattr(result, "Index"))
                        except Exception:
                            pass
                if before is not None:
                    try:
                        after = int(table.Count)
                        if after > before:
                            return after - 1
                    except Exception:
                        pass
                try:
                    count = int(table.Count)
                    if count > 0:
                        last = table[count - 1]
                        if last is not None and getattr(last, "Name", None) == mat_obj.Name:
                            return count - 1
                except Exception:
                    pass
            return None

        for new_li in sorted(used_new_layers):
            old_li = new_to_old.get(new_li)
            src_layer = src_layers_by_index.get(old_li) if old_li is not None else None
            layer_out = _layer_at(new_li)
            if src_layer is not None:
                name = material_name_from_full_path(_layer_full_path(src_layer))
                color = _layer_color(src_layer, Color)
            else:
                name = material_name_from_full_path(
                    _layer_full_path(layer_out) if layer_out is not None else ""
                )
                color = _layer_color(layer_out, Color) if layer_out is not None else None

            mat = Rhino.DocObjects.Material()
            try:
                mat.Name = name
            except Exception:
                pass
            if color is not None:
                try:
                    mat.DiffuseColor = color
                except Exception:
                    pass

            mat_index = _add_material_index(mat)
            if mat_index is None or layer_out is None:
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

        # 開檔用的 Views（不是 NamedViews）才會帶進相機／顯示模式
        try:
            active = src.Views.ActiveView
            if active is not None:
                vp = getattr(active, "ActiveViewport", None) or getattr(
                    active, "MainViewport", None
                )
                if vp is not None:
                    view_info = Rhino.DocObjects.ViewInfo(vp)
                    try:
                        view_info.Name = str(getattr(vp, "Name", None) or "Perspective")
                    except Exception:
                        view_info.Name = "Perspective"

                    # 盡力寫入顯示模式 Id（依 Rhino 版本 API 不同）
                    try:
                        dm = getattr(vp, "DisplayMode", None)
                        dm_id = getattr(dm, "Id", None) if dm is not None else None
                        if dm_id is not None:
                            for target in (view_info, getattr(view_info, "Viewport", None)):
                                if target is None:
                                    continue
                                for attr in ("DisplayModeId", "DisplayMode"):
                                    if hasattr(target, attr):
                                        try:
                                            setattr(
                                                target,
                                                attr,
                                                dm_id if attr.endswith("Id") else dm,
                                            )
                                        except Exception:
                                            pass
                    except Exception:
                        pass

                    def _clear_views(table):
                        if table is None:
                            return
                        try:
                            while int(table.Count) > 0:
                                try:
                                    table.Delete(0)
                                except Exception:
                                    try:
                                        table.RemoveAt(0)
                                    except Exception:
                                        break
                        except Exception:
                            pass

                    _clear_views(getattr(out, "Views", None))
                    _clear_views(getattr(out, "AllViews", None))

                    added_view = False
                    for table in (
                        getattr(out, "Views", None),
                        getattr(out, "AllViews", None),
                    ):
                        if table is None:
                            continue
                        try:
                            table.Add(view_info)
                            added_view = True
                            break
                        except Exception:
                            continue

                    # 同步放一份具名視圖，方便 RestoreNamedView
                    if added_view:
                        try:
                            named = Rhino.DocObjects.ViewInfo(vp)
                            named.Name = "R2B_Active"
                            try:
                                out.NamedViews.Add(named)
                            except Exception:
                                out.AllNamedViews.Add(named)
                        except Exception:
                            pass
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
            "已寫入 {} 個物件、{} 個圖層".format(added, len(old_index_to_new)),
            stage="export",
            data={
                "path": str(path),
                "blocks": build_blocks_payload(block_defs),
            },
        )
    finally:
        # 釋放檔案鎖定，避免後續 pending→R2B.3dm 碰上 WinError 32
        try:
            out.Dispose()
        except Exception:
            pass
        try:
            del out
        except Exception:
            pass
        gc.collect()
