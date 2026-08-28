# -*- coding: utf-8 -*-
"""Blender Open／Health：讀作業資料夾上的 last-good 時間。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import bpy

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from foundation.health import build_health_report
from foundation.paths import CONFIG_PARENT_NAME, PRODUCT_DIR_NAME, ensure_config_layout


def work_folder_from_scene(scene) -> str:
    folder = bpy.path.abspath(getattr(scene, "r2b_sync_folder", "") or "")
    if folder and os.path.isdir(folder):
        return folder
    blend = bpy.data.filepath
    if blend:
        return os.path.dirname(bpy.path.abspath(blend))
    return ""


def health_report_for_work_folder(work_folder: str) -> str:
    folder = Path(work_folder)
    root = folder / CONFIG_PARENT_NAME / PRODUCT_DIR_NAME
    return build_health_report(
        document="(Blender)",
        config_root=root,
        work_folder=folder,
    )


def open_config_root(work_folder: str) -> str:
    """開設定根；失敗回傳錯誤字串。"""
    folder = Path(work_folder)
    if not folder.is_dir():
        return "Work folder not found: {}".format(work_folder)
    root = ensure_config_layout(folder / CONFIG_PARENT_NAME / PRODUCT_DIR_NAME)
    try:
        os.startfile(str(root))
    except OSError as exc:
        return "Could not open folder: {}".format(exc)
    return ""
