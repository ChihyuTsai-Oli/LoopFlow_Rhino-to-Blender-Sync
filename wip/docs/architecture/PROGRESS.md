# LoopFlow Rhino-to-Blender Sync 3.0 重構進度

- 建立日期：2026-08-12
- 目標版本：`v3.0.0`
- 整合分支：`v3-development`
- 建立基準：`main` / `35bcd5d115b8f835f8023fac21634b2162c3873a`
- 穩定回復點：`v2.0.0` / `48d554f2f6a844cf2d5fa07e5fd02c46ea0ea71c`
- 狀態：重構模式已定案；**決策表多數已決**（含 `R2B-ED-01` 圖層＋類別勾選）；三家建議表已改名；操作模擬合併＋HTML 已產；開發順序先 R2B 再 R2O；命名契約待完整回寫；尚未修改產品程式碼

## AI 接手入口

本 repo 已建立自足的繁中維護文件。AI 開始前依序讀取根目錄 `AGENTS.md`、`wip/docs/_R2B_使用說明.md`、`wip/docs/_R2B_系統設定.md`、`wip/docs/_R2B_命名與資料契約.md`、`wip/docs/_R2B_重構計畫.md`、`wip/docs/architecture/DEVELOPMENT_ROADMAP.md`，最後讀本文件確認即時進度。若契約尚未定案，另讀 `wip/docs/前期規劃/資料生態決策表_三家建議.md`（尚待確認唯一來源）與 `wip/docs/rhino指令.md`（測試按鈕）。外部分析檔不再是必要輸入。

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
| 2026-08-27 | `codex/v3-decision-table` | 決策表改名 `_三家建議`；寫回 `R2B-ED-01`；合併模擬＋HTML；開發序 R2B→R2O | 文件已更新；衍生 HTML／合併表已重產 | 尚未 commit |
| 2026-08-27 | `codex/v3-decision-table` | 三版操作模擬合併為 `操作流程模擬_合併.md`（衝突處加註） | 已產；後續已寫入 ED-01 | 尚未 commit |
| 2026-08-27 | `codex/v3-decision-table` | 合併建議表＋操作流程模擬（Models→Camera→Light 兩輪） | 衍生 md 已產；裁決仍只寫原決策表 | 尚未 commit |
| 2026-08-27 | `codex/v3-decision-table` | 三欄 AI 多數決自動填「你的決定」；產生彩色 HTML；工具 `wip/tools/fill_decision_table.py` | R2B 待決定列已全數自動採用（強烈／一般／輕鬆×2+）；手填 XF 保留 | HTML 決定欄：白＝強烈、黃＝一般、綠＝輕鬆。尚未 commit |
| 2026-08-27 | `codex/v3-decision-table` | 建立 `前期規劃/` 決策表與藍圖；抽出 `rhino指令.md`（全部指令＋按鈕巨集） | 文件已建；待使用者逐項確認決策表 | 不寫產品碼。入口檔仍未建 |
| 2026-08-26 | `codex/v3-config-path` | 執行時設定／即時檔改跟工作檔：`_LoopFlow_Config/loopflow_R2B/` | 只改文件。已發布 2.x AppData 路徑不動 | 檔名與 schema 仍待盤點。Dropbox `exchange/` 不再當執行時根目錄 |
| 2026-08-12 | 文件 SSOT 建置 | 建立繁中使用說明、系統設定、重構計畫與 repo AI 規則；Markdown 本機連結檢查 | 通過 | 第一方註解依 feature 批次遷移；第三方 fork 原文與授權保留 |
| 2026-08-12 | 重構模式裁決 | 新版乾淨重建、一次切換；命名與跨程式資料契約先於程式架構 | 通過 | 尚未開始命名盤點與產品程式碼修改 |
| 2026-08-12 | 開發測試入口 | Rhino 測試按鈕暫定直接指向 repo 的 `wip/src/rhino/entrypoints/`；功能或路徑變動時同步更新系統設定與工具列 | 已記錄 | 入口檔尚未建立；正式安裝／RC 另用隔離 `%APPDATA%` 路徑 |
| 2026-08-12 | WIP 工作路徑 | 重構文件移至 `wip/docs/`，未來程式／測試／fixtures 統一置於 `wip/`；Dropbox 工作檔以 `LOOPFLOW_R2B_WORKFILES_ROOT` 解析 | 已記錄 | 公司路徑已登錄；家中電腦路徑待補 |
| 2026-08-12 | 交換 JSON 位置 | Rhino／Blender 即時 JSON 統一置於 Dropbox 工作根目錄的 `exchange/`，程式以環境變數解析 | 已記錄 | 檔名與 schema 待契約盤點；目前資料夾尚無 JSON |
| 2026-08-12 | 任務切分與開發路徑 | 建立 A–G 階段、任務依賴、分支 scope、完成檢查與雙機安全停點 | 已記錄 | 路徑可隨 schema、ABI 與實測結果調整 |

## 下一步

1. 以 `操作流程模擬_合併.md`／`.html` 與 `資料生態決策表_三家建議.md` 為準，把剩餘裁決回寫命名契約／系統設定／使用說明。
2. 依 Roadmap 做 R2B-A01 工作流盤點（開發優先於 R2O）。
3. 開發按鈕巨集見 `wip/docs/rhino指令.md`。空殼 entrypoints 已依 XF-ED-03＝B 允許，但仍不寫業務邏輯。
