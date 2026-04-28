# -*- coding: utf-8 -*-
"""
=================================================
LiveLink Rhino to Blender (Model Exporter)
=================================================
Script Name        : LiveLink_R2B_Models
Version            : v1.0
Date               : 2026-04-28
Author             : Cursor + Claude Sonnet 4.6
Environment        : Rhino 8 / CPython 3.9
Sync File          : Determined by the ModelFile field in R2B_Path.txt (default: R2B.3dm)

[System Overview]
This script optimises the render collaboration workflow between Rhino and Blender.
Through automated processing it ensures the exported model reaches
a clean "plug-and-play" state for Blender.

[Features & Operations]
1. Layer selection: a layer picker appears on each run; only the chosen parent layer and
   its sublayers are exported. The last selection is remembered in R2B_Path.txt (LastModelLayer).
2. Output path: writes to ModelDir when set; falls back to the Rhino working file's directory if empty.
3. Deep scene cleanup: auto-deletes Layouts, points, curves, text dots, annotations, and hatches.
4. Layer optimisation: shows/unlocks all layers; deletes helper layers containing "//" and their objects.
5. Material standardisation: syncs material definitions with layer colours and converts them to a
   structure recognisable by Blender.
6. UV standardisation: clears all existing mapping channels and applies a uniform
   BoxMapSize × BoxMapSize × BoxMapSize Box Mapping.

How to use:
- Save the Rhino file, then run this script and select the model layer in the popup.
- After completion the script automatically returns to the original working file; the
  intermediate file remains in the target directory for Blender to import.

[Variable Notes]
- orig_full_path: obtained from sc.doc.Path; the Rhino file must be saved first.
- export_full_path: ModelDir (fallback to Rhino working file directory if empty) + ModelFile.
- BoxMapSize: read from the BoxMapSize field in R2B_Path.txt; default 500.
- LastModelLayer: remembers the last chosen layer as the default for the next run.
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B__Config import load_r2b_config, save_r2b_config

def RhinoLiveLinkSync():
    # --- 1. Environment setup and path check ---
    orig_full_path = sc.doc.Path
    if not orig_full_path:
        rs.MessageBox("Please save the current Rhino file first!")
        return

    cfg = load_r2b_config()

    # --- 2. Layer picker (remembers last selection) ---
    last_layer = cfg.get("LastModelLayer") or None
    target_layer = rs.GetLayer("Select the model layer to export", layer=last_layer)
    if not target_layer:
        return
    cfg["LastModelLayer"] = target_layer
    save_r2b_config(cfg)

    # --- 3. Determine output path ---
    model_dir = cfg.get("ModelDir", "").strip() or os.path.dirname(orig_full_path)
    export_full_path = os.path.join(model_dir, cfg["ModelFile"])

    # BoxMapSize setting
    box_size = cfg.get("BoxMapSize", "500").strip() or "500"

    # Disable redraw for better performance
    rs.EnableRedraw(False)

    try:
        # --- 4. Add a safety box (prevents Export from failing on an empty scene) ---
        pts = [[0,0,0], [1,0,0], [1,1,0], [0,1,0], [0,0,1], [1,0,1], [1,1,1], [0,1,1]]
        rs.AddBox(pts)

        # --- 5. Filter objects by the selected layer ---
        rs.UnselectAllObjects()

        # Unlock/show all layers first
        for layer in sc.doc.Layers:
            if not layer.IsDeleted:
                layer.IsLocked = False
                layer.IsVisible = True
                layer.CommitChanges()

        rs.Command("_Show _Unlock", False)

        # Select objects inside the target layer (and its sublayers)
        target_fullpaths = set()
        for layer in sc.doc.Layers:
            if layer is None or layer.IsDeleted:
                continue
            fp = layer.FullPath
            if fp == target_layer or fp.startswith(target_layer + "::"):
                target_fullpaths.add(fp)

        if not target_fullpaths:
            print("R2B Models: Target layer '{}' not found. Export cancelled.".format(target_layer))
            return

        for layer_fp in target_fullpaths:
            layer_objs = rs.ObjectsByLayer(layer_fp)
            if layer_objs:
                rs.SelectObjects(layer_objs)

        # Include safety box (ensures at least one object is available for export)
        rs.Command("_SelAll", False)

        if os.path.exists(export_full_path):
            try:
                os.remove(export_full_path)
            except Exception:
                pass

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        # --- 6. Run export ---
        quote = chr(34)
        export_cmd = '_-ExportWithOrigin _0,0,0 ' + quote + export_full_path + quote + ' _Enter _Enter'
        rs.Command(export_cmd, False)

        # --- 7. Open intermediate file and clean it up ---
        rs.DocumentModified(False)
        rs.Command('_-Open ' + quote + export_full_path + quote + ' _Enter', False)

        # =========================================================
        # Silent API cleanup
        # =========================================================
        pages = sc.doc.Views.GetPageViews()
        if pages:
            for page in pages:
                try:
                    page.Close()
                except Exception:
                    pass

        for layer in sc.doc.Layers:
            if not layer.IsDeleted:
                layer.IsLocked = False
                layer.IsVisible = True
                layer.CommitChanges()

        for layer in sc.doc.Layers:
            if not layer.IsDeleted and "//" in layer.FullPath:
                layer_objs = rs.ObjectsByLayer(layer.FullPath)
                if layer_objs:
                    rs.DeleteObjects(layer_objs)

        for obj_type in [1, 4, 512, 8192, 65536]:
            useless_objs = rs.ObjectsByType(obj_type)
            if useless_objs:
                rs.DeleteObjects(useless_objs)

        # =========================================================
        # Command sequence
        # =========================================================
        rs.Command("_ExplodeBlock _AllBlocks", False)
        rs.Command("_SelAll _UngroupAll _SelNone", False)

        for layer in sc.doc.Layers:
            if layer.IsDeleted:
                continue
            path_parts = layer.FullPath.split("::")
            short_name = "::".join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
            temp_mat = Rhino.DocObjects.Material()
            temp_mat.Name = short_name
            temp_mat.DiffuseColor = layer.Color
            render_mat = Rhino.Render.RenderMaterial.CreateBasicMaterial(temp_mat, sc.doc)
            sc.doc.RenderMaterials.Add(render_mat)
            layer.RenderMaterial = render_mat

        for obj in sc.doc.Objects:
            attr = obj.Attributes
            attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
            obj.CommitChanges()

        rs.Command("_SelAll", False)
        rs.Command("_-RemoveMappingChannel 1 _Enter", False)
        mapping_macro = "-ApplyBoxMapping _Center 0,0,0 {0} {0} {0} _Yes _Single _Enter _Enter _Enter".format(box_size)
        rs.Command(mapping_macro, False)
        rs.Command("_SelNone", False)

        purge_cmd = "_-Purge _BlockDefinitions=Yes _AnnotationStyles=Yes _Groups=Yes _HatchPatterns=Yes _Layers=Yes _Linetypes=Yes _Materials=Yes _Textures=Yes _Environments=Yes _Bitmaps=Yes _Enter"
        rs.Command(purge_cmd, False)

        # =========================================================
        # Save and seamless switch back
        # =========================================================
        save_cmd = '_-SaveAs _Version=8 "{}" _Enter'.format(export_full_path)
        rs.Command(save_cmd, False)

        rs.DocumentModified(False)
        return_cmd = '_-Open "{}" _Enter'.format(orig_full_path)
        rs.Command(return_cmd, False)

    finally:
        rs.EnableRedraw(True)
        print("R2B Models: Export complete. Returned to working file. (Output: {})".format(export_full_path))

if __name__ == "__main__":
    RhinoLiveLinkSync()
