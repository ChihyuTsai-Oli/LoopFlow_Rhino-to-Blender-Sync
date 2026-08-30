#! python 3
# -*- coding: utf-8 -*-
"""Yak 指令 RBLight。開發入口仍是 entrypoints/RBLight.py。"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

PLUGIN_ID = "860a0589-cda5-46a6-97ef-d538db8e0db3"
PLUGIN_NAME = "LoopFlow R2B"
YAK_NAME = "loopflow-rhino-to-blender-sync"
MARKER = ("rhino", "entrypoints", "RBModels.py")
_CMD = "RBLight"
_started = False


def _has_src(root):
    try:
        return (root / "foundation").is_dir() and root.joinpath(*MARKER).is_file()
    except Exception:
        return False


def _from_package_dir(package_dir):
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
        if _has_src(candidate):
            return candidate
    return None


def _from_rhp(rhp):
    if not rhp:
        return None
    try:
        path = Path(str(rhp))
        if path.is_file():
            return _from_package_dir(path.resolve().parent)
        return _from_package_dir(path)
    except Exception:
        return None


def _from_script(script_file):
    raw = str(script_file)
    if raw.startswith("file:"):
        from urllib.parse import unquote

        raw = unquote(raw.replace("file:///", "").replace("file://", ""))
        if os.name == "nt":
            raw = raw.replace("/", os.sep)
    try:
        here = Path(raw)
        if not here.is_file():
            here = Path(str(script_file))
    except Exception:
        return None
    for parent in here.parents:
        found = _from_package_dir(parent)
        if found:
            return found
    return None


def _version_key(name):
    parts = []
    for bit in name.split("."):
        try:
            parts.append((0, int(bit)))
        except ValueError:
            parts.append((1, bit))
    return parts


def _from_yak_install():
    roots = []
    for key in ("APPDATA", "LOCALAPPDATA"):
        base = str(os.environ.get(key) or "").strip()
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
                hit = _from_package_dir(version_dir)
                if hit:
                    found.append((version_dir.name, hit))
        except Exception:
            continue
    if not found:
        return None
    found.sort(key=lambda item: _version_key(item[0]))
    return found[-1][1]


def _plugin_rhps():
    paths = []
    try:
        import Rhino
        from System import Guid
    except Exception:
        return paths
    try:
        paths.append(Rhino.PlugIns.PlugIn.PathFromId(Guid(PLUGIN_ID)))
    except Exception:
        pass
    try:
        paths.append(Rhino.PlugIns.PlugIn.PathFromName(PLUGIN_NAME))
    except Exception:
        pass
    return paths


def _product_src():
    hit = _from_script(__file__)
    if hit:
        return hit
    for rhp in _plugin_rhps():
        hit = _from_rhp(rhp)
        if hit:
            return hit
    hit = _from_yak_install()
    if hit:
        return hit
    raise RuntimeError("Cannot find {} package src.".format(YAK_NAME))


def _prepare_src():
    src = str(_product_src())
    doomed = [
        name
        for name in list(sys.modules)
        if name == "rhino"
        or name.startswith("rhino.")
        or name == "foundation"
        or name.startswith("foundation.")
    ]
    for name in doomed:
        del sys.modules[name]
    while src in sys.path:
        sys.path.remove(src)
    sys.path.insert(0, src)
    return src


def _run():
    global _started
    if _started:
        return
    _started = True
    try:
        _prepare_src()
        from foundation.user_assets import sync_user_assets

        sync_user_assets()
        import rhinoscriptsyntax as rs  # type: ignore

        from rhino.commands.light import light_toggle_auto

        result = light_toggle_auto()
        msg = "{} [{}] {}".format(_CMD, result.status, result.message)
        print(msg)
        if not result.ok and result.status == "blocked":
            rs.MessageBox(result.message)
    except Exception:
        err = traceback.format_exc()
        print(err)
        try:
            import rhinoscriptsyntax as rs  # type: ignore

            rs.MessageBox(err[-1500:], title=_CMD)
        except Exception:
            pass


def RunCommand(is_interactive):
    _run()


_run()
