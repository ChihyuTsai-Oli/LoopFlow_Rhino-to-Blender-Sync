# LoopFlow R2B commands

> Do not mix old toolbars, packages, or the Blender add-on in the same project.
>
> Workflow logic: [user guide](./USER_GUIDE.md). Command names are the Rhino command-line names (no spaces), for example `RBModels`.
>
> Rhino dialogs and the Blender panel are English.

## Project folder

Save the `.3dm` first. **That folder is the work folder.** Exchange files live in `_LoopFlow_Config/loopflow_R2B/` next to it. You can move the whole pack to another disk or computer without editing absolute paths.

Point Blender Work Folder at the **same folder as the `.3dm`**.

## Quick index

| Stage | Rhino | Blender | In one line |
|---|---|---|---|
| Open | `RBOpen` | Open / Health; Open Docs | Config root, last-good times, folders, this documentation |
| Main model | `RBModels` | Sync Models / Update Models | Layer export of textured `R2B.3dm` |
| Selection | `RBObjects` | Import Objects | Current selection → stamped 3dm, no materials |
| Camera | `RBCamera` / `RBCameraPush` | Camera Auto On / Off / Push Once | Active view → `live/camera.json` |
| Lights | `RBLight` / `RBLightPush` | Light Auto On / Off / Sync Lights | Lighting-layer Points → `live/light.json` |
| Shading | (none) | Shader Editor → Box Projection | Load PBR, no UVs |

Toolbar, four buttons, left / right click:

| Button | Left | Right |
|---|---|---|
| 1 | `RBOpen` | — |
| 2 | `RBModels` | `RBObjects` |
| 3 | `RBCamera` | `RBCameraPush` |
| 4 | `RBLight` | `RBLightPush` |

## Contents

