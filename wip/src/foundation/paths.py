# -*- coding: utf-8 -*-
"""R2B 專案設定根與交換檔路徑（開發暫定檔名；A02 凍結前可調）。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

from foundation.result import Result

PathLike = Union[str, os.PathLike]

CONFIG_PARENT_NAME = "_LoopFlow_Config"
PRODUCT_DIR_NAME = "loopflow_R2B"

LIVE_DIR_NAME = "live"
MODELS_DIR_NAME = "models"

# 開發暫定檔名（見工作流程／資料契約；尚未對使用者凍結）
CONFIG_FILE_NAME = "config.json"
LOG_FILE_NAME = "r2b.log"
CAMERA_FILE_NAME = "camera.json"
LIGHT_FILE_NAME = "light.json"
MODEL_FILE_NAME = "model.3dm"


def require_saved_document_path(doc_path: Optional[str]) -> Result:
    """未存檔工作檔不得發布設定／交換檔。"""
    if not doc_path or not str(doc_path).strip():
        return Result.blocked("請先儲存 Rhino 檔案", stage="require_saved")
    path = Path(doc_path)
    if not path.is_file():
        return Result.blocked("工作檔路徑無效或不存在：{}".format(doc_path), stage="require_saved")
    return Result.success(data=str(path.resolve()), stage="require_saved")


def config_root_for_document(doc_path: PathLike) -> Path:
    """已存檔 `.3dm` 旁的 `_LoopFlow_Config/loopflow_R2B/`。"""
    doc = Path(doc_path).resolve()
    return doc.parent / CONFIG_PARENT_NAME / PRODUCT_DIR_NAME


def live_dir(root: PathLike) -> Path:
    return Path(root) / LIVE_DIR_NAME


def models_dir(root: PathLike) -> Path:
    return Path(root) / MODELS_DIR_NAME


def camera_path(root: PathLike) -> Path:
    return live_dir(root) / CAMERA_FILE_NAME


def resolve_camera_json_from_work_folder(work_folder: PathLike) -> Path:
    """
    從作業資料夾（.3dm／.blend／_LoopFlow_Config 同層）解析 camera.json。

    主路徑：{work}/_LoopFlow_Config/loopflow_R2B/live/camera.json
    備援：舊測法指到 loopflow_R2B、live、或檔案本身所在目錄。
    """
    folder = Path(work_folder)
    candidates = (
        folder / CONFIG_PARENT_NAME / PRODUCT_DIR_NAME / LIVE_DIR_NAME / CAMERA_FILE_NAME,
        folder / PRODUCT_DIR_NAME / LIVE_DIR_NAME / CAMERA_FILE_NAME,
        folder / LIVE_DIR_NAME / CAMERA_FILE_NAME,
        folder / CAMERA_FILE_NAME,
    )
    for path in candidates:
        if path.is_file():
            return path.resolve()
    # 預設回傳主路徑（供錯誤訊息）
    return candidates[0]


def light_path(root: PathLike) -> Path:
    return live_dir(root) / LIGHT_FILE_NAME


def resolve_light_json_from_work_folder(work_folder: PathLike) -> Path:
    """
    從作業資料夾解析 light.json。

    主路徑：{work}/_LoopFlow_Config/loopflow_R2B/live/light.json
    """
    folder = Path(work_folder)
    candidates = (
        folder / CONFIG_PARENT_NAME / PRODUCT_DIR_NAME / LIVE_DIR_NAME / LIGHT_FILE_NAME,
        folder / PRODUCT_DIR_NAME / LIVE_DIR_NAME / LIGHT_FILE_NAME,
        folder / LIVE_DIR_NAME / LIGHT_FILE_NAME,
        folder / LIGHT_FILE_NAME,
    )
    for path in candidates:
        if path.is_file():
            return path.resolve()
    return candidates[0]


def model_path(root: PathLike) -> Path:
    return models_dir(root) / MODEL_FILE_NAME


def config_path(root: PathLike) -> Path:
    return Path(root) / CONFIG_FILE_NAME


def log_path(root: PathLike) -> Path:
    return Path(root) / LOG_FILE_NAME


def pending_path_for(final_path: PathLike) -> Path:
    """同目錄：`name.ext` → `name_pending.ext`。"""
    final = Path(final_path)
    return final.with_name("{}_pending{}".format(final.stem, final.suffix))


def ensure_config_layout(root: PathLike) -> Path:
    """建立設定根與 live／models 子目錄；回傳 resolve 後的 root。"""
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    live_dir(root_path).mkdir(parents=True, exist_ok=True)
    models_dir(root_path).mkdir(parents=True, exist_ok=True)
    return root_path.resolve()
