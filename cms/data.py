"""Utility functions for CMS data management."""

from typing import Dict, List, Optional, Set

from .models import Category, Content


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
    """Interactively modify categories with selection and collapsing."""

    collapsed: Set[str] = set()
    selected: Optional[str] = next(iter(categories)) if categories else None

    def rename_category() -> None:
        nonlocal selected
        name = input(f'Category to rename [{selected or ""}]: ').strip() or selected
        if not name or name not in categories:
            print('Category not found.')
            return
        new_name = input('New name: ').strip()
        if not new_name:
            print('Name cannot be empty.')
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
        if selected == name:
            selected = new_name

    def change_parent() -> None:
        name = input(f'Category to move [{selected or ""}]: ').strip() or selected
        if not name or name not in categories:
            print('Category not found.')
            return
        parent = input('New parent (blank for none): ').strip() or None
        categories[name].parent = parent

    def delete_category() -> None:
        nonlocal selected
        name = input(f'Category to delete [{selected or ""}]: ').strip() or selected
        if not name or name not in categories:
            print('Category not found.')
            return
        categories.pop(name)
        collapsed.discard(name)
        for c in categories.values():
            if c.parent == name:
                c.parent = None
        if selected == name:
            selected = None

    def toggle() -> None:
        if not selected:
            return
        if selected in collapsed:
            collapsed.remove(selected)
        else:
            # only allow collapsing if node has children
            if any(c.parent == selected for c in categories.values()):
                collapsed.add(selected)

    def select_category() -> None:
        nonlocal selected
        name = input('Category to select: ').strip()
        if name in categories:
            selected = name
        else:
            print('Category not found.')

    actions = {
        'r': rename_category,
        'e': change_parent,
        'd': delete_category,
        't': toggle,
        's': select_category,
    }

    while True:
        print_category_tree(categories, collapsed, selected)
        choice = input('[r]ename, [e]dit parent, [d]elete, [t]oggle, [s]elect, [q]uit: ').strip().lower()
        if choice == 'q':
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print('Unknown choice.')
