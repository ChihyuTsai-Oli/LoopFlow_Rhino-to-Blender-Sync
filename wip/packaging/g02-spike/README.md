# R2B 3.0 yak 建置

正式版號 **`3.0.2`**（`v3.0.0`／`v3.0.1` 永不移動）。yak 含 Blender Sync zip（`templates/`）；第一次跑任一產品指令拷到「文件\LoopFlow\Rhino to Blender Sync」。換版時先填暫存資料夾，成功後才換成產品資料夾。zip 為傳統 Add-on（無 `blender_manifest.toml`），內附 `foundation`；啟用前先把該目錄加入 `sys.path`。工具列 RUI 進包時改成與 `.rhp` 同名，Rhino 才會自動載入。

畫面名（已凍）：`loopflow Rhino to Blender Sync`  
機器名：`loopflow-rhino-to-blender-sync`

## 你要交的檔（可與指令檔並行）

放到 `wip/docs/toolbar/`：

- 產品 `.rui`（`ExportRuiFile` 匯出；含 `tool_bar_group`；不要寫 `SelectedToolbarSet`）
- Package Manager 圖示 PNG（建議 256×256），檔名 `icon.png`

正式按鈕巨集（不要抄開發用 ScriptEditor 路徑）：

```text
! _RBModels
! _RBObjects
! _RBCamera
! _RBCameraPush
! _RBLight
! _RBLightPush
! _RBOpen
```

## Script Editor 必須你點一次（不能手寫 rhproj）

Rhino 8.11 以上：

1. 完全關掉再打開 Rhino。
2. Script Editor → 新增專案（Python）。
3. 加入 `commands/` 底下 **只有** `指令名稱.txt` 列出的七支 `.py`（不要加 `command_locate.py`、`_gen_commands.py`）。
4. Libraries 加入 `wip/src`（讓 `rhino`／`foundation` 進套件）。
5. 另存成這個檔（檔名請一致）：  
   `wip/packaging/g02-spike/loopflow-rhino-to-blender-sync.rhproj`
6. 跟我說存好了。之後才跑 `build.ps1`。

指令的 `language` 必須是物件（Script Editor 會寫對）。不要改開發入口 `wip/src/rhino/entrypoints/`。

## 建置（有 rhproj 之後）

```powershell
cd wip/packaging/g02-spike
.\build.ps1
```

腳本會刪掉 RhinoCode 自動產生的 `.rui`，若 `wip/docs/toolbar/` 有產品 RUI／`icon.png` 再複製進去。產出 `.yak` 不進 Git。

裝完須**完全關 Rhino 再開**。不要跟 2.x 開發按鈕混測。正式上架打新 tag（現行 `v3.0.2`）；永不覆寫 `v3.0.1`／`v3.0.0`／`v2.0.0`。
