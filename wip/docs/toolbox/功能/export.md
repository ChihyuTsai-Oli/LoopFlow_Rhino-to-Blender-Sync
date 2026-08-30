# 功能：export

相依：無。卸載本模組後，Rename／Selection 仍可用。

## 按鈕（英文原文）

| 按鈕 | operator |
|---|---|
| Export All to USD | `loopflow_toolbox.export_all_usd` |
| All／None | `loopflow_toolbox.select_all_cols` |
| Export Selected to USD | `loopflow_toolbox.export_selected_usd` |

清單：場景頂層 Collection；勾選屬性 `loopflow_toolbox_export_selected`。

## 行為

1. 選輸出資料夾。
2. 每個目標 Collection 各出一份 `{安全檔名}.usdz`（`wm.usd_export`：無動畫、含 UV／法線／材質、instancing、只可見物件）。
3. 匯出前：隱藏其他頂層 Collection；把該 Collection 內無父（或不在同一批裡）的根物件移到世界原點。
4. 匯出後：還原位置與顯隱。
5. 無 MESH／CURVE／SURFACE／META／FONT 則略過該 Collection。

## 失敗

- 未勾選任何 Collection：報錯，不開資料夾。
- 中途例外：位置可能未還原 → 使用者 Undo。

## 卸載

必須 `del Collection.loopflow_toolbox_export_selected`。
