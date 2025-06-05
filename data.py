"""Utility functions for CMS data management."""

from typing import Dict, List, Optional
import json

from models import Category, Content


def seed_data(categories: Dict[str, Category], contents: Dict[str, Content]) -> None:
    """Populate dictionaries with sample catholic church data."""
    categories.clear()
    contents.clear()

    # Top level categories are created without a dedicated root node.
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


def export_json(categories: Dict[str, Category], contents: Dict[str, Content]) -> str:
    """Return a JSON string representing the current tree data."""
    data = {
        "categories": [
            {"name": c.name, "parent": c.parent} for c in categories.values()
        ],
        "contents": [
            {
                "name": c.name,
                "content_type": c.content_type,
                "category": c.category,
                "action": c.action,
            }
            for c in contents.values()
        ],
    }
    return json.dumps(data, indent=2)


def load_json(
    json_str: str, categories: Dict[str, Category], contents: Dict[str, Content]
) -> None:
    """Populate ``categories`` and ``contents`` from a JSON string."""
    data = json.loads(json_str)
    categories.clear()
    contents.clear()
    for cat in data.get("categories", []):
        categories[cat["name"]] = Category(cat["name"], cat.get("parent"))
    for cont in data.get("contents", []):
        contents[cont["name"]] = Content(
            cont["name"],
            cont["content_type"],
            cont["category"],
            cont["action"],
        )
