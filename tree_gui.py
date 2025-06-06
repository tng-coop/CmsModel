"""Simple PyQt-based tree editor for categories and articles."""

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
    QVBoxLayout,
    QTabWidget,
    QPlainTextEdit,
    QWidget,
    QInputDialog,
    QAbstractItemView,
    QLabel,
    QGroupBox,
)

from models import Category, Article
from data import export_json


class DragTreeWidget(QTreeWidget):
    """QTreeWidget that emits a callback after items are moved."""

    def __init__(self, on_drop, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_drop = on_drop
        # Enable drag and drop so categories can be reordered
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def dropEvent(self, event):
        super().dropEvent(event)
        if self._on_drop:
            self._on_drop()


class TreeGui:
    """Display categories in a PyQt ``QTreeWidget`` and allow basic editing."""

    def __init__(self, categories: Dict[str, Category], contents: Dict[str, Article]):
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

        main_layout = QVBoxLayout(self.window)
        top_layout = QHBoxLayout()

        tree_box = QGroupBox("Categories")
        tree_layout = QVBoxLayout()
        tree_layout.addWidget(self.tree)
        tree_box.setLayout(tree_layout)
        top_layout.addWidget(tree_box)

        content_box = QGroupBox("Articles")
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.content_list)
        content_box.setLayout(content_layout)
        top_layout.addWidget(content_box)

        main_layout.addLayout(top_layout)

        self.json_view = QPlainTextEdit()
        self.json_view.setReadOnly(True)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.json_view, "JSON")
        main_layout.addWidget(self.tabs)

        self.tree.itemSelectionChanged.connect(self._on_select)
        self.tree.itemDoubleClicked.connect(self._on_rename)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_menu)
        self.content_list.itemDoubleClicked.connect(self._on_content_edit)

        self._build_tree()
        self._update_json()

    # ----------------------------------------------------------------- tree utils
    def _build_tree(self) -> None:
        self.tree.clear()
        self.nodes.clear()
        children: Dict[str | None, list[Category]] = {}
        for cat in self.categories.values():
            children.setdefault(cat.parent, []).append(cat)

        def add_nodes(parent: str | None, parent_item: QTreeWidgetItem | None = None) -> None:
            for cat in sorted(children.get(parent, []), key=lambda c: c.sort_order_index):
                name = cat.name
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

        ordered: list[tuple[str, str | None, int]] = []

        def walk(item: QTreeWidgetItem, parent: str | None) -> None:
            name = item.text(0)
            parent_item = item.parent()
            index = parent_item.indexOfChild(item) if parent_item else self.tree.indexOfTopLevelItem(item)
            ordered.append((name, parent, index))
            for i in range(item.childCount()):
                walk(item.child(i), name)

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i), None)

        new_cats: Dict[str, Category] = {}
        for name, parent, idx in ordered:
            cat = self.categories.get(name, Category(name))
            cat.parent = parent
            cat.sort_order_index = idx
            new_cats[name] = cat

        self.categories.clear()
        self.categories.update(new_cats)
        self._update_json()

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
            for art in self.contents.values():
                art.categories = [new_name if c == name else c for c in art.categories]
            self._build_tree()
            self.tree.setCurrentItem(self.nodes[new_name])
            self._show_content(new_name)
        self._update_json()

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
            for art in self.contents.values():
                art.categories = [cat for cat in art.categories if cat != name]
            self._build_tree()
            self.content_list.clear()
        self._update_json()

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
            if cat in c.categories:
                item = QListWidgetItem(f"{c.name} (archived: {c.archived})")
                item.setData(Qt.UserRole, c.name)
                self.content_list.addItem(item)
                self._content_map[idx] = c.name
                idx += 1
        self._update_json()

    def _on_content_edit(self, item) -> None:
        name = item.data(Qt.UserRole)
        if name is None:
            return
        c = self.contents[name]
        new_name, ok = QInputDialog.getText(self.window, "Article Name", "Name:", text=c.name)
        if not ok or not new_name:
            return
        cat_str, ok = QInputDialog.getText(
            self.window,
            "Categories",
            "Categories (comma separated):",
            text=", ".join(c.categories),
        )
        if not ok:
            return
        cats = [cat.strip() for cat in cat_str.split(',') if cat.strip()]
        if not all(cat in self.categories for cat in cats):
            return
        archived_str, ok = QInputDialog.getText(
            self.window,
            "Archived",
            "Archived (true/false):",
            text=str(c.archived).lower(),
        )
        if not ok:
            return
        archived = archived_str.lower() == 'true'
        if new_name != name:
            self.contents.pop(name)
        self.contents[new_name] = Article(new_name, cats, archived)
        self._show_content(cats[0] if cats else '')
        self._update_json()

    def _update_json(self) -> None:
        """Refresh the JSON tab with current tree data."""
        self.json_view.setPlainText(export_json(self.categories, self.contents))

    # --------------------------------------------------------------------------
    def run(self) -> None:
        self.window.show()
        self.app.exec_()

