# -*- coding: utf-8 -*-
"""
LoopFlow R2B 內嵌 import_3dm fork（上游 0.0.18）。

- 上游唯讀參考：repo `import_3dm/import_3dm-0.0.18-windows_x64/`
- 本目錄為工作複本；以 Sync add-on 子套件載入，不需另啟用「Import Rhinoceros 3D」
- rhino3dm：見 `_bootstrap_rhino3dm.py`（解壓本目錄 wheels/）

注意：此檔不 import read3dm（會拉 bpy）；呼叫端再 from .import_3dm.read3dm import read_3dm。
"""
from __future__ import annotations

__all__ = ["default_import_options"]


def default_import_options(*, update_materials: bool) -> dict:
    """Models Update／Import 用的預設選項（對齊上游 Import3dm 常用預設）。"""
    return {
        "import_views": False,
        "import_named_views": False,
        "import_annotations": False,
        "import_curves": True,
        "import_pointset": False,
        "import_meshes": True,
        "import_subd": True,
        "import_extrusions": True,
        "import_brep": True,
        "import_hidden_objects": True,
        "import_hidden_layers": True,
        "import_layers_as_empties": False,
        "import_groups": False,
        "import_nested_groups": False,
        "import_instances": True,
        "import_instances_grid_layout": False,
        "import_instances_grid": 10,
        "link_materials_to": "PREFERENCES",
        "update_materials": bool(update_materials),
        "merge_by_distance": False,
        "merge_distance": 0.0001,
        "subD_level_viewport": 2,
        "subD_level_render": 2,
        "subD_boundary_smooth": "ALL",
    }
