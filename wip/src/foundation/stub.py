# -*- coding: utf-8 -*-
"""空殼共用訊息（無 Rhino／Blender 依賴）。"""

STUB_SUFFIX = "Not implemented (3.0 stub)"


def stub_message(command_id: str) -> str:
    """回傳給使用者看的空殼提示。"""
    return f"{command_id}: {STUB_SUFFIX}"
