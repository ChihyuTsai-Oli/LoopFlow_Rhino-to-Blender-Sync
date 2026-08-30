# LoopFlow R2B 指令逐項說明

> 同一專案不要混用舊版的工具列、套件或 Blender add-on。
>
> 整體流程見 [使用說明總覽](./USER_GUIDE_zh-TW.md)。指令名稱是 Rhino 命令列裡的正式名稱（連寫，例如 `RBModels`）。
>
> Rhino 對話框與 Blender 面板為英文。

## 專案資料夾原則

開始前先把 `.3dm` 存檔。**`.3dm` 所在資料夾就是作業資料夾**；交換檔在同層 `_LoopFlow_Config/loopflow_R2B/`。整包搬到其他磁碟或電腦仍可使用，不必改絕對路徑。

Blender Work Folder 指到與 `.3dm` **同一層**。

## 快速索引

| 階段 | Rhino | Blender | 一句話 |
|---|---|---|---|
| 開案 | `RBOpen` | Open / Health；Open Docs | 看設定根與上次成功時間；開資料夾或本說明 |
| 主模型 | `RBModels` | Sync Models／Update Models | 選圖層匯出有材質的 `R2B.3dm` |
| 選取物件 | `RBObjects` | Import Objects | 目前選取 → 時戳 3dm，無材質 |
| 相機 | `RBCamera`／`RBCameraPush` | Camera Auto On／Off／Push Once | 作用視角寫到 `live/camera.json` |
| 燈光 | `RBLight`／`RBLightPush` | Light Auto On／Off／Sync Lights | 燈光圖層 Point 位置寫到 `live/light.json` |
| 著色 | （無） | Shader Editor → Box Projection | 載入 PBR、不寫 UV |

工具列四顆鈕，左鍵／右鍵：

| 鈕 | 左鍵 | 右鍵 |
|---|---|---|
| 1 | `RBOpen` | — |
| 2 | `RBModels` | `RBObjects` |
| 3 | `RBCamera` | `RBCameraPush` |
| 4 | `RBLight` | `RBLightPush` |

## 目錄

