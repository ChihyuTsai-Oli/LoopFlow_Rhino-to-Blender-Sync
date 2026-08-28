# -*- coding: utf-8 -*-
"""Open／Health 摘要純 Python 測試。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.health import build_health_report, file_stamp
from foundation.paths import camera_path, ensure_config_layout, model_path


class HealthReportTests(unittest.TestCase):
    def test_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "loopflow_R2B")
            text = build_health_report(
                document=r"C:\proj\demo.3dm",
                config_root=root,
                work_folder=Path(tmp),
            )
            self.assertIn("R2B Health", text)
            self.assertIn("demo.3dm", text)
            self.assertIn("missing", text)
            self.assertIn("models/R2B.3dm", text)
            self.assertIn("models/R2B_Objects.3dm", text)
            self.assertIn("live/camera.json", text)
            self.assertIn("r2b.log", text)
            self.assertEqual(file_stamp(camera_path(root)), "missing")

    def test_existing_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "loopflow_R2B")
            target = model_path(root)
            target.write_bytes(b"x")
            stamp = file_stamp(target)
            self.assertNotEqual(stamp, "missing")
            text = build_health_report(
                document="demo.3dm",
                config_root=root,
                work_folder=Path(tmp),
            )
            self.assertIn("models/R2B.3dm", text)
            self.assertIn(stamp, text)


if __name__ == "__main__":
    unittest.main()
