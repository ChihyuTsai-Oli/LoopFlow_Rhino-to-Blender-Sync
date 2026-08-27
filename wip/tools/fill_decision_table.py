#!/usr/bin/env python3
"""依三欄 AI 建議多數決填寫「你的決定」，並產生彩色 HTML。

規則（使用者 2026-08-27）：
1. 兩個以上強烈建議 → 採用；HTML 決定欄文字白色
2. 兩個以上一般建議 → 採用；HTML 決定欄文字黃色
3. 兩個以上輕鬆建議 → 採用；HTML 決定欄文字綠色
若無任何強度達兩個以上 → 維持待決定。
優先序：強烈 > 一般 > 輕鬆（若同時滿足，取最高）。
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

# 支援 `**強烈建議**：…` 與 `**強烈建議：採 B。**`（冒號在粗體內）
STRENGTH_RE = re.compile(r"\*\*(強烈建議|一般建議|輕鬆建議)(?:\*\*[：:]|[：:][^*]*\*\*)")
OPTION_RE = re.compile(
    r"(?:採|同意|先採|維持|選)\s*([ABC])|"
    r"(?:強烈建議|一般建議|輕鬆建議)[：:*\s]*採?\s*([ABC])"
)
SKIP_IF_ONLY = ("尚未提供",)

PRIORITY = {"強烈建議": 3, "一般建議": 2, "輕鬆建議": 1}
COLOR = {
    "強烈建議": ("#ffffff", "auto-strong"),
    "一般建議": ("#f5e04a", "auto-general"),
    "輕鬆建議": ("#6fdc8c", "auto-light"),
}


def split_row_cells(line: str) -> list[str]:
    raw = line.strip()
    if not raw.startswith("|"):
        return []
    parts = raw.split("|")
    # leading/trailing empties from split
    return [p.strip() for p in parts[1:-1]]


def strength_of(cell: str) -> str | None:
    # 「尚未提供」且無建議強度標記 → 不計票
    if any(m in cell for m in SKIP_IF_ONLY) and not STRENGTH_RE.search(cell):
        return None
    m = STRENGTH_RE.search(cell)
    if m:
        return m.group(1)
    # 後備：粗體標記異常時仍辨識關鍵字
    for s in ("強烈建議", "一般建議", "輕鬆建議"):
        if s in cell:
            return s
    return None


def extract_option(cell: str) -> str | None:
    m = OPTION_RE.search(cell)
    if not m:
        return None
    for g in m.groups():
        if g:
            return g
    return None


def majority(ai_cells: list[str]) -> tuple[str | None, int, str | None]:
    """Return (strength, count, consensus_option_or_None)."""
    counts = {"強烈建議": 0, "一般建議": 0, "輕鬆建議": 0}
    options: dict[str, list[str]] = {"強烈建議": [], "一般建議": [], "輕鬆建議": []}
    for cell in ai_cells:
        s = strength_of(cell)
        if not s:
            continue
        counts[s] += 1
        opt = extract_option(cell)
        if opt:
            options[s].append(opt)
    chosen = None
    for s in ("強烈建議", "一般建議", "輕鬆建議"):
        if counts[s] >= 2:
            chosen = s
            break
    if not chosen:
        return None, 0, None
    opts = options[chosen]
    consensus = None
    if opts:
        # most common option among that strength
        consensus = max(set(opts), key=opts.count)
        if opts.count(consensus) < 1:
            consensus = None
    return chosen, counts[chosen], consensus


def synthesize_decision(strength: str, count: int, option: str | None, ai_cells: list[str]) -> str:
    bits = []
    if option:
        bits.append(f"採 {option}")
    # pull a short lead from first matching cell
    for cell in ai_cells:
        if strength_of(cell) != strength:
            continue
        # strip strength marker prefix for short note
        text = STRENGTH_RE.sub("", cell).lstrip("：: ").strip()
        # take first sentence-ish
        for sep in ("。", "；", "."):
            if sep in text:
                text = text.split(sep)[0].strip()
                break
        if len(text) > 80:
            text = text[:77] + "…"
        if text and text not in bits:
            bits.append(text)
        break
    body = "；".join(bits) if bits else "依多數 AI 建議採用"
    return f"**自動採用（{strength}×{count}，2026-08-27）**：{body}"


def process_markdown(text: str) -> tuple[str, list[dict]]:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    log: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        cells = split_row_cells(line.rstrip("\n"))
        # detect header with three AI columns + decision
        if (
            len(cells) >= 6
            and "你的決定" in cells[-1]
            and any("Grok" in c or "Claude" in c or "Codex" in c for c in cells)
        ):
            out.append(line)
            i += 1
            # skip separator
            if i < len(lines) and re.match(r"^\|[\s\-|]+\|\s*$", lines[i]):
                out.append(lines[i])
                i += 1
            while i < len(lines):
                row = lines[i]
                row_cells = split_row_cells(row.rstrip("\n"))
                if not row_cells or not row.strip().startswith("|"):
                    break
                if row_cells[0].startswith("---") or set(row_cells[0]) <= {"-", " "}:
                    out.append(row)
                    i += 1
                    continue
                # AI columns: last 4 are grok, claude, codex, decision (for 7-col)
                # or for tables: ID, principle, options, grok, claude, codex, decision
                if len(row_cells) < 5:
                    out.append(row)
                    i += 1
                    continue
                decision_idx = len(row_cells) - 1
                ai_cells = row_cells[decision_idx - 3 : decision_idx]
                row_id = row_cells[0]
                old_decision = row_cells[decision_idx]
                strength, count, option = majority(ai_cells)
                if old_decision.strip() in ("待決定", "") or old_decision.strip().startswith("待決定"):
                    if strength:
                        new_decision = synthesize_decision(strength, count, option, ai_cells)
                        row_cells[decision_idx] = new_decision
                        log.append(
                            {
                                "id": row_id,
                                "strength": strength,
                                "count": count,
                                "option": option,
                                "action": "filled",
                            }
                        )
                    else:
                        log.append({"id": row_id, "strength": None, "count": 0, "action": "pending"})
                else:
                    # keep user/prior text; still record strength for HTML color if majority exists
                    log.append(
                        {
                            "id": row_id,
                            "strength": strength,
                            "count": count,
                            "action": "kept",
                            "decision": old_decision[:40],
                        }
                    )
                new_line = "| " + " | ".join(row_cells) + " |\n"
                # preserve original newline style if \r\n
                if row.endswith("\r\n"):
                    new_line = new_line.replace("\n", "\r\n")
                out.append(new_line)
                i += 1
            continue
        out.append(line)
        i += 1
    return "".join(out), log


def md_inline_to_html(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def build_html(md_path: Path, title: str, color_by_id: dict[str, str]) -> str:
    md = md_path.read_text(encoding="utf-8")
    # crude but sufficient: convert tables
    sections: list[str] = []
    toc: list[tuple[str, str]] = []
    current_h2 = None
    body_parts: list[str] = []

    def flush_para(buf: list[str]) -> None:
        if not buf:
            return
        para = "\n".join(buf).strip()
        if para:
            body_parts.append(f"<p>{md_inline_to_html(para)}</p>")
        buf.clear()

    lines = md.splitlines()
    i = 0
    para_buf: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            flush_para(para_buf)
            body_parts.append(f"<h1>{md_inline_to_html(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            flush_para(para_buf)
            title_text = line[3:].strip()
            anchor = re.sub(r"[^\w\-]+", "-", title_text, flags=re.U).strip("-").lower()
            toc.append((title_text, anchor))
            body_parts.append(f'<h2 id="{anchor}">{md_inline_to_html(title_text)}</h2>')
        elif line.startswith("### "):
            flush_para(para_buf)
            body_parts.append(f"<h3>{md_inline_to_html(line[4:].strip())}</h3>")
        elif line.startswith(">"):
            flush_para(para_buf)
            body_parts.append(f"<blockquote><p>{md_inline_to_html(line.lstrip('> ').strip())}</p></blockquote>")
        elif line.startswith("|"):
            flush_para(para_buf)
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            i -= 1
            rows = [split_row_cells(t) for t in table_lines]
            if len(rows) >= 2:
                header = rows[0]
                # skip separator row[1]
                data = [r for r in rows[1:] if r and not re.match(r"^[\s\-:]+$", r[0])]
                ncols = len(header)
                kind = "tri-ai" if any("Claude" in h for h in header) else "plain"
                body_parts.append(f'<div class="tw"><table class="{kind} cols-{ncols}"><thead><tr>')
                for h in header:
                    body_parts.append(f"<th>{md_inline_to_html(h)}</th>")
                body_parts.append("</tr></thead><tbody>")
                for r in data:
                    while len(r) < ncols:
                        r.append("")
                    rid = r[0]
                    strength = color_by_id.get(rid)
                    cls = COLOR[strength][1] if strength else ""
                    if "待決定" in r[-1]:
                        cls = (cls + " pending").strip()
                    body_parts.append(f'<tr class="{cls}">' if cls else "<tr>")
                    for j, cell in enumerate(r[:ncols]):
                        style = ""
                        if j == ncols - 1 and strength and "待決定" not in cell:
                            style = f' style="color:{COLOR[strength][0]};font-weight:650"'
                        body_parts.append(f"<td{style}>{md_inline_to_html(cell)}</td>")
                    body_parts.append("</tr>")
                body_parts.append("</tbody></table></div>")
        elif line.strip() == "":
            flush_para(para_buf)
        elif line.startswith("- "):
            flush_para(para_buf)
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{md_inline_to_html(lines[i][2:].strip())}</li>")
                i += 1
            i -= 1
            body_parts.append("<ul>" + "".join(items) + "</ul>")
        else:
            para_buf.append(line)
        i += 1
    flush_para(para_buf)

    nav = "\n".join(f'<a href="#{a}">{html.escape(t)}</a>' for t, a in toc)
    css = r"""
