# R2B 3.0 — 操作流程模擬（Codex 版）

> 本文依 [`資料生態決策表_合併.md`](./資料生態決策表_合併.md) 的已決內容，並交叉核對 [`資料生態決策表.md`](./資料生態決策表.md)、[`現況與工作鏈藍圖.md`](./現況與工作鏈藍圖.md)、[`../rhino指令.md`](../rhino指令.md)、六份重構 SSOT 與現行 2.x 程式。
>
> 這是一份 **3.0 目標行為的操作與驗收模擬**，不是現行 2.x 功能說明，也不取代決策表或回寫後的正式契約。下列檔名代表已採用的角色方向；正式實作前仍須回寫 SSOT，凍結精確名稱與 schema。

## 先釐清 XF-ED-02

「不升級，新舊版不可混用」不是把舊版作業檔原地轉成新版。

- 舊版 `R2B_Path.txt`、AppData 資料、Blender add-on 與既有 scene 保留給 2.x 使用。
- 進入 3.0 時，改用隔離的 Blender profile／Extension、全新的專案設定根與 3.0 consumer；不讓 2.x、3.0 同時讀寫同一套同步資料。
- 原本的 Rhino `.3dm` 可以作為設計來源，但 3.0 不自動搬設定、不改寫來源，也不承諾把舊 Blender scene ID 或 collection 自動轉換。
- `R2B-ED-12` 所需的欄位／scene ID 對照表是盤點與人工重建依據，不是 migration 工具。

## 模擬專案與資料角色

- Rhino 工作檔：`Demo_Apt.3dm`，已存檔於可寫入位置。
- Blender 工作檔：`Demo_Apt_R2B.blend`，使用隔離的 3.0 profile。
- 專案設定根：與 `.3dm` 同目錄的 `_LoopFlow_Config/loopflow_R2B/`。
- 建議示範圖層：模型在 `R2B::MDL::*`；燈光對齊點在設定指定的 Light layer。
- Models、Camera、Light 是三條獨立通道；任何一條失敗都不應破壞另兩條的 last-good。

| 資料角色 | 模擬中的位置 | 發布規則 |
|---|---|---|
| 專案設定 | `config.json` | 驗證 schema；錯誤就停止，不猜預設路徑 |
| Models | `models/` 下的 pending 與 last-good `.3dm` | pending → validate → atomic replace |
| Camera | `live/` 下的 pending 與 last-good JSON | pending → validate → atomic replace |
| Light | `live/` 下的 pending 與 last-good JSON | pending → validate → atomic replace |
| 記錄 | `r2b.log` | 失敗可由訊息直接開到對應 stage |

## 情境一：第一次以 3.0 建立專案

### 1. 隔離版本並建立設定根

1. 完全關閉使用 2.x add-on 的 Blender；不要在同一個 Blender profile 內覆蓋安裝 3.0。
2. 在 Rhino 開啟 `Demo_Apt.3dm`。若文件尚未存檔，任何會建立設定或發布檔的動作都停止；只有純說明頁可以開啟（XF-ECO-01）。
3. 按 `R2B_Open`。第一次使用時，確認或建立 `_LoopFlow_Config/loopflow_R2B/`，再顯示 Health，而不是另外增加 `R2B_Config` 指令（R2B-ED-04／05）。
4. Health 應至少顯示：來源文件、實際設定根、三通道 last-good 狀態與時間、Blender Sync Folder 是否指到同一位置。
5. Blender 端先讀本機「目前專案指標」；若使用者填過手動路徑，以手動覆寫為準。路徑不存在、產品不是 R2B、來源文件不符或指標過舊時，停止並指出原因，不猜最近使用的資料夾（XF-ED-04）。

### 2. 第一次發布 Models

6. 在 Rhino 按 `R2B_Models`，從「全部／指定圖層／目前選取」三種互斥範圍選一種。模擬選「指定圖層 `R2B::MDL`」。
7. 指令先顯示將發布的範圍與物件數。使用者確認後才進入匯出；系統只記住上一次成功的模式作為下次預設（R2B-ED-01）。
8. Producer 依明確物件 ID 建立暫存內容，不使用 `_SelAll` 擴大範圍，也不靠切換／清理原工作文件完成匯出。
9. 匯出完成後先驗證 pending `.3dm` 可讀、非空、schema／單位資料完整，再以 atomic replace 更新 Models last-good（XF-ECO-04）。
10. 成功訊息包含 channel、物件數、輸出與完成時間；取消或失敗則顯示 stage、可採取動作與 log 位置，不能在 `finally` 無條件顯示成功（R2B-ED-03）。
11. 比對 Rhino 執行前後：來源物件、圖層、選取、隱藏／鎖定狀態與 `Modified` 狀態皆不變，且指令不替使用者自動存檔（XF-ECO-03）。
12. 在 Blender 的 3.0 Sync 介面執行第一次 Models 匯入。consumer 解析成功並完成套用後，才記錄「已套用」revision／mtime（XF-ECO-05）。
13. 第一次匯入可建立同步管理範圍；Blender 使用者之後指定的材質、collection 可見性、自訂屬性與非同步內容，其所有權要先依契約標記，不能只靠名稱猜測。

### 3. 第一次發布 Camera

