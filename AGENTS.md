# LoopFlow R2B Repository Instructions

範圍：本 repo。另須遵守上一層 `E:\_GitHub\AGENTS.md`。

## 開始作業前必讀

AI 必須依序完整讀取：

1. `docs/_R2B_使用說明.md`
2. `docs/_R2B_系統設定.md`
3. `docs/_R2B_重構計畫.md`
4. `docs/architecture/PROGRESS.md`

公開的 `README*.md` 與 `docs/USER_GUIDE*.md` 是使用者文件，不是重構指令的權威來源；改變使用行為時仍須同步更新。

## 分支與版本

- `main` 在 3.0 正式發布前維持穩定 2.x。
- `v3-development` 是 3.0 整合分支，不直接承接未分批的大型修改。
- 每項工作從 `v3-development` 建立 `codex/v3-<scope>` 短期分支。
- 2.x P0 修復從 `main` 建立獨立 hotfix，發布後再同步至 `v3-development`。
- 既有 `v2.0.0` tag 與 Release 永不移動、覆寫或重用；本輪重構目標固定為 `v3.0.0`。
- `1.x` 歷史維護分支保持不動，除非使用者明確要求修補。

## 文件與語言

- 維護、架構、設定、重構與進度文件一律使用繁體中文。
- 對外英文 README／使用指南是發布翻譯，可保留英文；功能事實改變時必須與繁中版本同步。
- 模組完整責任、流程、schema、副作用與 upstream／fork 邊界寫入 `docs/`，程式只保留必要說明。
- 新增或修改的 docstring、區塊註解與行內註解使用繁體中文；API、識別字、Blender／Rhino 名稱與第三方授權文字維持原文。
- 不批次翻譯整個 fork。修改某個第一方功能時，先把整體說明移入 docs，再精簡該範圍標頭；第三方 fork 註解除必要 patch 外保持可追溯。

## AI 作業流程

1. 確認 repo、branch、origin、upstream 與乾淨工作樹；只用 fast-forward pull。
2. 讀取上述四份文件，從 `PROGRESS.md` 確認目前階段與限制。
3. 建立短期工作分支，一批只處理一個 P0 或一條 feature。
4. 使用隔離的 Rhino、Blender profile、測試 `.3dm` 與輸出目錄；不得用唯一正式專案作 migration。
5. 修改前保存 golden workflow／fixture；完成後驗證成功、取消、失敗與中斷。
6. 同步更新使用說明、系統設定、重構計畫（若決策改變）與 `PROGRESS.md`。
7. 檢查 diff、授權、binary、秘密與產物後提交、推送短期分支。

使用者不負責操作 Git 或自行推導技術步驟；AI 應直接完成安全、可逆的操作，並以簡短繁體中文回報結果。
