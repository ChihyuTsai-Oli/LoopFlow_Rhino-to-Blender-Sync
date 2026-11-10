"""把淺／深色 SVG 寫進現行 Rhino 8 產品 LoopFlow_R2B.rui。"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUI = HERE / "LoopFlow_R2B.rui"

SCRIPT_TO_SVG = {
    "! _RBOpen": "R2B_Open.svg",
    "! _RBModels": "R2B_Model.svg",
    "! _RBCamera": "R2B_Camera.svg",
    "! _RBLight": "R2B_Light.svg",
}

MACRO_RE = re.compile(
    r'<macro_item\b([^>]*)>.*?<script>(.*?)</script>',
    re.DOTALL,
)
BITMAP_RE = re.compile(r'\bbitmap_id="([^"]+)"')
ICON_RE = re.compile(r'(<icon guid="([^"]+)"[^>]*>)(.*?)(</icon>)', re.DOTALL)
OUTER = (
    '<svg width="48" height="48" version="1.1" '
    'xmlns="http://www.w3.org/2000/svg" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" '
    'viewBox="0pt 0pt 48pt 48pt">'
)


def load_inner(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^?]*\?>\s*", "", text)
    text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", text)
    text = text.replace(' xmlns:affinity="https://www.affinity.studio/"', "")
    text = text.strip()
    if not text.startswith("<svg"):
        raise SystemExit("不是 SVG：%s" % path)
    return text


def wrap(inner: str, slot: str) -> str:
    return "      <%s>%s\n  %s\n</svg></%s>" % (slot, OUTER, inner, slot)


def bitmap_ids(rui_text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    scripts = set()
    for attrs, script in MACRO_RE.findall(rui_text):
        command = re.sub(r"\s+", " ", script).strip()
        scripts.add(command)
        svg_name = SCRIPT_TO_SVG.get(command)
        if svg_name is None:
            continue
        match = BITMAP_RE.search(attrs)
        if match is None:
            raise SystemExit("巨集沒有 bitmap_id：%s" % command)
        guid = match.group(1)
        previous = found.get(guid)
        if previous and previous != svg_name:
            raise SystemExit("同一 icon GUID 對到兩份 SVG：%s" % guid)
        found[guid] = svg_name
    missing = set(SCRIPT_TO_SVG) - scripts
    if missing:
        raise SystemExit("rui 找不到這些巨集：%s" % ", ".join(sorted(missing)))
    return found


def inject(rui_text: str, light_dir: Path, dark_dir: Path) -> str:
    targets = bitmap_ids(rui_text)
    used: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        open_tag, guid, _body, close_tag = match.group(1), match.group(2), match.group(3), match.group(4)
        svg_name = targets.get(guid)
        if svg_name is None:
            return match.group(0)
        used.add(guid)
        light = load_inner(light_dir / svg_name)
        dark = load_inner(dark_dir / svg_name)
        inner = "\n%s\n%s\n    " % (wrap(light, "light"), wrap(dark, "dark"))
        return open_tag + inner + close_tag

    updated = ICON_RE.sub(replace, rui_text)
    leftover = set(targets) - used
    if leftover:
        raise SystemExit("rui 找不到這些 icon GUID：%s" % ", ".join(sorted(leftover)))
    for guid, svg_name in targets.items():
        block = next(
            match.group(0)
            for match in ICON_RE.finditer(updated)
            if match.group(2) == guid
        )
        if "fill-dark=" in block:
            raise SystemExit("產品圖仍有 fill-dark：%s (%s)" % (guid, svg_name))
        if "<light>" not in block or "<dark>" not in block:
            raise SystemExit("產品圖缺少 light/dark：%s (%s)" % (guid, svg_name))
    return updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="寫入 Rhino 8 工具列淺／深色 SVG")
    parser.add_argument("--light", required=True, type=Path, help="淺色 SVG 資料夾")
    parser.add_argument("--dark", required=True, type=Path, help="深色 SVG 資料夾")
    args = parser.parse_args(argv)
    light_dir = args.light.expanduser().resolve()
    dark_dir = args.dark.expanduser().resolve()
    if not light_dir.is_dir() or not dark_dir.is_dir():
        raise SystemExit("找不到淺色或深色資料夾")
    text = RUI.read_text(encoding="utf-8")
    RUI.write_text(inject(text, light_dir, dark_dir), encoding="utf-8", newline="\n")
    print("updated", RUI)
    return 0


if __name__ == "__main__":
    sys.exit(main())
