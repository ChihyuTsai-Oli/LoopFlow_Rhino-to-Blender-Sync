# -*- coding: utf-8 -*-
"""相機自動同步閘：debounce＋姿態未變略過（純邏輯，不依賴 Rhino）。"""
from __future__ import annotations

from typing import Optional, Tuple

from foundation.camera_payload import poses_equivalent

DEFAULT_INTERVAL_SEC = 0.033

Pose = Optional[Tuple[float, ...]]


class CameraAutoPublishGate:
    """
    View.Modified 只標記 dirty；間隔到了才擷取寫盤（不在每幀 capture）。
    Idle 補發最後一幀。姿態未變則略過。
    """

    def __init__(self, interval_sec: float = DEFAULT_INTERVAL_SEC) -> None:
        self.interval_sec = float(interval_sec)
        self.dirty = False
        self.last_publish_t = 0.0
        self.last_pose: Pose = None

    def note_view_modified(self) -> None:
        self.dirty = True

    def due_to_flush(self, now: float) -> bool:
        """尚未到期則不 capture、不寫盤。"""
        if not self.dirty:
            return False
        if self.last_pose is not None and (now - self.last_publish_t) < self.interval_sec:
            return False
        return True

    def decide(self, now: float, pose: Pose) -> str:
        """回傳 publish／skip／wait。"""
        if not self.dirty:
            return "skip"
        if poses_equivalent(pose, self.last_pose):
            self.dirty = False
            return "skip"
        if self.last_pose is not None and (now - self.last_publish_t) < self.interval_sec:
            return "wait"
        return "publish"

    def mark_published(self, now: float, pose: Pose) -> None:
        self.dirty = False
        self.last_publish_t = float(now)
        self.last_pose = pose
