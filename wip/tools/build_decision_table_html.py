# -*- coding: utf-8 -*-
"""把 `前期規劃/資料生態決策表.md` 轉成寬版好讀的 HTML。

用途
    決策表有 6 欄且 AI 建議欄很長，在一般 Markdown 預覽裡會被擠成細長條。
    本檔產生的 HTML 給每一欄固定寬度、表頭與 ID 欄固定不捲動，方便逐列閱讀與填寫。
    `資料生態決策表.html` 是衍生檔，不應手動編輯；改 `.md` 後重新執行本腳本。

執行
    python wip/tools/build_decision_table_html.py
    python wip/tools/build_decision_table_html.py --check    # 只檢查是否過期，不寫檔

環境
    僅需 Python 3.8+ 標準函式庫。路徑相對本檔位置解析，不寫死任何電腦的絕對路徑。

來源
    改寫自 LoopFlow 2.0 的 `v2/tools/build_decision_table_html.py` 與 `build_workflow_html.py`，
    併成單一自含檔案，只保留決策表用得到的部分。

限制
    只支援本文件實際使用的 Markdown 子集：標題、段落、清單、表格、圍欄程式碼區塊、
    引言區塊、水平線、粗體與行內程式碼。表格儲存格內不可出現未跳脫的 `|`。
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

# Windows 主控台預設可能是 cp950，統一改用 UTF-8 輸出中文訊息
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# <repo>/wip/tools/ → <repo>/wip/docs/前期規劃/
_PLAN_DIR = Path(__file__).resolve().parents[1] / "docs" / "前期規劃"
DEFAULT_SRC = _PLAN_DIR / "資料生態決策表.md"
DEFAULT_OUT = DEFAULT_SRC.with_suffix(".html")


# ==================================================================
# Markdown → HTML（只支援本文件用到的子集）
# ==================================================================
def inline(text: str) -> str:
    """處理粗體與行內程式碼；行內程式碼先抽成佔位符，讓粗體能跨越它配對。"""
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return re.sub(
        r"\x00(\d+)\x00",
        lambda m: "<code>%s</code>" % html.escape(spans[int(m.group(1))]),
        text,
    )


def slug(text: str) -> str:
    """由標題文字產生錨點 id；保留中日韓字元，其餘非文字字元轉為連字號。"""
    return re.sub(r"[^\w一-鿿]+", "-", text).strip("-") or "sec"


def convert(md: str) -> tuple[str, list[tuple[int, str, str]]]:
    """回傳 (HTML 內容, 目錄項目清單)；目錄項目為 (層級, 標題, 錨點 id)。"""
    lines = md.split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    i, n = 0, len(lines)

    while i < n:
        stripped = lines[i].strip()

        # 圍欄程式碼區塊
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "text"
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(
                '<pre class="code" data-lang="%s"><code>%s</code></pre>'
                % (html.escape(lang), html.escape("\n".join(buf)))
            )
            continue

        # 水平線
        if re.fullmatch(r"-{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 表格：第二列必須是分隔列
        if (
            stripped.startswith("|")
            and i + 1 < n
            and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip())
        ):
            def cells(row: str) -> list[str]:
                return [c.strip() for c in row.strip().strip("|").split("|")]

            head = cells(stripped)
            i += 2
            body = []
            while i < n and lines[i].strip().startswith("|"):
                body.append(cells(lines[i]))
                i += 1

            kind = "dual-ai" if any("Claude 建議" in c for c in head) else "strength"
            parts = [
                '<div class="tw"><table class="%s cols-%d">' % (kind, len(head)),
                "<thead><tr>",
            ]
            parts += ["<th>%s</th>" % inline(c) for c in head]
            parts.append("</tr></thead><tbody>")
            for row in body:
                row = (row + [""] * len(head))[: len(head)]
                parts.append(
                    "<tr>" + "".join("<td>%s</td>" % inline(c) for c in row) + "</tr>"
                )
            parts.append("</tbody></table></div>")
            out.append("".join(parts))
            continue

        # 標題
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            sid = slug(title)
            cls = ' class="doctitle"' if level == 1 else ""
            out.append("<h%d%s id=\"%s\">%s</h%d>" % (level, cls, sid, inline(title), level))
            if level in (2, 3):
                toc.append((level, title, sid))
            i += 1
            continue

        # 有序清單
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(
                    "<li>%s</li>" % inline(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                )
                i += 1
            out.append("<ol>%s</ol>" % "".join(items))
            continue

        # 無序清單（含 `- [ ]` 檢查項）
        if re.match(r"^-\s+", stripped):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                text = re.sub(r"^-\s+", "", lines[i].strip())
                box = ""
                if text.startswith("[ ] "):
                    box, text = '<span class="box">☐</span>', text[4:]
                elif text.lower().startswith("[x] "):
                    box, text = '<span class="box done">☑</span>', text[4:]
                items.append("<li>%s%s</li>" % (box, inline(text)))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items))
            continue

        # 引言區塊
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            paras, cur = [], []
            for ln in buf:
                if ln.strip():
                    cur.append(ln.strip())
                elif cur:
                    paras.append(" ".join(cur))
                    cur = []
            if cur:
                paras.append(" ".join(cur))
            out.append(
                "<blockquote>%s</blockquote>"
                % "".join("<p>%s</p>" % inline(t) for t in paras)
            )
            continue

        # 空行
        if not stripped:
            i += 1
            continue

        # 段落
        buf = []
        while (
            i < n
            and lines[i].strip()
            and not re.match(r"^(#{1,4}\s|```|-{3,}$|\||-\s|\d+\.\s|>)", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    return "\n".join(out), toc


# ==================================================================
# 樣式與腳本（內嵌，確保離線可開）
# ==================================================================
CSS = r"""
:root{color-scheme:dark;--bg:#101417;--panel:#171d21;--line:#39444a;--text:#edf2f3;--muted:#a9b4b8;
  --accent:#74c9b4;--amber:#e4b86a;--red:#ef8c84;--grok:#c8a4e8;--claude:#7fc7d9;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft JhengHei","PingFang TC","Noto Sans TC",sans-serif;
  --mono:"Cascadia Mono",Consolas,"SF Mono",monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.7 var(--sans)}
