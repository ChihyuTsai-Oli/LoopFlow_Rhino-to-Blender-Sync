# LoopFlow R2B 3.0 — 任務切分與開發路徑

本文件把 Rhino → Blender 3.0 重構拆成可在單一工作時段完成、驗證、提交與推送的工作單位。功能契約以 `_R2B_命名與資料契約.md` 為準；即時狀態只記錄於 `PROGRESS.md`。

## 執行規則

- 一次只修改一個 repo；同一 repo 同一時間只由一台電腦／一個 AI 作業。
- 每項任務從 `v3-development` 建立 `codex/v3-<scope>`，結束前完成檢查、commit、push 與交接。
- Rhino、Blender integration、importer fork、Toolkit 是四個邊界；任務不得跨邊界混入無關整理。
- 開發期 Rhino 按鈕指向 repo 的 `src/rhino/entrypoints/`；正式安裝／RC 才使用隔離 `%APPDATA%` 與 Blender profile。
- 下表可隨功能、路徑、ABI 與實測結果調整；同步更新本文件、系統設定與 `PROGRESS.md`。

## 階段與任務

| ID | 任務／建議分支 scope | 前置 | 主要產出 | 完成檢查與安全停點 |
|---|---|---|---|---|
| R2B-A01 | 端到端工作流盤點／`workflow-inventory` | 無 | Models／Camera／Light 從 Rhino producer 到 Blender consumer 的輸入、輸出、state、副作用及失敗條件 | 可追溯至現行 Python／Blender 程式；只改文件 |
| R2B-A02 | 指令、設定與檔案命名／`naming-contract` | A01 | command、`R2B_Path.txt`、檔名、資料夾、顯示名稱與 migration 邊界 | 使用者可見變更已裁決；未定案明示 |
| R2B-A03 | Models／Camera／Light schema／`sync-schema` | A01–A02 | version、型別、單位、座標、document／session ID、成功條件 | producer／consumer 可共用 fixtures |
| R2B-A04 | Blender ID 與 state 契約／`blender-contract` | A01–A03 | operator、property、panel、collection、object、timer／state key | external ID 影響與 migration 已記錄 |
| R2B-A05 | Importer fork 邊界／`fork-boundary` | A01、A04 | `UPSTREAM.md`、`PATCHES.md`、第一方 integration boundary 與授權基準 | upstream／LoopFlow patch 可追溯 |
| R2B-A06 | Golden fixtures／`contract-fixtures` | A03–A05 | Models、Camera、Light、layer、material、instance、view、壞資料 fixtures | 不含私人場景；預期結果可機器比對 |
| R2B-B01 | 最小 source／測試骨架／`source-skeleton` | A02–A06 | Rhino／Blender source layout、bootstrap、entrypoints、tests | repo 入口可載入，不覆蓋穩定安裝 |
| R2B-B02 | 共用 foundation／`foundation-core` | B01 | result、stage、logging、version、config、path、atomic publish | 純 Python 測試通過；無個人路徑 |
| R2B-B03 | Rhino document adapter／`rhino-platform` | B01–B02 | explicit IDs、temporary data、來源狀態 snapshot／restore | success／cancel／failure／interruption 測試 |
| R2B-B04 | Blender registration 骨架／`blender-bootstrap` | B01–B02、A04 | metadata、register／unregister、reload 與隔離 package ID | 啟用、停用、重載不留半套 state |
| R2B-C01 | Models Rhino producer／`models-producer` | A03、B02–B03 | explicit source → pending 3DM → validate → replace | 原 Rhino 文件零變更，last good 保留 |
| R2B-C02 | Importer integration boundary／`importer-boundary` | A05–A06、B04 | 第一方同步呼叫 converter 的唯一入口 | importer fixtures 與錯誤隔離通過 |
| R2B-C03 | Models Blender consumer／`models-consumer` | C01–C02 | Models operator／sync handler／state 更新 | parse＋apply 成功才更新 state |
| R2B-D01 | Camera producer／`camera-producer` | A03、B02–B03 | atomic Camera payload 與入口 | 座標、焦距、重複發布與錯誤通過 |
| R2B-D02 | Camera consumer／`camera-consumer` | D01、B04 | apply、debounce／retry、state 管理 | 壞檔不污染場景且可重試 |
| R2B-D03 | Light producer／`light-producer` | A03、B02–B03 | Point light payload 與入口 | 建立、更新、刪除、空資料通過 |
| R2B-D04 | Light consumer／`light-consumer` | D03、B04 | Blender light apply 與 state 管理 | 未支援類型與失敗 stage 明確 |
| R2B-E01 | UI／operators／panels／`blender-ui` | C03、D02、D04 | UI 只呼叫穩定 application boundary | ID 不漂移、register／unregister 通過 |
| R2B-E02 | Timer／watcher lifecycle／`sync-lifecycle` | E01 | timer、content diff、reload、錯誤復原 | 重載、停用、壞檔及重試實機驗證 |
| R2B-E03 | Rhino Open／Config／`rhino-diagnostics` | B02、A02 | Open／Config／診斷入口 | 路徑與錯誤資訊可理解，不混入 Blender UI |
| R2B-F01 | Importer fork hardening／`importer-fixtures` | C02、A05–A06 | converter patch、fixtures、ABI 與授權驗證 | 每項 patch 可追溯 upstream 基準 |
| R2B-F02 | Toolkit baseline／`toolkit-baseline` | 主同步鏈穩定 | 現行 Toolkit 契約、registration 與測試 | 不擴充功能，不阻塞 Models／Camera／Light |
| R2B-F03 | Toolkit 整理／`toolkit-structure` | F02 | operators、panels、services 邊界 | 既有操作與重複執行通過 |
| R2B-G01 | v2 migration／`migration` | schema 與 ID 穩定 | scanner、預覽、備份、converter、rollback | 只測資料副本，失敗可回復 |
| R2B-G02 | Version／Manifest／Build／`build-release` | 核心功能完成 | version SSOT、manifest、ZIP、ABI、清單、SHA-256、RHC | Blender／Python ABI 與資產一致 |
| R2B-G03 | Rhino → Blender RC／`rc-validation` | G01–G02 | 隔離環境完整驗收記錄 | Models／Camera／Light 正常、取消、失敗、中斷與 last good 通過 |

## 建議開發波次

1. A01–A06：先鎖定跨軟體契約、fork 邊界與 fixtures。
2. B01–B04：建立最小可載入骨架與兩端生命週期。
3. C01–C03：先打通 Models 垂直鏈，校正架構。
4. D01–E03：Camera、Light 與 UI／watcher 分別接入。
5. F01–F03：主鏈穩定後整理 fork 與 Toolkit。
6. G01–G03：migration、build、ABI 與 RC；最後才合入 `main`。

## 雙機換機檢查點

每次換機前確認工作樹乾淨、任務分支已 push、upstream 差距 `0/0`，並在 `PROGRESS.md` 記錄已驗證事實、限制與下一步。不可同時在兩台電腦修改本 repo；Blender 測試 profile、私人 `.blend`／`.3dm` 與產物不代替 Git 交接。
