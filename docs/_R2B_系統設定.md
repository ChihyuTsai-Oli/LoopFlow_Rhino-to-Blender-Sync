# LoopFlow R2B — 系統設定

本文件是 R2B 維護設定與現況架構的權威來源。3.0 遷移方式另見 `_R2B_重構計畫.md`。

## Repo 與版本

| 項目 | 設定 |
|---|---|
| 穩定分支 | `main`（2.x） |
| 歷史維護分支 | `1.x` |
| 3.0 整合分支 | `v3-development` |
| 短期工作分支 | `codex/v3-<scope>` |
| 穩定 tag | `v2.0.0` |
| 目標版本 | `v3.0.0` |
| Rhino runtime | Rhino 8 / CPython 3.9 |
| Blender runtime | v2.0.0 資產為 Blender 5.1.x / Python 3.13 |

## 3.0 開發模式

- `main`、`v2.0.0` 與既有 `releases/` 作為舊版／fork 基準，不在重構過程逐支改造成半新半舊系統。
- 3.0 在新的 `src/`、隔離 Rhino 安裝與 Blender profile／package ID 中乾淨建立，正式發布時一次切換。
- 建立 feature 前先完成 `_R2B_命名與資料契約.md` 的 command、schema、operator／property／collection 與 fork 邊界。
- 新核心只使用 3.0 contract；v2 設定或 scene 升級由獨立 migration 工具負責。
- 每個階段仍做自動／fixture 測試；完整 Rhino→Blender 實機測試於主鏈接通後執行。

## 目前 Repo 結構

```text
releases/
  LoopFlow_Rhino-to-Blender-Sync/
    Python/                 # Rhino producer，共 5 支 Python
    LoopFlow_R2B.rhc
    LoopFlow_import_3dm.zip
    LoopFlow_Toolkit.zip
    install_LoopFlow_R2B.bat
  LoopFlow_import_3dm/      # importer fork、rhino3dm binary、manifest
  LoopFlow_Toolkit/         # 獨立 Blender add-on
docs/
  USER_GUIDE*.md
  _R2B_*.md
  architecture/PROGRESS.md
```

目前 repo 內約 21 支 Python，包含 Rhino producer、importer fork 與 Toolkit。`releases/` 同時承擔 source 與 payload；只有在 3.0 build 管線完成後才切換 `src/` 為唯一來源。

## 重構期間的 Rhino 測試入口

重構期間直接從 repo 執行 Rhino producer 入口，不必先複製到 `%APPDATA%`。測試按鈕固定指向 `entrypoints/`，不要直接指向仍會調整的 feature 或 foundation 模組：

```text
E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\src\rhino\entrypoints\
```

按鈕巨集範例：

```text
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\src\rhino\entrypoints\R2B_Models.py"
```

目前預計入口：

```text
R2B_Models.py
R2B_Camera.py
R2B_Light.py
R2B_Open.py
```

這是開發期暫定清單，不是凍結的 3.0 command contract。功能增減、入口檔名或 repo 內路徑改變時，應同步更新本節與測試工具列；正式安裝／RC 驗證才改用隔離的 `%APPDATA%` Rhino 開發安裝位置。Blender add-on 仍使用隔離測試 profile，不經 Rhino 按鈕啟動。

## 現行安裝位置

```text
%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\
  Data\
    R2B_Path.txt
    R2B_Camera_Sync.json
    R2B_Light_Sync.json
    cursor_R2B_debug_log.txt
  Py\
    LiveLink_R2B_*.py
```

`R2B.3dm` 預設在 Rhino 工作檔目錄；Blender 端的 importer 與 Toolkit 是兩個獨立 add-on。

## `R2B_Path.txt` 設定

| 欄位 | 預設值／規則 | 用途 |
|---|---|---|
| `DataPath` | 安裝目錄下 `Data` | Camera／Light 資料根目錄 |
| `ModelDir` | 空白 | 空白時使用 Rhino 工作檔目錄 |
| `LightLayer` | `R2B_LT_Points` | Light Point 掃描 layer |
| `CameraFile` | `R2B_Camera_Sync.json` | Camera 同步檔名 |
| `LightFile` | `R2B_Light_Sync.json` | Light 同步檔名 |
| `ModelFile` | `R2B.3dm` | Models 輸出檔名 |
| `BoxMapSize` | `500` | Box mapping 尺寸 |
| `LastModelLayer` | 空白 | 上次 Models 選擇 |

