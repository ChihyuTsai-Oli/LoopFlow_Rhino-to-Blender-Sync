# -*- coding: utf-8 -*-
"""
=================================
LiveLink Rhino to Blender (Camera Sender)
=================================
Script Name        : LiveLink_R2B_Camera
Version            : v1.0
Date               : 2026-04-28
Author             : Cursor + Claude Sonnet 4.6
Environment        : Rhino 8 / CPython 3.9
Sync File          : Determined by the CameraFile field in R2B_Path.txt (default: R2B_Camera_Sync.json)

[System Overview]
This script is the camera real-time sync engine on the Rhino side.
It uses background event listening to capture viewport changes and writes a
lightweight JSON file, enabling live camera linkage.

[Features & Operations]
- Toggle design: run once to start, run again to stop.
- Binds to the `RhinoView.Modified` event, triggered only on rotation or zoom.
- Extracts only camera XYZ position, direction vector, up vector, and lens length.
- Writes to the DataPath directory specified in R2B_Path.txt.

[Variable Notes]
- event_key: key name in sc.sticky; must match the identifier used by the Blender R2B_Camera listener.
- Output path is determined by DataPath + CameraFile from R2B_Path.txt (independent of doc.Path).
- If the active window has no ActiveView, export_camera silently skips that update.
"""
import Rhino
import scriptcontext as sc
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B__Config import load_r2b_config, DATA_DIR

def export_camera(sender, e):
    """Background handler: writes a minimal Camera JSON whenever the viewport changes."""
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return

    if not doc.Views.ActiveView:
        return

    vp = doc.Views.ActiveView.ActiveViewport

    # Extract only the minimal camera data
    data = {
        "location":  {"x": vp.CameraLocation.X,  "y": vp.CameraLocation.Y,  "z": vp.CameraLocation.Z},
        "direction": {"x": vp.CameraDirection.X,  "y": vp.CameraDirection.Y, "z": vp.CameraDirection.Z},
        "up":        {"x": vp.CameraUp.X,          "y": vp.CameraUp.Y,        "z": vp.CameraUp.Z},
        "lens": vp.Camera35mmLensLength
    }

    # Output to DataPath + CameraFile (cached in sticky at toggle time to avoid per-frame config reads)
    json_path = sc.sticky.get("R2B_CAMERA_JSON_PATH",
                              os.path.join(DATA_DIR, "R2B_Camera_Sync.json"))

    try:
        with open(json_path, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass  # Suppress errors if the file is locked, to avoid interrupting modelling

def toggle_camera_sync():
    """Start or stop the background event listener."""
    event_key = "R2B_Camera_Sync_Event"

    if sc.sticky.has_key(event_key):
        # Already running — stop and unbind
        func = sc.sticky[event_key]
        try:
            Rhino.Display.RhinoView.Modified -= func
        except Exception:
            pass
        del sc.sticky[event_key]
        if sc.sticky.has_key("R2B_CAMERA_JSON_PATH"):
            del sc.sticky["R2B_CAMERA_JSON_PATH"]
        print("R2B Camera Sync: Live sync stopped.")
    else:
        # Load config and pre-compute output path
        cfg = load_r2b_config()
        json_path = os.path.join(cfg["DataPath"], cfg["CameraFile"])
        sc.sticky["R2B_CAMERA_JSON_PATH"] = json_path

        sc.sticky[event_key] = export_camera
        Rhino.Display.RhinoView.Modified += export_camera
        print("R2B Camera Sync: Live sync started. (Output: {})".format(json_path))

if __name__ == "__main__":
    toggle_camera_sync()
