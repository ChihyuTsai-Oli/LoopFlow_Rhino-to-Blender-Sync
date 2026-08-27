# import_3dm 上游參考（唯讀）

本目錄存放 **Nathan Letwory（jesterKing）** 的 Blender `import_3dm` 發行物，供 R2B 3.0 開發當**乾淨基準**。

## 目前基準

- 目錄：`import_3dm-0.0.18-windows_x64/`
- 壓縮包：`import_3dm-0.0.18-windows_x64.zip`
- Manifest：`version = "0.0.18"`，`id = "import_3dm"`

## 使用規則

1. **不要修改**本目錄內檔案。
2. 實作時**複製**整個 `import_3dm-0.0.18-windows_x64` 到 `wip/` 工作複本（路徑見 `wip/docs/系統設定.md`），只在複本上改。
3. 現行 2.x 產品 fork 在 `releases/LoopFlow_import_3dm/`，僅行為對照，**不是** 3.0 上游基準。
4. 對上游的 patch 清單與基準說明於 A05 補 `UPSTREAM.md`／`PATCHES.md`（寫在工作複本或 `wip/docs`）。
