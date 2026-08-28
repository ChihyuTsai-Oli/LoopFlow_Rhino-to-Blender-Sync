# -*- coding: utf-8 -*-
"""Camera payload／atomic 純 Python 測試。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.atomic import atomic_publish_json
from foundation.camera_payload import (
    SCHEMA_VERSION,
    build_camera_payload,
    parse_camera_payload,
    validate_camera_file,
    validate_camera_payload,
)
from foundation.paths import camera_path, ensure_config_layout


class CameraPayloadTests(unittest.TestCase):
    def test_build_and_parse_roundtrip(self):
        payload = build_camera_payload(
            location=(1, 2, 3),
            direction=(0, 1, 0),
            up=(0, 0, 1),
            lens=35.0,
            document_name="demo.3dm",
        )
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertIsNone(validate_camera_payload(payload))
        parsed = parse_camera_payload(payload)
        self.assertTrue(parsed.ok)
        self.assertEqual(parsed.data["location"], (1.0, 2.0, 3.0))
        self.assertEqual(parsed.data["lens"], 35.0)

    def test_reject_unknown_schema(self):
        payload = build_camera_payload(
            location=(0, 0, 0), direction=(0, 0, 1), up=(0, 1, 0), lens=50
        )
        payload["schema_version"] = 99
        r = parse_camera_payload(payload)
        self.assertFalse(r.ok)
        self.assertIn("schema_version", r.message)

    def test_reject_legacy_without_schema(self):
        legacy = {
            "location": {"x": 0, "y": 0, "z": 0},
            "direction": {"x": 0, "y": 0, "z": 1},
            "up": {"x": 0, "y": 1, "z": 0},
            "lens": 50,
        }
        self.assertIsNotNone(validate_camera_payload(legacy))

    def test_atomic_publish_camera(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "loopflow_R2B")
            final = camera_path(root)
            payload = build_camera_payload(
                location=(10, 20, 30),
                direction=(1, 0, 0),
                up=(0, 0, 1),
                lens=50,
            )
            r = atomic_publish_json(final, payload, validate=validate_camera_file)
            self.assertTrue(r.ok, r.message)
            loaded = json.loads(final.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema_version"], SCHEMA_VERSION)
            self.assertTrue(parse_camera_payload(loaded).ok)


if __name__ == "__main__":
    unittest.main()
