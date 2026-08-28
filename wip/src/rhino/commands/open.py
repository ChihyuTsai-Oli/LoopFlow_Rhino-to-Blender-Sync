# -*- coding: utf-8 -*-
"""Rhino Open／Health：設定根、三通道 last-good 時間、Blender 作業資料夾。"""
from __future__ import annotations

import os
from pathlib import Path

from foundation.docs import open_docs_in_browser
from foundation.health import build_health_report
from foundation.paths import (
    config_root_for_document,
    ensure_config_layout,
    live_dir,
    models_dir,
    require_saved_document_path,
)
from foundation.result import Result
from rhino.platform.live import open_session


def collect_open_health() -> Result:
    session = open_session()
    saved = require_saved_document_path(session.document_path())
    if not saved.ok:
        return saved
    root = ensure_config_layout(config_root_for_document(saved.data))
    work = Path(saved.data).resolve().parent
    report = build_health_report(
        document=str(saved.data),
        config_root=root,
        work_folder=work,
    )
    return Result.success(
        report,
        stage="open_health",
        data={
            "root": str(root),
            "live": str(live_dir(root)),
            "models": str(models_dir(root)),
            "work": str(work),
            "report": report,
        },
    )


def _open_folder(path: str) -> None:
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    os.startfile(str(folder))  # noqa: S606  Windows Explorer


def show_open_dialog(health: Result) -> None:
    """英文對話框：摘要＋開設定根／live／models／Docs。失敗則 MessageBox。"""
    if not health.ok:
        import rhinoscriptsyntax as rs  # type: ignore

        rs.MessageBox(health.message, title="R2B_Open")
        return
    data = health.data or {}
    try:
        _show_eto(health.message, data)
    except Exception:
        import rhinoscriptsyntax as rs  # type: ignore

        rs.MessageBox(health.message, title="R2B_Open")


def _show_eto(report: str, data: dict) -> None:
    import Eto.Drawing as drawing  # type: ignore
    import Eto.Forms as forms  # type: ignore
    import Rhino.UI  # type: ignore

    class OpenHealthDialog(forms.Dialog):
        def __init__(self):
            forms.Dialog.__init__(self)
            self.Title = "R2B Open / Health"
            self.Padding = drawing.Padding(10)
            self.Resizable = True
            self.ClientSize = drawing.Size(520, 300)
            self.MinimumSize = drawing.Size(400, 240)

            box = forms.TextArea()
            box.Text = report
            box.ReadOnly = True

            open_root = forms.Button()
            open_root.Text = "Open Config"
            open_live = forms.Button()
            open_live.Text = "Open live"
            open_models = forms.Button()
            open_models.Text = "Open models"
            open_docs = forms.Button()
            open_docs.Text = "Open Docs"

            open_root.Click += lambda s, e: _open_folder(str(data.get("root") or ""))
            open_live.Click += lambda s, e: _open_folder(str(data.get("live") or ""))
            open_models.Click += lambda s, e: _open_folder(str(data.get("models") or ""))
            open_docs.Click += lambda s, e: open_docs_in_browser()

            # TableLayout 四欄等寬（Rhino 8 Eto 可用；勿用 StackLayout）
            buttons = forms.TableLayout()
            buttons.Spacing = drawing.Size(8, 0)
            table_row = forms.TableRow()
            table_row.ScaleHeight = False
            for btn in (open_root, open_live, open_models, open_docs):
                table_row.Cells.Add(forms.TableCell(btn, True))
            buttons.Rows.Add(table_row)

            layout = forms.DynamicLayout()
            layout.DefaultSpacing = drawing.Size(4, 8)
            layout.Add(box, yscale=True, xscale=True)
            layout.AddRow(buttons)
            self.Content = layout

    dialog = OpenHealthDialog()
    parent = None
    try:
        parent = Rhino.UI.RhinoEtoApp.MainWindow
    except Exception:
        parent = None
    dialog.ShowModal(parent)


def run_open() -> Result:
    health = collect_open_health()
    show_open_dialog(health)
    return health
