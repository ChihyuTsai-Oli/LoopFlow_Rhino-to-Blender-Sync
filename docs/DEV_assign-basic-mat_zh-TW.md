# 重新設計 Auto Basic Material Assigner

目標檔案：`releases/LoopFlow_import_3dm/__init__.py`

## 背景

原版本以硬寫的 `5_LT`、`Preset_Lighting_K` 等個人命名慣例驅動，不適合公開發布。新版改為三個 N Panel 欄位，使用者自行定義，無任何命名假設。

---

## N Panel 新增欄位

```
Prototype Object   : [_______________]   ← r2b_mat_source_obj   (StringProperty)
Light Source Object: [_______________]   ← r2b_light_source_obj (StringProperty)
Light Collection   : [_______________]   ← r2b_light_col        (StringProperty)
                   [Assign Basic Mat.]
```

- 三個欄位皆可在 Outliner / 場景中點選物件或 Collection，或手動輸入名稱
- 三個欄位皆為選填，使用者可只用其中部分功能

---

## 執行邏輯（兩階段，有明確先後順序）

### Phase 1 — 發光材質（Field 2 + Field 3）

**先執行**，確保 Field 3 物件在 Phase 2 前就已蓋章。

- 從 `r2b_light_source_obj` 指定的物件取第一個 material slot 作為發光材質來源
- 對 `r2b_light_col` 指定 Collection 內所有物件：
  - 若物件已有 object-level 自訂屬性 `r2b_light_stamped = True` → **跳過**（保留使用者手動編輯的材質）
  - 否則：替換所有 material slot 為發光材質副本，並在物件上寫入 `r2b_light_stamped = True`

### Phase 2 — 一般材質（Field 1）

- 從 `r2b_mat_source_obj` 指定的物件掃描所有 material slot，每個材質名稱作為關鍵字
- 全場景掃描所有材質（`bpy.data.materials`）：
  - 已有 `r2b_auto_assigned = True` 的材質 → **跳過**
  - 屬於 `r2b_light_col` Collection 內物件的材質 → **跳過**（Field 3 物件完全交由 Phase 1 處理）
  - 材質名稱包含任一關鍵字（不分大小寫）→ 替換為原型材質副本，寫入 `r2b_auto_assigned = True`
  - 多關鍵字時優先比對較長的（避免 `Wood` 誤中 `Plywood`）

---

## 蓋章機制對照

| 對象 | 蓋章位置 | 蓋章屬性 | 作用 |
|---|---|---|---|
| 一般材質（Phase 2） | material 自訂屬性 | `r2b_auto_assigned = True` | 重複執行不覆寫 |
| 發光材質（Phase 1） | object 自訂屬性 | `r2b_light_stamped = True` | 保留使用者手動編輯 |

蓋章位置的差異原因：Phase 1 蓋在物件層級，是因為使用者手動更換材質後，原材質物件已消失，蓋在材質上的印記會失效；蓋在物件上則無論材質怎麼換都能保住。

---

## 需要改動的程式碼

### 移除舊版硬寫常數（lines 89、91–94）

```python
# 移除以下四個常數
COL_MATERIALS   = "Materials"
MAT_PRESET_LT_K = "Preset_Lighting_K"
LAYER_SUFFIX_LT = "5_LT"
MAT_AUTO_5LT    = "Auto_5LT_Light"
```

### 新增三個 Scene property（register() 內）

```python
bpy.types.Scene.r2b_mat_source_obj   = bpy.props.StringProperty(name="Prototype Object")
bpy.types.Scene.r2b_light_source_obj = bpy.props.StringProperty(name="Light Source Object")
bpy.types.Scene.r2b_light_col        = bpy.props.StringProperty(name="Light Collection")
```

並在 `unregister()` 中對應新增：

```python
del bpy.types.Scene.r2b_mat_source_obj
del bpy.types.Scene.r2b_light_source_obj
del bpy.types.Scene.r2b_light_col
```

### 整體改寫 RHINO_OT_AssignBasicMat class（lines 355–475）

移除舊版 comment 掉的程式碼，依照上述兩階段邏輯全部重寫。

### 在 Panel draw 方法新增欄位與按鈕（line 714）

取消 comment 的按鈕同時，在其上方新增三個 `prop` 欄位。

### 在 classes tuple 加入新 class（line 723）

取消 `# RHINO_OT_AssignBasicMat,` 的 comment。

### 更新 docstring（檔案頂部 lines 40–50）

更新 Auto Basic Material Assigner 的說明段落，描述新的三欄操作方式。

---

## 使用者操作說明

- **Rhino 端**：把所有燈具物件放在同一個圖層，匯出後在 Blender 中成為同一個 Collection，填入 Light Collection（Field 3）
- **Blender 端**：準備兩個物件——一個掛所有一般材質原型（Field 1）、一個掛單一發光材質（Field 2）
- 第一次執行 **[Assign Basic Mat.]** 後，可手動進入各燈具物件修改發光材質細節
- 之後再次執行 **[Assign Basic Mat.]** 時，已手動編輯的燈具材質不會被覆蓋
