# LoopFlow Rhino-to-Blender Sync 3.0 重構進度

- 建立日期：2026-08-12
- 目標版本：`v3.0.0`
- 整合分支：`v3-development`
- 建立基準：`main` / `35bcd5d115b8f835f8023fac21634b2162c3873a`
- 穩定回復點：`v2.0.0` / `48d554f2f6a844cf2d5fa07e5fd02c46ea0ea71c`
- 狀態：隔離整合線與繁中維護文件 SSOT 已建立；尚未修改產品程式碼

## AI 接手入口

本 repo 已建立自足的繁中維護文件。AI 開始前依序讀取根目錄 `AGENTS.md`、`docs/_R2B_使用說明.md`、`docs/_R2B_系統設定.md`、`docs/_R2B_重構計畫.md`，最後讀本文件確認即時進度。外部分析檔不再是必要輸入。

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
- 2.x 的 P0 修復從 `main` 開獨立 hotfix 分支，發布後再同步至 `v3-development`。
- `v3.0.0` 只在 RC 與 Rhino / Blender 實機驗收完成、合回 `main` 後建立。
- `1.x` 歷史維護分支保持不動，除非另有明確修補需求。

## Golden workflow 基準

開始修改對應功能前，使用隔離的 Rhino 8、Blender、測試 `.3dm` 與輸出目錄，記錄以下現行結果：

- Models：已儲存／未儲存文件、明確物件集合、取消、匯出失敗與最後有效 3DM。
- Camera：Rhino producer、Blender consumer、座標／焦距與重複同步。
- Light：類型、能量、顏色、命名與重複同步。
- Blender integration：安裝、registration、timer/state、operators、panels 與解除安裝。
- `import_3dm` fork：代表性 3DM fixtures、instances、layers、materials、views 與 wheel / ABI。
- Toolkit：安裝、啟用、停用與既有操作；3.0 核心重構期間不擴充功能。

實機結果與 fixture 路徑必須在相關批次開始前補入本文件；未驗證項目不得標記為通過。

## 第一階段順序

1. Models P0：明確 object IDs、不 `_SelAll`、不丟未存修改、pending 驗證後才發布。
2. Rhino bootstrap / command catalog / foundation 與 Models 垂直切片。
3. Camera / Light schema 與 atomic producer / consumer state。
4. Blender registration、UI、sync 分層。
5. fork upstream、patch、fixtures 與 integration 邊界。

## 驗證紀錄

| 日期 | 分支 / commit | 檢查 | 結果 | 限制 |
|---|---|---|---|---|
| 2026-08-12 | `v3-development` 建立基準 | Git 同步、Release ZIP 完整性與 SHA-256、21 支 Python 靜態語法、RHC XML | 通過 | Blender CLI 不在 PATH；Rhino / Blender 實機流程由後續批次逐項驗證 |
| 2026-08-12 | 文件 SSOT 建置 | 建立繁中使用說明、系統設定、重構計畫與 repo AI 規則；Markdown 本機連結檢查 | 通過 | 第一方註解依 feature 批次遷移；第三方 fork 原文與授權保留 |

## 下一步

開始 Models P0 時，從 `v3-development` 建立 `codex/v3-models-p0`；不在整合分支直接進行未分批的大型改寫。
