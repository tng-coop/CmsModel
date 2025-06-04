"""Simple Tkinter-based tree editor for categories and contents."""

from __future__ import annotations

from typing import Dict

import tkinter as tk
from tkinter import simpledialog, ttk

from .models import Category, Content


class TreeGui:
    """Display categories in a Tkinter Treeview and allow basic editing."""

    def __init__(self, categories: Dict[str, Category], contents: Dict[str, Content]):
        self.categories = categories
        self.contents = contents
        self.nodes: Dict[str, str] = {}

        self.root = tk.Tk()
        self.root.title("CMS Tree GUI")

        self.tree = ttk.Treeview(self.root)
        self.tree.pack(side="left", fill="both", expand=True)

        self.content_list = tk.Listbox(self.root)
        self.content_list.pack(side="right", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_rename)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Rename", command=self._on_rename)
        self.menu.add_command(label="Delete", command=self._on_delete)
        self.tree.bind("<Button-3>", self._show_menu)

        self._build_tree()

    # ----------------------------------------------------------------- tree utils
    def _build_tree(self) -> None:
        self.tree.delete(*self.tree.get_children(""))
        self.nodes.clear()
        children: Dict[str | None, list[str]] = {}
        for cat in self.categories.values():
            children.setdefault(cat.parent, []).append(cat.name)

        def add_nodes(parent: str | None, parent_id: str = "") -> None:
            for name in sorted(children.get(parent, [])):
                item_id = self.tree.insert(parent_id, "end", text=name)
                self.nodes[name] = item_id
                add_nodes(name, item_id)

        add_nodes(None)

    # --------------------------------------------------------------------- actions
    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "text")
        self._show_content(name)

    def _on_rename(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "text")
        new_name = simpledialog.askstring("Rename Category", "New name:", initialvalue=name, parent=self.root)
        if new_name and new_name != name:
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
            self.tree.selection_set(self.nodes[new_name])
            self._show_content(new_name)

    def _on_delete(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "text")
        if name in self.categories:
            self.categories.pop(name)
            for c in self.categories.values():
                if c.parent == name:
                    c.parent = None
            self._build_tree()
            self.content_list.delete(0, "end")

    def _show_menu(self, event) -> None:
        sel = self.tree.identify_row(event.y)
        if sel:
            self.tree.selection_set(sel)
            self.menu.tk_popup(event.x_root, event.y_root)

    # -------------------------------------------------------------- content utils
    def _show_content(self, cat: str) -> None:
        self.content_list.delete(0, "end")
        self._content_map: Dict[int, str] = {}
        idx = 0
        for c in self.contents.values():
            if c.category == cat:
                self.content_list.insert("end", f"{c.name} ({c.content_type}, {c.action})")
                self._content_map[idx] = c.name
                idx += 1
        self.content_list.bind("<Double-1>", self._on_content_edit)

    def _on_content_edit(self, _event=None) -> None:
        sel = self.content_list.curselection()
        if not sel:
            return
        name = self._content_map.get(sel[0])
        if not name:
            return
        c = self.contents[name]
        new_name = simpledialog.askstring("Content Name", "Name:", initialvalue=c.name, parent=self.root)
        if not new_name:
            return
        ctype = simpledialog.askstring("Content Type", "Type:", initialvalue=c.content_type, parent=self.root)
        if not ctype:
            return
        options = sorted(self.categories.keys())
        parent = simpledialog.askstring("Category", "Category:", initialvalue=c.category, parent=self.root)
        if parent not in options:
            parent = c.category
        action = simpledialog.askstring("Action", "Action:", initialvalue=c.action, parent=self.root)
        if not action:
            return
        if new_name != name:
            self.contents.pop(name)
        self.contents[new_name] = Content(new_name, ctype, parent, action)
        self._show_content(parent)

    # --------------------------------------------------------------------------
    def run(self) -> None:
        self.root.mainloop()

