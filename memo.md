# LoopFlow Rhino-to-Blender-Sync — 開發備忘

---

## 安裝目錄結構

**Rhino 端**（安裝至此路徑）：

```
%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\
│
├── Data\                         ← 所有使用者可見檔案
│   ├── R2B_Path.txt              ← 主設定檔
│   ├── R2B_Camera_Sync.json      ← Camera.py 輸出，Blender 讀取
│   └── R2B_Light_Sync.json       ← Light.py 輸出，Blender 讀取
│
└── Python\                       ← Rhino 端 Python 腳本
    ├── LiveLink_R2B_Config.py
    ├── LiveLink_R2B_Camera.py
    ├── LiveLink_R2B_Light.py
    ├── LiveLink_R2B_Models.py
    └── LiveLink_R2B_Open.py
```

> `R2B.3dm` 輸出至 Rhino 作業檔同目錄（非 Data\），執行匯出前需先儲存 Rhino 檔案。

**Blender 端**（兩個各自獨立的 addon，以 Blender 預設方式安裝）：

```
releases/
├── LoopFlow_import_3dm/    → N Panel：LoopFlow 3dm
└── LoopFlow_Toolkit/       → N Panel：LoopFlow Toolkit
```

---

## R2B_Path.txt 欄位

```
DataPath:       （安裝時動態推算，預設同 Data\ 目錄）
ModelDir:       （空白 = 使用 Rhino 作業檔同目錄；可填絕對路徑自訂 3DM 輸出目錄）
LightLayer:     R2B_LT_Points
CameraFile:     R2B_Camera_Sync.json
LightFile:      R2B_Light_Sync.json
ModelFile:      R2B.3dm
BoxMapSize:     500
LastModelLayer: （空白，記憶上次匯出的 Rhino 圖層）
```

> `ModelDir` 空白時 fallback 至 `os.path.dirname(sc.doc.Path)`。  
> 若填入絕對路徑，Blender 端的 `rhino_update_path` 須改為對應絕對路徑（不能使用 `//` 相對路徑）。

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

- **`__file__` 備案**：若 Rhino 8 CPython 的 `__file__` 不可靠，改為每支腳本頂部保留單一 `_INSTALL_DIR` 常數，需逐檔修改但仍比過去集中。
- **安裝腳本**：安裝時需在 `Data\` 建立初始 `R2B_Path.txt`，內容為上方欄位預設值。
- **模型路徑**：`R2B.3dm` 輸出至 Rhino 作業檔同目錄。Blender 端 `rhino_update_path` 使用 `"//R2B.3dm"` 相對路徑（Blender 與 Rhino 作業檔放同目錄時 Auto-Detect 可直接生效）。
- **Assign Basic Mat.**：`LoopFlow_import_3dm/__init__.py` 中已以 `#` 整體停用，如需重新啟用，搜尋 `[DISABLED]` 標記移除對應 `#` 前綴即可。
