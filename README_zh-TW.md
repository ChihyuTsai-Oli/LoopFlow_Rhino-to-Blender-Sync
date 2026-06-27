# LoopFlow｜Rhino to Blender Sync

[▶ How it works（YouTube）](https://www.youtube.com/playlist?list=PLiJmu8T_uzJJTnDl6HLSOFZ3DimkI9bV8) · [▶ Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) · [▶ 指令說明](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/blob/main/docs/USER_GUIDE_zh-TW.md)

## 版本下載

| Blender 版本 | Release | Python |
|---|---|---|
| **5.1.x**（推薦）| [v2.0.0](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases/tag/v2.0.0) | 3.13 |
| 4.5.x | [v1.0.0](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases/tag/v1.0.0) | 3.11 |

## 主要功能

- **模型同步** — 一鍵匯出乾淨 3dm；Blender 可隨時更新模型、維持既有材質
- **相機同步** — 將 Rhino 的相機視角同步至 Blender
- **燈光對齊** — Rhino Points 位置同步，Blender 根據點位將燈光、燈具自動對齊

## 材質同步原理

主要功能是同步模型，不管同步幾次都可保持材質不斷連。透過 import_3dm addon 直接讀取 Rhino 檔案，我做了一個匯出機制，可以在 Rhino 作業中的任何狀態下，一鍵匯出專門給 Blender 使用的乾淨模型，在 Blender 中同樣一鍵匯入。就這樣，很簡單。

## 模組化設計

所有同步功能各自獨立，你可以只使用模型同步、或是只同步燈光等，這之間沒有連續的流程，自由選擇需要同步的項目即可，沒有限制。

## 為什麼是 Blender？

開源，表示他是免費的。而且這是一個操作手感很好的軟體，原生 Render 引擎 Cycles 的表現力也相當足夠，並且擁有多到數不清的資源跟社區支持。

## 安裝方式

請參閱 **[Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases)** 的逐步安裝說明。

## 也許你還有興趣

- [LoopFlow｜Half-automatic 2D/3D Sync](https://github.com/ChihyuTsai-Oli/LoopFlow)
- [LoopFlow｜Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync)

## 致謝

- **LoopFlow_import_3dm** 基於 [Nathan Letwory (jesterKing)](https://github.com/jesterKing) 的 [import_3dm](https://github.com/jesterKing/import_3dm) 專案 Fork 而來，採 MIT 授權

---

*最後更新：2026 年 6 月*
