# -*- coding: utf-8 -*-
"""G02 yak spike：manifest、指令檔、含 Blender add-on templates（不依賴 Rhino GUI）。"""
from __future__ import annotations

import py_compile
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SPIKE = WIP / "packaging" / "g02-spike"
COMMANDS = SPIKE / "commands"
NAMES = SPIKE / "指令名稱.txt"
MANIFEST = SPIKE / "manifest.yml"
ENTRYPOINTS = WIP / "src" / "rhino" / "entrypoints"
if str(SPIKE) not in sys.path:
    sys.path.insert(0, str(SPIKE))

import command_locate  # noqa: E402

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
            self.assertIn("_run()", text)
            self.assertIn("PLUGIN_ID = \"{}\"".format(command_locate.PLUGIN_ID), text)
            self.assertIn("_from_yak_install", text)
            self.assertIn("sync_user_assets", text)
            self.assertNotIn("_isolate.py", text)
            self.assertNotIn("import_3dm", text)
            self.assertNotIn("loopflow_r2b_sync_dev", text)
            py_compile.compile(str(path), doraise=True)
        extras = {p.stem for p in COMMANDS.glob("*.py")} - set(EXPECTED)
        self.assertEqual(extras, set())

    def test_dev_entrypoints_unchanged_names(self):
        for name in EXPECTED:
            self.assertTrue((ENTRYPOINTS / "{}.py".format(name)).is_file(), name)

    def test_manifest_spike_identity(self):
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertIn("name: loopflow-rhino-to-blender-sync", text)
        self.assertIn("version: 0.1.4", text)
        self.assertIn("Chihyu Tsai", text)
        self.assertIn("github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync", text)
        self.assertIn("guid:860a0589-cda5-46a6-97ef-d538db8e0db3", text)
        self.assertIn("platform: win", text)
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
        self.assertIn("templates", build)
        self.assertIn("loopflow_r2b_sync_dev", build)
        self.assertIn("loopflow_r2b_sync.zip", build)
        self.assertIn("_vendor", build)
        self.assertIn("matches rhp", build)

    def test_command_locate_compiles(self):
        py_compile.compile(str(SPIKE / "command_locate.py"), doraise=True)

    def test_command_locate_finds_libs_src(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"APPDATA": tmp, "LOCALAPPDATA": tmp}
            src = (
                Path(tmp)
                / "McNeel"
                / "Rhinoceros"
                / "packages"
                / "8.0"
                / command_locate.YAK_NAME
                / "0.1.0"
                / "libs"
                / "Abcd"
                / "src"
            )
            (src / "foundation").mkdir(parents=True)
            marker = src.joinpath(*command_locate.MARKER)
            marker.parent.mkdir(parents=True)
            marker.write_text("#", encoding="utf-8")
            hit = command_locate.from_yak_install(env)
            self.assertEqual(hit.resolve(), src.resolve())

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

    def test_blender_addon_is_sync_not_nested_import_3dm(self):
        addon = WIP / "src" / "blender" / "loopflow_r2b_sync_dev"
        nested = addon / "import_3dm" / "blender_manifest.toml"
        self.assertFalse(nested.is_file(), nested)
        manifest = (addon / "blender_manifest.toml").read_text(encoding="utf-8")
        self.assertIn('id = "loopflow_r2b_sync"', manifest)
        self.assertIn('name = "LoopFlow Rhino to Blender Sync"', manifest)
        self.assertNotIn('id = "import_3dm"', manifest)
        init = (addon / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('"name": "LoopFlow Rhino to Blender Sync"', init)
        self.assertIn("def register(", init)
        self.assertNotIn("Dev Stub", init)


if __name__ == "__main__":
    unittest.main()
