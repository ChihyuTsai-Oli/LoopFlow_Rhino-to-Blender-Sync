# LoopFlow R2B 3.0 — 邏輯架構

> 用 ASCII 圖說明 R2B 整體是怎麼組成的，輔助閱讀，**不是規格**。
> 內容整理自 `實作總覽.md`、`工作流程.md` 與實際程式目錄；若與六份實作文件不同，以六份為準。
> 中文字在等寬字型下寬度不一，方框右側刻意不封邊，避免歪掉。

---

## 一、產品邊界：兩端靠「檔案」溝通

```
+----------------------------+        +-----------------------+        +-----------------------------+
| Rhino 端（發布者）         |        | 交換檔                |        | Blender 端（接收者）
| 指令 RBModels、RBCamera…   | -----> | 放在工作檔旁的        | -----> | Sync add-on
| 只負責「安全地寫出檔案」   |  寫出  | _LoopFlow_Config/     |  讀取  | N 面板按鈕、計時器、狀態
| 不含任何 Blender 邏輯      |        | loopflow_R2B/         |        |        |
+----------------------------+        +-----------------------+        |        v 呼叫唯一入口
                                                                       | 內嵌 import_3dm（fork）
                                                                       | 只做 3DM --> Blender 轉換
                                                                       +-----------------------------+

主鏈之外（獨立，不影響同步）：
+----------------------------+        +----------------------------------------+
| Box Projection             |        | ToolBox
| Shader Editor 的著色輔助   |        | 獨立 Blender add-on（Export／Rename／
| 載入 PBR 貼圖、方盒投影    |        | Selection），不進 Rhino 安裝包
| 不寫 UV、不進同步鏈        |        | 細節見 toolbox/
+----------------------------+        +----------------------------------------+
```

兩端沒有網路連線、沒有共用的執行程式，只認同一個資料夾裡的檔案。

---

## 二、五條通道

每條通道可以單獨重跑；兩端要成對使用，不要交叉混用。

```
通道      Rhino 指令                交換檔                               Blender 按鈕
--------  ------------------------  -----------------------------------  ---------------------------
Models    RBModels                  models/R2B.3dm                       Sync Models（建材質）
主模型    選圖層＋幾何類別          models/R2B_blocks.json               Update Models（不覆寫材質）
          Block 炸開、材質跟圖層    （Block 關聯複製用）                 進 R2B 集合，先清再重建

Objects   RBObjects                 models/R2B_Objects_時戳.3dm          Import Objects
選取物件  先選取再匯出              每次新檔、不覆蓋                     選檔匯入，累加、不賦材質

Camera    RBCamera（自動開／關）    live/camera.json                     Camera Auto On／Off
相機      RBCameraPush（推一次）                                         Push Once

Light     RBLight（自動開／關）     live/light.json                      Light Auto On／Off
燈光      RBLightPush（推一次）     只同步燈點位置                       Sync Lights
          來源：R2B_LT_Points 子層                                       依名稱配對燈與燈具模板

Open      RBOpen                    （不寫交換檔）                       Open / Health
健康檢查  顯示路徑與各通道                                               Open Docs
          最後成功時間
```

---

## 三、安全發布：寧可不更新，也不留半套

```
手動發布（Models、Objects、Push 一次）

  [寫入 pending 檔] --> [驗證內容] --> [原子替換成正式檔] --> 完成
          |                  |
          +---- 失敗／取消 --+--> 正式檔（last-good）完全不動，來源 .3dm 狀態還原

自動同步（Camera、Light 開啟自動時）

  [視角或燈點有變] --> [直接覆蓋同一個 JSON]      內容沒變就不寫
                                |
                                v
  Blender 計時器定時讀檔 --> 解析成功且套用成功，才記為「已套用」
                             半寫或讀不懂的檔 --> 不套用、不更新狀態

共同規則：工作檔沒存檔就不發布；空範圍直接擋住，不假裝成功。
```