[01 開啟設定與說明](#01-開啟設定與說明) · [02 主模型](#02-主模型) · [03 選取物件](#03-選取物件) · [04 相機](#04-相機) · [05 燈光](#05-燈光) · [06 Blender Sync 面板](#06-blender-sync-面板) · [07 Box Projection](#07-box-projection) · [08 不要做的事](#08-不要做的事)

---

## 01　開啟設定與說明

**指令**：`RBOpen`

已存檔後執行。跳出英文 Health 視窗，四顆等寬按鈕由左到右：

- **Open Config** — 開啟 `_LoopFlow_Config/loopflow_R2B/`
- **Open live** — 相機／燈光 JSON
- **Open models** — `R2B.3dm` 與選取物件檔
- **Open Docs** — 本 GitHub 文件入口

摘要會列出設定根路徑，以及 Camera／Light／Models／Objects 上次成功寫出的時間。未存檔會被擋住。

Blender **Open / Health**：懸停看摘要，左鍵開設定根。**Open Docs** 開同一份文件入口。

---

## 02　主模型

**指令**：`RBModels`

匯出給 Blender 主同步用的乾淨模型（**有材質**）。

1. 檔案須已存檔。
2. 選要匯出的圖層（含子層，可捲動）。
3. 勾選幾何類別。同一 Rhino 視窗會記住上次成功的勾選；第一次時 Point／Curve 預設不勾。
4. 可輸入排除標記（預設 `//`；空白＝不排除）。圖層路徑含此文字者不匯出。
5. 成功後寫入 `models/R2B.3dm`。失敗不會蓋掉上次成功的檔。來源 Rhino 檔會回到執行前的狀態，過程中**不會**切到中間檔。

材質名稱是 `父圖層::末端圖層`，顏色跟圖層。Block 會炸開；同一 Block 定義多顆時，第一顆進 3dm，其餘用 sidecar 讓 Blender 關聯複製。

圖層名稱含 `//` 的輔助層預設略過。

Blender：日常用 **Update Models**（幾何更新、你調過的同名材質留下）。需要重掛基本材質槽時才用 **Sync Models**。兩邊都會重建 `R2B` 集合，不動 Lighting。

---

## 03　選取物件

**指令**：`RBObjects`

把**目前選取**匯成無材質 3dm，給 Blender **Import Objects**。

- 每次新檔：`models/R2B_Objects_年月日_時分秒.3dm`，不覆蓋舊檔
- 選到的 Block 每一顆都展開
- **不寫材質**

Blender 按 Import Objects 會開檔案總管（預設指到 `loopflow_R2B/models/`）。選哪份就匯哪份；取消則不匯入。結果累加在場景最上層，父物件名 `R2B_Objects`，**不**進 `R2B` 集合。

不要把 `R2B.3dm` 拿去 Import Objects，也不要把時戳檔拿去 Sync／Update Models。

---

## 04　相機

**指令**：`RBCamera`（開／關自動同步）、`RBCameraPush`（手動推一次）

- 用透視作用視角
- 檔案須已存檔
- 寫入 `live/camera.json`
- 再開一次 `RBCamera` 就停止自動同步

Blender：Camera Auto On／Off／Push Once。自動開啟後會跟隨 Rhino 視角。

---

## 05　燈光

**指令**：`RBLight`（開／關自動同步）、`RBLightPush`（手動推一次）

只同步 **LightLayer 子層**上的 Point 位置（預設父層名 `R2B_LT_Points`）。父層本身不要放 Point。

**Rhino 圖層範例**

| 圖層 | 放什麼 | 會同步？ |
|---|---|---|
| `R2B_LT_Points`（父層） | 不要放 Point | 否 |
| `R2B_LT_Points::Down_Light` | Point | 是；類型名 `Down_Light` |
| `R2B_LT_Points::Pendant` | Point | 是；類型名 `Pendant` |

**Blender 同步前自己準備**

| Collection（外面可以再包一層） | 放什麼 | 名稱 |
|---|---|---|
| `Lighting` | Blender 燈光 | 與 Rhino 子層末端同名 |
| `Lighting Fixtures` | 燈具模型 | 同名；檔裡不能重名時可用 `.001`，程式會對上 |

同步後出現 `R2B Lighting Points`：每個 Rhino Point 一個 empty，底下掛對應的燈與燈具。找不到模板就不會留空的 empty。沒有符合的 Point 時 Rhino **不寫檔**，Blender **也不清燈**。

改模板裡的燈具，組出來的實例會一起變。某一盞要不同亮度或顏色，請在 Blender 對該實例做 Make Single User。

---

## 06　Blender Sync 面板

3D 視窗 N 面板 → **LoopFlow** → **Rhino to Blender Sync**。

| 按鈕 | 說明 |
|---|---|
| **Sync Models** | 讀 `models/R2B.3dm`，重建 `R2B` 集合，掛基本 Principled（底色 `#F2F2F2FF`） |
| **Update Models** | 幾何同樣重建，**不覆寫**已有同名材質 |
| **Import Objects** | 選時戳 3dm，無材質、累加 |
| **Camera Auto On／Off／Push Once** | 讀 `live/camera.json` |
| **Light Auto On／Off／Sync Lights** | 讀 `live/light.json` |
| **Open / Health** | 懸停＝摘要；左鍵開設定根 |
| **Open Docs** | 開本文件入口 |

Work Folder 指到與 `.3dm` 同一層。不必再啟用獨立的 Import Rhinoceros 3D。Sync zip 在「文件\LoopFlow\Rhino to Blender Sync」，用 **Add-ons → Install from Disk** 安裝（不要走 Extensions）；列表名稱 **LoopFlow Rhino to Blender Sync**。若先前誤裝成 import_3dm、改名失敗，或啟用時出現 `No module named 'foundation'`：完全關掉 Blender，刪掉 `extensions\user_default` 與 `scripts\addons` 裡的 `loopflow_r2b_sync`／`loopflow_r2b_sync@`，再只裝 zip。Portable 若在 Dropbox 上，安裝前先暫停同步。

LoopFlow Toolkit 不在本產品同步範圍。

---

## 07　Box Projection

著色輔助，與模型／相機／燈光同步分開。

1. 到 Shader Editor，最好已有 Principled。
2. N 面板 **LoopFlow → Box Projection → Load PBR Maps**。
3. 一次可多選 Base Color／Roughness／Metallic／Normal（檔名含 `diff`／`rough`／`metal`／`nor` 即可）。
4. **Space**：World＝圖釘在場景；Object＝圖跟著物件。Scale 單位是公尺／張。Blend 0 接縫較硬。
5. 不寫 UV。

---

## 08　不要做的事

- 未存檔就按發布
- 把 `R2B.3dm` 與 `R2B_Objects_時戳.3dm` 交叉拿去對方的 Blender 按鈕
- 在 Octane 或別的軟體流程裡期待這套 Blender 按鈕
- 為了同步去改來源 `.3dm` 的檔名或把作業檔存成中間檔
