# Changelog

## [1.0.0] - 2026-04-28

First public release.

### Rhino-Side Scripts
- **LiveLink_R2B_Models** — One-click 3DM export with auto scene cleanup, material standardisation, and Box Mapping
- **LiveLink_R2B_Camera** — Toggle-based live camera sync; writes viewport data to JSON on every rotation/zoom
- **LiveLink_R2B_Light** — Scans Point objects and exports light position data for Blender auto-alignment
- **LiveLink_R2B_Open** — Quick open utility for config file, data folder, and debug log

### Blender Side — LoopFlow_import_3dm (Required)
- **Import Models / Update Models** — First-time import and seamless geometry updates preserving all layer, hide, exclude, and Bounds states
- **Start / Stop Camera Sync** — Background polling of `R2B_Camera_Sync.json` for real-time viewport sync
- **Sync Rhino Lights** — One-click fixture alignment from `R2B_Light_Sync.json` with orphan cleanup

### Blender Side — LoopFlow Toolkit (Optional)
- **Export Tools** — Batch and selective USDZ export for Collections
- **Rename Tools** — Sequential naming for Collections and Objects with instance dual-counter
- **Selection Tools** — Group, Un-Group, Re-Group, Select All in Group, Delete From Group, Material Isolator
