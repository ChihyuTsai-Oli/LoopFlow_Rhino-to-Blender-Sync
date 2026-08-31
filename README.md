# LoopFlow｜Rhino to Blender Sync

[繁體中文](./README_zh-TW.md)

> Do not mix old toolbars, packages, or the Blender add-on in the same project.

Push Rhino models, cameras, and light points one way into Blender. You stay in control of every step; LoopFlow only writes what you ask for.

Rhino installs as a single `.yak`. The first product command copies the Blender Sync zip to `Documents\LoopFlow\Rhino to Blender Sync`.

[▶ Documentation](./docs/README.md) · [▶ Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) · [▶ Tutorials](https://www.youtube.com/playlist?list=PLiJmu8T_uzJJTnDl6HLSOFZ3DimkI9bV8)

## Features

- **Model sync** — Export a clean 3dm from the working Rhino file. Blender can rebuild geometry and keep materials you already tuned.
- **Selected objects** — Export the current selection as a separate untextured 3dm and add it to the scene like an FBX.
- **Camera sync** — Mirror the active Rhino viewport to Blender.
- **Light alignment** — Rhino Points on the lighting layers align lights and fixtures you prepared in Blender.
- **Box Projection** — Load PBR maps in the Shader Editor with world or object space. No UVs.

Each channel is independent. You do not have to run them in a fixed order.

## System requirements

- **Rhino 8** (Windows)
- **Blender 5.2.1** (development target)

Rhino dialogs and the Blender panel are English. This page is English; a Traditional Chinese edition is linked above.

## Quick start

Not every tutorial video is updated yet.

### Installation

**Rhino**

1. Open Rhino 8 and run `PackageManager`.
2. Search for **`loopflow Rhino to Blender Sync`** and install.
3. Or download `loopflow-rhino-to-blender-sync-3.0.4-rh8_0-win.yak` from [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) and install from file.
4. **Quit Rhino completely and reopen it.**
5. Use the **Rhino to Blender Sync** toolbar. If it does not appear: **Tools → Options → Plug-ins**, enable **LoopFlow R2B**. If it still does not show, type `RBOpen` once.

The first product command copies the Blender zip to `Documents\LoopFlow\Rhino to Blender Sync`. After you install a new version, that command empties this product folder and copies the official files from the package. The same version does nothing.

**Blender**

Use **Edit → Preferences → Add-ons → Install from Disk** (legacy Add-ons). Do not use Get Extensions.

1. Remove or disable any leftover **import_3dm** or **LoopFlow Rhino to Blender Sync** / **loopflow_r2b_sync**.
2. **Quit Blender completely.** If Portable Blender lives on Dropbox, pause Dropbox first.
3. Delete leftover folders if they exist:
   - `portable\extensions\user_default\loopflow_r2b_sync`
   - `portable\extensions\user_default\loopflow_r2b_sync@`
   - `portable\scripts\addons\loopflow_r2b_sync`
4. Run any Rhino product command so the zip is copied to `Documents\LoopFlow\Rhino to Blender Sync`. Use that new zip, not an old one.
5. In Blender, open **Add-ons** (not Get Extensions) and **Install from Disk**. Pick the **zip** only.
6. Enable **LoopFlow Rhino to Blender Sync**. N-panel tab **LoopFlow**, bar **Rhino to Blender Sync**.
7. You do not need a separate Import Rhinoceros 3D add-on.

If Windows says the file is in use: quit Blender, pause Dropbox, delete the leftover folders, and install again.

Full command notes: [documentation](./docs/README.md).

## Basic workflow

1. Save the `.3dm` (unpublished files cannot publish).
2. Run `RBOpen` to check the config folder and last-good times.
3. For models, run `RBModels` (with materials) or `RBObjects` (selection, no materials).
4. For camera or lights, turn auto-sync on, or push once.
5. In Blender, point Work Folder at the same folder as the `.3dm`, then Sync / Update / Import.

Every step is started by you. If one channel fails, rerun that channel. You do not have to rebuild the whole scene.

## Support

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/discussions)
- [Issues](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/issues)
- [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases)

LoopFlow is a solo project by an architect and interior designer. AI assists with code and documentation; workflow, design decisions, and production checks stay with the author.

Response times vary with project workload.

## Related projects

- [LoopFlow｜Half-automatic 2D/3D Sync](https://github.com/ChihyuTsai-Oli/LoopFlow)
- [LoopFlow｜Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync)
- [LoopFlow ToolBox](./docs/TOOLBOX.md) (optional Blender tools; docs and download on that page)

## License and credits

Released under the [MIT License](./LICENSE). See [CREDITS](./CREDITS.md).
