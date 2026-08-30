# LoopFlow｜Rhino to Blender Sync

> 3.0 公開說明初稿（`wip/docs/readme/`）。尚未取代 repo 根目錄的 2.x 文件。英文尚未撰寫。

[2.x English homepage](../../../README.md)

> 把 Rhino 的模型、相機與燈光點位，單向同步到 Blender。

3.0 是重建，不是 2.x 的修補版。Rhino 端裝一份 `.yak`；Blender 端另裝 Sync add-on（內含 3dm 匯入）。同一專案不要混用 2.x 與 3.0。

[▶ 使用說明](./README.md) · [▶ Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) · [▶ 教學影片](https://www.youtube.com/playlist?list=PLiJmu8T_uzJJTnDl6HLSOFZ3DimkI9bV8)

## 主要功能

- **模型同步** — 從作業中的 Rhino 檔匯出乾淨 3dm；Blender 可更新幾何並維持既有材質
- **選取物件** — 把目前選取匯成另一份無材質 3dm，像 FBX 一樣累加進場景
- **相機同步** — 將 Rhino 作用視角同步到 Blender
- **燈光對齊** — Rhino 燈光圖層上的 Point 位置，用來對齊 Blender 裡預先準備的燈與燈具
- **Box Projection** — Shader Editor 裡載入 PBR 貼圖、世界／物件座標，不寫 UV

各通道彼此獨立，不必照固定順序一次做完。

## 與 2.x 的差異

- 3.0 是重建；指令改為 `RBModels`、`RBOpen` 等連寫名稱，不是舊的 `R2B_Models`
- 設定改放在已存檔 `.3dm` 旁的 `_LoopFlow_Config/loopflow_R2B/`，不再用 AppData 的 `R2B_Path.txt`
- Blender 只要裝 Sync add-on；**不必**再裝獨立的 Import Rhinoceros 3D 或 2.x 的 `LoopFlow_import_3dm`
- Rhino 套件只含 Rhino；Blender 不進 `.yak`
- 同一專案、同一套按鈕不要混用 2.x 與 3.0

## 系統需求

- **Rhino 8**（Windows）
- **Blender 5.2.1**（3.0 目標版本）

Rhino 對話框與 Blender 面板為英文；本說明為正體中文。

## 快速開始

教學影片尚未全部改為 3.0。

### 安裝

不要用 2.x 的解壓腳本或舊工具列。

**Rhino**

1. 開啟 Rhino 8，命令列執行 `PackageManager`
2. 正式上架後搜尋畫面名 **`loopflow Rhino to Blender Sync`**
3. 或從 [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) 下載 `.yak`，在 Package Manager 選擇從檔案安裝
4. **完全關掉 Rhino 再開**
5. 使用工具列 **Rhino to Blender Sync**；不要按 2.x 按鈕

3.0 正式上架前，請用本機／GitHub 提供的 `.yak` 從檔案安裝，不要搜尋到 2.x 就裝上去混用。

**Blender**

1. 安裝本 repo 的 Sync add-on（內含 3dm 匯入）
2. 啟用後，3D 視窗 N 面板標籤 **LoopFlow**、bar **Rhino to Blender Sync**
3. 不要再啟用獨立的「Import Rhinoceros 3D」

完整步驟與按鈕說明見 [使用說明](./README.md)。

## 基本工作流程

1. 把 `.3dm` 存檔（未存檔則無法發布）
2. `RBOpen` 確認設定資料夾與各通道上次成功時間
3. 需要模型時跑 `RBModels`（有材質）或 `RBObjects`（選取、無材質）
4. 需要相機或燈光時再開自動同步，或手動推一次
5. Blender 把作業資料夾指到與 `.3dm` 同一層，再按對應的 Sync／Update／Import

每一步都要自己按。走錯就停在該通道重跑，不必推翻整場。

## 支援與回報

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/discussions)：提問與使用經驗
- [Issues](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/issues)：回報錯誤或建議
- [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases)：已發布版本

LoopFlow 是由建築及室內設計師從實際工作中發展的單人專案。程式開發與文件整理使用 AI 協助；工作流程需求、設計決策與實務驗證仍以作者本人的專業經驗為基礎。

維護與回覆速度會依工作狀況調整。

## 相關專案

- [LoopFlow｜Half-automatic 2D/3D Sync](https://github.com/ChihyuTsai-Oli/LoopFlow/blob/main/README_zh-TW.md)
- [LoopFlow｜Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync/blob/main/README_zh-TW.md)

## 授權與致謝

本專案採用 [MIT License](../../../LICENSE) 發布。開發背景與致謝請參考 [CREDITS](./CREDITS.md)。
