# R2B 3.0 — Rhino 指令與測試入口

本文件是**開發期 Rhino 測試按鈕**巨集與**全部 Rhino 指令名稱**的清單。方便在 Rhino 建立／核對按鈕。正式 command 契約仍以 `資料契約.md` 與 `前期規劃/資料生態決策表_三家建議.md` 裁決後回寫為準。

系統設定裡的「重構期間的 Rhino 測試入口」一節改為指向本檔；路徑或指令增減時**先改本檔**，再同步系統設定摘要與測試工具列。

## 規則

- 入口檔名＝開發期指令 ID。入口只轉交 command，不放業務邏輯。
- 巨集路徑指向**這台開發機**的 repo；換機只改路徑前綴，不改指令名稱。程式與契約不得寫死 Dropbox 或他機絕對路徑。
- 目前 `wip/src/rhino/entrypoints/` **已落地**（Models／Camera／Light／Open 已接並合入 `v3-development`）；換機後路徑前綴若不同，只改本檔巨集。
- 改程式或入口後須**完全關掉 Rhino 再開**。
- 同一 Rhino 可測 R2B 與 R2O：每個入口會清掉對方的 `rhino`／`foundation` 快取。仍須關再開才載入最新腳本。
- 不要用已發布 2.x 工具列與 3.0 開發按鈕混著測同一案。
- 下列名稱**已凍結**（2026-08-29 自 `R2B_*` 改連寫）；再改名須使用者明示。Blender N 面板與磁碟檔名不變。

## 路徑前綴（本機）

公司／家中 Git 根若不同，只替換前綴：

```text
E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\
```

## 全部 Rhino 指令（已凍結）

| 指令 ID（入口檔名） | 成對 Blender | 顯示用途 | 狀態 |
|---|---|---|---|
| `RBModels` | Sync Models／Update Models | 選圖層＋型別 → `R2B.3dm`（**有材質**；Block→sidecar） | **已接** |
| `RBObjects` | Import Objects | 目前選取 → `R2B_Objects_時戳.3dm`（**無材質**；Block 各自展開；不覆蓋） | **已接** |
| `RBCamera` | Camera Auto On／Off | 開／關自動同步 | **已接** |
| `RBCameraPush` | Camera Push Once | 手動推送相機 JSON 一次 | **已接** |
| `RBLight` | Light Auto On／Off | 開／關自動同步 | **已接** |
| `RBLightPush` | Sync Lights | 手動推送燈光點位 JSON 一次 | **已接** |
| `RBOpen` | Open / Health；Open Docs | 四顆等寬：Config／live／models／Docs | **已接** |

## 開發按鈕巨集（ScriptEditor，可直接貼上）

**正式工具列不要用下面這段。** 正式左鍵請用下一節 `! _RBModels` 等。

```text
RBModels
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBModels.py"

RBObjects
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBObjects.py"

RBCamera
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBCamera.py"

RBCameraPush
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBCameraPush.py"

RBLight
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBLight.py"

RBLightPush
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBLightPush.py"

RBOpen
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\RBOpen.py"
```

## 正式工具列巨集（yak 裝上之後）

左鍵填這些；右鍵留空。指令尚未登錄前按了不會動。RUI 請 `ExportRuiFile` 存到 `wip/docs/toolbar/`。

```text
! _RBModels
! _RBObjects
! _RBCamera
! _RBCameraPush
! _RBLight
! _RBLightPush
! _RBOpen
```

## 不經 Rhino 按鈕

- Blender：Portable `E:\blender-5.2.1_wip`；跑 `wip/tools/link_dev_addon.ps1` 後啟用 Dev Stub（N-Panel 標籤 `LoopFlow`、bar `Rhino to Blender Sync`）。詳見 `系統設定.md`。
- `import_3dm`／Toolkit：同樣用隔離 profile；importer 工作複本自 `import_3dm/…0.0.18…` 複製。

## 變更紀錄

| 日期 | 說明 |
|---|---|
| 2026-08-30 | G02 `0.1.1`：yak 含 Sync add-on；第一次跑指令拷到「文件\LoopFlow」 |
| 2026-08-30 | G02：正式工具列巨集 `! _RBModels` 等；開發 ScriptEditor 巨集分開寫 |
| 2026-08-29 | Import Objects 檔案總管預設 `_LoopFlow_Config/loopflow_R2B/models/` |
| 2026-08-29 | 入口隔離，避免與 R2O 同 Rhino 互踩 |
| 2026-08-29 | `RBObjects`；時戳 3dm 不覆蓋；Import Objects 開檔案總管 |
| 2026-08-29 | Open／Health 家中通過；合入 `v3-development` |
| 2026-08-28 | `RBModels` 接業務（精準 ID／atomic／無 Open 中間檔）；Blender Update／Import |
| 2026-08-28 | `RBLight`＝toggle；新增 `RBLightPush`；Light 兩端 D02 |
| 2026-08-28 | `RBCamera`＝toggle；新增 `RBCameraPush`；Blender 作業資料夾＝工作檔同層 |
| 2026-08-28 | entrypoints 空殼落地；註明 Blender Dev Stub 路徑 |
| 2026-08-28 | 註明 Blender 測試 add-on 空殼測法（對齊 Rhino entrypoints） |
| 2026-08-27 | 初版：自系統設定抽出完整指令清單與巨集 |
