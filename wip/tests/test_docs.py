# -*- coding: utf-8 -*-
"""文件入口 URL 與開啟邏輯。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from foundation.docs import DOCS_ENTRY_URL, open_docs_in_browser


class DocsEntryTests(unittest.TestCase):
    def test_url_points_at_github_readme(self):
        self.assertIn("github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync", DOCS_ENTRY_URL)
        self.assertIn("/blob/main/", DOCS_ENTRY_URL)
        self.assertTrue(DOCS_ENTRY_URL.endswith("/docs/README.md"))

    def test_entry_page_links_both_languages(self):
        text = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
        self.assertIn("./USER_GUIDE.md", text)
        self.assertIn("./USER_GUIDE_zh-TW.md", text)
        self.assertIn("./TOOLBOX.md", text)
        self.assertIn("./TOOLBOX_zh-TW.md", text)
        self.assertIn("documentation entry", text)
        self.assertIn("文件入口", text)

    def test_open_docs_uses_opener(self):
        seen = []

        def fake(url):
            seen.append(url)

        err = open_docs_in_browser(opener=fake)
        self.assertEqual(err, "")
        self.assertEqual(seen, [DOCS_ENTRY_URL])

    def test_open_docs_reports_oserror(self):
        def boom(_url):
            raise OSError("blocked")

        err = open_docs_in_browser(opener=boom)
        self.assertIn("Could not open documentation", err)
        self.assertIn("blocked", err)

    def test_public_toolbox_page_version_and_fixed_tag(self):
        zh = (REPO / "docs" / "TOOLBOX_zh-TW.md").read_text(encoding="utf-8")
        en = (REPO / "docs" / "TOOLBOX.md").read_text(encoding="utf-8")
        for text in (zh, en):
            self.assertIn("1.0.0", text)
            self.assertIn("releases/tag/toolbox-1.0.0", text)
            self.assertIn("Install from Disk", text)
        self.assertIn("不要", zh)
        self.assertIn("Do **not** use", en)
        self.assertNotIn("尚未發布", zh)
        self.assertNotIn("not published yet", en)


if __name__ == "__main__":
    unittest.main()
