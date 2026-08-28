# -*- coding: utf-8 -*-
"""Light payload／路徑契約單元測試。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
sys.path.insert(0, str(SRC))

from foundation.atomic import atomic_publish_json
from foundation.light_payload import (
    build_light_payload,
    layer_matches_prefix,
    parse_light_payload,
    validate_light_file,
    validate_light_payload,
)
from foundation.paths import ensure_config_layout, light_path, resolve_light_json_from_work_folder


class LightPayloadTests(unittest.TestCase):
    def test_layer_prefix_requires_sublayer(self):
        self.assertFalse(layer_matches_prefix("R2B_LT_Points", "R2B_LT_Points"))
        self.assertTrue(layer_matches_prefix("R2B_LT_Points::Downlight", "R2B_LT_Points"))
        self.assertFalse(layer_matches_prefix("R2B_LT_Points_舊", "R2B_LT_Points"))
        self.assertFalse(layer_matches_prefix("Other", "R2B_LT_Points"))

    def test_build_and_parse_roundtrip(self):
        payload = build_light_payload(
            [{"guid": "abc", "type": "Downlight", "loc": (1.0, 2.0, 3.0)}],
            document_name="demo.3dm",
        )
        self.assertEqual(payload["schema_version"], 1)
        parsed = parse_light_payload(payload)
        self.assertTrue(parsed.ok)
        self.assertEqual(parsed.data["points"][0]["guid"], "abc")
        self.assertEqual(parsed.data["points"][0]["loc"], (1.0, 2.0, 3.0))
        self.assertFalse(parsed.data["clear"])

    def test_reject_empty_points_without_clear(self):
        err = validate_light_payload({"schema_version": 1, "points": []})
        self.assertIsNotNone(err)
        self.assertIn("ED-07", err)

    def test_allow_empty_with_clear(self):
        payload = build_light_payload([], clear=True)
        self.assertTrue(payload.get("clear"))
        self.assertIsNone(validate_light_payload(payload))
        parsed = parse_light_payload(payload)
        self.assertTrue(parsed.ok)
        self.assertTrue(parsed.data["clear"])
        self.assertEqual(parsed.data["points"], [])

    def test_reject_legacy_without_schema(self):
        err = validate_light_payload(
            {"points": [{"guid": "a", "type": "T", "loc": [0, 0, 0]}]}
        )
        self.assertIsNotNone(err)

    def test_atomic_publish_light(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "_LoopFlow_Config" / "loopflow_R2B")
            final = light_path(root)
            payload = build_light_payload(
                [{"guid": "g1", "type": "Spot", "loc": [10, 20, 30]}]
            )
            result = atomic_publish_json(final, payload, validate=validate_light_file)
            self.assertTrue(result.ok)
            loaded = json.loads(final.read_text(encoding="utf-8"))
            self.assertTrue(parse_light_payload(loaded).ok)

    def test_atomic_rejects_empty_keeps_last_good(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "_LoopFlow_Config" / "loopflow_R2B")
            final = light_path(root)
            good = build_light_payload(
                [{"guid": "keep", "type": "A", "loc": [1, 1, 1]}]
            )
            self.assertTrue(
                atomic_publish_json(final, good, validate=validate_light_file).ok
            )
            empty = {"schema_version": 1, "points": []}
            bad = atomic_publish_json(final, empty, validate=validate_light_file)
            self.assertFalse(bad.ok)
            loaded = json.loads(final.read_text(encoding="utf-8"))
            self.assertEqual(loaded["points"][0]["guid"], "keep")

    def test_atomic_clear_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "_LoopFlow_Config" / "loopflow_R2B")
            final = light_path(root)
            good = build_light_payload(
                [{"guid": "keep", "type": "A", "loc": [1, 1, 1]}]
            )
            self.assertTrue(
                atomic_publish_json(final, good, validate=validate_light_file).ok
            )
            clear = build_light_payload([], clear=True)
            ok = atomic_publish_json(final, clear, validate=validate_light_file)
            self.assertTrue(ok.ok)
            loaded = json.loads(final.read_text(encoding="utf-8"))
            self.assertEqual(loaded["points"], [])
            self.assertTrue(loaded["clear"])

    def test_resolve_from_work_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            target = (
                work
                / "_LoopFlow_Config"
                / "loopflow_R2B"
                / "live"
                / "light.json"
            )
            target.parent.mkdir(parents=True)
            target.write_text('{"schema_version":1,"points":[]}\n', encoding="utf-8")
            resolved = resolve_light_json_from_work_folder(work)
            self.assertEqual(resolved, target.resolve())


if __name__ == "__main__":
    unittest.main()
