# -*- coding: utf-8 -*-
"""把 yak templates 拷到「文件\\LoopFlow\\」產品資料夾（對齊出圖 2.0）。"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import FrozenSet, Optional

STAMP_NAME = ".loopflow_yak_version"
PRODUCT_FOLDER = "Rhino to Blender Sync"
KEEP_NAMES: FrozenSet[str] = frozenset()


def documents_product_dir() -> Path:
    return Path.home() / "Documents" / "LoopFlow" / PRODUCT_FOLDER


def find_templates(src_root: Path) -> Optional[Path]:
    for parent in [src_root, *src_root.parents]:
        candidate = parent / "templates"
        if candidate.is_dir():
            return candidate
    return None


def _skip_file(name: str) -> bool:
    return name.endswith(".pyc") or name == STAMP_NAME


def copy_tree(src: Path, dest: Path, keep_names: FrozenSet[str]) -> bool:
    """覆寫官方檔；keep_names 若目的地已有則跳過。回傳是否有拷任何檔。"""
    copied = False
    dest.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = [name for name in dirs if name != "__pycache__"]
        rel = os.path.relpath(root, src)
        target_dir = dest if rel == "." else dest / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            if _skip_file(name):
                continue
            target = target_dir / name
            if name in keep_names and target.is_file():
                continue
            shutil.copy2(Path(root) / name, target)
            copied = True
    return copied


def _fill_product_dir(dest: Path, zips, stamp_src: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for zip_path in zips:
        shutil.copy2(zip_path, dest / zip_path.name)
    if stamp_src:
        (dest / STAMP_NAME).write_text(stamp_src + "\n", encoding="utf-8")


def sync_user_assets(
    src_root: Optional[Path] = None,
    dest: Optional[Path] = None,
    open_folder: bool = True,
) -> bool:
    """
    套件版號與戳記相同則不動。
    換版或尚未拷過：先填好暫存資料夾，成功後才換成產品資料夾。
    拷失敗時留下舊檔，下次指令會再試。沒有 templates／zip（開發 repo）則略過。
    """
    root = Path(src_root) if src_root is not None else Path(__file__).resolve().parents[1]
    templates = find_templates(root)
    if templates is None:
        return False
    zips = list(templates.glob("*.zip"))
    if not zips:
        return False
    stamp_src = ""
    stamp_file = templates / STAMP_NAME
    if stamp_file.is_file():
        stamp_src = stamp_file.read_text(encoding="utf-8").strip()
    target = Path(dest) if dest is not None else documents_product_dir()
    stamp_dst = target / STAMP_NAME
    if stamp_src and stamp_dst.is_file() and stamp_dst.read_text(encoding="utf-8").strip() == stamp_src:
        return False
    pending = target.with_name(target.name + ".pending")
    if pending.exists():
        shutil.rmtree(pending)
    _fill_product_dir(pending, zips, stamp_src)
    if target.exists():
        shutil.rmtree(target)
    pending.rename(target)
    print("LoopFlow: copied Blender zip to {}".format(target))
    if open_folder:
        try:
            os.startfile(str(target))  # noqa: S606
        except OSError:
            pass
    return True
