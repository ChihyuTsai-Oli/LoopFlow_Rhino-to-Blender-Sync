# -*- coding: utf-8 -*-
"""G02 yak spike：manifest、指令檔、不得包進 Blender（不依賴 Rhino GUI）。"""
from __future__ import annotations

import py_compile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SPIKE = WIP / "packaging" / "g02-spike"
COMMANDS = SPIKE / "commands"
NAMES = SPIKE / "指令名稱.txt"
MANIFEST = SPIKE / "manifest.yml"
ENTRYPOINTS = WIP / "src" / "rhino" / "entrypoints"

EXPECTED = (
    "RBModels",
    "RBObjects",
    "RBCamera",
    "RBCameraPush",
    "RBLight",
    "RBLightPush",
    "RBOpen",
)


class G02SpikeTests(unittest.TestCase):
    def test_command_name_list(self):
        names = [
            line.strip()
            for line in NAMES.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(tuple(names), EXPECTED)

    def test_yak_command_files(self):
        for name in EXPECTED:
            path = COMMANDS / "{}.py".format(name)
            self.assertTrue(path.is_file(), path)
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("#! python 3"), name)
            self.assertIn("def RunCommand(", text)
            self.assertIn("_isolate.py", text)
            self.assertNotIn("blender", text.lower())
            self.assertNotIn("import_3dm", text)
            py_compile.compile(str(path), doraise=True)
        extras = {p.stem for p in COMMANDS.glob("*.py")} - set(EXPECTED)
        self.assertEqual(extras, set())

    def test_dev_entrypoints_unchanged_names(self):
        for name in EXPECTED:
            self.assertTrue((ENTRYPOINTS / "{}.py".format(name)).is_file(), name)

    def test_manifest_spike_identity(self):
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertIn("name: loopflow-rhino-to-blender-sync", text)
        self.assertIn("version: 0.1.0", text)
        self.assertIn("Chihyu Tsai", text)
        self.assertIn("github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync", text)
        self.assertNotIn("3.0.0", text)
        self.assertNotIn("import_3dm", text)

    def test_build_script_drops_auto_rui(self):
        build = (SPIKE / "build.ps1").read_text(encoding="utf-8")
        self.assertIn("Remove-Item", build)
        self.assertIn(".rui", build)
        self.assertIn("yak", build.lower())
        self.assertIn("docs\\toolbar", build)
        self.assertIn("build\\rh8", build)
        self.assertIn("yak-stage", build)

    def test_isolate_module_compiles(self):
        py_compile.compile(str(SPIKE / "_isolate.py"), doraise=True)

    def test_product_rui_and_icon(self):
        rui = WIP / "docs" / "toolbar" / "LoopFlow_R2B.rui"
        text = rui.read_text(encoding="utf-8")
        self.assertIn("<tool_bar_group ", text)
        self.assertIn("Rhino to Blender Sync", text)
        self.assertNotIn("SelectedToolbarSet", text)
        for cmd in EXPECTED:
            self.assertIn("! _{}".format(cmd), text)
        self.assertTrue((WIP / "docs" / "toolbar" / "icon.png").is_file())
        self.assertTrue((SPIKE / "loopflow-rhino-to-blender-sync.rhproj").is_file())


if __name__ == "__main__":
    unittest.main()
