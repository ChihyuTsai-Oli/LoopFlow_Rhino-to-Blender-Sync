# -*- coding: utf-8 -*-
"""同一 Rhino 行程裡 R2B／R2O 不得互踩套件快取。"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ISOLATE = (
    Path(__file__).resolve().parents[1] / "src" / "rhino" / "entrypoints" / "_isolate.py"
)


def _load_isolate():
    spec = importlib.util.spec_from_file_location("_loopflow_isolate_test", ISOLATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_fake_src(root: Path, marker: str) -> None:
    (root / "foundation").mkdir(parents=True)
    (root / "rhino" / "commands").mkdir(parents=True)
    (root / "foundation" / "__init__.py").write_text("", encoding="utf-8")
    (root / "rhino" / "__init__.py").write_text("", encoding="utf-8")
    (root / "rhino" / "commands" / "__init__.py").write_text("", encoding="utf-8")
    (root / "foundation" / "paths.py").write_text(
        "MARKER = {!r}\n".format(marker), encoding="utf-8"
    )
    (root / "rhino" / "commands" / "models.py").write_text(
        "from foundation.paths import MARKER\nVALUE = MARKER\n",
        encoding="utf-8",
    )


class IsolateTests(unittest.TestCase):
    def test_second_isolate_wins(self):
        iso = _load_isolate()
        real_src = Path(__file__).resolve().parents[1] / "src"
        with tempfile.TemporaryDirectory() as tmp:
            src_a = Path(tmp) / "a"
            src_b = Path(tmp) / "b"
            _write_fake_src(src_a, "product-a")
            _write_fake_src(src_b, "product-b")
            try:
                iso.isolate_src(str(src_a))
                from rhino.commands.models import VALUE as first

                self.assertEqual(first, "product-a")

                iso.isolate_src(str(src_b))
                from rhino.commands.models import VALUE as second

                self.assertEqual(second, "product-b")
                self.assertEqual(Path(sys.path[0]), src_b.resolve())
            finally:
                for folder in (src_a, src_b):
                    resolved = str(folder.resolve())
                    while resolved in sys.path:
                        sys.path.remove(resolved)
                iso.isolate_src(str(real_src))


if __name__ == "__main__":
    unittest.main()
