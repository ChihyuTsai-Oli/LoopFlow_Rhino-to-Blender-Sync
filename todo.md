# LoopFlow Rhino-to-Blender-Sync — 開發待辦清單

**建立日期**：2026-04-27
**說明**：審查 3 支 Rhino Python 腳本與 2 支 Blender addon 後規劃的硬編碼集中化工作，配合未來安裝檔部署路徑設計。

---

## 目標安裝目錄結構

**Rhino 端**（`releases/LoopFlow_Rhino-to-Blender-Sync` → 安裝至此路徑）：
```
%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\
│
├── Data\                         ← 所有使用者可見檔案
│   ├── R2B_Path.txt              ← 主設定檔
│   ├── R2B_Camera_Sync.json      ← Camera.py 輸出，Blender 讀取
│   └── R2B_Light_Sync.json       ← Light.py 輸出，Blender 讀取
│
└── Python\                       ← Rhino 端 Python 腳本
    ├── LiveLink_R2B_Config.py    ← 新增，集中路徑與設定讀寫
    ├── LiveLink_R2B_Camera.py
    ├── LiveLink_R2B_Light.py
    └── LiveLink_R2B_Models.py
```

**注意**：`R2B.3dm` 匯出至 Rhino 作業檔同目錄（非 Data\），執行匯出前需先儲存 Rhino 檔案。

**Blender 端**（兩個各自獨立的 addon，以 Blender 預設方式安裝）：
- `releases/LoopFlow_import_3dm/` → N Panel 改為 `LoopFlow 3dm`
- `releases/LoopFlow_Toolkit/` → 三個子工具合併為一支 addon，N Panel 改為 `LoopFlow Toolkit`

---

## R2B_Path.txt 完整欄位（目標狀態）

```
DataPath:       （安裝時動態推算，預設同 Data\ 目錄）
LightLayer:     R2B_LT_Points
CameraFile:     R2B_Camera_Sync.json
LightFile:      R2B_Light_Sync.json
ModelFile:      R2B.3dm
BoxMapSize:     500
LastModelLayer: （空白，記憶上次匯出的 Rhino 圖層）
```

---

## 待辦項目

### Python 端

- [ ] **新增 `LiveLink_R2B_Config.py`**
  - 集中管理路徑推算與設定讀寫，供三支腳本 import：
    ```python
    import os, sys

    _PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
    INSTALL_DIR = os.path.dirname(_PYTHON_DIR)
    DATA_DIR    = os.path.join(INSTALL_DIR, "Data")
    CONFIG_FILE = os.path.join(DATA_DIR, "R2B_Path.txt")

    DEFAULT_CONFIG = {
        "DataPath":       DATA_DIR,
        "LightLayer":     "R2B_LT_Points",
        "CameraFile":     "R2B_Camera_Sync.json",
        "LightFile":      "R2B_Light_Sync.json",
        "ModelFile":      "R2B.3dm",
        "BoxMapSize":     "500",
        "LastModelLayer": "",
    }
    ```
  - 提供 `load_r2b_config()` 與 `save_r2b_config(cfg)` 函式

- [ ] **`LiveLink_R2B_Camera.py`**
  - 頂部加入 sys.path.insert 並 import Config：
    ```python
    import os, sys
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _HERE)
    from LiveLink_R2B_Config import load_r2b_config, DATA_DIR
    ```
  - 輸出路徑由 `os.path.dirname(doc.Path)` 改為 `DATA_DIR`（固定路徑）
  - 輸出檔名改從 `cfg["CameraFile"]` 讀取（原硬編碼 `"R2B_Camera_Sync.json"`，line 54）
  - `event_key = "R2B_Camera_Sync_Event"` 保留為內部常數（不需使用者設定）

- [ ] **`LiveLink_R2B_Light.py`**
  - 頂部加入 sys.path.insert 並 import Config
  - 設定檔路徑改從 `CONFIG_FILE` 讀取（原 line 48 依賴 `rs.DocumentPath()` 的專案目錄）
  - 預設圖層改從 `cfg["LightLayer"]` 讀取（原硬編碼 `"R2B_LT_Points"`，line 55）
  - 輸出路徑改為 `DATA_DIR`（原 line 110 依賴專案目錄）
  - 輸出檔名改從 `cfg["LightFile"]` 讀取（原硬編碼 `"R2B_Light_Sync.json"`，line 110）

- [ ] **`LiveLink_R2B_Models.py`**
  - 頂部加入 sys.path.insert 並 import Config
  - 輸出路徑維持 `os.path.dirname(sc.doc.Path)`（需先存檔），僅檔名改從 `cfg["ModelFile"]` 讀取（原硬編碼 `"_R2B_Model.3dm"`，line 50）
  - Box Mapping 尺寸改從 `cfg["BoxMapSize"]` 讀取（原硬編碼 `500 500 500`，line 143）
  - 移除固定圖層邏輯，加入圖層選擇對話框並記憶上次選擇：
    ```python
    last_layer = cfg.get("LastModelLayer") or None
    target_layer = rs.GetLayer("選擇要匯出的模型圖層", default_layer=last_layer)
    if not target_layer:
        return
    cfg["LastModelLayer"] = target_layer
    save_r2b_config(cfg)
    ```

---

### Blender 端 — `LoopFlow_import_3dm`

只需修改 `releases/LoopFlow_import_3dm/__init__.py`：

- [ ] **N Panel 名稱**
  - `bl_category = 'Tool'`（line 617）→ `'LoopFlow 3dm'`
  - `bl_info["location"]`（line 59）→ `"N-Panel > LoopFlow 3dm"`

