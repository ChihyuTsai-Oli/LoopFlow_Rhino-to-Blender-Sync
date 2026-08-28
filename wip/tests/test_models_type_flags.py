# -*- coding: utf-8 -*-
"""Models 幾何類別 CheckListBox 預設勾選。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rhino.commands.models import checklist_defaults


class ModelTypeChecklistTests(unittest.TestCase):
    def test_builtin_defaults_skip_point_curve(self):
        rows = dict(checklist_defaults())
        self.assertFalse(rows["Point"])
        self.assertFalse(rows["Curve"])
        self.assertTrue(rows["Mesh"])
        self.assertTrue(rows["Block / Instance"])

    def test_last_labels_override(self):
        rows = dict(checklist_defaults(["Point", "Mesh"]))
        self.assertTrue(rows["Point"])
        self.assertFalse(rows["Curve"])
        self.assertTrue(rows["Mesh"])
        self.assertFalse(rows["Block / Instance"])


if __name__ == "__main__":
    unittest.main()
