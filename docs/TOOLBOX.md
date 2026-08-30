# LoopFlow ToolBox

[繁體中文](./TOOLBOX_zh-TW.md)

A separate Blender add-on (**1.0.0**). It is not Rhino sync and is **not** in the R2B `.yak`.

N-panel: tab **LoopFlow**, bar **ToolBox**. Buttons are English.

Rhino to Blender Sync docs: [documentation entry](./README.md).

## Download and install

Download the zip from a **fixed tag**. Do **not** use this repo’s [latest Release](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases/latest) (that is the R2B sync product):

- Tag: [`toolbox-1.0.0`](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases/tag/toolbox-1.0.0)
- File: `loopflow_toolbox-1.0.0.zip`

1. Edit → Preferences → Add-ons → **Install from Disk** (not Get Extensions)
2. Choose the zip only
3. Enable **LoopFlow ToolBox**
4. Do not use this with the old **LoopFlow Toolkit** add-on on a real project at the same time

It can run next to Sync: the same LoopFlow tab shows **Rhino to Blender Sync** and **ToolBox**. Use **OBJECT** mode.

## Export Tools

Each **top-level Collection** becomes one `.usdz`. Before export, root objects in that Collection move to the world origin; positions and visibility are restored afterwards. Collections with no geometry are skipped.

- **Export All to USD**: one file per top-level Collection
- Checklist + **All** / **None** + **Export Selected to USD**: only checked Collections

Selected with nothing checked: error, no folder dialog. If export fails mid-way, Undo if positions did not restore.

## Rename Tools

- **Rename Collections**: batch-rename Collections selected in the Outliner (or inferred from selected objects) and enable Render. Type a base name; the active Collection has no suffix, others get `_001`…
- **Rename Objects by Collections**: number objects from the Collection name. Shared meshes (`Alt+D`) get `_Ins`. Mesh data names stay in sync.
- **Rename Objects**: ignore hierarchy; number from bottom-left in XY ( +Y then +X ). The active object is first, with no suffix. Same `_Ins` rule.

Nothing selected: no rename.

## Selection Tools

- **Group**: last-clicked Mesh is the anchor. Selected meshes parent under it and sync to a **same-named** Collection (created if needed). Empty leftover Empty parents and empty Collections are removed.
- **Un-Group**: pick any member; unparent the whole hierarchy. Empty roots are deleted. World coordinates stay.
- **Re-Group**: active Mesh is the final anchor. Armature modifiers are applied, hierarchy flattened into `COL_FINAL_{anchor}`. Selected Empties / Armatures are deleted.
- **Select All in Group**: pick any member; select the whole hierarchy.
- **Delete Objects From Group**: delete the active parent; keep children.
- **Material Isolator**: copy materials to Object link with a `_Unique` suffix so `Alt+D` instances can differ. Then set Material Link to Object in Properties.
