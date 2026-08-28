# -*- coding: utf-8 -*-
"""相機自動同步閘：debounce＋姿態未變略過（純邏輯，不依賴 Rhino）。"""
from __future__ import annotations

from typing import Optional, Tuple

from foundation.camera_payload import poses_equivalent

DEFAULT_INTERVAL_SEC = 0.04

Pose = Optional[Tuple[float, ...]]


class CameraAutoPublishGate:
    """
    View.Modified 只標記 dirty；達到間隔或 Idle 強制刷新才發布。
    姿態與上次成功發布相同則略過寫盤。
    """

    def __init__(self, interval_sec: float = DEFAULT_INTERVAL_SEC) -> None:
        self.interval_sec = float(interval_sec)
        self.dirty = False
        self.last_publish_t = 0.0
        self.last_pose: Pose = None

    def note_view_modified(self) -> None:
        self.dirty = True

    def decide(self, now: float, pose: Pose, *, force: bool) -> str:
        """回傳 publish／skip／wait。"""
        if not self.dirty:
            return "skip"
        if poses_equivalent(pose, self.last_pose):
            self.dirty = False
            return "skip"
        if (
            self.last_pose is not None
            and not force
            and (now - self.last_publish_t) < self.interval_sec
        ):
            return "wait"
        return "publish"

    def mark_published(self, now: float, pose: Pose) -> None:
        self.dirty = False
        self.last_publish_t = float(now)
        self.last_pose = pose
