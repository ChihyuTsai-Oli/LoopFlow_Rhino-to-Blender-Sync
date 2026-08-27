#!/usr/bin/env python3
"""從資料生態決策表_三家建議.md 產生「三家建議併一欄」的合併稿。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from fill_decision_table import STRENGTH_RE, majority, split_row_cells, strength_of

SENT_SPLIT = re.compile(r"(?<=[。；])")


def short_text(cell: str, limit: int = 160) -> str:
    text = STRENGTH_RE.sub("", cell)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = text.lstrip("：: ").strip()
    # drop long code paths after first mention
    text = re.sub(r"`[^`]{40,}`", "`…`", text)
    parts = [p.strip() for p in SENT_SPLIT.split(text) if p.strip()]
    out = ""
    for p in parts:
        cand = (out + p).strip()
        if len(cand) > limit and out:
            break
        out = cand
        if len(out) >= limit // 2:
            break
    if not out:
        out = text[:limit]
    if len(out) > limit:
        out = out[: limit - 1] + "…"
    return out


def integrate(ai_cells: list[str], labels: list[str]) -> str:
    strength, count, option = majority(ai_cells)
    votes = []
    for lab, cell in zip(labels, ai_cells):
        s = strength_of(cell)
        if s:
            votes.append(f"{lab}{s[0]}")  # 強／一／輕
        elif "尚未提供" in cell:
            votes.append(f"{lab}缺")
        else:
            votes.append(f"{lab}？")
    vote_s = "／".join(votes)
    if strength:
        head = f"**共識 {strength}×{count}**（{vote_s}）"
    else:
        head = f"**無同強度兩票**（{vote_s}）"

    bits = [head]
    if option:
        bits.append(f"方向：採 {option}")

    # pick richest non-empty short from majority strength cells, else any
    chosen_cells = []
    for cell in ai_cells:
        if strength and strength_of(cell) == strength:
            chosen_cells.append(cell)
    if not chosen_cells:
        chosen_cells = [c for c in ai_cells if strength_of(c) or ("尚未提供" not in c and c.strip())]

    summaries = []
    for cell in chosen_cells:
        s = short_text(cell)
        if s and s not in summaries:
            summaries.append(s)
        if len(summaries) >= 2:
            break
    if summaries:
        bits.append("；".join(summaries))

    # note disagreements on option letters
    opts = []
    for cell in ai_cells:
        if strength_of(cell):
            from fill_decision_table import extract_option

            o = extract_option(cell)
            if o:
                opts.append(o)
    if opts and len(set(opts)) > 1:
        bits.append(f"選項字母有差（{'／'.join(opts)}），以「你的決定」為準")

    return "。".join(bits) if bits else "（無建議）"


def convert(md_text: str, product: str) -> str:
    lines = md_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    title_done = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("# ") and not title_done:
            name = line[2:].strip()
            out.append(f"# {name}（合併建議）\n")
            out.append("\n")
            out.append(
                f"> 由 `資料生態決策表_三家建議.md` 產生（2026-08-27）。"
                f"三欄 AI 建議已併為「整合建議」；「你的決定」照原表。"
                f"權威來源仍是原表；本檔僅供閱讀。詳見同目錄 `操作流程模擬.md`。\n"
            )
            out.append("\n")
            title_done = True
            i += 1
            continue
        if line.startswith(">") and "HTML 由" in line:
            i += 1
            continue
        if line.startswith(">") and ("寬版閱讀檔" in line or "三家併一欄" in line):
            i += 1
            continue
        # 合併稿不是裁決區：改寫「唯一來源」句
        if "尚待確認事項的**唯一來源**" in line or "尚待確認事項的唯一來源" in line:
            out.append(
                "本檔為閱讀用合併稿。裁決請改原檔 `資料生態決策表_三家建議.md`，再重跑 `merge_decision_table.py`。\n"
            )
            i += 1
            continue
        if "這是 `現況與工作鏈藍圖.md` 的使用者編輯區" in line:
            out.append(
                "對照藍圖見 `現況與工作鏈藍圖.md`。下列表格已將 Grok／Claude／Codex 併為一欄。\n"
            )
            i += 1
            continue
        # skip auto-rules / three-column how-to; keep strength legend lightly
        if line.startswith("### 三個 AI 建議欄怎麼讀") or line.startswith("### 自動裁決規則"):
            # skip until next ### or ## or ---
            i += 1
            while i < len(lines) and not (
                lines[i].startswith("## ")
                or lines[i].startswith("---")
                or (lines[i].startswith("### ") and "AI 建議強度" in lines[i])
            ):
                i += 1
            out.append("### 整合建議怎麼讀\n")
            out.append("\n")
            out.append("- 一欄濃縮 Grok／Claude／Codex；標明強度票數與方向。\n")
            out.append("- 以最右欄「你的決定」為準；衝突時以決定欄覆寫建議方向。\n")
            out.append("\n")
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = [split_row_cells(t) for t in table_lines]
            if len(rows) >= 2 and any("Claude" in h for h in rows[0]):
                header = rows[0]
                # ID | … | Grok | Claude | Codex | 決定
                # → ID | … | 整合建議 | 決定
                # assume last 4 are grok,claude,codex,decision
                new_header = header[:-4] + ["整合建議（Grok／Claude／Codex）", header[-1]]
                out.append("| " + " | ".join(new_header) + " |\n")
                # separator
                out.append("| " + " | ".join(["---"] * len(new_header)) + " |\n")
                for r in rows[1:]:
                    if not r or re.match(r"^[\s\-:]+$", r[0]):
                        continue
                    while len(r) < len(header):
                        r.append("")
                    prefix = r[: -4]
                    ai = r[-4:-1]
                    decision = r[-1]
                    integrated = integrate(ai, ["G", "C", "X"])
                    out.append("| " + " | ".join(prefix + [integrated, decision]) + " |\n")
                continue
            # non-AI table: pass through
            for t in table_lines:
                out.append(t if t.endswith("\n") else t + "\n")
            continue
        out.append(line if line.endswith("\n") else line + "\n")
        i += 1
    # light cleanup: collapse excessive blank lines
    text = "".join(out)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--product", default="")
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()
    src = args.markdown
    dst = args.output or src.with_name("資料生態決策表_合併.md")
    text = convert(src.read_text(encoding="utf-8"), args.product)
    dst.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
