"""Interactive tree viewer and editor for categories."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.shortcuts import input_dialog, radiolist_dialog
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.styles import Style

from .models import Category


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

    def __init__(self, categories: Dict[str, Category]):
        self.categories = categories
        self.selected_index = 0
        self.root = self._build_tree()
        self._lines: List[Tuple[TreeNode, str]] = []
        self.bindings = self._create_bindings()
        self.style = Style.from_dict({
            "line": "bg:#444444",
            "status": "bg:#222222 #aaaaaa",
        })
        self.app = self._create_app()

    # ------------------------------------------------------------------ utils
    def _build_tree(self) -> TreeNode:
        nodes = {name: TreeNode(name, c) for name, c in self.categories.items()}
        root = TreeNode("ROOT")
        for name, cat in self.categories.items():
            node = nodes[name]
            if cat.parent and cat.parent in nodes:
                nodes[cat.parent].children.append(node)
            else:
                root.children.append(node)
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

    # -------------------------------------------------------------- operations
    def _rename_node(self) -> None:
        node, _ = self._lines[self.selected_index]
        new_name = input_dialog(
            title="Rename Category",
            text=f"Enter new name for '{node.name}':",
            default=node.name,
        ).run()
        if new_name and new_name != node.name:
            old_name = node.name
            cat = self.categories.pop(old_name)
            cat.name = new_name
            self.categories[new_name] = cat
            for c in self.categories.values():
                if c.parent == old_name:
                    c.parent = new_name
            self.root = self._build_tree()
            self._reset_selection(new_name)
            self.app.invalidate()

    def _change_parent(self) -> None:
        node, _ = self._lines[self.selected_index]
        exclude = set(self._collect_descendants(node)) | {node.name}
        options = [('none', 'None')] + [
            (name, name) for name in sorted(self.categories.keys()) if name not in exclude
        ]
        result = radiolist_dialog(
            title="Change Parent",
            text=f"Select new parent for '{node.name}':",
            values=options,
        ).run()
        if result is None:
            return
        new_parent = None if result == 'none' else result
        self.categories[node.name].parent = new_parent
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
            if self.selected_index > 0:
                self.selected_index -= 1
                event.app.invalidate()

        @kb.add("down")
        def _down(event) -> None:
            if self.selected_index < len(self._lines) - 1:
                self.selected_index += 1
                event.app.invalidate()

        @kb.add("right")
        def _expand(event) -> None:
            node, _ = self._lines[self.selected_index]
            if node.children and not node.expanded:
                node.expanded = True
                event.app.invalidate()

        @kb.add("left")
        def _collapse(event) -> None:
            node, _ = self._lines[self.selected_index]
            if node.children and node.expanded:
                node.expanded = False
                event.app.invalidate()
            else:
                current_text = self._lines[self.selected_index][1]
                current_indent = len(current_text) - len(current_text.lstrip())
                for i in range(self.selected_index - 1, -1, -1):
                    text_i = self._lines[i][1]
                    indent_i = len(text_i) - len(text_i.lstrip())
                    if indent_i < current_indent:
                        self.selected_index = i
                        event.app.invalidate()
                        return

        @kb.add("r")
        def _rename(event) -> None:
            self._rename_node()

        @kb.add("p")
        def _parent(event) -> None:
            self._change_parent()

        @kb.add("q")
        def _quit(event) -> None:
            event.app.exit()

        return kb

    # ------------------------------------------------------------------ layout
    def _render(self):
        fragments = []
        self._lines = self._visible_lines(self.root, show_node=False)
        if not self._lines:
            return fragments
        if self.selected_index < 0:
            self.selected_index = 0
        if self.selected_index >= len(self._lines):
            self.selected_index = len(self._lines) - 1
        for idx, (node, text) in enumerate(self._lines):
            style = "reverse" if idx == self.selected_index else ""
            fragments.append((style, text + "\n", self._mouse_handler(node, idx)))
        return fragments

    def _mouse_handler(self, node: TreeNode, idx: int):
        def handler(mouse_event):
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.selected_index = idx
                if node.children:
                    node.toggle()
                self.app.invalidate()
        return handler

    def _create_app(self) -> Application:
        tree_control = FormattedTextControl(self._render, focusable=True, show_cursor=False)
        tree_window = Window(content=tree_control, wrap_lines=False)
        body = HSplit([
            tree_window,
            Window(height=1, char="─", style="class:line"),
            Window(content=FormattedTextControl(lambda: [
                ("class:status", " ↑/↓ move, ←/→ collapse/expand, R rename, P change parent, Q quit ")
            ]), height=1),
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

