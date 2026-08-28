# -*- coding: utf-8 -*-
"""R2B 經典材質顏色轉換。"""
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

from r2b_materials import classic_diffuse_linear_rgb


class ClassicDiffuseTests(unittest.TestCase):
    def test_red_255(self):
        r, g, b = classic_diffuse_linear_rgb((255, 0, 0))
        self.assertAlmostEqual(r, 1.0, places=5)
        self.assertAlmostEqual(g, 0.0, places=5)
        self.assertAlmostEqual(b, 0.0, places=5)

    def test_object_channels(self):
        class _C:
            R = 0
            G = 0
            B = 0

        r, g, b = classic_diffuse_linear_rgb(_C())
        self.assertEqual((r, g, b), (0.0, 0.0, 0.0))

    def test_none_is_gray(self):
        r, g, b = classic_diffuse_linear_rgb(None)
        self.assertAlmostEqual(r, g)
        self.assertAlmostEqual(g, b)
        self.assertGreater(r, 0.5)
        self.assertLess(r, 0.7)


if __name__ == "__main__":
    unittest.main()
