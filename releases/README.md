# LoopFlow Rhino-to-Blender Sync — Releases

[▶ Watch on YouTube](https://www.youtube.com/@LoopFlow) · [▶ Project Page](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync)

---

## Installation

**Rhino Side (Scripts)**

1. Download the latest release ZIP from [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases)
2. Extract and run `install_LoopFlow_R2B.bat` to automatically install the Rhino scripts
3. Drag `LoopFlow_R2B.rhc` into the Rhino viewport — the toolbar will appear

**Blender Side (Addons)**

1. In Blender, go to **Edit > Preferences > Add-ons > Install**
2. Install the following addons as ZIP files:
  - `LoopFlow_Toolkit.zip` — Export / Rename / Selection toolkit
  - `LoopFlow_import_3dm.zip` — 3DM model importer

> Package each addon folder as a ZIP before installing (select the folder, compress to ZIP).

---

## Included Files


| File / Folder                     | Description                                                 |
| --------------------------------- | ----------------------------------------------------------- |
| `LoopFlow_Rhino-to-Blender-Sync/` | Rhino-side Python scripts                                   |
| `LoopFlow_Toolkit/`               | Blender Addon source (package as `LoopFlow_Toolkit.zip`)    |
| `LoopFlow_import_3dm/`            | Blender Addon source (package as `LoopFlow_import_3dm.zip`) |
| `install_LoopFlow_R2B.bat`        | Rhino-side auto-installer                                   |
| `LoopFlow_R2B.rhc`                | Rhino toolbar definition                                    |


---

## Folder Structure

```
releases/
  LoopFlow_Rhino-to-Blender-Sync/   ← Rhino-side Python scripts
    LiveLink_R2B_*.py
    LiveLink_R2B__Config.py
  LoopFlow_import_3dm/               ← Blender Addon (package as LoopFlow_import_3dm.zip)
    __init__.py
    converters/
    rhino3dm/
  LoopFlow_Toolkit/                  ← Blender Addon (package as LoopFlow_Toolkit.zip)
    __init__.py
  install_LoopFlow_R2B.bat
  LoopFlow_R2B.rhc
  README.md
  README_zh-TW.md
```

---

## Credits

- **LoopFlow_import_3dm** is a fork of [import_3dm](https://github.com/jesterKing/import_3dm) by [Nathan Letwory (jesterKing)](https://github.com/jesterKing), licensed under MIT

