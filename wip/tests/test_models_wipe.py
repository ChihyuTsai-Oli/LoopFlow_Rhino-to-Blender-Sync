# -*- coding: utf-8 -*-
"""Models wipe 規則（不啟動 Blender）。"""
from __future__ import annotations

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
if str(IMPORT_3DM) not in sys.path:
    sys.path.insert(0, str(IMPORT_3DM))

from r2b_wipe import should_preserve_collection


class WipeRuleTests(unittest.TestCase):
    def test_keep_root(self):
        self.assertTrue(should_preserve_collection("R2B", "R2B"))

    def test_wipe_layer_child(self):
        self.assertFalse(should_preserve_collection("M3D", "R2B"))
        self.assertFalse(should_preserve_collection("Layers", "R2B"))

    def test_keep_lighting(self):
        self.assertTrue(should_preserve_collection("Lighting", "R2B"))
        self.assertTrue(should_preserve_collection("Lighting Fixtures", "R2B"))


if __name__ == "__main__":
    unittest.main()