:root{color-scheme:dark;--bg:#101417;--panel:#171d21;--line:#39444a;--text:#edf2f3;--muted:#a9b4b8;--accent:#74c9b4}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.65 system-ui,"Noto Sans TC",sans-serif}
.layout{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:100vh}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 20px;border-right:1px solid var(--line);background:#0c1012}
nav strong{display:block;margin-bottom:14px;color:var(--accent);font-size:18px}
nav a{display:block;padding:6px 8px;color:var(--muted);text-decoration:none;border-radius:5px}
nav a:hover{color:var(--text);background:#20292d}
main{min-width:0;padding:34px 36px 70px}h1{margin-top:0;font-size:28px}h2{margin-top:42px;padding-top:8px;border-top:1px solid var(--line)}
.notice{margin:0 0 22px;padding:12px 16px;border-left:4px solid var(--accent);background:#182421;color:#cde3de}
.tw{max-height:78vh;margin:18px 0 28px;overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}
table{width:100%;border-collapse:separate;border-spacing:0;min-width:2200px}
th,td{padding:10px 12px;vertical-align:top;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
th{position:sticky;top:0;z-index:3;background:#243036;color:#f5faf9;text-align:left}
th:first-child,td:first-child{position:sticky;left:0;z-index:2;background:#1b2428;font-weight:650}
th:first-child{z-index:4;background:#243036}
tr.pending td:last-child{opacity:.75}
code{padding:.12em .35em;background:#252d31;border-radius:4px}
.legend span{display:inline-block;margin-right:14px;font-weight:650}
"""
    legend = (
        '<p class="legend">決定欄顏色：'
        '<span style="color:#ffffff">白色＝強烈建議×2+</span>'
        '<span style="color:#f5e04a">黃色＝一般建議×2+</span>'
        '<span style="color:#6fdc8c">綠色＝輕鬆建議×2+</span></p>'
    )
    return f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{css}</style></head>
<body><div class="layout"><nav><strong>{html.escape(title)}</strong>{nav}</nav>
<main><div class="notice">由 Markdown 產生。請改 <code>資料生態決策表_三家建議.md</code> 後重跑 <code>wip/tools/fill_decision_table.py</code>。</div>
{legend}
{''.join(body_parts)}
</main></div></body></html>
"""


def extract_decisions(text: str) -> dict[str, str]:
    """row_id -> decision cell text."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        cells = split_row_cells(line)
        if len(cells) >= 5 and re.match(r"^(XF|R2B|R2O)-", cells[0]):
            out[cells[0]] = cells[-1]
    return out


def apply_xf_decisions(text: str, xf: dict[str, str]) -> tuple[str, int]:
    """Overwrite XF-* decision cells from another table (跨產品同文)."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    n = 0
    for line in lines:
        cells = split_row_cells(line.rstrip("\n"))
        if cells and cells[0].startswith("XF-") and cells[0] in xf:
            if cells[-1] != xf[cells[0]]:
                cells[-1] = xf[cells[0]]
                n += 1
                nl = "\r\n" if line.endswith("\r\n") else "\n"
                out.append("| " + " | ".join(cells) + " |" + nl)
                continue
        out.append(line)
    return "".join(out), n


def collect_color_map(text: str) -> dict[str, str]:
    """Compute majority strength per row for HTML coloring."""
    colors: dict[str, str] = {}
    for line in text.splitlines():
        cells = split_row_cells(line)
        if len(cells) < 5 or not re.match(r"^(XF|R2B|R2O)-", cells[0]):
            continue
        ai = cells[-4:-1]
        strength, _, _ = majority(ai)
        if strength:
            colors[cells[0]] = strength
    return colors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--title", default="資料生態決策表")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--html-only", action="store_true", help="只重產 HTML，不改 Markdown")
    parser.add_argument(
        "--sync-xf-from",
        type=Path,
        default=None,
        help="以另一份決策表的 XF-* 決定欄覆寫本檔（跨產品同文）",
    )
    args = parser.parse_args()
    src = args.markdown
    text = src.read_text(encoding="utf-8")
    log: list[dict] = []
    if args.html_only:
        new_text = text
    else:
        new_text, log = process_markdown(text)
        if args.sync_xf_from:
            xf = {
                k: v
                for k, v in extract_decisions(args.sync_xf_from.read_text(encoding="utf-8")).items()
                if k.startswith("XF-")
            }
            new_text, synced = apply_xf_decisions(new_text, xf)
            print(f"synced XF rows from {args.sync_xf_from.name}: {synced}")

    color_by_id = collect_color_map(new_text)
    html_path = src.with_suffix(".html")
    if not args.dry_run:
        if not args.html_only:
            src.write_text(new_text, encoding="utf-8", newline="\n")
        # build_html 從磁碟讀 md；html-only 時用原檔，否則已寫入 new_text
        html_path.write_text(build_html(src, args.title, color_by_id), encoding="utf-8", newline="\n")

    filled = sum(1 for e in log if e.get("action") == "filled")
    pending = sum(1 for e in log if e.get("action") == "pending")
    kept = sum(1 for e in log if e.get("action") == "kept")
    print(f"{src.name}: filled={filled} kept={kept} pending={pending}")
    for e in log:
        if e["action"] == "pending":
            print(f"  PENDING {e['id']}")
        elif e["action"] == "filled":
            print(f"  FILL {e['id']} {e['strength']}×{e['count']} opt={e.get('option')}")
    if not args.dry_run:
        print(f"wrote html: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
