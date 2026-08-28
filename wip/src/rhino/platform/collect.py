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
DEFAULT_LAYER_EXCLUDE_TOKEN = "//"


def layer_path_is_excluded(
    full_path: str, exclude_token: str = DEFAULT_LAYER_EXCLUDE_TOKEN
) -> bool:
    """
    圖層 FullPath 含排除標記則不匯出。

    預設標記 `//`（與 2.x 一致）。空白標記＝不排除。
    """
    token = (exclude_token or "").strip()
    if not token:
        return False
    return token in (full_path or "")


def layer_subtree_paths(
    all_paths: Sequence[str],
    root: str,
    *,
    exclude_token: str = DEFAULT_LAYER_EXCLUDE_TOKEN,
) -> tuple:
    """回傳 root 與其子圖層 FullPath（`::` 分隔）；略過含排除標記者。"""
    root = (root or "").strip()
    if not root:
        return ()
    if layer_path_is_excluded(root, exclude_token):
        return ()
    prefix = root + "::"
    out = []
    for path in all_paths:
        if path is None:
            continue
        p = str(path)
        if layer_path_is_excluded(p, exclude_token):
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
    exclude_token: str = DEFAULT_LAYER_EXCLUDE_TOKEN,
) -> tuple:
    """
    依圖層子樹收集物件 ID。

    - 只透過 session.objects_on_layer；禁止 _SelAll。
    - include_kinds 預設 DEFAULT_INCLUDED_KINDS；exclude_kinds 預設 point／curve。
    - 空清單由呼叫端決定是否阻擋（ED-07 Models）。
    """
    paths = layer_subtree_paths(
        session.layer_paths(), root, exclude_token=exclude_token
    )
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
