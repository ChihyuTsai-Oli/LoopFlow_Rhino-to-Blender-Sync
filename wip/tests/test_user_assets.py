# -*- coding: utf-8 -*-
"""拷 yak templates 到「文件\\LoopFlow」。"""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
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

    def test_sync_copies_zip_and_skips_same_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            src_root = Path(tmp) / "pkg" / "libs" / "x" / "src"
            src_root.mkdir(parents=True)
            templates = Path(tmp) / "pkg" / "templates"
            templates.mkdir(parents=True)
            zip_path = templates / "loopflow_r2b_sync.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("loopflow_r2b_sync/__init__.py", "1")
            (templates / STAMP_NAME).write_text("0.1.4\n", encoding="utf-8")
            dest = Path(tmp) / "out"
            first = sync_user_assets(src_root=src_root, dest=dest, open_folder=False)
            self.assertTrue(first)
            self.assertTrue((dest / "loopflow_r2b_sync.zip").is_file())
            self.assertFalse((dest / "loopflow_r2b_sync_dev").exists())
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("loopflow_r2b_sync/__init__.py", "2")
            second = sync_user_assets(src_root=src_root, dest=dest, open_folder=False)
            self.assertFalse(second)
            with zipfile.ZipFile(dest / "loopflow_r2b_sync.zip") as zf:
                self.assertEqual(zf.read("loopflow_r2b_sync/__init__.py"), b"1")

    def test_sync_noop_without_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            src_root = Path(tmp) / "src"
            src_root.mkdir()
            dest = Path(tmp) / "out"
            self.assertFalse(sync_user_assets(src_root=src_root, dest=dest, open_folder=False))


if __name__ == "__main__":
    unittest.main()
