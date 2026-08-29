# -*- coding: utf-8 -*-
"""Box 投影純資料與 Shader Editor 面板骨架（不依賴 bpy GUI）。"""
from __future__ import annotations

import ast
import py_compile
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.box_mapping import (
    DEFAULT_SIZE_M,
    GROUP_NAME,
    scale_from_size_meters,
)

ADDON = SRC / "blender" / "loopflow_r2b_sync_dev" / "__init__.py"
BOX_PROJ = SRC / "blender" / "loopflow_r2b_sync_dev" / "box_proj.py"


class BoxMappingTests(unittest.TestCase):
    def test_scale_from_size_meters(self):
        self.assertEqual(scale_from_size_meters(1.0), 1.0)
        self.assertEqual(scale_from_size_meters(2.0), 0.5)
        self.assertAlmostEqual(scale_from_size_meters(0.5), 2.0)
        with self.assertRaises(ValueError):
            scale_from_size_meters(0)
        with self.assertRaises(ValueError):
            scale_from_size_meters(-1)
        self.assertEqual(DEFAULT_SIZE_M, 1.0)
        self.assertEqual(GROUP_NAME, "LoopFlow Box Projection")

    def test_box_proj_module_compiles(self):
        py_compile.compile(str(SRC / "foundation" / "box_mapping.py"), doraise=True)
        py_compile.compile(str(BOX_PROJ), doraise=True)

    def test_shader_editor_panel_not_on_view3d_sync_bar(self):
        tree = ast.parse(BOX_PROJ.read_text(encoding="utf-8"))
        panel = None
        operator = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if node.name == "LOOPFLOW_R2B_DEV_PT_box_projection":
                    panel = node
                if node.name == "LOOPFLOW_R2B_DEV_OT_add_box_projection":
                    operator = node
        self.assertIsNotNone(panel)
        self.assertIsNotNone(operator)
        self.assertTrue(ast.get_docstring(operator))
        assigns = {}
        for item in panel.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        assigns[target.id] = ast.literal_eval(item.value)
        self.assertEqual(assigns["bl_space_type"], "NODE_EDITOR")
        self.assertEqual(assigns["bl_region_type"], "UI")
        self.assertEqual(assigns["bl_category"], "LoopFlow")
        self.assertEqual(assigns["bl_label"], "Box Projection")
        self.assertNotEqual(assigns["bl_label"], "Rhino to Blender Sync")

        addon = ADDON.read_text(encoding="utf-8")
        self.assertIn("box_proj", addon)
        self.assertIn("box_proj.CLASSES", addon)
        self.assertNotIn("Add Box Projection", addon.split("class LOOPFLOW_R2B_DEV_PT_panel")[1].split("class ")[0] if "class LOOPFLOW_R2B_DEV_PT_panel" in addon else addon)
        sync_panel = addon.split("class LOOPFLOW_R2B_DEV_PT_panel")[1]
        self.assertNotIn("add_box_projection", sync_panel)
        self.assertNotIn("Box Projection", sync_panel.split("_CLASSES")[0])

        src = BOX_PROJ.read_text(encoding="utf-8")
        self.assertIn("projection = \"BOX\"", src)
        self.assertIn('outputs["Object"]', src)
        self.assertIn("ShaderNodeMapping", src)
        self.assertNotIn("ShaderNodeUVMap", src)
        self.assertNotIn("uv.cube_project", src)


if __name__ == "__main__":
    unittest.main()