14. 在 Rhino 切到有效的透視 viewport，調整到預定視角。
15. `R2B_Camera` 預設啟用可開關 watcher；同一入口也要能手動推送一次。若工作環境不適合持續同步，使用者可關閉 watcher，不影響 Models 或 Light（R2B-ED-02／ECO-05）。
16. Camera payload 保留 Rhino 原生座標語意，並帶 `schema_version`、`revision`、`unit_system`、`meters_per_unit`、`coordinate_system` 等契約欄位；座標換算只在 Blender consumer 的單一位置處理（R2B-ND-05）。
17. Blender watcher 只在 revision／mtime 改變時解析；必須等相機位置、方向、up 與 lens 全部套用成功，才更新已套用狀態。
18. 若沒有有效相機、JSON 半寫、schema 不支援或套用失敗，保留上一個可用視角並回報失敗；不得吞掉錯誤，也不得先標記成已同步。

### 4. 第一次發布 Light

19. 在 Rhino 建立燈光對齊用 Point，全部放入設定指定的 Light layer。3.0 初版只傳 Point 的位置與穩定識別；顯示名可供診斷，但不驅動 Blender 燈參數（R2B-ED-06）。
20. 按 `R2B_Light` 或使用已啟用的 watcher。Producer 以 Rhino GUID 等穩定 ID 發布，不把圖層名或物件名當永久身分（R2B-ECO-06）。
21. Blender 端依穩定 ID 建立／更新同步管理的定位物件，再連接到使用者準備的燈具樣板。亮度、顏色與燈具內容仍由 Blender 擁有。
22. consumer 只清理「由 R2B 管理且本次權威資料已確認刪除」的衍生內容。使用者自行加在同步物件下、又不是同步管理命名／標記的內容，應保留或重新掛接（R2B-ED-08）。
23. 到此完成第一輪 Models、Camera、Light。三通道 Health 各自顯示最後成功時間，不能用其中一條成功掩蓋另一條失敗。

## 情境二：日常增量更新

24. 使用者在 Rhino 修改牆面與家具，另移動相機和兩個燈光 Point。需要保存設計變更時，由使用者自己存 `.3dm`。
25. 再按 `R2B_Models`，沿用上一次成功的「指定圖層」模式。預覽應只列出該範圍；若數量突然等於全文件，使用者可在真正發布前取消。
26. Blender 執行 Models 更新：幾何更新，但已指定材質、collection 顯示狀態、使用者自訂屬性與非同步物件依 ownership matrix 保留。Camera、Light 不因 Models 更新而被重建。
27. Camera watcher 開啟時，視角變動自動發布；關閉時按一次 `R2B_Camera`。Blender 只套用比目前成功 revision 新的資料。
28. `R2B_Light` 發布新增、移動與刪除結果。既有 GUID 的燈只移位，新 GUID 建立新定位，已從權威集合刪除的 GUID 才進入受控清理。
29. 任一通道失敗時，該通道仍指向上一份 last-good；使用者可以繼續使用其他兩條通道，不需重跑整套流程。

## 情境三：容易誤操作的復原演練

| 操作／故障 | 3.0 預期結果 | 使用者下一步 |
|---|---|---|
| 未存檔便發布 | 發布停止，不建立猜測路徑 | 先存 `.3dm`，再重跑 |
| Models 選取為空 | 不發布、不覆寫 last-good | 重選範圍；若真的要清空，執行另設且需再次確認的「發布空集合」 |
| Light layer 拼錯或沒有 Point | 不寫出空集合，不刪 Blender 燈具 | 修正設定／圖層後重跑 |
| 沒有有效透視相機 | Camera 發布停止，舊視角保留 | 切到有效 viewport 後手動推送 |
| pending `.3dm` 無法解析 | Models 整次失敗，last-good 不變 | 由錯誤訊息開 log，修正後重跑 |
| Camera／Light JSON 半寫或 schema 不符 | consumer 不 apply、不前移成功狀態 | 等下一份完整發布或手動重跑 |
| Blender 使用者物件名稱剛好像 `INST_*` | 名稱不能單獨決定所有權；若無管理標記不得自動刪 | 依 ownership／recovery 規則保留或重掛 |
| consumer 指到另一個專案 | Health 報來源不符並停止 | 改正手動路徑或重建本機指標 |

## 完成驗收

30. 連續跑兩次相同 Models，第二次不應改壞材質或產生重複 collection／物件。
31. 連續發布 Camera／Light，consumer 只處理新 revision；失敗後重送相同內容仍可恢復。
32. 每次發布前後比較來源 `.3dm`，確認沒有內容、圖層狀態、選取狀態或 Modified 狀態被同步流程改變。
33. 暫時鎖住輸出目錄或製造無效 pending，確認錯誤訊息指出 channel＋stage，且 last-good 可繼續使用。
34. 關閉 Camera／Light watcher，確認兩者仍可各自手動推送一次；關閉其中一條不影響另一條與 Models。
35. 在隔離 profile 內驗證 3.0 package／operator namespace 不覆蓋現行 `import_3dm.*` 2.x 安裝；Toolkit 可不安裝，主同步鏈仍能完成。

## 本輪刻意不做

- 不做 v2→v3 自動升級、雙寫、alias 或同一 scene 混用。
- 不新增同步種類；不把 Auto Basic Material 放回 3.0。
- 不擴充 Toolkit，也不讓 Toolkit 阻塞 Models／Camera／Light。
- 不把燈光能量、顏色或其他 Blender-owned 內容反向塞進 Rhino。
- 不把開發機 repo 絕對路徑或 Dropbox 測試資產路徑寫入產品 runtime。
