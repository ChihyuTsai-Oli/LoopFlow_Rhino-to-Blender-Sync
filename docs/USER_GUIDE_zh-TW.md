# LoopFlow R2B 使用說明

> 所有 Rhino 端指令皆在 Rhino 8 (CPython 3.9) 環境中執行。
> Blender 端必須安裝 `LoopFlow_import_3dm` Addon（模型匯入核心）。
> `LoopFlow_Toolkit` 為選擇性安裝的實用工具包，不參與同步流程。
> 開發環境為 Blender 5.1.2（Python 3.13）。

最後更新：2026-04-28

---

## 目錄

1. [Rhino 端指令](#rhino-端指令)
2. [Blender 端 — LoopFlow_import_3dm（必須）](#blender-端--loopflow_import_3dm必須)
3. [Blender 端 — LoopFlow Toolkit（選擇性）](#blender-端--loopflow-toolkit選擇性)
4. [設定檔](#設定檔)

---

## Rhino 端指令

---

### R2B_Models（模型同步）

一鍵匯出乾淨的 Rhino 模型供 Blender 使用。

**執行流程：**

1. 儲存目前的 Rhino 檔案（腳本會檢查是否已存檔）
2. 跳出圖層選擇視窗，選取要匯出的父圖層（記住上次選取）
3. 自動開啟中間檔進行清理：
  - 刪除 Layouts、點物件、曲線、文字點、標注、Hatch
  - 刪除圖層名稱包含 `//` 的輔助圖層及其物件
  - 炸開所有 Block
  - 將所有圖層顏色轉為 Blender 可識別的材質結構
  - 全部物件套用統一 Box Mapping（尺寸由 `BoxMapSize` 設定）
4. 儲存中間檔，自動切回原始工作檔

> **注意**：腳本執行期間會暫時切換至中間檔案；過程全自動，勿手動操作。
>
> 匯出完成後，Blender 端使用 `LoopFlow_import_3dm` addon 一鍵匯入即可，完整流程只需一鍵。

---

### R2B_Camera（相機即時同步）

Toggle 設計：執行一次開始同步，再次執行停止。

- 開啟後，偵測 Rhino 視窗旋轉或縮放事件即即時寫出相機資料
- 輸出 `R2B_Camera_Sync.json`，由 Blender 端的 Camera 監聽器讀取
- 不需要儲存檔案，未儲存的新檔案亦可即時同步

> **停止方式**：再次執行 R2B_Camera 指令即可停止背景監聽。

---

### R2B_Light（燈光位置同步）

掃描場景中的 Point 物件，輸出燈光位置資料供 Blender 端自動對齊燈具。

- 讀取設定中 `LightLayer` 指定的圖層前綴（預設：`R2B_LT_Points`）
- 子圖層名稱作為燈具類型（Template 名稱），Blender 端依此對應燈具模型
- 輸出 `R2B_Light_Sync.json`

**圖層命名範例：**

```
R2B_LT_Points/
  Downlight        ← layer_short = "Downlight"
  WallLight
  SpotLight
```

> 在 Blender 端執行燈光對齊後，燈具會依 type 名稱對應至預先準備好的燈具 Collection。

---

### R2B_Open（快速開啟工具）

從 Rhino 指令列快速開啟相關檔案。


| 選項             | 說明                                 |
| -------------- | ---------------------------------- |
| **Config**     | 開啟 `R2B_Path.txt` 設定檔              |
| **DataFolder** | 開啟資料目錄                             |
| **DebugLog**   | 開啟 `cursor_R2B_debug_log.txt` 除錯記錄 |


---

## Blender 端 — LoopFlow_import_3dm（必須）

所有操作位於 **N Panel > LoopFlow 3dm > Rhino Live Link**，分為兩個區塊。

---

### Model Sync（模型同步）


| 按鈕                | 說明                                        |
| ----------------- | ----------------------------------------- |
| **Import Models** | 首次匯入，同時更新材質                               |
| **Update Models** | 後續更新，完整保留 Blender 中已設定的材質、隱藏、排除、Bounds 狀態 |


- 路徑欄位預設 `//R2B.3dm`（與 Blender 檔案同目錄）
- 按路徑欄位旁的 **🔍** 按鈕（Auto-Detect）可自動填入模型路徑與 Sync Folder

> 一般作業時用 **Update Models**，材質不受影響。需要全面刷新材質時才用 **Import Models**。

---

### Camera & Light Sync（相機與燈光同步）


| 按鈕 / 欄位                      | 說明                                                          |
| ---------------------------- | ----------------------------------------------------------- |
| **Start / Stop Camera Sync** | Toggle，開啟後背景輪詢 `R2B_Camera_Sync.json`，即時更新 Viewport 視角      |
| **Scale**                    | 單位換算比例（預設 `0.01`，對應 Rhino 公分）                               |
| **Lens**                     | 鏡頭焦距倍率（預設 `1.80`；視角偏廣時調高）                                   |
| **Sync Rhino Lights**        | 一鍵讀取 `R2B_Light_Sync.json`，依 Rhino Points 位置對齊燈具並清除已刪除的孤立燈具 |
| **Sync Folder**              | JSON 同步檔目錄，點 Auto-Detect 自動填入                               |


**燈光同步前置設定：**

1. 建立 `Lighting Fixtures` Collection，放入燈具模型（名稱對應 Rhino 子圖層名稱）
2. 建立 `Lighting` Collection，放入燈光物件（同上）
3. 設定 Sync Folder 後，點 **Sync Rhino Lights** 即自動對齊

---

## Blender 端 — LoopFlow Toolkit（實用工具包，選擇安裝）

實用工具包，**不參與同步流程**，可按需求獨立使用。
所有工具位於 **View3D > N Panel > LoopFlow Toolkit**，分為三個面板。

---

### Export Tools（匯出工具）


| 功能                         | 說明                            |
| -------------------------- | ----------------------------- |
| **Export All to USD**      | 批次匯出場景中所有頂層 Collection 為 USDZ |
| **Export Selected to USD** | 勾選特定 Collection 後選擇性匯出        |


- 匯出前，根物件 Origin 自動移至 `(0,0,0)`；匯出後自動復原位置
- 選擇性匯出：在清單中勾選目標 Collection，搭配 **All / None** 快速全選

---

### Rename Tools（命名工具）


| 功能                                | 說明                                          |
| --------------------------------- | ------------------------------------------- |
| **Rename Collections**            | 批次依序命名在 Outliner 中選取的 Collection，並啟用 Render |
| **Rename Objects by Collections** | 以 Collection 名稱為基底，自動編號內部物件；支援 Alt+D 實例雙重計數 |
| **Rename Objects**                | 純序號命名，以 XY 空間位置排序（左下角優先，沿 +Y 推進）            |


> **Rename Objects by Collections**：偵測 `obj.data.users > 1` 的共享 Mesh，附加 `_Ins` 後綴並同步 Mesh Data 名稱。

---

### Selection Tools（選取工具）


| 功能                            | 說明                                                     |
| ----------------------------- | ------------------------------------------------------ |
| **Group**                     | 選取多個子 Mesh，最後選取的作為 Active（父物件），一鍵建立群組並同步至同名 Collection |
| **Un-Group**                  | 選取群組內任一成員，解散整個群組，還原世界座標                                |
| **Re-Group**                  | 拍平複雜階層，套用 Armature modifier，將所有 Mesh 整合至 Active 物件下    |
| **Select All in Group**       | 選取群組內任一物件，自動往上找根節點並選取整個階層                              |
| **Delete Objects From Group** | 刪除父物件，子物件解除父子關係並保留世界座標                                 |
| **Material Isolator**         | 選取物件後，將材質 Link 切換為 Object 模式，複製獨立材質（附加 `_Unique` 後綴）   |


> **Material Isolator 後續操作**：Properties 面板（右下）→ Material 分頁 → 將 Link 下拉改為 "Object"。

---

## 設定檔

### `R2B_Path.txt`（位於 `%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\`）

首次執行時自動建立，欄位缺失時自動補全。


| 欄位               | 預設值                    | 說明                       |
| ---------------- | ---------------------- | ------------------------ |
| `DataPath`       | （自動）                   | 資料輸出根目錄                  |
| `ModelDir`       | （空白）                   | 模型輸出目錄；空白時退回至 Rhino 工作目錄 |
| `LightLayer`     | `R2B_LT_Points`        | 燈光 Points 圖層前綴           |
| `CameraFile`     | `R2B_Camera_Sync.json` | 相機同步檔名稱                  |
| `LightFile`      | `R2B_Light_Sync.json`  | 燈光同步檔名稱                  |
| `ModelFile`      | `R2B.3dm`              | 模型輸出檔名稱                  |
| `BoxMapSize`     | `500`                  | 模型同步 Box Mapping 尺寸（mm）  |
| `LastModelLayer` | （自動）                   | 記住上次模型匯出選取的圖層            |


> 使用 `R2B_Open > Config` 可直接從 Rhino 指令列開啟此檔案。

