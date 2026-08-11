# LoopFlow R2B — 重構計畫

本文件定義 R2B 3.0 的完整重構邊界、順序與完成條件。它已整合原先外部分析與舊 memo 的有效內容；後續決策直接更新本文件與 `architecture/PROGRESS.md`。

## 版本裁決

- 既有穩定版為 `v2.0.0`，不可移動或重用。
- 本輪包含安裝、source layout、schema、build 與產品邊界的破壞性整理，目標固定為 `v3.0.0`。
- `main` 在 3.0 發布前維持 2.x；3.0 使用 `v3-development` 與 `codex/v3-<scope>`。
- 「LoopFlow Suite 2」可作整體名稱，但不要求三個 component 使用相同 tag。

## 重構模式裁決

本輪採「3.0 乾淨重建、正式發布時一次切換」：

- `main`、`v2.0.0`、既有 payload 與 fork 基準凍結為舊版參考與回復點。
- 3.0 在隔離 `src/`、Rhino 安裝、Blender profile／package ID 與測試資料建立，不要求開發中的半成品相容 v2。
- 不把 v2 指令逐支包進新架構，也不在核心長期保留 alias、雙寫或 compatibility wrapper。
- 開發仍按 contract、producer、consumer 與功能群分批提交；每段做自動／fixture／contract 測試。
- Models／Camera／Light 與 importer 主鏈接通後，再集中做 Rhino→Blender 端到端實機測試。
- v2 設定或 scene 若需升級，由獨立 migration 工具一次轉換。

## 產品邊界

### Rhino Producer

Models、Camera、Light、Open／Config。只從 Rhino 收集資料並安全發布，不包含 Blender UI 或 3DM conversion。

### Blender Sync Integration

接收 Models／Camera／Light、執行更新策略、管理 timer／state、operators／panels。這是 LoopFlow 第一方整合層。

### `import_3dm` Fork

只負責 3DM → Blender conversion。保留 upstream、授權、基準 commit 與 patch；同步 UI 不長在 converter 核心。

### LoopFlow Toolkit

獨立 Blender add-on。3.0 核心先不擴充 Toolkit，避免阻塞 Models／Camera／Light。

## 共同原則

- feature-first，不為 Rhino 端 5 支 script 建立過度層級。
- Python-first，不主動增加 C#。
- 命名、schema、Blender ID 與 fork 邊界先定義，完成前不建立正式 feature。
- Models P0 安全要求直接納入 3.0 新實作；只有使用者明確要求維護舊版時才另開 2.x hotfix。
- R2B／R2O 只共用文件層級的安全 pipeline、result 語彙與測試矩陣，不建立跨 repo runtime package。
- 3.0 開發安裝、設定、輸出、RHC 與 Blender profile 必須和 2.x 隔離。
- 不新增同步種類或 UI 功能。

## 目標結構

```text
src/
  rhino/
    r2b_rhino/
      bootstrap.py
      command_catalog.py
      features/       # models、camera、lights、diagnostics
      platform/       # RhinoDoc、camera、lights、3dm exporter
      foundation/     # config、path、log、result、atomic publish、version
    entrypoints/
  blender_addons/
    LoopFlow_import_3dm/
      __init__.py
      registration.py
      ui/
      operators/
      sync/
      integration/
      importer_fork/
      vendor/rhino3dm/
    LoopFlow_Toolkit/
      __init__.py
      registration.py
      operators/
      panels/
      services/
tests/
docs/
tools/
```

## Track 0：Models 資料安全

現況最高風險：

- 解鎖／顯示後 `_SelAll` 可能匯出整份文件。
- `DocumentModified(False)` 可能讓未存修改被視為可丟棄。
- Rhino commands 缺少一致結果檢查。
- `finally` 可能在失敗時仍顯示完成。

最終 pipeline：

```text
validate request
→ collect explicit object IDs
→ operate on temporary document/data
→ export pending 3DM
→ validate importer-readable output
→ atomically replace last good output
→ structured result
```

驗收：成功、取消、命令失敗與中斷後，原 Rhino 文件物件、layer、selection、path、modified flag 與未存內容全部不變。

## Camera／Light

### Camera

- Rhino producer 使用 atomic write。
- Blender 只有 JSON parse 與 apply 成功後才更新 mtime／state。
- 暫時性壞檔重試；加入 debounce／content diff。
- schema 包含 version、producer、document／session ID 與 payload。

### Light

- 本輪保留現有 Point 位置同步，不新增 Block、旋轉或燈種。
- collection 不存在可建立；建立、更新、刪除、空資料、未支援類型都有明確 result。
- producer／consumer schema 與成功條件一致。

## Blender Add-on 分層

- `__init__.py` 最終只保留 metadata 與 register／unregister。
- UI、operators、timer／state、sync handlers 分批移出。
- 搬移期間 operator ID、panel 與使用者流程保持不變。

## Fork 管理

先建立：

- `UPSTREAM.md`：來源、基準 commit／tag、授權與取得日期。
- `PATCHES.md`：LoopFlow 修改檔案、原因與測試。
- importer fixtures：layer、material、mesh、curve、instance、camera／view。
- 第一方 integration 與 upstream converter 檔案對照。

