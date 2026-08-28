# Patches on import_3dm 0.0.18 (R2B Sync embed)

| 日期 | 變更 |
|---|---|
| 2026-08-28 | 以 `_bootstrap_rhino3dm.py` 自 `wheels/` 解壓載入 rhino3dm（修正傳統 addon 無 Extension wheels → `No module named rhino3dm`） |
| 2026-08-28 | 套件改為 Sync 子模組；`__init__.py` 只暴露 `read_3dm`／`default_import_options`，不再註冊獨立 File→Import UI |
| 2026-08-28 | 僅附 Windows cp311／cp313 wheels（對應 Portable Blender 5.2＝cp313） |
| 2026-08-28 | `create_or_get_top_layer`：wipe `R2B` 子樹再建（對齊 2.x）；不動 Lighting 集合；wipe 後 `reset_all_dict` |
| 2026-08-28 | `handle_materials`：Update 不覆寫已有同名材質；新建／Import 用經典 Name＋Diffuse 建 Principled（R2B.3dm 無 RDK 時不再 skip） |
| 2026-08-28 | `converters/material.py`：`from ..r2b_materials`（錯成 `.r2b_materials` 會讓整個 Sync 載入失敗、N 面板消失） |
| 2026-08-28 | `read_3dm`：不再把預設材質設成 None；`convert_object` 一律掛槽（Update 仍不覆寫節點） |
