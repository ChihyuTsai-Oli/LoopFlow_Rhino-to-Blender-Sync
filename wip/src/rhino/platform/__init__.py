# -*- coding: utf-8 -*-
"""Rhino platform：snapshot／restore、圖層 ID 收集、Memory／Live session。"""

from rhino.platform.collect import (
    DEFAULT_EXCLUDED_KINDS,
    DEFAULT_INCLUDED_KINDS,
    collect_ids_under_layer,
    layer_subtree_paths,
)
from rhino.platform.guard import capture_snapshot, restore_snapshot, run_guarded
from rhino.platform.live import LiveSession, open_session
from rhino.platform.memory import MemorySession
from rhino.platform.state import DocumentSnapshot, ObjectViewState

__all__ = [
    "ObjectViewState",
    "DocumentSnapshot",
    "layer_subtree_paths",
    "collect_ids_under_layer",
    "DEFAULT_INCLUDED_KINDS",
    "DEFAULT_EXCLUDED_KINDS",
    "capture_snapshot",
    "restore_snapshot",
    "run_guarded",
    "MemorySession",
    "LiveSession",
    "open_session",
]
