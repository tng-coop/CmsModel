"""Utility functions for CMS data management."""

from typing import Dict, List, Optional

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


def print_category_tree(categories: Dict[str, Category]) -> None:
    """Display categories in a hierarchical tree."""
    children: Dict[Optional[str], List[str]] = {}
    for cat in categories.values():
        children.setdefault(cat.parent, []).append(cat.name)

    def _print(node: Optional[str], indent: int = 0) -> None:
        for child in sorted(children.get(node, [])):
            print('  ' * indent + child)
            _print(child, indent + 1)

    _print(None)


def interactive_tree_edit(categories: Dict[str, Category]) -> None:
    """Interactively modify categories using simple key shortcuts."""

    def rename_category() -> None:
        name = input('Category to rename: ').strip()
        if name not in categories:
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

    def change_parent() -> None:
        name = input('Category to move: ').strip()
        if name not in categories:
            print('Category not found.')
            return
        parent = input('New parent (blank for none): ').strip() or None
        categories[name].parent = parent

    def delete_category() -> None:
        name = input('Category to delete: ').strip()
        if name not in categories:
            print('Category not found.')
            return
        categories.pop(name)
        for c in categories.values():
            if c.parent == name:
                c.parent = None

    actions = {
        'r': rename_category,
        'e': change_parent,
        'd': delete_category,
    }

    while True:
        print_category_tree(categories)
        choice = input('[r]ename, [e]dit parent, [d]elete, [q]uit: ').strip().lower()
        if choice == 'q':
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print('Unknown choice.')
