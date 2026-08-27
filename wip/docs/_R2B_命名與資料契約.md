# LoopFlow R2B — 命名與資料契約

本文件是 R2B 3.0 的指令、設定、schema、Blender 識別字與跨軟體資料契約權威來源。程式架構建立前先完成盤點與裁決。

## 狀態

- 階段：**準備盤點／決策確認中**
- 套用版本：R2B `v3.0.0`
- 舊版參考：`v2.0.0`
- 原則：3.0 核心只使用新契約；舊版相容留在獨立 migration／import 邊界
- **尚待確認事項的唯一來源**：`前期規劃/資料生態決策表.md`（確認前不要在本檔填 canonical 當成已定案）
- 開發期 Rhino 指令與按鈕巨集：`rhino指令.md`

## 核心裁決

- Rhino producer、Blender integration、`import_3dm` fork、Toolkit 各自有清楚 namespace。
- 3.0 不在核心散落 v2 alias、雙寫欄位或臨時 wrapper。
- 既有正式 v2 安裝與資料保持不動；3.0 使用隔離 scripts、data、RHC、Blender profile 與 package ID。
- 外部 operator ID、property、collection、檔名與 schema 若改變，必須列入 migration／release notes。
- **設定與即時檔路徑已定**：工作檔所在資料夾的 `_LoopFlow_Config/loopflow_R2B/`。父資料夾 `_LoopFlow_Config` 與 LoopFlow／R2O／QTY 共用，產品各用自己的子資料夾。已發布 2.x 的 AppData `Data\` 保持不動，3.0 一次切換。
- 第三方 fork 的 upstream 名稱與授權不為統一風格任意改寫。

## 必須盤點的命名層級

| 層級 | 範圍 |
|---|---|
| Rhino commands | Models、Camera、Light、Open／Config 的顯示名稱與 command ID |
| Config | `R2B_Path.txt` 欄位、預設、型別與使用者可調範圍 |
| Files | 3DM、Camera／Light JSON、log、pending 與 last good |
| JSON schema | version、producer、session、payload、成功條件 |
| Blender API | operator ID、panel、property、timer／state key |
| Collections／objects | `_Ins`、`COL_FINAL_`、`_Unique` 等命名規則 |
| Importer | 第一方 integration、upstream converter、vendor binary namespace |
| Toolkit | registration、operator、panel 與 service namespace |
| Version／build | `bl_info`、manifest、ZIP、ABI、package ID |

## 依賴盤點格式

| 現行名稱 | 意義 | Producer | Consumer | 儲存／註冊位置 | 衝突／問題 | 3.0 canonical 名稱 | 遷移方式 | 狀態 |
|---|---|---|---|---|---|---|---|---|
| 待盤點 |  |  |  |  |  |  |  | 未定案 |

## 跨軟體 schema 規則

- Camera／Light／Models 都有獨立 schema version。
- 欄位定義包含型別、單位、座標系、必要值、空資料與 error stage。
- Blender consumer 只有 parse + apply 成功才更新 state。
- 3DM 檔案的可讀性與 importer version 是 Models 成功條件的一部分。
- Python producer 與 Blender consumer 使用同一組 fixtures。

## Blender 識別字規則

- operator ID、property name、collection／object naming 分開定義，不共用模糊縮寫。
- 對使用者顯示的 label 可用自然語言；程式 ID 使用穩定英文名稱。
- 第一方 integration 不直接依賴 upstream converter 內部名稱；由唯一 importer boundary 轉接。
- binary／ABI 名稱由 build 產生或驗證，不手動散落於 README、manifest 與程式。

## v2 → v3 遷移邊界

若需升級既有設定／Blender scene，使用獨立 scanner／migration：

```text
掃描 v2 設定與場景識別字
→ 顯示將變更的檔案、property、collection 與 package
→ 備份
→ 一次轉換
→ 以 v3 validator／fixtures 驗證
→ 失敗回復
```

3.0 一般同步指令不長期讀寫 v2 與 v3 兩套資料。

## 定案門檻

- 四個產品邊界與 namespace 完成。
- 所有跨軟體欄位有 producer／consumer、型別、單位與成功條件。
- operator／property／collection／檔名的使用者影響已確認。
- schema、fixtures、version、ABI 與 migration 範圍完成。
- `_R2B_系統設定.md` 與 `_R2B_重構計畫.md` 已同步。

完成後才建立 3.0 bootstrap、command catalog 與新 source layout。
