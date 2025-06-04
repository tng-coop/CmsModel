"""Utility functions for CMS data management."""

from typing import Dict, List, Optional, Set, Tuple

from .models import Category, Content
from prompt_toolkit import Application, PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import TextArea


def seed_data(categories: Dict[str, Category], contents: Dict[str, Content]) -> None:
    """Populate dictionaries with sample catholic church data."""
    categories.clear()
    contents.clear()

    seed_categories = {
        'Home': Category('Home'),
        'About': Category('About'),
        'Mass Times': Category('Mass Times'),
        'Sacraments': Category('Sacraments'),
        'Ministries': Category('Ministries'),
        'Downloads': Category('Downloads'),
        'Staff': Category('Staff', parent='About'),
        'History': Category('History', parent='About'),
        'Contact': Category('Contact', parent='About'),
        'Baptism': Category('Baptism', parent='Sacraments'),
        'Confirmation': Category('Confirmation', parent='Sacraments'),
        'Marriage': Category('Marriage', parent='Sacraments'),
        'Youth Ministry': Category('Youth Ministry', parent='Ministries'),
        'Choir': Category('Choir', parent='Ministries'),
        'High School': Category('High School', parent='Youth Ministry'),
    }
    categories.update(seed_categories)

    seed_contents = {
        'office_hours': Content('office_hours', 'office_info', 'Home', 'update'),
        'welcome': Content('welcome', 'tinymce', 'Home', 'new'),
        'bulletin': Content('bulletin', 'pdf', 'Downloads', 'update'),
        'youth_banner': Content('youth_banner', 'banner', 'Youth Ministry', 'new'),
        'old_news': Content('old_news', 'tinymce', 'Home', 'delete'),
    }
    contents.update(seed_contents)


def print_category_tree(
    categories: Dict[str, Category],
    collapsed: Optional[Set[str]] = None,
    selected: Optional[str] = None,
) -> None:
    """Display categories in a hierarchical tree.

    Parameters
    ----------
    categories:
        Mapping of category name to :class:`Category`.
    collapsed:
        Set of category names that should be displayed collapsed.
    selected:
        Currently selected category name for highlighting.
    """

    if collapsed is None:
        collapsed = set()

    children: Dict[Optional[str], List[str]] = {}
    for cat in categories.values():
        children.setdefault(cat.parent, []).append(cat.name)

    def _print(node: Optional[str], indent: int = 0) -> None:
        for child in sorted(children.get(node, [])):
            prefix = '+' if child in collapsed else '-'
            marker = '>' if child == selected else ' '
            print('  ' * indent + f"{marker}{prefix} {child}")
            if child not in collapsed:
                _print(child, indent + 1)

    _print(None)


def interactive_tree_edit(categories: Dict[str, Category]) -> None:
    """Interactively modify categories using arrow key navigation."""

    collapsed: Set[str] = set()

    def build_tree() -> Tuple[List[Tuple[str, int]], Dict[str, str]]:
        """Return visible nodes with indent and parent mapping."""
        children: Dict[Optional[str], List[str]] = {}
        parents: Dict[str, str] = {}
        for cat in categories.values():
            children.setdefault(cat.parent, []).append(cat.name)
            if cat.parent is not None:
                parents[cat.name] = cat.parent

        order: List[Tuple[str, int]] = []

        def _collect(node: Optional[str], indent: int = 0) -> None:
            for child in sorted(children.get(node, [])):
                order.append((child, indent))
                if child not in collapsed:
                    _collect(child, indent + 1)

        _collect(None)
        return order, parents

    session = PromptSession()
    tree, parents = build_tree()
    index = 0 if tree else -1

    kb = KeyBindings()

    def refresh() -> None:
        nonlocal tree, parents, index
        tree, parents = build_tree()
        if not tree:
            index = -1
        elif index >= len(tree):
            index = len(tree) - 1
        print("\x1b[2J\x1b[H", end="")
        for i, (name, indent) in enumerate(tree):
            prefix = '+' if name in collapsed else '-'
            marker = '>' if i == index else ' '
            print('  ' * indent + f"{marker}{prefix} {name}")
        print('\nUse arrows to navigate, Enter to rename, e:edit parent, d:delete, q:quit')

    def rename_category() -> None:
        nonlocal index
        if index == -1:
            return
        name = tree[index][0]
        new_name = session.prompt(f'New name for {name}: ').strip()
        if not new_name:
            return
        cat = categories.pop(name)
        cat.name = new_name
        categories[new_name] = cat
        for c in categories.values():
            if c.parent == name:
                c.parent = new_name
        if name in collapsed:
            collapsed.remove(name)
            collapsed.add(new_name)
        refresh()
        # update selection
        tree_names = [n for n, _ in tree]
        if name in tree_names:
            index = tree_names.index(new_name)

    def change_parent() -> None:
        if index == -1:
            return
        name = tree[index][0]
        parent = session.prompt('New parent (blank for none): ').strip() or None
        categories[name].parent = parent
        refresh()

    def delete_category() -> None:
        nonlocal index
        if index == -1:
            return
        name = tree[index][0]
        categories.pop(name)
        collapsed.discard(name)
        for c in categories.values():
            if c.parent == name:
                c.parent = None
        refresh()
        if tree:
            index = max(0, min(index, len(tree) - 1))
        else:
            index = -1

    def toggle_node() -> None:
        if index == -1:
            return
        name = tree[index][0]
        if name in collapsed:
            collapsed.remove(name)
        else:
            if any(c.parent == name for c in categories.values()):
                collapsed.add(name)
        refresh()

    @kb.add('up')
    def _(event) -> None:
        nonlocal index
        if tree:
            index = (index - 1) % len(tree)
            refresh()

    @kb.add('down')
    def _(event) -> None:
        nonlocal index
        if tree:
            index = (index + 1) % len(tree)
            refresh()

    @kb.add('left')
    def _(event) -> None:
        nonlocal index
        if index == -1:
            return
        name = tree[index][0]
        if name not in collapsed and any(c.parent == name for c in categories.values()):
            collapsed.add(name)
        else:
            parent = parents.get(name)
            if parent is not None:
                for i, (n, _) in enumerate(tree):
                    if n == parent:
                        index = i
                        break
        refresh()

    @kb.add('right')
    def _(event) -> None:
        nonlocal index
        if index == -1:
            return
        name = tree[index][0]
        if name in collapsed:
            collapsed.remove(name)
        else:
            children = [c.name for c in categories.values() if c.parent == name]
            if children:
                child = sorted(children)[0]
                for i, (n, _) in enumerate(tree):
                    if n == child:
                        index = i
                        break
        refresh()

    @kb.add('enter')
    def _(event) -> None:
        event.app.run_in_terminal(rename_category)

    @kb.add('e')
    def _(event) -> None:
        event.app.run_in_terminal(change_parent)

    @kb.add('d')
    def _(event) -> None:
        event.app.run_in_terminal(delete_category)

    @kb.add('q')
    def _(event) -> None:
        event.app.exit()

    refresh()

    app = Application(layout=Layout(TextArea('')), key_bindings=kb, full_screen=True)
    app.run()
