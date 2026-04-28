# -*- coding: utf-8 -*-
"""
============================================================
Module Name        : LiveLink_R2B__Config
Version            : v1.0
Date               : 2026-04-28
Author             : Cursor + Claude Sonnet 4.6
Environment        : Rhino 8 (CPython 3.9) / Python 3
============================================================
[Description]
Shared configuration module for the LiveLink R2B script series.
Centralizes reading, writing, and default values for R2B_Path.txt,
ensuring consistent configuration logic across all scripts.

[Install Location]
%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Py\LiveLink_R2B__Config.py

[Usage]
Add the following lines to the top of each script:
    import os, sys
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _HERE)
    from LiveLink_R2B__Config import load_r2b_config, save_r2b_config, DATA_DIR

[Variable Notes]
- Config file : %APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\R2B_Path.txt
- Debug log   : %APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Data\cursor_R2B_debug_log.txt
============================================================
"""
import os

# ── Global path resolution (auto-derived from install location, no hard-coding) ──
_PYTHON_DIR    = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR    = os.path.dirname(_PYTHON_DIR)
DATA_DIR       = os.path.join(INSTALL_DIR, "Data")
CONFIG_FILE    = os.path.join(DATA_DIR, "R2B_Path.txt")
DEBUG_LOG_FILE = os.path.join(DATA_DIR, "cursor_R2B_debug_log.txt")

# Complete default values shared by all scripts (single source of truth)
DEFAULT_CONFIG = {
    "DataPath":       DATA_DIR,
    "ModelDir":       "",           # Empty = fallback to same directory as Rhino working file
    "LightLayer":     "R2B_LT_Points",
    "CameraFile":     "R2B_Camera_Sync.json",
    "LightFile":      "R2B_Light_Sync.json",
    "ModelFile":      "R2B.3dm",
    "BoxMapSize":     "500",
    "LastModelLayer": "",
}

# Field order when writing the config file
_FIELD_ORDER = [
    "DataPath",
    "ModelDir",
    "LightLayer",
    "CameraFile",
    "LightFile",
    "ModelFile",
    "BoxMapSize",
    "LastModelLayer",
]


def load_r2b_config():
    """
    Load the global config file R2B_Path.txt.
    - If missing: auto-create and write all default fields.
    - If present but incomplete: backfill missing fields and rewrite.
    - Ensures the DataPath directory exists.
    """
    config = DEFAULT_CONFIG.copy()

    if not os.path.exists(CONFIG_FILE):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        save_r2b_config(config)
    else:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip()
                        val = parts[1].strip()
                        if key in config:
                            config[key] = val
        except Exception:
            pass

        # Backfill any missing fields
        needs_update = False
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            for key in _FIELD_ORDER:
                if (key + ":") not in content:
                    needs_update = True
                    break
        except Exception:
            needs_update = True

        if needs_update:
            save_r2b_config(config)

    if not os.path.exists(config["DataPath"]):
        try:
            os.makedirs(config["DataPath"])
        except Exception:
            pass

    return config


def save_r2b_config(config):
    """Write the config file in a fixed field order, preserving any user-modified values."""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
        except Exception:
            pass
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            for key in _FIELD_ORDER:
                f.write("{}: {}\n".format(key, config.get(key, DEFAULT_CONFIG.get(key, ""))))
    except Exception:
        pass
