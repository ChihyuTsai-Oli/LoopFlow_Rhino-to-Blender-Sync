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
    "R2B_Objects.py",
    "R2B_Camera.py",
    "R2B_Camera_Push.py",
    "R2B_Light.py",
    "R2B_Light_Push.py",
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
        self.assertIn("Not implemented", stub_message("R2B_Models"))

    def test_entrypoint_scripts_compile(self):
        for name in REQUIRED_ENTRYPOINTS:
            py_compile.compile(str(ENTRYPOINTS / name), doraise=True)
            text = (ENTRYPOINTS / name).read_text(encoding="utf-8")
            self.assertIn("_prepare_src", text)
            self.assertIn("_isolate.py", text)
        self.assertTrue((ENTRYPOINTS / "_isolate.py").is_file())

    def test_foundation_compile(self):
        self.assertTrue(compileall.compile_dir(str(SRC / "foundation"), quiet=1))

    def test_open_health_modules_compile(self):
        py_compile.compile(str(SRC / "foundation" / "health.py"), doraise=True)
        py_compile.compile(str(SRC / "rhino" / "commands" / "open.py"), doraise=True)
        py_compile.compile(
            str(SRC / "blender" / "loopflow_r2b_sync_dev" / "health_sync.py"),
            doraise=True,
        )
        open_py = (SRC / "rhino" / "commands" / "open.py").read_text(encoding="utf-8")
        order = ('Open Config', 'Open live', 'Open models', 'Open Docs')
        found = [open_py.find('"{}"'.format(name)) for name in order]
        self.assertTrue(all(i > 0 for i in found), found)
        self.assertEqual(found, sorted(found))
        self.assertNotIn('Text = "Close"', open_py)

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
        self.assertEqual(bl_info["version"], (0, 0, 9))

    def test_addon_registers_expected_stub_idnames(self):
        text = ADDON.read_text(encoding="utf-8")
        self.assertIn('bl_idname = "loopflow_r2b_dev.stub"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.reset_paths"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.update_models"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.import_models"', text)
        self.assertIn("ImportHelper", text)
        self.assertIn("fileselect_add", text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.camera_auto_on"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.camera_push"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.light_auto_on"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.sync_lights"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.open_health"', text)
        self.assertIn('bl_idname = "loopflow_r2b_dev.open_docs"', text)
        self.assertIn('bl_category = "LoopFlow"', text)
        self.assertIn('bl_label = "Rhino to Blender Sync"', text)
        self.assertNotIn("LoopFlow R2B Dev", text)
        self.assertIn("Work Folder", text)
        self.assertNotIn("作業資料夾", text)
        for label in (
            "Update Models",
            "Sync Models",
            "Import Objects",
            "Camera Auto On",
            "Camera Push Once",
            "Light Auto On",
            "Sync Lights",
            "Open / Health",
            "Open Docs",
        ):
            self.assertIn(label, text)
        self.assertNotIn('text="Import Models"', text)

    def test_addon_operator_hover_docstrings(self):
        tree = ast.parse(ADDON.read_text(encoding="utf-8"))
        required = (
            "LOOPFLOW_R2B_DEV_OT_reset_paths",
            "LOOPFLOW_R2B_DEV_OT_update_models",
            "LOOPFLOW_R2B_DEV_OT_import_models",
            "LOOPFLOW_R2B_DEV_OT_import_objects",
            "LOOPFLOW_R2B_DEV_OT_camera_auto_on",
            "LOOPFLOW_R2B_DEV_OT_camera_auto_off",
            "LOOPFLOW_R2B_DEV_OT_camera_push",
            "LOOPFLOW_R2B_DEV_OT_light_auto_on",
            "LOOPFLOW_R2B_DEV_OT_light_auto_off",
            "LOOPFLOW_R2B_DEV_OT_sync_lights",
            "LOOPFLOW_R2B_DEV_OT_open_health",
            "LOOPFLOW_R2B_DEV_OT_open_docs",
        )
        found = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in required:
                found[node.name] = ast.get_docstring(node)
        self.assertEqual(set(found), set(required))
        for name, doc in found.items():
            self.assertTrue(doc and doc.strip(), name)
        text = ADDON.read_text(encoding="utf-8")
        self.assertIn("def description(", text)
        self.assertIn("Hover for last-good file times", text)
        self.assertNotIn("popup_menu", text)


if __name__ == "__main__":
    unittest.main()
