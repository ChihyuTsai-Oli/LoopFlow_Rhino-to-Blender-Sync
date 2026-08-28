# -*- coding: utf-8 -*-
"""Models 路徑／atomic／驗證單元測試。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
sys.path.insert(0, str(SRC))

from foundation.atomic import atomic_publish_from_pending
from foundation.model_payload import validate_model_3dm
from foundation.paths import (
    ensure_config_layout,
    model_path,
    objects_path,
    pending_path_for,
    resolve_model_3dm_from_work_folder,
    resolve_objects_3dm_from_work_folder,
)
from rhino.commands.model_export import mapped_piece_layer, material_name_from_full_path


class ModelPublishTests(unittest.TestCase):
    def test_validate_rejects_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "R2B.3dm"
            p.write_bytes(b"")
            self.assertIsNotNone(validate_model_3dm(p))

    def test_validate_accepts_nonempty(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "R2B.3dm"
            p.write_bytes(b"3D Geometry File Format dummy")
            self.assertIsNone(validate_model_3dm(p))

    def test_atomic_from_pending_keeps_last_good_on_bad_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "_LoopFlow_Config" / "loopflow_R2B")
            final = model_path(root)
            pending = pending_path_for(final)
            final.write_bytes(b"LASTGOOD-CONTENT-XXXX")
            pending.write_bytes(b"")  # invalid
            bad = atomic_publish_from_pending(final, validate=validate_model_3dm)
            self.assertFalse(bad.ok)
            self.assertEqual(final.read_bytes(), b"LASTGOOD-CONTENT-XXXX")
            self.assertFalse(pending.exists())

    def test_atomic_from_pending_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = ensure_config_layout(Path(tmp) / "_LoopFlow_Config" / "loopflow_R2B")
            final = model_path(root)
            pending = pending_path_for(final)
            final.write_bytes(b"OLD")
            pending.write_bytes(b"NEW-3DM-PAYLOAD-BYTES")
            ok = atomic_publish_from_pending(final, validate=validate_model_3dm)
            self.assertTrue(ok.ok)
            self.assertEqual(final.read_bytes(), b"NEW-3DM-PAYLOAD-BYTES")
            self.assertFalse(pending.exists())

    def test_resolve_from_work_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            target = (
                work
                / "_LoopFlow_Config"
                / "loopflow_R2B"
                / "models"
                / "R2B.3dm"
            )
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            self.assertEqual(resolve_model_3dm_from_work_folder(work), target.resolve())

    def test_resolve_falls_back_to_legacy_model_3dm(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            legacy = (
                work
                / "_LoopFlow_Config"
                / "loopflow_R2B"
                / "models"
                / "model.3dm"
            )
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b"legacy")
            self.assertEqual(resolve_model_3dm_from_work_folder(work), legacy.resolve())

    def test_resolve_objects_3dm(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            target = (
                work
                / "_LoopFlow_Config"
                / "loopflow_R2B"
                / "models"
                / "R2B_Objects.3dm"
            )
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            self.assertEqual(resolve_objects_3dm_from_work_folder(work), target.resolve())
            root = ensure_config_layout(
                work / "_LoopFlow_Config" / "loopflow_R2B"
            )
            self.assertEqual(objects_path(root).name, "R2B_Objects.3dm")

    def test_mapped_piece_layer_prefers_definition(self):
        old_to_new = {10: 0, 20: 1, 30: 2}
        self.assertEqual(mapped_piece_layer(20, old_to_new, 10), 1)
        self.assertEqual(mapped_piece_layer(99, old_to_new, 10), 0)
        self.assertIsNone(mapped_piece_layer(99, old_to_new, 50))

    def test_material_name_parent_and_leaf(self):
        self.assertEqual(material_name_from_full_path("A::B::C"), "B::C")
        self.assertEqual(material_name_from_full_path("Parent::Leaf"), "Parent::Leaf")
        self.assertEqual(material_name_from_full_path("Solo"), "Solo")
        self.assertEqual(material_name_from_full_path(""), "Layer")


if __name__ == "__main__":
    unittest.main()
