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
    COLOR_SOCKET,
    DEFAULT_SCALE_XYZ,
    DEFAULT_SIZE_M,
    GROUP_VERSION,
    IMAGE_NODE_NAMES,
    MAP_SLOTS,
    NODE_LABEL,
    NODE_WIDTH_SCALE,
    classify_pbr_filename,
    classify_pbr_files,
    scale_from_size_meters,
)

ADDON = SRC / "blender" / "loopflow_r2b_sync_dev" / "__init__.py"
BOX_PROJ = SRC / "blender" / "loopflow_r2b_sync_dev" / "box_proj.py"
OSL = SRC / "blender" / "loopflow_r2b_sync_dev" / "box_projection.osl"


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
        self.assertEqual(DEFAULT_SCALE_XYZ, (1.0, 1.0, 1.0))
        self.assertEqual(NODE_LABEL, "LoopFlow Box Projection")
        self.assertEqual(COLOR_SOCKET, "Color")
        self.assertEqual(GROUP_VERSION, 7)
        self.assertEqual(NODE_WIDTH_SCALE, 1.5)
        self.assertEqual(len(MAP_SLOTS), 4)
        self.assertEqual(len(IMAGE_NODE_NAMES["color"]), 3)

    def test_classify_pbr_filenames(self):
        self.assertEqual(classify_pbr_filename("Brick_Base_Color.png"), "color")
        self.assertEqual(classify_pbr_filename("brick_albedo.jpg"), "color")
        self.assertEqual(classify_pbr_filename("brick_diff.tif"), "color")
        self.assertEqual(classify_pbr_filename("brick_roughness.png"), "roughness")
        self.assertEqual(classify_pbr_filename("brick_rough.png"), "roughness")
        self.assertEqual(classify_pbr_filename("brick_metallic.png"), "metallic")
        self.assertEqual(classify_pbr_filename("brick_metal.png"), "metallic")
        self.assertEqual(classify_pbr_filename("brick_normal.png"), "normal")
        self.assertEqual(classify_pbr_filename("brick_nor.png"), "normal")
        self.assertEqual(classify_pbr_filename("brick_nrm.png"), "normal")
        self.assertIsNone(classify_pbr_filename("readme.txt"))
        self.assertIsNone(classify_pbr_filename("north_wall.png"))
        classified = classify_pbr_files(
            [
                "D:/tex/wood_BaseColor.png",
                "D:/tex/wood_Roughness.png",
                "D:/tex/wood_Metallic.png",
                "D:/tex/wood_Normal.png",
                "D:/tex/notes.txt",
            ]
        )
        self.assertEqual(classified["color"], "D:/tex/wood_BaseColor.png")
        self.assertEqual(classified["roughness"], "D:/tex/wood_Roughness.png")
        self.assertEqual(classified["metallic"], "D:/tex/wood_Metallic.png")
        self.assertEqual(classified["normal"], "D:/tex/wood_Normal.png")

    def test_box_proj_module_compiles(self):
        py_compile.compile(str(SRC / "foundation" / "box_mapping.py"), doraise=True)
        py_compile.compile(str(BOX_PROJ), doraise=True)

    def test_osl_kept_as_math_reference(self):
        self.assertTrue(OSL.is_file(), OSL)
        src = OSL.read_text(encoding="utf-8")
        self.assertIn("loopflow_inv_euler_xyz", src)
        self.assertIn("loopflow_rot_z", src)
        self.assertIn("1e-8", src)
        self.assertNotIn("0.0001", src)

    def test_shader_editor_panel_not_on_view3d_sync_bar(self):
        tree = ast.parse(BOX_PROJ.read_text(encoding="utf-8"))
        panel = None
        operator = None
        load_op = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if node.name == "LOOPFLOW_R2B_DEV_PT_box_projection":
                    panel = node
                if node.name == "LOOPFLOW_R2B_DEV_OT_add_box_projection":
                    operator = node
                if node.name == "LOOPFLOW_R2B_DEV_OT_load_pbr_maps":
                    load_op = node
        self.assertIsNotNone(panel)
        self.assertIsNotNone(operator)
        self.assertIsNotNone(load_op)
        self.assertTrue(ast.get_docstring(operator))
        self.assertTrue(ast.get_docstring(load_op))
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

        addon = ADDON.read_text(encoding="utf-8")
        self.assertIn("box_proj", addon)
        self.assertIn("box_proj.CLASSES", addon)
        self.assertIn("box_proj.register_props", addon)
        sync_panel = addon.split("class LOOPFLOW_R2B_DEV_PT_panel")[1]
        self.assertNotIn("add_box_projection", sync_panel)
        self.assertNotIn("Box Projection", sync_panel.split("_CLASSES")[0])

        src = BOX_PROJ.read_text(encoding="utf-8")
        self.assertIn("load_pbr_maps", src)
        self.assertIn("box_space", src)
        self.assertIn("ShaderNodeTexCoord", src)
        self.assertIn("ShaderNodeVectorTransform", src)
        self.assertIn("convert_to", src)
        self.assertIn("SPACE_SOCKET", src)
        self.assertIn("ImportHelper", src)
        self.assertIn("connect_group_to_principled", src)
        self.assertIn("ShaderNodeNormalMap", src)
        self.assertIn("r2b_box_roughness", src)
        self.assertIn("r2b_box_metallic", src)
        self.assertIn("r2b_box_normal", src)
        self.assertIn("IMAGE_NODE_NAMES", src)
        self.assertIn("AXIS_ANGLE", src)
        self.assertIn("NODE_WIDTH_SCALE", src)
        self.assertIn("1e-8", src)
        self.assertNotIn("0.0001", src)
        self.assertNotIn("ShaderNodeScript", src)
        self.assertNotIn("shading_system", src)
        self.assertNotIn("ShaderNodeUVMap", src)
        self.assertNotIn("uv.cube_project", src)


if __name__ == "__main__":
    unittest.main()
