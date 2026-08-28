# -*- coding: utf-8 -*-
"""3.0 foundation：result／path／atomic／log（無 Rhino／Blender 依賴）。"""

from foundation.atomic import atomic_publish_bytes, atomic_publish_json, atomic_publish_text
from foundation.log import append_log
from foundation.paths import (
    CAMERA_FILE_NAME,
    CONFIG_FILE_NAME,
    CONFIG_PARENT_NAME,
    LIGHT_FILE_NAME,
    LOG_FILE_NAME,
    MODEL_FILE_NAME,
    PRODUCT_DIR_NAME,
    camera_path,
    config_path,
    config_root_for_document,
    ensure_config_layout,
    light_path,
    log_path,
    model_path,
    pending_path_for,
    require_saved_document_path,
)
from foundation.result import Result
from foundation.stub import STUB_SUFFIX, stub_message

__all__ = [
    "Result",
    "STUB_SUFFIX",
    "stub_message",
    "require_saved_document_path",
    "config_root_for_document",
    "ensure_config_layout",
    "camera_path",
    "light_path",
    "model_path",
    "config_path",
    "log_path",
    "pending_path_for",
    "atomic_publish_bytes",
    "atomic_publish_text",
    "atomic_publish_json",
    "append_log",
    "CONFIG_PARENT_NAME",
    "PRODUCT_DIR_NAME",
    "CONFIG_FILE_NAME",
    "LOG_FILE_NAME",
    "CAMERA_FILE_NAME",
    "LIGHT_FILE_NAME",
    "MODEL_FILE_NAME",
]
