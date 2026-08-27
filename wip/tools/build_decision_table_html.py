#!/usr/bin/env python3
"""相容入口：只重產 HTML（不改 Markdown）。"""
from pathlib import Path
import sys

from fill_decision_table import main

if __name__ == "__main__":
    # 預設對同目錄文件結構：傳入 md 路徑或使用 argv
    if len(sys.argv) == 1:
        root = Path(__file__).resolve().parents[1]
        md = root / "docs" / "前期規劃" / "資料生態決策表_三家建議.md"
        sys.argv = [sys.argv[0], str(md), "--html-only", "--title", "資料生態決策表"]
    elif "--html-only" not in sys.argv:
        sys.argv.append("--html-only")
    raise SystemExit(main())