現行 `LiveLink_R2B__Config.py` 會建立缺少的 config、補齊欄位並確保 `DataPath` 存在；目前多處例外會靜默忽略，需在重構中改為可追蹤 result／log。

## 內部契約，不是使用者設定

以下內容應由所屬 module 集中與測試，不直接塞進 `R2B_Path.txt`：

- `rs.ObjectsByType(1)` 等 Rhino API mask 與 command 字串。
- sticky event key、同步 schema version 與 consumer state key。
- `|||`、`TMP_R_`、`TMP_D_`、`rhino_guid` 等 importer／命名契約。
- `_Ins`、`COL_FINAL_`、`_Unique` 等 Blender collection／object 規則。
- `r2b_auto_assigned` 等未啟用功能的自訂屬性。

## 四個程式邊界

| 邊界 | 責任 | 不應包含 |
|---|---|---|
| Rhino Producer | 收集、轉換、安全發布 Models／Camera／Light | Blender UI、3DM conversion |
| Blender Integration | registration、UI、operators、timer/state、同步策略 | Rhino document 操作 |
| `import_3dm` fork | 3DM → Blender conversion | LoopFlow sync UI 與產品規則 |
| Toolkit | USD、rename、group、selection 工具 | Models／Camera／Light 必要鏈 |

## Schema 與發布規則

- Camera／Light schema 最終包含 version、producer、document／session ID 與 payload。
- Rhino producer 使用 pending 輸出；validate 成功後才 atomic replace last good。
- Blender consumer 只有 parse + apply 成功後才更新 mtime／state。
- 暫時性壞檔應 debounce／retry，不可永久略過。

## Fork、binary 與授權

- `LoopFlow_import_3dm` 基於上游 `import_3dm`，需新增 `UPSTREAM.md` 與 `PATCHES.md`。
- 第一方 integration 與 upstream converter 必須有清楚檔案邊界。
- `rhino3dm` binary 必須與實際 Blender Python ABI 相符。
- 第三方授權、upstream 註解與來源資訊不可因中文化而刪除或改寫。

## Manifest 與 Release

- `bl_info`、manifest、CHANGELOG、ZIP、Blender version 與 wheel／ABI 必須由同一 version/build 驗證。
- 現行 manifest 含模板／過期資訊與未提供的平台宣告，需在獨立批次清理。
- 先決定 Extension 或傳統 add-on 發行方式，只宣告實際提供的平台與 binary。
- RHC 內 R2O／Octane 殘留另批清理並做 Rhino 實機驗證。
- 3.0 build 最終輸出 Rhino payload、importer add-on、Toolkit add-on、清單、ZIP 與 SHA-256。

## 文件與程式註解規則

- 維護 SSOT：本文件、`_R2B_使用說明.md`、`_R2B_重構計畫.md`、`architecture/PROGRESS.md`。
- 命名與跨軟體 schema SSOT：`_R2B_命名與資料契約.md`。
- 內部文件與新增／修改的第一方註解使用繁體中文。
- 完整流程、schema、責任、副作用與回復方式寫入 docs；程式只保留必要原因、API 限制與 invariant。
- 現有第一方 Python 與 fork 有大量英文註解。按 feature／patch 逐批遷移，不為翻譯產生跨整個 fork 的巨大 diff。
- 第三方 fork 的原始註解與授權文字保留原文，只有 LoopFlow patch 的維護說明使用中文。
- 公開英文 README／Guide 是發布翻譯，不是 AI 重構指令。

## 基準檢查

目前沒有 CI／pytest 設定。每批至少執行：

- Python 靜態語法解析。
- RHC XML 解析。
- ZIP／manifest／binary 檔案清單檢查（涉及 build 時）。
- Rhino producer 與 Blender add-on 的對應 golden workflow。
- importer fixtures 與 ABI 實機驗證。
- `git diff --check`、授權、秘密、binary 與非預期產物檢查。

未在 Rhino／Blender 執行的項目不得寫成通過。
