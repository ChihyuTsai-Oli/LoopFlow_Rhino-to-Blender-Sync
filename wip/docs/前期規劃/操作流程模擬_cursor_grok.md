# R2B 3.0 — 操作流程模擬

> 依 [`資料生態決策表_三家建議.md`](資料生態決策表_三家建議.md)／[`資料生態決策表_合併.md`](資料生態決策表_合併.md) 的**已決原則**，用數字列表模擬真實操作。  
> 這是 **3.0 目標行為**的驗收腳本草案，不是現行已發布 2.x 保證會發生的事。  
> 指令名見 [`../rhino指令.md`](../rhino指令.md)。

## 本模擬假設的專案

- 工作檔：`Demo_Apt.3dm`（已存檔於工作機可寫路徑）
- 設定根：同目錄 `_LoopFlow_Config/loopflow_R2B/`（XF-ECO-02）
- Blender 端透過指標或手動覆寫指到同一設定根（XF-ED-04＝C）
- 圖層（示範名，可改成你的習慣）：

| 用途 | Rhino 圖層示範 | 誰讀它 |
|---|---|---|
| 建築／家具幾何 | `R2B::MDL::Architecture`、`R2B::MDL::Furniture` | Models（選取模式） |
| 燈光對齊點 | `R2B_LT_Points`（或設定裡的 `LightLayer`） | Light；只吃 Point |
| 其他 | （任意） | 本輪不同步 |

- Light 本輪只同步 **Point 位置與識別**（R2B-ED-06＝A）；燈的亮度／顏色在 Blender 樣板調。
- Camera／Light 預設可開 watcher，也可關、可手動推一次（R2B-ED-02＝B）。

---

## A. 開案與檢查

1. 在 Rhino 開啟 `Demo_Apt.3dm`，確認標題列**不是「未存檔」**。若尚未存檔：先存，再繼續（XF-ECO-01＝B：會寫設定／發布的指令未存檔就停）。
2. 按 `R2B_Open`：確認設定根指向本檔旁的 `loopflow_R2B/`；看 Health：三通道 last-good 時間、Blender Sync Folder 是否同一資料夾（R2B-ED-04／05）。
3. 在 Blender 開對應 `.blend`（或新建）。確認 Sync Folder／指標讀到同一 `loopflow_R2B/`；必要時手動覆寫路徑（手動優先於本機指標）。
4. （可選）在 Blender 準備好燈光樣板 collection：之後 Light 只搬點位，樣板參數留在 Blender。

---

## B. 第一輪：Models → Camera → Light

### B1. Models 同步

5. 在 Rhino 把要進 Blender 的幾何放在示範圖層（或先選好物件）。選取模式採三種之一：「全部／指定圖層／目前選取」；執行前應能看到**物件數與範圍**（R2B-ED-01）。
6. 按 `R2B_Models`。
7. 預期磁碟：在 `loopflow_R2B/`（或 `models/` 子層）出現 pending → 驗證通過 → **atomic** 換成 last-good 模型檔（XF-ECO-04；檔名角色見 R2B-ND-04）。失敗則 last-good 不變。
8. 預期 Rhino：來源 `.3dm` **內容與 Modified 狀態與執行前一致**（XF-ECO-03）；不會偷偷幫你存檔。
9. 在 Blender 更新／匯入該 last-good 模型。重複同步時**保留你已指定的材質與 Blender-owned 屬性**（R2B-ED-08）。
10. 若範圍是空的：應**阻擋發布**，不得假成功（R2B-ED-07）。

### B2. Camera 同步

11. 在 Rhino 調到你要的透視視角。
12. 按 `R2B_Camera`（或依賴已開啟且 Health 通過的 watcher 自動寫出）。
13. 預期磁碟：`live/camera.json`（或契約檔名）經 pending → validate → atomic last-good；內容為 Rhino 原生座標語意（R2B-ND-05＝A，由 Blender 端換算）。
14. 在 Blender：parse＋**套用成功**後才更新「已套用」狀態；半寫入失敗不得吞掉且不得標成已同步（XF-ECO-05）。
15. 若當下沒有有效相機：警告，**不覆寫** last-good（R2B-ED-07）。

### B3. Light 同步

16. 確認燈光對齊用的 Point 都在 `R2B_LT_Points`（或你在設定指定的 LightLayer）；圖層名打錯視同「沒有點」，不得發布空清單去清掉 Blender 燈具（R2B-ED-07）。
17. 按 `R2B_Light`（或 watcher）。
18. 預期磁碟：`live/light.json` atomic 發布；payload 含位置與穩定識別（如 `source_guid`），**不含**要驅動 Blender 燈能量／顏色的欄位（R2B-ED-06）。
19. 在 Blender：點位 empty 依 GUID 對齊；樣板複製為 `INST_*`；你在樣板上調的燈參數保留。
20. 到這裡，第一輪「模型＋相機＋燈光」齊備。

---

## C. 第二輪：改模型後重同步 → 再更新相機與燈光

### C1. 改模型並重跑 Models

21. 回 Rhino：改一面牆、移一張桌子，或增刪圖層物件；**先存檔**（若之後還要發布）。
22. 再按 `R2B_Models`（範圍規則同步驟 5）。
23. Blender 再更新模型：幾何換成新的 last-good；**材質指派等 Blender-owned 內容應留下**（R2B-ED-08）。相機與燈光**不必**因為 Models 重跑而自動清掉。

### C2. 改相機與燈光後再同步

24. 在 Rhino 改視角；需要時手動 `R2B_Camera`，或讓 watcher 寫出新 `camera.json`。
25. 移動／新增／刪除 `R2B_LT_Points` 上的 Point；再 `R2B_Light`。
26. Blender：相機跟到新視角；燈光 empty 跟到新點位。刪點時：同步衍生物件可清，使用者掛上去的非同步物件依契約保留／重掛（R2B-ED-08）。
27. 全程任一步失敗：該通道 last-good 保留上一版；來源 `.3dm` 不被指令改寫（XF-ECO-03／04）。

---

## D. 你應該感覺到的安全差異（對照 2.x 風險）

28. Models 失敗時，舊模型檔還在（不會先刪再匯出）。
29. LightLayer 打錯字時，Blender 燈具不會被空 JSON 一次清空。
30. Camera／Light 寫到一半時，Blender 不會把「已看見」記成「已套用成功」。
31. 未存檔就按發布類指令：停止並提示，不猜路徑。

---

## E. 本模擬不涵蓋

- Toolkit、Auto Basic Material（R2B-ED-09＝A，3.0 排除）
- 舊版設定自動升級（XF-ED-02：不升級、新舊不可混用）
- 正式 package 安裝與 RC；此處假設開發按鈕／隔離 profile 已能跑目標行為
