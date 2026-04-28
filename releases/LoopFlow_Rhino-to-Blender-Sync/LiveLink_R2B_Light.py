# -*- coding: utf-8 -*-
"""
=================================
LiveLink Rhino to Blender (Light Sender)
=================================
Script Name        : LiveLink_R2B_Light
Version            : v1.0
Date               : 2026-04-28
Author             : Cursor + Claude Sonnet 4.6
Environment        : Rhino 8 / CPython 3.9
Sync File          : Determined by the LightFile field in R2B_Path.txt (default: R2B_Light_Sync.json)

[System Overview]
This script is the light-point manual export engine on the Rhino side.
It converts Point objects in the Rhino scene into BIM light assembly data.

[Features & Operations]
- Reads R2B_Path.txt automatically; scans only the layer (and sublayers) specified by LightLayer.
- Auto-generates config: if R2B_Path.txt is missing, it is created with all default fields.
- Extracts the terminal sub-layer name of each point as the fixture template type.
- Extracts XYZ world coordinates of each point.
- Packages all matching points and writes them to the DataPath directory.

How to use:
- Verify the LightLayer setting in R2B_Path.txt is correct.
- Place Point objects in the designated layer (e.g. R2B_LT_Points::Downlight) to mark light positions.
- Run this script; the command line reports the number of points exported, then switch to Blender to sync.

[Variable Notes]
- R2B_Path.txt: managed centrally by LiveLink_R2B__Config.py, independent of doc.Path.
- LightLayer: prefix for target_layer; sublayers matched with startswith.
- layer_short: the last segment after splitting by "::", used as the fixture template type on the Blender side.
- JSON output path is determined by DataPath + LightFile, independent of doc.Path.
"""
import rhinoscriptsyntax as rs
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B__Config import load_r2b_config, DATA_DIR

def export_lights():
    """Manual run: scan point objects per R2B_Path.txt settings and write the Lights JSON."""
    cfg = load_r2b_config()
    target_layer = cfg["LightLayer"]
    target_prefix = target_layer  # startswith match

    # 2. Collect all Point objects in the scene (type code 1)
    points = rs.ObjectsByType(1)
    data = {"points": []}

    if points:
        for pt in points:
            layer_full = rs.ObjectLayer(pt)

            if not layer_full.startswith(target_prefix):
                continue

            # Strip parent layers and keep only the terminal sub-layer name as fixture Type
            layer_short = layer_full.split("::")[-1]
            coord = rs.PointCoordinates(pt)

            data["points"].append({
                "guid": str(pt),
                "type": layer_short,
                "loc": [coord.X, coord.Y, coord.Z]
            })

    # 3. Write to DataPath + LightFile
    json_path = os.path.join(cfg["DataPath"], cfg["LightFile"])

    try:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        print("R2B Light: Export complete. {} point(s) packed. (Output: {})".format(
            len(data["points"]), json_path
        ))
    except Exception as e:
        print("R2B Light: Export failed: {}".format(e))

if __name__ == "__main__":
    export_lights()
