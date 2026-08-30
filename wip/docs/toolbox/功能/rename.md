# 功能：rename

相依：無。`_Ins` 僅本模組使用，同步主鏈不讀。

## 按鈕（英文原文）

| 按鈕 | operator |
|---|---|
| Rename Collections | `loopflow_toolbox.rename_collections` |
| Rename Objects by Collections | `loopflow_toolbox.rename_objects_by_collections` |
| Rename Objects | `loopflow_toolbox.rename_objects` |

## Rename Collections

- 輸入：Outliner 選中的 Collection（跨視窗）；不足則用選中物件所屬 Collection 或作用中 Layer Collection。
- 對話框填 Base Name。作用中 Collection 當第一個、無後綴；其餘 `_001` 起。
- 同時 `hide_render = False`。
- 快取名稱用 `|||` 分隔；Collection 名不要含此字串。

## Rename Objects by Collections

- 以 Collection 名稱當底，幫裡面物件編號。
- `obj.data.users > 1` 視為實例：`{名}_Ins`、`{名}_Ins.001`…；其餘 `{名}`、`{名}.001`…。
- Mesh 資料名稱與物件對齊（同一 data 只改一次）。

## Rename Objects

- 選中物件；作用中物件當主名、排第一、不加後綴。
- 其餘依 `round(x, 3)` 再 `y`（左下起、先 +Y 再 +X；X 約 1mm 容差）。
- 同樣套用 `_Ins` 雙計數與 data 改名。

## 失敗

- 沒選到 Collection／物件：WARNING，不改名。
