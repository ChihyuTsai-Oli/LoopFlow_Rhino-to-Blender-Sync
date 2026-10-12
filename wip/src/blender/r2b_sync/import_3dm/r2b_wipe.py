# -*- coding: utf-8 -*-
"""R2B 子樹 wipe 規則（不依賴 bpy，方便純 Python 測試）。"""
from __future__ import annotations

# 若被誤掛在 R2B 下也不清（ED-08 燈光模板）。
PROTECTED_COLLECTION_NAMES = frozenset(
    {"Lighting", "Lighting Fixtures", "R2B Lighting Points"}
)


def should_preserve_collection(name: str, root_name: str) -> bool:
    """wipe 時保留根集合與燈光集合。"""
    return name == root_name or name in PROTECTED_COLLECTION_NAMES
