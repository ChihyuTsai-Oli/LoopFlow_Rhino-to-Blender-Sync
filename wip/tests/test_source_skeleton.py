# -*- coding: utf-8 -*-
"""來源骨架自動檢查（不依賴 Rhino／Blender GUI；標準庫 unittest）。"""
from __future__ import annotations

import ast
import compileall
import py_compile
import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRYPOINTS = SRC / "rhino" / "entrypoints"
ADDON = SRC / "blender" / "loopflow_r2b_sync_dev" / "__init__.py"

REQUIRED_ENTRYPOINTS = (
    "R2B_Models.py",
    "R2B_Camera.py",
    "R2B_Light.py",
    "R2B_Open.py",
)


class SourceSkeletonTests(unittest.TestCase):
    def test_entrypoint_files_exist(self):
        for name in REQUIRED_ENTRYPOINTS:
            self.assertTrue((ENTRYPOINTS / name).is_file(), name)

    def test_foundation_stub_message(self):
        sys.path.insert(0, str(SRC))
        from foundation.stub import stub_message

        self.assertIn("R2B_Models", stub_message("R2B_Models"))
        self.assertIn("尚未實作", stub_message("R2B_Models"))

    def test_entrypoint_scripts_compile(self):
        for name in REQUIRED_ENTRYPOINTS:
            py_compile.compile(str(ENTRYPOINTS / name), doraise=True)

    def test_foundation_compile(self):
        self.assertTrue(compileall.compile_dir(str(SRC / "foundation"), quiet=1))

    def test_addon_bl_info_without_importing_bpy(self):
        tree = ast.parse(ADDON.read_text(encoding="utf-8"))
        bl_info = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "bl_info":
                        bl_info = ast.literal_eval(node.value)
        self.assertIsNotNone(bl_info)
        self.assertEqual(bl_info["author"], "Chihyu Tsai")
        self.assertEqual(bl_info["blender"], (5, 2, 1))
        self.assertIn("Dev Stub", bl_info["name"])
        self.assertEqual(bl_info["version"], (0, 0, 2))

    def test_addon_registers_expected_stub_idnames(self):
        text = ADDON.read_text(encoding="utf-8")
        self.assertIn('bl_idname = "loopflow_r2b_dev.stub"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.camera_auto_on"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.camera_push"', text)
        self.assertIn('bl_category = "LoopFlow R2B Dev"', text)
        for label in (
            "Update Models",
            "Camera Auto On",
            "Camera Push Once",
            "Sync Lights",
            "Open / Health",
        ):
            self.assertIn(label, text)


if __name__ == "__main__":
    unittest.main()