`integration/importer.py` 成為第一方同步呼叫 fork 的唯一入口。先用測試隔離，再考慮搬移 converter；不為目錄美觀先大量搬第三方檔案。

## 版本、manifest 與 build

- version、`bl_info`、manifest、CHANGELOG、ZIP、Blender/Python ABI 由單一 build 驗證。
- 清理模板註解、上游 maintainer 與不存在的多平台 wheel 宣告。
- 先確認 Extension 或傳統 add-on 路線。
- `src` 穩定後才由 build 產 Rhino payload、import add-on、Toolkit add-on、清單與 hash。

## Git 與環境隔離

- 3.0 工作由短期分支合入 `v3-development`。
- `main` 原則上凍結；只有使用者明確要求舊版緊急修補時才從 `main` 開 2.x hotfix。
- RC 通過才合入 `main` 並建立 `v3.0.0`。
- Rhino Dev 使用獨立 scripts／data／RHC；Blender 使用測試 profile 或不同 package ID。
- 不用唯一正式 `.blend`／`.3dm` 作 importer 或 migration 測試。

## C# Gate

維持 Python。只有 Camera watcher／lifecycle 或已量測 Rhino-side 瓶頸，且 C# 能完整負責穩定邊界、build 與部署可回復時才評估。禁止 C# command → Python script → Rhino command 的多層殼。

## 與 R2O 的局部共用

共用文件與測試語彙：

- validate → explicit source → temporary data → export pending → validate → replace → result。
- `CommandResult`／stage／error。
- atomic publisher。
- 來源 Rhino 文件零變更 invariant。
- success／cancel／failure／interruption 矩陣。

不共用 Models／Camera／Light payload、3DM exporter、Blender consumer、產品 path 或 runtime package。純 Python helper 需至少兩次真實同步修改證據後才評估 build-time vendoring。

## 延後範圍：Auto Basic Material Assigner

3.0 核心重構不恢復此功能。現有停用 operator／help 應先一致標示未提供。

若未來重新排期，原構想為使用者指定 Prototype Object、Light Source Object、Light Collection：

- 發光材質：Light Source 第一個 material 套至 Light Collection，以 object `r2b_light_stamped` 避免覆寫手動調整。
- 一般材質：Prototype material names 依長字串優先比對，以 material `r2b_auto_assigned` 標記自動結果。

實作前需重新驗證 Blender version、linked data、material slot、collection traversal、undo、重複執行與手動修改保留；不可按舊 memo line number 解除註解。

## 新版建造順序

1. **工作流與依賴盤點**：Rhino Models／Camera／Light → Blender integration → importer fork，列出所有輸入、輸出、ID、state 與失敗條件。
2. **命名與資料契約**：完成 `_R2B_命名與資料契約.md`，鎖定 command、config、檔案、JSON schema、operator／property／collection、version 與 ABI。
3. **Fixtures 與 fork 邊界**：建立 Models／Camera／Light 與 importer fixtures，完成 `UPSTREAM.md`、`PATCHES.md` 與第一方 integration 邊界。
4. **最小新架構**：建立 `src/`、bootstrap、catalog、foundation、validator、測試骨架與隔離載入方式。
5. **Rhino producer**：依 Models → Camera → Light 建立；Models 直接採 explicit IDs、temporary data、pending、validate、atomic replace。
6. **Blender consumer**：registration、UI、operators、timer／state、sync handlers 與 importer boundary。
7. **主鏈端到端測試**：以隔離 Rhino／Blender、測試 `.3dm`／`.blend` 驗證正常、取消、失敗、中斷與 last good。
8. **Toolkit**：在同步主鏈穩定後獨立整理，不擴充功能。
9. **Migration／Build／切換**：v2 scanner、備份、一次轉換、manifest、CHANGELOG、RHC、ZIP、hash、RC，最後一次合入 `main` 發布 `v3.0.0`。

每一步都要提交與自動測試；「一次切換」不等於「全部寫完才第一次測試」。Auto Basic Material 只有使用者重新納入範圍後才處理。

## 每批完成門檻

- 一批只處理一個安全問題或一條 feature。
- golden workflow、取消、失敗、中斷與資料復原通過。
- Rhino 原文件不變，last good output 仍在。
- schema／path／version 只有一個權威來源。
- docs、progress、fixtures、測試與 build 資訊同步。
- diff 排除秘密、快取、未預期 binary／產物與第三方無關變更。
- commit、push、回復點與實機限制有紀錄。

## 3.0 完成條件

- Models 不改來源文件、不吃未存修改、不覆蓋 last good output。
- Camera／Light producer／consumer 的 schema 與成功條件一致。
- Rhino producer、Blender integration、fork、Toolkit 邊界清楚。
- `__init__.py` 只負責 metadata／registration。
- upstream、patch、授權與 fixtures 可追溯。
- version、manifest、`bl_info`、binary ABI、CHANGELOG、ZIP 一致。
- 3.0 開發環境與穩定 v2.0 隔離。
- Auto Basic Material 設計已保存但未誤納入核心範圍。
