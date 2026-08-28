# -*- coding: utf-8 -*-
"""相機自動同步閘：姿態未變略過（純邏輯，不依賴 Rhino）。"""
from __future__ import annotations

from typing import Optional, Tuple

from foundation.camera_payload import poses_equivalent

Pose = Optional[Tuple[float, ...]]


class CameraAutoPublishGate:
    """View.Modified 立刻寫盤；僅姿態未變時略過。"""

    def __init__(self) -> None:
        self.last_pose: Pose = None

    def should_publish(self, pose: Pose) -> bool:
        return not poses_equivalent(pose, self.last_pose)

    def mark_published(self, pose: Pose) -> None:
        self.last_pose = pose
