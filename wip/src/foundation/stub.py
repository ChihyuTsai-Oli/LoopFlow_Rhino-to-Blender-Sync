# -*- coding: utf-8 -*-
"""空殼共用訊息（無 Rhino／Blender 依賴）。"""

STUB_SUFFIX = "尚未實作（3.0 空殼入口）"


def stub_message(command_id: str) -> str:
    """回傳給使用者看的空殼提示。"""
    return f"{command_id}：{STUB_SUFFIX}"
