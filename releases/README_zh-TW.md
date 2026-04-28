# LoopFlow Rhino-to-Blender Sync — Releases

### 安裝方式

**Rhino 端（腳本）**

1. 從 Releases 下載最新版本的 ZIP
2. 解壓縮後執行 `install_LoopFlow_R2B.bat`，自動安裝 Rhino 端腳本
3. 將 `LoopFlow_R2B.rhc` 拖曳至 Rhino 視窗，工具列即出現

**Blender 端（Addon）**

4. 在 Blender 中選擇 Edit > Preferences > Add-ons > Install
5. 以 ZIP 格式安裝以下 Addon：
   - `LoopFlow_Toolkit.zip`：Export / Rename / Selection 整合工具包
   - `LoopFlow_import_3dm.zip`：3DM 模型匯入器（需另行打包）

### 包含檔案

| 檔案 / 資料夾 | 說明 |
|---|---|
| `LoopFlow_Rhino-to-Blender-Sync/` | Rhino 端 Python 腳本 |
| `LoopFlow_Toolkit/` | Blender Addon 原始碼（打包為 `LoopFlow_Toolkit.zip`） |
| `LoopFlow_import_3dm/` | Blender Addon 原始碼（打包為 `LoopFlow_import_3dm.zip`） |
| `install_LoopFlow_R2B.bat` | Rhino 端自動安裝程式 |
| `LoopFlow_R2B.rhc` | Rhino 工具列定義檔 |

### 資料夾結構

```
releases/
  LoopFlow_Rhino-to-Blender-Sync/   ← Rhino 端 Python 腳本
    LiveLink_R2B_*.py
    LiveLink_R2B__Config.py
  LoopFlow_import_3dm/               ← Blender Addon（打包為 LoopFlow_import_3dm.zip）
    __init__.py
    converters/
    rhino3dm/
    ...
  LoopFlow_Toolkit/                  ← Blender Addon（打包為 LoopFlow_Toolkit.zip）
    __init__.py
  install_LoopFlow_R2B.bat
  LoopFlow_R2B.rhc
  README.md
```
