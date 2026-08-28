# -*- coding: utf-8 -*-
"""相機自動同步閘與姿態略過。"""
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
from foundation.camera_hotpath import CameraAutoPublishGate
from foundation.camera_payload import (
    build_camera_payload,
    payload_pose,
    poses_equivalent,
    validate_camera_payload,
)


def _pose_at(z: float):
    payload = build_camera_payload(
        location=(0, 0, z),
        direction=(0, 1, 0),
        up=(0, 0, 1),
        lens=50.0,
    )
    return payload, payload_pose(payload)


class CameraPoseTests(unittest.TestCase):
    def test_equivalent_within_eps(self):
        a = payload_pose(
            build_camera_payload(
                location=(1, 2, 3), direction=(0, 1, 0), up=(0, 0, 1), lens=35
            )
        )
        b = payload_pose(
            build_camera_payload(
                location=(1 + 1e-9, 2, 3),
                direction=(0, 1, 0),
                up=(0, 0, 1),
                lens=35 + 1e-6,
            )
        )
        self.assertTrue(poses_equivalent(a, b))

    def test_different_location_not_equivalent(self):
        a = payload_pose(
            build_camera_payload(
                location=(0, 0, 0), direction=(0, 1, 0), up=(0, 0, 1), lens=50
            )
        )
        b = payload_pose(
            build_camera_payload(
                location=(1, 0, 0), direction=(0, 1, 0), up=(0, 0, 1), lens=50
            )
        )
        self.assertFalse(poses_equivalent(a, b))


class CameraAutoPublishGateTests(unittest.TestCase):
    def test_debounce_then_idle_flush(self):
        gate = CameraAutoPublishGate(interval_sec=0.08)
        _payload, pose = _pose_at(1.0)
        gate.note_view_modified()
        self.assertEqual(gate.decide(0.01, pose), "publish")
        gate.mark_published(0.01, pose)

        _payload2, pose2 = _pose_at(2.0)
        gate.note_view_modified()
        self.assertEqual(gate.decide(0.02, pose2), "wait")
        self.assertEqual(gate.decide(0.10, pose2), "publish")

    def test_skip_unchanged_pose(self):
        gate = CameraAutoPublishGate(interval_sec=0.08)
        _payload, pose = _pose_at(1.0)
        gate.note_view_modified()
        self.assertEqual(gate.decide(1.0, pose), "publish")
        gate.mark_published(1.0, pose)
        gate.note_view_modified()
        self.assertEqual(gate.decide(2.0, pose), "skip")
        self.assertFalse(gate.dirty)


class CameraHotpathPublishTests(unittest.TestCase):
    def test_compact_json_without_fsync(self):
        payload = build_camera_payload(
            location=(1, 2, 3), direction=(0, 1, 0), up=(0, 0, 1), lens=50
        )
        self.assertIsNone(validate_camera_payload(payload))
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "camera.json"
            r = atomic_publish_json(
                final,
                payload,
                indent=None,
                validate=None,
                fsync=False,
                retries=2,
                delay_sec=0.01,
            )
            self.assertTrue(r.ok, r.message)
            text = final.read_text(encoding="utf-8")
            self.assertNotIn("\n  ", text)
            loaded = json.loads(text)
            self.assertEqual(loaded["lens"], 50)


if __name__ == "__main__":
    unittest.main()
