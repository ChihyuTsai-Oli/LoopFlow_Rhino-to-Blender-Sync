# LoopFlow｜Rhino to Blender Sync

> 同一專案不要混用舊版的工具列、套件或 Blender add-on。

> 把 Rhino 的模型、相機與燈光點位，單向同步到 Blender。

Rhino 端裝一份 `.yak`（內含 Blender Sync zip）。第一次跑任一 Rhino 指令後，zip 會拷到「文件\LoopFlow\Rhino to Blender Sync」。

[▶ 使用說明](./docs/README.md) · [▶ Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) · [▶ 教學影片](https://www.youtube.com/playlist?list=PLiJmu8T_uzJJTnDl6HLSOFZ3DimkI9bV8)

## 主要功能

- **模型同步** — 從作業中的 Rhino 檔匯出乾淨 3dm；Blender 可更新幾何並維持既有材質
- **選取物件** — 把目前選取匯成另一份無材質 3dm，像 FBX 一樣累加進場景
- **相機同步** — 將 Rhino 作用視角同步到 Blender
- **燈光對齊** — Rhino 燈光圖層上的 Point 位置，用來對齊 Blender 裡預先準備的燈與燈具
- **Box Projection** — Shader Editor 裡載入 PBR 貼圖、世界／物件座標，不寫 UV

各通道彼此獨立，不必照固定順序一次做完。

## 系統需求

- **Rhino 8**（Windows）
- **Blender 5.2.1**（開發環境）

Rhino 對話框與 Blender 面板為英文；本說明為正體中文。

## 快速開始

教學影片尚未全部更新。

### 安裝

**Rhino**

1. 開啟 Rhino 8，命令列執行 `PackageManager`
2. 正式上架後搜尋畫面名 **`loopflow Rhino to Blender Sync`**
3. 或從 [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) 下載 `.yak`，在 Package Manager 選擇從檔案安裝
4. **完全關掉 Rhino 再開**
5. 使用工具列 **Rhino to Blender Sync**

尚未上架時，請用本機／GitHub 提供的 `.yak` 從檔案安裝。

**Blender**

請走 **Edit → Preferences → Add-ons → Install from Disk**（傳統 Add-ons），不要用 Extensions。

1. 若列表裡已有 **import_3dm** 或 **LoopFlow Rhino to Blender Sync**／**loopflow_r2b_sync**，先移除或停用
2. **完全關掉 Blender**。若 Portable 裝在 Dropbox 上，先暫停 Dropbox
3. 刪掉殘留資料夾（有哪個刪哪個）：
   - `portable\extensions\user_default\loopflow_r2b_sync`
   - `portable\extensions\user_default\loopflow_r2b_sync@`
   - `portable\scripts\addons\loopflow_r2b_sync`
4. 在 Rhino 跑一次任一產品指令，讓新版 zip 拷到「文件\LoopFlow\Rhino to Blender Sync」
5. 再開 Blender，**Install from Disk** 只選該資料夾裡的 **zip**（不要選資料夾）
6. 在 **Add-ons** 列表找到 **LoopFlow Rhino to Blender Sync** 並勾選啟用；N 面板標籤 **LoopFlow**、bar **Rhino to Blender Sync**
7. 不必再啟用獨立的「Import Rhinoceros 3D」

若仍出現「檔案正由另一個程序使用」：確認 Blender 已關、Dropbox 已暫停，再刪殘留資料夾後重裝。

完整步驟與按鈕說明見 [使用說明](./docs/README.md)。

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

本專案採用 [MIT License](./LICENSE) 發布。開發背景與致謝請參考 [CREDITS](./CREDITS.md)。