.layout{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:100vh}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 20px;border-right:1px solid var(--line);background:#0c1012}
nav strong{display:block;margin-bottom:14px;color:var(--accent);font-size:17px}
nav a{display:block;padding:6px 8px;color:var(--muted);text-decoration:none;border-radius:5px;font-size:13.4px}
nav a.l3{padding-left:20px;font-size:12.6px}
nav a:hover,nav a.active{color:var(--text);background:#20292d}
main{min-width:0;padding:34px 36px 90px}
h1{margin:0 0 6px;font-size:29px}
h2{margin-top:46px;padding-top:10px;border-top:1px solid var(--line);font-size:21px}
h3{margin-top:28px;color:#dce9e7;font-size:17px}
a{color:#8fd9c7}
code{padding:.12em .35em;background:#252d31;border-radius:4px;font-family:var(--mono);font-size:.87em;color:#e8c07d;word-break:break-word}
strong{color:#fff}
ul,ol{padding-left:24px}li{margin:4px 0}
.box{display:inline-block;width:1.3em;color:var(--muted)}.box.done{color:var(--accent)}
blockquote{margin:18px 0;padding:10px 16px;border-left:4px solid var(--amber);background:#211f18;color:#ded5bd}
blockquote p{margin:0}
pre.code{background:#12161f;border:1px solid var(--line);border-radius:7px;padding:14px 16px;overflow-x:auto}
pre.code code{background:none;padding:0;color:#b9c4d8;font-size:13px;white-space:pre}
.notice{margin:22px 0 26px;padding:12px 16px;border-left:4px solid var(--accent);background:#182421;color:#cde3de}

/* ---- 表格：寬版、表頭與 ID 欄固定 ---- */
.tw{max-height:80vh;margin:18px 0 32px;overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel);box-shadow:0 10px 28px #0005}
table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}
table.strength{min-width:640px}
table.dual-ai{min-width:2200px}
th,td{padding:11px 13px;vertical-align:top;border-right:1px solid var(--line);border-bottom:1px solid var(--line);font-size:13.6px;line-height:1.72;word-break:break-word}
th{position:sticky;top:0;z-index:3;background:#243036;color:#f5faf9;text-align:left;font-size:13px}
th:first-child,td:first-child{position:sticky;left:0;z-index:2;background:#1b2428;font-weight:650;color:var(--text)}
th:first-child{z-index:4;background:#243036}
.tw tr:last-child td{border-bottom:0}
.tw th:last-child,.tw td:last-child{border-right:0}
tbody tr:hover td{background:#202c30}tbody tr:hover td:first-child{background:#263338}

/* 6 欄：ID／原則／現況選項／Grok／Claude／你的決定。Claude 欄最寬，因為它帶程式碼證據。 */
.dual-ai.cols-6 col:nth-child(1){width:4.5%}
.dual-ai.cols-6 col:nth-child(2){width:12%}
.dual-ai.cols-6 col:nth-child(3){width:14%}
.dual-ai.cols-6 col:nth-child(4){width:16%}
.dual-ai.cols-6 col:nth-child(5){width:35%}
.dual-ai.cols-6 col:nth-child(6){width:18.5%}
.dual-ai th:nth-child(4){color:var(--grok)}
.dual-ai th:nth-child(5){color:var(--claude)}
.dual-ai td:nth-child(5){border-left:2px solid #2b4a52}

/* 依「你的決定」欄的內容標色，方便掃出還沒填的列 */
tr.adopted td:last-child{background:#173329}
tr.partial td:last-child{background:#3a2e18}
tr.pending td:last-child{background:#3a2224;color:#e9c9c9}
tr.delayed td:last-child{background:#29233a}

@media(max-width:900px){.layout{display:block}nav{position:static;width:auto;height:auto;border-right:0;border-bottom:1px solid var(--line)}main{padding:24px 16px}}
@media print{body{background:#fff;color:#111}.layout{display:block}nav,.notice{display:none}main{padding:0}
  .tw{max-height:none;overflow:visible;box-shadow:none}table.dual-ai,table.strength{min-width:0;font-size:8pt}
  th{position:static;background:#ddd;color:#111}th:first-child,td:first-child{position:static;background:#eee}}
"""

SCRIPT = r"""
document.querySelectorAll('.tw tbody tr').forEach(function(row){
  var cells=row.querySelectorAll('td'); if(!cells.length)return;
  var decision=cells[cells.length-1].textContent;
  if(decision.indexOf('部分採用')>=0)row.classList.add('partial');
  else if(decision.indexOf('採用')>=0)row.classList.add('adopted');
  else if(decision.indexOf('待決定')>=0)row.classList.add('pending');
  else if(decision.indexOf('延後')>=0)row.classList.add('delayed');
});
var links=[].slice.call(document.querySelectorAll('nav a'));
var targets=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
function upd(){var y=window.scrollY+150,best=-1;
  for(var i=0;i<targets.length;i++){if(targets[i]&&targets[i].offsetTop<=y)best=i;}
  links.forEach(function(a,i){a.classList.toggle('active',i===best);});}
window.addEventListener('scroll',upd,{passive:true});upd();
"""

PAGE = """<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title><style>%(css)s</style></head>
<body><div class="layout"><nav><strong>資料生態決策表</strong>%(nav)s</nav>
<main>%(body)s</main></div><script>%(script)s</script></body>
</html>
"""


def add_colgroups(body: str) -> str:
    """為每個表格補上 <colgroup>，讓 table-layout:fixed 的欄寬規則生效。"""

    def replace(m: re.Match) -> str:
        opening, cols = m.group(1), int(m.group(2))
        group = "<colgroup>%s</colgroup>" % ("<col>" * cols)
        return opening + group

    return re.sub(r'(<table class="[\w-]+ cols-(\d+)">)', replace, body)


def render(markdown: str) -> str:
    body, toc = convert(markdown)
    body = add_colgroups(body)

    m = re.search(r'<h1 class="doctitle"[^>]*>(.*?)</h1>', body, re.S)
    title = re.sub(r"<[^>]+>", "", m.group(1)) if m else "資料生態決策表"

    nav = "\n".join(
        '<a class="l%d" href="#%s">%s</a>' % (level, anchor, html.escape(heading))
        for level, heading, anchor in toc
    )
    notice = (
        '<div class="notice">這是由 Markdown 產生的寬版閱讀檔，方便橫向比較兩個 AI 的建議。'
        "內容請改 <code>資料生態決策表.md</code>，再執行 "
        "<code>wip/tools/build_decision_table_html.py</code> 更新本頁。"
        "「你的決定」欄仍未填的列會標成紅底。</div>"
    )
    # notice 放在文件標題之後、正文之前
    body = body.replace("</h1>", "</h1>" + notice, 1)

    return PAGE % {
        "title": html.escape(title),
        "css": CSS,
        "nav": nav,
        "body": body,
        "script": SCRIPT,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="產生資料生態決策表的寬版 HTML")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help="來源 Markdown")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="輸出 HTML")
    ap.add_argument("--check", action="store_true", help="只檢查是否過期，不寫檔")
    args = ap.parse_args(argv)

    if not args.src.exists():
        print("找不到來源檔：%s" % args.src, file=sys.stderr)
        return 2

    page = render(args.src.read_text(encoding="utf-8"))

    if args.check:
        if args.out.exists() and args.out.read_text(encoding="utf-8") == page:
            print("HTML 為最新：%s" % args.out.name)
            return 0
        print("HTML 已過期，請重新執行本腳本產生：%s" % args.out.name, file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8", newline="\n")
    print("已產生 %s（%d bytes）" % (args.out.name, len(page.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
