# -*- coding: utf-8 -*-
"""Block sidecar 矩陣與契約。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.block_payload import (
    build_blocks_payload,
    mat4_identity,
    mat4_invert,
    mat4_mul,
    relative_xform,
    rhino_mat4_translation_scaled,
    validate_blocks_payload,
)


def _translate(x, y, z):
    m = mat4_identity()
    m[3] = float(x)
    m[7] = float(y)
    m[11] = float(z)
    return m


class Mat4Tests(unittest.TestCase):
    def test_identity_inverse(self):
        ident = mat4_identity()
        inv = mat4_invert(ident)
        self.assertIsNotNone(inv)
        self.assertEqual(inv, ident)

    def test_relative_translation(self):
        proto = _translate(10, 0, 0)
        other = _translate(25, 0, 0)
        rel = relative_xform(proto, other)
        self.assertIsNotNone(rel)
        self.assertAlmostEqual(rel[3], 15.0, places=6)
        self.assertAlmostEqual(rel[7], 0.0, places=6)

    def test_scale_translation_only(self):
        m = _translate(100, 0, 0)
        scaled = rhino_mat4_translation_scaled(m, 0.01)
        self.assertAlmostEqual(scaled[3], 1.0, places=6)
        self.assertAlmostEqual(scaled[0], 1.0, places=6)


class BlocksPayloadTests(unittest.TestCase):
    def test_build_and_validate(self):
        payload = build_blocks_payload(
            [
                {
                    "id": "abc",
                    "name": "Chair",
                    "prototype_xform": mat4_identity(),
                    "copies": [{"xform": _translate(1, 2, 3), "layer": "A::B"}],
                }
            ]
        )
        self.assertIsNone(validate_blocks_payload(payload))

    def test_reject_bad_xform(self):
        err = validate_blocks_payload(
            {
                "schema_version": 1,
                "definitions": [
                    {
                        "id": "x",
                        "prototype_xform": [1, 2, 3],
                        "copies": [],
                    }
                ],
            }
        )
        self.assertIsNotNone(err)


if __name__ == "__main__":
    unittest.main()
