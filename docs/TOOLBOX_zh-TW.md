# LoopFlow ToolBox

[English](./TOOLBOX.md)

獨立的 Blender add-on（**1.0.0**）。不是 Rhino 同步，**不**含在 R2B 的 `.yak` 裡。

N 面板：標籤 **LoopFlow**，bar **ToolBox**。畫面按鈕為英文；本頁為正體中文。

Rhino to Blender Sync 的說明見 [使用說明入口](./README.md)。

## 下載與安裝

zip 上架後請從固定 tag 下載，**不要**用這個 repo 的 [latest Release](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases/latest)（那是 R2B 同步產品）：

- Tag：[`toolbox-1.0.0`](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases/tag/toolbox-1.0.0)
- 檔名：`loopflow_toolbox-1.0.0.zip`

**目前此 tag 尚未發布。** 上架前請用開發打包：`wip/tools/pack_toolbox.ps1`。

1. Edit → Preferences → Add-ons → **Install from Disk**（不要用 Get Extensions）
2. 只選上述 zip
3. 列表勾選 **LoopFlow ToolBox**
4. 不要與舊版 **LoopFlow Toolkit** 同時當正式專案使用

與 Sync 可同時啟用：同一個 LoopFlow 標籤會看到 **Rhino to Blender Sync** 和 **ToolBox**。請在 **OBJECT** 模式操作。

## Export Tools

把場景**頂層 Collection** 各出一份 `.usdz`。匯出前會把該 Collection 的根物件移到世界原點，出完還原位置與顯隱。沒有幾何的 Collection 會略過。

- **Export All to USD**：每個頂層 Collection 各一份
- 勾選清單 + **All**／**None** + **Export Selected to USD**：只出勾選的

未勾選就按 Selected：會報錯、不開資料夾。中途失敗時位置可能未還原，用 Ctrl+Z。

## Rename Tools

- **Rename Collections**：批次改 Outliner 裡選到的 Collection 名稱（也可從選中物件推回），並打開 Render。對話框填底名；作用中那一個不加後綴，其餘 `_001` 起。
- **Rename Objects by Collections**：用 Collection 名稱當底幫裡面物件編號。`Alt+D` 共用網格會加 `_Ins`；Mesh 資料名稱一併改。
- **Rename Objects**：不管層級，依平面位置從左下編號（先 +Y 再 +X）。作用中物件當主名、排第一、不加後綴；同樣有 `_Ins`。

沒選到 Collection 或物件時不會改名。

## Selection Tools

- **Group**：最後點的 Mesh 當錨點，選中的 Mesh 掛到其下，並對到**同名** Collection（沒有就建）。空的舊 Empty 父與空 Collection 會刪。
- **Un-Group**：選任一成員，整組解除親子；根若是 Empty 則刪根。世界座標保留。
- **Re-Group**：作用中 Mesh 當最終錨點；套用 Armature 後打平，掛進 `COL_FINAL_{錨點名}`。選中的 Empty／Armature 會刪。
- **Select All in Group**：選任一成員，整條層級一起選。
- **Delete Objects From Group**：刪作用中父物件，子物件留下。
- **Material Isolator**：選中 Mesh 的材質改成物件獨立一份（名稱加 `_Unique`），方便 `Alt+D` 實例用不同材質。之後在 Properties → Material 把 Link 設成 Object。
