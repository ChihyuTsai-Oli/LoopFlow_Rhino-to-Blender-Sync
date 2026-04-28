# LoopFlow R2B User Guide

> All Rhino-side scripts run in the Rhino 8 (CPython 3.9) environment.
> The `LoopFlow_import_3dm` addon is required on the Blender side (core import engine).
> `LoopFlow_Toolkit` is an optional utility package and is not part of the sync workflow.
> Developed and tested on Blender 4.5.4. Blender 5.x compatibility is not yet confirmed.

Last updated: 2026-04-28

---

## Table of Contents

1. [Rhino-Side Scripts](#rhino-side-scripts)
2. [Blender Side — LoopFlow_import_3dm (Required)](#blender-side--loopflow_import_3dm-required)
3. [Blender Side — LoopFlow Toolkit (Optional)](#blender-side--loopflow-toolkit-optional)
4. [Config File](#config-file)

---

## Rhino-Side Scripts

---

### R2B_Models (Model Sync)

One-click export of a clean Rhino model ready for Blender.

**Execution steps:**

1. Save the current Rhino file (the script checks that the file is saved)
2. A layer picker appears — select the parent layer to export (last selection is remembered)
3. The script opens an intermediate file and runs automatic cleanup:
   - Deletes Layouts, point objects, curves, text dots, annotations, and hatches
   - Deletes helper layers whose names contain `//` and all their objects
   - Explodes all Blocks
   - Converts all layer colours into a material structure recognisable by Blender
   - Applies uniform Box Mapping to all objects (size set by `BoxMapSize`)
4. Saves the intermediate file and automatically switches back to the original working file

> **Note:** The script temporarily switches to the intermediate file during execution — the process is fully automatic; do not interact manually.
>
> Once export is complete, use the `LoopFlow_import_3dm` addon in Blender to import with one click.

---

### R2B_Camera (Live Camera Sync)

Toggle design: run once to start, run again to stop.

- While active, writes camera data immediately on any Rhino viewport rotation or zoom
- Outputs `R2B_Camera_Sync.json`, read by the Blender-side camera listener
- No need to save the file first — unsaved new files sync immediately

> **To stop:** run R2B_Camera again to terminate the background listener.

---

### R2B_Light (Light Position Sync)

Scans Point objects in the scene and outputs light position data for Blender to auto-align fixtures.

- Reads the layer prefix set by `LightLayer` in the config (default: `R2B_LT_Points`)
- The terminal sub-layer name is used as the fixture type (template name); Blender matches it to a fixture Collection
- Outputs `R2B_Light_Sync.json`

**Layer naming example:**

```
R2B_LT_Points/
  Downlight        ← layer_short = "Downlight"
  WallLight
  SpotLight
```

> After running light sync in Blender, fixtures are placed according to their `type` name, matched against pre-prepared fixture Collections.

---

### R2B_Open (Quick Open Utility)

Opens related files directly from the Rhino command line.

| Option | Description |
|---|---|
| **Config** | Open `R2B_Path.txt` config file |
| **DataFolder** | Open the data directory |
| **DebugLog** | Open `cursor_R2B_debug_log.txt` debug log |

---

## Blender Side — LoopFlow_import_3dm (Required)

All controls are in **N Panel > LoopFlow 3dm > Rhino Live Link**, split into two sections.

---

### Model Sync

| Button | Description |
|---|---|
| **Import Models** | First-time import; also updates materials |
| **Update Models** | Subsequent updates; fully preserves materials, hide states, exclude states, and Bounds display modes already configured in Blender |

- The path field defaults to `//R2B.3dm` (same directory as the Blender file)
- Click the **🔍** button (Auto-Detect) beside the path field to auto-fill both the model path and Sync Folder

> Use **Update Models** for day-to-day work — materials are not affected. Use **Import Models** only when a full material refresh is needed.

---

### Camera & Light Sync

| Button / Field | Description |
|---|---|
| **Start / Stop Camera Sync** | Toggle; when active, polls `R2B_Camera_Sync.json` in the background and updates the Viewport in real time |
| **Scale** | Unit conversion ratio (default `0.01` for Rhino centimetres) |
| **Lens** | Lens focal length multiplier (default `1.80`; increase if the view appears too wide) |
| **Sync Rhino Lights** | One-click read of `R2B_Light_Sync.json` — aligns fixtures to Rhino Point positions and removes orphaned fixtures for deleted points |
| **Sync Folder** | Directory containing JSON sync files; click Auto-Detect to fill automatically |

**Light sync prerequisites:**

1. Create a `Lighting Fixtures` Collection and place fixture models inside it (names must match the Rhino sub-layer names)
2. Create a `Lighting` Collection and place light objects inside it (same naming rule)
3. Set the Sync Folder, then click **Sync Rhino Lights** to auto-align

---

## Blender Side — LoopFlow Toolkit (Optional)

A utility package that is **not part of the sync workflow** and can be used independently as needed.
All tools are in **View3D > N Panel > LoopFlow Toolkit**, split into three panels.

---

### Export Tools

| Function | Description |
|---|---|
| **Export All to USD** | Batch-exports all top-level Collections in the scene as USDZ |
| **Export Selected to USD** | Exports only checked Collections |

- Before export, the root object Origin is moved to `(0,0,0)`; restored after export
- Selective export: check target Collections in the list; use **All / None** for quick select/deselect

---

### Rename Tools

| Function | Description |
|---|---|
| **Rename Collections** | Batch sequential renaming of Collections selected in the Outliner; also enables Render |
| **Rename Objects by Collections** | Auto-numbers objects using the Collection name as a base; supports Alt+D instance dual-counter |
| **Rename Objects** | Pure sequential numbering, sorted by XY spatial position (bottom-left first, advancing along +Y) |

> **Rename Objects by Collections:** detects shared meshes where `obj.data.users > 1` and appends `_Ins`, syncing the Mesh Data name.

---

### Selection Tools

| Function | Description |
|---|---|
| **Group** | Select multiple child Meshes, make one Active last (parent anchor), and click to create a group synced to a same-named Collection |
| **Un-Group** | Select any group member to dissolve the entire group while preserving world coordinates |
| **Re-Group** | Flatten complex hierarchies, apply Armature modifiers, and re-parent all Meshes under the Active object |
| **Select All in Group** | Select any object in a group to auto-select the entire hierarchy from the root |
| **Delete Objects From Group** | Delete the parent object; children are unparented while preserving world coordinates |
| **Material Isolator** | Switch material Link to Object mode and copy independent materials (appends `_Unique` suffix) |

> **Material Isolator follow-up:** Properties panel (bottom-right) → Material tab → switch the Link dropdown from "Data" to "Object".

---

## Config File

### `R2B_Path.txt` (located at `%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\`)

Auto-created on first run; missing fields are backfilled automatically.

| Field | Default | Description |
|---|---|---|
| `DataPath` | (auto) | Root data output directory |
| `ModelDir` | (empty) | Model output directory; falls back to the Rhino working file directory when empty |
| `LightLayer` | `R2B_LT_Points` | Light Points layer prefix |
| `CameraFile` | `R2B_Camera_Sync.json` | Camera sync file name |
| `LightFile` | `R2B_Light_Sync.json` | Light sync file name |
| `ModelFile` | `R2B.3dm` | Model output file name |
| `BoxMapSize` | `500` | Box Mapping size for model sync (mm) |
| `LastModelLayer` | (auto) | Remembers the last layer selected for model export |

> Use `R2B_Open > Config` to open this file directly from the Rhino command line.
