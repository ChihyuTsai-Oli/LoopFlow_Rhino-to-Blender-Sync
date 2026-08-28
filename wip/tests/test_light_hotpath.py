# -*- coding: utf-8 -*-
"""燈光自動同步：事件過濾與指紋。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.light_hotpath import (
    light_payload_fingerprint,
    object_is_light_point,
)


class LightEventFilterTests(unittest.TestCase):
    def test_only_point_on_light_sublayer(self):
        self.assertTrue(
            object_is_light_point("point", "R2B_LT_Points::Downlight", "R2B_LT_Points")
        )
        self.assertFalse(
            object_is_light_point("brep", "R2B_LT_Points::Downlight", "R2B_LT_Points")
        )
        self.assertFalse(
            object_is_light_point("point", "Model::Wall", "R2B_LT_Points")
        )
        self.assertFalse(
            object_is_light_point("point", "R2B_LT_Points", "R2B_LT_Points")
        )


class LightFingerprintTests(unittest.TestCase):
    def test_order_independent(self):
        a = light_payload_fingerprint(
            [
                {"guid": "b", "type": "Spot", "loc": (1, 2, 3)},
                {"guid": "a", "type": "Down", "loc": (0, 0, 0)},
            ]
        )
        b = light_payload_fingerprint(
            [
                {"guid": "a", "type": "Down", "loc": (0, 0, 0)},
                {"guid": "b", "type": "Spot", "loc": (1, 2, 3)},
            ]
        )
        self.assertEqual(a, b)

    def test_location_change_differs(self):
        a = light_payload_fingerprint(
            [{"guid": "a", "type": "Down", "loc": (0, 0, 0)}]
        )
        b = light_payload_fingerprint(
            [{"guid": "a", "type": "Down", "loc": (1, 0, 0)}]
        )
        self.assertNotEqual(a, b)

    def test_clear_distinct_from_empty(self):
        self.assertEqual(light_payload_fingerprint([], clear=True), ("clear",))
        self.assertNotEqual(
            light_payload_fingerprint([], clear=True),
            light_payload_fingerprint([]),
        )


if __name__ == "__main__":
    unittest.main()
