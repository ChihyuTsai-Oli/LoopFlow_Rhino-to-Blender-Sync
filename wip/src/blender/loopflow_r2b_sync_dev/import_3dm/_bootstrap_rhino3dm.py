# -*- coding: utf-8 -*-
"""從本套件 wheels/ 載入 rhino3dm（不依賴 Blender Extension 自動 wheels）。"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def ensure_rhino3dm():
    """
    確保可 `import rhino3dm`。

    傳統 scripts/addons 不會吃 blender_manifest.toml 的 wheels，
    因此在此依 CPython 版本解壓對應 .whl 到 _vendor/。
    """
    try:
        import rhino3dm  # noqa: F401

        return
    except ImportError:
        pass

    here = Path(__file__).resolve().parent
    wheels_dir = here / "wheels"
    major, minor = sys.version_info[:2]
    tag = "cp{}{}".format(major, minor)

    candidates = sorted(wheels_dir.glob("rhino3dm-*-{}-*.whl".format(tag)))
    if not candidates:
        raise ImportError(
            "找不到 rhino3dm wheel（需要 {}）。目錄：{}".format(tag, wheels_dir)
        )

    chosen = None
    if sys.platform == "win32":
        for path in candidates:
            if "win_amd64" in path.name or "win32" in path.name:
                chosen = path
                break
    elif sys.platform == "darwin":
        for path in candidates:
            if "macosx" in path.name:
                chosen = path
                break
    else:
        for path in candidates:
            if "linux" in path.name or "manylinux" in path.name:
                chosen = path
                break
    if chosen is None:
        chosen = candidates[0]

    vendor = here / "_vendor" / "{}-{}".format(tag, sys.platform)
    marker = vendor / ".wheel_name"
    need_extract = True
    if vendor.is_dir() and marker.is_file():
        try:
            if marker.read_text(encoding="utf-8").strip() == chosen.name:
                need_extract = False
        except OSError:
            need_extract = True

    if need_extract:
        import shutil

        vendor.mkdir(parents=True, exist_ok=True)
        for child in list(vendor.iterdir()):
            if child.name == ".wheel_name":
                continue
            if child.is_file():
                try:
                    child.unlink()
                except OSError:
                    pass
            else:
                shutil.rmtree(child, ignore_errors=True)
        with zipfile.ZipFile(chosen, "r") as zf:
            zf.extractall(vendor)
        marker.write_text(chosen.name + "\n", encoding="utf-8")

    vendor_str = str(vendor)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

    import rhino3dm  # noqa: F401
