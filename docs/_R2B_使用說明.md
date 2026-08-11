# LoopFlow R2B — 使用說明

本文件記錄目前 2.x 對使用者可見的行為，是 3.0 重構期間不得無意改變的操作契約。完整逐步教學仍以 `USER_GUIDE_zh-TW.md` 為準。

3.0 採乾淨重建；本文件用於理解舊工作流與建立 fixtures，不要求開發中的半成品持續相容 v2。命名、schema 與操作若經使用者裁決可在 3.0 改變，但必須記錄於 `_R2B_命名與資料契約.md`，並在發布前完成新版使用說明。

## 產品邊界

R2B 由四個彼此不同的部分組成：

1. Rhino Producer：Models、Camera、Light、Open／Config。
2. Blender Sync Integration：接收同步資料、更新場景並管理 UI／timer／state。
3. `LoopFlow_import_3dm`：3DM → Blender converter fork。
4. LoopFlow Toolkit：獨立 Blender 工具，不是同步主鏈必要相依。

3.0 重構不得把這四個部分混成同一個模組，也不得讓 Rhino 指令承擔 Blender UI 或 converter 邏輯。

## 使用環境與版本

| 穩定版本 | Blender | Python | 說明 |
|---|---|---|---|
| `v2.0.0` | 5.1.x | 3.13 | 目前建議版本 |
| `v1.0.0` | 4.5.x | 3.11 | 歷史相容版本 |

Rhino 端使用 Rhino 8／CPython 3.9。3.0 開發版必須使用獨立 Rhino scripts/data/RHC 與 Blender 測試 profile／package ID，不覆蓋穩定 2.x。

## 安裝元件

- Rhino：`LoopFlow_Rhino-to-Blender-Sync` scripts、Data 與 `LoopFlow_R2B.rhc`。
- Blender 必要：`LoopFlow_import_3dm`。
- Blender 選用：`LoopFlow_Toolkit`。

安裝與版本選擇依 GitHub Release 及公開使用指南；不要混裝不同 Blender／Python ABI 的 `rhino3dm` binary。

## Rhino 指令

| 指令 | 行為契約 |
|---|---|
| `R2B_Models` | 收集指定模型並發布 `R2B.3dm`；不得匯出非目標物件或破壞未存修改 |
| `R2B_Camera` | 將 Rhino camera 狀態寫入 `R2B_Camera_Sync.json` |
| `R2B_Light` | 將指定 layer 的 Point 位置寫入 `R2B_Light_Sync.json` |
| `R2B_Open` | 開啟設定／資料位置與相關工具 |

Models 預設輸出到 Rhino 工作檔目錄，因此目前需先儲存 `.3dm`。若 `ModelDir` 有設定則依設定輸出。

## Blender 操作

### `LoopFlow_import_3dm`

- Model Sync 讀取 Rhino producer 發布的 3DM。
- Camera／Light Sync 讀取 JSON，只有 parse 與套用成功後才能更新已處理狀態。
- 重複同步應保留使用者已配置的材質與第一方同步狀態。

### LoopFlow Toolkit

提供 USD export、rename、group、selection 等獨立工具。Toolkit 不參與 Models／Camera／Light 的必要資料鏈，3.0 初期不得讓它阻塞安全修復。

## 使用安全契約

任何同步在成功、取消、失敗或中斷後都必須符合：

- Rhino 原文件的物件、layer、selection、path、modified flag 與未存內容不變。
- Models 只使用明確 object IDs，不以 `_SelAll` 取代資料選擇。
- 新 3DM 驗證可由 importer 讀取前，不覆蓋上一份有效輸出。
- Camera／Light 暫時性壞檔不污染 Blender state；consumer 可重試。
- Blender operator、panel、材質與使用者場景不因 reload／失敗留下半套狀態。
- 錯誤必須指出 stage，不得在失敗後仍顯示完成。

## Golden workflow

修改對應範圍前，使用測試 `.3dm`／`.blend` 記錄：

- Models：已存／未存、取消、失敗、last good 3DM、明確物件集合。
- Camera：座標、焦距、重複同步、壞 JSON 與 consumer state。
- Light：建立、更新、刪除、空資料、未支援類型。
- Blender integration：安裝、register／unregister、timer、operator、panel。
- importer：layers、materials、mesh、curve、instance、camera／view fixtures。
- Toolkit：安裝、啟用、停用與既有工具。

實機結果以 `architecture/PROGRESS.md` 為準。

## 設定與問題定位

- 設定檔：`%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\R2B_Path.txt`
- Debug log：同一 Data 目錄下的 `cursor_R2B_debug_log.txt`
- 先保存 Rhino／Blender 版本、錯誤畫面、log、輸入檔、是否未存與最後有效輸出，再交由 AI 處理。
- 不要自行刪除 Data、同步檔、正式 3DM 或 Blender add-on；先由 AI 比對設定與回復點。

## 文件責任

- `USER_GUIDE_zh-TW.md`：公開逐步使用指南。
- `_R2B_使用說明.md`：重構期間的行為契約。
- `_R2B_系統設定.md`：目前結構、設定、schema 與發行限制。
- `_R2B_命名與資料契約.md`：3.0 指令、Blender ID、跨軟體 schema 與 migration 的權威來源。
- `_R2B_重構計畫.md`：3.0 目標架構與遷移順序。
- `architecture/PROGRESS.md`：即時進度、檢查與下一步。
