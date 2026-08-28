# -*- coding: utf-8 -*-
"""圖層子樹與物件 ID 收集（純邏輯；不呼叫 Rhino Command／_SelAll）。"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence, Set

# ED-01：Point／Curve 預設不勾；其餘預設勾（呼叫端可覆寫）
DEFAULT_INCLUDED_KINDS: Set[str] = {
    "brep",
    "mesh",
    "subd",
    "extrusion",
    "surface",
    "polysurface",
    "block",
    "instance",
    "other",
}

DEFAULT_EXCLUDED_KINDS: Set[str] = {"point", "curve"}


def layer_path_is_excluded(full_path: str) -> bool:
    """FullPath 含 `//` 者不匯出（與 2.x 清理語意一致）。"""
    return "//" in (full_path or "")


def layer_subtree_paths(all_paths: Sequence[str], root: str) -> tuple:
    """回傳 root 與其子圖層 FullPath（`::` 分隔）；略過含 // 者。"""
    root = (root or "").strip()
    if not root:
        return ()
    if layer_path_is_excluded(root):
        return ()
    prefix = root + "::"
    out = []
    for path in all_paths:
        if path is None:
            continue
        p = str(path)
        if layer_path_is_excluded(p):
            continue
        if p == root or p.startswith(prefix):
            out.append(p)
    return tuple(out)


def collect_ids_under_layer(
    session,
    root: str,
    *,
    include_kinds: Optional[Iterable[str]] = None,
    exclude_kinds: Optional[Iterable[str]] = None,
) -> tuple:
    """
    依圖層子樹收集物件 ID。

    - 只透過 session.objects_on_layer；禁止 _SelAll。
    - include_kinds 預設 DEFAULT_INCLUDED_KINDS；exclude_kinds 預設 point／curve。
    - 空清單由呼叫端決定是否阻擋（ED-07 Models）。
    """
    paths = layer_subtree_paths(session.layer_paths(), root)
    if not paths:
        return ()

    allowed = (
        {str(k).lower() for k in include_kinds}
        if include_kinds is not None
        else set(DEFAULT_INCLUDED_KINDS)
    )
    excluded = (
        {str(k).lower() for k in exclude_kinds}
        if exclude_kinds is not None
        else set(DEFAULT_EXCLUDED_KINDS)
    )

    seen = set()
    ordered = []
    for path in paths:
        for oid in session.objects_on_layer(path):
            if oid in seen:
                continue
            kind = str(session.object_kind(oid) or "other").lower()
            if kind in excluded:
                continue
            if kind not in allowed:
                continue
            seen.add(oid)
            ordered.append(str(oid))
    return tuple(ordered)