- [ ] **同步檔名** 浮出為模組頂部常數
  - `CAMERA_SYNC_FILE = "R2B_Camera_Sync.json"`（原 line 116 硬編碼）
  - `LIGHT_SYNC_FILE  = "R2B_Light_Sync.json"`（原 line 176 硬編碼）

- [ ] **Collection 名稱** 浮出為模組頂部常數
  - `COL_FIXTURES    = "Lighting Fixtures"`（原 line 91）
  - `COL_LIGHTING    = "Lighting"`（原 line 92）
  - `COL_LIGHT_POINTS = "R2B Lighting Points"`（原 line 191）

- [ ] **材質相關常數** 浮出為模組頂部常數
  - `MAT_PRESET_LT_K = "Preset_Lighting_K"`（原 lines 345, 349, 355, 403）
  - `LAYER_SUFFIX_LT = "5_LT"`（原 line 360）
  - `MAT_AUTO_5LT    = "Auto_5LT_Light"`（原 lines 363, 366）

- [ ] **技術參數** 浮出為模組頂部常數
  - `CAMERA_POLL_INTERVAL = 0.03`（原 lines 121, 127, 163）
  - `DEFAULT_LENS         = 50.0`（原 line 140）
  - `EMPTY_DISPLAY_SIZE   = 0.3`（原 line 224）

- [ ] **`RHINO_OT_ResetPath` 更新**（原 line 503）
  - 模型路徑維持相對路徑預設值，僅更新檔名；Sync Folder 改為指向 Data 絕對路徑：
    ```python
    data_dir = os.path.join(os.getenv("APPDATA"), "McNeel", "Rhinoceros",
                            "8.0", "scripts", "LoopFlow_R2B", "Data")
    context.scene.rhino_update_path = "//R2B.3dm"
    context.scene.rhino_json_dir    = data_dir
    ```

---

### Blender 端 — `LoopFlow_Toolkit` 合併

三支分散的 addon 合併為單一 addon，所有 Panel `bl_category` 改為 `'LoopFlow Toolkit'`：

- [ ] **建立新目錄結構**
  ```
  LoopFlow_Toolkit/
  ├── __init__.py        ← 合併 bl_info + 統一 register/unregister
  ├── export_tools.py    ← 原 Export_Tools/__init__.py 的 classes（移除 bl_info）
  ├── rename_tools.py    ← 原 Rename_Tools/__init__.py 的 classes（移除 bl_info）
  └── selection_tools.py ← 原 Selection_Tools/__init__.py 的 classes（移除 bl_info）
  ```

- [ ] **`__init__.py` 合併後 `bl_info`**
  ```python
  bl_info = {
      "name": "LoopFlow Toolkit",
      "author": "Python Partner",
      "version": (1, 0, 0),
      "blender": (4, 5, 0),
      "location": "View3D > N Panel > LoopFlow Toolkit",
      "description": "Export、Rename、Selection 整合工具包",
      "category": "Object",
  }
  ```

- [ ] **`bl_category` 更新**（三支各有 Panel）
  - `Export_Tools`：`EXPORTTOOLS_PT_panel.bl_category = 'Item'` → `'LoopFlow Toolkit'`
  - `Rename_Tools`：`LIGHTHOUSE_PT_rename_tools_panel.bl_category = 'Item'` → `'LoopFlow Toolkit'`
  - `Selection_Tools`：`LIGHTHOUSE_PT_selection_tools.bl_category = 'Item'` → `'LoopFlow Toolkit'`

---

## 不需處理的項目

| 項目 | 原因 |
|---|---|
| `rs.ObjectsByType(1)` | Rhino API 代碼 |
| Rhino 命令字串（`_-ExportWithOrigin`、`_ExplodeBlock` 等） | Rhino 命令語法 |
| `event_key = "R2B_Camera_Sync_Event"` | 內部 sticky 鍵 |
| `"|||"` 分隔符（Rename_Tools） | 內部邏輯 |
| `"TMP_R_"`、`"TMP_D_"` 等臨時前綴 | 內部過渡名稱 |
| `"r2b_auto_assigned"`、`"rhino_guid"` 等 | 內部自訂屬性鍵 |
| `"_Ins"`、`"COL_FINAL_"` | 內部命名約定 |
| `"_Unique"` 後綴（Material Isolator） | 內部命名約定 |
| `0.01` / `1.80`（Blender Scene 屬性預設值） | 已在 UI 中可調整 |
| `"//"` 相對路徑預設值（Blender Scene 屬性） | 透過 Auto-Detect 按鈕處理 |

---

## 備註

- **`__file__` 備案**：若 Rhino 8 CPython 的 `__file__` 不可靠，改為每支腳本頂部保留單一 `_INSTALL_DIR` 常數，需逐檔修改但仍比現在集中。
- **安裝腳本**：安裝時需在 `Data\` 目錄建立初始 `R2B_Path.txt`，內容為上方「R2B_Path.txt 完整欄位」預設值。
- **模型路徑**：`R2B.3dm` 輸出至 Rhino 作業檔同目錄。Blender 端 `rhino_update_path` 使用 `"//R2B.3dm"` 相對路徑（Blender 與 Rhino 作業檔放同目錄時 Auto-Detect 可直接生效）。
- **Sync Folder**：Camera / Light JSON 固定輸出至 `Data\`，點擊 Auto-Detect 後自動填入 Data 絕對路徑。
