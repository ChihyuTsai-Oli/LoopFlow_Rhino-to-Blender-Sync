# -*- coding: utf-8 -*-
"""ToolBox 獨立 add-on：清單、bl_info、不進 yak（不依賴 Blender GUI）。"""
from __future__ import annotations

import ast
import compileall
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ADDON = SRC / "blender" / "loopflow_toolbox"
FEATURES_PY = ADDON / "features" / "__init__.py"
DOCS = WIP / "docs" / "toolbox"
YAK_BUILD = WIP / "packaging" / "g02-spike" / "build.ps1"

EXPECTED_FEATURES = ("export", "rename", "selection")
EXPECTED_OPS = (
    "loopflow_toolbox.export_all_usd",
    "loopflow_toolbox.export_selected_usd",
    "loopflow_toolbox.select_all_cols",
    "loopflow_toolbox.rename_collections",
    "loopflow_toolbox.rename_objects_by_collections",
    "loopflow_toolbox.rename_objects",
    "loopflow_toolbox.group",
    "loopflow_toolbox.un_group",
    "loopflow_toolbox.re_group",
    "loopflow_toolbox.select_all_in_group",
    "loopflow_toolbox.delete_objects_from_group",
    "loopflow_toolbox.material_isolator",
)


def _features_tuple():
    tree = ast.parse(FEATURES_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "FEATURES":
                    return ast.literal_eval(node.value)
    raise AssertionError("FEATURES not found")


class ToolboxAddonTests(unittest.TestCase):
    def test_features_match_packages_and_docs(self):
        names = _features_tuple()
        self.assertEqual(names, EXPECTED_FEATURES)
        for name in names:
            self.assertTrue((ADDON / "features" / name / "__init__.py").is_file(), name)
            self.assertTrue((DOCS / "功能" / "{0}.md".format(name)).is_file(), name)

    def test_feature_docs_exist_only_for_listed(self):
        listed = set(_features_tuple())
        on_disk = {p.stem for p in (DOCS / "功能").glob("*.md")}
        self.assertEqual(on_disk, listed)

    def test_bl_info_without_importing_bpy(self):
        tree = ast.parse((ADDON / "__init__.py").read_text(encoding="utf-8"))
        bl_info = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "bl_info":
                        bl_info = ast.literal_eval(node.value)
        self.assertIsNotNone(bl_info)
        self.assertEqual(bl_info["name"], "LoopFlow ToolBox")
        self.assertEqual(bl_info["author"], "Chihyu Tsai")
        self.assertEqual(bl_info["blender"], (5, 2, 1))
        self.assertEqual(bl_info["version"], (1, 0, 0))
        self.assertIn("ToolBox", bl_info["location"])

    def test_parent_panel_and_operator_prefix(self):
        root = (ADDON / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('bl_label = "ToolBox"', root)
        self.assertIn('bl_category = "LoopFlow"', root)
        constants = (ADDON / "constants.py").read_text(encoding="utf-8")
        self.assertIn('PARENT_PANEL_ID = "LOOPFLOW_TOOLBOX_PT_root"', constants)
        blob = "\n".join(
            p.read_text(encoding="utf-8") for p in ADDON.rglob("*.py")
        )
        self.assertNotIn("exporttools.", blob)
        self.assertNotIn("lighthouse.", blob)
        self.assertNotIn("r2b_export_selected", blob)
        self.assertIn("loopflow_toolbox_export_selected", blob)
        for op in EXPECTED_OPS:
            self.assertIn('bl_idname = "{0}"'.format(op), blob)
        self.assertNotIn("loopflow_r2b_sync_dev", blob)
        self.assertNotIn("from foundation", blob)
        self.assertNotIn("import_3dm", blob)
        self.assertFalse((ADDON / "blender_manifest.toml").is_file())

    def test_addon_compiles(self):
        self.assertTrue(compileall.compile_dir(str(ADDON), quiet=1))

    def test_not_in_yak_build(self):
        text = YAK_BUILD.read_text(encoding="utf-8")
        self.assertNotIn("loopflow_toolbox", text)
        self.assertNotIn("ToolBox", text)
        self.assertIn("loopflow_r2b_sync.zip", text)

    def test_pack_and_link_scripts(self):
        pack = (WIP / "tools" / "pack_toolbox.ps1").read_text(encoding="utf-8")
        self.assertIn("loopflow_toolbox-1.0.0.zip", pack)
        self.assertIn("Install from Disk", pack)
        self.assertNotIn("yak.exe", pack)
        self.assertNotIn("templates", pack)
        link = (WIP / "tools" / "link_dev_toolbox.ps1").read_text(encoding="utf-8")
        self.assertIn("loopflow_toolbox", link)
        self.assertIn("LoopFlow ToolBox", link)


if __name__ == "__main__":
    unittest.main()
