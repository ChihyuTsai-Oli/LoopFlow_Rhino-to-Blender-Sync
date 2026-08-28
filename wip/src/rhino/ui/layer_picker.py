# -*- coding: utf-8 -*-
"""Rhino 端簡易 Eto 對話框：階層圖層選取（可捲動）。"""
from __future__ import annotations

from typing import Optional, Sequence


def pick_layer_path(
    layer_paths: Sequence[str],
    *,
    default_path: Optional[str] = None,
    title: str = "R2B Models",
    message: str = "選擇要匯出的模型圖層，含子層",
) -> Optional[str]:
    """
    以 TreeGridView 顯示圖層階層，內建捲軸；確定／雙擊回傳 FullPath。

    失敗或取消回傳 None。
    """
    import Eto.Drawing as drawing  # type: ignore
    import Eto.Forms as forms  # type: ignore
    import Rhino.UI  # type: ignore

    paths = [str(p) for p in layer_paths if p]
    if not paths:
        return None

    class LayerTreeDialog(forms.Dialog[bool]):
        def __init__(self):
            self.Title = title
            self.Padding = drawing.Padding(10)
            self.Resizable = True
            self.ClientSize = drawing.Size(440, 520)
            self.selected_path = None  # type: Optional[str]

            self._label = forms.Label(Text=message)

            self._tree = forms.TreeGridView()
            self._tree.ShowHeader = False
            self._tree.AllowMultipleSelection = False
            col = forms.GridColumn()
            col.HeaderText = "圖層"
            col.DataCell = forms.TextBoxCell(0)
            col.Editable = False
            col.Expand = True
            self._tree.Columns.Add(col)
            self._tree.CellDoubleClick += self._on_double_click

            self._nodes = {}
            root_items = forms.TreeGridItemCollection()
            for path in paths:
                parts = path.split("::")
                for depth in range(len(parts)):
                    full = "::".join(parts[: depth + 1])
                    if full in self._nodes:
                        continue
                    item = forms.TreeGridItem()
                    item.Values = [parts[depth]]
                    item.Expanded = True
                    # Tag 存 FullPath
                    try:
                        item.Tag = full
                    except Exception:
                        pass
                    self._nodes[full] = item
                    if depth == 0:
                        root_items.Add(item)
                    else:
                        parent_full = "::".join(parts[:depth])
                        self._nodes[parent_full].Children.Add(item)

            self._tree.DataStore = root_items
            if default_path and default_path in self._nodes:
                try:
                    self._tree.SelectedItem = self._nodes[default_path]
                except Exception:
                    pass

            ok = forms.Button(Text="確定")
            cancel = forms.Button(Text="取消")
            ok.Click += self._on_ok
            cancel.Click += self._on_cancel
            self.DefaultButton = ok
            self.AbortButton = cancel

            buttons = forms.TableLayout()
            buttons.Spacing = drawing.Size(8, 0)
            buttons.Rows.Add(
                forms.TableRow(
                    None,
                    forms.TableCell(ok),
                    forms.TableCell(cancel),
                )
            )

            layout = forms.DynamicLayout()
            layout.DefaultSpacing = drawing.Size(6, 8)
            layout.AddRow(self._label)
            # TreeGridView 自帶捲軸；yscale 讓它吃滿對話框高度
            layout.Add(self._tree, yscale=True, xscale=True)
            layout.AddRow(buttons)
            self.Content = layout

        def _current_path(self):
            item = self._tree.SelectedItem
            if item is None:
                return None
            tag = getattr(item, "Tag", None)
            if tag:
                return str(tag)
            # 備援：由樹重建 FullPath（向上找父）
            return None

        def _on_ok(self, sender, e):
            path = self._current_path()
            if not path:
                return
            self.selected_path = path
            self.Close(True)

        def _on_cancel(self, sender, e):
            self.selected_path = None
            self.Close(False)

        def _on_double_click(self, sender, e):
            path = self._current_path()
            if path:
                self.selected_path = path
                self.Close(True)

    dialog = LayerTreeDialog()
    try:
        result = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    except Exception:
        # 少數環境 MainWindow 不可用時退回無父視窗
        result = dialog.ShowModal(None)
    if result and dialog.selected_path:
        return dialog.selected_path
    return None
