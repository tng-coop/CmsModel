"""Utility functions for CMS data management."""

from typing import Dict, List, Optional

from .models import Category, Content


def seed_data(categories: Dict[str, Category], contents: Dict[str, Content]) -> None:
    """Populate dictionaries with sample catholic church data."""
    categories.clear()
    contents.clear()

    # Create a root CMS node so that all menu items are grouped under it.
    seed_categories = {
        "CMS": Category("CMS"),
        'Home': Category('Home', parent='CMS'),
        'About': Category('About', parent='CMS'),
        'Mass Times': Category('Mass Times', parent='CMS'),
        'Sacraments': Category('Sacraments', parent='CMS'),
        'Ministries': Category('Ministries', parent='CMS'),
        'Downloads': Category('Downloads', parent='CMS'),
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
