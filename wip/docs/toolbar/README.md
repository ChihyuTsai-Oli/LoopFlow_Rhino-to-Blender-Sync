# 產品工具列與 Package Manager 圖示

把 `ExportRuiFile` 匯出的 `.rui` 與清單圖示 `icon.png` 放在這裡，建置時由 `wip/packaging/g02-spike/build.ps1` 複製進 yak。

正式工具列分頁是 **LoopFlow R2B**。四顆鈕懸停（左鍵／右鍵）：R2B Config／R2B Model（按鈕面 R2B Models）+R2B Objects／R2B Camera+R2B Camera Push／R2B Light+R2B Light Push。

RUI 需要一個 `tool_bar_group`（顯示名 `LoopFlow R2B`，與分頁相同）。不要寫入 `SelectedToolbarSet`。不要改 GUID。Package Manager 圖示檔名 `icon.png`。
