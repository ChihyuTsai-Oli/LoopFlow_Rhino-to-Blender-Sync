# LoopFlow R2B user guide

> Do not mix old toolbars, packages, or the Blender add-on in the same project.
>
> This page is the one-minute picture. Buttons and steps are in the [command notes](./COMMANDS.md). Product overview and install are on the [homepage](../README.md).

## One way, separate channels

**Rhino writes. Blender reads.** Nothing is sent back to Rhino.

1. **Save the `.3dm` first.** Unpublished files cannot publish. Settings and exchange files sit next to that file. Paths are not hard-coded to one computer.
2. **Channels are independent.** Models, selected objects, camera, and lights can run on their own. There is no required pipeline.
3. **Use matching pairs.** Rhino `RBModels` goes with Blender Sync / Update Models. `RBObjects` goes with Import Objects. Do not cross the files.

Model sync is meant so materials you already tuned in Blender can stay. Selected objects behave like FBX: no materials, and they accumulate.

## The project is a folder

The folder of the saved `.3dm` is the work folder. LoopFlow creates, next to it:

```text
_LoopFlow_Config/loopflow_R2B/
  live/      ← camera, lights
  models/    ← R2B.3dm, stamped selection 3dms
```

Point Blender’s Work Folder at the **same folder as the `.3dm`** (not inside `_LoopFlow_Config`). Move the whole project folder when you change computers.

## How the two sides meet

| You want | Rhino | Blender |
|---|---|---|
| Main model (with materials) | `RBModels` | **Sync Models** (reset basic materials) or **Update Models** (geometry only, keep existing materials) |
| Selection (no materials) | `RBObjects` | **Import Objects** (you pick the stamped 3dm) |
| Camera | `RBCamera` on/off; right-click `RBCameraPush` | Camera Auto On / Off / Push Once |
| Light positions | `RBLight` on/off; right-click `RBLightPush` | Light Auto On / Off / Sync Lights |
| Settings and docs | `RBOpen` | Open / Health; Open Docs |

The Rhino toolbar **Rhino to Blender Sync** has four buttons: left-click is the main action above; right-click is Objects / Camera Push / Light Push.

Blender 3D View N-panel: tab **LoopFlow**, bar **Rhino to Blender Sync**. Shading help lives in the Shader Editor under the same tab, bar **Box Projection**. It is not part of sync.

## Terms

| Term | Meaning |
|---|---|
| **Work folder** | Folder of the saved `.3dm`. Blender Work Folder points here too. |
| **Sync Models** | Rebuild the `R2B` collection and attach / refresh basic Principled slots. |
| **Update Models** | Same geometry rebuild, **without** overwriting materials you already edited. Use this day to day. |
| **Import Objects** | Add a `R2B_Objects_<stamp>.3dm` to the scene. No materials. Not inside the `R2B` collection. |
| **Health** | Config-root path, plus last-good times for Camera / Light / Models / Objects. |

## Where it stops

- Unsaved file: publish stops, with an English message.
- Export cancelled, failed, or interrupted: you stay on the original work file. The last good output is not replaced by a half-written file.
- Lighting layers have no matching Points: nothing is written, and Blender lights are not cleared.

The tool does not continue into the next channel by itself.

## How to press the buttons

This page is the logic. Command names, left/right-click, Blender buttons, and lighting layers are in the [command notes](./COMMANDS.md).
