"""Interactive tree viewer and editor for categories."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.shortcuts import input_dialog, radiolist_dialog
from prompt_toolkit.mouse_events import MouseEventType, MouseButton
from prompt_toolkit.filters import Condition
from prompt_toolkit.styles import Style

from .models import Category, Content


class TreeNode:
    """Node used by :class:`TreeEditor`."""

    def __init__(self, name: str, category: Optional[Category] = None):
        self.name = name
        self.category = category
        self.children: List["TreeNode"] = []
        self.expanded = False

    def toggle(self) -> None:
        if self.children:
            self.expanded = not self.expanded


class TreeEditor:
    """Full screen tree browser with rename and move commands."""

    def __init__(self, categories: Dict[str, Category], contents: Optional[Dict[str, Content]] = None):
        self.categories = categories
        self.contents = contents or {}
        self.selected_index = 0
        self.order = self._build_order()
        self.root = self._build_tree()
        self._lines: List[Tuple[TreeNode, str]] = []

        # Context menu and inline edit state
        self.show_menu = False
        self.menu_parent_index = -1
        self.is_editing = False
        self.edit_index = -1
        self.edit_text = ""

        # Drag and drop state
        self.dragging = False
        self.drag_index = -1

        self.is_editing_content = False
        self.edit_content_name = ""
        self.edit_content_values: List[str] = []
        self.edit_content_field = 0

        self.bindings = self._create_bindings()
        self.style = Style.from_dict({
            "line": "bg:#444444",
            "status": "bg:#222222 #aaaaaa",
        })
        self.app = self._create_app()

    def _build_order(self) -> Dict[Optional[str], List[str]]:
        """Create mapping of parent -> ordered child names."""
        order: Dict[Optional[str], List[str]] = {}
        for name, cat in self.categories.items():
            order.setdefault(cat.parent, []).append(name)
        return order

    def _selected_category(self) -> Optional[str]:
        """Return the currently selected category name, or None."""
        if not self._lines:
            return None
        node, _ = self._lines[self.selected_index]
        return node.name

    # ------------------------------------------------------------------ utils
    def _build_tree(self) -> TreeNode:
        nodes = {name: TreeNode(name, c) for name, c in self.categories.items()}
        root = TreeNode("ROOT")
        for parent, children in self.order.items():
            parent_node = root if parent is None else nodes.get(parent)
            if not parent_node:
                continue
            for name in children:
                node = nodes.get(name)
                if node:
                    parent_node.children.append(node)
        root.expanded = True
        return root

    def _visible_lines(self, node: TreeNode, prefix: str = "", show_node: bool = True) -> List[Tuple[TreeNode, str]]:
        lines: List[Tuple[TreeNode, str]] = []
        if show_node:
            icon = "   "
            if node.children:
                icon = "[-]" if node.expanded else "[+]"
            lines.append((node, f"{prefix}{icon} {node.name}"))
            prefix += "    "
        if node.expanded or not show_node:
            for child in node.children:
                lines.extend(self._visible_lines(child, prefix, True))
        return lines

    def _collect_descendants(self, node: TreeNode) -> List[str]:
        names = []
        for child in node.children:
            names.append(child.name)
            names.extend(self._collect_descendants(child))
        return names

    def _parent_name(self, idx: int) -> Optional[str]:
        """Return the parent category name for the line at index."""
        text = self._lines[idx][1]
        indent = len(text) - len(text.lstrip())
        for j in range(idx - 1, -1, -1):
            t = self._lines[j][1]
            indent_j = len(t) - len(t.lstrip())
            if indent_j < indent:
                node = self._lines[j][0]
                return None if node is self.root else node.name
        return None

    def _reorder_siblings(self, parent: Optional[str], from_idx: int, to_idx: int) -> None:
        from_node, _ = self._lines[from_idx]
        to_node, _ = self._lines[to_idx]
        lst = self.order.get(parent, [])
        try:
            fi = lst.index(from_node.name)
            ti = lst.index(to_node.name)
        except ValueError:
            return
        item = lst.pop(fi)
        if ti > fi:
            ti -= 1
        lst.insert(ti, item)
        self.root = self._build_tree()
        self.selected_index = to_idx

    # -------------------------------------------------------------- operations
    async def _rename_node(self) -> None:
        node, _ = self._lines[self.selected_index]
        new_name = await input_dialog(
            title="Rename Category",
            text=f"Enter new name for '{node.name}':",
            default=node.name,
        ).run_async()
        if new_name and new_name != node.name:
            old_name = node.name
            cat = self.categories.pop(old_name)
            cat.name = new_name
            self.categories[new_name] = cat
            for c in self.categories.values():
                if c.parent == old_name:
                    c.parent = new_name
            for lst in self.order.values():
                for i, n in enumerate(lst):
                    if n == old_name:
                        lst[i] = new_name
            self.root = self._build_tree()
            self._reset_selection(new_name)
            self.app.invalidate()

    async def _change_parent(self) -> None:
        node, _ = self._lines[self.selected_index]
        exclude = set(self._collect_descendants(node)) | {node.name}
        options = [('none', 'None')] + [
            (name, name) for name in sorted(self.categories.keys()) if name not in exclude
        ]
        result = await radiolist_dialog(
            title="Change Parent",
            text=f"Select new parent for '{node.name}':",
            values=options,
        ).run_async()
        if result is None:
            return
        new_parent = None if result == 'none' else result
        old_parent = self.categories[node.name].parent
        self.categories[node.name].parent = new_parent
        if old_parent in self.order:
            try:
                self.order[old_parent].remove(node.name)
            except ValueError:
                pass
        self.order.setdefault(new_parent, []).append(node.name)
        self.root = self._build_tree()
        self._reset_selection(node.name)
        self.app.invalidate()

    def _reset_selection(self, name: str) -> None:
        self.selected_index = 0
        for i, (n, _) in enumerate(self._visible_lines(self.root, show_node=False)):
            if n.name == name:
                self.selected_index = i
                break

    # ---------------------------------------------------------------- bindings
    def _create_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up")
        def _up(event) -> None:
            if self.is_editing:
                self.is_editing = False
            elif self.show_menu:
                self.show_menu = False
            elif self.selected_index > 0:
                self.selected_index -= 1
            event.app.invalidate()

        @kb.add("down")
        def _down(event) -> None:
            if self.is_editing:
                self.is_editing = False
            elif self.show_menu:
                self.show_menu = False
            elif self.selected_index < len(self._lines) - 1:
                self.selected_index += 1
            event.app.invalidate()

        @kb.add("right")
        def _expand(event) -> None:
            if self.is_editing:
                self.is_editing = False
            elif self.show_menu:
                self.show_menu = False
            else:
                node, _ = self._lines[self.selected_index]
                if node.children and not node.expanded:
                    node.expanded = True
            event.app.invalidate()

        @kb.add("left")
        def _collapse(event) -> None:
            if self.is_editing:
                self.is_editing = False
            elif self.show_menu:
                self.show_menu = False
            else:
                node, _ = self._lines[self.selected_index]
                if node.children and node.expanded:
                    node.expanded = False
                else:
                    current_text = self._lines[self.selected_index][1]
                    current_indent = len(current_text) - len(current_text.lstrip())
                    for i in range(self.selected_index - 1, -1, -1):
                        text_i = self._lines[i][1]
                        indent_i = len(text_i) - len(text_i.lstrip())
                        if indent_i < current_indent:
                            self.selected_index = i
                            break
            event.app.invalidate()

        @kb.add("enter")
        def _enter(event) -> None:
            if self.is_editing:
                node, _ = self._lines[self.edit_index]
                old_name = node.name
                new_name = self.edit_text
                if new_name and new_name != old_name:
                    cat = self.categories.pop(old_name)
                    cat.name = new_name
                    self.categories[new_name] = cat
                    for c in self.categories.values():
                        if c.parent == old_name:
                            c.parent = new_name
                    node.name = new_name
                    self.root = self._build_tree()
                    self._reset_selection(new_name)
                self.is_editing = False
                self.edit_index = -1
            elif self.is_editing_content:
                old = self.edit_content_name
                name, ctype, cat, action = self.edit_content_values
                if name != old:
                    self.contents.pop(old, None)
                self.contents[name] = Content(name, ctype, cat, action)
                self.is_editing_content = False
                self.edit_content_name = ""
            event.app.invalidate()

        @kb.add("escape")
        def _escape(event) -> None:
            if self.is_editing:
                self.is_editing = False
                self.edit_index = -1
            elif self.is_editing_content:
                self.is_editing_content = False
            elif self.show_menu:
                self.show_menu = False
                self.menu_parent_index = -1
            else:
                event.app.exit()
            event.app.invalidate()

        @kb.add("backspace")
        def _backspace(event) -> None:
            if self.is_editing:
                self.edit_text = self.edit_text[:-1]
                event.app.invalidate()
            elif self.is_editing_content:
                val = self.edit_content_values[self.edit_content_field]
                self.edit_content_values[self.edit_content_field] = val[:-1]
                event.app.invalidate()

        @kb.add("<any>", filter=Condition(lambda: self.is_editing or self.is_editing_content))
        def _any_key(event) -> None:
            key = event.key_sequence[0].key
            if len(key) == 1:
                if self.is_editing:
                    self.edit_text += key
                else:
                    val = self.edit_content_values[self.edit_content_field]
                    self.edit_content_values[self.edit_content_field] = val + key
                event.app.invalidate()

        @kb.add("tab", filter=Condition(lambda: self.is_editing_content))
        def _tab(event) -> None:
            self.edit_content_field = (self.edit_content_field + 1) % 4
            event.app.invalidate()

        @kb.add("r")
        def _rename(event) -> None:
            asyncio.create_task(self._rename_node())

        @kb.add("p")
        def _parent(event) -> None:
            asyncio.create_task(self._change_parent())

        @kb.add("q")
        def _quit(event) -> None:
            event.app.exit()

        return kb

    # ------------------------------------------------------------------ layout
    def _render(self):
        fragments = []
        lines = self._visible_lines(self.root, show_node=False)
        self._lines = lines
        total = len(lines)
        if total == 0:
            return fragments

        if self.selected_index < 0:
            self.selected_index = 0
        if self.selected_index >= total:
            self.selected_index = total - 1

        if self.show_menu and (self.menu_parent_index < 0 or self.menu_parent_index >= total):
            self.show_menu = False

        idx = 0
        while idx < total:
            node, text = lines[idx]
            style = "reverse" if idx == self.selected_index else ""
            if self.dragging and idx == self.drag_index:
                style = (style + " underline").strip()

            if self.is_editing and idx == self.edit_index:
                prefix = text[:-len(node.name)]
                displayed = f"{prefix}{self.edit_text}|"
                fragments.append((style, displayed + "\n", self._mouse_handler(node, idx)))
                idx += 1
                continue

            fragments.append((style, text + "\n", self._mouse_handler(node, idx)))
            idx += 1

            if self.show_menu and idx - 1 == self.menu_parent_index:
                fragments.append(("", "    ❏ Rename\n", self._menu_mouse_factory("rename", self.menu_parent_index)))
                fragments.append(("", "    ❏ Delete\n", self._menu_mouse_factory("delete", self.menu_parent_index)))

        return fragments

    def _menu_mouse_factory(self, option: str, parent_idx: int):
        """Return mouse handler for inline menu options."""

        def menu_handler(mouse_event):
            if (
                mouse_event.event_type == MouseEventType.MOUSE_UP
                and mouse_event.button == MouseButton.LEFT
            ):
                self.show_menu = False
                if option == "rename":
                    self.is_editing = True
                    self.edit_index = parent_idx
                    node, _ = self._lines[parent_idx]
                    self.edit_text = node.name
                    self.selected_index = parent_idx
                else:  # delete
                    node, text = self._lines[parent_idx]
                    if node is not self.root:
                        self.categories.pop(node.name, None)
                        parent_name = self._parent_name(parent_idx)
                        if parent_name in self.order:
                            try:
                                self.order[parent_name].remove(node.name)
                            except ValueError:
                                pass
                        indent_i = len(text) - len(text.lstrip())
                        parent = None
                        for j in range(parent_idx - 1, -1, -1):
                            node_j, text_j = self._lines[j]
                            indent_j = len(text_j) - len(text_j.lstrip())
                            if indent_j < indent_i:
                                parent = node_j
                                break
                        if parent and node in parent.children:
                            parent.children.remove(node)
                        self.root = self._build_tree()
                        visible_after = self._visible_lines(self.root, show_node=False)
                        self.selected_index = min(parent_idx, len(visible_after) - 1)
                self.menu_parent_index = -1
                self.app.invalidate()
        return menu_handler

    def _mouse_handler(self, node: TreeNode, idx: int):
        def handler(mouse_event):
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN and mouse_event.button == MouseButton.LEFT:
                if not self.is_editing:
                    self.dragging = True
                    self.drag_index = idx
                    self.selected_index = idx
                    self.app.invalidate()
                return

            if mouse_event.event_type == MouseEventType.MOUSE_UP:

                if self.dragging and mouse_event.button == MouseButton.LEFT:
                    self.dragging = False
                    if idx != self.drag_index:
                        p_from = self._parent_name(self.drag_index)
                        p_to = self._parent_name(idx)
                        if p_from == p_to:
                            self._reorder_siblings(p_from, self.drag_index, idx)
                    self.app.invalidate()
                    return

                if self.is_editing and mouse_event.button == MouseButton.LEFT:
                    if idx != self.edit_index:
                        self.is_editing = False
                        self.app.invalidate()
                        return

                if mouse_event.button == MouseButton.LEFT and not self.is_editing:
                    if self.show_menu and self.menu_parent_index != idx:
                        self.show_menu = False
                    else:
                        self.selected_index = idx
                        if node.children:
                            node.toggle()
                    self.app.invalidate()

                elif mouse_event.button == MouseButton.RIGHT and not self.is_editing:
                    self.selected_index = idx
                    self.menu_parent_index = idx
                    self.show_menu = True
                    self.app.invalidate()

        return handler

    def _content_mouse_factory(self, name: str):
        """Return mouse handler for content edit buttons."""

        def handler(mouse_event):
            if (
                mouse_event.event_type == MouseEventType.MOUSE_UP
                and mouse_event.button == MouseButton.LEFT
            ):
                self._start_content_edit(name)

        return handler

    def _start_content_edit(self, name: str) -> None:
        """Begin inline editing for a content item."""
        c = self.contents.get(name)
        if not c:
            return
        self.is_editing_content = True
        self.edit_content_name = name
        self.edit_content_values = [c.name, c.content_type, c.category, c.action]
        self.edit_content_field = 0
        self.app.invalidate()


    def _render_content(self):
        """Render the content panel for the selected category."""
        fragments = []
        cat = self._selected_category()
        if not cat:
            return fragments

        header = f"Content for '{cat}':\n"
        fragments.append(("class:status", header))

        for c in self.contents.values():
            if c.category == cat:
                if self.is_editing_content and c.name == self.edit_content_name:
                    labels = ["Name", "Type", "Category", "Action"]
                    for i, label in enumerate(labels):
                        val = self.edit_content_values[i]
                        cursor = "|" if self.edit_content_field == i else ""
                        style = "reverse" if self.edit_content_field == i else ""
                        fragments.append((style, f"  {label}: {val}{cursor}\n"))
                    fragments.append(("class:status", "(Tab to switch, Enter to save, Esc to cancel)\n"))
                else:
                    fragments.append(("", f"  {c.name} ({c.content_type}, {c.action}) "))
                    fragments.append(
                        ("class:status", "[Edit]\n", self._content_mouse_factory(c.name))
                    )

        return fragments

    def _create_app(self) -> Application:
        tree_control = FormattedTextControl(self._render, focusable=True, show_cursor=False)
        tree_window = Window(content=tree_control, wrap_lines=False)
        content_control = FormattedTextControl(self._render_content, focusable=False)
        content_window = Window(content=content_control, wrap_lines=True)

        main_area = VSplit([
            tree_window,
            Window(width=1, char="│", style="class:line"),
            content_window,
        ])

        body = HSplit([
            main_area,
            Window(height=1, char="─", style="class:line"),
            Window(
                content=FormattedTextControl(
                    lambda: [
                        (
                            "class:status",
                            (
                                " Editing: Type text, Enter to save, Esc to cancel. "
                                if self.is_editing or self.is_editing_content
                                else " Use ↑/↓ to move, ←/→ to collapse/expand, Right-click for menu, click [Edit] to modify content, Q or Esc to quit. "
                            ),
                        )
                    ]
                ),
                height=1,
            ),
        ])
        app = Application(
            layout=Layout(body, focused_element=tree_window),
            key_bindings=self.bindings,
            mouse_support=True,
            full_screen=True,
            style=self.style,
        )
        return app

    # ---------------------------------------------------------------------- API
    def run(self) -> None:
        """Run the interactive editor."""
        self.app.run()

