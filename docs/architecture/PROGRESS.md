# LoopFlow Rhino-to-Blender Sync 3.0 重構進度

- 建立日期：2026-08-12
- 目標版本：`v3.0.0`
- 整合分支：`v3-development`
- 建立基準：`main` / `35bcd5d115b8f835f8023fac21634b2162c3873a`
- 穩定回復點：`v2.0.0` / `48d554f2f6a844cf2d5fa07e5fd02c46ea0ea71c`
- 狀態：重構模式已定案；命名與跨程式資料契約待完整盤點；尚未修改產品程式碼

## AI 接手入口

本 repo 已建立自足的繁中維護文件。AI 開始前依序讀取根目錄 `AGENTS.md`、`docs/_R2B_使用說明.md`、`docs/_R2B_系統設定.md`、`docs/_R2B_命名與資料契約.md`、`docs/_R2B_重構計畫.md`，最後讀本文件確認即時進度。外部分析檔不再是必要輸入。

## Release 回復資產

| 項目 | 值 |
|---|---|
| 檔案 | `LoopFlow_R2B_v2.0.0.zip` |
| 大小 | 2,449,603 bytes |
| ZIP 項目數 | 9 |
| SHA-256 | `78967bb2ab7f416901355e551548910b5b371ace97b31f8bde48c2acdafcc972` |

此 ZIP 已能正常開啟，並與 GitHub `v2.0.0` Release 資產的大小一致。既有 `v2.0.0` tag 與 Release 不移動、不重用；本輪破壞性重構固定以 `v3.0.0` 發布。

## 分支規則

- `main`：3.0 正式發布前維持可發布的 2.x。
- `v3-development`：3.0 的唯一整合線。
- 每批工作從 `v3-development` 建立 `codex/v3-<scope>` 短期分支，檢查通過後才合入。
- `main` 原則上凍結，僅在使用者明確要求維護 2.x 時，才另開獨立 hotfix 分支並將必要修正同步至 `v3-development`。
- `v3.0.0` 只在 RC 與 Rhino / Blender 實機驗收完成、合回 `main` 後建立。
- `1.x` 歷史維護分支保持不動，除非另有明確修補需求。

## Golden workflow 基準

合約盤點期間，先從穩定版與既有範例整理可自動比對的 fixture、預期輸出與必要畫面基準。新版主要工作流串接完成後，再使用隔離的 Rhino 8、Blender、測試 `.3dm` 與輸出目錄，依下列清單進行完整實機端到端驗證：

- Models：已儲存／未儲存文件、明確物件集合、取消、匯出失敗與最後有效 3DM。
- Camera：Rhino producer、Blender consumer、座標／焦距與重複同步。
- Light：類型、能量、顏色、命名與重複同步。
- Blender integration：安裝、registration、timer/state、operators、panels 與解除安裝。
- `import_3dm` fork：代表性 3DM fixtures、instances、layers、materials、views 與 wheel / ABI。
- Toolkit：安裝、啟用、停用與既有操作；3.0 核心重構期間不擴充功能。

fixture 與預期結果應在對應功能建造前完成；實機結果則在主要工作流串接後集中補入本文件。未驗證項目不得標記為通過。

## 第一階段順序

1. 盤點完整 Rhino → 檔案／schema → Blender 工作流，以及所有命名與版本相依點。
2. 完成指令、設定、檔名、資料夾、JSON schema、Blender ID、fork 邊界與版本契約。
3. 固定 fixture、預期輸出、schema version 與舊專案轉換邊界；舊名稱只由獨立遷移工具辨識。
4. 建立新版 Rhino 與 Blender 最小架構，先驗證 import、registration、reload 與安裝隔離。
5. 契約確認後，依 Models → Camera → Light → Blender consumer 的真實操作順序接入功能並同步建立自動化與契約測試。
6. 主流程串接完成後，集中進行 Rhino／Blender 實機端到端測試，再完成 Toolkit 邊界、遷移工具、安裝包與 RC。

## 驗證紀錄

| 日期 | 分支 / commit | 檢查 | 結果 | 限制 |
|---|---|---|---|---|
| 2026-08-12 | `v3-development` 建立基準 | Git 同步、Release ZIP 完整性與 SHA-256、21 支 Python 靜態語法、RHC XML | 通過 | Blender CLI 不在 PATH；Rhino / Blender 實機流程由後續批次逐項驗證 |
| 2026-08-12 | 文件 SSOT 建置 | 建立繁中使用說明、系統設定、重構計畫與 repo AI 規則；Markdown 本機連結檢查 | 通過 | 第一方註解依 feature 批次遷移；第三方 fork 原文與授權保留 |
| 2026-08-12 | 重構模式裁決 | 新版乾淨重建、一次切換；命名與跨程式資料契約先於程式架構 | 通過 | 尚未開始命名盤點與產品程式碼修改 |

## 下一步

從 `v3-development` 建立 `codex/v3-naming-contract`，先盤點整套工作流及所有指令、設定、檔名、JSON schema、Blender ID、fork 與版本名稱。使用者確認契約前，不開始正式功能程式碼。
