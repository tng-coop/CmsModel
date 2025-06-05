"""Simple PyQt-based tree editor for categories and contents."""

from __future__ import annotations

from typing import Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QHBoxLayout,
    QWidget,
    QInputDialog,
    QAbstractItemView,
)

from models import Category, Content


class DragTreeWidget(QTreeWidget):
    """QTreeWidget that emits a callback after items are moved."""

    def __init__(self, on_drop, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_drop = on_drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def dropEvent(self, event):
        super().dropEvent(event)
        if self._on_drop:
            self._on_drop()


class TreeGui:
    """Display categories in a PyQt ``QTreeWidget`` and allow basic editing."""

    def __init__(self, categories: Dict[str, Category], contents: Dict[str, Content]):
        self.categories = categories
        self.contents = contents
        self.nodes: Dict[str, QTreeWidgetItem] = {}
        self._content_map: Dict[int, str] = {}

        self.app = QApplication([])
        self.window = QWidget()
        self.window.setWindowTitle("CMS Tree GUI")

        self.tree = DragTreeWidget(self._sync_categories)
        self.tree.setHeaderHidden(True)

        self.content_list = QListWidget()

        layout = QHBoxLayout(self.window)
        layout.addWidget(self.tree)
        layout.addWidget(self.content_list)

        self.tree.itemSelectionChanged.connect(self._on_select)
        self.tree.itemDoubleClicked.connect(self._on_rename)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_menu)
        self.content_list.itemDoubleClicked.connect(self._on_content_edit)

        self._build_tree()

    # ----------------------------------------------------------------- tree utils
    def _build_tree(self) -> None:
        self.tree.clear()
        self.nodes.clear()
        children: Dict[str | None, list[str]] = {}
        for cat in self.categories.values():
            children.setdefault(cat.parent, []).append(cat.name)

        def add_nodes(parent: str | None, parent_item: QTreeWidgetItem | None = None) -> None:
            for name in children.get(parent, []):
                item = QTreeWidgetItem([name])
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self.tree.addTopLevelItem(item)
                self.nodes[name] = item
                add_nodes(name, item)

        add_nodes(None)
        self.tree.expandAll()

    def _sync_categories(self) -> None:
        """Update category parents and order based on the tree structure."""

        ordered: list[tuple[str, str | None]] = []

        def walk(item: QTreeWidgetItem, parent: str | None) -> None:
            name = item.text(0)
            ordered.append((name, parent))
            for i in range(item.childCount()):
                walk(item.child(i), name)

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i), None)

        new_cats: Dict[str, Category] = {}
        for name, parent in ordered:
            cat = self.categories.get(name, Category(name))
            cat.parent = parent
            new_cats[name] = cat

        self.categories.clear()
        self.categories.update(new_cats)

    # --------------------------------------------------------------------- actions
    def _on_select(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            return
        name = items[0].text(0)
        self._show_content(name)

    def _on_rename(self, item=None) -> None:
        if item is None:
            items = self.tree.selectedItems()
            if not items:
                return
            item = items[0]
        name = item.text(0)
        new_name, ok = QInputDialog.getText(self.window, "Rename Category", "New name:", text=name)
        if ok and new_name and new_name != name:
            cat = self.categories.pop(name)
            cat.name = new_name
            self.categories[new_name] = cat
            for c in self.categories.values():
                if c.parent == name:
                    c.parent = new_name
            for cont in self.contents.values():
                if cont.category == name:
                    cont.category = new_name
            self._build_tree()
            self.tree.setCurrentItem(self.nodes[new_name])
            self._show_content(new_name)

    def _on_delete(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            return
        name = items[0].text(0)
        if name in self.categories:
            self.categories.pop(name)
            for c in self.categories.values():
                if c.parent == name:
                    c.parent = None
            self._build_tree()
            self.content_list.clear()

    def _show_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        if not item:
            return
        self.tree.setCurrentItem(item)
        menu = QMenu(self.tree)
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if action == rename_action:
            self._on_rename(item)
        elif action == delete_action:
            self._on_delete()

    # -------------------------------------------------------------- content utils
    def _show_content(self, cat: str) -> None:
        self.content_list.clear()
        self._content_map.clear()
        idx = 0
        for c in self.contents.values():
            if c.category == cat:
                item = QListWidgetItem(f"{c.name} ({c.content_type}, {c.action})")
                item.setData(Qt.UserRole, c.name)
                self.content_list.addItem(item)
                self._content_map[idx] = c.name
                idx += 1

    def _on_content_edit(self, item) -> None:
        name = item.data(Qt.UserRole)
        if name is None:
            return
        c = self.contents[name]
        new_name, ok = QInputDialog.getText(self.window, "Content Name", "Name:", text=c.name)
        if not ok or not new_name:
            return
        ctype, ok = QInputDialog.getText(self.window, "Content Type", "Type:", text=c.content_type)
        if not ok or not ctype:
            return
        options = sorted(self.categories.keys())
        parent, ok = QInputDialog.getText(self.window, "Category", "Category:", text=c.category)
        if not ok or parent not in options:
            parent = c.category
        action, ok = QInputDialog.getText(self.window, "Action", "Action:", text=c.action)
        if not ok or not action:
            return
        if new_name != name:
            self.contents.pop(name)
        self.contents[new_name] = Content(new_name, ctype, parent, action)
        self._show_content(parent)

    # --------------------------------------------------------------------------
    def run(self) -> None:
        self.window.show()
        self.app.exec_()

