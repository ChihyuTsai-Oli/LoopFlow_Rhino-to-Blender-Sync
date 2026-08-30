# LoopFlow R2B 使用說明總覽

> 同一專案不要混用舊版的工具列、套件或 Blender add-on。
>
> 一分鐘理解怎麼運作。按鈕與逐步操作見 [指令逐項說明](./COMMANDS_zh-TW.md)。產品介紹與安裝見 [專案主頁](../README_zh-TW.md)。

## 核心邏輯：單向、分通道

**Rhino 產出，Blender 讀取。** 不會從 Blender 改回 Rhino。

1. **先把 `.3dm` 存檔。** 未存檔就不能發布。設定與交換檔都放在這份檔案旁邊，不寫死某台電腦的路徑。
2. **各通道獨立。** 模型、選取物件、相機、燈光可以分開跑，沒有必須一次做完的固定流水線。
3. **成對使用。** Rhino 的 `RBModels` 對 Blender 的 Sync／Update Models；`RBObjects` 對 Import Objects。不要交叉拿檔。

模型同步的重點是：不管更新幾次，Blender 裡已經調好的同名材質可以留下。選取物件則像 FBX，不帶材質、可累加。

## 專案以資料夾為單位

已存檔的 `.3dm` 所在資料夾就是作業資料夾。LoopFlow 會在同一層建立：

```text
_LoopFlow_Config/loopflow_R2B/
  live/      ← 相機、燈光
  models/    ← R2B.3dm、選取物件的時戳 3dm
```

Blender 的 Work Folder 請指到**與 `.3dm` 同一層**（不是指進 `_LoopFlow_Config` 裡面）。換電腦時把整個專案資料夾一起搬即可。

## 兩端怎麼對

| 你要做的事 | Rhino | Blender |
|---|---|---|
| 主模型（有材質） | `RBModels` | **Sync Models**（刷新基本材質）或 **Update Models**（幾何更新、不覆寫已有材質） |
| 選取物件（無材質） | `RBObjects` | **Import Objects**（自己選時戳 3dm） |
| 相機 | `RBCamera` 開／關；右鍵 `RBCameraPush` 推一次 | Camera Auto On／Off／Push Once |
| 燈光位置 | `RBLight` 開／關；右鍵 `RBLightPush` 推一次 | Light Auto On／Off／Sync Lights |
| 看設定與說明 | `RBOpen` | Open / Health；Open Docs |

Rhino 工具列 **Rhino to Blender Sync** 有四顆鈕：左鍵是上表主功能，右鍵是 Objects／Camera Push／Light Push。

Blender 3D 視窗 N 面板：標籤 **LoopFlow**，bar **Rhino to Blender Sync**。著色輔助在 Shader Editor 同一個標籤、bar **Box Projection**，不進同步。

## 幾個要先懂的名詞

| 名詞 | 意思 |
|---|---|
| **作業資料夾** | 已存檔 `.3dm` 所在層；Blender Work Folder 也指這裡。 |
| **Sync Models** | 重建 `R2B` 集合的幾何，並掛／更新基本 Principled 材質槽。 |
| **Update Models** | 幾何同樣重建，但**不覆寫**你已經調過的同名材質。日常多用這個。 |
| **Import Objects** | 選一份 `R2B_Objects_時戳.3dm` 累加進場景，無材質、不進 `R2B` 集合。 |
| **Health** | 設定根路徑，以及 Camera／Light／Models／Objects 上次成功寫出的時間。 |

## 失敗時會停在哪

- 未存檔：發布停止，並用英文說明。
- 匯出取消、失敗或中斷：仍在原來的工作檔；上次成功的輸出不會被半套檔蓋掉。
- 燈光圖層沒有符合的 Point：不寫檔，也不會把 Blender 裡的燈清掉。

系統不會自己往下一通道繼續跑。

## 想知道怎麼按

這一頁只講邏輯。指令列名稱、工具列左／右鍵、Blender 按鈕與燈光圖層怎麼擺，見 [指令逐項說明](./COMMANDS_zh-TW.md)。
