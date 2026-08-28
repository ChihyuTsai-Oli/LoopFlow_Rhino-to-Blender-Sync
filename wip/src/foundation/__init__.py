# -*- coding: utf-8 -*-
"""3.0 foundation：result／path／atomic／log／camera_payload。"""

from foundation.atomic import atomic_publish_bytes, atomic_publish_json, atomic_publish_text
from foundation.camera_payload import (
    SCHEMA_VERSION,
    build_camera_payload,
    parse_camera_payload,
    validate_camera_payload,
)
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
    resolve_camera_json_from_work_folder,
)
from foundation.result import Result
from foundation.stub import STUB_SUFFIX, stub_message

__all__ = [
    "Result",
    "STUB_SUFFIX",
    "stub_message",
    "SCHEMA_VERSION",
    "build_camera_payload",
    "parse_camera_payload",
    "validate_camera_payload",
    "require_saved_document_path",
    "resolve_camera_json_from_work_folder",
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
