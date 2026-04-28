# -*- coding: utf-8 -*-
"""
============================================================
Script Name        : LiveLink R2B Quick Open Utility
Version            : v1.0
Date               : 2026-04-28
Author             : Cursor + Claude Sonnet 4.6
Environment        : Rhino 8 (CPython 3.9) / Python 3
============================================================
[Description]
Provides three quick-open options from the Rhino command line:
  Config     → Open R2B_Path.txt config file
  DataFolder → Open the Data\ folder
  DebugLog   → Open cursor_R2B_debug_log.txt debug log

[Rhino Toolbar Button Macro]
  ! _-RunPythonScript "%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B\Py\LiveLink_R2B_Open.py"
============================================================
"""
import rhinoscriptsyntax as rs
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from LiveLink_R2B__Config import CONFIG_FILE, DATA_DIR, DEBUG_LOG_FILE, load_r2b_config

mode = rs.GetString("R2B Open", "Config", ["Config", "DataFolder", "DebugLog"])

if not mode:
    pass  # User pressed Esc — exit silently

elif mode == "Config":
    load_r2b_config()  # Ensure config file exists
    os.startfile(CONFIG_FILE)
    print("R2B: Opened {}".format(CONFIG_FILE))

elif mode == "DataFolder":
    if not os.path.exists(DATA_DIR):
        load_r2b_config()  # Trigger auto-creation of Data\ directory
    os.startfile(DATA_DIR)
    print("R2B: Opened {}".format(DATA_DIR))

elif mode == "DebugLog":
    load_r2b_config()  # Ensure Data\ directory exists
    if not os.path.exists(DEBUG_LOG_FILE):
        open(DEBUG_LOG_FILE, 'a').close()  # Create empty log on first use
    os.startfile(DEBUG_LOG_FILE)
    print("R2B: Opened {}".format(DEBUG_LOG_FILE))
