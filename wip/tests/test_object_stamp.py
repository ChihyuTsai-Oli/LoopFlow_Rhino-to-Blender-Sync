# -*- coding: utf-8 -*-
"""Objects 時戳檔名：不覆蓋、同秒加一秒。"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.object_stamp import (
    latest_stamped_path,
    stamped_objects_name,
    unique_stamped_path,
)


class ObjectStampTests(unittest.TestCase):
    def test_name_format(self):
        when = datetime(2026, 8, 29, 20, 5, 9)
        self.assertEqual(
            stamped_objects_name("R2B_Objects", ".3dm", when),
            "R2B_Objects_260829_200509.3dm",
        )

    def test_unique_skips_existing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            when = datetime(2026, 8, 29, 20, 0, 0)
            first = folder / "R2B_Objects_260829_200000.3dm"
            first.write_bytes(b"x")
            taken = {first}

            def exists(path: Path) -> bool:
                return Path(path) in taken or Path(path).exists()

            nxt = unique_stamped_path(
                folder,
                "R2B_Objects",
                ".3dm",
                now_fn=lambda: when,
                exists_fn=exists,
            )
            self.assertEqual(nxt.name, "R2B_Objects_260829_200001.3dm")

    def test_latest_falls_back_to_legacy(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            legacy = folder / "R2B_Objects.3dm"
            legacy.write_bytes(b"old")
            self.assertEqual(
                latest_stamped_path(folder, "R2B_Objects", ".3dm"),
                legacy,
            )


if __name__ == "__main__":
    unittest.main()
