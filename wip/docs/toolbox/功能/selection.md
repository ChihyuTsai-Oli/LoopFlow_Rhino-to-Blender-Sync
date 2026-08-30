# 功能：selection

相依：無。`COL_FINAL_*` 僅 Re-Group 使用。

請在 OBJECT 模式。主要輸入：`active_object`、`selected_objects`。世界座標在改 parent 時要先存再寫回。

## 按鈕（英文原文）

| 按鈕 | operator |
|---|---|
| Group | `loopflow_toolbox.group` |
| Un-Group | `loopflow_toolbox.un_group` |
| Re-Group | `loopflow_toolbox.re_group` |
| Select All in Group | `loopflow_toolbox.select_all_in_group` |
| Delete Objects From Group | `loopflow_toolbox.delete_objects_from_group` |
| Material Isolator | `loopflow_toolbox.material_isolator` |

## Group

- 最後點的 Mesh＝錨點。選中 Mesh 掛到其下，並對到**同名** Collection（沒有就建、掛到場景）。
- 空的舊 Empty 父與空 Collection 會刪（不刪場景根）。

## Un-Group

- 選任一成員；追到根，子物件全部解除親子。根若是 Empty 則刪根。

## Re-Group

- 作用中 Mesh＝最終錨點。套用選中 Mesh 上的 Armature modifier，打平層級，掛進 `COL_FINAL_{錨點名}`。刪選中的 Empty／Armature。

## Select All in Group

- 選任一成員，整條層級一起選。

## Delete Objects From Group

- 刪作用中父物件；子物件解除親子並留下。空 Collection 刪除。

## Material Isolator

- 選中 Mesh 的材質槽改 `link = OBJECT`，並 `copy()` 一份名稱加 `_Unique`。
- 之後若還要獨立編輯，Properties → Material → Link 應為 Object。
