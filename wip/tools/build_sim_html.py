#!/usr/bin/env python3
"""將操作流程模擬_合併.md 轉成寬版 HTML。"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def md_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def convert(md: str, title: str) -> str:
    lines = md.splitlines()
    body: list[str] = []
    toc: list[tuple[str, str]] = []
    i = 0
    para: list[str] = []

    def flush() -> None:
        if not para:
            return
        body.append(f"<p>{md_inline(' '.join(para).strip())}</p>")
        para.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            flush()
            body.append(f"<h1>{md_inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            flush()
            t = line[3:].strip()
            aid = re.sub(r"[^\w\-]+", "-", t, flags=re.U).strip("-").lower() or f"s{i}"
            toc.append((t, aid))
            body.append(f'<h2 id="{aid}">{md_inline(t)}</h2>')
        elif line.startswith("### "):
            flush()
            body.append(f"<h3>{md_inline(line[4:].strip())}</h3>")
        elif line.startswith(">"):
            flush()
            body.append(f"<blockquote><p>{md_inline(line.lstrip('> ').strip())}</p></blockquote>")
        elif line.startswith("```"):
            flush()
            i += 1
            chunk = []
            while i < len(lines) and not lines[i].startswith("```"):
                chunk.append(html.escape(lines[i]))
                i += 1
            body.append("<pre><code>" + "\n".join(chunk) + "</code></pre>")
        elif line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().split("|")[1:-1]]
                rows.append(cells)
                i += 1
            i -= 1
            if len(rows) >= 2:
                body.append('<div class="tw"><table><thead><tr>')
                for h in rows[0]:
                    body.append(f"<th>{md_inline(h)}</th>")
                body.append("</tr></thead><tbody>")
                for r in rows[1:]:
                    if r and re.match(r"^[\s\-:]+$", r[0]):
                        continue
                    body.append("<tr>")
                    for c in r:
                        body.append(f"<td>{md_inline(c)}</td>")
                    body.append("</tr>")
                body.append("</tbody></table></div>")
        elif re.match(r"^\d+\.\s", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                items.append(f"<li>{md_inline(re.sub(r'^\\d+\\.\\s', '', lines[i]))}</li>")
                i += 1
            i -= 1
            body.append("<ol>" + "".join(items) + "</ol>")
        elif line.startswith("- "):
            flush()
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{md_inline(lines[i][2:])}</li>")
                i += 1
            i -= 1
            body.append("<ul>" + "".join(items) + "</ul>")
        elif line.strip() == "":
            flush()
        else:
            para.append(line)
        i += 1
    flush()

    nav = "\n".join(f'<a href="#{a}">{html.escape(t)}</a>' for t, a in toc)
    css = """
:root{color-scheme:dark;--bg:#101417;--panel:#171d21;--line:#39444a;--text:#edf2f3;--muted:#a9b4b8;--accent:#74c9b4}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.65 system-ui,"Noto Sans TC",sans-serif}
.layout{display:grid;grid-template-columns:240px minmax(0,1fr);min-height:100vh}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 18px;border-right:1px solid var(--line);background:#0c1012}
nav strong{display:block;margin-bottom:14px;color:var(--accent);font-size:17px}
nav a{display:block;padding:6px 8px;color:var(--muted);text-decoration:none;border-radius:5px}
nav a:hover{color:var(--text);background:#20292d}
main{padding:34px 36px 70px;max-width:980px}h1{margin-top:0}h2{margin-top:36px;padding-top:8px;border-top:1px solid var(--line)}
.notice{margin:0 0 18px;padding:12px 16px;border-left:4px solid var(--accent);background:#182421;color:#cde3de}
.tw{overflow:auto;margin:14px 0;border:1px solid var(--line);border-radius:8px;background:var(--panel)}
table{width:100%;border-collapse:collapse}th,td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:#243036}code{padding:.1em .35em;background:#252d31;border-radius:4px}
pre{padding:14px;overflow:auto;background:#151a1d;border:1px solid var(--line);border-radius:8px}
blockquote{margin:12px 0;padding:8px 14px;border-left:3px solid var(--accent);color:var(--muted)}
ol,ul{padding-left:1.4em}li{margin:4px 0}
"""
    return f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{css}</style></head>
<body><div class="layout"><nav><strong>{html.escape(title)}</strong>{nav}</nav>
<main><div class="notice">由 <code>操作流程模擬_合併.md</code> 產生。請改 Markdown 後重跑 <code>wip/tools/build_sim_html.py</code>。</div>
{''.join(body)}
</main></div></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown", type=Path, nargs="?", default=None)
    ap.add_argument("--title", default="操作流程模擬（合併）")
    args = ap.parse_args()
    if args.markdown is None:
        # default: sibling docs from tools/
        root = Path(__file__).resolve().parents[1]
        args.markdown = root / "docs" / "前期規劃" / "操作流程模擬_合併.md"
    md = args.markdown
    out = md.with_suffix(".html")
    out.write_text(convert(md.read_text(encoding="utf-8"), args.title), encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
