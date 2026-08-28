# -*- coding: utf-8 -*-
"""公開使用說明入口（GitHub；對齊 LoopFlow 2.0 `LF_Document`）。"""
from __future__ import annotations

import os
from typing import Callable, Optional

# 3.0 開發期指向整合分支；正式發布改 main（與 LoopFlow 2.0 相同型式）
DOCS_ENTRY_URL = (
    "https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/"
    "blob/v3-development/docs/README.md"
)

Opener = Callable[[str], None]


def default_opener(url: str) -> None:
    os.startfile(url)  # noqa: S606  Windows default browser


def open_docs_in_browser(*, opener: Optional[Opener] = None) -> str:
    """開入口頁；失敗回傳英文錯誤，成功回空字串。"""
    launch = opener or default_opener
    try:
        launch(DOCS_ENTRY_URL)
    except OSError as exc:
        return "Could not open documentation: {}".format(exc)
    return ""
