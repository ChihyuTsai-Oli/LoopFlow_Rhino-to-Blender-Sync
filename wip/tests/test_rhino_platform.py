# -*- coding: utf-8 -*-
"""R2B-B03 Rhino platform 純 Python 測試。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.result import Result
from rhino.platform.collect import collect_ids_under_layer, layer_subtree_paths
from rhino.platform.guard import run_guarded
from rhino.platform.memory import MemorySession


class LayerCollectTests(unittest.TestCase):
    def test_subtree_paths(self):
        all_paths = ("A", "A::B", "A::B::C", "Other", "A2")
        self.assertEqual(layer_subtree_paths(all_paths, "A"), ("A", "A::B", "A::B::C"))
        self.assertEqual(layer_subtree_paths(all_paths, "A2"), ("A2",))
        self.assertEqual(layer_subtree_paths(all_paths, ""), ())

    def test_collect_excludes_point_curve_by_default(self):
        s = MemorySession()
        s.add_object("m1", "Model", kind="brep")
        s.add_object("p1", "Model", kind="point")
        s.add_object("c1", "Model::Detail", kind="curve")
        s.add_object("m2", "Model::Detail", kind="mesh", hidden=True, locked=True)
        s.add_object("x1", "Other", kind="brep")
        ids = collect_ids_under_layer(s, "Model")
        self.assertEqual(ids, ("m1", "m2"))

    def test_empty_when_layer_missing(self):
        s = MemorySession()
        s.add_object("m1", "Model", kind="brep")
        self.assertEqual(collect_ids_under_layer(s, "Missing"), ())


class GuardTests(unittest.TestCase):
    def _session(self):
        s = MemorySession(path=r"E:\tmp\demo.3dm", modified=False)
        s.add_object("a", "L", kind="brep", selected=False)
        return s

    def test_success_restores_modified_and_selection(self):
        s = self._session()

        def action():
            s.set_document_modified(True)
            s.select_objects(["a"])
            self.assertTrue(s.objects["a"].selected)
            return Result.success("ok")

        r = run_guarded(s, action)
        self.assertTrue(r.ok)
        self.assertFalse(s.document_modified())
        self.assertFalse(s.objects["a"].selected)

    def test_fail_restores(self):
        s = self._session()

        def action():
            s.set_document_modified(True)
            s.select_objects(["a"])
            return Result.fail("boom", stage="x")

        r = run_guarded(s, action)
        self.assertFalse(r.ok)
        self.assertFalse(s.document_modified())
        self.assertFalse(s.objects["a"].selected)

    def test_exception_restores(self):
        s = self._session()

        def action():
            s.set_document_modified(True)
            raise RuntimeError("explode")

        r = run_guarded(s, action)
        self.assertEqual(r.status, "fail")
        self.assertFalse(s.document_modified())

    def test_select_objects_records_precise_ids_not_selall(self):
        s = self._session()
        s.add_object("b", "L", kind="brep")
        s.select_objects(["a"])
        self.assertEqual(s.select_calls[-1], ("a",))
        self.assertTrue(s.objects["a"].selected)
        self.assertFalse(s.objects["b"].selected)


if __name__ == "__main__":
    unittest.main()
