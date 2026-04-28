# LoopFlow｜Rhino to Blender Sync

[▶ How it works（YouTube）](https://www.youtube.com/playlist?list=PLiJmu8T_uzJJTnDl6HLSOFZ3DimkI9bV8) · [▶ Releases](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/releases) · [▶ User Guide](./docs/USER_GUIDE.md)

## Key Features

- **Model Sync** — One-click 3DM export; update geometry in Blender at any time while preserving all materials
- **Camera Sync** — Mirrors the active Rhino viewport to the Blender camera
- **Light Alignment** — Rhino Points sync; lights and fixtures auto-align to point positions in Blender

## How Material Sync Works

The core feature is model sync — no matter how many times you sync, materials stay connected. Using the import_3dm addon, I built an export mechanism that generates a clean, Blender-ready model from any state of your Rhino file with one click. One click to export from Rhino, one click to import in Blender. That's it.

## Modular by Design

Every sync function is independent. Use model sync only, light sync only, or any combination — there's no fixed sequence. Pick what you need, skip what you don't.

## Why Blender?

It's open source — meaning it's free. It's also genuinely enjoyable to work with, the native Cycles render engine is more than capable, and it has an enormous library of resources and community support.

## Installation

See **[releases/README.md](releases/README.md)** for step-by-step setup instructions.

## You Might Also Like

- [LoopFlow｜Half-automatic 2D/3D Sync](https://github.com/ChihyuTsai-Oli/LoopFlow)
- [LoopFlow｜Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync)

## Credits

- **LoopFlow_import_3dm** is a fork of [import_3dm](https://github.com/jesterKing/import_3dm) by [Nathan Letwory (jesterKing)](https://github.com/jesterKing), licensed under MIT

---

*Last updated: April 2026*