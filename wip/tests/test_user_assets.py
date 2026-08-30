# -*- coding: utf-8 -*-
"""拷 yak templates 到「文件\\LoopFlow」。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.user_assets import STAMP_NAME, copy_tree, sync_user_assets


class UserAssetsTests(unittest.TestCase):
    def test_copy_tree_skips_existing_keep_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            (src / "a.txt").write_text("new", encoding="utf-8")
            (src / "keep.txt").write_text("official", encoding="utf-8")
            dest.mkdir()
            (dest / "keep.txt").write_text("user", encoding="utf-8")
            (dest / "extra.txt").write_text("mine", encoding="utf-8")
            copied = copy_tree(src, dest, frozenset({"keep.txt"}))
            self.assertTrue(copied)
            self.assertEqual((dest / "a.txt").read_text(encoding="utf-8"), "new")
            self.assertEqual((dest / "keep.txt").read_text(encoding="utf-8"), "user")
            self.assertEqual((dest / "extra.txt").read_text(encoding="utf-8"), "mine")

    def test_sync_skips_same_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            src_root = Path(tmp) / "pkg" / "libs" / "x" / "src"
            templates = Path(tmp) / "pkg" / "templates"
            payload = templates / "blender" / "addon"
            payload.mkdir(parents=True)
            (payload / "file.py").write_text("1", encoding="utf-8")
            (templates / STAMP_NAME).write_text("0.1.1\n", encoding="utf-8")
            dest = Path(tmp) / "out"
            first = sync_user_assets(src_root=src_root, dest=dest, open_folder=False)
            self.assertTrue(first)
            self.assertTrue((dest / "addon" / "file.py").is_file())
            (payload / "file.py").write_text("2", encoding="utf-8")
            second = sync_user_assets(src_root=src_root, dest=dest, open_folder=False)
            self.assertFalse(second)
            self.assertEqual((dest / "addon" / "file.py").read_text(encoding="utf-8"), "1")

    def test_sync_noop_without_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            src_root = Path(tmp) / "src"
            src_root.mkdir()
            dest = Path(tmp) / "out"
            self.assertFalse(sync_user_assets(src_root=src_root, dest=dest, open_folder=False))


if __name__ == "__main__":
    unittest.main()
