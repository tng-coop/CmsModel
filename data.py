"""Utility functions for CMS data management."""

from typing import Dict, List, Optional
import json

from models import Category, Article


def seed_data(categories: Dict[str, Category], contents: Dict[str, Article]) -> None:
    """Populate dictionaries with sample catholic church data."""
    categories.clear()
    contents.clear()

    # Top level categories are created without a dedicated root node.
    seed_categories = {
        'Home': Category('Home', sort_order_index=0),
        'About': Category('About', sort_order_index=1),
        'Mass Times': Category('Mass Times', sort_order_index=2),
        'Sacraments': Category('Sacraments', sort_order_index=3),
        'Ministries': Category('Ministries', sort_order_index=4),
        'Downloads': Category('Downloads', sort_order_index=5),
        'Staff': Category('Staff', parent='About', sort_order_index=0),
        'History': Category('History', parent='About', sort_order_index=1),
        'Contact': Category('Contact', parent='About', sort_order_index=2),
        'Baptism': Category('Baptism', parent='Sacraments', sort_order_index=0),
        'Confirmation': Category('Confirmation', parent='Sacraments', sort_order_index=1),
        'Marriage': Category('Marriage', parent='Sacraments', sort_order_index=2),
        'Youth Ministry': Category('Youth Ministry', parent='Ministries', sort_order_index=0),
        'Choir': Category('Choir', parent='Ministries', sort_order_index=1),
        'High School': Category('High School', parent='Youth Ministry', sort_order_index=0),
    }
    categories.update(seed_categories)

    seed_contents = {
        'office_hours': Article('office_hours', ['Home'], False),
        'welcome': Article('welcome', ['Home'], False),
        'bulletin': Article('bulletin', ['Downloads'], False),
        'youth_banner': Article('youth_banner', ['Youth Ministry'], False),
        'old_news': Article('old_news', ['Home'], True),
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


def export_json(categories: Dict[str, Category], contents: Dict[str, Article]) -> str:
    """Return a JSON string representing the current tree data."""
    data = {
        "categories": [
            {
                "name": c.name,
                "parent": c.parent,
                "sort_order_index": c.sort_order_index,
            }
            for c in categories.values()
        ],
        "contents": [
            {
                "name": c.name,
                "categories": c.categories,
                "archived": c.archived,
            }
            for c in contents.values()
        ],
    }
    return json.dumps(data, indent=2)


def load_json(
    json_str: str, categories: Dict[str, Category], contents: Dict[str, Article]
) -> None:
    """Populate ``categories`` and ``contents`` from a JSON string."""
    data = json.loads(json_str)
    categories.clear()
    contents.clear()
    for cat in data.get("categories", []):
        categories[cat["name"]] = Category(
            cat["name"],
            cat.get("parent"),
            cat.get("sort_order_index", 0),
        )
    for cont in data.get("contents", []):
        contents[cont["name"]] = Article(
            cont["name"],
            list(cont.get("categories", [])),
            cont.get("archived", False),
        )