[01 Open and docs](#01-open-and-docs) · [02 Main model](#02-main-model) · [03 Selected objects](#03-selected-objects) · [04 Camera](#04-camera) · [05 Lights](#05-lights) · [06 Blender Sync panel](#06-blender-sync-panel) · [07 Box Projection](#07-box-projection) · [08 Do not](#08-do-not)

---

## 01 Open and docs

**Command:** `RBOpen`

Run after the file is saved. An English Health window appears, four equal-width buttons left to right:

- **Open Config** — `_LoopFlow_Config/loopflow_R2B/`
- **Open live** — camera / light JSON
- **Open models** — `R2B.3dm` and selection files
- **Open Docs** — this GitHub documentation entry

The summary lists the config-root path and last-good times for Camera / Light / Models / Objects. An unsaved file is blocked.

Blender **Open / Health**: hover for the summary; left-click opens the config root. **Open Docs** opens the same documentation entry.

---

## 02 Main model

**Command:** `RBModels`

Export the clean model for Blender’s main sync (**with materials**).

1. The file must be saved.
2. Pick layers to export (including children; the list scrolls).
3. Check geometry types. The same Rhino window remembers the last successful set. The first time, Point / Curve start unchecked.
4. Optional exclude mark (default `//`; empty = none). Layer paths that contain this text are skipped.
5. On success, `models/R2B.3dm` is written. Failure does not replace the last good file. The source Rhino file is restored; it is **not** switched to an intermediate file.

Material names are `parent::leaf` layer names, with layer colors. Blocks are exploded; if several instances share a definition, the first goes into the 3dm and the rest are instanced in Blender from a sidecar.

Layers whose names contain `//` are skipped by default.

In Blender, day-to-day use **Update Models** (geometry updates, materials you edited stay). Use **Sync Models** only when you need the basic material slots rebuilt. Both rebuild the `R2B` collection and leave Lighting alone.

---

## 03 Selected objects

**Command:** `RBObjects`

Export the **current selection** as an untextured 3dm for Blender **Import Objects**.

- New file each time: `models/R2B_Objects_YYYYMMDD_HHMMSS.3dm`. Old files are kept.
- Every selected Block instance is expanded.
- **No materials**

Import Objects opens a file picker (default `loopflow_R2B/models/`). Cancel does nothing. Results accumulate at the scene root under a parent named `R2B_Objects`, **not** inside the `R2B` collection.

Do not send `R2B.3dm` to Import Objects, and do not send a stamped file to Sync / Update Models.

---

## 04 Camera

**Commands:** `RBCamera` (auto on/off), `RBCameraPush` (once)

- Uses the active perspective viewport
- File must be saved
- Writes `live/camera.json`
- Run `RBCamera` again to stop auto-sync

Blender: Camera Auto On / Off / Push Once. With auto on, it follows the Rhino view.

---

## 05 Lights

**Commands:** `RBLight` (auto on/off), `RBLightPush` (once)

Only **Points on LightLayer children** are synced (default parent name `R2B_LT_Points`). Do not put Points on the parent itself.

**Rhino layers**

| Layer | Put | Synced? |
|---|---|---|
| `R2B_LT_Points` (parent) | No Points | No |
| `R2B_LT_Points::Down_Light` | Points | Yes; type name `Down_Light` |
| `R2B_LT_Points::Pendant` | Points | Yes; type name `Pendant` |

**Prepare in Blender first**

| Collection (an outer wrapper is fine) | Put | Names |
|---|---|---|
| `Lighting` | Blender lights | Same as the Rhino child-layer leaf |
| `Lighting Fixtures` | Fixture meshes | Same names; `.001` is OK if the file already has duplicates |

After sync, `R2B Lighting Points` appears: one empty per Rhino Point, with the matching light and fixture parented under it. Missing templates do not leave empty empties. If no Points match, Rhino **does not write**, and Blender **does not clear lights**.

Edit the template fixture and instances follow. For a one-off intensity or color, Make Single User on that instance.

---

## 06 Blender Sync panel

3D View N-panel → **LoopFlow** → **Rhino to Blender Sync**.

| Button | What it does |
|---|---|
| **Sync Models** | Read `models/R2B.3dm`, rebuild `R2B`, assign basic Principled (base color `#F2F2F2FF`) |
| **Update Models** | Same geometry rebuild; **does not overwrite** existing materials of the same name |
| **Import Objects** | Pick a stamped 3dm; no materials; accumulate |
| **Camera Auto On / Off / Push Once** | Read `live/camera.json` |
| **Light Auto On / Off / Sync Lights** | Read `live/light.json` |
| **Open / Health** | Hover = summary; left-click opens the config root |
| **Open Docs** | This documentation entry |

Work Folder is the same folder as the `.3dm`. You do not need a separate Import Rhinoceros 3D add-on. The Sync zip is in `Documents\LoopFlow\Rhino to Blender Sync`. Install with **Add-ons → Install from Disk** (not Extensions). The list name is **LoopFlow Rhino to Blender Sync**. If you previously installed import_3dm, hit a rename error, or saw `No module named 'foundation'`: quit Blender, delete `loopflow_r2b_sync` / `loopflow_r2b_sync@` under both `extensions\user_default` and `scripts\addons`, then install the zip only. If Portable Blender is on Dropbox, pause sync before installing.

LoopFlow [ToolBox](./TOOLBOX.md) is not part of this product (separate Blender add-on; not in the yak).

---

## 07 Box Projection

Shading help, separate from model / camera / light sync.

1. Open the Shader Editor. A Principled shader already there is easiest.
2. N-panel **LoopFlow → Box Projection → Load PBR Maps**.
3. Multi-select Base Color / Roughness / Metallic / Normal (filenames containing `diff` / `rough` / `metal` / `nor` are enough).
4. **Space:** World pins the map in the scene; Object follows the object. Scale is metres per tile. Blend 0 is a harder seam.
5. No UVs are written.

---

## 08 Do not

- Publish before saving
- Cross `R2B.3dm` and `R2B_Objects_<stamp>.3dm` onto the other Blender buttons
- Expect these Blender buttons inside an Octane (or other) workflow
- Rename the source `.3dm` or save the work file as an intermediate file just to sync
