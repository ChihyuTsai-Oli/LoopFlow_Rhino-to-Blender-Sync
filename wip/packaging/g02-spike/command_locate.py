# -*- coding: utf-8 -*-
"""找出已安裝 R2B yak 的 src。

RhinoCode 執行指令時會把腳本拷到 ``%USERPROFILE%\\.rhinocode\\stage\\``，
``__file__`` 不再位於套件目錄，也不能再載入旁邊的 ``_isolate.py``。
指令 ``.py`` 必須內嵌同一份查找邏輯（對齊出圖 2.0）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional

PLUGIN_ID = "860a0589-cda5-46a6-97ef-d538db8e0db3"
PLUGIN_NAME = "LoopFlow R2B"
YAK_NAME = "loopflow-rhino-to-blender-sync"
MARKER = ("rhino", "entrypoints", "RBModels.py")


def has_product_src(root: Path) -> bool:
    try:
        return (root / "foundation").is_dir() and root.joinpath(*MARKER).is_file()
    except Exception:
        return False


def from_package_dir(package_dir: Optional[Path]) -> Optional[Path]:
    if package_dir is None:
        return None
    try:
        package_dir = Path(str(package_dir))
        if not package_dir.is_dir():
            return None
        package_dir = package_dir.resolve()
    except Exception:
        return None
    candidates = [package_dir / "src", package_dir / "lib", package_dir]
    libs = package_dir / "libs"
    try:
        if libs.is_dir():
            for child in libs.iterdir():
                candidates.append(child / "src")
                candidates.append(child)
    except Exception:
        pass
    for candidate in candidates:
        if has_product_src(candidate):
            return candidate
    return None


def _version_key(name: str):
    parts = []
    for bit in name.split("."):
        try:
            parts.append((0, int(bit)))
        except ValueError:
            parts.append((1, bit))
    return parts


def from_yak_install(environ: Optional[Mapping[str, str]] = None) -> Optional[Path]:
    env = environ if environ is not None else os.environ
    roots = []
    for key in ("APPDATA", "LOCALAPPDATA"):
        base = str(env.get(key) or "").strip()
        if base:
            roots.append(
                Path(base) / "McNeel" / "Rhinoceros" / "packages" / "8.0" / YAK_NAME
            )
    found = []
    for root in roots:
        try:
            if not root.is_dir():
                continue
            for version_dir in root.iterdir():
                if not version_dir.is_dir():
                    continue
                hit = from_package_dir(version_dir)
                if hit:
                    found.append((version_dir.name, hit))
        except Exception:
            continue
    if not found:
        return None
    found.sort(key=lambda item: _version_key(item[0]))
    return found[-1][1]
