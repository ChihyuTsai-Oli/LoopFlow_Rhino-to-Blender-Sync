# -*- coding: utf-8 -*-
"""內嵌 import_3dm／rhino3dm bootstrap 測試。"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

IMPORT_3DM = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "blender"
    / "loopflow_r2b_sync_dev"
    / "import_3dm"
)


class EmbeddedImport3dmTests(unittest.TestCase):
    def test_wheels_present_for_win(self):
        wheels = IMPORT_3DM / "wheels"
        self.assertTrue(wheels.is_dir())
        names = {p.name for p in wheels.glob("rhino3dm-*.whl")}
        self.assertTrue(any("cp313" in n and "win_amd64" in n for n in names))
        self.assertTrue(any("cp311" in n and "win_amd64" in n for n in names))

    def test_bootstrap_loads_rhino3dm(self):
        tag = "cp{}{}".format(sys.version_info.major, sys.version_info.minor)
        whls = list((IMPORT_3DM / "wheels").glob("rhino3dm-*-{}-*.whl".format(tag)))
        if not whls:
            self.skipTest(
                "無對應 {} 的 rhino3dm wheel（請用 Blender 5.2 內建 Python 驗）".format(tag)
            )
        bootstrap = IMPORT_3DM / "_bootstrap_rhino3dm.py"
        spec = importlib.util.spec_from_file_location(
            "r2b_bootstrap_rhino3dm", bootstrap
        )
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        mod.ensure_rhino3dm()
        import rhino3dm  # noqa: F401

        self.assertTrue(hasattr(rhino3dm, "File3dm"))


if __name__ == "__main__":
    unittest.main()
