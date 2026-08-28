# -*- coding: utf-8 -*-
"""Rhino 端簡易對話框：階層圖層選取（可捲動）。"""
from __future__ import annotations

from typing import Optional, Sequence


def _pick_layer_listbox(
    layer_paths: Sequence[str],
    *,
    default_path: Optional[str],
    title: str,
    message: str,
) -> Optional[str]:
    """備援：縮排 ListBox（有捲軸；視覺階層）。"""
    import rhinoscriptsyntax as rs  # type: ignore

    display = []
    for path in layer_paths:
        parts = path.split("::")
        indent = "    " * (len(parts) - 1)
        display.append("{}{}".format(indent, parts[-1]))

    selected = rs.ListBox(display, message=message, title=title)
    if selected is None:
        return None
    try:
        idx = display.index(selected)
    except ValueError:
        return None
    return str(layer_paths[idx])


def pick_layer_path(
    layer_paths: Sequence[str],
    *,
    default_path: Optional[str] = None,
    title: str = "R2B Models",
    message: str = "選擇要匯出的模型圖層，含子層",
) -> Optional[str]:
    """優先 Eto TreeGridView；失敗則縮排 ListBox。"""
    paths = [str(p) for p in layer_paths if p]
    if not paths:
        return None

    try:
        return _pick_layer_eto(paths, default_path=default_path, title=title, message=message)
    except Exception:
        return _pick_layer_listbox(
            paths, default_path=default_path, title=title, message=message
        )


def _pick_layer_eto(
    paths,
    *,
    default_path: Optional[str],
    title: str,
    message: str,
) -> Optional[str]:
    import Eto.Drawing as drawing  # type: ignore
    import Eto.Forms as forms  # type: ignore
    import Rhino.UI  # type: ignore

    class LayerTreeDialog(forms.Dialog):
        def __init__(self):
            forms.Dialog.__init__(self)
            self.Title = title
            self.Padding = drawing.Padding(8)
            self.Resizable = True
            # 約為先前 440×520 的一半
            self.ClientSize = drawing.Size(220, 260)
            self.MinimumSize = drawing.Size(200, 200)
            self.selected_path = None

            label = forms.Label()
            label.Text = message

            tree = forms.TreeGridView()
            tree.ShowHeader = False
            tree.AllowMultipleSelection = False
            col = forms.GridColumn()
            col.DataCell = forms.TextBoxCell(0)
            col.Editable = False
            col.Expand = True
            tree.Columns.Add(col)

            self._tree = tree
            root_items = forms.TreeGridItemCollection()
            nodes = {}

            for path in paths:
                parts = path.split("::")
                for depth in range(len(parts)):
                    full = "::".join(parts[: depth + 1])
                    if full in nodes:
                        continue
                    item = forms.TreeGridItem()
                    # Values[0]=顯示名；Values[1]=FullPath（選取時讀回）
                    item.Values = [parts[depth], full]
                    item.Expanded = False  # 預設全部摺起，只見頂層
                    nodes[full] = item
                    if depth == 0:
                        root_items.Add(item)
                    else:
                        parent_full = "::".join(parts[:depth])
                        nodes[parent_full].Children.Add(item)

            tree.DataStore = root_items
            if default_path and default_path in nodes:
                # 展開通往預設項的祖先，其餘保持摺起
                parts = default_path.split("::")
                for depth in range(len(parts) - 1):
                    ancestor = "::".join(parts[: depth + 1])
                    if ancestor in nodes:
                        nodes[ancestor].Expanded = True
                try:
                    tree.SelectedItem = nodes[default_path]
                    self.selected_path = default_path
                except Exception:
                    pass

            tree.SelectedItemChanged += self._on_selection_changed
            tree.CellDoubleClick += self._on_double_click

            ok = forms.Button()
            ok.Text = "確定"
            cancel = forms.Button()
            cancel.Text = "取消"
            ok.Click += self._on_ok
            cancel.Click += self._on_cancel
            self.DefaultButton = ok
            self.AbortButton = cancel

            buttons = forms.DynamicLayout()
            buttons.DefaultSpacing = drawing.Size(8, 0)
            buttons.AddRow(None, ok, cancel)

            layout = forms.DynamicLayout()
            layout.DefaultSpacing = drawing.Size(4, 6)
            layout.AddRow(label)
            layout.Add(tree, yscale=True, xscale=True)
            layout.AddRow(buttons)
            self.Content = layout

        def _path_from_item(self, item):
            if item is None:
                return None
            try:
                values = item.Values
                if values is not None and len(values) >= 2 and values[1]:
                    return str(values[1])
            except Exception:
                pass
            return None

        def _current_path(self):
            try:
                return self._path_from_item(self._tree.SelectedItem)
            except Exception:
                return None

        def _on_selection_changed(self, sender, e):
            path = self._current_path()
            if path:
                self.selected_path = path

        def _on_ok(self, sender, e):
            path = self._current_path() or self.selected_path
            if not path:
                return
            self.selected_path = path
            self.Close()

        def _on_cancel(self, sender, e):
            self.selected_path = None
            self.Close()

        def _on_double_click(self, sender, e):
            # 雙擊列：以該列路徑確認（不依賴 SelectedItem 時序）
            path = None
            try:
                if e is not None and getattr(e, "Item", None) is not None:
                    path = self._path_from_item(e.Item)
            except Exception:
                path = None
            if not path:
                path = self._current_path() or self.selected_path
            if path:
                self.selected_path = path
                self.Close()

    dialog = LayerTreeDialog()
    parent = None
    try:
        parent = Rhino.UI.RhinoEtoApp.MainWindow
    except Exception:
        parent = None
    dialog.ShowModal(parent)
    return dialog.selected_path