---

## 四、程式分層（`wip/src/`）

```
+--------------------------------------------------------------------------+
| Rhino 端  src/rhino/
|
|   entrypoints/   每支指令一個檔（RBModels.py …），只轉交
|        |
|        v
|   commands/      各通道的實際流程
|                  models／model_export  主模型
|                  objects               選取物件
|                  camera／light         相機、燈光
|                  open                  健康檢查
|        |
|        v
|   platform/      碰 Rhino 的動作集中在這裡
|                  collect  依圖層收集物件 ID（不用 _SelAll）
|                  guard    執行前快照、結束後一律還原來源文件
|                  state    快照的資料格式
|                  live     真正連 Rhino 的執行環境
|                  memory   不需 Rhino 的替身，給自動測試用
|   ui/            layer_picker 階層圖層樹選擇視窗
+--------------------------------------------------------------------------+
                  |
                  v  兩端都用得到的「資料格式與安全寫檔」
+--------------------------------------------------------------------------+
| 共用基礎  src/foundation/   （不依賴 Rhino 或 Blender，可單獨測試）
|
|   *_payload      各通道交換檔的格式：model、block、camera、light
|   *_hotpath      自動同步的判斷邏輯（沒變就不寫）：camera、light
|   atomic         安全寫檔（pending --> 正式檔）
|   paths          設定根與各交換檔路徑
|   health         健康摘要          object_stamp  物件檔時戳命名
|   box_mapping    Box Projection 節點組的資料
|   user_assets    把安裝包範本拷到「文件\LoopFlow\」
|   docs           公開說明入口網址  result／log／stub
+--------------------------------------------------------------------------+
                  |
                  v
+--------------------------------------------------------------------------+
| Blender 端  src/blender/
|
|   loopflow_r2b_sync_dev/   Sync add-on
|       model_sync    主模型與選取物件匯入
|       camera_sync   相機        light_sync   燈光
|       health_sync   Open / Health
|       box_proj      Box Projection 節點
|       import_3dm/   內嵌的轉換器 fork（只做 3DM --> Blender）
|
|   loopflow_toolbox/        ToolBox 獨立 add-on
|       features/     Export、Rename、Selection
+--------------------------------------------------------------------------+
```

---

## 五、磁碟位置與周邊

```
<已存檔 .3dm 同一層>/
  _LoopFlow_Config/loopflow_R2B/
    config.json / r2b.log         設定與紀錄
    live/camera.json              相機（另有 camera_pending.json）
    live/light.json               燈光（另有 light_pending.json）
    models/R2B.3dm                主模型（另有 R2B_pending.3dm）
    models/R2B_blocks.json        Block 關聯複製資料
    models/R2B_Objects_時戳.3dm   選取物件，每次一份

+-------------------------------+     +--------------------------------------+
| 品質把關  wip/tests/          |     | 打包  wip/packaging/
| 格式、安全寫檔、健康摘要等    |     | Rhino 端 .yak 安裝包與正式指令
| 不需要開 Rhino／Blender       |     | Blender add-on 走 GitHub 發布
+-------------------------------+     +--------------------------------------+
+-------------------------------+     +--------------------------------------+
| 上游參考  repo 根 import_3dm/ |     | 文件
| 原版轉換器，唯讀對照用        |     | wip/docs/  實作規格（本資料夾，繁中）
| 要改先複製到 wip/ 再改        |     | 根 docs/   公開使用說明（中英）
+-------------------------------+     +--------------------------------------+
```

---

## 一句話總結

Rhino 端只負責把模型、相機、燈光安全地寫成檔案，Blender 端的 Sync add-on 讀檔後交給內嵌轉換器重建場景；兩端只靠工作檔旁的 `_LoopFlow_Config/loopflow_R2B/` 溝通，任何失敗都保留上一份有效檔。ToolBox 與 Box Projection 是主鏈之外的獨立輔助。
