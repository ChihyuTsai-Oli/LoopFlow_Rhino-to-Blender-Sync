# -*- coding: utf-8 -*-
"""foundation 純 Python 測試（B02）。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.atomic import atomic_publish_json, atomic_publish_text
from foundation.log import append_log
from foundation.paths import (
    CAMERA_FILE_NAME,
    PRODUCT_DIR_NAME,
    camera_path,
    config_root_for_document,
    ensure_config_layout,
    pending_path_for,
    require_saved_document_path,
    resolve_models_dir_from_work_folder,
)
from foundation.result import Result


class FoundationResultTests(unittest.TestCase):
    def test_success_fail_blocked(self):
        self.assertTrue(Result.success("ok").ok)
        self.assertEqual(Result.fail("x", stage="s").status, "fail")
        self.assertEqual(Result.blocked("未存檔").status, "blocked")
        self.assertFalse(Result.cancel().ok)


class FoundationPathTests(unittest.TestCase):
    def test_require_saved(self):
        self.assertEqual(require_saved_document_path(None).status, "blocked")
        self.assertEqual(require_saved_document_path("").status, "blocked")
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "demo.3dm"
            doc.write_bytes(b"x")
            r = require_saved_document_path(str(doc))
            self.assertTrue(r.ok)
            root = config_root_for_document(doc)
            self.assertEqual(root.name, PRODUCT_DIR_NAME)
            self.assertEqual(root.parent.name, "_LoopFlow_Config")
            self.assertEqual(camera_path(root).name, CAMERA_FILE_NAME)

    def test_pending_name(self):
        p = Path(r"C:\proj\_LoopFlow_Config\loopflow_R2B\live\camera.json")
        self.assertEqual(pending_path_for(p).name, "camera_pending.json")

    def test_ensure_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "cfg")
            self.assertTrue((root / "live").is_dir())
            self.assertTrue((root / "models").is_dir())

    def test_models_dir_from_work_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "job"
            work.mkdir()
            (work / "models").mkdir()
            nested = work / "_LoopFlow_Config" / "loopflow_R2B" / "models"
            nested.mkdir(parents=True)
            resolved = resolve_models_dir_from_work_folder(work)
            self.assertEqual(resolved, nested.resolve())


class FoundationAtomicTests(unittest.TestCase):
    def test_publish_leaves_last_good_on_validate_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "camera.json"
            final.write_text('{"keep": true}\n', encoding="utf-8")

            def bad_validate(_path: Path):
                return "假驗證失敗"

            r = atomic_publish_text(final, '{"new": true}\n', validate=bad_validate)
            self.assertFalse(r.ok)
            self.assertEqual(r.stage, "validate")
            self.assertEqual(json.loads(final.read_text(encoding="utf-8"))["keep"], True)
            self.assertFalse(pending_path_for(final).exists())

    def test_publish_replaces_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "light.json"
            final.write_text('{"points": []}\n', encoding="utf-8")
            payload = {"points": [{"guid": "a", "type": "Down", "loc": [1, 2, 3]}]}
            r = atomic_publish_json(final, payload)
            self.assertTrue(r.ok, r.message)
            loaded = json.loads(final.read_text(encoding="utf-8"))
            self.assertEqual(len(loaded["points"]), 1)
            self.assertFalse(pending_path_for(final).exists())

    def test_first_publish_without_prior_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "live" / "camera.json"
            r = atomic_publish_json(final, {"lens": 50})
            self.assertTrue(r.ok, r.message)
            self.assertTrue(final.is_file())


class FoundationLogTests(unittest.TestCase):
    def test_append_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "loopflow_R2B"
            r = append_log(root, "hello foundation")
            self.assertTrue(r.ok, r.message)
            text = Path(r.data).read_text(encoding="utf-8")
            self.assertIn("hello foundation", text)
            self.assertIn("[INFO]", text)


if __name__ == "__main__":
    unittest.main()
