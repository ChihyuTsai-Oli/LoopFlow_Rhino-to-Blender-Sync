# R2B 3.0 — Rhino 指令與測試入口

本文件是**開發期 Rhino 測試按鈕**巨集與**全部 Rhino 指令名稱**的清單。方便在 Rhino 建立／核對按鈕。正式 command 契約仍以 `資料契約.md` 與 `前期規劃/資料生態決策表_三家建議.md` 裁決後回寫為準。

系統設定裡的「重構期間的 Rhino 測試入口」一節改為指向本檔；路徑或指令增減時**先改本檔**，再同步系統設定摘要與測試工具列。

## 規則

- 入口檔名＝開發期指令 ID。入口只轉交 command，不放業務邏輯。
- 巨集路徑指向**這台開發機**的 repo；換機只改路徑前綴，不改指令名稱。程式與契約不得寫死 Dropbox 或他機絕對路徑。
- 目前 `wip/src/rhino/entrypoints/` **已落地空殼**（跑了只提示尚未實作）；換機後路徑前綴若不同，只改本檔巨集。
- 改程式或入口後須**完全關掉 Rhino 再開**。
- 不要用已發布 2.x 工具列與 3.0 開發按鈕混著測同一案。
- 下列名稱是開發暫定，**不是**已凍結的 3.0 contract；若決策表改名，同步改本檔與入口檔名。

## 路徑前綴（本機）

公司／家中 Git 根若不同，只替換前綴：

```text
E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\
```

## 全部 Rhino 指令（開發暫定）

| 指令 ID（入口檔名） | 顯示用途（暫） | 狀態 |
|---|---|---|
| `R2B_Models` | 選圖層＋型別 → atomic 發布 R2B.3dm（Block→sidecar 關聯複製） | **已接** |
| `R2B_Models_Objects` | 匯出目前選取 → `R2B_Objects.3dm`（Block 各自展開） | **已接** |
| `R2B_Camera` | 開／關自動同步（按一下切換） | **已接** |
| `R2B_Camera_Push` | 手動推送相機 JSON 一次 | **已接** |
| `R2B_Light` | 開／關自動同步（按一下切換） | **已接** |
| `R2B_Light_Push` | 手動推送燈光點位 JSON 一次 | **已接** |
| `R2B_Open` | 開啟設定／工作資料夾／說明 | 空殼已落地 |

是否另增 `R2B_Config`、是否改名 → 見決策表 `R2B-ED-05`、`R2B-ND-01`。

## 按鈕巨集（可直接貼上）

```text
R2B_Models
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Models.py"

R2B_Models_Objects
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Models_Objects.py"

R2B_Camera
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Camera.py"

R2B_Camera_Push
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Camera_Push.py"

R2B_Light
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Light.py"

R2B_Light_Push
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Light_Push.py"

R2B_Open
_-ScriptEditor _Run "E:\_GitHub\LoopFlow_Rhino-to-Blender-Sync\wip\src\rhino\entrypoints\R2B_Open.py"
```

## 不經 Rhino 按鈕

- Blender：Portable `E:\blender-5.2.1_wip`；跑 `wip/tools/link_dev_addon.ps1` 後啟用 Dev Stub（N-Panel `LoopFlow R2B Dev`）。詳見 `系統設定.md`。
- `import_3dm`／Toolkit：同樣用隔離 profile；importer 工作複本自 `import_3dm/…0.0.18…` 複製。

## 變更紀錄

| 日期 | 說明 |
|---|---|
| 2026-08-28 | `R2B_Models_Objects`；Blender Import Objects；Sync Models 改名；Block sidecar |
| 2026-08-28 | `R2B_Models` 接業務（精準 ID／atomic／無 Open 中間檔）；Blender Update／Import |
| 2026-08-28 | `R2B_Light`＝toggle；新增 `R2B_Light_Push`；Light 兩端 D02 |
| 2026-08-28 | `R2B_Camera`＝toggle；新增 `R2B_Camera_Push`；Blender 作業資料夾＝工作檔同層 |
| 2026-08-28 | entrypoints 空殼落地；註明 Blender Dev Stub 路徑 |
| 2026-08-28 | 註明 Blender 測試 add-on 空殼測法（對齊 Rhino entrypoints） |
| 2026-08-27 | 初版：自系統設定抽出完整指令清單與巨集 |
